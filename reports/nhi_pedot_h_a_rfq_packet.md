# NHI-PEDOT H-A RFQ Packet

This packet provides per-candidate RFQ text and a quote scoring rubric. It is not measured evidence.

**Status:** `ready_to_send_rfq`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Quote requests:** 4

## Attachments

- `reports/nhi_pedot_h_a_service_request.md`
- `data/nhi_pedot_h_a_raw_measurements_template.csv`
- `data/nhi_pedot_h_a_bundle_entry_sheet.csv`
- `reports/nhi_pedot_h_a_bundle_entry_sheet.md`
- `data/nhi_pedot_h_a_source_unlock_bundle_manifest.csv`
- `reports/nhi_pedot_h_a_source_unlock_pack.md`
- `reports/nhi_pedot_h_a_sentinel_packet.md`
- `data/nhi_pedot_h_a_sentinel_sample_manifest.csv`
- `data/nhi_pedot_h_a_sample_labels.csv`
- `data/nhi_pedot_h_a_chain_of_custody.csv`
- `reports/nhi_pedot_h_a_chain_of_custody.md`
- `reports/nhi_pedot_h_a_sample_submission_pack.md`
- `reports/nhi_pedot_h_a_split_scope_plan.md`
- `data/nhi_pedot_h_a_split_scope_plan.csv`
- `data/nhi_pedot_h_a_material_disclosure.csv`
- `reports/nhi_pedot_h_a_bench_sheet.md`
- `reports/nhi_pedot_h_a_minimum_measurement_checklist.md`
- `reports/nhi_pedot_alg_lam_protocol.md`
- `data/nhi_pedot_recipe_lock_v0_2.json`
- `reports/nhi_pedot_next_measurements.md`

## RFQ Score Rubric

| Criterion | Weight | Pass condition |
| --- | ---: | --- |
| `run_id_level_raw_data` | 5 | Vendor accepts one result per run_id/sample_event/target_field and does not require pooled reporting. |
| `media_physicochemical_coverage` | 4 | Vendor can report pH, osmolality, and conductivity before/after the requested timepoints, or clearly names a partner/subcontract path. |
| `coupon_physical_coverage` | 4 | Vendor can report swelling fraction, visible precipitate, shedding, delamination score, optical transparency, and supporting images. |
| `csv_schema_acceptance` | 4 | Vendor can fill or accept either the LIMINA raw-measurement CSV or the compact bundle-entry CSV without changing column names. |
| `bundle_entry_sheet_acceptance` | 2 | Vendor can use the compact one-row-per-source-file bundle sheet when one raw export/report supports multiple values. |
| `sample_handling_fit` | 3 | Vendor can handle neural medium, alginate/laminin/PEDOT:PSS coupons, 37 C timing, and chain-of-custody constraints. |
| `turnaround_and_cost` | 2 | Vendor can provide a practical R&D quote and turnaround for the 12-run/228-entry package. |
| `non_glp_scope_control` | 2 | Vendor can keep the first pass as exploratory R&D and not force a full GLP/ISO program before H-A. |

## Disqualifiers

- Only returns pooled averages or narrative pass/fail certificates.
- Will not preserve run_id, sample_event, and target_field mapping.
- Cannot return source files or raw exports for provenance.
- Requires replacing the requested material stack or timepoints without a documented deviation log.
- Treats vendor capability claims as final material suitability evidence.

## Scorecard Columns

```text
candidate_id,contact_date,reply_date,can_cover_full_h_a,needs_split_scope,run_id_level_raw_data,media_physicochemical_coverage,coupon_physical_coverage,csv_schema_acceptance,bundle_entry_sheet_acceptance,sample_handling_fit,turnaround_days,quoted_cost,decision,notes
```

## Per-Candidate RFQs

### Materials Metric

- Candidate ID: `materials_metric`
- Source: https://materialsmetric.com/
- Scope instruction: Ask whether they can execute the full H-A package or pair with a media physicochemical lab.
- Subject: RFQ: non-GLP acellular hydrogel-coupon H-A measurements (Materials Metric)

