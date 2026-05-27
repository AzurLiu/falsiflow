# Falsiflow RAG Quality Gate Proposal

This proposal defines a small starter template for retrieval-augmented
generation quality claims. It is intentionally not a bundled template yet. The
goal is to make the evidence contract clear enough that a contributor can turn
it into `examples/falsiflow/rag_quality_gate/` with `template-check` coverage.

## Template Sketch

- Template id: `rag_quality_gate`
- Domain: `rag-quality-and-citation-claims`
- Claim statement: "A RAG system is ready to claim improved answer quality only
  after evaluation-set provenance, retrieval quality, answer faithfulness,
  source coverage, and reproducibility gates pass."
- Positive demo evidence: `evidence_pass_demo.csv`
- Placeholder demo evidence: `evidence_placeholder_demo.csv`
- Primary source root: `source_files/`

## Required Source Files

The first version should keep all evidence local and reviewable:

- `source_files/rag_eval_manifest.json`: evaluation-set version, query-set hash,
  prompt-set hash, retriever index version, generator model version, baseline
  version, evaluator version, and evaluation timestamp.
- `source_files/retrieval_runs.jsonl`: per-query retrieved document ids,
  ranks, scores, and citation candidates.
- `source_files/answer_judgments.csv`: answer faithfulness, unsupported-answer
  labels, citation precision, and human spotcheck decisions.
- `source_files/source_attribution_report.csv`: source coverage, citation
  coverage, and missing-source findings.
- `source_files/regression_ci_run.txt`: public or internal CI run identifier for
  the replayed evaluation.

## Gates And Evidence Fields

### Evaluation Provenance

Required rows for candidate system `candidate_rag` and sample `rag_eval_001`:

- `eval_set_version_recorded == true`
- `query_set_hash_recorded == true`
- `prompt_set_hash_recorded == true`
- `retriever_index_version_recorded == true`
- `candidate_rag_version_recorded == true`
- `baseline_rag_version_recorded == true`
- `evaluator_version_recorded == true`

### Retrieval Quality

Required rows for `candidate_rag` and `baseline_rag`:

- `evaluated_query_count >= 200`
- `recall_at_5 >= 0.82` for `candidate_rag`
- `mrr_at_10 >= 0.70` for `candidate_rag`
- `retrieval_coverage_rate >= 0.95` for `candidate_rag`
- `recall_ratio_vs_baseline >= 1.05` as a derived metric

### Answer Faithfulness

Required rows for `candidate_rag`:

- `faithfulness_score >= 0.88`
- `grounded_answer_rate >= 0.92`
- `unsupported_answer_rate <= 0.04`
- `safety_policy_failure_rate <= 0.02`
- `human_spotcheck_passed == true`

### Source Coverage

Required rows for `candidate_rag`:

- `citation_precision >= 0.90`
- `source_coverage_rate >= 0.95`
- `missing_source_rate <= 0.03`
- `citation_audit_passed == true`

### Reproducibility Package

Required rows for `candidate_rag`:

- `raw_retrieval_runs_archived == true`
- `raw_answer_outputs_archived == true`
- `eval_script_hash_recorded == true`
- `random_seed_or_decode_settings_logged == true`
- `regression_ci_run_recorded == true`

## Placeholder Blocked Row

The placeholder demo should stay small and obviously blocked:

```csv
gate_id,candidate_id,sample_id,field,value,source_file,measured_at,operator_or_agent,instrument_id,notes
evaluation_provenance,candidate_rag,rag_eval_001,eval_set_version_recorded,eval_set_pending,source_files/rag_eval_manifest.json,2026-05-26T08:00:00Z,falsiflow_rag_eval_operator,rag_eval_harness_001,Placeholder eval-set version should block readiness.
```

Expected result: `claim_check_blocked`. The placeholder marker
`eval_set_pending` means the evaluation-set provenance is not pinned, so the
claim cannot become reviewable.

## Positive Demo Row

The positive demo should include the full set of rows above. A representative
source-backed row:

```csv
gate_id,candidate_id,sample_id,field,value,source_file,measured_at,operator_or_agent,instrument_id,notes
retrieval_quality,candidate_rag,rag_eval_001,recall_at_5,0.86,source_files/retrieval_runs.jsonl,2026-05-26T09:00:00Z,falsiflow_rag_eval_operator,rag_eval_harness_001,Candidate retriever recall over the pinned query set.
```

Expected result after all required rows and source files are present:
`claim_check_ready`.

## Acceptance Rule Sketch

The future `project.json` should include:

- `evaluation_provenance` with boolean equality rules for version, hash, and
  evaluator fields.
- `retrieval_quality` with absolute rules for recall, MRR, coverage, and item
  count, plus a derived `recall_ratio_vs_baseline` rule.
- `answer_faithfulness` with faithfulness, grounded-answer, unsupported-answer,
  safety, and human spotcheck rules.
- `source_coverage` with citation precision, source coverage, missing-source,
  and audit rules.
- `reproducibility_package` with raw output archive, script hash, decode
  settings, and CI run rules.

## Template Admission Checklist

Before bundling the template:

- Create `examples/falsiflow/rag_quality_gate/template.json`.
- Create `examples/falsiflow/rag_quality_gate/project.json`.
- Create `evidence_placeholder_demo.csv` with the blocked placeholder row.
- Create `evidence_pass_demo.csv` with every required row.
- Create the five required files under `source_files/`.
- Keep placeholder markers in `evidence_policy.placeholder_markers`, including
  `eval_set_pending`, `retrieval_pending`, `judgment_pending`, and `todo`.
- Add the template to the public casebook only after positive and blocked-path
  proof both pass.

## Verification Target

The finished template should pass:

```bash
python3 scripts/falsiflow.py template-check \
  --template-dir examples/falsiflow/rag_quality_gate \
  --out-dir data/falsiflow/rag_quality_gate_check \
  --force
```

It should also be covered by `falsiflow casebook-check` before it becomes a
bundled public starter.
