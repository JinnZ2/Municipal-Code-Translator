#!/usr/bin/env python3
"""
Regulatory Intelligence Engine - Municipal Code & Policy Intelligence Platform

Extends the plain-English translation in :mod:`municipal_translator` with deeper
regulatory analytics:

1. Root cause analysis (the systemic problem behind the regulation)
2. Citation graph of interconnected regulations (local, state, federal, standards)
3. Fee exploration engine, including formulaic and variable fees
4. Legislative intent and stated purpose extraction
5. Policy auditability and KPI metrics

The base parsing is not reimplemented here -- this module builds on
``MunicipalCodeTranslator`` so jargon, extraction, and scoring stay in one place.
"""

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from municipal_translator import (
    MunicipalCodeTranslator,
    MunicipalTranslationResult,
    format_report,
)

__all__ = [
    'ReferenceType',
    'RegulationReference',
    'FeeItem',
    'AuditMetric',
    'RegulatoryAnalysis',
    'RegulationRootCauseAnalyzer',
    'CitationGraphExtractor',
    'FeeExplorationEngine',
    'IntentAndPurposeExtractor',
    'PolicyAuditEngine',
    'RegulatoryIntelligenceEngine',
    'MunicipalCodeTranslator',
]


# =====================================================================
# DATA MODELS & SCHEMAS
# =====================================================================

class ReferenceType(Enum):
    MUNICIPAL = 'Municipal Code'
    STATE = 'State Statute'
    FEDERAL = 'Federal Act / Law'
    INDUSTRY_STANDARD = 'Building/Industry Standard'


@dataclass
class RegulationReference:
    """A cross-referenced legal citation found in the text."""

    citation: str
    ref_type: str
    relationship: str  # e.g. 'governed_by', 'statutory_mandate'
    context_clause: str


@dataclass
class FeeItem:
    """A flat or formulaic fee structure."""

    description: str
    base_amount: float
    is_formula: bool = False
    rate_unit: Optional[str] = None  # 'sqft', 'valuation', 'unit'
    formula_str: Optional[str] = None
    calculated_cost: float = 0.0
    # Formula fees need a project input to produce a real number. When the
    # caller does not supply one the cost is 0.0, which would otherwise look
    # like a free permit rather than an unanswered question.
    required_input: Optional[str] = None
    input_provided: bool = True


@dataclass
class AuditMetric:
    """A quantitative KPI or measurable standard for auditing a policy."""

    metric_description: str
    target_value: str
    metric_type: str  # 'timeline', 'threshold'
    verifiability_score: float  # 0.0-1.0, how measurable the rule is


@dataclass
class RegulatoryAnalysis(MunicipalTranslationResult):
    """A translation result plus the full regulatory intelligence signature."""

    stated_intent: str = 'Not explicitly stated'
    root_causes: List[str] = field(default_factory=list)
    interconnected_regulations: List[RegulationReference] = field(default_factory=list)
    fees_breakdown: List[FeeItem] = field(default_factory=list)
    total_estimated_fee: float = 0.0
    incomplete_fee_inputs: List[str] = field(default_factory=list)
    audit_metrics: List[AuditMetric] = field(default_factory=list)
    auditability_index: float = 0.0  # 0.0-1.0 measure of policy auditability


# =====================================================================
# SUB-ENGINES FOR ADVANCED ANALYTICS
# =====================================================================

class RegulationRootCauseAnalyzer:
    """Identifies the underlying systemic problems a regulation tries to fix."""

    def __init__(self) -> None:
        self.intent_taxonomy: Dict[str, List[str]] = {
            'Public Safety & Fire Prevention': [
                r'\bfire\b', r'\begress\b', r'\bemergency\b', r'\bhazard(?:ous)?\b',
                r'\blife safety\b', r'\bcombustible\b', r'\bsprinkler\b',
            ],
            'Affordable Housing & Density': [
                r'\baffordable\b', r'\blow[- ]income\b', r'\bdensity bonus\b',
                r'\binclusionary\b', r'\badus?\b', r'\baccessory dwelling\b',
                r'\bhousing supply\b',
            ],
            'Environmental Protection & Stormwater': [
                r'\bwetland\b', r'\bwater quality\b', r'\brunoff\b', r'\bstormwater\b',
                r'\bimpervious\b', r'\btree preservation\b', r'\bfloodplain\b',
            ],
            'Traffic Congestion & Parking Management': [
                r'\bparking spaces?\b', r'\btraffic\b', r'\btrip generation\b',
                r'\btransit\b', r'\bcurbside\b', r'\bdriveway\b',
            ],
            'Infrastructure Capacity & Impact Mitigation': [
                r'\bsewer\b', r'\bwater main\b', r'\bcapacity\b', r'\binfrastructure\b',
                r'\bgrid\b', r'\butilit(?:y|ies)\b', r'\bimpact fees?\b',
            ],
            'Nuisance Mitigation & Aesthetics': [
                r'\bnoise\b', r'\bodor\b', r'\bglare\b', r'\blight pollution\b',
                r'\bblight\b', r'\bneighborhood character\b', r'\bscreening\b',
            ],
        }
        self._compiled = {
            driver: [re.compile(p, re.IGNORECASE) for p in patterns]
            for driver, patterns in self.intent_taxonomy.items()
        }

    def analyze(self, text: str) -> List[str]:
        """Return the systemic drivers the text appears to address."""
        drivers = [
            driver for driver, patterns in self._compiled.items()
            if any(p.search(text) for p in patterns)
        ]
        return drivers or ['General Municipal Administration']