```text
Hello Materials Metric team,

I am requesting a feasibility review and non-GLP R&D quote for a small acellular biomaterials measurement package.

Study summary:
- Active material route: limina_alg_lam_pedot_lowdose_v0_2
- Runs: 12
- Raw measurement entries requested: 228
- Articles: no-coating control, alginate-laminin hydrogel control, low-loading ALG-LAM-PEDOT lead, high-loading boundary comparator
- Timepoints: 0 h, 24 h, 72 h
- Required outputs: sample-level pH, osmolality, conductivity, visible precipitate, visible shedding, swelling fraction, delamination score, optical transparency fraction, raw exports/images, and chain-of-custody by run_id

Important constraint: we need one result per provided run_id/sample_event/target_field. Pooled averages or narrative certificates alone will not satisfy the study. The compact bundle entry sheet is preferred when one raw export/report supports multiple values.

Could you please confirm:
- Can they execute the entire 12-run H-A service request as a custom R&D study?
- Can they include pH, osmolality, and conductivity, or should media tests be subcontracted?
- Can they return raw exports plus chain-of-custody by run_id?
- Whether you can fill or accept the provided raw-measurement CSV or compact bundle-entry CSV schema without changing column names
- Minimum sample volume/coupon count requirements
- Expected turnaround time, quote range, and any sample-prep constraints

Attached/package files to review:
- reports/nhi_pedot_h_a_service_request.md
- data/nhi_pedot_h_a_raw_measurements_template.csv
- data/nhi_pedot_h_a_bundle_entry_sheet.csv
- reports/nhi_pedot_h_a_bundle_entry_sheet.md
- data/nhi_pedot_h_a_source_unlock_bundle_manifest.csv
- reports/nhi_pedot_h_a_source_unlock_pack.md
- reports/nhi_pedot_h_a_sentinel_packet.md
- data/nhi_pedot_h_a_sentinel_sample_manifest.csv
- data/nhi_pedot_h_a_sample_labels.csv
- data/nhi_pedot_h_a_chain_of_custody.csv
- reports/nhi_pedot_h_a_chain_of_custody.md
- reports/nhi_pedot_h_a_sample_submission_pack.md
- reports/nhi_pedot_h_a_split_scope_plan.md
- data/nhi_pedot_h_a_split_scope_plan.csv
- data/nhi_pedot_h_a_material_disclosure.csv
- reports/nhi_pedot_h_a_bench_sheet.md
- reports/nhi_pedot_h_a_minimum_measurement_checklist.md
- reports/nhi_pedot_alg_lam_protocol.md
- data/nhi_pedot_recipe_lock_v0_2.json
- reports/nhi_pedot_next_measurements.md

This is exploratory R&D screening. We are not requesting a material suitability claim from the vendor; we only need traceable raw measurements to feed our internal QC gates.

Thank you.
```

### The Osmolality Lab

- Candidate ID: `the_osmolality_lab`
- Source: https://theosmolalitylab.com/
- Scope instruction: Ask for pH/osmolality/conductivity on all pre/post aliquots and whether they can add appearance/clarity notes.
- Subject: RFQ: non-GLP acellular hydrogel-coupon H-A measurements (The Osmolality Lab)

