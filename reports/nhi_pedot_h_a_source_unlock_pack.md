# NHI-PEDOT H-A Source Unlock Pack

This groups H-A source-value rows into consolidated raw-file handoff bundles. It is not measured evidence.

**Status:** `h_a_source_unlock_pack_ready`
**Source-value rows:** 228
**Consolidated bundles:** 96
**Existing bundle files:** 0
**Missing bundle files:** 96

## Bundle Priorities

| Priority | Meaning | Bundles |
| ---: | --- | ---: |
| 1 | setup, custody, build, and incubation provenance | 36 |
| 2 | pH, osmolality, and conductivity exports | 36 |
| 3 | physical inspection, swelling, delamination, and transparency records | 24 |

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

## First 40 Bundles

| Priority | Run | Source class | Rows unlocked | Target fields | Consolidated source file |
| ---: | --- | --- | ---: | --- | --- |
| 1 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `bench_or_chain_of_custody_record` | 3 | `date;medium_lot;medium_name` | `data/source_files/bench_records/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h/h_a_metadata_chain_of_custody_record.csv` |
| 2 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `conductivity_meter_export_or_photo` | 2 | `conductivity` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h/h_a_conductivity_meter_export_or_photo.csv` |
| 3 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `image_or_scoring_worksheet` | 4 | `delamination_score;optical_transparency_fraction;visible_precipitate;visible_shedding` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h/h_a_physical_inspection_scoring_worksheet.csv` |
| 2 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `osmometer_report_or_export` | 2 | `osmolality` | `data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h/h_a_osmolality_report_or_export.pdf` |
| 2 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `pH_meter_export_or_photo` | 2 | `pH` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h/h_a_pH_meter_export_or_photo.csv` |
| 1 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `supplier_or_build_record` | 4 | `electrode_material;laminin_or_peptide_density;mea_coupon_id;sterilization_or_aseptic_protocol` | `data/source_files/build_records/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h/h_a_build_or_supplier_record.pdf` |
| 3 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `swelling_dimension_or_mass_worksheet` | 1 | `swelling_fraction` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h/h_a_swelling_dimension_or_mass_worksheet.csv` |
| 1 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | `temperature_or_incubator_log` | 1 | `temperature_c` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h/h_a_temperature_or_incubator_log.csv` |
| 1 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `bench_or_chain_of_custody_record` | 3 | `date;medium_lot;medium_name` | `data/source_files/bench_records/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h/h_a_metadata_chain_of_custody_record.csv` |
| 2 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `conductivity_meter_export_or_photo` | 2 | `conductivity` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h/h_a_conductivity_meter_export_or_photo.csv` |
| 3 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `image_or_scoring_worksheet` | 4 | `delamination_score;optical_transparency_fraction;visible_precipitate;visible_shedding` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h/h_a_physical_inspection_scoring_worksheet.csv` |
| 2 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `osmometer_report_or_export` | 2 | `osmolality` | `data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h/h_a_osmolality_report_or_export.pdf` |
| 2 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `pH_meter_export_or_photo` | 2 | `pH` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h/h_a_pH_meter_export_or_photo.csv` |
| 1 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `supplier_or_build_record` | 4 | `electrode_material;laminin_or_peptide_density;mea_coupon_id;sterilization_or_aseptic_protocol` | `data/source_files/build_records/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h/h_a_build_or_supplier_record.pdf` |
| 3 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `swelling_dimension_or_mass_worksheet` | 1 | `swelling_fraction` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h/h_a_swelling_dimension_or_mass_worksheet.csv` |
| 1 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | `temperature_or_incubator_log` | 1 | `temperature_c` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h/h_a_temperature_or_incubator_log.csv` |
| 1 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `bench_or_chain_of_custody_record` | 3 | `date;medium_lot;medium_name` | `data/source_files/bench_records/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h/h_a_metadata_chain_of_custody_record.csv` |
| 2 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `conductivity_meter_export_or_photo` | 2 | `conductivity` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h/h_a_conductivity_meter_export_or_photo.csv` |
| 3 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `image_or_scoring_worksheet` | 4 | `delamination_score;optical_transparency_fraction;visible_precipitate;visible_shedding` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h/h_a_physical_inspection_scoring_worksheet.csv` |
| 2 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `osmometer_report_or_export` | 2 | `osmolality` | `data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h/h_a_osmolality_report_or_export.pdf` |
| 2 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `pH_meter_export_or_photo` | 2 | `pH` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h/h_a_pH_meter_export_or_photo.csv` |
| 1 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `supplier_or_build_record` | 4 | `electrode_material;laminin_or_peptide_density;mea_coupon_id;sterilization_or_aseptic_protocol` | `data/source_files/build_records/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h/h_a_build_or_supplier_record.pdf` |
| 3 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `swelling_dimension_or_mass_worksheet` | 1 | `swelling_fraction` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h/h_a_swelling_dimension_or_mass_worksheet.csv` |
| 1 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | `temperature_or_incubator_log` | 1 | `temperature_c` | `data/source_files/full/h_a/NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h/h_a_temperature_or_incubator_log.csv` |
| 1 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `bench_or_chain_of_custody_record` | 3 | `date;medium_lot;medium_name` | `data/source_files/bench_records/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h/h_a_metadata_chain_of_custody_record.csv` |
| 2 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `conductivity_meter_export_or_photo` | 2 | `conductivity` | `data/source_files/full/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h/h_a_conductivity_meter_export_or_photo.csv` |
| 3 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `image_or_scoring_worksheet` | 4 | `delamination_score;optical_transparency_fraction;visible_precipitate;visible_shedding` | `data/source_files/full/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h/h_a_physical_inspection_scoring_worksheet.csv` |
| 2 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `osmometer_report_or_export` | 2 | `osmolality` | `data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports/NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h/h_a_osmolality_report_or_export.pdf` |
| 2 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `pH_meter_export_or_photo` | 2 | `pH` | `data/source_files/full/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h/h_a_pH_meter_export_or_photo.csv` |
| 1 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `supplier_or_build_record` | 4 | `electrode_material;laminin_or_peptide_density;mea_coupon_id;sterilization_or_aseptic_protocol` | `data/source_files/build_records/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h/h_a_build_or_supplier_record.pdf` |
| 3 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `swelling_dimension_or_mass_worksheet` | 1 | `swelling_fraction` | `data/source_files/full/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h/h_a_swelling_dimension_or_mass_worksheet.csv` |
| 1 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | `temperature_or_incubator_log` | 1 | `temperature_c` | `data/source_files/full/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h/h_a_temperature_or_incubator_log.csv` |
| 1 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `bench_or_chain_of_custody_record` | 3 | `date;medium_lot;medium_name` | `data/source_files/bench_records/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h/h_a_metadata_chain_of_custody_record.csv` |
| 2 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `conductivity_meter_export_or_photo` | 2 | `conductivity` | `data/source_files/full/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h/h_a_conductivity_meter_export_or_photo.csv` |
| 3 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `image_or_scoring_worksheet` | 4 | `delamination_score;optical_transparency_fraction;visible_precipitate;visible_shedding` | `data/source_files/full/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h/h_a_physical_inspection_scoring_worksheet.csv` |
| 2 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `osmometer_report_or_export` | 2 | `osmolality` | `data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports/NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h/h_a_osmolality_report_or_export.pdf` |
| 2 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `pH_meter_export_or_photo` | 2 | `pH` | `data/source_files/full/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h/h_a_pH_meter_export_or_photo.csv` |
| 1 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `supplier_or_build_record` | 4 | `electrode_material;laminin_or_peptide_density;mea_coupon_id;sterilization_or_aseptic_protocol` | `data/source_files/build_records/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h/h_a_build_or_supplier_record.pdf` |
| 3 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `swelling_dimension_or_mass_worksheet` | 1 | `swelling_fraction` | `data/source_files/full/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h/h_a_swelling_dimension_or_mass_worksheet.csv` |
| 1 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | `temperature_or_incubator_log` | 1 | `temperature_c` | `data/source_files/full/h_a/NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h/h_a_temperature_or_incubator_log.csv` |
| - | - | - | - | - | 56 additional bundles in CSV. |

## How To Use

1. Place the real raw export, report, image, worksheet, or chain-of-custody file at the consolidated source path.
2. Fill `value`, `measured_at`, `operator_or_agent`, and `instrument_id` when required in `data/nhi_pedot_h_a_source_values.csv`.
3. Cite the same consolidated source path for every listed target field that the raw file actually supports.
4. Run `python3 scripts/run_limina_iteration.py` and let the importer, QC, H-A gate, and claim audit decide what is real.

## Boundary

This handoff pack consolidates required source-file delivery paths only. It does not create measured evidence; importers and claim audit still require real files and real values.
