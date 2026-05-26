# NHI-PEDOT: Laminin-Anchored PEDOT:PSS Neural Hydrogel Interphase

**ID:** `limina_nhi_pedot_laminin_v0_1`
**Priority lane:** `LIMINA-Cell-1`
**Status:** `nominated`

A brain-soft, ECM-adhesive hydrogel interphase that embeds low-loading PEDOT:PSS conductive microdomains under a laminin or peptide-presenting top environment for cell-facing MEA coupling.

## Design Claim

A CL1-like neural culture interface should not optimize conductivity alone. A soft ECM-adhesive hydrogel can host sparse PEDOT:PSS conductive domains so that cells primarily experience a brain-like hydrated matrix while electrodes still gain a lower-impedance mixed-conducting bridge.

## Core Material Stack

| Layer | Material | Function |
| --- | --- | --- |
| MEA anchor and insulation boundary | Oxygen-plasma or dopamine-primed MEA surface with masked electrode windows and nonfouling insulation regions | Keep the hydrogel attached to the recording surface while preserving defined electrode access and optical inspection. |
| soft neural hydrogel matrix | GelMA, hyaluronic-acid, or alginate-based hydrogel tuned around brain-like low-kPa mechanics | Provide a hydrated, mechanically gentle environment for neuronal attachment, neurite extension, and medium diffusion. |
| mixed-conducting microdomain phase | Low-loading PEDOT:PSS domains or tracks, pre-rinsed and stabilized to reduce free PSS and acidic leachables | Lower local impedance and improve ionic/electronic coupling without making the whole surface polymer-dominated. |
| cell-instructive presentation layer | Laminin, laminin-derived peptides, or ECM-mimetic adhesive motifs presented above or within the hydrogel | Prevent the conductive phase from becoming a bare material challenge and guide neuronal adhesion, neurite outgrowth, and network formation. |

## Why This Is New For LIMINA

- It treats the electrode surface as a cell-adaptation material rather than a passive conductor.
- It separates the biological presentation layer from the conductive microdomain fraction.
- It makes PEDOT:PSS loading a dose-controlled design variable with explicit leachables and network-activity gates.
- It can be tested on MEA coupons before any closed CL1 hardware integration.

## Fit To Requirements

- `cell_adaptation`: Brain-soft hydrogel mechanics and laminin/peptide cues are selected to support neuronal adhesion, neurites, and maturation.
- `electrical_coupling`: PEDOT:PSS microdomains are selected to lower impedance and improve mixed ionic/electronic coupling.
- `avoid_leachables`: The design requires aggressive pre-rinse, extract testing, pH monitoring, and PEDOT:PSS dose control before live-cell exposure.
- `culture_stability`: Hydrogel swelling, delamination, photoinitiator residue, and PEDOT:PSS drift are treated as gating risks.
- `mea_integration`: The material is designed for coupon-level MEA testing with masked electrode windows and impedance tracking.
- `monitorability`: Optical transparency, thickness, swelling, EIS, and MEA network activity can all be monitored directly.

## Validation Plan

- Run acellular hydrogel extract and soak tests for pH, osmolality, conductivity, visible particulates, swelling, delamination, and PEDOT:PSS-related leachables.
- Measure electrochemical impedance, charge-storage capacity, optical transparency, and thickness drift before and after 37 C culture-medium soaking.
- Compare hydrogel-only, hydrogel-plus-laminin, low-PEDOT:PSS, and high-PEDOT:PSS articles on the same MEA coupon geometry.
- Only after material blank and electrochemical stability gates pass, run neural viability, neurite, morphology, and MEA network activity pilots.
- Rerank PEDOT:PSS loading and ECM presentation using measured toxicity, impedance, and network stability rather than conductivity alone.

## Kill Criteria

- Extracts or soaks produce pH/osmolality/conductivity drift outside neural medium tolerance or visible particulate/shedding.
- PEDOT:PSS loading reduces viability, neurite formation, or network activity relative to hydrogel-only and laminin controls.
- Impedance benefits are small compared with hydrogel-only controls or disappear after medium soaking.
- The hydrogel swells, delaminates, cracks, or occludes electrode windows under culture conditions.
- Optical access or MEA signal quality becomes worse than a simpler PDA-laminin or hydrogel-only coating.

## Open Questions

- Which matrix, GelMA, hyaluronic acid, or alginate-laminin, best balances CL1-like culture compatibility with manufacturability?
- What PEDOT:PSS loading gives enough impedance reduction without PSS/leachable or stiffness penalties?
- Should conductive domains be continuous tracks, sparse islands, or a very low-loading bulk phase?
- Can the hydrogel be sterilized or prepared aseptically without changing impedance, modulus, or ligand presentation?
- Does the material improve long-duration network stability compared with plain laminin-coated MEA controls?

## Internal Score

- `cell_compatibility`: 5
- `electrical_coupling`: 3
- `mechanical_match`: 5
- `culture_stability`: 3
- `mea_integration`: 4
- `novelty_upside`: 4
- `risk_control`: 4
- `weighted_internal_score`: 4.08

## Evidence Refs

- `pedot_brain_monitoring_2025`
- `pedot_bio_sei_2026`
- `conductive_hydrogels_2025`
- `hydrogel_neural_tissue_2020`
- `stiffness_sensing_2020`
- `gelma_pedot_composite_2018`
- `pedot_neural_culture_hydrogel_2025`
- `gelma_pedot_micropatterning_2026`
- `dnt_nam_viability_neurite_mea_2022`
- `neuronal_network_material_biocompatibility_mea_2013`
