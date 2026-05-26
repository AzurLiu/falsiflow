# Falsiflow Template Authoring

Starter templates are the main way Falsiflow travels beyond the bundled demos.
A good template is not just a `project.json`: it is a small, reviewable evidence
contract with positive evidence, intentionally blocked placeholder evidence,
raw source files, and a verified release path.

## Template Layout

A reusable template directory should contain:

- `template.json`: template metadata, domain, claim summary, demo files, and
  first commands.
- `project.json`: the claim, required gates, samples, evidence policy, derived
  fields, and acceptance rules.
- `evidence_pass_demo.csv`: source-backed evidence that reaches `claim_ready`.
- `evidence_placeholder_demo.csv`: incomplete or placeholder evidence that must
  stay blocked.
- `source_files/`: raw source files referenced by evidence rows.
- `README.md`: a human summary of the claim, evidence contract, and responsible
  use boundary.

The template should be understandable without private lab data. Use synthetic,
sanitized, or public demo rows when the real workflow involves proprietary
measurements.

## Evidence Contract

Each gate should answer one review question. Good gates are narrow enough that
a blocked result points to a concrete repair:

- What source-backed field is missing?
- Which sample, candidate, or source file is responsible?
- Which acceptance rule failed?
- Which raw source file should a reviewer inspect?

Evidence rows should include required metadata such as `source_file`,
`measured_at`, `operator_or_agent`, and `instrument_id` unless the template's
domain has a documented reason to relax that policy.

## Positive And Placeholder Demos

Every template needs two stories:

- The positive demo proves that a complete, source-backed evidence set can
  become `claim_ready`.
- The placeholder demo proves that blanks, `TBD`, missing rows, missing source
  files, or unsupported values stay blocked.

If placeholder evidence passes, the template is unsafe to share. Tighten
required fields, placeholder markers, source-file policy, samples, derived
metrics, or acceptance rules until `template-check` reports that the placeholder
demo blocks.

## Authoring Flow

Start from a scaffold when possible:

```bash
falsiflow template-scaffold \
  --out my_template \
  --template-id my_template \
  --template-name "My Template" \
  --claim-statement "Candidate has enough source-backed evidence to proceed." \
  --gate gate_a:score,replicate_score \
  --rule "gate_a:score:>=:1:Score must be present." \
  --check-out-dir data/falsiflow/my_template_check \
  --json
```

Then run the same checks a maintainer will run:

```bash
falsiflow template-check --template-dir my_template --out-dir data/falsiflow/my_template_check --strict --force
falsiflow template-pack --template-dir my_template --out-dir data/falsiflow/my_template_pack --zip-out data/falsiflow/my_template_pack.zip --force
falsiflow verify-template-pack --zip data/falsiflow/my_template_pack.zip --strict
```

For a template meant to move between teams, build a registry, lock, attestation,
policy, and release bundle:

```bash
falsiflow template-registry --pack-zip data/falsiflow/my_template_pack.zip --out data/falsiflow/template_registry.json
falsiflow template-lock --registry data/falsiflow/template_registry.json --template my_template --version 0.1.0 --out data/falsiflow/falsiflow_template_lock.json
falsiflow template-attest --subject data/falsiflow/falsiflow_template_lock.json --subject-type template-lock --out data/falsiflow/falsiflow_template_lock.attestation.json --signing-key local-demo-secret
falsiflow template-policy --lock data/falsiflow/falsiflow_template_lock.json --attestation data/falsiflow/falsiflow_template_lock.attestation.json --out data/falsiflow/falsiflow_template_policy.json --signing-key local-demo-secret
falsiflow template-release --pack-zip data/falsiflow/my_template_pack.zip --registry data/falsiflow/template_registry.json --lock data/falsiflow/falsiflow_template_lock.json --attestation data/falsiflow/falsiflow_template_lock.attestation.json --policy data/falsiflow/falsiflow_template_policy.json --out data/falsiflow/my_template_release.zip --signing-key local-demo-secret
falsiflow verify-template-release --release data/falsiflow/my_template_release.zip --signing-key local-demo-secret --report-out data/falsiflow/my_template_release_verification.md --strict
falsiflow template-install --release data/falsiflow/my_template_release.zip --signing-key local-demo-secret --templates-dir data/falsiflow/installed_templates --force
```

## Admission Checklist

Before proposing a bundled template, confirm:

- `template-check` reports `template_ready`.
- `evidence_pass_demo.csv` reaches `claim_ready`.
- `evidence_placeholder_demo.csv` remains blocked.
- Source provenance is ready and source files exist under `source_files/`.
- `template-pack` and `verify-template-pack` report `template_pack_verified`.
- `template-release` and `verify-template-release` report
  `template_release_verified`.
- `template-install` reports `template_installed`.
- The template's README explains responsible-use boundaries and does not present
  `claim_ready` as scientific proof, regulatory approval, safety proof, or
  commercial readiness.

## Common Mistakes

- Treating a vendor statement as measured evidence without a source-backed row.
- Leaving placeholder values in the positive demo.
- Omitting raw source files or using paths outside `source_files/`.
- Making a gate so broad that a blocked result has no actionable repair.
- Adding a domain template without a blocked-path story.
- Sharing a zip before `verify-template-pack` or `verify-template-release`
  succeeds.

## Maintainer Review

Maintainers should review the template claim, gate names, required fields,
source-file policy, positive demo, placeholder demo, raw source files, generated
reports, and responsible-use language. A template is ready to bundle only when
the local release gate can verify it without private state.

Run:

```bash
falsiflow release-check --out-dir data/falsiflow/release_check --force
```

The release should remain `release_ready`, `template_gallery_ready`, and
`adoption_ready`.
