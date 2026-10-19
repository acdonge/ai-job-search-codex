"""Every recorded lead stays visible, with fit and eligibility kept separate."""
import copy
import importlib.util
from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('career_report', ROOT / 'tools/career_report.py')
REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT)


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.text = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)

    def leads(self):
        return [attrs for tag, attrs in self.tags if tag == 'tr' and 'data-lead-id' in attrs]

    def by_id(self, identity):
        return next(attrs for _, attrs in self.tags if attrs.get('id') == identity)


def assessment(disposition='eligible'):
    scored = disposition in ('eligible', 'provisional')
    return {
        'disposition': disposition,
        'reason': 'Evidence from the current official posting.',
        'evidence': [{'url': 'https://example.edu/jobs/1', 'note': 'Current employer posting',
                      'checked_on': '2026-10-19'}],
        'gates': {
            'availability': {'verdict': 'PASS', 'reason': 'Currently open.'},
            'eligibility': {'verdict': 'VERIFY' if disposition == 'provisional' else 'PASS',
                            'reason': 'Sponsorship requires employer confirmation.'},
            'constraints': {'verdict': 'PASS', 'reason': 'Location is within the requested scope.'},
        },
        'dimensions': {'technical': {'value': 80, 'reason': 'Relevant robotics experience.'},
                       'behavioral': {'value': None, 'reason': 'Working environment is unknown.'}},
        'score': {'lower': 68.0, 'upper': 83.0, 'coverage': 85.0,
                  'overall': None, 'band': 'Potential', 'weights': {'technical': 30, 'behavioral': 15}}
                 if scored else None,
    }


def payload(size=18):
    dispositions = ['eligible', 'provisional', 'excluded', 'closed', 'unreachable',
                    'duplicate', 'out_of_scope', 'pending', None]
    rows = []
    for number in range(size):
        disposition = dispositions[number % len(dispositions)]
        rows.append({'id': f'lead-{number:03}', 'title': f'Robotics role {number}',
                     'organization': f'Employer {number}',
                     'url': f'https://example.edu/jobs/{number}', 'cycle': '2027',
                     'assessment': assessment(disposition) if disposition else None})
    scored = sum(bool(row['assessment'] and row['assessment']['score']) for row in rows)
    pending = sum(row['assessment'] is None or row['assessment']['disposition'] == 'pending' for row in rows)
    return {'run_id': 'run-test-001', 'track': 'industry', 'query': 'Robotics research',
            'scope': {'request': 'All supplied robotics roles', 'mode': 'provided',
                      'source_urls': ['https://example.edu/jobs'],
                      'expected_urls': [row['url'] for row in rows], 'exclusions': []},
            'stop': {'reason': 'provided_complete', 'note': 'Every supplied posting was recorded.'},
            'complete': False, 'errors': ['Some leads still require assessment.'],
            'counts': {'observations': size + (3 if rows else 0), 'discovered': size,
                       'assessed': sum(row['assessment'] is not None for row in rows),
                       'scored': scored, 'unscored': size - scored, 'pending': pending,
                       'displayed': size},
            'rows': rows,
            'batches': [{'source_url': 'https://example.edu/jobs', 'query': 'Robotics research',
                         'checked_on': '2026-10-19', 'access': 'ok',
                         'note': 'Read every supplied posting.', 'results': rows + rows[:1] * 3}]}


