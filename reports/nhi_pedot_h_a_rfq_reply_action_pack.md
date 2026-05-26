# NHI-PEDOT H-A RFQ Reply Action Pack

This pack guides source-backed RFQ reply intake and provider selection. It is not measured evidence.

**Status:** `h_a_rfq_reply_action_pack_waiting_for_send`
**Action rows:** 4
**Waiting for send:** 4
**Awaiting reply:** 0
**Needs source file:** 0
**Needs review fields:** 0
**Ready for reply-log apply:** 0
**CSV:** `data/nhi_pedot_h_a_rfq_reply_action_queue.csv`
**Reply review templates:** `data/rfq_reply_review_templates/h_a`

## Action Queue

| Vendor | Status | Reply source file to save | Missing review fields | Next action |
| --- | --- | --- | --- | --- |
| Materials Metric | `waiting_for_rfq_send` | `data/rfq_reply_files/h_a/materials_metric_reply.txt` | `can_cover_full_h_a;needs_split_scope;run_id_level_raw_data;media_physicochemical_coverage;coupon_physical_coverage;csv_schema_acceptance;bundle_entry_sheet_acceptance;sample_handling_fit;non_glp_scope_control` | Send the RFQ first, then save a real send confirmation and apply the send log. |
| The Osmolality Lab | `waiting_for_rfq_send` | `data/rfq_reply_files/h_a/the_osmolality_lab_reply.txt` | `can_cover_full_h_a;needs_split_scope;run_id_level_raw_data;media_physicochemical_coverage;coupon_physical_coverage;csv_schema_acceptance;bundle_entry_sheet_acceptance;sample_handling_fit;non_glp_scope_control` | Send the RFQ first, then save a real send confirmation and apply the send log. |
| Cambridge Polymer Group | `waiting_for_rfq_send` | `data/rfq_reply_files/h_a/cambridge_polymer_group_hydrogel_reply.txt` | `can_cover_full_h_a;needs_split_scope;run_id_level_raw_data;media_physicochemical_coverage;coupon_physical_coverage;csv_schema_acceptance;bundle_entry_sheet_acceptance;sample_handling_fit;non_glp_scope_control` | Send the RFQ first, then save a real send confirmation and apply the send log. |
| MilliporeSigma Cell Culture Media Stability and Testing Services | `waiting_for_rfq_send` | `data/rfq_reply_files/h_a/sigmaaldrich_media_testing_reply.txt` | `can_cover_full_h_a;needs_split_scope;run_id_level_raw_data;media_physicochemical_coverage;coupon_physical_coverage;csv_schema_acceptance;bundle_entry_sheet_acceptance;sample_handling_fit;non_glp_scope_control` | Send the RFQ first, then save a real send confirmation and apply the send log. |

## Hard Required Selection Fields

- `run_id_level_raw_data`
- `csv_schema_acceptance`
- `sample_handling_fit`
- `non_glp_scope_control`

## After A Reply Arrives

1. Save the original vendor reply at the listed `reply_source_file` path.
2. Run `python3 scripts/intake_limina_rfq_replies.py --profile h_a`.
3. Run `python3 scripts/apply_limina_rfq_reply_log.py --profile h_a`.
4. Run `python3 scripts/evaluate_nhi_pedot_h_a_quote_replies.py` and then the full iteration.

## Boundary

This reply action pack is sourcing logistics only. Vendor replies and quotes can authorize execution, but only returned measurement files can become material evidence.
