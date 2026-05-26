# NHI-PEDOT H-A Minimum Real-Measurement Checklist

This compresses the first acellular H-A sentinel into the smallest practical execution view. It is not measured evidence.

**Status:** `awaiting_real_measurements`
**QC status:** `h_a_intake_not_ready`
**Runs:** 12
**Blank raw entries:** 228
**Raw template:** `/Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_raw_measurements_template.csv`

## Article-Timepoint Matrix

| Article | Role | Loading | Timepoints | Stop condition |
| --- | --- | ---: | --- | --- |
| `no_coating_mea_control` | matched medium/device control | 0 | 0 h, 24 h, 72 h | control is unstable or missing, because matched comparisons become invalid |
| `hydrogel_laminin_control` | soft matrix control | 0 | 0 h, 24 h, 72 h | hydrogel-only matrix fails, because PEDOT interpretation becomes confounded |
| `lead_nhi_pedot_low_loading` | 0.6 wt percent PEDOT:PSS lead | 0.006 | 0 h, 24 h, 72 h | lead shows pH drift >0.10 vs control, osmolality/conductivity drift >5%, shedding, swelling >0.20, delamination >0.5, or transparency <0.80 |
| `challenge_nhi_pedot_high_loading` | 1.2 wt percent PEDOT:PSS boundary comparator | 0.012 | 0 h, 24 h, 72 h | treat challenge as boundary only if it fails; do not promote to H-C |

## Claim-Critical Fields

| Field | Rows | Meaning |
| --- | ---: | --- |
| `conductivity_final_mS_cm` | 12 | final conductivity |
| `conductivity_initial_mS_cm` | 12 | initial conductivity |
| `date` | 12 | calendar date of the measurement event |
| `delamination_score` | 12 | 0 to 1 delamination score |
| `medium_lot` | 12 | actual medium lot |
| `medium_name` | 12 | actual medium or CL1-proxy medium name |
| `optical_transparency_fraction` | 12 | 0 to 1 optical transparency fraction |
| `osmolality_final_mOsm_kg` | 12 | final osmolality |
| `osmolality_initial_mOsm_kg` | 12 | initial osmolality |
| `pH_final` | 12 | final pH |
| `pH_initial` | 12 | initial pH |
| `swelling_fraction` | 12 | fractional swelling |
| `visible_precipitate` | 12 | visible precipitate, true or false |
| `visible_shedding` | 12 | visible material shedding, true or false |
| `temperature_c` | 3 | measurement/incubation temperature in C |

## Provenance Per Raw Row

- `measured_at`
- `operator_or_agent`
- `instrument_id`
- `source_file`

## Current QC Hotspots

| Field | Error rows |
| --- | ---: |
| `date` | 12 |
| `medium_name` | 12 |
| `medium_lot` | 12 |
| `pH_initial` | 12 |
| `pH_final` | 12 |
| `osmolality_initial_mOsm_kg` | 12 |
| `osmolality_final_mOsm_kg` | 12 |
| `conductivity_initial_mS_cm` | 12 |
| `conductivity_final_mS_cm` | 12 |
| `visible_precipitate` | 12 |
| `visible_shedding` | 12 |
| `swelling_fraction` | 12 |
| `delamination_score` | 12 |
| `optical_transparency_fraction` | 12 |
| `source_file` | 12 |
| `temperature_c` | 3 |

## After Filling Real Values

```bash
python3 scripts/run_limina_iteration.py
```

## Boundary

This checklist prepares data entry only. The material remains a hypothesis until QC-clean real rows pass H-A, H-B, H-C, long follow-up, and the final claim audit.
