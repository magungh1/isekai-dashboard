import logging
import os

from openai import OpenAI
from config import get, get_int

logger = logging.getLogger(__name__)


def get_client() -> OpenAI | None:
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not found in environment")
        return None
    base_url = get("llm", "base_url")
    logger.info("OPENROUTER_API_KEY found (length=%d), base_url=%s", len(api_key), base_url)
    return OpenAI(base_url=base_url, api_key=api_key)


def _call(client: OpenAI, prompt: str) -> str | None:
    model = get("llm", "model")
    max_tokens = get_int("llm", "max_tokens", default=1000)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=max_tokens,
        )
        text = response.choices[0].message.content
        if text:
            return text.strip()
        reasoning = getattr(response.choices[0].message, 'reasoning', None)
        if reasoning:
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
