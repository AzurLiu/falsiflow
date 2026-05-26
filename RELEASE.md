# Falsiflow Release Checklist

Use this checklist before tagging or publishing a Falsiflow release.

## Preflight

1. Confirm the version in [pyproject.toml](pyproject.toml) matches
   [falsiflow/__init__.py](falsiflow/__init__.py).
2. Update [CHANGELOG.md](CHANGELOG.md) for the release version.
3. Confirm [README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md), and
   [docs/falsiflow_mvp.md](docs/falsiflow_mvp.md) describe any new public
   commands, schemas, or release gates.
4. Confirm [scripts/install_local.sh](scripts/install_local.sh),
   [scripts/install_local.ps1](scripts/install_local.ps1), and
   [Makefile](Makefile) still install and launch the local browser app.
5. Confirm [docs/falsiflow_adoption_priorities.md](docs/falsiflow_adoption_priorities.md)
   still matches the current optimization priorities.
6. Confirm [SECURITY.md](SECURITY.md) and
   [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md) still match the release behavior and
   evidence-boundary language.

## Required Gates

```bash
python3 -m py_compile \
  falsiflow/core.py \
  falsiflow/cli.py \
  falsiflow/adapters.py \
  scripts/falsiflow.py \
  scripts/falsiflow_tests/regress_falsiflow_core.py

python3 scripts/falsiflow_tests/regress_falsiflow_core.py
scripts/install_local.sh --from-local . --prefix /tmp/falsiflow_install_check --check
python3 scripts/falsiflow.py onboard --out-dir /tmp/falsiflow_onboard_check --check --json
python3 scripts/falsiflow.py static-demo --out-dir /tmp/falsiflow_static_demo_check --force --json
python3 scripts/falsiflow.py demo-package --out-dir /tmp/falsiflow_public_demo_check --force --json
python3 scripts/falsiflow.py publish-kit --out-dir /tmp/falsiflow_publish_kit_check --force --json
python3 scripts/falsiflow.py external-check --out-dir /tmp/falsiflow_external_check --force
python3 scripts/falsiflow.py adoption-check --out-dir data/falsiflow/adoption_check --force
python3 scripts/falsiflow.py release-check --out-dir data/falsiflow/release_check --force
```

The final `release-check` must report:

- `release_ready`
- `package_ready`
- `adoption_ready`
- `release_validation_ready`
- `dist_ready`
- `demo_package_ready`
- `publish_kit_ready` for the generated release handoff kit
- `external_check_status` is `external_ready` for a public release, or
  `external_blocked` only while public repo/demo URLs, pipx, or Windows
  validation are intentionally pending
- zero package failures
- zero dist failures
- one-command `quickstart` reports `quickstart_ready`
- `quickstart_summary.json` includes doctor handoff `next_commands`
- one-command `doctor --project-dir` reports `doctor_ready`
- `doctor_summary.json` includes a `repair_checklist`
- one-command `claim-check --project-dir` reports `claim_check_ready`
- audit review decision cards generated and bundled
- all starter bundles verified
- template gallery ready with the bundled cross-domain starters
- packaged starter template pack verified
- template registry ready and template lock written
- registry `source_url` and lockfile SHA-256 source pin verified
- packaged starter template pack installed with `template_installed`
- template release bundle verified with `template_release_verified`
- packaged starter template release installed with `template_installed`
- `adoption_check.json` reports all five priorities ready
- `adoption_check.json` includes a `repair_checklist` command with expected
  artifact and success signal
- local build caches such as `build/` and `falsiflow.egg-info/` are not left
  behind by the distribution gate
- zero unsafe paths, unmanifested files, or registry/lock SHA-256 mismatches in
  the template release verification report
- GitHub Actions workflow files exist for full CI, GitHub Pages demo deploy,
  cross-platform Windows/macOS/Linux smoke tests, pipx smoke tests, and PyPI
  trusted-publishing release builds

## Artifact Review

Inspect these generated files before publishing:

- `data/falsiflow/release_check/release_check.json`
- `data/falsiflow/release_check/release_check.md`
- `data/falsiflow/release_check/public_demo/demo_package_summary.json`
- `data/falsiflow/release_check/public_demo/publish_checklist.md`
- `data/falsiflow/publish_kit/publish_handoff.json`
- `data/falsiflow/publish_kit/github_publish_commands.sh`
- `data/falsiflow/release_check/external_readiness/external_readiness.json`
- `data/falsiflow/release_check/external_readiness/external_readiness.md`
- `data/falsiflow/release_check/adoption_check.json`
- `data/falsiflow/release_check/adoption_check.md`
- `data/falsiflow/adoption_check/adoption_check.json`
- `data/falsiflow/adoption_check/adoption_check.md`
- `data/falsiflow/release_check/quickstart_project/quickstart_summary.json`
- `data/falsiflow/release_check/quickstart_project/quickstart_summary.md`
- `data/falsiflow/release_check/doctor/doctor_summary.json`
- `data/falsiflow/release_check/doctor/doctor_summary.md`
- `data/falsiflow/release_check/doctor/project_validation.json`
- `data/falsiflow/release_check/doctor/evidence_diagnostics.json`
- `data/falsiflow/release_check/claim_check/claim_check.json`
- `data/falsiflow/release_check/claim_check/claim_check.md`
- `data/falsiflow/release_check/claim_check/evidence_bundle_verify.md`
- `data/falsiflow/release_check/demo/audit/audit_review.json`
- `data/falsiflow/release_check/demo/audit/audit_review.md`
- `data/falsiflow/release_check/template_gallery.json`
- `data/falsiflow/release_check/template_gallery.md`
- `data/falsiflow/release_check/template_pack.zip`
- `data/falsiflow/release_check/template_pack_verification.md`
- `data/falsiflow/release_check/template_registry.json`
- `data/falsiflow/release_check/falsiflow_template_lock.json`
- `data/falsiflow/release_check/falsiflow_template_lock.attestation.json`
- `data/falsiflow/release_check/falsiflow_template_policy.json`
- `data/falsiflow/release_check/template_release.zip`
- `data/falsiflow/release_check/template_release_verification.json`
- `data/falsiflow/release_check/template_release_verification.md`
- `data/falsiflow/release_check/template_install_templates/falsiflow_template_index.json`
- `data/falsiflow/release_check/dist/wheel/*.whl`
- `data/falsiflow/release_check/dist/sdist/*.tar.gz`

The wheel must install in isolation and pass installed-package `release-check`.
The sdist must include release docs, package modules, and starter template data.
Security and responsible-use docs must be present in the sdist.
