# NHI-PEDOT long-duration MEA network follow-up package

**ID:** `nhi_pedot_long_followup_v0_1`
**Parent validation package:** `nhi_pedot_laminin_validation_v0_1`
**Lead variant:** `nhi_pedot_low_loading_laminin`

## Objective

Determine whether the low-loading NHI-PEDOT laminin hydrogel interphase preserves material integrity, electrode performance, neural health, and MEA network activity over a longer CL1-like culture window after H-A/H-B/H-C coupon gates pass.

## Scope

- `stage`: long-duration cell-contact MEA/network validation after coupon gates
- `entry_condition`: Run only after NHI-PEDOT H-A/H-B/H-C gates pass for the low-loading lead.
- `sample_type`: MEA coupons or disposable MEA cultures coated with laminin-only, hydrogel-laminin control, low-loading NHI-PEDOT lead, and high-loading challenge articles.
- `claim_after_success`: Supports first suitability claim for a CL1-like cell-contact MEA interphase, pending actual CL1 hardware integration constraints.
- `not_in_scope`: Regulatory approval, production CL1 modification, chronic implantable safety, and irreversible deployment into unavailable CL1 hardware.

## Test Articles

| ID | Variant | Role |
| --- | --- | --- |
| `long_laminin_only_control` | `laminin_only_mea` | standard biochemical adhesion control |
| `long_hydrogel_laminin_control` | `hydrogel_laminin_no_pedot` | soft matrix comparator |
| `long_lead_nhi_pedot_low_loading` | `nhi_pedot_low_loading_laminin` | lead long-duration candidate |
| `long_challenge_nhi_pedot_high_loading` | `nhi_pedot_high_loading_laminin` | conductivity-versus-toxicity boundary comparator |
| `long_positive_toxicity_control` | `-` | assay sensitivity control |

## Run Matrix

### L1: Long material and electrochemical stability

**Purpose:** Track hydrogel integrity, shedding, optical access, impedance drift, and charge-storage retention before claiming long-culture suitability.

**Articles:** `long_laminin_only_control`, `long_hydrogel_laminin_control`, `long_lead_nhi_pedot_low_loading`, `long_challenge_nhi_pedot_high_loading`

**Minimum replicates:** 3

**Timepoints:** 0 d, 7 d, 14 d, 28 d, 42 d

**Must pass before:** L2/L3 interpretation

### L2: Long neural health and spontaneous network stability

**Purpose:** Measure whether the lead preserves viability, morphology, electrode yield, spontaneous spiking, burst structure, and synchrony over a CL1-like culture window.

**Articles:** `long_laminin_only_control`, `long_hydrogel_laminin_control`, `long_lead_nhi_pedot_low_loading`, `long_challenge_nhi_pedot_high_loading`, `long_positive_toxicity_control`

**Minimum replicates:** 3

**Timepoints:** 7 d, 14 d, 28 d, 42 d

**Must pass before:** first suitability claim

### L3: Stimulus-recording resilience and recovery

**Purpose:** Check whether the interphase maintains usable MEA signal and network recovery after controlled stimulation/recording stress.

**Articles:** `long_laminin_only_control`, `long_hydrogel_laminin_control`, `long_lead_nhi_pedot_low_loading`, `long_challenge_nhi_pedot_high_loading`

**Minimum replicates:** 3

**Timepoints:** pre-stim, post-stim, 24 h recovery

**Must pass before:** first suitability claim

## Assay Panel

| ID | Readout | Method | Evidence |
| --- | --- | --- | --- |
| `long_material_integrity` | Visible shedding, delamination, swelling, optical transparency, electrode-window access, and imaging compatibility | longitudinal microscopy, image log, and physical inspection | `hydrogel_neural_tissue_2020`, `gelma_pedot_micropatterning_2026` |
| `long_electrochemical_stability` | 1 kHz impedance drift, charge-storage retention, baseline noise, and electrode yield | MEA or electrochemical workstation longitudinal measurement | `pedot_brain_monitoring_2025`, `pedot_neural_culture_hydrogel_2025` |
| `long_neural_health` | Viability, LDH or equivalent cytotoxicity, neurite/network coverage, and morphology stress flags | viability assay and high-content neural imaging | `iso_10993_5_cytotoxicity_extract_fda`, `dnt_nam_viability_neurite_mea_2022` |
| `long_network_function` | Spontaneous spike rate, burst rate, synchrony, electrode yield, and activity drift relative to hydrogel-laminin control | MEA network recording and analysis | `neuronal_network_material_biocompatibility_mea_2013`, `dnt_nam_viability_neurite_mea_2022` |
| `stimulus_recovery` | Post-stimulation signal recovery, spike/burst recovery, and irreversible impedance degradation | controlled MEA stimulation/recording stress test | `pedot_brain_monitoring_2025`, `neuronal_network_material_biocompatibility_mea_2013` |

