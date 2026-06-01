# Falsiflow Public Issue Queue

This page keeps the first public issue queue small, concrete, and easy to
verify. Use it after launch posts start receiving feedback, or before launch to
seed contributor-friendly work.

## Queue Rules

- Every issue should name one affected artifact: README, public demo,
  downstream PR, GitHub Action, starter template, adapter profile, or launch
  metrics.
- Every issue should include a verification command or public URL.
- `good first issue` means a newcomer can finish without changing the core
  claim engine.
- `help wanted` means external experience would improve the outcome.
- `launch` issues should be closed or updated during the 24-hour, 72-hour,
  7-day, and 14-day launch review windows.
- Do not request private evidence uploads in public issues.

## Starter Labels

- `launch`: public launch, demo, positioning, or adoption assets.
- `good first issue`: small documentation, demo, fixture, or example work.
- `help wanted`: useful external feedback or implementation help.
- `template`: starter template or template release work.
- `evidence-gate`: claim gate, evidence contract, or provenance behavior.
- `documentation`: README, guide, troubleshooting, or launch copy.

## Active Public Issues

Use this short queue as the public contribution entry point while the first
launch feedback is still small. Keep at least one concrete `good first issue`
open, plus one higher-context `help wanted` issue, so visitors can contribute
without touching the core claim engine.

