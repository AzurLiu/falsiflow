# NHI-PEDOT H-A Sentinel Packet

**Data-entry template:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_sentinel_template.csv`
**Sample manifest:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_sentinel_sample_manifest.csv`
**Rows:** 12
**Recipe lock:** `nhi_pedot_alg_lam_lowdose_recipe_lock_v0_2`

This packet is for the first acellular direct-contact sentinel. It is not evidence until real measurements are entered.

## Measurement Rows

| Run | Timepoint | Article | Readouts |
| --- | --- | --- | --- |
| `NHIPEDOT-H-A-no_coating_mea_control-R1-0h` | 0 h | `no_coating_mea_control` | medium_integrity;physical_stability |
| `NHIPEDOT-H-A-no_coating_mea_control-R1-24h` | 24 h | `no_coating_mea_control` | medium_integrity;physical_stability |
| `NHIPEDOT-H-A-no_coating_mea_control-R1-72h` | 72 h | `no_coating_mea_control` | medium_integrity;physical_stability |
| `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h` | 0 h | `hydrogel_laminin_control` | medium_integrity;physical_stability |
| `NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h` | 24 h | `hydrogel_laminin_control` | medium_integrity;physical_stability |
| `NHIPEDOT-H-A-hydrogel_laminin_control-R1-72h` | 72 h | `hydrogel_laminin_control` | medium_integrity;physical_stability |
| `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-0h` | 0 h | `lead_nhi_pedot_low_loading` | medium_integrity;physical_stability |
| `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h` | 24 h | `lead_nhi_pedot_low_loading` | medium_integrity;physical_stability |
| `NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-72h` | 72 h | `lead_nhi_pedot_low_loading` | medium_integrity;physical_stability |
| `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h` | 0 h | `challenge_nhi_pedot_high_loading` | medium_integrity;physical_stability |
| `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h` | 24 h | `challenge_nhi_pedot_high_loading` | medium_integrity;physical_stability |
| `NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h` | 72 h | `challenge_nhi_pedot_high_loading` | medium_integrity;physical_stability |

## H-A Gate

- Compare medium-integrity drift to the matched `no_coating_mea_control` row with the same timepoint and replicate.
- Pass requires material-driven pH drift <= 0.10 pH units versus no-coating control.
- Pass requires osmolality and conductivity drift <= 5 percent versus no-coating control.
- Pass requires no visible precipitate, no visible shedding, swelling <= 20 percent, delamination score <= 0.5, and optical transparency >= 0.80.
- If the lead fails H-A, do not advance to H-B electrochemistry or H-C neural culture.

## Recipe Lock

- Candidate: `limina_alg_lam_pedot_lowdose_v0_2`
- Hydrogel matrix: `alginate_laminin_2pct_wv_caso4_dmem`
- Conductive phase: 0.6 wt percent PEDOT:PSS lead, selected from the published neural-culture loading
- First-claim boundary: no suitability claim until non-synthetic H-A/H-B/H-C and long-duration rows pass
- Replace `record_exact` labels with actual formulation/process values before treating rows as measured evidence.

## After Measurement

1. Fill the data-entry template with real values.
2. Use the template as an active runs CSV for `evaluate_nhi_pedot_runs.py`.
3. Re-run `suggest_nhi_pedot_next_measurements.py` to decide whether to continue, repeat, or stop.
