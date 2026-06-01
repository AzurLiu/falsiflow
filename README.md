# Falsiflow

Stop unverifiable AI eval, RAG eval, product metric, and R&D claims from
passing CI.

![Falsiflow downstream PR proof strip](https://raw.githubusercontent.com/AzurLiu/falsiflow/main/docs/assets/falsiflow_downstream_pr_proof_strip.png)

[![Falsiflow](https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow.yml/badge.svg)](https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow.yml)
[![Cross Platform](https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow-cross-platform.yml/badge.svg)](https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow-cross-platform.yml)
[![Scorecard](https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow-scorecard.yml/badge.svg)](https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow-scorecard.yml)

Public demo: <https://azurliu.github.io/falsiflow/>. PyPI trusted publishing:
completed. Current release: `v0.1.39`.

## 30 Seconds

```bash
pipx install falsiflow
falsiflow quickstart --template ai_claim_evaluation --out falsiflow_ai_demo --strict
falsiflow doctor --project-dir falsiflow_ai_demo --strict
```

```text
quickstart             -> quickstart_ready
placeholder evidence   -> claim_check_blocked
source-backed evidence -> claim_check_ready
```

Falsiflow turns vague claims like "the model improved" into a checked evidence
package: project contract, evidence CSV, source files, source manifest, review
report, and bundle verification.

## Live Proof

Three public PRs show the same story: placeholder claims fail in CI; source
evidence is added; the PR becomes ready.

| Claim | Blocked | Ready |
| --- | --- | --- |
| [AI eval PR #1](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1) | [run 26711652990](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990) | [run 26711669112](https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112) |
| [RAG eval PR #1](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1) | [run 26721829145](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721829145) | [run 26721856616](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721856616) |
| [Product metric PR #1](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1) | [run 26726360229](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726360229) | [run 26726392921](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726392921) |

The shareable asset is
[docs/assets/falsiflow_downstream_pr_proof_strip.svg](docs/assets/falsiflow_downstream_pr_proof_strip.svg).
The live in-repo story is [PR #17](https://github.com/AzurLiu/falsiflow/pull/17):
[blocked run](https://github.com/AzurLiu/falsiflow/actions/runs/26708459093)
then [ready run](https://github.com/AzurLiu/falsiflow/actions/runs/26708472653).

Falsiflow proves evidence-package readiness. It does not prove benchmark
correctness, model quality, RAG answer quality, RAG safety, or product impact.

## GitHub Action

```yaml
name: Falsiflow

on:
  pull_request:
  workflow_dispatch:

jobs:
  claim-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: AzurLiu/falsiflow@v0.1.39
        with:
          mode: claim-check
          project-dir: falsiflow_ai_eval
          evidence: falsiflow_ai_eval/evidence.csv
          strict: "true"
```

Downstream examples:
[AI eval](examples/downstream_ai_eval_smoke),
[RAG eval](examples/downstream_rag_eval_smoke),
[product metric](examples/downstream_product_metric_smoke), and
[local LLM import](examples/local_llm_eval_import). More Action examples live
in [docs/falsiflow_github_action_examples.md](docs/falsiflow_github_action_examples.md).

## What It Is / Is Not

Falsiflow is:

- a local-first Python CLI and GitHub Action for claim gates;
- an evidence-package checker for AI eval, RAG eval, product metric, vendor, and
  R&D claims;
- a way to require source-backed evidence, provenance, thresholds, raw files,
  and bundle verification before CI passes.

Falsiflow is not:

- a model runner, hosted judge, RAG framework, experiment tracker, or API
  service;
- a replacement for human review, benchmark design, statistical analysis, or
  deployment approval;
- a place to upload private eval output. Local/private model artifacts are
  imported from files and checked in the repo or private runner.

## Use Cases

### AI eval

Use Falsiflow when a PR claims "model B improved over model A" and should prove
dataset version, prompt set hash, candidate and baseline model ids, evaluator
version, raw output artifact, metric rows, thresholds, and CI run metadata.

Start from
[examples/downstream_ai_eval_smoke](examples/downstream_ai_eval_smoke) or the
`ai_claim_evaluation` quickstart.

### RAG eval

Use Falsiflow when a PR claims retrieval or answer quality improved and should
prove eval-set provenance, query hash, RAG versions, judge version, retrieval
metrics, answer/source metrics, raw artifacts, and reproducibility metadata.

RAG import proof path:
[docs/falsiflow_rag_quality_gate_proposal.md](docs/falsiflow_rag_quality_gate_proposal.md)
and [examples/downstream_rag_eval_smoke](examples/downstream_rag_eval_smoke)
show `coverage_ready`, `claim_check_ready`, and the RAG evidence-package
readiness boundary with `--profile rag-eval`.

### Product metric

Use Falsiflow when a launch or experiment claim says activation, retention,
conversion, or another product metric moved and the PR should prove source
metric export, baseline, lift, guardrail, rollback readiness, and review notes.

Start from
[examples/downstream_product_metric_smoke](examples/downstream_product_metric_smoke)
or the article
[Evidence Gates For Product Metrics](docs/launch_articles/evidence_gates_for_product_metrics.md).

## More Docs

- Local LLM/private runner imports:
  [docs/falsiflow_local_llm_eval.md](docs/falsiflow_local_llm_eval.md) and
  [examples/local_llm_eval_import](examples/local_llm_eval_import).
- Adapter profiles for `vendor-measurement`, `instrument-export`,
  `plate-reader`, `ai-eval`, `local-llm-eval`, and `rag-eval`:
  [docs/falsiflow_adapter_profiles.md](docs/falsiflow_adapter_profiles.md).
- Data contract and schemas:
  [docs/falsiflow_data_contract.md](docs/falsiflow_data_contract.md),
  [docs/falsiflow_cli_reference.md](docs/falsiflow_cli_reference.md).
- Architecture and boundaries:
  [docs/falsiflow_architecture.md](docs/falsiflow_architecture.md),
  [docs/falsiflow_positioning.md](docs/falsiflow_positioning.md),
  [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md).
- MCP/local agent integration:
  [docs/falsiflow_mcp.md](docs/falsiflow_mcp.md).
- Public casebook and demo playbook:
  [docs/falsiflow_public_casebook.md](docs/falsiflow_public_casebook.md),
  [docs/falsiflow_demo_pr_playbook.md](docs/falsiflow_demo_pr_playbook.md).
- Template authoring and casebook checks:
  [docs/falsiflow_template_authoring.md](docs/falsiflow_template_authoring.md),
  [docs/falsiflow_casebook_check.md](docs/falsiflow_casebook_check.md).
- Troubleshooting, security, support, roadmap, citation, and governance:
  [docs/falsiflow_troubleshooting.md](docs/falsiflow_troubleshooting.md),
  [docs/falsiflow_security_posture.md](docs/falsiflow_security_posture.md),
  [SUPPORT.md](SUPPORT.md), [ROADMAP.md](ROADMAP.md),
  [CITATION.cff](CITATION.cff), [GOVERNANCE.md](GOVERNANCE.md).

## Release Posture

`v0.1.39` is the current PyPI and GitHub release. Patch releases are frozen
unless a real correctness, packaging, or security issue appears. The next
planned public launch release should be:

```text
v0.2.0: AI/RAG/Product Claim Gate Launch
```
