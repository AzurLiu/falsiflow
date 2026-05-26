# Falsiflow CLI Reference

This reference is generated from the active `argparse` command tree.

- Status: `cli_reference_ready`
- Commands: 56

Regenerate it with:

```bash
falsiflow cli-reference --out docs/falsiflow_cli_reference.md
```

## Command Families

- Core audit and bundle operations: `falsiflow demo`, `falsiflow validate`, `falsiflow portfolio`, `falsiflow render`, `falsiflow audit`, `falsiflow claim-check`, `falsiflow bundle`, `falsiflow verify-bundle`, `falsiflow next`, `falsiflow sources`
- Discovery and evidence import: `falsiflow discover`, `falsiflow agent`, `falsiflow agent discover`, `falsiflow candidate`, `falsiflow candidate rank`, `falsiflow assay-plan`, `falsiflow evidence`, `falsiflow evidence import`, `falsiflow ingest-limina-source-values`, `falsiflow ingest-wide-csv`
- First-run and browser workflows: `falsiflow start`, `falsiflow onboard`, `falsiflow try`, `falsiflow wizard`, `falsiflow serve`, `falsiflow quickstart`, `falsiflow doctor`
- Project setup: `falsiflow init`, `falsiflow scaffold`
- Release and public adoption: `falsiflow static-demo`, `falsiflow demo-package`, `falsiflow publish-kit`, `falsiflow launch-kit`, `falsiflow external-evidence`, `falsiflow external-check`, `falsiflow casebook-check`, `falsiflow cli-reference`, `falsiflow schema`, `falsiflow selftest`, `falsiflow adoption-check`, `falsiflow release-check`
- Template supply chain: `falsiflow template-scaffold`, `falsiflow templates`, `falsiflow template-gallery`, `falsiflow template-check`, `falsiflow template-pack`, `falsiflow verify-template-pack`, `falsiflow template-registry`, `falsiflow template-lock`, `falsiflow template-attest`, `falsiflow verify-template-attestation`, `falsiflow template-policy`, `falsiflow verify-template-policy`, `falsiflow template-release`, `falsiflow verify-template-release`, `falsiflow template-install`

## Command Index

| Command | Summary |
| --- | --- |
| `falsiflow init` | Copy a starter Falsiflow template. |
| `falsiflow start` | Open the beginner-friendly local Falsiflow app. |
| `falsiflow onboard` | Run the beginner onboarding check and write next-step guidance. |
| `falsiflow static-demo` | Export a hostable static demo site for zero-install visitors. |
| `falsiflow demo-package` | Prepare a GitHub Pages/Netlify-ready static demo package. |
| `falsiflow publish-kit` | Generate a local handoff kit for GitHub Pages, external readiness, and PyPI release steps. |
| `falsiflow launch-kit` | Generate public launch copy, demo script, proof card, and maintainer checklist. |
| `falsiflow external-evidence` | Write a structured JSON template for hosted demo, PyPI, pipx, and Windows validation evidence. |
| `falsiflow external-check` | Check public release dependencies such as hosted demo URL, repo URL, PyPI package URL, pipx, and Windows validation. |
| `falsiflow discover` | Generate a structured, non-AI discovery candidate queue and project draft. |
| `falsiflow agent` | Optional agent interfaces that still emit auditable Falsiflow artifacts. |
| `falsiflow agent discover` | Generate a structured discovery package through the agent-facing interface. |
| `falsiflow candidate` | Candidate queue utilities. |
| `falsiflow candidate rank` | Rank candidate recipes for a research goal and write ranking artifacts. |
| `falsiflow assay-plan` | Draft assay and RFQ packages for the top candidate from a research goal. |
| `falsiflow evidence` | Evidence import utilities. |
| `falsiflow evidence import` | Convert a wide lab CSV into Falsiflow evidence rows. |
| `falsiflow try` | Run a 30-second starter demo and write a local browser launchpad. |
| `falsiflow wizard` | Write a static browser wizard for drafting a claim gate. |
| `falsiflow serve` | Generate and serve the local Falsiflow browser demo on localhost. |
| `falsiflow quickstart` | Create a starter project and immediately run the one-command claim gate. |
| `falsiflow doctor` | Diagnose a project directory and run the complete claim gate with actionable next steps. |
| `falsiflow scaffold` | Create a custom Falsiflow project from gates and fields. |
| `falsiflow template-scaffold` | Create a reusable starter template with pass and placeholder demos. |
| `falsiflow templates` | List available starter templates. |
| `falsiflow template-gallery` | Write a Markdown and JSON gallery of starter template use cases. |
| `falsiflow casebook-check` | Verify public casebook starter proofs and blocked-path demos. |
| `falsiflow cli-reference` | Generate the Markdown and JSON command reference from argparse. |
| `falsiflow schema` | Print machine-readable Falsiflow JSON Schemas. |
| `falsiflow selftest` | Verify packaged schemas, templates, demo audits, and portfolio output. |
| `falsiflow demo` | Run the end-to-end starter walkthrough and produce a verified bundle. |
| `falsiflow template-check` | Validate an external or bundled starter template end to end. |
| `falsiflow template-pack` | Package a checked starter template into a verifiable zip artifact. |
| `falsiflow verify-template-pack` | Verify a template pack directory or zip archive against its manifest and hashes. |
| `falsiflow template-registry` | Build a verified local registry from one or more template-pack zip archives. |
| `falsiflow template-lock` | Lock a template registry entry to an exact source zip hash. |
| `falsiflow template-attest` | Create a provenance attestation for a template registry or lockfile. |
| `falsiflow verify-template-attestation` | Verify a template provenance attestation against its subject and optional HMAC key. |
| `falsiflow template-policy` | Create a reusable trust policy from a verified template lock attestation. |
| `falsiflow verify-template-policy` | Verify a template trust policy against a lock and attestation. |
| `falsiflow template-release` | Package a verified template pack, lock, attestation, and policy into one release zip. |
| `falsiflow verify-template-release` | Verify a template release zip before installation. |
| `falsiflow template-install` | Verify and install a template-pack zip into a reusable template root. |
| `falsiflow adoption-check` | Audit the five adoption priorities as a machine-readable readiness gate. |
| `falsiflow release-check` | Run the full pre-release gate: schemas, templates, bundles, zip verification, and portfolio. |
| `falsiflow validate` | Validate a Falsiflow project config. |
| `falsiflow portfolio` | Aggregate claim_summary.json files into a portfolio dashboard. |
| `falsiflow render` | Render measurement templates and an audit report. |
| `falsiflow audit` | Audit evidence against configured gates. |
| `falsiflow claim-check` | Run audit, source provenance, evidence bundle, and zip verification in one command. |
| `falsiflow bundle` | Build a portable evidence bundle with audit artifacts, sources, and hashes. |
| `falsiflow verify-bundle` | Verify a bundle directory or zip archive against its manifest and hashes. |
| `falsiflow next` | Print the next evidence-filling actions. |
| `falsiflow sources` | Write a source-file provenance manifest for evidence rows. |
| `falsiflow ingest-limina-source-values` | Convert LIMINA source-value sheets into Falsiflow evidence. |
| `falsiflow ingest-wide-csv` | Convert a wide lab CSV into Falsiflow evidence rows. |

## Commands

### `falsiflow init`

Copy a starter Falsiflow template.

