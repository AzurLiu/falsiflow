# NHI-PEDOT H-A Bundle Entry Sheet

This is a consolidated fillable sheet for H-A raw-file bundles. It is not measured evidence.

**Status:** `h_a_bundle_entry_sheet_ready`
**Bundle rows:** 96
**Filled bundle rows:** 0
**Ready to apply:** 0
**Rows with existing source files:** 0
**CSV:** `data/nhi_pedot_h_a_bundle_entry_sheet.csv`

## Source Classes

| Source class | Bundles |
| --- | ---: |
| `bench_or_chain_of_custody_record` | 12 |
| `conductivity_meter_export_or_photo` | 12 |
| `image_or_scoring_worksheet` | 12 |
| `osmometer_report_or_export` | 12 |
| `pH_meter_export_or_photo` | 12 |
| `supplier_or_build_record` | 12 |
| `swelling_dimension_or_mass_worksheet` | 12 |
| `temperature_or_incubator_log` | 12 |

## How To Use

- Fill the relevant `value_*` columns for a bundle from the real raw file, report, image, or worksheet.
- Fill `measured_at`, `operator_or_agent`, `instrument_id` when required, and `source_file`.
- Put the actual raw source file at `source_file`, then set `apply=yes` for that bundle.

## After Filling

```bash
python3 scripts/apply_nhi_pedot_h_a_bundle_entry_sheet.py
python3 scripts/run_limina_iteration.py
```

## First 40 Bundles

