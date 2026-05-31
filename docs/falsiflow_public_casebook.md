# Falsiflow Public Casebook

This casebook gives reviewers concrete stories to try before they decide
whether Falsiflow fits their own evidence-review workflow. Each case is backed
by a bundled starter template, a passing demo CSV, a placeholder demo CSV that
should stay blocked, and a repeatable command path.

For a machine-verifiable public proof of these positive and blocked paths, run
`falsiflow casebook-check --out-dir data/falsiflow/casebook_check --force` and
inspect `casebook_check.md`.

`claim_ready` means supplied evidence passed configured gates. It is not proof
of safety, efficacy, regulatory compliance, commercial readiness, or
experimental truth.

## Case Card Summary

| Case | Template | Decision Falsiflow Gates | What Reviewers Inspect |
| --- | --- | --- | --- |
| Biointerface coating screen | `biointerface_coatings` | Whether a coating is ready for early cell-contact screening. | Formulation provenance, extract stability, bioresponse screen, source files. |
| Neural materials interface | `neural_materials` | Whether a low-dose neural interface material can advance past acellular and early response checks. | Medium stability, electrical interface benefit, matched-control response. |
| AI claim evaluation | `ai_claim_evaluation` | Whether an AI model quality claim is ready for public comparison. | Dataset and model versions, benchmark deltas, raw outputs, reproducibility artifacts. |
| RAG quality gate | `rag_quality_gate` | Whether a RAG answer-quality claim is ready for release notes. | Eval set, query hash, retrieval quality, answer faithfulness, source coverage, raw artifacts. |
| Product metric launch | `product_metric_launch` | Whether a product metric improvement is ready to ship. | Metric provenance, activation lift, guardrail safety, rollback readiness. |
| Vendor or external-lab handoff | `rfq_vendor_evidence` | Whether a vendor reply is ready to support a measured-data work package. | Contact provenance, scope confirmation, measured-data return requirements. |
| Wetware support hardware | `wetware_support_hardware` | Whether support hardware can be used around living wetware experiments. | Material lot provenance, medium-contact stability, operational safety. |

## 1. Biointerface Coating Screen

**Scenario:** A team wants to move a surface treatment into early cell-contact
screening. The risk is not a failed experiment; the risk is spending lab time
on a coating whose formulation, substrate, stability, or basic bioresponse
evidence cannot be traced.

**Evidence contract:**

- `coating_provenance` requires formulation, substrate, and handling records.
- `extract_stability` checks source-backed pH/osmolality style stability
  evidence.
- `bioresponse_screen` keeps the claim blocked until early response fields are
  present and measured.

**Try it:**

```bash
falsiflow quickstart --template biointerface_coatings --out case_biointerface --strict
falsiflow doctor --project-dir case_biointerface --strict
falsiflow claim-check --project-dir case_biointerface --strict --force
```

**What to inspect:** `claim_check.md`, `audit_review.md`,
`evidence_bundle_verify.md`, and the referenced raw files under
`source_files/`.

**Blocked-path proof:** Replace `evidence_pass_demo.csv` with
`evidence_placeholder_demo.csv` and re-run `claim-check`; placeholder evidence
should keep the claim blocked.

## 2. Neural Materials Interface

**Scenario:** A neural-materials candidate should not advance because the
headline material looks promising. It needs a cell-free stability check, an
electrical interface signal, and a matched-control response boundary.

**Evidence contract:**

- `h_a_medium_stability` checks pH and osmolality drift from raw source files.
- `h_b_electrical_interface` requires source-backed electrical readouts.
- `h_c_network_response` compares early response against a control boundary.

**Try it:**

```bash
falsiflow quickstart --template neural_materials --out case_neural_materials --strict
falsiflow doctor --project-dir case_neural_materials --strict
falsiflow claim-check --project-dir case_neural_materials --strict --force
```

**What to inspect:** the ready/blocked decision in `claim_check.json`, the
human review card in `audit_review.md`, and the portable
`evidence_bundle.zip`.

**Blocked-path proof:** Run the same project with the placeholder evidence CSV
to confirm missing source-backed values cannot pass as a ready claim.

## 3. AI Claim Evaluation

**Scenario:** A team wants to publish that one AI model beats a pinned baseline.
The risk is turning a benchmark headline into a product or release claim without
dataset versions, model revisions, raw outputs, or reproducible evaluation
artifacts.

**Evidence contract:**

- `eval_provenance` requires dataset, prompt-set, model, baseline, and evaluator
  versions to be recorded.
- `benchmark_quality` checks absolute quality, relative improvement,
  hallucination, safety-policy failures, and evaluated item count against a
  pinned baseline.
- `reproducibility_package` requires script hashes, decode or seed settings, raw
  output archives, human spotchecks, and a regression CI run.

**Try it:**

```bash
falsiflow quickstart --template ai_claim_evaluation --out case_ai_claim --strict
falsiflow doctor --project-dir case_ai_claim --strict
falsiflow claim-check --project-dir case_ai_claim --strict --force
```

**What to inspect:** benchmark ratios in `claim_audit.md`, raw-output
provenance in `source_manifest.md`, and the portable `evidence_bundle.zip`.

**Blocked-path proof:** Use `evidence_placeholder_demo.csv` to confirm a
pending dataset or model version keeps the public comparison claim blocked.

## 4. RAG Quality Gate

**Scenario:** A team wants to claim its RAG system improved answer quality. The
risk is shipping a release note without pinned eval sets, query hashes,
retrieval runs, answer judgments, source-coverage reports, or raw outputs.

**Evidence contract:**

- `evaluation_provenance` requires the eval set, query hash, candidate and
  baseline RAG versions, and judge version.
