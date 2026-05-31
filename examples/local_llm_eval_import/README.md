# Falsiflow Local LLM Eval Import

This directory is a copy-paste fixture for teams that run Ollama, LM Studio,
llama.cpp, MLX, vLLM, or an internal model runner outside Falsiflow.

It starts blocked: `falsiflow_local_llm_eval/evidence.csv` matches
`evidence_placeholder_demo.csv`, so the claim gate reports
`claim_check_blocked`. The repair path imports the local runner artifacts in
`source_files/local_eval_results.jsonl` plus `local_model_manifest.json`, then
the same claim gate reports `claim_check_ready`.

Falsiflow does not run the model, call a hosted model, open an API port, or
judge the answers. It checks that the repo has reviewable evidence artifacts
before CI accepts the claim.

## Local Replay

Run from this directory:

```bash
falsiflow claim-check \
  --project-dir falsiflow_local_llm_eval \
  --evidence falsiflow_local_llm_eval/evidence.csv \
  --out-dir data/falsiflow/local_llm_blocked \
  --force
```

Expected status: `claim_check_blocked`.

Now import the local runner artifacts:

```bash
falsiflow evidence import \
  --profile local-llm-eval \
  --input falsiflow_local_llm_eval/source_files/local_eval_results.jsonl \
  --manifest falsiflow_local_llm_eval/local_model_manifest.json \
  --out falsiflow_local_llm_eval/evidence.csv \
  --summary-out data/falsiflow/local_llm_import/import_summary.json \
  --config falsiflow_local_llm_eval/project.json \
  --coverage-out data/falsiflow/local_llm_import/import_coverage.json \
  --source-file source_files/local_eval_results.jsonl \
  --strict
```

Then rerun the gate:

```bash
falsiflow claim-check \
  --project-dir falsiflow_local_llm_eval \
  --evidence falsiflow_local_llm_eval/evidence.csv \
  --out-dir data/falsiflow/local_llm_ready \
  --strict \
  --force
```

Expected statuses:

```text
placeholder evidence    -> claim_check_blocked
imported local artifacts -> claim_check_ready
import coverage          -> coverage_ready
```

## GitHub Action

The bundled workflow imports the local eval artifacts first, then runs the
claim gate against the generated evidence CSV:

```yaml
- uses: AzurLiu/falsiflow@v0.1.33
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
```

The second action step uses `mode: claim-check` with the generated evidence.

## Artifact Contract

The fixture pins the review facts a local model claim usually needs:

- dataset version and prompt-set hash;
- candidate model id plus local model file hash;
- baseline model id and version;
- eval harness version and script hash;
- deterministic decode settings;
- raw output artifact path;
- human spotcheck result;
- regression CI run URL or local run handle.

Replace the demo values with sanitized artifacts from your own runner before
using this in a real review.
