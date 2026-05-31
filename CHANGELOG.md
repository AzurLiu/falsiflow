# Changelog

## 0.1.33

- Upgraded `falsiflow launch-kit` so generated Hacker News, Reddit,
  LinkedIn, X, short-post, and reply-bank drafts include both live AI eval and
  live RAG eval blocked-to-ready downstream PR proof.
- Added RAG downstream proof links to generated GitHub repository profile
  handoff material.
- Added release-check and regression coverage so launch materials keep the
  AI/RAG proof links, run IDs, and responsible-use reply framing.

## 0.1.32

- Tightened the README first screen so new visitors see the claim, proof strip,
  three-command quickstart, blocked-vs-ready output, and GitHub Action snippet
  before longer release-proof details.
- Moved public evidence, live downstream PR links, current status, and source
  contributor guidance into scannable follow-up sections.
- Corrected the live in-repo demo PR copy to describe PR #17 as the AI eval
  gate story it actually proves.

## 0.1.31

- Added a release-check downstream smoke replay gate that runs the maintained
  AI eval, product metric, and RAG eval fixtures through both blocked
  placeholder evidence and source-backed ready evidence.
- Added release reports and JSON summary fields for downstream replay status,
  making fixture drift visible before a release can be tagged.
- Updated tests and release docs so source checkouts must report
  `downstream_smoke_replay_ready` while installed-package release checks skip
  the replay cleanly outside a source tree.

## 0.1.30

- Added `examples/downstream_rag_eval_smoke`, a copy-paste downstream repo
  fixture that blocks placeholder RAG eval claims in CI and turns ready after
  source-backed retrieval, faithfulness, citation, and reproducibility evidence
  is added.
- Linked the maintained RAG downstream fixture from the README, examples
  walkthrough, GitHub Action examples, and launch plan.
- Added release-check and source-distribution coverage so future releases keep
  the RAG fixture packaged and version-pinned with the reusable GitHub Action.

## 0.1.29

- Updated the public launchpad and downstream proof strip so the first visible
  demo now shows both live downstream stories: AI eval and RAG eval PRs moving
  from `claim_check_blocked` to `claim_check_ready`.
- Regenerated the public demo package and social preview PNG with the RAG
  blocked/ready run links.
- Added release-check coverage so the prebuilt public demo and generated demo
  package keep the live AI/RAG downstream proof links.

## 0.1.28

- Added a live downstream RAG eval demo repository and PR that moves from
  `claim_check_blocked` on placeholder/missing RAG evidence to
  `claim_check_ready` after source-backed rows and the raw RAG eval export are
  added.
- Linked the RAG blocked and ready GitHub Actions runs from the README, GitHub
  Action examples, demo PR playbook, launch execution notes, and public issue
  queue.
- Updated release metadata and `release-check` coverage so future releases
  keep the public RAG downstream proof visible and verifiable.

## 0.1.27

- Added `falsiflow release-proof` to generate a copy-paste release-note proof
  block from `falsiflow_external_evidence.json` and
  `external_readiness.json`.
- Updated External Evidence metadata, README/PyPI guidance, release docs,
  public issue queue docs, and release-check coverage so public proof snippets
  include the exact run URL, PyPI version match, published-package claim-check
  status, `claim_check_ready`, `bundle_verified`, and `external_ready`.
- Added a compact MCP client config block to the README/PyPI description.

## 0.1.26

- Added copy-paste MCP client configuration examples for generic stdio clients,
  Claude Desktop, and local checkout development.
- Added release-check coverage for the MCP client snippets and local
  no-HTTP/no-model boundary so agent integration docs stay verifiable.

## 0.1.25

- Seeded the real public contribution queue with current issues for release
  proof snippet generation, a live downstream RAG eval demo PR, and MCP client
  configuration examples.
- Updated `docs/falsiflow_public_issue_queue.md` with the active issue links,
  labels, goals, and verification commands, and added release-check coverage so
  the queue cannot silently become stale or empty again.

## 0.1.24

- Moved the public proof contract into the README/PyPI first screen so visitors
  see that each release links an exact External Evidence run proving
  `quickstart_ready`, `doctor_ready`, `claim_check_ready`, `bundle_verified`,
  `external_ready`, and `pypi_version_match`.
- Added release-check coverage so the first-screen proof contract cannot be
  removed without breaking the release gate.

## 0.1.23

- Required the public external-evidence workflow to prove the published PyPI
  package can run the generated AI eval starter through
  `claim-check --strict --force --json` and reach `claim_check_ready`.
