# Falsiflow 1k-Star Launch Plan

This plan turns the adoption priorities into concrete public-launch work. It is
not a promise that stars will arrive; it is the checklist for making the project
easy to understand, safe to try, and worth sharing.

## Launch Gate

Do not start broad distribution until these checks are green and linked from
the release notes:

- GitHub Pages public demo loads at <https://azurliu.github.io/falsiflow/>.
- `make test` passes on the release commit.
- `falsiflow release-check --out-dir data/falsiflow/release_check --force`
  reports `release_ready`, `package_ready`, and `adoption_ready`.
- `Falsiflow Publish` has a successful release-triggered `publish-pypi` job.
- `https://pypi.org/pypi/falsiflow/json` reports package `falsiflow` at the
  release version.
- `Falsiflow External Evidence` reports `external_ready` with the public demo,
  PyPI, checkout pipx, public-package pipx, and Windows smoke evidence.

If any item is missing, the launch can still be prepared, but public posts
should say what is still pending instead of implying full external readiness.

## First-Screen Conversion Assets

- README headline: CI gates for claims before they ship.
- Public demo: a ready/blocked proof surface for AI eval, product metric, R&D,
  and vendor handoff claims.
- One command path: `pipx install falsiflow`, with source installs kept for
  contributors.
- Reusable GitHub Action snippet for downstream repositories.
- Maintained downstream smoke fixture:
  `examples/downstream_ai_eval_smoke`.
- Product-metric downstream smoke fixture:
  `examples/downstream_product_metric_smoke`.
- RAG-eval downstream smoke fixture:
  `examples/downstream_rag_eval_smoke`.
- Live downstream AI proof repo:
  <https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo>.
- Live downstream RAG proof repo:
  <https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo>.
- Live downstream product-metric proof repo:
  <https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo>.
- Shareable downstream proof strip:
  [docs/assets/falsiflow_downstream_pr_proof_strip.svg](assets/falsiflow_downstream_pr_proof_strip.svg).
- Comparison boundary: Falsiflow complements Great Expectations, Evidently,
  Deepchecks, MLflow, and plain GitHub Actions rather than replacing them.

## Demo Narrative

The public demo and launch posts should repeat the same compact story:

1. A team writes a claim such as "the model improved" or "activation lifted."
2. Placeholder evidence stays `claim_check_blocked`.
3. Source-backed rows, required metadata, source files, audit reports, and
   bundle verification can make the same claim `claim_check_ready`.
4. `claim_ready` means the configured evidence gate passed. It is not proof of
   scientific truth, safety, regulatory approval, or business impact.

## Distribution Sequence

Day 0:

- Use the current PyPI release, live PR demo, and external-evidence workflow as
  the launch trust baseline.
- Update the release body with the demo URL, PR #17, blocked/ready PR runs,
  PyPI URL, CI runs, publish run, external-evidence workflow, and
  responsible-use boundary.
- Post a concise Show HN or equivalent launch thread.
- Post the longer launch note in one MLOps or evaluation community.
- Share the GitHub Action snippet with a copy-paste downstream smoke example.
  Use `examples/downstream_ai_eval_smoke` as the maintained fixture.
  Link the live downstream PR story:
  <https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1>.
  For RAG-focused readers, link the matching downstream RAG story:
  <https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1>.
  Use `examples/downstream_rag_eval_smoke` as the copy-paste fixture.
  For product/growth readers, link the matching downstream product-metric
  story:
  <https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1>.
  Use `docs/assets/falsiflow_downstream_pr_proof_strip.svg` when a full screen
  recording is too heavy.
- Share `examples/downstream_product_metric_smoke` with product or growth
  engineering readers who care more about activation, conversion, retention,
  guardrail, or rollback-readiness claims than model evals.

Day 1:

- Reply to install failures and unclear positioning questions first.
- Convert repeated questions into issues with labels, owner, affected artifact,
  and verification command.
- Submit to one or two relevant awesome lists only after the README and PyPI
  path are stable.

Day 3:

- Publish the first article draft from `docs/launch_articles/`.
- Add screenshots or short clips captured from the live Pages demo.
- Review traffic, stars, forks, clones, demo visits, installs, and repeated
  questions in `launch_metrics.md`.

Day 7 and Day 14:

- Publish the second and third articles.
- Ship one docs/demo improvement based on real user confusion.
- Add or refine one starter template only if the request includes a clear claim,
  evidence contract, source-file fixture, and responsible-use boundary.

## 1k-Star Workstreams

| Workstream | Outcome | Evidence |
| --- | --- | --- |
| Release trust | PyPI, CI, external evidence, and release notes are coherent. | Release body, CI URLs, PyPI JSON, external-readiness artifact. |
| Fast try | A new visitor can understand and run the project in minutes. | README first screen, Pages demo, quickstart, GitHub Action example. |
| Strong positioning | The project has a crisp reason to exist. | Positioning doc, comparison table, launch posts, replies to common questions. |
| Case breadth | The workflow is not a one-domain toy. | Public casebook, `casebook-check`, AI eval, product metric, R&D, vendor cases. |
| Contribution path | New contributors can help without touching the core engine. | Good-first issues, issue templates, contributing guide, docs/demo tasks. |
| Repeatable launch review | Growth work creates maintainable follow-up, not vague activity. | `launch_metrics.json`, `launch_metrics.md`, weekly maintainer review. |

## Article Drafts

- [Stop Shipping Unverifiable AI Eval Claims](launch_articles/stop_shipping_unverifiable_ai_eval_claims.md)
- [Benchmarks Should Fail Builds](launch_articles/benchmarks_should_fail_builds.md)
- [Evidence Gates For Product Metrics](launch_articles/evidence_gates_for_product_metrics.md)

## Stop Conditions

- Do not publish a release announcement if PyPI returns 404 for the package JSON
  API.
- Do not call the project externally ready until `external-check --strict`
  reports `external_ready`.
- Do not frame stars as quality proof. Track stars as distribution feedback,
  then judge the project by install success, issue quality, contributor pull
  requests, and repeated use cases.
