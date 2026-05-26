# LIMINA Smoke Starter Batch Readiness

This audits the 19-row starter batch for import readiness. It is not measured evidence.

**Status:** `smoke_starter_batch_awaiting_values`
**Starter rows:** 19
**Ready for import:** 0
**Filled values:** 0
**Rows with existing source files:** 0
**Blocked rows:** 19

## Missing Items

| Missing item | Rows |
| --- | ---: |
| `instrument_id` | 12 |
| `measured_at` | 19 |
| `operator_or_agent` | 19 |
| `source_file_missing` | 19 |
| `value` | 19 |

## Starter Rows

| Queue | Field | Ready | Missing items | Source file |
| --- | --- | --- | --- | --- |
| `SQ-0096` | `date` | `false` | `measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_date_bench_or_chain_of_custody_record.csv` |
| `SQ-0097` | `medium_name` | `false` | `measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_medium_name_bench_or_chain_of_custody_record.csv` |
| `SQ-0098` | `medium_lot` | `false` | `measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_medium_lot_bench_or_chain_of_custody_record.csv` |
| `SQ-0099` | `temperature_c` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_temperature_c_temperature_or_incubator_log.csv` |
| `SQ-0100` | `mea_coupon_id` | `false` | `measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_mea_coupon_id_supplier_or_build_record.pdf` |
| `SQ-0101` | `electrode_material` | `false` | `measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_electrode_material_supplier_or_build_record.pdf` |
| `SQ-0102` | `laminin_or_peptide_density` | `false` | `measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_laminin_or_peptide_density_supplier_or_build_record.pdf` |
| `SQ-0103` | `sterilization_or_aseptic_protocol` | `false` | `measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_sterilization_or_aseptic_protocol_supplier_or_build_record.pdf` |
| `SQ-0104` | `pH` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/initial_pH_initial_pH_meter_export_or_photo.csv` |
| `SQ-0105` | `osmolality` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/initial_osmolality_initial_mOsm_kg_osmometer_report_or_export.pdf` |
| `SQ-0106` | `conductivity` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/initial_conductivity_initial_mS_cm_conductivity_meter_export_or_photo.csv` |
| `SQ-0107` | `pH` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/final_pH_final_pH_meter_export_or_photo.csv` |
| `SQ-0108` | `osmolality` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/final_osmolality_final_mOsm_kg_osmometer_report_or_export.pdf` |
| `SQ-0109` | `conductivity` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/final_conductivity_final_mS_cm_conductivity_meter_export_or_photo.csv` |
| `SQ-0110` | `visible_precipitate` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_visible_precipitate_image_or_scoring_worksheet.png` |
| `SQ-0111` | `visible_shedding` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_visible_shedding_image_or_scoring_worksheet.png` |
| `SQ-0112` | `swelling_fraction` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_swelling_fraction_swelling_dimension_or_mass_worksheet.csv` |
| `SQ-0113` | `delamination_score` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_delamination_score_image_or_scoring_worksheet.png` |
| `SQ-0114` | `optical_transparency_fraction` | `false` | `instrument_id;measured_at;operator_or_agent;source_file_missing;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_optical_transparency_fraction_image_or_scoring_worksheet.png` |

## When Ready

```bash
python3 scripts/run_limina_iteration.py
```

## Boundary

Starter readiness only checks whether rows can be imported. It is not measured evidence and cannot satisfy any material suitability claim.
