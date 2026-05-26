# ZRC-ND Phase A RFQ Reply Action Pack

This pack guides source-backed RFQ reply intake and provider selection. It is not measured evidence.

**Status:** `zrc_phase_a_rfq_reply_action_pack_waiting_for_send`
**Action rows:** 4
**Waiting for send:** 4
**Awaiting reply:** 0
**Needs source file:** 0
**Needs review fields:** 0
**Ready for reply-log apply:** 0
**CSV:** `data/zrc_nd_phase_a_rfq_reply_action_queue.csv`
**Reply review templates:** `data/rfq_reply_review_templates/zrc_phase_a`

## Action Queue

| Vendor | Status | Reply source file to save | Missing review fields | Next action |
| --- | --- | --- | --- | --- |
| Pacific BioLabs Physicochemical Properties Testing | `waiting_for_rfq_send` | `data/rfq_reply_files/zrc_phase_a/pacific_biolabs_physicochemical_reply.txt` | `can_cover_full_phase_a;needs_split_scope;run_id_level_raw_data;phase_a_media_panel_coverage;csv_schema_acceptance;sample_handling_fit;source_file_provenance;non_glp_scope_control` | Send the ZRC-ND Phase A RFQ first, then save a real send confirmation and apply the send log. |
| MilliporeSigma Cell Culture Media Stability and Testing Services | `waiting_for_rfq_send` | `data/rfq_reply_files/zrc_phase_a/sigmaaldrich_media_testing_reply.txt` | `can_cover_full_phase_a;needs_split_scope;run_id_level_raw_data;phase_a_media_panel_coverage;csv_schema_acceptance;sample_handling_fit;source_file_provenance;non_glp_scope_control` | Send the ZRC-ND Phase A RFQ first, then save a real send confirmation and apply the send log. |
| The Osmolality Lab | `waiting_for_rfq_send` | `data/rfq_reply_files/zrc_phase_a/the_osmolality_lab_reply.txt` | `can_cover_full_phase_a;needs_split_scope;run_id_level_raw_data;phase_a_media_panel_coverage;csv_schema_acceptance;sample_handling_fit;source_file_provenance;non_glp_scope_control` | Send the ZRC-ND Phase A RFQ first, then save a real send confirmation and apply the send log. |
| Jordi Labs Analytical Testing | `waiting_for_rfq_send` | `data/rfq_reply_files/zrc_phase_a/jordi_labs_el_polymer_reply.txt` | `can_cover_full_phase_a;needs_split_scope;run_id_level_raw_data;phase_a_media_panel_coverage;csv_schema_acceptance;sample_handling_fit;source_file_provenance;non_glp_scope_control` | Send the ZRC-ND Phase A RFQ first, then save a real send confirmation and apply the send log. |

## Hard Required Selection Fields

- `run_id_level_raw_data`
- `csv_schema_acceptance`
- `sample_handling_fit`
- `source_file_provenance`
- `non_glp_scope_control`

## After A Reply Arrives

1. Save the original vendor reply at the listed `reply_source_file` path.
2. Run `python3 scripts/intake_limina_rfq_replies.py --profile zrc_phase_a`.
3. Run `python3 scripts/apply_limina_rfq_reply_log.py --profile zrc_phase_a`.
4. Run `python3 scripts/evaluate_zrc_nd_phase_a_quote_replies.py` and then the full iteration.

## Boundary

This reply action pack is sourcing logistics only. Vendor replies and quotes can authorize execution, but only returned measurement files can become ZRC-ND material evidence.
