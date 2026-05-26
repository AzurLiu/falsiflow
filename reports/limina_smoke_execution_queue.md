# LIMINA Smoke Execution Queue

This converts the smoke tranche into field-level measurement/provenance work items. It is not measured evidence.

**Status:** `smoke_execution_queue_ready`
**Rows:** 172
**H-A rows:** 114
**ZRC-ND rows:** 58
**Awaiting values:** 172
**Source-ready rows:** 0
**Source manifest:** `source_file_manifest_ready`; allowed_roots=12

## Batches

| Batch | Rows | Meaning |
| --- | ---: | --- |
| `B0_HA_setup_records` | 42 | H-A setup, medium, lot, build, and custody records. |
| `B1_HA_local_measurements` | 60 | H-A local pH, conductivity, temperature, imaging, swelling, and stability readouts. |
| `B2_HA_osmolality_external` | 12 | H-A osmometer report/export rows. |
| `B3_ZRC_parallel_local` | 50 | Parallel ZRC-ND local/source-record smoke rows. |
| `B4_ZRC_external_osmolality` | 8 | Parallel ZRC-ND osmometer report/export rows. |

## First 40 Queue Rows

| Priority | Queue | Batch | Branch | Run | Event | Field | Status | Recommended source file |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `SQ-0001` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `metadata` | `date` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/metadata_date_bench_or_chain_of_custody_record.csv` |
| 1 | `SQ-0002` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `metadata` | `medium_name` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/metadata_medium_name_bench_or_chain_of_custody_record.csv` |
| 1 | `SQ-0003` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `metadata` | `medium_lot` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/metadata_medium_lot_bench_or_chain_of_custody_record.csv` |
| 2 | `SQ-0004` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `metadata` | `temperature_c` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/metadata_temperature_c_temperature_or_incubator_log.csv` |
| 1 | `SQ-0005` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `metadata` | `mea_coupon_id` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/metadata_mea_coupon_id_supplier_or_build_record.pdf` |
| 1 | `SQ-0006` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `metadata` | `electrode_material` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/metadata_electrode_material_supplier_or_build_record.pdf` |
| 1 | `SQ-0007` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `metadata` | `laminin_or_peptide_density` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/metadata_laminin_or_peptide_density_supplier_or_build_record.pdf` |
| 1 | `SQ-0008` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `metadata` | `sterilization_or_aseptic_protocol` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/metadata_sterilization_or_aseptic_protocol_supplier_or_build_record.pdf` |
| 2 | `SQ-0009` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `initial` | `pH` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/initial_pH_initial_pH_meter_export_or_photo.csv` |
| 3 | `SQ-0010` | `B2_HA_osmolality_external` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `initial` | `osmolality` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/initial_osmolality_initial_mOsm_kg_osmometer_report_or_export.pdf` |
| 2 | `SQ-0011` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `initial` | `conductivity` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/initial_conductivity_initial_mS_cm_conductivity_meter_export_or_photo.csv` |
| 2 | `SQ-0012` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `final` | `pH` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/final_pH_final_pH_meter_export_or_photo.csv` |
| 3 | `SQ-0013` | `B2_HA_osmolality_external` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `final` | `osmolality` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/final_osmolality_final_mOsm_kg_osmometer_report_or_export.pdf` |
| 2 | `SQ-0014` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `final` | `conductivity` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/final_conductivity_final_mS_cm_conductivity_meter_export_or_photo.csv` |
| 2 | `SQ-0015` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `physical_inspection` | `visible_precipitate` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/physical_inspection_visible_precipitate_image_or_scoring_worksheet.png` |
| 2 | `SQ-0016` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `physical_inspection` | `visible_shedding` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/physical_inspection_visible_shedding_image_or_scoring_worksheet.png` |
| 2 | `SQ-0017` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `physical_inspection` | `swelling_fraction` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/physical_inspection_swelling_fraction_swelling_dimension_or_mass_worksheet.csv` |
| 2 | `SQ-0018` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `physical_inspection` | `delamination_score` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/physical_inspection_delamination_score_image_or_scoring_worksheet.png` |
| 2 | `SQ-0019` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | `physical_inspection` | `optical_transparency_fraction` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-0h/physical_inspection_optical_transparency_fraction_image_or_scoring_worksheet.png` |
| 1 | `SQ-0020` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `metadata` | `date` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/metadata_date_bench_or_chain_of_custody_record.csv` |
| 1 | `SQ-0021` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `metadata` | `medium_name` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/metadata_medium_name_bench_or_chain_of_custody_record.csv` |
| 1 | `SQ-0022` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `metadata` | `medium_lot` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/metadata_medium_lot_bench_or_chain_of_custody_record.csv` |
| 2 | `SQ-0023` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `metadata` | `temperature_c` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/metadata_temperature_c_temperature_or_incubator_log.csv` |
| 1 | `SQ-0024` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `metadata` | `mea_coupon_id` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/metadata_mea_coupon_id_supplier_or_build_record.pdf` |
| 1 | `SQ-0025` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `metadata` | `electrode_material` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/metadata_electrode_material_supplier_or_build_record.pdf` |
| 1 | `SQ-0026` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `metadata` | `laminin_or_peptide_density` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/metadata_laminin_or_peptide_density_supplier_or_build_record.pdf` |
| 1 | `SQ-0027` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `metadata` | `sterilization_or_aseptic_protocol` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/metadata_sterilization_or_aseptic_protocol_supplier_or_build_record.pdf` |
| 2 | `SQ-0028` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `initial` | `pH` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/initial_pH_initial_pH_meter_export_or_photo.csv` |
| 3 | `SQ-0029` | `B2_HA_osmolality_external` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `initial` | `osmolality` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/initial_osmolality_initial_mOsm_kg_osmometer_report_or_export.pdf` |
| 2 | `SQ-0030` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `initial` | `conductivity` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/initial_conductivity_initial_mS_cm_conductivity_meter_export_or_photo.csv` |
| 2 | `SQ-0031` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `final` | `pH` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/final_pH_final_pH_meter_export_or_photo.csv` |
| 3 | `SQ-0032` | `B2_HA_osmolality_external` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `final` | `osmolality` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/final_osmolality_final_mOsm_kg_osmometer_report_or_export.pdf` |
| 2 | `SQ-0033` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `final` | `conductivity` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/final_conductivity_final_mS_cm_conductivity_meter_export_or_photo.csv` |
| 2 | `SQ-0034` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `physical_inspection` | `visible_precipitate` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/physical_inspection_visible_precipitate_image_or_scoring_worksheet.png` |
| 2 | `SQ-0035` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `physical_inspection` | `visible_shedding` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/physical_inspection_visible_shedding_image_or_scoring_worksheet.png` |
| 2 | `SQ-0036` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `physical_inspection` | `swelling_fraction` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/physical_inspection_swelling_fraction_swelling_dimension_or_mass_worksheet.csv` |
| 2 | `SQ-0037` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `physical_inspection` | `delamination_score` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/physical_inspection_delamination_score_image_or_scoring_worksheet.png` |
| 2 | `SQ-0038` | `B1_HA_local_measurements` | NHI-PEDOT H-A | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | `physical_inspection` | `optical_transparency_fraction` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-no_coating_mea_control-R1-24h/physical_inspection_optical_transparency_fraction_image_or_scoring_worksheet.png` |
| 1 | `SQ-0039` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `metadata` | `date` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h/metadata_date_bench_or_chain_of_custody_record.csv` |
| 1 | `SQ-0040` | `B0_HA_setup_records` | NHI-PEDOT H-A | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `metadata` | `medium_name` | `awaiting_value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h/metadata_medium_name_bench_or_chain_of_custody_record.csv` |
| 0 | `-` | `-` | - | `-` | `-` | `-` | `-` | 132 additional rows in CSV. |

## Post-Fill Commands

```bash
python3 scripts/preflight_limina_local_capture.py --tasks data/limina_smoke_capture_tasks.csv --h-a-local data/nhi_pedot_h_a_smoke_local_capture_template.csv --h-a-outsource data/nhi_pedot_h_a_smoke_osmolality_outsource_template.csv --zrc-local data/zrc_nd_phase_a_smoke_local_capture_template.csv --zrc-outsource data/zrc_nd_phase_a_smoke_osmolality_outsource_template.csv --json-out data/limina_smoke_capture_preflight.json --report reports/limina_smoke_capture_preflight.md
```
```bash
python3 scripts/run_limina_smoke_rehearsal.py
```
```bash
python3 scripts/run_limina_iteration.py
```

## Boundary

This queue is execution scaffolding only. It cannot satisfy a material suitability claim without real source files, QC-clean rows, gate passes, and claim_ready=true.
