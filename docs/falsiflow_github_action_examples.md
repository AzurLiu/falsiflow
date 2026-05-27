# Falsiflow GitHub Action Examples

This page gives downstream repositories a copy-paste path for running
Falsiflow in CI before PyPI publishing is complete. The reusable action installs
from its versioned action checkout by default through `GITHUB_ACTION_PATH`.
Override `install-command` only when you want to install from PyPI, a fork, or a
repository-local editable checkout.

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

