# Falsiflow Claim Audit

**Project:** `falsiflow_neural_materials_demo`
**Claim:** `alg_lam_pedot_lowdose_interface_claim`
**Status:** `claim_blocked`
**Claim ready:** `false`

## Gates

| Gate | Status | Valid rows | Required rows | Derived | Blockers |
| --- | --- | ---: | ---: | ---: | ---: |
| `h_a_medium_stability` | `blocked_missing_evidence` | 0 | 7 | 0 | 14 |
| `h_b_electrical_interface` | `blocked_missing_evidence` | 1 | 6 | 0 | 11 |
| `h_c_network_response` | `blocked_missing_evidence` | 0 | 6 | 0 | 14 |

## Project Validation

- status: `valid`
- none

## Evidence Diagnostics

- none

## Blockers

- `h_a_medium_stability` `ha_demo_001` `ph_initial`: value is blank or placeholder
- `h_a_medium_stability` `ha_demo_001` `ph_final`: missing evidence row
- `h_a_medium_stability` `ha_demo_001` `osmolality_initial_mosm`: missing evidence row
- `h_a_medium_stability` `ha_demo_001` `osmolality_final_mosm`: missing evidence row
- `h_a_medium_stability` `ha_demo_001` `conductivity_initial_ms_cm`: missing evidence row
- `h_a_medium_stability` `ha_demo_001` `conductivity_final_ms_cm`: missing evidence row
- `h_a_medium_stability` `ha_demo_001` `visible_debris_present`: missing evidence row
- `h_a_medium_stability` `ha_demo_001` `ph_drift_24h_abs`: derived field failed: required input field is missing: ph_final
- `h_a_medium_stability` `ha_demo_001` `osmolality_drift_24h_mosm`: derived field failed: required input field is missing: osmolality_final_mosm
- `h_a_medium_stability` `ha_demo_001` `conductivity_drift_24h_pct`: derived field failed: required input field is missing: conductivity_initial_ms_cm
- `h_a_medium_stability` `ha_demo_001` `ph_drift_24h_abs`: acceptance field is missing or not derived
- `h_a_medium_stability` `ha_demo_001` `osmolality_drift_24h_mosm`: acceptance field is missing or not derived
- `h_a_medium_stability` `ha_demo_001` `conductivity_drift_24h_pct`: acceptance field is missing or not derived
- `h_a_medium_stability` `ha_demo_001` `visible_debris_present`: acceptance field is missing or not derived
- `h_b_electrical_interface` `hb_demo_001` `impedance_1khz_candidate_ohm`: missing evidence row
- `h_b_electrical_interface` `hb_demo_001` `charge_storage_control_mC_cm2`: missing evidence row
- `h_b_electrical_interface` `hb_demo_001` `charge_storage_candidate_mC_cm2`: missing evidence row
- `h_b_electrical_interface` `hb_demo_001` `noise_control_uvrms`: missing evidence row
- `h_b_electrical_interface` `hb_demo_001` `noise_candidate_uvrms`: missing evidence row
- `h_b_electrical_interface` `hb_demo_001` `impedance_reduction_1khz_pct`: derived field failed: required input field is missing: impedance_1khz_candidate_ohm
- `h_b_electrical_interface` `hb_demo_001` `charge_storage_gain_pct`: derived field failed: required input field is missing: charge_storage_control_mC_cm2
- `h_b_electrical_interface` `hb_demo_001` `noise_increase_uvrms`: derived field failed: required input field is missing: noise_candidate_uvrms
- `h_b_electrical_interface` `hb_demo_001` `impedance_reduction_1khz_pct`: acceptance field is missing or not derived
- `h_b_electrical_interface` `hb_demo_001` `charge_storage_gain_pct`: acceptance field is missing or not derived
- `h_b_electrical_interface` `hb_demo_001` `noise_increase_uvrms`: acceptance field is missing or not derived
- `h_c_network_response` `hc_demo_candidate` `viability_pct`: missing evidence row
- `h_c_network_response` `hc_demo_candidate` `burst_rate_hz`: missing evidence row
- `h_c_network_response` `hc_demo_candidate` `inflammation_marker`: missing evidence row
- `h_c_network_response` `hc_demo_control` `viability_pct`: missing evidence row
- `h_c_network_response` `hc_demo_control` `burst_rate_hz`: missing evidence row
- `h_c_network_response` `hc_demo_control` `inflammation_marker`: missing evidence row
- `h_c_network_response` `hc_demo_candidate` `burst_rate_ratio_vs_control`: derived field failed: required input field is missing: hydrogel_laminin_control:hc_demo_control:burst_rate_hz
- `h_c_network_response` `hc_demo_control` `burst_rate_ratio_vs_control`: derived field failed: required input field is missing: hydrogel_laminin_control:hc_demo_control:burst_rate_hz
- `h_c_network_response` `hc_demo_candidate` `inflammation_marker_ratio_vs_control`: derived field failed: required input field is missing: hydrogel_laminin_control:hc_demo_control:inflammation_marker
- `h_c_network_response` `hc_demo_control` `inflammation_marker_ratio_vs_control`: derived field failed: required input field is missing: hydrogel_laminin_control:hc_demo_control:inflammation_marker
- `h_c_network_response` `hc_demo_candidate` `viability_pct`: acceptance field is missing or not derived
- `h_c_network_response` `hc_demo_control` `viability_pct`: acceptance field is missing or not derived
- `h_c_network_response` `hc_demo_candidate` `burst_rate_ratio_vs_control`: acceptance field is missing or not derived
- `h_c_network_response` `hc_demo_candidate` `inflammation_marker_ratio_vs_control`: acceptance field is missing or not derived

## Next Actions

- 1. `fill_h_a_medium_stability_evidence` - Gate `h_a_medium_stability` is `blocked_missing_evidence` with 14 blocker(s).
- 2. `fill_h_b_electrical_interface_evidence` - Gate `h_b_electrical_interface` is `blocked_missing_evidence` with 11 blocker(s).
- 3. `fill_h_c_network_response_evidence` - Gate `h_c_network_response` is `blocked_missing_evidence` with 14 blocker(s).
