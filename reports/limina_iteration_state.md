# LIMINA Local Iteration State

This report records one local dry-lab discovery iteration. It is not a material suitability claim.

**Run timestamp:** `2026-05-24T07:25:44+00:00`
**Iteration status:** `completed`
**Top candidate:** `limina_alg_lam_pedot_lowdose_v0_2`
**Top priority:** `promote_now`
**Mission state:** `awaiting_real_h_a_measurements`
**Claim ready:** `false`
**Claim status:** `no_suitable_material_claim_ready`
**Portfolio bypass audit:** `no_h_a_bypass_claim_ready`; non_H-A_claim_ready=0; top_non_H-A=limina_all_dry_zwitterionic_external_v0_1

## Current Gate State

| Area | Value |
| --- | --- |
| H-A status | `h_a_invalid_provenance` |
| H-A measured rows | 0 / 12 |
| H-A placeholder rows | 12 |
| H-A synthetic rows | 0 |
| H-A QC | `h_a_intake_not_ready`; errors=183; warnings=24 |
| H-A source values sheet | `h_a_source_values_sheet_ready`; rows=228; filled=0; source-files=0; import-ready=0 |
| H-A source drop plan | `nhi_pedot_h_a_source_drop_plan_ready`; planned files=228; dirs=48; existing files=0; missing files=228 |
| H-A source unlock pack | `h_a_source_unlock_pack_ready`; source rows=228; bundles=96; existing files=0; missing files=96 |
| H-A bundle entry sheet | `h_a_bundle_entry_sheet_ready`; bundles=96; filled=0; ready-to-apply=0; existing files=0 |
| H-A vendor bundle entry sheet | `h_a_vendor_bundle_entry_sheet_ready`; bundles=96; ready=0; blocked=0; existing files=0 |
| H-A bundle entry apply | `h_a_bundle_entry_apply_no_apply_rows`; bundles=0; source rows=0; errors=0 |
| H-A vendor bundle entry return apply | `h_a_vendor_bundle_entry_return_no_apply_rows`; sheet-exists=true; bundles=0; source rows=0; errors=0 |
| H-A source file templates | `nhi_pedot_h_a_source_file_template_pack_ready`; templates=8; target files=228 |
| H-A raw CSV extraction | `h_a_raw_csv_value_extraction_no_raw_csv`; files=0; rows=0; errors=0 |
| H-A source value import | `h_a_source_value_import_no_importable_rows`; files=2; rows=228; imported=0; errors=0 |
| Raw merge | applied=0; unresolved=0 |
| Bench sheet | tasks=12; blank raw entries=228 |
| H-A service request | `ready_to_request_real_measurements`; raw entries=228 |
| Hybrid measurement routing | `hybrid_measurement_plan_ready`; local=184; outsource-preferred=40; provenance=126; total=350 |
| Local capture pack | `local_capture_pack_ready`; tasks=350; local=184; outsource=40; provenance=126 |
| Source-file manifest | `source_file_manifest_ready`; allowed roots=12; source classes=12 |
| Source-file inventory | `source_file_inventory_empty`; files=0; refs=0; capture refs=0; filled source-value refs=0; missing refs=0; unreferenced=0 |
| Local capture preflight | `local_capture_preflight_awaiting_entries`; ready=false; filled=0; pending=350; errors=0; warnings=0 |
| Smoke capture tranche | `smoke_capture_tranche_ready`; tasks=172; local_or_record=152; outsource=20 |
| Smoke execution queue | `smoke_execution_queue_ready`; rows=172; H-A=114; ZRC=58; awaiting=172; source-ready=0 |
| Smoke entry sheet | `smoke_entry_sheet_ready`; rows=172; filled=0; ready-to-apply=0 |
| Smoke source drop plan | `smoke_source_drop_plan_ready`; planned files=172; dirs=10; existing files=0; missing files=172 |
| Smoke source values sheet | `smoke_source_values_sheet_ready`; rows=172; starter=19; filled=0; import-ready=0 |
| Smoke starter batch readiness | `smoke_starter_batch_awaiting_values`; rows=19; ready=0; blocked=19 |
| Smoke starter execution pack | `smoke_starter_execution_pack_ready`; rows=19; dirs=1; existing files=0 |
| Smoke starter raw-file templates | `smoke_starter_raw_file_template_pack_ready`; rows=19; templates=8 |
| Smoke raw CSV extraction | `smoke_raw_csv_value_extraction_no_raw_csv`; files=0; rows=0; errors=0 |
| Smoke unstructured source intake | `smoke_unstructured_source_intake_waiting_for_files`; rows=10; ready=0; missing=10; invalid=0 |
| Smoke unstructured review values | `smoke_unstructured_review_values_waiting_for_source_files`; rows=10; ready_sources=0; filled=0; import-ready=0; invalid_sources=0 |
| Smoke source value import | `smoke_source_value_import_no_importable_rows`; files=3; rows=182; imported=0; errors=0 |
| Smoke entry apply | `smoke_entry_apply_no_filled_rows`; applied=0; errors=0 |
| Smoke capture preflight | `local_capture_preflight_awaiting_entries`; ready=false; filled=0; pending=172; errors=0; warnings=0 |
| Smoke rehearsal | `smoke_rehearsal_waiting_for_preflight`; preflight=local_capture_preflight_awaiting_entries; ready=false; filled=0; pending=172; H-A_QC=-; ZRC_validation=- |
| H-A sample handoff | `ready_for_sample_handoff`; labels=36; custody rows=36; pending transfers=36 |
| H-A sample submission | `sample_submission_precheck_ready`; shipping=do_not_ship_until_vendor_confirms_quote_sample_acceptance_sds_and_custody |
| H-A split-scope plan | `split_scope_plan_ready`; pairs=7; preferred=5 |
| H-A delivery package | `ready_to_send`; missing files=0 |
| H-A vendor outreach | `ready_for_vendor_screening`; first-wave contacts=4 |
| H-A RFQ packet | `ready_to_send_rfq` |
| H-A RFQ outbox | `ready_to_send_outbox`; ready=4 / 4 |
| H-A quote tracker | `pending_outreach` |
| H-A RFQ send confirmation intake | `nhi_pedot_h_a_rfq_send_confirmation_intake_waiting_for_confirmation_files`; files=0; applied=0; needs-review=0; bundle-matched=0 |
| H-A RFQ send confirmation entry sheet | `h_a_rfq_send_confirmation_entry_sheet_waiting_for_confirmation_files`; rows=4; source-files=0; ready=0; blocked=0 |
| H-A RFQ send confirmation entry apply | `h_a_rfq_send_confirmation_entry_apply_no_apply_rows`; apply rows=0; applied=0; blocked=0 |
| H-A RFQ send log | `nhi_pedot_h_a_rfq_send_log_waiting_for_sent_entries`; rows=4; sent=0; valid=0; applied dates=0; errors=0 |
| H-A RFQ reply intake | `nhi_pedot_h_a_rfq_reply_intake_waiting_for_reply_files`; files=0; applied=0; needs-review=0; needs-verified-send=0 |
| H-A RFQ reply log | `nhi_pedot_h_a_rfq_reply_log_waiting_for_reply_files`; rows=4; received=0; valid=0; applied fields=0; errors=0 |
| H-A vendor contact plan | `contact_plan_ready`; ready first-wave=4; standby second-wave=4; total=8 |
| H-A vendor contact source audit | `h_a_vendor_contact_source_audit_ready`; rows=4; pass=4; fail=0; stale=0 |
| H-A RFQ EML drafts | `h_a_rfq_eml_drafts_ready`; rows=4; ready=4; missing-to=0; missing-bundle=0 |
| H-A RFQ EML integrity audit | `h_a_rfq_eml_integrity_ready`; rows=4; pass=4; fail=0; attachment-mismatch=0 |
| H-A RFQ send action pack | `h_a_rfq_send_action_pack_ready`; rows=4; ready=4; verified=0; needs-confirmation=0 |
| H-A RFQ dispatch manifest | `h_a_rfq_dispatch_manifest_ready`; rows=4; ready=4; blocked=0; bundle-matches=4 |
| H-A RFQ reply action pack | `h_a_rfq_reply_action_pack_waiting_for_send`; rows=4; waiting-send=4; awaiting-reply=0; needs-source=0; ready-apply=0 |
| H-A RFQ send cockpit | `h_a_rfq_send_cockpit_ready_for_manual_send`; rows=4; ready=4; confirmations=0; replies=0; missing-eml=0; missing-bundle=0; html=`reports/nhi_pedot_h_a_rfq_send_cockpit.html` |
| H-A RFQ dispatch archive | `h_a_rfq_dispatch_archive_ready`; files=22; missing=0; hash-mismatches=0; archive=`data/nhi_pedot_h_a_rfq_dispatch_archive/nhi_pedot_h_a_rfq_dispatch_archive.zip`; sha256=`b739036ff6d618bec4b57e1c028676338ef58599a11fb7a6822a6df9b725368b` |
| First-wave RFQ dispatch cockpit | `first_wave_rfq_dispatch_cockpit_ready_for_manual_send`; rows=8; ready=8; confirmations=0; replies=0; missing-messages=0; missing-bundles=0; html=`reports/limina_first_wave_rfq_dispatch_cockpit.html` |
| First-wave post-dispatch processing | `first_wave_post_dispatch_waiting_for_real_send_confirmations`; failed commands=0; confirmations=0; replies=0 |
| Second-wave candidate queue | `second_wave_candidate_queue_ready_while_first_wave_waits`; rows=6; ready-scope-lock=2; watch=2; hold=2 |
| Second-wave scope-lock pack | `second_wave_scope_lock_pack_ready`; ready candidates=2; tasks=8; source classes=5; claim evidence created=false |
| H-A quote selection | `pending_outreach`; sent=0; replies=0; source-backed replies=0; shortlisted=0 |
| H-A execution authorization log | `nhi_pedot_h_a_execution_authorization_waiting_for_selected_provider`; rows=0; valid=0; errors=0 |
| H-A execution release audit | `nhi_pedot_h_a_execution_release_blocked_no_source_backed_provider_selection`; ready=false; released=false; blockers=1; authorization blockers=0 |
| H-A vendor return intake | `awaiting_vendor_return_files`; raw value rows=0; bundle rows=96; bundle apply rows=0; export files=0 |
| Forward H-B/H-C package | `preregistered_waiting_for_h_a`; rows=28 |
| Forward H-B/H-C source values | `nhi_pedot_forward_source_values_sheet_ready`; rows=592; filled=0; import-ready=0 |
| Forward H-B/H-C source drop plan | `nhi_pedot_forward_source_drop_plan_ready`; planned files=592; dirs=28; existing files=0; missing files=592 |
| Forward H-B/H-C source file templates | `nhi_pedot_forward_source_file_template_pack_ready`; templates=6; target files=592 |
| Forward H-B/H-C raw CSV extraction | `nhi_pedot_forward_raw_csv_value_extraction_no_raw_csv`; files=0; rows=0; errors=0 |
| Forward H-B/H-C source import | `nhi_pedot_forward_source_value_import_no_importable_rows`; rows=592; imported=0; errors=0 |
| NHI-PEDOT coupon results | `no_data`; rows=0 |
| Long-duration source values | `nhi_pedot_long_source_values_sheet_ready`; rows=4836; filled=0; import-ready=0 |
| Long-duration source drop plan | `nhi_pedot_long_source_drop_plan_ready`; planned files=4836; dirs=156; existing files=0; missing files=4836 |
| Long-duration source file templates | `nhi_pedot_long_source_file_template_pack_ready`; templates=5; target files=4836 |
| Long-duration raw CSV extraction | `nhi_pedot_long_raw_csv_value_extraction_no_raw_csv`; files=0; rows=0; errors=0 |
| Long-duration source import | `nhi_pedot_long_source_value_import_no_importable_rows`; rows=4836; imported=0; errors=0 |
| NHI-PEDOT long results | `no_data`; rows=0 |
| ZRC-ND readiness | `not_suitable_yet_no_measured_data`; suitable=false |
| ZRC-ND Phase A sentinel | `no_sentinel_rows`; rows=0 |
| ZRC-ND next measurements | `needs_phase_a_sentinel`; recommended rows=8 |
| ZRC-ND Phase A source values | `zrc_nd_phase_a_source_values_sheet_ready`; rows=304; filled=0; import-ready=0 |
| ZRC-ND Phase A source drop plan | `zrc_nd_phase_a_source_drop_plan_ready`; planned files=304; dirs=8; existing files=0; missing files=304 |
| ZRC-ND Phase A source file templates | `zrc_nd_phase_a_source_file_template_pack_ready`; templates=8; target files=304 |
| ZRC-ND Phase A vendor bundle entry sheet | `zrc_phase_a_vendor_bundle_entry_sheet_ready`; bundles=64; ready=0; blocked=0 |
| ZRC-ND Phase A vendor bundle entry apply | `zrc_phase_a_vendor_bundle_entry_apply_no_apply_rows`; apply rows=0; bundles=0; source rows=0; errors=0 |
| ZRC-ND Phase A raw CSV extraction | `zrc_nd_phase_a_raw_csv_value_extraction_no_raw_csv`; files=0; rows=0; errors=0 |
| ZRC-ND Phase A source import | `zrc_nd_phase_a_source_value_import_no_importable_rows`; rows=304; imported=0; errors=0 |
| ZRC-ND Phase A service request | `ready_to_request_real_phase_a_measurements`; runs=8 |
| ZRC-ND Phase A sample handoff | `ready_for_phase_a_sample_handoff`; labels=16; custody rows=16; pending transfers=16 |
| ZRC-ND Phase A delivery package | `ready_to_send`; missing files=0 |
| ZRC-ND Phase A vendor outreach | `ready_for_vendor_screening`; first-wave contacts=4 |
| ZRC-ND Phase A RFQ packet | `ready_to_send_rfq` |
| ZRC-ND Phase A RFQ outbox | `ready_to_send_outbox`; ready=4 / 4 |
| ZRC-ND Phase A quote tracker | `pending_outreach` |
| ZRC-ND Phase A RFQ send confirmation intake | `zrc_nd_phase_a_rfq_send_confirmation_intake_waiting_for_confirmation_files`; files=0; applied=0; needs-review=0; bundle-matched=0 |
| ZRC-ND Phase A RFQ send confirmation entry sheet | `zrc_phase_a_rfq_send_confirmation_entry_sheet_waiting_for_confirmation_files`; rows=4; source-files=0; ready=0; blocked=0 |
| ZRC-ND Phase A RFQ send confirmation entry apply | `zrc_phase_a_rfq_send_confirmation_entry_apply_no_apply_rows`; apply rows=0; applied=0; blocked=0 |
| ZRC-ND Phase A RFQ send log | `zrc_nd_phase_a_rfq_send_log_waiting_for_sent_entries`; rows=4; sent=0; valid=0; applied dates=0; errors=0 |
| ZRC-ND Phase A RFQ reply intake | `zrc_nd_phase_a_rfq_reply_intake_waiting_for_reply_files`; files=0; applied=0; needs-review=0; needs-verified-send=0 |
| ZRC-ND Phase A RFQ reply log | `zrc_nd_phase_a_rfq_reply_log_waiting_for_reply_files`; rows=4; received=0; valid=0; applied fields=0; errors=0 |
| ZRC-ND Phase A vendor contact plan | `contact_plan_ready`; ready first-wave=4; standby second-wave=4; total=8 |
| ZRC-ND Phase A RFQ dispatch manifest | `zrc_phase_a_rfq_dispatch_manifest_ready`; rows=4; ready=4; blocked=0 |
| ZRC-ND Phase A RFQ dispatch archive | `zrc_phase_a_rfq_dispatch_archive_ready`; files=24; missing=0; hash-mismatches=0; archive=`data/zrc_nd_phase_a_rfq_dispatch_archive/zrc_nd_phase_a_rfq_dispatch_archive.zip`; sha256=`2a2ca661089a7d5ae0a91205968a383b98d7fbd90cea45c46fd4f6c8eab917d7` |
| ZRC-ND Phase A RFQ reply action pack | `zrc_phase_a_rfq_reply_action_pack_waiting_for_send`; rows=4; waiting-send=4; awaiting-reply=0; needs-source=0; ready-apply=0 |
| ZRC-ND Phase A RFQ send cockpit | `zrc_phase_a_rfq_send_cockpit_ready_for_manual_send`; rows=4; ready=4; confirmations=0; replies=0; missing-email=0; missing-bundle=0; html=`reports/zrc_nd_phase_a_rfq_send_cockpit.html` |
| ZRC-ND Phase A quote selection | `pending_outreach`; sent=0; replies=0; source-backed replies=0; shortlisted=0 |
| ZRC-ND Phase A execution authorization log | `zrc_nd_phase_a_execution_authorization_waiting_for_selected_provider`; rows=0; valid=0; errors=0 |
| ZRC-ND Phase A execution release audit | `zrc_nd_phase_a_execution_release_blocked_no_source_backed_provider_selection`; ready=false; released=false; blockers=1; authorization blockers=0 |
| ZRC-ND Phase A vendor return intake | `awaiting_vendor_return_files`; rows=0; export files=0 |
| ZRC-ND measurement merge | `awaiting_measurement_file`; inserted=0; updated=0; output rows=0 |
| ZRC-ND run completeness | `no_measured_rows`; measured known=0 / 132 |
| ZRC-ND validation results | `no_data`; rows=0 |

