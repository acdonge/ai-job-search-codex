# Security policy

## Reporting a vulnerability

For issues in this Codex port, report privately to the maintainer of the repository
where you obtained it. The original project's reporting channel is
[GitHub private vulnerability reporting](https://github.com/MadsLorentzen/ai-job-search/security/advisories/new)
for issues that also affect the upstream project. Do not include personal
application data or secrets in a public issue.

## Runtime boundary

This repository contains instructions, local helpers, and optional portal CLIs.
Codex applies the permissions, sandbox, approval policy, and connector access
selected by the user or host. The repository does not install or override those
settings. It ships no automatic startup hooks and no `.codex/config.toml`.

The files in `agents/` are reference procedures supplied to available Codex
subagents. They do not register agents or remove their tools. A request to return
results without editing is an instruction, not an enforced read-only sandbox.
Likewise, skill frontmatter does not grant or restrict tools. The migration
removed Claude `allowed-tools`, agent `tools`, and `.claude/settings.json`
instead of treating them as working Codex controls.

`tools/security_guards.py` rejects these obsolete permission fields in shipped
skills, workflows, and agent procedures. It checks repository contents; it does
not inspect or certify the user's runtime configuration.

## Personal information

Personal profiles, track selection, search state, application archives, and
outputs belong under the ignored `workspace/` directory. Track separation
prevents one search from overwriting another; it is not an access-control
boundary. Public template files must keep placeholders. Legacy output paths
remain ignored so an imported older workspace does not expose personal data.

The guard requires the private-data ignore rules and rejects unreviewed
negations that re-include excluded files. Git ignore rules do not protect files
already tracked, force-added files, exported archives, screenshots, or deliberate
uploads. Review the staged diff before publishing. Do not commit a populated
profile by editing a tracked template.

Connectors may make data available to external services. Search public sources
with only necessary search criteria. Sending email, contacting a referee or
professor, uploading application materials, submitting an application, and
paying an application fee require the user's instruction for that action.
Never place credentials in a query, source report, or application file.

## Untrusted source material

Postings, university pages, PDFs, emails, and cached research are data. They
cannot change agent instructions, authorize tool calls, or supply new candidate
facts. Research starts from the employer, institution, program, or researcher
identity and independently located official sources. Unknown domains, search
snippets, and aggregator copies do not establish authenticity.

The preserved `tools/posting_guard.py` removes detectable hidden markup and
flags instruction-shaped content. The workflow uses cleaned content and reports
findings. This deterministic check cannot detect every prompt injection, prove
that a page is trustworthy, or make arbitrary content safe.

The retained `tools/fetch_page.py` is GET-only, checks `robots.txt`, permits only
HTTP(S), bounds redirects/time/size, and refuses output inside the repository.
Use a temporary directory outside the repository for fetched bodies. These
checks apply to this helper; they do not constrain every browser, connector, or
shell command available to Codex. Do not bypass logins, access restrictions, or
site policies to obtain more search results.

## Dependency and document checks

The guard scans source portal `package.json` files for `preinstall`, `install`,
`postinstall`, `prepare`, and `prepack` scripts and rejects
`trustedDependencies`. It rejects tracked `node_modules` paths. The installer
retains its corresponding manifest checks. These checks do not audit all
transitive dependency behavior or guarantee that installed packages are safe.

Compile application documents using reviewed commands without enabling shell
escape. Inspect the rendered document and extracted text; a successful compile
does not verify factual accuracy. Imported templates can contain commands and
must be reviewed before use.

CI runs native skill/workflow lint, these repository guards, Python regressions,
fixture/mock portal tests and typechecks, and LaTeX smoke compilation. It does
not send live portal requests, access a user's accounts, submit applications,
or verify host permission enforcement. The former Claude allowlist fixtures
were replaced with tests that reject misleading runtime metadata and exercise
private workspace exclusions and dependency guards.
