"""LLM-powered keyword expansion from seed terms."""

from src.shared.llm import generate_json
from src.shared.logger import get_logger

logger = get_logger("keyword_expander")

KEYWORD_EXPANSION_PROMPT = """Given the seed keyword "{seed}" for digital template products (Notion dashboards, planners, budget sheets, productivity systems), generate semantically related keyword variations.

Generate variations in these categories:
1. Problem-framed: keywords describing the problem the template solves
2. Audience-framed: keywords targeting specific user segments
3. Feature-framed: keywords highlighting specific template features
4. Format-framed: keywords specifying the template format/platform

Respond in JSON:
{{
  "problem_framed": ["keyword1", "keyword2", ...],
  "audience_framed": ["keyword1", "keyword2", ...],
  "feature_framed": ["keyword1", "keyword2", ...],
  "format_framed": ["keyword1", "keyword2", ...]
}}

Generate 5-8 keywords per category. Focus on terms people would actually search for on Etsy, Pinterest, or Google."""


def expand_keyword(seed: str) -> dict[str, list[str]]:
    """Use LLM to generate semantically related keywords from a seed term.

    Args:
        seed: The seed keyword to expand (e.g., "student planner").

    Returns:
        Dict with categories as keys and lists of expanded keywords as values.
    """
    logger.info("expanding_keyword_llm", seed=seed)

    prompt = KEYWORD_EXPANSION_PROMPT.format(seed=seed)
    result = generate_json(prompt)

    total = sum(len(v) for v in result.values() if isinstance(v, list))
    logger.info("keyword_expansion_complete", seed=seed, total_keywords=total)

    return result


def expand_all(seeds: list[str]) -> dict[str, dict[str, list[str]]]:
    """Expand multiple seed keywords.

    Args:
        seeds: List of seed keywords.

    Returns:
        Dict mapping each seed to its expansion results.
    """
    results: dict[str, dict[str, list[str]]] = {}
    for seed in seeds:
        results[seed] = expand_keyword(seed)
    return results