## Interpretation

- Replace fixture, pending, and record_actual/record_lot placeholders with real measured provenance before interpreting H-A.
- No suitability claim is allowed until real, non-placeholder, non-synthetic measured rows pass the required gates.

## Commands

| Command | Stage | Return | Seconds | Artifact |
| --- | --- | ---: | ---: | --- |
| `import_evidence` | `evidence` | 0 | 0.024 | `reports/evidence_register.md` |
| `validate_data_refs` | `evidence` | 0 | 0.024 | `reports/data_validation.md` |
| `rank_discovery_candidates` | `candidate_selection` | 0 | 0.030 | `reports/limina_discovery_ranking.md` |
| `render_alg_lam_protocol` | `candidate_handoff` | 0 | 0.024 | `reports/nhi_pedot_alg_lam_protocol.md` |
| `render_source_file_manifest` | `source_file_guard` | 0 | 0.026 | `reports/limina_source_file_manifest.md` |
| `render_h_a_source_values_sheet` | `h_a_intake` | 0 | 0.035 | `reports/nhi_pedot_h_a_source_values_sheet.md` |
| `render_h_a_source_drop_plan` | `h_a_intake` | 0 | 0.092 | `reports/nhi_pedot_h_a_source_drop_plan.md` |
| `render_h_a_source_unlock_pack` | `h_a_intake` | 0 | 0.047 | `reports/nhi_pedot_h_a_source_unlock_pack.md` |
| `render_h_a_bundle_entry_sheet` | `h_a_intake` | 0 | 0.030 | `reports/nhi_pedot_h_a_bundle_entry_sheet.md` |
| `render_h_a_vendor_bundle_entry_sheet` | `h_a_intake` | 0 | 0.036 | `reports/nhi_pedot_h_a_vendor_bundle_entry_sheet.md` |
| `apply_h_a_bundle_entry_sheet` | `h_a_intake` | 0 | 0.027 | `reports/nhi_pedot_h_a_bundle_entry_apply.md` |
| `apply_h_a_vendor_bundle_entry_return` | `h_a_intake` | 0 | 0.026 | `reports/nhi_pedot_h_a_vendor_bundle_entry_apply.md` |
| `render_h_a_source_file_template_pack` | `h_a_intake` | 0 | 0.029 | `reports/nhi_pedot_h_a_source_file_template_pack.md` |
| `extract_h_a_raw_csv_values` | `h_a_intake` | 0 | 0.029 | `reports/nhi_pedot_h_a_raw_csv_value_extraction.md` |
| `import_h_a_source_values` | `h_a_intake` | 0 | 0.028 | `reports/nhi_pedot_h_a_source_value_import.md` |
| `merge_h_a_raw_measurements` | `h_a_intake` | 0 | 0.028 | `reports/nhi_pedot_h_a_measurement_merge.md` |
| `render_h_a_bench_sheet` | `h_a_intake` | 0 | 0.026 | `reports/nhi_pedot_h_a_bench_sheet.md` |
| `qc_h_a_intake` | `h_a_intake` | 0 | 0.029 | `reports/nhi_pedot_h_a_intake_qc.md` |
| `render_h_a_minimum_checklist` | `h_a_intake` | 0 | 0.024 | `reports/nhi_pedot_h_a_minimum_measurement_checklist.md` |
| `render_h_a_service_request` | `h_a_intake` | 0 | 0.024 | `reports/nhi_pedot_h_a_service_request.md` |
| `render_h_a_chain_of_custody` | `h_a_intake` | 0 | 0.026 | `reports/nhi_pedot_h_a_chain_of_custody.md` |
| `render_h_a_sample_submission_pack` | `h_a_intake` | 0 | 0.025 | `reports/nhi_pedot_h_a_sample_submission_pack.md` |
| `render_h_a_split_scope_plan` | `h_a_intake` | 0 | 0.025 | `reports/nhi_pedot_h_a_split_scope_plan.md` |
| `render_h_a_delivery_package` | `h_a_intake` | 0 | 0.026 | `reports/nhi_pedot_h_a_delivery_package_manifest.md` |
| `render_h_a_vendor_outreach` | `h_a_intake` | 0 | 0.024 | `reports/nhi_pedot_h_a_vendor_outreach_brief.md` |
| `render_h_a_rfq_packet` | `h_a_intake` | 0 | 0.024 | `reports/nhi_pedot_h_a_rfq_packet.md` |
| `render_h_a_rfq_outbox` | `h_a_intake` | 0 | 0.043 | `reports/nhi_pedot_h_a_rfq_outbox.md` |
| `render_h_a_quote_tracker` | `h_a_intake` | 0 | 0.025 | `reports/nhi_pedot_h_a_quote_tracker.md` |
| `intake_h_a_rfq_send_confirmations` | `h_a_intake` | 0 | 0.043 | `reports/nhi_pedot_h_a_rfq_send_confirmation_intake.md` |
| `render_h_a_rfq_send_confirmation_entry_sheet` | `h_a_intake` | 0 | 0.028 | `reports/nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.md` |
| `apply_h_a_rfq_send_confirmation_entry_sheet` | `h_a_intake` | 0 | 0.029 | `reports/nhi_pedot_h_a_rfq_send_confirmation_entry_apply.md` |
| `apply_h_a_rfq_send_log` | `h_a_intake` | 0 | 0.034 | `reports/nhi_pedot_h_a_rfq_send_log.md` |
| `intake_h_a_rfq_replies` | `h_a_intake` | 0 | 0.042 | `reports/nhi_pedot_h_a_rfq_reply_intake.md` |
| `apply_h_a_rfq_reply_log` | `h_a_intake` | 0 | 0.034 | `reports/nhi_pedot_h_a_rfq_reply_log.md` |
| `render_h_a_vendor_contact_plan` | `h_a_intake` | 0 | 0.025 | `reports/nhi_pedot_h_a_vendor_contact_plan.md` |
| `audit_h_a_vendor_contact_sources` | `h_a_intake` | 0 | 0.029 | `reports/nhi_pedot_h_a_vendor_contact_source_audit.md` |
| `render_h_a_rfq_eml_drafts` | `h_a_intake` | 0 | 0.046 | `reports/nhi_pedot_h_a_rfq_eml_drafts.md` |
| `audit_h_a_rfq_eml_integrity` | `h_a_intake` | 0 | 0.042 | `reports/nhi_pedot_h_a_rfq_eml_integrity_audit.md` |
| `render_h_a_rfq_send_action_pack` | `h_a_intake` | 0 | 0.026 | `reports/nhi_pedot_h_a_rfq_send_action_pack.md` |
| `render_h_a_rfq_dispatch_manifest` | `h_a_intake` | 0 | 0.028 | `reports/nhi_pedot_h_a_rfq_dispatch_manifest.md` |
| `render_h_a_rfq_reply_action_pack` | `h_a_intake` | 0 | 0.026 | `reports/nhi_pedot_h_a_rfq_reply_action_pack.md` |
| `render_h_a_rfq_send_cockpit` | `h_a_intake` | 0 | 0.029 | `reports/nhi_pedot_h_a_rfq_send_cockpit.md` |
| `render_h_a_rfq_dispatch_archive` | `h_a_intake` | 0 | 0.040 | `reports/nhi_pedot_h_a_rfq_dispatch_archive_manifest.md` |
| `evaluate_h_a_quote_replies` | `h_a_intake` | 0 | 0.025 | `reports/nhi_pedot_h_a_quote_selection.md` |
| `apply_h_a_execution_authorization_log` | `h_a_intake` | 0 | 0.034 | `reports/nhi_pedot_h_a_execution_authorization_log.md` |
| `audit_h_a_execution_release` | `h_a_intake` | 0 | 0.033 | `reports/nhi_pedot_h_a_execution_release_audit.md` |
| `render_h_a_vendor_return_intake` | `h_a_intake` | 0 | 0.028 | `reports/nhi_pedot_h_a_vendor_return_intake.md` |
| `interpret_h_a_sentinel` | `h_a_gate` | 0 | 0.026 | `reports/nhi_pedot_h_a_sentinel_interpretation.md` |
| `refresh_next_measurements` | `h_a_next_actions` | 0 | 0.025 | `reports/nhi_pedot_next_measurements.md` |
| `refresh_h_a_packet` | `h_a_next_actions` | 0 | 0.025 | `reports/nhi_pedot_h_a_sentinel_packet.md` |
| `design_variant_ladder` | `adaptive_design` | 0 | 0.024 | `reports/nhi_pedot_variant_ladder.md` |
| `generate_forward_gate_package` | `forward_evidence` | 0 | 0.026 | `reports/nhi_pedot_forward_gate_package.md` |
| `render_nhi_forward_source_values_sheet` | `forward_evidence` | 0 | 0.046 | `reports/nhi_pedot_forward_source_values_sheet.md` |
| `render_nhi_forward_source_drop_plan` | `forward_evidence` | 0 | 0.142 | `reports/nhi_pedot_forward_source_drop_plan.md` |
| `render_nhi_forward_source_file_template_pack` | `forward_evidence` | 0 | 0.033 | `reports/nhi_pedot_forward_source_file_template_pack.md` |
| `extract_nhi_forward_raw_csv_values` | `forward_evidence` | 0 | 0.032 | `reports/nhi_pedot_forward_raw_csv_value_extraction.md` |
| `import_nhi_forward_source_values` | `forward_evidence` | 0 | 0.031 | `reports/nhi_pedot_forward_source_values_import.md` |
| `evaluate_nhi_coupon_runs` | `forward_evidence` | 0 | 0.025 | `reports/nhi_pedot_results.md` |
| `render_nhi_long_source_values_sheet` | `long_duration_evidence` | 0 | 0.207 | `reports/nhi_pedot_long_source_values_sheet.md` |
| `render_nhi_long_source_drop_plan` | `long_duration_evidence` | 0 | 1.214 | `reports/nhi_pedot_long_source_drop_plan.md` |
| `render_nhi_long_source_file_template_pack` | `long_duration_evidence` | 0 | 0.090 | `reports/nhi_pedot_long_source_file_template_pack.md` |
| `extract_nhi_long_raw_csv_values` | `long_duration_evidence` | 0 | 0.078 | `reports/nhi_pedot_long_raw_csv_value_extraction.md` |
| `import_nhi_long_source_values` | `long_duration_evidence` | 0 | 0.052 | `reports/nhi_pedot_long_source_values_import.md` |
| `evaluate_nhi_long_runs` | `long_duration_evidence` | 0 | 0.028 | `reports/nhi_pedot_long_results.md` |
| `interpret_zrc_phase_a_sentinel` | `zrc_phase_a` | 0 | 0.025 | `reports/zrc_nd_sentinel_interpretation.md` |
| `suggest_zrc_next_measurements` | `zrc_phase_a` | 0 | 0.027 | `reports/zrc_nd_next_measurements.md` |
| `generate_zrc_phase_a_packet` | `zrc_phase_a` | 0 | 0.025 | `reports/zrc_nd_phase_a_sentinel_packet.md` |
| `render_zrc_phase_a_source_values_sheet` | `zrc_phase_a` | 0 | 0.036 | `reports/zrc_nd_phase_a_source_values_sheet.md` |
| `render_zrc_phase_a_source_drop_plan` | `zrc_phase_a` | 0 | 0.070 | `reports/zrc_nd_phase_a_source_drop_plan.md` |
| `render_zrc_phase_a_source_file_template_pack` | `zrc_phase_a` | 0 | 0.030 | `reports/zrc_nd_phase_a_source_file_template_pack.md` |
| `render_zrc_phase_a_vendor_bundle_entry_sheet` | `zrc_phase_a` | 0 | 0.032 | `reports/zrc_nd_phase_a_vendor_bundle_entry_sheet.md` |
| `apply_zrc_phase_a_vendor_bundle_entry_sheet` | `zrc_phase_a` | 0 | 0.028 | `reports/zrc_nd_phase_a_vendor_bundle_entry_apply.md` |
| `extract_zrc_phase_a_raw_csv_values` | `zrc_phase_a` | 0 | 0.029 | `reports/zrc_nd_phase_a_raw_csv_value_extraction.md` |
| `import_zrc_phase_a_source_values` | `zrc_phase_a` | 0 | 0.029 | `reports/zrc_nd_phase_a_source_values_import.md` |
| `render_zrc_phase_a_service_request` | `zrc_phase_a` | 0 | 0.025 | `reports/zrc_nd_phase_a_service_request.md` |
| `render_hybrid_measurement_plan` | `measurement_routing` | 0 | 0.026 | `reports/limina_hybrid_measurement_plan.md` |
| `render_local_capture_pack` | `measurement_routing` | 0 | 0.035 | `reports/limina_local_capture_pack.md` |
| `audit_source_file_inventory` | `measurement_routing` | 0 | 0.064 | `reports/limina_source_file_inventory.md` |
| `regress_source_value_inventory` | `measurement_routing` | 0 | 0.035 | `reports/limina_source_value_inventory_regression.md` |
| `regress_h_a_raw_csv_extraction` | `measurement_routing` | 0 | 0.030 | `reports/nhi_pedot_h_a_raw_csv_extraction_regression.md` |
| `regress_h_a_bundle_entry` | `measurement_routing` | 0 | 0.028 | `reports/nhi_pedot_h_a_bundle_entry_regression.md` |
| `regress_h_a_vendor_bundle_entry_return` | `measurement_routing` | 0 | 0.028 | `reports/nhi_pedot_h_a_vendor_bundle_entry_return_regression.md` |
| `regress_wide_raw_csv_extraction` | `measurement_routing` | 0 | 0.028 | `reports/limina_wide_raw_csv_extraction_regression.md` |
| `regress_rfq_send_log` | `measurement_routing` | 0 | 0.042 | `reports/limina_rfq_send_log_regression.md` |
| `regress_rfq_send_confirmation_intake` | `measurement_routing` | 0 | 0.053 | `reports/limina_rfq_send_confirmation_intake_regression.md` |
| `regress_rfq_reply_intake` | `measurement_routing` | 0 | 0.053 | `reports/limina_rfq_reply_intake_regression.md` |
| `regress_rfq_reply_log` | `measurement_routing` | 0 | 0.037 | `reports/limina_rfq_reply_log_regression.md` |
| `regress_quote_selection_source_guard` | `measurement_routing` | 0 | 0.022 | `reports/limina_quote_selection_source_guard_regression.md` |
| `regress_execution_release` | `measurement_routing` | 0 | 0.029 | `reports/limina_execution_release_regression.md` |
| `regress_execution_authorization_log` | `measurement_routing` | 0 | 0.037 | `reports/limina_execution_authorization_log_regression.md` |
| `preflight_local_capture` | `measurement_routing` | 0 | 0.040 | `reports/limina_local_capture_preflight.md` |
| `render_smoke_capture_tranche` | `measurement_routing` | 0 | 0.028 | `reports/limina_smoke_capture_tranche.md` |
| `render_smoke_execution_queue` | `measurement_routing` | 0 | 0.031 | `reports/limina_smoke_execution_queue.md` |
| `render_smoke_entry_sheet` | `measurement_routing` | 0 | 0.028 | `reports/limina_smoke_entry_sheet.md` |
| `render_smoke_source_drop_plan` | `measurement_routing` | 0 | 0.041 | `reports/limina_smoke_source_drop_plan.md` |
| `render_smoke_source_values_sheet` | `measurement_routing` | 0 | 0.030 | `reports/limina_smoke_source_values_sheet.md` |
| `audit_smoke_starter_batch_readiness` | `measurement_routing` | 0 | 0.027 | `reports/limina_smoke_starter_batch_readiness.md` |
| `render_smoke_starter_execution_pack` | `measurement_routing` | 0 | 0.027 | `reports/limina_smoke_starter_execution_pack.md` |
| `render_smoke_starter_raw_file_template_pack` | `measurement_routing` | 0 | 0.026 | `reports/limina_smoke_starter_raw_file_template_pack.md` |
| `extract_smoke_raw_csv_values` | `measurement_routing` | 0 | 0.026 | `reports/limina_smoke_raw_csv_value_extraction.md` |
| `intake_smoke_unstructured_sources` | `measurement_routing` | 0 | 0.044 | `reports/limina_smoke_unstructured_source_intake.md` |
| `render_smoke_unstructured_review_values` | `measurement_routing` | 0 | 0.026 | `reports/limina_smoke_unstructured_review_values.md` |
| `import_smoke_source_values` | `measurement_routing` | 0 | 0.029 | `reports/limina_smoke_source_value_import.md` |
| `apply_smoke_entry_sheet` | `measurement_routing` | 0 | 0.027 | `reports/limina_smoke_entry_apply.md` |
| `refresh_smoke_execution_queue_after_entry_apply` | `measurement_routing` | 0 | 0.030 | `reports/limina_smoke_execution_queue.md` |
| `preflight_smoke_capture` | `measurement_routing` | 0 | 0.034 | `reports/limina_smoke_capture_preflight.md` |
| `run_smoke_rehearsal` | `measurement_routing` | 0 | 0.027 | `reports/limina_smoke_rehearsal.md` |
| `render_zrc_phase_a_chain_of_custody` | `zrc_phase_a` | 0 | 0.026 | `reports/zrc_nd_phase_a_chain_of_custody.md` |
| `render_zrc_phase_a_delivery_package` | `zrc_phase_a` | 0 | 0.026 | `reports/zrc_nd_phase_a_delivery_package_manifest.md` |
| `render_zrc_phase_a_vendor_outreach` | `zrc_phase_a_sourcing` | 0 | 0.024 | `reports/zrc_nd_phase_a_vendor_outreach_brief.md` |
| `render_zrc_phase_a_rfq_packet` | `zrc_phase_a_sourcing` | 0 | 0.024 | `reports/zrc_nd_phase_a_rfq_packet.md` |
| `render_zrc_phase_a_rfq_outbox` | `zrc_phase_a_sourcing` | 0 | 0.037 | `reports/zrc_nd_phase_a_rfq_outbox.md` |
| `render_zrc_phase_a_quote_tracker` | `zrc_phase_a_sourcing` | 0 | 0.024 | `reports/zrc_nd_phase_a_quote_tracker.md` |
| `render_zrc_phase_a_vendor_contact_plan` | `zrc_phase_a_sourcing` | 0 | 0.024 | `reports/zrc_nd_phase_a_vendor_contact_plan.md` |
| `render_zrc_phase_a_rfq_dispatch_manifest` | `zrc_phase_a_sourcing` | 0 | 0.028 | `reports/zrc_nd_phase_a_rfq_dispatch_manifest.md` |
| `intake_zrc_phase_a_rfq_send_confirmations` | `zrc_phase_a_sourcing` | 0 | 0.042 | `reports/zrc_nd_phase_a_rfq_send_confirmation_intake.md` |
| `render_zrc_phase_a_rfq_send_confirmation_entry_sheet` | `zrc_phase_a_sourcing` | 0 | 0.028 | `reports/zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.md` |
| `apply_zrc_phase_a_rfq_send_confirmation_entry_sheet` | `zrc_phase_a_sourcing` | 0 | 0.026 | `reports/zrc_nd_phase_a_rfq_send_confirmation_entry_apply.md` |
| `apply_zrc_phase_a_rfq_send_log` | `zrc_phase_a_sourcing` | 0 | 0.033 | `reports/zrc_nd_phase_a_rfq_send_log.md` |
| `intake_zrc_phase_a_rfq_replies` | `zrc_phase_a_sourcing` | 0 | 0.043 | `reports/zrc_nd_phase_a_rfq_reply_intake.md` |
| `apply_zrc_phase_a_rfq_reply_log` | `zrc_phase_a_sourcing` | 0 | 0.034 | `reports/zrc_nd_phase_a_rfq_reply_log.md` |
| `render_zrc_phase_a_rfq_dispatch_archive` | `zrc_phase_a_sourcing` | 0 | 0.034 | `reports/zrc_nd_phase_a_rfq_dispatch_archive_manifest.md` |
| `render_zrc_phase_a_rfq_reply_action_pack` | `zrc_phase_a_sourcing` | 0 | 0.026 | `reports/zrc_nd_phase_a_rfq_reply_action_pack.md` |
| `render_zrc_phase_a_rfq_send_cockpit` | `zrc_phase_a_sourcing` | 0 | 0.030 | `reports/zrc_nd_phase_a_rfq_send_cockpit.md` |
| `render_first_wave_rfq_dispatch_cockpit` | `sourcing` | 0 | 0.029 | `reports/limina_first_wave_rfq_dispatch_cockpit.md` |
| `process_first_wave_post_dispatch` | `sourcing` | 0 | 0.712 | `reports/limina_first_wave_post_dispatch_processing.md` |
| `evaluate_zrc_phase_a_quote_replies` | `zrc_phase_a_sourcing` | 0 | 0.025 | `reports/zrc_nd_phase_a_quote_selection.md` |
| `apply_zrc_phase_a_execution_authorization_log` | `zrc_phase_a_sourcing` | 0 | 0.033 | `reports/zrc_nd_phase_a_execution_authorization_log.md` |
| `audit_zrc_phase_a_execution_release` | `zrc_phase_a_sourcing` | 0 | 0.031 | `reports/zrc_nd_phase_a_execution_release_audit.md` |
| `render_zrc_phase_a_vendor_return_intake` | `zrc_phase_a_intake` | 0 | 0.027 | `reports/zrc_nd_phase_a_vendor_return_intake.md` |
| `merge_zrc_phase_a_measurements` | `zrc_phase_a_intake` | 0 | 0.023 | `reports/zrc_nd_measurement_merge.md` |
| `check_zrc_run_completeness` | `zrc_phase_a_intake` | 0 | 0.024 | `reports/zrc_nd_run_completeness.md` |
| `evaluate_zrc_validation_runs` | `zrc_phase_a_gate` | 0 | 0.029 | `reports/zrc_nd_validation_results.md` |
| `refresh_zrc_phase_a_sentinel_after_merge` | `zrc_phase_a_gate` | 0 | 0.024 | `reports/zrc_nd_sentinel_interpretation.md` |
| `refresh_zrc_next_measurements_after_merge` | `zrc_phase_a_next_actions` | 0 | 0.027 | `reports/zrc_nd_next_measurements.md` |
| `audit_zrc_readiness` | `zrc_claim_guard` | 0 | 0.024 | `reports/zrc_nd_readiness_audit.md` |
| `select_portfolio_branch` | `portfolio` | 0 | 0.024 | `reports/limina_technology_portfolio.md` |
| `render_second_wave_candidate_queue` | `portfolio` | 0 | 0.026 | `reports/limina_second_wave_candidate_queue.md` |
| `render_second_wave_scope_lock_pack` | `portfolio` | 0 | 0.024 | `reports/limina_second_wave_scope_lock_pack.md` |
| `audit_claim_readiness` | `claim_guard` | 0 | 0.027 | `reports/limina_suitability_claim_audit.md` |
| `audit_portfolio_bypass_paths` | `claim_guard` | 0 | 0.024 | `reports/limina_portfolio_bypass_audit.md` |
| `regress_portfolio_claim_boundary` | `claim_guard` | 0 | 0.053 | `reports/limina_portfolio_claim_boundary_regression.md` |
| `regress_source_file_claim_guard` | `claim_guard` | 0 | 0.027 | `reports/limina_source_file_claim_guard_regression.md` |
| `summarize_cycle_state` | `cycle_state` | 0 | 0.056 | `reports/limina_discovery_cycle_state.md` |

