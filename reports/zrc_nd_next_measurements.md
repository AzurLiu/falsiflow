# ZRC-ND Next Measurements

**Status:** `needs_phase_a_sentinel`
**Mode:** `adaptive`
**Reason:** `phase_a_sentinel_no_measured_rows`
**Evaluator status:** `no_data`
**Sentinel status:** `no_sentinel_rows`
**Sentinel next action:** Generate and fill the Phase A sentinel packet.
**Output CSV:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_next_measurements.csv`

## Sentinel Gate

The Phase A material-blank sentinel is a front-door gate for adaptive non-cell advancement.

- Status: `no_sentinel_rows`
- Action: Generate and fill the Phase A sentinel packet.

## Replicate Coverage

Required passed lead replicates per phase: 3

| Phase | Passed lead replicates |
| --- | --- |
| A | - |
| B | - |
| C | - |

## Recommended Rows

| Priority | Run | Phase | Timepoint | Replicate | Article | Role | Readouts |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `ZRCND-A-baseline_rc_3p5m_guard-R1-0h` | A | 0 h | 1 | `baseline_rc_3p5m_guard` | `baseline_snapshot` | medium_integrity |
| 2 | `ZRCND-A-baseline_rc_3p5m_guard-R1-24h` | A | 24 h | 1 | `baseline_rc_3p5m_guard` | `gate_evaluable` | medium_integrity |
| 3 | `ZRCND-A-challenge_zrc_nd_10m_guard-R1-0h` | A | 0 h | 1 | `challenge_zrc_nd_10m_guard` | `baseline_snapshot` | medium_integrity |
| 4 | `ZRCND-A-challenge_zrc_nd_10m_guard-R1-24h` | A | 24 h | 1 | `challenge_zrc_nd_10m_guard` | `gate_evaluable` | medium_integrity |
| 5 | `ZRCND-A-lead_zrc_nd_3p5m_guard-R1-0h` | A | 0 h | 1 | `lead_zrc_nd_3p5m_guard` | `baseline_snapshot` | medium_integrity |
| 6 | `ZRCND-A-lead_zrc_nd_3p5m_guard-R1-24h` | A | 24 h | 1 | `lead_zrc_nd_3p5m_guard` | `gate_evaluable` | medium_integrity |
| 7 | `ZRCND-A-no_module_static_control-R1-0h` | A | 0 h | 1 | `no_module_static_control` | `matched_control` | medium_integrity |
| 8 | `ZRCND-A-no_module_static_control-R1-24h` | A | 24 h | 1 | `no_module_static_control` | `matched_control` | medium_integrity |

## Interpretation

- `adaptive` mode recommends a small, high-information batch first; it is not enough for a suitability claim.
- A suitability claim still requires the readiness audit to pass with measured non-cell and biological rows.
- Keep all recommended rows tied to their deterministic `run_id` so evaluator and completeness checks can reuse them.
