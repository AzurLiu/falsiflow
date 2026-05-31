# Falsiflow Downstream RAG Eval Smoke

This directory is a copy-paste downstream repository fixture for a RAG eval
claim. It starts in the same state a release-note PR often starts in:
`falsiflow_rag_eval/evidence.csv` matches
`falsiflow_rag_eval/evidence_placeholder_demo.csv` and contains placeholder
retrieval, faithfulness, citation, and reproducibility evidence, so the
workflow should fail with `claim_check_blocked`.

## Copy Into A Clean Repository

```bash
cp -R examples/downstream_rag_eval_smoke/. /path/to/downstream-repo/
cd /path/to/downstream-repo
git add .github/workflows/falsiflow-rag-eval.yml falsiflow_rag_eval
git commit -m "Add blocked Falsiflow RAG eval claim gate"
```

Open a pull request. The `Falsiflow Downstream RAG Eval Smoke` workflow should
fail on the placeholder row in `falsiflow_rag_eval/evidence.csv`.

Then repair the PR:

```bash
cp falsiflow_rag_eval/evidence_pass_demo.csv falsiflow_rag_eval/evidence.csv
git add falsiflow_rag_eval/evidence.csv
git commit -m "Add source-backed RAG eval evidence"
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

Expected statuses:

```text
placeholder evidence   -> claim_check_blocked
source-backed evidence -> claim_check_ready
```

`claim_check_ready` means the downstream repository supplied a reviewable
evidence package for the RAG eval claim: evaluation-set provenance, retrieval
quality, answer faithfulness, citation/source coverage, and reproducibility.
It does not prove the RAG system is good, safe, or shippable.
