"""Tests for the regulatory intelligence analytics layer."""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from regulatory_intelligence_engine import (  # noqa: E402
    CitationGraphExtractor,
    FeeExplorationEngine,
    IntentAndPurposeExtractor,
    PolicyAuditEngine,
    RegulationRootCauseAnalyzer,
    RegulatoryAnalysis,
    RegulatoryIntelligenceEngine,
    format_intelligence_report,
    main,
)

SAMPLE_PATH = Path(__file__).resolve().parent.parent / 'examples' / 'sample_ordinance.txt'
SAMPLE = SAMPLE_PATH.read_text(encoding='utf-8')


class TestFeeExploration(unittest.TestCase):
    def setUp(self):
        self.engine = FeeExplorationEngine()

    def test_no_phantom_zero_fee_from_a_rate(self):
        """'$0.75 per sq. ft.' is a rate, not a $0 flat fee."""
        items, _, _ = self.engine.explore_fees('A fee of $0.75 per sq. ft. applies.')
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0].is_formula)
        self.assertNotIn(0.0, [i.base_amount for i in items])

    def test_flat_fee_parsed(self):
        items, total, _ = self.engine.explore_fees('Pay an application fee of $350.')
        self.assertEqual(total, 350.0)
        self.assertEqual(items[0].description, 'Application Fee')

    def test_sqft_formula_uses_project_input(self):
        items, total, missing = self.engine.explore_fees(
            'A plan review fee of $0.75 per sq. ft. applies.', {'sqft': 800.0}
        )
        self.assertEqual(total, 600.0)
        self.assertEqual(missing, [])
        self.assertTrue(items[0].input_provided)

    def test_valuation_percentage(self):
        _, total, _ = self.engine.explore_fees(
            'An impact fee of 0.5% of project valuation applies.',
            {'valuation': 150000.0},
        )
        self.assertEqual(total, 750.0)

    def test_per_unit_fee(self):
        _, total, _ = self.engine.explore_fees(
            'An impact fee of $1,200 per dwelling unit applies.', {'units': 3.0}
        )
        self.assertEqual(total, 3600.0)

    def test_missing_input_is_reported(self):
        items, total, missing = self.engine.explore_fees(
            'A plan review fee of $0.75 per sq. ft. applies.'
        )
        self.assertEqual(missing, ['sqft'])
        self.assertEqual(total, 0.0)
        self.assertFalse(items[0].input_provided)

    def test_full_sample_totals_correctly(self):
        _, total, missing = self.engine.explore_fees(
            SAMPLE, {'sqft': 800.0, 'valuation': 150000.0}
        )
        # $350 flat + ($0.75 x 800) + (0.5% x $150,000)
        self.assertEqual(total, 350.0 + 600.0 + 750.0)
        self.assertEqual(missing, [])

    def test_comma_separated_amount(self):
        _, total, _ = self.engine.explore_fees('The deposit is $1,250.00.')
        self.assertEqual(total, 1250.0)


class TestCitationGraph(unittest.TestCase):
    def setUp(self):
        self.extractor = CitationGraphExtractor()

    def test_prose_is_not_read_as_a_citation(self):
        """'this ordinance is to expand...' is prose, not a citation."""
        refs = self.extractor.extract_references(
            'The intent of this ordinance is to expand housing supply.'
        )
        self.assertEqual(refs, [])

    def test_ordinance_number_is_captured(self):
        refs = self.extractor.extract_references('ORDINANCE NO. 2026-42 - ADU REGULATION')
        self.assertEqual(len(refs), 1)
        self.assertIn('2026-42', refs[0].citation)

    def test_chapter_citation(self):
        refs = self.extractor.extract_references('Pursuant to Chapter 17.04 of the Code.')
        self.assertTrue(any('17.04' in r.citation for r in refs))

    def test_standards_citation(self):
        refs = self.extractor.extract_references('In accordance with IBC 2024 standards.')
        self.assertTrue(any(r.ref_type == 'Building/Industry Standard' for r in refs))

    def test_state_citation(self):
        refs = self.extractor.extract_references('As required by State Housing Element Law.')
        self.assertTrue(any(r.ref_type == 'State Statute' for r in refs))

    def test_federal_citation(self):
        refs = self.extractor.extract_references('Facilities must comply with the ADA.')
        self.assertTrue(any(r.ref_type == 'Federal Act / Law' for r in refs))

    def test_duplicates_are_collapsed(self):
        refs = self.extractor.extract_references('See Chapter 17.04. Also see Chapter 17.04.')
        self.assertEqual(len([r for r in refs if '17.04' in r.citation]), 1)

    def test_context_clause_is_populated(self):
        refs = self.extractor.extract_references('Pursuant to Chapter 17.04 of the Code.')
        self.assertIn('Chapter 17.04', refs[0].context_clause)


