## What Changed

Describe the user-visible behavior, command, report, template, packaging, or documentation change.

## Verification

Paste the commands you ran and the final status:

```bash
python3 -m py_compile falsiflow/core.py falsiflow/cli.py falsiflow/adapters.py falsiflow/casebook_check.py scripts/falsiflow.py scripts/falsiflow_tests/regress_falsiflow_core.py
python3 scripts/falsiflow_tests/regress_falsiflow_core.py
falsiflow adoption-check --out-dir data/falsiflow/adoption_check --force
falsiflow release-check --out-dir data/falsiflow/release_check --force
```

## Evidence Boundary

- [ ] This change does not make `claim_ready` bypass missing provenance, placeholder evidence, malformed configuration, or failed gates.
- [ ] New public commands or JSON fields are documented and covered by tests or release-check expectations.
- [ ] Template distribution changes were checked with `template-check`, `template-pack`, `verify-template-pack`, `template-release`, `verify-template-release`, and `template-install` where applicable.
- [ ] Security-sensitive changes preserve bundle verification, SHA-256 integrity, path handling, and source-file provenance.
- [ ] Responsible use remains clear: Falsiflow readiness is not proof of safety, efficacy, regulatory compliance, or experimental truth.

## Release Impact

- [ ] `CHANGELOG.md`, `README.md`, `RELEASE.md`, `SECURITY.md`, or `RESPONSIBLE_USE.md` were updated when relevant.
- [ ] `adoption-check` and `release-check` pass, or this PR explains why they cannot run in the current environment.
