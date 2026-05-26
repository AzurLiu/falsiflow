# LIMINA Hybrid Measurement Plan

This plan separates locally capturable fields from vendor-preferred fields. It is not measured evidence.

**Status:** `hybrid_measurement_plan_ready`
**NHI-PEDOT candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**ZRC-ND candidate:** `limina_zrc_nd_v0_1`
**Field rows routed:** 350

## Route Totals

| Route | Fields | Rows | Meaning |
| --- | ---: | ---: | --- |
| `inhouse_ready` | 16 | 184 | Can be captured locally or by a simple bench operator if calibrated instruments/images are available. |
| `outsourced_preferred` | 3 | 40 | Prefer external lab unless a calibrated instrument is already available locally. |
| `supplier_or_build_record` | 13 | 126 | Record from supplier, fabrication batch, or chain-of-custody rather than analytical testing. |
| `vendor_or_future_gate` | 0 | 0 | Not required for the current front-door gate or likely needs later specialist testing. |

## Branch Summary

| Branch | Fields | Rows | Local rows | Outsource-preferred rows | Provenance rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| NHI-PEDOT H-A | 16 | 228 | 120 | 24 | 84 |
| ZRC-ND Phase A | 16 | 122 | 64 | 16 | 42 |

## NHI-PEDOT H-A

| Field | Rows | Route | Evidence requirement | Source file requirement |
| --- | ---: | --- | --- | --- |
| `conductivity` | 24 | `inhouse_ready` | Calibrated conductivity for the specified H-A sample event. | Conductivity meter export, calibration log, or display photo reconciled to run_id. |
| `delamination_score` | 12 | `inhouse_ready` | 0 to 1 delamination score using the preregistered H-A rubric. | Image plus scoring worksheet or vendor image-analysis report. |
| `optical_transparency_fraction` | 12 | `inhouse_ready` | 0 to 1 transparency estimate from a consistent imaging/lightbox method. | Image-analysis export or vendor microscopy report. |
| `pH` | 24 | `inhouse_ready` | Calibrated pH measurement for the specified H-A sample event. | Meter export, calibration log, or time-stamped display photo reconciled to run_id. |
| `swelling_fraction` | 12 | `inhouse_ready` | Fractional swelling from pre/post dimensions or mass using the same method across rows. | Image analysis export, caliper log, or mass/dimension worksheet. |
| `temperature_c` | 12 | `inhouse_ready` | Actual incubation or measurement temperature in C. | Incubator log, probe export, or time-stamped photo. |
| `visible_precipitate` | 12 | `inhouse_ready` | Boolean precipitate/turbidity/extractables concern scored from inspection. | Time-stamped image or vendor inspection report. |
| `visible_shedding` | 12 | `inhouse_ready` | Boolean visible material shedding score. | Time-stamped image or microscopy/stereoscope export. |
| `osmolality` | 24 | `outsourced_preferred` | Measured osmolality for the specified H-A sample event. | Osmometer report/export reconciled to run_id. |
| `date` | 12 | `supplier_or_build_record` | ISO date for the actual measurement or sample-handling event. | Bench sheet, vendor report, or chain-of-custody CSV. |
| `electrode_material` | 12 | `supplier_or_build_record` | Actual electrode/coupon substrate material used for the row. | Supplier documentation, build sheet, or sample label record. |
| `laminin_or_peptide_density` | 12 | `supplier_or_build_record` | Applied laminin or adhesion-peptide target density or documented formulation value. | Recipe record, supplier CoA, coating log, or build sheet. |
| `mea_coupon_id` | 12 | `supplier_or_build_record` | Traceable MEA or coupon identifier for the exposed article. | Build sheet, sample label, or chain-of-custody record. |
| `medium_lot` | 12 | `supplier_or_build_record` | Exact medium lot used for matched article/control rows. | Lot CoA, bottle label image, or chain-of-custody record. |
| `medium_name` | 12 | `supplier_or_build_record` | Exact medium or CL1-proxy medium name. | Medium bottle photo, lot CoA, or chain-of-custody record. |
| `sterilization_or_aseptic_protocol` | 12 | `supplier_or_build_record` | Actual sterilization or aseptic-handling protocol applied to the article. | SOP identifier, batch record, or chain-of-custody record. |

## ZRC-ND Phase A

| Field | Rows | Route | Evidence requirement | Source file requirement |
| --- | ---: | --- | --- | --- |
| `conductivity_final_mS_cm` | 8 | `inhouse_ready` | Calibrated conductivity after the row timepoint. | Conductivity meter export, calibration log, or display photo. |
| `conductivity_initial_mS_cm` | 8 | `inhouse_ready` | Calibrated conductivity before exposure or matched start measurement. | Conductivity meter export, calibration log, or display photo. |
| `exposure_time_h` | 8 | `inhouse_ready` | Actual elapsed exposure time for the row. | Incubation start/stop log or vendor report. |
| `initial_volume_ml` | 8 | `inhouse_ready` | Starting medium volume per row. | Pipetting worksheet or balance/volume log. |
| `pH_final` | 8 | `inhouse_ready` | Calibrated pH measurement after the row timepoint. | Meter export, calibration log, or time-stamped display photo. |
| `pH_initial` | 8 | `inhouse_ready` | Calibrated pH measurement before exposure or matched start measurement. | Meter export, calibration log, or time-stamped display photo. |
| `temperature_c` | 8 | `inhouse_ready` | Actual incubation or measurement temperature in C. | Incubator log, probe export, or time-stamped photo. |
| `visible_precipitate` | 8 | `inhouse_ready` | Boolean precipitate/turbidity/extractables concern scored from inspection. | Time-stamped image or vendor inspection report. |
| `osmolality_final_mOsm_kg` | 8 | `outsourced_preferred` | Measured osmolality after the row timepoint. | Osmometer report/export reconciled to run_id. |
| `osmolality_initial_mOsm_kg` | 8 | `outsourced_preferred` | Measured osmolality before exposure or matched start measurement. | Osmometer report/export reconciled to run_id. |
| `date` | 8 | `supplier_or_build_record` | ISO date for the actual measurement or sample-handling event. | Bench sheet, vendor report, or chain-of-custody CSV. |
| `medium_lot` | 8 | `supplier_or_build_record` | Exact medium lot used for matched article/control rows. | Lot CoA, bottle label image, or chain-of-custody record. |
| `medium_name` | 8 | `supplier_or_build_record` | Exact medium or CL1-proxy medium name. | Medium bottle photo, lot CoA, or chain-of-custody record. |
| `membrane_area_cm2` | 6 | `supplier_or_build_record` | Exposed membrane area used for normalization. | Build drawing, measurement worksheet, or supplier documentation. |
| `membrane_lot` | 6 | `supplier_or_build_record` | Actual membrane/module lot for exposed ZRC-ND articles. | Supplier label, CoA, build sheet, or chain-of-custody record. |
| `prefilter_lot` | 6 | `supplier_or_build_record` | Guard prefilter lot or explicit none/not_applicable. | Supplier label, build sheet, or chain-of-custody record. |

## Execution Notes

- Local capture can reduce vendor scope, but every local value still needs measured_at, operator_or_agent, instrument_id, and source_file provenance.
- Osmolality is kept as outsourced_preferred because it commonly requires a dedicated osmometer; use a local instrument only if it is calibrated and produces traceable output.
- Supplier/build records do not prove compatibility by themselves; they only remove provenance blockers.
- Never enter phone photos, emails, or vendor capability replies as material evidence unless they contain real run-level measured values.

## Boundary

This plan only routes work. Suitability remains false until real, non-synthetic rows pass gate evaluators and the final claim audit.
