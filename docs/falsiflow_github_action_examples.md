# Falsiflow GitHub Action Examples

This page gives downstream repositories a copy-paste path for running
Falsiflow in CI before PyPI publishing is complete. The reusable action installs
from its versioned action checkout by default through `GITHUB_ACTION_PATH`.
Override `install-command` only when you want to install from PyPI, a fork, or a
repository-local editable checkout.

## Clean Downstream Smoke Repo

Use this recipe when the downstream repository does not contain Falsiflow yet
and you want a copy-paste smoke test before wiring it into real release checks.

The maintained fixture lives in
[`examples/downstream_ai_eval_smoke`](../examples/downstream_ai_eval_smoke).
Copy that directory into a clean repository when you want the smallest
blocked-then-ready PR story without hand-assembling files from prose.

Live downstream proof is available in
[`AzurLiu/falsiflow-downstream-ai-eval-demo`](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo):
[PR #1](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1)
first failed in
[run 26711652990](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990),
then passed in
[run 26711669112](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112)
after source-backed eval evidence replaced the placeholder row.

RAG downstream proof is available in
[`AzurLiu/falsiflow-downstream-rag-eval-demo`](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo):
[PR #1](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1)
first failed in
[run 26721829145](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721829145)
with `claim_check_blocked`, then passed in
[run 26721856616](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721856616)
with `claim_check_ready` after source-backed RAG evidence and the raw eval
export were added.

Product metric downstream proof is available in
[`AzurLiu/falsiflow-downstream-product-metric-demo`](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo):
[PR #1](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1)
first failed in
[run 26726360229](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726360229)
with `claim_check_blocked`, then passed in
[run 26726392921](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726392921)
with `claim_check_ready` after metric provenance, lift, guardrail, and
rollback-readiness evidence was source-backed.

Target layout:

```text
.github/workflows/falsiflow-ai-eval.yml
falsiflow_ai_eval/project.json
falsiflow_ai_eval/evidence.csv
falsiflow_ai_eval/evidence_pass_demo.csv
falsiflow_ai_eval/evidence_placeholder_demo.csv
falsiflow_ai_eval/source_files/ai_eval_raw_export.csv
```

Bootstrap the fixture from a Falsiflow checkout:

```bash
git clone https://github.com/AzurLiu/falsiflow /tmp/falsiflow
mkdir -p falsiflow_ai_eval
cp -R /tmp/falsiflow/examples/falsiflow/ai_claim_evaluation/. falsiflow_ai_eval/
cp falsiflow_ai_eval/evidence_placeholder_demo.csv falsiflow_ai_eval/evidence.csv
```

Commit that layout plus this workflow:

```yaml
name: Falsiflow Downstream Smoke

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  claim-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Run claim gate
        id: falsiflow
        uses: AzurLiu/falsiflow@v0.1.37
        with:
          mode: claim-check
          project-dir: falsiflow_ai_eval
          evidence: falsiflow_ai_eval/evidence.csv
          out-dir: data/falsiflow/downstream_smoke
          strict: "true"

      - name: Upload claim reports
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: falsiflow-downstream-smoke
          path: |
            ${{ steps.falsiflow.outputs.summary-json }}
            ${{ steps.falsiflow.outputs.summary-md }}
            data/falsiflow/downstream_smoke/evidence_bundle.zip
            data/falsiflow/downstream_smoke/evidence_bundle_verify.md
```

Expected blocked run:

```bash
cp falsiflow_ai_eval/evidence_placeholder_demo.csv falsiflow_ai_eval/evidence.csv
git add falsiflow_ai_eval/evidence.csv .github/workflows/falsiflow-ai-eval.yml
git commit -m "Add blocked Falsiflow downstream smoke"
```

The strict job should fail with `claim_check_blocked`, while the uploaded JSON
and Markdown reports show the placeholder evidence repair action. The GitHub
Step Summary also prints the status, blocking stage, top blockers, and
evidence todo so reviewers can see which rows to add before downloading
artifacts.

Expected ready run:

```bash
cp falsiflow_ai_eval/evidence_pass_demo.csv falsiflow_ai_eval/evidence.csv
git add falsiflow_ai_eval/evidence.csv
git commit -m "Use source-backed Falsiflow downstream smoke evidence"
```

The job should pass with `claim_check_ready`, upload both report formats, and
include the source-backed bundle artifacts.

Local reproduction before pushing:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e /tmp/falsiflow
python -m falsiflow.cli claim-check \
  --project-dir falsiflow_ai_eval \
  --evidence falsiflow_ai_eval/evidence.csv \
  --out-dir data/falsiflow/downstream_blocked \
  --force
cp falsiflow_ai_eval/evidence_pass_demo.csv falsiflow_ai_eval/evidence.csv
python -m falsiflow.cli claim-check \
  --project-dir falsiflow_ai_eval \
  --evidence falsiflow_ai_eval/evidence.csv \
  --out-dir data/falsiflow/downstream_ready \
  --strict \
  --force
```

The first command sequence should produce `claim_check_blocked`; the second
should produce `claim_check_ready` and exit successfully in strict mode.

## Product Metric Downstream Smoke

Use this when the downstream claim is "activation improved", "conversion
lifted", or "this launch metric is ready to ship." The maintained fixture lives
in
[`examples/downstream_product_metric_smoke`](../examples/downstream_product_metric_smoke).
It mirrors the AI eval smoke: default placeholder evidence blocks CI, and
`evidence_pass_demo.csv` provides source-backed metric, guardrail, and rollback
rows.

Live proof:
[`AzurLiu/falsiflow-downstream-product-metric-demo` PR #1](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1)
shows the first commit blocked by strict CI in
[run 26726360229](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726360229),
then the repair commit passing in
[run 26726392921](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726392921).

Target layout:

```text
.github/workflows/falsiflow-product-metric.yml
falsiflow_product_metric/project.json
falsiflow_product_metric/evidence.csv
falsiflow_product_metric/evidence_pass_demo.csv
falsiflow_product_metric/evidence_placeholder_demo.csv
falsiflow_product_metric/source_files/product_metric_raw_export.csv
```

Expected blocked run:

```bash
cp -R examples/downstream_product_metric_smoke/. /path/to/downstream-repo/
cd /path/to/downstream-repo
git add .github/workflows/falsiflow-product-metric.yml falsiflow_product_metric
git commit -m "Add blocked Falsiflow product metric claim gate"
```

The strict job should fail with `claim_check_blocked` because
`metric_definition_recorded` is still `analysis_pending`.

Expected ready run:

```bash
cp falsiflow_product_metric/evidence_pass_demo.csv falsiflow_product_metric/evidence.csv
git add falsiflow_product_metric/evidence.csv
git commit -m "Add source-backed product metric evidence"
```

The same workflow should pass with `claim_check_ready`, upload JSON and
Markdown summaries, and include `evidence_bundle.zip` plus
`evidence_bundle_verify.md`.

Local reproduction before pushing:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install falsiflow
falsiflow claim-check \
  --project-dir falsiflow_product_metric \
  --evidence falsiflow_product_metric/evidence.csv \
  --out-dir data/falsiflow/product_metric_blocked \
  --force
cp falsiflow_product_metric/evidence_pass_demo.csv falsiflow_product_metric/evidence.csv
falsiflow claim-check \
  --project-dir falsiflow_product_metric \
  --evidence falsiflow_product_metric/evidence.csv \
  --out-dir data/falsiflow/product_metric_ready \
  --strict \
  --force
```

`claim_check_ready` means the activation-rate, retained-user-count, guardrail,
and rollback evidence package is reviewable. It does not prove the product
change caused the metric movement or should ship.

The default `install-command` is intentionally omitted. The action installs
from the checked-out action directory via `GITHUB_ACTION_PATH`, which keeps this
downstream smoke usable before PyPI exists. After a stable release is published,
pin the action to a tag such as `AzurLiu/falsiflow@v0.1.37`; override
`install-command` only when installing from PyPI, a fork, or a local checkout is
part of the thing you are testing.

## Local LLM Eval Import And Claim Gate

Use this when a downstream repository has local/private model artifacts from
Ollama, LM Studio, llama.cpp, MLX, vLLM, or an internal runner. The first action
step converts those artifacts into the Falsiflow evidence CSV; the second step
runs the claim gate. Falsiflow does not run a model, call a hosted model, open
an API port, or judge answer quality itself.

The maintained fixture is
[`examples/local_llm_eval_import`](../examples/local_llm_eval_import).

```yaml
name: Local LLM Eval Evidence Gate

on:
  pull_request:
  push:
    branches: [main]

jobs:
  local-llm-eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Import local LLM eval artifacts
        id: falsiflow_import
        uses: AzurLiu/falsiflow@v0.1.37
        with:
          mode: evidence-import
          profile: local-llm-eval
          input: falsiflow_local_llm_eval/source_files/local_eval_results.jsonl
          manifest: falsiflow_local_llm_eval/local_model_manifest.json
          config: falsiflow_local_llm_eval/project.json
          evidence: falsiflow_local_llm_eval/evidence.csv
          source-file: source_files/local_eval_results.jsonl
          out-dir: data/falsiflow/local_llm_import
          strict: "true"

      - name: Run Falsiflow claim gate
        id: falsiflow
        uses: AzurLiu/falsiflow@v0.1.37
        with:
          mode: claim-check
          project-dir: falsiflow_local_llm_eval
          evidence: falsiflow_local_llm_eval/evidence.csv
          out-dir: data/falsiflow/local_llm_claim_check
          strict: "true"
```

Expected outputs:

- `falsiflow_import.outputs.summary-json` points to `import_summary.json`.
- `data/falsiflow/local_llm_import/import_coverage.json` reports
  `coverage_ready`.
- The claim gate reports `claim_check_ready` only after the imported evidence
  satisfies provenance, benchmark, and reproducibility rows.

## RAG Eval Downstream Claim Gate

Use this when a downstream repository already has RAG eval artifacts from an
eval runner, retrieval harness, or CI job and wants release-note claims to fail
until the evidence rows are source-backed. The bundled
[`rag_quality_gate`](../falsiflow/templates/rag_quality_gate) starter and
[RAG quality gate proposal](falsiflow_rag_quality_gate_proposal.md) define the
small demo contract: evaluation-set provenance, retrieval quality, answer
faithfulness, source coverage, and reproducibility rows.

For a copy-paste downstream repository fixture, use
[`examples/downstream_rag_eval_smoke`](../examples/downstream_rag_eval_smoke):

```bash
cp -R examples/downstream_rag_eval_smoke/. /path/to/downstream-repo/
```

Live proof:
[`AzurLiu/falsiflow-downstream-rag-eval-demo` PR #1](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1)
shows the first commit blocked by strict CI in
[run 26721829145](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721829145),
then the repair commit passing in
[run 26721856616](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721856616).

Target layout:

```text
.github/workflows/falsiflow-rag-eval.yml
falsiflow_rag_eval/project.json
falsiflow_rag_eval/evidence.csv
falsiflow_rag_eval/evidence_pass_demo.csv
falsiflow_rag_eval/evidence_placeholder_demo.csv
falsiflow_rag_eval/source_files/rag_eval_raw_export.csv
```

One-screen Action snippet:

```yaml
name: RAG Eval Evidence Gate

on:
  pull_request:
  push:
    branches: [main]

jobs:
  rag-eval-evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Run Falsiflow RAG claim gate
        id: falsiflow
        uses: AzurLiu/falsiflow@v0.1.37
        with:
          mode: claim-check
          project-dir: falsiflow_rag_eval
          evidence: falsiflow_rag_eval/evidence.csv
          out-dir: data/falsiflow/rag_eval_claim_check
          strict: "true"

      - name: Upload RAG claim reports
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: falsiflow-rag-eval-claim-check
          path: |
            ${{ steps.falsiflow.outputs.summary-json }}
            ${{ steps.falsiflow.outputs.summary-md }}
            data/falsiflow/rag_eval_claim_check/evidence_bundle.zip
            data/falsiflow/rag_eval_claim_check/evidence_bundle_verify.md
```

Expected blocked run:

```bash
cp -R examples/downstream_rag_eval_smoke/. /path/to/downstream-repo/
cd /path/to/downstream-repo
git add .github/workflows/falsiflow-rag-eval.yml falsiflow_rag_eval
git commit -m "Add blocked Falsiflow RAG eval gate"
```

The strict job should fail with `claim_check_blocked` because the placeholder
row keeps evaluation-set provenance unpinned.

Expected ready run:

```bash
cp falsiflow_rag_eval/evidence_pass_demo.csv falsiflow_rag_eval/evidence.csv
git add falsiflow_rag_eval/evidence.csv falsiflow_rag_eval/source_files/rag_eval_raw_export.csv
git commit -m "Add source-backed RAG eval evidence"
```

The same workflow should pass with `claim_check_ready` and upload the JSON,
Markdown, bundle, and bundle-verification reports.

Local reproduction before pushing:

```bash
falsiflow claim-check \
  --project-dir falsiflow_rag_eval \
  --evidence falsiflow_rag_eval/evidence.csv \
  --out-dir data/falsiflow/rag_eval_blocked \
  --force
cp falsiflow_rag_eval/evidence_pass_demo.csv falsiflow_rag_eval/evidence.csv
falsiflow claim-check \
  --project-dir falsiflow_rag_eval \
  --evidence falsiflow_rag_eval/evidence.csv \
  --out-dir data/falsiflow/rag_eval_ready \
  --strict \
  --force
```

This is artifact-first. Falsiflow does not call a hosted model, open an API
port, or judge answer quality itself; it checks the evidence files your RAG eval
runner already produced.

## AI Eval Claim Gate

Use this when the repository already contains a Falsiflow project directory with
`project.json`, `evidence.csv`, and the referenced source files.

```yaml
name: AI Eval Evidence Gate

on:
  pull_request:
  push:
    branches: [main]

jobs:
  ai-eval-evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Run Falsiflow claim gate
        id: falsiflow
        uses: AzurLiu/falsiflow@v0.1.37
        with:
          mode: claim-check
          project-dir: falsiflow_ai_eval
          evidence: falsiflow_ai_eval/evidence.csv
          out-dir: data/falsiflow/ai_eval_claim_check
          strict: "true"

      - name: Upload Falsiflow reports
        uses: actions/upload-artifact@v7
        with:
          name: falsiflow-ai-eval-claim-check
          path: |
            ${{ steps.falsiflow.outputs.summary-json }}
            ${{ steps.falsiflow.outputs.summary-md }}
            data/falsiflow/ai_eval_claim_check/evidence_bundle.zip
            data/falsiflow/ai_eval_claim_check/evidence_bundle_verify.md
```

Expected result:

- `summary-json` points to `claim_check.json`.
- `summary-md` points to `claim_check.md`.
- Passing evidence reports `claim_check_ready`.
- Placeholder, missing metadata, missing source files, or failed thresholds
  report `claim_check_blocked` and fail the job in strict mode.

## Generate A Starter In CI

Use this smoke workflow when you want to prove the action works before adding a
project directory to your repository.

```yaml
name: Falsiflow Starter Smoke

on:
  workflow_dispatch:
  pull_request:

jobs:
  quickstart:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Run AI claim quickstart
        id: falsiflow
        uses: AzurLiu/falsiflow@v0.1.37
        with:
          mode: quickstart
          template: ai_claim_evaluation
          out-dir: data/falsiflow/ai_claim_quickstart
          strict: "true"

      - name: Upload Falsiflow starter reports
        uses: actions/upload-artifact@v7
        with:
          name: falsiflow-ai-claim-quickstart
          path: |
            ${{ steps.falsiflow.outputs.summary-json }}
            ${{ steps.falsiflow.outputs.summary-md }}
            data/falsiflow/ai_claim_quickstart/claim_check/claim_check.json
            data/falsiflow/ai_claim_quickstart/claim_check/claim_check.md
```

Expected result: `quickstart_ready` with a nested `claim_check_ready` report.

## Install Overrides

The default install path is best for tagged action use:

```yaml
- uses: AzurLiu/falsiflow@v0.1.37
  with:
    mode: claim-check
    project-dir: falsiflow_ai_eval
```

Install from PyPI after publication:

```yaml
- uses: AzurLiu/falsiflow@v0.1.37
  with:
    install-command: python -m pip install falsiflow
    mode: claim-check
    project-dir: falsiflow_ai_eval
```

Install from an editable checkout when using `uses: ./` inside this repository:

```yaml
- uses: ./
  with:
    install-command: python -m pip install -e .
    mode: quickstart
    template: ai_claim_evaluation
```

## Reviewer Commands

Run these locally before copying the workflow into a public repository:

```bash
falsiflow quickstart --template ai_claim_evaluation --out falsiflow_ai_demo --strict
falsiflow claim-check --project-dir falsiflow_ai_demo --strict --force
falsiflow release-check --out-dir data/falsiflow/release_check --force
```

## Demo PR Playbook

For a public-ready PR demonstration, use
[falsiflow_demo_pr_playbook.md](falsiflow_demo_pr_playbook.md). It shows the
same AI eval gate moving from `claim_check_blocked` with
`evidence_placeholder_demo.csv` to `claim_check_ready` with
`evidence_pass_demo.csv`, including the copyable workflow and artifact upload
paths.
