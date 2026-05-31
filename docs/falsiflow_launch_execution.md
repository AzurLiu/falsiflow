# Falsiflow Launch Execution

This page turns the 1k-star launch plan into concrete copy, channels, and
follow-up checks. Use it after the current public release evidence is green.

## Launch State

- Repository: <https://github.com/AzurLiu/falsiflow>
- Public demo: <https://azurliu.github.io/falsiflow/>
- PyPI: <https://pypi.org/project/falsiflow/>
- Release: <https://github.com/AzurLiu/falsiflow/releases/latest>
- External evidence workflow:
  <https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow-external-evidence.yml>
- Live downstream AI demo repo:
  <https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo>
- Live downstream AI PR:
  <https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1>
- Downstream AI blocked run:
  <https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990>
- Downstream AI ready run:
  <https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112>
- Live downstream RAG demo repo:
  <https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo>
- Live downstream RAG PR:
  <https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1>
- Downstream RAG blocked run:
  <https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721829145>
- Downstream RAG ready run:
  <https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721856616>
- Live downstream product-metric demo repo:
  <https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo>
- Live downstream product-metric PR:
  <https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1>
- Downstream product-metric blocked run:
  <https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726360229>
- Downstream product-metric ready run:
  <https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726392921>
- Shareable downstream proof strip:
  [docs/assets/falsiflow_downstream_pr_proof_strip.svg](assets/falsiflow_downstream_pr_proof_strip.svg)
- Live PR demo: <https://github.com/AzurLiu/falsiflow/pull/17>
- Blocked PR run: <https://github.com/AzurLiu/falsiflow/actions/runs/26708459093>
- Ready PR run: <https://github.com/AzurLiu/falsiflow/actions/runs/26708472653>
- Social preview source: run
  `falsiflow launch-kit --out-dir falsiflow_launch_kit --force`, then review
  and upload `social_preview.png` in GitHub repository settings.
- Pre-public-post baseline recorded on 2026-06-01 05:49 CST after the
  upload-ready social preview release:
  0 stars, 2 forks, 0 watchers, 8 total views, 1 unique view, 466 total clones,
  283 unique clones, open issues #22 and #31, completed seed issues #26, #27, #28, #29, and #30, and open PR #17.
  Treat clone counts as likely inflated by CI/release automation until
  public-post traffic arrives.
- Latest external evidence workflow:
  <https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow-external-evidence.yml>

## One-Line Positioning

Falsiflow is a Python CLI and GitHub Action that keeps AI eval, product metric,
R&D, and vendor handoff claims blocked until the evidence package is complete.

## Public Issue Queue

