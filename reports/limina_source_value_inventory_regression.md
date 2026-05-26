# LIMINA Source-Value Inventory Regression

This verifies that filled source-value rows are inventoried and missing source files are caught.

**Status:** `pass`
**Source references:** 1
**Filled source-value references:** 1
**Missing references:** 1

## Checks

| Check | Pass |
| --- | --- |
| `filled_source_value_reference_count_is_one` | `true` |
| `blank_source_value_row_ignored` | `true` |
| `missing_reference_detected` | `true` |
| `status_reports_missing_reference` | `true` |

## Boundary

This regression uses temporary source-value rows only. It does not create source files or measured material evidence.
