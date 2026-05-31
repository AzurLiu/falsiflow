# Changelog

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
