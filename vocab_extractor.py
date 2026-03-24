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
    # 1. From DB
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT word FROM kana_srs")
            for row in cursor.fetchall():
                words.add(row[0])
            conn.close()
        except Exception as e:
            print(f"Warning: Could not read from database. {e}")
            
    # 2. From Output CSV
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith('#'):
                    words.add(row[0].strip())
                    
    # 3. From example_vocab.csv
    example_csv = "example_vocab.csv"
    if os.path.exists(example_csv):
        with open(example_csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith('#'):
                    words.add(row[0].strip())
                    
    return words

def extract_vocab_from_text(text: str, client: OpenAI) -> list[dict]:
    prompt = f"""
    You are an expert Japanese tutor. Extract useful Japanese vocabularies (words) from the following text.
    For each word, provide:
    1. word: The Japanese word (in its original/dictionary form).
    2. type: The character type, choose exactly one from: 'katakana', 'hiragana', or 'kanji'.
    3. meaning: The English meaning of the word in this context.
    
    Return the result STRICTLY as a JSON array of objects, with keys "word", "type", "meaning". 
    Do not include markdown formatting like ```json or any other text.
    
    Example output format:
    [
        {{"word": "パソコン", "type": "katakana", "meaning": "personal computer"}},
        {{"word": "食べる", "type": "kanji", "meaning": "to eat"}}
    ]
    
    Text:
    {text}
    """
    
    # We use gemini-2.5-pro via OpenRouter for high-quality extraction
    response = client.chat.completions.create(
        model="google/gemini-2.5-pro", 
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.choices[0].message.content.strip()
    
    # Clean up markdown if the LLM adds it anyway
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
            # Try to find a list value just in case
            for val in data.values():
                if isinstance(val, list):
                    return val
            return []
    except json.JSONDecodeError:
        print("Failed to parse LLM output as JSON.")
        print("Raw output:", content)
        return []

def main():
    parser = argparse.ArgumentParser(description="Extract Japanese vocabularies from a text file and append new ones to a CSV.")
    parser.add_argument("input_file", help="Path to the input text or markdown file.")
    parser.add_argument("--output", default="more_vocab.csv", help="Path to the output CSV file.")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        print("Please set it via: export OPENROUTER_API_KEY='your_key'")
        return

    # Initialize OpenAI client pointed at OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    if not os.path.exists(args.input_file):
        print(f"Error: Input file {args.input_file} not found.")
        return

    with open(args.input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"Extracting vocabularies from {args.input_file}...")
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
            writer.writerow(["# word", "type", "meaning"])
            
        for vocab in new_vocabs:
            writer.writerow([vocab.get("word"), vocab.get("type"), vocab.get("meaning")])
            
    print(f"Done! {len(new_vocabs)} words appended. Please review {args.output} before inserting into the DB.")

if __name__ == "__main__":
    main()