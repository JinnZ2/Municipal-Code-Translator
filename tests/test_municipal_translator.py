"""Tests for the plain-English municipal code translator."""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from municipal_translator import (  # noqa: E402
    MunicipalCodeTranslator,
    MunicipalTranslationResult,
    format_report,
    main,
)

SAMPLE = (
    'An accessory dwelling unit shall be permitted on any lot in an R-1 district. '
    'No person shall construct an accessory dwelling unit exceeding 16 feet. '
    'A conditional use permit shall be required prior to construction. '
    'The applicant shall pay an application fee of $350. '
    'The Planning Department shall render a decision within 60 days of submittal. '
    'Contact the Planning Department at (555) 123-4567 or permits@example.gov.'
)


class TestJargonTranslation(unittest.TestCase):
    def setUp(self):
        self.translator = MunicipalCodeTranslator()

    def test_prohibition_is_not_inverted(self):
        """'No person shall construct' must not become 'no person must construct'."""
        plain = self.translator.translate_jargon('No person shall construct a fence.')
        self.assertNotIn('must construct', plain.lower())
        self.assertIn('no one may construct', plain.lower())

    def test_shall_not_keeps_its_negation(self):
        plain = self.translator.translate_jargon('Signs shall not exceed 20 feet.')
        self.assertIn('must not exceed', plain.lower())

    def test_shall_be_permitted_reads_as_permission(self):
        plain = self.translator.translate_jargon('An ADU shall be permitted on any lot.')
        self.assertIn('is allowed', plain.lower())
        self.assertNotIn('must be permitted', plain.lower())

    def test_bare_shall_becomes_must(self):
        plain = self.translator.translate_jargon('The applicant shall pay the fee.')
        self.assertIn('must pay', plain.lower())

    def test_no_cascading_substitution(self):
        """
        'conditional use permit' expands to text mentioning a public meeting;
        that replacement text must not be expanded a second time.
        """
        plain = self.translator.translate_jargon('A conditional use permit is needed.')
        self.assertEqual(plain.lower().count('special permission needed'), 1)
        self.assertNotIn('[public hearing]', plain.lower())

    def test_original_term_is_preserved_for_reference(self):
        plain = self.translator.translate_jargon('A variance is needed.')
        self.assertIn('[variance]', plain)

    def test_keep_original_can_be_disabled(self):
        plain = self.translator.translate_jargon('A variance is needed.', keep_original=False)
        self.assertNotIn('[variance]', plain)

    def test_zoning_code_is_annotated_not_replaced(self):
        plain = self.translator.translate_jargon('Located in the R-1 district.')
        self.assertIn('R-1 (single-family residential, low density)', plain)

    def test_article_agrees_with_the_replacement(self):
        """'an accessory dwelling unit' must not become 'an a small second home'."""
        plain = self.translator.translate_jargon('An accessory dwelling unit is allowed.')
        self.assertNotIn('an a small', plain.lower())
        self.assertTrue(plain.startswith('A small second home'))

    def test_article_is_corrected_for_vowel_sounds(self):
        plain = self.translator.translate_jargon('A variance is needed.')
        self.assertTrue(plain.lower().startswith('an exception'))

    def test_zoning_code_keeps_its_original_article(self):
        plain = self.translator.translate_jargon('Located in an R-1 district.')
        self.assertIn('an R-1 (', plain)

    def test_longest_phrase_wins(self):
        plain = self.translator.translate_jargon('Such use shall not be permitted here.')
        self.assertIn('is not allowed', plain.lower())

    def test_empty_text(self):
        self.assertEqual(self.translator.translate_jargon(''), '')


class TestSentenceSplitting(unittest.TestCase):
    def setUp(self):
        self.translator = MunicipalCodeTranslator()

    def test_decimals_are_not_split(self):
        sentences = self.translator.split_sentences('A fee of $0.75 applies.')
        self.assertEqual(len(sentences), 1)

    def test_section_numbers_are_not_split(self):
        sentences = self.translator.split_sentences('See Section 17.04.120 for details.')
        self.assertEqual(len(sentences), 1)

    def test_sentences_are_separated(self):
        sentences = self.translator.split_sentences('First rule here. Second rule here.')
        self.assertEqual(len(sentences), 2)

    def test_blank_input_yields_nothing(self):
        self.assertEqual(self.translator.split_sentences('   \n  '), [])


class TestExtractors(unittest.TestCase):
    def setUp(self):
        self.translator = MunicipalCodeTranslator()

    def test_permits_are_found(self):
        permits = self.translator.extract_permits(SAMPLE)
        self.assertTrue(any('conditional use permit' in p.lower() for p in permits))

    def test_fees_are_found(self):
        self.assertTrue(any('$350' in f for f in self.translator.extract_fees(SAMPLE)))

    def test_fee_amounts_are_extracted(self):
        self.assertEqual(self.translator.extract_fee_amounts(SAMPLE), ['$350'])

    def test_deadlines_are_found(self):
        deadlines = self.translator.extract_deadlines(SAMPLE)
        self.assertTrue(any('60 days' in d for d in deadlines))

    def test_allowed_excludes_prohibitions(self):
        text = 'Sheds shall be permitted. Fences shall not be permitted.'
        allowed = self.translator.extract_allowed(text)
        self.assertEqual(len(allowed), 1)
        self.assertIn('Sheds', allowed[0])

    def test_prohibited_is_found(self):
        prohibited = self.translator.extract_prohibited(SAMPLE)
        self.assertTrue(any('No person shall' in p for p in prohibited))

    def test_contact_info_finds_phone_and_email(self):
        contacts = self.translator.extract_contact_info(SAMPLE)
        self.assertIn('(555) 123-4567', contacts)
        self.assertIn('permits@example.gov', contacts)

    def test_extractors_return_whole_sentences(self):
        for permit in self.translator.extract_permits(SAMPLE):
            self.assertGreater(len(permit.split()), 3)

    def test_results_are_deduplicated(self):
        text = 'A permit is required. A permit is required.'
        self.assertEqual(len(self.translator.extract_permits(text)), 1)


