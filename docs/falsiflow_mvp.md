# Falsiflow MVP

Falsiflow is a small, configurable evidence-gated R&D workflow engine. It grew
out of the LIMINA neural-materials work, but its valuable part is broader:
make high-risk technical claims earn promotion only after source-backed gates
pass.

## Highest-Value Improvement Direction

The highest-value direction is to turn the bespoke LIMINA workflow into a
general open-source tool flow:

1. define a claim, gates, required fields, source-file policy, and acceptance
   rules in JSON;
2. render measurement templates that tell a human or lab vendor exactly what
   evidence is missing;
3. ingest long-form evidence CSV rows with raw-source provenance;
4. audit whether the claim is ready, blocked by missing evidence, or failed by
   acceptance rules;
5. compute fixed, inspectable derived metrics such as drift, percent change,
   ratios, and gains from raw evidence;
6. print and write the next evidence-filling actions.

That is more valuable than a single ALG-LAM-PEDOT bet because it can travel to
other high-uncertainty R&D domains: biomaterials, MEA interfaces, cartridges,
wetware support hardware, coatings, and later any project where unsupported
claims are expensive.

For positioning against spreadsheets, CI suites, ELN/LIMS systems, ML eval
harnesses, materials databases, and workflow orchestrators, see
[falsiflow_positioning.md](falsiflow_positioning.md).
For the module map, command flow, release invariants, and extension points, see
[falsiflow_architecture.md](falsiflow_architecture.md).
For evidence CSV fields, JSON status contracts, report artifacts, schemas, and
CI/ELN/LIMS integration boundaries, see
[falsiflow_data_contract.md](falsiflow_data_contract.md).
For vendor, instrument, plate-reader, and generic wide-CSV adapter profiles,
see [falsiflow_adapter_profiles.md](falsiflow_adapter_profiles.md).
For blocked command recovery, install/start failures, template verification
failures, `claim_check_blocked`, and `external_blocked`, see
[falsiflow_troubleshooting.md](falsiflow_troubleshooting.md).
For external template authoring, placeholder demo design, source provenance, and
verified release flow, see
[falsiflow_template_authoring.md](falsiflow_template_authoring.md).
For public case cards covering the bundled starter templates and reviewer
scripts, see [falsiflow_public_casebook.md](falsiflow_public_casebook.md).
For machine-verifiable casebook proof across positive demos and placeholder
blockers, see [falsiflow_casebook_check.md](falsiflow_casebook_check.md).
For community expectations, support boundaries, and public project direction,
see [../CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md),
[../SUPPORT.md](../SUPPORT.md), [../GOVERNANCE.md](../GOVERNANCE.md),
[../CITATION.cff](../CITATION.cff), and [../ROADMAP.md](../ROADMAP.md).
For the local-first security posture, Dependabot automation, OpenSSF Scorecard
workflow, bundle verification boundary, and release trust gates, see
[falsiflow_security_posture.md](falsiflow_security_posture.md).
For the generated command reference, see
[falsiflow_cli_reference.md](falsiflow_cli_reference.md), which is produced by
`falsiflow cli-reference --out docs/falsiflow_cli_reference.md`.

## MVP Commands

Run the beginner local app:

```bash
make install-local
make start
```

Run the same path as a one-command local installer:

```bash
scripts/install_local.sh --from-local . --check
```

`scripts/install_local.sh` can also clone a public Git repository when
`FALSIFLOW_REPO_URL` is set. It creates a virtual environment under
`~/.falsiflow`, installs Falsiflow, and runs the local browser app.

Windows users can run the PowerShell installer:

```powershell
.\scripts\install_local.ps1 -FromLocal . -Check
```

`pipx` users can install from a checkout:

```bash
make pipx-install
make pipx-start
```

Run onboarding:

```bash
python3 scripts/falsiflow.py onboard \
  --check \
  --json
```

`onboard` writes `onboard_summary.json` with the launchpad, report, wizard,
plain-language steps, and next commands.

Export a static demo site:

```bash
python3 scripts/falsiflow.py static-demo \
  --out-dir data/falsiflow/static_demo \
  --force
```

`static-demo` writes a hostable `index.html`, `try_report.html`,
`falsiflow_wizard.html`, and `static_demo_summary.json` for GitHub Pages,
Netlify, or any static file server.

For a public-demo handoff package:

```bash
python3 scripts/falsiflow.py demo-package \
  --out-dir data/falsiflow/public_demo \
  --force
python3 scripts/falsiflow.py publish-kit \
  --out-dir data/falsiflow/publish_kit \
  --force
python3 scripts/falsiflow.py launch-kit \
  --out-dir data/falsiflow/launch_kit \
  --force
python3 scripts/falsiflow.py external-evidence \
  --out data/falsiflow/external_evidence.json \
  --force
python3 scripts/falsiflow.py external-check \
  --out-dir data/falsiflow/external_check \
  --evidence data/falsiflow/external_evidence.json \
  --force
```

