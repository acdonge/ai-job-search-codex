#!/usr/bin/env python3
"""Render every recorded career lead as deterministic, self-contained HTML.

This module does not search, assess, mutate state, or perform file/network I/O.
The pipeline validates assessments; this view also fails closed on count mismatches.
"""
from base64 import b64encode
from hashlib import sha256
from html import escape
from urllib.parse import urlsplit


TRACKS = {'industry': 'US industry jobs', 'graduate': 'US MS/PhD admissions',
          'academia': 'US academic jobs'}
DISPOSITIONS = ('eligible', 'provisional', 'excluded', 'closed', 'unreachable',
                'duplicate', 'out_of_scope', 'pending')
NEXT_STEPS = {
    'eligible': 'Review the evidence and application requirements before applying.',
    'provisional': 'Resolve the VERIFY gates and unknown dimensions before deciding.',
    'excluded': 'Review the failed gate and exclusion reason.',
    'closed': 'Retain this record; confirm a new opening before applying.',
    'unreachable': 'Retry the official source and record the access result.',
    'duplicate': 'Review the linked original record; keep this discovery in the ledger.',
    'out_of_scope': 'Review the user-defined scope exclusion.',
    'pending': 'Complete the evidence, gates, and assessment before finishing this run.',
}

# Static assets contain no interpolated user data. Their hashes allow a strict CSP
# while keeping the report portable as a single local file.
STYLE = '''
:root{color-scheme:light;--ink:#172c36;--muted:#4b606b;--line:#d4dfe3;--accent:#135a6d;--paper:#fff;--wash:#f4f7f8}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--accent);text-underline-offset:3px;overflow-wrap:anywhere}a:hover{color:#093e4c}
main{max-width:1560px;margin:auto;padding:40px 36px 64px}header{border-bottom:2px solid var(--ink);padding-bottom:24px}
.eyebrow{font-size:.76rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 6px}
h1{font-size:clamp(1.8rem,4vw,2.7rem);font-weight:650;letter-spacing:-.04em;line-height:1.15;margin:0 0 12px}
h2{font-size:1.2rem;font-weight:650;letter-spacing:-.02em;margin:0 0 12px}h3{font-size:1rem;margin:18px 0 6px}p{margin:8px 0}
.muted,.meta{color:var(--muted);font-size:.86rem}.meta{display:block;overflow-wrap:anywhere}.query{font-size:1.05rem;max-width:90ch}
.status{padding:18px 0;border-bottom:1px solid var(--line)}.status strong{font-size:.85rem;letter-spacing:.06em}.status.incomplete{border-left:4px solid #9b5408;padding-left:16px;background:#fffaf3}
.status ul{margin:8px 0 0;padding-left:20px}.stats{display:flex;gap:22px;flex-wrap:wrap;margin:24px 0;padding:0}.stats div{min-width:100px}
.stats dt{font-size:.76rem;color:var(--muted)}.stats dd{font-variant-numeric:tabular-nums;font-size:1.6rem;font-weight:600;margin:0}
.toolbar{display:flex;align-items:end;gap:14px;flex-wrap:wrap;padding:16px 0}.field{display:flex;flex-direction:column;gap:5px}.field.search{flex:1;min-width:220px}
label{font-size:.8rem;font-weight:600}input,select,button{font:inherit;padding:9px 12px;border:1px solid #9dafb7;border-radius:4px;background:#fff;color:var(--ink);min-height:42px}
button{cursor:pointer;font-weight:600}button:hover{background:var(--wash)}input:focus-visible,select:focus-visible,button:focus-visible,summary:focus-visible,a:focus-visible{outline:3px solid #14738e;outline-offset:3px}
.count{margin:0 0 14px;color:var(--muted);font-size:.86rem}.table-wrap{overflow-x:auto;border-top:1px solid var(--ink)}table{border-collapse:collapse;width:100%;text-align:left;table-layout:fixed;min-width:930px}
caption{text-align:left;padding:10px 0;color:var(--muted);font-size:.82rem}th{font-size:.77rem;font-weight:650;color:var(--muted);background:var(--wash)}th,td{padding:16px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th:first-child,td:first-child{padding-left:0}th:nth-child(1){width:25%}th:nth-child(2){width:13%}th:nth-child(3){width:14%}th:nth-child(4){width:15%}th:nth-child(5){width:33%}
.title{font-weight:650;font-size:1rem;line-height:1.4;margin-bottom:6px}.score{font-size:1.12rem;font-weight:650;font-variant-numeric:tabular-nums;white-space:nowrap}
.disposition{font-size:.84rem;font-weight:650;text-transform:capitalize}.gate{font-size:.83rem;font-weight:650}.reason{font-size:.86rem;overflow-wrap:anywhere}
summary{cursor:pointer;color:var(--accent);font-size:.84rem;font-weight:600}details p,details li{font-size:.85rem}details ul{padding-left:20px}.review{margin-top:12px}.review dl{margin:10px 0}.review dt{font-weight:650;font-size:.8rem;margin-top:8px}.review dd{margin:2px 0;font-size:.84rem}
.provenance{margin-top:36px;padding-top:24px;border-top:1px solid var(--line)}.context{display:grid;grid-template-columns:1fr 1fr;gap:32px}.context dl{margin:0}.context dt{font-size:.8rem;color:var(--muted);margin-top:14px}.context dd{margin:4px 0;overflow-wrap:anywhere}
.batch-list{padding-left:22px}.batch-list>li{padding:12px 0;border-bottom:1px solid var(--line)}.empty{padding:24px 0}.footer{margin-top:32px;font-size:.78rem;color:var(--muted)}[hidden]{display:none!important}
@media(max-width:700px){main{padding:24px 16px 40px}.context{grid-template-columns:1fr;gap:0}.stats{gap:16px}.stats div{min-width:85px}.toolbar{align-items:stretch}.field{flex:1}.field.search{flex-basis:100%}.stats dd{font-size:1.35rem}}
@media print{main{padding:0;max-width:none}.toolbar,.count{display:none}.table-wrap{overflow:visible}table{min-width:0;font-size:10px}th,td{padding:8px 5px}tr[hidden]{display:table-row!important}.title,.score{font-size:11px}a{color:inherit}.status{break-inside:avoid}.provenance{break-before:auto}}
'''
SCRIPT = '''
(function () {
  "use strict";
  const rows = Array.from(document.querySelectorAll("tr[data-lead-id]"));
  const text = document.getElementById("text-filter");
  const disposition = document.getElementById("disposition-filter");
  const count = document.getElementById("visible-count");
  const empty = document.getElementById("no-matches");
  function update() {
    const query = text.value.trim().toLocaleLowerCase();
    let shown = 0;
    rows.forEach(function (row) {
      const matchesText = !query || row.textContent.toLocaleLowerCase().includes(query);
      const matchesStatus = disposition.value === "all" || row.dataset.disposition === disposition.value;
      row.hidden = !(matchesText && matchesStatus);
      if (!row.hidden) shown += 1;
    });
    count.textContent = shown + " of " + rows.length + " recorded leads shown";
    empty.hidden = shown !== 0 || rows.length === 0;
  }
  text.addEventListener("input", update);
  disposition.addEventListener("change", update);
  document.getElementById("reset-filters").addEventListener("click", function () {
    text.value = "";
    disposition.value = "all";
    update();
    text.focus();
  });
  // Reset restored browser control values: every opening starts with all leads.
  text.value = "";
  disposition.value = "all";
  update();
})();
'''


