#!/usr/bin/env python3
"""Account for every recorded discovery before completing a US career search.

Hosts search and assess evidence; this helper preserves observations, calculates
scores, and generates/validates the complete report. It makes no network calls.
See docs/SEARCH_PIPELINE.md for input schemas and limits.
"""
import argparse
from contextlib import contextmanager
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

try:
    from .career import ROOT, TRACKS, STATUSES, is_http_source, profile, read_json, save_json
    from .career_scoring import assess, rubric_for, validate_industry_exclusion, IndustryExclusionError
    from .career_report import render_report
except ImportError:
    from career import ROOT, TRACKS, STATUSES, is_http_source, profile, read_json, save_json
    from career_scoring import assess, rubric_for, validate_industry_exclusion, IndustryExclusionError
    from career_report import render_report


SCHEMA = 1
DISPOSITIONS = {'eligible', 'provisional', 'excluded', 'closed', 'unreachable',
                'duplicate', 'out_of_scope', 'pending'}
STOP_REASONS = ('saturated', 'provided_complete', 'user_limit', 'blocked')


def nonempty(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be a nonempty string.')
    return value.strip()


def http(value, name):
    if not is_http_source(value) or re.search(r'\s', value):
        raise ValueError(f'{name} must be an HTTP(S) URL without credentials or whitespace.')
    return value.strip()


def checked_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('checked_on must be YYYY-MM-DD.')
    date.fromisoformat(value)
    return value


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode('utf-8')).hexdigest()


def lead_id(track, row):
    value = '\n'.join((track, row['url'].strip(), row['title'].strip(), row.get('cycle', '').strip()))
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:20]


def private_path(workspace, track, *parts):
    """Never allow a run identifier or an internal symlink to escape private state."""
    if track not in TRACKS:
        raise ValueError('Unknown track.')
    workspace = workspace.absolute()
    if workspace.resolve() == ROOT.resolve():
        raise ValueError('Workspace must be a private directory, not the repository root.')
    # A custom path inside this source checkout must still live in its ignored workspace.
    if workspace.resolve().is_relative_to(ROOT.resolve()):
        if not workspace.resolve().is_relative_to((ROOT / 'workspace').resolve()):
            raise ValueError('Repository-local pipeline state must be inside workspace/.')
    target = workspace / track
    for part in parts:
        target /= part
    for p in (target, *target.parents):
        if p == workspace:
            break
        if p.is_symlink():
            raise ValueError(f'Refusing symlink in private output path: {p}')
    if not target.resolve().is_relative_to(workspace.resolve()):
        raise ValueError('Output escapes the private workspace.')
    return target


@contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = path.open('x', encoding='utf-8')
    except FileExistsError as exc:
        raise ValueError(f'Pipeline state is locked: {path}. Resolve the active writer before retrying.') from exc
    try:
        with fd:
            fd.write(now())
        yield
    finally:
        path.unlink(missing_ok=True)


def scope_contract(value, track):
    if not isinstance(value, dict):
        raise ValueError('Scope must be an object.')
    allowed = {'request', 'mode', 'source_urls', 'exclusions', 'expected_urls', 'expected_leads', 'user_limit'}
    if set(value) - allowed:
        raise ValueError('Unsupported scope fields (candidate limits are not supported).')
    result = dict(value)
    result['request'] = nonempty(result.get('request'), 'scope.request')
    if result.get('mode') not in ('open', 'provided'):
        raise ValueError('scope.mode must be open or provided.')
    urls = result.get('source_urls')
    if not isinstance(urls, list) or not urls:
        raise ValueError('scope.source_urls must name the initial discovery sources.')
    result['source_urls'] = [http(u, 'source URL') for u in urls]
    exclusions = result.get('exclusions', [])
    if not isinstance(exclusions, list):
        raise ValueError('scope.exclusions must be a list of explicit user criteria.')
    result['exclusions'] = [nonempty(x, 'scope exclusion') for x in exclusions]
    if result['mode'] == 'provided':
        if 'expected_leads' not in result and 'expected_urls' not in result:
            raise ValueError('Provided scope requires expected_leads (or unique expected_urls).')
        if 'expected_urls' in result:
            expected = result['expected_urls']
            if not isinstance(expected, list):
                raise ValueError('expected_urls must be a list.')
            result['expected_urls'] = [http(u, 'expected URL') for u in expected]
            if len(set(result['expected_urls'])) != len(expected):
                raise ValueError('Shared URLs require expected_leads with distinct titles and cycles, not duplicate expected_urls.')
        if 'expected_leads' in result:
            if not isinstance(result['expected_leads'], list):
                raise ValueError('expected_leads must be a list of complete discovery identities.')
            expected = [clean_lead(track, r) for r in result['expected_leads']]
            if len({r['id'] for r in expected}) != len(expected):
                raise ValueError('expected_leads repeats an identical opportunity.')
            result['expected_leads'] = [{k: v for k, v in r.items() if k != 'id'} for r in expected]
    elif 'expected_urls' in result or 'expected_leads' in result:
        raise ValueError('Expected discoveries belong only to a provided corpus.')
    if 'user_limit' in result:
        limit = result['user_limit']
        if (not isinstance(limit, dict) or set(limit) != {'batches', 'quote'}
                or type(limit['batches']) is not int or limit['batches'] < 1):
            raise ValueError('user_limit requires positive batches and the exact user quote.')
        nonempty(limit['quote'], 'user_limit.quote')
    return result


