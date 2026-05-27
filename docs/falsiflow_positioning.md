# Falsiflow Positioning and Casebook

Falsiflow is an evidence-gated R&D workflow engine for claims that should not
advance on placeholders, missing provenance, malformed files, or ambiguous
thresholds. It is designed for the narrow moment between "we have a technical
claim" and "we are willing to let that claim drive money, lab time, vendor
handoffs, or public release notes."

## What It Is

- A claim gate: it turns a technical claim into required evidence rows,
  source-file policy, derived metrics, and acceptance rules.
- A provenance check: it keeps measured values, raw source files, operators,
  instruments, and timestamps connected.
- A review bundle: it writes JSON for CI and Markdown/HTML reports for humans.
- A template supply-chain path: starter templates can be checked, packed,
  locked, attested, policy-verified, released, and installed.
- A public casebook proof path: starter cases can be checked for positive demo
  readiness, placeholder blockers, source provenance, and verified bundles.
- A release readiness gate: `adoption-check`, `release-check`,
  `external-evidence`, and `external-check` keep local and external publication
  evidence explicit.

## What It Is Not

- It is not an ELN, LIMS, database, or inventory system.
- It is not an arbitrary workflow orchestrator.
- It is not a scientific truth engine, safety proof, regulatory approval, or
  replacement for independent experimental validation.
- It is not a model evaluation leaderboard. It can gate evidence produced by AI
  or lab workflows, but `claim_ready` only means configured evidence gates
  passed.
- It is not a hidden Python plugin runtime. Derived metrics are fixed,
  inspectable operations rather than arbitrary code execution inside project
  configs.

## Comparison Map

| Alternative | Good At | Falsiflow Adds | Boundary |
| --- | --- | --- | --- |
| Spreadsheet checklist | Quick manual tracking | Structured evidence rows, schema checks, source-file policy, repeatable audits | Keep the spreadsheet if it is enough; use Falsiflow when the claim must be machine-checkable. |
| CI test suite | Checking code behavior | Claim-specific evidence gates, raw source provenance, human audit cards, bundles | Falsiflow complements CI; it does not replace unit tests. |
| ELN or LIMS | Capturing lab records and inventory | A lightweight gate that can point to exported lab evidence and block readiness | Keep ELN/LIMS as source of record; Falsiflow reviews handoff evidence. |
| ML eval harness | Scoring model outputs | Provenance-aware claim gates for broader R&D evidence and release decisions | Use evals for model quality; use Falsiflow for evidence-backed claim promotion. |
| Materials database | Searching known properties | Project-specific thresholds, measured evidence rows, and source-backed acceptance decisions | Databases inform candidates; Falsiflow gates your claim about them. |
| Workflow orchestrator | Running multi-step jobs | Conservative ready/blocked decisions and portable review bundles | Orchestrators run work; Falsiflow decides whether evidence is ready. |

## Named Tool Boundaries

These boundaries are intentionally cooperative. Falsiflow should sit after the
systems that generate or validate evidence, then block the claim until the
configured evidence package is complete.

| Neighbor | Use It For | Use Falsiflow When |
| --- | --- | --- |
| Great Expectations | Data quality expectations, validation results, and data documentation for tables and pipelines. | A release claim spans evidence rows, raw-source files, operators, timestamps, and a ready/blocked decision, not just table validity. |
| Evidently | ML, LLM, and data evaluations or monitoring metrics. | The team wants to promote a headline such as "model quality improved" only after dataset versions, model versions, raw outputs, benchmark deltas, and provenance pass. |
| Deepchecks | Testing, CI, and monitoring checks for ML data and models. | The model check is one input to a broader claim gate that also needs source manifests, review artifacts, and bundle verification. |
| MLflow | Experiment tracking, run metadata, model artifacts, and registry workflows. | The tracked run is evidence, but the release or announcement should stay blocked until the full claim package is reviewable in CI. |
| Plain GitHub Actions | Running scripts, tests, and deployment jobs. | The repository needs a portable evidence contract, consistent `claim_check_ready` or `claim_check_blocked` status, and human-readable repair actions. |

## Casebook