## Command Output Tail

### import_evidence

```text
Imported 50 evidence records
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/evidence_records.jsonl
Skipped DuckDB export because duckdb is not installed in this Python environment
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/evidence_register.md
```

### validate_data_refs

```text
Validation passed for 50 evidence ids
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/data_validation.md
```

### rank_discovery_candidates

```text
Top discovery prospect: limina_alg_lam_pedot_lowdose_v0_2
Priority: promote_now
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_discovery_ranking.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_discovery_ranking.md
```

### render_alg_lam_protocol

```text
Rendered protocol: nhi_pedot_alg_lam_protocol_v0_2
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_alg_lam_protocol.md
```

### render_source_file_manifest

```text
Source-file manifest: source_file_manifest_ready
Allowed roots: 12
Expected source classes: 12
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_source_file_manifest.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_source_file_manifest.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_source_file_manifest.md
```

### render_h_a_source_values_sheet

```text
H-A source values sheet: h_a_source_values_sheet_ready
Rows: 228
Import-ready rows: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_source_values.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_source_values_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_source_values_sheet.md
```

### render_h_a_source_drop_plan

```text
Planned source files: 228
Created directories: 0
Existing source files: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_source_drop_plan.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_source_drop_plan.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_source_drop_plan.md
```

### render_h_a_source_unlock_pack

