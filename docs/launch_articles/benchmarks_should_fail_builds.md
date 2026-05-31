# Benchmarks Should Fail Builds

Benchmarks often live outside the release gate. They appear in notebooks,
spreadsheets, dashboards, or screenshots, then someone copies the conclusion
into a pull request. By then the benchmark has become prose, not evidence.

If a benchmark can justify shipping, it should also be able to fail the build.

## Live Proof

The benchmark-shaped version of the blocked-to-ready story is live in
[AzurLiu/falsiflow-downstream-ai-eval-demo PR #1](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1).
The first PR state kept eval provenance at `dataset_pending`, so strict CI
failed in
[run 26711652990](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990)
with `claim_check_blocked`. After source-backed benchmark-quality rows and the
raw eval export were added, the same PR passed in
[run 26711669112](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112)
with `claim_check_ready`.

That boundary matters: Falsiflow validates that the benchmark claim has a
reviewable evidence package. It does not decide benchmark correctness, model
quality, or whether the claimed improvement should ship. Keep using your
trusted eval harness for scoring; use Falsiflow to stop incomplete benchmark
evidence from becoming release copy.

## What Should Fail

The build should fail when:

- the benchmark references a missing raw source file;
- metadata such as dataset version, sample count, or operator is blank;
- a placeholder marker stands in for a measured value;
- the result fails a configured threshold;
- the bundle that reviewers depend on cannot be verified.

That does not require turning CI into a research platform. It requires a small
contract around the claim being promoted.

## What Falsiflow Adds

Plain CI can run any script. Falsiflow adds a stable evidence contract around a
claim:

- `project.json` declares the claim, gates, thresholds, and source policy;
- evidence CSV rows record measured values and metadata;
- source manifests prove referenced raw files are present;
- audit reports explain ready or blocked status;
- evidence bundles let humans review the same artifacts CI checked.

The output is not "the script exited 0." It is a reviewable
`claim_check_ready` or `claim_check_blocked` status.

## Where This Fits

Use the benchmark tool you already trust for scoring. Use Falsiflow when the
score becomes a claim that can move a release, launch, vendor handoff, or R&D
decision. The benchmark remains evidence; Falsiflow decides whether the evidence
package is complete enough to promote the claim.

## Try It

```bash
falsiflow quickstart --template ai_claim_evaluation --out benchmark_gate --strict
falsiflow claim-check --project-dir benchmark_gate --strict --force
```

Swap in the placeholder evidence CSV and the same path should block. That is
the behavior worth showing in public demos.
