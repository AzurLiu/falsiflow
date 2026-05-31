# Falsiflow Bundle Verification

- Status: `bundle_verified`
- Integrity: `integrity_verified`
- Bundle status: `bundle_ready`
- Input: `zip` `docs/public_demo/project/claim_check/evidence_bundle.zip`
- Artifacts checked: 13/13
- Issues: 0 errors=0 warnings=0

## Review Artifact Index

| Artifact | Status | Path | Purpose |
| --- | --- | --- | --- |
| Bundle input | `bundle_verified` | `docs/public_demo/project/claim_check/evidence_bundle.zip` | Received zip or bundle directory being verified before review or forwarding. |
| Bundle manifest | `bundle_ready` | `docs/public_demo/project/claim_check/evidence_bundle.zip:bundle_manifest.json` | Declared bundle contents, roles, byte counts, and SHA-256 hashes. |
| Audit review | `bundle_ready` | `docs/public_demo/project/claim_check/evidence_bundle.zip:audit/audit_review.md` | Reviewer decision card for the claim audit. |
| Claim audit | `bundle_ready` | `docs/public_demo/project/claim_check/evidence_bundle.zip:audit/claim_audit.md` | Detailed gate-by-gate evidence evaluation. |
| Source manifest | `bundle_ready` | `docs/public_demo/project/claim_check/evidence_bundle.zip:source_manifest.md` | Source-file provenance, missing-file, blank-row, and allowed-root review. |
| Dashboard | `bundle_ready` | `docs/public_demo/project/claim_check/evidence_bundle.zip:audit/dashboard.html` | Browser-readable view of measured evidence and claim state. |
| Integrity issues | `integrity_verified` | `docs/public_demo/project/claim_check/evidence_bundle.zip` | Use the issues table below if integrity is not verified. |

## Counters

| Metric | Count |
| --- | ---: |
| `missing_artifact_count` | 0 |
| `bytes_mismatch_count` | 0 |
| `hash_mismatch_count` | 0 |
| `unsafe_path_count` | 0 |
| `duplicate_path_count` | 0 |
| `unmanifested_file_count` | 0 |
| `zip_member_count` | 14 |
| `zip_extracted_file_count` | 14 |
| `zip_issue_count` | 0 |

## Issues

No issues found.
