# NHI-PEDOT laminin hydrogel interphase validation package

**ID:** `nhi_pedot_laminin_validation_v0_1`
**Lead variant:** `nhi_pedot_low_loading_laminin`
**Parent technology:** `limina_nhi_pedot_laminin_v0_1`

## Objective

Determine whether a laminin-anchored, low-loading PEDOT:PSS neural hydrogel interphase is suitable to enter CL1-like MEA neural culture follow-up by proving acellular material stability, electrochemical benefit, and early neural compatibility without medium drift or material shedding.

## Scope

- `stage`: cell-contact coupon and MEA validation
- `claim_after_success`: Ready for longer CL1-like neural network pilot on MEA coupons, not yet proven as a final CL1 material.
- `lead_design`: Brain-soft hydrogel matrix with laminin or laminin-like adhesive presentation and low-loading PEDOT:PSS conductive microdomains on a defined MEA coupon.
- `design_boundary`: Direct cell-contact interface; no closed CL1 deployment until extract, soak, electrochemical, and biological pilot gates pass.
- `not_in_scope`: Implantable claims, GMP manufacturing, final sterilization validation, and irreversible modification of production CL1 hardware.

## Procurement Specs

| ID | Component | Required spec | Preferred format | Reject if | Evidence |
| --- | --- | --- | --- | --- | --- |
| `neural_hydrogel_matrix` | Soft hydrogel matrix | GelMA, hyaluronic-acid, or alginate-based matrix that can be tuned near brain-like low-kPa mechanics, prepared aseptically, and measured for swelling and extractables. | Small-batch coupon casting or micropatterned format compatible with MEA witness coupons. | Unknown crosslinking chemistry, persistent photoinitiator toxicity, opacity that blocks inspection, or uncontrolled swelling over 24-72 h. | `hydrogel_neural_tissue_2020`, `stiffness_sensing_2020`, `gelma_pedot_composite_2018` |
| `pedot_pss_conductive_phase` | Conductive PEDOT:PSS phase | Low-loading PEDOT:PSS dispersion or preformed microdomain route with neutralized/rinsed formulation, recorded solids fraction, and no unqualified conductivity enhancer in the cell-contact path. | Dose ladder with hydrogel-only control, low PEDOT:PSS lead, and high PEDOT:PSS challenge article. | Acidic pH drift, visible particle shedding, uncontrolled PSS/leachable release, or impedance benefit only at cell-toxic loading. | `pedot_brain_monitoring_2025`, `pedot_bio_sei_2026`, `conductive_hydrogels_2025`, `pedot_neural_culture_hydrogel_2025` |
| `laminin_presentation` | Cell-instructive adhesive layer | Laminin, laminin-derived peptide, or ECM-mimetic adhesive motif compatible with the selected hydrogel chemistry and neural culture model. | Matched hydrogel-plus-laminin control without PEDOT:PSS to isolate electrical versus biochemical effects. | Adhesive cue rapidly desorbs, blocks electrodes, causes unstable coating thickness, or fails to support neurite outgrowth in controls. | `hydrogel_neural_tissue_2020`, `pedot_neural_culture_hydrogel_2025` |
| `mea_coupon_substrate` | MEA witness coupon | MEA-like electrode coupon or disposable MEA with known electrode geometry, insulation material, optical access, and stable baseline impedance. | Dedicated test coupon, not a production CL1 consumable, with uncoated, laminin-only, and hydrogel-only controls. | Unknown electrode material, poor baseline impedance stability, opaque layout, or bonding chemistry that cannot be replicated. | `neuronal_network_material_biocompatibility_mea_2013`, `pedot_brain_monitoring_2025` |

## Test Articles

| ID | Variant | Role | Description |
| --- | --- | --- | --- |
| `no_coating_mea_control` | `-` | baseline device control | MEA coupon with standard cell-culture coating or uncoated material-control state. |
| `laminin_only_control` | `laminin_only_mea` | biochemical adhesion control | MEA coupon with laminin or laminin-like adhesive cue but no hydrogel or PEDOT:PSS phase. |
| `hydrogel_laminin_control` | `hydrogel_laminin_no_pedot` | soft matrix control | Soft hydrogel plus laminin presentation without conductive PEDOT:PSS. |
| `lead_nhi_pedot_low_loading` | `nhi_pedot_low_loading_laminin` | lead candidate | Soft laminin-presenting hydrogel with low-loading PEDOT:PSS microdomains. |
| `challenge_nhi_pedot_high_loading` | `nhi_pedot_high_loading_laminin` | high-conductivity challenge | Same hydrogel and laminin presentation with higher PEDOT:PSS loading for conductivity-versus-toxicity boundary testing. |

