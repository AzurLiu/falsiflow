# Falsiflow Downstream AI Eval Smoke

This directory is a copy-paste downstream repository fixture. It starts in the
same state a launch-demo PR should start in: `falsiflow_ai_eval/evidence.csv`
matches `falsiflow_ai_eval/evidence_placeholder_demo.csv` and contains
placeholder eval evidence, so the workflow should fail with
`claim_check_blocked`.

## Copy Into A Clean Repository

```bash
cp -R examples/downstream_ai_eval_smoke/. /path/to/downstream-repo/
cd /path/to/downstream-repo
git add .github/workflows/falsiflow-ai-eval.yml falsiflow_ai_eval
git commit -m "Add blocked Falsiflow AI eval claim gate"
```

Open a pull request. The `Falsiflow Downstream AI Eval Smoke` workflow should
fail on the placeholder row in `falsiflow_ai_eval/evidence.csv`.

Then repair the PR:

```bash
cp falsiflow_ai_eval/evidence_pass_demo.csv falsiflow_ai_eval/evidence.csv
git add falsiflow_ai_eval/evidence.csv
git commit -m "Add source-backed AI eval evidence"
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
  --project-dir falsiflow_ai_eval \
  --evidence falsiflow_ai_eval/evidence.csv \
  --out-dir data/falsiflow/downstream_blocked \
  --force

cp falsiflow_ai_eval/evidence_pass_demo.csv falsiflow_ai_eval/evidence.csv

falsiflow claim-check \
  --project-dir falsiflow_ai_eval \
  --evidence falsiflow_ai_eval/evidence.csv \
  --out-dir data/falsiflow/downstream_ready \
  --strict \
  --force
```

Expected statuses:

```text
placeholder evidence  -> claim_check_blocked
source-backed evidence -> claim_check_ready
```

`claim_check_ready` means the downstream repository supplied the evidence
package required by its own claim gate. It is not proof that the model, eval,
or launch claim is correct.
