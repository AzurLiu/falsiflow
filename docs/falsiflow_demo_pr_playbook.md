# Falsiflow Demo PR Playbook

This is the launch demo reviewers understand fastest: a pull request says a
model or RAG system improved, CI blocks it because the eval evidence is only a
placeholder, then the same PR turns green after the author adds source-backed
eval evidence.

The point is not to prove the model is good. The point is to show that
Falsiflow keeps "the model improved" out of release notes until the claim
package is reviewable by CI and humans.

## Public Demo Evidence

The cleanest live demo is the downstream
[PR #1](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1).
It shows Falsiflow running as a reusable GitHub Action in another repository,
not only inside the Falsiflow repo.
For social posts or docs where a full screen recording is too heavy, use the
shareable downstream proof strip at
[`docs/assets/falsiflow_downstream_pr_proof_strip.svg`](assets/falsiflow_downstream_pr_proof_strip.svg).

| Evidence | Link | What it proves |
| --- | --- | --- |
| Downstream demo PR | [#1](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1) | The claim-gate story is a real downstream GitHub PR, not a static screenshot. |
| Downstream blocked CI run | [26711652990](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990) | `falsiflow_ai_eval/evidence.csv` used placeholder/missing eval evidence and strict CI failed with `claim_check_blocked`. |
| Downstream ready CI run | [26711669112](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112) | The same PR passed after `evidence.csv` was replaced with source-backed eval evidence. |

An internal repo version is also available in
[PR #17](https://github.com/AzurLiu/falsiflow/pull/17), with blocked run
[26708459093](https://github.com/AzurLiu/falsiflow/actions/runs/26708459093)
and ready run
[26708472653](https://github.com/AzurLiu/falsiflow/actions/runs/26708472653).

## The Story

Use this PR narrative:

```text
PR title: Claim candidate_model is ready for public eval comparison

The author wants to publish:
"candidate_model improves answer quality over baseline_model on the pinned
claims_eval_v2026_05_26 task set."
```

For a RAG audience, use the same evidence gate and call the claim:

```text
"the RAG assistant has better grounded-answer quality than the pinned baseline."
```

The gate still asks for the same things developers expect to see before
trusting the claim: dataset or task-set version, prompt-set hash, model and
baseline versions, evaluator version, raw outputs, item count, safety or
hallucination metrics, script hash, and a regression CI run.

## What The Reviewer Sees

| PR Moment | Evidence State | CI Result | Reviewer Takeaway |
| --- | --- | --- | --- |
| First commit | `evidence.csv` contains `dataset_pending` and missing rows. | `claim_check_blocked`; strict CI fails. | A benchmark headline cannot pass as evidence. |
| Second commit | `evidence.csv` is replaced with source-backed eval rows. | `claim_check_ready`; strict CI passes. | The claim now has pinned versions, thresholds, raw sources, and a bundle to inspect. |

Expected blocked summary:

```text
status: claim_check_blocked
blocking_stage: gate_evidence
audit_status: claim_blocked
source_status: sources_ready
verification_status: bundle_blocked
```

Expected ready summary:

```text
status: claim_check_ready
blocking_stage: ready_for_human_review
audit_status: claim_ready
source_status: sources_ready
verification_status: bundle_verified
```

`claim_check_ready` still does not prove the model is good, safe, fair, or
useful. It means the repository supplied the evidence package required by its
own claim gate.

## Tiny LLM Eval Fixture

The bundled `ai_claim_evaluation` template is intentionally small enough to
copy into a clean downstream repository. The same fixture can be narrated as a
RAG eval gate when the public claim is about grounded-answer quality:

```bash
mkdir -p falsiflow_ai_eval
cp -R examples/falsiflow/ai_claim_evaluation/. falsiflow_ai_eval/
cp falsiflow_ai_eval/evidence_placeholder_demo.csv falsiflow_ai_eval/evidence.csv
```

Commit these files:

```text
falsiflow_ai_eval/project.json
falsiflow_ai_eval/evidence.csv
falsiflow_ai_eval/evidence_pass_demo.csv
falsiflow_ai_eval/evidence_placeholder_demo.csv
falsiflow_ai_eval/source_files/ai_eval_raw_export.csv
```

The blocked fixture contains the row reviewers should notice immediately:

```csv
gate_id,candidate_id,sample_id,field,value,source_file,measured_at,operator_or_agent,instrument_id,notes
eval_provenance,candidate_model,eval_run_001,dataset_version_recorded,dataset_pending,source_files/ai_eval_raw_export.csv,2026-05-26T08:00:00Z,falsiflow_eval_operator,eval_harness_001,Placeholder dataset version should block readiness.
```

The ready fixture contains the full evidence package. This is the recognizable
benchmark row in the diff:

```csv
gate_id,candidate_id,sample_id,field,value,source_file,measured_at,operator_or_agent,instrument_id,notes
benchmark_quality,candidate_model,eval_run_001,exact_match_rate,0.86,source_files/ai_eval_raw_export.csv,2026-05-26T09:00:00Z,falsiflow_eval_operator,eval_harness_001,Candidate exact-match metric.
```

## Copyable GitHub Action

Create `.github/workflows/falsiflow-ai-eval.yml`:

```yaml
name: AI Eval Claim Gate

on:
  pull_request:
  push:
    branches: [main]

jobs:
  ai-eval-claim:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Run Falsiflow claim gate
        id: falsiflow
        uses: AzurLiu/falsiflow@v0.1.19
        with:
          mode: claim-check
          project-dir: falsiflow_ai_eval
          evidence: falsiflow_ai_eval/evidence.csv
          out-dir: data/falsiflow/ai_eval_claim_check
          strict: "true"

      - name: Upload Falsiflow reports
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: falsiflow-ai-eval-claim-check
          path: |
            ${{ steps.falsiflow.outputs.summary-json }}
            ${{ steps.falsiflow.outputs.summary-md }}
            data/falsiflow/ai_eval_claim_check/evidence_bundle.zip
            data/falsiflow/ai_eval_claim_check/evidence_bundle_verify.md
```

The action installs from its checked-out `GITHUB_ACTION_PATH` by default, so a
tagged action can run even when a downstream project does not want to depend on
PyPI. To force the published package path, add:

```yaml
          install-command: python -m pip install falsiflow
```

## Blocked PR Commit

Create the intentionally failing branch:

```bash
git checkout -b demo/blocked-ai-eval-claim
cp falsiflow_ai_eval/evidence_placeholder_demo.csv falsiflow_ai_eval/evidence.csv
git add falsiflow_ai_eval .github/workflows/falsiflow-ai-eval.yml
git commit -m "Demo blocked AI eval claim"
git push -u origin demo/blocked-ai-eval-claim
```

Suggested PR body:

```markdown
This PR intentionally tries to publish an AI/RAG eval claim with placeholder
evidence.

Expected Falsiflow result:

- `claim_check_blocked`
- strict CI job fails
- `blocking_stage: gate_evidence`
- repair action asks for source-backed eval evidence

This is the behavior we want: placeholder evidence should not pass CI.
```

Reviewers should open the uploaded `claim_check.md` and see that the missing
evidence is named directly. The first repair actions should be:

```text
fill_eval_provenance_evidence
fill_benchmark_quality_evidence
fill_reproducibility_package_evidence
```

## Ready PR Commit

Now replace the placeholder with source-backed evidence:

```bash
cp falsiflow_ai_eval/evidence_pass_demo.csv falsiflow_ai_eval/evidence.csv
git add falsiflow_ai_eval/evidence.csv
git commit -m "Add source-backed AI eval evidence"
git push
```

Expected CI result:

```text
claim_check_ready
bundle_verified
```

The reviewer can inspect:

- `claim_check.md` for the ready/blocked decision.
- `source_manifest.md` for raw source provenance.
- `evidence_bundle_verify.md` for zip integrity.
- `evidence_bundle.zip` for the portable review package.
- `source_files/ai_eval_raw_export.csv` for the raw eval export used by the
  evidence rows.

## Local Rehearsal

Run the same transition locally before recording or sharing the demo:

```bash
cp falsiflow_ai_eval/evidence_placeholder_demo.csv falsiflow_ai_eval/evidence.csv
falsiflow claim-check \
  --project-dir falsiflow_ai_eval \
  --evidence falsiflow_ai_eval/evidence.csv \
  --out-dir data/falsiflow/demo_pr_blocked \
  --force
jq -r '.status, .blocking_stage, .audit_status, .verification_status' \
  data/falsiflow/demo_pr_blocked/claim_check.json

cp falsiflow_ai_eval/evidence_pass_demo.csv falsiflow_ai_eval/evidence.csv
falsiflow claim-check \
  --project-dir falsiflow_ai_eval \
  --evidence falsiflow_ai_eval/evidence.csv \
  --out-dir data/falsiflow/demo_pr_ready \
  --strict \
  --force
jq -r '.status, .blocking_stage, .audit_status, .verification_status' \
  data/falsiflow/demo_pr_ready/claim_check.json
```

Expected output:

```text
claim_check_blocked
gate_evidence
claim_blocked
bundle_blocked

claim_check_ready
ready_for_human_review
claim_ready
bundle_verified
```

## 30-second Recording Script

1. Show the PR title and the failing `AI Eval Claim Gate` job.
2. Open the uploaded `claim_check.md` and highlight `claim_check_blocked`.
3. Show the evidence diff changing `dataset_pending` into source-backed rows.
4. Re-run CI and show `claim_check_ready`.
5. End on `evidence_bundle_verify.md` and the raw eval source file.

Use this closing line:

```text
Falsiflow does not decide that the model is good. It decides whether the claim
has enough pinned, source-backed evidence to pass CI.
```