- Added `public_package_claim_check` to the external evidence schema,
  external-check gate, release evidence ledger, workflow artifacts,
  release-check coverage, and README/release docs.

## 0.1.22

- Required the public external-evidence workflow to prove the published PyPI
  package README first-run path: `quickstart --template ai_claim_evaluation`
  followed by strict `doctor`.
- Added `public_package_first_run` to the external evidence schema,
  external-check gate, release evidence ledger, workflow artifacts,
  release-check coverage, and README/release docs.

## 0.1.21

- Added a reusable GitHub Action `evidence-import` mode so downstream CI can
  convert local/private eval artifacts before running `claim-check`.
- Added the copy-paste `examples/local_llm_eval_import` fixture with a blocked
  placeholder evidence file, local runner JSONL, model manifest, generated
  ready evidence demo, workflow, docs, and regression coverage.
- Added JSON output for `falsiflow evidence import` so action and CI logs can
  consume the import summary directly.

## 0.1.20

- Required the public external-evidence workflow to prove
  `falsiflow mcp --selftest --json` from the published PyPI package, so local
  MCP integration claims are gated by the same public artifact chain as the
  hosted demo, PyPI page, pipx smoke, and Windows smoke.
- Added `mcp_public_package_selftest` to the external evidence schema,
  external-check readiness gate, release evidence ledger, README/release docs,
  and regression coverage.

## 0.1.19

- Added `falsiflow mcp --selftest --json` so local agent integrations can
  verify MCP initialize, tool listing, resource listing, source-backed claim
  checking, bundle verification, blocker explanation, and evidence todo output
  before wiring a stdio client.
- Expanded MCP, README, release, roadmap, CLI reference, adoption, and
  release-check coverage for the local stdio/no-network/no-model boundary.

## 0.1.18

- Synced the launch execution baseline into the release line and made the
  baseline wording version-neutral so future patch releases do not make the
  pre-public-post launch copy stale.
- Added release-check coverage for the launch execution baseline, completed
  seed queue, external-evidence workflow, and blocked-to-ready launch copy.

## 0.1.17

- Added a compact downstream RAG eval GitHub Action example that shows
  `claim_check_blocked` on placeholder evidence and `claim_check_ready` after
  source-backed RAG eval rows are supplied.
- Recorded public PyPI README rendering proof for the v0.1.16 image URL fix
  and added release-check coverage so the proof remains part of the release
  runbook.

## 0.1.16

- Switched README proof images to absolute HTTPS asset URLs so PyPI long
  descriptions and other external renderers can show the downstream proof
  strip instead of depending on repository-relative image paths.
- Added release-check coverage to keep README image embeds PyPI-renderable for
  future launch hardening releases.

## 0.1.15

- Updated the generated browser launchpad and checked-in public demo to lead
  with the real downstream AI eval PR #1, including blocked and ready CI links,
  before keeping the in-repo PR #17 replay as a secondary proof path.
- Packaged the downstream PR proof strip so `falsiflow try` and
  `falsiflow demo-package` produce the same stronger public demo from source
  installs and PyPI installs.
- Added a downstream proof-strip PNG for social preview metadata so shared
  public demo links show the blocked-to-ready downstream PR story.

## 0.1.14

- Added a local LLM eval quickstart for turning local model outputs into
  Falsiflow evidence rows without sending prompts, outputs, or raw artifacts to
  a hosted service.
- Added a shareable downstream PR proof strip that leads the README, launch
  article, demo PR playbook, and launch plan with the real blocked-to-ready AI
  eval PR story.
- Added a copy-paste downstream product-metric smoke fixture that blocks
  placeholder launch evidence and passes only after source-backed metric rows
  are provided.
- Promoted the bundled RAG quality gate acceptance path by supporting
  `falsiflow template-check --strict` and covering it in release checks.

## 0.1.13

- Updated the generated launch posts, GitHub repo profile handoff, and launch
  execution copy to lead with the live downstream AI eval PR, blocked CI run,
  and ready CI run.
- Added release-check coverage so generated launch-kit posts keep the
  downstream proof links and `claim_check_blocked` / `claim_check_ready`
  narrative in future releases.

## 0.1.12

- Tightened the README/PyPI first screen around the one-sentence value
  proposition, three-command install path, blocked-vs-ready output, reusable
  GitHub Action snippet, and live downstream proof links.
- Reworked the launch article demo section to lead with the clean downstream
  PR that fails on placeholder AI eval provenance before passing with
  source-backed evidence.

## 0.1.11

