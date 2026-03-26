import argparse
import sqlite3
import csv
import os
import json
from openai import OpenAI
from typing import Set

DB_PATH = "isekai.db"

def get_existing_words(csv_path: str) -> Set[str]:
    words = set()
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT word FROM english_srs")
            for row in cursor.fetchall():
                words.add(row[0])
            conn.close()
        except Exception as e:
            print(f"Warning: Could not read from database. {e}")
            
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith('#'):
                    words.add(row[0].strip())
                    
    return words

def extract_vocab_from_text(text: str, client: OpenAI) -> list[dict]:
    prompt = f"""
    You are an expert English vocabulary tutor. Extract useful English vocabulary words from the following text.
    For each word, provide:
    1. word: The English word (in its dictionary/base form).
    2. part_of_speech: The part of speech, choose exactly one from: 'noun', 'verb', 'adj', 'adv', 'prep', 'conj', 'interj', 'pron'.
    3. definition: Clear English definition of the word in this context.
    4. example: A sentence example showing how the word is used.
    
    Return the result STRICTLY as a JSON array of objects, with keys "word", "part_of_speech", "definition", "example". 
    Do not include markdown formatting like ```json or any other text.
    
    Example output format:
    [
        {{"word": "ephemeral", "part_of_speech": "adj", "definition": "lasting for a very short time", "example": "Ephemeral containers are destroyed after use"}},
        {{"word": "ubiquitous", "part_of_speech": "adj", "definition": "present, appearing, or found everywhere", "example": "Smartphones have become ubiquitous in modern society"}}
    ]
    
    Text:
    {text}
    """
    
    response = client.chat.completions.create(
        model="google/gemini-2.5-pro", 
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.choices[0].message.content.strip()
    
    if content.startswith("```json"):
        content = content[7:-3].strip()
    elif content.startswith("```"):
        content = content[3:-3].strip()
        
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "vocabularies" in data:
             return data["vocabularies"]
        elif isinstance(data, list):
             return data
        elif isinstance(data, dict):
            for val in data.values():
                if isinstance(val, list):
                    return val
            return []
    except json.JSONDecodeError:
        print("Failed to parse LLM output as JSON.")
        print("Raw output:", content)
        return []

def main():
    parser = argparse.ArgumentParser(description="Extract English vocabularies from text and append new ones to a CSV.")
    parser.add_argument("--text", help="Direct text input to extract vocabularies from.")
    parser.add_argument("input_file", nargs='?', help="Path to the input text or markdown file.")
    parser.add_argument("--output", default="english_vocab.csv", help="Path to the output CSV file.")
    args = parser.parse_args()

    if not args.text and not args.input_file:
        print("Error: Either --text or input_file must be provided.")
        print("Usage:")
        print("  uv run english_vocab_extractor.py --text 'your text here'")
        print("  uv run english_vocab_extractor.py path/to/file.md")
        return

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        print("Please set it via: export OPENROUTER_API_KEY='your_key'")
        return

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    if args.text:
        text = args.text
        print("Extracting English vocabularies from provided text...")
    else:
        if not os.path.exists(args.input_file):
            print(f"Error: Input file {args.input_file} not found.")
            return
        with open(args.input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"Extracting English vocabularies from {args.input_file}...")

    extracted_vocabs = extract_vocab_from_text(text, client)
    
    if not extracted_vocabs:
        print("No vocabularies extracted.")
        return
        
    existing_words = get_existing_words(args.output)
    
    new_vocabs = []
    for vocab in extracted_vocabs:
        word = vocab.get("word")
        if word and word not in existing_words:
            new_vocabs.append(vocab)
            existing_words.add(word)
            
    if not new_vocabs:
        print("All extracted vocabularies already exist in the database or CSVs.")
        return
        
    print(f"Found {len(new_vocabs)} new vocabularies. Appending to {args.output}...")
    
    file_exists = os.path.exists(args.output)
    with open(args.output, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["# word", "part_of_speech", "definition", "example"])
            
        for vocab in new_vocabs:
            writer.writerow([
                vocab.get("word", ""), 
                vocab.get("part_of_speech", ""), 
                vocab.get("definition", ""),
                vocab.get("example", "")
            ])
            
    print(f"Done! {len(new_vocabs)} words appended. Please review {args.output} before inserting into the DB.")

if __name__ == "__main__":
    main()
