# LIMINA Portfolio Bypass Audit

This audit checks whether a ranked prospect can avoid the active NHI-PEDOT H-A gate and still support the first suitability claim. It is not a suitability claim.

**Status:** `no_h_a_bypass_claim_ready`
**Claim ready:** `false`
**Portfolio status:** `no_suitable_material_yet`
**Portfolio primary next branch:** `limina_nhi_pedot_laminin_v0_1`
**Active discovery candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Non-H-A claim-ready rows:** `0`
**Top non-H-A candidate:** `limina_all_dry_zwitterionic_external_v0_1`
**Recommended action:** `run_zrc_phase_a_real_measurements_before_any_non_h_a_claim`

## Prospect Decisions

| Rank | Prospect | Parent route | Requires H-A | Can bypass H-A | Decision | Provenance | Blocking reason |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `limina_alg_lam_pedot_lowdose_v0_2` | NHI-PEDOT cell-contact branch | `true` | `false` | `blocked_by_h_a_claim_gate` | coupon=0/0 measured; h_a_sentinel=0/12 measured; long_duration=0/0 measured | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status. |
| 2 | `limina_pda_anchor_alg_lam_pedot_window_v0_1` | NHI-PEDOT cell-contact branch | `true` | `false` | `blocked_by_h_a_claim_gate` | coupon=0/0 measured; h_a_sentinel=0/12 measured; long_duration=0/0 measured | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status. |
| 3 | `limina_all_dry_zwitterionic_external_v0_1` | ZRC-ND external-material branch | `false` | `true` | `non_h_a_path_not_claim_ready` | biological=0/0 measured; non_cell=0/0 measured | ZRC-ND readiness audit is not suitable. |
| 4 | `limina_alg_gel_pedot_ppy_lowoxidant_v0_1` | NHI-PEDOT cell-contact branch | `true` | `false` | `blocked_by_h_a_claim_gate` | coupon=0/0 measured; h_a_sentinel=0/12 measured; long_duration=0/0 measured | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status. |
| 5 | `limina_zwitterionic_pedot_hydrogel_v0_1` | NHI-PEDOT cell-contact branch | `true` | `false` | `blocked_by_h_a_claim_gate` | coupon=0/0 measured; h_a_sentinel=0/12 measured; long_duration=0/0 measured | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status. |
| 6 | `limina_pedot_sgagh_ecm_signal_hydrogel_v0_1` | NHI-PEDOT cell-contact branch | `true` | `false` | `blocked_by_h_a_claim_gate` | coupon=0/0 measured; h_a_sentinel=0/12 measured; long_duration=0/0 measured | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status. |
| 7 | `limina_hydrogel_actuated_multilayer_3d_mea_v0_1` | NHI-PEDOT cell-contact branch | `true` | `false` | `blocked_by_h_a_claim_gate` | coupon=0/0 measured; h_a_sentinel=0/12 measured; long_duration=0/0 measured | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status. |
| 8 | `limina_anisotropic_spedot_psbma_hydrogel_v0_1` | NHI-PEDOT cell-contact branch | `true` | `false` | `blocked_by_h_a_claim_gate` | coupon=0/0 measured; h_a_sentinel=0/12 measured; long_duration=0/0 measured | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status. |
| 9 | `limina_cameo_cnt_organoid_frame_v0_1` | NHI-PEDOT cell-contact branch | `true` | `false` | `blocked_by_h_a_claim_gate` | coupon=0/0 measured; h_a_sentinel=0/12 measured; long_duration=0/0 measured | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status. |
| 10 | `limina_op_apa_fillerfree_hydrogel_v0_1` | NHI-PEDOT cell-contact branch | `true` | `false` | `blocked_by_h_a_claim_gate` | coupon=0/0 measured; h_a_sentinel=0/12 measured; long_duration=0/0 measured | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status. |
| 11 | `limina_entangled_zwitterionic_mechanoadaptive_matrix_v0_1` | NHI-PEDOT cell-contact branch | `true` | `false` | `blocked_by_h_a_claim_gate` | coupon=0/0 measured; h_a_sentinel=0/12 measured; long_duration=0/0 measured | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status. |
| 12 | `limina_mxene_gel_oha_sensing_hydrogel_v0_1` | NHI-PEDOT cell-contact branch | `true` | `false` | `blocked_by_h_a_claim_gate` | coupon=0/0 measured; h_a_sentinel=0/12 measured; long_duration=0/0 measured | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status. |

## Interpretation

- Cell-contact prospects inherit the NHI-PEDOT H-A/H-B/H-C and long-duration measurement gates before a suitability claim.
- The ZRC-ND external branch is the only ranked non-H-A path right now, but it still needs real Phase A/non-cell and biological measured provenance.
- Literature-backed discovery ranking can prioritize experiments; it cannot replace source-file-backed measurement rows in the final claim audit.
