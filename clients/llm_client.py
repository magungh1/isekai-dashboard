import os

from openai import OpenAI

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
MODEL = 'google/gemini-2.5-pro-exp-03-25:free'


def get_client() -> OpenAI | None:
    if not OPENROUTER_API_KEY:
        return None
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)


def generate_mnemonic(word: str, meaning: str) -> str | None:
    client = get_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{
                'role': 'user',
                'content': (
                    f"You are a helpful Japanese tutor for an ML Engineer. "
                    f"Create a short, clever mnemonic to help remember the Katakana word "
                    f"'{word}' which means '{meaning}'. "
                    f"Relate it to software engineering or machine learning if possible. "
                    f"Keep it under 20 words. Reply with ONLY the mnemonic, nothing else."
                )
            }],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def generate_english_mnemonic(word: str, definition: str) -> str | None:
    client = get_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{
                'role': 'user',
                'content': (
                    f"You are a vocabulary coach for an ML Engineer. "
                    f"Create a short, clever mnemonic to remember that "
                    f"'{word}' means '{definition}'. "
                    f"Use wordplay, etymology, or relate it to tech/ML if possible. "
                    f"Keep it under 20 words. Reply with ONLY the mnemonic, nothing else."
                )
            }],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None