class CitationGraphExtractor:
    """Detects and categorizes local, state, federal, and standards citations."""

    def __init__(self) -> None:
        # A citation number must start with a digit. Without that anchor,
        # "this ordinance is to expand..." parses as a citation to an
        # ordinance named "is" -- the character class matches letters, and
        # IGNORECASE makes [A-Z] match lowercase too.
        self.re_local = re.compile(
            r'\b(?:Section|Sections|Sec\.|Chapter|Title|Article|Ordinance)\s+'
            r'(?:No\.?\s*)?(\d[\w.\-]*)',
            re.IGNORECASE,
        )
        self.re_state = re.compile(
            r'\b(?:State\s+(?:Vehicle|Health(?:\s+and\s+Safety)?|Building|Government|Housing)'
            r'\s+Code(?:\s+Section\s+[\d.]+)?'
            r'|(?:Government|Health and Safety|Public Resources)\s+Code\s+Section\s+[\d.]+'
            r'|State\s+Housing\s+Element\s+Law)\b',
            re.IGNORECASE,
        )
        self.re_federal = re.compile(
            r'\b(?:ADA|Americans with Disabilities Act|Clean Water Act|'
            r'Fair Housing Act|NEPA|\d+\s+C\.?F\.?R\.?(?:\s+\S+)?|U\.S\.C\.)\b',
            re.IGNORECASE,
        )
        self.re_standards = re.compile(
            r'\b(?:IBC|IRC|IECC|NEC|NFPA|ANSI|ASTM|ASHRAE|IEEE)\s*(?:\d[\d\-.]*)?',
            re.IGNORECASE,
        )

    @staticmethod
    def _context(text: str, start: int, end: int, window: int = 70) -> str:
        """Return the surrounding clause for a citation match."""
        left = max(0, start - window)
        right = min(len(text), end + window)
        return re.sub(r'\s+', ' ', text[left:right]).strip()

    def extract_references(self, text: str) -> List[RegulationReference]:
        """Extract every categorized citation, deduplicated by citation text."""
        specs: List[Tuple[re.Pattern, ReferenceType, str]] = [
            (self.re_local, ReferenceType.MUNICIPAL, 'governed_by'),
            (self.re_state, ReferenceType.STATE, 'statutory_mandate'),
            (self.re_federal, ReferenceType.FEDERAL, 'federal_compliance'),
            (self.re_standards, ReferenceType.INDUSTRY_STANDARD, 'technical_standard'),
        ]

        refs: List[RegulationReference] = []
        seen = set()
        for pattern, ref_type, relationship in specs:
            for match in pattern.finditer(text):
                citation = re.sub(r'\s+', ' ', match.group(0)).strip().rstrip('.,;')
                key = (ref_type.value, citation.lower())
                if key in seen:
                    continue
                seen.add(key)
                refs.append(RegulationReference(
                    citation=citation,
                    ref_type=ref_type.value,
                    relationship=relationship,
                    context_clause=self._context(text, match.start(), match.end()),
                ))
        return refs