| Bundle | Run | Source class | Status | Missing items | Value columns |
| --- | --- | --- | --- | --- | --- |
| `H-A-BUNDLE-001` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `bench_or_chain_of_custody_record` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;value_date;value_medium_name;value_medium_lot;source_file_missing` | `value_date;value_medium_name;value_medium_lot` |
| `H-A-BUNDLE-002` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `conductivity_meter_export_or_photo` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_conductivity_initial_mS_cm;value_conductivity_final_mS_cm;source_file_missing` | `value_conductivity_initial_mS_cm;value_conductivity_final_mS_cm` |
| `H-A-BUNDLE-003` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `image_or_scoring_worksheet` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_visible_precipitate;value_visible_shedding;value_delamination_score;value_optical_transparency_fraction;source_file_missing` | `value_visible_precipitate;value_visible_shedding;value_delamination_score;value_optical_transparency_fraction` |
| `H-A-BUNDLE-004` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `osmometer_report_or_export` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_osmolality_initial_mOsm_kg;value_osmolality_final_mOsm_kg;source_file_missing` | `value_osmolality_initial_mOsm_kg;value_osmolality_final_mOsm_kg` |
| `H-A-BUNDLE-005` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `pH_meter_export_or_photo` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_pH_initial;value_pH_final;source_file_missing` | `value_pH_initial;value_pH_final` |
| `H-A-BUNDLE-006` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `supplier_or_build_record` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;value_mea_coupon_id;value_electrode_material;value_laminin_or_peptide_density;value_sterilization_or_aseptic_protocol;source_file_missing` | `value_mea_coupon_id;value_electrode_material;value_laminin_or_peptide_density;value_sterilization_or_aseptic_protocol` |
| `H-A-BUNDLE-007` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `swelling_dimension_or_mass_worksheet` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_swelling_fraction;source_file_missing` | `value_swelling_fraction` |
| `H-A-BUNDLE-008` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `temperature_or_incubator_log` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_temperature_c;source_file_missing` | `value_temperature_c` |
| `H-A-BUNDLE-009` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `bench_or_chain_of_custody_record` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;value_date;value_medium_name;value_medium_lot;source_file_missing` | `value_date;value_medium_name;value_medium_lot` |
| `H-A-BUNDLE-010` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `conductivity_meter_export_or_photo` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_conductivity_initial_mS_cm;value_conductivity_final_mS_cm;source_file_missing` | `value_conductivity_initial_mS_cm;value_conductivity_final_mS_cm` |
| `H-A-BUNDLE-011` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `image_or_scoring_worksheet` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_visible_precipitate;value_visible_shedding;value_delamination_score;value_optical_transparency_fraction;source_file_missing` | `value_visible_precipitate;value_visible_shedding;value_delamination_score;value_optical_transparency_fraction` |
| `H-A-BUNDLE-012` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `osmometer_report_or_export` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_osmolality_initial_mOsm_kg;value_osmolality_final_mOsm_kg;source_file_missing` | `value_osmolality_initial_mOsm_kg;value_osmolality_final_mOsm_kg` |
| `H-A-BUNDLE-013` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `pH_meter_export_or_photo` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_pH_initial;value_pH_final;source_file_missing` | `value_pH_initial;value_pH_final` |
| `H-A-BUNDLE-014` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `supplier_or_build_record` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;value_mea_coupon_id;value_electrode_material;value_laminin_or_peptide_density;value_sterilization_or_aseptic_protocol;source_file_missing` | `value_mea_coupon_id;value_electrode_material;value_laminin_or_peptide_density;value_sterilization_or_aseptic_protocol` |
| `H-A-BUNDLE-015` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `swelling_dimension_or_mass_worksheet` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_swelling_fraction;source_file_missing` | `value_swelling_fraction` |
| `H-A-BUNDLE-016` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `temperature_or_incubator_log` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_temperature_c;source_file_missing` | `value_temperature_c` |
| `H-A-BUNDLE-017` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `bench_or_chain_of_custody_record` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;value_date;value_medium_name;value_medium_lot;source_file_missing` | `value_date;value_medium_name;value_medium_lot` |
| `H-A-BUNDLE-018` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `conductivity_meter_export_or_photo` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_conductivity_initial_mS_cm;value_conductivity_final_mS_cm;source_file_missing` | `value_conductivity_initial_mS_cm;value_conductivity_final_mS_cm` |
| `H-A-BUNDLE-019` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `image_or_scoring_worksheet` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_visible_precipitate;value_visible_shedding;value_delamination_score;value_optical_transparency_fraction;source_file_missing` | `value_visible_precipitate;value_visible_shedding;value_delamination_score;value_optical_transparency_fraction` |
| `H-A-BUNDLE-020` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `osmometer_report_or_export` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_osmolality_initial_mOsm_kg;value_osmolality_final_mOsm_kg;source_file_missing` | `value_osmolality_initial_mOsm_kg;value_osmolality_final_mOsm_kg` |
| `H-A-BUNDLE-021` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `pH_meter_export_or_photo` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_pH_initial;value_pH_final;source_file_missing` | `value_pH_initial;value_pH_final` |
| `H-A-BUNDLE-022` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `supplier_or_build_record` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;value_mea_coupon_id;value_electrode_material;value_laminin_or_peptide_density;value_sterilization_or_aseptic_protocol;source_file_missing` | `value_mea_coupon_id;value_electrode_material;value_laminin_or_peptide_density;value_sterilization_or_aseptic_protocol` |
| `H-A-BUNDLE-023` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `swelling_dimension_or_mass_worksheet` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_swelling_fraction;source_file_missing` | `value_swelling_fraction` |
| `H-A-BUNDLE-024` | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `temperature_or_incubator_log` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_temperature_c;source_file_missing` | `value_temperature_c` |
| `H-A-BUNDLE-025` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `bench_or_chain_of_custody_record` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;value_date;value_medium_name;value_medium_lot;source_file_missing` | `value_date;value_medium_name;value_medium_lot` |
| `H-A-BUNDLE-026` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `conductivity_meter_export_or_photo` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_conductivity_initial_mS_cm;value_conductivity_final_mS_cm;source_file_missing` | `value_conductivity_initial_mS_cm;value_conductivity_final_mS_cm` |
| `H-A-BUNDLE-027` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `image_or_scoring_worksheet` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_visible_precipitate;value_visible_shedding;value_delamination_score;value_optical_transparency_fraction;source_file_missing` | `value_visible_precipitate;value_visible_shedding;value_delamination_score;value_optical_transparency_fraction` |
| `H-A-BUNDLE-028` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `osmometer_report_or_export` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_osmolality_initial_mOsm_kg;value_osmolality_final_mOsm_kg;source_file_missing` | `value_osmolality_initial_mOsm_kg;value_osmolality_final_mOsm_kg` |
| `H-A-BUNDLE-029` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `pH_meter_export_or_photo` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_pH_initial;value_pH_final;source_file_missing` | `value_pH_initial;value_pH_final` |
| `H-A-BUNDLE-030` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `supplier_or_build_record` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;value_mea_coupon_id;value_electrode_material;value_laminin_or_peptide_density;value_sterilization_or_aseptic_protocol;source_file_missing` | `value_mea_coupon_id;value_electrode_material;value_laminin_or_peptide_density;value_sterilization_or_aseptic_protocol` |
| `H-A-BUNDLE-031` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `swelling_dimension_or_mass_worksheet` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_swelling_fraction;source_file_missing` | `value_swelling_fraction` |
| `H-A-BUNDLE-032` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `temperature_or_incubator_log` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_temperature_c;source_file_missing` | `value_temperature_c` |
| `H-A-BUNDLE-033` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `bench_or_chain_of_custody_record` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;value_date;value_medium_name;value_medium_lot;source_file_missing` | `value_date;value_medium_name;value_medium_lot` |
| `H-A-BUNDLE-034` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `conductivity_meter_export_or_photo` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_conductivity_initial_mS_cm;value_conductivity_final_mS_cm;source_file_missing` | `value_conductivity_initial_mS_cm;value_conductivity_final_mS_cm` |
| `H-A-BUNDLE-035` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `image_or_scoring_worksheet` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_visible_precipitate;value_visible_shedding;value_delamination_score;value_optical_transparency_fraction;source_file_missing` | `value_visible_precipitate;value_visible_shedding;value_delamination_score;value_optical_transparency_fraction` |
| `H-A-BUNDLE-036` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `osmometer_report_or_export` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_osmolality_initial_mOsm_kg;value_osmolality_final_mOsm_kg;source_file_missing` | `value_osmolality_initial_mOsm_kg;value_osmolality_final_mOsm_kg` |
| `H-A-BUNDLE-037` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `pH_meter_export_or_photo` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_pH_initial;value_pH_final;source_file_missing` | `value_pH_initial;value_pH_final` |
| `H-A-BUNDLE-038` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `supplier_or_build_record` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;value_mea_coupon_id;value_electrode_material;value_laminin_or_peptide_density;value_sterilization_or_aseptic_protocol;source_file_missing` | `value_mea_coupon_id;value_electrode_material;value_laminin_or_peptide_density;value_sterilization_or_aseptic_protocol` |
| `H-A-BUNDLE-039` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `swelling_dimension_or_mass_worksheet` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_swelling_fraction;source_file_missing` | `value_swelling_fraction` |
| `H-A-BUNDLE-040` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `temperature_or_incubator_log` | `awaiting_bundle_entry` | `measured_at;operator_or_agent;instrument_id;value_temperature_c;source_file_missing` | `value_temperature_c` |
| `-` | `-` | `-` | `-` | `-` | 56 additional bundles in CSV. |

## Boundary

This sheet only consolidates source-value entry across H-A bundles. It is not measured evidence; the apply step, source-value importer, merge, QC, gates, and claim audit still control evidence status.
