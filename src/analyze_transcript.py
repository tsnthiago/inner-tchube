"""Analyze YouTube video transcript with Gemini."""

import sys

from google import genai

from .config import (
    GEMINI_API_KEY,
    GEMINI_COST_PER_1M_INPUT,
    GEMINI_COST_PER_1M_OUTPUT,
    GEMINI_MODEL,
)
from .get_transcript import get_transcript


def analyze_transcript(url_or_id: str, prompt: str, model: str | None = None) -> dict:
    """Fetch transcript, send to Gemini, return analysis with usage and cost. Accepts video URL or ID."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env")

    segments = get_transcript(url_or_id)
    transcript_text = "\n".join(s["text"] for s in segments).strip()
    if not transcript_text:
        raise ValueError("Transcript not available for this video.")

    full_prompt = f"{prompt}\n\n{transcript_text}"
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=model or GEMINI_MODEL,
        contents=full_prompt,
    )

    result = {"text": response.text}
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        meta = response.usage_metadata
        tokens_in = getattr(meta, "prompt_token_count", 0) or 0
        tokens_out = getattr(meta, "candidates_token_count", 0) or 0
        total = getattr(meta, "total_token_count", 0) or (tokens_in + tokens_out)
        cost_in = (tokens_in / 1_000_000) * GEMINI_COST_PER_1M_INPUT
        cost_out = (tokens_out / 1_000_000) * GEMINI_COST_PER_1M_OUTPUT
        result["usage"] = {
            "prompt_token_count": tokens_in,
            "candidates_token_count": tokens_out,
            "total_token_count": total,
            "estimated_cost_usd": round(cost_in + cost_out, 6),
        }
    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m src.analyze_transcript <url_or_id> <prompt>")
        sys.exit(1)
    try:
        out = analyze_transcript(sys.argv[1], sys.argv[2])
        print(out["text"])
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
