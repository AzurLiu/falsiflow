# Falsiflow

Evidence-gated R&D workflow engine for high-risk technical claims.

[![Falsiflow](https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow.yml/badge.svg)](https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow.yml)
[![Falsiflow Cross Platform](https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow-cross-platform.yml/badge.svg)](https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow-cross-platform.yml)

Falsiflow turns a claim into explicit gates, required evidence rows, source-file
policy, derived metrics, and acceptance rules. A claim only becomes ready when
the project config is valid, the evidence CSV is structurally sound, required
metadata and raw-source files are present, and all configured gates pass.

It grew out of the LIMINA neural-materials work, but the valuable part is
general: prevent expensive research claims from advancing on placeholders,
missing provenance, malformed files, or ambiguous configuration.

## Project Priorities

Falsiflow is being optimized for open-source adoption in this order:

1. Clear first-run experience.
2. Trusted JSON and Markdown audit reports.
3. Templates that prove the workflow is broader than one material domain.
4. Repeatable release and package distribution.
5. Simple commands and actionable failure messages.

The maintained priority record is
[docs/falsiflow_adoption_priorities.md](docs/falsiflow_adoption_priorities.md).

## When To Use It

Use Falsiflow when a claim should not move forward until the evidence is
source-backed, repeatable, and reviewable. Good fits include:

- R&D screening gates where missing provenance can waste experiment budget.
- Vendor or external-lab handoffs where replies, quotes, and measured evidence
  must stay distinct.
- Reusable project templates that need version locks, hashes, provenance
  attestations, and adoption policy before another team installs them.
- CI checks that should fail when a workflow quietly regresses from measured
  evidence to placeholders.

## Thirty-Second Try

Install and open the local app first if you only want to see the workflow:

```bash
make install-local
make start
```

`make install-local` installs the current checkout in editable mode.
`make start` runs `falsiflow start`, the beginner entry point. It chooses a
free localhost port, opens the browser automatically, writes
`serve_summary.json`, and keeps all data on the local machine. The page explains
the example decision in plain language, then links to the proof report,
dashboard, review bundle, wizard, and `workbench.html`. The workbench lets a
local browser user select a template, upload `project.json`, evidence CSV, and
raw source files, run the evidence check, then inspect ready/blocked status,
next actions, dashboard, and evidence bundle links without touching the
terminal. Use `falsiflow start --reset` when you want to regenerate the local
demo files.

For a one-command local install from an existing checkout:

```bash
scripts/install_local.sh --from-local . --check
```

For a public GitHub release, publish `scripts/install_local.sh` and set the
repository URL in the install command:

```bash
FALSIFLOW_REPO_URL=https://github.com/YOUR_ORG/falsiflow.git \
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/YOUR_ORG/falsiflow/main/scripts/install_local.sh)" -- --check
```

That installer clones or copies Falsiflow into `~/.falsiflow`, creates a Python
virtual environment, installs the package, and starts the same local browser app.

If you use `pipx` after packaging or from a checkout:

```bash
make pipx-install
make pipx-start
```

On Windows PowerShell, use the matching installer:

```powershell
.\scripts\install_local.ps1 -FromLocal . -Check
```

For scripted checks or CI, run the same beginner path without leaving the server
open:

```bash
falsiflow start --check --json
make start-check
falsiflow onboard --check --json
```

`falsiflow onboard` writes `onboard_summary.json`, checks the local launchpad,
and returns a beginner-friendly next-step checklist. To export a hostable static
demo for zero-install visitors:

```bash
falsiflow static-demo --out-dir falsiflow_static_demo --force
```

The static demo directory includes `static_demo_summary.json` and can be served
by GitHub Pages, Netlify, or any static file server.

This repository also includes a prebuilt public demo at `docs/public_demo` and a
root `netlify.toml`, so Netlify can publish the demo without GitHub Pages. For
Cloudflare Pages or Vercel, use `docs/public_demo` as the output directory and
leave the build command empty. See `docs/static_hosting.md`.

To prepare a publish-ready static demo directory with hosting metadata:

```bash
falsiflow demo-package --out-dir falsiflow_public_demo --force
```

`falsiflow demo-package` writes `demo_package_summary.json`,
`static_demo_summary.json`, `.nojekyll`, `netlify.toml`, and a
`publish_checklist.md`. The package records `external_url_required=true`:
hosting the folder is an external step, and the hosted URL should be recorded
with `FALSIFLOW_PUBLIC_DEMO_URL`.

To generate a full account-bound publishing handoff kit:

```bash
falsiflow publish-kit --out-dir falsiflow_publish_kit --force
```

