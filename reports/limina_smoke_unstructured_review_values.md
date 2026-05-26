# LIMINA Smoke Unstructured Review Values

This renders fillable source-value rows for unstructured starter source files. It is not measured evidence.

**Status:** `smoke_unstructured_review_values_waiting_for_source_files`
**Review rows:** 10
**Ready source rows:** 0
**Missing source rows:** 10
**Invalid source rows:** 0
**Filled values:** 0
**Import-ready rows:** 0
**CSV:** `data/limina_smoke_unstructured_review_values.csv`

## Fill Contract

- Fill only values read from real existing PDF/image/other source files listed in `source_file`.
- Keep `source_file` pointed at the raw source file, not this review-values sheet.
- The importer reads only the accepted source-value columns; context columns are operator guidance.

```text
queue_id,run_id,sample_event,target_field,value,measured_at,operator_or_agent,instrument_id,source_file,notes,apply
```

## Review Rows

| Queue | Field | Source status | Review status | Missing items | Source file |
| --- | --- | --- | --- | --- | --- |
| `SQ-0100` | `mea_coupon_id` | `missing_source_file` | `awaiting_source_file` | `measured_at;operator_or_agent;source_missing_source_file;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_mea_coupon_id_supplier_or_build_record.pdf` |
| `SQ-0101` | `electrode_material` | `missing_source_file` | `awaiting_source_file` | `measured_at;operator_or_agent;source_missing_source_file;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_electrode_material_supplier_or_build_record.pdf` |
| `SQ-0102` | `laminin_or_peptide_density` | `missing_source_file` | `awaiting_source_file` | `measured_at;operator_or_agent;source_missing_source_file;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_laminin_or_peptide_density_supplier_or_build_record.pdf` |
| `SQ-0103` | `sterilization_or_aseptic_protocol` | `missing_source_file` | `awaiting_source_file` | `measured_at;operator_or_agent;source_missing_source_file;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_sterilization_or_aseptic_protocol_supplier_or_build_record.pdf` |
| `SQ-0105` | `osmolality` | `missing_source_file` | `awaiting_source_file` | `instrument_id;measured_at;operator_or_agent;source_missing_source_file;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/initial_osmolality_initial_mOsm_kg_osmometer_report_or_export.pdf` |
| `SQ-0108` | `osmolality` | `missing_source_file` | `awaiting_source_file` | `instrument_id;measured_at;operator_or_agent;source_missing_source_file;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/final_osmolality_final_mOsm_kg_osmometer_report_or_export.pdf` |
| `SQ-0110` | `visible_precipitate` | `missing_source_file` | `awaiting_source_file` | `instrument_id;measured_at;operator_or_agent;source_missing_source_file;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_visible_precipitate_image_or_scoring_worksheet.png` |
| `SQ-0111` | `visible_shedding` | `missing_source_file` | `awaiting_source_file` | `instrument_id;measured_at;operator_or_agent;source_missing_source_file;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_visible_shedding_image_or_scoring_worksheet.png` |
| `SQ-0113` | `delamination_score` | `missing_source_file` | `awaiting_source_file` | `instrument_id;measured_at;operator_or_agent;source_missing_source_file;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_delamination_score_image_or_scoring_worksheet.png` |
| `SQ-0114` | `optical_transparency_fraction` | `missing_source_file` | `awaiting_source_file` | `instrument_id;measured_at;operator_or_agent;source_missing_source_file;value` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_optical_transparency_fraction_image_or_scoring_worksheet.png` |

## Boundary

This review-values sheet is a fillable sidecar for manually extracted values from existing PDF/image/other unstructured source files. It is not measured evidence and cannot support a claim unless the cited raw source file and filled values pass the importer, preflight, merge/QC, gate evaluation, and claim audit.