class FeeExplorationEngine:
    """Parses flat fees, unit rates, and valuation percentages into cost estimates."""

    def __init__(self) -> None:
        # The three lookaheads force the whole number to be consumed before the
        # "not a rate" test runs. Without them the regex backtracks to a prefix:
        # "$0.75 per sq. ft." yields a phantom $0.00 flat fee, and "$1,200 per
        # unit" yields a phantom $1.00. They must still allow a sentence-ending
        # period ("a fee of $350.") to follow the amount.
        self.re_flat_fee = re.compile(
            r'\$\s?(\d[\d,]*(?:\.\d+)?)(?!\d)(?!,\d)(?!\.\d)(?!\s*(?:per\b|/|of\b))'
        )
        self.re_formula_sqft = re.compile(
            r'\$\s?(\d+(?:\.\d+)?)\s*(?:per|/)\s*(?:square\s*foot|square\s*feet|sq\.?\s*ft\.?|sqft)',
            re.IGNORECASE,
        )
        self.re_formula_unit = re.compile(
            r'\$\s?(\d[\d,]*(?:\.\d+)?)\s*(?:per|/)\s*(?:dwelling\s*)?unit',
            re.IGNORECASE,
        )
        self.re_formula_val = re.compile(
            r'(\d+(?:\.\d+)?)\s*(?:%|percent)\s*of\s*(?:the\s*)?(?:total\s*)?'
            r'(?:project\s*|construction\s*)?(?:valuation|value|cost)',
            re.IGNORECASE,
        )

    @staticmethod
    def _describe(text: str, position: int, default: str) -> str:
        """
        Name a fee from the words immediately before it.

        Picks the *nearest* preceding keyword rather than the first one in the
        list: in "a plan review fee of $0.75 per sq. ft. and an impact fee of
        0.5% of valuation", both keywords sit in the window, and only the
        closest one describes the fee actually being matched.
        """
        window_start = max(0, position - 90)
        context = text[window_start:position].lower()
        best_label = default
        best_index = -1
        for keyword, label in (
            ('plan review', 'Plan Review Fee'),
            ('plan check', 'Plan Check Fee'),
            ('inspection', 'Inspection Fee'),
            ('impact', 'Impact Fee'),
            ('application', 'Application Fee'),
            ('filing', 'Filing Fee'),
            ('permit', 'Permit Fee'),
            ('license', 'License Fee'),
            ('deposit', 'Deposit'),
        ):
            index = context.rfind(keyword)
            if index > best_index:
                best_index = index
                best_label = label
        return best_label

    def explore_fees(
        self, text: str, project_params: Optional[Dict[str, float]] = None
    ) -> Tuple[List[FeeItem], float, List[str]]:
        """
        Parse every fee in the text and estimate the total.

        Returns the itemized fees, the estimated total, and the names of any
        project inputs (``sqft``, ``valuation``, ``units``) that were needed but
        not supplied -- the total is an undercount whenever that list is non-empty.
        """
        params = project_params or {}
        items: List[FeeItem] = []
        missing: List[str] = []
        total = 0.0

        for match in self.re_flat_fee.finditer(text):
            amount = float(match.group(1).replace(',', ''))
            items.append(FeeItem(
                description=self._describe(text, match.start(), 'Fixed Fee'),
                base_amount=amount,
                is_formula=False,
                calculated_cost=amount,
            ))
            total += amount

        formula_specs = [
            (self.re_formula_sqft, 'sqft', 'sq.ft.', 'Area-Based Fee'),
            (self.re_formula_unit, 'units', 'unit', 'Per-Unit Fee'),
        ]
        for pattern, param_key, unit_label, default_desc in formula_specs:
            for match in pattern.finditer(text):
                rate = float(match.group(1).replace(',', ''))
                quantity = params.get(param_key)
                provided = quantity is not None
                quantity = quantity or 0.0
                cost = rate * quantity
                if not provided:
                    missing.append(param_key)
                items.append(FeeItem(
                    description=self._describe(
                        text, match.start(), f'{default_desc} (${rate}/{unit_label})'
                    ),
                    base_amount=rate,
                    is_formula=True,
                    rate_unit=param_key,
                    formula_str=f'${rate} x {quantity:g} {unit_label}',
                    calculated_cost=round(cost, 2),
                    required_input=param_key,
                    input_provided=provided,
                ))
                total += cost

        for match in self.re_formula_val.finditer(text):
            pct = float(match.group(1)) / 100.0
            valuation = params.get('valuation')
            provided = valuation is not None
            valuation = valuation or 0.0
            cost = pct * valuation
            if not provided:
                missing.append('valuation')
            items.append(FeeItem(
                description=self._describe(
                    text, match.start(), f'Valuation Assessment Fee ({pct * 100:g}%)'
                ),
                base_amount=pct,
                is_formula=True,
                rate_unit='valuation',
                formula_str=f'{pct * 100:g}% of ${valuation:,.2f}',
                calculated_cost=round(cost, 2),
                required_input='valuation',
                input_provided=provided,
            ))
            total += cost

        return items, round(total, 2), sorted(set(missing))


