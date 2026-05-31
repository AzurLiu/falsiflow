# Falsiflow Data Contract

This document summarizes the machine-facing contract that external scripts, CI
jobs, dashboards, ELN/LIMS exports, and template registries can rely on. The
contract is intentionally conservative: JSON is the source for automation,
Markdown and HTML are review surfaces, and `claim_ready` only means configured
evidence gates passed.

## Stable Inputs

Falsiflow reads two primary project inputs:

- `project.json`: claim, gates, samples, evidence policy, derived fields, and
  acceptance rules.
- Evidence CSV: long-form evidence rows keyed by `gate_id`, `candidate_id`,
  `sample_id`, and `field`.

Common evidence CSV columns are:

- `gate_id`
- `candidate_id`
- `sample_id`
- `field`
- `value`
- `source_file`
- `measured_at`
- `operator_or_agent`
- `instrument_id`
- `notes`

The unique configured evidence key is `gate_id/candidate_id/sample_id/field`.
Replicates should use distinct `sample_id` values. Duplicate configured keys,
missing required columns, blank required metadata, placeholder values, missing
source files, and failed acceptance rules block readiness.

## JSON Status Contract

Automation should key off `status` fields and explicit boolean fields instead of
parsing Markdown text.

Common ready statuses include:

- `claim_ready`
- `claim_check_ready`
- `doctor_ready`
- `quickstart_ready`
- `template_ready`
- `template_pack_verified`
- `template_installed`
- `template_release_verified`
- `adoption_ready`
- `release_ready`
- `external_ready`

Common blocked or skipped statuses include:

- `claim_blocked`
- `claim_check_blocked`
- `doctor_blocked`
- `quickstart_blocked`
- `template_blocked`
- `template_install_blocked`
- `adoption_blocked`
- `release_blocked`
- `external_blocked`
- `dist_skipped`
- `release_validation_skipped`

Blocked reports should include repair context such as `next_actions`,
`next_commands`, `repair_checklist`, `failures`, `blockers`, or diagnostic
records. Consumers should treat unknown non-ready statuses as blocked.

## Report Artifacts

Important machine-readable artifacts include:

- `claim_summary.json`
- `claim_check.json`
- `doctor_summary.json`
- `project_validation.json`
- `evidence_diagnostics.json`
- `source_manifest.json`
- `bundle_manifest.json`
- `bundle_verification.json`
- `template_check.json`
- `template_pack_manifest.json`
- `template_pack_verification.json`
- `template_release_verification.json`
- `external_readiness.json`
- `adoption_check.json`
- `release_check.json`

Matching Markdown reports are for humans. They can change wording more freely
than JSON keys and schema names.

## Source Provenance

Rows that refer to source files should use relative `source_file` paths that can
be resolved from the project or configured source root. Source manifests and
bundle verification records include byte sizes, SHA-256 hashes, copied source
records, missing files, outside-root files, unsafe paths, duplicate paths, and
unmanifested files.

For portable review, generate and verify a bundle:

```bash
falsiflow sources --config project.json --evidence evidence.csv --out source_manifest.json --strict
falsiflow bundle --config project.json --evidence evidence.csv --out-dir evidence_bundle --zip-out evidence_bundle.zip --strict
falsiflow verify-bundle --zip evidence_bundle.zip --strict
```

## JSON Schemas

Schemas are generated from runtime constants:

```bash
falsiflow schema --kind all --out falsiflow_schemas.json
```

Use individual schemas for focused integrations:

```bash
falsiflow schema --kind project
falsiflow schema --kind evidence-row
falsiflow schema --kind claim-check
falsiflow schema --kind doctor-summary
falsiflow schema --kind source-manifest
falsiflow schema --kind bundle-verification
falsiflow schema --kind template-check
falsiflow schema --kind external-readiness
falsiflow schema --kind adoption-check
falsiflow schema --kind release-check
```

CI and downstream tooling should validate the schema that matches the artifact
they consume, then check `status`, failure counts, and repair fields.

## Integration Guidance

- Use `falsiflow evidence import` or `ingest-wide-csv` to convert wide lab,
  vendor, instrument, AI eval, local LLM eval, or RAG eval exports into
  long-form evidence rows.
- Use `--profile generic-wide`, `--profile vendor-measurement`,
  `--profile instrument-export`, `--profile plate-reader`,
  `--profile ai-eval`, `--profile local-llm-eval`, or `--profile rag-eval`
  for common evidence shapes. Adapter-profile details live in
  [falsiflow_adapter_profiles.md](falsiflow_adapter_profiles.md).
- Keep model execution, RAG retrieval, LLM judging, experiment tracking, and
  dashboards outside Falsiflow. Falsiflow consumes their artifacts and decides
  whether the claim has reviewable evidence for CI.
- Keep ELN/LIMS or vendor systems as the source of record; point Falsiflow rows
  at exported raw files through `source_file`.
- In CI, run commands with `--json` where available and `--strict` when a
  blocked state should fail the job.
- Store generated JSON artifacts as build artifacts so humans can review the
  exact gate outcome.
- Do not infer readiness from file existence. Read the JSON status.

## Compatibility Notes

Falsiflow is still pre-1.0, so schema details can evolve. Release-facing changes
must update docs, schemas, tests, and `release-check`. Integrations should pin a
Falsiflow version or commit, keep generated schemas with CI artifacts, and treat
new unknown statuses as blocked until reviewed.

`claim_ready` is a local evidence-contract status, not proof of scientific
truth, regulatory approval, safety, clinical efficacy, or commercial readiness.
