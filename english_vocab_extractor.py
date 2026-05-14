import argparse
import csv
import os
import json
from openai import OpenAI
from typing import Set

from core.db import get_shared_connection, release_connection


def get_existing_words(csv_path: str) -> Set[str]:
    words = set()
    conn = get_shared_connection()
    try:
        for row in conn.execute("SELECT word FROM english_srs"):
            words.add(row["word"])
    except Exception as e:
        print(f"Warning: Could not read from database. {e}")
    finally:
        release_connection(conn)

    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            for row in csv.reader(f):
                if row and not row[0].startswith("#"):
                    words.add(row[0].strip())
    return words


def extract_vocab_from_text(text: str, client: OpenAI) -> list[dict]:
    prompt = f"""
    You are an expert English vocabulary tutor. Extract useful vocabulary from the following text.
    For each word, provide: word, part_of_speech, definition, example sentence.
    Return strictly as a JSON array. Do not include markdown formatting.
    Text:
    {text}
    """
    response = client.chat.completions.create(
        model="google/gemini-2.5-pro",
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.choices[0].message.content.strip()
    for marker in ("```json", "```"):
        if content.startswith(marker):
            content = content[len(marker):].strip()
            if content.endswith("```"):
                content = content[:-3].strip()
            break
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data.get("vocabularies", next((v for v in data.values() if isinstance(v, list)), []))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        print("Failed to parse LLM output as JSON.")
        print("Raw output:", content)
        return []


def main():
    parser = argparse.ArgumentParser(description="Extract English vocabularies from text.")
    parser.add_argument("--text", help="Direct text input.")
    parser.add_argument("input_file", nargs="?", help="Path to text/markdown file.")
    parser.add_argument("--output", default="english_vocab.csv", help="Output CSV path.")
    args = parser.parse_args()

    if not args.text and not args.input_file:
        print("Usage: uv run english_vocab_extractor.py --text 'text' | file.md")
        return

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: Set OPENROUTER_API_KEY environment variable.")
        return

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    if args.text:
        text = args.text
        print("Extracting English vocabularies from provided text...")
    else:
        if not os.path.exists(args.input_file):
            print(f"Error: File not found: {args.input_file}")
            return
        with open(args.input_file, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"Extracting English vocabularies from {args.input_file}...")

    extracted = extract_vocab_from_text(text, client)
    if not extracted:
        print("No vocabularies extracted.")
        return

    existing = get_existing_words(args.output)
    new = [v for v in extracted if v.get("word") and v["word"] not in existing]
    if not new:
        print("All extracted vocabularies already exist.")
        return

    print(f"Found {len(new)} new vocabularies. Appending to {args.output}...")
    file_exists = os.path.exists(args.output)
    with open(args.output, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["# word", "part_of_speech", "definition", "example"])
        for v in new:
            writer.writerow([v.get("word", ""), v.get("part_of_speech", ""),
                             v.get("definition", ""), v.get("example", "")])
    print(f"Done! {len(new)} words appended.")


if __name__ == "__main__":
    main()