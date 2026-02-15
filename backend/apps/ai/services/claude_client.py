"""
AI client using OpenRouter for model access.
Handles summarization, vault insights, and question answering.
"""
import json
import re
from typing import Any, Dict, List
from django.conf import settings
import requests


class ClaudeClient:
    """
    Wrapper for OpenRouter API calls with consistent error handling and token counting.
    Uses OpenRouter to access various AI models (Claude, Gemini, etc.)
    """

    def __init__(self) -> None:
        self.api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured in settings")

        self.model = getattr(settings, 'OPENROUTER_MODEL', 'google/gemini-2.5-pro-preview')
        self.site_url = getattr(settings, 'OPENROUTER_SITE_URL', 'http://localhost:3000')
        self.site_name = getattr(settings, 'OPENROUTER_SITE_NAME', 'SyncScript')
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def _make_request(self, messages: List[Dict[str, str]], max_tokens: int = 2000) -> Dict[str, Any]:
        """Make a request to OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name,
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from response, handling markdown code blocks."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # Try to find raw JSON object
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            raise ValueError("Could not parse JSON from response")

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
            from apps.ai.prompts import format_source_summary_prompt
            prompt = format_source_summary_prompt(text, source_type)

            response = self._make_request(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )

            # Extract response
            response_text = response['choices'][0]['message']['content']
            tokens_used = response.get('usage', {}).get('total_tokens', 0)

            try:
                result = self._parse_json_response(response_text)
                result['tokens_used'] = tokens_used
                return result
            except (json.JSONDecodeError, ValueError):
                return {
                    "error": "Failed to parse JSON response",
                    "raw_response": response_text[:500],
                    "tokens_used": tokens_used
                }

        except requests.exceptions.RequestException as e:
            return {
                "error": f"API request error: {str(e)}",
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
            from apps.ai.prompts import format_vault_insights_prompt

            # Build context from sources
            sources_text = "\n\n".join([
                f"Title: {s.get('title', 'Untitled')}\n"
                f"Authors: {s.get('authors', 'Unknown')}\n"
                f"Summary: {s.get('summary', 'No summary available')}\n"
                f"URL: {s.get('url', '')}"
                for s in sources_data
            ])

            prompt = format_vault_insights_prompt(sources_text)

            response = self._make_request(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000
            )

            response_text = response['choices'][0]['message']['content']
            tokens_used = response.get('usage', {}).get('total_tokens', 0)

            try:
                result = self._parse_json_response(response_text)
                result['tokens_used'] = tokens_used
                return result
            except (json.JSONDecodeError, ValueError):
                return {
                    "error": "Failed to parse JSON response",
                    "tokens_used": tokens_used
                }

        except requests.exceptions.RequestException as e:
            return {
                "error": f"API request error: {str(e)}",
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
            from apps.ai.prompts import format_question_answer_prompt

            # Build context with chunk indices
            context_text = "\n\n".join([
                f"[Chunk {i}]\n{chunk}"
                for i, chunk in enumerate(context_chunks)
            ])

            prompt = format_question_answer_prompt(question, context_text)

            response = self._make_request(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )

            response_text = response['choices'][0]['message']['content']
            tokens_used = response.get('usage', {}).get('total_tokens', 0)

            try:
                result = self._parse_json_response(response_text)
                result['tokens_used'] = tokens_used
                return result
            except (json.JSONDecodeError, ValueError):
                return {
                    "error": "Failed to parse JSON response",
                    "tokens_used": tokens_used
                }

        except requests.exceptions.RequestException as e:
            return {
                "error": f"API request error: {str(e)}",
                "tokens_used": 0
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "tokens_used": 0
            }
