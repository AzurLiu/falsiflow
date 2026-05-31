# Falsiflow Release Checklist

Use this checklist before tagging or publishing a Falsiflow release.

## Preflight

1. Confirm the version in [pyproject.toml](pyproject.toml) matches
   [falsiflow/__init__.py](falsiflow/__init__.py).
2. Update [CHANGELOG.md](CHANGELOG.md) for the release version.
3. Confirm the PyPI package metadata in [pyproject.toml](pyproject.toml):
   `requires-python`, keywords, classifiers, and project URLs for homepage,
   docs, source, issues, changelog, demo, architecture, data contract,
   casebook check, citation, and governance.
4. Confirm [README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md),
   [CITATION.cff](CITATION.cff), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md),
   [GOVERNANCE.md](GOVERNANCE.md), [SUPPORT.md](SUPPORT.md),
   [ROADMAP.md](ROADMAP.md), and
   [docs/falsiflow_architecture.md](docs/falsiflow_architecture.md) plus
   [docs/falsiflow_data_contract.md](docs/falsiflow_data_contract.md),
   [docs/falsiflow_adapter_profiles.md](docs/falsiflow_adapter_profiles.md),
   [docs/falsiflow_mcp.md](docs/falsiflow_mcp.md),
   [docs/falsiflow_casebook_check.md](docs/falsiflow_casebook_check.md),
   [docs/falsiflow_security_posture.md](docs/falsiflow_security_posture.md),
   [docs/falsiflow_template_authoring.md](docs/falsiflow_template_authoring.md),
   [docs/falsiflow_troubleshooting.md](docs/falsiflow_troubleshooting.md),
   and [docs/falsiflow_1k_launch_plan.md](docs/falsiflow_1k_launch_plan.md)
   describe the current citation, community, governance, security,
   architecture, data contract, adapter profiles, MCP agent boundary, casebook
   proof, template authoring, troubleshooting, launch, supply-chain, and
   release posture.
5. Confirm [SECURITY.md](SECURITY.md) and
   [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md) still match the release behavior and
   evidence-boundary language.
6. Confirm `.github/dependabot.yml` still tracks GitHub Actions and Python
   packaging inputs, and `.github/workflows/falsiflow-scorecard.yml` still runs
   OpenSSF Scorecard with SARIF upload.
7. Confirm [scripts/install_local.sh](scripts/install_local.sh),
   [scripts/install_local.ps1](scripts/install_local.ps1), and
   [Makefile](Makefile) still install and launch the local browser app.
8. Confirm [action.yml](action.yml) still exposes the reusable GitHub Action
   for `claim-check`, `template-check`, `casebook-check`, `release-check`,
   `adoption-check`, `quickstart`, and `external-check` modes.
9. Confirm [docs/falsiflow_adoption_priorities.md](docs/falsiflow_adoption_priorities.md)
   still matches the current optimization priorities.
10. Confirm
   [docs/falsiflow_mvp.md](docs/falsiflow_mvp.md) describe any new public
   commands, schemas, community expectations, support boundaries, roadmap
   direction, security posture, or release gates.

## Required Gates

