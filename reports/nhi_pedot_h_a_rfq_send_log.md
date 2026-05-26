# NHI-PEDOT H-A RFQ Send Log

This report validates RFQ send confirmations. It is not measured evidence.

**Status:** `nhi_pedot_h_a_rfq_send_log_waiting_for_sent_entries`
**Send log CSV:** `data/nhi_pedot_h_a_rfq_send_log.csv`
**Send confirmation directory:** `data/rfq_send_confirmation_files/h_a`
**Tracker CSV:** `data/nhi_pedot_h_a_quote_tracker.csv`
**Rows:** 4
**Pending rows:** 4
**Sent rows:** 0
**Valid sent rows:** 0
**Applied tracker contact dates:** 0
**Errors:** 0
**Warnings:** 0

## Required When Sent

- `sent_at`
- `sent_by`
- `send_method`
- `recipient_or_form`
- `message_id_or_confirmation`
- `send_confirmation_source_file`

## Send Status Values

- `do_not_send`
- `emailed`
- `form_submitted`
- `needs_attention`
- `paused`
- `pending_send`
- `sent`
- `submitted`

## Next Step

Fill a row as `sent` only after a real email/form submission has been made and an original confirmation file has been saved. Rerun this script, then rerun the iteration.

## Boundary

RFQ send logs and quote trackers only document execution logistics. They are not material evidence and cannot advance suitability gates without returned measured rows.