## Run Matrix

### Phase H-A: Acellular material blank and extract

**Purpose:** Detect medium drift, leachables, swelling, shedding, opacity, and delamination before live-cell exposure.

**Inputs:** fresh complete neuronal medium or closest CL1-like medium proxy, MEA witness coupons, hydrogel test articles

**Articles:** `no_coating_mea_control`, `laminin_only_control`, `hydrogel_laminin_control`, `lead_nhi_pedot_low_loading`, `challenge_nhi_pedot_high_loading`

**Minimum replicates:** 3

**Timepoints:** 0 h, 4 h, 24 h, 72 h

**Must pass before:** H-B and H-C

### Phase H-B: Electrochemical and physical stability

**Purpose:** Measure whether PEDOT:PSS loading improves interface metrics without thickness, transparency, swelling, or adhesion failure.

**Inputs:** MEA witness coupons, culture-medium-soaked articles

**Articles:** `no_coating_mea_control`, `laminin_only_control`, `hydrogel_laminin_control`, `lead_nhi_pedot_low_loading`, `challenge_nhi_pedot_high_loading`

**Minimum replicates:** 3

**Timepoints:** pre-soak, 24 h soak, 72 h soak, post-cycling

**Must pass before:** H-C

### Phase H-C: Neural compatibility pilot

**Purpose:** Test whether the lead improves or preserves neural survival, neurites, morphology, and early network activity compared with laminin and hydrogel controls.

**Inputs:** primary cortical neurons or human iPSC-derived cortical neurons, matched MEA coupons, validated medium

**Articles:** `laminin_only_control`, `hydrogel_laminin_control`, `lead_nhi_pedot_low_loading`, `challenge_nhi_pedot_high_loading`

**Minimum replicates:** 3

**Timepoints:** 24 h, 7 d, 14 d, 28 d if early gates pass

**Must pass before:** long-duration CL1-like pilot

## Assay Panel

| ID | Readout | Method class | Matrix | Control requirement | Evidence |
| --- | --- | --- | --- | --- | --- |
| `medium_integrity` | pH, osmolality, conductivity, visible particulates, color/opacity, and precipitate | standard media chemistry, visual inspection, and microscopy | fresh medium soak and extract samples | same timepoints for no-coating, laminin-only, and hydrogel-only controls | `iso_10993_5_cytotoxicity_extract_fda` |
| `physical_stability` | Hydrogel thickness, swelling, delamination, cracking, electrode-window occlusion, and optical transparency | profilometry or calibrated microscopy plus image log | MEA witness coupons | pre-soak baseline and hydrogel-only comparator | `gelma_pedot_micropatterning_2026`, `gelma_pedot_composite_2018` |
| `electrochemical_interface` | Electrochemical impedance spectroscopy, charge-storage capacity, cyclic-voltammetry drift, and stimulation-safe voltage excursion where available | MEA/electrochemical workstation measurement | coated MEA coupons before and after medium soak | uncoated, laminin-only, and hydrogel-only coupon baselines | `pedot_brain_monitoring_2025`, `pedot_neural_culture_hydrogel_2025` |
| `neural_viability` | Metabolic viability, LDH release or equivalent cytotoxicity, live/dead imaging | in vitro cytotoxicity and neural culture viability assay | neural culture on coated coupons and material extracts | negative material control and positive cytotoxicity control | `iso_10993_5_cytotoxicity_extract_fda`, `dnt_nam_viability_neurite_mea_2022` |
| `neurite_and_morphology` | Neurite length/density, network coverage, cell clustering, and morphology stress flags | immunostaining or high-content imaging | neural culture on coated MEA coupons | laminin-only and hydrogel-only controls | `hydrogel_neural_tissue_2020`, `dnt_nam_viability_neurite_mea_2022` |
| `network_activity` | Spike rate, burst metrics, electrode yield, impedance drift during culture, and network synchrony where available | MEA recording and analysis | neural culture on MEA coupons | same culture batch across laminin-only, hydrogel-only, lead, and high-loading challenge articles | `neuronal_network_material_biocompatibility_mea_2013`, `pedot_neural_culture_hydrogel_2025` |

## Acceptance Gates

