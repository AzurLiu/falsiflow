# ZRC-ND Phase A Delivery Package Manifest

This manifest tracks the files needed to request real acellular Phase A measurements. It is not measured evidence.

**Status:** `ready_to_send`
**Active candidate:** `limina_zrc_nd_v0_1`

## Package Files

| ID | Required | Exists | Bytes | SHA256 | Role | Path |
| --- | --- | --- | ---: | --- | --- | --- |
| `service_request` | `true` | `true` | 5958 | `b238fae53a65e6d6...` | Primary Phase A lab/cooperator request: matrix, deliverables, acceptance gate, and rejection rules. | `reports/zrc_nd_phase_a_service_request.md` |
| `phase_a_template` | `true` | `true` | 2577 | `e818351e23fb1dda...` | The 8-row Phase A CSV to fill with real medium-integrity measurements. | `data/zrc_nd_phase_a_sentinel_template.csv` |
| `sentinel_packet` | `true` | `true` | 2121 | `3909825a725dda64...` | Human-readable Phase A sentinel packet and gate description. | `reports/zrc_nd_phase_a_sentinel_packet.md` |
| `sample_manifest` | `true` | `true` | 3819 | `9c6b4f82658ea78b...` | Sample-level manifest tying run_id to sample_event, article, timepoint, and readouts. | `data/zrc_nd_phase_a_sentinel_sample_manifest.csv` |
| `sample_labels` | `true` | `true` | 7214 | `916a6fbd8f037631...` | Printable/transferable labels with sample IDs, planned container IDs, article IDs, and handling notes. | `data/zrc_nd_phase_a_sample_labels.csv` |
| `chain_of_custody_csv` | `true` | `true` | 4185 | `d78e28317e5a2573...` | Blank chain-of-custody transfer rows to complete during preparation, release, receipt, and return. | `data/zrc_nd_phase_a_chain_of_custody.csv` |
| `chain_of_custody_report` | `true` | `true` | 3921 | `956241196106ba96...` | Human-readable sample handoff instructions, blank fields, and rejection rules. | `reports/zrc_nd_phase_a_chain_of_custody.md` |
| `next_measurements` | `true` | `true` | 2320 | `401abb7ac6fc1049...` | Current adaptive selector output showing why Phase A is the next ZRC-ND batch. | `reports/zrc_nd_next_measurements.md` |
| `validation_package` | `true` | `true` | 16446 | `24d8c12bf6184352...` | Machine-readable validation package defining articles, assays, fields, and gates. | `data/zrc_nd_3p5k_guard_validation_package.json` |
| `run_plan` | `true` | `true` | 910 | `97fae50d5aef7e2d...` | Full non-cell run plan context; Phase A is the current first sentinel subset. | `reports/zrc_nd_run_plan.md` |

## Expected Return Files

| ID | Path | Acceptance |
| --- | --- | --- |
| `completed_phase_a_csv` | `data/zrc_nd_phase_a_sentinel_template.csv` | Same schema as the package template, with all requested real values and provenance fields filled. |
| `instrument_exports` | `external_lab_exports/zrc_nd_phase_a/` | Original pH, osmolality, conductivity, and inspection files reconciled to run_id or sample_id. |
| `completed_chain_of_custody` | `data/zrc_nd_phase_a_chain_of_custody.csv` | Prepared/released/received fields, actual lot IDs, module/tube IDs, condition on receipt, and deviations filled. |
| `deviation_log` | `reports/zrc_nd_phase_a_deviation_log.md` | Lists every deviation from membrane, module, guard, medium, timing, temperature, rinse, or instrument assumptions. |

## Post-Return Verification

```bash
python3 scripts/merge_zrc_nd_measurements.py
python3 scripts/interpret_zrc_nd_sentinel.py
python3 scripts/evaluate_zrc_nd_validation_runs.py --runs data/zrc_nd_validation_runs_active.csv
python3 scripts/suggest_zrc_nd_next_measurements.py --runs data/zrc_nd_validation_runs_active.csv
python3 scripts/audit_zrc_nd_readiness.py
python3 scripts/run_limina_iteration.py
```

## Boundary

This manifest only packages the Phase A measurement request. ZRC-ND suitability still requires real Phase A/B/C rows, biological follow-up, readiness audit pass, and final claim audit.
