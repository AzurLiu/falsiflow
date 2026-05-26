# Materials Metric H-A RFQ Reply Review Notes

This is a planning template only. Do not cite this file as `reply_source_file`.

After a real vendor reply arrives, save the original email export, quote PDF, attached proposal, or confirmation page to:

`data/rfq_reply_files/h_a/materials_metric_reply.txt`

The intake script can register the matching row in `data/nhi_pedot_h_a_rfq_reply_log.csv` for review.
Use these fields if manual review is needed:

- `candidate_id`: `materials_metric`
- `reply_status`: `quote_received`, `received`, `clarification_received`, `declined`, or `cannot_quote`
- `reply_at`: timestamp or date of the vendor reply
- `responder_name`: sender/person/team name
- `quote_id_or_reference`: quote ID, ticket, email subject, or proposal reference
- `reply_source_file`: `data/rfq_reply_files/h_a/materials_metric_reply.txt`

Review fields to extract from the original reply:
- `can_cover_full_h_a`
- `needs_split_scope`
- `run_id_level_raw_data`
- `media_physicochemical_coverage`
- `coupon_physical_coverage`
- `csv_schema_acceptance`
- `bundle_entry_sheet_acceptance`
- `sample_handling_fit`
- `non_glp_scope_control`

Hard required fields for execution selection:
- `run_id_level_raw_data`
- `csv_schema_acceptance`
- `sample_handling_fit`
- `non_glp_scope_control`

Do not select a provider unless the reply is source-backed and preserves run_id-level raw data.

After saving the real reply, run:

`python3 scripts/intake_limina_rfq_replies.py --profile h_a`

Then run:

`python3 scripts/apply_limina_rfq_reply_log.py --profile h_a`
