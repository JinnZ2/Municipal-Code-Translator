# CLAUDE.md

## Project Overview

Municipal Code Translator is a Python tool that translates zoning laws, building codes, permit requirements, and municipal ordinances into plain English. It converts bureaucratic jargon into actionable information for homeowners, small business owners, renters, and contractors.

## Repository Structure

```
Municipal-Code-Translator/
├── municipal-translator.py   # Main application (single-file CLI tool)
├── README.md                 # Project documentation and usage examples
├── LICENSE                   # MIT License
└── CLAUDE.md                 # This file
```

This is a minimal, single-file Python project. All logic lives in `municipal-translator.py`.

## Naming Convention

- **Kebab-case** for filenames (e.g. `municipal-translator.py`)
- **snake_case** for Python identifiers (functions, variables, methods) per PEP 8
- **PascalCase** for class names per PEP 8
- Private/internal methods prefixed with `_` (e.g. `_load_municipal_jargon`)
- Code pattern keys use kebab-case (e.g. `'business-licensing'`)

## Tech Stack

- **Language**: Python 3.7+
- **Dependencies** (no `requirements.txt` yet — listed in README only):
  - `requests` — HTTP requests / web scraping
  - `beautifulsoup4` (`bs4`) — HTML parsing
  - `pandas` — data processing
- **Standard library**: `re`, `json`, `time`, `urllib.parse`, `pathlib`, `dataclasses`, `typing`, `argparse`

## Key Architecture

### Data Classes
- `MunicipalTranslationResult` — dataclass holding translation output: original text, plain English, actionable lists (what you can/cannot do, permits, deadlines, fees, contacts, next steps), confidence score, code type, and municipality.

### Main Class: `MunicipalCodeTranslator`
- Initializes internal dictionaries at construction time via private loader methods:
  - `_load_municipal_jargon()` — term translations (zoning, building, admin, fees, business licensing)
  - `_load_code_patterns()` — regex patterns for detecting municipal code types (zoning, building, business-licensing, housing)
  - `_load_zoning_codes()` — zoning designation mappings (R-1, C-2, M-1, etc.)
  - `_load_permit_keywords()` — phrases indicating permit requirements
- Public translation methods:
  - `detect_code_type(text)` — scores text against code patterns to classify it
  - `translate_jargon(text)` — replaces jargon terms with plain English
  - `extract_permits(text)` — finds sentences containing permit keywords
  - `extract_fees(text)` — finds dollar amounts in context
  - `extract_deadlines(text)` — finds deadline/timeframe references
  - `translate_municipal_code(text, municipality)` — main entry point, returns `MunicipalTranslationResult`

## CLI Usage

```bash
# Process a local text file
python municipal-translator.py --file "city-zoning-code.txt" --municipality "Your City"

# Scrape a city website
python municipal-translator.py --url "https://cityname.gov/municipal-code" --municipality "Your City"

# Process text directly
python municipal-translator.py --text "Your municipal code text here"
```

## Build / Test / Lint

**None configured.** There are currently no tests, linting, CI/CD, or build commands. No `requirements.txt`, `setup.py`, or `pyproject.toml` exists.

## Code Conventions

- Type hints on all method signatures (PEP 484)
- Docstrings on all methods
- Single class per module pattern
- Dictionary-heavy data modeling for jargon/pattern lookup
- `@dataclass` for structured results
- Imports grouped: standard library first, then third-party (PEP 8)

## Development Notes

- The project is early-stage with a well-defined vision.
- When contributing, maintain the plain-English translation philosophy — jargon mappings should be accessible to non-experts.
- Keep the single-file architecture unless complexity demands splitting.
- Note: because the filename uses kebab-case, it cannot be imported as a Python module directly. It is intended as a CLI script.
