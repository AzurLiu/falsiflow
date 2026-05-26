# NHI-PEDOT H-A RFQ Send Confirmation Entry Sheet

This sheet is for source-backed manual review of non-EML send confirmations. It is not measured evidence.

**Status:** `h_a_rfq_send_confirmation_entry_sheet_waiting_for_confirmation_files`
**Rows:** 4
**Source files present:** 0
**Ready to apply:** 0
**Blocked:** 0
**Waiting for confirmation files:** 4
**CSV:** `data/nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.csv`

## Rows

| Vendor | Status | Source file | Current SHA-256 | Apply | Sent at | Confirmation ID |
| --- | --- | --- | --- | --- | --- | --- |
| Materials Metric | `waiting_for_confirmation_file` | `data/rfq_send_confirmation_files/h_a/materials_metric_send_confirmation.txt` | `-` | `no` | `-` | `-` |
| The Osmolality Lab | `waiting_for_confirmation_file` | `data/rfq_send_confirmation_files/h_a/the_osmolality_lab_send_confirmation.txt` | `-` | `no` | `-` | `-` |
| Cambridge Polymer Group | `waiting_for_confirmation_file` | `data/rfq_send_confirmation_files/h_a/cambridge_polymer_group_hydrogel_send_confirmation.txt` | `-` | `no` | `-` | `-` |
| MilliporeSigma Cell Culture Media Stability and Testing Services | `waiting_for_confirmation_file` | `data/rfq_send_confirmation_files/h_a/sigmaaldrich_media_testing_send_confirmation.txt` | `-` | `no` | `-` | `-` |

## Apply Rule

Set `apply=yes` only after a real confirmation file exists, `sent_at`, `sent_by`, `message_id_or_confirmation`, and `human_reviewed_by` are filled, and `sent_bundle_sha256_to_record` equals `expected_bundle_sha256`.

Then run:

`python3 scripts/apply_nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.py`

## Boundary

Manual RFQ send-confirmation entries document outreach logistics only. They are not quote replies, measurements, or material suitability evidence.
