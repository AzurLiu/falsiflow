# Falsiflow Public Issue Queue

This page keeps the first public contribution queue small without mirroring
every GitHub issue. GitHub issues are the source of truth for open and closed
work; this document only records the rules and the current public entry points.

## Queue Rules

- Every issue should name one affected artifact: README, public demo,
  downstream PR, GitHub Action, starter template, adapter profile, or launch
  metrics.
- Every issue should include a verification command or public URL.
- `good first issue` means a newcomer can finish without changing the core
  claim engine.
- `help wanted` means external experience would improve the outcome.
- `launch` issues should be updated during the 24-hour, 72-hour, 7-day, and
  14-day launch review windows.
- Do not request private evidence uploads in public issues.

## Active Public Issues

Use GitHub as the live queue. Keep one concrete `good first issue` open plus
one higher-context `help wanted` issue while launch feedback is still small.

1. [Run the first launch metrics review](https://github.com/AzurLiu/falsiflow/issues/22)

   Labels: `help wanted`, `launch`

   Goal: review public-post traffic, stars, forks, clone/download signals,
   repeated questions, install failures, and docs gaps using
   `launch_metrics.md`.

   Evidence: update the issue with the 24-hour, 72-hour, 7-day, and 14-day
   review notes and turn repeated external feedback into concrete follow-up
   issues with verification commands.

2. [Add a short launch GIF from the live PR story](https://github.com/AzurLiu/falsiflow/issues/39)

   Labels: `good first issue`, `documentation`, `launch`

   Goal: turn the existing live PR story into a compact visual that is easier
   to share in launch posts and issue comments.

   Evidence: add a GIF or short screenshot sequence based on
   `docs/assets/falsiflow_live_pr_story_reel.svg`, keep
   `claim_check_blocked`, `claim_check_ready`, and the evidence-package
   readiness boundary visible, then run `python3 scripts/falsiflow.py
   launch-kit --out-dir /tmp/falsiflow_launch_gif_check --force --json` and
   `python3 scripts/falsiflow.py release-check --out-dir
   /tmp/falsiflow_launch_gif_release_check --force --skip-dist --json`.

## Completed Work

Closed GitHub issues are the archive for completed seed work. Do not duplicate
their full status here; link back to GitHub when launch notes need history.

Useful proof anchors:

- live AI eval downstream PR proof:
  <https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1>
- live RAG eval downstream PR proof:
  <https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1>
- live product-metric downstream PR proof:
  <https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1>
- release proof generation: `falsiflow release-proof`
- public release gate: `falsiflow release-check`