```text
H-A source unlock bundles: 96 for 228 source-value rows
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_source_unlock_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_source_unlock_bundle_manifest.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_source_unlock_pack.md
```

### render_h_a_bundle_entry_sheet

```text
H-A bundle entry sheet: h_a_bundle_entry_sheet_ready
Bundles: 96
Ready to apply: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_bundle_entry_sheet.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_bundle_entry_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_bundle_entry_sheet.md
```

### render_h_a_vendor_bundle_entry_sheet

```text
H-A vendor bundle entry sheet: h_a_vendor_bundle_entry_sheet_ready
Bundles: 96
Ready to apply: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_vendor_return_inbox/completed_bundle_entry_sheet.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_vendor_bundle_entry_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_vendor_bundle_entry_sheet.md
```

### apply_h_a_bundle_entry_sheet

```text
H-A bundle entry apply: h_a_bundle_entry_apply_no_apply_rows
Applied bundles: 0
Applied source-value rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_bundle_entry_apply.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_bundle_entry_apply.md
```

### apply_h_a_vendor_bundle_entry_return

```text
H-A vendor bundle entry return apply: h_a_vendor_bundle_entry_return_no_apply_rows
Applied bundles: 0
Applied source-value rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_vendor_bundle_entry_apply.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_vendor_bundle_entry_apply.md
```

