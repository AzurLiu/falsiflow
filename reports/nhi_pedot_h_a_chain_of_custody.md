# NHI-PEDOT H-A Sample Labels and Chain of Custody

This packet prepares sample handoff for real acellular H-A measurements. It is not measured evidence.

**Status:** `ready_for_sample_handoff`
**Active candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Service request:** `ready_to_request_real_measurements`
**Sample labels:** 36
**Chain-of-custody rows:** 36
**Unique H-A runs:** 12
**Pending transfers:** 36

## Output Files

| Artifact | Path |
| --- | --- |
| `sample_labels_csv` | `data/nhi_pedot_h_a_sample_labels.csv` |
| `chain_of_custody_csv` | `data/nhi_pedot_h_a_chain_of_custody.csv` |
| `json` | `data/nhi_pedot_h_a_chain_of_custody.json` |
| `report` | `reports/nhi_pedot_h_a_chain_of_custody.md` |

## Label Preview

| Container | Sample | Article | Timepoint | Event | Condition |
| --- | --- | --- | --- | --- | --- |
| `H-A-01-NO-COATING-MEA-CON-0-H-INITIAL` | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h-initial` | `no_coating_mea_control` | 0 h | `initial` | matched medium/device control |
| `H-A-02-NO-COATING-MEA-CON-0-H-FINAL` | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h-final` | `no_coating_mea_control` | 0 h | `final` | matched medium/device control |
| `H-A-03-NO-COATING-MEA-CON-0-H-PHYSICAL-INS` | `NHIPEDOT-H-A-no_coating_mea_control-R1-0h-physical_inspection` | `no_coating_mea_control` | 0 h | `physical_inspection` | matched medium/device control |
| `H-A-04-NO-COATING-MEA-CON-24-H-INITIAL` | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h-initial` | `no_coating_mea_control` | 24 h | `initial` | matched medium/device control |
| `H-A-05-NO-COATING-MEA-CON-24-H-FINAL` | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h-final` | `no_coating_mea_control` | 24 h | `final` | matched medium/device control |
| `H-A-06-NO-COATING-MEA-CON-24-H-PHYSICAL-INS` | `NHIPEDOT-H-A-no_coating_mea_control-R1-24h-physical_inspection` | `no_coating_mea_control` | 24 h | `physical_inspection` | matched medium/device control |
| `H-A-07-NO-COATING-MEA-CON-72-H-INITIAL` | `NHIPEDOT-H-A-no_coating_mea_control-R1-72h-initial` | `no_coating_mea_control` | 72 h | `initial` | matched medium/device control |
| `H-A-08-NO-COATING-MEA-CON-72-H-FINAL` | `NHIPEDOT-H-A-no_coating_mea_control-R1-72h-final` | `no_coating_mea_control` | 72 h | `final` | matched medium/device control |
| `H-A-09-NO-COATING-MEA-CON-72-H-PHYSICAL-INS` | `NHIPEDOT-H-A-no_coating_mea_control-R1-72h-physical_inspection` | `no_coating_mea_control` | 72 h | `physical_inspection` | matched medium/device control |
| `H-A-10-HYDROGEL-LAMININ-C-0-H-INITIAL` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h-initial` | `hydrogel_laminin_control` | 0 h | `initial` | soft matrix control |
| `H-A-11-HYDROGEL-LAMININ-C-0-H-FINAL` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h-final` | `hydrogel_laminin_control` | 0 h | `final` | soft matrix control |
| `H-A-12-HYDROGEL-LAMININ-C-0-H-PHYSICAL-INS` | `NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h-physical_inspection` | `hydrogel_laminin_control` | 0 h | `physical_inspection` | soft matrix control |

## Blank Fields To Complete During Transfer

- `prepared_by`
- `prepared_at`
- `preparation_batch_id`
- `medium_name`
- `medium_lot`
- `coupon_or_well_id`
- `released_by`
- `released_at`
- `carrier_or_transfer_method`
- `received_by`
- `received_at`
- `condition_on_receipt`
- `storage_location`
- `source_file_returned`
- `deviation_notes`

## Rejection Rules

- Do not treat a label row, planned container ID, or blank custody row as measured evidence.
- Do not pool samples or collapse initial/final/physical-inspection events before raw data entry.
- Do not replace missing transfer fields with pending, TBD, unknown, synthetic, or fixture markers.
- Do not accept returned measurement rows unless source_file links back to instrument export or image files.

## Boundary

Pending or blank transfer logs are not evidence. Only returned raw measurement rows with real values, provenance, and source files can count toward H-A.
