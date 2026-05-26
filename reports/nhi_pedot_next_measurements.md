# NHI-PEDOT Next Measurements

**Status:** `needs_h_a_sentinel`
**Reason:** `phase_h_a_sentinel_no_measured_rows`
**Evaluator status:** `no_data`
**Output CSV:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_next_measurements.csv`

## Replicate Coverage

Required passed lead replicates per phase: 3

| Phase | Passed lead replicates |
| --- | --- |
| H-A | - |
| H-B | - |
| H-C | - |

## Recommended Rows

| Priority | Run | Phase | Timepoint | Replicate | Article | Readouts |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | H-A | 0 h | 1 | `no_coating_mea_control` | medium_integrity;physical_stability |
| 2 | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | H-A | 24 h | 1 | `no_coating_mea_control` | medium_integrity;physical_stability |
| 3 | `NHIPEDOT-H-A-no_coating_mea_control-R1-72h` | H-A | 72 h | 1 | `no_coating_mea_control` | medium_integrity;physical_stability |
| 4 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | H-A | 0 h | 1 | `hydrogel_laminin_control` | medium_integrity;physical_stability |
| 5 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | H-A | 24 h | 1 | `hydrogel_laminin_control` | medium_integrity;physical_stability |
| 6 | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-72h` | H-A | 72 h | 1 | `hydrogel_laminin_control` | medium_integrity;physical_stability |
| 7 | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-0h` | H-A | 0 h | 1 | `lead_nhi_pedot_low_loading` | medium_integrity;physical_stability |
| 8 | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | H-A | 24 h | 1 | `lead_nhi_pedot_low_loading` | medium_integrity;physical_stability |
| 9 | `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-72h` | H-A | 72 h | 1 | `lead_nhi_pedot_low_loading` | medium_integrity;physical_stability |
| 10 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | H-A | 0 h | 1 | `challenge_nhi_pedot_high_loading` | medium_integrity;physical_stability |
| 11 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | H-A | 24 h | 1 | `challenge_nhi_pedot_high_loading` | medium_integrity;physical_stability |
| 12 | `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | H-A | 72 h | 1 | `challenge_nhi_pedot_high_loading` | medium_integrity;physical_stability |

## Interpretation

- H-A sentinel rows are the first decisive acellular material-contact check.
- H-B/H-C must not start if H-A lead rows fail medium-integrity or physical-stability gates.
- A real suitability claim still requires measured data; synthetic fixtures are evaluator regressions only.
