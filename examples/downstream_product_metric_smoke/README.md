# Falsiflow Downstream Product Metric Smoke

This directory is a copy-paste downstream repository fixture for a product
metric claim. It starts in the same state a launch review PR often starts in:
`falsiflow_product_metric/evidence.csv` matches
`falsiflow_product_metric/evidence_placeholder_demo.csv` and contains
placeholder analytics evidence, so the workflow should fail with
`claim_check_blocked`.

## Copy Into A Clean Repository

```bash
cp -R examples/downstream_product_metric_smoke/. /path/to/downstream-repo/
cd /path/to/downstream-repo
git add .github/workflows/falsiflow-product-metric.yml falsiflow_product_metric
git commit -m "Add blocked Falsiflow product metric claim gate"
```

Open a pull request. The `Falsiflow Downstream Product Metric Smoke` workflow
should fail on the placeholder row in `falsiflow_product_metric/evidence.csv`.

Then repair the PR:

```bash
cp falsiflow_product_metric/evidence_pass_demo.csv falsiflow_product_metric/evidence.csv
git add falsiflow_product_metric/evidence.csv
git commit -m "Add source-backed product metric evidence"
```

The same PR should pass with `claim_check_ready` and upload the JSON,
Markdown, bundle, and bundle verification artifacts.

## Local Replay

From the copied downstream repository:

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

Expected statuses:

```text
placeholder evidence   -> claim_check_blocked
source-backed evidence -> claim_check_ready
```

`claim_check_ready` means the downstream repository supplied a reviewable
evidence package for the activation lift, guardrail, and rollback-readiness
claim. It does not prove the product change caused the metric movement or
should ship.