| Gate | Criterion | Rationale | Failure response |
| --- | --- | --- | --- |
| `blank_integrity_gate` | Acellular soak or extract shows no material-driven pH drift greater than 0.10 pH units, no osmolality or conductivity drift greater than 5 percent versus hydrogel-free controls, no visible shedding/precipitate, and no unresolved color/opacity issue. | A direct cell-contact material cannot advance if it changes base neural medium chemistry or sheds material. | Reduce PEDOT:PSS loading, change matrix/pre-rinse/crosslinking, or reject the formulation before cell exposure. |
| `physical_stability_gate` | Hydrogel thickness changes less than 20 percent, no delamination/cracking, electrode windows remain inspectable, and transparency remains sufficient for cell monitoring after 72 h soak. | MEA culture needs stable geometry and optical access; swelling or delamination can dominate biological outcomes. | Change matrix concentration, anchoring chemistry, pattern geometry, or crosslinking route. |
| `electrochemical_benefit_gate` | The low-loading lead improves impedance or charge-storage metrics by at least 25 percent versus hydrogel-laminin control after soak, without unstable cyclic-voltammetry drift. | PEDOT:PSS must add measurable electrical value beyond a soft biochemical coating. | Rerank loading, domain geometry, or drop PEDOT:PSS if the hydrogel-only control is equivalent. |
| `neural_health_gate` | Lead viability, LDH or equivalent cytotoxicity, neurite coverage, and morphology are non-inferior to laminin-only and hydrogel-laminin controls at early timepoints. | The lead is only useful if its electrical benefit does not degrade basic neural health. | Lower PEDOT:PSS loading, improve rinse/neutralization, change ECM presentation, or reject the conductive phase. |
| `network_activity_gate` | Lead MEA cultures maintain electrode yield and network activity at least non-inferior to hydrogel-laminin controls, with lower impedance drift, through the pilot window. | For CL1-like use, material suitability must be functional, not only cytocompatible. | If cells survive but network activity falls, change stiffness, ligand density, thickness, or conductive-domain geometry before longer tests. |

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
- `mea_coupon_id`
- `electrode_material`
- `hydrogel_matrix`
- `hydrogel_modulus_kpa`
- `hydrogel_thickness_um`
- `pedot_pss_loading_fraction`
- `pedot_pss_pre_rinse_protocol`
- `laminin_or_peptide_density`
- `crosslinking_protocol`
- `sterilization_or_aseptic_protocol`
- `medium_name`
- `medium_lot`
- `temperature_c`
- `pH_initial`
- `pH_final`
- `osmolality_initial_mOsm_kg`
- `osmolality_final_mOsm_kg`
- `conductivity_initial_mS_cm`
- `conductivity_final_mS_cm`
- `visible_precipitate`
- `visible_shedding`
- `swelling_fraction`
- `delamination_score`
- `optical_transparency_fraction`
- `eis_1khz_initial_ohm`
- `eis_1khz_final_ohm`
- `charge_storage_capacity_initial`
- `charge_storage_capacity_final`
- `cell_model`
- `seeding_density`
- `viability_fraction`
- `ldh_fold_control`
- `neurite_coverage_fraction`
- `mean_neurite_length_um`
- `electrode_yield_fraction`
- `spike_rate_hz`
- `burst_rate_hz`
- `gate_results`
- `notes`

## Decision Rules

| Condition | Action |
| --- | --- |
| All H-A/H-B/H-C gates pass for low-loading NHI-PEDOT | Promote to cell-contact biological pilot candidate and design a longer MEA network stability study. |
| Blank and neural health pass but electrochemical benefit fails | Demote PEDOT:PSS to optional and compare hydrogel-laminin-only coating against simpler PDA-laminin controls. |
| Electrochemical benefit passes but neural health fails | Reduce PEDOT:PSS loading, strengthen rinse/neutralization, or reject the conductive phase before live-cell continuation. |
| High-loading challenge outperforms lead electrically but harms cells | Use the high-loading result only as an upper toxicity/electrical boundary; do not promote it. |
| Hydrogel swells, delaminates, or blocks optical/MEA access | Change matrix, anchoring chemistry, or geometry before any biological interpretation. |

## Source Refs

- `pedot_brain_monitoring_2025`
- `pedot_bio_sei_2026`
- `conductive_hydrogels_2025`
- `hydrogel_neural_tissue_2020`
- `stiffness_sensing_2020`
- `gelma_pedot_composite_2018`
- `pedot_neural_culture_hydrogel_2025`
- `gelma_pedot_micropatterning_2026`
- `iso_10993_5_cytotoxicity_extract_fda`
- `dnt_nam_viability_neurite_mea_2022`
- `neuronal_network_material_biocompatibility_mea_2013`
