# Security Policy

Falsiflow is a local-first evidence workflow tool. It does not execute arbitrary
project-config code, but it does read project files, evidence CSVs, source-file
references, bundle archives, and generated reports. Treat those inputs as
untrusted unless they come from a source you control.

## Reporting Security Issues

Please avoid posting exploit details in public issues. Use the repository's
private security advisory channel when available. If no private channel exists,
contact the maintainers through the least-public project channel available and
include only enough detail to reproduce the issue safely.

Treat a vulnerability in path handling, bundle or template-pack verification,
source provenance, or packaging as security-sensitive even when it does not
involve network access.

Useful reports include:

- a short impact summary
- affected Falsiflow version or commit
- operating system and Python version
- a minimal reproduction bundle, project config, or command
- whether source files, zip archives, or generated reports are involved

## Scope

Security-relevant issues include:

- unsafe bundle zip extraction or path traversal
- incorrect SHA-256 or byte-size verification
- unsafe template-pack zip extraction or template substitution
- source-file provenance bypasses
- unexpected file writes outside requested output directories
- command behavior that marks blocked evidence as ready
- packaging issues that omit required templates or release documentation

## Evidence Bundle Handling

Run `falsiflow verify-bundle` before trusting a received bundle. Do not treat a
bundle as trustworthy just because it opens successfully; verification must
check paths, hashes, byte sizes, copied source records, and unmanifested files.

Run `falsiflow verify-template-pack` before trusting a received starter
template. Prefer `falsiflow template-install` for adoption: it verifies the zip,
reruns `template-check`, and writes `falsiflow_template_index.json` before a
template is reused. For repeatable adoption, generate a registry with
`falsiflow template-registry`, lock an entry with `falsiflow template-lock`, and
install from `falsiflow_template_lock.json` so the source zip byte count and
SHA-256 are pinned. Treat registry `source_url` values as untrusted until the
lock and install steps re-check their hashes. For distributed locks, run
`falsiflow template-attest` and `falsiflow verify-template-attestation`; a
`template_attestation_verified` report means the lockfile bytes and optional
HMAC signature matched the expected subject. Use `template-install --attestation
... --require-attestation` when adopting templates from a signed lock. For team
allowlists, create `falsiflow template-policy`, verify it with
`falsiflow verify-template-policy`, and install with `template-install --policy`.
For distribution to another team or machine, prefer `falsiflow
template-release`, verify it with `falsiflow verify-template-release`, and
install with `template-install --release` so the pack, registry, lock,
attestation, and policy are checked together. Treat a release as untrusted if
verification reports unsafe artifact paths, duplicate artifact paths,
unmanifested files, hash mismatches, or a registry SHA-256 mismatch against the
lockfile. Use `verify-template-release --report-out` to keep a Markdown review
record alongside the machine-readable JSON report.

## Supported Versions

The active development version is checked by `falsiflow release-check`. Until
the project has multiple maintained release lines, security fixes target the
current release line.
