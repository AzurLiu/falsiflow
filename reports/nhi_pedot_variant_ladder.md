# NHI-PEDOT Variant Ladder

This is an adaptive design ladder, not measured evidence and not a suitability claim.

**Recipe lock:** `nhi_pedot_alg_lam_lowdose_recipe_lock_v0_2`
**Discovery top candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Rows:** 7

## Ranked Variant Ladder

| Rank | Utility | Variant | Role | Trigger | Primary readouts |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 0.617 | `alg_lam_pedot_0p6pct_lead` | current first-claim lead | primary_H-A_then_H-B_then_H-C_route | H-A_medium_integrity;H-A_physical_stability;H-B_EIS;H-B_charge_storage;H-C_neural_health_if_H-A_H-B_pass |
| 2 | 0.598 | `alg_lam_pedot_0p9pct_midpoint` | dose-response midpoint | use_if_0p6pct_passes_H-A_but_H-B_electrical_benefit_is_borderline | H-A_medium_integrity;transparency;EIS;charge_storage;CV_drift |
| 3 | 0.563 | `alg_lam_pedot_1p2pct_upper_boundary` | high-loading boundary challenge | use_as_boundary_not_first_claim_lead | H-A_shedding;H-A_transparency;H-B_EIS;H-B_charge_storage;CV_stability |
| 4 | 0.557 | `alg_lam_pedot_0p3pct_safety_rescue` | low-dose safety rescue | use_if_0p6pct_lead_has_mild_H-A_drift_or_shedding_without_hydrogel_control_failure | pH;osmolality;conductivity;visible_shedding;swelling;transparency;EIS_if_blank_passes |
| 5 | 0.536 | `pda_anchor_alg_lam_pedot_0p6pct` | adhesion/window rescue | use_if_unanchored_0p6pct_passes_medium_gates_but_fails_delamination_or_window_stability | primer_extract;delamination;electrode_window_occlusion;transparency;EIS |
| 6 | 0.517 | `alg_lam_hydrogel_no_pedot_control` | matched negative material baseline | always_pair_with_every_H-A_or_H-B_batch | pH;osmolality;conductivity;swelling;delamination;transparency;EIS_baseline_if_H-B |
| 7 | 0.495 | `alg_gel_pedot_ppy_acellular_comparator` | high-conductivity comparator only | use_after_ALG-LAM-PEDOT_baseline_if_H-B_needs_wider_conductive_hydrogel_context | extract_pH;osmolality;conductivity;visible_shedding;EIS;charge_storage;transparency |

## Decision Logic

- Keep `alg_lam_pedot_0p6pct_lead` as the first-claim route until real H-A/H-B/H-C data contradict it.
- Use `alg_lam_pedot_0p3pct_safety_rescue` only if the lead shows mild PEDOT-linked H-A drift while hydrogel-only controls remain clean.
- Use `alg_lam_pedot_0p9pct_midpoint` only if the lead passes H-A but H-B electrical benefit is borderline.
- Use `pda_anchor_alg_lam_pedot_0p6pct` only if medium integrity is clean and the dominant failure is delamination or electrode-window instability.
- Keep Alg-Gel PEDOT/PPy as an acellular comparator; it cannot displace the lead without its own extract and neural network gates.

## Hard Boundary

No row in this ladder can support a suitability claim until the corresponding non-synthetic measurement rows pass the active LIMINA gates.
