"""End-to-end completion contracts: no silently lost or unevaluated discoveries."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools/career_pipeline.py'


class SearchPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.workspace = self.base / 'workspace'
        self.workspace.mkdir()
        self.write('workspace/profile.json', {'schema_version': 1, 'active_track': 'industry',
                   'profiles': {t: {} for t in ('industry', 'graduate', 'academia')}})
        self.track = 'industry'
        self.leads = [{'title': f'Engineer {i}', 'organization': 'Example Robotics',
                       'url': f'https://example.org/jobs/{i}'} for i in range(14)]
        self.scope = {'request': 'Review all supplied example opportunities.', 'mode': 'provided',
                      'source_urls': ['https://example.org/careers'], 'exclusions': [],
                      'expected_urls': [r['url'] for r in self.leads]}

    def write(self, name, value):
        p = self.base / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value), encoding='utf-8')
        return str(p)

    def cli(self, *args, ok=True):
        p = subprocess.run([sys.executable, str(SCRIPT), '--workspace', str(self.workspace), *args],
                           text=True, capture_output=True, encoding='utf-8')
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
            return json.loads(p.stdout)
        self.assertNotEqual(p.returncode, 0, p.stdout)
        return p

    def start(self):
        args = ['start', '--track', self.track, '--query', 'robotics',
                '--scope', self.write('scope.json', self.scope)]
        if self.track == 'academia':
            args += ['--academic-role', 'postdoc']
        self.run = self.cli(*args)['run_id']
        return self.run

    def call(self, command, *args, **kw):
        return self.cli(command, '--track', self.track, '--run', self.run, *args, **kw)

    def batch(self, results=None, query='robotics', source='https://example.org/careers', access='ok'):
        data = {'source_url': source, 'query': query, 'checked_on': '2026-10-19',
                'results': self.leads if results is None else results, 'access': access,
                'note': 'Fixture results; no actual opportunity claim.'}
        return self.call('batch', '--file', self.write('batch.json', data))

    def assessments(self, rows):
        weights = self.cli('rubric', '--track', self.track,
                           *(['--academic-role', 'postdoc'] if self.track == 'academia' else []))['weights']
        return [{'id': r['id'], 'disposition': 'provisional', 'reason': 'Fit assessed; authorization unknown.',
                 'evidence': [{'url': r['url'], 'note': 'Fixture posting requires robotics.', 'checked_on': '2026-10-19'}],
                 'gates': {k: {'verdict': 'VERIFY' if k == 'eligibility' else 'PASS',
                                'reason': 'Unconfirmed authorization.' if k == 'eligibility' else 'Supported by supplied facts.'}
                           for k in ('availability', 'eligibility', 'constraints')},
                 'dimensions': {k: {'value': None if k == 'behavioral' else 80,
                                    'reason': 'Work environment unknown.' if k == 'behavioral' else 'Relevant candidate and posting evidence.'}
                                for k in weights}} for r in rows]

    def assess(self, values):
        return self.call('assess', '--file', self.write('assessments.json', {'assessments': values}))

    def stop(self, reason='provided_complete'):
        return self.call('stop', '--reason', reason, '--note', 'Declared scope processed.')

    def ready(self):
        self.start()
        rows = self.batch()['rows']
        self.assess(self.assessments(rows))
        self.stop()

    def test_missing_scores_cannot_complete_or_masquerade_as_finished_report(self):
        self.start(); self.batch(); self.stop()
        self.call('complete', ok=False)
        result = self.call('report')
        self.assertFalse(result['complete'])
        html = Path(result['report_html']).read_text(encoding='utf-8')
        self.assertIn('INCOMPLETE', html)
        self.assertEqual(html.count('data-lead-id='), 14)
        self.call('check', ok=False)

    def test_all_rows_partial_scores_and_provisional_gates_survive_complete(self):
        self.ready()
        result = self.call('complete')
        self.assertTrue(result['complete'])
        self.assertEqual(result['counts']['displayed'], 14)
        self.assertEqual(result['counts']['scored'], 14)
        first = result['rows'][0]['assessment']
        self.assertEqual(first['score']['coverage'], 85)
        self.assertEqual(first['score']['lower'], 68)
        self.assertEqual(first['score']['upper'], 83)
        self.assertIsNone(first['score']['overall'])
        self.assertEqual(first['gates']['eligibility']['verdict'], 'VERIFY')
        html = Path(result['report_html']).read_text(encoding='utf-8')
        self.assertEqual(html.count('data-lead-id='), 14)
        self.assertTrue(self.call('check')['complete'])
        store = json.loads((self.workspace / self.track / 'opportunities.json').read_text(encoding='utf-8'))
        self.assertEqual(len(store), 14)

    def test_supplied_corpus_cannot_be_cut_to_three(self):
        self.start(); rows = self.batch(self.leads[:3])['rows']
        self.assess(self.assessments(rows)); self.stop()
        failure = self.call('complete', ok=False)
        self.assertIn('expected', failure.stdout + failure.stderr)
        self.assertEqual(self.call('status')['counts']['discovered'], 3)

    def test_stop_reason_cannot_hide_missing_provided_leads(self):
        self.scope['user_limit'] = {'batches': 1, 'quote': 'Run one batch.'}
        self.start(); rows = self.batch(self.leads[:3])['rows']
        self.assess(self.assessments(rows)); self.stop('user_limit')
        self.call('complete', ok=False)

    def test_missing_exported_record_invalidates_completion(self):
        self.ready(); self.call('complete')
        path = self.workspace / self.track / 'opportunities.json'
        records = json.loads(path.read_text(encoding='utf-8'))
        del records[next(iter(records))]
        path.write_text(json.dumps(records), encoding='utf-8')
        self.call('check', ok=False)

    def test_same_url_programs_are_distinct_expected_leads(self):
        self.track = 'graduate'
        self.leads = [{'title': name, 'organization': 'Example University',
                       'url': 'https://example.edu/admissions', 'cycle': 'Fall 2027'}
                      for name in ('Robotics MS', 'Robotics PhD')]
        self.scope.pop('expected_urls')
        self.scope['expected_leads'] = self.leads
        self.start(); rows = self.batch(self.leads[:1])['rows']
        self.assess(self.assessments(rows)); self.stop()
        self.call('complete', ok=False)
        rows = self.batch(self.leads[1:])['rows']
        self.assess(self.assessments(rows)); self.stop()
        self.assertEqual(self.call('complete')['counts']['discovered'], 2)

    def test_ambiguous_duplicate_url_manifest_requires_full_identities(self):
        self.scope['expected_urls'] = [self.leads[0]['url']] * 2
        self.cli('start', '--track', self.track, '--query', 'robotics',
                 '--scope', self.write('ambiguous.json', self.scope), ok=False)

    def test_unassessed_one_of_fourteen_blocks_completion(self):
        self.start(); rows = self.batch()['rows']; self.stop()
        self.assess(self.assessments(rows[:-1]))
        failure = self.call('complete', ok=False)
        self.assertIn(rows[-1]['id'], failure.stdout + failure.stderr)

    def test_duplicate_observations_do_not_destroy_provenance(self):
        self.start(); self.batch(); result = self.batch(self.leads[:3], query='robot software')
        self.assertEqual(result['counts']['observations'], 17)
        self.assertEqual(result['counts']['discovered'], 14)
        self.assertEqual(len(result['batches']), 2)

    def test_delete_a_record_or_edit_a_final_report_is_detected(self):
        self.ready(); result = self.call('complete')
        html = Path(result['report_html'])
        original = html.read_text(encoding='utf-8')
        html.write_text(original.replace('data-lead-id=', 'data-hidden-id=', 1), encoding='utf-8')
        self.call('check', ok=False)
        html.write_text(original, encoding='utf-8')
        state = self.workspace / self.track / 'search_runs' / (self.run + '.json')
        data = json.loads(state.read_text(encoding='utf-8'))
        del data['leads'][next(iter(data['leads']))]
        state.write_text(json.dumps(data), encoding='utf-8')
        self.call('check', ok=False)

    def test_new_search_or_assessment_invalidates_previous_completion(self):
        self.ready(); self.call('complete')
        result = self.batch([{'title': 'One more', 'organization': 'Example', 'url': 'https://example.org/new'}])
        self.assertFalse(result['complete'])
        html = Path(result['report_html']).read_text(encoding='utf-8')
        self.assertIn('INCOMPLETE', html)
        self.assertEqual(html.count('data-lead-id='), 15)
        self.call('check', ok=False)

    def test_repeated_zero_result_query_does_not_prove_search_saturation(self):
        self.scope['mode'] = 'open'; self.scope.pop('expected_urls')
        self.start(); self.batch([]); self.batch([]); self.batch([]); self.stop('saturated')
        self.call('complete', ok=False)

    def test_two_distinct_empty_batches_after_three_sources_allow_saturated_scope(self):
        self.scope['mode'] = 'open'; self.scope.pop('expected_urls')
        self.start(); rows = self.batch()['rows']; self.assess(self.assessments(rows))
        self.batch([], 'adjacent robotics', 'https://two.example/careers')
        self.batch([], 'new grad robot', 'https://three.example/careers')
        self.stop('saturated')
        self.assertTrue(self.call('complete')['complete'])

    def test_saturation_cannot_skip_a_declared_source(self):
        self.scope['mode'] = 'open'; self.scope.pop('expected_urls')
        self.scope['source_urls'].append('https://four.example/careers')
        self.start(); rows = self.batch()['rows']; self.assess(self.assessments(rows))
        self.batch([], 'adjacent robotics', 'https://two.example/careers')
        self.batch([], 'new grad robot', 'https://three.example/careers')
        self.stop('saturated')
        failure = self.call('complete', ok=False)
        self.assertIn('https://four.example/careers', failure.stderr)
        self.batch([], 'fourth source', 'https://four.example/careers')
        self.stop('saturated')
        self.assertTrue(self.call('complete')['complete'])

    def test_blocked_fetch_is_not_a_successful_empty_search_batch(self):
        self.scope['mode'] = 'open'; self.scope.pop('expected_urls')
        self.start(); self.batch([])
        self.batch([], 'second', 'https://two.example/careers', 'blocked')
        self.batch([], 'third', 'https://three.example/careers', 'blocked')
        self.stop('saturated'); self.call('complete', ok=False)

    def test_user_limit_requires_explicit_initial_budget_and_quote(self):
        self.scope['mode'] = 'open'; self.scope.pop('expected_urls')
        self.start(); self.batch([]); self.stop('user_limit'); self.call('complete', ok=False)
        self.scope['user_limit'] = {'batches': 1, 'quote': 'Run one search batch as a test.'}
        self.start(); self.batch([]); self.stop('user_limit')
        self.assertTrue(self.call('complete')['complete'])

    def test_bad_assessment_batch_is_atomic(self):
        self.start(); rows = self.batch()['rows']
        values = self.assessments(rows)
        values[-1]['dimensions']['technical']['value'] = 101
        self.call('assess', '--file', self.write('bad.json', {'assessments': values}), ok=False)
        self.assertEqual(self.call('status')['counts']['assessed'], 0)

    def test_all_unknown_is_pending_not_fake_zero_score(self):
        self.start(); rows = self.batch()['rows']; values = self.assessments(rows)
        for a in values:
            for d in a['dimensions'].values():
                d.update(value=None, reason='Evidence not available yet.')
        result = self.assess(values); self.stop()
        self.assertEqual(result['counts']['pending'], 14)
        self.call('complete', ok=False)

    def test_duplicate_target_must_exist_and_must_not_be_a_cycle(self):
        self.start(); rows = self.batch()['rows']; values = self.assessments(rows[:2])
        for i, a in enumerate(values):
            a.update(disposition='duplicate', duplicate_of=rows[1-i]['id'])
            a.pop('dimensions')
        self.call('assess', '--file', self.write('cycle.json', {'assessments': values}), ok=False)
        values[0]['duplicate_of'] = 'missing'
        self.call('assess', '--file', self.write('missing.json', {'assessments': values[:1]}), ok=False)

    def test_unrequested_scope_exclusion_is_not_accepted(self):
        self.start(); rows = self.batch()['rows']; a = self.assessments(rows[:1])[0]
        a.update(disposition='out_of_scope', scope_exclusion='Only keep top three')
        a.pop('dimensions')
        self.call('assess', '--file', self.write('scope-cut.json', {'assessments': [a]}), ok=False)

    def test_industry_hard_user_constraint_must_exist_in_initial_scope(self):
        self.start(); rows = self.batch()['rows']; a = self.assessments(rows[:1])[0]
        a.update(disposition='excluded', gates={'constraints': {'verdict': 'FAIL', 'reason': 'Unsupported invented rule.'}},
                 hard_gate={'kind': 'explicit_user_constraint', 'requirement_quote': 'Role is in Boston.',
                            'candidate_fact': 'Invented location restriction.', 'source_url': rows[0]['url'],
                            'user_constraint': 'Only keep my favorite three roles.'})
        a.pop('dimensions')
        self.call('assess', '--file', self.write('invented-gate.json', {'assessments': [a]}), ok=False)

    def test_old_unstructured_exclusion_is_pending_and_repairable_without_editing_source(self):
        self.ready(); self.call('complete')
        path = self.workspace/self.track/'search_runs'/f'{self.run}.json'
        run = json.loads(path.read_text(encoding='utf-8'))
        key = next(iter(run['leads']))
        old = run['leads'][key]['assessment']
        old.update(disposition='excluded', score=None,
                   gates={'eligibility': {'verdict': 'FAIL', 'reason': 'Ordinary experience gap.'}})
        old.pop('dimensions')
        path.write_text(json.dumps(run), encoding='utf-8')
        status = self.call('report')
        self.assertEqual(status['counts']['pending'], 1)
        self.assertEqual(status['counts']['displayed'], 14)
        self.assertIn('Requires reassessment', status['rows'][0]['assessment']['reason'])
        self.assertIn('INCOMPLETE', Path(status['report_html']).read_text(encoding='utf-8'))
        self.call('complete', ok=False)
        self.assess(self.assessments(status['rows'][:1]))
        self.assertTrue(self.call('complete')['complete'])

    def test_history_outcomes_are_preserved_when_exporting_search(self):
        self.ready()
        rows = self.call('status')['rows']
        self.write('workspace/industry/opportunities.json', {rows[0]['id']: {
            **rows[0], 'status': 'submitted', 'confirmed_at': '2026-09-10'}})
        self.call('complete')
        saved = json.loads((self.workspace/'industry/opportunities.json').read_text(encoding='utf-8'))
        self.assertEqual(saved[rows[0]['id']]['status'], 'submitted')
        self.assertEqual(saved[rows[0]['id']]['confirmed_at'], '2026-09-10')

    def test_new_run_preserves_old_receipt_and_old_rerun_preserves_latest_score(self):
        self.ready(); first = self.call('complete'); old_id = self.run
        self.ready(); newer_id = self.run
        values = self.assessments(self.call('status')['rows'])
        values[0]['dimensions']['technical']['value'] = 90
        self.assess(values); self.call('complete')
        self.run = old_id
        self.assertTrue(self.call('check')['complete'])
        self.call('complete')
        saved = json.loads((self.workspace/'industry/opportunities.json').read_text(encoding='utf-8'))
        latest = saved[first['rows'][0]['id']]
        self.assertEqual(latest['search_run_id'], newer_id)
        self.assertEqual(latest['search_assessment']['dimensions']['technical']['value'], 90)

    def test_all_three_tracks_compute_their_own_rubric(self):
        for track in ('graduate', 'academia'):
            with self.subTest(track=track):
                self.track = track
                if track == 'graduate':
                    for r in self.leads: r['cycle'] = 'Fall 2027'
                self.ready(); result = self.call('complete')
                self.assertEqual(result['track'], track)
                self.assertEqual(result['rows'][0]['assessment']['score']['overall'], 80)
                self.assertNotIn('technical', result['rows'][0]['assessment']['score']['weights'])

    def test_invalid_track_run_id_or_lock_cannot_modify_state(self):
        self.start()
        self.cli('status', '--track', 'industry', '--run', '../escape', ok=False)
        state = self.workspace / self.track / 'search_runs' / (self.run+'.json')
        before = state.read_bytes()
        state.with_suffix('.lock').write_text('busy', encoding='utf-8')
        self.call('batch', '--file', self.write('empty.json', {}), ok=False)
        self.assertEqual(state.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