1. [Run the first launch metrics review](https://github.com/AzurLiu/falsiflow/issues/22)

   Labels: `help wanted`, `launch`

   Goal: review public-post traffic, stars, forks, clone/download signals,
   repeated questions, install failures, and docs gaps using
   `launch_metrics.md`.

   Evidence: update the issue with the 24-hour, 72-hour, 7-day, and 14-day
   review notes and turn repeated external feedback into concrete follow-up
   issues with verification commands.

2. [Add a local LLM eval import proof snippet to the local model guide](https://github.com/AzurLiu/falsiflow/issues/34)

   Labels: `good first issue`, `documentation`, `evidence-gate`

   Goal: give local/private model users a copy-paste proof snippet that imports
   existing eval output and validates the evidence gate without Falsiflow
   opening an API server.

   Evidence: update `docs/falsiflow_local_llm_eval.md` using the existing
   `examples/local_llm_eval_import` fixture, keep the no-model-execution
   boundary explicit, then run
   `python3 scripts/falsiflow.py release-check --out-dir
   /tmp/falsiflow_local_llm_doc_check --force --skip-dist --json`.

## Completed Seed Issues

Create these as public issues before broad launch distribution:

1. Add a launch-article visual for the AI/RAG blocked-to-ready story

   Labels: `good first issue`, `documentation`, `launch`

   Status: completed in
   `docs/launch_articles/stop_shipping_unverifiable_ai_eval_claims.md` by
   [Stop Shipping Unverifiable AI Eval Claims](launch_articles/stop_shipping_unverifiable_ai_eval_claims.md),
   tracked in [issue #29](https://github.com/AzurLiu/falsiflow/issues/29).

   Goal: make the long-form AI eval launch article easier to scan by adding a
   compact visual or existing proof-strip asset near the first third of the
   article.

   Evidence: the article embeds
   `docs/assets/falsiflow_downstream_pr_proof_strip.svg` directly under
   `The Demo That Explains It` with descriptive alt text, a caption, and the
   evidence-package readiness boundary.

2. Add live product-metric proof links to the product metrics launch article

   Labels: `good first issue`, `documentation`, `launch`

   Status: completed in
   `docs/launch_articles/evidence_gates_for_product_metrics.md`, tracked in
   [issue #31](https://github.com/AzurLiu/falsiflow/issues/31).

   Goal: make the product-metric launch article point readers directly to the
   live downstream PR where placeholder launch-metric evidence fails and
   source-backed evidence passes.

   Evidence: the article links the live product-metric PR, blocked run
   `26726360229`, ready run `26726392921`, and the product-impact boundary.

3. Add live benchmark failure proof links to the benchmarks launch article

   Labels: `good first issue`, `documentation`, `launch`

   Status: completed in
   `docs/launch_articles/benchmarks_should_fail_builds.md`, tracked in
   [issue #32](https://github.com/AzurLiu/falsiflow/issues/32).

   Goal: make the benchmark launch article point readers directly to a live PR
   where placeholder benchmark evidence fails and source-backed evidence
   passes.

   Evidence: the article links the live AI eval PR, blocked run `26711652990`,
   ready run `26711669112`, and the benchmark correctness/model-quality
   boundary.

4. Add benchmark proof links to the README proof section

   Labels: `good first issue`, `documentation`, `launch`

   Status: completed in `README.md`, tracked in
   [issue #33](https://github.com/AzurLiu/falsiflow/issues/33).

   Goal: make the README first proof section point readers to the
   benchmark-shaped CI story without lengthening the first screen.

   Evidence: README links
   `docs/launch_articles/benchmarks_should_fail_builds.md`, the live AI eval
   PR, blocked run `26711652990`, ready run `26711669112`, and the
   evidence-package readiness boundary that this is not benchmark correctness
   or model quality.

5. Create a live product-metric downstream PR proof

   Labels: `help wanted`, `template`, `evidence-gate`, `launch`

   Status: completed by
   [AzurLiu/falsiflow-downstream-product-metric-demo PR #1](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1),
   tracked in [issue #30](https://github.com/AzurLiu/falsiflow/issues/30).

   Goal: mirror the live AI/RAG downstream stories for product-metric claims,
   using placeholder evidence that fails as `claim_check_blocked` and
   source-backed evidence that passes as `claim_check_ready`.

   Evidence: the PR failed with `claim_check_blocked` in
   [run 26726360229](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726360229)
   and passed with `claim_check_ready` in
   [run 26726392921](https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726392921)
   after metric provenance, lift, guardrail, and rollback-readiness rows were
   added.

6. Create a live downstream RAG eval claim-gate demo PR

   Labels: `help wanted`, `template`, `evidence-gate`, `launch`

   Status: completed by
   [AzurLiu/falsiflow-downstream-rag-eval-demo PR #1](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1),
   tracked in [issue #27](https://github.com/AzurLiu/falsiflow/issues/27).

   Goal: mirror the live AI eval downstream proof with the bundled
   `rag_quality_gate` starter, including one blocked placeholder CI run and one
   ready source-backed CI run.

   Evidence: the PR failed with `claim_check_blocked` in
   [run 26721829145](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721829145)
   and passed with `claim_check_ready` in
   [run 26721856616](https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721856616)
   after source-backed rows and the raw RAG eval export were added.

7. Generate a release proof snippet from External Evidence artifacts

   Labels: `good first issue`, `documentation`, `release`

   Status: completed by `falsiflow release-proof`, tracked in
   [issue #26](https://github.com/AzurLiu/falsiflow/issues/26).

   Goal: make the public proof contract easier to maintain by generating a
   copy-paste release-note snippet from `external_readiness.json` and
   `falsiflow_external_evidence.json`.

   Evidence: the snippet includes the exact External Evidence run URL,
   `pypi_version_match=passed`, `public_package_claim_check=passed`,
   `claim_check_ready`, `bundle_verified`, and `external_ready`; then
   `release-check` still reports `release_ready`.

8. Add copy-paste MCP client configuration examples

   Labels: `good first issue`, `documentation`, `evidence-gate`

   Status: completed by [docs/falsiflow_mcp.md](falsiflow_mcp.md), tracked in
   [issue #28](https://github.com/AzurLiu/falsiflow/issues/28).

   Goal: add exact stdio client configuration snippets for local MCP use while
   preserving the no-network-listener and no-model-execution boundary.

   Evidence: `docs/falsiflow_mcp.md` includes generic, Claude Desktop, and
   local checkout snippets; `falsiflow mcp --selftest --json` reports
   `mcp_selftest_ready`; and `release-check` still reports `release_ready`.

9. Capture a short downstream PR proof clip

   Labels: `launch`, `documentation`, `good first issue`

   Status: completed by
   `docs/assets/falsiflow_downstream_pr_proof_strip.svg` and tracked in
   [issue #18](https://github.com/AzurLiu/falsiflow/issues/18).

   Goal: add a short GIF/video or screenshot sequence that shows the
   downstream PR moving from `claim_check_blocked` to `claim_check_ready`.

   Evidence: link the downstream PR, blocked run, ready run, and generated
   asset path.

10. Add a local LLM eval quickstart note

   Labels: `documentation`, `help wanted`, `evidence-gate`

   Status: completed by
   [docs/falsiflow_local_llm_eval.md](falsiflow_local_llm_eval.md), the
   `examples/local_llm_eval_import` copy-paste fixture, and tracked in
   [issue #19](https://github.com/AzurLiu/falsiflow/issues/19).

   Goal: show how Ollama, LM Studio, llama.cpp, or another local model runner
   can produce source-backed eval evidence without Falsiflow opening an API
   server.

   Evidence: `falsiflow quickstart --template ai_claim_evaluation`,
   `falsiflow evidence import --profile local-llm-eval`, and
   `falsiflow doctor --strict` still pass.

11. Promote the RAG quality gate proposal toward a starter template

   Labels: `template`, `evidence-gate`, `help wanted`

   Status: completed by the bundled `rag_quality_gate` starter template and
   tracked in [issue #20](https://github.com/AzurLiu/falsiflow/issues/20).

   Goal: turn the documented RAG gate proposal into a bundled template only
   after the evidence contract, raw export fixture, placeholder blocker, and
   responsible-use boundary are clear.

   Evidence: `template-check`, `casebook-check`, and `release-check` pass.

12. Add a product-metric downstream smoke example

   Labels: `template`, `launch`, `good first issue`

   Status: completed by
   `examples/downstream_product_metric_smoke` and tracked in
   [issue #21](https://github.com/AzurLiu/falsiflow/issues/21).

   Goal: mirror the AI eval downstream story for a product metric claim such as
   activation lift, retention change, or conversion improvement.

   Evidence: the example has one blocked placeholder run and one ready
   source-backed run.

13. Run the first launch metrics review

   Labels: `launch`, `help wanted`

   Goal: record the 24-hour launch snapshot after the first public post:
   stars, forks, install friction, repeated questions, demo clicks, and next
   follow-up issues.

   Evidence: update `launch_metrics.md` or a launch review issue with public
   post URLs and the review window.
