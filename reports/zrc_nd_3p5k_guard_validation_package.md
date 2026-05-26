# ZRC-ND-3.5M Guard validation package

**ID:** `zrc_nd_3p5k_guard_validation_v0_1`
**Lead variant:** `zrc_nd_3p5k_mpc_guard`
**Parent technology:** `limina_zrc_nd_v0_1`

## Objective

Determine whether the ZRC-ND-3.5M Guard lead is suitable to enter biological conditioned-medium follow-up by proving small-waste exchange, trophic-factor retention, low material interference, and stable module behavior in non-cell media tests.

## Scope

- `stage`: non-cell media-chemistry validation
- `claim_after_success`: Ready for conditioned-medium and biological follow-up, not yet proven safe for direct or long-duration neural culture use.
- `lead_design`: 3.5 kDa regenerated-cellulose dialysis membrane with MPC-like zwitterionic wetted-surface modification, low-binding PES/SFCA guard prefilter, and COC/COP monitored housing.
- `design_boundary`: Side-stream cartridge outside the cell chamber; no direct cell exposure before blank and recovery gates pass.
- `not_in_scope`: Final sterilization validation, GMP manufacturing, implantable/device claims, and CL1 API integration.

## Procurement Specs

| ID | Component | Required spec | Preferred format | Reject if | Evidence |
| --- | --- | --- | --- | --- | --- |
| `primary_rc_3p5k_membrane` | Primary exchange membrane | Regenerated-cellulose dialysis membrane or cassette, nominal 3.5 kDa MWCO, low nonspecific protein adsorption, aqueous medium compatibility, enough area to fabricate replicate coupons or small side-stream modules. | Closed cassette or flat/tubular membrane coupon that can be placed in an external loop without exposing cells to adhesives or unvalidated housing. | Cellulose ester only without regenerated-cellulose comparator, unknown MWCO, high protein binding, incompatible preservatives, or no usable extractables/handling information. | `rc_3p5k_repligen_vendor_spec`, `dialysis_mwco_principle_thermo`, `low_binding_rc_membrane_vendor` |
| `challenge_rc_10k_membrane` | High-clearance challenge membrane | Regenerated-cellulose dialysis membrane or cassette, nominal 10 kDa MWCO, same geometry class as the 3.5 kDa lead when possible. | Matched coupon or cassette for retention-clearance boundary testing. | Geometry, area, or handling differs enough that clearance cannot be compared to the 3.5 kDa lead. | `dialysis_mwco_principle_thermo`, `bdnf_uniprot_p23560`, `ngf_uniprot_p01138` |
| `low_binding_guard_prefilter` | Guard prefilter | Sterile low-protein-binding PES or SFCA filter, preferably 0.22 um for debris/sterility-style guarding in a short upstream position. | Small inline or syringe-filter format that can be bypassed for matched no-guard controls. | High protein binding, surfactant leaching risk, unknown membrane material, or large hold-up volume that changes medium composition. | `low_binding_membrane_media_technical` |
| `coc_cop_housing` | Observed side-stream housing | COC/COP or PEEK wetted housing with low extractables risk, optical observation of bubbles/precipitate, and ports for pH, conductivity, and flow/pressure monitoring. | COC/COP first, PEEK backup; avoid PDMS in the lead path unless adsorption is intentionally being tested. | PDMS as primary wetted housing, unknown adhesive exposure, opaque housing that prevents bubble checks, or no blank-extractables plan. | `organ_chip_perfusion_review_2022`, `coc_cop_ooc_material_review_2026`, `coc_pdms_sorption_2025` |
| `mpc_like_zwitterionic_surface` | Antifouling wetted-surface modification | Primary coupon route: PDA/polyMPC controlled surface-only deposition with pore-protection/backflow or equivalent pore-preserving process control. Backup routes: PMMMSi MPC-silane crosslinked brush or PSBMA cellulose brush only after the primary route fails a defined gate. | Thin, stable surface treatment with matched unmodified RC and housing controls, measured before and after coating for MWCO/transport shift. | Coating blocks low-MW transport, changes MWCO unpredictably, sheds measurable extractables, or lowers BDNF/NGF recovery. | `polympc_polyprev_retained_pore_2019`, `pda_click_pmpc_membrane_2025`, `zwitterionic_membrane_antifouling_2016`, `zwitterionic_cellulose_acetate_hfm_2026`, `psbma_cellulose_si_raft_2013` |

## Test Articles

