# Falsiflow Claim Check

- Status: `claim_check_ready`
- Claim ready: `true`
- Audit: `claim_ready`
- Audit review: `review_ready`
- Sources: `sources_ready`
- Bundle: `bundle_ready`
- Verification: `bundle_verified`
- Config: `docs/public_demo/project/project.json`
- Evidence: `docs/public_demo/project/evidence_pass_demo.csv`
- Blocking stage: `ready_for_human_review`
- Completion: 100.0%
- Blockers: 0
- Failures: 0

## Outputs

| Artifact | Path |
| --- | --- |
| `claim_check` | `docs/public_demo/project/claim_check/claim_check.json` |
| `claim_check_report` | `docs/public_demo/project/claim_check/claim_check.md` |
| `claim_audit` | `docs/public_demo/project/claim_check/evidence_bundle/audit/claim_audit.json` |
| `claim_audit_report` | `docs/public_demo/project/claim_check/evidence_bundle/audit/claim_audit.md` |
| `audit_review` | `docs/public_demo/project/claim_check/evidence_bundle/audit/audit_review.json` |
| `audit_review_report` | `docs/public_demo/project/claim_check/evidence_bundle/audit/audit_review.md` |
| `claim_summary` | `docs/public_demo/project/claim_check/evidence_bundle/audit/claim_summary.json` |
| `next_actions` | `docs/public_demo/project/claim_check/evidence_bundle/audit/next_actions.json` |
| `dashboard` | `docs/public_demo/project/claim_check/evidence_bundle/audit/dashboard.html` |
| `source_manifest` | `docs/public_demo/project/claim_check/evidence_bundle/source_manifest.json` |
| `source_manifest_report` | `docs/public_demo/project/claim_check/evidence_bundle/source_manifest.md` |
| `bundle_manifest` | `docs/public_demo/project/claim_check/evidence_bundle/bundle_manifest.json` |
| `bundle_zip` | `docs/public_demo/project/claim_check/evidence_bundle.zip` |
| `bundle_verification` | `docs/public_demo/project/claim_check/evidence_bundle_verify.json` |
| `bundle_verification_report` | `docs/public_demo/project/claim_check/evidence_bundle_verify.md` |

## Review Artifact Index

| Artifact | Status | Link | Purpose |
| --- | --- | --- | --- |
| Claim-check report | `claim_check_ready` | [Claim-check report](<claim_check.md>) | Top-level ready/blocked decision, blocking stage, failures, and next actions. |
| Claim-check JSON | `claim_check_ready` | [Claim-check JSON](<claim_check.json>) | Machine-readable status for CI, release-check, and browser handoffs. |
| Audit review | `review_ready` | [Audit review](<evidence_bundle/audit/audit_review.md>) | Human review card for gate results, blockers, and decision boundaries. |
| Claim audit | `claim_ready` | [Claim audit](<evidence_bundle/audit/claim_audit.md>) | Detailed measured evidence evaluation for the claim gates. |
| Source manifest | `sources_ready` | [Source manifest](<evidence_bundle/source_manifest.md>) | Raw source-file provenance, missing files, allowed roots, and blank source rows. |
| Bundle manifest | `bundle_ready` | [Bundle manifest](<evidence_bundle/bundle_manifest.json>) | Declared bundle contents with byte counts and SHA-256 hashes. |
| Bundle verification | `bundle_verified` | [Bundle verification](<evidence_bundle_verify.md>) | Independent zip integrity check for the review bundle. |
| Claim dashboard | `claim_check_ready` | [Claim dashboard](<evidence_bundle/audit/dashboard.html>) | Browser-readable evidence dashboard for non-CLI reviewers. |
| Evidence bundle | `bundle_ready` | [Evidence bundle](<evidence_bundle.zip>) | Portable review package containing inputs, audit outputs, source manifest, and copied sources. |

## Next Actions

| Rank | Action | Why |
| ---: | --- | --- |
| 1 | `review_claim_for_release` | All required gates passed with source-backed evidence. |

## Evidence Todo

No evidence todo items recorded.

## Failures

No failures found.