class CareerReportTests(unittest.TestCase):
    def test_all_eighteen_rows_render_exactly_once_in_source_order(self):
        data = payload()
        document = Document(REPORT.render_report(data))
        self.assertEqual([row['data-lead-id'] for row in document.leads()],
                         [row['id'] for row in data['rows']])

    def test_every_disposition_and_pending_missing_assessment_stays_visible(self):
        document = Document(REPORT.render_report(payload()))
        statuses = [row['data-disposition'] for row in document.leads()]
        self.assertEqual(statuses.count('pending'), 4)
        self.assertEqual(set(statuses), {'eligible', 'provisional', 'excluded', 'closed',
                         'unreachable', 'duplicate', 'out_of_scope', 'pending'})
        for row in document.leads():
            self.assertNotIn('hidden', row)
            self.assertNotIn('display:none', row.get('style', '').replace(' ', ''))

    def test_default_filter_is_all_and_live_count_shows_all_rows(self):
        document = Document(REPORT.render_report(payload()))
        self.assertTrue(any(tag == 'option' and attrs.get('value') == 'all' and 'selected' in attrs
                            for tag, attrs in document.tags))
        self.assertIn('18 of 18', ''.join(document.text))
        self.assertEqual(document.by_id('visible-count')['aria-live'], 'polite')
        self.assertEqual(document.by_id('reset-filters')['type'], 'button')

    def test_controls_have_accessible_labels_and_no_script_required_to_read_results(self):
        document = Document(REPORT.render_report(payload()))
        labelled = {attrs.get('for') for tag, attrs in document.tags if tag == 'label'}
        self.assertIn('text-filter', labelled)
        self.assertIn('disposition-filter', labelled)
        self.assertEqual(len(document.leads()), 18)
        self.assertIn('All results remain visible without JavaScript.', ''.join(document.text))

    def test_fit_range_coverage_and_eligibility_are_distinct(self):
        document = Document(REPORT.render_report(payload()))
        text = ''.join(document.text)
        self.assertIn('68.0–83.0', text)
        self.assertIn('85% known', text)
        self.assertIn('Eligibility', text)
        self.assertIn('VERIFY', text)
        self.assertIn('Sponsorship requires employer confirmation.', text)
        self.assertIn('Fit does not establish application eligibility.', text)

    def test_full_and_zero_scores_are_not_confused_with_missing_scores(self):
        data = payload(1)
        data['rows'][0]['assessment']['score'].update(overall=0.0, lower=0.0, upper=0.0, coverage=100.0)
        html = REPORT.render_report(data)
        self.assertIn('0.0 / 100', html)
        self.assertIn('100% known', html)

    def test_unscored_and_unassessed_are_explicit_and_do_not_get_fake_scores(self):
        data = payload(9)
        document = Document(REPORT.render_report(data))
        text = ''.join(document.text)
        self.assertIn('Not evaluated', text)
        self.assertIn('Not scored', text)
        self.assertIn('Working environment is unknown.', text)
        self.assertNotIn('50.0 / 100', text)

    def test_incomplete_banner_and_supplied_errors_are_visible(self):
        document = Document(REPORT.render_report(payload()))
        text = ''.join(document.text)
        self.assertIn('INCOMPLETE', text)
        self.assertIn('Some leads still require assessment.', text)
        self.assertEqual(document.by_id('run-status')['role'], 'status')

    def test_count_mismatch_makes_claimed_complete_run_visibly_incomplete(self):
        data = payload(1)
        data['complete'] = True
        data['errors'] = []
        data['counts']['displayed'] = 0
        text = ''.join(Document(REPORT.render_report(data)).text)
        self.assertIn('INCOMPLETE', text)
        self.assertIn('displayed count', text)
        self.assertEqual(len(Document(REPORT.render_report(data)).leads()), 1)

    def test_pending_assessment_blocks_complete_label_even_with_consistent_counts(self):
        data = payload(9)
        data['complete'] = True
        data['errors'] = []
        text = ''.join(Document(REPORT.render_report(data)).text)
        self.assertIn('INCOMPLETE', text)
        self.assertIn('pending assessment', text)

    def test_missing_fit_score_cannot_render_as_complete(self):
        data = payload(1)
        data.update(complete=True, errors=[])
        data['rows'][0]['assessment']['score'] = None
        data['counts'].update(scored=0, unscored=1)
        text = ''.join(Document(REPORT.render_report(data)).text)
        self.assertIn('INCOMPLETE', text)
        self.assertIn('missing a fit score', text)

    def test_missing_stopping_evidence_cannot_render_as_complete(self):
        data = payload(1)
        data.update(complete=True, errors=[], stop=None)
        text = ''.join(Document(REPORT.render_report(data)).text)
        self.assertIn('INCOMPLETE', text)
        self.assertIn('stopping evidence', text)

    def test_observation_count_reconciles_with_recorded_batches(self):
        data = payload(1)
        data.update(complete=True, errors=[])
        data['counts']['observations'] = 12
        text = ''.join(Document(REPORT.render_report(data)).text)
        self.assertIn('INCOMPLETE', text)
        self.assertIn('batch observations', text)

    def test_complete_banner_is_explicitly_scoped_to_recorded_run(self):
        data = payload(1)
        data['complete'] = True
        data['errors'] = []
        text = ''.join(Document(REPORT.render_report(data)).text)
        self.assertIn('RECORDED RUN COMPLETE', text)
        self.assertNotIn('INCOMPLETE', text)
        self.assertIn('not exhaustive market coverage', text)

    def test_safe_source_links_dates_and_search_provenance_are_present(self):
        document = Document(REPORT.render_report(payload(1)))
        hrefs = [attrs.get('href') for tag, attrs in document.tags if tag == 'a']
        self.assertIn('https://example.edu/jobs/0', hrefs)
        self.assertIn('https://example.edu/jobs/1', hrefs)
        self.assertIn('https://example.edu/jobs', hrefs)
        text = ''.join(document.text)
        for expected in ('2026-10-19', 'provided_complete', 'Every supplied posting was recorded.',
                         'Read every supplied posting.', 'All supplied robotics roles', 'run-test-001'):
            self.assertIn(expected, text)

    def test_duplicate_and_scope_exclusion_reasons_are_not_lost(self):
        data = payload(1)
        item = data['rows'][0]['assessment']
        item.update(disposition='duplicate', duplicate_of='lead-original', scope_exclusion='Outside New York')
        text = ''.join(Document(REPORT.render_report(data)).text)
        self.assertIn('lead-original', text)
        self.assertIn('Outside New York', text)

    def test_shared_url_scope_displays_both_provided_identities(self):
        data = payload(2)
        data['scope'].pop('expected_urls')
        data['scope']['expected_leads'] = [
            {'title': title, 'organization': 'Example University',
             'url': 'https://example.edu/admissions'} for title in ('MS', 'PhD')]
        html = REPORT.render_report(data)
        self.assertIn('<dt>Provided identities</dt><dd>2</dd>', html)

    def test_every_untrusted_field_is_escaped_without_creating_elements(self):
        data = payload(1)
        hostile = '<img src=x onerror="alert(1)"></script><script>alert(2)</script>&'
        data.update(run_id=hostile, query=hostile, errors=[hostile])
        data['scope']['request'] = hostile
        data['stop']['note'] = hostile
        data['batches'][0]['note'] = hostile
        row = data['rows'][0]
        row.update(id=hostile, title=hostile, organization=hostile, cycle=hostile)
        row['assessment']['reason'] = hostile
        row['assessment']['evidence'][0]['note'] = hostile
        row['assessment']['gates']['eligibility']['reason'] = hostile
        row['assessment']['dimensions']['technical']['reason'] = hostile
        html = REPORT.render_report(data)
        document = Document(html)
        self.assertFalse(any(tag == 'img' for tag, _ in document.tags))
        self.assertEqual(sum(tag == 'script' for tag, _ in document.tags), 1)
        self.assertFalse(any(any(name.startswith('on') for name in attrs) for _, attrs in document.tags))
        self.assertEqual(document.leads()[0]['data-lead-id'], hostile)
        self.assertIn('&lt;img', html)

    def test_unsafe_urls_are_inert_in_all_link_locations(self):
        for unsafe in ['javascript:alert(1)', 'data:text/html,<script>bad</script>',
                       '//example.com/path', 'https://user:secret@example.com',
                       'https://example.com/\nmalicious', 'https://example.com\\evil']:
            with self.subTest(unsafe=unsafe):
                data = payload(1)
                data['rows'][0]['url'] = unsafe
                data['rows'][0]['assessment']['evidence'][0]['url'] = unsafe
                data['batches'][0]['source_url'] = unsafe
                data['scope']['source_urls'] = [unsafe]
                document = Document(REPORT.render_report(data))
                self.assertFalse(any(tag == 'a' and attrs.get('href') == unsafe for tag, attrs in document.tags))

    def test_no_external_assets_or_embedded_untrusted_json(self):
        document = Document(REPORT.render_report(payload()))
        self.assertFalse(any(tag in ('script', 'img', 'iframe', 'link') and
                             ('src' in attrs or 'href' in attrs) for tag, attrs in document.tags))
        self.assertTrue(any(tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy'
                            for tag, attrs in document.tags))

    def test_input_is_unchanged_and_output_is_deterministic(self):
        data = payload()
        before = copy.deepcopy(data)
        first = REPORT.render_report(data)
        self.assertEqual(data, before)
        self.assertEqual(first, REPORT.render_report(data))

    def test_empty_run_renders_zero_rows_without_losing_provenance(self):
        data = payload(0)
        document = Document(REPORT.render_report(data))
        self.assertEqual(document.leads(), [])
        self.assertIn('0 of 0', ''.join(document.text))
        self.assertIn('No leads recorded.', ''.join(document.text))


if __name__ == '__main__':
    unittest.main()
