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

## Seed Issues

Create these as public issues before broad launch distribution:

1. Capture a short downstream PR proof clip

   Labels: `launch`, `documentation`, `good first issue`

   Status: completed by
   `docs/assets/falsiflow_downstream_pr_proof_strip.svg` and tracked in
   [issue #18](https://github.com/AzurLiu/falsiflow/issues/18).

   Goal: add a short GIF/video or screenshot sequence that shows the
   downstream PR moving from `claim_check_blocked` to `claim_check_ready`.

   Evidence: link the downstream PR, blocked run, ready run, and generated
   asset path.

2. Add a local LLM eval quickstart note

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

3. Promote the RAG quality gate proposal toward a starter template

   Labels: `template`, `evidence-gate`, `help wanted`

   Status: completed by the bundled `rag_quality_gate` starter template and
   tracked in [issue #20](https://github.com/AzurLiu/falsiflow/issues/20).

   Goal: turn the documented RAG gate proposal into a bundled template only
   after the evidence contract, raw export fixture, placeholder blocker, and
   responsible-use boundary are clear.

   Evidence: `template-check`, `casebook-check`, and `release-check` pass.

4. Add a product-metric downstream smoke example

   Labels: `template`, `launch`, `good first issue`

   Status: completed by
   `examples/downstream_product_metric_smoke` and tracked in
   [issue #21](https://github.com/AzurLiu/falsiflow/issues/21).

   Goal: mirror the AI eval downstream story for a product metric claim such as
   activation lift, retention change, or conversion improvement.

   Evidence: the example has one blocked placeholder run and one ready
   source-backed run.

5. Run the first launch metrics review

   Labels: `launch`, `help wanted`

   Goal: record the 24-hour launch snapshot after the first public post:
   stars, forks, install friction, repeated questions, demo clicks, and next
   follow-up issues.

   Evidence: update `launch_metrics.md` or a launch review issue with public
   post URLs and the review window.
