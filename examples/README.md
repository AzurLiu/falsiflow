# Falsiflow Walkthrough

This walkthrough takes a starter claim from first-run quickstart to a verified
portable evidence bundle. It uses the neural-materials demo because it exercises
the core Falsiflow contract: gates, required evidence rows, source-file
provenance, audit outputs, bundle generation, and zip verification.

Run from the repository root.

## One-Command Quickstart

```bash
python3 scripts/falsiflow.py quickstart \
  --template biointerface_coatings \
  --out /tmp/falsiflow_quickstart \
  --strict
```

Expected result: `Falsiflow quickstart: quickstart_ready`.

The quickstart project contains `quickstart_summary.json`,
`quickstart_summary.md`, and a complete `claim_check/` directory. The report
title is `Falsiflow Quickstart`, and `next_commands` points to the matching
doctor command.

## One-Command Doctor

```bash
python3 scripts/falsiflow.py doctor \
  --project-dir /tmp/falsiflow_quickstart \
  --strict
```

Expected result: `Falsiflow doctor: doctor_ready`.

The doctor report is titled `Falsiflow Doctor` and writes
`doctor_summary.json`, `doctor_summary.md`, `project_validation.json`, and
`evidence_diagnostics.json` before preserving the complete claim-check output.
When blocked, `repair_checklist` gives the first repair command, expected
artifact, and success signal to use before rerunning doctor. When ready, the
same table points to the next review step.

## One-Command Demo

```bash
python3 scripts/falsiflow.py demo \
  --out-dir /tmp/falsiflow_walkthrough \
  --force
```

Expected result: `Falsiflow demo: demo_ready`.

## Template Gallery

```bash
python3 scripts/falsiflow.py template-gallery \
  --out /tmp/falsiflow_template_gallery.md \
  --json-out /tmp/falsiflow_template_gallery.json
```

Expected result: `Falsiflow template-gallery: template_gallery_ready`.

The gallery shows the neural-materials, RFQ vendor evidence,
biointerface-coatings, and wetware-support-hardware starters side by side before
you choose a template to copy.

## Downstream AI Eval Smoke

For a copy-paste repository fixture that starts blocked in CI and turns ready
after source-backed eval evidence is added, use:

```bash
cp -R examples/downstream_ai_eval_smoke/. /tmp/falsiflow_downstream_repo/
```

The fixture includes `.github/workflows/falsiflow-ai-eval.yml` and the
`falsiflow_ai_eval/` project files expected by the workflow. Its initial
`evidence.csv` is intentionally the placeholder demo, so a downstream PR should
show `claim_check_blocked` before the repair commit copies
`evidence_pass_demo.csv` over `evidence.csv`.

The sections below show the same flow step by step.

## Downstream Product Metric Smoke

For a copy-paste repository fixture that starts blocked on placeholder product
analytics evidence and turns ready after source-backed activation, guardrail,
and rollback rows are added, use:

```bash
cp -R examples/downstream_product_metric_smoke/. /tmp/falsiflow_product_metric_downstream_repo/
```

The fixture includes `.github/workflows/falsiflow-product-metric.yml` and the
`falsiflow_product_metric/` project files expected by the workflow. Its initial
`evidence.csv` is intentionally the placeholder demo, so a downstream PR should
show `claim_check_blocked` before the repair commit copies
`evidence_pass_demo.csv` over `evidence.csv`.

## Local LLM Eval Import

For a copy-paste fixture that starts blocked on placeholder AI eval evidence,
then turns local Ollama, LM Studio, llama.cpp, MLX, vLLM, or private-runner
artifacts into source-backed evidence rows, use:

```bash
cp -R examples/local_llm_eval_import/. /tmp/falsiflow_local_llm_eval_repo/
```

The fixture includes `.github/workflows/falsiflow-local-llm-eval.yml`, a
placeholder `falsiflow_local_llm_eval/evidence.csv`, a raw local eval artifact
at `falsiflow_local_llm_eval/source_files/local_eval_results.jsonl`, and
`falsiflow_local_llm_eval/local_model_manifest.json`. Its workflow runs the
reusable action in `mode: evidence-import`, then reruns the same action in
`mode: claim-check`. Expected statuses are `coverage_ready` followed by
`claim_check_ready`; no model server or API port is opened by Falsiflow.

