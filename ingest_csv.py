import sqlite3
import csv
import sys
import os

DB_PATH = 'isekai.db'

def ingest_csv(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist.")
        sys.exit(1)

    if not os.path.exists(DB_PATH):
        print(f"Error: Database {DB_PATH} does not exist. Please run 'make init' first.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip empty lines and comments
            if not row or row[0].startswith('#'):
                continue
            
            # Ensure the row has word, type, and meaning
            if len(row) >= 3:
                word = row[0].strip()
                word_type = row[1].strip()
                meaning = row[2].strip()
                
                try:
                    cursor.execute(
                        'INSERT INTO kana_srs (word, meaning, type) VALUES (?, ?, ?)',
                        (word, meaning, word_type)
                    )
                    count += 1
                except sqlite3.IntegrityError:
                    # Word already exists in DB, skip
                    pass

    conn.commit()
    conn.close()
    print(f"Successfully ingested {count} new vocabularies from {csv_path} into the database.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python ingest_csv.py <path_to_csv>")
        sys.exit(1)
        
    ingest_csv(sys.argv[1])