# LIMINA Second-Wave Candidate Queue

This queue keeps material discovery moving while first-wave H-A/ZRC sourcing waits for real confirmations, replies, and measurements. It is not a suitability claim.

**Status:** `second_wave_candidate_queue_ready_while_first_wave_waits`
**Rows:** 6
**Ready for scope lock:** 2
**Watch rows:** 2
**Hold rows:** 2
**First-wave confirmations:** 0
**First-wave replies:** 0
**CSV:** `data/limina_second_wave_candidate_queue.csv`

## Queue

| Rank | Decision | Priority | Score | Candidate | Dependency | Scope action |
| ---: | --- | --- | ---: | --- | --- | --- |
| 1 | `ready_for_second_wave_scope_lock_measurement_dependency` | `parallel_screen` | 3.670 | `limina_pda_anchor_alg_lam_pedot_window_v0_1` | `requires_primary_h_a_blank_pass` | Lock the PDA/primer chemistry, electrode-window mask, extract-blank fields, and single-coupon H-A/H-B rescue trigger before any live-cell work. |
| 2 | `ready_for_second_wave_scope_lock_measurement_dependency` | `parallel_screen` | 3.500 | `limina_all_dry_zwitterionic_external_v0_1` | `requires_zrc_phase_a_failure_mode` | Lock coated-surface placement, fouling/adsorption readouts, extract-blank fields, and ZRC Phase A trigger before procurement or coating outreach. |
| 3 | `watch_after_primary_gate_data` | `watch` | 3.192 | `limina_alg_gel_pedot_ppy_lowoxidant_v0_1` | `requires_primary_h_a_blank_pass` | Lock material identity, procurement route, source-file classes, and a tiny acellular witness-coupon acceptance table. |
| 4 | `watch_after_primary_gate_data` | `watch` | 3.171 | `limina_zwitterionic_pedot_hydrogel_v0_1` | `scope_lock_can_start_now` | Lock material identity, procurement route, source-file classes, and a tiny acellular witness-coupon acceptance table. |
| 5 | `hold_until_discovery_gate_failure_resolved` | `hold` | 3.198 | `limina_pedot_sgagh_ecm_signal_hydrogel_v0_1` | `scope_lock_can_start_now` | Lock material identity, procurement route, source-file classes, and a tiny acellular witness-coupon acceptance table. |
| 6 | `hold_until_discovery_gate_failure_resolved` | `hold` | 3.170 | `limina_hydrogel_actuated_multilayer_3d_mea_v0_1` | `scope_lock_can_start_now` | Lock material identity, procurement route, source-file classes, and a tiny acellular witness-coupon acceptance table. |

## Candidate Notes

### limina_pda_anchor_alg_lam_pedot_window_v0_1

- Name: PDA-Anchored ALG-LAM-PEDOT Electrode-Window Interphase
- Measurement lane: `cell_contact_anchor_rescue_coupon`
- Near-term test: Add one anchored lead article to H-B electrochemical/physical stability only after the acellular H-A blank passes for the unanchored low-dose lead.
- Evidence refs: `pedot_neural_culture_hydrogel_2025`, `pedot_brain_monitoring_2025`, `gelma_pedot_micropatterning_2026`, `neuronal_network_material_biocompatibility_mea_2013`
- Gate failures: none
- Known risks: Primer chemistry may add its own extractables.; Localized conductive domains may be harder to fabricate reproducibly.; Anchoring can improve stability while reducing softness at the cell interface.

### limina_all_dry_zwitterionic_external_v0_1

- Name: All-Dry Zwitterionic Gradient External-Fluidic Coating
- Measurement lane: `external_material_phase_a_comparator`
- Near-term test: Run as a coating-on-housing comparator after ZRC-ND Phase A sentinel defines whether adsorption/fouling is the limiting failure mode.
- Evidence refs: `all_dry_zwitterionic_gradient_2024`, `zwitterionic_membrane_antifouling_2016`, `zwitterionic_cellulose_acetate_hfm_2026`, `organ_chip_perfusion_review_2022`
- Gate failures: none
- Known risks: Coating could change extractables or optical inspection properties.; It may not solve protein loss if the MWCO membrane itself dominates adsorption.; Not yet validated in CL1-like neuronal medium.

