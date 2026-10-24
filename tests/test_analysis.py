import hashlib
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from analysis import (
    broader_experience_title, build_summary, canonicalize_skill, categorize_skill,
    compute_category_occurrence_composition, compute_category_posting_prevalence,
    compute_role_counts, compute_sample_audit, compute_skill_frequency,
    load_and_clean_data, normalization_audit, normalize_skills, parse_skill_list,
    validate_dataset_columns,
)
from scraper import extract_detail_links, posting_identity, validate_output
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


class ParsingTests(unittest.TestCase):
    def test_aliases(self):
        for raw, expected in {'React.js': 'React', 'GitHub': 'Git', 'Tensorflow': 'TensorFlow',
                              'C / C++': 'C++', 'Golang': 'Go'}.items():
            with self.subTest(raw=raw):
                self.assertEqual(canonicalize_skill(raw), expected)

    def test_unknown_retained(self):
        self.assertEqual(normalize_skills(['  New Skill  ', 'Linux', 'C#']), ['New Skill', 'Linux', 'C#'])
        self.assertEqual(categorize_skill('New Skill'), 'Other')

    def test_deterministic_deduplication(self):
        self.assertEqual(normalize_skills(['GitHub', 'React.js', 'Git', 'React', 'Golang', 'Go']), ['Git', 'React', 'Go'])

    def test_invalid_fields_have_context(self):
        for value in ["[broken", "{}", "'Python'", "['Python', 1]", "[None]", "[' ']", None, float('nan')]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'row 7'):
                parse_skill_list(value, 7)

    def test_missing_columns(self):
        with self.assertRaisesRegex(ValueError, 'Missing required columns'):
            validate_dataset_columns(pd.DataFrame({'skills': []}))

    def test_csv_failure_has_index_and_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'invalid.csv'
            pd.DataFrame([dict(job_role='role', company='co', title='title', skills='bad')]).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "row 0: 'bad'"):
                load_and_clean_data(path)

    def test_empty_list(self):
        self.assertEqual(parse_skill_list('[]'), [])

    def test_title_heuristic(self):
        for title in ['Backend Engineer (4년 이하)', 'Software Engineer (~6년)', '신입~1년차', '0~5년']:
            self.assertTrue(broader_experience_title(title))
        for title in ['신입', '경력 무관', '2025 개발자', '0년']:
            self.assertFalse(broader_experience_title(title))


class HistoricalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / 'wanted_jobs.csv'
        cls.df = load_and_clean_data(cls.path)

    def test_frozen_hash(self):
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), '1fc9dd4a73dffd3c6cd2e3b7a0aa76c50f0ab67798243d7552b537c6ac95a5f1')

    def test_role_counts(self):
        self.assertEqual(len(self.df), 119)
        self.assertEqual(compute_role_counts(self.df), {'서버 개발자': 44, '프론트엔드 개발자': 46, '데이터 사이언티스트': 29})

    def test_proxy_audit(self):
        audit = compute_sample_audit(self.df)
        self.assertEqual(audit['unique_company_title_proxy_count'], 112)
        self.assertEqual(audit['cross_role_duplicate_proxy_count'], 7)
        self.assertEqual(audit['broader_experience_title_row_count'], 9)
        self.assertEqual(audit['rows_removed'], 0)
        self.assertFalse(audit['sample_scope']['strict_entry_level_verified'])

    def test_historical_top_values(self):
        frequency = compute_skill_frequency(self.df)
        expected = {'서버 개발자': {'Java': 36.4, 'AWS': 36.4},
                    '프론트엔드 개발자': {'React': 71.7, 'TypeScript': 47.8},
                    '데이터 사이언티스트': {'Python': 65.5, 'PyTorch': 44.8, 'TensorFlow': 31.0}}
        for role, skills in expected.items():
            actual = {r['skill']: round(r['percentage'], 1) for r in frequency[role]}
            for skill, percentage in skills.items():
                self.assertEqual(actual[skill], percentage)

    def test_composition_totals(self):
        for categories in compute_category_occurrence_composition(self.df).values():
            self.assertAlmostEqual(sum(categories.values()), 100)

    def test_prevalence_bounds(self):
        for categories in compute_category_posting_prevalence(self.df).values():
            self.assertTrue(all(0 <= value <= 100 for value in categories.values()))

    def test_no_valid_tag_lost(self):
        for row in self.df.itertuples():
            self.assertEqual(set(row.skills), {canonicalize_skill(s) for s in row.skills_raw})
        audit = normalization_audit(self.df)
        self.assertEqual(audit.raw_occurrence_count.sum(), 503)
        self.assertTrue((audit.mapping_type == 'retained_unmapped').any())
        summary = build_summary(self.df, self.path)
        self.assertEqual(summary['raw_skill_mentions'], 503)
        self.assertEqual(summary['silent_dropped_valid_skill_mentions'], 0)

    def test_taxonomy(self):
        self.assertEqual(categorize_skill('Git'), 'Development Tool')
        self.assertEqual(categorize_skill('Linux'), 'Cloud/Infra')
        self.assertEqual(categorize_skill('C#'), 'Language')


class MetricTests(unittest.TestCase):
    def test_denominators_and_empty_postings(self):
        df = pd.DataFrame({'job_role': ['role'] * 3, 'skills': [['AWS', 'Docker', 'Git'], ['Git'], []]})
        composition = compute_category_occurrence_composition(df)['role']
        prevalence = compute_category_posting_prevalence(df)['role']
        self.assertEqual(composition['Cloud/Infra'], 50)
        self.assertAlmostEqual(prevalence['Cloud/Infra'], 100 / 3)
        self.assertAlmostEqual(prevalence['Development Tool'], 200 / 3)

    def test_all_empty_skills(self):
        df = pd.DataFrame({'job_role': ['role'], 'skills': [[]]})
        self.assertEqual(sum(compute_category_occurrence_composition(df)['role'].values()), 0)
        self.assertEqual(sum(compute_category_posting_prevalence(df)['role'].values()), 0)

    def test_proxy_key_is_tuple_not_concatenation(self):
        df = pd.DataFrame({'job_role': ['role', 'role'], 'company': ['ab', 'a'], 'title': ['c', 'bc'], 'skills': [[], []]})
        self.assertEqual(compute_sample_audit(df)['unique_company_title_proxy_count'], 2)


class ScraperTests(unittest.TestCase):
    def test_historical_output_blocked(self):
        for path in [ROOT / 'wanted_jobs.csv', Path('wanted_jobs.csv')]:
            with self.assertRaises(ValueError):
                validate_output(path)

    def test_existing_output_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fresh.csv'
            path.touch()
            with self.assertRaises(FileExistsError):
                validate_output(path)

    def test_posting_identity(self):
        self.assertEqual(posting_identity('/wd/123?foo=bar'), ('https://www.wanted.co.kr/wd/123', '123'))
        self.assertIsNone(posting_identity('/unknown')[1])
        with self.assertRaises(ValueError):
            posting_identity('https://example.com/wd/123')

    def test_deduplication_per_query(self):
        soup = BeautifulSoup('''<div data-cy="job-card"><a href="/wd/123"></a></div>
                               <div data-cy="job-card"><a href="/wd/123?foo=bar"></a></div>''', 'html.parser')
        self.assertEqual(extract_detail_links(soup), ['https://www.wanted.co.kr/wd/123'])


if __name__ == '__main__':
    unittest.main()
