#!/usr/bin/env python3
"""
Regulatory Intelligence Engine - Municipal Code & Policy Intelligence Platform

Extends basic municipal code translation with deep regulatory analytics:
1. Root Cause Analysis (Systemic drivers behind the regulation)
2. Citation Graph & Interconnected Regulations (Local, State, Federal, Standards)
3. Formulaic Fee Exploration Engine (Variable cost calculations)
4. Legislative Intent & Stated Purpose Extraction
5. Policy Auditability & KPI Metric Engine
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum


# =====================================================================
# DATA MODELS & SCHEMAS
# =====================================================================

class ReferenceType(Enum):
    MUNICIPAL = "Municipal Code"
    STATE = "State Statute"
    FEDERAL = "Federal Act / Law"
    INDUSTRY_STANDARD = "Building/Industry Standard"


@dataclass
class RegulationReference:
    """Represents a cross-referenced legal citation."""
    citation: str
    ref_type: str
    relationship: str  # e.g., 'pursuant to', 'in accordance with', 'supersedes'
    context_clause: str


@dataclass
class FeeItem:
    """Represents a flat or formulaic fee structure."""
    description: str
    base_amount: float
    is_formula: bool = False
    rate_unit: Optional[str] = None  # e.g., 'sqft', 'valuation', 'unit'
    formula_str: Optional[str] = None
    calculated_cost: float = 0.0


@dataclass
class AuditMetric:
    """Represents a quantitative KPI or measurable standard for auditing policy success."""
    metric_description: str
    target_value: str
    metric_type: str  # 'timeline', 'threshold', 'fee', 'performance'
    verifiability_score: float  # 0.0 to 1.0 score of how measurable this rule is


@dataclass
class MunicipalTranslationResult:
    """The unified 360-degree regulatory intelligence signature."""
    original_text: str
    plain_english: str
    code_type: str = "Unknown"
    municipality: str = "Generic Jurisdiction"
    confidence_score: float = 0.0
    
    # Base Operational Rules
    what_you_can_do: List[str] = field(default_factory=list)
    what_you_cannot_do: List[str] = field(default_factory=list)
    permits_required: List[str] = field(default_factory=list)
    deadlines: List[str] = field(default_factory=list)
    contact_info: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    # Advanced Regulatory Intelligence
    stated_intent: str = "Not explicitly stated"
    root_causes: List[str] = field(default_factory=list)
    interconnected_regulations: List[RegulationReference] = field(default_factory=list)
    fees_breakdown: List[FeeItem] = field(default_factory=list)
    total_estimated_fee: float = 0.0
    audit_metrics: List[AuditMetric] = field(default_factory=list)
    auditability_index: float = 0.0  # 0.0 to 1.0 measure of policy auditability


# =====================================================================
# SUB-ENGINES FOR ADVANCED ANALYTICS
# =====================================================================

class RegulationRootCauseAnalyzer:
    """Identifies the underlying systemic problems a regulation attempts to fix."""

    def __init__(self):
        self.intent_taxonomy = {
            "Public Safety & Fire Prevention": [
                r'\bfire\b', r'\begress\b', r'\bemergency\b', r'\bhazard\b', r'\blife safety\b', r'\bcombustible\b'
            ],
            "Affordable Housing & Density": [
                r'\baffordable\b', r'\blow-income\b', r'\bdensity bonus\b', r'\binclusionary\b', r'\badu\b', r'\bhousing supply\b'
            ],
            "Environmental Protection & Stormwater": [
                r'\bwetland\b', r'\bwater quality\b', r'\brunoff\b', r'\bstormwater\b', r'\bimpervious\b', r'\btree preservation\b'
            ],
            "Traffic Congestion & Parking Management": [
                r'\bparking space\b', r'\btraffic\b', r'\btrip generation\b', r'\btransit\b', r'\bcurbside\b'
            ],
            "Infrastructure Capacity & Impact Mitigation": [
                r'\bsewer\b', r'\bwater main\b', r'\bcapacity\b', r'\binfrastructure\b', r'\bgrid\b', r'\butility\b'
            ],
            "Nuisance Mitigation & Aesthetics": [
                r'\bnoise\b', r'\bodor\b', r'\bglare\b', r'\blight pollution\b', r'\bblight\b', r'\bneighborhood character\b'
            ]
        }

    def analyze(self, text: str) -> List[str]:
        drivers = []
        text_lower = text.lower()
        for driver, patterns in self.intent_taxonomy.items():
            if any(re.search(p, text_lower) for p in patterns):
                drivers.append(driver)
        return drivers or ["General Municipal Administration"]


class CitationGraphExtractor:
    """Detects and categorizes intra-code, state, federal, and standard citations."""

    def __init__(self):
        self.re_local = re.compile(r'\b(?:Section|Chapter|Title|Article|Ordinance)\s+([0-9A-Z.\-]+)\b', re.I)
        self.re_state = re.compile(r'\b(?:State\s+(?:Vehicle|Health|Building|Government)\s+Code|Government Code Section\s+[0-9]+)\b', re.I)
        self.re_federal = re.compile(r'\b(?:ADA|Clean Water Act|Fair Housing Act|CFR|U\.S\.C\.|NEPA)\b', re.I)
        self.re_standards = re.compile(r'\b(?:IBC|IRC|NFPA|ANSI|ASTM|IEEE)\s*(?:[0-9\-]+)?\b', re.I)

    def extract_references(self, text: str) -> List[RegulationReference]:
        refs = []
        
        # Local Municipal Citations
        for match in self.re_local.finditer(text):
            refs.append(RegulationReference(
                citation=match.group(0),
                ref_type=ReferenceType.MUNICIPAL.value,
                relationship="governed_by",
                context_clause=match.group(0)
            ))

        # State Statute Citations
        for match in self.re_state.finditer(text):
            refs.append(RegulationReference(
                citation=match.group(0),
                ref_type=ReferenceType.STATE.value,
                relationship="statutory_mandate",
                context_clause=match.group(0)
            ))

        # Federal Citations
        for match in self.re_federal.finditer(text):
            refs.append(RegulationReference(
                citation=match.group(0),
                ref_type=ReferenceType.FEDERAL.value,
                relationship="federal_compliance",
                context_clause=match.group(0)
            ))

        # Industry Standards
        for match in self.re_standards.finditer(text):
            refs.append(RegulationReference(
                citation=match.group(0),
                ref_type=ReferenceType.INDUSTRY_STANDARD.value,
                relationship="technical_standard",
                context_clause=match.group(0)
            ))

        return refs


class FeeExplorationEngine:
    """Parses flat fees, unit-based rates, and valuation percentages to estimate project costs."""

    def __init__(self):
        self.re_flat_fee = re.compile(r'\$(\d+(?:\,\d{3})*(?:\.\d{2})?)\b(?!\s*per|\s*of)')
        self.re_formula_sqft = re.compile(r'\$(\d+(?:\.\d{2})?)\s*per\s*(?:square\s*foot|sq\.?\s*ft\.?|sqft)', re.I)
        self.re_formula_val = re.compile(r'(\d+(?:\.\d+)?)\%\s*of\s*(?:project\s*)?valuation', re.I)

    def explore_fees(self, text: str, project_params: Optional[Dict[str, float]] = None) -> Tuple[List[FeeItem], float]:
        params = project_params or {}
        items = []
        total = 0.0

        # 1. Parse Flat Fees
        for match in self.re_flat_fee.finditer(text):
            val = float(match.group(1).replace(',', ''))
            items.append(FeeItem(
                description="Fixed Application / Processing Fee",
                base_amount=val,
                is_formula=False,
                calculated_cost=val
            ))
            total += val

        # 2. Parse Square-Footage Formulas
        for match in self.re_formula_sqft.finditer(text):
            rate = float(match.group(1))
            sqft = params.get('sqft', 0.0)
            calc = rate * sqft
            items.append(FeeItem(
                description=f"Area-Based Fee (${rate}/sq.ft.)",
                base_amount=rate,
                is_formula=True,
                rate_unit="sqft",
                formula_str=f"${rate} * {sqft} sqft",
                calculated_cost=calc
            ))
            total += calc

        # 3. Parse Valuation Percentages
        for match in self.re_formula_val.finditer(text):
            pct = float(match.group(1)) / 100.0
            val = params.get('valuation', 0.0)
            calc = pct * val
            items.append(FeeItem(
                description=f"Valuation Assessment Fee ({pct*100}%)",
                base_amount=pct,
                is_formula=True,
                rate_unit="valuation",
                formula_str=f"{pct*100}% of ${val:,.2f}",
                calculated_cost=calc
            ))
            total += calc

        return items, round(total, 2)


class IntentAndPurposeExtractor:
    """Extracts explicit legislative purpose clauses or infers stated goals."""

    def __init__(self):
        self.re_purpose_block = re.compile(
            r'(?:purpose|intent|legislative findings|declaration of policy)[:.\s]+([^\n]+(?:\n[^\n]+){1,4})',
            re.I
        )
        self.re_whereas = re.compile(r'WHEREAS,\s*([^;\n]+)', re.I)

    def extract_intent(self, text: str) -> str:
        # Check for explicit Purpose section
        match = self.re_purpose_block.search(text)
        if match:
            return re.sub(r'\s+', ' ', match.group(1)).strip()

        # Check for Whereas preambles
        whereas_matches = self.re_whereas.findall(text)
        if whereas_matches:
            return "Inferred from preambles: " + " ".join(whereas_matches[:2])

        return "Standard regulatory compliance and public safety objective."


class PolicyAuditEngine:
    """Extracts quantitative, verifiable metrics to measure policy implementation and success."""

    def __init__(self):
        self.re_deadlines = re.compile(r'\b\d+\s+(?:days|months|years)\b', re.I)
        self.re_quant_limits = re.compile(r'\b(?:maximum|minimum|not to exceed|at least)\s+\d+(?:\.\d+)?\s*(?:feet|sq\.?\s*ft\.?|units|percent|%)?', re.I)

    def audit_policy(self, text: str) -> Tuple[List[AuditMetric], float]:
        metrics = []

        # Extract timeline KPIs
        for match in self.re_deadlines.finditer(text):
            metrics.append(AuditMetric(
                metric_description="Mandatory Processing / Review Timeline Window",
                target_value=match.group(0),
                metric_type="timeline",
                verifiability_score=0.95
            ))

        # Extract quantitative standard thresholds
        for match in self.re_quant_limits.finditer(text):
            metrics.append(AuditMetric(
                metric_description="Objective Development / Performance Limit",
                target_value=match.group(0),
                metric_type="threshold",
                verifiability_score=0.85
            ))

        # Calculate overall auditability index
        word_count = len(text.split())
        verifiable_elements = len(metrics)
        raw_index = (verifiable_elements * 40.0) / max(word_count, 1)
        auditability_index = min(round(raw_index, 2), 1.0)

        return metrics, auditability_index


# =====================================================================
# CORE PARSER (REFACTORED TRANSLATOR BASE)
# =====================================================================

class MunicipalCodeTranslator:
    """Core parser for translating legal municipal text into structured plain English."""

    def __init__(self):
        self.jargon = {
            'conditional use permit': 'special permission required (requires public hearing)',
            'variance': 'hardship exception to standard zoning limits',
            'accessory dwelling unit': 'secondary residential home (ADU / backyard cottage)',
            'setback requirements': 'minimum required distance from property boundary lines',
            'floor area ratio': 'maximum building size ratio relative to total lot size',
        }

    def parse_base(self, text: str, municipality: str) -> MunicipalTranslationResult:
        result = MunicipalTranslationResult(
            original_text=text,
            plain_english=self._simplify(text),
            municipality=municipality,
            code_type="Municipal Ordinance"
        )

        # Basic operational rule extractions
        result.what_you_can_do = self._extract_clause(r'([^.;\n]*?\b(?:permitted|allowed|authorized)\b[^.;\n]*)', text)
        result.what_you_cannot_do = self._extract_clause(r'([^.;\n]*?\b(?:shall not|prohibited|unlawful)\b[^.;\n]*)', text)
        result.permits_required = self._extract_clause(r'([^.;\n]*?\b(?:permit|approval|variance)\b[^.;\n]*)', text)
        
        return result

    def _simplify(self, text: str) -> str:
        plain = text
        for j, translation in self.jargon.items():
            plain = re.sub(rf'\b{j}\b', f"**[{translation.upper()}]**", plain, flags=re.I)
        plain = re.sub(r'\bshall\b', 'must', plain, flags=re.I)
        return plain

    def _extract_clause(self, pattern: str, text: str) -> List[str]:
        matches = re.findall(pattern, text, re.I)
        return [m.strip() for m in matches[:3] if len(m.strip()) > 10]


# =====================================================================
# ADVANCED PIPELINE ORCHESTRATOR
# =====================================================================

class RegulatoryIntelligenceEngine:
    """Orchestrates the translation engine alongside advanced analytics pipelines."""

    def __init__(self):
        self.translator = MunicipalCodeTranslator()
        self.root_cause_analyzer = RegulationRootCauseAnalyzer()
        self.citation_extractor = CitationGraphExtractor()
        self.fee_engine = FeeExplorationEngine()
        self.intent_extractor = IntentAndPurposeExtractor()
        self.audit_engine = PolicyAuditEngine()

    def analyze(
        self,
        text: str,
        municipality: str = "Generic Jurisdiction",
        project_params: Optional[Dict[str, float]] = None
    ) -> MunicipalTranslationResult:
        """Runs full 360-degree regulatory intelligence pipeline on input text."""
        # Step 1: Run Base Translation Parsing
        result = self.translator.parse_base(text, municipality)

        # Step 2: Extract Intent & Root Cause Analysis
        result.stated_intent = self.intent_extractor.extract_intent(text)
        result.root_causes = self.root_cause_analyzer.analyze(text)

        # Step 3: Map Interconnected Citation Graph
        result.interconnected_regulations = self.citation_extractor.extract_references(text)

        # Step 4: Explore Formulaic & Variable Fees
        fees, total_fee = self.fee_engine.explore_fees(text, project_params)
        result.fees_breakdown = fees
        result.total_estimated_fee = total_fee

        # Step 5: Audit Policy KPIs & Verifiability
        metrics, auditability = self.audit_engine.audit_policy(text)
        result.audit_metrics = metrics
        result.auditability_index = auditability

        return result


# =====================================================================
# DEMONSTRATION & VERIFICATION
# =====================================================================

if __name__ == "__main__":
    engine = RegulatoryIntelligenceEngine()

    complex_ordinance = (
        "ORDINANCE NO. 2026-42 - ACCESSORY DWELLING UNIT (ADU) REGULATION\n"
        "PURPOSE AND INTENT: The intent of this ordinance is to expand affordable housing supply "
        "and mitigate residential density shortages in accordance with State Housing Element Law.\n\n"
        "Section 1. Authorization.\n"
        "An Accessory Dwelling Unit (ADU) is permitted on any single-family residential lot. "
        "No person shall construct an ADU exceeding a maximum height restriction of 16 feet.\n\n"
        "Section 2. Compliance and Fees.\n"
        "Pursuant to Chapter 17.04 of the Municipal Code and in alignment with IBC 2024 standards, "
        "a building permit shall be required prior to construction. The applicant shall pay a "
        "fixed application fee of $350, plus a plan review fee of $0.75 per sq. ft. and 0.5% of project valuation. "
        "The Planning Department shall render a decision within 60 days of submittal."
    )

    # Property Owner Inputs (800 sq ft ADU, $150,000 project valuation)
    user_project_input = {
        'sqft': 800.0,
        'valuation': 150000.0
    }

    report = engine.analyze(
        text=complex_ordinance,
        municipality="City of Austin",
        project_params=user_project_input
    )

    print("======================================================================")
    print(f"REGULATORY INTELLIGENCE REPORT: {report.municipality.upper()}")
    print("======================================================================\n")

    print(f"📜 STATED INTENT:\n  \"{report.stated_intent}\"\n")

    print("🎯 ROOT CAUSE ANALYSIS (Systemic Drivers):")
    for cause in report.root_causes:
        print(f"  • {cause}")

    print("\n💰 FEE EXPLORATION & ESTIMATION ENGINE:")
    print(f"  Project Input: {user_project_input['sqft']} sqft, ${user_project_input['valuation']:,.2f} valuation")
    for fee in report.fees_breakdown:
        formula_info = f" ({fee.formula_str})" if fee.is_formula else ""
        print(f"  - {fee.description}: ${fee.calculated_cost:,.2f}{formula_info}")
    print(f"  ➜ TOTAL ESTIMATED PERMIT & PLAN FEES: ${report.total_estimated_fee:,.2f}\n")

    print("🔗 INTERCONNECTED CITATIONS & DEPENDENCIES:")
    for ref in report.interconnected_regulations:
        print(f"  • [{ref.ref_type}] {ref.citation}")

    print("\n📊 POLICY AUDITABILITY & KPI METRICS:")
    print(f"  Policy Auditability Index: {report.auditability_index * 100:.0f}% (High verifiability)")
    for metric in report.audit_metrics:
        print(f"  • [{metric.metric_type.upper()}] {metric.metric_description} -> Target: {metric.target_value}")

    print("\n✅ PLAIN ENGLISH OPERATIONAL SUMMARY:")
    print(f"  {report.plain_english[:250]}...")
