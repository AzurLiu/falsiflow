# LIMINA Technology Portfolio

**Portfolio status:** `no_suitable_material_yet`
**Active discovery candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Active discovery priority:** `promote_now`
**Primary next branch:** `limina_nhi_pedot_laminin_v0_1`

## Branch Decisions

| Priority | Technology | Lane | Status | Score | Next action |
| ---: | --- | --- | --- | ---: | --- |
| 1 | `limina_nhi_pedot_laminin_v0_1` | LIMINA-Cell-1 | `active_needs_h_a_real_measurements` | 4.08 | Use the H-A service request to obtain real acellular medium/physical rows for the promoted ALG-LAM-PEDOT route before advancing H-B/H-C. |
| 1 | `limina_zrc_nd_v0_1` | LIMINA-External-1 | `active_needs_phase_a_sentinel` | 4.02 | Fill the 8-row Phase A sentinel packet and re-run sentinel interpretation before more non-cell work. |

## Validation Packages

### limina_nhi_pedot_laminin_v0_1

- All present: `true`
- Present: `data/nhi_pedot_validation_package.json`, `data/nhi_pedot_long_followup_package.json`
- Expected: `data/nhi_pedot_validation_package.json`, `data/nhi_pedot_long_followup_package.json`
- Proof boundary: Not suitable until final claim audit verifies H-A/H-B/H-C and long-duration source-file provenance.

### limina_zrc_nd_v0_1

- All present: `true`
- Present: `data/zrc_nd_3p5k_guard_validation_package.json`, `data/zrc_nd_biological_followup_package.json`
- Expected: `data/zrc_nd_3p5k_guard_validation_package.json`, `data/zrc_nd_biological_followup_package.json`
- Proof boundary: Not suitable until the final claim audit verifies measured non-cell and biological provenance.

## Interpretation

- Portfolio priority is a workflow selector, not a suitability score.
- A branch can be high priority because it is the next cheapest decisive test, even if it is not experimentally proven.
- `suitable` remains false until `limina_suitability_claim_audit` reports `claim_ready=true` with source-file-backed measured rows.