`falsiflow publish-kit` writes `publish_handoff.json`, `publish_handoff.md`,
`publish.env.example`, `github_publish_commands.sh`, and a nested public demo
package. It marks `account_action_required=true`, because GitHub login,
repository creation, Pages deployment, workflow results, and PyPI publishing
require real account state outside the local Core.

Before calling a public release externally ready, check the environment and
hosted links:

```bash
falsiflow external-check --out-dir falsiflow_external_check --force
```

`falsiflow external-check` writes `external_readiness.json` and
`external_readiness.md`. It returns `external_ready` only when the public repo
URL, hosted demo URL, pipx path, and Windows/PowerShell validation evidence are
present; otherwise it returns `external_blocked` with concrete next actions.
CI can record successful smoke tests with `FALSIFLOW_PIPX_VALIDATED=1` and
`FALSIFLOW_WINDOWS_VALIDATED=1`.

If you prefer to write static files without starting a localhost server:

```bash
falsiflow try --out-dir falsiflow_try --force --open
```

`falsiflow try` creates a starter project, runs the claim gate, and writes
`try_summary.json`, `index.html`, `workbench.html`, and `try_report.html`. The `index.html`
launchpad is titled `Falsiflow Launchpad` and points new users to the proof
report, generated `dashboard.html`, evidence bundle, and
`falsiflow_wizard.html` starter wizard. The HTML report is titled
`Falsiflow Try` and links to the quickstart report, claim-check report, evidence
bundle, verification report, and wizard. This is the lowest-friction entry point
for people who want a local browser view before learning every CLI command.

To use the same demo through a local `localhost` URL:

```bash
falsiflow serve --out-dir falsiflow_try --force --open
```

`falsiflow serve` generates the try output when needed, serves the local
`index.html` launchpad and `try_report.html` report, and writes
`serve_summary.json` with the URL, `try_report_url`, `wizard_url`, and HTTP
check status. It does not upload project data or require an account.

For a browser-first project draft, write the static wizard:

```bash
falsiflow wizard --out falsiflow_wizard.html --open
```

The `Falsiflow Browser Wizard` starts from plain-language presets such as
material screening, vendor evidence review, or a custom R&D decision. It then
drafts a claim, gate, threshold rule, starter `project.json`, starter
`evidence_template.csv`, and the matching `falsiflow scaffold` command without
requiring a server or account.

Generate a structured discovery package without requiring an AI model:

```bash
falsiflow discover --goal "MEA neural interface material" --out-dir falsiflow_discovery --force
```

`falsiflow discover` writes `evidence_records.json`, `candidate_queue.json`,
`ranking.md`, `assay_plan.md`, `rfq_package.md`, and a placeholder
`project_draft/`. It marks `ai_used=false` and `claim_ready=false`; discovery
artifacts propose candidates and gates only, while Falsiflow Core still requires
source-backed evidence before any claim can become ready.

The same structured outputs are also available through narrower public
interfaces:

```bash
falsiflow agent discover --goal "MEA neural interface material" --out-dir falsiflow_discovery --force
falsiflow candidate rank --goal "MEA neural interface material" --out-dir falsiflow_candidate_rank --force
falsiflow assay-plan --goal "MEA neural interface material" --out-dir falsiflow_assay_plan --force
```

These commands do not make an AI result authoritative. They only write
candidate queues, rankings, assay/RFQ drafts, and a Falsiflow project draft that
must still pass Core evidence gates.

## Five-Minute Quickstart

For the full walkthrough, see [examples/README.md](examples/README.md). To run a
ready starter project and inspect the outputs:

```bash
python3 -m pip install -e .

falsiflow template-gallery \
  --out data/falsiflow/template_gallery.md \
  --json-out data/falsiflow/template_gallery.json
falsiflow selftest

falsiflow quickstart --template biointerface_coatings --out my_falsiflow_project --strict
falsiflow doctor --project-dir my_falsiflow_project --strict
falsiflow adoption-check --out-dir data/falsiflow/adoption_check --skip-dist --force
```

The one-command quickstart creates the project, runs the claim gate, and writes:

- `quickstart_summary.json`
- `quickstart_summary.md`
- `claim_check.json`
- `claim_check.md`
- `claim_audit.json`
- `claim_audit.md`
- `audit_review.json`
- `audit_review.md`
- `claim_summary.json`
- `next_actions.json`
- `dashboard.html`
- `evidence_bundle.zip`
- `evidence_bundle_verify.json`
- `evidence_bundle_verify.md`

The Markdown quickstart report is titled `Falsiflow Quickstart`.
`quickstart_ready` means the starter project was created and its claim gate
returned `claim_check_ready`; `quickstart_blocked` preserves the generated
project and points to the blocked stage. Its JSON includes `next_commands`,
starting with the matching `falsiflow doctor --project-dir ... --strict`
diagnosis command.

