# CLAUDE.md

## Project Overview

Municipal Code Translator is a Python tool that translates zoning laws, building codes, permit requirements, and municipal ordinances into plain English. It converts bureaucratic jargon into actionable information for homeowners, small business owners, renters, and contractors.

## Repository Structure

```
Municipal-Code-Translator/
├── municipal_translator.py              # Core translator (CLI + importable module)
├── regulatory_intelligence_engine.py    # Analytics layer built on the translator
├── examples/
│   └── sample_ordinance.txt             # Sample input used by docs and tests
├── tests/
│   ├── test_municipal_translator.py
│   └── test_regulatory_intelligence_engine.py
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore rules
├── README.md                 # Project documentation and usage examples
├── LICENSE                   # MIT License
└── CLAUDE.md                 # This file
```

Two modules, layered. `municipal_translator.py` owns all parsing, jargon, and
extraction. `regulatory_intelligence_engine.py` imports from it and adds
analytics — it must never reimplement translation logic. Three divergent copies
of `MunicipalCodeTranslator` previously existed; keep it to one.

## Naming Conventions

- **snake_case** for filenames, functions, variables, methods (PEP 8)
- **PascalCase** for class names (PEP 8)
- Private/internal methods prefixed with `_` (e.g. `_load_municipal_jargon`)

## Tech Stack

- **Language**: Python 3.7+
- **Dependencies** (see `requirements.txt`):
  - `requests` — HTTP requests / web scraping
  - `beautifulsoup4` (`bs4`) — HTML parsing
- **Standard library**: `re`, `json`, `enum`, `urllib.parse`, `pathlib`, `dataclasses`, `typing`, `argparse`, `unittest`

## Key Architecture

### `municipal_translator.py` — core translator

**Data class:** `MunicipalTranslationResult` — original text, plain English,
actionable lists (what you can/cannot do, permits, deadlines, fees, contacts,
next steps), confidence score, code type + label, municipality. Has
`to_dict()` / `to_json()`.

**Private loaders** (called at init):
- `_load_municipal_jargon()` — term translations (zoning, building, admin, fees, licensing)
- `_load_legalese()` — legalese phrase rewrites (`shall` family, `prior to`, …)
- `_load_code_patterns()` — indicator terms for classifying code type
- `_load_zoning_codes()` — zoning designation mappings (R-1, C-2, M-1, …)
- `_load_permit_keywords()` — phrases indicating permit requirements
- `_compile_regexes()` — builds the combined single-pass substitution table

**Public methods:**
- `detect_code_type(text)` — weighted scoring; multi-word indicators count 3x
- `translate_jargon(text, keep_original=True)` — single-pass plain-English rewrite
- `split_sentences(text)` — decimal- and section-number-safe sentence splitter
- `extract_permits / extract_fees / extract_fee_amounts / extract_deadlines`
- `extract_allowed / extract_prohibited / extract_contact_info`
- `translate_municipal_code(text, municipality)` — main entry point
- `translate(...)` — alias for the above
- `fetch_and_translate_url(url, ...)` — scrape and translate a page

**Module function:** `format_report(result)` — plain-text report rendering.

### `regulatory_intelligence_engine.py` — analytics layer

Imports `MunicipalCodeTranslator` from the core module. Never reimplements it.

- `RegulatoryAnalysis` — subclasses `MunicipalTranslationResult`, adding stated
  intent, root causes, citations, fee breakdown, audit metrics
- `RegulationRootCauseAnalyzer` — maps text to systemic policy drivers
- `CitationGraphExtractor` — local / state / federal / standards citations
- `FeeExplorationEngine` — flat, per-sqft, per-unit, and valuation-% fees;
  reports which project inputs were missing so totals are not silently low
- `IntentAndPurposeExtractor` — purpose clauses and WHEREAS preambles
- `PolicyAuditEngine` — measurable KPIs and an auditability index
- `RegulatoryIntelligenceEngine.analyze(...)` — runs the whole pipeline
- `format_intelligence_report(report)` — plain-text report rendering

## CLI Usage

```bash
# Core translator
python municipal_translator.py --file "city-zoning-code.txt" --municipality "Your City"
python municipal_translator.py --url "https://cityname.gov/municipal-code"
python municipal_translator.py --text "Your municipal code text here" --format json
python municipal_translator.py --file code.txt --output reports/my-city   # .txt + .json

# Regulatory intelligence, with project inputs for the fee estimator
python regulatory_intelligence_engine.py --file examples/sample_ordinance.txt \
    --municipality "City of Austin" --sqft 800 --valuation 150000
```

Both CLIs take exactly one input source (`--file`, `--url`, or `--text`) and
support `--format report|json`. PDFs are rejected with a message telling the
user to convert first; there is no PDF parser in this project.

## Python API

```python
from municipal_translator import MunicipalCodeTranslator
translator = MunicipalCodeTranslator()
result = translator.translate_municipal_code(code_text, municipality="Your City")

from regulatory_intelligence_engine import RegulatoryIntelligenceEngine
engine = RegulatoryIntelligenceEngine()
report = engine.analyze(code_text, municipality="Your City",
                        project_params={"sqft": 800, "valuation": 150000})
```

## Install

```bash
pip install -r requirements.txt
```

`requests` and `beautifulsoup4` are only needed for `--url`. Everything else
runs on the standard library.

## Build / Test / Lint

```bash
python -m unittest discover -s tests
```

84 tests, standard-library `unittest` only. No linter or CI is configured yet.

## Code Conventions

- Type hints on all method signatures (PEP 484)
- Docstrings on all methods
- One responsibility per class; the analytics sub-engines are separate classes
- Dictionary-heavy data modeling for jargon/pattern lookup
- `@dataclass` for structured results
- Imports grouped: standard library first, then third-party (PEP 8)

## Development Notes

- When contributing, maintain the plain-English translation philosophy — jargon mappings should be accessible to non-experts.
- Keep translation logic in `municipal_translator.py` only. The engine layer
  builds on it; do not fork a second copy of the translator.
- Each module is both a CLI script and an importable module.
- Add a regression test for every parsing bug fixed — `tests/` documents the
  known failure modes (meaning-inverting `shall` rewrites, cascading jargon
  substitution, phantom $0 fees from rate expressions, prose read as citations).