### render_h_a_source_file_template_pack

```text
Source file template pack: nhi_pedot_h_a_source_file_template_pack_ready
Source-class templates: 8
Target source files: 228
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_source_file_template_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_source_file_template_manifest.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_source_file_template_pack.md
```

### extract_h_a_raw_csv_values

```text
Raw CSV/TSV files found: 0
Extracted rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_raw_csv_extracted_values.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_raw_csv_value_extraction.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_raw_csv_value_extraction.md
```

### import_h_a_source_values

```text
H-A source value import: h_a_source_value_import_no_importable_rows
Source value files: 2
Imported rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_source_value_import.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_source_value_import.md
```

### merge_h_a_raw_measurements

```text
Merged H-A raw measurements: applied=0 unresolved=0 unknown_run_ids=0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_raw_measurements_template.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_runs_active.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_measurement_merge.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_measurement_merge.md
```

### render_h_a_bench_sheet

```text
Rendered H-A bench sheet: tasks=12 blank_raw_entries=228
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_bench_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_bench_sheet.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_bench_sheet.md
```

### qc_h_a_intake

```text
H-A intake QC: h_a_intake_not_ready
Errors: 183
Warnings: 24
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_intake_qc.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_intake_qc.md
```

### render_h_a_minimum_checklist

```text
Rendered H-A minimum measurement checklist: runs=12
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_minimum_measurement_checklist.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_minimum_measurement_checklist.md
```

### render_h_a_service_request