```text
falsiflow init [-h] [--template TEMPLATE]
                      [--template-root TEMPLATE_ROOT] --out OUT
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template` | `TEMPLATE` | `no` | `neural_materials` |  |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to search before bundled templates. Repeatable. |
| `--out` | `OUT` | `yes` | `` |  |

### `falsiflow start`

Open the beginner-friendly local Falsiflow app.

```text
falsiflow start [-h] [--template TEMPLATE]
                       [--template-root TEMPLATE_ROOT] [--out-dir OUT_DIR]
                       [--host HOST] [--port PORT] [--reset] [--no-open]
                       [--check] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template` | `TEMPLATE` | `no` | `biointerface_coatings` | Starter example to show. Defaults to biointerface_coatings. |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to search before bundled templates. Repeatable. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_start` | Directory for the local app files. |
| `--host` | `HOST` | `no` | `127.0.0.1` | Host interface for the local server. |
| `--port` | `PORT` | `no` | `0` | Port for the local app. Defaults to a free port. |
| `--reset` | `` | `no` | `False` | Regenerate the local app output directory before opening it. |
| `--no-open` | `` | `no` | `False` | Do not open the browser automatically. |
| `--check` | `` | `no` | `False` | Start the server, fetch index.html once, write serve_summary.json, and exit. |
| `--json` | `` | `no` | `False` | Print machine-readable local app summary. |

### `falsiflow onboard`

Run the beginner onboarding check and write next-step guidance.

```text
falsiflow onboard [-h] [--template TEMPLATE]
                         [--template-root TEMPLATE_ROOT] [--out-dir OUT_DIR]
                         [--host HOST] [--port PORT] [--reset] [--no-open]
                         [--check] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template` | `TEMPLATE` | `no` | `biointerface_coatings` | Starter example to show. Defaults to biointerface_coatings. |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to search before bundled templates. Repeatable. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_onboard` | Directory for onboarding files. |
| `--host` | `HOST` | `no` | `127.0.0.1` | Host interface for the local check server. |
| `--port` | `PORT` | `no` | `0` | Port for the local check server. Defaults to a free port. |
| `--reset` | `` | `no` | `False` | Regenerate the onboarding output directory before checking it. |
| `--no-open` | `` | `no` | `False` | Do not open the browser after onboarding. |
| `--check` | `` | `no` | `False` | Run the onboarding HTTP check and exit. |
| `--json` | `` | `no` | `False` | Print machine-readable onboarding summary. |

### `falsiflow static-demo`

Export a hostable static demo site for zero-install visitors.

```text
falsiflow static-demo [-h] [--template TEMPLATE]
                             [--template-root TEMPLATE_ROOT]
                             [--out-dir OUT_DIR] [--force] [--open] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template` | `TEMPLATE` | `no` | `biointerface_coatings` | Starter template to export. Defaults to biointerface_coatings. |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to search before bundled templates. Repeatable. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_static_demo` | Directory for static demo files. |
| `--force` | `` | `no` | `False` | Allow replacing an existing static demo directory. |
| `--open` | `` | `no` | `False` | Open the exported index.html in the default browser. |
| `--json` | `` | `no` | `False` | Print machine-readable static demo summary. |

### `falsiflow demo-package`

Prepare a GitHub Pages/Netlify-ready static demo package.

```text
falsiflow demo-package [-h] [--template TEMPLATE]
                              [--template-root TEMPLATE_ROOT]
                              [--out-dir OUT_DIR] [--force] [--open] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template` | `TEMPLATE` | `no` | `biointerface_coatings` | Starter template to export. Defaults to biointerface_coatings. |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to search before bundled templates. Repeatable. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_public_demo` | Directory for publishable demo files. |
| `--force` | `` | `no` | `False` | Allow replacing an existing demo package directory. |
| `--open` | `` | `no` | `False` | Open the exported index.html in the default browser. |
| `--json` | `` | `no` | `False` | Print machine-readable demo package summary. |

### `falsiflow publish-kit`

Generate a local handoff kit for GitHub Pages, external readiness, and PyPI release steps.

```text
falsiflow publish-kit [-h] [--template TEMPLATE]
                             [--template-root TEMPLATE_ROOT]
                             [--out-dir OUT_DIR] [--repo-slug REPO_SLUG]
                             [--public-demo-url PUBLIC_DEMO_URL] [--tag TAG]
                             [--force] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template` | `TEMPLATE` | `no` | `biointerface_coatings` | Starter template to export in the public demo package. |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to search before bundled templates. Repeatable. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_publish_kit` | Directory for publish handoff artifacts. |
| `--repo-slug` | `REPO_SLUG` | `no` | `` | Optional GitHub repo slug such as OWNER/falsiflow. |
| `--public-demo-url` | `PUBLIC_DEMO_URL` | `no` | `` | Optional hosted public demo URL. |
| `--tag` | `TAG` | `no` | `v0.1.1` | Release tag to include in generated GitHub commands. |
| `--force` | `` | `no` | `False` | Allow replacing an existing publish-kit directory. |
| `--json` | `` | `no` | `False` | Print machine-readable publish handoff summary. |

### `falsiflow launch-kit`

Generate public launch copy, demo script, proof card, and maintainer checklist.

```text
falsiflow launch-kit [-h] [--template TEMPLATE]
                            [--template-root TEMPLATE_ROOT]
                            [--out-dir OUT_DIR] [--repo-slug REPO_SLUG]
                            [--public-demo-url PUBLIC_DEMO_URL] [--tag TAG]
                            [--force] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template` | `TEMPLATE` | `no` | `biointerface_coatings` | Starter template to use in the nested public demo package. |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to search before bundled templates. Repeatable. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_launch_kit` | Directory for public launch materials. |
| `--repo-slug` | `REPO_SLUG` | `no` | `` | Optional GitHub repo slug such as OWNER/falsiflow. |
| `--public-demo-url` | `PUBLIC_DEMO_URL` | `no` | `` | Optional hosted public demo URL. |
| `--tag` | `TAG` | `no` | `v0.1.1` | Release tag to include in launch materials. |
| `--force` | `` | `no` | `False` | Allow replacing an existing launch-kit directory. |
| `--json` | `` | `no` | `False` | Print machine-readable launch kit summary. |

### `falsiflow external-evidence`

Write a structured JSON template for hosted demo, PyPI, pipx, and Windows validation evidence.

```text
falsiflow external-evidence [-h] [--out OUT] [--repo-url REPO_URL]
                                   [--public-demo-url PUBLIC_DEMO_URL]
                                   [--pypi-package-url PYPI_PACKAGE_URL]
                                   [--force] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--out` | `OUT` | `no` | `falsiflow_external_evidence.json` | Path for the external evidence JSON template. |
| `--repo-url` | `REPO_URL` | `no` | `` | Optional public repository URL to prefill. |
| `--public-demo-url` | `PUBLIC_DEMO_URL` | `no` | `` | Optional hosted public demo URL to prefill. |
| `--pypi-package-url` | `PYPI_PACKAGE_URL` | `no` | `` | Optional public PyPI project URL to prefill. |
| `--force` | `` | `no` | `False` | Allow replacing an existing external evidence file. |
| `--json` | `` | `no` | `False` | Print machine-readable external evidence summary. |

### `falsiflow external-check`

Check public release dependencies such as hosted demo URL, repo URL, PyPI package URL, pipx, and Windows validation.

```text
falsiflow external-check [-h] [--out-dir OUT_DIR] [--evidence EVIDENCE]
                                [--force] [--strict] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_external_check` | Directory for external readiness artifacts. |
