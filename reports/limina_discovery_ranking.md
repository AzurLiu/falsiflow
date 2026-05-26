# LIMINA Discovery Ranking

This ranks material-technology prospects by how quickly they can generate defensible evidence toward the first suitability claim. It is not a suitability claim.

**Top prospect:** `limina_alg_lam_pedot_lowdose_v0_2`
**Priority:** `promote_now`
**Weighted score:** `4.285`

## Ranked Prospects

| Rank | Priority | Score | Prospect | Lane | Near-term test | Main risks |
| ---: | --- | ---: | --- | --- | --- | --- |
| 1 | `promote_now` | 4.285 | `limina_alg_lam_pedot_lowdose_v0_2` | LIMINA-Cell-1 | Lock the H-A sentinel to alginate-laminin low-dose PEDOT:PSS and fill acellular medium, physical stability, and electrochemical fields before any live-cell expansion. | PEDOT:PSS or PSS-related extractables could still harm long-lived cultures.; Hydrogel swelling or delamination can erase electrochemical benefits.; Published neural culture format must be adapted to the actual MEA geometry. |
| 2 | `parallel_screen` | 3.670 | `limina_pda_anchor_alg_lam_pedot_window_v0_1` | LIMINA-Cell-1 | Add one anchored lead article to H-B electrochemical/physical stability only after the acellular H-A blank passes for the unanchored low-dose lead. | Primer chemistry may add its own extractables.; Localized conductive domains may be harder to fabricate reproducibly.; Anchoring can improve stability while reducing softness at the cell interface. |
| 3 | `parallel_screen` | 3.500 | `limina_all_dry_zwitterionic_external_v0_1` | LIMINA-External-1 | Run as a coating-on-housing comparator after ZRC-ND Phase A sentinel defines whether adsorption/fouling is the limiting failure mode. | Coating could change extractables or optical inspection properties.; It may not solve protein loss if the MWCO membrane itself dominates adsorption.; Not yet validated in CL1-like neuronal medium. |
| 4 | `watch` | 3.192 | `limina_alg_gel_pedot_ppy_lowoxidant_v0_1` | LIMINA-Cell-1 | Use only after ALG-LAM-PEDOT H-A/H-B establishes a baseline; run as an acellular H-B conductivity/stability comparator with strict extract and shedding fields. | Fibroblast cytocompatibility is not a neuronal-network compatibility claim.; PPy oxidation chemistry can leave residues that matter in long-lived neural cultures.; High conductivity may trade off with optical transparency or softness. |
| 5 | `watch` | 3.171 | `limina_zwitterionic_pedot_hydrogel_v0_1` | LIMINA-Cell-1 | Do not displace ALG-LAM-PEDOT yet; use as a later comparator if acellular extract and impedance data look better than the alginate-laminin lead. | In vivo electrode evidence does not prove in vitro neuronal network compatibility.; Zwitterionic monomers and crosslinkers can create new leachable risks.; Fabrication complexity may slow the first suitability claim. |
| 6 | `hold` | 3.198 | `limina_pedot_sgagh_ecm_signal_hydrogel_v0_1` | LIMINA-Cell-1 | Keep behind ALG-LAM-PEDOT until a small H-A/H-B witness coupon can show clean extract behavior, stable pH/osmolality/conductivity, retained BDNF/laminin signal, and no delamination. | High novelty comes with synthesis, procurement, and reproducibility uncertainty.; Growth-factor binding is attractive but could perturb neuronal differentiation or maturation in unwanted directions.; No direct long-duration human neuronal-network compatibility evidence yet. |
| 7 | `hold` | 3.170 | `limina_hydrogel_actuated_multilayer_3d_mea_v0_1` | LIMINA-Cell-1 | Keep as a device-architecture horizon scan; extract a simplified witness-coupon plan only after the planar ALG-LAM-PEDOT H-A/H-B route has real data. | Fabrication is much harder than a planar witness coupon.; Pt-black, PDMS, and actuator hydrogels each need extractables, adsorption, and stability checks.; Organoid electrophysiology evidence does not directly prove compatibility with the current CL1-like planar path. |
| 8 | `hold` | 3.067 | `limina_anisotropic_spedot_psbma_hydrogel_v0_1` | LIMINA-Cell-1 | Do not displace ALG-LAM-PEDOT. If formulation access is practical, run a tiny acellular witness coupon for pH, osmolality, conductivity, protein adsorption, swelling, delamination, transparency, and 1 kHz impedance before any neural work. | Physiological monitoring evidence is not direct neuronal-network compatibility evidence.; Zwitterionic antifouling chemistry may interfere with laminin presentation unless a cell-adhesion layer is engineered.; Synthesis and alignment may be harder to reproduce than the current alginate-laminin PEDOT:PSS route. |
| 9 | `hold` | 2.802 | `limina_cameo_cnt_organoid_frame_v0_1` | LIMINA-Cell-1 | Do not place in first-claim path; use as a literature/device benchmark until CNT exposure, particle release, and long-duration neural health risks are bounded. | CNT exposure is a major long-duration neural culture uncertainty.; The value may be device geometry rather than material chemistry.; Fabrication may not be accessible on the current local project timeline. |
| 10 | `hold` | 2.799 | `limina_op_apa_fillerfree_hydrogel_v0_1` | LIMINA-Cell-1 | Keep as literature-watch until formulation access, independent replication, extract chemistry, and neural culture compatibility are clearer. | Preprint-level evidence.; Reproducibility and sourcing are uncertain.; First proof requires more materials work before coupon validation. |
| 11 | `hold` | 2.761 | `limina_entangled_zwitterionic_mechanoadaptive_matrix_v0_1` | LIMINA-Cell-1 | Do not promote yet; first require extract chemistry, laminin presentation, neural adhesion, and medium-stability witness coupons. | No direct neural-network or MEA evidence yet.; Zwitterionic non-fouling behavior may resist the very protein adhesion needed for neurons.; Synthesis and functionalization need a clearer near-term recipe before coupon testing. |
| 12 | `hold` | 2.597 | `limina_mxene_gel_oha_sensing_hydrogel_v0_1` | LIMINA-Cell-1 | Use only as an acellular extract and impedance comparator after safer PEDOT:PSS and hydrogel-only leads establish a baseline. | Nanomaterial leaching or particle shedding could dominate neural toxicity.; Adhesive performance may not translate to transparent MEA culture.; The proof gap is larger than for PEDOT:PSS hydrogel routes. |

