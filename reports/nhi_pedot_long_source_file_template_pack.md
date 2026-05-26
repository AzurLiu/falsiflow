# NHI-PEDOT long-duration Source File Template Pack

This pack provides source-class templates for real raw exports, reports, and worksheets. It is not measured evidence.

**Status:** `nhi_pedot_long_source_file_template_pack_ready`
**Source-value rows covered:** 4836
**Source-class templates:** 5
**Target source files:** 4836
**Template directory:** `data/limina_source_file_templates/nhi_long`

## Target Extensions

| Extension | Target files |
| --- | ---: |
| `.csv` | 3588 |
| `.png` | 1248 |

## Templates

| Source class | Rows | Template | Required source metadata |
| --- | ---: | --- | --- |
| `bench_or_chain_of_custody_record` | 1248 | `data/limina_source_file_templates/nhi_long/source_class_templates/bench_or_chain_of_custody_record.csv` | run_id or sample_id, operator, date, transfer or exposure event |
| `biological_assay_or_imaging_export` | 624 | `data/limina_source_file_templates/nhi_long/source_class_templates/biological_assay_or_imaging_export.csv` | run_id, culture model, assay date, operator or vendor, instrument_id or imaging/export method |
| `electrochemical_or_mea_export` | 2184 | `data/limina_source_file_templates/nhi_long/source_class_templates/electrochemical_or_mea_export.csv` | run_id, measurement date, instrument_id, channel/electrode mapping, and analysis method |
| `image_or_scoring_worksheet` | 624 | `data/limina_source_file_templates/nhi_long/source_class_templates/image_or_scoring_worksheet.csv` | run_id, imaging/scoring method, operator or vendor |
| `swelling_dimension_or_mass_worksheet` | 156 | `data/limina_source_file_templates/nhi_long/source_class_templates/swelling_dimension_or_mass_worksheet.csv` | run_id, pre/post measurement basis, method, operator |

## Boundary

Templates are outside allowed source-file roots and are never measured evidence. Only real files placed at target source_file paths can support measured rows.
