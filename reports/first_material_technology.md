# ZRC-ND: Zwitterionic Regenerated-Cellulose Neurodialysis Cartridge

**ID:** `limina_zrc_nd_v0_1`
**Priority lane:** `LIMINA-External-1`
**Status:** `nominated`

A side-stream, MWCO-graded regenerated-cellulose dialysis cartridge with a low-fouling zwitterionic hydration layer to remove lactate/ammonium-class small wastes while preserving neurotrophic proteins and secretome signals.

## Design Claim

A passive side-stream neurodialysis cartridge can be made more suitable for long-lived neural wetware by combining MWCO-based small-waste exchange with low-fouling zwitterionic surface chemistry, rather than relying on bulk medium exchange or broad adsorbent beds.

## Core Material Stack

| Layer | Material | Function |
| --- | --- | --- |
| low-binding prefilter | PES or SFCA membrane in a short upstream guard position | Remove debris while minimizing protein/growth-factor adsorption. |
| primary selective exchange membrane | Regenerated cellulose dialysis membrane, first screened at 3.5 kDa and 10 kDa MWCO | Exchange lactate, ammonium/ammonia, salts, and other low-MW waste while retaining high-MW trophic proteins. |
| antifouling hydration layer | Thin zwitterionic graft/coating such as sulfobetaine, carboxybetaine, or MPC-like chemistry on the medium-facing membrane/housing surfaces | Reduce protein fouling and preserve membrane performance in protein-rich neuronal medium. |
| monitoring and safety shell | Low-leachable COC/COP or PEEK cartridge body with pH, conductivity, pressure/flow, and bubble observation points | Keep the waste cartridge outside the cell chamber and make silent failure detectable. |

## Why This Is New For LIMINA

- It treats culture medium as a signaling environment, not a disposable buffer.
- It separates waste removal from cell exposure by using a side-stream cartridge.
- It combines size-selective regenerated cellulose dialysis with antifouling zwitterionic chemistry for neural-medium preservation.
- It explicitly optimizes for both waste clearance and BDNF/NGF/albumin/transferrin retention.

## Fit To Requirements

- `remove_lactate_ammonium`: Supported by low-MW dialysis/exchange rationale; needs quantitative clearance tests.
- `preserve_growth_factors`: Supported by MWCO retention logic and low-binding membrane evidence; needs BDNF/NGF recovery data.
- `avoid_leachables`: Material family is plausible, but cartridge body, coating, sterilization, and extractables must be tested.
- `avoid_protein_stripping`: Zwitterionic/low-binding surfaces are selected specifically to reduce fouling; recovery assays are mandatory.
- `culture_stability`: Passive side-stream design reduces direct cell exposure; long-duration 37 C fouling and drift remain open.
- `monitorability`: Side-stream shell includes pH, conductivity, flow/pressure, and bubble observation points.

## Validation Plan

- Run fresh-medium blank through the module to detect pH, osmolality, conductivity, turbidity, and extractables shifts.
- Run spiked recovery panel for lactate, ammonium, BDNF/NGF proxy, albumin, transferrin, and total protein.
- Compare 3.5 kDa versus 10 kDa RC MWCO before adding active polishing.
- Compare unmodified RC against zwitterionic-modified RC/housing surfaces for protein recovery and fouling drift.
- Only after media-chemistry gates pass, test neuronal conditioned-media viability and morphology.

## Kill Criteria

- BDNF/NGF or proxy neurotrophic factor recovery is unacceptably low at useful clearance.
- Fresh-medium blank shows meaningful leachables, pH drift, osmolality drift, or conductivity drift.
- Flow resistance or fouling drifts rapidly under protein-rich medium.
- The zwitterionic coating changes MWCO/permeability so much that waste clearance is no longer useful.
- Bulk medium exchange outperforms the cartridge even after accounting for secretome dilution.

## Open Questions

- Which MWCO gives the best retention-clearance balance for the actual CL1-like medium?
- Can zwitterionic modification be applied without clogging low-MWCO RC pores?
- Is coating the cartridge housing enough, or must the membrane surface itself be modified?
- Does retaining secretome signals improve neural network stability relative to bulk medium exchange?
- Which low-leachable cartridge housing material is best: COC/COP, PEEK, glass, or another option?

## Internal Score

- `target_selectivity`: 4
- `growth_factor_retention`: 5
- `low_leachables`: 3
- `culture_stability`: 3
- `integration_complexity`: 3
- `monitorability`: 5
- `novelty_upside`: 5
- `risk_control`: 3
- `weighted_internal_score`: 4.02

## Evidence Refs

- `dialysis_medium_partitioning_2020`
- `ammonia_importance_review_1996`
- `lactate_ammonia_growth_inhibition_1991`
- `inhibitory_metabolites_2021`
- `low_binding_membrane_media_technical`
- `low_binding_rc_membrane_vendor`
- `zwitterionic_membrane_antifouling_2016`
- `zwitterionic_cellulose_acetate_hfm_2026`
- `bdnf_uniprot_p23560`
- `ngf_uniprot_p01138`
- `dialysis_mwco_principle_thermo`
- `neural_microfluidic_systems_2023`
