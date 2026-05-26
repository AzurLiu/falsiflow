# ZRC-ND Readiness Audit

**Technology:** `limina_zrc_nd_v0_1`
**Lead variant:** `zrc_nd_3p5k_mpc_guard`
**Technology status:** `nominated`
**Readiness:** `not_suitable_yet_no_measured_data`
**Non-cell validated:** `false`
**Biological validated:** `false`
**Suitable:** `false`

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| `technology_record_present` | `pass` | Technology record exists. |
| `validation_result_status` | `fail` | Expected `lead_passes_non_cell_gates`, observed `no_data`. |
| `aggregate_lead_superiority` | `fail` | Expected `pass`, observed `not_evaluable`. |
| `phase_coverage` | `fail` | Required ['A', 'B', 'C'], observed []. |
| `lead_replicate_coverage` | `fail` | Required >= 3 passed lead replicates per phase; observed {}. |
| `failed_lead_rows` | `pass` | Failed lead rows: 0. |
| `bio_result_status` | `fail` | Expected `bio_followup_passes_gates`, observed `no_data`. |
| `aggregate_bio_superiority` | `fail` | Expected `pass`, observed `not_evaluable`. |
| `bio_phase_coverage` | `fail` | Required ['D1', 'D2', 'D3'], observed []. |
| `bio_lead_replicate_coverage` | `fail` | Required >= 3 passed lead replicates per phase; observed {}. |
| `failed_bio_lead_rows` | `pass` | Failed biological lead rows: 0. |

## Missing Evidence

- Measured Phase A/B/C rows that pass non-cell validation gates.
- conditioned-medium viability or toxicity screen
- neurite/morphology or equivalent neural-health readout
- MEA/network activity or equivalent functional stability readout if available
- no unresolved material blank or extractables issue