def clean_lead(track, row):
    if not isinstance(row, dict):
        raise ValueError('Every result must be an object.')
    allowed = {'title', 'organization', 'url', 'cycle'}
    if set(row) - allowed:
        raise ValueError('Discovery results accept title, organization, url and cycle; assess separately.')
    result = {k: nonempty(row.get(k), k) for k in ('title', 'organization')}
    result['url'] = http(row.get('url'), 'lead URL')
    cycle = row.get('cycle', '')
    if not isinstance(cycle, str) or (track == 'graduate' and not cycle.strip()):
        raise ValueError('Graduate discoveries require a named admission cycle.')
    result['cycle'] = cycle.strip()
    result['id'] = lead_id(track, result)
    return result


def validate_links(run):
    for key, row in run['leads'].items():
        a = row.get('assessment')
        if not a:
            continue
        if a['disposition'] == 'out_of_scope':
            if a.get('scope_exclusion') not in run['scope']['exclusions']:
                raise ValueError(f'{key}: exclusion was not an explicit initial scope criterion.')
        proof = a.get('hard_gate')
        if (run['track'] == 'industry' and a['disposition'] == 'excluded'
                and isinstance(proof, dict)
                and proof.get('kind') in ('explicit_user_constraint', 'hard_compensation')
                and proof.get('user_constraint') not in run['scope']['exclusions']):
            raise ValueError(f'{key}: hard_gate user_constraint was not an explicit initial scope criterion.')
        if a['disposition'] == 'duplicate':
            target = a.get('duplicate_of')
            if target not in run['leads'] or target == key:
                raise ValueError(f'{key}: duplicate_of must reference another existing lead.')
            visited = {key}
            while target:
                if target in visited:
                    raise ValueError('Duplicate relationship contains a cycle.')
                visited.add(target)
                other = run['leads'][target].get('assessment') or {}
                target = other.get('duplicate_of') if other.get('disposition') == 'duplicate' else None
                if target and target not in run['leads']:
                    raise ValueError('Duplicate target does not exist.')


def validate_run(run, track, identifier):
    if (not isinstance(run, dict) or run.get('schema_version') != SCHEMA
            or run.get('track') != track or run.get('run_id') != identifier
            or not isinstance(run.get('leads'), dict) or not isinstance(run.get('batches'), list)):
        raise ValueError('Invalid pipeline run; preserve it and repair before continuing.')
    scope_contract(run.get('scope'), track)
    nonempty(run.get('query'), 'query')
    rubric_for(track, run.get('academic_role'))
    observed = set()
    known = set()
    for batch in run['batches']:
        if not isinstance(batch, dict) or not isinstance(batch.get('results'), list):
            raise ValueError('Invalid discovery batch.')
        http(batch.get('source_url'), 'source URL')
        nonempty(batch.get('query'), 'query')
        checked_date(batch.get('checked_on'))
        if batch.get('access') not in ('ok', 'blocked'):
            raise ValueError('Invalid batch access.')
        if any(not isinstance(k, str) or k not in run['leads'] for k in batch['results']):
            raise ValueError('A recorded discovery is missing from the ledger.')
        new = list(dict.fromkeys(k for k in batch['results'] if k not in known))
        if batch.get('new_ids') != new:
            raise ValueError('Discovery batch count does not match its observations.')
        known.update(batch['results']); observed.update(batch['results'])
    if observed != set(run['leads']):
        raise ValueError('Lead ledger and discovery observations do not reconcile.')
    for key, row in run['leads'].items():
        if not isinstance(row, dict):
            raise ValueError('Invalid lead record.')
        normalized = clean_lead(track, {k: row[k] for k in ('title', 'organization', 'url', 'cycle') if k in row})
        if key != normalized['id'] or row.get('id') != key:
            raise ValueError('Lead identity has changed; preserve the recorded discovery.')
        a = row.get('assessment')
        if a is not None:
            original = {k: v for k, v in a.items() if k != 'score'}
            try:
                expected = assess(track, original, run.get('academic_role'))
            except IndustryExclusionError:
                # Older drafts omitted structured exclusion proof. Keep their data
                # readable and repairable, but never let them satisfy completion.
                expected = {**original, 'score': None}
            if a != expected:
                raise ValueError(f'{key}: stored scoring differs from the canonical calculation.')
    validate_links(run)
    if run.get('stop') is not None:
        if not isinstance(run['stop'], dict) or run['stop'].get('reason') not in STOP_REASONS:
            raise ValueError('Invalid search stopping record.')
        nonempty(run['stop'].get('note'), 'stop.note')


