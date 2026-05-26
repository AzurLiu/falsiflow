# Regenerated-cellulose MWCO baseline for selective neuronal-media waste exchange

**ID:** `external1_rc_dialysis_mwco_baseline_v0_1`
**Priority lane:** `LIMINA-External-1`

## Objective

Identify a passive side-stream dialysis architecture that removes low-molecular-weight waste from neuronal culture medium while preserving protein/growth-factor signals.

## Hypothesis

Regenerated-cellulose membranes with lower MWCO values will preserve trophic proteins better, while higher MWCO values will clear lactate/ammonium faster but may leak useful signaling molecules. A side-stream design can reveal the useful trade-off without exposing cells to unvalidated cartridge materials.

## Scope

- `design_level`: screening experiment design, not a wet-lab SOP
- `system_context`: CL1-like neural wetware life-support loop
- `cartridge_position`: side-stream or external loop, not directly in the cell chamber
- `primary_material_family`: regenerated cellulose dialysis membrane
- `first_question`: Which MWCO range best balances small-waste clearance and trophic-factor retention?

## Test Articles

| ID | Name | Rationale | Expected trade-off |
| --- | --- | --- | --- |
| `rc_1kda` | Regenerated cellulose, 1 kDa MWCO | Most conservative retention option; expected to preserve trophic proteins but may clear waste slowly. | high retention, low clearance |
| `rc_3_5kda` | Regenerated cellulose, 3.5 kDa MWCO | Common small-molecule dialysis cutoff; expected to retain BDNF/NGF-sized proteins while allowing lactate/ammonium exchange. | high retention, moderate clearance |
| `rc_10kda` | Regenerated cellulose, 10 kDa MWCO | Potential clearance/retention compromise; may preserve BDNF dimer while risking partial NGF or monomeric factor loss. | moderate retention, higher clearance |
| `rc_20kda` | Regenerated cellulose, 20 kDa MWCO | Stress-test high-clearance option; useful to quantify whether trophic-factor leakage becomes unacceptable. | highest clearance, highest protein-factor leakage risk |
| `low_binding_prefilter_rc_3_5kda` | Low-binding PES/SFCA prefilter plus 3.5 kDa RC dialysis | Tests whether debris control can be added before dialysis without stripping proteins. | better debris control, added adsorption risk |

## Controls

| ID | Control | Purpose |
| --- | --- | --- |
| `static_no_cartridge` | Static conditioned medium, no cartridge | Measures waste accumulation and factor stability without exchange. |
| `bulk_medium_exchange` | Bulk medium exchange reference | Represents conventional refresh behavior and secretome dilution risk. |
| `fresh_medium_blank` | Fresh medium blank through each module | Detects extractables, pH/osmolality drift, and baseline adsorption without cell-derived waste. |
| `spiked_recovery_panel` | Medium spiked with albumin, BDNF/NGF analog panel, lactate, and ammonium | Separates material retention/clearance behavior from biological variability. |

## Readouts

### Waste Clearance

- lactate concentration before/after cartridge exposure
- ammonium/ammonia concentration before/after cartridge exposure
- optional targeted metabolite panel for unknown inhibitory metabolites

### Factor Retention

- BDNF recovery or proxy neurotrophic protein recovery
- NGF recovery or proxy neurotrophic protein recovery
- albumin recovery
- transferrin recovery
- total protein recovery

### Medium Integrity

- pH drift
- osmolality drift
- conductivity drift
- visible precipitation or turbidity
- extractables screen if available

### Module Performance

- flow resistance or pressure proxy
- bubble formation events
- fouling or flux decline
- post-run membrane visual inspection

### Biological Followup

- neuronal conditioned-media viability screen
- neurite outgrowth or morphology screen
- network activity/MEA readout only after media-chemistry gates pass

## Decision Gates

| Gate | Criterion | Failure response |
| --- | --- | --- |
| `factor_retention_gate` | Prefer variants that retain high-molecular-weight trophic proteins and albumin while avoiding broad protein loss. | If retention is poor, move to lower MWCO or add zwitterionic/low-fouling membrane modification. |
| `clearance_gate` | Require measurable lactate and ammonium exchange relative to no-cartridge control. | If clearance is weak at acceptable retention, consider larger membrane area, longer side-stream exposure, or a polishing stage. |
| `medium_integrity_gate` | Reject variants causing unacceptable pH, osmolality, conductivity, turbidity, or extractables shifts. | Change membrane handling, module housing, sterilization workflow, or material family. |
| `no_silent_stripping_gate` | Reject nonselective adsorbers that reduce useful factors even if waste removal is strong. | Keep broad adsorbents out of the cell-facing life-support path unless tightly confined and analytically monitored. |

## Risk Controls

| Risk | Detection |
| --- | --- |
| MWCO removes helpful small molecules or secretome factors | Compare targeted factor recovery and total protein before/after; add metabolomics in later rounds. |
| Membrane or housing leachables harm neurons | Run fresh-medium blanks through each module before any biological followup. |
| Fouling changes performance over time | Track flow resistance and clearance/retention across repeated or aged-medium exposures. |
| Bulk exchange outperforms cartridge in short-term tests | Compare against bulk exchange, but evaluate secretome dilution as a separate cost. |

## Next Decisions

| Condition | Action |
| --- | --- |
| 3.5 kDa or 10 kDa RC clears waste and preserves trophic factors | Use that MWCO as the passive baseline and test membrane area/flow geometry. |
| Retention is strong but clearance is weak | Increase membrane area or exposure before adding active polishing. |
| Clearance is strong but trophic-factor loss is high | Lower MWCO and prioritize zwitterionic/low-fouling membrane surfaces. |
| Passive dialysis cannot meet clearance targets | Evaluate ICP or confined ion-exchange side-stream module as a second-stage polish. |

## Source Refs

- `dialysis_medium_partitioning_2020`
- `ammonia_importance_review_1996`
- `lactate_ammonia_growth_inhibition_1991`
- `inhibitory_metabolites_2021`
- `neural_microfluidic_systems_2023`
- `bdnf_uniprot_p23560`
- `ngf_uniprot_p01138`
- `dialysis_mwco_principle_thermo`