```text
Hello The Osmolality Lab team,

I am requesting a feasibility review and non-GLP R&D quote for a small acellular biomaterials measurement package.

Study summary:
- Active material route: limina_alg_lam_pedot_lowdose_v0_2
- Runs: 12
- Raw measurement entries requested: 228
- Articles: no-coating control, alginate-laminin hydrogel control, low-loading ALG-LAM-PEDOT lead, high-loading boundary comparator
- Timepoints: 0 h, 24 h, 72 h
- Required outputs: sample-level pH, osmolality, conductivity, visible precipitate, visible shedding, swelling fraction, delamination score, optical transparency fraction, raw exports/images, and chain-of-custody by run_id

Important constraint: we need one result per provided run_id/sample_event/target_field. Pooled averages or narrative certificates alone will not satisfy the study. The compact bundle entry sheet is preferred when one raw export/report supports multiple values.

Could you please confirm:
- Can they run matched pre/post aliquots from 37 C acellular neural-medium soaks?
- Can they preserve one result per LIMINA run_id rather than batch averages?
- Can they accept PEDOT:PSS/alginate/laminin soak media as nonclinical R&D samples?
- Whether you can fill or accept the provided raw-measurement CSV or compact bundle-entry CSV schema without changing column names
- Minimum sample volume/coupon count requirements
- Expected turnaround time, quote range, and any sample-prep constraints

Attached/package files to review:
- reports/nhi_pedot_h_a_service_request.md
- data/nhi_pedot_h_a_raw_measurements_template.csv
- data/nhi_pedot_h_a_bundle_entry_sheet.csv
- reports/nhi_pedot_h_a_bundle_entry_sheet.md
- data/nhi_pedot_h_a_source_unlock_bundle_manifest.csv
- reports/nhi_pedot_h_a_source_unlock_pack.md
- reports/nhi_pedot_h_a_sentinel_packet.md
- data/nhi_pedot_h_a_sentinel_sample_manifest.csv
- data/nhi_pedot_h_a_sample_labels.csv
- data/nhi_pedot_h_a_chain_of_custody.csv
- reports/nhi_pedot_h_a_chain_of_custody.md
- reports/nhi_pedot_h_a_sample_submission_pack.md
- reports/nhi_pedot_h_a_split_scope_plan.md
- data/nhi_pedot_h_a_split_scope_plan.csv
- data/nhi_pedot_h_a_material_disclosure.csv
- reports/nhi_pedot_h_a_bench_sheet.md
- reports/nhi_pedot_h_a_minimum_measurement_checklist.md
- reports/nhi_pedot_alg_lam_protocol.md
- data/nhi_pedot_recipe_lock_v0_2.json
- reports/nhi_pedot_next_measurements.md

This is exploratory R&D screening. We are not requesting a material suitability claim from the vendor; we only need traceable raw measurements to feed our internal QC gates.

Thank you.
```

### Cambridge Polymer Group

- Candidate ID: `cambridge_polymer_group_hydrogel`
- Source: https://www.campoly.com/services/analytical-testing/material-characterization-techniques/hydrogel-characterization/
- Scope instruction: Ask whether they can execute the full H-A package or pair with a media physicochemical lab.
- Subject: RFQ: non-GLP acellular hydrogel-coupon H-A measurements (Cambridge Polymer Group)

```text
Hello Cambridge Polymer Group team,

I am requesting a feasibility review and non-GLP R&D quote for a small acellular biomaterials measurement package.

Study summary:
- Active material route: limina_alg_lam_pedot_lowdose_v0_2
- Runs: 12
- Raw measurement entries requested: 228
- Articles: no-coating control, alginate-laminin hydrogel control, low-loading ALG-LAM-PEDOT lead, high-loading boundary comparator
- Timepoints: 0 h, 24 h, 72 h
- Required outputs: sample-level pH, osmolality, conductivity, visible precipitate, visible shedding, swelling fraction, delamination score, optical transparency fraction, raw exports/images, and chain-of-custody by run_id

Important constraint: we need one result per provided run_id/sample_event/target_field. Pooled averages or narrative certificates alone will not satisfy the study. The compact bundle entry sheet is preferred when one raw export/report supports multiple values.

Could you please confirm:
- Can they do simple optical transparency and delamination scoring on MEA witness coupons?
- Can they handle hydrated alginate-laminin-PEDOT:PSS coupons under culture-medium timing?
- Can they pair physical scoring with pH/osmolality/conductivity or only coupon characterization?
- Whether you can fill or accept the provided raw-measurement CSV or compact bundle-entry CSV schema without changing column names
- Minimum sample volume/coupon count requirements
- Expected turnaround time, quote range, and any sample-prep constraints

Attached/package files to review:
- reports/nhi_pedot_h_a_service_request.md
- data/nhi_pedot_h_a_raw_measurements_template.csv
- data/nhi_pedot_h_a_bundle_entry_sheet.csv
- reports/nhi_pedot_h_a_bundle_entry_sheet.md
- data/nhi_pedot_h_a_source_unlock_bundle_manifest.csv
- reports/nhi_pedot_h_a_source_unlock_pack.md
- reports/nhi_pedot_h_a_sentinel_packet.md
- data/nhi_pedot_h_a_sentinel_sample_manifest.csv
- data/nhi_pedot_h_a_sample_labels.csv
- data/nhi_pedot_h_a_chain_of_custody.csv
- reports/nhi_pedot_h_a_chain_of_custody.md
- reports/nhi_pedot_h_a_sample_submission_pack.md
- reports/nhi_pedot_h_a_split_scope_plan.md
- data/nhi_pedot_h_a_split_scope_plan.csv
- data/nhi_pedot_h_a_material_disclosure.csv
- reports/nhi_pedot_h_a_bench_sheet.md
- reports/nhi_pedot_h_a_minimum_measurement_checklist.md
- reports/nhi_pedot_alg_lam_protocol.md
- data/nhi_pedot_recipe_lock_v0_2.json
- reports/nhi_pedot_next_measurements.md

This is exploratory R&D screening. We are not requesting a material suitability claim from the vendor; we only need traceable raw measurements to feed our internal QC gates.

Thank you.
```

