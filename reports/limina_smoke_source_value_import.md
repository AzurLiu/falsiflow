# LIMINA Smoke Source Value Import

This report imports source-value sidecars into the smoke entry sheet. It is not measured evidence.

**Status:** `smoke_source_value_import_no_importable_rows`
**Source value files:** 3
**Source value rows:** 182
**Imported rows:** 0
**Changed rows:** 0
**Errors:** 0
**Warnings:** 0

## Accepted Sidecar Columns

`queue_id` is preferred. Alternatively use `run_id`, `sample_event`, and `target_field` together.

```text
queue_id,run_id,sample_event,target_field,value,measured_at,operator_or_agent,instrument_id,source_file,notes,apply
```

## Value Files

- `data/limina_smoke_raw_csv_extracted_values.csv`
- `data/limina_smoke_source_values.csv`
- `data/limina_smoke_unstructured_review_values.csv`

## Imported Rows

- No rows imported.

## Issues

- No import issues.

## Boundary

This importer only copies real, source-file-backed values into the smoke entry sheet. It does not create measured evidence; apply, preflight, merge, QC, and claim audit still control the gate.
