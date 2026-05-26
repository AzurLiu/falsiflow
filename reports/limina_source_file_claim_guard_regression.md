# LIMINA Source-File Claim Guard Regression

This regression checks that measured-looking rows cannot become claimable unless they cite an existing source_file under the manifest.

**Status:** `pass`
**Missing-source claimable:** `false`
**Positive-control claimable:** `true`

## Assertions

| Assertion | Result | Detail |
| --- | --- | --- |
| `missing_source_not_claimable` | `pass` | claimable=False |
| `blank_source_file_is_placeholder` | `pass` | placeholder_markers=['source_file=missing'] |
| `missing_source_file_is_issue` | `pass` | source_file_issue_count=1 |
| `existing_allowed_source_can_be_claimable` | `pass` | claimable=True; measured=1 |

## Boundary

The positive-control source file is temporary regression scaffolding only. It is not LIMINA material evidence.