class IntentAndPurposeExtractor:
    """Extracts explicit legislative purpose clauses or infers stated goals."""

    def __init__(self) -> None:
        # {0,4} rather than {1,4}: a purpose statement that fits on one line,
        # followed by a blank line, is the common case and was being missed
        # because the pattern demanded at least one continuation line.
        self.re_purpose_block = re.compile(
            r'\b(?:purpose(?:\s+and\s+intent)?|intent|legislative findings|'
            r'declaration of policy)\b[:.\-\s]+(\S[^\n]*(?:\n[^\n]+){0,4})',
            re.IGNORECASE,
        )
        self.re_whereas = re.compile(r'WHEREAS,?\s*([^;\n]+)', re.IGNORECASE)

    def extract_intent(self, text: str) -> str:
        """Return the stated legislative intent, or a documented fallback."""
        match = self.re_purpose_block.search(text)
        if match:
            intent = re.sub(r'\s+', ' ', match.group(1)).strip()
            # Strip a leading "of this ordinance is to" style lead-in artifact.
            if intent:
                return intent

        whereas_matches = self.re_whereas.findall(text)
        if whereas_matches:
            joined = ' '.join(re.sub(r'\s+', ' ', w).strip() for w in whereas_matches[:2])
            return f'Inferred from preambles: {joined}'

        return 'Not explicitly stated (no purpose or findings clause detected).'


class PolicyAuditEngine:
    """Extracts quantitative, verifiable metrics for measuring policy outcomes."""

    def __init__(self) -> None:
        self.re_deadlines = re.compile(
            r'\b(?:within\s+)?\d+\s+(?:calendar\s+|business\s+|working\s+)?'
            r'(?:days?|weeks?|months?|years?)\b',
            re.IGNORECASE,
        )
        # Allow a few words between the qualifier and its number so
        # "maximum height restriction of 16 feet" is captured, not just
        # "maximum 16 feet". The {0,4} bound keeps the match local.
        self.re_quant_limits = re.compile(
            r'\b(?:maximum|minimum|not to exceed|at least|no more than|no less than|'
            r'no greater than|exceeding)\b(?:\s+\w+){0,4}?\s+'
            r'\d+(?:\.\d+)?\s*(?:feet|foot|ft\.?|sq\.?\s*ft\.?|square feet|units|'
            r'stories|percent|%|acres?)',
            re.IGNORECASE,
        )

    def audit_policy(self, text: str) -> Tuple[List[AuditMetric], float]:
        """Return measurable policy metrics and an overall auditability index."""
        metrics: List[AuditMetric] = []
        seen = set()

        def add(description: str, value: str, metric_type: str, score: float) -> None:
            normalized = re.sub(r'\s+', ' ', value).strip()
            key = (metric_type, normalized.lower())
            if key in seen:
                return
            seen.add(key)
            metrics.append(AuditMetric(
                metric_description=description,
                target_value=normalized,
                metric_type=metric_type,
                verifiability_score=score,
            ))

        for match in self.re_deadlines.finditer(text):
            add('Mandatory processing / review timeline window',
                match.group(0), 'timeline', 0.95)

        for match in self.re_quant_limits.finditer(text):
            add('Objective development / performance limit',
                match.group(0), 'threshold', 0.85)

        # Index the metrics against sentence count rather than raw word count,
        # so a long ordinance is not penalized purely for being long.
        sentences = [s for s in re.split(r'(?<=[.;!?])\s+', text) if s.strip()]
        if not sentences:
            return metrics, 0.0
        auditability_index = min(round(len(metrics) / len(sentences), 2), 1.0)
        return metrics, auditability_index


# =====================================================================
# ADVANCED PIPELINE ORCHESTRATOR
# =====================================================================

class RegulatoryIntelligenceEngine:
    """Runs the translator alongside the advanced analytics pipelines."""

    def __init__(self, translator: Optional[MunicipalCodeTranslator] = None) -> None:
        self.translator = translator or MunicipalCodeTranslator()
        self.root_cause_analyzer = RegulationRootCauseAnalyzer()
        self.citation_extractor = CitationGraphExtractor()
        self.fee_engine = FeeExplorationEngine()
        self.intent_extractor = IntentAndPurposeExtractor()
        self.audit_engine = PolicyAuditEngine()

    def analyze(
        self,
        text: str,
        municipality: str = 'Unknown',
        project_params: Optional[Dict[str, float]] = None,
    ) -> RegulatoryAnalysis:
        """Run the full regulatory intelligence pipeline over the text."""
        base = self.translator.translate_municipal_code(text, municipality=municipality)
        result = RegulatoryAnalysis(**asdict(base))

        result.stated_intent = self.intent_extractor.extract_intent(text)
        result.root_causes = self.root_cause_analyzer.analyze(text)
        result.interconnected_regulations = self.citation_extractor.extract_references(text)

        fees, total_fee, missing = self.fee_engine.explore_fees(text, project_params)
        result.fees_breakdown = fees
        result.total_estimated_fee = total_fee
        result.incomplete_fee_inputs = missing

        metrics, auditability = self.audit_engine.audit_policy(text)
        result.audit_metrics = metrics
        result.auditability_index = auditability

        return result


