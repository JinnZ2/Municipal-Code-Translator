#!/usr/bin/env python3
"""
Municipal Code Translator - Making Local Government Understandable

Translates zoning laws, building codes, permit requirements, and municipal ordinances
into plain English so regular people can understand what they can actually do.
"""

import re
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Set
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup


@dataclass
class MunicipalTranslationResult:
    original_text: str
    plain_english: str
    what_you_can_do: List[str] = field(default_factory=list)
    what_you_cannot_do: List[str] = field(default_factory=list)
    permits_required: List[str] = field(default_factory=list)
    deadlines: List[str] = field(default_factory=list)
    fees: List[str] = field(default_factory=list)
    contact_info: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    code_type: str = "Unknown"
    municipality: str = "Generic"


class MunicipalCodeTranslator:
    """
    Translates legalistic municipal codes, zoning bylaws, and permit requirements
    into structured, actionable plain-English guidance.
    """

    def __init__(self):
        self.municipal_jargon = self.load_municipal_jargon()
        self.code_patterns = self.load_code_patterns()
        self.zoning_codes = self.load_zoning_codes()
        self.permit_keywords = self.load_permit_keywords()
        self._compile_regexes()

    def load_municipal_jargon(self) -> Dict[str, str]:
        """Municipal government jargon translation dictionary."""
        return {
            # Zoning terms
            'conditional use permit': 'special permission needed (requires application and public hearing)',
            'variance': 'exception to standard zoning rules (requires showing hardship)',
            'non-conforming use': 'grandfathered property use (legal past use allowed to continue)',
            'setback requirements': 'minimum required distance between building and property line',
            'floor area ratio': 'limit on total building size relative to lot area',
            'density restrictions': 'maximum allowed dwelling units per acre',
            'height restrictions': 'maximum allowed building height',
            'lot coverage': 'maximum percentage of lot ground covered by structures',
            'accessory dwelling unit': 'secondary residential unit (ADU / guest house / mother-in-law suite)',
            'planned unit development': 'custom development zone with flexible rules',

            # Building codes
            'certificate of occupancy': 'official permit required before living in or using a building',
            'building permit': 'official authorization to begin construction or renovation',
            'right of way': 'publicly owned land reserved for roads, sidewalks, or utilities',
            'easement': 'legal right for utility companies or neighbors to access part of your land',
            'egress requirements': 'mandatory exit paths and emergency rescue openings',
            'fire separation': 'fire-resistant barriers between adjoining spaces',
            'structural load': 'weight capacity limits for floors, roofs, and foundations',
            'code compliance': 'meeting all safety, structural, and environmental standards',

            # Administrative terms
            'public hearing': 'formal community meeting where neighbors can comment on your proposal',
            'administrative review': 'staff-level review (no public hearing required)',
            'discretionary permit': 'approval choice left to council/board subjective judgment',
            'ministerial permit': 'mandatory approval if objective checklist criteria are met',
            'site plan review': 'detailed engineering and layout assessment by city staff',
            'environmental review': 'assessment of potential ecological impacts',
            'appeals process': 'formal steps to challenge a rejected permit decision',
            'vested rights': 'protected legal rights preventing retroactive rule changes',

            # Fees and timing
            'impact fees': 'mandatory city fees to fund local infrastructure strain',
            'processing time': 'estimated review window before decision is issued',
            'renewal requirements': 'mandatory steps to keep permit active',
            'expiration date': 'deadline when unused permit authorization voids',
            'phased development': 'approved multi-stage construction plan over time',

            # Business licensing
            'business license': 'official permit to operate a business',
            'home occupation permit': 'permission to run a small business from a home',
            'commercial use': 'retail, office, or service business activities',
            'industrial use': 'manufacturing, processing, or heavy commercial storage',
            'mixed use': 'combined residential and commercial development',
        }

    def load_code_patterns(self) -> Dict[str, Dict]:
        """Patterns for identifying ordinance and code categories."""
        return {
            'zoning': {
                'indicators': ['zone', 'district', 'setback', 'lot area', 'use classification', 'adu', 'far'],
                'label': 'Zoning Ordinance'
            },
            'building': {
                'indicators': ['building code', 'occupancy', 'fire wall', 'egress', 'electrical', 'plumbing', 'ibc'],
                'label': 'Building & Safety Code'
            },
            'permitting': {
                'indicators': ['application', 'permit fee', 'submittal', 'site plan', 'review period'],
                'label': 'Permit Administrative Rule'
            },
            'business': {
                'indicators': ['business license', 'home occupation', 'signage', 'noise ordinance', 'operating hours'],
                'label': 'Business & Commercial Regulation'
            }
        }

    def load_zoning_codes(self) -> Dict[str, str]:
        """Common municipal zoning designation lookup map."""
        return {
            'R-1': 'Single-Family Residential (Low Density)',
            'R-2': 'Two-Family / Duplex Residential',
            'R-3': 'Multi-Family Residential (Apartments / Condos)',
            'C-1': 'Neighborhood Commercial (Local retail & services)',
            'C-2': 'General Commercial (Shopping centers & offices)',
            'M-1': 'Light Industrial (Warehousing & light assembly)',
            'M-2': 'Heavy Industrial (Manufacturing)',
            'PUD': 'Planned Unit Development (Custom mixed zoning)',
            'A-1': 'Agricultural / Open Space'
        }

    def load_permit_keywords(self) -> List[str]:
        """Keywords indicating mandatory approval mechanisms."""
        return [
            'shall obtain', 'permit required', 'subject to approval', 'conditional use',
            'variance required', 'application shall be submitted', 'license required'
        ]

    def _compile_regexes(self):
        """Pre-compiles extraction regular expressions for speed."""
        self.re_allow = re.compile(
            r'([^.;\n]*?\b(?:shall be permitted|is allowed|may construct|may operate|permitted use|authorized to|right to)\b[^.;\n]*)',
            re.I
        )
        self.re_prohibit = re.compile(
            r'([^.;\n]*?\b(?:shall not|prohibited|unlawful|no person shall|not permitted|forbidden|strictly restricted)\b[^.;\n]*)',
            re.I
        )
        self.re_permits = re.compile(
            r'([^.;\n]*?\b(?:permit|variance|approval|certificate|license|authorization)\b[^.;\n]*)',
            re.I
        )
        self.re_deadlines = re.compile(
            r'([^.;\n]*?\b(?:\d+\s+(?:days|months|years)|prior to|within|no later than|deadline|expiration)\b[^.;\n]*)',
            re.I
        )
        self.re_fees = re.compile(
            r'([^.;\n]*?\b(?:\$\d+(?:\,\d{3})*(?:\.\d{2})?|fee|charge|assessment|deposit)\b[^.;\n]*)',
            re.I
        )
        self.re_contact = re.compile(
            r'([^.;\n]*?\b(?:department|official|inspector|clerk|email|phone|office of|board)\b[^.;\n]*)',
            re.I
        )

    def translate(self, text: str, municipality: str = "Generic Jurisdiction") -> MunicipalTranslationResult:
        """Processes legal text into plain English and structured actionable rules."""
        if not text.strip():
            return MunicipalTranslationResult(original_text="", plain_english="No text provided.", municipality=municipality)

        code_type = self._determine_code_type(text)
        plain_text = self._convert_to_plain_english(text)

        can_do = self._clean_matches(self.re_allow.findall(text))
        cannot_do = self._clean_matches(self.re_prohibit.findall(text))
        permits = self._clean_matches(self.re_permits.findall(text))
        deadlines = self._clean_matches(self.re_deadlines.findall(text))
        fees = self._clean_matches(self.re_fees.findall(text))
        contact = self._clean_matches(self.re_contact.findall(text))

        next_steps = self._generate_next_steps(permits, deadlines, fees)
        confidence = self._calculate_confidence(text, can_do, cannot_do, permits)

        return MunicipalTranslationResult(
            original_text=text,
            plain_english=plain_text,
            what_you_can_do=can_do,
            what_you_cannot_do=cannot_do,
            permits_required=permits,
            deadlines=deadlines,
            fees=fees,
            contact_info=contact,
            next_steps=next_steps,
            confidence_score=confidence,
            code_type=code_type,
            municipality=municipality
        )

    def fetch_and_translate_url(self, url: str, selector: Optional[str] = None) -> MunicipalTranslationResult:
        """Fetches municipal code from a URL and translates it."""
        try:
            headers = {'User-Agent': 'MunicipalCodeTranslator/2.0 (Public Legal Access Tool)'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            target_node = soup.select_one(selector) if selector else (soup.find('main') or soup.find('body'))
            text_content = target_node.get_text(separator=' ', strip=True) if target_node else soup.get_text()

            domain = urlparse(url).netloc
            return self.translate(text_content[:4000], municipality=domain)
        except Exception as e:
            return MunicipalTranslationResult(
                original_text="",
                plain_english=f"Error fetching document from URL: {str(e)}",
                confidence_score=0.0
            )

    def _determine_code_type(self, text: str) -> str:
        """Identifies ordinance domain using keyword frequencies."""
        text_lower = text.lower()
        scores = {}
        for category, config in self.code_patterns.items():
            matches = sum(1 for kw in config['indicators'] if kw in text_lower)
            scores[config['label']] = matches

        best_match = max(scores, key=scores.get)
        return best_match if scores[best_match] > 0 else "General Municipal Code"

    def _convert_to_plain_english(self, text: str) -> str:
        """Translates legal jargon into simplified plain text."""
        plain = text
        
        # Replace zoning notation matches
        for zone, desc in self.zoning_codes.items():
            plain = re.sub(rf'\b{zone}\b', f"{zone} ({desc})", plain)

        # Replace jargon terms (case-insensitive substitution)
        for term, plain_term in self.municipal_jargon.items():
            pattern = re.compile(rf'\b{re.escape(term)}\b', re.I)
            plain = pattern.sub(f"**[{plain_term.upper()}]**", plain)

        # Simplify common legalese
        plain = re.sub(r'\bshall\b', 'must', plain, flags=re.I)
        plain = re.sub(r'\bprior to\b', 'before', plain, flags=re.I)
        plain = re.sub(r'\bpursuant to\b', 'under', plain, flags=re.I)

        return plain

    def _clean_matches(self, matches: List[str]) -> List[str]:
        """Cleans and deduplicates extracted clause fragments."""
        cleaned = []
        seen = set()
        for m in matches:
            clause = m.strip().rstrip(',;')
            clause_clean = re.sub(r'\s+', ' ', clause)
            if len(clause_clean) > 15 and clause_clean.lower() not in seen:
                seen.add(clause_clean.lower())
                cleaned.append(clause_clean)
        return cleaned[:5]  # Top 5 distinct clauses

    def _generate_next_steps(self, permits: List[str], deadlines: List[str], fees: List[str]) -> List[str]:
        """Generates concrete sequential next steps for property owners."""
        steps = []
        if permits:
            steps.append("Contact the local Planning & Building Department to obtain application forms.")
        if fees:
            steps.append("Verify fee amounts and required payment methods before submitting.")
        if deadlines:
            steps.append("Calendar all review timelines and submittal expiration dates.")
        if not steps:
            steps.append("Review full municipal code text or confirm compliance with city staff.")
        return steps

    def _calculate_confidence(self, text: str, can_do: List[str], cannot_do: List[str], permits: List[str]) -> float:
        """Estimates parsing confidence based on rule match density."""
        word_count = len(text.split())
        if word_count == 0:
            return 0.0

        matches = len(can_do) + len(cannot_do) + len(permits)
        density = matches / (word_count / 50.0)  # Expect ~1 match per 50 words
        confidence = min(0.5 + (density * 0.25), 0.95)
        return round(confidence, 2)


# --- Example Usage Demonstration ---

if __name__ == "__main__":
    translator = MunicipalCodeTranslator()

    sample_ordinance = (
        "Section 17.04.120 - Accessory Dwelling Units (ADU) in R-1 Zones.\n"
        "An ADU shall be permitted on any lot containing an existing single-family residence. "
        "No person shall construct an ADU exceeding a maximum height restriction of 16 feet. "
        "A conditional use permit is required prior to construction if setback requirements are less than 4 feet. "
        "Application shall be submitted to the Planning Department with a non-refundable processing fee of $350. "
        "The department shall render a decision within 60 days of complete submittal."
    )

    result = translator.translate(sample_ordinance, municipality="City of Oakridge")

    print(f"=== MUNICIPAL TRANSLATION REPORT ===")
    print(f"Jurisdiction  : {result.municipality}")
    print(f"Category      : {result.code_type}")
    print(f"Confidence    : {result.confidence_score * 100}%\n")

    print("--- PLAIN ENGLISH SUMMARY ---")
    print(result.plain_english)

    print("\n--- WHAT YOU CAN DO ---")
    for item in result.what_you_can_do:
        print(f"  ✓ {item}")

    print("\n--- WHAT YOU CANNOT DO ---")
    for item in result.what_you_cannot_do:
        print(f"  ✗ {item}")

    print("\n--- PERMITS REQUIRED ---")
    for item in result.permits_required:
        print(f"  ! {item}")

    print("\n--- FEES & DEADLINES ---")
    print(f"  Fees     : {', '.join(result.fees) if result.fees else 'None detected'}")
    print(f"  Deadlines: {', '.join(result.deadlines) if result.deadlines else 'None detected'}")

    print("\n--- RECOMMENDED NEXT STEPS ---")
    for step in result.next_steps:
        print(f"  -> {step}")
