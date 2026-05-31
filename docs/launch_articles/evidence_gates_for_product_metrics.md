# Evidence Gates For Product Metrics

Product metric claims have the same problem as AI eval claims: the sentence is
short, but the evidence package is not. "Activation improved" should not ship
without a metric definition, experiment identity, exposure, guardrails,
rollback owner, and source-backed analysis.

Falsiflow turns that launch sentence into a gate.

## The Risk

Dashboard screenshots are persuasive but fragile. They can omit assignment
unit, analysis window, sample size, guardrail movement, or whether the metric
definition changed. A launch decision needs those details to be explicit enough
for CI and humans to review.

## The Template

The `product_metric_launch` starter template checks:

- metric provenance: definition, experiment id, assignment unit, analysis
  window, and source file;
- launch metric lift: activation rate, baseline rate, and retained-user
  exposure on both arms;
- guardrail safety: error rate, support-ticket rate, and p95 latency;
- rollback readiness: rollout state, owner, monitoring dashboard, and raw
  evidence.

Run it locally:

```bash
falsiflow quickstart --template product_metric_launch --out product_metric_review --strict
falsiflow doctor --project-dir product_metric_review --strict
```

## What Reviewers Get

Reviewers should not have to scrape CI logs. They should get:

- JSON status for automation;
- Markdown and HTML reports for human review;
- a source manifest for raw evidence files;
- a bundle that can be verified independently;
- a repair checklist when the claim is blocked.

## The Boundary

Falsiflow does not decide whether the product should ship. It decides whether
the configured evidence package is complete enough for the launch claim to be
reviewed. The final product decision still belongs to the team.
