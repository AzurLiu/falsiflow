# NHI-PEDOT H-A Source File Template Pack

This pack provides source-class templates for real raw exports, reports, and worksheets. It is not measured evidence.

**Status:** `nhi_pedot_h_a_source_file_template_pack_ready`
**Source-value rows covered:** 228
**Source-class templates:** 8
**Target source files:** 228
**Template directory:** `data/limina_source_file_templates/h_a`

## Target Extensions

| Extension | Target files |
| --- | ---: |
| `.csv` | 108 |
| `.pdf` | 72 |
| `.png` | 48 |

## Templates

| Source class | Rows | Template | Required source metadata |
| --- | ---: | --- | --- |
| `bench_or_chain_of_custody_record` | 36 | `data/limina_source_file_templates/h_a/source_class_templates/bench_or_chain_of_custody_record.csv` | run_id or sample_id, operator, date, transfer or exposure event |
| `conductivity_meter_export_or_photo` | 24 | `data/limina_source_file_templates/h_a/source_class_templates/conductivity_meter_export_or_photo.csv` | run_id, measurement date, instrument_id or standard-check record |
| `image_or_scoring_worksheet` | 48 | `data/limina_source_file_templates/h_a/source_class_templates/image_or_scoring_worksheet.csv` | run_id, imaging/scoring method, operator or vendor |
| `osmometer_report_or_export` | 24 | `data/limina_source_file_templates/h_a/source_class_templates/osmometer_report_or_export.csv` | run_id, mOsm/kg value, vendor or osmometer identifier |
| `pH_meter_export_or_photo` | 24 | `data/limina_source_file_templates/h_a/source_class_templates/pH_meter_export_or_photo.csv` | run_id, measurement date, instrument_id or calibration record |
| `supplier_or_build_record` | 48 | `data/limina_source_file_templates/h_a/source_class_templates/supplier_or_build_record.csv` | lot, recipe, CoA, label, or build identifier |
| `swelling_dimension_or_mass_worksheet` | 12 | `data/limina_source_file_templates/h_a/source_class_templates/swelling_dimension_or_mass_worksheet.csv` | run_id, pre/post measurement basis, method, operator |
| `temperature_or_incubator_log` | 12 | `data/limina_source_file_templates/h_a/source_class_templates/temperature_or_incubator_log.csv` | run_id or batch window, date/time, temperature source |

## Boundary

Templates are outside allowed source-file roots and are never measured evidence. Only real files placed at target source_file paths can support measured rows.
