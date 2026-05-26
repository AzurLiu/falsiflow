# LIMINA Smoke Starter Execution Pack

This is the execution checklist for the 19-row starter batch. It is not measured evidence.

**Status:** `smoke_starter_execution_pack_ready`
**Starter rows:** 19
**Source directories:** 1
**Existing source files:** 0
**Ready for import:** 0
**Blocked rows:** 19
**CSV:** `data/limina_smoke_starter_execution_pack.csv`

## Source Classes

| Source class | Rows |
| --- | ---: |
| `bench_or_chain_of_custody_record` | 3 |
| `conductivity_meter_export_or_photo` | 2 |
| `image_or_scoring_worksheet` | 4 |
| `osmometer_report_or_export` | 2 |
| `pH_meter_export_or_photo` | 2 |
| `supplier_or_build_record` | 4 |
| `swelling_dimension_or_mass_worksheet` | 1 |
| `temperature_or_incubator_log` | 1 |

## File Checklist

| Seq | Queue | Field | Source class | Exists | Required metadata | Source file |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `SQ-0096` | `date` | `bench_or_chain_of_custody_record` | `false` | run_id or sample_id, operator, date, transfer or exposure event | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_date_bench_or_chain_of_custody_record.csv` |
| 2 | `SQ-0097` | `medium_name` | `bench_or_chain_of_custody_record` | `false` | run_id or sample_id, operator, date, transfer or exposure event | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_medium_name_bench_or_chain_of_custody_record.csv` |
| 3 | `SQ-0098` | `medium_lot` | `bench_or_chain_of_custody_record` | `false` | run_id or sample_id, operator, date, transfer or exposure event | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_medium_lot_bench_or_chain_of_custody_record.csv` |
| 4 | `SQ-0099` | `temperature_c` | `temperature_or_incubator_log` | `false` | run_id or batch window, date/time, temperature source | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_temperature_c_temperature_or_incubator_log.csv` |
| 5 | `SQ-0100` | `mea_coupon_id` | `supplier_or_build_record` | `false` | lot, recipe, CoA, label, or build identifier | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_mea_coupon_id_supplier_or_build_record.pdf` |
| 6 | `SQ-0101` | `electrode_material` | `supplier_or_build_record` | `false` | lot, recipe, CoA, label, or build identifier | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_electrode_material_supplier_or_build_record.pdf` |
| 7 | `SQ-0102` | `laminin_or_peptide_density` | `supplier_or_build_record` | `false` | lot, recipe, CoA, label, or build identifier | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_laminin_or_peptide_density_supplier_or_build_record.pdf` |
| 8 | `SQ-0103` | `sterilization_or_aseptic_protocol` | `supplier_or_build_record` | `false` | lot, recipe, CoA, label, or build identifier | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_sterilization_or_aseptic_protocol_supplier_or_build_record.pdf` |
| 9 | `SQ-0104` | `pH` | `pH_meter_export_or_photo` | `false` | run_id, measurement date, instrument_id or calibration record | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/initial_pH_initial_pH_meter_export_or_photo.csv` |
| 10 | `SQ-0105` | `osmolality` | `osmometer_report_or_export` | `false` | run_id, mOsm/kg value, vendor or osmometer identifier | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/initial_osmolality_initial_mOsm_kg_osmometer_report_or_export.pdf` |
| 11 | `SQ-0106` | `conductivity` | `conductivity_meter_export_or_photo` | `false` | run_id, measurement date, instrument_id or standard-check record | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/initial_conductivity_initial_mS_cm_conductivity_meter_export_or_photo.csv` |
| 12 | `SQ-0107` | `pH` | `pH_meter_export_or_photo` | `false` | run_id, measurement date, instrument_id or calibration record | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/final_pH_final_pH_meter_export_or_photo.csv` |
| 13 | `SQ-0108` | `osmolality` | `osmometer_report_or_export` | `false` | run_id, mOsm/kg value, vendor or osmometer identifier | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/final_osmolality_final_mOsm_kg_osmometer_report_or_export.pdf` |
| 14 | `SQ-0109` | `conductivity` | `conductivity_meter_export_or_photo` | `false` | run_id, measurement date, instrument_id or standard-check record | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/final_conductivity_final_mS_cm_conductivity_meter_export_or_photo.csv` |
| 15 | `SQ-0110` | `visible_precipitate` | `image_or_scoring_worksheet` | `false` | run_id, imaging/scoring method, operator or vendor | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_visible_precipitate_image_or_scoring_worksheet.png` |
| 16 | `SQ-0111` | `visible_shedding` | `image_or_scoring_worksheet` | `false` | run_id, imaging/scoring method, operator or vendor | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_visible_shedding_image_or_scoring_worksheet.png` |
| 17 | `SQ-0112` | `swelling_fraction` | `swelling_dimension_or_mass_worksheet` | `false` | run_id, pre/post measurement basis, method, operator | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_swelling_fraction_swelling_dimension_or_mass_worksheet.csv` |
| 18 | `SQ-0113` | `delamination_score` | `image_or_scoring_worksheet` | `false` | run_id, imaging/scoring method, operator or vendor | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_delamination_score_image_or_scoring_worksheet.png` |
| 19 | `SQ-0114` | `optical_transparency_fraction` | `image_or_scoring_worksheet` | `false` | run_id, imaging/scoring method, operator or vendor | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_optical_transparency_fraction_image_or_scoring_worksheet.png` |

## Post-Fill Commands

```bash
python3 scripts/audit_limina_smoke_starter_batch_readiness.py
```
```bash
python3 scripts/run_limina_iteration.py
```

## Boundary

This execution pack is an operational checklist only. It does not create raw files, measured rows, or material-suitability evidence.