# =====================================================================
# REPORTING & CLI
# =====================================================================

def format_intelligence_report(
    report: RegulatoryAnalysis, project_params: Optional[Dict[str, float]] = None
) -> str:
    """Render a regulatory analysis as a readable plain-text report."""
    lines: List[str] = [
        '=' * 70,
        f'REGULATORY INTELLIGENCE REPORT: {report.municipality}',
        '=' * 70,
        '',
        'STATED INTENT:',
        f'  "{report.stated_intent}"',
        '',
        'ROOT CAUSE ANALYSIS (systemic drivers):',
    ]
    lines.extend(f'  - {cause}' for cause in report.root_causes)

    lines.append('')
    lines.append('FEE EXPLORATION & ESTIMATION:')
    if project_params:
        inputs = ', '.join(f'{k}={v:g}' for k, v in sorted(project_params.items()))
        lines.append(f'  Project input: {inputs}')
    if report.fees_breakdown:
        for fee in report.fees_breakdown:
            formula = f' ({fee.formula_str})' if fee.is_formula else ''
            flag = '' if fee.input_provided else '  <- needs project input'
            lines.append(
                f'  - {fee.description}: ${fee.calculated_cost:,.2f}{formula}{flag}'
            )
        lines.append(f'  => TOTAL ESTIMATED FEES: ${report.total_estimated_fee:,.2f}')
        if report.incomplete_fee_inputs:
            missing = ', '.join(report.incomplete_fee_inputs)
            lines.append(
                f'  !! Undercounted: supply {missing} to estimate the formula fees.'
            )
    else:
        lines.append('  (no fees detected)')

    lines.append('')
    lines.append('INTERCONNECTED CITATIONS & DEPENDENCIES:')
    if report.interconnected_regulations:
        lines.extend(
            f'  - [{ref.ref_type}] {ref.citation}'
            for ref in report.interconnected_regulations
        )
    else:
        lines.append('  (none detected)')

    lines.append('')
    lines.append('POLICY AUDITABILITY & KPI METRICS:')
    lines.append(f'  Auditability index: {report.auditability_index * 100:.0f}%')
    if report.audit_metrics:
        lines.extend(
            f'  - [{m.metric_type.upper()}] {m.metric_description} -> {m.target_value}'
            for m in report.audit_metrics
        )
    else:
        lines.append('  - (no measurable targets found -- this policy is hard to audit)')

    lines.append('')
    lines.append(format_report(report))
    return '\n'.join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description='Run deep regulatory analysis on municipal code text'
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--file', type=str, help='Path to a municipal code text file')
    source.add_argument('--text', type=str, help='Municipal code text to analyze directly')
    parser.add_argument(
        '--municipality', type=str, default='Unknown', help='Name of the municipality'
    )
    parser.add_argument('--sqft', type=float, help='Project size in square feet')
    parser.add_argument('--valuation', type=float, help='Project valuation in dollars')
    parser.add_argument('--units', type=float, help='Number of dwelling units')
    parser.add_argument(
        '--format', choices=['report', 'json'], default='report',
        help='Output format (default: report)',
    )
    args = parser.parse_args(argv)

    if args.file:
        path = Path(args.file)
        if not path.exists():
            raise SystemExit(f'Error: file not found: {args.file}')
        text = path.read_text(encoding='utf-8', errors='replace')
    else:
        text = args.text

    project_params = {
        key: value for key, value in (
            ('sqft', args.sqft), ('valuation', args.valuation), ('units', args.units)
        ) if value is not None
    }

    engine = RegulatoryIntelligenceEngine()
    report = engine.analyze(
        text, municipality=args.municipality, project_params=project_params or None
    )

    if args.format == 'json':
        print(json.dumps(asdict(report), indent=2))
    else:
        print(format_intelligence_report(report, project_params or None))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
