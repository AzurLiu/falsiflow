# ZRC-ND Phase A Vendor Return Intake

This report checks the return inbox for real Phase A measurement files. It is not measured evidence.

**Status:** `awaiting_vendor_return_files`
**Return directory:** `data/zrc_nd_phase_a_vendor_return_inbox`
**Inbox README:** `data/zrc_nd_phase_a_vendor_return_inbox/README.md`

## File Checklist

| Item | Required | Exists | Status | Path |
| --- | --- | --- | --- | --- |
| `completed_phase_a_measurements` | `true` | `false` | `missing_or_incomplete` | `data/zrc_nd_phase_a_vendor_return_inbox/completed_phase_a_measurements.csv` |
| `completed_bundle_entry_sheet` | `false` | `true` | `missing_or_incomplete` | `data/zrc_nd_phase_a_vendor_return_inbox/completed_bundle_entry_sheet.csv` |
| `completed_chain_of_custody` | `true` | `false` | `missing_or_incomplete` | `data/zrc_nd_phase_a_vendor_return_inbox/completed_chain_of_custody.csv` |
| `instrument_exports` | `true` | `true` | `missing_or_unresolved` | `data/zrc_nd_phase_a_vendor_return_inbox/external_lab_exports` |
| `deviation_log` | `true` | `false` | `missing` | `data/zrc_nd_phase_a_vendor_return_inbox/deviation_log.md` |

## Phase A Measurement CSV

- Path: `data/zrc_nd_phase_a_vendor_return_inbox/completed_phase_a_measurements.csv`
- Exists: `False`
- Schema OK: `False`
- Expected rows: 8
- Rows: 0
- Missing run IDs: 8
- Unknown run IDs: 0
- Rows with missing/placeholder values: 0
- Missing fields: `run_id`, `date`, `operator_or_agent`, `phase`, `timepoint`, `replicate`, `article_id`, `variant_id`, `control_article_id`, `membrane_lot`, `mwco_kda`, `membrane_area_cm2`, `surface_modification`, `prefilter_lot`, `housing_material`, `medium_name`, `medium_lot`, `initial_volume_ml`, `flow_rate_ul_min`, `exposure_time_h`, `temperature_c`, `pH_initial`, `pH_final`, `osmolality_initial_mOsm_kg`, `osmolality_final_mOsm_kg`, `conductivity_initial_mS_cm`, `conductivity_final_mS_cm`, `lactate_initial_mM`, `lactate_final_mM`, `ammonia_initial_uM`, `ammonia_final_uM`, `bdnf_initial_pg_ml`, `bdnf_final_pg_ml`, `ngf_initial_pg_ml`, `ngf_final_pg_ml`, `albumin_initial`, `albumin_final`, `transferrin_initial`, `transferrin_final`, `total_protein_initial`, `total_protein_final`, `flow_resistance_initial`, `flow_resistance_final`, `bubble_events`, `visible_precipitate`, `gate_results`, `source_file`, `notes`

## Bundle Entry Sheet

- Path: `data/zrc_nd_phase_a_vendor_return_inbox/completed_bundle_entry_sheet.csv`
- Exists: `True`
- Schema OK: `True`
- Rows: 64
- Apply rows: 0
- Ready to apply: 0
- Blocked apply rows: 0
- Missing/unresolved source_file references: 0

## Bundle Entry Apply

- Path: `data/zrc_nd_phase_a_vendor_bundle_entry_apply.json`
- Status: `zrc_phase_a_vendor_bundle_entry_apply_no_apply_rows`
- Applied bundles: 0
- Applied source-value rows: 0
- Errors: 0

## Chain Of Custody

- Path: `data/zrc_nd_phase_a_vendor_return_inbox/completed_chain_of_custody.csv`
- Exists: `False`
- Schema OK: `False`
- Rows: 0
- Pending transfer rows: 0
- Missing/unresolved instrument exports: 0

## Instrument Exports

- Directory: `data/zrc_nd_phase_a_vendor_return_inbox/external_lab_exports`
- File count: 0

## Post-Return Commands

```bash
python3 scripts/render_zrc_nd_phase_a_vendor_bundle_entry_sheet.py
python3 scripts/apply_zrc_nd_phase_a_vendor_bundle_entry_sheet.py
python3 scripts/import_limina_wide_source_values.py --profile zrc_phase_a
python3 scripts/merge_zrc_nd_measurements.py --measurements data/zrc_nd_phase_a_vendor_return_inbox/completed_phase_a_measurements.csv --out data/zrc_nd_validation_runs_active.csv
python3 scripts/interpret_zrc_nd_sentinel.py --runs data/zrc_nd_validation_runs_active.csv
python3 scripts/evaluate_zrc_nd_validation_runs.py --runs data/zrc_nd_validation_runs_active.csv
python3 scripts/suggest_zrc_nd_next_measurements.py --runs data/zrc_nd_validation_runs_active.csv
python3 scripts/run_limina_iteration.py
```

## Boundary

This intake report only checks whether returned Phase A files are ready for merge/QC. Returned files are not material evidence until real rows pass merge, sentinel interpretation, readiness audit, and final claim audit.