class TestCodeTypeDetection(unittest.TestCase):
    def setUp(self):
        self.translator = MunicipalCodeTranslator()

    def test_zoning_detected(self):
        text = (
            'The zoning district establishes setback and lot coverage standards '
            'for each dwelling unit in the land use table.'
        )
        self.assertEqual(self.translator.detect_code_type(text), 'zoning')

    def test_building_detected(self):
        text = (
            'The building code requires a certificate of occupancy and egress '
            'inspection before occupancy.'
        )
        self.assertEqual(self.translator.detect_code_type(text), 'building')

    def test_housing_detected(self):
        text = (
            'The landlord must maintain habitability of every rental unit and '
            'may not begin an eviction without notice to the tenant.'
        )
        self.assertEqual(self.translator.detect_code_type(text), 'housing')

    def test_unrelated_text_is_general(self):
        self.assertEqual(self.translator.detect_code_type('The sky is blue today.'), 'general')

    def test_multiword_indicator_outweighs_incidental_word(self):
        text = 'A business license is required for every business license holder.'
        self.assertEqual(self.translator.detect_code_type(text), 'business-licensing')


class TestConfidence(unittest.TestCase):
    def setUp(self):
        self.translator = MunicipalCodeTranslator()

    def test_empty_text_scores_zero(self):
        self.assertEqual(self.translator._compute_confidence('', ''), 0.0)

    def test_score_is_within_bounds(self):
        score = self.translator._compute_confidence(SAMPLE, SAMPLE)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 0.95)

    def test_dense_code_scores_higher_than_unrelated_prose(self):
        prose = (
            'The weather was pleasant that afternoon and the park was busy with '
            'families walking along the river path enjoying the long summer light.'
        )
        self.assertGreater(
            self.translator._compute_confidence(SAMPLE, SAMPLE),
            self.translator._compute_confidence(prose, prose),
        )

    def test_short_input_does_not_report_high_certainty(self):
        score = self.translator._compute_confidence('A permit is required.', '')
        self.assertLess(score, 0.5)


class TestTranslateMunicipalCode(unittest.TestCase):
    def setUp(self):
        self.translator = MunicipalCodeTranslator()

    def test_returns_populated_result(self):
        result = self.translator.translate_municipal_code(SAMPLE, municipality='Testville')
        self.assertIsInstance(result, MunicipalTranslationResult)
        self.assertEqual(result.municipality, 'Testville')
        self.assertTrue(result.permits_required)
        self.assertTrue(result.fees)
        self.assertTrue(result.deadlines)
        self.assertTrue(result.next_steps)

    def test_next_steps_always_include_a_disclaimer(self):
        result = self.translator.translate_municipal_code(SAMPLE)
        self.assertTrue(any('not legal advice' in s for s in result.next_steps))

    def test_empty_input_is_handled(self):
        result = self.translator.translate_municipal_code('   ')
        self.assertEqual(result.plain_english, 'No text provided.')
        self.assertEqual(result.confidence_score, 0.0)

    def test_translate_alias_matches(self):
        self.assertEqual(
            self.translator.translate(SAMPLE).plain_english,
            self.translator.translate_municipal_code(SAMPLE).plain_english,
        )

    def test_result_is_json_serializable(self):
        result = self.translator.translate_municipal_code(SAMPLE)
        self.assertIn('plain_english', result.to_json())

    def test_code_type_label_is_set(self):
        result = self.translator.translate_municipal_code(SAMPLE)
        self.assertTrue(result.code_type_label)

    def test_report_renders(self):
        report = format_report(self.translator.translate_municipal_code(SAMPLE))
        self.assertIn('MUNICIPAL TRANSLATION REPORT', report)
        self.assertIn('NEXT STEPS', report)


class TestCli(unittest.TestCase):
    def setUp(self):
        """Keep CLI output out of the test log."""
        self._silence = redirect_stdout(io.StringIO())
        self._silence.__enter__()
        self.addCleanup(self._silence.__exit__, None, None, None)

    def test_text_input_json(self):
        self.assertEqual(main(['--text', SAMPLE, '--format', 'json']), 0)

    def test_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            main(['--file', 'does-not-exist.txt'])

    def test_pdf_input_is_rejected_clearly(self):
        with self.assertRaises(SystemExit) as ctx:
            main(['--file', 'ordinance.pdf'])
        self.assertIn('PDF', str(ctx.exception))

    def test_sample_file_translates(self):
        sample = Path(__file__).resolve().parent.parent / 'examples' / 'sample_ordinance.txt'
        self.assertEqual(main(['--file', str(sample), '--municipality', 'Oakridge']), 0)


if __name__ == '__main__':
    unittest.main()