| ID | Variant | Role | Description |
| --- | --- | --- | --- |
| `lead_zrc_nd_3p5m_guard` | `zrc_nd_3p5k_mpc_guard` | lead candidate | 3.5 kDa RC exchange element, MPC-like zwitterionic wetted-surface modification, low-binding PES/SFCA guard, COC/COP housing. |
| `baseline_rc_3p5m_guard` | `zrc_nd_3p5k_unmodified_guard` | unmodified baseline | 3.5 kDa RC exchange element with the same guard and housing but no zwitterionic modification. |
| `challenge_zrc_nd_10m_guard` | `zrc_nd_10k_mpc_guard` | high-clearance retention challenge | 10 kDa RC exchange element with the same zwitterionic/guard/housing concept. |
| `no_module_static_control` | `-` | stability and background control | Matched medium held without cartridge exposure. |
| `bulk_exchange_reference` | `-` | process reference | Conventional medium refresh reference for waste dilution and secretome dilution comparison. |

## Run Matrix

### Phase A: Fresh-medium material blank

**Purpose:** Detect pH, osmolality, conductivity, turbidity, and extractables shifts before any biological material is used.

**Inputs:** fresh complete neuronal medium or closest CL1-like medium proxy

**Articles:** `lead_zrc_nd_3p5m_guard`, `baseline_rc_3p5m_guard`, `challenge_zrc_nd_10m_guard`, `no_module_static_control`

**Minimum replicates:** 3

**Timepoints:** 0 h, 1 h, 4 h, 24 h

**Must pass before:** Phase B

### Phase B: Spiked recovery and clearance panel

**Purpose:** Measure whether the module removes lactate/ammonium-class wastes while retaining trophic proteins and bulk proteins.

**Inputs:** matched medium spiked with lactate, matched medium spiked with ammonium, BDNF or validated BDNF proxy, NGF or validated NGF proxy, albumin, transferrin

**Articles:** `lead_zrc_nd_3p5m_guard`, `baseline_rc_3p5m_guard`, `challenge_zrc_nd_10m_guard`, `no_module_static_control`

**Minimum replicates:** 3

**Timepoints:** 0 h, 1 h, 4 h, 24 h

**Must pass before:** Phase C

### Phase C: Conditioned-medium non-cell challenge

**Purpose:** Stress the cartridge with protein-rich or aged neural-conditioned medium without exposing live cells to unvalidated materials.

**Inputs:** conditioned medium or aged medium proxy, matched fresh medium blank

**Articles:** `lead_zrc_nd_3p5m_guard`, `baseline_rc_3p5m_guard`, `no_module_static_control`, `bulk_exchange_reference`

**Minimum replicates:** 3

**Timepoints:** 0 h, 4 h, 24 h, repeat exposure if fouling is low

**Must pass before:** Phase D biological pilot

## Assay Panel

| ID | Readout | Method class | Matrix | Control requirement | Evidence |
| --- | --- | --- | --- | --- | --- |
| `lactate_clearance` | Lactate concentration | colorimetric or enzymatic lactate assay | matched medium and conditioned-medium proxy | medium-matched calibration and spike/recovery control | `lactate_assay_cell_culture_vendor` |
| `ammonia_clearance` | Total ammonia/ammonium concentration | colorimetric or enzymatic ammonia assay | matched medium and conditioned-medium proxy | record pH; run standards in matched medium | `ammonia_assay_cell_culture_vendor`, `ammonia_importance_review_1996` |
| `bdnf_retention` | BDNF or BDNF-proxy recovery | ELISA or validated immunoassay | spiked medium and conditioned-medium proxy when available | matrix spike/recovery and no-cartridge stability control | `bdnf_uniprot_p23560`, `bdnf_elisa_cell_culture_vendor` |
| `ngf_retention` | NGF or NGF-proxy recovery | ELISA or validated immunoassay | spiked medium and conditioned-medium proxy when available | matrix spike/recovery and no-cartridge stability control | `ngf_uniprot_p01138`, `ngf_elisa_cell_culture_vendor` |
| `bulk_protein_retention` | Albumin, transferrin, and total protein recovery | protein-specific assay plus total protein assay | spiked matched medium | no-cartridge stability and unmodified RC baseline | `low_binding_membrane_media_technical`, `low_binding_rc_membrane_vendor` |
| `medium_integrity` | pH, osmolality, conductivity, turbidity, and visible precipitate | standard media chemistry and visual inspection | fresh medium blank and all recovery samples | same timepoints for no-module static control | `organ_chip_perfusion_review_2022` |
| `module_performance` | Flow resistance, bubble events, and apparent fouling/flux decline | inline flow/pressure proxy and observation log | all phases | record module geometry, membrane area, flow rate, and exposure time for normalization | `neural_microfluidic_systems_2023` |

## Acceptance Gates

