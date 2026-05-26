# NHI-PEDOT H-A RFQ Reply Log

This report validates source-backed RFQ replies. It is not measured evidence.

**Status:** `nhi_pedot_h_a_rfq_reply_log_waiting_for_reply_files`
**Reply log CSV:** `data/nhi_pedot_h_a_rfq_reply_log.csv`
**Reply file directory:** `data/rfq_reply_files/h_a`
**Tracker CSV:** `data/nhi_pedot_h_a_quote_tracker.csv`
**Rows:** 4
**Pending rows:** 4
**Received rows:** 0
**Valid reply rows:** 0
**Applied tracker field updates:** 0
**Errors:** 0
**Warnings:** 0

## Required When Received

- `reply_at`
- `responder_name`
- `reply_source_file`
- `can_cover_full_h_a`
- `needs_split_scope`
- `run_id_level_raw_data`
- `media_physicochemical_coverage`
- `coupon_physical_coverage`
- `csv_schema_acceptance`
- `bundle_entry_sheet_acceptance`
- `sample_handling_fit`
- `non_glp_scope_control`

## Reply Status Values

- `awaiting_reply`
- `cannot_quote`
- `clarification_received`
- `declined`
- `needs_clarification`
- `no_reply`
- `not_sent_yet`
- `out_of_scope`
- `pending_reply`
- `quote_received`
- `received`
- `reply_received`

## Next Step

After a real RFQ reply arrives, save the original reply file in the reply directory, fill the matching row, rerun this script, then rerun the iteration.

## Boundary

RFQ reply logs and quote trackers document sourcing and execution selection only. They are not material evidence and cannot advance suitability gates without returned measured rows.