- Added a maintained `examples/downstream_ai_eval_smoke` fixture that can be
  copied into a clean repository to show a placeholder AI eval claim failing CI
  before source-backed evidence makes the same workflow pass.
- Linked the live downstream proof repository and PR that show the same
  blocked-to-ready AI eval claim gate outside the Falsiflow repository.

## 0.1.10

- Moved the secondary 30-second CLI visual below the install/status block so the
  README first screen gets to copy-paste commands faster.
- Added PyPI project URLs for the Live PR Story, blocked CI run, ready CI run,
  and launch article so package readers can jump to proof links without relying
  on rendered README images.
- Pinned copy-paste GitHub Action snippets to `AzurLiu/falsiflow@v0.1.10` and
  surfaced the six-file downstream AI eval smoke recipe from the README.

## 0.1.9

- Added a shareable Live PR Story reel SVG that shows PR #17 moving from a
  risky AI/RAG eval claim to `claim_check_blocked`, source-backed repair, and
  `claim_check_ready`.
- Embedded the reel in the README, launch article, demo PR playbook, and public
  demo launchpad so the blocked-to-ready story is visible without opening the
  full playbook first.
- Added release-check coverage for the reel asset, README embedding, manifest
  inclusion, and packaged launchpad references.

## 0.1.8

- Added description, Open Graph, and Twitter card metadata to the public demo
  launchpad so shared links preview the live PR story.
- Enabled automatic GitHub Pages deploys on `main` pushes that affect the demo
  generator, packaged public demo, or Pages workflow.
- Sharpened README/PyPI first-screen copy around the Live PR Story proof path.

## 0.1.7

- Put the live AI eval PR story on the public demo launchpad: PR #17 now appears
  as a first-screen sequence from risky claim to blocked CI to source-backed
  ready CI.
- Updated `falsiflow try` and `falsiflow demo-package` output so regenerated
  static demos keep the same real PR proof path instead of leading with only a
  static starter example.
- Refreshed the checked-in `docs/public_demo` package with the new launchpad.

## 0.1.6

- Fixed `rag-eval` CSV imports so manifest and artifact rows are promoted into
  provenance and reproducibility evidence, allowing the bundled RAG raw eval
  export to import and pass `claim-check` without a separate JSON manifest.
- Added timestamps and explicit candidate/baseline RAG version rows to the RAG
  quality gate raw export used by examples and quickstart templates.
- Added regression coverage for the real path: raw RAG eval export -> evidence
  import -> `claim_check_ready`.

## 0.1.5

- Updated launch execution copy from the older v0.1.2 trust baseline to the
  live AI/RAG eval PR story, PyPI release path, and external-evidence workflow.
- Switched the README/PyPI long description to a stable external-evidence
  workflow link so package metadata does not point at an outdated single run.
- Refreshed PyPI trusted-publishing verification guidance so future releases
  check the current release version instead of carrying the original v0.1.2
  recovery wording into launch copy.

## 0.1.4

