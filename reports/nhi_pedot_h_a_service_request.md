# NHI-PEDOT H-A Real-Measurement Service Request

This packet is written for an external lab, collaborator, or bench operator. It requests real acellular H-A measurements only; it is not a suitability claim.

**Status:** `ready_to_request_real_measurements`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Runs:** 12
**Raw entries requested:** 228
**Current QC:** `h_a_intake_not_ready`; errors=183; warnings=24

## Requested Matrix

- Articles: `no_coating_mea_control`, `hydrogel_laminin_control`, `lead_nhi_pedot_low_loading`, `challenge_nhi_pedot_high_loading`
- Timepoints: 0 h, 24 h, 72 h
- Replicates: 1

## Required Capabilities

- Acellular soak/incubation of MEA witness coupons or equivalent electrode-window coupons at 37 C.
- pH measurement before and after each timepoint.
- Osmolality measurement before and after each timepoint.
- Conductivity measurement before and after each timepoint.
- Brightfield or stereoscope imaging sufficient to score shedding, delamination, swelling, and transparency.
- Lot-level provenance for medium, hydrogel reagents, electrode coupons, laminin or peptide source, and sterilization/aseptic handling.

## Deliverables

| Deliverable | Acceptance | Target artifact |
| --- | --- | --- |
| Completed long-form raw measurement CSV | All 228 raw entries have values, measured_at, operator_or_agent, instrument_id, source_file, and notes when relevant. | `data/nhi_pedot_h_a_raw_measurements_template.csv` |
| Completed one-row-per-source-file bundle entry sheet | Preferred compact return path: fill one row per raw-file bundle, set apply=yes, and cite the returned source file for each bundle. | `data/nhi_pedot_h_a_vendor_return_inbox/completed_bundle_entry_sheet.csv` |
| Sample/coupon chain of custody | Each coupon/well maps to one run_id, sample_id, container ID, article_id, timepoint, replicate, medium lot, and preparation batch. | `data/nhi_pedot_h_a_chain_of_custody.csv` |
| Instrument exports and images | Raw pH, osmolality, conductivity, and imaging/inspection exports are preserved with file names referenced in source_file. | `external_lab_exports/` |
| Deviation log | Any substitution in medium, electrode coupon, hydrogel batch, incubation time, temperature, or instrument calibration is listed explicitly. | `reports/nhi_pedot_h_a_deviation_log.md` |

## Required Fields

| Field | Rows | Description |
| --- | ---: | --- |
| `conductivity_final_mS_cm` | 12 | final conductivity |
| `conductivity_initial_mS_cm` | 12 | initial conductivity |
| `date` | 12 | calendar date of the measurement event |
| `delamination_score` | 12 | 0 to 1 delamination score |
| `medium_lot` | 12 | actual medium lot |
| `medium_name` | 12 | actual medium or CL1-proxy medium name |
| `optical_transparency_fraction` | 12 | 0 to 1 optical transparency fraction |
| `osmolality_final_mOsm_kg` | 12 | final osmolality |
| `osmolality_initial_mOsm_kg` | 12 | initial osmolality |
| `pH_final` | 12 | final pH |
| `pH_initial` | 12 | initial pH |
| `swelling_fraction` | 12 | fractional swelling |
| `temperature_c` | 3 | measurement/incubation temperature in C |
| `visible_precipitate` | 12 | visible precipitate, true or false |
| `visible_shedding` | 12 | visible material shedding, true or false |

## Stop Rules

| Article | Role | Stop or branch condition |
| --- | --- | --- |
| `no_coating_mea_control` | matched medium/device control | control is unstable or missing, because matched comparisons become invalid |
| `hydrogel_laminin_control` | soft matrix control | hydrogel-only matrix fails, because PEDOT interpretation becomes confounded |
| `lead_nhi_pedot_low_loading` | 0.6 wt percent PEDOT:PSS lead | lead shows pH drift >0.10 vs control, osmolality/conductivity drift >5%, shedding, swelling >0.20, delamination >0.5, or transparency <0.80 |
| `challenge_nhi_pedot_high_loading` | 1.2 wt percent PEDOT:PSS boundary comparator | treat challenge as boundary only if it fails; do not promote to H-C |

## Rejection Rules

- Do not replace missing values with pending, record_actual, TBD, unknown, synthetic, fixture, or not_evidence markers.
- Do not average across coupons before data entry; enter one row per run_id/sample_event/target_field.
- Do not omit no-coating controls; matched controls are required for pH, osmolality, and conductivity drift decisions.
- Do not interpret H-A as a suitability claim; it only authorizes or blocks H-B/H-C follow-up.

## Source Artifacts

- raw_measurement_template: `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_raw_measurements_template.csv`
- internal_bundle_entry_sheet: `data/nhi_pedot_h_a_bundle_entry_sheet.csv`
- vendor_bundle_entry_sheet: `data/nhi_pedot_h_a_vendor_return_inbox/completed_bundle_entry_sheet.csv`
- vendor_bundle_entry_report: `reports/nhi_pedot_h_a_vendor_bundle_entry_sheet.md`
- source_unlock_bundle_manifest: `data/nhi_pedot_h_a_source_unlock_bundle_manifest.csv`
- active_runs: `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_runs_active.csv`
- bench_sheet: `data/nhi_pedot_h_a_bench_sheet.json`
- minimum_checklist: `data/nhi_pedot_h_a_minimum_measurement_checklist.json`

## After Delivery

Run these commands after the completed raw-measurement CSV is placed back into the workspace:

```bash
python3 scripts/render_nhi_pedot_h_a_vendor_return_intake.py
python3 scripts/render_nhi_pedot_h_a_vendor_bundle_entry_sheet.py
python3 scripts/apply_nhi_pedot_h_a_vendor_bundle_entry_return.py --sheet data/nhi_pedot_h_a_vendor_return_inbox/completed_bundle_entry_sheet.csv
python3 scripts/import_nhi_pedot_h_a_source_values.py
python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py
python3 scripts/qc_nhi_pedot_h_a_intake.py --strict-exit
python3 scripts/interpret_nhi_pedot_h_a_sentinel.py
python3 scripts/audit_limina_suitability_claim.py
```

## Boundary

This checklist prepares data entry only. The material remains a hypothesis until QC-clean real rows pass H-A, H-B, H-C, long follow-up, and the final claim audit.
