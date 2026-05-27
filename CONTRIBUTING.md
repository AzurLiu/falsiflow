# Contributing to Falsiflow

Falsiflow is a conservative evidence-gated workflow engine. Contributions should
preserve the core contract: a claim only advances when configuration, evidence,
source provenance, bundles, and verification artifacts agree.

## Development Setup

```bash
python3 -m pip install -e .
falsiflow selftest
falsiflow release-check --out-dir data/falsiflow/release_check
```

## First Contributions

Good first issues should be small, externally useful, and release-checkable.
The best starter contributions are usually one of these:

- Improve a first-run doc, screenshot, demo script, or troubleshooting path.
- Add a narrow evidence-gate fixture to an existing starter template.
- Add or refine an adapter-profile example with sanitized CSV input.
- Improve GitHub Action examples, issue templates, or launch-readiness copy.

For any first contribution, name the command that proves the change. Prefer
`falsiflow quickstart`, `falsiflow doctor`, `falsiflow casebook-check`,
`falsiflow adoption-check`, or `falsiflow release-check`.

For a faster local loop while editing docs or small CLI behavior, use:

```bash
falsiflow release-check --out-dir data/falsiflow/release_check --skip-dist --force
```

Run the full gate before proposing a release or substantial change:

```bash
python3 -m py_compile \
  falsiflow/core.py \
  falsiflow/cli.py \
  falsiflow/adapters.py \
  falsiflow/casebook_check.py \
  scripts/falsiflow.py \
  scripts/falsiflow_tests/regress_falsiflow_core.py

python3 scripts/falsiflow_tests/regress_falsiflow_core.py
python3 scripts/falsiflow.py release-check --out-dir data/falsiflow/release_check --force
```

## Evidence-Gate Rules

- Do not bypass `claim_ready` with warnings, placeholders, missing metadata, or
  missing source files.
- Keep new workflow behavior backed by schemas, CLI output, and regression
  coverage.
- Add or update starter-template evidence when changing project contracts.
- If a command emits machine-readable JSON, document and test its schema.
- If a bundle or verification artifact changes, run zip verification and update
  release-check expectations.
- If import adapter profiles or CSV column mappings change, update
  `docs/falsiflow_adapter_profiles.md` and the wide-ingest regression tests.
- If public starter examples or launch proof changes, run `casebook-check` and
  update `docs/falsiflow_casebook_check.md`.
- If starter template authoring or distribution changes, run `template-check`,
  `template-pack`, `verify-template-pack`, `template-registry`,
  `template-lock`, `template-attest`, `verify-template-attestation`, and
  `template-policy`, `verify-template-policy`, `template-release`,
  `verify-template-release --report-out`, and `template-install` and update
  release-check expectations.
- Preserve the boundaries in `RESPONSIBLE_USE.md`: Falsiflow readiness is not
  proof of safety, efficacy, regulatory compliance, or experimental truth.
- Treat bundle verification, path handling, and source provenance bypasses as
  security-sensitive; see `SECURITY.md`.

## Pull Request Checklist

- The change is scoped to Falsiflow behavior, packaging, docs, or examples.
- Regression tests pass.
- `release-check` passes, or the reason it cannot run is documented.
- New public commands or fields are reflected in `README.md`,
  `docs/falsiflow_mvp.md`, and schemas.
- Data-contract changes update `docs/falsiflow_data_contract.md`.
- Adapter-profile changes update `docs/falsiflow_adapter_profiles.md`.
- Public casebook or starter-proof changes update
  `docs/falsiflow_casebook_check.md`.
- Architecture-impacting changes update `docs/falsiflow_architecture.md`.
- Template authoring or template admission changes update
  `docs/falsiflow_template_authoring.md`.
- User-facing failures or repair actions update
  `docs/falsiflow_troubleshooting.md`.
- Version-facing changes are summarized in `CHANGELOG.md`.
- Security or responsible-use changes update `SECURITY.md` or
  `RESPONSIBLE_USE.md` and keep `release-check` passing.
- Community behavior, support expectations, or project-direction changes update
  `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `GOVERNANCE.md`, `CITATION.cff`, or
  `ROADMAP.md` when relevant.
