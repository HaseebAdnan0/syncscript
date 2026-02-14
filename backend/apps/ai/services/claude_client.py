"""
Claude API client for AI research assistant features.
Handles summarization, vault insights, and question answering.
"""
from typing import Any, Dict, List
from django.conf import settings
import anthropic


class ClaudeClient:
    """
    Wrapper for Claude API calls with consistent error handling and token counting.
    """

    def __init__(self) -> None:
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured in settings")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Latest Sonnet model

    def summarize(self, text: str, source_type: str) -> Dict[str, Any]:
        """
        Generate academic summary of a source.

        Args:
            text: Source text content
            source_type: 'pdf' or 'url'

        Returns:
            Dict with keys: abstract, key_findings, methodology, limitations, keywords,
            language, quality_flags, tokens_used
            On error: {"error": "error message", "tokens_used": 0}
        """
        try:
            prompt = f"""You are an academic research assistant. Analyze the following {source_type} content and provide a structured summary.

Content:
{text[:50000]}  # Limit to ~50k chars to avoid context overflow

Provide a JSON response with this exact structure:
{{
  "abstract": "Brief 2-3 sentence overview",
  "key_findings": ["Finding 1", "Finding 2", ...],
  "methodology": "Description of research methods used",
  "limitations": "Study limitations or gaps",
  "keywords": ["keyword1", "keyword2", ...],
  "language": "detected language code (e.g., 'en', 'es', 'fr')",
  "quality_flags": ["preprint", "not_peer_reviewed", "retracted"] // include only if applicable
}}

Focus on academic rigor. If this is not an academic source, adapt the structure appropriately."""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract JSON from response
            content_block = message.content[0]
            if not hasattr(content_block, 'text'):
                return {"error": "Invalid response format", "tokens_used": 0}
            response_text = content_block.text
            tokens_used = message.usage.input_tokens + message.usage.output_tokens

            # Try to parse JSON from response
            import json
            try:
                result = json.loads(response_text)
                result['tokens_used'] = tokens_used
                return result
            except json.JSONDecodeError:
                # If response isn't pure JSON, try to extract it
                # Look for JSON object in markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                    result['tokens_used'] = tokens_used
                    return result
                else:
                    # Return structured error
                    return {
                        "error": "Failed to parse JSON response",
                        "tokens_used": tokens_used
                    }

        except anthropic.APIError as e:
            return {
                "error": f"Claude API error: {str(e)}",
                "tokens_used": 0
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "tokens_used": 0
            }

    def analyze_sources(self, sources_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate vault-level insights from multiple sources.

        Args:
            sources_data: List of dicts with keys: title, summary (optional), authors, url

        Returns:
            Dict with keys: themes, research_gaps, cross_references, suggested_searches, tokens_used
            On error: {"error": "error message", "tokens_used": 0}
        """
        try:
            # Build context from sources
            sources_text = "\n\n".join([
                f"Title: {s.get('title', 'Untitled')}\n"
                f"Authors: {s.get('authors', 'Unknown')}\n"
                f"Summary: {s.get('summary', 'No summary available')}\n"
                f"URL: {s.get('url', '')}"
                for s in sources_data
            ])

            prompt = f"""You are an academic research assistant analyzing a collection of sources in a researcher's vault.

Sources:
{sources_text[:40000]}  # Limit context

Identify patterns and provide insights in JSON format:
{{
  "themes": [
    {{"name": "Theme name", "weight": 0.0-1.0, "source_count": N}},
    ...
  ],
  "research_gaps": ["Gap description 1", "Gap description 2", ...],
  "cross_references": [
    {{"sources": ["Title A", "Title B"], "connection": "How they relate"}},
    ...
  ],
  "suggested_searches": ["Search term 1", "Search term 2", ...]
}}

Focus on identifying conceptual themes, methodological gaps, and opportunities for synthesis."""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )

            content_block = message.content[0]
            if not hasattr(content_block, 'text'):
                return {"error": "Invalid response format", "tokens_used": 0}
            response_text = content_block.text
            tokens_used = message.usage.input_tokens + message.usage.output_tokens

            # Parse JSON
            import json
            import re
            try:
                result = json.loads(response_text)
                result['tokens_used'] = tokens_used
                return result
            except json.JSONDecodeError:
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                    result['tokens_used'] = tokens_used
                    return result
                else:
                    return {
                        "error": "Failed to parse JSON response",
                        "tokens_used": tokens_used
                    }

        except anthropic.APIError as e:
            return {
                "error": f"Claude API error: {str(e)}",
                "tokens_used": 0
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "tokens_used": 0
            }

    def answer_question(self, question: str, context_chunks: List[str]) -> Dict[str, Any]:
        """
        Answer a question using provided context chunks with citations.

        Args:
            question: User's question
            context_chunks: List of relevant text chunks from sources

        Returns:
            Dict with keys: answer, citations (list of chunk indices referenced), tokens_used
            On error: {"error": "error message", "tokens_used": 0}
        """
        try:
            # Build context with chunk indices
            context_text = "\n\n".join([
                f"[Chunk {i}]\n{chunk}"
                for i, chunk in enumerate(context_chunks)
            ])

            prompt = f"""You are an academic research assistant. Answer the user's question based ONLY on the provided context chunks.

Context:
{context_text[:45000]}

Question: {question}

Provide a JSON response:
{{
  "answer": "Your detailed answer with academic rigor",
  "citations": [0, 2, 5],  // List of chunk indices you referenced
  "confidence": "high|medium|low"  // How well the context supports your answer
}}

Rules:
- Cite specific chunks by their index number
- If the context doesn't contain enough information, say so clearly (confidence: low)
- Use academic tone
- Admit uncertainty when appropriate"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            content_block = message.content[0]
            if not hasattr(content_block, 'text'):
                return {"error": "Invalid response format", "tokens_used": 0}
            response_text = content_block.text
            tokens_used = message.usage.input_tokens + message.usage.output_tokens

            # Parse JSON
            import json
            import re
            try:
                result = json.loads(response_text)
                result['tokens_used'] = tokens_used
                return result
            except json.JSONDecodeError:
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                    result['tokens_used'] = tokens_used
                    return result
                else:
                    return {
                        "error": "Failed to parse JSON response",
                        "tokens_used": tokens_used
                    }

        except anthropic.APIError as e:
            return {
                "error": f"Claude API error: {str(e)}",
                "tokens_used": 0
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "tokens_used": 0
            }
