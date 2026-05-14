import psycopg2.errors
import csv
import sys
import os

from core.db import get_shared_connection, release_connection


def ingest_csv(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist.")
        sys.exit(1)

    conn = get_shared_connection()
    count = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith("#"):
                continue

            if len(row) >= 3:
                word = row[0].strip()
                word_type = row[1].strip()
                meaning = row[2].strip()

                try:
                    if word_type == "kanji":
                        kun_reading = row[3].strip() if len(row) > 3 else ""
                        on_reading = row[4].strip() if len(row) > 4 else ""

                        conn.execute(
                            "INSERT INTO kanji_srs "
                            "(kanji, kun_reading, on_reading, meaning) "
                            "VALUES (%s, %s, %s, %s)",
                            (word, kun_reading, on_reading, meaning),
                        )
                    else:
                        conn.execute(
                            "INSERT INTO kana_srs "
                            "(word, meaning, type) VALUES (%s, %s, %s)",
                            (word, meaning, word_type),
                        )
                    count += 1
                except psycopg2.errors.UniqueViolation:
                    conn.rollback()

    conn.commit()
    release_connection(conn)
    print(f"Successfully ingested {count} new vocabularies into the database.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_csv.py <path_to_csv>")
        sys.exit(1)

    ingest_csv(sys.argv[1])