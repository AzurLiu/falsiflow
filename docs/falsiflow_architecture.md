# Falsiflow Architecture

Falsiflow is intentionally small: most commands are thin orchestration around a
shared evidence-gate contract. The architecture goal is to keep claims blocked
until project config, evidence rows, source provenance, templates, bundles, and
release artifacts all agree.

## Core Data Model

- `project.json` defines the claim, required gates, samples, evidence policy,
  derived fields, and acceptance rules.
- Long-form evidence CSV rows provide `gate_id`, `candidate_id`, `sample_id`,
  `field`, `value`, source-file metadata, operator/agent metadata, timestamps,
  and notes.
- Source manifests record raw source files, byte sizes, SHA-256 hashes, and
  missing/unmanifested file issues.
- Audit, claim-check, doctor, casebook-check, adoption-check, and release-check
  summaries are machine-readable JSON with matching Markdown reports for human
  review.
- Template packs, registries, lockfiles, attestations, policies, and release
  bundles carry hashes and verification reports so starter workflows can move
  between teams without losing provenance.

## Command Flow

1. `quickstart`, `init`, `template-install`, or `template-scaffold` creates a
   project directory and evidence template.
2. `validate` and `doctor` check config shape, evidence CSV diagnostics, source
   file presence, and repair actions.
3. `audit` and `claim-check` evaluate the same core gates and write ready or
   blocked review artifacts.
4. `sources`, `bundle`, and `verify-bundle` attach source provenance and prove
   bundle integrity.
5. `template-check`, `template-pack`, `template-registry`, `template-lock`,
   `template-attest`, `template-policy`, `template-release`, and
   `template-install` verify starter-template supply-chain artifacts.
6. `casebook-check` proves public starter positive and blocked paths.
7. `adoption-check` and `release-check` aggregate first-run, documentation,
   packaging, template, casebook, bundle, demo, launch, external evidence, and
   distribution readiness.

## Module Map

- `falsiflow.core`: schema constants, CSV diagnostics, project validation,
  derived-field computation, and the core audit decision.
- `falsiflow.cli`: command routing and CLI argument handling.
- `falsiflow.claim_check`, `doctor`, `quickstart`, `demo`, `browser_demo`, and
  `local_server`: first-run and review workflows built on the core contract.
- `falsiflow.bundle`: source manifests, bundle creation, bundle verification,
  and report rendering.
- `falsiflow.casebook_check`: public starter casebook proof summaries.
- `falsiflow.template_*`: template discovery, gallery, authoring checks,
  packaging, registries, lockfiles, attestations, policies, releases, and
  verified installs.
- `falsiflow.adoption` and `falsiflow.release`: adoption priority checks,
  distribution checks, package surface checks, and release report rendering.
- `falsiflow.public_release`: static demo, publish kit, launch kit, and
  external evidence/readiness handoff artifacts.

## Release Invariants

- `claim_ready` only appears when validation, evidence diagnostics, source
  policy, required fields, derived metrics, and acceptance rules agree.
- Placeholder values, duplicate evidence keys, malformed CSV headers, missing
  source files, failed acceptance rules, unsafe archive paths, hash mismatches,
  and unmanifested files must block readiness.
- Project configs are data. They do not execute Python, shell commands,
  notebooks, plugins, or arbitrary code.
- JSON output is the machine contract; Markdown and HTML are review surfaces
  derived from the same summaries.
- The integration-facing contract is summarized in
  [falsiflow_data_contract.md](falsiflow_data_contract.md).
- CSV adapter profiles are summarized in
  [falsiflow_adapter_profiles.md](falsiflow_adapter_profiles.md).
- Public starter positive and blocked paths are summarized in
  [falsiflow_casebook_check.md](falsiflow_casebook_check.md).
- Full `release-check` must clean local build caches, build wheel and sdist,
  inspect sdist contents, install the wheel in isolation, and run
  installed-package `release-check`.

## Extension Points

Good extension work usually fits one of these surfaces:

- Add an import adapter profile that converts a vendor, lab, or instrument
  export into long-form evidence rows while preserving raw source files.
- Add a starter template with passing and blocked demo evidence, source files,
  responsible-use language, and template release verification.
- Improve local browser review surfaces without changing the JSON contracts.
- Add schema-backed commands only when they have stable JSON output,
  documentation, release-check coverage, and regression tests.
- Add release or external evidence checks that produce explicit repair actions
  instead of silent warnings.

Avoid extensions that make configs executable, hide evidence provenance, mark
warnings as ready, weaken bundle/template hash checks, or present `claim_ready`
as scientific proof, regulatory approval, safety proof, or commercial readiness.

## Contributor Checklist

Before opening a substantial change:

- Read [../CONTRIBUTING.md](../CONTRIBUTING.md),
  [../GOVERNANCE.md](../GOVERNANCE.md), and
  [falsiflow_security_posture.md](falsiflow_security_posture.md).
- Update [falsiflow_mvp.md](falsiflow_mvp.md), this architecture note, and
  [falsiflow_cli_reference.md](falsiflow_cli_reference.md) when public commands,
  schemas, modules, or release invariants change.
- Run `python3 scripts/falsiflow_tests/regress_falsiflow_core.py`.
- Run `python3 scripts/falsiflow.py release-check --out-dir
  data/falsiflow/release_check --force` before release-facing changes.