The doctor command then writes:

- `doctor_summary.json`
- `doctor_summary.md`
- `project_validation.json`
- `evidence_diagnostics.json`

The Markdown diagnosis report is titled `Falsiflow Doctor`.
`doctor_ready` means the project config, evidence CSV, claim check, audit
review, source provenance, bundle, and zip verification all passed.
`doctor_blocked` preserves the same diagnosis artifacts and points to the next
repair action. Its JSON includes `repair_checklist`, which turns the next
repair or review step into a command, expected artifact, and success signal.

The Markdown gate report is titled `Falsiflow Claim Check`.
`claim_check_ready` means the configured claim passed audit, source provenance,
bundle generation, and zip verification. `claim_check_blocked` preserves the
same artifacts but points to the first blocking stage and next action.

The Markdown review is titled `Falsiflow Audit Review`. It is a concise
decision card for humans and CI: `review_ready` means the configured claim is
ready for human release review, while `review_blocked` identifies the first
blocking stage, gate snapshot, top blockers, next actions, and review
checklist.

## Adoption Path

Most users start with claim audits and evidence bundles. Template authors and
teams can then move to the supply-chain workflow:

```bash
falsiflow template-check --template-dir examples/falsiflow/neural_materials --out-dir data/falsiflow/template_check --force
falsiflow template-pack --template-dir examples/falsiflow/neural_materials --out-dir data/falsiflow/template_pack --force
falsiflow template-registry --pack-zip data/falsiflow/template_pack.zip --out data/falsiflow/template_registry.json
falsiflow template-lock --registry data/falsiflow/template_registry.json --template neural_materials --version 0.1.0 --out data/falsiflow/falsiflow_template_lock.json
falsiflow template-attest --subject data/falsiflow/falsiflow_template_lock.json --subject-type template-lock --out data/falsiflow/falsiflow_template_lock.attestation.json --signing-key local-demo-secret
falsiflow template-policy --lock data/falsiflow/falsiflow_template_lock.json --attestation data/falsiflow/falsiflow_template_lock.attestation.json --out data/falsiflow/falsiflow_template_policy.json --signing-key local-demo-secret
falsiflow template-release --pack-zip data/falsiflow/template_pack.zip --registry data/falsiflow/template_registry.json --lock data/falsiflow/falsiflow_template_lock.json --attestation data/falsiflow/falsiflow_template_lock.attestation.json --policy data/falsiflow/falsiflow_template_policy.json --out data/falsiflow/falsiflow_template_release.zip --signing-key local-demo-secret
falsiflow verify-template-release --release data/falsiflow/falsiflow_template_release.zip --signing-key local-demo-secret --out data/falsiflow/falsiflow_template_release_verification.json --report-out data/falsiflow/falsiflow_template_release_verification.md --strict
falsiflow template-install --release data/falsiflow/falsiflow_template_release.zip --signing-key local-demo-secret --templates-dir data/falsiflow/installed_templates --force
```

Run the full repository gate before publishing or proposing a substantial
change:

```bash
falsiflow adoption-check --out-dir data/falsiflow/adoption_check --force
falsiflow release-check --out-dir data/falsiflow/release_check --force
```

The release gate writes `release_check.json` and `release_check.md` with a
top-level `release_validation_status`. A full distribution run reports
`release_validation_ready`; a `--skip-dist` run can still be useful as a fast
local smoke test, but reports `release_validation_skipped` until wheel, sdist,
isolated install, and installed-package release checks complete.

The adoption gate writes `adoption_check.json` and `adoption_check.md`. The
Markdown report is titled `Falsiflow Adoption Check`. `adoption_ready` means all
five project priorities are backed by current CLI, documentation, template,
quickstart, doctor, claim-check, and release evidence; `adoption_blocked`
identifies which priority still has a failing check. Its JSON includes
`repair_checklist`, with a command, expected artifact, and success signal for
the first priority repair or final ready recheck. Use `--skip-dist` for a fast
local pass, then run without it before validating distribution readiness.
`release_validation_status` is `release_validation_skipped` in that fast mode
and `release_validation_ready` only after wheel, sdist, isolated install, and
installed-package release checks complete.
When `adoption-check` is embedded in `release-check`, its ready recheck command
writes to an `adoption_recheck/` subdirectory so rerunning it does not overwrite
the release-check artifacts.

## Safety Contract

Falsiflow is intentionally conservative.

- Project validation errors block `claim_ready`, even if evidence rows pass.
- Evidence diagnostics with level `error` block `claim_ready`.
- Duplicate configured evidence keys block the claim.
- Placeholder values, blank required metadata, missing source files, or source
  files outside allowed roots block the relevant gate.
