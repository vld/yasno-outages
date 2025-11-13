# Yasno outages parser

## How to run

1. **Create a virtual environment**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate 
   ```

1. **Install `uv`**
   ```bash
   pip install uv
   ```

1. **Install all required packages**
   ```bash
   uv sync
   ```

1. **Create env file**
   ```bash
   cp example.env .env
   ```
1. **Run the project**
   ```bash
   uv run --env-file .env main.py >> yasno.log 2>&1
   ```

1. **Run tests**
   ```bash
   uv run pytest
   ```

## TODO:
- [ ] Don't notify with empty slots 
- [ ] Don't notify about tomorrow until 12:00
- [ ] Change message for all day without outages 
