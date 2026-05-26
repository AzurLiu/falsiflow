# NHI-PEDOT H-A Split-Scope Execution Plan

This plan is a fallback if one vendor cannot cover all H-A readouts. It is not measured evidence.

**Status:** `split_scope_plan_ready`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Runs:** 12
**Raw entries:** 228
**Pairs:** 7
**Preferred pairs:** 5

## Field Split

- Media fields: `date`, `medium_name`, `medium_lot`, `temperature_c`, `pH_initial`, `pH_final`, `osmolality_initial_mOsm_kg`, `osmolality_final_mOsm_kg`, `conductivity_initial_mS_cm`, `conductivity_final_mS_cm`, `visible_precipitate`
- Coupon fields: `mea_coupon_id`, `electrode_material`, `visible_shedding`, `swelling_fraction`, `delamination_score`, `optical_transparency_fraction`, `image_source_file`

## Preferred Pairings

| Pair | Media vendor | Coupon vendor | Role | Score | Decision |
| --- | --- | --- | --- | ---: | --- |
| `the_osmolality_lab__cambridge_polymer_group_hydrogel` | The Osmolality Lab | Cambridge Polymer Group | `split_scope` | 36 | `preferred_split_scope` |
| `the_osmolality_lab__materials_metric` | The Osmolality Lab | Materials Metric | `split_scope` | 33 | `preferred_split_scope` |
| `sigmaaldrich_media_testing__cambridge_polymer_group_hydrogel` | MilliporeSigma Cell Culture Media Stability and Testing Services | Cambridge Polymer Group | `split_scope` | 30 | `preferred_split_scope` |
| `sigmaaldrich_media_testing__materials_metric` | MilliporeSigma Cell Culture Media Stability and Testing Services | Materials Metric | `split_scope` | 27 | `preferred_split_scope` |
| `the_osmolality_lab__nikon_bioimaging_lab` | The Osmolality Lab | Nikon BioImaging Lab USA | `split_scope` | 25 | `secondary_needs_contact_plan` |
| `materials_metric__materials_metric` | Materials Metric | Materials Metric | `integrated_or_prime_with_subcontract` | 23 | `preferred_split_scope` |
| `sigmaaldrich_media_testing__nikon_bioimaging_lab` | MilliporeSigma Cell Culture Media Stability and Testing Services | Nikon BioImaging Lab USA | `split_scope` | 19 | `secondary_needs_contact_plan` |

## Shared Requirements

- Both vendors must preserve LIMINA run_id and sample_event labels.
- Both vendors must return source_file names that resolve to instrument exports or image files.
- One operator must reconcile completed_raw_measurements.csv before merge.
- Chain-of-custody must identify which vendor handled each sample_event.
- Split scope cannot change timepoints, articles, or replicates without a deviation log.

## Operating Rules

- Prefer one integrated provider only if it preserves run_id-level raw rows and source files.
- Use split scope when media chemistry and coupon imaging/physical scoring are stronger at different vendors.
- Assign media fields and coupon fields explicitly before shipment; do not let either vendor pool across run_id.
- Merge both vendors into one completed_raw_measurements.csv before LIMINA QC.
- A split-scope plan authorizes execution logistics only; it is not material evidence.

## Boundary

Vendor capability claims do not count as material evidence. Only returned real run-level measurements that pass LIMINA QC and claim audit can advance the material.
