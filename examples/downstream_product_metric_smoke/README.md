# Falsiflow Downstream Product Metric Smoke

This directory is a copy-paste downstream repository fixture for product-metric
claims. It starts in the blocked state: `falsiflow_product_metric/evidence.csv`
matches `falsiflow_product_metric/evidence_placeholder_demo.csv` and contains
placeholder metric evidence, so the workflow should fail with
`claim_check_blocked`.

## Gates

| Gate | Metric | Threshold |
|------|--------|-----------|
| `activation_gate` | Activation rate | ≥ 40% |
| `conversion_gate` | Conversion rate | ≥ 5% |
| `retention_gate` | Day-7 retention | ≥ 30% |
| `retention_gate` | Day-30 retention | ≥ 15% |

## Copy Into A Clean Repository

```bash
cp -R examples/downstream_product_metric_smoke/. /path/to/downstream-repo/
cd /path/to/downstream-repo
git add .github/workflows/falsiflow-product-metric.yml falsiflow_product_metric
git commit -m "Add blocked Falsiflow product metric claim gate"
```

Open a pull request. The `Falsiflow Product Metric Smoke` workflow should fail
on the placeholder rows in `falsiflow_product_metric/evidence.csv`.

Then repair the PR:

```bash
cp falsiflow_product_metric/evidence_pass_demo.csv falsiflow_product_metric/evidence.csv
git add falsiflow_product_metric/evidence.csv
git commit -m "Add source-backed product metric evidence"
```

The same PR should pass with `claim_check_ready` and upload the JSON, Markdown,
and bundle verification artifacts.

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
placeholder evidence  -> claim_check_blocked
source-backed evidence -> claim_check_ready
```

`claim_check_ready` means the downstream repository supplied the evidence
package required by its own claim gate. It is not proof that the product metric
claim is causally true.

## Boundary

Do not imply the product change is effective. `claim_check_ready` means the
configured evidence package is reviewable, not that the metric is causally true.
