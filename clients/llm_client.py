import logging
import os
import re

from openai import OpenAI

logger = logging.getLogger(__name__)

from config import get
OPENROUTER_BASE_URL = get("llm", "base_url", "https://openrouter.ai/api/v1")
MODEL = get("llm", "model", "nvidia/nemotron-3-super-120b-a12b:free")

# Reasoning models need extra token budget for internal thinking
_MAX_TOKENS = get("llm", "max_tokens", 1000)


def get_client() -> OpenAI | None:
    api_key = get("llm", "api_key", "") or os.environ.get('OPENROUTER_API_KEY', '')
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set in config or environment")
        return None
    logger.info("OpenRouter API key found (length=%d)", len(api_key))
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


def _call(client: OpenAI, prompt: str) -> str | None:
    """Make an API call and extract content, with reasoning model fallback."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=_MAX_TOKENS,
        )
        text = response.choices[0].message.content
        if text:
            return text.strip()
        # Fallback: extract from reasoning field
        reasoning = getattr(response.choices[0].message, 'reasoning', None)
        if reasoning:
            # Take last non-empty line as the answer
            lines = [l.strip() for l in reasoning.strip().split('\n') if l.strip()]
            if lines:
                return lines[-1]
        return None
    except Exception:
        logger.exception("API call failed")
        return "(API error — check isekai.log)"


def generate_mnemonic(word: str, meaning: str) -> str | None:
    client = get_client()
    if client is None:
        return None
    return _call(client, (
        f"Create a short, clever mnemonic for the Katakana word '{word}' "
        f"meaning '{meaning}'. Under 20 words. Reply with ONLY the mnemonic."
    ))


def generate_kanji_mnemonic(kanji: str, meaning: str,
                            kun: str | None, on: str | None) -> str | None:
    client = get_client()
    if client is None:
        return None

    readings = []
    if kun:
        readings.append(f"kun: {kun}")
    if on:
        readings.append(f"on: {on}")
    reading_str = ", ".join(readings) if readings else "no common readings"

    return _call(client, (
        f"Create a short mnemonic for kanji '{kanji}' meaning '{meaning}' "
        f"({reading_str}). Under 25 words. Reply with ONLY the mnemonic."
    ))


def generate_english_mnemonic(word: str, definition: str) -> str | None:
    client = get_client()
    if client is None:
        return None
    return _call(client, (
        f"Create a short mnemonic for the word '{word}' meaning '{definition}'. "
        f"Under 20 words. Reply with ONLY the mnemonic."
    ))
