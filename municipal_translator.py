#!/usr/bin/env python3
"""
Municipal Code Translator - Making Local Government Understandable

Translates zoning laws, building codes, permit requirements, and municipal ordinances
into plain English so regular people can understand what they can actually do.
"""

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - exercised only without optional deps
    requests = None
    BeautifulSoup = None


CODE_TYPE_LABELS: Dict[str, str] = {
    'zoning': 'Zoning Ordinance',
    'building': 'Building & Safety Code',
    'permitting': 'Permit Administrative Rule',
    'business-licensing': 'Business & Commercial Regulation',
    'housing': 'Housing & Tenant Regulation',
    'general': 'General Municipal Code',
}


@dataclass
class MunicipalTranslationResult:
    """Structured, plain-English translation of a block of municipal code."""

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
    code_type: str = 'general'
    code_type_label: str = CODE_TYPE_LABELS['general']
    municipality: str = 'Unknown'

    def to_dict(self) -> Dict:
        """Return the result as a plain dictionary (JSON-serializable)."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Return the result as a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class MunicipalCodeTranslator:
    """
    Translates legalistic municipal codes, zoning bylaws, and permit requirements
    into structured, actionable plain-English guidance.
    """

    # Splits on sentence-ending punctuation only when the next chunk starts a new
    # sentence. Guards decimals ("0.75"), section numbers ("17.04.120"), and
    # lowercase abbreviations ("sq. ft. and ...") from being split apart.
    _SENTENCE_SPLIT = re.compile(r'(?<=[.;!?])\s+(?=["\'(\[]?[A-Z0-9])')
    _PARAGRAPH_SPLIT = re.compile(r'\n\s*\n')

    def __init__(self) -> None:
        self.municipal_jargon = self._load_municipal_jargon()
        self.code_patterns = self._load_code_patterns()
        self.zoning_codes = self._load_zoning_codes()
        self.permit_keywords = self._load_permit_keywords()
        self.legalese = self._load_legalese()
        self._compile_regexes()

    # ------------------------------------------------------------------
    # Data loaders
    # ------------------------------------------------------------------

    def _load_municipal_jargon(self) -> Dict[str, str]:
        """Municipal government jargon translation dictionary."""
        return {
            # Zoning terms
            'conditional use permit': 'special permission needed (requires an application and usually a public meeting)',
            'variance': 'exception to the normal rules (you must show hardship, and these are hard to get)',
            'non-conforming use': "something that was legal before the rules changed (usually allowed to continue)",
            'setback requirements': 'how far from your property lines you must build',
            'floor area ratio': 'limit on how big your building can be compared to your lot',
            'density restrictions': 'limits on how many homes you can have per acre',
            'height restrictions': 'maximum height allowed for buildings',
            'lot coverage': 'the percentage of your lot that buildings can cover',
            'accessory dwelling unit': 'a small second home on your property (ADU, guest house, granny flat)',
            'planned unit development': 'a custom development zone with more flexible rules',
            'overlay district': 'extra rules layered on top of the normal zoning for this area',

            # Building codes
            'certificate of occupancy': 'official sign-off before anyone can live in or use the building',
            'building permit': 'permission to build or renovate',
            'right of way': 'public land reserved for roads, sidewalks, or utilities',
            'easement': 'a legal right for someone else (a neighbor or utility) to use part of your land',
            'egress requirements': 'rules about exits and emergency escape routes',
            'fire separation': 'fire-resistant walls that slow fire spreading between spaces',
            'structural load': 'how much weight the floors, roof, and foundation can safely hold',
            'code compliance': 'meeting all the safety and legal requirements',

            # Administrative terms
            'public hearing': 'a public meeting where neighbors can speak for or against your proposal',
            'administrative review': 'city staff decide on their own (no public meeting)',
            'discretionary permit': 'approval is a judgment call by staff or the board',
            'ministerial permit': 'approval is automatic if you meet the checklist',
            'site plan review': 'a detailed staff review of your construction plans',
            'environmental review': 'a study of the environmental impact',
            'appeals process': 'how to challenge a decision you disagree with',
            'vested rights': "permission you already have that can't be taken away by a rule change",

            # Fees and timing
            'impact fees': 'charges to cover the strain your project puts on roads, sewers, and schools',
            'processing time': 'how long the review takes',
            'renewal requirements': 'what you have to do to keep the permit active',
            'expiration date': 'the date the permission runs out',
            'phased development': 'building in stages over time',

            # Business licensing
            'business license': 'permission to operate a business',
            'home occupation permit': 'permission to run a business out of your home',
            'commercial use': 'retail, office, or service business activity',
            'industrial use': 'manufacturing, processing, or heavy storage',
            'mixed use': 'a combination of homes and businesses',
        }

    def _load_legalese(self) -> Dict[str, str]:
        """
        Legalese phrases rewritten in plain English.

        Order does not matter here: matching is longest-phrase-first, so
        'shall not be permitted' wins over 'shall not', which wins over 'shall'.
        Getting this precedence right is what keeps prohibitions intact -- a
        naive 'shall' -> 'must' rewrite turns "no person shall construct" into
        "no person must construct", which means the opposite.
        """
        return {
            'no person shall': 'no one may',
            'it shall be unlawful to': 'it is illegal to',
            'shall not be permitted': 'is not allowed',
            'shall not be allowed': 'is not allowed',
            'shall not': 'must not',
            'shall be permitted': 'is allowed',
            'shall be allowed': 'is allowed',
            'shall be required': 'is required',
            'shall require': 'requires',
            'shall be subject to': 'must follow',
            'shall': 'must',
            'prior to': 'before',
            'pursuant to': 'under',
            'in accordance with': 'following',
            'notwithstanding': 'despite',
            'hereinafter': 'from here on',
            'herein': 'in this section',
            'thereof': 'of it',
            'said premises': 'that property',
        }

    def _load_code_patterns(self) -> Dict[str, Dict]:
        """Indicators used to classify what kind of municipal code the text is."""
        return {
            'zoning': {
                'indicators': [
                    'zoning district', 'land use', 'setback', 'lot area', 'lot coverage',
                    'accessory dwelling', 'floor area ratio', 'overlay', 'zone', 'zoning',
                    'district', 'dwelling unit',
                ],
            },
            'building': {
                'indicators': [
                    'building code', 'certificate of occupancy', 'egress', 'fire separation',
                    'structural', 'electrical', 'plumbing', 'construction', 'inspection',
                    'building', 'fire',
                ],
            },
            'permitting': {
                'indicators': [
                    'permit fee', 'application shall be submitted', 'site plan review',
                    'review period', 'submittal', 'application', 'permit', 'approval',
                ],
            },
            'business-licensing': {
                'indicators': [
                    'business license', 'home occupation', 'operating hours', 'signage',
                    'noise ordinance', 'licensing', 'license', 'commercial', 'business',
                ],
            },
            'housing': {
                'indicators': [
                    'habitability', 'rent control', 'tenant', 'landlord', 'rental unit',
                    'eviction', 'housing', 'rental',
                ],
            },
        }

    def _load_zoning_codes(self) -> Dict[str, str]:
        """Common zoning code designations and their meanings."""
        return {
            'R-1': 'single-family residential, low density',
            'R-2': 'two-family residential (duplex)',
            'R-3': 'multi-family residential (apartments, condos)',
            'R-4': 'high-density residential',
            'C-1': 'neighborhood commercial (small local shops)',
            'C-2': 'general commercial (shopping centers, offices)',
            'C-3': 'heavy commercial',
            'M-1': 'light industrial (warehouses, workshops)',
            'M-2': 'heavy industrial (factories)',
            'O-S': 'open space',
            'P-D': 'planned development',
            'PUD': 'planned unit development (custom mixed zoning)',
            'A-1': 'agricultural',
            'MU': 'mixed use (homes plus businesses)',
        }

    def _load_permit_keywords(self) -> List[str]:
        """Keywords that indicate a permit or approval is required."""
        return [
            'permit required',
            'permit is required',
            'permit shall be required',
            'permits are required',
            'approval is required',
            'approval shall be required',
            'license is required',
            'license required',
            'variance required',
            'shall obtain',
            'must obtain',
            'subject to approval',
            'approval of',
            'application required',
            'application shall be submitted',
            'conditional use',
            'certificate of occupancy',
            'reviewed by',
            'shall be reviewed',
        ]

    # ------------------------------------------------------------------
    # Regex setup
    # ------------------------------------------------------------------

    def _compile_regexes(self) -> None:
        """
        Pre-compile the extraction patterns and build the single-pass
        substitution table used by :meth:`translate_jargon`.
        """
        # One combined table so every phrase is rewritten in a single pass.
        # A single pass is what prevents cascading substitution, where a
        # replacement's own wording ("...a public hearing") gets expanded again
        # by a later rule.
        self._substitutions: Dict[str, str] = {}
        for term, plain in self.municipal_jargon.items():
            self._substitutions[term.lower()] = plain
        for phrase, plain in self.legalese.items():
            self._substitutions[phrase.lower()] = plain
        for code, meaning in self.zoning_codes.items():
            self._substitutions[code.lower()] = f'{code} ({meaning})'

        # Longest phrases first so multi-word rules win over their own prefixes.
        # The optional leading article is captured so "an accessory dwelling
        # unit" can become "a small second home ..." rather than "an a small
        # second home ..." -- swapping in a long phrase breaks a/an agreement.
        ordered = sorted(self._substitutions, key=len, reverse=True)
        self._substitution_re = re.compile(
            r'\b(?:(?P<article>[Aa]n|[Aa])\s+)?'
            r'(?P<term>' + '|'.join(re.escape(term) for term in ordered) + r')\b',
            re.IGNORECASE,
        )

        # Jargon-only matcher, used for confidence scoring.
        self._jargon_re = re.compile(
            r'\b(' + '|'.join(
                re.escape(t) for t in sorted(self.municipal_jargon, key=len, reverse=True)
            ) + r')\b',
            re.IGNORECASE,
        )

        self._permit_re = re.compile(
            r'\b(' + '|'.join(
                re.escape(k) for k in sorted(self.permit_keywords, key=len, reverse=True)
            ) + r')\b',
            re.IGNORECASE,
        )
        self._allowed_re = re.compile(
            r'\b(?:shall be permitted|is permitted|are permitted|permitted use|'
            r'permitted by right|as of right|shall be allowed|is allowed|are allowed|'
            r'may be used|may construct|may operate|may install|is authorized|'
            r'are authorized|authorized to)\b',
            re.IGNORECASE,
        )
        self._prohibited_re = re.compile(
            r'\b(?:shall not|may not|is prohibited|are prohibited|prohibited use|'
            r'is not permitted|are not permitted|is not allowed|are not allowed|'
            r'no person shall|it shall be unlawful|unlawful|forbidden)\b',
            re.IGNORECASE,
        )
        self._deadline_re = re.compile(
            r'(?:\b\d+\s*(?:-|to|through)?\s*\d*\s*(?:calendar\s+|business\s+|working\s+)?'
            r'(?:day|days|week|weeks|month|months|year|years)\b'
            r'|\bno later than\b|\bdeadline\b|\bexpires?\b|\bexpiration\b|\bdue date\b'
            r'|\btime limit\b|\bwithin\s+\d+\b)',
            re.IGNORECASE,
        )
        self._fee_re = re.compile(
            r'(?:\$\s?\d[\d,]*(?:\.\d{2})?'
            r'|\b(?:fee|fees|charge|surcharge|deposit|assessment|payable|non-refundable)\b)',
            re.IGNORECASE,
        )
        self._contact_sentence_re = re.compile(
            r'\b(?:department of|planning department|building department|planning division|'
            r'building division|city clerk|public works|code enforcement|contact|'
            r'inspector|permit center|office of)\b',
            re.IGNORECASE,
        )
        self._phone_re = re.compile(
            r'(?<!\d)(?:\+?1[\s.-])?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)'
        )
        self._email_re = re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.-]*[\w]\b')
        self._amount_re = re.compile(r'\$\s?\d[\d,]*(?:\.\d{2})?')

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------

    def split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentence-like units.

        Works on paragraphs first so that headings and section titles without
        terminal punctuation stay separate, then splits within each paragraph.
        """
        sentences: List[str] = []
        for paragraph in self._PARAGRAPH_SPLIT.split(text):
            for line_group in paragraph.split('\n'):
                for piece in self._SENTENCE_SPLIT.split(line_group):
                    cleaned = re.sub(r'\s+', ' ', piece).strip()
                    if cleaned:
                        sentences.append(cleaned)
        return sentences

    @staticmethod
    def _dedupe(items: List[str]) -> List[str]:
        """Drop duplicates (case-insensitively) while preserving order."""
        seen = set()
        unique = []
        for item in items:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

    # Words that stay lowercase inside a title-cased heading.
    _HEADING_CONNECTORS = {
        'a', 'an', 'and', 'at', 'by', 'for', 'in', 'of', 'on', 'or', 'the', 'to', 'with',
    }

    @classmethod
    def _looks_like_heading(cls, sentence: str) -> bool:
        """
        True for short title-cased or all-caps section headings.

        Headings such as "Compliance and Fees." trip the keyword extractors
        without stating a rule, so they are filtered out of the results. Real
        short rules ("Fences are prohibited.") keep their lowercase verbs and
        are not treated as headings.
        """
        words = sentence.rstrip('.:;').split()
        if not words or len(words) > 5:
            return False
        if any(char.isdigit() or char == '$' for char in sentence):
            return False
        return all(
            word[:1].isupper() or word.lower() in cls._HEADING_CONNECTORS
            for word in words if word[:1].isalpha()
        )

    def _match_sentences(self, text: str, pattern: re.Pattern) -> List[str]:
        """Return whole sentences matching a pattern, deduplicated and in order."""
        return self._dedupe([
            s for s in self.split_sentences(text)
            if pattern.search(s) and not self._looks_like_heading(s)
        ])

    # ------------------------------------------------------------------
    # Detection and translation
    # ------------------------------------------------------------------

    def detect_code_type(self, text: str) -> str:
        """
        Detect what type of municipal code the text represents.

        Multi-word indicators score higher than single words, so "building code"
        outweighs an incidental mention of "building".
        """
        text_lower = text.lower()
        scores: Dict[str, int] = {}
        for code_type, info in self.code_patterns.items():
            score = 0
            for indicator in info['indicators']:
                occurrences = len(re.findall(
                    r'\b' + re.escape(indicator) + r'\b', text_lower
                ))
                if occurrences:
                    weight = 3 if ' ' in indicator else 1
                    score += occurrences * weight
            scores[code_type] = score

        if not scores or max(scores.values()) == 0:
            return 'general'
        return max(scores, key=lambda key: scores[key])

    def translate_jargon(self, text: str, keep_original: bool = True) -> str:
        """
        Replace municipal jargon, legalese, and zoning codes with plain English.

        Runs as a single pass, so replacement text is never itself rewritten.
        When ``keep_original`` is true the original term is kept in brackets so
        readers can still match the translation back to the code they were sent.
        """
        if not text:
            return ''

        zoning_keys = {c.lower() for c in self.zoning_codes}

        def replace(match: re.Match) -> str:
            article = match.group('article')
            term = match.group('term')
            plain = self._substitutions[term.lower()]

            if term.lower() in zoning_keys:
                # Zoning codes already embed their own explanation.
                body = plain
            elif term.lower() in self.legalese:
                # Short legalese swaps read better without the bracketed original.
                body = plain
            elif keep_original:
                body = f'{plain} [{term}]'
            else:
                body = plain

            if article is None:
                return self._match_case(term, body)

            if term.lower() in zoning_keys:
                # A zoning code keeps its own article: "an R-1 district" is
                # correct because the letter is read aloud as a vowel sound,
                # which a first-letter test would get wrong.
                return f'{article} {body}'

            # The replacement may supply its own article ("a small second
            # home"); keeping the original one would double it up.
            if re.match(r'an?\s', body, re.IGNORECASE):
                rebuilt = body
            else:
                corrected = 'an' if body[:1].lower() in 'aeio' else 'a'
                rebuilt = f'{corrected} {body}'
            return self._match_case(article, rebuilt)

        return self._substitution_re.sub(replace, text)

    @staticmethod
    def _match_case(original: str, replacement: str) -> str:
        """Preserve leading capitalization when swapping a phrase."""
        if original[:1].isupper():
            return replacement[:1].upper() + replacement[1:]
        return replacement

    # ------------------------------------------------------------------
    # Extractors
    # ------------------------------------------------------------------

    def extract_permits(self, text: str) -> List[str]:
        """Extract sentences describing a permit or approval requirement."""
        return self._match_sentences(text, self._permit_re)

    def extract_fees(self, text: str) -> List[str]:
        """Extract sentences that mention fees or dollar amounts."""
        return self._match_sentences(text, self._fee_re)

    def extract_fee_amounts(self, text: str) -> List[str]:
        """Extract just the dollar amounts mentioned in the text."""
        return self._dedupe([m.strip() for m in self._amount_re.findall(text)])

    def extract_deadlines(self, text: str) -> List[str]:
        """Extract sentences describing deadlines and timeframes."""
        return self._match_sentences(text, self._deadline_re)

    def extract_allowed(self, text: str) -> List[str]:
        """
        Extract statements about what is permitted.

        Sentences that also carry a prohibition ("shall not be permitted") are
        left out, since they belong on the prohibited list instead.
        """
        allowed = self._match_sentences(text, self._allowed_re)
        return [s for s in allowed if not self._prohibited_re.search(s)]

    def extract_prohibited(self, text: str) -> List[str]:
        """Extract statements about what is prohibited or restricted."""
        return self._match_sentences(text, self._prohibited_re)

    def extract_contact_info(self, text: str) -> List[str]:
        """Extract phone numbers, email addresses, and department references."""
        contacts: List[str] = []
        contacts.extend(self._phone_re.findall(text))
        contacts.extend(self._email_re.findall(text))
        contacts.extend(self._match_sentences(text, self._contact_sentence_re))
        return self._dedupe(contacts)

    # ------------------------------------------------------------------
    # Scoring and guidance
    # ------------------------------------------------------------------

    def _generate_next_steps(
        self,
        permits: List[str],
        deadlines: List[str],
        fees: List[str],
        contacts: List[str],
    ) -> List[str]:
        """Turn the extracted findings into concrete next steps."""
        steps: List[str] = []
        if permits:
            steps.append(
                'Contact your local planning or building department for the '
                'application forms named in this code.'
            )
        if fees:
            steps.append(
                'Confirm the current fee amounts and accepted payment methods '
                'before you submit -- published fees go out of date.'
            )
        if deadlines:
            steps.append(
                'Put every review window and expiration date on a calendar.'
            )
        if contacts:
            steps.append(
                'Call the department listed above and ask them to confirm your '
                'reading of this section.'
            )
        if not steps:
            steps.append(
                'Read the full code section or ask city staff to confirm how '
                'it applies to your property.'
            )
        steps.append(
            'This is information, not legal advice -- verify anything you are '
            'relying on with your municipality.'
        )
        return steps

    def _compute_confidence(self, text: str, plain_english: str) -> float:
        """
        Score how much of the text this tool actually understood.

        Blends two signals: how much recognized jargon appeared, and how many
        sentences produced a usable extraction. Short or unrecognized text
        scores low, which is the honest answer.
        """
        if not text.strip():
            return 0.0

        sentences = self.split_sentences(text)
        if not sentences:
            return 0.0

        jargon_hits = len(self._jargon_re.findall(text))
        jargon_signal = min(jargon_hits / len(sentences), 1.0)

        extractors = (
            self._permit_re, self._fee_re, self._deadline_re,
            self._allowed_re, self._prohibited_re,
        )
        matched = sum(
            1 for s in sentences if any(p.search(s) for p in extractors)
        )
        coverage = matched / len(sentences)

        # Very short inputs give the extractors little to work with; damp the
        # score rather than reporting false certainty on a single sentence.
        length_factor = min(len(text.split()) / 40.0, 1.0)

        score = (0.20 + 0.45 * coverage + 0.35 * jargon_signal) * length_factor
        return round(min(score, 0.95), 2)

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------

    def translate_municipal_code(
        self, text: str, municipality: str = 'Unknown'
    ) -> MunicipalTranslationResult:
        """Translate a block of municipal code text into plain English."""
        if not text or not text.strip():
            return MunicipalTranslationResult(
                original_text=text or '',
                plain_english='No text provided.',
                municipality=municipality,
            )

        code_type = self.detect_code_type(text)
        permits = self.extract_permits(text)
        fees = self.extract_fees(text)
        deadlines = self.extract_deadlines(text)
        contacts = self.extract_contact_info(text)

        return MunicipalTranslationResult(
            original_text=text,
            plain_english=self.translate_jargon(text),
            what_you_can_do=self.extract_allowed(text),
            what_you_cannot_do=self.extract_prohibited(text),
            permits_required=permits,
            deadlines=deadlines,
            fees=fees,
            contact_info=contacts,
            next_steps=self._generate_next_steps(permits, deadlines, fees, contacts),
            confidence_score=self._compute_confidence(text, self.translate_jargon(text)),
            code_type=code_type,
            code_type_label=CODE_TYPE_LABELS.get(code_type, CODE_TYPE_LABELS['general']),
            municipality=municipality,
        )

    def translate(
        self, text: str, municipality: str = 'Unknown'
    ) -> MunicipalTranslationResult:
        """Alias for :meth:`translate_municipal_code`."""
        return self.translate_municipal_code(text, municipality=municipality)

    def fetch_and_translate_url(
        self,
        url: str,
        municipality: Optional[str] = None,
        selector: Optional[str] = None,
        max_chars: Optional[int] = None,
        timeout: int = 30,
    ) -> MunicipalTranslationResult:
        """
        Fetch a municipal code page and translate it.

        ``max_chars`` truncates very long pages; it defaults to no limit so the
        whole ordinance is read unless the caller asks otherwise.
        """
        if requests is None or BeautifulSoup is None:
            raise ImportError(
                'Fetching URLs requires "requests" and "beautifulsoup4". '
                'Install them with: pip install -r requirements.txt'
            )

        headers = {'User-Agent': 'MunicipalCodeTranslator (public legal access tool)'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        node = soup.select_one(selector) if selector else (
            soup.find('main') or soup.find('article') or soup.find('body') or soup
        )
        text = node.get_text(separator='\n', strip=True)
        if max_chars is not None:
            text = text[:max_chars]

        return self.translate_municipal_code(
            text, municipality=municipality or urlparse(url).netloc
        )


# ----------------------------------------------------------------------
# Report rendering and CLI
# ----------------------------------------------------------------------

def format_report(result: MunicipalTranslationResult) -> str:
    """Render a translation result as a readable plain-text report."""
    lines: List[str] = [
        '=' * 70,
        f'MUNICIPAL TRANSLATION REPORT: {result.municipality}',
        '=' * 70,
        f'Category   : {result.code_type_label} ({result.code_type})',
        f'Confidence : {result.confidence_score * 100:.0f}%',
        '',
        '--- PLAIN ENGLISH ---',
        result.plain_english,
    ]

    sections: List[Tuple[str, str, List[str]]] = [
        ('WHAT YOU CAN DO', 'v', result.what_you_can_do),
        ('WHAT YOU CANNOT DO', 'x', result.what_you_cannot_do),
        ('PERMITS REQUIRED', '!', result.permits_required),
        ('DEADLINES', '@', result.deadlines),
        ('FEES', '$', result.fees),
        ('CONTACTS', '#', result.contact_info),
        ('NEXT STEPS', '>', result.next_steps),
    ]
    for title, bullet, items in sections:
        lines.append('')
        lines.append(f'--- {title} ---')
        if items:
            lines.extend(f'  {bullet} {item}' for item in items)
        else:
            lines.append('  (none detected)')
    return '\n'.join(lines)


def _read_source(args: argparse.Namespace, translator: MunicipalCodeTranslator):
    """Resolve the CLI input source into a translation result."""
    if args.text:
        return translator.translate_municipal_code(
            args.text, municipality=args.municipality
        )

    if args.file:
        path = Path(args.file)
        if path.suffix.lower() == '.pdf':
            raise SystemExit(
                'Error: PDF input is not supported. Convert it to text first '
                '(for example: pdftotext ordinance.pdf ordinance.txt).'
            )
        if not path.exists():
            raise SystemExit(f'Error: file not found: {args.file}')
        text = path.read_text(encoding='utf-8', errors='replace')
        return translator.translate_municipal_code(
            text, municipality=args.municipality
        )

    return translator.fetch_and_translate_url(
        args.url,
        municipality=args.municipality if args.municipality != 'Unknown' else None,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description='Translate municipal codes into plain English'
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--file', type=str, help='Path to a municipal code text file')
    source.add_argument('--url', type=str, help='URL of a municipal code webpage')
    source.add_argument('--text', type=str, help='Municipal code text to translate directly')
    parser.add_argument(
        '--municipality', type=str, default='Unknown', help='Name of the municipality'
    )
    parser.add_argument(
        '--format', choices=['report', 'json'], default='report',
        help='Output format (default: report)',
    )
    parser.add_argument(
        '--output', type=str,
        help='Write results to this path without extension (creates .txt and .json)',
    )
    args = parser.parse_args(argv)

    translator = MunicipalCodeTranslator()
    result = _read_source(args, translator)

    if args.format == 'json':
        print(result.to_json())
    else:
        print(format_report(result))

    if args.output:
        base = Path(args.output)
        base.parent.mkdir(parents=True, exist_ok=True)
        base.with_suffix('.txt').write_text(format_report(result), encoding='utf-8')
        base.with_suffix('.json').write_text(result.to_json(), encoding='utf-8')
        print(f'\nSaved: {base.with_suffix(".txt")} and {base.with_suffix(".json")}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
