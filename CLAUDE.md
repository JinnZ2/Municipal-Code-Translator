# CLAUDE.md

## Project Overview

Municipal Code Translator is a Python tool that translates zoning laws, building codes, permit requirements, and municipal ordinances into plain English. It converts bureaucratic jargon into actionable information for homeowners, small business owners, renters, and contractors.

## Repository Structure

```
Municipal-Code-Translator/
├── municipal_translator.py   # Main application (single-file tool, importable module)
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore rules
├── README.md                 # Project documentation and usage examples
├── LICENSE                   # MIT License
└── CLAUDE.md                 # This file
```

Single-file Python project. All logic lives in `municipal_translator.py`.

## Naming Conventions

- **snake_case** for filenames, functions, variables, methods (PEP 8)
- **PascalCase** for class names (PEP 8)
- Private/internal methods prefixed with `_` (e.g. `_load_municipal_jargon`)

## Tech Stack

- **Language**: Python 3.7+
- **Dependencies** (see `requirements.txt`):
  - `requests` — HTTP requests / web scraping
  - `beautifulsoup4` (`bs4`) — HTML parsing
- **Standard library**: `re`, `json`, `time`, `urllib.parse`, `pathlib`, `dataclasses`, `typing`, `argparse`

## Key Architecture

### Data Classes
- `MunicipalTranslationResult` — dataclass holding translation output: original text, plain English, actionable lists (what you can/cannot do, permits, deadlines, fees, contacts, next steps), confidence score, code type, and municipality.

### Main Class: `MunicipalCodeTranslator`

**Private loader methods** (called at init):
- `_load_municipal_jargon()` — term translations (zoning, building, admin, fees, business licensing)
- `_load_code_patterns()` — regex patterns for detecting municipal code types
- `_load_zoning_codes()` — zoning designation mappings (R-1, C-2, M-1, etc.)
- `_load_permit_keywords()` — phrases indicating permit requirements

**Public extraction methods:**
- `detect_code_type(text)` — scores text against code patterns to classify it
- `translate_jargon(text)` — replaces jargon terms with plain English
- `extract_permits(text)` — finds sentences containing permit keywords
- `extract_fees(text)` — finds dollar amounts in context
- `extract_deadlines(text)` — finds deadline/timeframe references
- `extract_allowed(text)` — finds statements about what is permitted
- `extract_prohibited(text)` — finds statements about what is prohibited
- `extract_contact_info(text)` — finds phone numbers, emails, department references

**Private helpers:**
- `_compute_confidence(text, plain_english)` — dynamic confidence score based on jargon recognition ratio

**Main entry point:**
- `translate_municipal_code(text, municipality)` — orchestrates all extractors, returns `MunicipalTranslationResult`

## CLI Usage

```bash
# Process a local text file
python municipal_translator.py --file "city-zoning-code.txt" --municipality "Your City"

# Scrape a city website
python municipal_translator.py --url "https://cityname.gov/municipal-code" --municipality "Your City"

# Process text directly
python municipal_translator.py --text "Your municipal code text here"
```

## Python API

```python
from municipal_translator import MunicipalCodeTranslator
translator = MunicipalCodeTranslator()
result = translator.translate_municipal_code(code_text, municipality="Your City")
```

## Install

```bash
pip install -r requirements.txt
```

## Build / Test / Lint

No test framework, linting, or CI/CD is configured yet.

## Code Conventions

- Type hints on all method signatures (PEP 484)
- Docstrings on all methods
- Single class per module
- Dictionary-heavy data modeling for jargon/pattern lookup
- `@dataclass` for structured results
- Imports grouped: standard library first, then third-party (PEP 8)

## Development Notes

- When contributing, maintain the plain-English translation philosophy — jargon mappings should be accessible to non-experts.
- Keep the single-file architecture unless complexity demands splitting.
- The file is both a CLI script and an importable module.
