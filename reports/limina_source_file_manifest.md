# LIMINA Source-File Manifest

This manifest defines where auditable source files must live before local/outsource capture rows can pass preflight.

**Status:** `source_file_manifest_ready`
**Allowed roots:** 12
**Expected source classes:** 12

## Allowed Roots

| Root | Path | Scope | Purpose |
| --- | --- | --- | --- |
| `local_h_a_full` | `data/source_files/full/h_a` | NHI-PEDOT H-A full local capture | Local instrument exports, photos, worksheets, calibration logs, and bench records for the full H-A matrix. |
| `local_zrc_full` | `data/source_files/full/zrc_nd_phase_a` | ZRC-ND Phase A full local capture | Local records and instrument outputs for the full ZRC-ND Phase A matrix. |
| `local_nhi_forward_full` | `data/source_files/full/nhi_pedot_forward` | NHI-PEDOT H-B/H-C full local capture | Local instrument exports, images, worksheets, and biological assay records for NHI-PEDOT H-B/H-C coupon gates. |
| `local_nhi_long_full` | `data/source_files/full/nhi_pedot_long` | NHI-PEDOT long-duration full local capture | Long-duration MEA, neural health, stimulus-recovery, imaging, and material-integrity records for NHI-PEDOT. |
| `local_zrc_bio_full` | `data/source_files/full/zrc_nd_bio` | ZRC-ND biological follow-up full local capture | Biological assay records, imaging, MEA outputs, and worksheets for ZRC-ND conditioned-medium follow-up gates. |
| `smoke_h_a` | `data/source_files/smoke/h_a` | NHI-PEDOT H-A smoke capture | Minimal source files for the smoke-tranche H-A pipeline rehearsal. |
| `smoke_zrc` | `data/source_files/smoke/zrc_nd_phase_a` | ZRC-ND Phase A smoke capture | Minimal source files for the smoke-tranche ZRC-ND pipeline rehearsal. |
| `calibration_logs` | `data/source_files/calibration_logs` | shared measurement provenance | Calibration or standard-check files referenced by pH, conductivity, temperature, osmometer, image, mass, or dimension records. |
| `bench_records` | `data/source_files/bench_records` | shared local capture | Bench logs, pipetting worksheets, chain-of-custody exports, and operator worksheets. |
| `build_records` | `data/source_files/build_records` | supplier/build provenance | Recipe records, supplier CoAs, sample labels, coating logs, and build sheets. |
| `h_a_vendor_exports` | `data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports` | NHI-PEDOT H-A vendor/cooperator returns | Original external lab exports, reports, images, and worksheets referenced by returned H-A rows. |
| `zrc_vendor_exports` | `data/zrc_nd_phase_a_vendor_return_inbox/external_lab_exports` | ZRC-ND Phase A vendor/cooperator returns | Original external lab exports, reports, images, and worksheets referenced by returned ZRC-ND rows. |

## Source Classes

| Source class | Task signals | Required metadata | Recommended roots |
| --- | --- | --- | --- |
| `pH_meter_export_or_photo` | `pH,pH_initial,pH_final` | run_id, measurement date, instrument_id or calibration record | `local_h_a_full;local_nhi_forward_full;local_nhi_long_full;smoke_h_a;calibration_logs;h_a_vendor_exports;zrc_vendor_exports` |
| `conductivity_meter_export_or_photo` | `conductivity,conductivity_initial_mS_cm,conductivity_final_mS_cm` | run_id, measurement date, instrument_id or standard-check record | `local_h_a_full;local_nhi_forward_full;local_nhi_long_full;smoke_h_a;calibration_logs;h_a_vendor_exports;zrc_vendor_exports` |
| `osmometer_report_or_export` | `osmolality,osmolality_initial_mOsm_kg,osmolality_final_mOsm_kg` | run_id, mOsm/kg value, vendor or osmometer identifier | `h_a_vendor_exports;zrc_vendor_exports;local_h_a_full;local_nhi_forward_full;local_nhi_long_full;smoke_h_a;smoke_zrc;calibration_logs` |
| `temperature_or_incubator_log` | `temperature_c` | run_id or batch window, date/time, temperature source | `local_h_a_full;local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;smoke_h_a;bench_records;h_a_vendor_exports;zrc_vendor_exports` |
| `image_or_scoring_worksheet` | `visible_precipitate,visible_shedding,delamination_score,optical_transparency_fraction` | run_id, imaging/scoring method, operator or vendor | `local_h_a_full;local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;smoke_h_a;smoke_zrc;bench_records;h_a_vendor_exports;zrc_vendor_exports` |
| `swelling_dimension_or_mass_worksheet` | `swelling_fraction,membrane_area_cm2,initial_volume_ml` | run_id, pre/post measurement basis, method, operator | `local_h_a_full;local_nhi_forward_full;local_nhi_long_full;smoke_h_a;smoke_zrc;bench_records;h_a_vendor_exports;zrc_vendor_exports` |
| `bench_or_chain_of_custody_record` | `date,medium_name,medium_lot,operator_or_agent,exposure_time_h` | run_id or sample_id, operator, date, transfer or exposure event | `bench_records;build_records;local_h_a_full;local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;smoke_h_a;smoke_zrc;h_a_vendor_exports;zrc_vendor_exports` |
| `supplier_or_build_record` | `membrane_lot,prefilter_lot,electrode_material,laminin_or_peptide_density,sterilization_or_aseptic_protocol` | lot, recipe, CoA, label, or build identifier | `build_records;bench_records;local_zrc_full;local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;smoke_zrc;h_a_vendor_exports;zrc_vendor_exports` |
| `electrochemical_or_mea_export` | `eis_1khz,charge_storage_capacity,spike_rate,burst_rate,synchrony,electrode_yield,baseline_noise,post_stim` | run_id, measurement date, instrument_id, channel/electrode mapping, and analysis method | `local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;calibration_logs` |
| `biological_assay_or_imaging_export` | `viability,ldh,neurite,morphology,cell_body_count,cell_model,seeding_density` | run_id, culture model, assay date, operator or vendor, instrument_id or imaging/export method | `local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;bench_records` |
| `biochemical_or_plate_reader_export` | `lactate,ammonia,bdnf,ngf,albumin,transferrin,total_protein` | run_id, analyte, assay date, instrument_id or vendor report id, calibration/standard curve record | `local_zrc_full;local_zrc_bio_full;zrc_vendor_exports;calibration_logs` |
| `pressure_flow_or_resistance_export` | `flow_resistance,flow_rate,bubble_events` | run_id, flow/pressure method, instrument_id, time window, calculation method | `local_zrc_full;zrc_vendor_exports;bench_records` |

## Rejected Sources

- `email`, `quote`, `verbal`, `capability`, `phone_call`, `synthetic`, `fixture`, `placeholder`

## Boundary

This manifest is a provenance guardrail. It creates drop locations and policy only; it does not create measured evidence.