def _text(value):
    return escape('' if value is None else str(value), quote=True)


def _safe_url(value):
    if not isinstance(value, str) or not value or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value) or '\\' in value:
        return False
    try:
        parsed = urlsplit(value)
        parsed.port  # Access validates invalid or out-of-range ports.
        return (parsed.scheme in ('http', 'https') and bool(parsed.hostname)
                and not parsed.username and not parsed.password)
    except ValueError:
        return False


def _link(url, label=None):
    label = _text(url if label is None else label)
    if _safe_url(url):
        return f'<a href="{_text(url)}" target="_blank" rel="noopener noreferrer">{label}</a>'
    return f'<span>{label}</span><span class="meta">Invalid or unavailable source URL</span>'


def _items(values):
    return '<ul>' + ''.join(f'<li>{_text(value)}</li>' for value in values) + '</ul>'


def _number(value, decimals=1):
    return f'{value:.{decimals}f}'


def _score_markup(assessment):
    score = assessment.get('score')
    if not score:
        label = 'Not evaluated' if assessment.get('disposition', 'pending') == 'pending' else 'Not scored'
        return f'<span class="score">{label}</span>'
    if score.get('overall') is not None:
        fit = f'{_number(score["overall"])} / 100'
    else:
        fit = f'{_number(score["lower"])}–{_number(score["upper"])}'
    coverage = format(score['coverage'], 'g')
    return (f'<span class="score">{_text(fit)}</span>'
            f'<span class="meta">{_text(coverage)}% known</span>'
            f'<span class="meta">{_text(score.get("band", ""))}</span>')


