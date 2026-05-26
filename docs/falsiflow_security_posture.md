# Falsiflow Security Posture

Falsiflow is local-first by design. The core workflow reads project configs,
evidence CSV files, source-file references, template packs, release bundles, and
generated reports from the user's machine. It does not upload project data to a
hosted service, and project configuration is data, not arbitrary code executed
by the runtime.

This document is the public security and supply-chain posture for maintainers,
reviewers, and early adopters. For private vulnerability reporting, see
[../SECURITY.md](../SECURITY.md).

## Runtime Boundaries

- Project configs, evidence rows, source manifests, and templates are treated as
  untrusted input.
- Config files describe gates, derived metrics, and acceptance rules. They do
  not run Python, shell commands, notebook cells, or plugin code.
- Evidence readiness is conservative: malformed CSV headers, duplicate evidence
  keys, missing source files, placeholder values, invalid configs, and failed
  acceptance rules block `claim_ready`.
- Browser demos and local launchpads are generated static/local artifacts. They
  are for review and onboarding, not a hosted processing service.

## Bundle And Template Verification

Falsiflow's highest-risk file boundary is the exchange of generated zip
archives and starter templates. The maintained verification commands are:

- `falsiflow verify-bundle`
- `falsiflow verify-template-pack`
- `falsiflow verify-template-attestation`
- `falsiflow verify-template-policy`
- `falsiflow verify-template-release`

These checks verify relative paths, reject unsafe path traversal, compare byte
sizes and SHA-256 hashes, report unmanifested files, and block template release
installs when pack, registry, lockfile, attestation, policy, or release metadata
do not agree.

## Repository Automation

Public repository automation should keep the project auditable without making a
maintainer manually remember every trust signal:

- `.github/dependabot.yml` tracks GitHub Actions and Python packaging inputs on
  a weekly schedule.
- `.github/workflows/falsiflow-scorecard.yml` runs OpenSSF Scorecard, writes a
  SARIF result, uploads it through `github/codeql-action/upload-sarif`, and uses
  `security-events: write` plus `id-token: write` permissions for security
  reporting and published Scorecard results.
- `.github/workflows/falsiflow.yml` runs the core regression, schema, template,
  bundle, and release gates.
- `.github/workflows/falsiflow-cross-platform.yml` runs Linux, macOS, Windows,
  pipx, installer, browser-entry, and external readiness smoke tests.
- `.github/workflows/falsiflow-external-evidence.yml` captures hosted demo,
  public PyPI package URL, checkout pipx, public-package pipx, Windows, and
  `external-check --strict` artifacts for public launch review.
- `.github/workflows/falsiflow-publish.yml` builds wheel and sdist artifacts,
  runs `twine check`, uploads distributions, and supports PyPI trusted
  publishing.

## Release Gates

`falsiflow release-check` is the local release gate. It checks the security
posture files, Dependabot config, Scorecard workflow, SECURITY policy, source
distribution contents, installed wheel behavior, template release verification,
external evidence readiness, and all starter-template verification paths.

The release is not considered externally ready until `external-check --strict`
has evidence for the public repository, hosted demo URL, pipx smoke path, and
Windows/PowerShell validation.

## Known Limitations

- A generated local HTML demo can be inspected by a browser, but it is not an
  authorization boundary.
- Scorecard and Dependabot only run after the project is on GitHub with Actions
  enabled.
- Falsiflow can verify hashes and paths for declared artifacts, but it cannot
  prove that an upstream lab, vendor, or instrument produced truthful data.
- `claim_ready` is an evidence gate for a configured workflow. It is not
  regulatory approval, clinical validation, or a substitute for independent
  engineering review.
