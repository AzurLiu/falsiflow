# ZRC-ND Phase A Real-Measurement Service Request

This packet is for an external lab, collaborator, or bench operator. It requests real acellular Phase A measurements only; it is not a suitability claim.

**Status:** `ready_to_request_real_phase_a_measurements`
**Active candidate:** `limina_zrc_nd_v0_1`
**Lead variant:** `zrc_nd_3p5k_mpc_guard`
**Sentinel selector:** `needs_phase_a_sentinel`; reason=`phase_a_sentinel_no_measured_rows`
**Runs:** 8
**Sample events:** 16

## Requested Matrix

- Articles: `baseline_rc_3p5m_guard`, `challenge_zrc_nd_10m_guard`, `lead_zrc_nd_3p5m_guard`, `no_module_static_control`
- Timepoints: 0 h, 24 h
- Replicates: 1
- Sample event types: final, initial

## Required Capabilities

- Acellular 37 C or matched-temperature medium exposure of small membrane/module witness articles.
- Matched no-module control handling for the same timepoints and medium lot.
- pH measurement before and after each row.
- Osmolality measurement before and after each row.
- Conductivity measurement before and after each row.
- Visual inspection for precipitate, turbidity, bubbles, color shift, or obvious extractables.
- Lot-level provenance for membrane, guard, housing, rinse/preconditioning, and medium.

## Acceptance Gate

- `zrc_nd_phase_a_blank_integrity_gate`: Material-driven pH drift must be <= 0.10 pH units versus matched no-module control; osmolality and conductivity drift must be <= 5 percent versus control; no visible precipitate or unresolved turbidity/extractables concern.

## Deliverables

| Deliverable | Acceptance | Target artifact |
| --- | --- | --- |
| Completed ZRC-ND Phase A sentinel CSV | All 8 run rows have real values for the required medium-integrity and provenance fields. | `data/zrc_nd_phase_a_sentinel_template.csv` |
| Sample/module chain of custody | Every initial/final sample event maps to a run_id, sample_id, article_id, module/cup/tube ID, medium lot, and receipt condition. | `data/zrc_nd_phase_a_chain_of_custody.csv` |
| Instrument exports and inspection images | Raw pH, osmolality, conductivity, and visual-inspection files are preserved and named in the deviation or return log. | `external_lab_exports/zrc_nd_phase_a/` |
| Deviation log | Any substitution in membrane, housing, guard, medium, exposure time, temperature, rinse, or instrument calibration is listed explicitly. | `reports/zrc_nd_phase_a_deviation_log.md` |

## Required Fields

| Field | Rows | Description |
| --- | ---: | --- |
| `date` | 8 | Measurement date for each Phase A sentinel row. |
| `membrane_lot` | 6 | Actual lot for every membrane or module-exposed article; leave blank only for no-module controls. |
| `membrane_area_cm2` | 6 | Exposed membrane area for baseline, lead, and 10 kDa challenge articles. |
| `prefilter_lot` | 6 | Guard prefilter lot if present, or explicit none/not_applicable when omitted. |
| `medium_name` | 8 | Fresh complete neuronal medium or closest CL1-like medium proxy. |
| `medium_lot` | 8 | Actual medium lot shared with control rows where possible. |
| `initial_volume_ml` | 8 | Starting medium volume for normalization and drift interpretation. |
| `exposure_time_h` | 8 | Actual exposure duration; must match the run timepoint within deviation-log tolerance. |
| `temperature_c` | 8 | Actual incubation or measurement temperature. |
| `pH_initial` | 8 | Initial pH before exposure or matched start measurement. |
| `pH_final` | 8 | Final pH at the run timepoint. |
| `osmolality_initial_mOsm_kg` | 8 | Initial osmolality in matched medium. |
| `osmolality_final_mOsm_kg` | 8 | Final osmolality at the run timepoint. |
| `conductivity_initial_mS_cm` | 8 | Initial conductivity in matched medium. |
| `conductivity_final_mS_cm` | 8 | Final conductivity at the run timepoint. |
| `visible_precipitate` | 8 | yes/no visible precipitate, turbidity, bubble, or extractables concern. |

## Article Roles

| Article | Role | Description |
| --- | --- | --- |
| `lead_zrc_nd_3p5m_guard` | lead candidate | 3.5 kDa RC exchange element, MPC-like zwitterionic wetted-surface modification, low-binding PES/SFCA guard, COC/COP housing. |
| `baseline_rc_3p5m_guard` | unmodified baseline | 3.5 kDa RC exchange element with the same guard and housing but no zwitterionic modification. |
| `challenge_zrc_nd_10m_guard` | high-clearance retention challenge | 10 kDa RC exchange element with the same zwitterionic/guard/housing concept. |
| `no_module_static_control` | stability and background control | Matched medium held without cartridge exposure. |

## Rejection Rules

- Do not enter pending, TBD, unknown, synthetic, fixture, or not_evidence markers as measured values.
- Do not pool the baseline, lead, challenge, or no-module rows before data entry.
- Do not advance Phase B/C or biological follow-up if the lead Phase A blank-integrity gate fails.
- Do not treat Phase A as a suitability claim; it only authorizes or blocks later ZRC-ND validation rows.

## Source Artifacts

- phase_a_template: `data/zrc_nd_phase_a_sentinel_template.csv`
- sample_manifest: `data/zrc_nd_phase_a_sentinel_sample_manifest.csv`
- sentinel_packet: `reports/zrc_nd_phase_a_sentinel_packet.md`
- next_measurements: `reports/zrc_nd_next_measurements.md`
- validation_package: `data/zrc_nd_3p5k_guard_validation_package.json`

## After Delivery

Run these commands after the completed Phase A CSV is placed back into the workspace:

```bash
python3 scripts/merge_zrc_nd_measurements.py
python3 scripts/interpret_zrc_nd_sentinel.py
python3 scripts/evaluate_zrc_nd_validation_runs.py --runs data/zrc_nd_validation_runs_active.csv
python3 scripts/suggest_zrc_nd_next_measurements.py --runs data/zrc_nd_validation_runs_active.csv
python3 scripts/audit_zrc_nd_readiness.py
python3 scripts/audit_limina_suitability_claim.py
```

## Boundary

Phase A is a material-blank front-door gate for the external cartridge branch. It cannot prove CL1 suitability without later Phase B/C non-cell and biological rows.
