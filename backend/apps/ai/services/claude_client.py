"""
Claude API client for AI research assistant features.
Handles summarization, vault insights, and question answering.
"""
from typing import Any, Dict, List
from django.conf import settings
import anthropic
from apps.ai.prompts import (
    format_source_summary_prompt,
    format_vault_insights_prompt,
    format_question_answer_prompt,
)


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
            prompt = format_source_summary_prompt(text, source_type)

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

            prompt = format_vault_insights_prompt(sources_text)

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

            prompt = format_question_answer_prompt(question, context_text)

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
