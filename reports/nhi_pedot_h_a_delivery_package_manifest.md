# NHI-PEDOT H-A Delivery Package Manifest

This manifest tracks the files needed to request real acellular H-A measurements. It is not measured evidence.

**Status:** `ready_to_send`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`

## Package Files

| ID | Required | Exists | Bytes | SHA256 | Role | Path |
| --- | --- | --- | ---: | --- | --- | --- |
| `service_request` | `true` | `true` | 6071 | `14d7277ad1e8dd61...` | Primary lab/cooperator request: matrix, deliverables, capabilities, stop rules, and rejection rules. | `reports/nhi_pedot_h_a_service_request.md` |
| `raw_measurement_template` | `true` | `true` | 19363 | `461bc7c75b03a261...` | The long-form CSV to fill with real instrument and inspection values. | `data/nhi_pedot_h_a_raw_measurements_template.csv` |
| `bundle_entry_sheet` | `true` | `true` | 78006 | `900bf5c472a6ae2a...` | Preferred compact CSV for returning one row per raw-file bundle; it expands into the source-values sheet after validation. | `data/nhi_pedot_h_a_bundle_entry_sheet.csv` |
| `bundle_entry_report` | `true` | `true` | 14450 | `9461cd24b403ac17...` | Human-readable instructions for filling the compact H-A bundle entry sheet. | `reports/nhi_pedot_h_a_bundle_entry_sheet.md` |
| `source_unlock_bundle_manifest` | `true` | `true` | 55071 | `afbe99df61e730fd...` | Machine-readable manifest mapping run_id/source_class bundles to consolidated source-file paths and target fields. | `data/nhi_pedot_h_a_source_unlock_bundle_manifest.csv` |
| `source_unlock_pack` | `true` | `true` | 12281 | `0ee3c70dbfc6b221...` | Human-readable overview of required H-A raw-file bundles and source classes. | `reports/nhi_pedot_h_a_source_unlock_pack.md` |
| `sentinel_packet` | `true` | `true` | 3391 | `614e63ace4f0c460...` | Recipe-locked H-A sentinel packet and sample handling context. | `reports/nhi_pedot_h_a_sentinel_packet.md` |
| `sample_manifest` | `true` | `true` | 13687 | `f9ef2f6783f34bfb...` | Sample-level manifest tying run_id to sample_event, article, timepoint, and readouts. | `data/nhi_pedot_h_a_sentinel_sample_manifest.csv` |
| `sample_labels` | `true` | `true` | 19897 | `06fafd2460820f07...` | Printable/transferable label rows with sample IDs, planned container IDs, article IDs, and handling notes. | `data/nhi_pedot_h_a_sample_labels.csv` |
| `chain_of_custody_csv` | `true` | `true` | 9320 | `250f8486ecca4206...` | Blank chain-of-custody transfer rows to complete during preparation, release, receipt, and return. | `data/nhi_pedot_h_a_chain_of_custody.csv` |
| `chain_of_custody_report` | `true` | `true` | 3959 | `caae2d348bdcf503...` | Human-readable sample handoff instructions, blank fields, and rejection rules. | `reports/nhi_pedot_h_a_chain_of_custody.md` |
| `sample_submission_pack` | `true` | `true` | 5872 | `c5d6ce3d89cfa7e1...` | Vendor-facing nonclinical sample-submission precheck, material disclosure, pre-ship questions, and shipping boundary. | `reports/nhi_pedot_h_a_sample_submission_pack.md` |
| `split_scope_plan` | `true` | `true` | 3145 | `5ab79c352248c1dc...` | Fallback execution plan for splitting media chemistry and coupon physical/imaging readouts across vendors. | `reports/nhi_pedot_h_a_split_scope_plan.md` |
| `split_scope_plan_csv` | `true` | `true` | 6892 | `1d0bd6ca8844067b...` | Machine-readable split-scope vendor pairings, field assignments, shared requirements, and decisions. | `data/nhi_pedot_h_a_split_scope_plan.csv` |
| `material_disclosure_csv` | `true` | `true` | 1858 | `9d2be57f0822e116...` | Machine-readable component disclosure checklist for sample submission and SDS readiness. | `data/nhi_pedot_h_a_material_disclosure.csv` |
| `bench_sheet` | `true` | `true` | 7103 | `4273e8690d386bbd...` | Operator-facing bench sheet with task order and stop criteria. | `reports/nhi_pedot_h_a_bench_sheet.md` |
| `minimum_checklist` | `true` | `true` | 3105 | `c2868593b7cea471...` | Compact checklist of claim-critical fields and current QC hotspots. | `reports/nhi_pedot_h_a_minimum_measurement_checklist.md` |
| `recipe_protocol` | `true` | `true` | 4980 | `c3b05c0991bbfe10...` | Recipe-specific ALG-LAM-PEDOT protocol handoff. | `reports/nhi_pedot_alg_lam_protocol.md` |
| `recipe_lock` | `true` | `true` | 3671 | `2cba9abebc5126ba...` | Machine-readable recipe lock that defines the active lead and controls. | `data/nhi_pedot_recipe_lock_v0_2.json` |
| `next_measurements` | `true` | `true` | 2586 | `3cb57c4162cabf07...` | Current recommended H-A measurement rows. | `reports/nhi_pedot_next_measurements.md` |

## Expected Return Files

| ID | Path | Acceptance |
| --- | --- | --- |
| `completed_raw_measurement_csv` | `data/nhi_pedot_h_a_raw_measurements_template.csv` | Same schema as the package template, with all requested real values and provenance fields filled. |
| `completed_bundle_entry_sheet` | `data/nhi_pedot_h_a_bundle_entry_sheet.csv` | Preferred compact return option: filled value_* columns, measured_at, operator_or_agent, instrument_id where required, source_file, and apply=yes for each completed raw-file bundle. |
| `instrument_exports` | `external_lab_exports/` | Original pH, osmolality, conductivity, chain-of-custody, build, and image/inspection files referenced by source_file. |
| `completed_chain_of_custody` | `data/nhi_pedot_h_a_chain_of_custody.csv` | Prepared/released/received fields, actual medium lot, coupon or well ID, condition on receipt, and transfer deviations filled for every returned sample row. |
| `deviation_log` | `reports/nhi_pedot_h_a_deviation_log.md` | Lists every deviation from recipe, timing, instrument, sample, medium, or storage assumptions. |

## Post-Return Verification

```bash
python3 scripts/render_nhi_pedot_h_a_vendor_return_intake.py
python3 scripts/apply_nhi_pedot_h_a_bundle_entry_sheet.py
python3 scripts/import_nhi_pedot_h_a_source_values.py
python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py
python3 scripts/qc_nhi_pedot_h_a_intake.py --strict-exit
python3 scripts/interpret_nhi_pedot_h_a_sentinel.py
python3 scripts/run_limina_iteration.py
```

## Boundary

This manifest only packages the measurement request. Suitability still requires real rows to pass H-A, H-B, H-C, long follow-up, and the final claim audit.