| Gate | Criterion | Rationale | Failure response |
| --- | --- | --- | --- |
| `blank_integrity_gate` | Fresh-medium blank shows no material-driven pH drift greater than 0.10 pH units, no osmolality or conductivity drift greater than 5 percent versus no-module control, no visible precipitate/turbidity increase, and no unresolved extractables concern. | No biological follow-up should begin if the cartridge changes base medium chemistry. | Change housing, guard, coating, rinse/preconditioning, or membrane source before retesting. |
| `factor_retention_gate` | BDNF/NGF or validated proxy recovery is at least 90 percent versus no-module control, with albumin/transferrin/total protein recovery also at least 90 percent. | The lead is selected to preserve neural signaling context rather than maximize waste clearance. | Lower MWCO, remove or change guard/coating, or reduce adsorption-prone wetted area. |
| `waste_clearance_gate` | Lactate and total ammonia/ammonium decrease at least 25 percent more than no-module control over the chosen exposure window without violating retention or blank-integrity gates. | The module must show useful waste exchange, not just passive compatibility. | Increase membrane area/exposure, consider 10 kDa challenge data, or add a second-stage confined polishing module. |
| `fouling_stability_gate` | Flow resistance or pressure proxy changes less than 20 percent during the test window, and clearance/retention does not degrade across repeat exposure. | A wetware life-support cartridge must fail visibly and slowly, not silently strip or clog. | Improve prefilter, surface modification, geometry, or cleaning/preconditioning strategy. |
| `lead_superiority_gate` | The lead must outperform unmodified 3.5 kDa RC on fouling or protein recovery while remaining safer than the 10 kDa challenge on retention. | This gate tests whether the zwitterionic lead adds value beyond a simple RC baseline. | If unmodified RC performs equally well, downselect to simpler RC-3.5K Guard; if 10 kDa retains factors adequately, rerank the variants. |

## Data Capture Fields

- `run_id`
- `date`
- `operator_or_agent`
- `phase`
- `timepoint`
- `replicate`
- `article_id`
- `variant_id`
- `control_article_id`
- `membrane_lot`
- `mwco_kda`
- `membrane_area_cm2`
- `surface_modification`
- `prefilter_lot`
- `housing_material`
- `medium_name`
- `medium_lot`
- `initial_volume_ml`
- `flow_rate_ul_min`
- `exposure_time_h`
- `temperature_c`
- `pH_initial`
- `pH_final`
- `osmolality_initial_mOsm_kg`
- `osmolality_final_mOsm_kg`
- `conductivity_initial_mS_cm`
- `conductivity_final_mS_cm`
- `lactate_initial_mM`
- `lactate_final_mM`
- `ammonia_initial_uM`
- `ammonia_final_uM`
- `bdnf_initial_pg_ml`
- `bdnf_final_pg_ml`
- `ngf_initial_pg_ml`
- `ngf_final_pg_ml`
- `albumin_initial`
- `albumin_final`
- `transferrin_initial`
- `transferrin_final`
- `total_protein_initial`
- `total_protein_final`
- `flow_resistance_initial`
- `flow_resistance_final`
- `bubble_events`
- `visible_precipitate`
- `gate_results`
- `notes`

## Decision Rules

| Condition | Action |
| --- | --- |
| All acceptance gates pass for ZRC-ND-3.5M Guard | Promote the technology from nominated to validation-passed-for-non-cell-media and design Phase D biological conditioned-medium pilot. |
| Blank integrity passes, retention passes, but waste clearance fails | Keep 3.5 kDa as retention-safe baseline and optimize membrane area, exposure time, or a confined second-stage polishing module. |
| Blank integrity passes, clearance passes, but factor retention fails | Reject the lead geometry for CL1-like neural medium and move to lower MWCO or lower-adsorption wetted surfaces. |
| Zwitterionic lead does not beat unmodified 3.5 kDa RC | Demote the coating to optional; simplify toward RC-3.5K Guard until fouling data justify added chemistry. |
| 10 kDa challenge passes retention and improves clearance | Rerun variant screen with measured retention/clearance values and reconsider 10 kDa as lead. |
| Any material blank fails | Do not expose cells; replace the suspect material or preconditioning workflow and repeat Phase A. |

## Source Refs

- `rc_3p5k_repligen_vendor_spec`
- `dialysis_medium_partitioning_2020`
- `dialysis_mwco_principle_thermo`
- `low_binding_membrane_media_technical`
- `low_binding_rc_membrane_vendor`
- `polympc_polyprev_retained_pore_2019`
- `pda_click_pmpc_membrane_2025`
- `zwitterionic_membrane_antifouling_2016`
- `zwitterionic_cellulose_acetate_hfm_2026`
- `zwitterionic_peptide_membrane_2025`
- `psbma_cellulose_si_raft_2013`
- `coc_cop_ooc_material_review_2026`
- `coc_pdms_sorption_2025`
- `lactate_assay_cell_culture_vendor`
- `ammonia_assay_cell_culture_vendor`
- `bdnf_elisa_cell_culture_vendor`
- `ngf_elisa_cell_culture_vendor`
- `organ_chip_perfusion_review_2022`
- `neural_microfluidic_systems_2023`
