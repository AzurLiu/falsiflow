# ZRC-ND Phase A RFQ Packet

This packet provides per-candidate RFQ text and a quote scoring rubric. It is not measured evidence.

**Status:** `ready_to_send_rfq`
**Active candidate:** `limina_zrc_nd_v0_1`
**Quote requests:** 4

## Attachments

- `reports/zrc_nd_phase_a_service_request.md`
- `data/zrc_nd_phase_a_sentinel_template.csv`
- `reports/zrc_nd_phase_a_sentinel_packet.md`
- `data/zrc_nd_phase_a_sentinel_sample_manifest.csv`
- `data/zrc_nd_phase_a_sample_labels.csv`
- `data/zrc_nd_phase_a_chain_of_custody.csv`
- `reports/zrc_nd_phase_a_chain_of_custody.md`
- `reports/zrc_nd_next_measurements.md`
- `data/zrc_nd_3p5k_guard_validation_package.json`
- `reports/zrc_nd_run_plan.md`

## RFQ Score Rubric

| Criterion | Weight | Pass condition |
| --- | ---: | --- |
| `run_id_level_raw_data` | 5 | Vendor accepts one result per run_id/sample_event/test field and does not require pooled reporting. |
| `phase_a_media_panel_coverage` | 5 | Vendor can report pH, osmolality, conductivity, and appearance/turbidity/visible precipitate, or clearly defines a split path for the missing field. |
| `csv_schema_acceptance` | 4 | Vendor can fill or accept the ZRC-ND Phase A CSV without changing column names. |
| `sample_handling_fit` | 3 | Vendor can handle nonclinical neural-medium aliquots exposed to regenerated-cellulose/module witness articles. |
| `source_file_provenance` | 3 | Vendor can return raw exports, instrument reports, or stable filenames that reconcile to run_id/sample_id. |
| `turnaround_and_cost` | 2 | Vendor can provide practical R&D quote, sample requirements, and turnaround for the 8-run Phase A package. |
| `non_glp_scope_control` | 2 | Vendor can keep the first pass exploratory and avoid forcing a full GLP/E&L program before Phase A. |

## Disqualifiers

- Only returns pooled averages, certificates, or narrative feasibility opinions.
- Will not preserve run_id, sample_event, and target-field mapping.
- Cannot return raw exports, instrument reports, or traceable source files.
- Requires changing article identity, timepoints, membrane material, or control rows without a deviation log.
- Treats quote, supplier support, or vendor capability claims as final material suitability evidence.

## Scorecard Columns

```text
candidate_id,contact_date,reply_date,can_cover_full_phase_a,needs_split_scope,run_id_level_raw_data,phase_a_media_panel_coverage,csv_schema_acceptance,sample_handling_fit,source_file_provenance,non_glp_scope_control,turnaround_days,quoted_cost,decision,notes
```

## Per-Candidate RFQs

### Pacific BioLabs Physicochemical Properties Testing

- Candidate ID: `pacific_biolabs_physicochemical`
- Source: https://pacificbiolabs.com/physicochemical-properties
- Contact: https://pacificbiolabs.com/contact/
- Scope instruction: Ask whether they can execute the full Phase A pH/osmolality/conductivity/appearance package or identify a split path for missing fields.
- Subject: RFQ: non-GLP acellular ZRC-ND Phase A medium-integrity measurements (Pacific BioLabs Physicochemical Properties Testing)

```text
Hello Pacific BioLabs Physicochemical Properties Testing team,

I am requesting a feasibility review and non-GLP R&D quote for a small acellular medium-integrity measurement package.

Study summary:
- Active material route: limina_zrc_nd_v0_1
- Lead variant: zrc_nd_3p5k_mpc_guard
- Runs: 8
- Sample events: 16
- Articles: unmodified 3.5 kDa RC baseline, MPC-like 3.5 kDa lead, 10 kDa challenge, and no-module static control
- Timepoints: 0 h and 24 h
- Required outputs: pH, osmolality, conductivity, appearance/turbidity/visible precipitate, raw exports or instrument reports, and chain-of-custody by run_id

Important constraint: we need one result per provided run_id/sample_event/test field. Pooled averages or narrative certificates alone will not satisfy the study.

Could you please confirm:
- Can conductivity be added to the pH/osmolality/appearance panel or routed to another internal analytical service?
- Can they accept nonclinical neural-medium aliquots exposed to regenerated-cellulose membrane/module articles?
- Can they preserve one report row per LIMINA run_id and return raw values in the provided CSV schema?
- Whether you can fill or accept the provided Phase A CSV schema without changing column names
- Minimum aliquot volume, sample container, and sample count requirements
- Expected turnaround time, quote range, sample acceptance constraints, and whether SDS/lot documentation is required before shipping

Attached/package files to review:
- reports/zrc_nd_phase_a_service_request.md
- data/zrc_nd_phase_a_sentinel_template.csv
- reports/zrc_nd_phase_a_sentinel_packet.md
- data/zrc_nd_phase_a_sentinel_sample_manifest.csv
- data/zrc_nd_phase_a_sample_labels.csv
- data/zrc_nd_phase_a_chain_of_custody.csv
- reports/zrc_nd_phase_a_chain_of_custody.md
- reports/zrc_nd_next_measurements.md
- data/zrc_nd_3p5k_guard_validation_package.json
- reports/zrc_nd_run_plan.md

This is exploratory R&D screening. We are not requesting a material suitability claim from the vendor; we only need traceable raw measurements to feed our internal Phase A gate.

Thank you.
```

