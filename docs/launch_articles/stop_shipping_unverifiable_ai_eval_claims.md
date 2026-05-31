# Stop Shipping Unverifiable AI Eval Claims

AI eval claims often enter release notes as a sentence: "the model improved."
That sentence can hide the parts reviewers actually need: dataset version,
prompt set, model revision, baseline, raw outputs, evaluator settings, and a
clear boundary for what the metric does not prove.

Falsiflow treats that sentence as a claim gate. The claim stays blocked until
evidence rows, source files, metadata, thresholds, audit reports, and bundle
verification agree.

## The Failure Mode

A benchmark headline is easy to copy into a changelog. It is harder to prove
that the benchmark still points to the same evaluation set, that raw outputs
exist, that placeholder rows did not sneak into the CSV, and that the result is
being compared against the intended baseline.

When those pieces are missing, the right release status is not "probably fine."
It is `claim_check_blocked`.

## The Falsiflow Shape

The `ai_claim_evaluation` starter template checks:

- eval provenance: dataset, prompt set, model, baseline, evaluator versions;
- benchmark quality: absolute score, relative improvement, evaluated item
  count, hallucination rate, safety-policy failures;
- reproducibility package: script hash, decode or seed settings, raw output
  archive, human spotcheck, and regression CI run.

The command is intentionally boring:

```bash
falsiflow quickstart --template ai_claim_evaluation --out ai_claim_review --strict
falsiflow doctor --project-dir ai_claim_review --strict
```

The useful part is the output contract. CI gets JSON. Humans get Markdown and
HTML. Reviewers get source manifests and a portable evidence bundle.

## The Boundary

`claim_check_ready` does not mean the model is good, safe, fair, or useful. It
means the supplied evidence passed the configured gate. That boundary is the
point: a tool should make the evidence review repeatable without pretending to
replace expert judgment.

## Launch Angle

For the public launch, lead with the blocked path. Show a placeholder eval row
failing first, then show the same claim becoming ready only after source-backed
evidence exists. That contrast explains Falsiflow faster than a feature list.
