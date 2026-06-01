# Falsiflow

Stop numeric claims from passing CI until the evidence is reviewable.

Falsiflow checks a project contract, an evidence CSV, and referenced source
files. It returns `claim_ready` only when required evidence exists, placeholder
values are gone, derived metrics compute, thresholds pass, and the review bundle
verifies.

## 30 Seconds

```bash
pipx install falsiflow
git clone https://github.com/AzurLiu/falsiflow
cd falsiflow

EX=examples/minimal_numeric_claim
falsiflow check --config "$EX/project.json" --evidence "$EX/evidence_placeholder.csv" --strict
falsiflow check --config "$EX/project.json" --evidence "$EX/evidence_blocked.csv" --strict
falsiflow check --config "$EX/project.json" --evidence "$EX/evidence_ready.csv" --strict
```

```text
placeholder evidence   -> claim_blocked
weak numeric lift      -> claim_blocked
source-backed evidence -> claim_ready
```

## GitHub Action

```yaml
name: Claim Gate

on:
  pull_request:

jobs:
  claim-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: AzurLiu/falsiflow@v0.2.0
        with:
          config: examples/minimal_numeric_claim/project.json
          evidence: examples/minimal_numeric_claim/evidence_ready.csv
          strict: "true"
```

## What It Is

Falsiflow is a small Python CLI and GitHub Action for gating numeric claims:

- RAG recall improved by a configured threshold.
- A model eval metric beat a baseline.
- A product metric moved enough to ship.
- A vendor, lab, or instrument result meets a spec.

It writes a machine-readable summary, Markdown report, source manifest, and
evidence bundle zip under the chosen output directory.

## What It Is Not

Falsiflow does not prove that a model is good, a RAG answer is safe, a product
metric is causally true, or a scientific claim is correct. It only proves that
the configured evidence package is complete enough to review.
