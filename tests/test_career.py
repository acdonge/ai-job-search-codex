import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'career.py'


class CareerCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name) / 'workspace'

    def run_cli(self, *args, stdin=''):
        return subprocess.run([sys.executable, str(SCRIPT), '--workspace', str(self.workspace), *args],
                              input=stdin, capture_output=True, text=True)

    def test_first_start_requires_selection_without_silently_defaulting(self):
        result = self.run_cli('init')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('industry', result.stdout)
        self.assertIn('graduate', result.stdout)
        self.assertIn('academia', result.stdout)
        self.assertFalse((self.workspace / 'profile.json').exists())

    def test_switching_preserves_private_profiles_and_outputs(self):
        for track in ('industry', 'graduate', 'academia'):
            result = self.run_cli('init', '--track', track)
            self.assertEqual(result.returncode, 0, result.stderr)
            (self.workspace / track / 'notes.md').write_text(track)
        profile = self.workspace / 'profile.json'
        data = json.loads(profile.read_text())
        data['profiles']['graduate']['field'] = 'robotics'
        profile.write_text(json.dumps(data))
        self.assertEqual(self.run_cli('init', '--track', 'graduate').returncode, 0)
        data = json.loads(profile.read_text())
        self.assertEqual(data['active_track'], 'graduate')
        self.assertEqual(data['profiles']['graduate']['field'], 'robotics')
        for track in data['profiles']:
            self.assertEqual((self.workspace / track / 'notes.md').read_text(), track)
            self.assertTrue((self.workspace / track / 'profile' / 'candidate-profile.md').is_file())

    def test_bad_track_cannot_escape_workspace(self):
        self.assertNotEqual(self.run_cli('init', '--track', '../escape').returncode, 0)
        self.assertFalse(self.workspace.exists())

    def test_corrupt_existing_state_is_not_overwritten(self):
        self.workspace.mkdir()
        state = self.workspace / 'profile.json'
        for content in ('{broken', '[]', '{"schema_version":99}',
                        '{"schema_version":1,"active_track":"industry","profiles":[]}'):
            state.write_text(content)
            result = self.run_cli('init', '--track', 'graduate')
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(state.read_text(), content)

    def test_sources_filter_track_and_query_is_data(self):
        self.run_cli('init', '--track', 'graduate')
        result = self.run_cli('search-plan', '--query', 'robotics $(touch bad)', '--cycle', 'Fall 2027')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['track'], 'graduate')
        self.assertTrue(data['queries'])
        self.assertTrue(all('graduate' in s['tracks'] for s in data['sources']))
        self.assertTrue(any('Fall 2027' in q for q in data['queries']))
        self.assertFalse(Path('bad').exists())

    def test_search_plan_does_not_search_ats_documentation_for_vacancies(self):
        result = self.run_cli('search-plan', '--track', 'industry', '--query', 'engineer')
        self.assertEqual(result.returncode, 0, result.stderr)
        queries = json.loads(result.stdout)['queries']
        self.assertFalse(any(q.startswith(('site:docs.greenhouse.io ', 'site:github.com ',
                                          'site:developers.ashbyhq.com ')) for q in queries))

    def test_record_is_track_and_cycle_scoped_and_defaults_to_discovered(self):
        payload = Path(self.temp.name) / 'record.json'
        row = {'title': 'Robotics PhD', 'organization': 'Example University',
               'url': 'https://example.edu/phd', 'cycle': 'Fall 2027'}
        payload.write_text(json.dumps(row))
        self.run_cli('init', '--track', 'graduate')
        a = self.run_cli('record', '--file', str(payload))
        self.assertEqual(a.returncode, 0, a.stderr)
        self.assertEqual(json.loads(a.stdout)['status'], 'discovered')
        b = self.run_cli('record', '--file', str(payload))
        self.assertEqual(json.loads(a.stdout)['id'], json.loads(b.stdout)['id'])
        row['cycle'] = 'Fall 2028'
        payload.write_text(json.dumps(row))
        c = self.run_cli('record', '--file', str(payload))
        self.assertNotEqual(json.loads(a.stdout)['id'], json.loads(c.stdout)['id'])
        self.assertEqual(len(json.loads((self.workspace / 'graduate' / 'opportunities.json').read_text())), 2)

    def test_record_does_not_infer_submission_and_rejects_unconfirmed_transition(self):
        self.run_cli('init', '--track', 'industry')
        payload = Path(self.temp.name) / 'record.json'
        payload.write_text(json.dumps({'title':'Engineer','organization':'Example',
            'url':'https://example.com/jobs/1','status':'submitted'}))
        self.assertNotEqual(self.run_cli('record', '--file', str(payload)).returncode, 0)
        result = self.run_cli('record', '--file', str(payload), '--user-confirmed')
        self.assertEqual(result.returncode, 0, result.stderr)


    def payload(self, **updates):
        path = Path(self.temp.name) / 'record.json'
        row = {'title': 'Engineer', 'organization': 'Example',
               'url': 'https://example.com/jobs/1'}
        row.update(updates)
        path.write_text(json.dumps(row), encoding='utf-8')
        return path

    def test_explicit_record_track_is_preserved_after_another_chat_switches(self):
        self.run_cli('init', '--track', 'industry')
        self.run_cli('init', '--track', 'academia')
        result = self.run_cli('record', '--track', 'industry', '--file', str(self.payload()))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['track'], 'industry')
        self.assertTrue((self.workspace / 'industry/opportunities.json').exists())
        self.assertFalse((self.workspace / 'academia/opportunities.json').exists())
        self.assertEqual(json.loads((self.workspace / 'profile.json').read_text())['active_track'], 'academia')

    def test_confirmed_status_cannot_be_downgraded_without_confirmation(self):
        self.run_cli('init', '--track', 'industry')
        payload = self.payload(status='submitted')
        self.assertEqual(self.run_cli('record', '--file', str(payload), '--user-confirmed').returncode, 0)
        store = self.workspace / 'industry/opportunities.json'
        original = store.read_text()
        payload = self.payload(status='discovered')
        result = self.run_cli('record', '--file', str(payload))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--user-confirmed', result.stderr)
        self.assertEqual(store.read_text(), original)
        result = self.run_cli('record', '--file', str(payload), '--user-confirmed')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'discovered')

    def test_refreshing_details_preserves_confirmed_status_without_reapproval(self):
        self.run_cli('init', '--track', 'industry')
        payload = self.payload(status='submitted')
        self.run_cli('record', '--file', str(payload), '--user-confirmed')
        payload = self.payload(notes='Fresh official source verified')
        result = self.run_cli('record', '--file', str(payload))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'submitted')
        self.assertEqual(json.loads(result.stdout)['notes'], 'Fresh official source verified')

    def test_malformed_status_values_fail_cleanly_without_touching_store(self):
        self.run_cli('init', '--track', 'industry')
        self.run_cli('record', '--file', str(self.payload()))
        store = self.workspace / 'industry/opportunities.json'
        original = store.read_text()
        for status in ([], {}, None, 3, True, 'interviewing'):
            with self.subTest(status=status):
                result = self.run_cli('record', '--file', str(self.payload(status=status)))
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('Traceback', result.stderr)
                self.assertIn('Unsupported status', result.stderr)
                self.assertEqual(store.read_text(), original)

    def test_malformed_record_json_fails_without_creating_records(self):
        self.run_cli('init', '--track', 'industry')
        payload = self.payload()
        for content in ('{broken', '[]', 'null', '{"title":"x","organization":"X","url":"https://example.com/x","score":NaN}'):
            with self.subTest(content=content):
                payload.write_text(content, encoding='utf-8')
                result = self.run_cli('record', '--file', str(payload))
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('Traceback', result.stderr)
                self.assertFalse((self.workspace / 'industry/opportunities.json').exists())

    def test_malformed_saved_status_is_not_silently_replaced(self):
        self.run_cli('init', '--track', 'industry')
        payload = self.payload()
        result = self.run_cli('record', '--file', str(payload))
        saved = json.loads(result.stdout)
        saved['status'] = []
        store = self.workspace / 'industry/opportunities.json'
        store.write_text(json.dumps({saved['id']: saved}), encoding='utf-8')
        original = store.read_text()
        result = self.run_cli('record', '--file', str(self.payload(status='discovered')))
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(store.read_text(), original)

    def test_malformed_active_track_fails_cleanly_without_writes(self):
        self.workspace.mkdir()
        profile = self.workspace / 'profile.json'
        for track in ([], {}, None, True):
            with self.subTest(track=track):
                original = json.dumps({'schema_version': 1, 'active_track': track, 'profiles': {}})
                profile.write_text(original, encoding='utf-8')
                result = self.run_cli('status')
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(profile.read_text(), original)

    def test_malformed_source_registry_is_a_clean_error(self):
        root = Path(self.temp.name) / 'source-fixture'
        (root / 'tools').mkdir(parents=True)
        (root / 'config').mkdir()
        shutil.copy(SCRIPT, root / 'tools/career.py')
        registry = root / 'config/us_sources.json'
        invalid = [[], {}, {'sources': None}, {'sources': [None]},
                   {'sources': [{'tracks': 'industry'}]},
                   {'sources': [{'tracks': ['industry'], 'url': [], 'authority': 'primary'}]},
                   {'sources': [{'tracks': ['industry'], 'url': 'https://[invalid', 'authority': 'primary'}]},
                   {'sources': [{'tracks': ['industry'], 'url': 'https://example.com'}]}]
        for data in invalid:
            with self.subTest(data=data):
                registry.write_text(json.dumps(data), encoding='utf-8')
                result = subprocess.run([sys.executable, str(root / 'tools/career.py'),
                                         'search-plan', '--track', 'industry', '--query', 'engineer'],
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('Traceback', result.stderr)
                self.assertIn('career:', result.stderr)


if __name__ == '__main__':
    unittest.main()
