# Falsiflow Audit Review

- Decision: `ready_for_human_release_review`
- Status: `review_ready`
- Claim ready: `true`
- Blocking stage: `ready_for_human_review`
- Completion: 100.0%
- Blockers: 0
- Project errors: 0
- Evidence errors: 0

## Gate Snapshot

| Gate | Status | Completion | Valid rows | Required rows | Blockers |
| --- | --- | ---: | ---: | ---: | ---: |
| `coating_provenance` | `passed` | 100.0% | 3 | 3 | 0 |
| `extract_stability` | `passed` | 100.0% | 5 | 5 | 0 |
| `bioresponse_screen` | `passed` | 100.0% | 6 | 6 | 0 |

## Checks

| Check | Status | Message |
| --- | --- | --- |
| `project_config_errors` | `passed` | Project validation errors: 0. |
| `evidence_file_errors` | `passed` | Evidence diagnostics errors: 0. |
| `required_gate_evidence` | `passed` | Required evidence completion: 100.0%. |
| `gate_blockers` | `passed` | Gate blockers: 0. |
| `warnings_review` | `passed` | Warnings requiring reviewer attention: 0. |
| `human_release_review` | `review` | A ready audit still needs human review of raw sources, claim wording, and downstream-use boundaries. |

## Top Blockers

No blockers found.

## Next Actions

- 1. `review_claim_for_release` - All required gates passed with source-backed evidence.

## Human Review Checklist

- Confirm raw source files match the evidence rows and sample ids.
- Confirm claim wording is no broader than the configured gates and measured evidence.
- Confirm warnings are intentionally accepted or repaired before release.
- Confirm the audit is not treated as biological safety, clinical efficacy, regulatory compliance, or commercial readiness proof.
