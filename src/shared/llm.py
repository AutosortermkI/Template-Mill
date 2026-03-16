"""Claude API wrapper with retry, rate limiting, and structured output."""

import json

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from src.shared.config import settings
from src.shared.exceptions import LLMException, LLMParseError
from src.shared.logger import get_logger

logger = get_logger("llm")

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Get or create the Anthropic client."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def generate(
    prompt: str,
    system: str = "",
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> str:
    """Generate text from Claude with automatic retry."""
    logger.info("llm_generate", model=model, prompt_length=len(prompt))
    try:
        messages = [{"role": "user", "content": prompt}]
        response = get_client().messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system if system else anthropic.NOT_GIVEN,
            messages=messages,
        )
        result = response.content[0].text
        logger.info("llm_generate_complete", response_length=len(result))
        return result
    except anthropic.APIError as e:
        logger.error("llm_api_error", error=str(e))
        raise LLMException(f"Claude API error: {e}") from e


def generate_json(prompt: str, system: str = "", **kwargs: object) -> dict:
    """Generate and parse JSON response from Claude."""
    json_system = (system + "\n\n" if system else "") + "Respond ONLY with valid JSON. No markdown, no preamble."
    raw = generate(prompt, system=json_system, **kwargs)
    clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        logger.error("llm_json_parse_error", raw_response=raw[:200], error=str(e))
        raise LLMParseError(f"Failed to parse LLM JSON response: {e}") from e