## Template Authoring Check

```bash
python3 scripts/falsiflow.py template-check \
  --template-dir examples/falsiflow/neural_materials \
  --out-dir /tmp/falsiflow_template_check \
  --force
```

Expected result: `Falsiflow template-check: template_ready`.

This check proves the starter template has a passing demo, a blocked placeholder
demo, complete source provenance, and a verified bundle.

## Create a Custom Starter Template

```bash
python3 scripts/falsiflow.py template-scaffold \
  --out /tmp/falsiflow_custom_template \
  --template-id custom_template \
  --claim-statement "Candidate has enough source-backed evidence to proceed." \
  --gate gate_a:score,replicate_score \
  --rule "gate_a:score:>=:1:Score must be present." \
  --check-out-dir /tmp/falsiflow_custom_template_check \
  --force
```

Expected result: `Falsiflow template-scaffold: template_scaffolded`.

## Package a Template

```bash
python3 scripts/falsiflow.py template-pack \
  --template-dir examples/falsiflow/neural_materials \
  --out-dir /tmp/falsiflow_template_pack \
  --zip-out /tmp/falsiflow_template_pack.zip \
  --force

python3 scripts/falsiflow.py verify-template-pack \
  --zip /tmp/falsiflow_template_pack.zip \
  --strict

python3 scripts/falsiflow.py template-registry \
  --pack-zip /tmp/falsiflow_template_pack.zip \
  --out /tmp/falsiflow_template_registry.json

python3 scripts/falsiflow.py template-lock \
  --registry /tmp/falsiflow_template_registry.json \
  --template neural_materials \
  --version 0.1.0 \
  --out /tmp/falsiflow_template_lock.json

python3 scripts/falsiflow.py template-attest \
  --subject /tmp/falsiflow_template_lock.json \
  --subject-type template-lock \
  --out /tmp/falsiflow_template_lock.attestation.json \
  --signing-key local-demo-secret

python3 scripts/falsiflow.py verify-template-attestation \
  --attestation /tmp/falsiflow_template_lock.attestation.json \
  --subject /tmp/falsiflow_template_lock.json \
  --signing-key local-demo-secret \
  --strict

python3 scripts/falsiflow.py template-policy \
  --lock /tmp/falsiflow_template_lock.json \
  --attestation /tmp/falsiflow_template_lock.attestation.json \
  --out /tmp/falsiflow_template_policy.json \
  --signing-key local-demo-secret

python3 scripts/falsiflow.py verify-template-policy \
  --policy /tmp/falsiflow_template_policy.json \
  --lock /tmp/falsiflow_template_lock.json \
  --attestation /tmp/falsiflow_template_lock.attestation.json \
  --signing-key local-demo-secret \
  --strict

python3 scripts/falsiflow.py template-release \
  --pack-zip /tmp/falsiflow_template_pack.zip \
  --registry /tmp/falsiflow_template_registry.json \
  --lock /tmp/falsiflow_template_lock.json \
  --attestation /tmp/falsiflow_template_lock.attestation.json \
  --policy /tmp/falsiflow_template_policy.json \
  --out /tmp/falsiflow_template_release.zip \
  --signing-key local-demo-secret

python3 scripts/falsiflow.py verify-template-release \
  --release /tmp/falsiflow_template_release.zip \
  --out /tmp/falsiflow_template_release_verification.json \
  --report-out /tmp/falsiflow_template_release_verification.md \
  --signing-key local-demo-secret \
  --strict

python3 scripts/falsiflow.py template-install \
  --release /tmp/falsiflow_template_release.zip \
  --signing-key local-demo-secret \
  --templates-dir /tmp/falsiflow_installed_templates \
  --force
```

Expected result: `Falsiflow template-install: template_installed`. Signed
attestations reach `template_attestation_verified` when verified with the same
HMAC key. Policies reach `template_policy_verified`, release bundles reach
`template_release_verified`, and installation blocks when any embedded artifact
does not match.

## 1. Copy a Starter Project

```bash
rm -rf /tmp/falsiflow_walkthrough
python3 scripts/falsiflow.py init \
  --template neural_materials \
  --out /tmp/falsiflow_walkthrough/neural_materials
```

