# ZRC-ND Non-Cell Execution Queue

**Validation package:** `zrc_nd_3p5k_guard_validation_v0_1`
**Lead variant:** `zrc_nd_3p5k_mpc_guard`
**Queue rows:** 132
**Sample manifest rows:** 264

This is an execution scaffold for non-cell media-chemistry validation. It is not experimental evidence.

## Queue Counts

| Phase | Rows |
| --- | ---: |
| A | 48 |
| B | 48 |
| C | 36 |

| Role | Rows |
| --- | ---: |
| `baseline_snapshot` | 24 |
| `gate_evaluable` | 66 |
| `matched_control` | 33 |
| `process_reference` | 9 |

## First Evidence-Unlocking Tranche

Phase A should be filled before Phase B/C and before any biological follow-up. The rows below are the first gate-relevant tranche.

| Queue | Run | Article | Timepoint | Replicate | Required readouts |
| ---: | --- | --- | --- | --- | --- |
| 2 | `ZRCND-A-baseline_rc_3p5m_guard-R1-1h` | `baseline_rc_3p5m_guard` | 1 h | 1 | medium_integrity |
| 3 | `ZRCND-A-baseline_rc_3p5m_guard-R1-24h` | `baseline_rc_3p5m_guard` | 24 h | 1 | medium_integrity |
| 4 | `ZRCND-A-baseline_rc_3p5m_guard-R1-4h` | `baseline_rc_3p5m_guard` | 4 h | 1 | medium_integrity |
| 6 | `ZRCND-A-challenge_zrc_nd_10m_guard-R1-1h` | `challenge_zrc_nd_10m_guard` | 1 h | 1 | medium_integrity |
| 7 | `ZRCND-A-challenge_zrc_nd_10m_guard-R1-24h` | `challenge_zrc_nd_10m_guard` | 24 h | 1 | medium_integrity |
| 8 | `ZRCND-A-challenge_zrc_nd_10m_guard-R1-4h` | `challenge_zrc_nd_10m_guard` | 4 h | 1 | medium_integrity |
| 10 | `ZRCND-A-lead_zrc_nd_3p5m_guard-R1-1h` | `lead_zrc_nd_3p5m_guard` | 1 h | 1 | medium_integrity |
| 11 | `ZRCND-A-lead_zrc_nd_3p5m_guard-R1-24h` | `lead_zrc_nd_3p5m_guard` | 24 h | 1 | medium_integrity |
| 12 | `ZRCND-A-lead_zrc_nd_3p5m_guard-R1-4h` | `lead_zrc_nd_3p5m_guard` | 4 h | 1 | medium_integrity |
| 13 | `ZRCND-A-no_module_static_control-R1-0h` | `no_module_static_control` | 0 h | 1 | medium_integrity |
| 14 | `ZRCND-A-no_module_static_control-R1-1h` | `no_module_static_control` | 1 h | 1 | medium_integrity |
| 15 | `ZRCND-A-no_module_static_control-R1-24h` | `no_module_static_control` | 24 h | 1 | medium_integrity |
| 16 | `ZRCND-A-no_module_static_control-R1-4h` | `no_module_static_control` | 4 h | 1 | medium_integrity |
| 18 | `ZRCND-A-baseline_rc_3p5m_guard-R2-1h` | `baseline_rc_3p5m_guard` | 1 h | 2 | medium_integrity |
| 19 | `ZRCND-A-baseline_rc_3p5m_guard-R2-24h` | `baseline_rc_3p5m_guard` | 24 h | 2 | medium_integrity |
| 20 | `ZRCND-A-baseline_rc_3p5m_guard-R2-4h` | `baseline_rc_3p5m_guard` | 4 h | 2 | medium_integrity |

## Data Integrity Rules

- Every gate-evaluable row needs a matched `no_module_static_control` row with the same phase, timepoint, and replicate.
- `0 h` rows are baseline snapshots; they are useful for traceability but must not be counted as material pass/fail evidence.
- Phase A unlocks only blank-integrity evidence. Phase B/C carry waste-clearance, factor-retention, and fouling evidence.
- Synthetic fixture rows are allowed only for evaluator regression; real suitability requires measured rows in the validation template.
