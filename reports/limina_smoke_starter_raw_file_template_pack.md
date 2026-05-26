# LIMINA Smoke Starter Raw File Template Pack

This pack provides source-class CSV templates for the 19-row starter batch. It is not measured evidence.

**Status:** `smoke_starter_raw_file_template_pack_ready`
**Starter rows covered:** 19
**Source-class templates:** 8
**Template directory:** `data/limina_smoke_starter_raw_file_templates`

## Target Extensions

| Extension | Starter rows |
| --- | ---: |
| `.csv` | 9 |
| `.pdf` | 6 |
| `.png` | 4 |

## Templates

| Source class | Rows | Template | Required source metadata |
| --- | ---: | --- | --- |
| `bench_or_chain_of_custody_record` | 3 | `data/limina_smoke_starter_raw_file_templates/source_class_templates/bench_or_chain_of_custody_record.csv` | run_id or sample_id, operator, date, transfer or exposure event |
| `conductivity_meter_export_or_photo` | 2 | `data/limina_smoke_starter_raw_file_templates/source_class_templates/conductivity_meter_export_or_photo.csv` | run_id, measurement date, instrument_id or standard-check record |
| `image_or_scoring_worksheet` | 4 | `data/limina_smoke_starter_raw_file_templates/source_class_templates/image_or_scoring_worksheet.csv` | run_id, imaging/scoring method, operator or vendor |
| `osmometer_report_or_export` | 2 | `data/limina_smoke_starter_raw_file_templates/source_class_templates/osmometer_report_or_export.csv` | run_id, mOsm/kg value, vendor or osmometer identifier |
| `pH_meter_export_or_photo` | 2 | `data/limina_smoke_starter_raw_file_templates/source_class_templates/pH_meter_export_or_photo.csv` | run_id, measurement date, instrument_id or calibration record |
| `supplier_or_build_record` | 4 | `data/limina_smoke_starter_raw_file_templates/source_class_templates/supplier_or_build_record.csv` | lot, recipe, CoA, label, or build identifier |
| `swelling_dimension_or_mass_worksheet` | 1 | `data/limina_smoke_starter_raw_file_templates/source_class_templates/swelling_dimension_or_mass_worksheet.csv` | run_id, pre/post measurement basis, method, operator |
| `temperature_or_incubator_log` | 1 | `data/limina_smoke_starter_raw_file_templates/source_class_templates/temperature_or_incubator_log.csv` | run_id or batch window, date/time, temperature source |

## Boundary

Templates are outside allowed source-file roots and are never measured evidence. Only real files placed at the target source_file paths can support a measured row.
