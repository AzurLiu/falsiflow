# ZRC-ND Phase A Sentinel Packet

**Data-entry template:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_sentinel_template.csv`
**Sample manifest:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_sentinel_sample_manifest.csv`
**Rows:** 8

This packet is for the first non-cell material-blank sentinel measurement. It is not evidence until real measurements are entered.

## Measurement Rows

| Run | Timepoint | Article | Role | Required readouts |
| --- | --- | --- | --- | --- |
| `ZRCND-A-baseline_rc_3p5m_guard-R1-0h` | 0 h | `baseline_rc_3p5m_guard` | `baseline_snapshot` | medium_integrity |
| `ZRCND-A-baseline_rc_3p5m_guard-R1-24h` | 24 h | `baseline_rc_3p5m_guard` | `gate_evaluable` | medium_integrity |
| `ZRCND-A-challenge_zrc_nd_10m_guard-R1-0h` | 0 h | `challenge_zrc_nd_10m_guard` | `baseline_snapshot` | medium_integrity |
| `ZRCND-A-challenge_zrc_nd_10m_guard-R1-24h` | 24 h | `challenge_zrc_nd_10m_guard` | `gate_evaluable` | medium_integrity |
| `ZRCND-A-lead_zrc_nd_3p5m_guard-R1-0h` | 0 h | `lead_zrc_nd_3p5m_guard` | `baseline_snapshot` | medium_integrity |
| `ZRCND-A-lead_zrc_nd_3p5m_guard-R1-24h` | 24 h | `lead_zrc_nd_3p5m_guard` | `gate_evaluable` | medium_integrity |
| `ZRCND-A-no_module_static_control-R1-0h` | 0 h | `no_module_static_control` | `matched_control` | medium_integrity |
| `ZRCND-A-no_module_static_control-R1-24h` | 24 h | `no_module_static_control` | `matched_control` | medium_integrity |

## Phase A Gate

- Compare each material-exposed row to the matched `no_module_static_control` row with the same timepoint and replicate.
- Pass requires material-driven pH drift <= 0.10 pH units versus control.
- Pass requires osmolality and conductivity drift <= 5 percent versus control.
- Pass requires no visible precipitate or unresolved turbidity/extractables concern.

## After Measurement

1. Fill the data-entry template with real values.
2. Merge the measured CSV into an active runs file.
3. Run the validation evaluator and the next-measurement recommender.
