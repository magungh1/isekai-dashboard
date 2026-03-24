"""Import vocabulary from a CSV file into the database.

Kana CSV format (3 columns, no header):
    word,type,meaning
    むらさき,hiragana,purple
    コーヒー,katakana,coffee

English CSV format (4 columns, no header):
    word,part_of_speech,definition,example
    ephemeral,adj,lasting for a very short time,Ephemeral containers are destroyed after use

Usage:
    uv run python import_vocab.py vocab.csv                  # auto-detect format
    uv run python import_vocab.py --type kana vocab.csv      # force kana
    uv run python import_vocab.py --type english vocab.csv   # force english
"""

import csv
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from core.db import get_shared_connection


def import_kana_csv(filepath: str) -> None:
    conn = get_shared_connection()
    added = 0
    skipped = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, 1):
            if not row or row[0].startswith('#'):
                continue

            if len(row) < 3:
                print(f"  Line {row_num}: skipped (need 3 columns, got {len(row)})")
                skipped += 1
                continue

            word = row[0].strip()
            kana_type = row[1].strip().lower()
            meaning = row[2].strip()

            if kana_type not in ('hiragana', 'katakana'):
                print(f"  Line {row_num}: skipped (type must be 'hiragana' or 'katakana', got '{kana_type}')")
                skipped += 1
                continue

            try:
                conn.execute(
                    'INSERT INTO kana_srs (word, meaning, type) VALUES (?, ?, ?)',
                    (word, meaning, kana_type)
                )
                added += 1
            except sqlite3.IntegrityError:
                print(f"  Line {row_num}: skipped ('{word}' already exists)")
                skipped += 1

    conn.commit()
    print(f"Kana import done. Added: {added}, Skipped: {skipped}")


def import_english_csv(filepath: str) -> None:
    conn = get_shared_connection()
    added = 0
    skipped = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, 1):
            if not row or row[0].startswith('#'):
                continue

            if len(row) < 3:
                print(f"  Line {row_num}: skipped (need at least 3 columns, got {len(row)})")
                skipped += 1
                continue

            word = row[0].strip()
            pos = row[1].strip().lower()
            definition = row[2].strip()
            example = row[3].strip() if len(row) > 3 else None

            try:
                conn.execute(
                    'INSERT INTO english_srs (word, part_of_speech, definition, example) VALUES (?, ?, ?, ?)',
                    (word, pos, definition, example)
                )
                added += 1
            except sqlite3.IntegrityError:
                print(f"  Line {row_num}: skipped ('{word}' already exists)")
                skipped += 1

    conn.commit()
    print(f"English import done. Added: {added}, Skipped: {skipped}")


def detect_type(filepath: str) -> str:
    """Auto-detect CSV type by checking column content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            if len(row) >= 3:
                col2 = row[1].strip().lower()
                if col2 in ('hiragana', 'katakana'):
                    return 'kana'
                return 'english'
    return 'english'


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]

    if not args:
        print("Usage: uv run python import_vocab.py [--type kana|english] <file.csv>")
        print()
        print("Kana CSV (3 columns):    word,type,meaning")
        print("  むらさき,hiragana,purple")
        print()
        print("English CSV (3-4 columns): word,part_of_speech,definition[,example]")
        print("  ephemeral,adj,lasting for a very short time,Ephemeral containers vanish")
        sys.exit(1)

    filepath = args[0]
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    vocab_type = None
    for flag in flags:
        if flag.startswith('--type='):
            vocab_type = flag.split('=', 1)[1]
        elif flag == '--type' and len(args) > 1:
            vocab_type = args.pop(0)

    # Parse --type flag
    for i, flag in enumerate(flags):
        if flag == '--type' and i + 1 < len(sys.argv):
            # Find the value after --type
            idx = sys.argv.index('--type')
            if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith('--'):
                vocab_type = sys.argv[idx + 1]

    if vocab_type is None:
        vocab_type = detect_type(filepath)
        print(f"Auto-detected type: {vocab_type}")

    if vocab_type == 'kana':
        import_kana_csv(filepath)
    elif vocab_type == 'english':
        import_english_csv(filepath)
    else:
        print(f"Error: Unknown type '{vocab_type}'. Use 'kana' or 'english'.")
        sys.exit(1)