```bash
python3 -m py_compile \
  falsiflow/core.py \
  falsiflow/cli.py \
  falsiflow/adapters.py \
  falsiflow/api.py \
  falsiflow/mcp_server.py \
  falsiflow/release.py \
  falsiflow/adoption.py \
  falsiflow/casebook_check.py \
  falsiflow/bundle.py \
  falsiflow/browser_demo.py \
  falsiflow/demo.py \
  falsiflow/discovery.py \
  falsiflow/local_server.py \
  falsiflow/public_release.py \
  falsiflow/claim_check.py \
  falsiflow/doctor.py \
  falsiflow/quickstart.py \
  falsiflow/scaffold.py \
  falsiflow/template_discovery.py \
  falsiflow/template_gallery.py \
  falsiflow/template_check.py \
  falsiflow/template_pack.py \
  falsiflow/template_registry.py \
  falsiflow/template_provenance.py \
  falsiflow/template_release.py \
  falsiflow/template_install.py \
  scripts/falsiflow.py \
  scripts/falsiflow_tests/regress_falsiflow_core.py

python3 scripts/falsiflow_tests/regress_falsiflow_core.py
python3 scripts/falsiflow.py mcp --selftest --json
scripts/install_local.sh --from-local . --prefix /tmp/falsiflow_install_check --check
python3 scripts/falsiflow.py onboard --out-dir /tmp/falsiflow_onboard_check --check --json
python3 scripts/falsiflow.py static-demo --out-dir /tmp/falsiflow_static_demo_check --force --json
python3 scripts/falsiflow.py demo-package --out-dir /tmp/falsiflow_public_demo_check --force --json
python3 scripts/falsiflow.py publish-kit --out-dir /tmp/falsiflow_publish_kit_check --force --json
python3 scripts/falsiflow.py launch-kit --out-dir /tmp/falsiflow_launch_kit_check --force --json
python3 scripts/falsiflow.py external-evidence --out /tmp/falsiflow_external_evidence.json --force --json
python3 scripts/falsiflow.py external-check --out-dir /tmp/falsiflow_external_check --force
python3 scripts/falsiflow.py evidence import --profile local-llm-eval --input examples/local_llm_eval_import/falsiflow_local_llm_eval/source_files/local_eval_results.jsonl --manifest examples/local_llm_eval_import/falsiflow_local_llm_eval/local_model_manifest.json --out /tmp/falsiflow_local_llm_evidence.csv --summary-out /tmp/falsiflow_local_llm_import_summary.json --config examples/local_llm_eval_import/falsiflow_local_llm_eval/project.json --coverage-out /tmp/falsiflow_local_llm_import_coverage.json --source-file source_files/local_eval_results.jsonl --strict --json
python3 scripts/falsiflow.py casebook-check --out-dir data/falsiflow/casebook_check --force
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
- `launch_kit_ready` for public copy, proof card, demo script, launch metrics,
  and maintainer checklist
- `downstream_smoke_replay_ready`, proving the maintained downstream AI eval,
  product metric, and RAG eval fixtures replay as placeholder
  `claim_check_blocked` and source-backed `claim_check_ready` with
  `bundle_verified` from `examples/downstream_ai_eval_smoke`,
  `examples/downstream_product_metric_smoke`, and
  `examples/downstream_rag_eval_smoke`
- reusable `action.yml` supports `evidence-import`, and
  `examples/local_llm_eval_import` proves a local/private model JSONL plus
  `local_model_manifest.json` can move from `claim_check_blocked` to
  `coverage_ready` and `claim_check_ready` without Falsiflow running a model or
  opening an API port
- `external-evidence` has produced a structured evidence file for hosted demo,
  public PyPI package URL, checkout-based pipx smoke, public-package pipx
  smoke, public-package first-run quickstart/doctor, public-package MCP selftest,
  public-package claim-check, public-package first-run and MCP selftest proof,
  Windows/PowerShell smoke results, the expected PyPI package version,
  and the PyPI JSON API response
- the `Falsiflow External Evidence` workflow artifact includes
  `falsiflow_external_evidence.json`, `falsiflow_pypi_project.json`,
  `falsiflow_expected_version.txt`, `falsiflow_pypi_version.txt`,
  `falsiflow_public_package_first_run_quickstart.json`,
  `falsiflow_public_package_first_run_doctor.json`,
  `falsiflow_public_package_claim_check.json`,
  `falsiflow_public_package_mcp_selftest.json`,
  `external_readiness.json`, and `external_readiness.md` for the final public
  demo URL and PyPI package; the PyPI JSON `published_version` must match the
  workflow `expected_version` input or the version in `pyproject.toml`
- after downloading the `falsiflow-external-evidence` workflow artifact, run
  `falsiflow release-proof --evidence falsiflow_external_evidence.json --readiness falsiflow_external_check/external_readiness.json --out release_proof.md`
  to generate a release-note proof snippet. The snippet must include the exact
  External Evidence run URL, `pypi_version_match=passed`,
  `public_package_claim_check=passed`, `claim_check_ready`,
  `bundle_verified`, and `external_ready`.
- `external_check_status` is `external_ready` for a public release, or
  `external_blocked` only while public repo/demo/PyPI URLs, pipx public-package
  smoke, public-package first-run quickstart/doctor, public-package claim-check,
  public-package MCP selftest, or Windows validation are intentionally pending
- if PyPI returns `invalid-publisher`, the maintainer has followed
  [docs/falsiflow_pypi_trusted_publishing.md](docs/falsiflow_pypi_trusted_publishing.md)
  and configured the pending publisher or existing-project trusted publisher
  with project `falsiflow`, owner `AzurLiu`, repository `falsiflow`, workflow
  `falsiflow-publish.yml`, and environment `pypi`
- zero package failures
- zero dist failures
- one-command `quickstart` reports `quickstart_ready`
- `quickstart_summary.json` includes doctor handoff `next_commands`
- one-command `doctor --project-dir` reports `doctor_ready`
- `doctor_summary.json` includes a `repair_checklist`
- one-command `claim-check --project-dir` reports `claim_check_ready`
- `mcp --selftest --json` reports `mcp_selftest_ready`, lists the local
  claim/bundle/blocker/todo tools, lists local resources, runs a source-backed
  bundled claim check, verifies its bundle, and reads the blocker context
- audit review decision cards generated and bundled
- all starter bundles verified
- template gallery ready with the bundled cross-domain starters
- `casebook_check_ready` with positive demo proofs, placeholder blockers, source
  provenance, verified bundles, and reviewer replay scripts across bundled
  starters
- packaged starter template pack verified
- template registry ready and template lock written
- registry `source_url` and lockfile SHA-256 source pin verified
- packaged starter template pack installed with `template_installed`
- template release bundle verified with `template_release_verified`
- packaged starter template release installed with `template_installed`
- `adoption_check.json` reports all five priorities ready
- `adoption_check.json` includes a `repair_checklist` command with expected
  artifact and success signal
- PyPI metadata declares `requires-python`, discovery keywords, audience/topic
  classifiers, and project URLs for homepage, docs, source, issues, changelog,
  demo, architecture, data contract, adapter profiles, casebook check, citation,
  and governance
- architecture documentation is present:
  `docs/falsiflow_architecture.md`
- data contract documentation is present:
  `docs/falsiflow_data_contract.md`
- adapter profile documentation is present:
  `docs/falsiflow_adapter_profiles.md`
- casebook-check documentation is present:
  `docs/falsiflow_casebook_check.md`
- template authoring documentation is present:
  `docs/falsiflow_template_authoring.md`
- troubleshooting documentation is present:
  `docs/falsiflow_troubleshooting.md`
- community trust files are present: `CODE_OF_CONDUCT.md`, `SUPPORT.md`, and
  `ROADMAP.md`
- citation and governance files are present: `CITATION.cff` and
  `GOVERNANCE.md`
- security posture files and automation are present: `SECURITY.md`,
  `docs/falsiflow_security_posture.md`, `.github/dependabot.yml`, and the
  `Falsiflow Scorecard` workflow with SARIF upload
- local build caches such as `build/` and `falsiflow.egg-info/` are not left
  behind by the distribution gate
- zero unsafe paths, unmanifested files, or registry/lock SHA-256 mismatches in
  the template release verification report
- GitHub Actions workflow files exist for full CI, GitHub Pages demo deploy,
  cross-platform Windows/macOS/Linux smoke tests, pipx smoke tests, external
  evidence artifact capture with PyPI JSON expected-version verification,
  OpenSSF Scorecard
  reporting, and PyPI trusted-publishing release builds
- `action.yml` exists for downstream GitHub Actions adoption and the main CI
  workflow runs a reusable-action quickstart smoke

## Artifact Review

Inspect these generated files before publishing:

- `data/falsiflow/release_check/release_check.md`, especially the
  `Release Review Artifact Index` linking claim-check, source manifest, bundle
  verification, evidence bundle, and template release verification artifacts
- `data/falsiflow/release_check/release_check.json`
- `data/falsiflow/release_check/release_check.md`
- `data/falsiflow/release_check/public_demo/demo_package_summary.json`
- `data/falsiflow/release_check/public_demo/publish_checklist.md`
- `data/falsiflow/publish_kit/publish_handoff.json`
- `data/falsiflow/publish_kit/github_publish_commands.sh`
- `data/falsiflow/release_check/publish_kit/public_release_evidence.json`
- `data/falsiflow/release_check/publish_kit/public_release_evidence.md`
- `data/falsiflow/release_check/publish_kit/release_rehearsal.json`
- `data/falsiflow/release_check/publish_kit/release_rehearsal.md`
  for the public release rehearsal commands, expected artifacts, success
  signals, and strict external stop conditions
- `data/falsiflow/release_check/launch_kit/launch_summary.json`
- `data/falsiflow/release_check/launch_kit/proof_card.md`
- `data/falsiflow/release_check/launch_kit/announcement.md`
- `data/falsiflow/release_check/launch_kit/demo_script.md`
- `data/falsiflow/release_check/launch_kit/readme_proof_strip.svg`
- `data/falsiflow/release_check/launch_kit/social_preview.png`
- `data/falsiflow/release_check/launch_kit/social_preview.svg`
- `data/falsiflow/release_check/launch_kit/github_repo_profile.md`
- `data/falsiflow/release_check/launch_kit/launch_posts.md`
- `data/falsiflow/release_check/launch_kit/launch_metrics.json`
- `data/falsiflow/release_check/launch_kit/launch_metrics.md`
- `data/falsiflow/release_check/launch_kit/maintainer_checklist.md`
- `data/falsiflow/release_check/launch_kit/publish_kit/public_release_evidence.md`
- `data/falsiflow/release_check/launch_kit/publish_kit/release_rehearsal.md`
- `data/falsiflow/release_check/publish_kit/external_evidence_template.json`
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
- the `Review Artifact Index` sections in `claim_check.md`,
  `evidence_bundle_verify.md`, and `template_release_verification.md`
- `data/falsiflow/release_check/demo/audit/audit_review.json`
- `data/falsiflow/release_check/demo/audit/audit_review.md`
- `data/falsiflow/release_check/template_gallery.json`
- `data/falsiflow/release_check/template_gallery.md`
- `data/falsiflow/release_check/casebook_check/casebook_reviewer_replay.md`
- `data/falsiflow/release_check/casebook_check/casebook_reviewer_replay.sh`
- `data/falsiflow/release_check/casebook_check/casebook_reviewer_replay.ps1`
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
The sdist must include release docs, package modules, starter template data,
community templates, architecture documentation, template authoring
documentation, data contract documentation, adapter profile documentation,
casebook-check documentation, citation and governance files,
Dependabot config, Scorecard workflow, troubleshooting documentation, and the
security posture documentation. Security and responsible-use docs must be
present in the sdist.
