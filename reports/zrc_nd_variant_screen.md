# ZRC-ND Variant Screen

This is a heuristic design-prioritization model, not an experimental result.

**Lead variant:** `zrc_nd_3p5k_mpc_guard` - ZRC-ND-3.5M Guard
**Lead score:** 0.811

## Ranking

Rows are ordered by gate pass first, then composite score.

| Rank | Status | Score | Variant | MWCO | Surface | Gate failures |
| ---: | --- | ---: | --- | ---: | --- | --- |
| 1 | lead | 0.811 | ZRC-ND-3.5M Guard | 3.5 | mpc_like_zwitterionic | - |
| 2 | screen | 0.761 | RC-3.5K Guard Baseline | 3.5 | none | - |
| 3 | screen | 0.812 | ZRC-ND-10M Guard | 10.0 | mpc_like_zwitterionic | factor_retention |
| 4 | screen | 0.777 | ZRC-ND-20M Guard | 20.0 | mpc_like_zwitterionic | factor_retention |
| 5 | screen | 0.763 | ZRC-ND-1M Guard | 1.0 | mpc_like_zwitterionic | waste_clearance |
| 6 | screen | 0.756 | RC-10K No-Guard High-Clearance Baseline | 10.0 | none | factor_retention |

## Lead Metric Detail

**Design intent:** Conservative lead variant prioritizing trophic-factor retention and fouling resistance while preserving useful lactate/ammonium exchange.

- `waste_clearance`: 0.565
- `factor_retention`: 0.98
- `fouling_control`: 0.9
- `leachable_safety`: 0.764
- `integration`: 0.773
- `monitorability`: 0.85
- `novelty`: 0.848

## Lead Evidence Refs

- `dialysis_medium_partitioning_2020`
- `low_binding_membrane_media_technical`
- `zwitterionic_membrane_antifouling_2016`
- `zwitterionic_cellulose_acetate_hfm_2026`
- `bdnf_uniprot_p23560`
- `ngf_uniprot_p01138`
- `dialysis_mwco_principle_thermo`

## Model Weights

- `waste_clearance`: 0.2
- `factor_retention`: 0.24
- `fouling_control`: 0.14
- `leachable_safety`: 0.14
- `integration`: 0.1
- `monitorability`: 0.08
- `novelty`: 0.1

## Gates

- `waste_clearance` >= 0.5
- `factor_retention` >= 0.9
- `leachable_safety` >= 0.65
- `integration` >= 0.58

## Interpretation

The lead favors 3.5 kDa regenerated cellulose because the model treats trophic-factor retention as more important than maximum waste clearance for the first neural-medium cartridge. The MPC-like zwitterionic layer raises fouling control and protein-retention confidence, but it remains a validation risk because coating chemistry can change permeability and introduce extractables.

## Required Next Evidence

- Measured lactate and ammonium clearance for 3.5 kDa versus 10 kDa RC.
- BDNF/NGF or proxy trophic-factor recovery across unmodified and zwitterionic surfaces.
- Fresh-medium blank extractables, pH, osmolality, and conductivity drift.
- Fouling/flow-resistance drift in protein-rich conditioned medium.
