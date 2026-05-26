# Falsiflow Adoption Priorities

This file records the optimization order for turning Falsiflow from a working
local tool into a serious open-source project that other teams can understand,
trust, and adopt.

## Priority Order

1. Open-source entry point
   Make the README and first commands clear enough that a new user can
   understand the value in one minute and run a starter workflow in five.

2. Trusted audit experience
   Keep JSON outputs for CI and Markdown reports for human review. Verification
   results should explain what was checked, what failed, and whether a claim,
   bundle, template pack, or release can be trusted.

3. Generality proof
   Maintain starter templates beyond neural materials so Falsiflow is visibly a
   general evidence-gated R&D workflow engine, not a single wetware project.

4. Release and distribution
   Keep package metadata, wheel/sdist builds, release-check, template release
   bundles, and installed-package smoke tests passing before publishing.

5. User experience convergence
   Prefer short first-run commands, predictable output paths, explicit next
   actions, and clear failure messages over adding more advanced machinery.

## Current Optimization Track

The current track is adoption readiness:

- README first-screen clarity and five-minute quickstart.
- A beginner `start` command that opens the local browser app on a free
  localhost port before users learn `try`, `serve`, or schema terms.
- A low-friction `try` command that runs a starter claim and writes a local
  `index.html` launchpad plus `try_report.html` browser entry before users
  learn the full CLI.
- A `serve` command that turns the same local demo into a localhost browser
  experience with a checkable `serve_summary.json` and direct report/wizard
  URLs.
- A localhost `workbench.html` behind `start` that lets users upload project,
  evidence, and raw source files, run the local evidence gate, and inspect
  ready/blocked status without using the terminal for that project check.
- A static `wizard` command with plain-language presets that lets browser-first
  users draft a claim gate and generate the matching scaffold command, project
  JSON, and evidence CSV.
- A non-AI-dependent `discover` command that turns a research goal into
  structured evidence records, candidate recipes, ranking, assay/RFQ drafts, and
  a placeholder project draft while keeping `claim_ready=false`.
- Focused public interfaces for the same contract: `agent discover`,
  `candidate rank`, `assay-plan`, and `evidence import`.
- A `demo-package` command that prepares GitHub Pages/Netlify-friendly static
  demo artifacts, plus an `external-check` gate for public repo/demo URLs,
  pipx, and Windows/PowerShell validation evidence.
- A `publish-kit` handoff command that writes account-bound GitHub/Pages/PyPI
  setup artifacts without pretending those external account actions already
  happened.
- GitHub Actions workflows for the public static demo, cross-platform
  Linux/macOS/Windows and pipx smoke tests, and PyPI trusted-publishing release
  builds.
- Release verification reports that are useful both to CI and to humans.
- Trusted `audit_review.json` and `audit_review.md` decision cards for fast
  human review of claim readiness, blockers, next actions, and boundaries.
- Starter templates that demonstrate neural-materials, vendor evidence,
  biointerface coating, and wetware-support-hardware use cases.
- A release-checked `template-gallery` command that turns that breadth into
  Markdown and JSON evidence for users and CI.
- A release-checked `claim-check --project-dir` path that makes audit, source
  provenance, bundle creation, and zip verification a single first-run claim
  gate.
- A release-checked `quickstart` command that creates a starter project and
  runs its claim gate in one first-run command, then records `next_commands`
  for the doctor handoff.
- A release-checked `doctor` command that diagnoses a project config, evidence
  file, claim gate, source provenance, bundle, and zip verification in one
  project-health report with a command-oriented repair checklist.
- A release-checked `adoption-check` command that turns this priority order
  into `adoption_check.json` and `adoption_check.md`, with `adoption_ready`
  only when all five priorities have current evidence and `repair_checklist`
  entries that point blocked priorities or ready rechecks to concrete commands.
- Full `release-check` coverage for package metadata, distribution artifacts,
  build-cache hygiene, template supply-chain verification, and installed package
  behavior.