| `--evidence` | `EVIDENCE` | `no` | `` | Optional structured external evidence JSON from `falsiflow external-evidence`. |
| `--force` | `` | `no` | `False` | Allow replacing an existing external-check directory. |
| `--strict` | `` | `no` | `False` | Exit non-zero unless every external readiness check passes. |
| `--json` | `` | `no` | `False` | Print machine-readable external readiness summary. |

### `falsiflow discover`

Generate a structured, non-AI discovery candidate queue and project draft.

```text
falsiflow discover [-h] --goal GOAL [--out-dir OUT_DIR] [--force]
                          [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--goal` | `GOAL` | `yes` | `` | Research goal to turn into evidence records, candidates, gates, and an assay plan. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_discovery` | Directory for discovery artifacts. |
| `--force` | `` | `no` | `False` | Allow replacing an existing discovery directory. |
| `--json` | `` | `no` | `False` | Print machine-readable discovery summary. |

### `falsiflow agent`

Optional agent interfaces that still emit auditable Falsiflow artifacts.

```text
falsiflow agent [-h] {discover} ...
```

Nested commands:
- `falsiflow agent discover`

No command-specific arguments.

### `falsiflow agent discover`

Generate a structured discovery package through the agent-facing interface.

```text
falsiflow agent discover [-h] --goal GOAL [--out-dir OUT_DIR] [--force]
                                [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--goal` | `GOAL` | `yes` | `` | Research goal to turn into evidence records, candidates, gates, and an assay plan. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_discovery` | Directory for discovery artifacts. |
| `--force` | `` | `no` | `False` | Allow replacing an existing discovery directory. |
| `--json` | `` | `no` | `False` | Print machine-readable discovery summary. |

### `falsiflow candidate`

Candidate queue utilities.

```text
falsiflow candidate [-h] {rank} ...
```

Nested commands:
- `falsiflow candidate rank`

No command-specific arguments.

### `falsiflow candidate rank`

Rank candidate recipes for a research goal and write ranking artifacts.

```text
falsiflow candidate rank [-h] --goal GOAL [--out-dir OUT_DIR] [--force]
                                [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--goal` | `GOAL` | `yes` | `` | Research goal to turn into evidence records, candidates, gates, and an assay plan. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_candidate_rank` | Directory for discovery artifacts. |
| `--force` | `` | `no` | `False` | Allow replacing an existing discovery directory. |
| `--json` | `` | `no` | `False` | Print machine-readable discovery summary. |

### `falsiflow assay-plan`

Draft assay and RFQ packages for the top candidate from a research goal.

```text
falsiflow assay-plan [-h] --goal GOAL [--out-dir OUT_DIR] [--force]
                            [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--goal` | `GOAL` | `yes` | `` | Research goal to turn into evidence records, candidates, gates, and an assay plan. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_assay_plan` | Directory for discovery artifacts. |
| `--force` | `` | `no` | `False` | Allow replacing an existing discovery directory. |
| `--json` | `` | `no` | `False` | Print machine-readable discovery summary. |

### `falsiflow evidence`

Evidence import utilities.

```text
falsiflow evidence [-h] {import} ...
```

Nested commands:
- `falsiflow evidence import`

No command-specific arguments.

### `falsiflow evidence import`

Convert a wide lab CSV into Falsiflow evidence rows.

```text
falsiflow evidence import [-h] --input INPUT --out OUT
                                 [--summary-out SUMMARY_OUT] [--config CONFIG]
                                 [--coverage-out COVERAGE_OUT] [--strict]
                                 [--profile {generic-wide,instrument-export,plate-reader,vendor-measurement}]
                                 --gate-id GATE_ID --candidate-id CANDIDATE_ID
                                 [--sample-id-column SAMPLE_ID_COLUMN]
                                 [--field FIELD]
                                 [--exclude-column EXCLUDE_COLUMN]
                                 [--gate-id-column GATE_ID_COLUMN]
                                 [--candidate-id-column CANDIDATE_ID_COLUMN]
                                 [--source-file SOURCE_FILE]
                                 [--source-file-column SOURCE_FILE_COLUMN]
                                 [--measured-at MEASURED_AT]
                                 [--measured-at-column MEASURED_AT_COLUMN]
                                 [--operator-or-agent OPERATOR_OR_AGENT]
                                 [--operator-or-agent-column OPERATOR_OR_AGENT_COLUMN]
                                 [--instrument-id INSTRUMENT_ID]
                                 [--instrument-id-column INSTRUMENT_ID_COLUMN]
                                 [--notes NOTES] [--notes-column NOTES_COLUMN]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--input` | `INPUT` | `yes` | `` | Wide lab CSV. Repeatable. |
| `--out` | `OUT` | `yes` | `` | Falsiflow evidence CSV to write. |
| `--summary-out` | `SUMMARY_OUT` | `no` | `` | Optional conversion summary JSON. |
| `--config` | `CONFIG` | `no` | `` | Optional project config for import coverage precheck. |
| `--coverage-out` | `COVERAGE_OUT` | `no` | `` | Optional coverage precheck JSON output path. |
| `--strict` | `` | `no` | `False` | Exit non-zero when project coverage is blocked. |
| `--profile` | `{generic-wide,instrument-export,plate-reader,vendor-measurement}` | `no` | `generic-wide` | Column mapping profile for common lab, vendor, or instrument CSV shapes. |
| `--gate-id` | `GATE_ID` | `yes` | `` |  |
| `--candidate-id` | `CANDIDATE_ID` | `yes` | `` |  |
| `--sample-id-column` | `SAMPLE_ID_COLUMN` | `no` | `` | Column containing sample ids. Defaults to the selected profile. |
| `--field` | `FIELD` | `no` | `[]` | Value column to import. Repeatable. Defaults to all non-metadata columns. |
| `--exclude-column` | `EXCLUDE_COLUMN` | `no` | `[]` | Column to ignore when auto-selecting value columns. |
| `--gate-id-column` | `GATE_ID_COLUMN` | `no` | `` |  |
| `--candidate-id-column` | `CANDIDATE_ID_COLUMN` | `no` | `` |  |
| `--source-file` | `SOURCE_FILE` | `no` | `` |  |
| `--source-file-column` | `SOURCE_FILE_COLUMN` | `no` | `` |  |
| `--measured-at` | `MEASURED_AT` | `no` | `` |  |
| `--measured-at-column` | `MEASURED_AT_COLUMN` | `no` | `` |  |
| `--operator-or-agent` | `OPERATOR_OR_AGENT` | `no` | `` |  |
| `--operator-or-agent-column` | `OPERATOR_OR_AGENT_COLUMN` | `no` | `` |  |
| `--instrument-id` | `INSTRUMENT_ID` | `no` | `` |  |
| `--instrument-id-column` | `INSTRUMENT_ID_COLUMN` | `no` | `` |  |
| `--notes` | `NOTES` | `no` | `` |  |
| `--notes-column` | `NOTES_COLUMN` | `no` | `` |  |

### `falsiflow try`

Run a 30-second starter demo and write a local browser launchpad.

```text
falsiflow try [-h] [--template TEMPLATE]
                     [--template-root TEMPLATE_ROOT] [--out-dir OUT_DIR]
                     [--force] [--open] [--strict] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template` | `TEMPLATE` | `no` | `biointerface_coatings` | Starter template to run. Defaults to biointerface_coatings. |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to search before bundled templates. Repeatable. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_try` | Directory for the demo project, JSON, launchpad, and HTML report. |
| `--force` | `` | `no` | `False` | Allow replacing an existing try output directory. |
| `--open` | `` | `no` | `False` | Open the local launchpad in the default browser after writing it. |
| `--strict` | `` | `no` | `False` | Exit non-zero unless the starter claim is ready. |
| `--json` | `` | `no` | `False` | Print machine-readable try summary. |

### `falsiflow wizard`

Write a static browser wizard for drafting a claim gate.

```text
falsiflow wizard [-h] [--out OUT] [--force] [--open] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--out` | `OUT` | `no` | `falsiflow_wizard.html` | HTML wizard file to write. |
| `--force` | `` | `no` | `False` | Allow replacing an existing wizard HTML file. |
| `--open` | `` | `no` | `False` | Open the wizard in the default browser after writing it. |
| `--json` | `` | `no` | `False` | Print machine-readable wizard summary. |

### `falsiflow serve`

Generate and serve the local Falsiflow browser demo on localhost.

```text
falsiflow serve [-h] [--template TEMPLATE]
                       [--template-root TEMPLATE_ROOT] [--out-dir OUT_DIR]
                       [--host HOST] [--port PORT] [--force] [--open]
                       [--check] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template` | `TEMPLATE` | `no` | `biointerface_coatings` | Starter template to run when generating the demo. |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to search before bundled templates. Repeatable. |
| `--out-dir` | `OUT_DIR` | `no` | `falsiflow_try` | Directory containing or receiving index.html and try_report.html. |
| `--host` | `HOST` | `no` | `127.0.0.1` | Host interface for the local server. |
| `--port` | `PORT` | `no` | `8765` | Port for the local server. Use 0 to choose a free port. |
| `--force` | `` | `no` | `False` | Regenerate the try output directory before serving. |
| `--open` | `` | `no` | `False` | Open the local demo URL in the default browser. |
| `--check` | `` | `no` | `False` | Start the server, fetch index.html once, write serve_summary.json, and exit. |
| `--json` | `` | `no` | `False` | Print machine-readable serve summary. |

### `falsiflow quickstart`

Create a starter project and immediately run the one-command claim gate.

```text
falsiflow quickstart [-h] [--template TEMPLATE]
                            [--template-root TEMPLATE_ROOT] --out OUT
                            [--force] [--strict] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template` | `TEMPLATE` | `no` | `neural_materials` |  |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to search before bundled templates. Repeatable. |
| `--out` | `OUT` | `yes` | `` | Project directory to create. |
| `--force` | `` | `no` | `False` | Allow replacing an existing quickstart project directory. |
| `--strict` | `` | `no` | `False` | Exit non-zero unless the quickstart claim check is ready. |
| `--json` | `` | `no` | `False` | Print machine-readable quickstart summary. |

### `falsiflow doctor`

Diagnose a project directory and run the complete claim gate with actionable next steps.

```text
falsiflow doctor [-h] [--project-dir PROJECT_DIR] [--config CONFIG]
                        [--evidence EVIDENCE] [--out-dir OUT_DIR] [--force]
                        [--strict] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--project-dir` | `PROJECT_DIR` | `no` | `` | Project directory containing project.json and an evidence CSV; defaults --out-dir to PROJECT_DIR/doctor. |
| `--config` | `CONFIG` | `no` | `` | Project config JSON path. Defaults to PROJECT_DIR/project.json when --project-dir is used. |
| `--evidence` | `EVIDENCE` | `no` | `` | Evidence CSV path. Defaults to PROJECT_DIR/evidence_pass_demo.csv, evidence.csv, or evidence_template.csv when --project-dir is used. |
| `--out-dir` | `OUT_DIR` | `no` | `` | Output directory. Defaults to PROJECT_DIR/doctor when --project-dir is used. |
| `--force` | `` | `no` | `False` | Allow writing into a non-empty doctor output directory. |
| `--strict` | `` | `no` | `False` | Exit non-zero unless the doctor summary is ready. |
| `--json` | `` | `no` | `False` | Print machine-readable doctor summary. |

### `falsiflow scaffold`

Create a custom Falsiflow project from gates and fields.

```text
falsiflow scaffold [-h] --out OUT --project-id PROJECT_ID
                          [--project-name PROJECT_NAME] [--domain DOMAIN]
                          --claim-id CLAIM_ID
                          --claim-statement CLAIM_STATEMENT --gate GATE
                          [--gate-title GATE_TITLE] [--sample SAMPLE]
                          [--rule RULE] [--candidate-id CANDIDATE_ID]
                          [--sample-id SAMPLE_ID] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--out` | `OUT` | `yes` | `` | Directory to create. |
| `--project-id` | `PROJECT_ID` | `yes` | `` |  |
| `--project-name` | `PROJECT_NAME` | `no` | `` |  |
| `--domain` | `DOMAIN` | `no` | `custom-rd` |  |
| `--claim-id` | `CLAIM_ID` | `yes` | `` |  |
| `--claim-statement` | `CLAIM_STATEMENT` | `yes` | `` |  |
| `--gate` | `GATE` | `yes` | `` | Gate definition as `gate_id:field_a,field_b`. Repeatable. |
| `--gate-title` | `GATE_TITLE` | `no` | `[]` | Optional title as `gate_id=Human title`. Repeatable. |
| `--sample` | `SAMPLE` | `no` | `[]` | Sample as `candidate_id:sample_id` for all gates, or `gate_id:candidate_id:sample_id`. Repeatable. |
| `--rule` | `RULE` | `no` | `[]` | Acceptance rule as `gate_id:field:operator:value[:reason]`. Repeatable. |
| `--candidate-id` | `CANDIDATE_ID` | `no` | `candidate_a` | Default candidate_id when --sample is omitted. |
| `--sample-id` | `SAMPLE_ID` | `no` | `sample_001` | Default sample_id when --sample is omitted. |
| `--json` | `` | `no` | `False` | Print machine-readable scaffold summary. |

### `falsiflow template-scaffold`

Create a reusable starter template with pass and placeholder demos.

```text
falsiflow template-scaffold [-h] --out OUT --template-id TEMPLATE_ID
                                   [--template-name TEMPLATE_NAME]
                                   [--template-description TEMPLATE_DESCRIPTION]
                                   [--project-id PROJECT_ID]
                                   [--project-name PROJECT_NAME]
                                   [--domain DOMAIN] [--claim-id CLAIM_ID]
                                   --claim-statement CLAIM_STATEMENT
                                   --gate GATE [--gate-title GATE_TITLE]
                                   [--sample SAMPLE] [--rule RULE]
                                   [--candidate-id CANDIDATE_ID]
                                   [--sample-id SAMPLE_ID]
                                   [--check-out-dir CHECK_OUT_DIR] [--force]
                                   [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--out` | `OUT` | `yes` | `` | Template directory to create. |
| `--template-id` | `TEMPLATE_ID` | `yes` | `` |  |
| `--template-name` | `TEMPLATE_NAME` | `no` | `` |  |
| `--template-description` | `TEMPLATE_DESCRIPTION` | `no` | `` |  |
| `--project-id` | `PROJECT_ID` | `no` | `` |  |
| `--project-name` | `PROJECT_NAME` | `no` | `` |  |
| `--domain` | `DOMAIN` | `no` | `custom-rd` |  |
| `--claim-id` | `CLAIM_ID` | `no` | `` |  |
| `--claim-statement` | `CLAIM_STATEMENT` | `yes` | `` |  |
| `--gate` | `GATE` | `yes` | `` | Gate definition as `gate_id:field_a,field_b`. Repeatable. |
| `--gate-title` | `GATE_TITLE` | `no` | `[]` | Optional title as `gate_id=Human title`. Repeatable. |
| `--sample` | `SAMPLE` | `no` | `[]` | Sample as `candidate_id:sample_id` for all gates, or `gate_id:candidate_id:sample_id`. Repeatable. |
| `--rule` | `RULE` | `no` | `[]` | Acceptance rule as `gate_id:field:operator:value[:reason]`. Repeatable. |
| `--candidate-id` | `CANDIDATE_ID` | `no` | `candidate_a` | Default candidate_id when --sample is omitted. |
| `--sample-id` | `SAMPLE_ID` | `no` | `sample_001` | Default sample_id when --sample is omitted. |
| `--check-out-dir` | `CHECK_OUT_DIR` | `no` | `` | Optional directory for template-check artifacts. |
| `--force` | `` | `no` | `False` | Allow replacing a non-empty template or check output directory. |
| `--json` | `` | `no` | `False` | Print machine-readable template-scaffold summary. |

### `falsiflow templates`

List available starter templates.

```text
falsiflow templates [-h] [--template-root TEMPLATE_ROOT] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to list before bundled templates. Repeatable. |
| `--json` | `` | `no` | `False` | Print machine-readable template metadata. |

### `falsiflow template-gallery`

Write a Markdown and JSON gallery of starter template use cases.

```text
falsiflow template-gallery [-h] [--template-root TEMPLATE_ROOT]
                                  [--out OUT] [--json-out JSON_OUT] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to include before bundled templates. Repeatable. |
| `--out` | `OUT` | `no` | `` | Optional Markdown gallery output path. |
| `--json-out` | `JSON_OUT` | `no` | `` | Optional JSON gallery output path. |
| `--json` | `` | `no` | `False` | Print machine-readable template-gallery summary. |

### `falsiflow casebook-check`

Verify public casebook starter proofs and blocked-path demos.

```text
falsiflow casebook-check [-h] [--template-root TEMPLATE_ROOT]
                                --out-dir OUT_DIR [--json] [--force]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template-root` | `TEMPLATE_ROOT` | `no` | `[]` | Extra template root to include before bundled templates. Repeatable. |
| `--out-dir` | `OUT_DIR` | `yes` | `` | Directory for casebook-check artifacts and reports. |
| `--json` | `` | `no` | `False` | Print machine-readable casebook-check summary. |
| `--force` | `` | `no` | `False` | Allow writing into a non-empty casebook-check directory. |

### `falsiflow cli-reference`

Generate the Markdown and JSON command reference from argparse.

```text
falsiflow cli-reference [-h] [--out OUT] [--json-out JSON_OUT] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--out` | `OUT` | `no` | `` | Optional Markdown reference output path. |
| `--json-out` | `JSON_OUT` | `no` | `` | Optional JSON reference output path. |
| `--json` | `` | `no` | `False` | Print machine-readable CLI reference summary. |

### `falsiflow schema`

Print machine-readable Falsiflow JSON Schemas.

```text
falsiflow schema [-h]
                        [--kind {project,evidence-row,evidence-record,candidate-recipe,discovery-summary,claim-summary,audit-review,portfolio-summary,import-coverage,source-manifest,bundle-manifest,bundle-verification,claim-check,quickstart-summary,doctor-summary,demo-summary,template-check,template-pack-manifest,template-pack-verification,template-install,template-registry,template-lock,template-attestation,template-attestation-verification,template-policy,template-policy-verification,template-release,template-release-verification,template-gallery,casebook-check,external-evidence,external-readiness,adoption-check,release-check,all}]
                        [--out OUT]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--kind` | `{project,evidence-row,evidence-record,candidate-recipe,discovery-summary,claim-summary,audit-review,portfolio-summary,import-coverage,source-manifest,bundle-manifest,bundle-verification,claim-check,quickstart-summary,doctor-summary,demo-summary,template-check,template-pack-manifest,template-pack-verification,template-install,template-registry,template-lock,template-attestation,template-attestation-verification,template-policy,template-policy-verification,template-release,template-release-verification,template-gallery,casebook-check,external-evidence,external-readiness,adoption-check,release-check,all}` | `no` | `project` |  |
| `--out` | `OUT` | `no` | `` | Optional JSON output path. |

### `falsiflow selftest`

Verify packaged schemas, templates, demo audits, and portfolio output.

```text
falsiflow selftest [-h] [--out-dir OUT_DIR] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--out-dir` | `OUT_DIR` | `no` | `` | Optional directory for selftest artifacts. |
| `--json` | `` | `no` | `False` | Print machine-readable selftest results. |

### `falsiflow demo`

Run the end-to-end starter walkthrough and produce a verified bundle.

```text
falsiflow demo [-h] --out-dir OUT_DIR [--template TEMPLATE] [--json]
                      [--force]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--out-dir` | `OUT_DIR` | `yes` | `` | Directory for demo project and artifacts. |
| `--template` | `TEMPLATE` | `no` | `neural_materials` | Starter template to run. Defaults to neural_materials. |
| `--json` | `` | `no` | `False` | Print machine-readable demo summary. |
| `--force` | `` | `no` | `False` | Allow replacing a non-empty demo output directory. |

### `falsiflow template-check`

Validate an external or bundled starter template end to end.

```text
falsiflow template-check [-h] --template-dir TEMPLATE_DIR
                                --out-dir OUT_DIR [--json] [--force]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template-dir` | `TEMPLATE_DIR` | `yes` | `` | Directory containing template.json, project.json, evidence demos, and source_files/. |
| `--out-dir` | `OUT_DIR` | `yes` | `` | Directory for template-check artifacts and reports. |
| `--json` | `` | `no` | `False` | Print machine-readable template-check summary. |
| `--force` | `` | `no` | `False` | Allow writing into a non-empty template-check directory. |

### `falsiflow template-pack`

Package a checked starter template into a verifiable zip artifact.

```text
falsiflow template-pack [-h] --template-dir TEMPLATE_DIR
                               --out-dir OUT_DIR [--zip-out ZIP_OUT]
                               [--verify-out VERIFY_OUT]
                               [--report-out REPORT_OUT] [--force] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--template-dir` | `TEMPLATE_DIR` | `yes` | `` | Template directory to package. |
| `--out-dir` | `OUT_DIR` | `yes` | `` | Directory for the unpacked template pack. |
| `--zip-out` | `ZIP_OUT` | `no` | `` | Zip archive path. Defaults to OUT_DIR with .zip suffix. |
| `--verify-out` | `VERIFY_OUT` | `no` | `` | Optional JSON verification output path. Defaults next to the zip. |
| `--report-out` | `REPORT_OUT` | `no` | `` | Optional Markdown verification report output path. Defaults next to the zip. |
| `--force` | `` | `no` | `False` | Allow replacing a non-empty template pack directory. |
| `--json` | `` | `no` | `False` | Print machine-readable template-pack summary. |

### `falsiflow verify-template-pack`

Verify a template pack directory or zip archive against its manifest and hashes.

```text
falsiflow verify-template-pack [-h] (--pack-dir PACK_DIR |
                                      --zip ZIP_PATH) [--out OUT]
                                      [--report-out REPORT_OUT] [--strict]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--pack-dir` | `PACK_DIR` | `no` | `` | Template pack directory containing template_pack_manifest.json. |
| `--zip` | `ZIP_PATH` | `no` | `` | Template pack zip archive to verify without manual extraction. |
| `--out` | `OUT` | `no` | `` | Optional JSON verification report output path. |
| `--report-out` | `REPORT_OUT` | `no` | `` | Optional Markdown verification report output path. |
| `--strict` | `` | `no` | `False` | Exit non-zero unless the template pack is verified and ready. |

### `falsiflow template-registry`

Build a verified local registry from one or more template-pack zip archives.

```text
falsiflow template-registry [-h] --pack-zip PACK_ZIP --out OUT
                                   [--report-out REPORT_OUT]
                                   [--base-url BASE_URL] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--pack-zip` | `PACK_ZIP` | `yes` | `` | Template pack zip archive to index. Repeatable. |
| `--out` | `OUT` | `yes` | `` | JSON registry output path. |
| `--report-out` | `REPORT_OUT` | `no` | `` | Optional Markdown registry report output path. |
| `--base-url` | `BASE_URL` | `no` | `` | Optional public base URL for registry source_url entries. |
| `--json` | `` | `no` | `False` | Print machine-readable template-registry summary. |

### `falsiflow template-lock`

Lock a template registry entry to an exact source zip hash.

```text
falsiflow template-lock [-h] --registry REGISTRY --template TEMPLATE
                               [--version VERSION] --out OUT
                               [--cache-dir CACHE_DIR] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--registry` | `REGISTRY` | `yes` | `` | Template registry JSON path. |
| `--template` | `TEMPLATE` | `yes` | `` | Template id to lock. |
| `--version` | `VERSION` | `no` | `` | Optional exact template version to lock when a registry has multiple versions. |
| `--out` | `OUT` | `yes` | `` | Template lock JSON output path. |
| `--cache-dir` | `CACHE_DIR` | `no` | `` | Optional cache directory for verifying source_url entries. |
| `--json` | `` | `no` | `False` | Print machine-readable template-lock summary. |

### `falsiflow template-attest`

Create a provenance attestation for a template registry or lockfile.

```text
falsiflow template-attest [-h] --subject SUBJECT
                                 [--subject-type {template-registry,template-lock}]
                                 --out OUT [--builder BUILDER]
                                 [--key-id KEY_ID] [--signing-key SIGNING_KEY]
                                 [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--subject` | `SUBJECT` | `yes` | `` | Template registry or lock JSON file to attest. |
| `--subject-type` | `{template-registry,template-lock}` | `no` | `` | Optional subject type. Inferred from the subject when omitted. |
| `--out` | `OUT` | `yes` | `` | Template attestation JSON output path. |
| `--builder` | `BUILDER` | `no` | `` | Builder or CI identity to record in the attestation payload. |
| `--key-id` | `KEY_ID` | `no` | `` | Optional identifier for the signing key. |
| `--signing-key` | `SIGNING_KEY` | `no` | `` | Optional HMAC signing key. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY. |
| `--json` | `` | `no` | `False` | Print machine-readable template-attestation summary. |

### `falsiflow verify-template-attestation`

Verify a template provenance attestation against its subject and optional HMAC key.

```text
falsiflow verify-template-attestation [-h] --attestation ATTESTATION
                                             [--subject SUBJECT]
                                             [--signing-key SIGNING_KEY]
                                             [--out OUT] [--strict] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--attestation` | `ATTESTATION` | `yes` | `` | Template attestation JSON path. |
| `--subject` | `SUBJECT` | `no` | `` | Optional subject path override. |
| `--signing-key` | `SIGNING_KEY` | `no` | `` | Optional HMAC signing key. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY. |
| `--out` | `OUT` | `no` | `` | Optional JSON verification report output path. |
| `--strict` | `` | `no` | `False` | Exit non-zero unless the attestation signature is verified. |
| `--json` | `` | `no` | `False` | Print machine-readable template-attestation verification. |

### `falsiflow template-policy`

Create a reusable trust policy from a verified template lock attestation.

```text
falsiflow template-policy [-h] --lock LOCK --attestation ATTESTATION
                                 --out OUT [--policy-id POLICY_ID]
                                 [--owner OWNER] [--signing-key SIGNING_KEY]
                                 [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--lock` | `LOCK` | `yes` | `` | Template lock JSON path. |
| `--attestation` | `ATTESTATION` | `yes` | `` | Template-lock attestation JSON path. |
| `--out` | `OUT` | `yes` | `` | Template policy JSON output path. |
| `--policy-id` | `POLICY_ID` | `no` | `` | Optional stable policy id. Defaults to template_id@version. |
| `--owner` | `OWNER` | `no` | `` | Optional owner or team name recorded in the policy. |
| `--signing-key` | `SIGNING_KEY` | `no` | `` | HMAC signing key for verifying the attestation. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY. |
| `--json` | `` | `no` | `False` | Print machine-readable template-policy summary. |

### `falsiflow verify-template-policy`

Verify a template trust policy against a lock and attestation.

```text
falsiflow verify-template-policy [-h] --policy POLICY --lock LOCK
                                        --attestation ATTESTATION
                                        [--signing-key SIGNING_KEY]
                                        [--out OUT] [--strict] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--policy` | `POLICY` | `yes` | `` | Template policy JSON path. |
| `--lock` | `LOCK` | `yes` | `` | Template lock JSON path. |
| `--attestation` | `ATTESTATION` | `yes` | `` | Template-lock attestation JSON path. |
| `--signing-key` | `SIGNING_KEY` | `no` | `` | HMAC signing key for verifying the attestation. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY. |
| `--out` | `OUT` | `no` | `` | Optional JSON policy verification report output path. |
| `--strict` | `` | `no` | `False` | Exit non-zero unless the template policy is verified. |
| `--json` | `` | `no` | `False` | Print machine-readable template-policy verification. |

### `falsiflow template-release`

Package a verified template pack, lock, attestation, and policy into one release zip.

```text
falsiflow template-release [-h] --pack-zip PACK_ZIP --registry REGISTRY
                                  --lock LOCK --attestation ATTESTATION
                                  --policy POLICY --out OUT
                                  [--signing-key SIGNING_KEY] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--pack-zip` | `PACK_ZIP` | `yes` | `` | Verified template-pack zip archive. |
| `--registry` | `REGISTRY` | `yes` | `` | Template registry JSON path. |
| `--lock` | `LOCK` | `yes` | `` | Template lock JSON path. |
| `--attestation` | `ATTESTATION` | `yes` | `` | Template-lock attestation JSON path. |
| `--policy` | `POLICY` | `yes` | `` | Template adoption policy JSON path. |
| `--out` | `OUT` | `yes` | `` | Template release zip output path. |
| `--signing-key` | `SIGNING_KEY` | `no` | `` | HMAC signing key for verifying the attestation and policy before packaging. |
| `--json` | `` | `no` | `False` | Print machine-readable template-release summary. |

### `falsiflow verify-template-release`

Verify a template release zip before installation.

```text
falsiflow verify-template-release [-h] --release RELEASE
                                         [--signing-key SIGNING_KEY]
                                         [--out OUT] [--report-out REPORT_OUT]
                                         [--strict] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--release` | `RELEASE` | `yes` | `` | Template release zip path. |
| `--signing-key` | `SIGNING_KEY` | `no` | `` | HMAC signing key for verifying the release attestation and policy. |
| `--out` | `OUT` | `no` | `` | Optional JSON release verification report output path. |
| `--report-out` | `REPORT_OUT` | `no` | `` | Optional Markdown release verification report output path. |
| `--strict` | `` | `no` | `False` | Exit non-zero unless the template release is verified. |
| `--json` | `` | `no` | `False` | Print machine-readable template-release verification. |

### `falsiflow template-install`

Verify and install a template-pack zip into a reusable template root.

```text
falsiflow template-install [-h] (--zip ZIP_PATH | --lock LOCK_PATH |
                                  --release RELEASE_PATH)
                                  --templates-dir TEMPLATES_DIR
                                  [--check-out-dir CHECK_OUT_DIR]
                                  [--cache-dir CACHE_DIR]
                                  [--attestation ATTESTATION_PATH]
                                  [--signing-key SIGNING_KEY]
                                  [--policy POLICY_PATH]
                                  [--require-attestation] [--force] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--zip` | `ZIP_PATH` | `no` | `` | Template pack zip archive to verify and install. |
| `--lock` | `LOCK_PATH` | `no` | `` | Template lock JSON file to verify before installing. |
| `--release` | `RELEASE_PATH` | `no` | `` | Template release zip to verify and install. |
| `--templates-dir` | `TEMPLATES_DIR` | `yes` | `` | Template root where the verified template directory will be installed. |
| `--check-out-dir` | `CHECK_OUT_DIR` | `no` | `` | Optional directory for installed-template check artifacts. |
| `--cache-dir` | `CACHE_DIR` | `no` | `` | Optional cache directory for lockfile source_url downloads. |
| `--attestation` | `ATTESTATION_PATH` | `no` | `` | Optional template-lock attestation to verify before installing from --lock. |
| `--signing-key` | `SIGNING_KEY` | `no` | `` | Optional HMAC signing key for --attestation. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY. |
| `--policy` | `POLICY_PATH` | `no` | `` | Optional template policy to verify before installing from --lock. |
| `--require-attestation` | `` | `no` | `False` | Block installation unless --attestation verifies with a trusted signature. |
| `--force` | `` | `no` | `False` | Allow replacing an installed template with the same id. |
| `--json` | `` | `no` | `False` | Print machine-readable template-install summary. |

### `falsiflow adoption-check`

Audit the five adoption priorities as a machine-readable readiness gate.

```text
falsiflow adoption-check [-h] --out-dir OUT_DIR [--json] [--force]
                                [--skip-dist]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--out-dir` | `OUT_DIR` | `yes` | `` | Directory for adoption-check artifacts and reports. |
| `--json` | `` | `no` | `False` | Print machine-readable adoption-check results. |
| `--force` | `` | `no` | `False` | Allow writing into a non-empty adoption-check directory. |
| `--skip-dist` | `` | `no` | `False` | Skip wheel/sdist build and isolated wheel install checks. |

### `falsiflow release-check`

Run the full pre-release gate: schemas, templates, bundles, zip verification, and portfolio.

```text
falsiflow release-check [-h] --out-dir OUT_DIR [--json] [--force]
                               [--skip-dist]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--out-dir` | `OUT_DIR` | `yes` | `` | Directory for release-check artifacts and reports. |
| `--json` | `` | `no` | `False` | Print machine-readable release-check results. |
| `--force` | `` | `no` | `False` | Allow replacing a non-empty release-check directory. |
| `--skip-dist` | `` | `no` | `False` | Skip wheel/sdist build and isolated wheel install checks. |

### `falsiflow validate`

Validate a Falsiflow project config.

```text
falsiflow validate [-h] --config CONFIG [--out OUT] [--strict]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--config` | `CONFIG` | `yes` | `` |  |
| `--out` | `OUT` | `no` | `` | Optional validation JSON output path. |
| `--strict` | `` | `no` | `False` | Exit non-zero when validation has errors. |

### `falsiflow portfolio`

Aggregate claim_summary.json files into a portfolio dashboard.

```text
falsiflow portfolio [-h] [--input INPUT] --out-dir OUT_DIR [--strict]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--input` | `INPUT` | `no` | `` | Audit directory, claim_summary.json, or root to scan. Repeatable. |
| `--out-dir` | `OUT_DIR` | `yes` | `` |  |
| `--strict` | `` | `no` | `False` | Exit non-zero when any claim is blocked. |

### `falsiflow render`

Render measurement templates and an audit report.

```text
falsiflow render [-h] --config CONFIG [--evidence EVIDENCE]
                        --out-dir OUT_DIR
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--config` | `CONFIG` | `yes` | `` |  |
| `--evidence` | `EVIDENCE` | `no` | `` |  |
| `--out-dir` | `OUT_DIR` | `yes` | `` |  |

### `falsiflow audit`

Audit evidence against configured gates.

```text
falsiflow audit [-h] --config CONFIG --evidence EVIDENCE
                       --out-dir OUT_DIR [--strict]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--config` | `CONFIG` | `yes` | `` |  |
| `--evidence` | `EVIDENCE` | `yes` | `` |  |
| `--out-dir` | `OUT_DIR` | `yes` | `` |  |
| `--strict` | `` | `no` | `False` | Exit non-zero when claim_ready is false. |

### `falsiflow claim-check`

Run audit, source provenance, evidence bundle, and zip verification in one command.

```text
falsiflow claim-check [-h] [--project-dir PROJECT_DIR]
                             [--config CONFIG] [--evidence EVIDENCE]
                             [--out-dir OUT_DIR] [--strict] [--force] [--json]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--project-dir` | `PROJECT_DIR` | `no` | `` | Project directory containing project.json and evidence_pass_demo.csv; defaults --out-dir to PROJECT_DIR/claim_check. |
| `--config` | `CONFIG` | `no` | `` | Project config JSON path. Defaults to PROJECT_DIR/project.json when --project-dir is used. |
| `--evidence` | `EVIDENCE` | `no` | `` | Evidence CSV path. Defaults to PROJECT_DIR/evidence_pass_demo.csv when --project-dir is used. |
| `--out-dir` | `OUT_DIR` | `no` | `` | Output directory. Defaults to PROJECT_DIR/claim_check when --project-dir is used. |
| `--strict` | `` | `no` | `False` | Exit non-zero unless the complete claim check is ready. |
| `--force` | `` | `no` | `False` | Allow writing into a non-empty claim-check directory. |
| `--json` | `` | `no` | `False` | Print machine-readable claim-check summary. |

### `falsiflow bundle`

Build a portable evidence bundle with audit artifacts, sources, and hashes.

```text
falsiflow bundle [-h] --config CONFIG --evidence EVIDENCE
                        --out-dir OUT_DIR [--zip-out ZIP_OUT] [--strict]
                        [--force]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--config` | `CONFIG` | `yes` | `` |  |
| `--evidence` | `EVIDENCE` | `yes` | `` |  |
| `--out-dir` | `OUT_DIR` | `yes` | `` |  |
| `--zip-out` | `ZIP_OUT` | `no` | `` | Optional zip archive path for the bundle directory. |
| `--strict` | `` | `no` | `False` | Exit non-zero when audit or source provenance is blocked. |
| `--force` | `` | `no` | `False` | Allow writing into a non-empty bundle directory. |

### `falsiflow verify-bundle`

Verify a bundle directory or zip archive against its manifest and hashes.

```text
falsiflow verify-bundle [-h] (--bundle-dir BUNDLE_DIR | --zip ZIP_PATH)
                               [--out OUT] [--report-out REPORT_OUT]
                               [--strict]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--bundle-dir` | `BUNDLE_DIR` | `no` | `` | Bundle directory containing bundle_manifest.json. |
| `--zip` | `ZIP_PATH` | `no` | `` | Bundle zip archive to verify without manual extraction. |
| `--out` | `OUT` | `no` | `` | Optional JSON verification report output path. |
| `--report-out` | `REPORT_OUT` | `no` | `` | Optional Markdown verification report output path. |
| `--strict` | `` | `no` | `False` | Exit non-zero unless the bundle is verified and bundle_ready. |

### `falsiflow next`

Print the next evidence-filling actions.

```text
falsiflow next [-h] --config CONFIG [--evidence EVIDENCE]
                      --out-dir OUT_DIR
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--config` | `CONFIG` | `yes` | `` |  |
| `--evidence` | `EVIDENCE` | `no` | `` |  |
| `--out-dir` | `OUT_DIR` | `yes` | `` |  |

### `falsiflow sources`

Write a source-file provenance manifest for evidence rows.

```text
falsiflow sources [-h] --config CONFIG --evidence EVIDENCE --out OUT
                         [--report-out REPORT_OUT] [--strict]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--config` | `CONFIG` | `yes` | `` |  |
| `--evidence` | `EVIDENCE` | `yes` | `` |  |
| `--out` | `OUT` | `yes` | `` | Source manifest JSON output path. |
| `--report-out` | `REPORT_OUT` | `no` | `` | Optional Markdown report output path. |
| `--strict` | `` | `no` | `False` | Exit non-zero when required source provenance is incomplete. |

### `falsiflow ingest-limina-source-values`

Convert LIMINA source-value sheets into Falsiflow evidence.

```text
falsiflow ingest-limina-source-values [-h] --input INPUT --out OUT
                                             [--summary-out SUMMARY_OUT]
                                             [--project-out PROJECT_OUT]
                                             --default-candidate DEFAULT_CANDIDATE
                                             [--default-gate DEFAULT_GATE]
                                             [--project-id PROJECT_ID]
                                             [--claim-id CLAIM_ID]
                                             [--claim-statement CLAIM_STATEMENT]
                                             [--source-file-base-dir SOURCE_FILE_BASE_DIR]
                                             [--allowed-source-root ALLOWED_SOURCE_ROOT]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--input` | `INPUT` | `yes` | `` | LIMINA source-value CSV. Repeatable. |
| `--out` | `OUT` | `yes` | `` | Falsiflow evidence CSV to write. |
| `--summary-out` | `SUMMARY_OUT` | `no` | `` | Optional conversion summary JSON. |
| `--project-out` | `PROJECT_OUT` | `no` | `` | Optional generated Falsiflow project JSON. |
| `--default-candidate` | `DEFAULT_CANDIDATE` | `yes` | `` |  |
| `--default-gate` | `DEFAULT_GATE` | `no` | `h_a_medium_stability` |  |
| `--project-id` | `PROJECT_ID` | `no` | `limina_nhi_pedot_habc_falsiflow` |  |
| `--claim-id` | `CLAIM_ID` | `no` | `limina_nhi_pedot_habc_evidence_completeness` |  |
| `--claim-statement` | `CLAIM_STATEMENT` | `no` | `LIMINA NHI-PEDOT H-A/H-B/H-C evidence pack is complete enough for Falsiflow provenance audit. This is not a material suitability claim.` |  |
| `--source-file-base-dir` | `SOURCE_FILE_BASE_DIR` | `no` | `.` |  |
| `--allowed-source-root` | `ALLOWED_SOURCE_ROOT` | `no` | `['data/source_files']` |  |

### `falsiflow ingest-wide-csv`

Convert a wide lab CSV into Falsiflow evidence rows.

```text
falsiflow ingest-wide-csv [-h] --input INPUT --out OUT
                                 [--summary-out SUMMARY_OUT] [--config CONFIG]
                                 [--coverage-out COVERAGE_OUT] [--strict]
                                 [--profile {generic-wide,instrument-export,plate-reader,vendor-measurement}]
                                 --gate-id GATE_ID --candidate-id CANDIDATE_ID
                                 [--sample-id-column SAMPLE_ID_COLUMN]
                                 [--field FIELD]
                                 [--exclude-column EXCLUDE_COLUMN]
                                 [--gate-id-column GATE_ID_COLUMN]
                                 [--candidate-id-column CANDIDATE_ID_COLUMN]
                                 [--source-file SOURCE_FILE]
                                 [--source-file-column SOURCE_FILE_COLUMN]
                                 [--measured-at MEASURED_AT]
                                 [--measured-at-column MEASURED_AT_COLUMN]
                                 [--operator-or-agent OPERATOR_OR_AGENT]
                                 [--operator-or-agent-column OPERATOR_OR_AGENT_COLUMN]
                                 [--instrument-id INSTRUMENT_ID]
                                 [--instrument-id-column INSTRUMENT_ID_COLUMN]
                                 [--notes NOTES] [--notes-column NOTES_COLUMN]
```

| Argument | Value | Required | Default | Help |
| --- | --- | --- | --- | --- |
| `--input` | `INPUT` | `yes` | `` | Wide lab CSV. Repeatable. |
| `--out` | `OUT` | `yes` | `` | Falsiflow evidence CSV to write. |
| `--summary-out` | `SUMMARY_OUT` | `no` | `` | Optional conversion summary JSON. |
| `--config` | `CONFIG` | `no` | `` | Optional project config for import coverage precheck. |
| `--coverage-out` | `COVERAGE_OUT` | `no` | `` | Optional coverage precheck JSON output path. |
| `--strict` | `` | `no` | `False` | Exit non-zero when project coverage is blocked. |
| `--profile` | `{generic-wide,instrument-export,plate-reader,vendor-measurement}` | `no` | `generic-wide` | Column mapping profile for common lab, vendor, or instrument CSV shapes. |
| `--gate-id` | `GATE_ID` | `yes` | `` |  |
| `--candidate-id` | `CANDIDATE_ID` | `yes` | `` |  |
| `--sample-id-column` | `SAMPLE_ID_COLUMN` | `no` | `` | Column containing sample ids. Defaults to the selected profile. |
| `--field` | `FIELD` | `no` | `[]` | Value column to import. Repeatable. Defaults to all non-metadata columns. |
| `--exclude-column` | `EXCLUDE_COLUMN` | `no` | `[]` | Column to ignore when auto-selecting value columns. |
| `--gate-id-column` | `GATE_ID_COLUMN` | `no` | `` |  |
| `--candidate-id-column` | `CANDIDATE_ID_COLUMN` | `no` | `` |  |
| `--source-file` | `SOURCE_FILE` | `no` | `` |  |
| `--source-file-column` | `SOURCE_FILE_COLUMN` | `no` | `` |  |
| `--measured-at` | `MEASURED_AT` | `no` | `` |  |
| `--measured-at-column` | `MEASURED_AT_COLUMN` | `no` | `` |  |
| `--operator-or-agent` | `OPERATOR_OR_AGENT` | `no` | `` |  |
| `--operator-or-agent-column` | `OPERATOR_OR_AGENT_COLUMN` | `no` | `` |  |
| `--instrument-id` | `INSTRUMENT_ID` | `no` | `` |  |
| `--instrument-id-column` | `INSTRUMENT_ID_COLUMN` | `no` | `` |  |
| `--notes` | `NOTES` | `no` | `` |  |
| `--notes-column` | `NOTES_COLUMN` | `no` | `` |  |