- `retrieval_quality` checks recall, MRR, coverage, and improvement against a
  pinned baseline.
- `answer_faithfulness` and `source_coverage` keep unsupported answers,
  citation quality, source coverage, and missing-source findings inside the
  claim boundary.
- `reproducibility_package` requires retrieval runs, raw answers, script hash,
  and a regression CI run.

**Try it:**

```bash
falsiflow quickstart --template rag_quality_gate --out case_rag_quality --strict
falsiflow doctor --project-dir case_rag_quality --strict
falsiflow claim-check --project-dir case_rag_quality --strict --force
```

**What to inspect:** retrieval ratios in `claim_audit.md`, source coverage in
`audit_review.md`, and raw eval provenance in `source_manifest.md`.

**Blocked-path proof:** Use `evidence_placeholder_demo.csv` to show that
`eval_set_pending` prevents a RAG quality claim from passing CI.

## 5. Product Metric Launch

**Scenario:** A product team wants to ship a change because activation improved.
The risk is turning a dashboard screenshot into a launch claim without pinning
metric definitions, exposure, guardrails, rollback ownership, or source files.

**Evidence contract:**

- `metric_provenance` requires the metric definition, experiment id, assignment
  unit, and analysis window.
- `launch_metric_lift` compares activation rate against a baseline and requires
  enough retained users on both arms.
- `guardrail_safety` checks error rate, support-ticket rate, and p95 latency.
- `rollback_readiness` requires rollout state, rollback owner, and monitoring
  dashboard evidence.

**Try it:**

```bash
falsiflow quickstart --template product_metric_launch --out case_product_metric --strict
falsiflow doctor --project-dir case_product_metric --strict
falsiflow claim-check --project-dir case_product_metric --strict --force
```

**What to inspect:** activation lift in `claim_audit.md`, guardrail rows in
`claim_check.md`, rollback source evidence in `source_manifest.md`, and the
portable `evidence_bundle.zip`.

**Blocked-path proof:** Use `evidence_placeholder_demo.csv` to show that a
pending metric definition keeps the launch claim blocked.

## 6. Vendor Or External-Lab Handoff

**Scenario:** A vendor says they can run the requested work package. The team
needs a gate that keeps contact claims, scope statements, and measured-data
return requirements separate before money or samples move.

**Evidence contract:**

- `contact_provenance` requires archived contact and organization evidence.
- `scope_confirmation` records whether the vendor can measure requested fields.
- `return_package_requirements` keeps source files and measured-data return
  expectations explicit.

**Try it:**

```bash
falsiflow quickstart --template rfq_vendor_evidence --out case_vendor_handoff --strict
falsiflow doctor --project-dir case_vendor_handoff --strict
falsiflow claim-check --project-dir case_vendor_handoff --strict --force
```

**What to inspect:** source-file references in `claim_check.md`, the vendor
reply source file, and the bundle verification report.

**Blocked-path proof:** Use `evidence_placeholder_demo.csv` to show that a
vendor statement is not treated as measured evidence without the required
source-backed rows.

## 7. Wetware Support Hardware

**Scenario:** A cartridge, manifold, tubing path, or optical window may look
mechanically acceptable but still needs provenance, medium-contact stability,
and operating-boundary checks before living wetware is exposed to it.

**Evidence contract:**

- `hardware_provenance` records material lot, fluid path, and handling
  provenance.
- `medium_contact_stability` checks source-backed medium-contact stability.
- `operational_safety` records basic operating boundaries before screening.

**Try it:**

```bash
falsiflow quickstart --template wetware_support_hardware --out case_wetware_hardware --strict
falsiflow doctor --project-dir case_wetware_hardware --strict
falsiflow claim-check --project-dir case_wetware_hardware --strict --force
```

**What to inspect:** `repair_checklist` output when evidence is incomplete,
`source_manifest.json`, and `evidence_bundle_verify.md` when the claim is
ready.

**Blocked-path proof:** Swap in placeholder evidence and confirm the readiness
status changes from `claim_check_ready` to a blocked claim-check result.

## Public Demo Script

Use this sequence when showing Falsiflow to a new reviewer:

```bash
falsiflow template-gallery --out data/falsiflow/template_gallery.md --json-out data/falsiflow/template_gallery.json
falsiflow casebook-check --out-dir data/falsiflow/casebook_check --force
falsiflow quickstart --template biointerface_coatings --out public_case_demo --strict
falsiflow claim-check --project-dir public_case_demo --strict --force
falsiflow launch-kit --out-dir falsiflow_launch_kit --force
```

End the demo by opening the local launchpad or hosted static demo, then show
that the same case can produce JSON, Markdown, HTML, and zip verification
artifacts.

For a reviewer who wants to replay every case rather than watch a demo, open the
generated `casebook_reviewer_replay.md` or run:

```bash
bash data/falsiflow/casebook_check/casebook_reviewer_replay.sh
```

On Windows, use:

```powershell
pwsh -File data/falsiflow/casebook_check/casebook_reviewer_replay.ps1
```

Those scripts rerun each starter's positive claim-check and placeholder
blocked-path claim-check, then leave the generated `claim_check.md` reports in
the replay output directory.

## Reviewer Rubric

Ask these questions for each case before adopting the template:

- Is the claim narrow enough to have a ready/blocked decision?
- Are source files mandatory for the values that matter?
- Do placeholders, missing metadata, or malformed rows block the claim?
- Can another reviewer reproduce the decision from the emitted JSON and
  Markdown artifacts?
- Does the bundle carry enough context for a vendor, collaborator, or release
  reviewer to inspect the evidence boundary?