- Source-file provenance can be exported as a standalone manifest before
  sharing or reviewing an evidence pack.
- `audit_review.json` and `audit_review.md` summarize the audit decision,
  first blocking stage, top blockers, next actions, and human review checklist.
- A complete evidence bundle can package inputs, audit outputs, source
  manifest, copied raw files, and SHA-256 checksums for handoff.
- Falsiflow output is an audit of supplied evidence, not proof of biological
  safety, clinical efficacy, regulatory compliance, or commercial readiness.
- Derived metrics use fixed operations such as drift, percent change, gain,
  reduction, ratio, boolean any/all, and copy. Arbitrary code execution is not
  part of the project config.
- Warnings are visible in audit outputs but do not block readiness by
  themselves.

If a claim is blocked, `next_actions.json` identifies the first repairs to make,
such as `fix_project_config_diagnostics`, `fix_evidence_file_diagnostics`, or a
gate-specific evidence-filling action.

## Starter Templates

```bash
falsiflow templates
```

Included templates:

- `neural_materials`: H-A/H-B/H-C neural-interface material workflow.
- `rfq_vendor_evidence`: external lab or vendor readiness workflow.
- `biointerface_coatings`: coating provenance, extract stability, and
  matched-control bioresponse workflow.
- `wetware_support_hardware`: fluid-path provenance, medium-contact stability,
  and operational safety workflow.

## Template Gallery

Generate the cross-domain starter overview before picking a template:

```bash
falsiflow template-gallery \
  --out data/falsiflow/template_gallery.md \
  --json-out data/falsiflow/template_gallery.json
```

The Markdown report is titled `Falsiflow Template Gallery` and lists every
starter template's domain, claim, gates, required evidence rows, demo files,
source files, and first commands. The JSON output reaches
`template_gallery_ready` only when discovered templates have valid project
configs, positive and placeholder demo evidence, and source-file artifacts.
The bundled gallery currently spans neural-materials, external/vendor evidence,
biointerface coating, and wetware-support-hardware workflows.

Check a bundled or external template before sharing it:

```bash
falsiflow template-check \
  --template-dir examples/falsiflow/neural_materials \
  --out-dir data/falsiflow/template_check \
  --force
```

A checked template needs `template.json`, `project.json`, positive demo
evidence, placeholder demo evidence, and `source_files/`. The manifest should
declare `project_config`, `demo_evidence`, and `placeholder_evidence`.
`template-check` only returns `template_ready` when the positive demo reaches
`claim_ready`, the placeholder demo stays blocked, source provenance is ready,
and the generated bundle verifies from zip.

Package a checked template for distribution:

```bash
falsiflow template-pack \
  --template-dir examples/falsiflow/neural_materials \
  --out-dir data/falsiflow/template_pack \
  --zip-out data/falsiflow/neural_materials_template_pack.zip \
  --verify-out data/falsiflow/neural_materials_template_pack_verify.json \
  --report-out data/falsiflow/neural_materials_template_pack_verify.md \
  --force

falsiflow verify-template-pack \
  --zip data/falsiflow/neural_materials_template_pack.zip \
  --strict
```

`template-pack` copies the template, embeds `template-check` artifacts, writes a
`template_pack_manifest.json` with SHA-256 hashes, zips the pack, and verifies
the zip. A recipient should see `template_pack_verified` before trusting or
reusing the template.

Create a registry and lock a specific template source before installation:

```bash
falsiflow template-registry \
  --pack-zip data/falsiflow/neural_materials_template_pack.zip \
  --base-url https://example.org/falsiflow/templates/ \
  --out data/falsiflow/template_registry.json \
  --report-out data/falsiflow/template_registry.md

falsiflow template-lock \
  --registry data/falsiflow/template_registry.json \
  --template neural_materials \
  --version 0.1.0 \
  --out data/falsiflow/falsiflow_template_lock.json

falsiflow template-attest \
  --subject data/falsiflow/falsiflow_template_lock.json \
  --subject-type template-lock \
  --out data/falsiflow/falsiflow_template_lock.attestation.json \
  --builder release-ci \
  --key-id release-key \
  --signing-key local-demo-secret

falsiflow verify-template-attestation \
  --attestation data/falsiflow/falsiflow_template_lock.attestation.json \
  --subject data/falsiflow/falsiflow_template_lock.json \
  --signing-key local-demo-secret \
  --strict

falsiflow template-policy \
  --lock data/falsiflow/falsiflow_template_lock.json \
  --attestation data/falsiflow/falsiflow_template_lock.attestation.json \
  --out data/falsiflow/falsiflow_template_policy.json \
  --policy-id neural-materials-approved \
  --owner release-team \
  --signing-key local-demo-secret

falsiflow verify-template-policy \
  --policy data/falsiflow/falsiflow_template_policy.json \
  --lock data/falsiflow/falsiflow_template_lock.json \
  --attestation data/falsiflow/falsiflow_template_lock.attestation.json \
  --signing-key local-demo-secret \
  --strict

falsiflow template-release \
  --pack-zip data/falsiflow/neural_materials_template_pack.zip \
  --registry data/falsiflow/template_registry.json \
  --lock data/falsiflow/falsiflow_template_lock.json \
  --attestation data/falsiflow/falsiflow_template_lock.attestation.json \
  --policy data/falsiflow/falsiflow_template_policy.json \
  --out data/falsiflow/falsiflow_template_release.zip \
  --signing-key local-demo-secret

falsiflow verify-template-release \
  --release data/falsiflow/falsiflow_template_release.zip \
  --out data/falsiflow/falsiflow_template_release_verification.json \
  --report-out data/falsiflow/falsiflow_template_release_verification.md \
  --signing-key local-demo-secret \
  --strict
```

