# Falsiflow GitHub Action Examples

This page gives downstream repositories a copy-paste path for running
Falsiflow in CI before PyPI publishing is complete. The reusable action installs
from its versioned action checkout by default through `GITHUB_ACTION_PATH`.
Override `install-command` only when you want to install from PyPI, a fork, or a
repository-local editable checkout.

## Clean Downstream Smoke Repo

Use this recipe when the downstream repository does not contain Falsiflow yet
and you want a copy-paste smoke test before wiring it into real release checks.

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
        uses: AzurLiu/falsiflow@main
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
and Markdown reports show the placeholder evidence repair action.

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

The default `install-command` is intentionally omitted. The action installs
from the checked-out action directory via `GITHUB_ACTION_PATH`, which keeps this
downstream smoke usable before PyPI exists. After a stable release is published,
pin the action to a tag such as `AzurLiu/falsiflow@v0.1.2`; override
`install-command` only when installing from PyPI, a fork, or a local checkout is
part of the thing you are testing.

## AI Eval Claim Gate

Use this when the repository already contains a Falsiflow project directory with
`project.json`, `evidence_pass_demo.csv`, and the referenced source files.

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
        uses: AzurLiu/falsiflow@main
        with:
          mode: claim-check
          project-dir: falsiflow_ai_eval
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
        uses: AzurLiu/falsiflow@main
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
- uses: AzurLiu/falsiflow@main
  with:
    mode: claim-check
    project-dir: falsiflow_ai_eval
```

Install from PyPI after publication:

```yaml
- uses: AzurLiu/falsiflow@main
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
