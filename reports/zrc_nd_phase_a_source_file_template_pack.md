# ZRC-ND Phase A Source File Template Pack

This pack provides source-class templates for real raw exports, reports, and worksheets. It is not measured evidence.

**Status:** `zrc_nd_phase_a_source_file_template_pack_ready`
**Source-value rows covered:** 304
**Source-class templates:** 8
**Target source files:** 304
**Template directory:** `data/limina_source_file_templates/zrc_phase_a`

## Target Extensions

| Extension | Target files |
| --- | ---: |
| `.csv` | 280 |
| `.pdf` | 16 |
| `.png` | 8 |

## Templates

| Source class | Rows | Template | Required source metadata |
| --- | ---: | --- | --- |
| `bench_or_chain_of_custody_record` | 104 | `data/limina_source_file_templates/zrc_phase_a/source_class_templates/bench_or_chain_of_custody_record.csv` | run_id or sample_id, operator, date, transfer or exposure event |
| `biochemical_or_plate_reader_export` | 112 | `data/limina_source_file_templates/zrc_phase_a/source_class_templates/biochemical_or_plate_reader_export.csv` | run_id, analyte, assay date, instrument_id or vendor report id, calibration/standard curve record |
| `conductivity_meter_export_or_photo` | 16 | `data/limina_source_file_templates/zrc_phase_a/source_class_templates/conductivity_meter_export_or_photo.csv` | run_id, measurement date, instrument_id or standard-check record |
| `image_or_scoring_worksheet` | 8 | `data/limina_source_file_templates/zrc_phase_a/source_class_templates/image_or_scoring_worksheet.csv` | run_id, imaging/scoring method, operator or vendor |
| `osmometer_report_or_export` | 16 | `data/limina_source_file_templates/zrc_phase_a/source_class_templates/osmometer_report_or_export.csv` | run_id, mOsm/kg value, vendor or osmometer identifier |
| `pH_meter_export_or_photo` | 16 | `data/limina_source_file_templates/zrc_phase_a/source_class_templates/pH_meter_export_or_photo.csv` | run_id, measurement date, instrument_id or calibration record |
| `pressure_flow_or_resistance_export` | 24 | `data/limina_source_file_templates/zrc_phase_a/source_class_templates/pressure_flow_or_resistance_export.csv` | run_id, flow/pressure method, instrument_id, time window, calculation method |
| `temperature_or_incubator_log` | 8 | `data/limina_source_file_templates/zrc_phase_a/source_class_templates/temperature_or_incubator_log.csv` | run_id or batch window, date/time, temperature source |

## Boundary

Templates are outside allowed source-file roots and are never measured evidence. Only real files placed at target source_file paths can support measured rows.
