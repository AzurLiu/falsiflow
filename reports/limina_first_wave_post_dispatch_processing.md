# LIMINA First-Wave Post-Dispatch Processing

This report processes saved RFQ confirmations and replies. It is not measured evidence.

**Status:** `first_wave_post_dispatch_waiting_for_real_send_confirmations`
**First-wave cockpit:** `first_wave_rfq_dispatch_cockpit_ready_for_manual_send`; rows=8; ready=8; confirmations=0; replies=0
**Failed commands:** 0

## Track Summaries

| Track | Send intake | Send log | Reply intake | Reply log | Quote selection | Execution release | Vendor return |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `h_a` | `nhi_pedot_h_a_rfq_send_confirmation_intake_waiting_for_confirmation_files`; files=0; applied=0; review=0 | `nhi_pedot_h_a_rfq_send_log_waiting_for_sent_entries`; sent=0; valid=0 | `nhi_pedot_h_a_rfq_reply_intake_waiting_for_reply_files`; files=0; applied=0; review=0 | `nhi_pedot_h_a_rfq_reply_log_waiting_for_reply_files`; received=0; valid=0 | `pending_outreach`; replies=0; source_backed=0; shortlist=0 | `nhi_pedot_h_a_execution_release_blocked_no_source_backed_provider_selection`; ready=false; released=false | `awaiting_vendor_return_files` |
| `zrc_phase_a` | `zrc_nd_phase_a_rfq_send_confirmation_intake_waiting_for_confirmation_files`; files=0; applied=0; review=0 | `zrc_nd_phase_a_rfq_send_log_waiting_for_sent_entries`; sent=0; valid=0 | `zrc_nd_phase_a_rfq_reply_intake_waiting_for_reply_files`; files=0; applied=0; review=0 | `zrc_nd_phase_a_rfq_reply_log_waiting_for_reply_files`; received=0; valid=0 | `pending_outreach`; replies=0; source_backed=0; shortlist=0 | `zrc_nd_phase_a_execution_release_blocked_no_source_backed_provider_selection`; ready=false; released=false | `awaiting_vendor_return_files` |

## Commands Run

| Command | Return | Purpose |
| --- | ---: | --- |
| `intake_h_a_send_confirmations` | 0 | Register source-backed H-A sent-email or web-form confirmations. |
| `render_h_a_non_eml_confirmation_sheet` | 0 | Refresh guarded H-A manual-confirmation rows for non-EML confirmations. |
| `apply_h_a_non_eml_confirmation_sheet` | 0 | Apply reviewed H-A non-EML confirmation entries into the send log. |
| `apply_h_a_send_log` | 0 | Apply verified H-A send rows into the quote tracker. |
| `intake_h_a_replies` | 0 | Register original H-A reply source files for review. |
| `apply_h_a_reply_log` | 0 | Apply reviewed H-A reply fields into the quote tracker. |
| `evaluate_h_a_quotes` | 0 | Evaluate source-backed H-A quote replies for provider selection. |
| `apply_h_a_execution_authorization` | 0 | Validate any H-A execution authorization records. |
| `audit_h_a_execution_release` | 0 | Check whether H-A execution can be released after provider selection and authorization. |
| `check_h_a_vendor_return` | 0 | Check whether real H-A return files are ready for merge/QC. |
| `intake_zrc_send_confirmations` | 0 | Register source-backed ZRC sent-email or web-form confirmations. |
| `render_zrc_non_eml_confirmation_sheet` | 0 | Refresh guarded ZRC manual-confirmation rows for non-EML confirmations. |
| `apply_zrc_non_eml_confirmation_sheet` | 0 | Apply reviewed ZRC non-EML confirmation entries into the send log. |
| `apply_zrc_send_log` | 0 | Apply verified ZRC send rows into the quote tracker. |
| `intake_zrc_replies` | 0 | Register original ZRC reply source files for review. |
| `apply_zrc_reply_log` | 0 | Apply reviewed ZRC reply fields into the quote tracker. |
| `evaluate_zrc_quotes` | 0 | Evaluate source-backed ZRC quote replies for provider selection. |
| `apply_zrc_execution_authorization` | 0 | Validate any ZRC execution authorization records. |
| `audit_zrc_execution_release` | 0 | Check whether ZRC execution can be released after provider selection and authorization. |
| `check_zrc_vendor_return` | 0 | Check whether real ZRC return files are ready for merge/QC. |
| `refresh_first_wave_cockpit` | 0 | Refresh the combined dispatch cockpit after processing saved files. |

## Next Commands

- `python3 scripts/process_limina_first_wave_post_dispatch.py`
- `python3 scripts/run_limina_iteration.py`

## Boundary

This processing step handles outreach and sourcing artifacts only. It does not create measurements, authorize execution, or support a material suitability claim without real returned measurement rows.
