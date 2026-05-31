# Falsiflow Local LLM Eval Quickstart

Falsiflow does not need to run your local model, expose an API port, or receive
cloud credentials. Keep Ollama, LM Studio, llama.cpp, MLX, vLLM, or an internal
runner on your side of the boundary. Falsiflow consumes the evidence artifacts
that runner already produced.

Use this when a claim such as "the local model improved" should stay blocked in
CI until the repository provides reviewable provenance, raw outputs, metric
rows, and reproducibility metadata.

For a maintained copy-paste fixture, see
[`examples/local_llm_eval_import`](../examples/local_llm_eval_import). It
contains a placeholder evidence file that blocks, a local runner JSONL export,
a model manifest, the generated ready evidence demo, and a GitHub Actions
workflow that imports artifacts before running the claim gate.

## Artifact Contract

A local LLM eval handoff should include:

- dataset or task-set version;
- prompt-set hash;
- candidate model id and local model file hash;
- baseline model id or revision;
- evaluator or harness version;
- raw output artifact path;
- item count, score, hallucination or safety boundary, and run metadata;
- deterministic decode settings, seed, or an explicit note when the run is not
  deterministic.

Those values can come from a JSON manifest, JSONL metric rows, CSV exports, or a
small wrapper script around your local runner.

## Copy-Paste Path

```bash
pipx install falsiflow
falsiflow quickstart --template ai_claim_evaluation --out local_llm_eval_gate --strict
cd local_llm_eval_gate
```

Store the raw eval export under `source_files/` so the source manifest can prove
the evidence file exists:

```bash
cat > source_files/local_eval_results.jsonl <<'JSONL'
{"model_id":"candidate_model","metric":"exact_match_rate","value":0.86}
{"model_id":"candidate_model","metric":"hallucination_rate","value":0.035}
{"model_id":"candidate_model","metric":"safety_policy_failure_rate","value":0.012}
{"model_id":"candidate_model","metric":"evaluated_item_count","value":640}
{"model_id":"baseline_model","metric":"exact_match_rate","value":0.78}
{"model_id":"baseline_model","metric":"hallucination_rate","value":0.07}
{"model_id":"baseline_model","metric":"safety_policy_failure_rate","value":0.025}
{"model_id":"baseline_model","metric":"evaluated_item_count","value":640}
JSONL
```

Add the run manifest from your local runner:

```bash
cat > local_model_manifest.json <<'JSON'
{
  "eval_run_id": "eval_run_001",
  "candidate_model_id": "candidate_model",
  "baseline_model_id": "baseline_model",
  "dataset_version": "claims_eval_v2026_05_26",
  "prompt_set_hash": "promptset_sha256_demo",
  "model_file_hash": "gguf_sha256_demo",
  "baseline_model_version": "baseline_llm_2026_05_01",
  "evaluator_version": "eval_harness_0.4.0",
  "eval_script_hash": "eval_script_sha256_demo",
  "decode_params": {"temperature": 0, "top_p": 1, "seed": 7},
  "raw_outputs_uri": "source_files/local_eval_results.jsonl",
  "human_spotcheck_passed": true,
  "ci_run_url": "local://manual-run",
  "runtime": "llama.cpp",
  "quantization": "Q4_K_M",
  "measured_at": "2026-05-26T12:00:00Z"
}
JSON
```

Import the local runner artifacts into the Falsiflow evidence contract:

```bash
falsiflow evidence import \
  --profile local-llm-eval \
  --input source_files/local_eval_results.jsonl \
  --manifest local_model_manifest.json \
  --out evidence.csv \
  --config project.json \
  --coverage-out import_coverage.json \
  --source-file source_files/local_eval_results.jsonl \
  --strict
```

Then run the same checks a reviewer or CI gate can run:

```bash
falsiflow doctor --project-dir . --strict
falsiflow claim-check --config project.json --evidence evidence.csv --out-dir claim_check --strict --force
```

Expected result:

```text
doctor_ready
claim_check_ready
bundle_verified
```

The repository fixture runs the same repair path from checked-in artifacts:

```bash
cd examples/local_llm_eval_import
falsiflow claim-check --project-dir falsiflow_local_llm_eval --evidence falsiflow_local_llm_eval/evidence.csv --out-dir data/falsiflow/local_llm_blocked --force
falsiflow evidence import --profile local-llm-eval --input falsiflow_local_llm_eval/source_files/local_eval_results.jsonl --manifest falsiflow_local_llm_eval/local_model_manifest.json --out falsiflow_local_llm_eval/evidence.csv --summary-out data/falsiflow/local_llm_import/import_summary.json --config falsiflow_local_llm_eval/project.json --coverage-out data/falsiflow/local_llm_import/import_coverage.json --source-file source_files/local_eval_results.jsonl --strict
falsiflow claim-check --project-dir falsiflow_local_llm_eval --evidence falsiflow_local_llm_eval/evidence.csv --out-dir data/falsiflow/local_llm_ready --strict --force
```

## Mapping Runner Outputs

Common local runner fields map naturally into the Falsiflow manifest:

| Runner fact | Manifest field |
| --- | --- |
| Ollama, LM Studio, llama.cpp, MLX, vLLM, or internal harness name | `runtime` |
| GGUF, safetensors, adapter, or model artifact hash | `model_file_hash` or `adapter_hash` |
| Quantization method | `quantization` |
| Temperature, top-p, max tokens, seed | `decode_params` |
| Eval dataset, task set, or prompt collection | `dataset_version`, `prompt_set_hash` |
| Harness or judge revision | `evaluator_version`, `eval_script_hash` |
| Raw model outputs | `raw_outputs_uri` |

If your local runner emits a different JSON shape, keep a tiny normalization
script outside Falsiflow that writes `local_eval_results.jsonl` and
`local_model_manifest.json`. Falsiflow should remain the evidence gate, not the
model runner.

## CI Boundary

In CI, commit or upload sanitized eval artifacts, then run the reusable action:

```yaml
- uses: AzurLiu/falsiflow@v0.1.34
  with:
    mode: evidence-import
    profile: local-llm-eval
    input: local_llm_eval_gate/source_files/local_eval_results.jsonl
    manifest: local_llm_eval_gate/local_model_manifest.json
    config: local_llm_eval_gate/project.json
    evidence: local_llm_eval_gate/evidence.csv
    source-file: source_files/local_eval_results.jsonl
    out-dir: data/falsiflow/local_llm_import
    strict: "true"

- uses: AzurLiu/falsiflow@v0.1.34
  with:
    mode: claim-check
    project-dir: local_llm_eval_gate
    evidence: local_llm_eval_gate/evidence.csv
    out-dir: data/falsiflow/local_llm_claim_check
    strict: "true"
```

`claim_check_ready` means the configured evidence package is complete enough for
review. It does not prove the local model is safe, correct, non-hallucinating,
or better for your product.
