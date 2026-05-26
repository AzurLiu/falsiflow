# Falsiflow Troubleshooting

Use this page when a command exits non-zero, a claim is blocked, or a release
gate reports that more evidence is needed. Falsiflow is conservative by design:
most failures are meant to preserve the project directory and point to the next
repair command.

## Fast Triage

Start with the project doctor when a generated or existing project is not ready:

```bash
falsiflow doctor --project-dir my_falsiflow_project --strict
```

Then inspect:

- `doctor/doctor_summary.json`
- `doctor/doctor_summary.md`
- `doctor/project_validation.json`
- `doctor/evidence_diagnostics.json`
- `claim_check/claim_check.json`
- `claim_check/claim_check.md`

Look for `repair_checklist`, `next_commands`, `next_actions`, and the first
blocked stage. Those fields name the next command, expected artifact, and
success signal.

## Install Or Start Fails

Check the Python version first. Falsiflow expects Python `>=3.10`.

```bash
python3 --version
python3 -m pip install -e .
falsiflow selftest
```

For the local browser entry point, prefer the maintained shortcuts:

```bash
make install-local
make start
```

If the local app directory already has generated files, reset it:

```bash
falsiflow start --reset
```

For CI or scripted checks, avoid leaving a server running:

```bash
falsiflow start --check --json
```

## `claim_check_blocked`

`claim_check_blocked` means the project was preserved and the claim did not earn
readiness. Common causes are:

- placeholder values such as `TBD`, `unknown`, `placeholder`, or blank values
- missing required evidence rows
- blank required metadata fields
- missing `source_file` references or raw source files
- duplicate evidence keys for the same gate, candidate, sample, and field
- malformed evidence CSV headers
- failed acceptance rules or derived metrics

Run:

```bash
falsiflow doctor --project-dir my_falsiflow_project --strict
falsiflow claim-check --project-dir my_falsiflow_project --strict --force
```

Then fill the first missing evidence row or source file named in
`repair_checklist` or `next_actions.json`. Do not edit reports to force
`claim_ready`; the source-backed evidence needs to change.

## `doctor_blocked`

`doctor_blocked` usually means the project config, evidence CSV, source files,
or claim check failed before the full review path was ready.

Useful recovery order:

```bash
falsiflow validate --config my_falsiflow_project/project.json --strict
falsiflow coverage --config my_falsiflow_project/project.json --evidence my_falsiflow_project/evidence.csv --strict
falsiflow doctor --project-dir my_falsiflow_project --strict
```

If `project_validation.json` names an unsupported operator, invalid gate, or
missing claim requirement, fix `project.json` before editing evidence rows.

## Template Checks Fail

`template_blocked` or `template_install_blocked` means the starter template is
not safe to share or adopt yet.

Run the authoring and verification path:

```bash
falsiflow template-check --template-dir my_template --strict
falsiflow template-pack --template-dir my_template --out my_template.zip --force
falsiflow verify-template-pack --bundle my_template.zip --strict
```

For a reusable template, the passing demo must become `claim_ready` and the
placeholder demo must remain blocked. If placeholder evidence passes, tighten
the gate, required fields, placeholder markers, or source-file policy.

For distributed templates, also verify registry, lockfile, attestation, policy,
release, and install artifacts:

```bash
falsiflow template-release --template-dir my_template --out template_release.zip --force
falsiflow verify-template-release --release template_release.zip --strict --report-out template_release_verification.md
falsiflow template-install --release template_release.zip --out-dir installed_templates --require-attestation
```

Unsafe archive paths, hash mismatches, duplicate artifact paths, or
unmanifested files should stay blocked.

## `release_blocked` Or `dist_blocked`

Use `--skip-dist` only for a fast docs or metadata loop:

```bash
falsiflow release-check --out-dir data/falsiflow/release_check --skip-dist --force
```

Before a release-facing change, run the full gate:

```bash
rm -rf build falsiflow.egg-info data/falsiflow/release_check
falsiflow release-check --out-dir data/falsiflow/release_check --force
```

Avoid running two full distribution checks at the same time in one checkout.
They both build wheels and sdists, so parallel runs can compete for `build/`.

Inspect:

- `release_check.json`
- `release_check.md`
- `dist/wheel/*.whl`
- `dist/sdist/*.tar.gz`
- `dist/installed_release_check/release_check.json`

The full gate should finish with `release_ready`, `package_ready`, `dist_ready`,
and `release_validation_ready` for local release validation.

## `external_blocked`

`external_blocked` is expected before public account-bound evidence exists. A
local release can be ready while external readiness waits on:

- public repository URL
- hosted demo URL
- public PyPI package URL
- checkout-based pipx smoke evidence
- public-package pipx smoke evidence
- Windows/PowerShell smoke evidence
- the `Falsiflow External Evidence` workflow artifact
- `public_release_evidence.md` from `falsiflow publish-kit`

After publishing the repository and demo, write or collect structured evidence:

```bash
falsiflow external-evidence --out falsiflow_external_evidence.json --force
falsiflow external-check --out-dir falsiflow_external_check --evidence falsiflow_external_evidence.json --strict --force
```

Only call the public launch externally ready after `external-check --strict`
reports `external_ready`.

## When To Open An Issue

Open an issue when the repair checklist is unclear, a valid-looking project is
blocked without a concrete next action, or a verifier accepts an unsafe bundle,
template, or release artifact.

Include:

- the exact command
- operating system and Python version
- Falsiflow version or commit
- the relevant JSON report, such as `doctor_summary.json`,
  `claim_check.json`, `external_readiness.json`, or `release_check.json`
- whether the issue uses bundled demo data or private evidence

Do not attach private lab data, credentials, proprietary vendor replies, or
sensitive source files to public issues. See [../SUPPORT.md](../SUPPORT.md) and
[../SECURITY.md](../SECURITY.md) for routing.
