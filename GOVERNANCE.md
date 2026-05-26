# Falsiflow Governance

Falsiflow is maintained as a conservative evidence-gated workflow project. The
governance goal is to keep the public tool easy to try, hard to misuse, and
clear about what `claim_ready` does and does not mean.

## Maintainer Responsibilities

Maintainers are responsible for:

- preserving the evidence-gate contract in code, docs, examples, and release
  artifacts
- reviewing changes that affect schemas, bundled templates, bundle
  verification, release gates, or responsible-use wording
- keeping the first-run path, template gallery, and release-check workflow
  reliable
- triaging issues according to [SUPPORT.md](SUPPORT.md),
  [SECURITY.md](SECURITY.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- declining changes that blur `claim_ready` into scientific proof, regulatory
  approval, safety proof, or commercial readiness

## Decision Process

Routine bug fixes, docs improvements, and template corrections can be accepted
after one maintainer review when the relevant tests or release gates pass.
Changes to project contracts, public schemas, release automation, security
behavior, or responsible-use boundaries should receive a second maintainer or
domain-reviewer pass when available.

When tradeoffs are unclear, prefer the option that keeps evidence blocked until
source-backed data, metadata, and configured gates agree.

## Template Admission

New bundled templates should include:

- a clear domain and claim that a reviewer can understand quickly
- `project.json`, evidence templates, passing demo evidence, placeholder demo
  evidence, and raw source files
- at least one blocked-path story that proves missing or placeholder evidence
  does not become `claim_ready`
- `template-check`, `template-pack`, `verify-template-pack`, `template-release`,
  `verify-template-release`, and `template-install` coverage in release gates
- responsible-use wording when a domain could be mistaken for safety, clinical,
  regulatory, or commercial validation

Template authors should follow
[docs/falsiflow_template_authoring.md](docs/falsiflow_template_authoring.md)
before proposing a bundled template.

## Release Ownership

A release owner should run `falsiflow release-check --force`, inspect the
generated release artifacts, confirm the source distribution contains the
community, citation, governance, security, and support files, and verify that
external evidence is either `external_ready` or intentionally documented as
`external_blocked`.

Public releases should not be announced as externally ready until the hosted demo
URL, pipx path, Windows/PowerShell smoke path, and public repository evidence
have passed `external-check --strict`.

## Security And Conduct

Security-sensitive reports follow [SECURITY.md](SECURITY.md). Conduct reports
follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Maintainers may pause, close,
or redirect issues and pull requests that publish private evidence, bypass
verification, or present blocked evidence as ready.