### limina_alg_gel_pedot_ppy_lowoxidant_v0_1

- Name: Alg-Gel PEDOT/PPy Low-Oxidant Biointerface Comparator
- Measurement lane: `cell_contact_acellular_witness_coupon`
- Near-term test: Use only after ALG-LAM-PEDOT H-A/H-B establishes a baseline; run as an acellular H-B conductivity/stability comparator with strict extract and shedding fields.
- Evidence refs: `alg_gel_pedot_ppy_biointerface_2026`, `gelma_pedot_composite_2018`, `conductive_hydrogels_2025`, `iso_10993_5_cytotoxicity_extract_fda`
- Gate failures: none
- Known risks: Fibroblast cytocompatibility is not a neuronal-network compatibility claim.; PPy oxidation chemistry can leave residues that matter in long-lived neural cultures.; High conductivity may trade off with optical transparency or softness.

### limina_zwitterionic_pedot_hydrogel_v0_1

- Name: Zwitterionic PEDOT:PSS Hydrated Electrode Hydrogel
- Measurement lane: `cell_contact_acellular_witness_coupon`
- Near-term test: Do not displace ALG-LAM-PEDOT yet; use as a later comparator if acellular extract and impedance data look better than the alginate-laminin lead.
- Evidence refs: `zwitterionic_pedot_eeg_hydrogel_2025`, `pedot_brain_monitoring_2025`, `pedot_bio_sei_2026`, `conductive_hydrogels_2025`
- Gate failures: none
- Known risks: In vivo electrode evidence does not prove in vitro neuronal network compatibility.; Zwitterionic monomers and crosslinkers can create new leachable risks.; Fabrication complexity may slow the first suitability claim.

### limina_pedot_sgagh_ecm_signal_hydrogel_v0_1

- Name: PEDOT:sGAGh Electronic ECM Signal Hydrogel
- Measurement lane: `cell_contact_acellular_witness_coupon`
- Near-term test: Keep behind ALG-LAM-PEDOT until a small H-A/H-B witness coupon can show clean extract behavior, stable pH/osmolality/conductivity, retained BDNF/laminin signal, and no delamination.
- Evidence refs: `pedot_sgagh_electronic_ecm_2026`, `pedot_bio_sei_2026`, `conductive_hydrogels_2025`, `hydrogel_neural_tissue_2020`
- Gate failures: measurement_accessibility below 3: The next claim candidate must be testable with near-term coupon, medium, or simple material measurements.
- Known risks: High novelty comes with synthesis, procurement, and reproducibility uncertainty.; Growth-factor binding is attractive but could perturb neuronal differentiation or maturation in unwanted directions.; No direct long-duration human neuronal-network compatibility evidence yet.

### limina_hydrogel_actuated_multilayer_3d_mea_v0_1

- Name: Hydrogel-Actuated Multilayer 3D Organoid MEA Interface
- Measurement lane: `cell_contact_acellular_witness_coupon`
- Near-term test: Keep as a device-architecture horizon scan; extract a simplified witness-coupon plan only after the planar ALG-LAM-PEDOT H-A/H-B route has real data.
- Evidence refs: `mlmea_organoid_depth_interface_2026`, `eflower_hydrogel_actuated_3d_mea_2024`, `shape_conformal_organoid_framework_2026`, `neuronal_network_material_biocompatibility_mea_2013`
- Gate failures: measurement_accessibility below 3: The next claim candidate must be testable with near-term coupon, medium, or simple material measurements.
- Known risks: Fabrication is much harder than a planar witness coupon.; Pt-black, PDMS, and actuator hydrogels each need extractables, adsorption, and stability checks.; Organoid electrophysiology evidence does not directly prove compatibility with the current CL1-like planar path.

## Boundary

- A second-wave row can justify scope locking, procurement scouting, or a witness-coupon plan.
- It cannot bypass H-A, ZRC Phase A, source-file provenance, or the final suitability claim audit.
- If a first-wave branch returns real measurements, rerun the full iteration before promoting any second-wave candidate.

## Next Commands

- `python3 scripts/render_limina_second_wave_candidate_queue.py`
- `python3 scripts/run_limina_iteration.py`
