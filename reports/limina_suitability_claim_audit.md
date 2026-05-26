# LIMINA Suitability Claim Audit

**Claim ready:** `false`
**Claim candidate:** `-`
**Claim parent technology:** `-`
**Active discovery candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Portfolio status:** `no_suitable_material_yet`
**Portfolio primary next branch:** `limina_nhi_pedot_laminin_v0_1`

## Candidate Decisions

| Technology | Claim candidate | Decision | Evidence status | Provenance | Blockers |
| --- | --- | --- | --- | --- | --- |
| `limina_zrc_nd_v0_1` | `limina_zrc_nd_v0_1` | `not_claim_ready` | readiness=not_suitable_yet_no_measured_data, suitable=False | non_cell=0/0 measured rows; synthetic=0; placeholder=0; source_file_issues=0; claimable=false; biological=0/0 measured rows; synthetic=0; placeholder=0; source_file_issues=0; claimable=false | ZRC-ND readiness audit is not suitable; measured non-cell and biological gates are incomplete.; ZRC-ND non-cell source has no measured run rows.; ZRC-ND biological source has no measured run rows. |
| `limina_nhi_pedot_laminin_v0_1` | `limina_alg_lam_pedot_lowdose_v0_2` | `not_claim_ready` | h_a_status=h_a_invalid_provenance, h_a_measured_rows=0, forward_status=preregistered_waiting_for_h_a, forward_rows=28, coupon_status=no_data, coupon_result_rows=0, long_status=no_data, long_result_rows=0 | h_a_sentinel=0/12 measured rows; synthetic=0; placeholder=12; source_file_issues=0; claimable=false; coupon=0/0 measured rows; synthetic=0; placeholder=0; source_file_issues=0; claimable=false; long_duration=0/0 measured rows; synthetic=0; placeholder=0; source_file_issues=0; claimable=false | NHI-PEDOT H-A sentinel is `h_a_invalid_provenance`, not a QC-clean pass/continue status.; NHI-PEDOT coupon gates are `no_data`, not `nhi_pedot_passes_gates`.; NHI-PEDOT H-B/H-C forward gate package is preregistered and waiting for H-A, not measured evidence.; NHI-PEDOT long-duration gates are `no_data`, not `nhi_pedot_long_passes_gates`.; NHI-PEDOT H-A sentinel source has no measured run rows.; NHI-PEDOT H-A sentinel source contains placeholder or pending-measurement rows.; NHI-PEDOT coupon source has no measured run rows.; NHI-PEDOT long-duration source has no measured run rows. |

## Provenance Inputs

| Technology | Source | Path | Rows | Measured rows | Synthetic rows | Placeholder rows | Source-file issues | Claimable source | Examples |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `limina_zrc_nd_v0_1` | non_cell | `data/zrc_nd_validation_runs_active.csv` | 0 | 0 | 0 | 0 | 0 | `false` | - |
| `limina_zrc_nd_v0_1` | biological | `data/zrc_nd_bio_runs_template.csv` | 0 | 0 | 0 | 0 | 0 | `false` | - |
| `limina_nhi_pedot_laminin_v0_1` | h_a_sentinel | `data/nhi_pedot_h_a_runs_active.csv` | 12 | 0 | 0 | 12 | 0 | `false` | NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-0h, NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-24h, NHIPEDOT-H-A-challenge_nhi_pedot_high_loading-R1-72h, NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h, NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h, NHIPEDOT-H-A-hydrogel_laminin_control-R1-72h, NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-0h, NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h |
| `limina_nhi_pedot_laminin_v0_1` | coupon | `data/nhi_pedot_runs_template.csv` | 0 | 0 | 0 | 0 | 0 | `false` | - |
| `limina_nhi_pedot_laminin_v0_1` | long_duration | `data/nhi_pedot_long_runs_template.csv` | 0 | 0 | 0 | 0 | 0 | `false` | - |

## Interpretation

- This audit is the gate for saying LIMINA has found a suitable material technology.
- Synthetic fixtures can prove evaluator logic, but they are rejected as material evidence.
- Template rows with missing dates, `pending_real_measurement`, `record_exact`, `record_actual`, or `record_lot` placeholders are rejected until replaced by measured provenance.
- A future claim requires passing gate status and CSV provenance with non-synthetic measured rows that cite existing source_file records under the source-file manifest.