class TestIntentExtraction(unittest.TestCase):
    def setUp(self):
        self.extractor = IntentAndPurposeExtractor()

    def test_single_line_purpose_block_is_found(self):
        """A one-line purpose statement followed by a blank line still counts."""
        text = 'PURPOSE AND INTENT: To expand affordable housing supply.\n\nSection 1.'
        self.assertIn('affordable housing', self.extractor.extract_intent(text))

    def test_intent_found_in_full_sample(self):
        intent = self.extractor.extract_intent(SAMPLE)
        self.assertIn('affordable housing', intent.lower())

    def test_whereas_preamble_fallback(self):
        text = 'WHEREAS, the city faces a shortage of rental housing; and'
        self.assertIn('Inferred from preambles', self.extractor.extract_intent(text))

    def test_missing_intent_is_stated_plainly(self):
        intent = self.extractor.extract_intent('Fences may not exceed six feet.')
        self.assertIn('Not explicitly stated', intent)


class TestPolicyAudit(unittest.TestCase):
    def setUp(self):
        self.engine = PolicyAuditEngine()

    def test_timeline_metric(self):
        metrics, _ = self.engine.audit_policy('A decision is issued within 60 days.')
        self.assertEqual(metrics[0].metric_type, 'timeline')

    def test_threshold_with_words_between_qualifier_and_number(self):
        """'maximum height restriction of 16 feet' is a measurable threshold."""
        metrics, _ = self.engine.audit_policy(
            'No ADU may exceed a maximum height restriction of 16 feet.'
        )
        self.assertTrue(any(m.metric_type == 'threshold' for m in metrics))

    def test_metrics_are_deduplicated(self):
        metrics, _ = self.engine.audit_policy('Within 60 days. Again within 60 days.')
        self.assertEqual(len([m for m in metrics if m.metric_type == 'timeline']), 1)

    def test_index_is_bounded(self):
        _, index = self.engine.audit_policy(SAMPLE)
        self.assertGreaterEqual(index, 0.0)
        self.assertLessEqual(index, 1.0)

    def test_unmeasurable_policy_scores_zero(self):
        metrics, index = self.engine.audit_policy(
            'The board shall act in a reasonable and neighborly manner.'
        )
        self.assertEqual(metrics, [])
        self.assertEqual(index, 0.0)

    def test_empty_text(self):
        self.assertEqual(self.engine.audit_policy(''), ([], 0.0))


class TestRootCauseAnalysis(unittest.TestCase):
    def setUp(self):
        self.analyzer = RegulationRootCauseAnalyzer()

    def test_housing_driver(self):
        causes = self.analyzer.analyze('This expands affordable housing supply via ADUs.')
        self.assertIn('Affordable Housing & Density', causes)

    def test_fire_safety_driver(self):
        causes = self.analyzer.analyze('Egress and fire separation requirements apply.')
        self.assertIn('Public Safety & Fire Prevention', causes)

    def test_fallback_driver(self):
        self.assertEqual(
            self.analyzer.analyze('The clerk keeps the records.'),
            ['General Municipal Administration'],
        )


class TestEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = RegulatoryIntelligenceEngine()

    def test_analysis_includes_base_translation_fields(self):
        report = self.engine.analyze(SAMPLE, municipality='Austin')
        self.assertIsInstance(report, RegulatoryAnalysis)
        self.assertTrue(report.plain_english)
        self.assertTrue(report.permits_required)
        # Base fields the previous engine left permanently empty:
        self.assertTrue(report.deadlines)
        self.assertTrue(report.contact_info)
        self.assertTrue(report.next_steps)

    def test_code_type_is_detected_not_hardcoded(self):
        report = self.engine.analyze(SAMPLE)
        self.assertNotEqual(report.code_type, 'general')

    def test_full_pipeline_populates_analytics(self):
        report = self.engine.analyze(
            SAMPLE, municipality='Austin',
            project_params={'sqft': 800.0, 'valuation': 150000.0},
        )
        self.assertIn('affordable housing', report.stated_intent.lower())
        self.assertTrue(report.root_causes)
        self.assertTrue(report.interconnected_regulations)
        self.assertEqual(report.total_estimated_fee, 1700.0)
        self.assertTrue(report.audit_metrics)

    def test_empty_text_does_not_crash(self):
        report = self.engine.analyze('')
        self.assertEqual(report.total_estimated_fee, 0.0)
        self.assertEqual(report.auditability_index, 0.0)

    def test_report_renders(self):
        report = self.engine.analyze(SAMPLE, municipality='Austin')
        text = format_intelligence_report(report)
        self.assertIn('REGULATORY INTELLIGENCE REPORT', text)
        self.assertIn('ROOT CAUSE ANALYSIS', text)

    def test_report_flags_missing_fee_inputs(self):
        report = self.engine.analyze(SAMPLE, municipality='Austin')
        self.assertTrue(report.incomplete_fee_inputs)
        self.assertIn('Undercounted', format_intelligence_report(report))


class TestCli(unittest.TestCase):
    def setUp(self):
        """Keep CLI output out of the test log."""
        self._silence = redirect_stdout(io.StringIO())
        self._silence.__enter__()
        self.addCleanup(self._silence.__exit__, None, None, None)

    def test_file_input_json(self):
        self.assertEqual(
            main(['--file', str(SAMPLE_PATH), '--sqft', '800', '--format', 'json']), 0
        )

    def test_text_input_report(self):
        self.assertEqual(main(['--text', SAMPLE, '--municipality', 'Austin']), 0)

    def test_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            main(['--file', 'does-not-exist.txt'])


if __name__ == '__main__':
    unittest.main()
