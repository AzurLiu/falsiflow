# Falsiflow RAG Quality Gate Proposal

This proposal has been promoted into the bundled `rag_quality_gate` starter
template for retrieval-augmented generation quality claims. The goal is to keep
the evidence contract small enough to understand, while still proving
`template-check`, `casebook-check`, and `claim-check` can block unsupported RAG
claims in CI.

## Template Sketch

- Template id: `rag_quality_gate`
- Domain: `rag-quality-and-citation-claims`
- Claim statement: "A RAG quality claim is ready for release notes only after
  evaluation-set provenance, retrieval quality, answer faithfulness, source
  coverage, and reproducibility gates pass."
- Positive demo evidence: `evidence_pass_demo.csv`
- Placeholder demo evidence: `evidence_placeholder_demo.csv`
- Primary source root: `source_files/`

## Required Source Files

The bundled first version keeps all demo evidence local and reviewable:

- `source_files/rag_eval_raw_export.csv`: compact demo export containing the
  manifest, retrieval metrics, answer judgments, source coverage, and artifact
  rows. Real projects can point rows at separate JSON, JSONL, CSV, and CI
  artifacts.

## Gates And Evidence Fields

### Evaluation Provenance

Required rows for candidate system `candidate_rag` and sample `rag_eval_001`:

- `eval_set_version_recorded == true`
- `query_set_hash_recorded == true`
- `candidate_rag_version_recorded == true`
- `baseline_rag_version_recorded == true`
- `judge_version_recorded == true`

### Retrieval Quality

Required rows for `candidate_rag` and `baseline_rag`:

- `recall_at_5 >= 0.82` for `candidate_rag`
- `mrr_at_10 >= 0.70` for `candidate_rag`
- `retrieval_coverage_rate >= 0.95` for `candidate_rag`
- `recall_ratio_vs_baseline >= 1.05` as a derived metric

### Answer Faithfulness

Required rows for `candidate_rag`:

- `faithfulness_rate >= 0.92`
- `unsupported_answer_rate <= 0.04`
- `answer_correctness_rate >= 0.84`
- `judged_item_count >= 300`

### Source Coverage

Required rows for `candidate_rag`:

- `citation_precision >= 0.90`
- `source_coverage_rate >= 0.95`
- `missing_source_rate <= 0.02`

### Reproducibility Package

Required rows for `candidate_rag`:

- `retrieval_run_archived == true`
- `raw_answers_archived == true`
- `eval_script_hash_recorded == true`
- `regression_ci_run_recorded == true`

## Placeholder Blocked Row

The placeholder demo should stay small and obviously blocked:

```csv
gate_id,candidate_id,sample_id,field,value,source_file,measured_at,operator_or_agent,instrument_id,notes
evaluation_provenance,candidate_rag,rag_eval_001,eval_set_version_recorded,eval_set_pending,source_files/rag_eval_raw_export.csv,2026-05-26T08:00:00Z,falsiflow_rag_eval_operator,rag_eval_harness_001,Placeholder eval-set version should block readiness.
```

Expected result: `claim_check_blocked`. The placeholder marker
`eval_set_pending` means the evaluation-set provenance is not pinned, so the
claim cannot become reviewable.

## Positive Demo Row

The positive demo should include the full set of rows above. A representative
source-backed row:

```csv
gate_id,candidate_id,sample_id,field,value,source_file,measured_at,operator_or_agent,instrument_id,notes
retrieval_quality,candidate_rag,rag_eval_001,recall_at_5,0.86,source_files/rag_eval_raw_export.csv,2026-05-26T09:00:00Z,falsiflow_rag_eval_operator,rag_eval_harness_001,Candidate retriever recall over the pinned query set.
```

Expected result after all required rows and source files are present:
`claim_check_ready`.

## Acceptance Rule Sketch

The bundled `project.json` includes:

- `evaluation_provenance` with boolean equality rules for version, hash, and
  evaluator fields.
- `retrieval_quality` with absolute rules for recall, MRR, coverage, plus a
  derived `recall_ratio_vs_baseline` rule.
- `answer_faithfulness` with faithfulness, unsupported-answer, correctness,
  and judged-item-count rules.
- `source_coverage` with citation precision, source coverage, and
  missing-source rules.
- `reproducibility_package` with raw output archive, script hash, and CI run
  rules.

## Template Admission Checklist

Before changing the bundled template:

- Keep `examples/falsiflow/rag_quality_gate/` and
  `falsiflow/templates/rag_quality_gate/` mirrored.
- Keep `evidence_placeholder_demo.csv` blocked by `eval_set_pending`.
- Keep `evidence_pass_demo.csv` source-backed for every required row.
- Keep placeholder markers in `evidence_policy.placeholder_markers`, including
  `eval_set_pending`, `query_hash_pending`, `rag_version_pending`, and `todo`.
- Run `template-check`, `casebook-check`, and `release-check` after changing
  gates, rows, or source files.

## Verification Target

The template should pass:

```bash
python3 scripts/falsiflow.py template-check \
  --template-dir examples/falsiflow/rag_quality_gate \
  --out-dir data/falsiflow/rag_quality_gate_check \
  --strict \
  --force
```

It is also covered by `falsiflow casebook-check` as a bundled public starter.