The registry records verified template-pack sources, byte sizes, and SHA-256
hashes. The lockfile pins one registry entry in `falsiflow_template_lock.json`
so installation can later prove the source zip has not changed. `--base-url`
writes publishable `source_url` entries; `template-lock` downloads URL sources
into a cache and verifies bytes plus SHA-256 before writing the lock.
`template-attest` records the lockfile digest, pinned source digest, builder,
and optional HMAC signature; `verify-template-attestation` returns
`template_attestation_verified` only when the subject bytes and signature match.
`template-policy` turns that verified lock into a commit-friendly adoption
allowlist, and `verify-template-policy` returns `template_policy_verified` only
when the lock, source hash, attestation payload, and trusted key id still match.
`template-release` bundles the pack, registry, lock, attestation, and policy
into one zip; `verify-template-release` returns `template_release_verified`
only when every included artifact and gate still matches. Release verification
also rejects unsafe artifact paths, duplicate artifact paths, unmanifested files,
and embedded registries whose SHA-256 no longer matches the lockfile.

Install a verified template pack into a local template root:

```bash
falsiflow template-install \
  --release data/falsiflow/falsiflow_template_release.zip \
  --signing-key local-demo-secret \
  --templates-dir data/falsiflow/installed_templates \
  --force

falsiflow templates \
  --template-root data/falsiflow/installed_templates

falsiflow init \
  --template neural_materials \
  --template-root data/falsiflow/installed_templates \
  --out my_installed_template_project
```

`template-install` verifies the lock attestation when `--attestation` is
provided, verifies an adoption policy when `--policy` is present, blocks adoption
with `--require-attestation` unless the report is `template_attestation_verified`,
verifies the zip, reruns `template-check` after installation, and writes
`falsiflow_template_index.json`. With `--release`, it verifies the release zip
and installs the bundled pack only after the attestation and policy pass. It
only returns
`template_installed` when the installed template is ready to reuse.

## Custom Workflows

Create a new evidence-gated claim without starting from a bundled template:

```bash
falsiflow scaffold \
  --out my_custom_claim \
  --project-id custom_screen \
  --claim-id custom_screen_claim \
  --claim-statement "Candidate has enough source-backed screening evidence to proceed." \
  --gate stability:ph_initial,ph_final,osmolality_final_mosm \
  --gate response:viability_pct,burst_rate_hz \
  --rule "response:viability_pct:>=:80:Viability must clear the screen." \
  --sample candidate_a:sample_001 \
  --sample response:control:control_001
```

The scaffold writes `project.json`, `evidence_template.csv`, `source_files/`,
and a local README. Fill the evidence template with measured values and raw
source-file references, then run `validate`, `render`, and `audit` as usual.
Use `--rule "gate_id:field:operator:value[:reason]"` for acceptance thresholds;
quote rules containing `<` or `>` in the shell.

Generate a reusable starter template for other teams:

```bash
falsiflow template-scaffold \
  --out my_custom_template \
  --template-id my_custom_template \
  --template-name "My Custom Template" \
  --claim-statement "Candidate has enough source-backed evidence to proceed." \
  --gate gate_a:score,replicate_score \
  --rule "gate_a:score:>=:1:Score must be present." \
  --check-out-dir data/falsiflow/my_custom_template_check \
  --json
```

The command writes `template.json`, `project.json`, `evidence_pass_demo.csv`,
`evidence_placeholder_demo.csv`, `source_files/demo_raw_export.csv`, and a local
README. It runs `template-check` before returning `template_scaffolded`, so the
generated template already proves that its positive demo passes and its
placeholder demo blocks.

