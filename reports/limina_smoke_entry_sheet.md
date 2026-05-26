# LIMINA Smoke Entry Sheet

This is the single fillable intake sheet for smoke-tranche values. It is not measured evidence.

**Status:** `smoke_entry_sheet_ready`
**Rows:** 172
**Filled values:** 0
**Ready to apply:** 0
**Blocked value rows:** 0
**Sheet:** `data/limina_smoke_entry_sheet.csv`

## How To Use

- Fill `value`, `measured_at`, `operator_or_agent`, `instrument_id` when required, and `source_file`.
- Put the actual raw file, image, worksheet, report, or calibration log at the `source_file` path.
- Leave `apply=yes` for rows that should be written back to the smoke templates.

## After Filling

```bash
python3 scripts/apply_limina_smoke_entry_sheet.py
python3 scripts/run_limina_iteration.py
```

## Boundary

This sheet is a fillable intake surface only. Values require real source files and downstream preflight before they can reach any evidence gate.