def exclusion_error(run, assessment):
    if run['track'] == 'industry' and assessment and assessment['disposition'] == 'excluded':
        try:
            validate_industry_exclusion(assessment)
        except IndustryExclusionError as exc:
            return str(exc)
    return None


def completeness_errors(run):
    errors = []
    if run['scope']['mode'] == 'provided':
        actual = {r['url'] for r in run['leads'].values()}
        missing = sorted(set(run['scope'].get('expected_urls', [])) - actual)
        if missing:
            errors.append('Missing expected corpus URLs: ' + ', '.join(missing))
        missing_leads = [r for r in run['scope'].get('expected_leads', [])
                         if lead_id(run['track'], r) not in run['leads']]
        if missing_leads:
            errors.append('Missing expected corpus identities: ' + '; '.join(
                f"{r['title']} ({r.get('cycle', '')}) {r['url']}" for r in missing_leads))
    for key, row in run['leads'].items():
        a = row.get('assessment')
        if not a or a['disposition'] == 'pending':
            errors.append(f'{key}: assessment pending; score known dimensions or document a supported disposition.')
        proof_error = exclusion_error(run, a)
        if proof_error:
            errors.append(f'{key}: Requires reassessment: {proof_error}')
    stop = run.get('stop')
    batches = run['batches']
    if not batches:
        errors.append('No discovery batches recorded.')
    if not stop:
        errors.append('Search stop evidence is missing.')
        return errors
    reason = stop['reason']
    if reason == 'blocked':
        errors.append('Search blocked; this is a partial result, not a completed search.')
    elif reason == 'provided_complete':
        if run['scope']['mode'] != 'provided':
            errors.append('provided_complete requires a declared provided corpus.')
    elif reason == 'user_limit':
        budget = run['scope'].get('user_limit')
        if not budget or len(batches) < budget['batches']:
            errors.append('User limit was not declared with a quote or has not been reached.')
    elif reason == 'saturated':
        attempted = {b['source_url'] for b in batches}
        missing_sources = sorted(set(run['scope']['source_urls']) - attempted)
        if missing_sources:
            errors.append('Declared sources have not been attempted: ' + ', '.join(missing_sources))
        good = {b['source_url'] for b in batches if b['access'] == 'ok'}
        last = batches[-2:]
        if (len(good) < 3 or len(last) != 2 or any(b['access'] != 'ok' or b['new_ids'] for b in last)
                or len({(b['query'].casefold().strip(), b['source_url']) for b in last}) != 2):
            errors.append('Saturation needs three successful sources and two distinct final successful batches with no new discoveries.')
    return errors


def fingerprint(run):
    return digest({k: v for k, v in run.items() if k != 'completion'})


def payload(run):
    rows = []
    for original in run['leads'].values():
        row = dict(original)
        proof_error = exclusion_error(run, row.get('assessment'))
        if proof_error:
            prior = row['assessment']
            row['assessment'] = {**prior, 'disposition': 'pending', 'score': None,
                                 'reason': 'Requires reassessment: ' + proof_error +
                                           ' Previous exclusion: ' + prior['reason']}
        rows.append(row)
    scored = sum(bool((r.get('assessment') or {}).get('score')) for r in rows)
    pending = sum(not r.get('assessment') or r['assessment']['disposition'] == 'pending' for r in rows)
    return {'run_id': run['run_id'], 'track': run['track'], 'query': run['query'],
            'scope': run['scope'], 'stop': run.get('stop'), 'complete': False,
            'errors': completeness_errors(run), 'rows': rows, 'batches': run['batches'],
            'counts': {'observations': sum(len(b['results']) for b in run['batches']),
                       'discovered': len(rows), 'assessed': sum(r.get('assessment') is not None for r in rows),
                       'scored': scored, 'unscored': len(rows)-scored, 'pending': pending, 'displayed': len(rows)}}