## Core Commands

```bash
falsiflow init --template neural_materials --out project_dir
falsiflow quickstart --template biointerface_coatings --out quickstart_project --strict
falsiflow doctor --project-dir quickstart_project --strict
falsiflow scaffold --out custom_project --project-id custom_project --claim-id custom_claim --claim-statement "Source-backed claim." --gate gate_a:score --rule "gate_a:score:>=:1"
falsiflow template-scaffold --out custom_template --template-id custom_template --claim-statement "Source-backed claim." --gate gate_a:score --rule "gate_a:score:>=:1"
falsiflow template-gallery --out data/falsiflow/template_gallery.md --json-out data/falsiflow/template_gallery.json
falsiflow selftest --out-dir data/falsiflow/selftest
falsiflow demo --out-dir data/falsiflow/demo --force
falsiflow template-check --template-dir examples/falsiflow/neural_materials --out-dir data/falsiflow/template_check --force
falsiflow template-pack --template-dir examples/falsiflow/neural_materials --out-dir data/falsiflow/template_pack --force
falsiflow verify-template-pack --zip data/falsiflow/template_pack.zip --strict
falsiflow template-registry --pack-zip data/falsiflow/template_pack.zip --out data/falsiflow/template_registry.json
falsiflow template-lock --registry data/falsiflow/template_registry.json --template neural_materials --version 0.1.0 --out data/falsiflow/falsiflow_template_lock.json
falsiflow template-attest --subject data/falsiflow/falsiflow_template_lock.json --subject-type template-lock --out data/falsiflow/falsiflow_template_lock.attestation.json --signing-key local-demo-secret
falsiflow verify-template-attestation --attestation data/falsiflow/falsiflow_template_lock.attestation.json --subject data/falsiflow/falsiflow_template_lock.json --signing-key local-demo-secret --strict
falsiflow template-policy --lock data/falsiflow/falsiflow_template_lock.json --attestation data/falsiflow/falsiflow_template_lock.attestation.json --out data/falsiflow/falsiflow_template_policy.json --signing-key local-demo-secret
falsiflow verify-template-policy --policy data/falsiflow/falsiflow_template_policy.json --lock data/falsiflow/falsiflow_template_lock.json --attestation data/falsiflow/falsiflow_template_lock.attestation.json --signing-key local-demo-secret --strict
falsiflow template-release --pack-zip data/falsiflow/template_pack.zip --registry data/falsiflow/template_registry.json --lock data/falsiflow/falsiflow_template_lock.json --attestation data/falsiflow/falsiflow_template_lock.attestation.json --policy data/falsiflow/falsiflow_template_policy.json --out data/falsiflow/falsiflow_template_release.zip --signing-key local-demo-secret
falsiflow verify-template-release --release data/falsiflow/falsiflow_template_release.zip --signing-key local-demo-secret --out data/falsiflow/falsiflow_template_release_verification.json --report-out data/falsiflow/falsiflow_template_release_verification.md --strict
falsiflow template-install --release data/falsiflow/falsiflow_template_release.zip --signing-key local-demo-secret --templates-dir data/falsiflow/installed_templates --force
falsiflow adoption-check --out-dir data/falsiflow/adoption_check --skip-dist
falsiflow release-check --out-dir data/falsiflow/release_check
falsiflow validate --config project_dir/project.json --strict
falsiflow render --config project_dir/project.json --out-dir project_dir/blank_audit
falsiflow doctor --project-dir project_dir --strict
falsiflow claim-check --project-dir project_dir --strict
falsiflow claim-check --config project_dir/project.json --evidence project_dir/evidence_pass_demo.csv --out-dir project_dir/claim_check --strict
falsiflow audit --config project_dir/project.json --evidence project_dir/evidence_pass_demo.csv --out-dir project_dir/audit --strict
falsiflow sources --config project_dir/project.json --evidence project_dir/evidence_pass_demo.csv --out project_dir/source_manifest.json --report-out project_dir/source_manifest.md --strict
falsiflow bundle --config project_dir/project.json --evidence project_dir/evidence_pass_demo.csv --out-dir project_dir/evidence_bundle --zip-out project_dir/evidence_bundle.zip --strict
falsiflow next --config project_dir/project.json --evidence project_dir/evidence_placeholder_demo.csv --out-dir project_dir/next
falsiflow portfolio --input data/falsiflow --out-dir data/falsiflow/portfolio
```

When `portfolio --input` is omitted, Falsiflow scans `./data/falsiflow` in the
current working directory.

## Data Ingest

Convert a generic wide lab CSV into long-form Falsiflow evidence:

```bash
falsiflow ingest-wide-csv \
  --input path/to/lab_export.csv \
  --out data/falsiflow/my_run/evidence.csv \
  --config my_custom_claim/project.json \
  --coverage-out data/falsiflow/my_run/import_coverage.json \
  --gate-id h_a_medium_stability \
  --candidate-id my_candidate \
  --sample-id-column sample_id \
  --measured-at-column measured_at \
  --operator-or-agent-column operator \
  --source-file path/to/lab_export.csv \
  --field ph_initial \
  --field ph_final
```

The public namespaced form is equivalent and is the preferred command for new
workflows:

```bash
falsiflow evidence import \
  --input path/to/lab_export.csv \
  --out data/falsiflow/my_run/evidence.csv \
  --gate-id h_a_medium_stability \
  --candidate-id my_candidate \
  --sample-id-column sample_id \
  --field ph_initial \
  --field ph_final
```

When `--config` is provided, Falsiflow compares the imported evidence keys
against the project's required gate/candidate/sample/field rows before audit.
Use `--strict` to exit non-zero when required evidence rows are still missing
or duplicated.

Write a source-file provenance manifest for an evidence pack:

```bash
falsiflow sources \
  --config my_custom_claim/project.json \
  --evidence data/falsiflow/my_run/evidence.csv \
  --out data/falsiflow/my_run/source_manifest.json \
  --report-out data/falsiflow/my_run/source_manifest.md \
  --strict
```

The manifest lists every referenced source file, resolved path, reference
count, missing file, outside-root file, and evidence row with a blank
`source_file`.

Run the complete claim gate in one step:

```bash
falsiflow claim-check \
  --project-dir my_custom_claim \
  --evidence data/falsiflow/my_run/evidence.csv \
  --out-dir data/falsiflow/my_run/claim_check \
  --strict
```

The `claim-check` command writes `claim_check.json`, `claim_check.md`,
`evidence_bundle.zip`, and `evidence_bundle_verify.*`. The report title is
`Falsiflow Claim Check`, and the machine status is either `claim_check_ready`
or `claim_check_blocked`. With `--project-dir`, Falsiflow defaults to
`PROJECT_DIR/project.json`, `PROJECT_DIR/evidence_pass_demo.csv`, and
`PROJECT_DIR/claim_check`; pass explicit paths when using a different evidence
CSV or output location.

Build a portable evidence bundle:

```bash
falsiflow bundle \
  --config my_custom_claim/project.json \
  --evidence data/falsiflow/my_run/evidence.csv \
  --out-dir data/falsiflow/my_run/evidence_bundle \
  --zip-out data/falsiflow/my_run/evidence_bundle.zip \
  --strict
```

The bundle contains `inputs/`, `audit/`, `sources/`, `source_manifest.*`, and
`bundle_manifest.json` with SHA-256 checksums for copied artifacts.

Verify a received bundle before trusting or forwarding it:

```bash
falsiflow verify-bundle \
  --zip data/falsiflow/my_run/evidence_bundle.zip \
  --out data/falsiflow/my_run/evidence_bundle_verify.json \
  --report-out data/falsiflow/my_run/evidence_bundle_verify.md \
  --strict
```

Verification checks required artifact roles, relative paths, byte sizes,
SHA-256 hashes, missing files, duplicate paths, copied source records, and
unmanifested files. Use `--bundle-dir` instead of `--zip` when you already have
an extracted bundle directory.

Convert existing LIMINA source-value sheets:

```bash
falsiflow ingest-limina-source-values \
  --input data/nhi_pedot_h_a_source_values.csv \
  --input data/nhi_pedot_forward_source_values.csv \
  --out data/falsiflow/limina_nhi_pedot_habc/evidence_from_source_values.csv \
  --summary-out data/falsiflow/limina_nhi_pedot_habc/ingest_summary.json \
  --project-out configs/falsiflow/limina_nhi_pedot_habc/project.json \
  --default-candidate limina_alg_lam_pedot_lowdose_v0_2 \
  --default-gate h_a_medium_stability \
  --source-file-base-dir ../../.. \
  --allowed-source-root data/source_files \
  --allowed-source-root data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports
```

The generated LIMINA config is a provenance-completeness audit, not a material
suitability claim.

## Machine-Readable Schemas