def _review_markup(assessment, disposition):
    evidence = assessment.get('evidence') or []
    details = ['<details class="review"><summary>Evidence and scoring details</summary>']
    details.append('<h3>Verification gates</h3><dl>')
    for gate in ('availability', 'eligibility', 'constraints'):
        entry = assessment.get('gates', {}).get(gate, {})
        details.append(f'<dt>{_text(gate.title())}: {_text(entry.get("verdict", "NOT ASSESSED"))}</dt>'
                       f'<dd>{_text(entry.get("reason", "No assessment recorded."))}</dd>')
    details.append('</dl><h3>Fit dimensions</h3><dl>')
    dimensions = assessment.get('dimensions') or {}
    for name, dimension in dimensions.items():
        value = dimension.get('value')
        value_text = 'Unknown' if value is None else f'{_number(value)} / 100'
        weight = (assessment.get('score') or {}).get('weights', {}).get(name)
        weight_text = '' if weight is None else f' · {_text(weight)}% weight'
        details.append(f'<dt>{_text(name.replace("_", " ").title())}: {_text(value_text)}{weight_text}</dt>'
                       f'<dd>{_text(dimension.get("reason", ""))}</dd>')
    if not dimensions:
        details.append('<dd>No fit dimensions recorded.</dd>')
    details.append('</dl><h3>Evidence</h3><ul>')
    for entry in evidence:
        details.append(f'<li>{_link(entry.get("url", ""))}'
                       f'<span class="meta">Checked {_text(entry.get("checked_on", "not recorded"))}</span>'
                       f'<p>{_text(entry.get("note", ""))}</p></li>')
    if not evidence:
        details.append('<li>No evidence recorded.</li>')
    details.append('</ul>')
    if assessment.get('duplicate_of'):
        details.append(f'<p>Duplicate of: {_text(assessment["duplicate_of"])}</p>')
    if assessment.get('scope_exclusion'):
        details.append(f'<p>Scope exclusion: {_text(assessment["scope_exclusion"])}</p>')
    details.append(f'<h3>Next step</h3><p>{_text(NEXT_STEPS.get(disposition, NEXT_STEPS["pending"]))}</p></details>')
    return ''.join(details)


def _row_markup(row):
    assessment = row.get('assessment') or {}
    disposition = assessment.get('disposition', 'pending')
    eligibility = assessment.get('gates', {}).get('eligibility') or {}
    cycle = f'<span class="meta">Cycle: {_text(row["cycle"])}</span>' if row.get('cycle') else ''
    reason = assessment.get('reason') or 'No assessment recorded; this lead must remain visible.'
    return (f'<tr data-lead-id="{_text(row["id"])}" data-disposition="{_text(disposition)}">'
            f'<td><div class="title">{_link(row.get("url", ""), row.get("title", "Untitled opportunity"))}</div>'
            f'<span>{_text(row.get("organization", ""))}</span>{cycle}'
            f'<span class="meta">ID: {_text(row["id"])}</span></td>'
            f'<td><span class="disposition">{_text(disposition.replace("_", " "))}</span></td>'
            f'<td>{_score_markup(assessment)}</td>'
            f'<td><span class="gate">{_text(eligibility.get("verdict", "NOT ASSESSED"))}</span>'
            f'<p class="reason">{_text(eligibility.get("reason", "No eligibility evidence recorded."))}</p></td>'
            f'<td><p class="reason">{_text(reason)}</p>{_review_markup(assessment, disposition)}</td></tr>')