`demo-package` adds `demo_package_summary.json`, `.nojekyll`, `netlify.toml`,
and `publish_checklist.md`. `publish-kit` writes `publish_handoff.json`,
`publish_handoff.md`, `publish.env.example`, `github_publish_commands.sh`,
`public_release_evidence.json`, `public_release_evidence.md`,
`release_rehearsal.json`, `release_rehearsal.md`, and a nested public demo
package so account-bound GitHub/Pages/PyPI steps have a reviewable handoff
artifact, a one-page final evidence ledger, and a public release rehearsal with
ordered commands, expected artifacts, success signals, and stop conditions.
`launch-kit` adds
`launch_summary.json`,
`proof_card.md`, `announcement.md`, `demo_script.md`,
`readme_proof_strip.svg`, `social_preview.svg`, `github_repo_profile.md`,
`launch_posts.md`, `launch_metrics.json`, `launch_metrics.md`, and
`maintainer_checklist.md` so public launch copy, GitHub repository profile
settings, social preview imagery, proof points, and 1k-star launch tracking are
reviewed before account-bound publishing. The nested publish handoff also
includes `release_rehearsal.md` so launch reviewers can rehearse the final
public release path before announcements. `external-evidence` writes a fillable JSON
template for hosted demo, public PyPI package URL plus PyPI JSON API proof,
checkout-based pipx smoke, public-package pipx smoke, and Windows/PowerShell
smoke evidence.
`external-check --evidence` writes `external_readiness.json` and reports
`external_ready` or `external_blocked` based on public repo URL, hosted demo
URL, PyPI package URL, pipx, and Windows/PowerShell validation evidence.
After the hosted demo is live, the `Falsiflow External Evidence` GitHub Actions
workflow accepts the demo URL and PyPI package URL, verifies the demo over
HTTPS, fetches `https://pypi.org/pypi/falsiflow/json`, runs checkout pipx,
public-package pipx, and Windows smoke tests, writes
`falsiflow_external_evidence.json`, runs
`external-check --strict`, and uploads the evidence/readiness artifact.

The root `action.yml` is the downstream CI entry point. It installs Falsiflow and
can run `claim-check`, `template-check`, `casebook-check`, `release-check`,
`adoption-check`, `quickstart`, or `external-check`, writing the same JSON and
Markdown artifacts that local commands produce. The default `install-command`
installs from `GITHUB_ACTION_PATH`, so a versioned action tag can run before
PyPI publication is complete. Downstream repositories can still override
`install-command` when they want to install from PyPI, a fork, or a
repository-local editable checkout.

For repository-local CI checks:

```bash
python3 scripts/falsiflow.py start \
  --check \
  --json
```

`start` is the lowest-friction entry point. It chooses a free localhost port by
default, opens the browser unless `--no-open` is used, writes
`serve_summary.json`, and points users to the launchpad, report, dashboard,
bundle, wizard, and `workbench.html` without requiring an account. The workbench
adds the first browser-side closed loop: select a template, upload an optional
`project.json`, evidence CSV, and source files, run the local doctor/claim-check
path through the localhost API, and inspect ready/blocked status plus report,
review flow, evidence lineage, repair checklist, source manifest, dashboard,
bundle verification, and bundle links.

Run a static local browser demo:

```bash
python3 scripts/falsiflow.py try \
  --out-dir data/falsiflow/try \
  --force
```

`try` writes `try_summary.json`, `index.html`, and `try_report.html`. The
launchpad is titled `Falsiflow Launchpad` and links directly to the proof
report, generated claim dashboard, bundle, and generated browser wizard. The
report is titled `Falsiflow Try` and keeps the audit details one click deeper.

Generate a structured discovery package without making AI a core dependency:

```bash
python3 scripts/falsiflow.py discover \
  --goal "MEA neural interface material" \
  --out-dir data/falsiflow/discovery \
  --force
```

`discover` writes `evidence_records.json`, `candidate_queue.json`, `ranking.md`,
`assay_plan.md`, `rfq_package.md`, and a placeholder `project_draft/`. It
records `ai_used=false` and `claim_ready=false`, because discovery can propose
candidates, source requirements, and gates but cannot make a material or R&D
claim ready without measured evidence.

The same artifact contract is exposed through focused public interfaces:

```bash
python3 scripts/falsiflow.py agent discover \
  --goal "MEA neural interface material" \
  --out-dir data/falsiflow/discovery \
  --force
python3 scripts/falsiflow.py candidate rank \
  --goal "MEA neural interface material" \
  --out-dir data/falsiflow/candidate_rank \
  --force
python3 scripts/falsiflow.py assay-plan \
  --goal "MEA neural interface material" \
  --out-dir data/falsiflow/assay_plan \
  --force
```

`agent discover`, `candidate rank`, and `assay-plan` are interface names around
the same Core boundary: they may propose candidates, rankings, gates, assay
plans, and RFQ drafts, but they cannot turn `claim_ready` true.

Serve the same local browser demo over localhost:

```bash
python3 scripts/falsiflow.py serve \
  --out-dir data/falsiflow/try \
  --force \
  --check
```

`serve` writes `serve_summary.json` with the localhost URL, `try_report_url`,
and `wizard_url`, then can run an HTTP check that fetches `index.html` before
exiting.

Draft a project from a static browser wizard:

```bash
python3 scripts/falsiflow.py wizard \
  --out data/falsiflow/falsiflow_wizard.html \
  --force
```

`wizard` writes `Falsiflow Browser Wizard`, an offline HTML form that generates
a scaffold command plus starter `project.json` and `evidence_template.csv`
downloads. The wizard includes plain-language presets for material screening,
vendor evidence review, and custom R&D decisions.

Render a blank template and audit:

```bash
python3 scripts/falsiflow.py render \
  --config examples/falsiflow/neural_materials/project.json \
  --out-dir data/falsiflow/neural_materials_blank
```

Audit a passing demonstration evidence file:

```bash
python3 scripts/falsiflow.py audit \
  --config examples/falsiflow/neural_materials/project.json \
  --evidence examples/falsiflow/neural_materials/evidence_pass_demo.csv \
  --out-dir data/falsiflow/neural_materials_pass \
  --strict
```

Every audit writes a concise review card in addition to the full audit:
`audit_review.json` and `audit_review.md`. The Markdown report is titled
`Falsiflow Audit Review`; `review_ready` means the claim can move to human
release review, while `review_blocked` records the first blocking stage, top
blockers, next actions, and human review checklist.

Ask for the next blocked actions from placeholder evidence:

```bash
python3 scripts/falsiflow.py next \
  --config examples/falsiflow/neural_materials/project.json \
  --evidence examples/falsiflow/neural_materials/evidence_placeholder_demo.csv \
  --out-dir data/falsiflow/neural_materials_placeholder
```

