# Falsiflow Support

Falsiflow support is focused on helping users reproduce command behavior,
understand ready/blocked reports, and adopt starter templates safely.

Before opening an issue, check
[docs/falsiflow_troubleshooting.md](docs/falsiflow_troubleshooting.md) for the
common recovery path for install failures, `claim_check_blocked`,
`doctor_blocked`, template verification failures, `release_blocked`, and
`external_blocked`.

## Good Support Requests

Open an issue when you can share:

- the exact command you ran
- operating system and Python version
- Falsiflow version or commit
- the relevant `claim_check.json`, `doctor_summary.json`,
  `external_readiness.json`, or `release_check.json`
- the `repair_checklist`, `next_commands`, or `next_actions` entry you followed
- whether the issue uses bundled demo data or private evidence

Do not attach private lab data, credentials, proprietary vendor replies, or
sensitive source files to public issues. Use sanitized fixtures or describe the
shape of the evidence instead.

## Where To Ask

- Bugs: use `.github/ISSUE_TEMPLATE/bug_report.yml`.
- Feature requests: use `.github/ISSUE_TEMPLATE/feature_request.yml`.
- Claim-gate or template requests: use
  `.github/ISSUE_TEMPLATE/claim_gate_request.yml`.
- Security issues: follow `SECURITY.md`.
- Conduct issues: follow `CODE_OF_CONDUCT.md`.

## What Maintainers Can Help With

- reproducing CLI failures
- interpreting blocked readiness reports
- improving docs, templates, schemas, or release gates
- triaging template supply-chain verification issues
- identifying whether a request belongs in Falsiflow or in an ELN/LIMS,
  spreadsheet, CI suite, or workflow orchestrator

## What Maintainers Cannot Provide

Maintainers cannot validate scientific truth, regulatory compliance, medical
safety, commercial readiness, or private experimental conclusions. Falsiflow can
audit supplied evidence against configured gates; independent expert review is
still required for high-risk decisions.