### MilliporeSigma Cell Culture Media Stability and Testing Services

- Candidate ID: `sigmaaldrich_media_testing`
- Source: https://www.sigmaaldrich.com/US/en/services/testing/cell-culture-media-stability-and-testing-services
- Scope instruction: Ask for pH/osmolality/conductivity on all pre/post aliquots and whether they can add appearance/clarity notes.
- Subject: RFQ: non-GLP acellular hydrogel-coupon H-A measurements (MilliporeSigma Cell Culture Media Stability and Testing Services)

```text
Hello MilliporeSigma Cell Culture Media Stability and Testing Services team,

I am requesting a feasibility review and non-GLP R&D quote for a small acellular biomaterials measurement package.

Study summary:
- Active material route: limina_alg_lam_pedot_lowdose_v0_2
- Runs: 12
- Raw measurement entries requested: 228
- Articles: no-coating control, alginate-laminin hydrogel control, low-loading ALG-LAM-PEDOT lead, high-loading boundary comparator
- Timepoints: 0 h, 24 h, 72 h
- Required outputs: sample-level pH, osmolality, conductivity, visible precipitate, visible shedding, swelling fraction, delamination score, optical transparency fraction, raw exports/images, and chain-of-custody by run_id

Important constraint: we need one result per provided run_id/sample_event/target_field. Pooled averages or narrative certificates alone will not satisfy the study. The compact bundle entry sheet is preferred when one raw export/report supports multiple values.

Could you please confirm:
- Can conductivity be added to the report?
- Can the service handle customer-prepared hydrogel coupon soak media rather than only standard media lots?
- Can they return raw sample-level values in the LIMINA CSV schema?
- Whether you can fill or accept the provided raw-measurement CSV or compact bundle-entry CSV schema without changing column names
- Minimum sample volume/coupon count requirements
- Expected turnaround time, quote range, and any sample-prep constraints

Attached/package files to review:
- reports/nhi_pedot_h_a_service_request.md
- data/nhi_pedot_h_a_raw_measurements_template.csv
- data/nhi_pedot_h_a_bundle_entry_sheet.csv
- reports/nhi_pedot_h_a_bundle_entry_sheet.md
- data/nhi_pedot_h_a_source_unlock_bundle_manifest.csv
- reports/nhi_pedot_h_a_source_unlock_pack.md
- reports/nhi_pedot_h_a_sentinel_packet.md
- data/nhi_pedot_h_a_sentinel_sample_manifest.csv
- data/nhi_pedot_h_a_sample_labels.csv
- data/nhi_pedot_h_a_chain_of_custody.csv
- reports/nhi_pedot_h_a_chain_of_custody.md
- reports/nhi_pedot_h_a_sample_submission_pack.md
- reports/nhi_pedot_h_a_split_scope_plan.md
- data/nhi_pedot_h_a_split_scope_plan.csv
- data/nhi_pedot_h_a_material_disclosure.csv
- reports/nhi_pedot_h_a_bench_sheet.md
- reports/nhi_pedot_h_a_minimum_measurement_checklist.md
- reports/nhi_pedot_alg_lam_protocol.md
- data/nhi_pedot_recipe_lock_v0_2.json
- reports/nhi_pedot_next_measurements.md

This is exploratory R&D screening. We are not requesting a material suitability claim from the vendor; we only need traceable raw measurements to feed our internal QC gates.

Thank you.
```

## Boundary

Vendor capability claims do not count as material evidence. Only returned real run-level measurements that pass LIMINA QC and claim audit can advance the material.