## Evidence And Rationale

### limina_alg_lam_pedot_lowdose_v0_2

- Name: ALG-LAM-PEDOT Low-Dose Neural Hydrogel Interphase
- Status: `promote_to_recipe_specific_validation`
- Why it matters: This is the shortest path to a real suitability claim because it has direct 28-day human iPSC cortical neuron culture evidence and can reuse the existing H-A/H-B/H-C plus long-duration NHI-PEDOT gates.
- Evidence: [pedot_neural_culture_hydrogel_2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12620795/), [pedot_brain_monitoring_2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12075682/), [hydrogel_neural_tissue_2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7014813/), [dnt_nam_viability_neurite_mea_2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9421662/)
- Gate failures: none.

### limina_pda_anchor_alg_lam_pedot_window_v0_1

- Name: PDA-Anchored ALG-LAM-PEDOT Electrode-Window Interphase
- Status: `parallel_design_variant`
- Why it matters: If the current NHI-PEDOT lead fails by delamination or window occlusion rather than biology, this variant gives a fast rescue path without changing the main biological presentation concept.
- Evidence: [pedot_neural_culture_hydrogel_2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12620795/), [pedot_brain_monitoring_2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12075682/), [gelma_pedot_micropatterning_2026](https://www.nature.com/articles/s41528-026-00529-5), [neuronal_network_material_biocompatibility_mea_2013](https://pubmed.ncbi.nlm.nih.gov/24176966/)
- Gate failures: none.

### limina_all_dry_zwitterionic_external_v0_1

- Name: All-Dry Zwitterionic Gradient External-Fluidic Coating
- Status: `external_surface_rescue_candidate`
- Why it matters: This can improve the ZRC-ND external branch without risking direct cell-contact exposure, and it is especially useful if the Phase A sentinel shows protein adsorption or fouling rather than MWCO failure.
- Evidence: [all_dry_zwitterionic_gradient_2024](https://pubmed.ncbi.nlm.nih.gov/39567918/), [zwitterionic_membrane_antifouling_2016](https://pubmed.ncbi.nlm.nih.gov/27025359/), [zwitterionic_cellulose_acetate_hfm_2026](https://link.springer.com/article/10.1557/s43579-026-00933-y), [organ_chip_perfusion_review_2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9966054/)
- Gate failures: none.

### limina_alg_gel_pedot_ppy_lowoxidant_v0_1

- Name: Alg-Gel PEDOT/PPy Low-Oxidant Biointerface Comparator
- Status: `electrochemical_comparator_candidate`
- Why it matters: It has a large optimization surface for conductivity, impedance, and wet stability, but the PPy route adds residue and leachable risk that makes it a comparator rather than the first living-network claim path.
- Evidence: [alg_gel_pedot_ppy_biointerface_2026](https://pubs.rsc.org/en/content/articlelanding/2026/tb/d5tb02148k), [gelma_pedot_composite_2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC11150039/), [conductive_hydrogels_2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12840763/), [iso_10993_5_cytotoxicity_extract_fda](https://www.fda.gov/media/85865/download)
- Gate failures: none.

### limina_zwitterionic_pedot_hydrogel_v0_1

- Name: Zwitterionic PEDOT:PSS Hydrated Electrode Hydrogel
- Status: `watch_for_second_wave`
- Why it matters: It may solve the core NHI-PEDOT tension between hydrated cell compatibility and electrical coupling, but the current evidence is more implant/electrode oriented than CL1-like culture oriented.
- Evidence: [zwitterionic_pedot_eeg_hydrogel_2025](https://pubmed.ncbi.nlm.nih.gov/40801064/), [pedot_brain_monitoring_2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12075682/), [pedot_bio_sei_2026](https://www.mdpi.com/2073-4360/18/1/20), [conductive_hydrogels_2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12840763/)
- Gate failures: none.

### limina_pedot_sgagh_ecm_signal_hydrogel_v0_1

- Name: PEDOT:sGAGh Electronic ECM Signal Hydrogel
- Status: `high_novelty_horizon_scan`
- Why it matters: This is one of the most interesting new design spaces because it may move beyond passive biocompatibility into controllable biochemical cue presentation, but it has not yet earned first-claim status for CL1-like neuronal networks.
- Evidence: [pedot_sgagh_electronic_ecm_2026](https://pubmed.ncbi.nlm.nih.gov/41883146/), [pedot_bio_sei_2026](https://www.mdpi.com/2073-4360/18/1/20), [conductive_hydrogels_2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12840763/), [hydrogel_neural_tissue_2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7014813/)
- Gate failures:
  - measurement_accessibility below 3: The next claim candidate must be testable with near-term coupon, medium, or simple material measurements.

### limina_hydrogel_actuated_multilayer_3d_mea_v0_1

- Name: Hydrogel-Actuated Multilayer 3D Organoid MEA Interface
- Status: `3d_organoid_horizon_scan`
- Why it matters: If the project shifts from planar neuronal cultures toward organoids or neural aggregates, depth-resolved and mechanically adaptive electrode geometries may matter as much as hydrogel chemistry.
- Evidence: [mlmea_organoid_depth_interface_2026](https://www.nature.com/articles/s41378-026-01328-8), [eflower_hydrogel_actuated_3d_mea_2024](https://pubmed.ncbi.nlm.nih.gov/39413178/), [shape_conformal_organoid_framework_2026](https://www.nature.com/articles/s41551-026-01620-y), [neuronal_network_material_biocompatibility_mea_2013](https://pubmed.ncbi.nlm.nih.gov/24176966/)
- Gate failures:
  - measurement_accessibility below 3: The next claim candidate must be testable with near-term coupon, medium, or simple material measurements.

### limina_anisotropic_spedot_psbma_hydrogel_v0_1

- Name: Anisotropic S-PEDOT/PSBMA Antifouling Hydrogel Electrode
- Status: `high_novelty_antifouling_conductive_hydrogel`
- Why it matters: It targets the same core tension as the first LIMINA cell-contact route: retain a wet, low-fouling biological interface while improving electrical coupling. The latest evidence makes it a useful second-wave comparator, but not a first-claim replacement until extract and neural gates are available.
- Evidence: [anisotropic_spedot_psbma_hydrogel_2026](https://www.sciencedirect.com/science/article/pii/S1385894726032341), [zwitterionic_pedot_eeg_hydrogel_2025](https://pubmed.ncbi.nlm.nih.gov/40801064/), [topologically_entangled_psbma_hydrogel_2026](https://www.nature.com/articles/s41467-026-73355-y), [conductive_hydrogels_2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12840763/)
- Gate failures:
  - measurement_accessibility below 3: The next claim candidate must be testable with near-term coupon, medium, or simple material measurements.

### limina_cameo_cnt_organoid_frame_v0_1

- Name: CNT Organoid MEA Recording Frame
- Status: `device_side_horizon_scan`
- Why it matters: It points toward higher-surface-area, scalable electrophysiology for organoid formats, which may matter if CL1 moves from 2D cultures toward 3D aggregates.
- Evidence: [cameo_cnt_organoid_mea_2026](https://www.nature.com/articles/s44328-026-00088-9), [shape_conformal_organoid_framework_2026](https://www.nature.com/articles/s41551-026-01620-y), [neuronal_network_material_biocompatibility_mea_2013](https://pubmed.ncbi.nlm.nih.gov/24176966/), [iso_10993_5_cytotoxicity_extract_fda](https://www.fda.gov/media/85865/download)
- Gate failures:
  - measurement_accessibility below 3: The next claim candidate must be testable with near-term coupon, medium, or simple material measurements.
  - integration_risk_control below 2.5: Direct cell-contact candidates with uncontrolled leachables or fabrication risk should not be first-claim leads.

### limina_op_apa_fillerfree_hydrogel_v0_1

- Name: OP-APA Filler-Free Adaptive Bioelectronic Hydrogel
- Status: `watch_high_novelty`
- Why it matters: It points toward a material class that could be biologically gentle and mechanically adaptive, but the proof path is less immediate than the alginate-laminin PEDOT:PSS route.
- Evidence: [op_apa_self_adaptive_hydrogel_2026](https://arxiv.org/abs/2604.23945), [hydrogel_neural_tissue_2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7014813/), [conductive_hydrogels_2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12840763/)
- Gate failures:
  - measurement_accessibility below 3: The next claim candidate must be testable with near-term coupon, medium, or simple material measurements.
  - proof_gap_clarity below 3: The next experiments must have clear pass/fail criteria, not only a broad research direction.
  - integration_risk_control below 2.5: Direct cell-contact candidates with uncontrolled leachables or fabrication risk should not be first-claim leads.

### limina_entangled_zwitterionic_mechanoadaptive_matrix_v0_1

- Name: Entangled Zwitterionic Mechanoadaptive Hydrogel Matrix
- Status: `mechanics_low_fouling_horizon_scan`
- Why it matters: It expands the non-conductive matrix design space: if ALG-LAM-PEDOT fails because of swelling, fouling, or softness mismatch, a zwitterionic mechanoadaptive matrix could become a later rescue substrate.
- Evidence: [topologically_entangled_psbma_hydrogel_2026](https://www.nature.com/articles/s41467-026-73355-y), [zwitterionic_membrane_antifouling_2016](https://pubmed.ncbi.nlm.nih.gov/27025359/), [hydrogel_neural_tissue_2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7014813/), [iso_10993_5_cytotoxicity_extract_fda](https://www.fda.gov/media/85865/download)
- Gate failures:
  - measurement_accessibility below 3: The next claim candidate must be testable with near-term coupon, medium, or simple material measurements.
  - proof_gap_clarity below 3: The next experiments must have clear pass/fail criteria, not only a broad research direction.

### limina_mxene_gel_oha_sensing_hydrogel_v0_1

- Name: MXene-Gel/OHA Conductive Adhesive Hydrogel Comparator
- Status: `hold_direct_cell_contact`
- Why it matters: It can benchmark the maximum conductivity/adhesion upside, but it is unlikely to be the first safe CL1-like cell-contact material without a large toxicity and leachability proof package.
- Evidence: [mxene_adhesive_hydrogel_bmi_2025](https://www.sciencedirect.com/science/article/abs/pii/S0021979725000863), [conductive_hydrogels_2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12840763/), [iso_10993_5_cytotoxicity_extract_fda](https://www.fda.gov/media/85865/download)
- Gate failures:
  - measurement_accessibility below 3: The next claim candidate must be testable with near-term coupon, medium, or simple material measurements.
  - proof_gap_clarity below 3: The next experiments must have clear pass/fail criteria, not only a broad research direction.
  - integration_risk_control below 2.5: Direct cell-contact candidates with uncontrolled leachables or fabrication risk should not be first-claim leads.

## Interpretation

- The queue promotes `limina_alg_lam_pedot_lowdose_v0_2` because it has the clearest direct neural-culture evidence and can reuse the existing NHI-PEDOT gates.
- New 2026 electronic-ECM, anisotropic S-PEDOT/PSBMA, Alg-Gel PEDOT/PPy, MLMEA/organoid-electrode, and zwitterionic-mechanics leads expand the exploration space but remain behind the first-claim route until extractables, stability, fabrication access, and direct neuronal-network gates are measured.
- High-novelty hydrogels and 3D organoid architectures remain valuable, but they are behind the first-claim path until procurement, simplified witness coupons, extract chemistry, and neural culture compatibility are clearer.
- ZRC-ND still remains the external-material branch; the all-dry zwitterionic coating is a rescue/enhancement option if sentinel data show fouling or adsorption.