### MilliporeSigma Cell Culture Media Stability and Testing Services

- Candidate ID: `sigmaaldrich_media_testing`
- Source: https://www.sigmaaldrich.com/US/en/services/testing/cell-culture-media-stability-and-testing-services
- Contact: https://www.sigmaaldrich.com/US/en/collections/offices
- Scope instruction: Ask whether they can execute the full Phase A pH/osmolality/conductivity/appearance package or identify a split path for missing fields.
- Subject: RFQ: non-GLP acellular ZRC-ND Phase A medium-integrity measurements (MilliporeSigma Cell Culture Media Stability and Testing Services)

```text
Hello MilliporeSigma Cell Culture Media Stability and Testing Services team,

I am requesting a feasibility review and non-GLP R&D quote for a small acellular medium-integrity measurement package.

Study summary:
- Active material route: limina_zrc_nd_v0_1
- Lead variant: zrc_nd_3p5k_mpc_guard
- Runs: 8
- Sample events: 16
- Articles: unmodified 3.5 kDa RC baseline, MPC-like 3.5 kDa lead, 10 kDa challenge, and no-module static control
- Timepoints: 0 h and 24 h
- Required outputs: pH, osmolality, conductivity, appearance/turbidity/visible precipitate, raw exports or instrument reports, and chain-of-custody by run_id

Important constraint: we need one result per provided run_id/sample_event/test field. Pooled averages or narrative certificates alone will not satisfy the study.

Could you please confirm:
- Can conductivity be added for the Phase A material-blank gate?
- Can they test customer-prepared medium aliquots exposed to dialysis membrane/module witness articles?
- Can they return one row per run_id instead of product-lot summaries?
- Whether you can fill or accept the provided Phase A CSV schema without changing column names
- Minimum aliquot volume, sample container, and sample count requirements
- Expected turnaround time, quote range, sample acceptance constraints, and whether SDS/lot documentation is required before shipping

Attached/package files to review:
- reports/zrc_nd_phase_a_service_request.md
- data/zrc_nd_phase_a_sentinel_template.csv
- reports/zrc_nd_phase_a_sentinel_packet.md
- data/zrc_nd_phase_a_sentinel_sample_manifest.csv
- data/zrc_nd_phase_a_sample_labels.csv
- data/zrc_nd_phase_a_chain_of_custody.csv
- reports/zrc_nd_phase_a_chain_of_custody.md
- reports/zrc_nd_next_measurements.md
- data/zrc_nd_3p5k_guard_validation_package.json
- reports/zrc_nd_run_plan.md

This is exploratory R&D screening. We are not requesting a material suitability claim from the vendor; we only need traceable raw measurements to feed our internal Phase A gate.

Thank you.
```

### The Osmolality Lab

- Candidate ID: `the_osmolality_lab`
- Source: https://theosmolalitylab.com/services/
- Contact: https://theosmolalitylab.com/contact-us/
- Scope instruction: Use as focused pH/osmolality provider and ask whether conductivity is supported or must be split.
- Subject: RFQ: non-GLP acellular ZRC-ND Phase A medium-integrity measurements (The Osmolality Lab)

