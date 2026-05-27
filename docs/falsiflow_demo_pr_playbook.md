# Falsiflow Demo PR Playbook

Use this playbook to create the public demo reviewers understand fastest: one
pull request is blocked because the AI-eval claim is backed only by placeholder
evidence, then the same pull request turns green after the evidence is replaced
with source-backed measurements.

The goal is not to prove a real model is good. The goal is to show that
Falsiflow keeps the sentence "the model improved" out of release notes until
the claim package is reviewable by CI and humans.

## Tiny LLM Eval Fixture

For an AI-tool audience, frame the demo as a small LLM eval regression gate:

```text
Claim: candidate_model is ready to claim better answer quality than the pinned
baseline on claims_eval_v2026_05_26.
```

The blocked version can be this single placeholder row in
`falsiflow_ai_eval/evidence.csv`:

```csv
gate_id,candidate_id,sample_id,field,value,source_file,measured_at,operator_or_agent,instrument_id,notes
eval_provenance,candidate_model,eval_run_001,dataset_version_recorded,dataset_pending,source_files/ai_eval_raw_export.csv,2026-05-26T08:00:00Z,falsiflow_eval_operator,eval_harness_001,Placeholder dataset version should block readiness.
```

Expected result: `claim_check_blocked`. The blocker is intentional: the dataset
version is not pinned, and the placeholder marker keeps the claim out of release
notes.

The ready version should use the full bundled `evidence_pass_demo.csv`, because
the gate requires provenance, benchmark quality, baseline comparison, and
reproducibility rows. This is the representative LLM eval row reviewers should
recognize in the ready diff:

```csv
gate_id,candidate_id,sample_id,field,value,source_file,measured_at,operator_or_agent,instrument_id,notes
benchmark_quality,candidate_model,eval_run_001,exact_match_rate,0.86,source_files/ai_eval_raw_export.csv,2026-05-26T09:00:00Z,falsiflow_eval_operator,eval_harness_001,Candidate exact-match metric.
```

Expected result after copying the complete `evidence_pass_demo.csv`:
`claim_check_ready`. The ready state still does not prove the model is truly
better; it only proves the repository supplied the evidence package required by
its own LLM eval claim gate.

## Demo Shape

| Step | Branch State | Expected CI Status | Reviewer Takeaway |
| --- | --- | --- | --- |
| Blocked PR | `evidence.csv` is copied from `evidence_placeholder_demo.csv`. | `claim_check_blocked` and the strict GitHub Action job fails. | Placeholder values cannot become launch claims. |
| Ready PR | `evidence.csv` is copied from `evidence_pass_demo.csv`. | `claim_check_ready` and the GitHub Action job passes. | Versioned eval evidence, source files, and thresholds are enough to review. |

## Repository Setup

Copy the AI claim starter into a downstream repository:

```bash
mkdir -p falsiflow_ai_eval
cp -R examples/falsiflow/ai_claim_evaluation/. falsiflow_ai_eval/
cp falsiflow_ai_eval/evidence_placeholder_demo.csv falsiflow_ai_eval/evidence.csv
```

Commit `falsiflow_ai_eval/project.json`, `falsiflow_ai_eval/evidence.csv`, and
`falsiflow_ai_eval/source_files/ai_eval_raw_export.csv`. Keep
`evidence_pass_demo.csv` and `evidence_placeholder_demo.csv` in the same
directory if you want the PR description to show the before/after diff.

## Copyable GitHub Action

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
        uses: AzurLiu/falsiflow@main
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

The action installs from its checked-out `GITHUB_ACTION_PATH`, so the demo works
before PyPI is published. After PyPI trusted publishing is complete, the demo can
switch to `install-command: python -m pip install falsiflow`.

## Blocked PR

Create a branch and open the first version of the PR:

```bash
git checkout -b demo/blocked-ai-claim
cp falsiflow_ai_eval/evidence_placeholder_demo.csv falsiflow_ai_eval/evidence.csv
git add falsiflow_ai_eval .github/workflows/falsiflow-ai-eval.yml
git commit -m "Demo blocked AI eval claim"
git push -u origin demo/blocked-ai-claim
```

Suggested PR title:

```text
Demo: block unsupported AI model improvement claim
```

Suggested PR body:

```markdown
This PR intentionally claims an AI evaluation result with placeholder evidence.

Expected Falsiflow result:

- `claim_check_blocked`
- strict CI job fails
- uploaded report names `evidence_placeholder_demo.csv`
- repair action asks for source-backed eval evidence
```

## Ready PR Update

Replace the placeholder evidence with the positive demo evidence:

```bash
cp falsiflow_ai_eval/evidence_pass_demo.csv falsiflow_ai_eval/evidence.csv
git add falsiflow_ai_eval/evidence.csv
git commit -m "Add source-backed AI eval evidence"
git push
```

Expected Falsiflow result:

- `claim_check_ready`
- strict CI job passes
- uploaded report includes `claim_check.md`
- bundle verification report points to a SHA-256 checked evidence zip
- reviewer can inspect `source_files/ai_eval_raw_export.csv`

## Local Proof

Run the same transition locally before recording or sharing the demo:

```bash
cp falsiflow_ai_eval/evidence_placeholder_demo.csv falsiflow_ai_eval/evidence.csv
falsiflow claim-check --project-dir falsiflow_ai_eval --evidence falsiflow_ai_eval/evidence.csv --out-dir data/falsiflow/demo_pr_blocked --force
jq -r '.status' data/falsiflow/demo_pr_blocked/claim_check.json

cp falsiflow_ai_eval/evidence_pass_demo.csv falsiflow_ai_eval/evidence.csv
falsiflow claim-check --project-dir falsiflow_ai_eval --evidence falsiflow_ai_eval/evidence.csv --out-dir data/falsiflow/demo_pr_ready --strict --force
jq -r '.status' data/falsiflow/demo_pr_ready/claim_check.json
```

The expected statuses are `claim_check_blocked` first and `claim_check_ready`
second.

## 30-second Recording Script

1. Show the PR title and failing `AI Eval Claim Gate` job.
2. Open the uploaded `claim_check.md` report and highlight `claim_check_blocked`.
3. Show the one-line evidence change from placeholder values to source-backed
   rows.
4. Re-run CI and show `claim_check_ready`.
5. End on the bundle verification artifact and the README 30-second strip.

Do not say Falsiflow proves the model is better. Say it proves the repository
has supplied the evidence package its own claim gate requires.
