# LIMINA Second-Wave Scope-Lock Pack

This pack turns ready second-wave candidates into concrete scope-lock tasks. It does not create material suitability evidence.

**Status:** `second_wave_scope_lock_pack_ready`
**Ready candidates:** 2
**Tasks:** 8
**Source-file classes:** 5
**Claim evidence created:** `false`
**CSV:** `data/limina_second_wave_scope_lock_tasks.csv`

## Candidates

| Candidate | Lane | Dependency | Tasks |
| --- | --- | --- | ---: |
| `limina_pda_anchor_alg_lam_pedot_window_v0_1` | `cell_contact_anchor_rescue_coupon` | `requires_primary_h_a_blank_pass` | 4 |
| `limina_all_dry_zwitterionic_external_v0_1` | `external_material_phase_a_comparator` | `requires_zrc_phase_a_failure_mode` | 4 |

## Tasks

| Order | Candidate | Type | Route | Source class | Acceptance criterion |
| ---: | --- | --- | --- | --- | --- |
| 1 | `limina_pda_anchor_alg_lam_pedot_window_v0_1` | `scope_lock` | `desk_review` | `supplier_or_build_record` | Primer chemistry, MEA substrate, mask/window geometry, and hydrogel article identity are fixed before any measurement package is released. |
| 2 | `limina_pda_anchor_alg_lam_pedot_window_v0_1` | `measurement_plan` | `h_a_rescue_prereq` | `bench_or_chain_of_custody_record` | Blank article has pH, osmolality, conductivity, visible shedding, swelling, delamination, and transparency fields mapped to source files. |
| 3 | `limina_pda_anchor_alg_lam_pedot_window_v0_1` | `measurement_plan` | `h_b_conditional` | `electrochemical_or_mea_export` | 1 kHz impedance, charge-storage proxy, impedance drift, and window-occlusion notes are listed as conditional H-B fields. |
| 4 | `limina_pda_anchor_alg_lam_pedot_window_v0_1` | `decision_gate` | `portfolio` | `bench_or_chain_of_custody_record` | Candidate can only advance if primary H-A is clean enough and measured failure mode points to delamination, adhesion, or window instability. |
| 1 | `limina_all_dry_zwitterionic_external_v0_1` | `scope_lock` | `desk_review` | `supplier_or_build_record` | Substrate, coating location, uncoated comparator, and membrane/housing exposure boundary are fixed before outreach or purchase. |
| 2 | `limina_all_dry_zwitterionic_external_v0_1` | `measurement_plan` | `zrc_phase_a_comparator` | `pH_meter_export_or_photo` | pH, osmolality, conductivity, turbidity/visible residue, and extractable-risk notes are mapped to source-backed fields. |
| 3 | `limina_all_dry_zwitterionic_external_v0_1` | `measurement_plan` | `zrc_phase_a_comparator` | `biochemical_or_plate_reader_export` | BSA or albumin adsorption, BDNF/proxy recovery, flow resistance drift, and post-soak inspection are listed as required comparator fields. |
| 4 | `limina_all_dry_zwitterionic_external_v0_1` | `decision_gate` | `portfolio` | `bench_or_chain_of_custody_record` | Candidate can only advance if ZRC Phase A real data show adsorption, fouling, or housing-surface loss as a limiting failure mode. |

## Boundary

- Scope lock means material identity, trigger rules, and future source classes are defined.
- No task in this pack changes H-A, ZRC, H-B/H-C, long-duration, or claim-audit evidence.
- The first suitable material still requires real measured rows and a final claim audit with `claim_ready=true`.

## Next Commands

- `python3 scripts/render_limina_second_wave_scope_lock_pack.py`
- `python3 scripts/run_limina_iteration.py`
