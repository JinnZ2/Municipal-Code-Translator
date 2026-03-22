# CLAUDE.md

## Project Overview

Municipal Code Translator is a Python tool that translates zoning laws, building codes, permit requirements, and municipal ordinances into plain English. It converts bureaucratic jargon into actionable information for homeowners, small business owners, renters, and contractors.

## Repository Structure

```
Municipal-Code-Translator/
├── municipal_translator.py   # Main application (single-file tool)
├── README.md                 # Project documentation and usage examples
├── LICENSE                   # MIT License
└── CLAUDE.md                 # This file
```

This is a minimal, single-file Python project. All logic lives in `municipal_translator.py`.

## Tech Stack

- **Language**: Python 3.7+
- **Dependencies** (no `requirements.txt` yet — listed in README only):
  - `requests` — HTTP requests / web scraping
  - `beautifulsoup4` (`bs4`) — HTML parsing
  - `pandas` — data processing
  - `PyPDF2` or `PyMuPDF` — PDF processing (referenced in README)
- **Standard library**: `re`, `json`, `time`, `urllib.parse`, `pathlib`, `dataclasses`, `typing`

## Key Architecture

### Data Classes
- `MunicipalTranslationResult` — dataclass holding translation output: original text, plain English, actionable lists (what you can/cannot do, permits, deadlines, fees, contacts, next steps), confidence score, code type, and municipality.

### Main Class: `MunicipalCodeTranslator`
- Initializes internal dictionaries at construction time:
  - `load_municipal_jargon()` — 500+ term translations (zoning, building, admin, fees, business licensing)
  - `load_code_patterns()` — regex patterns for different municipal code types
  - `load_zoning_codes()` — zoning code reference data
  - `load_permit_keywords()` — keywords identifying permit requirements

### Supported Document Types
- Zoning ordinances
- Building codes
- Business licensing requirements
- Housing regulations
- Development standards

### Supported Regions
- California, Texas, Florida, and general US city patterns

## CLI Usage

```bash
# Process a local PDF
python municipal_translator.py --file "city-zoning-code.pdf" --output "my-zoning-explained"

# Scrape a city website
python municipal_translator.py --url "https://cityname.gov/municipal-code" --municipality "Your City"

# Process text directly
python municipal_translator.py --text "Your municipal code text here"
```

### Python API

```python
from municipal_translator import MunicipalCodeTranslator
translator = MunicipalCodeTranslator()
result = translator.translate_municipal_code(code_text, municipality="Your City")
```

## Build / Test / Lint

**None configured.** There are currently no tests, linting, CI/CD, or build commands. No `requirements.txt`, `setup.py`, or `pyproject.toml` exists.

## Known Issues

- `municipal_translator.py` contains **triplicated content** — the same module header, imports, dataclass, and class definition are repeated three times in the file.
- The file uses `**init**` instead of `__init__` (markdown-style bold formatting leaked into code).
- Code blocks use markdown triple-backtick fences (` ``` `) inside the `.py` file — this is invalid Python syntax.
- Methods like `load_code_patterns()` are incomplete (return statement with `{` but no body).

## Code Conventions

- Type hints used throughout (PEP 484 style)
- Docstrings on methods
- Single class per module pattern
- Dictionary-heavy data modeling for jargon/pattern lookup
- `@dataclass` for structured results

## Development Notes

- The project is early-stage with a well-defined vision but incomplete implementation.
- When contributing, maintain the plain-English translation philosophy — jargon mappings should be accessible to non-experts.
- Keep the single-file architecture unless complexity demands splitting.
