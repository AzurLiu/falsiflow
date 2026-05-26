# NHI-PEDOT Forward H-B/H-C Gate Package

This preregisters the next evidence gates after H-A. It is not measured evidence and not a material suitability claim.

**Status:** `preregistered_waiting_for_h_a`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**H-A status:** `h_a_invalid_provenance`
**Forward rows:** 28
**Activation rule:** Run H-B only after H-A has QC-clean real rows and an H-A pass/continue status.

## Phase Packages

### H-B - Electrochemical and physical stability

- Activation: `after_H-A_pass`
- Articles: `hydrogel_laminin_control`, `lead_nhi_pedot_low_loading`, `challenge_nhi_pedot_high_loading`
- Timepoints: pre-soak, 24 h soak, 72 h soak, post-cycling
- Required fields: `date`, `operator_or_agent`, `mea_coupon_id`, `electrode_material`, `hydrogel_matrix`, `pedot_pss_loading_fraction`, `pedot_pss_pre_rinse_protocol`, `laminin_or_peptide_density`, `crosslinking_protocol`, `sterilization_or_aseptic_protocol`, `medium_name`, `medium_lot`, `temperature_c`, `source_file`, `swelling_fraction`, `delamination_score`, `optical_transparency_fraction`, `eis_1khz_initial_ohm`, `eis_1khz_final_ohm`, `charge_storage_capacity_initial`, `charge_storage_capacity_final`

| Gate | Criterion | Failure response |
| --- | --- | --- |
| `physical_stability_gate` | Hydrogel thickness changes less than 20 percent, no delamination/cracking, electrode windows remain inspectable, and transparency remains sufficient for cell monitoring after 72 h soak. | Change matrix concentration, anchoring chemistry, pattern geometry, or crosslinking route. |
| `electrochemical_benefit_gate` | The low-loading lead improves impedance or charge-storage metrics by at least 25 percent versus hydrogel-laminin control after soak, without unstable cyclic-voltammetry drift. | Rerank loading, domain geometry, or drop PEDOT:PSS if the hydrogel-only control is equivalent. |

### H-C - Neural compatibility pilot

- Activation: `after_H-B_pass`
- Articles: `laminin_only_control`, `hydrogel_laminin_control`, `lead_nhi_pedot_low_loading`, `challenge_nhi_pedot_high_loading`
- Timepoints: 24 h, 7 d, 14 d, 28 d if early gates pass
- Required fields: `date`, `operator_or_agent`, `mea_coupon_id`, `electrode_material`, `hydrogel_matrix`, `pedot_pss_loading_fraction`, `pedot_pss_pre_rinse_protocol`, `laminin_or_peptide_density`, `crosslinking_protocol`, `sterilization_or_aseptic_protocol`, `medium_name`, `medium_lot`, `temperature_c`, `source_file`, `cell_model`, `seeding_density`, `viability_fraction`, `ldh_fold_control`, `neurite_coverage_fraction`, `mean_neurite_length_um`, `electrode_yield_fraction`, `spike_rate_hz`, `burst_rate_hz`

| Gate | Criterion | Failure response |
| --- | --- | --- |
| `neural_health_gate` | Lead viability, LDH or equivalent cytotoxicity, neurite coverage, and morphology are non-inferior to laminin-only and hydrogel-laminin controls at early timepoints. | Lower PEDOT:PSS loading, improve rinse/neutralization, change ECM presentation, or reject the conductive phase. |
| `network_activity_gate` | Lead MEA cultures maintain electrode yield and network activity at least non-inferior to hydrogel-laminin controls, with lower impedance drift, through the pilot window. | If cells survive but network activity falls, change stiffness, ligand density, thickness, or conductive-domain geometry before longer tests. |

## First Activated Rows