```text
Rendered H-A service request: runs=12 raw_entries=228
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_service_request.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_service_request.md
```

### render_h_a_chain_of_custody

```text
H-A chain of custody: ready_for_sample_handoff
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_sample_labels.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_chain_of_custody.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_chain_of_custody.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_chain_of_custody.md
```

### render_h_a_sample_submission_pack

```text
H-A sample submission pack: sample_submission_precheck_ready
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_material_disclosure.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_sample_submission_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_sample_submission_pack.md
```

### render_h_a_split_scope_plan

```text
H-A split-scope plan: split_scope_plan_ready
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_split_scope_plan.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_split_scope_plan.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_split_scope_plan.md
```

### render_h_a_delivery_package

```text
H-A delivery package: ready_to_send
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_delivery_package_manifest.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_delivery_package_manifest.md
```

### render_h_a_vendor_outreach

```text
H-A vendor outreach: ready_for_vendor_screening
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_vendor_outreach.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_vendor_outreach_brief.md
```

### render_h_a_rfq_packet

```text
H-A RFQ packet: ready_to_send_rfq
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_packet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_packet.md
```

### render_h_a_rfq_outbox

```text
H-A RFQ outbox: ready_to_send_outbox
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_outbox_manifest.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_outbox.md
```

### render_h_a_quote_tracker

```text
H-A quote tracker: pending_outreach
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_quote_tracker.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_quote_tracker.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_quote_tracker.md
```

### intake_h_a_rfq_send_confirmations

```text
Files scanned: 0
Applied rows: 0
Needs review: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_send_confirmation_intake.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_send_confirmation_intake.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_send_confirmation_intake.md
```

### render_h_a_rfq_send_confirmation_entry_sheet

```text
H-A RFQ send confirmation entry sheet: h_a_rfq_send_confirmation_entry_sheet_waiting_for_confirmation_files
Ready to apply: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.md
```

### apply_h_a_rfq_send_confirmation_entry_sheet

```text
H-A RFQ send confirmation entry apply: h_a_rfq_send_confirmation_entry_apply_no_apply_rows
Applied: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_send_confirmation_entry_apply.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_send_confirmation_entry_apply.md
```

### apply_h_a_rfq_send_log

```text
Sent rows: 0
Applied tracker contact dates: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_send_log.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_send_log.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_send_log.md
```

### intake_h_a_rfq_replies

```text
Files scanned: 0
Applied rows: 0
Needs manual review: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_reply_intake.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_reply_intake.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_reply_intake.md
```

### apply_h_a_rfq_reply_log

```text
Received rows: 0
Applied tracker field updates: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_reply_log.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_reply_log.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_reply_log.md
```

### render_h_a_vendor_contact_plan

```text
H-A vendor contact plan: contact_plan_ready
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_vendor_contact_plan.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_vendor_contact_plan.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_vendor_contact_plan.md
```

### audit_h_a_vendor_contact_sources

```text
H-A vendor contact source audit: h_a_vendor_contact_source_audit_ready
Pass: 4 / 4
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_vendor_contact_source_audit.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_vendor_contact_source_audit.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_vendor_contact_source_audit.md
```

### render_h_a_rfq_eml_drafts

```text
H-A RFQ EML drafts: h_a_rfq_eml_drafts_ready
Ready to open: 4
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_eml_drafts.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_eml_drafts.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_eml_drafts.md
```

### audit_h_a_rfq_eml_integrity

```text
H-A RFQ EML integrity audit: h_a_rfq_eml_integrity_ready
Pass: 4 / 4
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_eml_integrity_audit.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_eml_integrity_audit.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_eml_integrity_audit.md
```

### render_h_a_rfq_send_action_pack

```text
H-A RFQ send action pack: h_a_rfq_send_action_pack_ready
Ready to send: 4
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_send_action_queue.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_send_action_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_send_action_pack.md
```

### render_h_a_rfq_dispatch_manifest

```text
H-A RFQ dispatch manifest: h_a_rfq_dispatch_manifest_ready
Ready for manual dispatch: 4 / 4
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_dispatch_manifest.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_dispatch_manifest.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_dispatch_manifest.md
```

### render_h_a_rfq_reply_action_pack

```text
H-A RFQ reply action pack: h_a_rfq_reply_action_pack_waiting_for_send
Action rows: 4
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_reply_action_queue.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_reply_action_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_reply_action_pack.md
```

### render_h_a_rfq_send_cockpit

```text
H-A RFQ send cockpit: h_a_rfq_send_cockpit_ready_for_manual_send
Ready to use: 4 / 4
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_send_cockpit.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_send_cockpit.md
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_send_cockpit.html
```

### render_h_a_rfq_dispatch_archive

```text
Included files: 22
Archive SHA-256: b739036ff6d618bec4b57e1c028676338ef58599a11fb7a6822a6df9b725368b
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_dispatch_archive/nhi_pedot_h_a_rfq_dispatch_archive.zip
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_dispatch_archive_manifest.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_rfq_dispatch_archive_manifest.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_rfq_dispatch_archive_manifest.md
```

### evaluate_h_a_quote_replies

```text
H-A quote selection: pending_outreach
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_quote_selection.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_quote_selection.md
```

### apply_h_a_execution_authorization_log

```text
Rows: 0
Valid authorizations: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_execution_authorization_log.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_execution_authorization_log.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_execution_authorization_log.md
```

### audit_h_a_execution_release

```text
NHI-PEDOT H-A execution release audit: nhi_pedot_h_a_execution_release_blocked_no_source_backed_provider_selection
Ready for authorization: false
Released for execution: false
Blockers: 1
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_execution_release_audit.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_execution_release_audit.md
```

### render_h_a_vendor_return_intake

```text
H-A vendor return intake: awaiting_vendor_return_files
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_vendor_return_checklist.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_vendor_return_intake.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_vendor_return_intake.md
```

### interpret_h_a_sentinel

```text
NHI-PEDOT H-A sentinel: h_a_invalid_provenance
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_sentinel_interpretation.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_sentinel_interpretation.md
```

### refresh_next_measurements

```text
Recommendation: needs_h_a_sentinel
Recommended rows: 12
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_next_measurements.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_next_measurements.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_next_measurements.md
```

### refresh_h_a_packet

```text
Generated 12 NHI-PEDOT H-A sentinel template rows
Generated 36 sample manifest rows
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_sentinel_template.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_sentinel_sample_manifest.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_sentinel_packet.md
```

### design_variant_ladder

```text
Designed 7 NHI-PEDOT variant ladder rows
Top variant: alg_lam_pedot_0p6pct_lead
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_variant_ladder.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_variant_ladder.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_variant_ladder.md
```

### generate_forward_gate_package

```text
NHI-PEDOT forward gate package: preregistered_waiting_for_h_a
Rows: 28
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_forward_gate_package.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_forward_gate_rows.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_forward_gate_package.md
```

### render_nhi_forward_source_values_sheet

```text
NHI-PEDOT H-B/H-C source values sheet: nhi_pedot_forward_source_values_sheet_ready
Rows: 592
Import-ready rows: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_forward_source_values.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_forward_source_values_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_forward_source_values_sheet.md
```

### render_nhi_forward_source_drop_plan

```text
Planned source files: 592
Created directories: 0
Existing source files: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_forward_source_drop_plan.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_forward_source_drop_plan.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_forward_source_drop_plan.md
```

### render_nhi_forward_source_file_template_pack

```text
Source file template pack: nhi_pedot_forward_source_file_template_pack_ready
Source-class templates: 6
Target source files: 592
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_forward_source_file_template_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_forward_source_file_template_manifest.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_forward_source_file_template_pack.md
```

### extract_nhi_forward_raw_csv_values

```text
Raw CSV/TSV files found: 0
Extracted rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_forward_raw_csv_extracted_values.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_forward_raw_csv_value_extraction.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_forward_raw_csv_value_extraction.md
```

### import_nhi_forward_source_values

```text
NHI-PEDOT H-B/H-C source value import: nhi_pedot_forward_source_value_import_no_importable_rows
Source value files: 2
Imported rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_forward_source_values_import.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_forward_source_values_import.md
```

### evaluate_nhi_coupon_runs

```text
NHI-PEDOT: no_data
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_results.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_results.md
```

### render_nhi_long_source_values_sheet

```text
NHI-PEDOT long-duration source values sheet: nhi_pedot_long_source_values_sheet_ready
Rows: 4836
Import-ready rows: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_long_source_values.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_long_source_values_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_long_source_values_sheet.md
```

### render_nhi_long_source_drop_plan

```text
Planned source files: 4836
Created directories: 0
Existing source files: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_long_source_drop_plan.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_long_source_drop_plan.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_long_source_drop_plan.md
```

### render_nhi_long_source_file_template_pack

```text
Source file template pack: nhi_pedot_long_source_file_template_pack_ready
Source-class templates: 5
Target source files: 4836
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_long_source_file_template_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_long_source_file_template_manifest.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_long_source_file_template_pack.md
```

### extract_nhi_long_raw_csv_values

