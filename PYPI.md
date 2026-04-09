# PyPI Packaging Plan
**Branch:** `feat/pypi-packaging`

## Context
Make the dashboard installable via `pip install isekai-dashboard` so it can be used on any machine without cloning the repo.

## Steps

### 1. Create package directory
Move all source code into `isekai_dashboard/`:
```
isekai_dashboard/
  __init__.py          # version = "0.1.0"
  main.py              # from root main.py
  db_init.py           # from root db_init.py
  import_vocab.py      # from root import_vocab.py
  ingest_csv.py        # from root ingest_csv.py
  vocab_extractor.py   # from root vocab_extractor.py
  clients/             # from root clients/
  core/                # from root core/
  services/            # from root services/
  ui/                  # from root ui/
  data/                # CSV example files (optional, for seeding)
```

### 2. Fix all internal imports
Every `from clients.x` / `from services.x` / `from ui.x` / `from core.x` becomes `from isekai_dashboard.clients.x` etc.

Use relative imports within the package where appropriate (e.g., `from .clients.x`).

### 3. Update pyproject.toml
```toml
[project]
name = "isekai-dashboard"
version = "0.1.0"
description = "Terminal-based developer dashboard with quests, SRS, pomodoro, and calendar"
readme = "README.md"
requires-python = ">=3.11"   # lower from 3.13 for wider reach
license = "MIT"
authors = [{ name = "Your Name", email = "you@example.com" }]
dependencies = [
    "icalevents>=0.3.1",
    "openai>=2.29.0",
    "textual>=8.1.1",
]

[project.scripts]
isekai = "isekai_dashboard.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
]
```

### 4. Fix DB and log file paths
Currently `isekai.db` and `isekai.log` are created in CWD. For a pip-installed tool, use XDG-compliant paths:
- DB: `~/.local/share/isekai-dashboard/isekai.db`
- Log: `~/.local/share/isekai-dashboard/isekai.log`
- Create directory on first run with `os.makedirs(..., exist_ok=True)`
- Allow override via `ISEKAI_DATA_DIR` env var

### 5. Ensure main.py has a callable entry point
```python
def main():
    app = IsekaiDashboard()
    app.run()

if __name__ == "__main__":
    main()
```

### 6. Add LICENSE file
Pick a license (MIT suggested) and add `LICENSE` to repo root.

### 7. Update .gitignore
Ensure these are excluded:
```
dist/
*.egg-info/
isekai.db
isekai.log
```

### 8. Include package data
If shipping CSV example files or CSS, configure in pyproject.toml:
```toml
[tool.hatchling.build]
include = ["isekai_dashboard/**"]
```

### 9. Update Makefile
Update `make run` and other targets to work with the new package structure:
```makefile
run:
    uv run -m isekai_dashboard.main
```

### 10. Update tests
Fix test imports to match new package paths.

---

## Verification
```bash
# Local editable install
pip install -e .
isekai              # should launch dashboard

# Build
pip install build
python -m build     # should produce dist/*.whl and dist/*.tar.gz

# Publish (when ready)
pip install twine
twine upload dist/*
```

## Decisions to make before starting
- [ ] License choice (MIT?)
- [ ] Lower `requires-python` to `>=3.11`? (3.13 limits audience)
- [ ] Ship example CSV data in the package or keep separate?
- [ ] PyPI package name — `isekai-dashboard` available?
