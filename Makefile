.PHONY: run init extract ingest clean help

help:
	@echo "Available commands:"
	@echo "  make run                   - Run the Isekai Dev Dashboard (via uv)"
	@echo "  make init                  - Initialize database and seed base vocab (via uv)"
	@echo "  make extract FILE=path     - Extract vocabularies from a text/markdown file (e.g., make extract FILE=novel.md)"
	@echo "  make ingest FILE=path.csv  - Ingest vocabularies from a CSV into the DB (e.g., make ingest FILE=more_vocab.csv)"
	@echo "  make clean                 - Clean up cache files (__pycache__, uv cache)"

run:
	uv run main.py

init:
	uv run db_init.py

extract:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE argument is required. Usage: make extract FILE=path/to/file.md"; \
		exit 1; \
	fi
	uv run vocab_extractor.py "$(FILE)"

ingest:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE argument is required. Usage: make ingest FILE=path/to/file.csv"; \
		exit 1; \
	fi
	uv run ingest_csv.py "$(FILE)"

clean:
	@echo "Cleaning up cache..."
	uv cache clean
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "Done."