Before broad launch distribution, seed a small public queue from
[falsiflow_public_issue_queue.md](falsiflow_public_issue_queue.md). The current
pre-launch queue keeps
[issue #22](https://github.com/AzurLiu/falsiflow/issues/22) open for the
24-hour post-public-post metrics review,
[issue #31](https://github.com/AzurLiu/falsiflow/issues/31) open as a
`good first issue` for product-metric launch-article proof links,
[issue #29](https://github.com/AzurLiu/falsiflow/issues/29) completed by the
launch-article blocked-to-ready visual, and
[issue #30](https://github.com/AzurLiu/falsiflow/issues/30) completed by the
live product-metric downstream PR proof. Completed seed issues #26, #27, #28,
#29, and #30 cover release proof snippet generation, the live downstream RAG
eval demo PR, MCP client configuration examples, launch-article visual polish,
and the live downstream product-metric demo PR.
Summary phrase for release checks: release proof snippet generation, live downstream RAG eval demo, MCP client configuration examples, launch-article visual polish, product-metric downstream proof.
New public issues after launch should come from repeated external feedback, not
from internal polish already completed before distribution.

## Show HN

Title:

```text
Show HN: Falsiflow - stop unverifiable AI eval claims from passing CI
```

URL:

```text
https://github.com/AzurLiu/falsiflow
```

First comment:

```text
I built Falsiflow for the moment a team writes "the model improved",
"activation went up", or "this experiment is ready" and the sentence starts
moving toward a release note.

Falsiflow turns that sentence into a CI gate. A placeholder claim stays
claim_check_blocked. A source-backed claim can become claim_check_ready only
when required rows, metadata, source files, audit reports, and bundle
verification line up.

The current release is intentionally small and boring:

- pipx install falsiflow
- GitHub Action support for downstream repos
- real downstream PR where placeholder AI eval evidence fails CI, then
  source-backed evidence passes:
  https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1
- blocked run:
  https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990
- ready run:
  https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112
- real downstream RAG PR where placeholder/missing RAG evidence fails CI, then
  raw source-backed evidence passes:
  https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1
- RAG blocked run:
  https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721829145
- RAG ready run:
  https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721856616
- real downstream product-metric PR where placeholder launch-metric evidence
  fails CI, then source-backed metric provenance, lift, guardrail, and rollback
  evidence passes:
  https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1
- product-metric blocked run:
  https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726360229
- product-metric ready run:
  https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726392921
- public demo: https://azurliu.github.io/falsiflow/
- PyPI: https://pypi.org/project/falsiflow/
- external evidence workflow proving demo, PyPI, pipx, and Windows smoke:
  https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow-external-evidence.yml

Boundary: claim_ready does not mean the model is safe, the product should ship,
or the science is true. It means the configured evidence package passed and is
ready for human review.

I would especially like feedback on the evidence contract, the GitHub Action
shape, and whether the blocked/ready demo explains the idea quickly enough.
```

## MLOps Community Post

Title:

```text
Falsiflow: fail CI when AI eval or product metric claims lack evidence
```

Body:

```text
I released Falsiflow, a Python CLI and GitHub Action for evidence-gating
claims before they ship.

The problem it targets is not scoring itself. Teams already have benchmark
tools, dashboards, notebooks, and eval harnesses. The weak point is when a score
becomes a claim in a PR, release note, launch doc, or vendor handoff.

Falsiflow makes that claim reviewable:

- project.json declares the claim, gates, thresholds, and source policy
- evidence CSV rows record measured values and required metadata
- source manifests prove raw files exist
- audit reports explain ready or blocked status
- bundles let humans inspect the same artifacts CI checked

Install:

pipx install falsiflow
falsiflow quickstart --template ai_claim_evaluation --out ai_claim_review --strict

Demo: https://azurliu.github.io/falsiflow/
Live downstream PR: https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1
Blocked run: https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990
Ready run: https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112
RAG downstream PR: https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1
RAG blocked run: https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721829145
RAG ready run: https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721856616
Product metric downstream PR: https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1
Product metric blocked run: https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726360229
Product metric ready run: https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726392921
Repo: https://github.com/AzurLiu/falsiflow
PyPI: https://pypi.org/project/falsiflow/

I am looking for feedback on where this should sit alongside Great Expectations,
Evidently, Deepchecks, MLflow, and plain GitHub Actions. My current framing is:
use those tools for measurement and pipelines; use Falsiflow when a measurement
becomes a claim that should fail a build if its evidence package is incomplete.
```

## Short Social Posts

LinkedIn:

```text
I released Falsiflow.

It is a Python CLI and GitHub Action for one specific problem: claims like "the
model improved", "activation lifted", or "the experiment is ready" should not
ship unless the evidence package is complete.

Falsiflow keeps placeholder claims claim_check_blocked and lets source-backed
claims become claim_check_ready only after required rows, metadata, source
files, audit reports, and bundle verification line up.

Demo: https://azurliu.github.io/falsiflow/
Live downstream PR: https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1
Blocked run: https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990
Ready run: https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112
RAG downstream PR: https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1
RAG blocked run: https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721829145
RAG ready run: https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721856616
Product metric downstream PR: https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1
Product metric blocked run: https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726360229
Product metric ready run: https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726392921
Repo: https://github.com/AzurLiu/falsiflow
PyPI: https://pypi.org/project/falsiflow/
```

X / short post:

```text
Released Falsiflow.

It fails CI when AI eval, product metric, R&D, or vendor handoff claims do not
have enough evidence to review.

pipx install falsiflow

Demo: https://azurliu.github.io/falsiflow/
Downstream PR: https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1
RAG downstream PR: https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1
Product metric downstream PR: https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1
Repo: https://github.com/AzurLiu/falsiflow
```

## Awesome-List Candidates

Submit only after the first public feedback pass, and open small PRs with a
neutral one-line description.

- Awesome AI Eval: <https://github.com/Vvkmnn/awesome-ai-eval>
- Awesome MLOps: <https://github.com/kelvins/awesome-mlops>
- Awesome data quality: <https://github.com/MigoXLab/awesome-data-quality>
- Awesome Actions: <https://github.com/sdras/awesome-actions>

Suggested entry:

```markdown
- [Falsiflow](https://github.com/AzurLiu/falsiflow) - Python CLI and GitHub
  Action that gates AI eval, product metric, R&D, and vendor handoff claims on
  source-backed evidence before they ship.
```

## Reply Bank

What is this replacing?

```text
It is not trying to replace Great Expectations, Evidently, Deepchecks, MLflow,
or GitHub Actions. Those tools are useful for checks, monitoring, evals, and
pipelines. Falsiflow sits at the promotion step: when a result becomes a claim,
it asks whether the evidence package is complete enough to review.
```

Does `claim_ready` mean the claim is true?

```text
No. `claim_ready` means the configured gate passed and the evidence package is
complete enough for review. It does not prove scientific truth, safety,
regulatory compliance, or product impact.
```

Why a CSV instead of a database?

```text
The first release optimizes for boring reviewability. CSV, JSON, Markdown, HTML,
and zip bundles make it easy to inspect artifacts in CI and in a pull request.
Connectors can come later if repeated users need them.
```

## Metrics Review Windows

Record snapshots at 24 hours, 72 hours, 7 days, and 14 days after the first
public post.

| Window | Signals | Action |
| --- | --- | --- |
| 24 hours | stars, forks, install failures, repeated questions | Fix README/demo confusion first. |
| 72 hours | issue quality, community replies, PyPI install path, demo clicks | Convert repeated confusion into issues. |
| 7 days | stars, forks, clone/download trend, first external PRs | Publish the first article and one docs improvement. |
| 14 days | contribution activity, repeated use cases, awesome-list outcomes | Add or refine one starter template only if demand is concrete. |

## Do Not Overclaim

- Do not call stars a quality signal.
- Do not imply Falsiflow proves a model, launch, or experiment is correct.
- Do not post the same copy into multiple communities without adapting it.
- Do not submit to awesome lists until the README, PyPI, demo, and evidence
  links stay stable after the first feedback pass.