Run the regression check:

```bash
python3 scripts/falsiflow_tests/regress_falsiflow_core.py
```

Run an installed-package style smoke test of schemas, templates, demo audits,
and portfolio output:

```bash
python3 scripts/falsiflow.py selftest --out-dir data/falsiflow/selftest
python3 scripts/falsiflow.py demo --out-dir data/falsiflow/demo --force
python3 scripts/falsiflow.py template-check \
  --template-dir examples/falsiflow/neural_materials \
  --out-dir data/falsiflow/template_check \
  --force
```

Generate a cross-domain starter gallery:

```bash
python3 scripts/falsiflow.py template-gallery \
  --out data/falsiflow/template_gallery.md \
  --json-out data/falsiflow/template_gallery.json
```

`template-gallery` writes a Markdown `Falsiflow Template Gallery` and JSON
summary that show each starter template's domain, claim, gates, required
evidence rows, demo evidence, placeholder evidence, source files, and first
commands. It is the release-checked generality proof that the engine is not
limited to the original neural-materials use case.

Generate the machine-verifiable public casebook proof:

```bash
python3 scripts/falsiflow.py casebook-check \
  --out-dir data/falsiflow/casebook_check \
  --force
```

`casebook-check` writes `casebook_check.json` and `casebook_check.md`. The
Markdown report is titled `Falsiflow Casebook Check`. `casebook_check_ready`
means every starter's positive demo reaches `claim_ready`, every placeholder
demo stays blocked, source provenance is ready, and every positive demo bundle
verifies from zip. It also writes `casebook_reviewer_replay.md`,
`casebook_reviewer_replay.sh`, and `casebook_reviewer_replay.ps1`; those replay
artifacts run each template's positive claim-check and placeholder blocked-path
claim-check for reviewers who want to reproduce the casebook outside CI.

Run the adoption-priority readiness gate:

```bash
python3 scripts/falsiflow.py adoption-check \
  --out-dir data/falsiflow/adoption_check \
  --skip-dist \
  --force
```

`adoption-check` writes `adoption_check.json` and `adoption_check.md`. The
Markdown report is titled `Falsiflow Adoption Check`. `adoption_ready` means
the five maintained priorities are backed by current open-source entry,
trusted-audit, generality, release/distribution, and user-experience evidence;
`adoption_blocked` names the priority and check that still needs repair. The
summary includes `repair_checklist` commands, expected artifacts, and success
signals for priority repairs or final ready rechecks. Run without `--skip-dist`
before treating distribution readiness as validated. The
`release_validation_status` field is `release_validation_skipped` when
distribution checks are skipped and `release_validation_ready` after wheel,
sdist, isolated install, and installed-package release checks complete. When embedded in
`release-check`, the ready recheck command writes to an `adoption_recheck/`
subdirectory so the release-check artifacts are not overwritten.

Create a custom project from a claim, gate list, required fields, and samples:

```bash
python3 scripts/falsiflow.py scaffold \
  --out data/falsiflow/custom_screen_project \
  --project-id custom_screen \
  --claim-id custom_screen_claim \
  --claim-statement "Candidate has enough source-backed screening evidence to proceed." \
  --gate stability:ph_initial,ph_final \
  --gate response:viability_pct,burst_rate_hz \
  --rule "response:viability_pct:>=:80:Viability must clear the screen." \
  --sample candidate_a:sample_001 \
  --sample response:control:control_001
```

The scaffold writes `project.json`, `evidence_template.csv`, `source_files/`,
and a local README. Its placeholder evidence is intentionally blocked until the
user fills measured values, metadata, and source-file references. Optional
`--rule` entries add acceptance thresholds in the form
`gate_id:field:operator:value[:reason]`; quote rules that use `<` or `>` so the
shell does not treat them as redirection.

Create a reusable starter template with built-in positive and placeholder demos:

```bash
python3 scripts/falsiflow.py template-scaffold \
  --out data/falsiflow/custom_template \
  --template-id custom_template \
  --template-name "Custom Template" \
  --claim-statement "Candidate has enough source-backed evidence to proceed." \
  --gate gate_a:score,replicate_score \
  --rule "gate_a:score:>=:1:Score must be present." \
  --check-out-dir data/falsiflow/custom_template_check
```

`template-scaffold` writes `template.json`, `project.json`,
`evidence_pass_demo.csv`, `evidence_placeholder_demo.csv`,
`source_files/demo_raw_export.csv`, and a local README. It runs
`template-check` before returning `template_scaffolded`, so generated templates
start with a passing demo, a blocked placeholder demo, complete source
provenance, and a verified bundle.

Package a checked template into a distributable zip:

```bash
python3 scripts/falsiflow.py template-pack \
  --template-dir examples/falsiflow/neural_materials \
  --out-dir data/falsiflow/template_pack \
  --zip-out data/falsiflow/neural_materials_template_pack.zip \
  --verify-out data/falsiflow/neural_materials_template_pack_verify.json \
  --report-out data/falsiflow/neural_materials_template_pack_verify.md \
  --force

python3 scripts/falsiflow.py verify-template-pack \
  --zip data/falsiflow/neural_materials_template_pack.zip \
  --strict
```

The pack contains the copied template, `template-check` artifacts, and
`template_pack_manifest.json` with SHA-256 hashes. A recipient should verify the
zip and see `template_pack_verified` before adopting the template.

Index and lock a verified template-pack source:

```bash
python3 scripts/falsiflow.py template-registry \
  --pack-zip data/falsiflow/neural_materials_template_pack.zip \
  --base-url https://example.org/falsiflow/templates/ \
  --out data/falsiflow/template_registry.json \
  --report-out data/falsiflow/template_registry.md

python3 scripts/falsiflow.py template-lock \
  --registry data/falsiflow/template_registry.json \
  --template neural_materials \
  --version 0.1.0 \
  --out data/falsiflow/falsiflow_template_lock.json

python3 scripts/falsiflow.py template-attest \
  --subject data/falsiflow/falsiflow_template_lock.json \
  --subject-type template-lock \
  --out data/falsiflow/falsiflow_template_lock.attestation.json \
  --builder release-ci \
  --key-id release-key \
  --signing-key local-demo-secret

python3 scripts/falsiflow.py verify-template-attestation \
  --attestation data/falsiflow/falsiflow_template_lock.attestation.json \
  --subject data/falsiflow/falsiflow_template_lock.json \
  --signing-key local-demo-secret \
  --strict

python3 scripts/falsiflow.py template-policy \
  --lock data/falsiflow/falsiflow_template_lock.json \
  --attestation data/falsiflow/falsiflow_template_lock.attestation.json \
  --out data/falsiflow/falsiflow_template_policy.json \
  --policy-id neural-materials-approved \
  --owner release-team \
  --signing-key local-demo-secret

python3 scripts/falsiflow.py verify-template-policy \
  --policy data/falsiflow/falsiflow_template_policy.json \
  --lock data/falsiflow/falsiflow_template_lock.json \
  --attestation data/falsiflow/falsiflow_template_lock.attestation.json \
  --signing-key local-demo-secret \
  --strict

python3 scripts/falsiflow.py template-release \
  --pack-zip data/falsiflow/neural_materials_template_pack.zip \
  --registry data/falsiflow/template_registry.json \
  --lock data/falsiflow/falsiflow_template_lock.json \
  --attestation data/falsiflow/falsiflow_template_lock.attestation.json \
  --policy data/falsiflow/falsiflow_template_policy.json \
  --out data/falsiflow/falsiflow_template_release.zip \
  --signing-key local-demo-secret

python3 scripts/falsiflow.py verify-template-release \
  --release data/falsiflow/falsiflow_template_release.zip \
  --out data/falsiflow/falsiflow_template_release_verification.json \
  --report-out data/falsiflow/falsiflow_template_release_verification.md \
  --signing-key local-demo-secret \
  --strict
```

The registry records verified sources, byte sizes, and SHA-256 hashes. The
lockfile pins one source in `falsiflow_template_lock.json`. `--base-url`
publishes `source_url` entries; locking and installation verify URL downloads by
byte count and SHA-256. `template-attest` records the lock digest and pinned
source digest with an optional HMAC signature; `verify-template-attestation`
returns `template_attestation_verified` only when the subject and signature
match. `template-policy` writes a reusable adoption allowlist, and
`verify-template-policy` returns `template_policy_verified` only when the lock,
source hash, attestation payload, and trusted key id still match.
`template-release` writes a single distributable zip containing the verified
pack, registry, lock, attestation, and policy; `verify-template-release`
returns `template_release_verified` only when every included artifact and
internal gate still matches. Verification rejects unsafe artifact paths,
duplicate artifact paths, unmanifested files, and registry bytes that no longer
match the lockfile's `registry_sha256`. Use `--report-out` to write a Markdown
audit report such as `falsiflow_template_release_verification.md` for human
review alongside the JSON verification report. The report includes a
`Review Artifact Index` for the release zip, release manifest, template pack,
registry, lock, attestation, and policy.

Install a verified template release into an external template root:

```bash
python3 scripts/falsiflow.py template-install \
  --release data/falsiflow/falsiflow_template_release.zip \
  --signing-key local-demo-secret \
  --templates-dir data/falsiflow/installed_templates \
  --force

python3 scripts/falsiflow.py templates \
  --template-root data/falsiflow/installed_templates

python3 scripts/falsiflow.py init \
  --template neural_materials \
  --template-root data/falsiflow/installed_templates \
  --out data/falsiflow/installed_project
```

`template-install` can enforce the attestation with `--require-attestation`,
can enforce an adoption policy with `--policy`, then verifies the zip, reruns
`template-check` from the installed
directory, and writes `falsiflow_template_index.json`. With `--release`, it
verifies the release zip, embedded attestation, and embedded policy before
installing the bundled pack. It returns `template_installed` only when the
installed template is reusable.

List and validate templates:

```bash
python3 scripts/falsiflow.py templates
python3 scripts/falsiflow.py validate \
  --config examples/falsiflow/neural_materials/project.json \
  --strict
```

`validate --strict` is meant to run before evidence collection starts. It now
checks the project structure, duplicate gate/sample/required-field ids, derived
fields that would overwrite raw evidence fields, references to unavailable
raw/derived fields, ambiguous or missing cross-sample references, unknown
acceptance operators, and acceptance rules that target fields the audit engine
cannot compute.
The same validation is embedded in `audit`, `render`, and `next`: any project
validation error blocks the claim even if the submitted evidence rows would
otherwise pass every gate. The first next action becomes
`fix_project_config_diagnostics` until the project config has zero validation
errors.

Emit machine-readable schemas for external tools:

