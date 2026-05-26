# NHI-PEDOT H-B/H-C Source File Template Pack

This pack provides source-class templates for real raw exports, reports, and worksheets. It is not measured evidence.

**Status:** `nhi_pedot_forward_source_file_template_pack_ready`
**Source-value rows covered:** 592
**Source-class templates:** 6
**Target source files:** 592
**Template directory:** `data/limina_source_file_templates/nhi_forward`

## Target Extensions

| Extension | Target files |
| --- | ---: |
| `.csv` | 504 |
| `.png` | 88 |

## Templates

| Source class | Rows | Template | Required source metadata |
| --- | ---: | --- | --- |
| `bench_or_chain_of_custody_record` | 368 | `data/limina_source_file_templates/nhi_forward/source_class_templates/bench_or_chain_of_custody_record.csv` | run_id or sample_id, operator, date, transfer or exposure event |
| `biological_assay_or_imaging_export` | 64 | `data/limina_source_file_templates/nhi_forward/source_class_templates/biological_assay_or_imaging_export.csv` | run_id, culture model, assay date, operator or vendor, instrument_id or imaging/export method |
| `electrochemical_or_mea_export` | 96 | `data/limina_source_file_templates/nhi_forward/source_class_templates/electrochemical_or_mea_export.csv` | run_id, measurement date, instrument_id, channel/electrode mapping, and analysis method |
| `image_or_scoring_worksheet` | 24 | `data/limina_source_file_templates/nhi_forward/source_class_templates/image_or_scoring_worksheet.csv` | run_id, imaging/scoring method, operator or vendor |
| `swelling_dimension_or_mass_worksheet` | 12 | `data/limina_source_file_templates/nhi_forward/source_class_templates/swelling_dimension_or_mass_worksheet.csv` | run_id, pre/post measurement basis, method, operator |
| `temperature_or_incubator_log` | 28 | `data/limina_source_file_templates/nhi_forward/source_class_templates/temperature_or_incubator_log.csv` | run_id or batch window, date/time, temperature source |

## Boundary

Templates are outside allowed source-file roots and are never measured evidence. Only real files placed at target source_file paths can support measured rows.