## 2. Validate the Project Contract

```bash
python3 scripts/falsiflow.py validate \
  --config /tmp/falsiflow_walkthrough/neural_materials/project.json \
  --strict
```

Expected result: `Falsiflow validate: valid`.

## 3. Run the One-Command Claim Gate

```bash
python3 scripts/falsiflow.py claim-check \
  --project-dir /tmp/falsiflow_walkthrough/neural_materials \
  --strict
```

Expected result: `Falsiflow claim-check: claim_check_ready`.

The project now contains `claim_check/claim_check.json`,
`claim_check/claim_check.md`, `claim_check/evidence_bundle.zip`, and
`claim_check/evidence_bundle_verify.*`. The report title is `Falsiflow Claim
Check`; `claim_check_blocked` preserves the same artifacts and points to the
blocking stage and next actions. Use explicit `--config`, `--evidence`, and
`--out-dir` when checking a non-default evidence CSV.

## 4. Audit Passing Evidence

```bash
python3 scripts/falsiflow.py audit \
  --config /tmp/falsiflow_walkthrough/neural_materials/project.json \
  --evidence /tmp/falsiflow_walkthrough/neural_materials/evidence_pass_demo.csv \
  --out-dir /tmp/falsiflow_walkthrough/audit \
  --strict
```

Expected result: `Claim ready: true`.

The audit directory also contains `audit_review.json` and `audit_review.md`.
The review report is titled `Falsiflow Audit Review` and gives the release
decision, first blocking stage when present, top blockers, next actions, and
human review checklist.

## 5. Inspect Source Provenance

```bash
python3 scripts/falsiflow.py sources \
  --config /tmp/falsiflow_walkthrough/neural_materials/project.json \
  --evidence /tmp/falsiflow_walkthrough/neural_materials/evidence_pass_demo.csv \
  --out /tmp/falsiflow_walkthrough/source_manifest.json \
  --report-out /tmp/falsiflow_walkthrough/source_manifest.md \
  --strict
```

Expected result: `Falsiflow sources: sources_ready`.

## 6. Build a Portable Evidence Bundle

```bash
python3 scripts/falsiflow.py bundle \
  --config /tmp/falsiflow_walkthrough/neural_materials/project.json \
  --evidence /tmp/falsiflow_walkthrough/neural_materials/evidence_pass_demo.csv \
  --out-dir /tmp/falsiflow_walkthrough/evidence_bundle \
  --zip-out /tmp/falsiflow_walkthrough/evidence_bundle.zip \
  --strict
```

Expected result: `Falsiflow bundle: bundle_ready`.

## 7. Verify the Bundle Zip

```bash
python3 scripts/falsiflow.py verify-bundle \
  --zip /tmp/falsiflow_walkthrough/evidence_bundle.zip \
  --out /tmp/falsiflow_walkthrough/evidence_bundle_verify.json \
  --report-out /tmp/falsiflow_walkthrough/evidence_bundle_verify.md \
  --strict
```

Expected result: `Falsiflow verify-bundle: bundle_verified`.

The verified bundle means the files match the manifest. It does not mean the
material is biologically safe, clinically useful, regulatory-ready, or
commercially ready. See [../RESPONSIBLE_USE.md](../RESPONSIBLE_USE.md).

## 8. Run the Adoption Gate

```bash
python3 scripts/falsiflow.py adoption-check \
  --out-dir /tmp/falsiflow_walkthrough/adoption_check \
  --skip-dist \
  --force
```

Expected result: `Falsiflow adoption-check: adoption_ready`.

This writes `adoption_check.json` and the `Falsiflow Adoption Check` report so
the five maintained priorities can be reviewed before the full release gate.
The report includes a `repair_checklist` table with the command, expected
artifact, and success signal for the next priority repair or ready recheck.

## 9. Run the Full Release Gate

```bash
python3 scripts/falsiflow.py release-check \
  --out-dir /tmp/falsiflow_walkthrough/release_check \
  --force
```

Expected result: `Falsiflow release-check: release_ready`.

For installed usage, replace `python3 scripts/falsiflow.py` with `falsiflow`.