def _reconcile(payload):
    rows = payload['rows']
    counts = payload.get('counts', {})
    scored = sum(bool(row.get('assessment') and row['assessment'].get('score')) for row in rows)
    pending = sum(not row.get('assessment') or row['assessment'].get('disposition') == 'pending' for row in rows)
    actual = {'discovered': len(rows), 'displayed': len(rows),
              'assessed': sum(row.get('assessment') is not None for row in rows),
              'scored': scored, 'unscored': len(rows) - scored, 'pending': pending}
    errors = list(payload.get('errors') or [])
    for name, value in actual.items():
        if type(counts.get(name)) is not int or counts[name] != value:
            errors.append(f'Recorded {name} count ({counts.get(name, "missing")}) does not match the {value} rendered records.')
    observations = counts.get('observations')
    if not isinstance(observations, int) or isinstance(observations, bool) or observations < len(rows):
        errors.append('Observation count is missing or smaller than the discovered lead count.')
    observed = sum(len(batch.get('results', [])) for batch in payload.get('batches', []))
    if observations != observed:
        errors.append(f'Recorded observation count does not match the {observed} batch observations.')
    for row in rows:
        assessment = row.get('assessment') or {}
        if assessment.get('disposition') in ('eligible', 'provisional') and not assessment.get('score'):
            errors.append(f'Lead {row["id"]} is missing a fit score.')
    stop = payload.get('stop') or {}
    if not stop.get('reason') or not stop.get('note'):
        errors.append('The run is missing stopping evidence.')
    if pending:
        errors.append(f'{pending} lead(s) have pending assessment.')
    if len({row['id'] for row in rows}) != len(rows):
        errors.append('Duplicate lead IDs are present in the report payload.')
    return actual, errors


def _context_markup(payload):
    scope = payload.get('scope') or {}
    stop = payload.get('stop') or {}
    sources = ''.join(f'<li>{_link(url)}</li>' for url in scope.get('source_urls', []))
    exclusions = _items(scope.get('exclusions', [])) if scope.get('exclusions') else '<p>None declared.</p>'
    limit = scope.get('user_limit')
    limit_html = (f'<dt>User-declared batch limit</dt><dd>{_text(limit.get("batches"))} batches; '
                  f'“{_text(limit.get("quote", ""))}”</dd>') if limit else ''
    context = (f'<section class="provenance" aria-labelledby="scope-heading"><h2 id="scope-heading">Search scope and provenance</h2>'
               f'<div class="context"><dl><dt>Request</dt><dd>{_text(scope.get("request", payload.get("query", "")))}</dd>'
               f'<dt>Scope mode</dt><dd>{_text(scope.get("mode", "not recorded"))}</dd>'
               f'<dt>Sources</dt><dd><ul>{sources}</ul></dd><dt>User-defined exclusions</dt><dd>{exclusions}</dd>{limit_html}</dl>'
               f'<dl><dt>Stop reason</dt><dd>{_text(stop.get("reason", "Not recorded"))}</dd>'
               f'<dt>Stop evidence</dt><dd>{_text(stop.get("note", "No stopping evidence recorded."))}</dd>'
               f'<dt>Provided identities</dt><dd>{len(scope.get("expected_leads", []))}</dd>'
               f'<dt>Provided URLs</dt><dd>{len(scope.get("expected_urls", []))}</dd></dl></div>'
               '<h3>Recorded search batches</h3><ol class="batch-list">')
    batches = []
    for batch in payload.get('batches', []):
        batches.append(f'<li>{_link(batch.get("source_url", ""))}'
                       f'<span class="meta">Checked {_text(batch.get("checked_on", "not recorded"))} · '
                       f'Access: {_text(batch.get("access", "not recorded"))} · '
                       f'{len(batch.get("results", []))} observations</span>'
                       f'<p>Query: {_text(batch.get("query", ""))}</p><p>{_text(batch.get("note", ""))}</p></li>')
    return context + ''.join(batches) + '</ol></section>'


