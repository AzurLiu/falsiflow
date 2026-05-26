# Falsiflow Claim Check

- Status: `claim_check_ready`
- Claim ready: `true`
- Audit: `claim_ready`
- Audit review: `review_ready`
- Sources: `sources_ready`
- Bundle: `bundle_ready`
- Verification: `bundle_verified`
- Config: `public_demo/project/project.json`
- Evidence: `public_demo/project/evidence_pass_demo.csv`
- Blocking stage: `ready_for_human_review`
- Completion: 100.0%
- Blockers: 0
- Failures: 0

## Outputs

| Artifact | Path |
| --- | --- |
| `claim_check` | `public_demo/project/claim_check/claim_check.json` |
| `claim_check_report` | `public_demo/project/claim_check/claim_check.md` |
| `claim_audit` | `public_demo/project/claim_check/evidence_bundle/audit/claim_audit.json` |
| `claim_audit_report` | `public_demo/project/claim_check/evidence_bundle/audit/claim_audit.md` |
| `audit_review` | `public_demo/project/claim_check/evidence_bundle/audit/audit_review.json` |
| `audit_review_report` | `public_demo/project/claim_check/evidence_bundle/audit/audit_review.md` |
| `claim_summary` | `public_demo/project/claim_check/evidence_bundle/audit/claim_summary.json` |
| `next_actions` | `public_demo/project/claim_check/evidence_bundle/audit/next_actions.json` |
| `dashboard` | `public_demo/project/claim_check/evidence_bundle/audit/dashboard.html` |
| `source_manifest` | `public_demo/project/claim_check/evidence_bundle/source_manifest.json` |
| `source_manifest_report` | `public_demo/project/claim_check/evidence_bundle/source_manifest.md` |
| `bundle_manifest` | `public_demo/project/claim_check/evidence_bundle/bundle_manifest.json` |
| `bundle_zip` | `public_demo/project/claim_check/evidence_bundle.zip` |
| `bundle_verification` | `public_demo/project/claim_check/evidence_bundle_verify.json` |
| `bundle_verification_report` | `public_demo/project/claim_check/evidence_bundle_verify.md` |

## Next Actions

| Rank | Action | Why |
| ---: | --- | --- |
| 1 | `review_claim_for_release` | All required gates passed with source-backed evidence. |

## Failures

No failures found.
