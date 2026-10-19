#!/usr/bin/env python3
"""Private track selection, US source plans and opportunity records; no network calls."""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
TRACKS = {'industry': 'US industry jobs', 'graduate': 'US MS/PhD admissions', 'academia': 'US academic jobs'}
STATUSES = {'discovered', 'verified', 'shortlisted', 'drafted', 'submitted', 'interview',
            'offer', 'admitted', 'waitlisted', 'rejected', 'withdrawn', 'accepted', 'enrolled',
            'hired', 'declined', 'expired', 'unreachable'}
CONFIRMED = {'submitted', 'interview', 'offer', 'admitted', 'waitlisted', 'rejected',
             'withdrawn', 'accepted', 'enrolled', 'hired', 'declined'}


def reject_nonfinite_json(value):
    raise ValueError(f'Non-finite JSON number is not supported: {value}')


def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'), parse_constant=reject_nonfinite_json)
    except (OSError, ValueError) as exc:
        raise ValueError(f'Cannot read {path}: {exc}') from exc


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.career-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(data, out, indent=2, ensure_ascii=False, allow_nan=False)
            out.write('\n')
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def profile(workspace, allow_new=False):
    path = workspace / 'profile.json'
    if not path.exists() and allow_new:
        return {'schema_version': 1, 'active_track': None, 'profiles': {}}
    data = read_json(path)
    if (not isinstance(data, dict) or data.get('schema_version') != 1
            or not isinstance(data.get('active_track'), str)
            or data['active_track'] not in TRACKS
            or not isinstance(data.get('profiles'), dict)
            or data['active_track'] not in data['profiles']
            or any(t not in TRACKS or not isinstance(p, dict) for t, p in data['profiles'].items())):
        raise ValueError('Invalid profile schema; preserve the file and repair it before continuing.')
    return data


def initialize(workspace, track):
    data = profile(workspace, allow_new=True)
    # Validate before creating anything; reselecting a track must preserve edits.
    base = workspace / track
    for folder in ('profile', 'cv', 'cover_letters', 'documents/cv', 'documents/linkedin',
                   'documents/diplomas', 'documents/references', 'documents/projects',
                   'documents/applications', 'documents/postings',
                   'job_scraper', 'company_research', 'reports', 'upskill', 'gmail_sync'):
        (base / folder).mkdir(parents=True, exist_ok=True)
    copies = [(ROOT / 'templates/candidate-profile.md', base / 'profile/candidate-profile.md')]
    copies += [(p, base / 'profile' / p.name) for p in
               (ROOT / '.agents/skills/job-application-assistant').glob('[0-9][0-9]-*.md')]
    copies += [(ROOT / '.agents/skills/job-scraper/search-queries.md', base / 'profile/search-queries.md'),
               (ROOT / 'cv/main_example.tex', base / 'cv/main_example.tex'),
               (ROOT / 'cover_letters/cover_example.tex', base / 'cover_letters/cover_example.tex'),
               (ROOT / 'cover_letters/cover.cls', base / 'cover_letters/cover.cls')]
    for source, destination in copies:
        if not destination.exists():
            shutil.copyfile(source, destination)
    fonts = base / 'cover_letters/OpenFonts'
    if not fonts.exists():
        shutil.copytree(ROOT / 'cover_letters/OpenFonts', fonts)
    data['profiles'].setdefault(track, {})
    data['active_track'] = track
    save_json(workspace / 'profile.json', data)
    return {'track': track, 'workspace': str(base), 'next': 'Read workflows/codex.md and complete intake.'}


def is_http_source(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme in ('http', 'https') and bool(parsed.hostname)
                and not parsed.username and not parsed.password)
    except ValueError:
        return False


