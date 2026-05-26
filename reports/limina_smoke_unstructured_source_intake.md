# LIMINA Smoke Unstructured Source Intake

This routes PDF/image/other non-CSV starter source files for value extraction. It is not measured evidence.

**Status:** `smoke_unstructured_source_intake_waiting_for_files`
**Unstructured plan rows:** 10
**Existing unstructured files:** 0
**Ready for value extraction:** 0
**Invalid source files:** 0
**Missing source files:** 10
**CSV:** `data/limina_smoke_unstructured_source_intake.csv`

## Rows

| Queue | Field | Source class | Status | Validation | Source file |
| --- | --- | --- | --- | --- | --- |
| `SQ-0100` | `mea_coupon_id` | `supplier_or_build_record` | `missing_source_file` | `not_run_missing_file` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_mea_coupon_id_supplier_or_build_record.pdf` |
| `SQ-0101` | `electrode_material` | `supplier_or_build_record` | `missing_source_file` | `not_run_missing_file` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_electrode_material_supplier_or_build_record.pdf` |
| `SQ-0102` | `laminin_or_peptide_density` | `supplier_or_build_record` | `missing_source_file` | `not_run_missing_file` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_laminin_or_peptide_density_supplier_or_build_record.pdf` |
| `SQ-0103` | `sterilization_or_aseptic_protocol` | `supplier_or_build_record` | `missing_source_file` | `not_run_missing_file` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/metadata_sterilization_or_aseptic_protocol_supplier_or_build_record.pdf` |
| `SQ-0105` | `osmolality` | `osmometer_report_or_export` | `missing_source_file` | `not_run_missing_file` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/initial_osmolality_initial_mOsm_kg_osmometer_report_or_export.pdf` |
| `SQ-0108` | `osmolality` | `osmometer_report_or_export` | `missing_source_file` | `not_run_missing_file` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/final_osmolality_final_mOsm_kg_osmometer_report_or_export.pdf` |
| `SQ-0110` | `visible_precipitate` | `image_or_scoring_worksheet` | `missing_source_file` | `not_run_missing_file` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_visible_precipitate_image_or_scoring_worksheet.png` |
| `SQ-0111` | `visible_shedding` | `image_or_scoring_worksheet` | `missing_source_file` | `not_run_missing_file` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_visible_shedding_image_or_scoring_worksheet.png` |
| `SQ-0113` | `delamination_score` | `image_or_scoring_worksheet` | `missing_source_file` | `not_run_missing_file` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_delamination_score_image_or_scoring_worksheet.png` |
| `SQ-0114` | `optical_transparency_fraction` | `image_or_scoring_worksheet` | `missing_source_file` | `not_run_missing_file` | `data/source_files/smoke/h_a/NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h/physical_inspection_optical_transparency_fraction_image_or_scoring_worksheet.png` |

## Extraction Contract

- For PDF reports, read or OCR the real report and write the measured value to a source-value sidecar.
- For images, score the image or use the image-analysis worksheet, then write the scored value to a source-value sidecar.
- The sidecar must cite the raw PDF/image as `source_file`; the sidecar itself is never evidence.

## Boundary

This intake hashes and routes unstructured source files only. It does not extract or create measured values; value rows must still pass the source-value importer, preflight, merge/QC, gate evaluation, and claim audit.