```text
Raw CSV/TSV files found: 0
Extracted rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_long_raw_csv_extracted_values.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_long_raw_csv_value_extraction.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_long_raw_csv_value_extraction.md
```

### import_nhi_long_source_values

```text
NHI-PEDOT long-duration source value import: nhi_pedot_long_source_value_import_no_importable_rows
Source value files: 2
Imported rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_long_source_values_import.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_long_source_values_import.md
```

### evaluate_nhi_long_runs

```text
NHI-PEDOT long: no_data
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_long_results.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_long_results.md
```

### interpret_zrc_phase_a_sentinel

```text
Sentinel: no_sentinel_rows
Next action: Generate and fill the Phase A sentinel packet.
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_sentinel_interpretation.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_sentinel_interpretation.md
```

### suggest_zrc_next_measurements

```text
Recommendation: needs_phase_a_sentinel
Recommended rows: 8
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_next_measurements.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_next_measurements.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_next_measurements.md
```

### generate_zrc_phase_a_packet

```text
Generated 8 Phase A sentinel template rows
Generated 16 sample manifest rows
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_sentinel_template.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_sentinel_sample_manifest.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_sentinel_packet.md
```

### render_zrc_phase_a_source_values_sheet

```text
ZRC-ND Phase A source values sheet: zrc_nd_phase_a_source_values_sheet_ready
Rows: 304
Import-ready rows: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_source_values.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_source_values_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_source_values_sheet.md
```

### render_zrc_phase_a_source_drop_plan

```text
Planned source files: 304
Created directories: 0
Existing source files: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_source_drop_plan.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_source_drop_plan.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_source_drop_plan.md
```

### render_zrc_phase_a_source_file_template_pack

```text
Source file template pack: zrc_nd_phase_a_source_file_template_pack_ready
Source-class templates: 8
Target source files: 304
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_source_file_template_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_source_file_template_manifest.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_source_file_template_pack.md
```

### render_zrc_phase_a_vendor_bundle_entry_sheet

```text
ZRC-ND Phase A vendor bundle entry sheet: zrc_phase_a_vendor_bundle_entry_sheet_ready
Bundles: 64
Ready to apply: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_vendor_return_inbox/completed_bundle_entry_sheet.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_vendor_bundle_entry_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_vendor_bundle_entry_sheet.md
```

### apply_zrc_phase_a_vendor_bundle_entry_sheet

```text
ZRC-ND Phase A vendor bundle entry apply: zrc_phase_a_vendor_bundle_entry_apply_no_apply_rows
Applied bundles: 0
Applied source-value rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_vendor_bundle_entry_apply.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_vendor_bundle_entry_apply.md
```

### extract_zrc_phase_a_raw_csv_values

```text
Raw CSV/TSV files found: 0
Extracted rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_raw_csv_extracted_values.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_raw_csv_value_extraction.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_raw_csv_value_extraction.md
```

### import_zrc_phase_a_source_values

```text
ZRC-ND Phase A source value import: zrc_nd_phase_a_source_value_import_no_importable_rows
Source value files: 2
Imported rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_source_values_import.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_source_values_import.md
```

### render_zrc_phase_a_service_request

```text
ZRC-ND Phase A service request: ready_to_request_real_phase_a_measurements
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_service_request.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_service_request.md
```

### render_hybrid_measurement_plan

```text
Hybrid measurement plan: hybrid_measurement_plan_ready
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_hybrid_measurement_plan.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_hybrid_measurement_plan.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_hybrid_measurement_plan.md
```

### render_local_capture_pack

```text
Local capture pack: local_capture_pack_ready
Tasks: 350
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_local_capture_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_local_capture_pack.md
```

### audit_source_file_inventory

```text
Source-file inventory: source_file_inventory_empty
Files: 0
Missing references: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_source_file_inventory.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_source_file_inventory.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_source_file_inventory.md
```

### regress_source_value_inventory

```text
LIMINA source-value inventory regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_source_value_inventory_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_source_value_inventory_regression.md
```

### regress_h_a_raw_csv_extraction

```text
NHI-PEDOT H-A raw CSV extraction regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_raw_csv_extraction_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_raw_csv_extraction_regression.md
```

### regress_h_a_bundle_entry

```text
NHI-PEDOT H-A bundle entry regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_bundle_entry_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_bundle_entry_regression.md
```

### regress_h_a_vendor_bundle_entry_return

```text
NHI-PEDOT H-A vendor bundle-entry return regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/nhi_pedot_h_a_vendor_bundle_entry_return_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/nhi_pedot_h_a_vendor_bundle_entry_return_regression.md
```

### regress_wide_raw_csv_extraction

```text
LIMINA wide raw CSV extraction regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_wide_raw_csv_extraction_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_wide_raw_csv_extraction_regression.md
```

### regress_rfq_send_log

```text
LIMINA RFQ send-log regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_rfq_send_log_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_rfq_send_log_regression.md
```

### regress_rfq_send_confirmation_intake

```text
LIMINA RFQ send-confirmation intake regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_rfq_send_confirmation_intake_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_rfq_send_confirmation_intake_regression.md
```

### regress_rfq_reply_intake

```text
LIMINA RFQ reply intake regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_rfq_reply_intake_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_rfq_reply_intake_regression.md
```

### regress_rfq_reply_log

```text
LIMINA RFQ reply-log regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_rfq_reply_log_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_rfq_reply_log_regression.md
```

### regress_quote_selection_source_guard

```text
LIMINA quote-selection source guard regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_quote_selection_source_guard_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_quote_selection_source_guard_regression.md
```

### regress_execution_release

```text
LIMINA execution-release regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_execution_release_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_execution_release_regression.md
```

### regress_execution_authorization_log

```text
LIMINA execution authorization log regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_execution_authorization_log_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_execution_authorization_log_regression.md
```

### preflight_local_capture

```text
Local capture preflight: local_capture_preflight_awaiting_entries
Filled tasks: 0 / 350
Errors: 0
Warnings: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_local_capture_preflight.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_local_capture_preflight.md
```

### render_smoke_capture_tranche

```text
Smoke capture tranche: smoke_capture_tranche_ready
Tasks: 172
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_capture_tranche.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_capture_tranche.md
```

### render_smoke_execution_queue

```text
Smoke execution queue: smoke_execution_queue_ready
Rows: 172
Awaiting values: 172
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_execution_queue.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_execution_queue.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_execution_queue.md
```

### render_smoke_entry_sheet

```text
Smoke entry sheet: smoke_entry_sheet_ready
Rows: 172
Ready to apply: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_entry_sheet.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_entry_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_entry_sheet.md
```

### render_smoke_source_drop_plan

```text
Planned source files: 172
Created directories: 0
Existing source files: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_source_drop_plan.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_source_drop_plan.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_source_drop_plan.md
```

### render_smoke_source_values_sheet

```text
Starter rows: 19
Import-ready rows: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_source_values.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_source_values_starter_batch.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_source_values_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_source_values_sheet.md
```

### audit_smoke_starter_batch_readiness

```text
Starter rows: 19
Ready for import: 0
Blocked rows: 19
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_starter_batch_readiness.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_starter_batch_readiness.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_starter_batch_readiness.md
```

### render_smoke_starter_execution_pack

```text
Starter rows: 19
Ready for import: 0
Blocked rows: 19
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_starter_execution_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_starter_execution_pack.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_starter_execution_pack.md
```

### render_smoke_starter_raw_file_template_pack

```text
Smoke starter raw-file template pack: smoke_starter_raw_file_template_pack_ready
Starter rows covered: 19
Source-class templates: 8
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_starter_raw_file_template_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_starter_raw_file_template_manifest.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_starter_raw_file_template_pack.md
```

### extract_smoke_raw_csv_values

```text
Raw CSV/TSV files found: 0
Extracted rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_raw_csv_extracted_values.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_raw_csv_value_extraction.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_raw_csv_value_extraction.md
```

### intake_smoke_unstructured_sources

```text
Unstructured plan rows: 10
Ready for value extraction: 0
Invalid source files: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_unstructured_source_intake.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_unstructured_source_intake.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_unstructured_source_intake.md
```

### render_smoke_unstructured_review_values

```text
Review rows: 10
Ready source rows: 0
Import-ready rows: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_unstructured_review_values.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_unstructured_review_values.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_unstructured_review_values.md
```

### import_smoke_source_values

```text
Smoke source value import: smoke_source_value_import_no_importable_rows
Source value files: 3
Imported rows: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_source_value_import.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_source_value_import.md
```

### apply_smoke_entry_sheet

```text
Smoke entry apply: smoke_entry_apply_no_filled_rows
Applied values: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_entry_apply.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_entry_apply.md
```

### refresh_smoke_execution_queue_after_entry_apply

```text
Smoke execution queue: smoke_execution_queue_ready
Rows: 172
Awaiting values: 172
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_execution_queue.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_execution_queue.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_execution_queue.md
```

### preflight_smoke_capture

```text
Local capture preflight: local_capture_preflight_awaiting_entries
Filled tasks: 0 / 172
Errors: 0
Warnings: 0
Wrote data/limina_smoke_capture_preflight.json
Wrote reports/limina_smoke_capture_preflight.md
```