def report_paths(workspace, run):
    folder = private_path(workspace, run['track'], 'reports', run['run_id'])
    return folder / 'index.html', folder / 'results.json'


def inspect(run, workspace):
    result = payload(run)
    receipt = run.get('completion')
    html, data = report_paths(workspace, run)
    result.update(report_html=str(html), report_json=str(data))
    if not receipt:
        result['errors'].append('Completion receipt missing; run complete after resolving pending work.')
    elif result['errors'] or receipt.get('fingerprint') != fingerprint(run):
        result['errors'].append('Completion receipt is stale for this run.')
    else:
        expected = payload(run)
        expected['complete'] = True
        text = render_report(expected)
        if (not html.is_file() or not data.is_file()
                or html.read_text(encoding='utf-8') != text or read_json(data) != expected):
            result['errors'].append('The complete report is missing or differs from all recorded results.')
        else:
            store_path = private_path(workspace, run['track'], 'opportunities.json')
            entries = read_json(store_path) if store_path.exists() else {}
            if not isinstance(entries, dict) or any(
                    not isinstance(entries.get(key), dict)
                    or entries[key].get('search_assessments', {}).get(run['run_id'],
                        entries[key].get('search_assessment') if entries[key].get('search_run_id') == run['run_id'] else None) != row['assessment']
                    or any(entries[key].get(k) != row[k] for k in ('id', 'title', 'organization', 'url', 'cycle'))
                    for key, row in run['leads'].items()):
                result['errors'].append('Exported opportunities do not contain every assessed discovery; regenerate completion.')
            else:
                result['complete'] = True
    return result


def atomic_text(path, content):
    # Use the same atomic-replace convention as private JSON writes.
    import os
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.career-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as out:
            out.write(content)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_report(run, workspace, complete):
    result = payload(run)
    result['complete'] = complete
    if not complete and not result['errors']:
        result['errors'].append('Completion verification has not been run; use complete to validate and export this run.')
    html, data = report_paths(workspace, run)
    atomic_text(html, render_report(result))
    save_json(data, result)
    return html, data


def export_opportunities(run, workspace):
    path = private_path(workspace, run['track'], 'opportunities.json')
    with lock(private_path(workspace, run['track'], '.pipeline-export.lock')):
        entries = read_json(path) if path.exists() else {}
        if not isinstance(entries, dict) or any(not isinstance(v, dict) or v.get('status') not in STATUSES for v in entries.values()):
            raise ValueError('Invalid existing opportunity store; refusing to replace it.')
        for key, row in run['leads'].items():
            previous = entries.get(key, {})
            a = row['assessment']
            status = {'eligible': 'verified', 'provisional': 'verified', 'closed': 'expired',
                      'unreachable': 'unreachable'}.get(a['disposition'], 'discovered')
            history = previous.get('search_assessments', {})
            if not isinstance(history, dict):
                raise ValueError('Invalid search assessment history; refusing to overwrite it.')
            history = dict(history)
            if previous.get('search_run_id') and previous.get('search_assessment'):
                history.setdefault(previous['search_run_id'], previous['search_assessment'])
            history[run['run_id']] = a
            saved = {**previous, **{k: row[k] for k in ('id', 'title', 'organization', 'url', 'cycle')},
                     'track': run['track'], 'status': previous.get('status', status),
                     'search_assessments': history}
            if run['created_at'] >= previous.get('search_run_created_at', ''):
                saved.update(search_run_id=run['run_id'], search_assessment=a,
                             search_run_created_at=run['created_at'], updated_at=now())
            entries[key] = saved
        save_json(path, entries)


