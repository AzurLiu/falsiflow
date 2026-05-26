# ZRC-ND Phase D biological follow-up package

**ID:** `zrc_nd_bio_followup_v0_1`
**Parent validation package:** `zrc_nd_3p5k_guard_validation_v0_1`
**Lead variant:** `zrc_nd_3p5k_mpc_guard`

## Objective

Determine whether ZRC-ND-conditioned medium that has passed non-cell chemistry gates preserves neural culture health, morphology, and functional activity well enough to support a first suitability claim.

## Scope

- `stage`: biological follow-up after non-cell validation
- `entry_condition`: Run only after Phase A/B/C non-cell gates pass for the lead article.
- `sample_type`: media or conditioned-media proxy exposed to the ZRC-ND lead, unmodified 3.5 kDa baseline, 10 kDa challenge, and no-module controls
- `claim_after_success`: Supports suitability for biological conditioned-medium pilot use, not final long-duration CL1 deployment.
- `not_in_scope`: Regulatory approval, chronic manufacturing validation, direct cell-contact material certification, and organismal safety.

## Test Articles

| ID | Variant | Role |
| --- | --- | --- |
| `bio_no_module_control` | `-` | negative/control medium |
| `bio_lead_zrc_nd_3p5m_guard` | `zrc_nd_3p5k_mpc_guard` | lead biological challenge |
| `bio_baseline_rc_3p5m_guard` | `zrc_nd_3p5k_unmodified_guard` | unmodified baseline biological comparator |
| `bio_challenge_zrc_nd_10m_guard` | `zrc_nd_10k_mpc_guard` | high-clearance retention-risk biological comparator |
| `bio_positive_toxicity_control` | `-` | assay sensitivity control |

## Run Matrix

### D1: Extract or conditioned-medium viability screen

**Purpose:** Detect acute material-conditioned medium toxicity before morphology or network claims.

**Articles:** `bio_no_module_control`, `bio_lead_zrc_nd_3p5m_guard`, `bio_baseline_rc_3p5m_guard`, `bio_challenge_zrc_nd_10m_guard`, `bio_positive_toxicity_control`

**Minimum replicates:** 3

**Timepoints:** 24 h, 72 h

**Must pass before:** D2

### D2: Neurite and morphology screen

**Purpose:** Check whether ZRC-ND-conditioned medium preserves neural morphology and outgrowth relative to no-module control.

**Articles:** `bio_no_module_control`, `bio_lead_zrc_nd_3p5m_guard`, `bio_baseline_rc_3p5m_guard`, `bio_challenge_zrc_nd_10m_guard`

**Minimum replicates:** 3

**Timepoints:** 72 h

**Must pass before:** D3

### D3: Network activity stability screen

**Purpose:** Check whether ZRC-ND-conditioned medium preserves MEA or equivalent functional network activity relative to no-module control.

**Articles:** `bio_no_module_control`, `bio_lead_zrc_nd_3p5m_guard`, `bio_baseline_rc_3p5m_guard`, `bio_challenge_zrc_nd_10m_guard`

**Minimum replicates:** 3

**Timepoints:** 72 h

**Must pass before:** suitability claim

## Assay Panel

| ID | Readout | Method | Evidence |
| --- | --- | --- | --- |
| `viability_toxicity` | Metabolic viability and LDH/cell lysis relative to no-module control | metabolic viability assay plus LDH or equivalent cytotoxicity assay | `iso_10993_5_cytotoxicity_extract_fda`, `dnt_nam_viability_neurite_mea_2022` |
| `neurite_morphology` | Neurite length/branching and cell-body count relative to no-module control | high-content imaging or equivalent neural morphology assay | `dnt_nam_viability_neurite_mea_2022` |
| `network_activity` | MEA spike rate, burst rate, and synchrony relative to no-module control | MEA or equivalent functional network activity assay | `neuronal_network_material_biocompatibility_mea_2013`, `dnt_nam_viability_neurite_mea_2022` |

## Acceptance Gates

| Gate | Criterion | Failure response |
| --- | --- | --- |
| `bio_viability_gate` | Lead-conditioned medium keeps metabolic viability >= 90 percent of no-module control and LDH/cell lysis <= 120 percent of no-module control. | Do not claim suitability; investigate extractables, coating residues, medium drift, or cartridge preconditioning. |
| `bio_morphology_gate` | Lead-conditioned medium keeps neurite length and branching >= 85 percent of no-module control and cell-body count >= 90 percent. | Do not claim neural suitability; repeat with lower exposure, extra rinsing, or simplified unmodified RC baseline. |
| `bio_function_gate` | Lead-conditioned medium keeps spike rate, burst rate, and synchrony within 70 to 130 percent of no-module control, unless a domain-specific assay defines a tighter gate. | Do not claim CL1-like functional suitability; preserve the candidate as chemistry-compatible only. |
| `bio_superiority_gate` | Lead is not worse than unmodified 3.5 kDa baseline on viability/morphology and is safer than the 10 kDa challenge on functional or morphology retention. | Reconsider whether the coating route adds value or whether the MWCO challenge is too disruptive. |

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
- `medium_condition`
- `exposure_time_h`
- `viability_metabolic_pct_control`
- `ldh_release_pct_control`
- `neurite_length_pct_control`
- `neurite_branching_pct_control`
- `cell_body_count_pct_control`
- `network_spike_rate_pct_control`
- `burst_rate_pct_control`
- `synchrony_pct_control`
- `morphology_notes`
- `gate_results`
- `notes`

## Source Refs

- `iso_10993_5_cytotoxicity_extract_fda`
- `neuronal_network_material_biocompatibility_mea_2013`
- `dnt_nam_viability_neurite_mea_2022`
- `neural_microfluidic_systems_2023`
- `organ_chip_perfusion_review_2022`
