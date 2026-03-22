#!/usr/bin/env python3
"""
Municipal Code Translator - Making Local Government Understandable

Translates zoning laws, building codes, permit requirements, and municipal ordinances
into plain English so regular people can understand what they can actually do.
"""

import re
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import pandas as pd


@dataclass
class MunicipalTranslationResult:
    original_text: str
    plain_english: str
    what_you_can_do: List[str]
    what_you_cannot_do: List[str]
    permits_required: List[str]
    deadlines: List[str]
    fees: List[str]
    contact_info: List[str]
    next_steps: List[str]
    confidence_score: float
    code_type: str
    municipality: str


class MunicipalCodeTranslator:
    def __init__(self):
        self.municipal_jargon = self._load_municipal_jargon()
        self.code_patterns = self._load_code_patterns()
        self.zoning_codes = self._load_zoning_codes()
        self.permit_keywords = self._load_permit_keywords()

    def _load_municipal_jargon(self) -> Dict[str, str]:
        """Municipal government jargon translation dictionary."""
        return {
            # Zoning terms
            'conditional use permit': 'special permission needed (requires application and possibly a hearing)',
            'variance': 'exception to the normal rules (hard to get)',
            'non-conforming use': "something that was legal before but isn't now (usually can continue)",
            'setback requirements': 'how far from property lines you must build',
            'floor area ratio': 'limits on how big your building can be compared to your lot size',
            'density restrictions': 'limits on how many units you can have',
            'height restrictions': 'maximum height allowed for buildings',
            'lot coverage': 'percentage of your lot that can have buildings on it',
            'accessory dwelling unit': 'small apartment or guest house on your property',
            'planned unit development': 'special development with relaxed rules',

            # Building codes
            'certificate of occupancy': 'official permission to live in or use a building',
            'building permit': 'permission to construct or renovate',
            'right of way': 'public property (usually for roads/utilities)',
            'easement': 'someone else has rights to use part of your property',
            'egress requirements': 'rules about exits and escape routes',
            'fire separation': 'walls that slow down fire spread',
            'structural load': 'how much weight a building can safely hold',
            'code compliance': 'meets all the safety and legal requirements',

            # Administrative terms
            'public hearing': 'meeting where residents can speak for/against proposal',
            'administrative review': 'staff decides (no public hearing)',
            'discretionary permit': 'decision depends on specific circumstances',
            'ministerial permit': 'automatic if you meet requirements',
            'site plan review': 'detailed review of your construction plans',
            'environmental review': 'study of environmental impact',
            'appeals process': 'how to challenge a decision',
            'vested rights': "permission you already have that can't be taken away",

            # Fees and timing
            'impact fees': 'charges for effects on infrastructure',
            'processing time': 'how long approval takes',
            'renewal requirements': 'what you need to do to keep permits active',
            'expiration date': 'when permission runs out',
            'phased development': 'building in stages over time',

            # Business licensing
            'business license': 'permission to operate a business',
            'home occupation permit': 'permission to run business from home',
            'commercial use': 'business or retail activity',
            'industrial use': 'manufacturing or heavy business',
            'mixed use': 'combination of residential and commercial',
        }

    def _load_code_patterns(self) -> Dict[str, Dict]:
        """Patterns for different types of municipal codes."""
        return {
            'zoning': {
                'keywords': ['zone', 'zoning', 'land use', 'district', 'overlay'],
                'pattern': r'(?i)(zone|zoning|land\s+use|district|overlay)',
            },
            'building': {
                'keywords': ['building', 'construction', 'structural', 'fire', 'egress'],
                'pattern': r'(?i)(building|construction|structural|fire|egress)',
            },
            'business-licensing': {
                'keywords': ['license', 'licensing', 'business', 'occupation', 'commercial'],
                'pattern': r'(?i)(license|licensing|business|occupation|commercial)',
            },
            'housing': {
                'keywords': ['housing', 'rental', 'tenant', 'landlord', 'habitability'],
                'pattern': r'(?i)(housing|rental|tenant|landlord|habitability)',
            },
        }

    def _load_zoning_codes(self) -> Dict[str, str]:
        """Common zoning code designations and their meanings."""
        return {
            'R-1': 'single-family residential',
            'R-2': 'two-family residential (duplex)',
            'R-3': 'multi-family residential (apartments)',
            'R-4': 'high-density residential',
            'C-1': 'neighborhood commercial (small shops)',
            'C-2': 'general commercial (larger businesses)',
            'C-3': 'heavy commercial',
            'M-1': 'light industrial (warehouses, workshops)',
            'M-2': 'heavy industrial (factories)',
            'O-S': 'open space',
            'P-D': 'planned development',
            'A-1': 'agricultural',
            'MU': 'mixed use (residential + commercial)',
        }

    def _load_permit_keywords(self) -> List[str]:
        """Keywords that indicate a permit or approval is required."""
        return [
            'shall require',
            'permit required',
            'subject to approval',
            'must obtain',
            'application required',
            'conditional upon',
            'prior to',
            'approval of',
            'reviewed by',
            'in accordance with',
        ]

    def detect_code_type(self, text: str) -> str:
        """Detect what type of municipal code the text represents."""
        scores: Dict[str, int] = {}
        text_lower = text.lower()
        for code_type, info in self.code_patterns.items():
            matches = re.findall(info['pattern'], text_lower)
            scores[code_type] = len(matches)
        if not scores or max(scores.values()) == 0:
            return 'general'
        return max(scores, key=scores.get)

    def translate_jargon(self, text: str) -> str:
        """Replace municipal jargon with plain-English equivalents."""
        result = text
        for jargon, plain in sorted(self.municipal_jargon.items(), key=lambda x: -len(x[0])):
            pattern = re.compile(re.escape(jargon), re.IGNORECASE)
            result = pattern.sub(f'{plain}', result)
        return result

    def extract_permits(self, text: str) -> List[str]:
        """Extract permit requirements from the text."""
        permits: List[str] = []
        for keyword in self.permit_keywords:
            pattern = re.compile(rf'([^.]*{re.escape(keyword)}[^.]*\.)', re.IGNORECASE)
            matches = pattern.findall(text)
            permits.extend(matches)
        return permits

    def extract_fees(self, text: str) -> List[str]:
        """Extract fee amounts mentioned in the text."""
        fee_pattern = re.compile(r'[^.]*\$[\d,]+(?:\.\d{2})?[^.]*\.', re.IGNORECASE)
        return fee_pattern.findall(text)

    def extract_deadlines(self, text: str) -> List[str]:
        """Extract deadlines and timeframes from the text."""
        deadline_pattern = re.compile(
            r'[^.]*(?:within\s+\d+\s+days|deadline|expires?|due\s+date|'
            r'no\s+later\s+than|time\s+limit)[^.]*\.',
            re.IGNORECASE,
        )
        return deadline_pattern.findall(text)

    def translate_municipal_code(
        self, text: str, municipality: str = "Unknown"
    ) -> MunicipalTranslationResult:
        """Translate a block of municipal code text into plain English."""
        code_type = self.detect_code_type(text)
        plain_english = self.translate_jargon(text)
        permits = self.extract_permits(text)
        fees = self.extract_fees(text)
        deadlines = self.extract_deadlines(text)

        return MunicipalTranslationResult(
            original_text=text,
            plain_english=plain_english,
            what_you_can_do=[],
            what_you_cannot_do=[],
            permits_required=permits,
            deadlines=deadlines,
            fees=fees,
            contact_info=[],
            next_steps=[],
            confidence_score=0.5,
            code_type=code_type,
            municipality=municipality,
        )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Translate municipal codes into plain English'
    )
    parser.add_argument('--file', type=str, help='Path to a municipal code file (PDF or text)')
    parser.add_argument('--url', type=str, help='URL of a municipal code webpage to scrape')
    parser.add_argument('--text', type=str, help='Municipal code text to translate directly')
    parser.add_argument('--municipality', type=str, default='Unknown', help='Name of the municipality')
    parser.add_argument('--output', type=str, help='Output file path (without extension)')
    args = parser.parse_args()

    translator = MunicipalCodeTranslator()

    if args.text:
        result = translator.translate_municipal_code(args.text, municipality=args.municipality)
        print(json.dumps(asdict(result), indent=2))
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file not found: {args.file}")
            raise SystemExit(1)
        text = path.read_text(encoding='utf-8')
        result = translator.translate_municipal_code(text, municipality=args.municipality)
        print(json.dumps(asdict(result), indent=2))
    elif args.url:
        response = requests.get(args.url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        result = translator.translate_municipal_code(text, municipality=args.municipality)
        print(json.dumps(asdict(result), indent=2))
    else:
        parser.print_help()
