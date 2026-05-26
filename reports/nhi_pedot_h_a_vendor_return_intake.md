# NHI-PEDOT H-A Vendor Return Intake

This report checks the return inbox for real H-A measurement files. It is not measured evidence.

**Status:** `awaiting_vendor_return_files`
**Return directory:** `data/nhi_pedot_h_a_vendor_return_inbox`
**Inbox README:** `data/nhi_pedot_h_a_vendor_return_inbox/README.md`

## File Checklist

| Item | Required | Exists | Status | Path |
| --- | --- | --- | --- | --- |
| `completed_raw_measurements` | `true` | `false` | `missing_or_incomplete` | `data/nhi_pedot_h_a_vendor_return_inbox/completed_raw_measurements.csv` |
| `completed_bundle_entry_sheet` | `false` | `true` | `missing_or_incomplete` | `data/nhi_pedot_h_a_vendor_return_inbox/completed_bundle_entry_sheet.csv` |
| `completed_chain_of_custody` | `true` | `false` | `missing_or_incomplete` | `data/nhi_pedot_h_a_vendor_return_inbox/completed_chain_of_custody.csv` |
| `instrument_exports` | `true` | `true` | `missing_or_empty` | `data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports` |
| `deviation_log` | `true` | `false` | `missing` | `data/nhi_pedot_h_a_vendor_return_inbox/deviation_log.md` |

## Raw Measurement CSV

- Path: `data/nhi_pedot_h_a_vendor_return_inbox/completed_raw_measurements.csv`
- Exists: `False`
- Schema OK: `False`
- Rows: 0
- Rows with values: 0
- Missing/unresolved source_file references: 0
- Missing fields: `run_id`, `sample_event`, `target_field`, `value`, `unit`, `measured_at`, `operator_or_agent`, `instrument_id`, `source_file`, `notes`

## Bundle Entry Sheet

- Path: `data/nhi_pedot_h_a_vendor_return_inbox/completed_bundle_entry_sheet.csv`
- Exists: `True`
- Schema OK: `True`
- Rows: 96
- Apply rows: 0
- Ready to apply: 0
- Blocked apply rows: 0
- Missing/unresolved source_file references: 0

## Chain Of Custody

- Path: `data/nhi_pedot_h_a_vendor_return_inbox/completed_chain_of_custody.csv`
- Exists: `False`
- Schema OK: `False`
- Rows: 0
- Pending transfer rows: 0

## Instrument Exports

- Directory: `data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports`
- File count: 0

## Post-Return Commands

```bash
python3 scripts/render_nhi_pedot_h_a_vendor_bundle_entry_sheet.py
python3 scripts/apply_nhi_pedot_h_a_vendor_bundle_entry_return.py --sheet data/nhi_pedot_h_a_vendor_return_inbox/completed_bundle_entry_sheet.csv
python3 scripts/import_nhi_pedot_h_a_source_values.py
python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py
python3 scripts/qc_nhi_pedot_h_a_intake.py --runs data/nhi_pedot_h_a_runs_active.csv --strict-exit
python3 scripts/interpret_nhi_pedot_h_a_sentinel.py --runs data/nhi_pedot_h_a_runs_active.csv
python3 scripts/run_limina_iteration.py
```

## Boundary

This intake report only checks whether returned files are ready for merge/QC. Returned files are not material evidence until real rows pass merge, intake QC, H-A interpretation, and the final claim audit.
