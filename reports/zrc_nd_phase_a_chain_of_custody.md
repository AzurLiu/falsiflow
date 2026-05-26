# ZRC-ND Phase A Sample Labels and Chain of Custody

This packet prepares sample handoff for real acellular Phase A measurements. It is not measured evidence.

**Status:** `ready_for_phase_a_sample_handoff`
**Active candidate:** `limina_zrc_nd_v0_1`
**Service request:** `ready_to_request_real_phase_a_measurements`
**Sample labels:** 16
**Chain-of-custody rows:** 16
**Unique Phase A runs:** 8
**Pending transfers:** 16

## Output Files

| Artifact | Path |
| --- | --- |
| `sample_labels_csv` | `data/zrc_nd_phase_a_sample_labels.csv` |
| `chain_of_custody_csv` | `data/zrc_nd_phase_a_chain_of_custody.csv` |
| `json` | `data/zrc_nd_phase_a_chain_of_custody.json` |
| `report` | `reports/zrc_nd_phase_a_chain_of_custody.md` |

## Label Preview

| Container | Sample | Article | Timepoint | Event | Condition |
| --- | --- | --- | --- | --- | --- |
| `ZRC-A-01-BASELINE-RC-3P5M-GUA-0-H-INITIAL` | `ZRCND-A-baseline_rc_3p5m_guard-R1-0h-initial` | `baseline_rc_3p5m_guard` | 0 h | `initial` | unmodified baseline |
| `ZRC-A-02-BASELINE-RC-3P5M-GUA-0-H-FINAL` | `ZRCND-A-baseline_rc_3p5m_guard-R1-0h-final` | `baseline_rc_3p5m_guard` | 0 h | `final` | unmodified baseline |
| `ZRC-A-03-BASELINE-RC-3P5M-GUA-24-H-INITIAL` | `ZRCND-A-baseline_rc_3p5m_guard-R1-24h-initial` | `baseline_rc_3p5m_guard` | 24 h | `initial` | unmodified baseline |
| `ZRC-A-04-BASELINE-RC-3P5M-GUA-24-H-FINAL` | `ZRCND-A-baseline_rc_3p5m_guard-R1-24h-final` | `baseline_rc_3p5m_guard` | 24 h | `final` | unmodified baseline |
| `ZRC-A-05-CHALLENGE-ZRC-ND-10M-0-H-INITIAL` | `ZRCND-A-challenge_zrc_nd_10m_guard-R1-0h-initial` | `challenge_zrc_nd_10m_guard` | 0 h | `initial` | high-clearance retention challenge |
| `ZRC-A-06-CHALLENGE-ZRC-ND-10M-0-H-FINAL` | `ZRCND-A-challenge_zrc_nd_10m_guard-R1-0h-final` | `challenge_zrc_nd_10m_guard` | 0 h | `final` | high-clearance retention challenge |
| `ZRC-A-07-CHALLENGE-ZRC-ND-10M-24-H-INITIAL` | `ZRCND-A-challenge_zrc_nd_10m_guard-R1-24h-initial` | `challenge_zrc_nd_10m_guard` | 24 h | `initial` | high-clearance retention challenge |
| `ZRC-A-08-CHALLENGE-ZRC-ND-10M-24-H-FINAL` | `ZRCND-A-challenge_zrc_nd_10m_guard-R1-24h-final` | `challenge_zrc_nd_10m_guard` | 24 h | `final` | high-clearance retention challenge |
| `ZRC-A-09-LEAD-ZRC-ND-3P5M-GUA-0-H-INITIAL` | `ZRCND-A-lead_zrc_nd_3p5m_guard-R1-0h-initial` | `lead_zrc_nd_3p5m_guard` | 0 h | `initial` | lead candidate |
| `ZRC-A-10-LEAD-ZRC-ND-3P5M-GUA-0-H-FINAL` | `ZRCND-A-lead_zrc_nd_3p5m_guard-R1-0h-final` | `lead_zrc_nd_3p5m_guard` | 0 h | `final` | lead candidate |
| `ZRC-A-11-LEAD-ZRC-ND-3P5M-GUA-24-H-INITIAL` | `ZRCND-A-lead_zrc_nd_3p5m_guard-R1-24h-initial` | `lead_zrc_nd_3p5m_guard` | 24 h | `initial` | lead candidate |
| `ZRC-A-12-LEAD-ZRC-ND-3P5M-GUA-24-H-FINAL` | `ZRCND-A-lead_zrc_nd_3p5m_guard-R1-24h-final` | `lead_zrc_nd_3p5m_guard` | 24 h | `final` | lead candidate |

## Blank Fields To Complete During Transfer

- `prepared_by`
- `prepared_at`
- `module_or_tube_id`
- `membrane_lot`
- `prefilter_lot`
- `housing_material`
- `medium_name`
- `medium_lot`
- `initial_volume_ml`
- `exposure_started_at`
- `exposure_ended_at`
- `temperature_c`
- `released_by`
- `released_at`
- `carrier_or_transfer_method`
- `received_by`
- `received_at`
- `condition_on_receipt`
- `storage_location`
- `instrument_export_returned`
- `deviation_notes`

## Rejection Rules

- Do not treat a label row, planned container ID, or blank custody row as measured evidence.
- Do not pool initial and final events before pH, osmolality, or conductivity entry.
- Do not replace missing transfer fields with pending, TBD, unknown, synthetic, or fixture markers.
- Do not accept returned Phase A rows unless instrument exports and deviation notes can be reconciled to run_id.

## Boundary

Labels and blank custody rows are logistics artifacts only. ZRC-ND Phase A remains unmeasured until real medium-integrity values and provenance are returned.