def render_report(payload):
    """Return an offline report that displays every supplied row without a cap.

    The caller provides validated assessment records. Count or pending-state
    inconsistencies make the completion banner fail closed without hiding rows.
    """
    actual, errors = _reconcile(payload)
    complete = bool(payload.get('complete')) and not errors
    status = 'RECORDED RUN COMPLETE' if complete else 'INCOMPLETE'
    status_class = '' if complete else ' incomplete'
    error_list = _items(errors) if errors else ''
    if not complete and not errors:
        error_list = '<p>This recorded run has not passed pipeline completion checks.</p>'
    title = TRACKS.get(payload.get('track'), payload.get('track', 'Career search'))
    counts = payload.get('counts', {})
    stats = ''.join(f'<div><dt>{label}</dt><dd>{_text(counts.get(key, "—"))}</dd></div>' for key, label in (
        ('observations', 'Observations'), ('discovered', 'Discovered'), ('assessed', 'Assessed'),
        ('scored', 'Scored'), ('unscored', 'Unscored, incl. pending'), ('pending', 'Pending')))
    stats += f'<div><dt>Displayed in this report</dt><dd>{actual["displayed"]}</dd></div>'
    options = '<option value="all" selected>All dispositions</option>' + ''.join(
        f'<option value="{name}">{name.replace("_", " ").title()}</option>' for name in DISPOSITIONS)
    rows = ''.join(_row_markup(row) for row in payload['rows'])
    empty = '<p class="empty">No leads recorded.</p>' if not payload['rows'] else ''
    style_hash = b64encode(sha256(STYLE.encode('utf-8')).digest()).decode('ascii')
    script_hash = b64encode(sha256(SCRIPT.encode('utf-8')).digest()).decode('ascii')
    csp = (f"default-src 'none'; script-src 'sha256-{script_hash}'; style-src 'sha256-{style_hash}'; "
           "object-src 'none'; base-uri 'none'; form-action 'none'")
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<meta http-equiv="Content-Security-Policy" content="{_text(csp)}">'
            f'<title>{_text(title)} — complete result ledger</title><style>{STYLE}</style></head><body><main>'
            f'<header><p class="eyebrow">Career search / {_text(title)}</p><h1>All recorded opportunities</h1>'
            f'<p class="query">{_text(payload.get("query", ""))}</p>'
            f'<p class="meta">Run {_text(payload.get("run_id", ""))}</p></header>'
            f'<section id="run-status" role="status" class="status{status_class}"><strong>{status}</strong>{error_list}'
            '<p class="muted">Completion applies to this recorded run, not exhaustive market coverage. '
            'Fit does not establish application eligibility.</p></section>'
            f'<dl class="stats">{stats}</dl><section aria-labelledby="results-heading"><h2 id="results-heading">Results</h2>'
            '<p class="muted">Every discovered lead is retained, including exclusions and unavailable postings. '
            'Unknown fit dimensions remain unknown; eligibility is evaluated separately.</p>'
            '<div class="toolbar"><div class="field search"><label for="text-filter">Find in all recorded leads</label>'
            '<input id="text-filter" type="search" placeholder="Title, employer, evidence, or reason" autocomplete="off"></div>'
            '<div class="field"><label for="disposition-filter">Disposition</label>'
            f'<select id="disposition-filter">{options}</select></div>'
            '<button id="reset-filters" type="button">Reset to all</button></div>'
            f'<p id="visible-count" class="count" aria-live="polite" aria-atomic="true">{len(payload["rows"])} of '
            f'{len(payload["rows"])} recorded leads shown</p>'
            '<noscript><p>All results remain visible without JavaScript.</p></noscript>'
            '<div class="table-wrap"><table><caption>One row per recorded lead. Expand a row’s details to inspect its evidence and scoring.</caption>'
            '<thead><tr><th scope="col">Opportunity</th><th scope="col">Disposition</th><th scope="col">Fit score</th>'
            '<th scope="col">Eligibility</th><th scope="col">Reason and evidence</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>{empty}'
            '<p id="no-matches" hidden>No leads match these filters. Use “Reset to all” to restore every result.</p></section>'
            f'{_context_markup(payload)}<p class="footer">Private report · self-contained HTML · no external assets</p>'
            f'</main><script>{SCRIPT}</script></body></html>\n')