```bash
python3 scripts/falsiflow.py schema --kind project
python3 scripts/falsiflow.py schema --kind evidence-row
python3 scripts/falsiflow.py schema --kind claim-summary
python3 scripts/falsiflow.py schema --kind audit-review
python3 scripts/falsiflow.py schema --kind portfolio-summary
python3 scripts/falsiflow.py schema --kind import-coverage
python3 scripts/falsiflow.py schema --kind source-manifest
python3 scripts/falsiflow.py schema --kind bundle-manifest
python3 scripts/falsiflow.py schema --kind bundle-verification
python3 scripts/falsiflow.py schema --kind claim-check
python3 scripts/falsiflow.py schema --kind quickstart-summary
python3 scripts/falsiflow.py schema --kind doctor-summary
python3 scripts/falsiflow.py schema --kind demo-summary
python3 scripts/falsiflow.py schema --kind template-check
python3 scripts/falsiflow.py schema --kind template-pack-manifest
python3 scripts/falsiflow.py schema --kind template-pack-verification
python3 scripts/falsiflow.py schema --kind template-install
python3 scripts/falsiflow.py schema --kind template-registry
python3 scripts/falsiflow.py schema --kind template-lock
python3 scripts/falsiflow.py schema --kind template-attestation
python3 scripts/falsiflow.py schema --kind template-attestation-verification
python3 scripts/falsiflow.py schema --kind template-policy
python3 scripts/falsiflow.py schema --kind template-policy-verification
python3 scripts/falsiflow.py schema --kind template-release
python3 scripts/falsiflow.py schema --kind template-release-verification
python3 scripts/falsiflow.py schema --kind template-gallery
python3 scripts/falsiflow.py schema --kind casebook-check
python3 scripts/falsiflow.py schema --kind external-evidence
python3 scripts/falsiflow.py schema --kind external-readiness
python3 scripts/falsiflow.py schema --kind adoption-check
python3 scripts/falsiflow.py schema --kind release-check
python3 scripts/falsiflow.py schema --kind all --out data/falsiflow/schemas.json
```

Schema kinds are `project`, `evidence-row`, `claim-summary`, `audit-review`,
`portfolio-summary`, `import-coverage`, `source-manifest`, `bundle-manifest`,
`bundle-verification`, `claim-check`, `quickstart-summary`, `doctor-summary`, `demo-summary`, `template-check`,
`template-pack-manifest`, `template-pack-verification`, `template-install`,
`template-registry`, `template-lock`, `template-attestation`,
`template-attestation-verification`, `template-policy`,
`template-policy-verification`, `template-release`,
`template-release-verification`, `template-gallery`, `casebook-check`,
`adoption-check`, `release-check`, and
`all`. They are
generated from the same operation, operator, and evidence-column constants used
by the runtime, so integrations can pin their forms and editor hints to the
active Falsiflow contract.

Available starter templates:

- `neural_materials`: H-A/H-B/H-C material-interface workflow.
- `rfq_vendor_evidence`: vendor or external-lab readiness workflow that keeps
  quotes and capability replies separate from measured evidence.
- `biointerface_coatings`: coating provenance, extract stability, and
  matched-control bioresponse screening.
- `wetware_support_hardware`: fluid-path provenance, medium-contact stability,
  and operational safety for support hardware.
- `ai_claim_evaluation`: versioned AI evaluation provenance, benchmark quality,
  and reproducibility-package evidence for public model comparison claims.
- `product_metric_launch`: activation lift, guardrail safety, and rollback
  readiness evidence for product launch claims.

The repository also has Python package metadata, so local development can use a
standard console command after installation:

```bash
python3 -m pip install -e .
falsiflow selftest
falsiflow release-check --out-dir data/falsiflow/release_check
falsiflow adoption-check --out-dir data/falsiflow/adoption_check --skip-dist
falsiflow quickstart --template biointerface_coatings --out data/falsiflow/quickstart_project --strict
falsiflow doctor --project-dir data/falsiflow/quickstart_project --strict
falsiflow claim-check --project-dir examples/falsiflow/neural_materials --out-dir data/falsiflow/claim_check --strict
falsiflow template-scaffold \
  --out my_custom_template \
  --template-id my_custom_template \
  --claim-statement "Custom claim has source-backed evidence." \
  --gate gate_a:score \
  --rule "gate_a:score:>=:1"
falsiflow scaffold \
  --out my_custom_claim \
  --project-id my_custom_claim \
  --claim-id my_custom_claim_readiness \
  --claim-statement "Custom claim has source-backed evidence." \
  --gate gate_a:score \
  --rule "gate_a:score:>=:1"
falsiflow audit \
  --config examples/falsiflow/neural_materials/project.json \
  --evidence examples/falsiflow/neural_materials/evidence_pass_demo.csv \
  --out-dir data/falsiflow/neural_materials_pass \
  --strict
```

For a short end-to-end walkthrough from starter template to verified bundle, see
`examples/README.md`. The same path can be run as a one-command demo with
`falsiflow demo --out-dir data/falsiflow/demo --force`.

Template authors can run `falsiflow template-check --template-dir path/to/template
--out-dir data/falsiflow/template_check --force` before publishing a template.
The template manifest should declare `project_config`, `demo_evidence`, and
`placeholder_evidence`; the check only returns `template_ready` when the
positive demo passes, the placeholder demo remains blocked, source provenance is
complete, and the generated bundle verifies from zip.

Installed packages include the starter templates. A user can start outside the
repository without copying example files by hand:

```bash
falsiflow templates
falsiflow init --template biointerface_coatings --out my_coating_readiness
falsiflow audit \
  --config my_coating_readiness/project.json \
  --evidence my_coating_readiness/evidence_pass_demo.csv \
  --out-dir my_coating_readiness/audit \
  --strict
```

Convert the live LIMINA NHI-PEDOT source-value sheets into Falsiflow evidence
and a generated project config:

```bash
python3 scripts/falsiflow.py ingest-limina-source-values \
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

Audit the migrated LIMINA evidence pack:

```bash
python3 scripts/falsiflow.py audit \
  --config configs/falsiflow/limina_nhi_pedot_habc/project.json \
  --evidence data/falsiflow/limina_nhi_pedot_habc/evidence_from_source_values.csv \
  --out-dir data/falsiflow/limina_nhi_pedot_habc/audit
```

Aggregate multiple audit outputs into a portfolio dashboard:

```bash
python3 scripts/falsiflow.py portfolio \
  --input data/falsiflow \
  --out-dir data/falsiflow/portfolio
