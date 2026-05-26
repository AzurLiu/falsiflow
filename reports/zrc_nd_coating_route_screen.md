# ZRC-ND Coating Route Screen

This is a route-prioritization model, not evidence that a coating is safe or effective in neural medium.

**Lead route:** `pda_polympc_polyprev_surface_only` - PDA/polyMPC surface-only controlled deposition
**Lead score:** 0.727

## Ranking

| Rank | Status | Score | Route | Class | Gate failures |
| ---: | --- | ---: | --- | --- | --- |
| 1 | lead_route | 0.727 | PDA/polyMPC surface-only controlled deposition | surface_only_pda_polympc | - |
| 2 | screen | 0.668 | PDA-click PMPC grafting-to | pda_click_grafting_to | - |
| 3 | screen | 0.734 | PMMMSi MPC-silane crosslinked brush | crosslinked_mpc_silane | implementation_feasibility |
| 4 | screen | 0.678 | PSBMA SI-RAFT cellulose brush | cellulose_grafted_sulfobetaine | pore_preservation, implementation_feasibility, extractables_safety |
| 5 | control | 0.787 | Unmodified regenerated-cellulose surface control | no_coating_control | antifouling_evidence |

## Lead Route Detail

**Chemistry:** Thin PDA primer plus polyMPC antifouling layer, deposited with pore-protection/backflow or equivalent surface-only control.

**Intended role:** first coating route for ZRC-ND-3.5M Guard coupon testing

### Metrics

- `pore_preservation`: 0.88
- `antifouling_evidence`: 0.82
- `cellulose_relevance`: 0.55
- `implementation_feasibility`: 0.7
- `extractables_safety`: 0.62
- `coating_durability`: 0.6
- `novelty_upside`: 0.75

### Advantages

- Directly addresses the low-MWCO pore-clogging risk by prioritizing surface-only deposition.
- Uses MPC-like zwitterionic chemistry already aligned with the ZRC-ND lead.
- Can be screened on coupons against an unmodified RC control before cartridge commitment.

### Risks

- PDA/polyMPC extractables and color/adsorption effects must be checked.
- Evidence is from ultrafiltration membranes, not 3.5 kDa regenerated cellulose.
- Requires process control to keep coating out of pores.

### Evidence Refs

- `polympc_polyprev_retained_pore_2019`
- `pda_click_pmpc_membrane_2025`
- `zwitterionic_membrane_antifouling_2016`

## Interpretation

For the first ZRC-ND-3.5M Guard coupon run, the coating route should protect the 3.5 kDa membrane pores before it tries to maximize coating density. The selected PDA/polyMPC controlled-deposition route is therefore a practical first coating route, while unmodified RC remains a mandatory baseline and PMMMSi MPC-silane remains the advanced durability backup.

## Required Next Evidence

- Coupon-level BDNF/NGF and albumin recovery after coating.
- Measured lactate/ammonium exchange before and after coating.
- Fresh-medium extractables and pH/conductivity/osmolality drift for PDA/polyMPC.
- Fouling drift versus unmodified RC in protein-rich conditioned-medium proxy.

## Weights

- `pore_preservation`: 0.24
- `antifouling_evidence`: 0.2
- `cellulose_relevance`: 0.16
- `implementation_feasibility`: 0.12
- `extractables_safety`: 0.12
- `coating_durability`: 0.1
- `novelty_upside`: 0.06

## Gates

- `pore_preservation` >= 0.7
- `antifouling_evidence` >= 0.65
- `implementation_feasibility` >= 0.55
- `extractables_safety` >= 0.55