For a public-facing casebook with reviewer scripts and blocked-path proofs
across all bundled starter templates, see
[falsiflow_public_casebook.md](falsiflow_public_casebook.md).
For the machine-verifiable casebook proof command, see
[falsiflow_casebook_check.md](falsiflow_casebook_check.md).

### R&D Screening Gate

Use Falsiflow when a project should stop until measured evidence passes agreed
thresholds. A coating candidate can require adhesion, cytotoxicity, impedance
drift, metadata, and raw test exports before the claim becomes ready.

Proof path:

```bash
falsiflow quickstart --template biointerface_coatings --out my_falsiflow_project --strict
falsiflow doctor --project-dir my_falsiflow_project --strict
```

### Vendor Evidence Handoff

Use Falsiflow when vendor claims, quotes, lab exports, and raw files need to
stay distinct. The `rfq_vendor_evidence` template shows how replies and
measurements can be audited without treating unverified statements as evidence.

Proof path:

```bash
falsiflow template-gallery --out data/falsiflow/template_gallery.md --json-out data/falsiflow/template_gallery.json
falsiflow casebook-check --out-dir data/falsiflow/casebook_check --force
falsiflow quickstart --template rfq_vendor_evidence --out rfq_review --strict
```

### AI Claim Evaluation

Use Falsiflow when an AI model quality claim should not become public until the
dataset, prompt set, model versions, baseline, raw outputs, and reproducibility
artifacts are pinned. The `ai_claim_evaluation` template shows how an eval
headline can stay blocked until source-backed benchmark gates pass.

Proof path:

```bash
falsiflow quickstart --template ai_claim_evaluation --out ai_claim_review --strict
falsiflow doctor --project-dir ai_claim_review --strict
```

### Product Metric Launch

Use Falsiflow when a product metric claim should not ship until metric
definitions, experiment identity, activation lift, retained-user exposure,
guardrails, rollback owner, and monitoring evidence are source-backed. The
`product_metric_launch` template shows how a launch-readiness claim stays
blocked until both the positive metric and the safety envelope pass.

Proof path:

```bash
falsiflow quickstart --template product_metric_launch --out product_metric_review --strict
falsiflow doctor --project-dir product_metric_review --strict
```

### Template Authoring

Use Falsiflow when another team needs to install a reusable starter template
with hashes, lockfiles, attestations, and policy checks. This turns a template
from a folder of examples into a reviewable supply-chain artifact.

Proof path:

```bash
falsiflow template-check --template-dir examples/falsiflow/neural_materials --out-dir data/falsiflow/template_check --force
falsiflow template-pack --template-dir examples/falsiflow/neural_materials --out-dir data/falsiflow/template_pack --force
```

### Release Review

Use Falsiflow when maintainers need one local command that checks package
metadata, distribution artifacts, starter templates, bundles, launch materials,
and installed-package behavior before publishing.

Proof path:

```bash
falsiflow adoption-check --out-dir data/falsiflow/adoption_check --force
falsiflow release-check --out-dir data/falsiflow/release_check --force
```

### Public Launch

Use Falsiflow when the repository needs a public demo, launch copy, proof card,
release rehearsal, and external validation evidence before calling a release
externally ready.

Proof path:

```bash
falsiflow launch-kit --out-dir falsiflow_launch_kit --force
falsiflow external-evidence --out falsiflow_external_evidence.json --force
falsiflow external-check --out-dir falsiflow_external_check --evidence falsiflow_external_evidence.json --force
```

The generated `release_rehearsal.md` keeps the last-mile sequence explicit:
local regression, release-check, casebook replay, launch-kit review, external
evidence capture, `external-check --strict`, and public announcement stop
conditions.

## Decision Rubric

Falsiflow is a strong fit when all of these are true:

- The claim has a clear ready/blocked decision.
- Missing source provenance should block the claim.
- Evidence must be reviewable by both humans and CI.
- A reusable template or handoff bundle would reduce repeated review work.
- The team can define thresholds, metadata expectations, and source-file rules.

Falsiflow is probably too heavy when the work is exploratory and no readiness
decision exists yet. In that case, use discovery notes, ELN/LIMS exports, or a
plain spreadsheet first, then promote the decision into Falsiflow once the
claim, gates, and evidence expectations are clear.