```

When `--input` is omitted, `falsiflow portfolio` scans
`./data/falsiflow` in the current working directory. That keeps installed
package behavior tied to the user's project directory rather than the Python
installation path.

Write a standalone source-file provenance manifest:

```bash
python3 scripts/falsiflow.py sources \
  --config examples/falsiflow/neural_materials/project.json \
  --evidence examples/falsiflow/neural_materials/evidence_pass_demo.csv \
  --out data/falsiflow/neural_materials_pass/source_manifest.json \
  --report-out data/falsiflow/neural_materials_pass/source_manifest.md \
  --strict
```

The source manifest checks blank `source_file` cells, missing raw files, and
files outside `allowed_source_roots`. It is meant to travel with an audit report
when evidence is sent to a collaborator, reviewer, or lab partner.

Run the complete claim gate in one step:

```bash
python3 scripts/falsiflow.py claim-check \
  --project-dir examples/falsiflow/neural_materials \
  --out-dir data/falsiflow/neural_materials_pass/claim_check \
  --strict
```

`claim-check` writes `claim_check.json`, `claim_check.md`,
`evidence_bundle.zip`, `evidence_bundle_verify.json`, and
`evidence_bundle_verify.md`. The Markdown report is titled
`Falsiflow Claim Check`. Machine status is `claim_check_ready` only when audit,
source provenance, bundle generation, and bundle verification all pass; otherwise
it returns `claim_check_blocked` with a blocking stage and next actions. The
report includes a `Review Artifact Index` linking the audit review, source
manifest, bundle manifest, dashboard, bundle verification, and evidence bundle.
With `--project-dir`, default inputs are `project.json` and
`evidence_pass_demo.csv`, and default output is `PROJECT_DIR/claim_check`.

Build a portable evidence bundle:

```bash
python3 scripts/falsiflow.py bundle \
  --config examples/falsiflow/neural_materials/project.json \
  --evidence examples/falsiflow/neural_materials/evidence_pass_demo.csv \
  --out-dir data/falsiflow/neural_materials_pass/evidence_bundle \
  --zip-out data/falsiflow/neural_materials_pass/evidence_bundle.zip \
  --strict
```

The bundle directory contains `inputs/`, `audit/`, copied `sources/`,
`source_manifest.*`, and `bundle_manifest.json` with SHA-256 checksums. It is
the handoff artifact for reviewers who need to inspect both decision outputs and
the raw files behind them.

Verify a received bundle before trusting or forwarding it:

```bash
python3 scripts/falsiflow.py verify-bundle \
  --zip data/falsiflow/neural_materials_pass/evidence_bundle.zip \
  --out data/falsiflow/neural_materials_pass/evidence_bundle_verify.json \
  --report-out data/falsiflow/neural_materials_pass/evidence_bundle_verify.md \
  --strict
```

Verification checks required artifact roles, relative paths, byte sizes,
SHA-256 hashes, duplicate paths, missing files, copied source records, and
unmanifested files. With `--strict`, a bundle only exits zero when its integrity
is verified and its manifest status is `bundle_ready`. The Markdown verification
report includes a `Review Artifact Index` pointing to the bundle manifest, audit
review, source manifest, dashboard, and integrity issue table. Use `--bundle-dir`
when the evidence bundle has already been extracted.

Convert a generic wide lab CSV into Falsiflow evidence:

```bash
python3 scripts/falsiflow.py ingest-wide-csv \
  --input path/to/lab_export.csv \
  --out data/falsiflow/my_run/evidence.csv \
  --config data/falsiflow/custom_screen_project/project.json \
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

New workflows can use the namespaced public interface:

```bash
python3 scripts/falsiflow.py evidence import \
  --profile generic-wide \
  --input path/to/lab_export.csv \
  --out data/falsiflow/my_run/evidence.csv \
  --gate-id h_a_medium_stability \
  --candidate-id my_candidate \
  --sample-id-column sample_id \
  --field ph_initial \
  --field ph_final
```

When `--config` is present, the import writes a coverage precheck that compares
the generated evidence keys against the configured required rows. `--strict`
turns missing required rows or duplicate configured rows into a non-zero exit,
so field/sample mapping mistakes can be caught before full audit.

Built-in adapter profiles cover common shapes:

```bash
python3 scripts/falsiflow.py evidence import \
  --profile vendor-measurement \
  --input vendor_return.csv \
  --out data/falsiflow/vendor_return/evidence.csv \
  --summary-out data/falsiflow/vendor_return/import_summary.json \
  --gate-id vendor_return_gate \
  --candidate-id fallback_candidate
```

The import summary records `adapter_profile` and `adapter_settings`. Profile
details live in [falsiflow_adapter_profiles.md](falsiflow_adapter_profiles.md).

## Neural-Materials Template

The first template models the earlier ALG-LAM-PEDOT low-dose neural hydrogel
question as three gates:

- `h_a_medium_stability`: cell-free medium stability before any cell claim.
- `h_b_electrical_interface`: impedance, charge-storage, and noise benefit.
- `h_c_network_response`: viability and basic network response not worse than
  control.

The example is intentionally narrow. It demonstrates the contract Falsiflow
enforces: no source file, blank metadata, placeholder value, missing row, or
failed acceptance rule can become a ready claim.

The example now uses raw fields rather than precomputed success metrics:

- H-A computes `ph_drift_24h_abs`, `osmolality_drift_24h_mosm`, and
  `conductivity_drift_24h_pct` from initial/final values.
- H-B computes `impedance_reduction_1khz_pct`, `charge_storage_gain_pct`, and
  `noise_increase_uvrms` from control/candidate values.
- H-C computes `burst_rate_ratio_vs_control` and
  `inflammation_marker_ratio_vs_control` by referencing a matched control
  sample.

## LIMINA Adapter

The `ingest-limina-source-values` command converts existing LIMINA long-form
source-value sheets into Falsiflow evidence rows. It maps:

