# LIMINA Smoke Source Values Sheet

This renders the consolidated sheet read by the source-value importer. It is not measured evidence.

**Status:** `smoke_source_values_sheet_ready`
**Rows:** 172
**Starter batch rows:** 19
**Filled values:** 0
**Rows with existing source files:** 0
**Import-ready rows:** 0
**Sheet:** `data/limina_smoke_source_values.csv`
**Starter batch:** `data/limina_smoke_source_values_starter_batch.csv`

## Recommended Rounds

| Round | Rows | Purpose |
| --- | ---: | --- |
| `R0_pipeline_debug_single_h_a_lead_24h` | 19 | One 19-field lead 24h run to prove raw-file intake, importer, apply, preflight, and rehearsal wiring. |
| `R1_h_a_local_and_records` | 85 | H-A records plus local pH, conductivity, temperature, imaging, swelling, and stability rows. |
| `R2_h_a_osmolality_external` | 10 | H-A osmometer report/export rows. |
| `R3_zrc_local_and_records` | 50 | Parallel ZRC-ND records and local/source-record rows. |
| `R4_zrc_osmolality_external` | 8 | Parallel ZRC-ND osmometer report/export rows. |

## Fill Contract

- The importer reads `queue_id`, `value`, `measured_at`, `operator_or_agent`, `instrument_id`, `source_file`, `notes`, and `apply`.
- `instrument_id` is required when `instrument_required=true`.
- `source_file` must point to the raw export, report, image, or worksheet, not this source-values sheet.

## Starter Rows

| Queue | Run | Field | Instrument required | Source file |
| --- | --- | --- | --- | --- |
| `SQ-0096` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `date` | `false` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_date_bench_or_chain_of_custody_record.csv` |
| `SQ-0097` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `medium_name` | `false` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_medium_name_bench_or_chain_of_custody_record.csv` |
| `SQ-0098` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `medium_lot` | `false` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_medium_lot_bench_or_chain_of_custody_record.csv` |
| `SQ-0099` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `temperature_c` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_temperature_c_temperature_or_incubator_log.csv` |
| `SQ-0100` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `mea_coupon_id` | `false` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_mea_coupon_id_supplier_or_build_record.pdf` |
| `SQ-0101` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `electrode_material` | `false` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_electrode_material_supplier_or_build_record.pdf` |
| `SQ-0102` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `laminin_or_peptide_density` | `false` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_laminin_or_peptide_density_supplier_or_build_record.pdf` |
| `SQ-0103` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `sterilization_or_aseptic_protocol` | `false` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_sterilization_or_aseptic_protocol_supplier_or_build_record.pdf` |
| `SQ-0104` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `pH` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/initial_pH_initial_pH_meter_export_or_photo.csv` |
| `SQ-0105` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `osmolality` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/initial_osmolality_initial_mOsm_kg_osmometer_report_or_export.pdf` |
| `SQ-0106` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `conductivity` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/initial_conductivity_initial_mS_cm_conductivity_meter_export_or_photo.csv` |
| `SQ-0107` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `pH` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/final_pH_final_pH_meter_export_or_photo.csv` |
| `SQ-0108` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `osmolality` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/final_osmolality_final_mOsm_kg_osmometer_report_or_export.pdf` |
| `SQ-0109` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `conductivity` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/final_conductivity_final_mS_cm_conductivity_meter_export_or_photo.csv` |
| `SQ-0110` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `visible_precipitate` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_visible_precipitate_image_or_scoring_worksheet.png` |
| `SQ-0111` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `visible_shedding` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_visible_shedding_image_or_scoring_worksheet.png` |
| `SQ-0112` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `swelling_fraction` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_swelling_fraction_swelling_dimension_or_mass_worksheet.csv` |
| `SQ-0113` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `delamination_score` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_delamination_score_image_or_scoring_worksheet.png` |
| `SQ-0114` | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | `optical_transparency_fraction` | `true` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_optical_transparency_fraction_image_or_scoring_worksheet.png` |

## Boundary

This is a fillable intake sheet for source-backed values only. It is not a raw source file and does not count as measured evidence.
