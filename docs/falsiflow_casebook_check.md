# Falsiflow Casebook Check

`falsiflow casebook-check` turns the public casebook into a machine-verifiable
proof artifact. It runs every bundled starter template through the same
positive and placeholder evidence paths that a reviewer sees in
[falsiflow_public_casebook.md](falsiflow_public_casebook.md).

The command is meant for release reviewers, launch reviewers, and maintainers
who need one concise answer to: "Do the public examples actually prove the
workflow, and do the placeholder examples still block?"

## What It Proves

- Positive demo evidence reaches `claim_ready=true` for each starter template.
- Placeholder evidence stays blocked and does not become `claim_ready`.
- Source provenance reaches `sources_ready` for the positive demo path.
- Evidence bundles reach `bundle_ready`.
- Bundle zip verification reaches `bundle_verified`.
- Each template leaves a nested `template_check.json` and human-readable
  `template_check.md` for deeper review.

`casebook_check_ready` means all checked starters have positive demos,
placeholder blockers, source-ready provenance, and verified bundles. It is not
scientific proof, safety proof, regulatory approval, or a statement that the
demo evidence is real experimental evidence.

## Run It

```bash
falsiflow casebook-check --out-dir data/falsiflow/casebook_check --force
```

The command writes:

- `casebook_check.json`
- `casebook_check.md`
- `casebook_reviewer_replay.md`
- `casebook_reviewer_replay.sh`
- `casebook_reviewer_replay.ps1`
- `templates/<template>/template_check.json`
- `templates/<template>/template_check.md`
- nested audit, source-manifest, bundle, and bundle-verification artifacts

Use `--json` when a CI job or release script needs the summary on stdout:

```bash
falsiflow casebook-check --out-dir data/falsiflow/casebook_check --force --json
```

## Positive Demo Proof

The JSON summary records these counters:

- `template_count`
- `ready_template_count`
- `positive_demo_ready_count`
- `source_ready_count`
- `bundle_verified_count`

For a public release, `ready_template_count`, `positive_demo_ready_count`,
`source_ready_count`, and `bundle_verified_count` should match
`template_count`.

## Blocked-path Proof

The command also records `blocked_path_count`. This should match
`template_count`; otherwise at least one placeholder demo accidentally became a
ready claim.

That blocked-path proof is important for Falsiflow's public promise. The tool
is not only showing happy-path examples; it is proving that incomplete or
placeholder evidence cannot silently pass the same claim gate.

## Reviewer Replay Scripts

`casebook-check` writes a reviewer replay guide plus Bash and PowerShell
scripts. The scripts run:

- `falsiflow template-gallery`
- `falsiflow casebook-check`
- `falsiflow template-check` for every bundled starter
- a strict positive `falsiflow claim-check` for every passing demo
- a non-strict placeholder `falsiflow claim-check` for every blocked-path demo

The replay guide records the expected statuses: positive demos should produce
`claim_check_ready`, while placeholder demos should produce
`claim_check_blocked`. The Bash and PowerShell scripts assert those statuses
after each `claim-check` run. These artifacts let a release reviewer reproduce
the public casebook without hand-copying commands from prose.

## Release Contract

`falsiflow release-check` runs `casebook-check` and includes the resulting
status as `casebook_check_status`. `falsiflow adoption-check` also checks that
the casebook has positive demos, placeholder blockers, and verified bundles
across the starter templates.

Before publishing or posting the project publicly, the release should show:

- `casebook_check_ready`
- `casebook_positive_and_blocked_paths` passed
- `template_gallery_ready`
- `template_ready` for every starter template
- `bundle_verified` for every positive demo bundle

The public casebook can then point reviewers at the generated
`casebook_check.md` instead of asking them to trust documentation alone.