```bash
falsiflow schema --kind project
falsiflow schema --kind evidence-row
falsiflow schema --kind claim-summary
falsiflow schema --kind audit-review
falsiflow schema --kind portfolio-summary
falsiflow schema --kind import-coverage
falsiflow schema --kind source-manifest
falsiflow schema --kind bundle-manifest
falsiflow schema --kind bundle-verification
falsiflow schema --kind claim-check
falsiflow schema --kind quickstart-summary
falsiflow schema --kind doctor-summary
falsiflow schema --kind demo-summary
falsiflow schema --kind template-check
falsiflow schema --kind template-pack-manifest
falsiflow schema --kind template-pack-verification
falsiflow schema --kind template-install
falsiflow schema --kind template-registry
falsiflow schema --kind template-lock
falsiflow schema --kind template-attestation
falsiflow schema --kind template-attestation-verification
falsiflow schema --kind template-policy
falsiflow schema --kind template-policy-verification
falsiflow schema --kind template-release
falsiflow schema --kind template-release-verification
falsiflow schema --kind template-gallery
falsiflow schema --kind adoption-check
falsiflow schema --kind release-check
falsiflow schema --kind all --out schemas.json
```

Schemas are generated from the same operation, operator, and evidence-column
constants used by the runtime, so editors and integrations can stay aligned
with the active Falsiflow contract.

## Repository Map

- `falsiflow/`: package implementation.
- `falsiflow/templates/`: packaged starter templates.
- `Makefile`: local install, start, test, release-check, and clean shortcuts.
- `.github/workflows/falsiflow.yml`: full regression, release-check, template,
  and bundle CI gate.
- `.github/workflows/falsiflow-pages.yml`: GitHub Pages static demo deployment
  built from `falsiflow demo-package`.
- `.github/workflows/falsiflow-cross-platform.yml`: Linux, macOS, Windows,
  pipx, installer, browser-entry, and external-check smoke tests.
- `.github/workflows/falsiflow-publish.yml`: wheel/sdist build, `twine check`,
  artifact upload, and optional PyPI trusted publishing.
- `scripts/install_local.sh`: one-command local installer for checkout or
  public Git repository installs.
- `scripts/install_local.ps1`: Windows PowerShell installer for the same local
  app flow.
- `examples/falsiflow/`: readable copies of starter templates.
- `scripts/falsiflow.py`: repository-local CLI wrapper.
- `scripts/falsiflow_tests/regress_falsiflow_core.py`: dependency-light
  regression suite.
- `docs/falsiflow_mvp.md`: schema, command, and design contract.
- `docs/limina_strategy.md` and `docs/limina_tooling_roadmap.md`: historical
  LIMINA research context that motivated Falsiflow.
- `data/falsiflow/`: generated demo and migrated LIMINA audit outputs.

## Verification

Contributor, release, security, and responsible-use notes live in
[CONTRIBUTING.md](CONTRIBUTING.md), [RELEASE.md](RELEASE.md),
[SECURITY.md](SECURITY.md), and [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md).

```bash
python3 -m py_compile \
  falsiflow/core.py \
  falsiflow/cli.py \
  falsiflow/adapters.py \
  scripts/falsiflow.py \
  scripts/falsiflow_tests/regress_falsiflow_core.py

python3 scripts/falsiflow_tests/regress_falsiflow_core.py
```

CI also compiles the package, runs the regression suite, emits JSON Schemas,
validates all starter templates, runs `falsiflow selftest`, runs `falsiflow
demo`, runs `falsiflow quickstart`, runs `falsiflow doctor`, runs
`falsiflow template-gallery`, runs `falsiflow adoption-check`, runs
`falsiflow template-check`, runs `falsiflow claim-check`, runs strict demo
audits, checks source manifests, verifies evidence bundle zip archives,
smoke-tests `falsiflow template-scaffold`, checks `scripts/install_local.sh`,
checks `scripts/install_local.ps1`, checks the `Makefile` shortcuts, checks
`falsiflow onboard`, checks `falsiflow static-demo`, packages and verifies a
template pack, runs `falsiflow release-check`, and builds a strict portfolio
dashboard.

`release-check` also verifies the repository release surface: `pyproject.toml`,
`README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `RELEASE.md`,
`SECURITY.md`, `RESPONSIBLE_USE.md`, `MANIFEST.in`, the console script entry
point, package template data, packaged starter files, the end-to-end walkthrough,
external template authoring docs, starter template generation docs,
one-command quickstart docs, one-command doctor docs, one-command claim gate docs, trusted audit review
docs, priority-readiness adoption gate docs, template gallery docs, template pack packaging docs,
`template-check` results for packaged templates, `template-pack` verification
reports, template
registry, lockfile, attestation,
`verify-template-attestation`, policy, and `verify-template-policy` reports,
template release bundles and `verify-template-release` reports,
`adoption_check.json` and `adoption_check.md`, bundle zip
verification reports, generated wheel/sdist artifacts, an isolated wheel
install, and the portfolio generated from ready starter bundles. Use
`--skip-dist` only when you want a faster local check without wheel/sdist
validation.