```text
Hello The Osmolality Lab team,

I am requesting a feasibility review and non-GLP R&D quote for a small acellular medium-integrity measurement package.

Study summary:
- Active material route: limina_zrc_nd_v0_1
- Lead variant: zrc_nd_3p5k_mpc_guard
- Runs: 8
- Sample events: 16
- Articles: unmodified 3.5 kDa RC baseline, MPC-like 3.5 kDa lead, 10 kDa challenge, and no-module static control
- Timepoints: 0 h and 24 h
- Required outputs: pH, osmolality, conductivity, appearance/turbidity/visible precipitate, raw exports or instrument reports, and chain-of-custody by run_id

Important constraint: we need one result per provided run_id/sample_event/test field. Pooled averages or narrative certificates alone will not satisfy the study.

Could you please confirm:
- Can they accept acellular neural-medium aliquots that are non-biohazard and non-radioactive?
- Can they run all 8 Phase A rows as individual run_id samples with pre/post mapping?
- Can they support conductivity directly, or should conductivity be measured by another lab or internally?
- Whether you can fill or accept the provided Phase A CSV schema without changing column names
- Minimum aliquot volume, sample container, and sample count requirements
- Expected turnaround time, quote range, sample acceptance constraints, and whether SDS/lot documentation is required before shipping

Attached/package files to review:
- reports/zrc_nd_phase_a_service_request.md
- data/zrc_nd_phase_a_sentinel_template.csv
- reports/zrc_nd_phase_a_sentinel_packet.md
- data/zrc_nd_phase_a_sentinel_sample_manifest.csv
- data/zrc_nd_phase_a_sample_labels.csv
- data/zrc_nd_phase_a_chain_of_custody.csv
- reports/zrc_nd_phase_a_chain_of_custody.md
- reports/zrc_nd_next_measurements.md
- data/zrc_nd_3p5k_guard_validation_package.json
- reports/zrc_nd_run_plan.md

This is exploratory R&D screening. We are not requesting a material suitability claim from the vendor; we only need traceable raw measurements to feed our internal Phase A gate.

Thank you.
```

### Jordi Labs Analytical Testing

- Candidate ID: `jordi_labs_el_polymer`
- Source: https://jordilabs.com/lab-testing/
- Contact: https://jordilabs.com/contact/
- Scope instruction: Use for custom chemistry or E&L escalation if Phase A shows drift, particulates, or extractables concern.
- Subject: RFQ: non-GLP acellular ZRC-ND Phase A medium-integrity measurements (Jordi Labs Analytical Testing)

```text
Hello Jordi Labs Analytical Testing team,

I am requesting a feasibility review and non-GLP R&D quote for a small acellular medium-integrity measurement package.

Study summary:
- Active material route: limina_zrc_nd_v0_1
- Lead variant: zrc_nd_3p5k_mpc_guard
- Runs: 8
- Sample events: 16
- Articles: unmodified 3.5 kDa RC baseline, MPC-like 3.5 kDa lead, 10 kDa challenge, and no-module static control
- Timepoints: 0 h and 24 h
- Required outputs: pH, osmolality, conductivity, appearance/turbidity/visible precipitate, raw exports or instrument reports, and chain-of-custody by run_id

Important constraint: we need one result per provided run_id/sample_event/test field. Pooled averages or narrative certificates alone will not satisfy the study.

Could you please confirm:
- Can they run a minimal aqueous neural-medium material-blank screen before a full E&L program?
- Can they preserve run_id-level aliquot identity and source-file provenance?
- Can they add basic pH/osmolality/conductivity, or should they only be used after Phase A shows extractables or particulate concerns?
- Whether you can fill or accept the provided Phase A CSV schema without changing column names
- Minimum aliquot volume, sample container, and sample count requirements
- Expected turnaround time, quote range, sample acceptance constraints, and whether SDS/lot documentation is required before shipping

Attached/package files to review:
- reports/zrc_nd_phase_a_service_request.md
- data/zrc_nd_phase_a_sentinel_template.csv
- reports/zrc_nd_phase_a_sentinel_packet.md
- data/zrc_nd_phase_a_sentinel_sample_manifest.csv
- data/zrc_nd_phase_a_sample_labels.csv
- data/zrc_nd_phase_a_chain_of_custody.csv
- reports/zrc_nd_phase_a_chain_of_custody.md
- reports/zrc_nd_next_measurements.md
- data/zrc_nd_3p5k_guard_validation_package.json
- reports/zrc_nd_run_plan.md

This is exploratory R&D screening. We are not requesting a material suitability claim from the vendor; we only need traceable raw measurements to feed our internal Phase A gate.

Thank you.
```

## Boundary

Vendor capability claims and supplier guidance do not count as material evidence. Only returned real run-level measurements that pass LIMINA QC and claim audit can advance the material.
