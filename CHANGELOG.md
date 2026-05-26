# Changelog

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
