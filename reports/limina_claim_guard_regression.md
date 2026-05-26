# LIMINA Claim Guard Regression

This regression proves that full-pass synthetic fixtures cannot support a material suitability claim.

**Status:** `pass`
**Temporary output directory:** `/var/folders/z5/yhrnv1l15ng04x9hykysm46w0000gn/T/limina_claim_guard_regression_jer61x20`

## Key Outcomes

- H-A synthetic fixture interpretation: `h_a_invalid_provenance`
- Coupon synthetic fixture evaluator: `nhi_pedot_passes_gates`
- Long synthetic fixture evaluator: `nhi_pedot_long_passes_gates`
- ZRC-ND synthetic fixture evaluator: `lead_passes_non_cell_gates`
- ZRC-ND biological synthetic fixture evaluator: `bio_followup_passes_gates`
- ZRC-ND synthetic readiness: `suitable`
- Forward package state: `preregistered_waiting_for_h_a`
- Final claim audit: claim_ready=`false`, status=`no_suitable_material_claim_ready`

## NHI Provenance Rejection

| Source | Rows | Measured | Synthetic | Placeholder | Claimable |
| --- | ---: | ---: | ---: | ---: | --- |
| `coupon` | 168 | 0 | 168 | 168 | `false` |
| `h_a_sentinel` | 12 | 0 | 12 | 12 | `false` |
| `long_duration` | 156 | 0 | 156 | 156 | `false` |

## ZRC-ND Provenance Rejection

| Source | Rows | Measured | Synthetic | Placeholder | Claimable |
| --- | ---: | ---: | ---: | ---: | --- |
| `biological` | 54 | 0 | 54 | 54 | `false` |
| `non_cell` | 72 | 0 | 72 | 72 | `false` |

## Assertions

| Assertion | Result | Detail |
| --- | --- | --- |
| `all_commands_succeeded` | `pass` | all steps returned 0 |
| `coupon_fixture_exercises_full_pass` | `pass` | coupon evaluator status=nhi_pedot_passes_gates |
| `long_fixture_exercises_full_pass` | `pass` | long evaluator status=nhi_pedot_long_passes_gates |
| `zrc_fixture_exercises_full_pass` | `pass` | zrc evaluator status=lead_passes_non_cell_gates |
| `zrc_bio_fixture_exercises_full_pass` | `pass` | zrc bio evaluator status=bio_followup_passes_gates |
| `zrc_readiness_fixture_can_reach_suitable` | `pass` | zrc readiness=suitable; suitable=True |
| `h_a_fixture_rejected_before_interpretation` | `pass` | h_a status=h_a_invalid_provenance; h_a_qc intake_ready=False |
| `forward_package_not_activated_by_fixture` | `pass` | forward status=preregistered_waiting_for_h_a |
| `audit_refuses_synthetic_claim` | `pass` | claim_ready=False; status=no_suitable_material_claim_ready |
| `h_a_source_non_claimable` | `pass` | claimable=False; synthetic=12 |
| `coupon_source_non_claimable` | `pass` | claimable=False; synthetic=168 |
| `long_source_non_claimable` | `pass` | claimable=False; synthetic=156 |
| `zrc_source_non_claimable` | `pass` | claimable=False; synthetic=72 |
| `zrc_bio_source_non_claimable` | `pass` | claimable=False; synthetic=54 |

## Commands

| Step | Return code |
| --- | ---: |
| `generate_h_a_raw_fixture` | 0 |
| `generate_coupon_fixture` | 0 |
| `generate_long_fixture` | 0 |
| `merge_h_a_full_pass_fixture` | 0 |
| `qc_h_a_full_pass_fixture` | 0 |
| `interpret_h_a_full_pass_fixture` | 0 |
| `generate_forward_package` | 0 |
| `evaluate_coupon_full_pass_fixture` | 0 |
| `evaluate_long_full_pass_fixture` | 0 |
| `evaluate_zrc_full_pass_fixture` | 0 |
| `evaluate_zrc_bio_full_pass_fixture` | 0 |
| `audit_zrc_with_full_pass_fixtures` | 0 |
| `audit_claim_with_full_pass_fixtures` | 0 |

## Boundary

Synthetic fixtures are allowed to exercise evaluator logic only. The claim audit must still require non-synthetic measured rows before LIMINA says a material technology is suitable.
