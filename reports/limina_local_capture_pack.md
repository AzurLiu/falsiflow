# LIMINA Local Capture Pack

This pack converts the hybrid measurement routing plan into fillable files. It is not measured evidence.

**Status:** `local_capture_pack_ready`
**Tasks:** 350
**Local measured tasks:** 184
**Provenance/build-record tasks:** 126
**Outsource-preferred tasks:** 40

## Generated Files

| File | Purpose |
| --- | --- |
| `data/limina_local_capture_tasks.csv` | Row-level task table with route, source-file requirement, and merge command. |
| `data/nhi_pedot_h_a_local_capture_template.csv` | Fill local/provenance H-A long-form rows. |
| `data/nhi_pedot_h_a_osmolality_outsource_template.csv` | Fill H-A osmolality rows from external osmometer/lab report. |
| `data/zrc_nd_phase_a_local_capture_template.csv` | Fill ZRC-ND Phase A local/provenance wide rows. |
| `data/zrc_nd_phase_a_osmolality_outsource_template.csv` | Fill ZRC-ND Phase A osmolality rows from external osmometer/lab report. |
| `data/limina_local_instrument_register_template.csv` | Record instrument IDs, calibration requirements, and owners. |
| `data/limina_local_capture_qc_checklist.csv` | Pre-merge local QC checks that keep placeholders out of evidence. |

## Entry Counts

| Template | Rows |
| --- | ---: |
| H-A local/provenance long-form rows | 204 |
| H-A outsource osmolality long-form rows | 24 |
| ZRC-ND local/provenance wide rows | 8 |
| ZRC-ND outsource osmolality wide rows | 8 |

## Merge Commands After Real Values Exist

```bash
python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py --raw data/nhi_pedot_h_a_local_capture_template.csv
```

```bash
python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py --base data/nhi_pedot_h_a_runs_active.csv --raw data/nhi_pedot_h_a_osmolality_outsource_template.csv --out data/nhi_pedot_h_a_runs_active.csv
```

```bash
python3 scripts/merge_zrc_nd_measurements.py --measurements data/zrc_nd_phase_a_local_capture_template.csv
```

```bash
python3 scripts/merge_zrc_nd_measurements.py --base data/zrc_nd_validation_runs_active.csv --measurements data/zrc_nd_phase_a_osmolality_outsource_template.csv --out data/zrc_nd_validation_runs_active.csv
```

## Guardrails

- Fill values only from real measurements, calibrated logs, source files, supplier records, or vendor reports.
- Do not paste vendor capability replies or quotes into measurement fields.
- Keep osmolality separate unless a calibrated local osmometer is available.
- Run the normal iteration and claim guard after merging any real rows.

## Boundary

This pack is logistics and data-entry scaffolding only; it is not measured evidence until filled with real values and passed through QC, gate evaluators, and the final claim audit.