- `H-A` rows to `h_a_medium_stability`;
- `H-B` rows to `h_b_electrical_interface`;
- `H-C` rows to `h_c_network_response`;
- `run_id` to `sample_id`;
- `target_field` to `field`;
- source provenance columns to Falsiflow metadata.

For H-A source-value rows that use `sample_event`, Falsiflow preserves the
event in the field id, for example `final.pH` or
`physical_inspection.visible_shedding`.

The generated config in `configs/falsiflow/limina_nhi_pedot_habc/project.json`
is a provenance-completeness audit, not a material suitability claim. It is
intended to prove that real values, measured timestamps, operators, and raw
source files exist before the stronger scientific acceptance rules are applied.
The generated LIMINA config also receives a small NHI-PEDOT scientific-rule
overlay when the needed fields are present: H-A drift limits, H-B lead
electrical-benefit rules with candidate filters, and H-C lead health rules.

The `ingest-wide-csv` command is the generic adapter for common lab exports:
one row per sample, metadata columns such as `sample_id`/`measured_at`, and one
or more measurement columns. It writes standard Falsiflow evidence rows, so the
same audit engine can process vendor exports, instrument summaries, or small
bench spreadsheets. Adapter profiles add named mappings for `generic-wide`,
`vendor-measurement`, `instrument-export`, and `plate-reader`.

## Current Schema

Project JSON:

- `project`: identity and version metadata.
- `claim`: claim id, statement, and required gate ids.
- `evidence_policy`: placeholder markers, required metadata fields, and allowed
  raw source roots.
- `evidence_policy.source_file_base_dir`: optional base directory for resolving
  source-file paths when config files live outside the repository root.
- `gates`: sample definitions, required fields, optional derived fields, and
  acceptance rules.
- `gates[].derived_fields`: fixed operations such as `abs_delta`,
  `abs_pct_change`, `reduction_pct`, `gain_pct`, `subtract`, `ratio`,
  `any_true`, `all_false`, or `copy`.
- Derived-field inputs can be same-sample field names or cross-sample reference
  objects such as `{"candidate_id": "control", "sample_id": "c1", "field":
  "burst_rate_hz"}`.
- `gates[].acceptance_rules`: operator checks over raw or derived fields.
  Rules can be limited with `candidate_id`, `candidate_ids`,
  `candidate_id_contains`, `sample_id`, `sample_ids`, or
  `sample_id_contains`.

Validation contract:

- each gate id must be unique;
- each configured sample key, `candidate_id/sample_id`, must be unique within a
  gate;
- required fields must be non-blank and unique within a gate;
- derived field ids must be unique and cannot overwrite required evidence
  fields;
- same-sample derived inputs must refer to required fields or earlier derived
  fields;
- cross-sample derived inputs must match exactly one configured sample and
  reference an available field;
- acceptance rules must target a required field or derived field and use a
  supported operator.

Evidence CSV:

- `gate_id`
- `candidate_id`
- `sample_id`
- `field`
- `value`
- `source_file`
- `measured_at`
- `operator_or_agent`
- `instrument_id`
- `notes`

Evidence CSV validation:

- `gate_id`, `candidate_id`, `sample_id`, `field`, and `value` are required
  columns;
- `source_file`, `measured_at`, `operator_or_agent`, `instrument_id`, and
  `notes` are standard columns and missing ones are reported as warnings;
- duplicate column names are errors because Python CSV parsing would otherwise
  lose one value;
- rows with more values than header columns are warnings and extra values are
  ignored;
- blank `gate_id`/`candidate_id`/`sample_id`/`field` key components are
  warnings because those rows cannot match configured evidence.

Audit artifacts:

- `claim_check.json`
- `claim_check.md`
- `claim_audit.json`
- `claim_audit.md`
- `audit_review.json`
- `audit_review.md`
- `claim_summary.json`
- `dashboard.html`
- `next_actions.json`

Project validation diagnostics are part of every audit. A project config with
level `error` diagnostics cannot produce a ready claim. Validation warnings are
reported for human review but do not block readiness by themselves.

Evidence diagnostics are part of every audit. A duplicate configured
`gate_id/candidate_id/sample_id/field` key is an error and blocks the claim;
replicates must use distinct `sample_id` values. Evidence rows that do not
match any configured required gate/sample/field are warnings and are ignored by
the claim decision. Header and row-format issues from the evidence CSV are
included in the same diagnostics. Any diagnostic with level `error` blocks the
claim even if every gate's acceptance rules would otherwise pass; warnings are
visible but do not block readiness by themselves. This keeps extra imported lab
data visible without letting malformed or ambiguous rows silently overwrite each
other.

Portfolio artifacts:

- `portfolio_summary.json`
- `portfolio_summary.md`
- `portfolio_dashboard.html`

Machine-readable schemas:

- `project`: JSON Schema for project config files.
- `evidence-row`: JSON Schema for one long-form evidence CSV row after CSV
  parsing.
- `claim-summary`: JSON Schema for `claim_summary.json`.
- `audit-review`: JSON Schema for `audit_review.json` decision cards.
- `portfolio-summary`: JSON Schema for `portfolio_summary.json`.
- `import-coverage`: JSON Schema for `import_coverage.json` from
  project-aware ingest checks.
- `source-manifest`: JSON Schema for `source_manifest.json`.
- `bundle-manifest`: JSON Schema for `bundle_manifest.json`.
- `bundle-verification`: JSON Schema for bundle integrity reports.
- `claim-check`: JSON Schema for the one-command claim gate summary.
- `quickstart-summary`: JSON Schema for the first-run project creation and
  claim-gate summary, including `next_commands` for the doctor handoff.
- `doctor-summary`: JSON Schema for project-health diagnosis reports, including
  `repair_checklist` repair/review commands, expected artifacts, and success
  signals.