def mutate(run, command, args):
    if command == 'batch':
        batch = read_json(args.file)
        if not isinstance(batch, dict) or set(batch) - {'source_url', 'query', 'checked_on', 'results', 'access', 'note'}:
            raise ValueError('Invalid discovery batch fields.')
        results = batch.get('results')
        if not isinstance(results, list):
            raise ValueError('batch.results must contain all discovered opportunities.')
        b = {'source_url': http(batch.get('source_url'), 'source URL'),
             'query': nonempty(batch.get('query'), 'query'),
             'checked_on': checked_date(batch.get('checked_on')), 'access': batch.get('access'),
             'note': nonempty(batch.get('note'), 'batch.note'), 'results': [], 'new_ids': []}
        if b['access'] not in ('ok', 'blocked'):
            raise ValueError('batch.access must be ok or blocked.')
        cleaned = [clean_lead(run['track'], r) for r in results]
        for row in cleaned:
            key = row['id']; b['results'].append(key)
            if key not in run['leads']:
                run['leads'][key] = {**row, 'assessment': None}
                b['new_ids'].append(key)
        run['batches'].append(b)
        run['stop'] = None
    elif command == 'assess':
        data = read_json(args.file)
        if not isinstance(data, dict) or set(data) != {'assessments'} or not isinstance(data['assessments'], list):
            raise ValueError('Expected an assessments array.')
        seen = set()
        for a in data['assessments']:
            if not isinstance(a, dict) or a.get('id') not in run['leads'] or a['id'] in seen:
                raise ValueError('Assessment IDs must be unique existing discoveries.')
            key = a['id']; seen.add(key)
            run['leads'][key]['assessment'] = assess(run['track'], {k: v for k, v in a.items() if k != 'id'}, run.get('academic_role'))
        validate_links(run)
    elif command == 'stop':
        run['stop'] = {'reason': args.reason, 'note': nonempty(args.note, 'stop.note')}
    run['completion'] = None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT / 'workspace')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('start', 'rubric'):
        p = sub.add_parser(name)
        p.add_argument('--track', choices=TRACKS, required=True)
        p.add_argument('--academic-role', choices=('faculty', 'postdoc', 'research_staff'))
        if name == 'start':
            p.add_argument('--query', required=True); p.add_argument('--scope', type=Path, required=True)
    for name in ('batch', 'assess', 'stop', 'status', 'report', 'complete', 'check'):
        p = sub.add_parser(name)
        p.add_argument('--track', choices=TRACKS, required=True); p.add_argument('--run', required=True)
        if name in ('batch', 'assess'):
            p.add_argument('--file', type=Path, required=True)
        if name == 'stop':
            p.add_argument('--reason', choices=STOP_REASONS, required=True); p.add_argument('--note', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'rubric':
            result = {'track': args.track, 'weights': rubric_for(args.track, args.academic_role)}
        elif args.command == 'start':
            data = profile(args.workspace)
            if args.track not in data['profiles']:
                raise ValueError('Initialize the explicitly selected track first.')
            rubric_for(args.track, args.academic_role)
            scope = scope_contract(read_json(args.scope), args.track)
            identifier = uuid.uuid4().hex[:16]
            path = private_path(args.workspace, args.track, 'search_runs', identifier+'.json')
            run = {'schema_version': SCHEMA, 'run_id': identifier, 'track': args.track,
                   'academic_role': args.academic_role, 'query': nonempty(args.query, 'query'),
                   'scope': scope, 'created_at': now(), 'batches': [], 'leads': {},
                   'stop': None, 'completion': None}
            save_json(path, run)
            result = {'run_id': identifier, 'track': args.track, 'path': str(path)}
        else:
            if not re.fullmatch(r'[a-f0-9]{16}', args.run):
                raise ValueError('Invalid run ID.')
            path = private_path(args.workspace, args.track, 'search_runs', args.run+'.json')
            with lock(path.with_suffix('.lock')):
                run = read_json(path)
                validate_run(run, args.track, args.run)
                if args.command in ('batch', 'assess', 'stop'):
                    mutate(run, args.command, args)
                    validate_run(run, args.track, args.run)
                    save_json(path, run)
                    write_report(run, args.workspace, False)
                elif args.command == 'complete':
                    errors = completeness_errors(run)
                    if errors:
                        raise ValueError('Cannot complete search:\n'+'\n'.join(errors))
                    export_opportunities(run, args.workspace)
                    write_report(run, args.workspace, True)
                    run['completion'] = {'fingerprint': fingerprint(run), 'completed_at': now()}
                    save_json(path, run)
                elif args.command == 'report':
                    ready = inspect(run, args.workspace)['complete']
                    write_report(run, args.workspace, ready)
                result = inspect(run, args.workspace)
                if args.command in ('complete', 'check') and not result['complete']:
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    return 1
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'career_pipeline: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