| Priority | Phase | Run | Article | Timepoint | Activation | Gate focus |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | H-B | `NHIPEDOT-H-B-hydrogel_laminin_control-R1-pre_soak` | `hydrogel_laminin_control` | pre-soak | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 2 | H-B | `NHIPEDOT-H-B-hydrogel_laminin_control-R1-24hsoak` | `hydrogel_laminin_control` | 24 h soak | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 3 | H-B | `NHIPEDOT-H-B-hydrogel_laminin_control-R1-72hsoak` | `hydrogel_laminin_control` | 72 h soak | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 4 | H-B | `NHIPEDOT-H-B-hydrogel_laminin_control-R1-post_cycling` | `hydrogel_laminin_control` | post-cycling | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 5 | H-B | `NHIPEDOT-H-B-lead_nhi_pedot_low_loading-R1-pre_soak` | `lead_nhi_pedot_low_loading` | pre-soak | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 6 | H-B | `NHIPEDOT-H-B-lead_nhi_pedot_low_loading-R1-24hsoak` | `lead_nhi_pedot_low_loading` | 24 h soak | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 7 | H-B | `NHIPEDOT-H-B-lead_nhi_pedot_low_loading-R1-72hsoak` | `lead_nhi_pedot_low_loading` | 72 h soak | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 8 | H-B | `NHIPEDOT-H-B-lead_nhi_pedot_low_loading-R1-post_cycling` | `lead_nhi_pedot_low_loading` | post-cycling | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 9 | H-B | `NHIPEDOT-H-B-challenge_nhi_pedot_high_loading-R1-pre_soak` | `challenge_nhi_pedot_high_loading` | pre-soak | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 10 | H-B | `NHIPEDOT-H-B-challenge_nhi_pedot_high_loading-R1-24hsoak` | `challenge_nhi_pedot_high_loading` | 24 h soak | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 11 | H-B | `NHIPEDOT-H-B-challenge_nhi_pedot_high_loading-R1-72hsoak` | `challenge_nhi_pedot_high_loading` | 72 h soak | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 12 | H-B | `NHIPEDOT-H-B-challenge_nhi_pedot_high_loading-R1-post_cycling` | `challenge_nhi_pedot_high_loading` | post-cycling | `after_H-A_pass` | physical_stability_gate;electrochemical_benefit_gate |
| 13 | H-C | `NHIPEDOT-H-C-laminin_only_control-R1-24h` | `laminin_only_control` | 24 h | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 14 | H-C | `NHIPEDOT-H-C-laminin_only_control-R1-7d` | `laminin_only_control` | 7 d | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 15 | H-C | `NHIPEDOT-H-C-laminin_only_control-R1-14d` | `laminin_only_control` | 14 d | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 16 | H-C | `NHIPEDOT-H-C-laminin_only_control-R1-28difearlygatespass` | `laminin_only_control` | 28 d if early gates pass | `after_H-C_24h_7d_14d_early_gates_pass` | neural_health_gate;network_activity_gate |
| 17 | H-C | `NHIPEDOT-H-C-hydrogel_laminin_control-R1-24h` | `hydrogel_laminin_control` | 24 h | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 18 | H-C | `NHIPEDOT-H-C-hydrogel_laminin_control-R1-7d` | `hydrogel_laminin_control` | 7 d | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 19 | H-C | `NHIPEDOT-H-C-hydrogel_laminin_control-R1-14d` | `hydrogel_laminin_control` | 14 d | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 20 | H-C | `NHIPEDOT-H-C-hydrogel_laminin_control-R1-28difearlygatespass` | `hydrogel_laminin_control` | 28 d if early gates pass | `after_H-C_24h_7d_14d_early_gates_pass` | neural_health_gate;network_activity_gate |
| 21 | H-C | `NHIPEDOT-H-C-lead_nhi_pedot_low_loading-R1-24h` | `lead_nhi_pedot_low_loading` | 24 h | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 22 | H-C | `NHIPEDOT-H-C-lead_nhi_pedot_low_loading-R1-7d` | `lead_nhi_pedot_low_loading` | 7 d | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 23 | H-C | `NHIPEDOT-H-C-lead_nhi_pedot_low_loading-R1-14d` | `lead_nhi_pedot_low_loading` | 14 d | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 24 | H-C | `NHIPEDOT-H-C-lead_nhi_pedot_low_loading-R1-28difearlygatespass` | `lead_nhi_pedot_low_loading` | 28 d if early gates pass | `after_H-C_24h_7d_14d_early_gates_pass` | neural_health_gate;network_activity_gate |
| 25 | H-C | `NHIPEDOT-H-C-challenge_nhi_pedot_high_loading-R1-24h` | `challenge_nhi_pedot_high_loading` | 24 h | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 26 | H-C | `NHIPEDOT-H-C-challenge_nhi_pedot_high_loading-R1-7d` | `challenge_nhi_pedot_high_loading` | 7 d | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 27 | H-C | `NHIPEDOT-H-C-challenge_nhi_pedot_high_loading-R1-14d` | `challenge_nhi_pedot_high_loading` | 14 d | `after_H-B_pass` | neural_health_gate;network_activity_gate |
| 28 | H-C | `NHIPEDOT-H-C-challenge_nhi_pedot_high_loading-R1-28difearlygatespass` | `challenge_nhi_pedot_high_loading` | 28 d if early gates pass | `after_H-C_24h_7d_14d_early_gates_pass` | neural_health_gate;network_activity_gate |

## Variant Triggers

- `alg_lam_pedot_0p9pct_midpoint`: use_if_0p6pct_passes_H-A_but_H-B_electrical_benefit_is_borderline
- `pda_anchor_alg_lam_pedot_0p6pct`: use_if_unanchored_0p6pct_passes_medium_gates_but_fails_delamination_or_window_stability
- `alg_lam_pedot_0p3pct_safety_rescue`: use_if_0p6pct_lead_has_mild_H-A_drift_or_shedding_without_hydrogel_control_failure

## Boundary

This package is a preregistered next-step plan. It is not evidence and cannot support a material suitability claim without real measured rows and the final claim audit.
