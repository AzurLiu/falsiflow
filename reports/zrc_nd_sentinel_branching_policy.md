# ZRC-ND Sentinel Branching Policy

This policy controls what the agent may recommend after the compact Phase A material-blank sentinel batch.

## Gate Statuses

| Sentinel status | Advancement decision | Required action |
| --- | --- | --- |
| `no_sentinel_rows` | Do not claim suitability. Start with the 8-row Phase A sentinel packet. | Fill the Phase A sentinel rows and interpret them before later adaptive batches. |
| `sentinel_needs_more_data` | Stop advancement. | Complete missing medium-integrity fields for the lead article and matched no-module control. |
| `sentinel_lead_fails_stop` | Stop lead advancement. | Do not start Phase B/C or biological Phase D rows for the lead article. |
| `sentinel_lead_passes_comparator_issue` | Continue lead cautiously. | Quarantine failed comparators and exclude them from superiority claims until retested. |
| `sentinel_passes_continue` | Continue to the next adaptive non-cell batch. | Complete Phase A replicate coverage before Phase B/C confidence claims. |

## Lead-Failure Branch

If `lead_zrc_nd_3p5m_guard` fails the sentinel:

- Inspect blank-integrity drift sources: housing, membrane rinse/preconditioning, PDA/polyMPC coating, guard filter, and medium lot.
- Repeat Phase A sentinel with no-module control, `baseline_rc_3p5m_guard`, and `lead_zrc_nd_3p5m_guard` after isolating the suspected drift source.
- If `baseline_rc_3p5m_guard` passes while the lead fails, demote the PDA/polyMPC coating route and branch to `zrc_nd_3p5k_unmodified_guard`.
- If all material rows fail against no-module control, treat housing, rinsing, or medium handling as the primary failure mode before changing membrane chemistry.
- Do not use failed lead rows as evidence for material suitability.

## Comparator-Failure Branch

If the lead passes but a comparator fails:

- Keep the failed comparator out of superiority claims.
- Retest the failed comparator with a fresh article lot and matched no-module control.
- Continue only lead-centered adaptive measurement until comparator status is clean enough for ranking.

## Suitability Boundary

A passing sentinel only authorizes the next non-cell batch. It does not prove CL1-adjacent material suitability. A suitability claim still requires measured non-cell Phase A/B/C coverage and measured biological Phase D coverage passing the readiness audit.