def source_plan(track, query=None, cycle=None):
    registry = read_json(ROOT / 'config/us_sources.json')
    if not isinstance(registry, dict) or not isinstance(registry.get('sources'), list):
        raise ValueError('Invalid source registry: expected a sources list.')
    for index, source in enumerate(registry['sources']):
        if (not isinstance(source, dict)
                or not isinstance(source.get('tracks'), list)
                or not source['tracks']
                or any(not isinstance(t, str) or t not in TRACKS for t in source['tracks'])
                or not is_http_source(source.get('url'))
                or not isinstance(source.get('authority'), str)
                or not source['authority'].strip()):
            raise ValueError(f'Invalid source registry entry {index}: tracks, URL and authority are required.')
    sources = [s for s in registry['sources'] if track in s['tracks']]
    result = {'track': track, 'sources': sources,
              'note': 'Discovery plan only. Fetch current official pages before asserting facts.'}
    if query is not None:
        suffix = {'industry': 'United States careers job', 'graduate': 'graduate admissions funding',
                  'academia': 'United States faculty postdoc research position'}[track]
        terms = ' '.join(x for x in (query, suffix, cycle) if x)
        result['queries'] = [f'site:{urlsplit(s["url"]).netloc} {terms}'
                             for s in sources if s['authority'] != 'context' and s.get('category') != 'employer_ats']
        result['queries'].insert(0, f'site:edu {terms}' if track != 'industry' else f'{terms} official careers')
    return result


def record(workspace, track, row, user_confirmed):
    if not isinstance(row, dict):
        raise ValueError('Opportunity must be a JSON object.')
    for field in ('title', 'organization', 'url'):
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError(f'Opportunity requires a nonempty {field}.')
    if not is_http_source(row['url']):
        raise ValueError('Opportunity URL must be a public http(s) source without credentials.')
    cycle = row.get('cycle', '')
    if not isinstance(cycle, str) or (track == 'graduate' and not cycle.strip()):
        raise ValueError('Graduate opportunities require a named admission cycle.')
    identity = '\n'.join((track, row['url'].strip(), row['title'].strip(), cycle.strip()))
    key = hashlib.sha256(identity.encode()).hexdigest()[:20]
    path = workspace / track / 'opportunities.json'
    entries = read_json(path) if path.exists() else {}
    if not isinstance(entries, dict) or any(
            not isinstance(v, dict) or not isinstance(v.get('status'), str)
            or v['status'] not in STATUSES for v in entries.values()):
        raise ValueError('Invalid opportunity store; refusing to overwrite it.')
    previous = entries.get(key, {})
    status = row.get('status', previous.get('status', 'discovered'))
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError(f'Unsupported status: {status}')
    previous_status = previous.get('status')
    confirmed_change = status != previous_status and (status in CONFIRMED or previous_status in CONFIRMED)
    if confirmed_change and not user_confirmed:
        raise ValueError('This outcome requires user evidence; pass --user-confirmed only after confirmation.')
    saved = {**previous, **row, 'id': key, 'track': track, 'status': status,
             'updated_at': datetime.now(timezone.utc).isoformat()}
    entries[key] = saved
    save_json(path, entries)
    return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT / 'workspace',
                        help='Private storage; custom paths must be excluded from version control.')
    subs = parser.add_subparsers(dest='command', required=True)
    init = subs.add_parser('init', help='Select a track; no existing data is reset.')
    init.add_argument('--track', choices=TRACKS)
    subs.add_parser('status')
    for command in ('sources', 'search-plan'):
        sub = subs.add_parser(command)
        sub.add_argument('--track', choices=TRACKS)
        if command == 'search-plan':
            sub.add_argument('--query', required=True)
            sub.add_argument('--cycle')
    rec = subs.add_parser('record')
    rec.add_argument('--track', choices=TRACKS, help="Pin this chat's selected track; defaults to the saved active track.")
    rec.add_argument('--file', type=Path, required=True)
    rec.add_argument('--user-confirmed', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'init':
            track = args.track
            if not track:
                print('Which application path would you like to use?')
                for n, (key, label) in enumerate(TRACKS.items(), 1):
                    print(f'{n}. {label} ({key})')
                if not sys.stdin.isatty():
                    print('Select explicitly with init --track industry|graduate|academia.')
                    return 2
                answer = input('Choice: ').strip()
                track = dict(zip(('1', '2', '3'), TRACKS)).get(answer, answer)
                if track not in TRACKS:
                    raise ValueError('Choose 1, 2, 3 or a valid track name.')
            result = initialize(args.workspace, track)
        elif args.command == 'status':
            result = profile(args.workspace)
        else:
            track = getattr(args, 'track', None) or profile(args.workspace)['active_track']
            if args.command == 'record':
                result = record(args.workspace, track, read_json(args.file), args.user_confirmed)
            else:
                result = source_plan(track, getattr(args, 'query', None), getattr(args, 'cycle', None))
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, OSError, EOFError) as exc:
        print(f'career: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