- Added a live public AI/RAG eval PR demo:
  [PR #17](https://github.com/AzurLiu/falsiflow/pull/17) now shows placeholder
  eval evidence failing CI and source-backed evidence passing the same claim
  gate.
- Added the bundled `rag_quality_gate` starter template plus `rag-eval`,
  `local-llm-eval`, and `ai-eval` artifact import coverage for JSON, JSONL,
  CSV, and manifest-backed eval outputs.
- Added local agent integration surfaces: `falsiflow/api.py`,
  `falsiflow mcp`, and MCP documentation for local stdio use by AI coding
  agents.
- Improved GitHub Action summaries with top blockers, evidence todo items, and
  next evidence actions for blocked claim checks.
- Fixed the reusable GitHub Action so `evidence:` overrides the project-dir
  default evidence file in `claim-check` mode.

## 0.1.3

- Sharpened the README first screen around the AI/RAG eval claim-gate story:
  one-line CI positioning, PyPI quickstart, blocked-vs-ready output, and a
  copy-paste GitHub Action snippet.
- Reworked the public demo PR playbook into a complete failing-PR-to-ready-PR
  story for AI/RAG eval claims with local rehearsal commands, expected CI
  statuses, report artifacts, and a 30-second recording script.
- Rewrote the launch article `Stop Shipping Unverifiable AI Eval Claims` around
  the industry failure mode first, then introduced Falsiflow as the CI evidence
  gate.
- Added launch-execution copy and included it in the source distribution so
  public posts, channels, and metrics review notes ship with the package.

## 0.1.2

- Added the `product_metric_launch` starter template and public casebook
  coverage so Falsiflow now demonstrates AI eval, product-metric, vendor,
  wetware, biointerface, and neural-materials claim gates.
- Made the reusable GitHub Action install from its checked-out action path by
  default, keeping downstream claim gates usable before PyPI publication.
- Updated GitHub Actions dependencies and added copy-paste AI eval action
  examples for downstream repositories.
- Added a README 30-second ready-vs-blocked demo strip and release-checked it
  as a first-screen visual asset.
- Added named neighboring-tool boundaries for Great Expectations, Evidently,
  Deepchecks, MLflow, and plain GitHub Actions.
- Added a public demo PR playbook that rehearses an AI-eval claim moving from
  `claim_check_blocked` with placeholder evidence to `claim_check_ready` with
  source-backed evidence.
- Sharpened launch-kit posts, announcement copy, demo script, launch metrics,
  and maintainer checklist around the demo PR path, PyPI status, and
  responsible-use reply bank.
- Extended release-check and regression coverage so launch copy, demo PR
  references, sdist docs, README assets, and Markdown code fences remain
  checked before tagging.

## 0.1.1

- Introduced the Falsiflow evidence-gated R&D workflow engine.
- Added configurable project gates, evidence CSV validation, derived metrics,
  claim audits, next actions, dashboards, and portfolio aggregation.
- Added starter templates for neural materials, biointerface coatings, RFQ
  vendor evidence, wetware support hardware, and AI claim evaluation.
- Added root `action.yml` so downstream GitHub Actions workflows can run
  Falsiflow claim, template, casebook, release, adoption, quickstart, and
  external-readiness gates with one `uses:` step.
- Added source-file provenance manifests, portable evidence bundles,
  bundle zip verification, and release-check quality gates.
- Added template-check, template-scaffold, template-pack, template-registry,
  template-lock, and template-install flows for authoring, verifying,
  distributing, locking, and installing reusable external starter templates.
- Added versioned template locks and registry `source_url` support so published
  template packs can be pinned by URL, byte count, and SHA-256 hash.
- Added template provenance attestations with optional HMAC signatures so
  locked template sources can be independently verified before installation.
- Added `template-install --attestation --require-attestation` so signed
  lockfile provenance can be enforced during template adoption.
- Added template adoption policies with `template-policy`,
  `verify-template-policy`, and `template-install --policy`.
- Added template release bundles with `template-release`,
  `verify-template-release`, and `template-install --release`.
- Hardened template release verification against unsafe artifact paths,
  duplicate paths, unmanifested files, and embedded registry/lock mismatches.
- Added Markdown template release verification reports for human review in CI,
  release-check, and adoption workflows.
- Added an adoption-priorities document and README first-run path to keep
  optimization focused on open-source usability.
- Added `template-gallery` JSON and Markdown outputs so cross-domain starter
  breadth is visible and checked by release workflows.
- Added `casebook-check` JSON and Markdown outputs so public starter casebook
  positive demos, placeholder blockers, source provenance, and verified bundles
  are checked by adoption and release workflows.
- Added casebook reviewer replay artifacts (`casebook_reviewer_replay.md`,
  `.sh`, and `.ps1`) so launch reviewers can rerun every positive demo and
  placeholder blocked-path proof from generated scripts.
- Added launch metrics artifacts (`launch_metrics.json` and
  `launch_metrics.md`) so the 1k-star path has review windows for traffic,
  referrers, stars, demo visits, install signals, repeated questions, and
  follow-up fixes.
- Added public package evidence checks to `external-evidence`,
  `external-check`, and the external evidence workflow so final external
  readiness requires a PyPI project URL and a pipx smoke test from the published
  package, not only a local checkout.
- Added `public_release_evidence.json` and `public_release_evidence.md` to the
  publish kit so final public release evidence across repo, demo, PyPI, pipx,
  Windows, Scorecard, release-check, casebook replay, and launch metrics is
  reviewed from one generated ledger.
- Added `release_rehearsal.json` and `release_rehearsal.md` to the publish kit
  so public release reviewers can rehearse the final command sequence, expected
  artifacts, success signals, and external stop conditions before announcements.
- Added adapter profiles for generic wide CSV, vendor measurement returns,
  instrument exports, and plate-reader exports in `evidence import` and
  `ingest-wide-csv`.
- Added `audit_review.json` and `audit_review.md` decision cards for faster
  human review of audit status, blockers, next actions, and release boundaries.
- Added `claim-check` with `claim_check.json` and `claim_check.md` so audit,
  source provenance, bundle creation, and zip verification can run as one
  user-facing claim gate.
- Added review artifact indexes to claim-check, bundle verification, release
  check, and template release verification reports so reviewers can jump between
  source manifests, bundle integrity, dashboards, and template-release artifacts.
- Added `claim-check --project-dir` so initialized starter projects can use
  default `project.json`, `evidence_pass_demo.csv`, and `claim_check/` paths.
- Added `quickstart` with `quickstart_summary.json` and `quickstart_summary.md`
  so first-run users can create a starter project and verify its claim gate in
  one command.
- Added `next_commands` to quickstart summaries so first-run users are handed
  directly to `falsiflow doctor`.
- Added `start` as the beginner-friendly local app command with a free
  localhost port, automatic browser opening, `--check`, and `serve_summary.json`.
- Added `scripts/install_local.sh` plus `make install-local`, `make start`, and
  `make start-check` so a local checkout or public Git repository can be pulled
  into a virtual environment and launched with one command.
- Added `scripts/install_local.ps1` for the same local install/start flow on
  Windows PowerShell.
- Added `pipx` Makefile shortcuts for checkout-based `pipx install --force .`
  workflows.
- Added `onboard` with `onboard_summary.json` for beginner next-step guidance.
- Added `static-demo` with `static_demo_summary.json` so a zero-install browser
  demo can be exported to static hosting.
- Added `demo-package` with `demo_package_summary.json`, `.nojekyll`,
  `netlify.toml`, and `publish_checklist.md` for a public static-demo handoff.
- Added `publish-kit` with `publish_handoff.json`, `publish_handoff.md`,
  `publish.env.example`, and `github_publish_commands.sh` for account-bound
  GitHub/Pages/PyPI release handoff steps.
- Added `external-check` with `external_readiness.json` and
  `external_readiness.md` so public repo/demo URLs, pipx, and
  Windows/PowerShell validation are explicit external gates.
- Added GitHub Actions workflows for static demo deployment, Linux/macOS/Windows
  and pipx smoke tests, and PyPI trusted-publishing release builds.
- Added a localhost `workbench.html` and API behind `falsiflow start` so browser
  users can upload project/evidence/source files, run the local evidence gate,
  and inspect ready/blocked results, review flow, evidence lineage, repair
  checklist, and linked review artifacts without touching the terminal.
- Added `discover` with `evidence_records.json`, `candidate_queue.json`,
  `ranking.md`, `assay_plan.md`, `rfq_package.md`, and a placeholder
  `project_draft/` so discovery output is structured while remaining
  non-AI-dependent and non-claim-ready.
- Added `agent discover`, `candidate rank`, `assay-plan`, and
  `evidence import` as namespaced public interfaces for structured discovery
  and evidence-import workflows.
- Added discovery schemas for evidence records, candidate recipes, and discovery
  summaries.
- Added `try` with `try_summary.json`, `index.html`, and `try_report.html` so
  first-run users can open a local browser launchpad, proof report, and
  generated starter wizard before learning the full CLI.
- Added `serve` with `serve_summary.json` so the local launchpad, try report,
  and wizard can be opened through a localhost browser demo.
- Added `wizard` so browser-first users can draft a claim gate from
  plain-language presets and export the matching scaffold command, project JSON,
  and evidence CSV without a server.
- Added `doctor` with `doctor_summary.json` and `doctor_summary.md` so users can
  diagnose project health and next repair actions after quickstart.
- Added `repair_checklist` to doctor summaries so blocked diagnoses include a
  concrete command, expected artifact, and success signal.
- Added `adoption-check` with `adoption_check.json` and `adoption_check.md` so
  the five open-source adoption priorities can be audited as `adoption_ready`
  or `adoption_blocked`.
- Added `repair_checklist` to adoption-check summaries so blocked priorities
  and final ready rechecks include commands, expected artifacts, and success
  signals.
- Hardened release-check distribution hygiene so local `build/`, `dist/`, and
  `*.egg-info/` artifacts are ignored and transient build caches are cleaned.
- Surfaced distribution hygiene in the `release_and_distribution` adoption
  priority so adoption reports show build-cache cleanup evidence directly.
- Embedded adoption priority evidence tables in `release_check.md` so release
  reports are standalone for human review.
- Added `release_validation_status` to adoption-check summaries so fast
  `--skip-dist` adoption readiness cannot be confused with full distribution
  validation.
- Added top-level `release_validation_status` to release-check summaries,
  reports, and CLI output so fast release smoke tests cannot be confused with
  complete distribution validation.
- Required `release_validation_ready` in the release checklist gate so publishing
  docs match the adoption-check validation boundary.