### run_smoke_rehearsal

```text
Smoke rehearsal: smoke_rehearsal_waiting_for_preflight
Preflight: local_capture_preflight_awaiting_entries
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_smoke_rehearsal.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_smoke_rehearsal.md
```

### render_zrc_phase_a_chain_of_custody

```text
ZRC-ND Phase A chain of custody: ready_for_phase_a_sample_handoff
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_sample_labels.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_chain_of_custody.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_chain_of_custody.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_chain_of_custody.md
```

### render_zrc_phase_a_delivery_package

```text
ZRC-ND Phase A delivery package: ready_to_send
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_delivery_package_manifest.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_delivery_package_manifest.md
```

### render_zrc_phase_a_vendor_outreach

```text
ZRC-ND Phase A vendor outreach: ready_for_vendor_screening
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_vendor_outreach.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_vendor_outreach_brief.md
```

### render_zrc_phase_a_rfq_packet

```text
ZRC-ND Phase A RFQ packet: ready_to_send_rfq
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_packet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_packet.md
```

### render_zrc_phase_a_rfq_outbox

```text
ZRC-ND Phase A RFQ outbox: ready_to_send_outbox
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_outbox_manifest.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_outbox.md
```

### render_zrc_phase_a_quote_tracker

```text
ZRC-ND Phase A quote tracker: pending_outreach
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_quote_tracker.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_quote_tracker.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_quote_tracker.md
```

### render_zrc_phase_a_vendor_contact_plan

```text
ZRC-ND Phase A vendor contact plan: contact_plan_ready
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_vendor_contact_plan.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_vendor_contact_plan.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_vendor_contact_plan.md
```

### render_zrc_phase_a_rfq_dispatch_manifest

```text
ZRC-ND Phase A RFQ dispatch manifest: zrc_phase_a_rfq_dispatch_manifest_ready
Ready rows: 4 / 4
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_dispatch_manifest.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_dispatch_manifest.md
```

### intake_zrc_phase_a_rfq_send_confirmations

```text
Files scanned: 0
Applied rows: 0
Needs review: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_send_confirmation_intake.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_send_confirmation_intake.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_send_confirmation_intake.md
```

### render_zrc_phase_a_rfq_send_confirmation_entry_sheet

```text
ZRC-ND Phase A RFQ send confirmation entry sheet: zrc_phase_a_rfq_send_confirmation_entry_sheet_waiting_for_confirmation_files
Ready to apply: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.md
```

### apply_zrc_phase_a_rfq_send_confirmation_entry_sheet

```text
ZRC-ND Phase A RFQ send confirmation entry apply: zrc_phase_a_rfq_send_confirmation_entry_apply_no_apply_rows
Applied: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_send_confirmation_entry_apply.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_send_confirmation_entry_apply.md
```

### apply_zrc_phase_a_rfq_send_log

```text
Sent rows: 0
Applied tracker contact dates: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_send_log.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_send_log.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_send_log.md
```

### intake_zrc_phase_a_rfq_replies

```text
Files scanned: 0
Applied rows: 0
Needs manual review: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_reply_intake.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_reply_intake.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_reply_intake.md
```

### apply_zrc_phase_a_rfq_reply_log

```text
Received rows: 0
Applied tracker field updates: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_reply_log.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_reply_log.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_reply_log.md
```

### render_zrc_phase_a_rfq_dispatch_archive

```text
ZRC-ND Phase A RFQ dispatch archive: zrc_phase_a_rfq_dispatch_archive_ready
Archive SHA-256: 2a2ca661089a7d5ae0a91205968a383b98d7fbd90cea45c46fd4f6c8eab917d7
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_dispatch_archive_manifest.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_dispatch_archive_manifest.md
```

### render_zrc_phase_a_rfq_reply_action_pack

```text
ZRC-ND Phase A RFQ reply action pack: zrc_phase_a_rfq_reply_action_pack_waiting_for_send
Action rows: 4
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_reply_action_queue.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_reply_action_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_reply_action_pack.md
```

### render_zrc_phase_a_rfq_send_cockpit

```text
ZRC-ND Phase A RFQ send cockpit: zrc_phase_a_rfq_send_cockpit_ready_for_manual_send
Ready to use: 4 / 4
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_rfq_send_cockpit.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_send_cockpit.md
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_rfq_send_cockpit.html
```

### render_first_wave_rfq_dispatch_cockpit

```text
First-wave RFQ dispatch cockpit: first_wave_rfq_dispatch_cockpit_ready_for_manual_send
Ready to send: 8 / 8
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_first_wave_rfq_dispatch_cockpit.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_first_wave_rfq_dispatch_cockpit.md
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_first_wave_rfq_dispatch_cockpit.html
```

### process_first_wave_post_dispatch

```text
First-wave post-dispatch processing: first_wave_post_dispatch_waiting_for_real_send_confirmations
Failed commands: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_first_wave_post_dispatch_processing.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_first_wave_post_dispatch_processing.md
```

### evaluate_zrc_phase_a_quote_replies

```text
ZRC-ND Phase A quote selection: pending_outreach
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_quote_selection.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_quote_selection.md
```

### apply_zrc_phase_a_execution_authorization_log

```text
Rows: 0
Valid authorizations: 0
Errors: 0
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_execution_authorization_log.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_execution_authorization_log.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_execution_authorization_log.md
```

### audit_zrc_phase_a_execution_release

```text
ZRC-ND Phase A execution release audit: zrc_nd_phase_a_execution_release_blocked_no_source_backed_provider_selection
Ready for authorization: false
Released for execution: false
Blockers: 1
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_execution_release_audit.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_execution_release_audit.md
```

### render_zrc_phase_a_vendor_return_intake

```text
ZRC-ND Phase A vendor return intake: awaiting_vendor_return_files
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_vendor_return_checklist.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_phase_a_vendor_return_intake.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_phase_a_vendor_return_intake.md
```

### merge_zrc_phase_a_measurements

```text
Merged measurements: inserted=0 updated=0 skipped=0
Status: awaiting_measurement_file
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_measurement_merge.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_validation_runs_active.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_measurement_merge.md
```

### check_zrc_run_completeness

```text
Completeness: no_measured_rows
Measured/planned: 0 / 132
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_run_completeness.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_run_completeness.md
```

### evaluate_zrc_validation_runs

```text
Evaluated 0 row(s): no_data
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_validation_results.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_validation_results.md
Template ready at /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_validation_runs_active.csv
```

### refresh_zrc_phase_a_sentinel_after_merge

```text
Sentinel: no_sentinel_rows
Next action: Generate and fill the Phase A sentinel packet.
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_sentinel_interpretation.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_sentinel_interpretation.md
```

### refresh_zrc_next_measurements_after_merge

```text
Recommendation: needs_phase_a_sentinel
Recommended rows: 8
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_next_measurements.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_next_measurements.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_next_measurements.md
```

### audit_zrc_readiness

```text
Readiness: not_suitable_yet_no_measured_data
Suitable: False
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/zrc_nd_readiness_audit.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/zrc_nd_readiness_audit.md
```

### select_portfolio_branch

```text
Portfolio: no_suitable_material_yet
Primary next branch: limina_nhi_pedot_laminin_v0_1
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_technology_portfolio.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_technology_portfolio.md
```

### render_second_wave_candidate_queue

```text
Second-wave candidate queue: second_wave_candidate_queue_ready_while_first_wave_waits
Rows: 6
Ready for scope lock: 2
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_second_wave_candidate_queue.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_second_wave_candidate_queue.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_second_wave_candidate_queue.md
```

### render_second_wave_scope_lock_pack

```text
Second-wave scope-lock pack: second_wave_scope_lock_pack_ready
Ready candidates: 2
Tasks: 8
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_second_wave_scope_lock_pack.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_second_wave_scope_lock_tasks.csv
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_second_wave_scope_lock_pack.md
```

### audit_claim_readiness

```text
Claim ready: False
Status: no_suitable_material_claim_ready
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_suitability_claim_audit.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_suitability_claim_audit.md
```

### audit_portfolio_bypass_paths

```text
Portfolio bypass status: no_h_a_bypass_claim_ready
Non-H-A claim-ready rows: 0
Top non-H-A candidate: limina_all_dry_zwitterionic_external_v0_1
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_portfolio_bypass_audit.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_portfolio_bypass_audit.md
```

### regress_portfolio_claim_boundary

```text
LIMINA portfolio claim-boundary regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_portfolio_claim_boundary_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_portfolio_claim_boundary_regression.md
```

### regress_source_file_claim_guard

```text
LIMINA source-file claim guard regression: pass
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_source_file_claim_guard_regression.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_source_file_claim_guard_regression.md
```

### summarize_cycle_state

```text
Mission state: awaiting_real_h_a_measurements
Claim ready: False
Active candidate: limina_alg_lam_pedot_lowdose_v0_2
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/data/limina_discovery_cycle_state.json
Wrote /Users/azur/Documents/Codex/2026-05-23/applications-mentioned-by-the-user-appshot/reports/limina_discovery_cycle_state.md
```
