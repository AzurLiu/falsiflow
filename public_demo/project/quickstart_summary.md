# Falsiflow Quickstart

- Status: `quickstart_ready`
- Template: `biointerface_coatings`
- Project: `public_demo/project`
- Claim check: `claim_check_ready`
- Claim ready: `true`
- Audit review: `review_ready`
- Sources: `sources_ready`
- Bundle: `bundle_ready`
- Verification: `bundle_verified`
- Failures: 0

## Outputs

| Artifact | Path |
| --- | --- |
| `project_dir` | `public_demo/project` |
| `project_config` | `public_demo/project/project.json` |
| `evidence` | `public_demo/project/evidence_pass_demo.csv` |
| `quickstart_summary` | `public_demo/project/quickstart_summary.json` |
| `quickstart_report` | `public_demo/project/quickstart_summary.md` |
| `claim_check` | `public_demo/project/claim_check/claim_check.json` |
| `claim_check_report` | `public_demo/project/claim_check/claim_check.md` |
| `dashboard` | `public_demo/project/claim_check/evidence_bundle/audit/dashboard.html` |
| `evidence_bundle_zip` | `public_demo/project/claim_check/evidence_bundle.zip` |
| `bundle_verification` | `public_demo/project/claim_check/evidence_bundle_verify.json` |
| `bundle_verification_report` | `public_demo/project/claim_check/evidence_bundle_verify.md` |

## Next Commands

- `falsiflow doctor --project-dir public_demo/project --strict`
- `falsiflow claim-check --project-dir public_demo/project --strict --force`

## Failures

No failures found.