- `demo-summary`: JSON Schema for `demo_summary.json`.
- `template-check`: JSON Schema for template authoring check reports.
- `template-pack-manifest`: JSON Schema for publishable template pack manifests.
- `template-pack-verification`: JSON Schema for template pack integrity reports.
- `template-install`: JSON Schema for verified template installation summaries.
- `template-registry`: JSON Schema for verified template source registries.
- `template-lock`: JSON Schema for pinned template source lockfiles.
- `template-attestation`: JSON Schema for lockfile/registry provenance attestations.
- `template-attestation-verification`: JSON Schema for attestation verification reports.
- `template-policy`: JSON Schema for template adoption allowlists.
- `template-policy-verification`: JSON Schema for template policy verification reports.
- `template-release`: JSON Schema for bundled template release manifests.
- `template-release-verification`: JSON Schema for template release verification reports.
  Reports include counters for missing artifacts, byte/hash mismatches, unsafe
  paths, duplicate paths, unmanifested files, and zip extraction issues.
- `template-gallery`: JSON Schema for the starter template gallery summary.
- `casebook-check`: JSON Schema for public casebook proof reports, including
  positive demos, placeholder blockers, source provenance, and bundle
  verification counters.
- `adoption-check`: JSON Schema for the five-priority adoption readiness gate,
  including `repair_checklist` commands, expected artifacts, and success
  signals, plus `release_validation_status` so fast `--skip-dist` runs are not
  confused with full distribution validation.
- `release-check`: JSON Schema for pre-release quality gate reports, including
  a top-level `release_validation_status` so fast `--skip-dist` runs are not
  confused with full distribution validation.

CI:

- `.github/workflows/falsiflow.yml` compiles the Falsiflow package, runs the
  regression script, emits schemas, runs `falsiflow selftest`, validates all
  starter templates, runs `falsiflow demo`, runs `falsiflow quickstart`, runs
  `falsiflow doctor`, runs `falsiflow template-gallery`, runs
  `falsiflow casebook-check`, runs `falsiflow adoption-check`, runs
  `falsiflow template-check`, runs
  `falsiflow claim-check`, verifies all passing demo audits, checks
  source manifests, verifies evidence bundle zip archives, smoke-tests
  `falsiflow template-scaffold`, runs
  `falsiflow template-pack`, verifies template pack zips, builds template
  registries, writes template lockfiles, creates and verifies template
  attestations, creates and verifies template policies, creates and verifies
  template release bundles, installs from releases, runs
  `falsiflow release-check`, and builds a strict portfolio dashboard. The
  regression script also performs a temporary package install and confirms that
  installed packaged templates can be self-tested, listed, initialized,
  audited, source-checked, bundled, and aggregated from an unrelated working
  directory.
- `.github/workflows/falsiflow-pages.yml` builds `falsiflow demo-package`,
  uploads the static demo directory with `actions/upload-pages-artifact`, and
  deploys it with `actions/deploy-pages` when GitHub Pages is enabled.
- `.github/workflows/falsiflow-cross-platform.yml` runs Linux, macOS, and
  Windows smoke tests covering `scripts/install_local.sh`,
  `scripts/install_local.ps1`, `pipx`, `start --check`, `demo-package`, and
  `external-check`.
- `.github/workflows/falsiflow-external-evidence.yml` verifies the hosted demo
  URL, runs pipx and Windows PowerShell smoke tests, writes
  `falsiflow_external_evidence.json`, runs `external-check --strict`, and
  uploads the evidence/readiness artifact for public release review.
- `.github/workflows/falsiflow-scorecard.yml` runs OpenSSF Scorecard, writes a
  SARIF report, uploads it with `github/codeql-action/upload-sarif`, and
  publishes repository security signals for public trust review.
- `.github/workflows/falsiflow-publish.yml` builds wheel/sdist distributions,
  runs `twine check`, uploads the dist artifact, and can publish to PyPI through
  trusted publishing when a GitHub release is published.
- `.github/dependabot.yml` schedules weekly Dependabot updates for GitHub
  Actions and Python packaging inputs.
- `release-check` also verifies release surface files and metadata:
  `pyproject.toml`, PyPI package metadata (`requires-python`, keywords,
  classifiers, and project URLs), `README.md`, `LICENSE`, `CHANGELOG.md`,
  `CONTRIBUTING.md`, `RELEASE.md`, `SECURITY.md`, `RESPONSIBLE_USE.md`,
  `CITATION.cff`, `GOVERNANCE.md`, `docs/falsiflow_architecture.md`,
  `docs/falsiflow_data_contract.md`,
  `docs/falsiflow_adapter_profiles.md`,
  `docs/falsiflow_casebook_check.md`,
  `docs/falsiflow_security_posture.md`,
  `docs/falsiflow_template_authoring.md`,
  `docs/falsiflow_troubleshooting.md`, `MANIFEST.in`,
  `.github/dependabot.yml`, `.github/workflows/falsiflow-scorecard.yml`,
  version consistency, contributor and release instructions,
  responsible-use boundaries, security reporting guidance, console script entry
  points, package template data, starter template files, the end-to-end
  walkthrough, external template authoring docs, starter template generation docs, one-command quickstart docs,
  one-command doctor docs, one-command claim gate docs, trusted audit review docs,
  template gallery docs, `template-check` results for packaged templates,
  template pack verification
  reports, template registry
  reports, lockfiles, attestation reports, policy reports, template release
  bundles, template release verification reports, bundle zip verification
  reports, priority-readiness adoption docs, `adoption_check.json`,
  `adoption_check.md`, generated wheel and sdist artifacts, an isolated wheel
  install, and the generated portfolio.

## Next Iterations

1. Add specialized import adapters for common vendor/instrument report formats
   while keeping raw source files as the audit anchor.
2. Add richer filtering and sorting to the portfolio dashboard.
3. Publish the package and add user-facing examples beyond the repository.
