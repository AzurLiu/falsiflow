## What Changed

Describe the user-visible change to `falsiflow check`, the GitHub Action, reports, packaging, or docs.

## Verification

Paste the commands you ran and the final status:

```bash
python3 -m py_compile falsiflow/core.py falsiflow/bundle.py falsiflow/claim_check.py falsiflow/cli.py scripts/falsiflow.py scripts/falsiflow_tests/regress_falsiflow_core.py
python3 scripts/falsiflow_tests/regress_falsiflow_core.py
python3 -m build
python3 -m twine check dist/*
```

## Evidence Boundary

- [ ] This change does not let `claim_ready` bypass missing provenance, placeholder evidence, malformed config, failed thresholds, or bundle verification.
- [ ] New public CLI or Action behavior is covered by a regression test or smoke check.
- [ ] The public surface remains limited to `check` and `schema`; compatibility aliases stay hidden.
- [ ] Shared artifacts and logs do not include secrets, credentials, or private raw data.

## Release Impact

- [ ] `README.md`, `CHANGELOG.md`, `SECURITY.md`, or `CONTRIBUTING.md` were updated when relevant.
- [ ] This PR does not reintroduce launch, demo, discovery, MCP, template marketplace, or release/adoption automation systems.