## Acceptance Gates

| Gate | Criterion | Failure response |
| --- | --- | --- |
| `long_material_integrity_gate` | Lead shows no visible shedding, delamination score <= 0.5, swelling <= 20 percent, optical transparency >= 0.75, and electrode-window access preserved through the long window. | Do not claim suitability; change matrix, anchoring chemistry, thickness, or PEDOT:PSS loading. |
| `long_electrochemical_stability_gate` | Lead 1 kHz impedance drift remains within 25 percent of its initial value or stays at least 20 percent better than hydrogel-laminin control, with charge-storage retention >= 80 percent. | Do not claim MEA suitability; change conductive-domain geometry, stabilization, or rinse protocol. |
| `long_neural_health_gate` | Lead keeps viability >= 90 percent of hydrogel-laminin control, LDH/cytotoxicity <= 120 percent of control, neurite/network coverage >= 85 percent of control, and morphology stress score <= 1. | Treat the formulation as biologically unsafe or under-optimized; lower loading or change presentation chemistry. |
| `long_network_stability_gate` | Lead keeps electrode yield >= 90 percent of hydrogel-laminin control, spike rate and burst rate within 70-130 percent of control, synchrony within 70-130 percent, and no monotonic collapse across timepoints. | Do not claim CL1-like functional suitability; tune stiffness, ligand density, thickness, or conductive-domain layout. |
| `long_stimulus_recovery_gate` | After controlled stimulation/recording stress, lead recovers >= 85 percent of pre-stim spike/burst activity within 24 h and shows irreversible impedance degradation <= 20 percent. | Preserve as passive interface only; do not advance as robust recording/stimulation interphase. |
| `long_superiority_gate` | Lead is non-inferior to hydrogel-laminin control on neural health and network stability while improving or stabilizing electrochemical readouts; high-loading challenge must not be safer than the lead. | If hydrogel-laminin control is equivalent, demote PEDOT:PSS; if high-loading is safer and stronger, rerank loading. |

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
- `cell_model`
- `culture_day`
- `mea_coupon_id`
- `hydrogel_matrix`
- `pedot_pss_loading_fraction`
- `laminin_or_peptide_density`
- `visible_shedding`
- `swelling_fraction`
- `delamination_score`
- `optical_transparency_fraction`
- `electrode_window_access`
- `eis_1khz_initial_ohm`
- `eis_1khz_current_ohm`
- `eis_1khz_pct_hydrogel_control`
- `charge_storage_capacity_initial`
- `charge_storage_capacity_current`
- `charge_storage_capacity_retention_fraction`
- `baseline_noise_uv`
- `viability_pct_hydrogel_control`
- `ldh_pct_hydrogel_control`
- `neurite_coverage_pct_hydrogel_control`
- `morphology_stress_score`
- `electrode_yield_pct_hydrogel_control`
- `spike_rate_pct_hydrogel_control`
- `burst_rate_pct_hydrogel_control`
- `synchrony_pct_hydrogel_control`
- `post_stim_spike_recovery_pct_pre`
- `post_stim_burst_recovery_pct_pre`
- `post_stim_impedance_degradation_pct`
- `gate_results`
- `notes`

## Source Refs

- `pedot_brain_monitoring_2025`
- `pedot_neural_culture_hydrogel_2025`
- `hydrogel_neural_tissue_2020`
- `gelma_pedot_micropatterning_2026`
- `iso_10993_5_cytotoxicity_extract_fda`
- `dnt_nam_viability_neurite_mea_2022`
- `neuronal_network_material_biocompatibility_mea_2013`
