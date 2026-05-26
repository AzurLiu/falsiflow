#!/usr/bin/env python3
"""Summarize the current LIMINA material-discovery cycle state."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLAIM_AUDIT = ROOT / "data" / "limina_suitability_claim_audit.json"
DEFAULT_RANKING = ROOT / "data" / "limina_discovery_ranking.json"
DEFAULT_PORTFOLIO_BYPASS = ROOT / "data" / "limina_portfolio_bypass_audit.json"
DEFAULT_H_A = ROOT / "data" / "nhi_pedot_h_a_sentinel_interpretation.json"
DEFAULT_H_A_MERGE = ROOT / "data" / "nhi_pedot_h_a_measurement_merge.json"
DEFAULT_H_A_BENCH = ROOT / "data" / "nhi_pedot_h_a_bench_sheet.json"
DEFAULT_H_A_QC = ROOT / "data" / "nhi_pedot_h_a_intake_qc.json"
DEFAULT_H_A_SERVICE = ROOT / "data" / "nhi_pedot_h_a_service_request.json"
DEFAULT_H_A_CHAIN = ROOT / "data" / "nhi_pedot_h_a_chain_of_custody.json"
DEFAULT_H_A_SAMPLE_SUBMISSION = ROOT / "data" / "nhi_pedot_h_a_sample_submission_pack.json"
DEFAULT_H_A_SPLIT_SCOPE = ROOT / "data" / "nhi_pedot_h_a_split_scope_plan.json"
DEFAULT_H_A_VENDOR = ROOT / "data" / "nhi_pedot_h_a_vendor_outreach.json"
DEFAULT_H_A_RFQ = ROOT / "data" / "nhi_pedot_h_a_rfq_packet.json"
DEFAULT_H_A_RFQ_OUTBOX = ROOT / "data" / "nhi_pedot_h_a_rfq_outbox_manifest.json"
DEFAULT_H_A_RFQ_EML_DRAFTS = ROOT / "data" / "nhi_pedot_h_a_rfq_eml_drafts.json"
DEFAULT_H_A_RFQ_EML_INTEGRITY = ROOT / "data" / "nhi_pedot_h_a_rfq_eml_integrity_audit.json"
DEFAULT_H_A_QUOTE_TRACKER = ROOT / "data" / "nhi_pedot_h_a_quote_tracker.json"
DEFAULT_H_A_RFQ_SEND_ACTION_PACK = ROOT / "data" / "nhi_pedot_h_a_rfq_send_action_pack.json"
DEFAULT_H_A_RFQ_DISPATCH_MANIFEST = ROOT / "data" / "nhi_pedot_h_a_rfq_dispatch_manifest.json"
DEFAULT_H_A_RFQ_REPLY_ACTION_PACK = ROOT / "data" / "nhi_pedot_h_a_rfq_reply_action_pack.json"
DEFAULT_H_A_RFQ_SEND_COCKPIT = ROOT / "data" / "nhi_pedot_h_a_rfq_send_cockpit.json"
DEFAULT_H_A_RFQ_DISPATCH_ARCHIVE = ROOT / "data" / "nhi_pedot_h_a_rfq_dispatch_archive_manifest.json"
DEFAULT_H_A_RFQ_SEND_CONFIRMATION_INTAKE = ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_intake.json"
DEFAULT_H_A_RFQ_SEND_CONFIRMATION_ENTRY_SHEET = ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.json"
DEFAULT_H_A_RFQ_SEND_CONFIRMATION_ENTRY_APPLY = ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_entry_apply.json"
DEFAULT_H_A_RFQ_REPLY_INTAKE = ROOT / "data" / "nhi_pedot_h_a_rfq_reply_intake.json"
DEFAULT_H_A_RFQ_SEND_LOG = ROOT / "data" / "nhi_pedot_h_a_rfq_send_log.json"
DEFAULT_H_A_RFQ_REPLY_LOG = ROOT / "data" / "nhi_pedot_h_a_rfq_reply_log.json"
DEFAULT_H_A_CONTACT_PLAN = ROOT / "data" / "nhi_pedot_h_a_vendor_contact_plan.json"
DEFAULT_H_A_CONTACT_SOURCE_AUDIT = ROOT / "data" / "nhi_pedot_h_a_vendor_contact_source_audit.json"
DEFAULT_H_A_QUOTE_SELECTION = ROOT / "data" / "nhi_pedot_h_a_quote_selection.json"
DEFAULT_H_A_EXECUTION_AUTHORIZATION = ROOT / "data" / "nhi_pedot_h_a_execution_authorization_log.json"
DEFAULT_H_A_EXECUTION_RELEASE = ROOT / "data" / "nhi_pedot_h_a_execution_release_audit.json"
DEFAULT_H_A_VENDOR_RETURN = ROOT / "data" / "nhi_pedot_h_a_vendor_return_intake.json"
DEFAULT_H_A_VENDOR_BUNDLE_ENTRY_SHEET = ROOT / "data" / "nhi_pedot_h_a_vendor_bundle_entry_sheet.json"
DEFAULT_H_A_VENDOR_BUNDLE_ENTRY_APPLY = ROOT / "data" / "nhi_pedot_h_a_vendor_bundle_entry_apply.json"
DEFAULT_H_A_SOURCE_VALUES_SHEET = ROOT / "data" / "nhi_pedot_h_a_source_values_sheet.json"
DEFAULT_H_A_SOURCE_DROP = ROOT / "data" / "nhi_pedot_h_a_source_drop_plan.json"
DEFAULT_H_A_RAW_CSV_EXTRACTION = ROOT / "data" / "nhi_pedot_h_a_raw_csv_value_extraction.json"
DEFAULT_H_A_SOURCE_VALUE_IMPORT = ROOT / "data" / "nhi_pedot_h_a_source_value_import.json"
DEFAULT_NHI_FORWARD = ROOT / "data" / "nhi_pedot_forward_gate_package.json"
DEFAULT_NHI_FORWARD_SOURCE_VALUES = ROOT / "data" / "nhi_pedot_forward_source_values_sheet.json"
DEFAULT_NHI_FORWARD_SOURCE_DROP = ROOT / "data" / "nhi_pedot_forward_source_drop_plan.json"
DEFAULT_NHI_FORWARD_SOURCE_TEMPLATE_PACK = ROOT / "data" / "nhi_pedot_forward_source_file_template_pack.json"
DEFAULT_NHI_FORWARD_RAW_CSV_EXTRACTION = ROOT / "data" / "nhi_pedot_forward_raw_csv_value_extraction.json"
DEFAULT_NHI_FORWARD_SOURCE_IMPORT = ROOT / "data" / "nhi_pedot_forward_source_values_import.json"
DEFAULT_NHI_RESULTS = ROOT / "data" / "nhi_pedot_results.json"
DEFAULT_NHI_LONG_SOURCE_VALUES = ROOT / "data" / "nhi_pedot_long_source_values_sheet.json"
DEFAULT_NHI_LONG_SOURCE_DROP = ROOT / "data" / "nhi_pedot_long_source_drop_plan.json"
DEFAULT_NHI_LONG_SOURCE_TEMPLATE_PACK = ROOT / "data" / "nhi_pedot_long_source_file_template_pack.json"
DEFAULT_NHI_LONG_RAW_CSV_EXTRACTION = ROOT / "data" / "nhi_pedot_long_raw_csv_value_extraction.json"
DEFAULT_NHI_LONG_SOURCE_IMPORT = ROOT / "data" / "nhi_pedot_long_source_values_import.json"
DEFAULT_NHI_LONG_RESULTS = ROOT / "data" / "nhi_pedot_long_results.json"
DEFAULT_NEXT = ROOT / "data" / "nhi_pedot_next_measurements.json"
DEFAULT_LADDER = ROOT / "data" / "nhi_pedot_variant_ladder.json"
DEFAULT_ZRC_READINESS = ROOT / "data" / "zrc_nd_readiness_audit.json"
DEFAULT_ZRC_SENTINEL = ROOT / "data" / "zrc_nd_sentinel_interpretation.json"
DEFAULT_ZRC_NEXT = ROOT / "data" / "zrc_nd_next_measurements.json"
DEFAULT_ZRC_PHASE_A_SOURCE_VALUES = ROOT / "data" / "zrc_nd_phase_a_source_values_sheet.json"
DEFAULT_ZRC_PHASE_A_SOURCE_DROP = ROOT / "data" / "zrc_nd_phase_a_source_drop_plan.json"
DEFAULT_ZRC_PHASE_A_SOURCE_TEMPLATE_PACK = ROOT / "data" / "zrc_nd_phase_a_source_file_template_pack.json"
DEFAULT_ZRC_PHASE_A_VENDOR_BUNDLE_ENTRY_SHEET = ROOT / "data" / "zrc_nd_phase_a_vendor_bundle_entry_sheet.json"
DEFAULT_ZRC_PHASE_A_VENDOR_BUNDLE_ENTRY_APPLY = ROOT / "data" / "zrc_nd_phase_a_vendor_bundle_entry_apply.json"
DEFAULT_ZRC_PHASE_A_RAW_CSV_EXTRACTION = ROOT / "data" / "zrc_nd_phase_a_raw_csv_value_extraction.json"
DEFAULT_ZRC_PHASE_A_SOURCE_IMPORT = ROOT / "data" / "zrc_nd_phase_a_source_values_import.json"
DEFAULT_ZRC_PHASE_A_SERVICE = ROOT / "data" / "zrc_nd_phase_a_service_request.json"
DEFAULT_ZRC_PHASE_A_CHAIN = ROOT / "data" / "zrc_nd_phase_a_chain_of_custody.json"
DEFAULT_ZRC_PHASE_A_DELIVERY = ROOT / "data" / "zrc_nd_phase_a_delivery_package_manifest.json"
DEFAULT_ZRC_PHASE_A_VENDOR = ROOT / "data" / "zrc_nd_phase_a_vendor_outreach.json"
DEFAULT_ZRC_PHASE_A_RFQ = ROOT / "data" / "zrc_nd_phase_a_rfq_packet.json"
DEFAULT_ZRC_PHASE_A_RFQ_OUTBOX = ROOT / "data" / "zrc_nd_phase_a_rfq_outbox_manifest.json"
DEFAULT_ZRC_PHASE_A_QUOTE_TRACKER = ROOT / "data" / "zrc_nd_phase_a_quote_tracker.json"
DEFAULT_ZRC_PHASE_A_RFQ_SEND_CONFIRMATION_INTAKE = ROOT / "data" / "zrc_nd_phase_a_rfq_send_confirmation_intake.json"
DEFAULT_ZRC_PHASE_A_RFQ_SEND_CONFIRMATION_ENTRY_SHEET = ROOT / "data" / "zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.json"
DEFAULT_ZRC_PHASE_A_RFQ_SEND_CONFIRMATION_ENTRY_APPLY = ROOT / "data" / "zrc_nd_phase_a_rfq_send_confirmation_entry_apply.json"
DEFAULT_ZRC_PHASE_A_RFQ_SEND_LOG = ROOT / "data" / "zrc_nd_phase_a_rfq_send_log.json"
DEFAULT_ZRC_PHASE_A_RFQ_REPLY_INTAKE = ROOT / "data" / "zrc_nd_phase_a_rfq_reply_intake.json"
DEFAULT_ZRC_PHASE_A_RFQ_REPLY_LOG = ROOT / "data" / "zrc_nd_phase_a_rfq_reply_log.json"
DEFAULT_ZRC_PHASE_A_CONTACT_PLAN = ROOT / "data" / "zrc_nd_phase_a_vendor_contact_plan.json"
DEFAULT_ZRC_PHASE_A_RFQ_DISPATCH_MANIFEST = ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_manifest.json"
DEFAULT_ZRC_PHASE_A_RFQ_DISPATCH_ARCHIVE = ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_archive_manifest.json"
DEFAULT_ZRC_PHASE_A_RFQ_REPLY_ACTION_PACK = ROOT / "data" / "zrc_nd_phase_a_rfq_reply_action_pack.json"
DEFAULT_ZRC_PHASE_A_RFQ_SEND_COCKPIT = ROOT / "data" / "zrc_nd_phase_a_rfq_send_cockpit.json"
DEFAULT_ZRC_PHASE_A_QUOTE_SELECTION = ROOT / "data" / "zrc_nd_phase_a_quote_selection.json"
DEFAULT_ZRC_PHASE_A_EXECUTION_AUTHORIZATION = ROOT / "data" / "zrc_nd_phase_a_execution_authorization_log.json"
DEFAULT_ZRC_PHASE_A_EXECUTION_RELEASE = ROOT / "data" / "zrc_nd_phase_a_execution_release_audit.json"
DEFAULT_ZRC_PHASE_A_VENDOR_RETURN = ROOT / "data" / "zrc_nd_phase_a_vendor_return_intake.json"
DEFAULT_ZRC_MEASUREMENT_MERGE = ROOT / "data" / "zrc_nd_measurement_merge.json"
DEFAULT_ZRC_RUN_COMPLETENESS = ROOT / "data" / "zrc_nd_run_completeness.json"
DEFAULT_ZRC_VALIDATION_RESULTS = ROOT / "data" / "zrc_nd_validation_results.json"
DEFAULT_HYBRID_MEASUREMENT_PLAN = ROOT / "data" / "limina_hybrid_measurement_plan.json"
DEFAULT_LOCAL_CAPTURE_PACK = ROOT / "data" / "limina_local_capture_pack.json"
DEFAULT_SOURCE_FILE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_SOURCE_FILE_INVENTORY = ROOT / "data" / "limina_source_file_inventory.json"
DEFAULT_LOCAL_CAPTURE_PREFLIGHT = ROOT / "data" / "limina_local_capture_preflight.json"
DEFAULT_SMOKE_CAPTURE_TRANCHE = ROOT / "data" / "limina_smoke_capture_tranche.json"
DEFAULT_SMOKE_EXECUTION_QUEUE = ROOT / "data" / "limina_smoke_execution_queue.json"
DEFAULT_SMOKE_ENTRY_SHEET = ROOT / "data" / "limina_smoke_entry_sheet.json"
DEFAULT_SMOKE_SOURCE_DROP = ROOT / "data" / "limina_smoke_source_drop_plan.json"
DEFAULT_SMOKE_SOURCE_VALUES_SHEET = ROOT / "data" / "limina_smoke_source_values_sheet.json"
DEFAULT_SMOKE_STARTER_READINESS = ROOT / "data" / "limina_smoke_starter_batch_readiness.json"
DEFAULT_SMOKE_STARTER_EXECUTION_PACK = ROOT / "data" / "limina_smoke_starter_execution_pack.json"
DEFAULT_SMOKE_STARTER_TEMPLATE_PACK = ROOT / "data" / "limina_smoke_starter_raw_file_template_pack.json"
DEFAULT_SMOKE_RAW_CSV_EXTRACTION = ROOT / "data" / "limina_smoke_raw_csv_value_extraction.json"
DEFAULT_SMOKE_UNSTRUCTURED_INTAKE = ROOT / "data" / "limina_smoke_unstructured_source_intake.json"
DEFAULT_SMOKE_UNSTRUCTURED_REVIEW_VALUES = ROOT / "data" / "limina_smoke_unstructured_review_values.json"
DEFAULT_SMOKE_SOURCE_VALUE_IMPORT = ROOT / "data" / "limina_smoke_source_value_import.json"
DEFAULT_SMOKE_ENTRY_APPLY = ROOT / "data" / "limina_smoke_entry_apply.json"
DEFAULT_SMOKE_CAPTURE_PREFLIGHT = ROOT / "data" / "limina_smoke_capture_preflight.json"
DEFAULT_SMOKE_REHEARSAL = ROOT / "data" / "limina_smoke_rehearsal.json"
DEFAULT_FIRST_WAVE_RFQ_DISPATCH_COCKPIT = ROOT / "data" / "limina_first_wave_rfq_dispatch_cockpit.json"
DEFAULT_FIRST_WAVE_POST_DISPATCH = ROOT / "data" / "limina_first_wave_post_dispatch_processing.json"
DEFAULT_SECOND_WAVE_CANDIDATE_QUEUE = ROOT / "data" / "limina_second_wave_candidate_queue.json"
DEFAULT_SECOND_WAVE_SCOPE_LOCK_PACK = ROOT / "data" / "limina_second_wave_scope_lock_pack.json"
DEFAULT_JSON = ROOT / "data" / "limina_discovery_cycle_state.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_discovery_cycle_state.md"


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def top_item(ranking: dict[str, Any]) -> dict[str, Any]:
    items = ranking.get("items", [])
    return items[0] if items else {}


def candidate_audit(claim: dict[str, Any], technology_id: str) -> dict[str, Any]:
    for audit in claim.get("candidate_audits", []):
        if audit.get("technology_id") == technology_id:
            return audit
    return {}


def variant_by_id(ladder: dict[str, Any], variant_id: str) -> dict[str, Any]:
    for item in ladder.get("items", []):
        if item.get("variant_id") == variant_id:
            return item
    return {}


def missing_field_summary(h_a: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for row in h_a.get("missing_required_fields", []):
        counts.update(row.get("missing_fields", []))
    return [
        {"field": field, "missing_rows": count}
        for field, count in counts.most_common(limit)
    ]


def blocker_summary(claim: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for audit in claim.get("candidate_audits", []):
        rows.append({
            "technology_id": audit.get("technology_id"),
            "decision": audit.get("decision"),
            "blockers": audit.get("blockers", []),
        })
    return rows


def action(
    rank: int,
    action_id: str,
    stage: str,
    why: str,
    command: str,
    target_artifact: str,
    success_criterion: str,
) -> dict[str, Any]:
    return {
        "rank": rank,
        "action_id": action_id,
        "stage": stage,
        "why": why,
        "command": command,
        "target_artifact": target_artifact,
        "success_criterion": success_criterion,
    }


def build_actions(
    claim: dict[str, Any],
    ranking: dict[str, Any],
    h_a: dict[str, Any],
    h_a_merge: dict[str, Any],
    h_a_bench: dict[str, Any],
    h_a_qc: dict[str, Any],
    h_a_service: dict[str, Any],
    h_a_chain: dict[str, Any],
    h_a_sample_submission: dict[str, Any],
    h_a_split_scope: dict[str, Any],
    h_a_vendor: dict[str, Any],
    h_a_rfq: dict[str, Any],
    h_a_rfq_outbox: dict[str, Any],
    h_a_rfq_eml_drafts: dict[str, Any],
    h_a_rfq_eml_integrity: dict[str, Any],
    h_a_quote_tracker: dict[str, Any],
    h_a_rfq_send_action_pack: dict[str, Any],
    h_a_rfq_dispatch_manifest: dict[str, Any],
    h_a_rfq_reply_action_pack: dict[str, Any],
    h_a_rfq_send_cockpit: dict[str, Any],
    h_a_rfq_dispatch_archive: dict[str, Any],
    h_a_rfq_send_confirmation_intake: dict[str, Any],
    h_a_rfq_send_confirmation_entry_sheet: dict[str, Any],
    h_a_rfq_send_confirmation_entry_apply: dict[str, Any],
    h_a_rfq_reply_intake: dict[str, Any],
    h_a_rfq_send_log: dict[str, Any],
    h_a_rfq_reply_log: dict[str, Any],
    h_a_contact_plan: dict[str, Any],
    h_a_contact_source_audit: dict[str, Any],
    h_a_quote_selection: dict[str, Any],
    h_a_vendor_return: dict[str, Any],
    h_a_vendor_bundle_entry_sheet: dict[str, Any],
    h_a_vendor_bundle_entry_apply: dict[str, Any],
    next_rows: dict[str, Any],
    ladder: dict[str, Any],
) -> tuple[str, str, list[dict[str, Any]], list[str]]:
    if claim.get("claim_ready") is True:
        return (
            "claim_ready_review",
            "A candidate has passed the current claim audit; perform final human review before treating it as the first suitable material technology.",
            [
                action(
                    1,
                    "review_claim_audit",
                    "claim",
                    "The audit currently reports claim_ready true.",
                    "python3 scripts/audit_limina_suitability_claim.py",
                    "data/limina_suitability_claim_audit.json",
                    "claim_ready remains true after a fresh audit and all cited measurement sources are real, non-synthetic rows.",
                )
            ],
            [],
        )

    h_a_status = h_a.get("status", "unknown")
    h_a_merge_stats = h_a_merge.get("stats", {})
    h_a_bench_tasks = h_a_bench.get("task_count")
    h_a_bench_blanks = h_a_bench.get("blank_raw_entries_to_fill")
    h_a_qc_status = h_a_qc.get("status", "not_run")
    h_a_qc_counts = h_a_qc.get("issue_counts", {})
    h_a_service_status = h_a_service.get("status", "unknown")
    h_a_service_raw_entries = h_a_service.get("requested_matrix", {}).get("raw_entries", 0)
    h_a_chain_status = h_a_chain.get("status", "unknown")
    h_a_sample_label_count = h_a_chain.get("sample_label_count", 0)
    h_a_chain_rows = h_a_chain.get("chain_of_custody_row_count", 0)
    h_a_pending_transfers = h_a_chain.get("pending_transfer_rows", 0)
    h_a_sample_submission_status = h_a_sample_submission.get("status", "unknown")
    h_a_shipping_status = h_a_sample_submission.get("shipping_status", "unknown")
    h_a_split_scope_status = h_a_split_scope.get("status", "unknown")
    h_a_split_scope_pairs = h_a_split_scope.get("pair_count", 0)
    h_a_split_scope_preferred = h_a_split_scope.get("preferred_pair_count", 0)
    h_a_vendor_status = h_a_vendor.get("status", "unknown")
    h_a_vendor_first_wave = len(h_a_vendor.get("first_wave", []))
    h_a_rfq_status = h_a_rfq.get("status", "unknown")
    h_a_rfq_outbox_status = h_a_rfq_outbox.get("status", "unknown")
    h_a_rfq_outbox_ready = h_a_rfq_outbox.get("ready_to_send_count", 0)
    h_a_rfq_outbox_total = h_a_rfq_outbox.get("quote_request_count", 0)
    h_a_rfq_eml_summary = h_a_rfq_eml_drafts.get("summary", {})
    h_a_rfq_eml_status = h_a_rfq_eml_drafts.get("status", "unknown")
    h_a_rfq_eml_rows = h_a_rfq_eml_summary.get("draft_rows", 0)
    h_a_rfq_eml_ready = h_a_rfq_eml_summary.get("ready_to_open_rows", 0)
    h_a_rfq_eml_missing_to = h_a_rfq_eml_summary.get("missing_to_address_rows", 0)
    h_a_rfq_eml_missing_bundle = h_a_rfq_eml_summary.get("missing_bundle_rows", 0)
    h_a_rfq_eml_integrity_summary = h_a_rfq_eml_integrity.get("summary", {})
    h_a_rfq_eml_integrity_status = h_a_rfq_eml_integrity.get("status", "unknown")
    h_a_rfq_eml_integrity_rows = h_a_rfq_eml_integrity_summary.get("audit_rows", 0)
    h_a_rfq_eml_integrity_pass = h_a_rfq_eml_integrity_summary.get("pass_rows", 0)
    h_a_rfq_eml_integrity_fail = h_a_rfq_eml_integrity_summary.get("fail_rows", 0)
    h_a_rfq_eml_integrity_attachment_mismatch = h_a_rfq_eml_integrity_summary.get("attachment_mismatch_rows", 0)
    h_a_quote_tracker_status = h_a_quote_tracker.get("status", "unknown")
    h_a_send_pack_summary = h_a_rfq_send_action_pack.get("summary", {})
    h_a_send_pack_status = h_a_rfq_send_action_pack.get("status", "unknown")
    h_a_send_pack_rows = h_a_send_pack_summary.get("action_rows", 0)
    h_a_send_pack_ready = h_a_send_pack_summary.get("ready_to_send_rows", 0)
    h_a_send_pack_verified = h_a_send_pack_summary.get("sent_confirmation_verified_rows", 0)
    h_a_dispatch_summary = h_a_rfq_dispatch_manifest.get("summary", {})
    h_a_dispatch_status = h_a_rfq_dispatch_manifest.get("status", "unknown")
    h_a_dispatch_rows = h_a_dispatch_summary.get("dispatch_rows", 0)
    h_a_dispatch_ready = h_a_dispatch_summary.get("ready_for_manual_dispatch_rows", 0)
    h_a_dispatch_blocked = h_a_dispatch_summary.get("blocked_rows", 0)
    h_a_dispatch_bundle_matches = h_a_dispatch_summary.get("bundle_sha256_match_rows", 0)
    h_a_send_cockpit_summary = h_a_rfq_send_cockpit.get("summary", {})
    h_a_send_cockpit_status = h_a_rfq_send_cockpit.get("status", "unknown")
    h_a_send_cockpit_rows = h_a_send_cockpit_summary.get("vendor_rows", 0)
    h_a_send_cockpit_ready = h_a_send_cockpit_summary.get("ready_to_use_rows", 0)
    h_a_send_cockpit_confirmations = h_a_send_cockpit_summary.get("confirmation_files_present", 0)
    h_a_send_cockpit_replies = h_a_send_cockpit_summary.get("reply_files_present", 0)
    h_a_send_cockpit_missing_eml = h_a_send_cockpit_summary.get("missing_eml_rows", 0)
    h_a_send_cockpit_missing_bundle = h_a_send_cockpit_summary.get("missing_bundle_rows", 0)
    h_a_dispatch_archive_summary = h_a_rfq_dispatch_archive.get("summary", {})
    h_a_dispatch_archive_status = h_a_rfq_dispatch_archive.get("status", "unknown")
    h_a_dispatch_archive_files = h_a_dispatch_archive_summary.get("included_files", 0)
    h_a_dispatch_archive_missing = h_a_dispatch_archive_summary.get("missing_files", 0)
    h_a_dispatch_archive_hash_mismatches = h_a_dispatch_archive_summary.get("hash_mismatch_files", 0)
    h_a_dispatch_archive_path = h_a_rfq_dispatch_archive.get("generated_artifacts", {}).get("archive", "")
    h_a_send_intake_status = h_a_rfq_send_confirmation_intake.get("status", "unknown")
    h_a_send_intake_files = h_a_rfq_send_confirmation_intake.get("row_count", 0)
    h_a_send_intake_applied = h_a_rfq_send_confirmation_intake.get("applied_rows", 0)
    h_a_send_intake_needs_review = h_a_rfq_send_confirmation_intake.get("needs_review_rows", 0)
    h_a_send_intake_bundle_matched = h_a_rfq_send_confirmation_intake.get("bundle_hash_matched_rows", 0)
    h_a_send_entry_sheet_summary = h_a_rfq_send_confirmation_entry_sheet.get("summary", {})
    h_a_send_entry_sheet_status = h_a_rfq_send_confirmation_entry_sheet.get("status", "unknown")
    h_a_send_entry_sheet_rows = h_a_send_entry_sheet_summary.get("entry_rows", 0)
    h_a_send_entry_sheet_files = h_a_send_entry_sheet_summary.get("source_file_present_rows", 0)
    h_a_send_entry_sheet_ready = h_a_send_entry_sheet_summary.get("ready_to_apply_rows", 0)
    h_a_send_entry_sheet_blocked = h_a_send_entry_sheet_summary.get("blocked_rows", 0)
    h_a_send_entry_apply_summary = h_a_rfq_send_confirmation_entry_apply.get("summary", {})
    h_a_send_entry_apply_status = h_a_rfq_send_confirmation_entry_apply.get("status", "unknown")
    h_a_send_entry_apply_rows = h_a_send_entry_apply_summary.get("apply_rows", 0)
    h_a_send_entry_apply_applied = h_a_send_entry_apply_summary.get("applied_rows", 0)
    h_a_send_entry_apply_blocked = h_a_send_entry_apply_summary.get("blocked_rows", 0)
    h_a_send_log_status = h_a_rfq_send_log.get("status", "unknown")
    h_a_send_log_rows = h_a_rfq_send_log.get("row_count", 0)
    h_a_send_log_sent = h_a_rfq_send_log.get("sent_rows", 0)
    h_a_send_log_valid = h_a_rfq_send_log.get("valid_sent_rows", 0)
    h_a_reply_intake_status = h_a_rfq_reply_intake.get("status", "unknown")
    h_a_reply_intake_files = h_a_rfq_reply_intake.get("row_count", 0)
    h_a_reply_intake_applied = h_a_rfq_reply_intake.get("applied_rows", 0)
    h_a_reply_intake_needs_review = h_a_rfq_reply_intake.get("needs_manual_review_rows", 0)
    h_a_reply_intake_needs_send = h_a_rfq_reply_intake.get("needs_verified_send_rows", 0)
    h_a_reply_log_status = h_a_rfq_reply_log.get("status", "unknown")
    h_a_reply_log_rows = h_a_rfq_reply_log.get("row_count", 0)
    h_a_reply_log_received = h_a_rfq_reply_log.get("received_rows", 0)
    h_a_reply_log_valid = h_a_rfq_reply_log.get("valid_reply_rows", 0)
    h_a_reply_pack_summary = h_a_rfq_reply_action_pack.get("summary", {})
    h_a_reply_pack_status = h_a_rfq_reply_action_pack.get("status", "unknown")
    h_a_reply_pack_rows = h_a_reply_pack_summary.get("action_rows", 0)
    h_a_reply_pack_waiting_send = h_a_reply_pack_summary.get("waiting_for_send_rows", 0)
    h_a_reply_pack_awaiting = h_a_reply_pack_summary.get("awaiting_reply_rows", 0)
    h_a_reply_pack_ready_apply = h_a_reply_pack_summary.get("ready_for_reply_log_apply_rows", 0)
    h_a_contact_plan_status = h_a_contact_plan.get("status", "unknown")
    h_a_contact_ready = h_a_contact_plan.get("status_counts", {}).get("ready_to_send", 0)
    h_a_contact_standby = h_a_contact_plan.get("status_counts", {}).get("standby_secondary_wave", 0)
    h_a_contact_total = h_a_contact_plan.get("row_count", 0)
    h_a_contact_source_summary = h_a_contact_source_audit.get("summary", {})
    h_a_contact_source_status = h_a_contact_source_audit.get("status", "unknown")
    h_a_contact_source_rows = h_a_contact_source_summary.get("audit_rows", 0)
    h_a_contact_source_pass = h_a_contact_source_summary.get("pass_rows", 0)
    h_a_contact_source_fail = h_a_contact_source_summary.get("fail_rows", 0)
    h_a_contact_source_stale = h_a_contact_source_summary.get("stale_proof_rows", 0)
    h_a_quote_selection_status = h_a_quote_selection.get("status", "unknown")
    h_a_quote_selection_replies = h_a_quote_selection.get("reply_count", 0)
    h_a_quote_selection_source_backed = h_a_quote_selection.get("source_backed_reply_count", 0)
    h_a_quote_selection_shortlist = h_a_quote_selection.get("shortlist_count", 0)
    h_a_vendor_return_status = h_a_vendor_return.get("status", "unknown")
    h_a_vendor_return_values = h_a_vendor_return.get("raw_measurements", {}).get("value_row_count", 0)
    h_a_vendor_return_bundle = h_a_vendor_return.get("bundle_entry_sheet", {})
    h_a_vendor_return_bundle_rows = h_a_vendor_return_bundle.get("row_count", 0)
    h_a_vendor_return_bundle_apply_rows = h_a_vendor_return_bundle.get("apply_row_count", 0)
    h_a_vendor_return_exports = h_a_vendor_return.get("instrument_export_file_count", 0)
    h_a_vendor_bundle_entry_sheet_summary = h_a_vendor_bundle_entry_sheet.get("summary", {})
    h_a_vendor_bundle_entry_sheet_status = h_a_vendor_bundle_entry_sheet.get("status", "unknown")
    h_a_vendor_bundle_entry_sheet_rows = h_a_vendor_bundle_entry_sheet_summary.get("bundle_rows", 0)
    h_a_vendor_bundle_entry_sheet_ready = h_a_vendor_bundle_entry_sheet_summary.get("ready_to_apply_rows", 0)
    h_a_vendor_bundle_entry_sheet_blocked = h_a_vendor_bundle_entry_sheet_summary.get("blocked_rows", 0)
    h_a_vendor_bundle_entry_summary = h_a_vendor_bundle_entry_apply.get("summary", {})
    h_a_vendor_bundle_entry_status = h_a_vendor_bundle_entry_apply.get("status", "unknown")
    h_a_vendor_bundle_entry_sheet_exists = h_a_vendor_bundle_entry_summary.get("sheet_exists", False)
    h_a_vendor_bundle_entry_bundles = h_a_vendor_bundle_entry_summary.get("applied_bundles", 0)
    h_a_vendor_bundle_entry_source_rows = h_a_vendor_bundle_entry_summary.get("applied_source_value_rows", 0)
    h_a_vendor_bundle_entry_errors = h_a_vendor_bundle_entry_summary.get("error_count", 0)
    provenance = h_a.get("provenance", {})
    recommended_rows = next_rows.get("recommended_rows", [])
    lead = variant_by_id(ladder, "alg_lam_pedot_0p6pct_lead")
    rescue = variant_by_id(ladder, "alg_lam_pedot_0p3pct_safety_rescue")
    midpoint = variant_by_id(ladder, "alg_lam_pedot_0p9pct_midpoint")
    anchor = variant_by_id(ladder, "pda_anchor_alg_lam_pedot_0p6pct")

    if h_a_status in {"h_a_invalid_provenance", "h_a_no_sentinel_rows", "h_a_sentinel_needs_more_data"}:
        state = "awaiting_real_h_a_measurements"
        reason = h_a.get("next_action") or "Complete the first acellular H-A sentinel with real measured provenance."
        actions = [
            action(
                1,
                "render_h_a_service_request",
                "H-A",
                "The service request is the handoff packet for turning the dry-lab H-A blocker into real acellular measurements.",
                "python3 scripts/render_nhi_pedot_h_a_service_request.py",
                "reports/nhi_pedot_h_a_service_request.md",
                "Service request is ready and lists the 12-run matrix, 228 raw entries, deliverables, provenance fields, and rejection rules.",
            ),
            action(
                2,
                "render_h_a_chain_of_custody",
                "H-A",
                "The sample handoff needs label rows and transfer blanks before the package can be sent or received cleanly.",
                "python3 scripts/render_nhi_pedot_h_a_chain_of_custody.py",
                "reports/nhi_pedot_h_a_chain_of_custody.md",
                "Sample labels and chain-of-custody rows exist for every H-A sample_event, with transfer fields left blank until real handoff.",
            ),
            action(
                3,
                "render_h_a_sample_submission_pack",
                "H-A",
                "Vendors commonly need material disclosure, SDS expectations, sample count, and pre-shipment constraints before accepting H-A samples.",
                "python3 scripts/render_nhi_pedot_h_a_sample_submission_pack.py",
                "reports/nhi_pedot_h_a_sample_submission_pack.md",
                "Sample submission pack is ready and explicitly blocks shipping until quote, SDS, sample acceptance, and custody requirements are confirmed.",
            ),
            action(
                4,
                "render_h_a_split_scope_plan",
                "H-A",
                "If no single provider covers the full H-A matrix, split media chemistry and coupon physical/imaging work without losing run_id provenance.",
                "python3 scripts/render_nhi_pedot_h_a_split_scope_plan.py",
                "reports/nhi_pedot_h_a_split_scope_plan.md",
                "Split-scope plan is ready with preferred vendor pairings, field assignments, and shared source_file/custody requirements.",
            ),
            action(
                5,
                "screen_h_a_vendor_or_cooperator",
                "H-A",
                "The outreach brief translates the H-A package into concrete vendor/cooperator screening questions.",
                "python3 scripts/render_nhi_pedot_h_a_vendor_outreach.py",
                "reports/nhi_pedot_h_a_vendor_outreach_brief.md",
                "Vendor outreach brief is ready and includes first-wave contacts, source links, and quote-screening questions.",
            ),
            action(
                6,
                "send_h_a_rfq_packet",
                "H-A",
                "The RFQ packet contains per-vendor email text, attachment list, disqualifiers, and quote scoring rules.",
                "python3 scripts/render_nhi_pedot_h_a_rfq_packet.py",
                "reports/nhi_pedot_h_a_rfq_packet.md",
                "RFQ packet is ready_to_send_rfq and quote tracker rows exist for each first-wave contact.",
            ),
            action(
                7,
                "send_h_a_rfq_outbox",
                "H-A",
                "The outbox converts the RFQ packet into vendor-specific email files and zip bundles that can be sent without manual attachment drift.",
                "python3 scripts/render_nhi_pedot_h_a_rfq_outbox.py",
                "reports/nhi_pedot_h_a_rfq_outbox.md",
                "RFQ outbox is ready_to_send_outbox and every first-wave vendor has a zip bundle with the current attachment manifest.",
            ),
            action(
                8,
                "track_h_a_quote_replies",
                "H-A",
                "Quote replies must be preserved and screened before selecting who can produce real H-A rows.",
                "python3 scripts/render_nhi_pedot_h_a_quote_tracker.py",
                "reports/nhi_pedot_h_a_quote_tracker.md",
                "Quote tracker preserves any existing contact dates, replies, decisions, and notes while recording disqualifiers plus decision rules.",
            ),
            action(
                9,
                "send_first_wave_contacts",
                "H-A",
                "The contact plan maps each ready RFQ bundle to official vendor contact channels and the tracker fields that must be updated after sending.",
                "python3 scripts/render_nhi_pedot_h_a_vendor_contact_plan.py",
                "reports/nhi_pedot_h_a_vendor_contact_plan.md",
                "Contact plan is contact_plan_ready with official channels for every first-wave vendor and no missing outbox bundles.",
            ),
            action(
                10,
                "score_h_a_quote_replies",
                "H-A",
                "When replies arrive, the scorecard should choose execution partners by raw-data fidelity and field coverage rather than narrative vendor claims.",
                "python3 scripts/evaluate_nhi_pedot_h_a_quote_replies.py",
                "reports/nhi_pedot_h_a_quote_selection.md",
                "Quote selection reports ready_to_select_provider only when reply fields pass hard requirements and the scorecard threshold.",
            ),
            action(
                11,
                "check_vendor_return_inbox",
                "H-A",
                "Once a vendor returns files, the inbox checker verifies raw CSV schema, chain-of-custody, deviation log, and source_file references before merge/QC.",
                "python3 scripts/render_nhi_pedot_h_a_vendor_return_intake.py",
                "reports/nhi_pedot_h_a_vendor_return_intake.md",
                "Vendor return intake reports vendor_return_ready_for_merge only when required return files and source_file references are present.",
            ),
            action(
                12,
                "render_h_a_bench_sheet",
                "H-A",
                "The bench sheet compresses the active H-A rows and raw template into an executable wet-bench checklist.",
                "python3 scripts/render_nhi_pedot_h_a_bench_sheet.py",
                "reports/nhi_pedot_h_a_bench_sheet.md",
                "Bench sheet lists all 12 H-A run tasks, lead rows, blank raw entries, and stop criteria.",
            ),
            action(
                13,
                "merge_raw_h_a_measurements",
                "H-A",
                "Raw instrument/inspection entries should be merged into an active runs CSV before QC.",
                "python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py",
                "data/nhi_pedot_h_a_runs_active.csv",
                "Raw rows have been merged into active runs and no unresolved target or unknown run_id errors remain.",
            ),
            action(
                14,
                "complete_h_a_rows_and_run_intake_qc",
                "H-A",
                "The leading route cannot move until the acellular medium/physical sentinel has QC-clean real rows.",
                "python3 scripts/qc_nhi_pedot_h_a_intake.py --runs data/nhi_pedot_h_a_runs_active.csv",
                "data/nhi_pedot_h_a_runs_active.csv",
                "H-A intake QC reports h_a_intake_ready with zero errors and claimable measured provenance.",
            ),
            action(
                15,
                "interpret_qc_ready_h_a",
                "H-A",
                "The H-A interpreter should only be trusted after intake QC is clean.",
                "python3 scripts/interpret_nhi_pedot_h_a_sentinel.py --runs data/nhi_pedot_h_a_runs_active.csv",
                "data/nhi_pedot_h_a_sentinel_interpretation.json",
                "H-A interpretation is no longer h_a_invalid_provenance and measured_row_count equals row_count for required sentinel rows.",
            ),
            action(
                16,
                "refresh_next_measurement_selector",
                "H-A",
                "The selector should be regenerated after any new measured rows land.",
                "python3 scripts/suggest_nhi_pedot_next_measurements.py",
                "data/nhi_pedot_next_measurements.json",
                "Recommended rows match the remaining unmet H-A coverage instead of stale no-data rows.",
            ),
            action(
                17,
                "refresh_h_a_packet",
                "H-A",
                "The data-entry packet should reflect the current selector output and recipe lock.",
                "python3 scripts/generate_nhi_pedot_sentinel_packet.py",
                "reports/nhi_pedot_h_a_sentinel_packet.md",
                "The packet rows match the current next-measurement selector and remain marked as pending until real values are entered.",
            ),
            action(
                18,
                "keep_variant_ladder_ready",
                "adaptive_design",
                f"Current lead is {lead.get('variant_id', 'alg_lam_pedot_0p6pct_lead')}; rescue routes are predeclared but must wait for measured H-A signals.",
                "python3 scripts/design_nhi_pedot_variant_ladder.py",
                "reports/nhi_pedot_variant_ladder.md",
                "Variant ladder still ranks the 0.6 wt percent lead first and records trigger conditions for rescue variants.",
            ),
        ]
        actions = [
            action(
                1,
                "send_h_a_rfq_eml_drafts",
                "H-A",
                "The RFQ .eml drafts and vendor bundles are ready, contact-source audited, integrity checked, bound into a dispatch manifest, and packaged into a single dispatch archive; real H-A measurements cannot arrive until the first-wave outreach is actually sent.",
                "manual: use data/nhi_pedot_h_a_rfq_dispatch_archive/nhi_pedot_h_a_rfq_dispatch_archive.zip or reports/nhi_pedot_h_a_rfq_send_cockpit.html to send ready drafts",
                "data/rfq_send_confirmation_files/h_a",
                "Each sent vendor has a real sent-email export, web-form confirmation, PDF, or screenshot saved under data/rfq_send_confirmation_files/h_a, after h_a_vendor_contact_source_audit_ready, h_a_rfq_dispatch_manifest_ready, h_a_rfq_dispatch_archive_ready, and h_a_rfq_eml_integrity_ready remain true.",
            ),
            action(
                2,
                "intake_h_a_rfq_send_confirmations",
                "H-A",
                "Saved confirmations should be parsed before the tracker is treated as source-backed outreach.",
                "python3 scripts/intake_limina_rfq_send_confirmations.py --profile h_a",
                "data/nhi_pedot_h_a_rfq_send_confirmation_intake.json",
                "The intake registers real confirmation files with matching bundle hashes or flags rows for human review.",
            ),
            action(
                3,
                "apply_h_a_non_eml_send_confirmations",
                "H-A",
                "If the RFQ was sent through a web form, PDF/screenshot/saved-page confirmations need a guarded manual entry path before the send log is trusted.",
                "run: python3 scripts/render_nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.py, then python3 scripts/apply_nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.py",
                "data/nhi_pedot_h_a_rfq_send_confirmation_entry_apply.json",
                "Non-EML confirmations are applied only when a real source file exists, current SHA-256 is recorded, bundle hash matches the dispatch manifest, and apply=yes is human-reviewed.",
            ),
            action(
                4,
                "apply_h_a_rfq_send_log",
                "H-A",
                "Verified send rows must be reflected into the RFQ send log and quote tracker before replies are accepted as sourced.",
                "python3 scripts/apply_limina_rfq_send_log.py --profile h_a",
                "data/nhi_pedot_h_a_rfq_send_log.json",
                "The send log has valid sent rows and tracker contact dates for the sent first-wave vendors.",
            ),
            action(
                5,
                "save_h_a_rfq_replies",
                "H-A",
                "Vendor replies are the next external input after verified sends, but they must be preserved as original source files.",
                "manual: save original replies under data/rfq_reply_files/h_a",
                "data/rfq_reply_files/h_a",
                "Every received vendor reply, quote PDF, proposal, or clarification email is saved at the path listed in reports/nhi_pedot_h_a_rfq_reply_action_pack.md.",
            ),
            action(
                6,
                "intake_h_a_rfq_replies",
                "H-A",
                "Reply intake only registers parsable source-backed replies after verified sends and leaves quote interpretation to review.",
                "python3 scripts/intake_limina_rfq_replies.py --profile h_a",
                "data/nhi_pedot_h_a_rfq_reply_intake.json",
                "Source-backed replies are registered for review without auto-scoring or provider selection.",
            ),
            action(
                7,
                "apply_h_a_rfq_reply_log",
                "H-A",
                "Reviewed reply fields should be applied to the tracker before provider scoring.",
                "python3 scripts/apply_limina_rfq_reply_log.py --profile h_a",
                "data/nhi_pedot_h_a_rfq_reply_log.json",
                "The reply log has valid received rows and applies only source-backed review fields.",
            ),
            action(
                8,
                "score_h_a_quote_replies",
                "H-A",
                "The scorecard should choose execution partners by raw-data fidelity and field coverage rather than narrative vendor claims.",
                "python3 scripts/evaluate_nhi_pedot_h_a_quote_replies.py",
                "reports/nhi_pedot_h_a_quote_selection.md",
                "Quote selection reports ready_to_select_provider only when reply fields pass hard requirements and the scorecard threshold.",
            ),
            action(
                9,
                "record_h_a_execution_authorization",
                "H-A",
                "A selected provider still needs human authorization before samples are released.",
                "python3 scripts/apply_limina_execution_authorization_log.py --profile h_a",
                "data/nhi_pedot_h_a_execution_authorization_log.json",
                "Execution authorization is source-backed for the selected provider or remains explicitly waiting for human authorization.",
            ),
            action(
                10,
                "audit_h_a_execution_release",
                "H-A",
                "The release audit checks that provider selection, authorization, custody, sample submission, and return expectations are all satisfied.",
                "python3 scripts/audit_limina_execution_release.py --profile h_a",
                "data/nhi_pedot_h_a_execution_release_audit.json",
                "Execution is released only when the audit has no blockers and the authorized provider is source-backed.",
            ),
            action(
                11,
                "check_h_a_vendor_return_inbox",
                "H-A",
                "Once a vendor returns files, the inbox checker verifies raw CSV schema, chain-of-custody, deviation log, bundle-entry sheet, and source_file references before merge/QC.",
                "python3 scripts/render_nhi_pedot_h_a_vendor_return_intake.py",
                "reports/nhi_pedot_h_a_vendor_return_intake.md",
                "Vendor return intake reports vendor_return_ready_for_merge only when required return files and source_file references are present.",
            ),
            action(
                12,
                "render_h_a_vendor_bundle_entry_sheet",
                "H-A",
                "The compact returned bundle-entry path needs a scaffold in the vendor inbox so providers can fill one row per source-file bundle.",
                "python3 scripts/render_nhi_pedot_h_a_vendor_bundle_entry_sheet.py",
                "reports/nhi_pedot_h_a_vendor_bundle_entry_sheet.md",
                "The vendor bundle-entry sheet is ready, points source_file defaults at the vendor return inbox, and has no ready rows until real returned files are reviewed.",
            ),
            action(
                13,
                "apply_h_a_vendor_bundle_entry_return",
                "H-A",
                "The compact returned bundle-entry sheet can fill source-value rows without hand-copying 228 individual entries.",
                "python3 scripts/apply_nhi_pedot_h_a_vendor_bundle_entry_return.py",
                "data/nhi_pedot_h_a_vendor_bundle_entry_apply.json",
                "Returned apply=yes bundle rows are expanded into source-value rows with allowed source_file references and zero errors.",
            ),
            action(
                14,
                "extract_h_a_raw_csv_values",
                "H-A",
                "Raw vendor CSV exports should be converted to source-value rows before merge.",
                "python3 scripts/extract_nhi_pedot_h_a_raw_csv_values.py",
                "data/nhi_pedot_h_a_raw_csv_value_extraction.json",
                "Extraction finds real raw CSV files and emits no schema or source-reference errors.",
            ),
            action(
                15,
                "import_h_a_source_values",
                "H-A",
                "Source-value rows from returned bundles or raw CSV extraction must be imported before active H-A runs can change.",
                "python3 scripts/import_nhi_pedot_h_a_source_values.py",
                "data/nhi_pedot_h_a_source_value_import.json",
                "Import applies only rows with filled values and real source_file provenance.",
            ),
            action(
                16,
                "merge_raw_h_a_measurements",
                "H-A",
                "Raw instrument/inspection entries should be merged into an active runs CSV before QC.",
                "python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py",
                "data/nhi_pedot_h_a_runs_active.csv",
                "Raw rows have been merged into active runs and no unresolved target or unknown run_id errors remain.",
            ),
            action(
                17,
                "complete_h_a_rows_and_run_intake_qc",
                "H-A",
                "The leading route cannot move until the acellular medium/physical sentinel has QC-clean real rows.",
                "python3 scripts/qc_nhi_pedot_h_a_intake.py --runs data/nhi_pedot_h_a_runs_active.csv",
                "data/nhi_pedot_h_a_runs_active.csv",
                "H-A intake QC reports h_a_intake_ready with zero errors and claimable measured provenance.",
            ),
            action(
                18,
                "interpret_qc_ready_h_a",
                "H-A",
                "The H-A interpreter should only be trusted after intake QC is clean.",
                "python3 scripts/interpret_nhi_pedot_h_a_sentinel.py --runs data/nhi_pedot_h_a_runs_active.csv",
                "data/nhi_pedot_h_a_sentinel_interpretation.json",
                "H-A interpretation is no longer h_a_invalid_provenance and measured_row_count equals row_count for required sentinel rows.",
            ),
            action(
                19,
                "refresh_next_measurement_selector",
                "H-A",
                "The selector should be regenerated after any new measured rows land.",
                "python3 scripts/suggest_nhi_pedot_next_measurements.py",
                "data/nhi_pedot_next_measurements.json",
                "Recommended rows match the remaining unmet H-A coverage instead of stale no-data rows.",
            ),
            action(
                20,
                "refresh_h_a_packet",
                "H-A",
                "The data-entry packet should reflect the current selector output and recipe lock.",
                "python3 scripts/generate_nhi_pedot_sentinel_packet.py",
                "reports/nhi_pedot_h_a_sentinel_packet.md",
                "The packet rows match the current next-measurement selector and remain marked as pending until real values are entered.",
            ),
            action(
                21,
                "keep_variant_ladder_ready",
                "adaptive_design",
                f"Current lead is {lead.get('variant_id', 'alg_lam_pedot_0p6pct_lead')}; rescue routes are predeclared but must wait for measured H-A signals.",
                "python3 scripts/design_nhi_pedot_variant_ladder.py",
                "reports/nhi_pedot_variant_ladder.md",
                "Variant ladder still ranks the 0.6 wt percent lead first and records trigger conditions for rescue variants.",
            ),
        ]
        evidence_gaps = [
            f"H-A measured rows: {provenance.get('measured_row_count', 0)} of {provenance.get('row_count', 0)}",
            f"H-A placeholder rows: {provenance.get('placeholder_row_count', 0)}",
            f"H-A bench sheet: tasks={h_a_bench_tasks if h_a_bench_tasks is not None else 'unknown'}; blank_raw_entries={h_a_bench_blanks if h_a_bench_blanks is not None else 'unknown'}",
            f"H-A service request: {h_a_service_status}; raw_entries={h_a_service_raw_entries}",
            f"H-A sample handoff: {h_a_chain_status}; labels={h_a_sample_label_count}; custody_rows={h_a_chain_rows}; pending_transfers={h_a_pending_transfers}",
            f"H-A sample submission: {h_a_sample_submission_status}; shipping_status={h_a_shipping_status}",
            f"H-A split-scope plan: {h_a_split_scope_status}; pairs={h_a_split_scope_pairs}; preferred_pairs={h_a_split_scope_preferred}",
            f"H-A vendor outreach: {h_a_vendor_status}; first_wave_contacts={h_a_vendor_first_wave}",
            f"H-A RFQ packet: {h_a_rfq_status}; quote_tracker={h_a_quote_tracker_status}",
            f"H-A RFQ outbox: {h_a_rfq_outbox_status}; ready_to_send={h_a_rfq_outbox_ready} of {h_a_rfq_outbox_total}",
            f"H-A RFQ EML drafts: {h_a_rfq_eml_status}; rows={h_a_rfq_eml_rows}; ready={h_a_rfq_eml_ready}; missing_to={h_a_rfq_eml_missing_to}; missing_bundle={h_a_rfq_eml_missing_bundle}",
            f"H-A RFQ EML integrity audit: {h_a_rfq_eml_integrity_status}; rows={h_a_rfq_eml_integrity_rows}; pass={h_a_rfq_eml_integrity_pass}; fail={h_a_rfq_eml_integrity_fail}; attachment_mismatch={h_a_rfq_eml_integrity_attachment_mismatch}",
            f"H-A RFQ send action pack: {h_a_send_pack_status}; rows={h_a_send_pack_rows}; ready={h_a_send_pack_ready}; verified={h_a_send_pack_verified}",
            f"H-A RFQ dispatch manifest: {h_a_dispatch_status}; rows={h_a_dispatch_rows}; ready={h_a_dispatch_ready}; blocked={h_a_dispatch_blocked}; bundle_matches={h_a_dispatch_bundle_matches}",
            f"H-A RFQ send cockpit: {h_a_send_cockpit_status}; rows={h_a_send_cockpit_rows}; ready={h_a_send_cockpit_ready}; confirmations={h_a_send_cockpit_confirmations}; replies={h_a_send_cockpit_replies}; missing_eml={h_a_send_cockpit_missing_eml}; missing_bundle={h_a_send_cockpit_missing_bundle}",
            f"H-A RFQ dispatch archive: {h_a_dispatch_archive_status}; files={h_a_dispatch_archive_files}; missing={h_a_dispatch_archive_missing}; hash_mismatches={h_a_dispatch_archive_hash_mismatches}; archive={h_a_dispatch_archive_path}",
            f"H-A RFQ send confirmation intake: {h_a_send_intake_status}; files={h_a_send_intake_files}; applied={h_a_send_intake_applied}; needs_review={h_a_send_intake_needs_review}; bundle_matched={h_a_send_intake_bundle_matched}",
            f"H-A RFQ send confirmation entry sheet: {h_a_send_entry_sheet_status}; rows={h_a_send_entry_sheet_rows}; source_files={h_a_send_entry_sheet_files}; ready={h_a_send_entry_sheet_ready}; blocked={h_a_send_entry_sheet_blocked}",
            f"H-A RFQ send confirmation entry apply: {h_a_send_entry_apply_status}; apply_rows={h_a_send_entry_apply_rows}; applied={h_a_send_entry_apply_applied}; blocked={h_a_send_entry_apply_blocked}",
            f"H-A RFQ send log: {h_a_send_log_status}; rows={h_a_send_log_rows}; sent={h_a_send_log_sent}; valid={h_a_send_log_valid}",
            f"H-A RFQ reply intake: {h_a_reply_intake_status}; files={h_a_reply_intake_files}; applied={h_a_reply_intake_applied}; needs_review={h_a_reply_intake_needs_review}; needs_verified_send={h_a_reply_intake_needs_send}",
            f"H-A RFQ reply log: {h_a_reply_log_status}; rows={h_a_reply_log_rows}; received={h_a_reply_log_received}; valid={h_a_reply_log_valid}",
            f"H-A RFQ reply action pack: {h_a_reply_pack_status}; rows={h_a_reply_pack_rows}; waiting_send={h_a_reply_pack_waiting_send}; awaiting_reply={h_a_reply_pack_awaiting}; ready_apply={h_a_reply_pack_ready_apply}",
            f"H-A vendor contact plan: {h_a_contact_plan_status}; ready_first_wave={h_a_contact_ready}; standby_second_wave={h_a_contact_standby}; total={h_a_contact_total}",
            f"H-A vendor contact source audit: {h_a_contact_source_status}; rows={h_a_contact_source_rows}; pass={h_a_contact_source_pass}; fail={h_a_contact_source_fail}; stale={h_a_contact_source_stale}",
            f"H-A quote selection: {h_a_quote_selection_status}; replies={h_a_quote_selection_replies}; source_backed_replies={h_a_quote_selection_source_backed}; shortlist={h_a_quote_selection_shortlist}",
            f"H-A vendor return intake: {h_a_vendor_return_status}; raw_value_rows={h_a_vendor_return_values}; bundle_rows={h_a_vendor_return_bundle_rows}; bundle_apply_rows={h_a_vendor_return_bundle_apply_rows}; export_files={h_a_vendor_return_exports}",
            f"H-A vendor bundle entry sheet: {h_a_vendor_bundle_entry_sheet_status}; bundles={h_a_vendor_bundle_entry_sheet_rows}; ready={h_a_vendor_bundle_entry_sheet_ready}; blocked={h_a_vendor_bundle_entry_sheet_blocked}",
            f"H-A vendor bundle entry return apply: {h_a_vendor_bundle_entry_status}; sheet_exists={str(bool(h_a_vendor_bundle_entry_sheet_exists)).lower()}; bundles={h_a_vendor_bundle_entry_bundles}; source_rows={h_a_vendor_bundle_entry_source_rows}; errors={h_a_vendor_bundle_entry_errors}",
            f"H-A raw merge: applied={h_a_merge_stats.get('applied_values', 'unknown')}; unresolved_targets={h_a_merge_stats.get('unresolved_targets', 'unknown')}; unknown_run_ids={h_a_merge_stats.get('skipped_unknown_run_id', 'unknown')}",
            f"H-A intake QC: {h_a_qc_status}; errors={h_a_qc_counts.get('error', 'unknown')}; warnings={h_a_qc_counts.get('warning', 'unknown')}",
            f"Recommended H-A rows waiting: {len(recommended_rows)}",
        ]
        return state, reason, actions, evidence_gaps

    if h_a_status == "h_a_lead_fails_stop":
        state = "lead_h_a_failed_branch_required"
        reason = "Measured H-A lead rows failed; do not advance to live cells or H-B until the failure mode is remediated."
        actions = [
            action(
                1,
                "branch_to_safety_rescue",
                "adaptive_design",
                f"Use {rescue.get('variant_id', '0.3 wt percent safety rescue')} if the H-A failure is PEDOT-linked medium drift or mild shedding.",
                "python3 scripts/design_nhi_pedot_variant_ladder.py",
                "data/nhi_pedot_variant_ladder.csv",
                "A new H-A packet is generated for the rescue loading and passes provenance checks before interpretation.",
            ),
            action(
                2,
                "branch_to_anchor_rescue_if_mechanical",
                "adaptive_design",
                f"Use {anchor.get('variant_id', 'PDA anchor rescue')} only when medium integrity is clean and delamination/window instability is dominant.",
                "python3 scripts/design_nhi_pedot_variant_ladder.py",
                "reports/nhi_pedot_variant_ladder.md",
                "Primer extract blanks are added before any anchored lead reaches H-B or H-C.",
            ),
        ]
        return state, reason, actions, ["H-A lead failed; failure mode classification required from measured rows."]

    if h_a_status in {
        "h_a_lead_passes_continue_h_b",
        "h_a_lead_passes_continue_challenge_boundary",
        "h_a_lead_passes_hydrogel_control_issue",
    }:
        state = "ready_for_h_b_electrochemical_gate"
        reason = "H-A is compatible enough to authorize H-B; suitability is still unproven."
        actions = [
            action(
                1,
                "generate_h_b_rows",
                "H-B",
                "The lead must show electrochemical value beyond hydrogel-laminin control.",
                "python3 scripts/suggest_nhi_pedot_next_measurements.py",
                "data/nhi_pedot_next_measurements.csv",
                "H-B recommended rows cover hydrogel control, lead, and high-loading challenge with required EIS/charge-storage fields.",
            ),
            action(
                2,
                "use_midpoint_if_electrical_benefit_borderline",
                "adaptive_design",
                f"Use {midpoint.get('variant_id', '0.9 wt percent midpoint')} only if H-A passes but H-B benefit is borderline.",
                "python3 scripts/design_nhi_pedot_variant_ladder.py",
                "reports/nhi_pedot_variant_ladder.md",
                "Midpoint variant remains gated behind H-A pass and H-B borderline result.",
            ),
        ]
        return state, reason, actions, ["H-B and H-C measured rows are still missing."]

    state = "needs_state_refresh"
    reason = f"H-A status `{h_a_status}` is not mapped to a confident next branch; refresh upstream reports."
    actions = [
        action(
            1,
            "refresh_core_reports",
            "orchestration",
            "The cycle controller needs fresh upstream JSON before it can choose a branch.",
            "python3 scripts/rank_limina_discovery_candidates.py",
            "data/limina_discovery_cycle_state.json",
            "Discovery ranking is fresh; then rerun the H-A interpreter, claim audit, and discovery cycle controller.",
        )
    ]
    return state, reason, actions, [f"Unmapped H-A status: {h_a_status}"]


def build_state(args: argparse.Namespace) -> dict[str, Any]:
    claim = load_json(args.claim_audit)
    ranking = load_json(args.ranking)
    portfolio_bypass = load_json(args.portfolio_bypass)
    h_a = load_json(args.h_a)
    h_a_merge = load_json(args.h_a_merge)
    h_a_bench = load_json(args.h_a_bench)
    h_a_qc = load_json(args.h_a_qc)
    h_a_service = load_json(args.h_a_service)
    h_a_chain = load_json(args.h_a_chain)
    h_a_sample_submission = load_json(args.h_a_sample_submission)
    h_a_split_scope = load_json(args.h_a_split_scope)
    h_a_vendor = load_json(args.h_a_vendor)
    h_a_rfq = load_json(args.h_a_rfq)
    h_a_rfq_outbox = load_json(args.h_a_rfq_outbox)
    h_a_rfq_eml_drafts = load_json(args.h_a_rfq_eml_drafts)
    h_a_rfq_eml_integrity = load_json(args.h_a_rfq_eml_integrity)
    h_a_quote_tracker = load_json(args.h_a_quote_tracker)
    h_a_rfq_send_action_pack = load_json(args.h_a_rfq_send_action_pack)
    h_a_rfq_dispatch_manifest = load_json(args.h_a_rfq_dispatch_manifest)
    h_a_rfq_reply_action_pack = load_json(args.h_a_rfq_reply_action_pack)
    h_a_rfq_send_cockpit = load_json(args.h_a_rfq_send_cockpit)
    h_a_rfq_dispatch_archive = load_json(args.h_a_rfq_dispatch_archive)
    h_a_rfq_send_confirmation_intake = load_json(args.h_a_rfq_send_confirmation_intake)
    h_a_rfq_send_confirmation_entry_sheet = load_json(args.h_a_rfq_send_confirmation_entry_sheet)
    h_a_rfq_send_confirmation_entry_apply = load_json(args.h_a_rfq_send_confirmation_entry_apply)
    h_a_rfq_reply_intake = load_json(args.h_a_rfq_reply_intake)
    h_a_rfq_send_log = load_json(args.h_a_rfq_send_log)
    h_a_rfq_reply_log = load_json(args.h_a_rfq_reply_log)
    h_a_contact_plan = load_json(args.h_a_contact_plan)
    h_a_contact_source_audit = load_json(args.h_a_contact_source_audit)
    h_a_quote_selection = load_json(args.h_a_quote_selection)
    h_a_execution_authorization = load_json(args.h_a_execution_authorization)
    h_a_execution_release = load_json(args.h_a_execution_release)
    h_a_vendor_return = load_json(args.h_a_vendor_return)
    h_a_vendor_bundle_entry_sheet = load_json(args.h_a_vendor_bundle_entry_sheet)
    h_a_vendor_bundle_entry_apply = load_json(args.h_a_vendor_bundle_entry_apply)
    h_a_source_values_sheet = load_json(args.h_a_source_values_sheet)
    h_a_source_drop = load_json(args.h_a_source_drop)
    h_a_raw_csv_extraction = load_json(args.h_a_raw_csv_extraction)
    h_a_source_value_import = load_json(args.h_a_source_value_import)
    nhi_forward = load_json(args.nhi_forward)
    nhi_forward_source_values = load_json(args.nhi_forward_source_values)
    nhi_forward_source_drop = load_json(args.nhi_forward_source_drop)
    nhi_forward_source_template_pack = load_json(args.nhi_forward_source_template_pack)
    nhi_forward_raw_csv_extraction = load_json(args.nhi_forward_raw_csv_extraction)
    nhi_forward_source_import = load_json(args.nhi_forward_source_import)
    nhi_results = load_json(args.nhi_results)
    nhi_long_source_values = load_json(args.nhi_long_source_values)
    nhi_long_source_drop = load_json(args.nhi_long_source_drop)
    nhi_long_source_template_pack = load_json(args.nhi_long_source_template_pack)
    nhi_long_raw_csv_extraction = load_json(args.nhi_long_raw_csv_extraction)
    nhi_long_source_import = load_json(args.nhi_long_source_import)
    nhi_long_results = load_json(args.nhi_long_results)
    next_rows = load_json(args.next_measurements)
    ladder = load_json(args.variant_ladder)
    zrc_readiness = load_json(args.zrc_readiness)
    zrc_sentinel = load_json(args.zrc_sentinel)
    zrc_next = load_json(args.zrc_next_measurements)
    zrc_phase_a_source_values = load_json(args.zrc_phase_a_source_values)
    zrc_phase_a_source_drop = load_json(args.zrc_phase_a_source_drop)
    zrc_phase_a_source_template_pack = load_json(args.zrc_phase_a_source_template_pack)
    zrc_phase_a_vendor_bundle_entry_sheet = load_json(args.zrc_phase_a_vendor_bundle_entry_sheet)
    zrc_phase_a_vendor_bundle_entry_apply = load_json(args.zrc_phase_a_vendor_bundle_entry_apply)
    zrc_phase_a_raw_csv_extraction = load_json(args.zrc_phase_a_raw_csv_extraction)
    zrc_phase_a_source_import = load_json(args.zrc_phase_a_source_import)
    zrc_phase_a_service = load_json(args.zrc_phase_a_service)
    zrc_phase_a_chain = load_json(args.zrc_phase_a_chain)
    zrc_phase_a_delivery = load_json(args.zrc_phase_a_delivery)
    zrc_phase_a_vendor = load_json(args.zrc_phase_a_vendor)
    zrc_phase_a_rfq = load_json(args.zrc_phase_a_rfq)
    zrc_phase_a_rfq_outbox = load_json(args.zrc_phase_a_rfq_outbox)
    zrc_phase_a_quote_tracker = load_json(args.zrc_phase_a_quote_tracker)
    zrc_phase_a_rfq_send_confirmation_intake = load_json(args.zrc_phase_a_rfq_send_confirmation_intake)
    zrc_phase_a_rfq_send_confirmation_entry_sheet = load_json(args.zrc_phase_a_rfq_send_confirmation_entry_sheet)
    zrc_phase_a_rfq_send_confirmation_entry_apply = load_json(args.zrc_phase_a_rfq_send_confirmation_entry_apply)
    zrc_phase_a_rfq_send_log = load_json(args.zrc_phase_a_rfq_send_log)
    zrc_phase_a_rfq_reply_intake = load_json(args.zrc_phase_a_rfq_reply_intake)
    zrc_phase_a_rfq_reply_log = load_json(args.zrc_phase_a_rfq_reply_log)
    zrc_phase_a_contact_plan = load_json(args.zrc_phase_a_contact_plan)
    zrc_phase_a_rfq_dispatch_manifest = load_json(args.zrc_phase_a_rfq_dispatch_manifest)
    zrc_phase_a_rfq_dispatch_archive = load_json(args.zrc_phase_a_rfq_dispatch_archive)
    zrc_phase_a_rfq_reply_action_pack = load_json(args.zrc_phase_a_rfq_reply_action_pack)
    zrc_phase_a_rfq_send_cockpit = load_json(args.zrc_phase_a_rfq_send_cockpit)
    zrc_phase_a_quote_selection = load_json(args.zrc_phase_a_quote_selection)
    zrc_phase_a_execution_authorization = load_json(args.zrc_phase_a_execution_authorization)
    zrc_phase_a_execution_release = load_json(args.zrc_phase_a_execution_release)
    zrc_phase_a_vendor_return = load_json(args.zrc_phase_a_vendor_return)
    zrc_measurement_merge = load_json(args.zrc_measurement_merge)
    zrc_run_completeness = load_json(args.zrc_run_completeness)
    zrc_validation_results = load_json(args.zrc_validation_results)
    hybrid_measurement_plan = load_json(args.hybrid_measurement_plan)
    local_capture_pack = load_json(args.local_capture_pack)
    source_file_manifest = load_json(args.source_file_manifest)
    source_file_inventory = load_json(args.source_file_inventory)
    local_capture_preflight = load_json(args.local_capture_preflight)
    smoke_capture_tranche = load_json(args.smoke_capture_tranche)
    smoke_execution_queue = load_json(args.smoke_execution_queue)
    smoke_entry_sheet = load_json(args.smoke_entry_sheet)
    smoke_source_drop = load_json(args.smoke_source_drop)
    smoke_source_values_sheet = load_json(args.smoke_source_values_sheet)
    smoke_starter_readiness = load_json(args.smoke_starter_readiness)
    smoke_starter_execution_pack = load_json(args.smoke_starter_execution_pack)
    smoke_starter_template_pack = load_json(args.smoke_starter_template_pack)
    smoke_raw_csv_extraction = load_json(args.smoke_raw_csv_extraction)
    smoke_unstructured_intake = load_json(args.smoke_unstructured_intake)
    smoke_unstructured_review_values = load_json(args.smoke_unstructured_review_values)
    smoke_source_value_import = load_json(args.smoke_source_value_import)
    smoke_entry_apply = load_json(args.smoke_entry_apply)
    smoke_capture_preflight = load_json(args.smoke_capture_preflight)
    smoke_rehearsal = load_json(args.smoke_rehearsal)
    first_wave_rfq_dispatch_cockpit = load_json(args.first_wave_rfq_dispatch_cockpit)
    first_wave_post_dispatch = load_json(args.first_wave_post_dispatch)
    second_wave_candidate_queue = load_json(args.second_wave_candidate_queue)
    second_wave_scope_lock_pack = load_json(args.second_wave_scope_lock_pack)
    top = top_item(ranking)
    bypass_summary = portfolio_bypass.get("summary", {})
    nhi_audit = candidate_audit(claim, "limina_nhi_pedot_laminin_v0_1")
    zrc_merge_stats = zrc_measurement_merge.get("stats", {})
    zrc_result_summary = zrc_validation_results.get("summary", {})
    hybrid_summary = hybrid_measurement_plan.get("summary", {})
    hybrid_routes = hybrid_summary.get("route_totals", {})
    hybrid_status = hybrid_measurement_plan.get("status", "unknown")
    hybrid_inhouse = hybrid_routes.get("inhouse_ready", {}).get("row_count", 0)
    hybrid_outsource = hybrid_routes.get("outsourced_preferred", {}).get("row_count", 0)
    hybrid_provenance = hybrid_routes.get("supplier_or_build_record", {}).get("row_count", 0)
    hybrid_total = hybrid_summary.get("row_count", 0)
    local_capture_summary = local_capture_pack.get("summary", {})
    local_capture_status = local_capture_pack.get("status", "unknown")
    local_capture_tasks = local_capture_summary.get("task_count", 0)
    local_capture_local = local_capture_summary.get("ready_to_collect_local_rows", 0)
    local_capture_outsource = local_capture_summary.get("outsourced_preferred_rows", 0)
    local_capture_provenance = local_capture_summary.get("ready_to_record_provenance_rows", 0)
    source_file_manifest_status = source_file_manifest.get("status", "unknown")
    source_file_allowed_roots = len(source_file_manifest.get("allowed_roots", []))
    source_file_expected_classes = len(source_file_manifest.get("expected_source_classes", []))
    source_file_inventory_summary = source_file_inventory.get("summary", {})
    source_file_inventory_status = source_file_inventory.get("status", "unknown")
    source_file_inventory_files = source_file_inventory_summary.get("file_count", 0)
    source_file_inventory_refs = source_file_inventory_summary.get("source_reference_count", 0)
    source_file_inventory_capture_refs = source_file_inventory_summary.get("capture_template_reference_count", 0)
    source_file_inventory_source_value_refs = source_file_inventory_summary.get("filled_source_value_reference_count", 0)
    source_file_inventory_missing = source_file_inventory_summary.get("missing_reference_count", 0)
    source_file_inventory_unreferenced = source_file_inventory_summary.get("unreferenced_file_count", 0)
    local_preflight_issue_counts = local_capture_preflight.get("issue_counts", {})
    local_preflight_status = local_capture_preflight.get("status", "unknown")
    local_preflight_ready = bool(local_capture_preflight.get("preflight_ready"))
    local_preflight_filled = local_capture_preflight.get("filled_task_count", 0)
    local_preflight_pending = local_capture_preflight.get("pending_task_count", 0)
    local_preflight_errors = local_preflight_issue_counts.get("error", 0)
    local_preflight_warnings = local_preflight_issue_counts.get("warning", 0)
    smoke_summary = smoke_capture_tranche.get("summary", {})
    smoke_status = smoke_capture_tranche.get("status", "unknown")
    smoke_tasks = smoke_summary.get("task_count", 0)
    smoke_local_or_record = smoke_summary.get("local_or_record_tasks", 0)
    smoke_outsource = smoke_summary.get("outsourced_preferred_tasks", 0)
    smoke_queue_summary = smoke_execution_queue.get("summary", {})
    smoke_queue_status = smoke_execution_queue.get("status", "unknown")
    smoke_queue_rows = smoke_queue_summary.get("queue_row_count", 0)
    smoke_queue_h_a_rows = smoke_queue_summary.get("h_a_rows", 0)
    smoke_queue_zrc_rows = smoke_queue_summary.get("zrc_rows", 0)
    smoke_queue_awaiting = smoke_queue_summary.get("awaiting_value_rows", 0)
    smoke_queue_source_ready = smoke_queue_summary.get("source_ready_rows", 0)
    smoke_entry_sheet_summary = smoke_entry_sheet.get("summary", {})
    smoke_entry_sheet_status = smoke_entry_sheet.get("status", "unknown")
    smoke_entry_sheet_rows = smoke_entry_sheet_summary.get("entry_rows", 0)
    smoke_entry_sheet_ready = smoke_entry_sheet_summary.get("ready_to_apply_rows", 0)
    smoke_entry_sheet_filled = smoke_entry_sheet_summary.get("filled_value_rows", 0)
    smoke_source_drop_summary = smoke_source_drop.get("summary", {})
    smoke_source_drop_status = smoke_source_drop.get("status", "unknown")
    smoke_source_drop_planned = smoke_source_drop_summary.get("planned_source_file_count", 0)
    smoke_source_drop_dirs = smoke_source_drop_summary.get("source_dir_count", 0)
    smoke_source_drop_existing = smoke_source_drop_summary.get("existing_source_file_count", 0)
    smoke_source_drop_missing = smoke_source_drop_summary.get("missing_source_file_count", 0)
    smoke_source_values_sheet_summary = smoke_source_values_sheet.get("summary", {})
    smoke_source_values_sheet_status = smoke_source_values_sheet.get("status", "unknown")
    smoke_source_values_sheet_rows = smoke_source_values_sheet_summary.get("source_value_rows", 0)
    smoke_source_values_sheet_starter = smoke_source_values_sheet_summary.get("starter_batch_rows", 0)
    smoke_source_values_sheet_filled = smoke_source_values_sheet_summary.get("filled_value_rows", 0)
    smoke_source_values_sheet_import_ready = smoke_source_values_sheet_summary.get("import_ready_rows", 0)
    smoke_starter_readiness_summary = smoke_starter_readiness.get("summary", {})
    smoke_starter_readiness_status = smoke_starter_readiness.get("status", "unknown")
    smoke_starter_rows = smoke_starter_readiness_summary.get("starter_rows", 0)
    smoke_starter_ready = smoke_starter_readiness_summary.get("ready_for_import_rows", 0)
    smoke_starter_blocked = smoke_starter_readiness_summary.get("blocked_rows", 0)
    smoke_starter_execution_pack_summary = smoke_starter_execution_pack.get("summary", {})
    smoke_starter_execution_pack_status = smoke_starter_execution_pack.get("status", "unknown")
    smoke_starter_execution_pack_rows = smoke_starter_execution_pack_summary.get("starter_rows", 0)
    smoke_starter_execution_pack_dirs = smoke_starter_execution_pack_summary.get("source_dir_count", 0)
    smoke_starter_execution_pack_existing = smoke_starter_execution_pack_summary.get("source_file_exists_rows", 0)
    smoke_starter_template_pack_summary = smoke_starter_template_pack.get("summary", {})
    smoke_starter_template_pack_status = smoke_starter_template_pack.get("status", "unknown")
    smoke_starter_template_pack_rows = smoke_starter_template_pack_summary.get("starter_rows", 0)
    smoke_starter_template_pack_templates = smoke_starter_template_pack_summary.get("source_class_template_count", 0)
    smoke_raw_csv_extraction_summary = smoke_raw_csv_extraction.get("summary", {})
    smoke_raw_csv_extraction_status = smoke_raw_csv_extraction.get("status", "unknown")
    smoke_raw_csv_extraction_files = smoke_raw_csv_extraction_summary.get("raw_csv_found", 0)
    smoke_raw_csv_extraction_rows = smoke_raw_csv_extraction_summary.get("extracted_rows", 0)
    smoke_raw_csv_extraction_errors = smoke_raw_csv_extraction_summary.get("error_count", 0)
    smoke_unstructured_intake_summary = smoke_unstructured_intake.get("summary", {})
    smoke_unstructured_intake_status = smoke_unstructured_intake.get("status", "unknown")
    smoke_unstructured_intake_rows = smoke_unstructured_intake_summary.get("unstructured_plan_rows", 0)
    smoke_unstructured_intake_ready = smoke_unstructured_intake_summary.get("ready_for_value_extraction", 0)
    smoke_unstructured_intake_missing = smoke_unstructured_intake_summary.get("missing_source_files", 0)
    smoke_unstructured_intake_invalid = smoke_unstructured_intake_summary.get("invalid_source_files", 0)
    smoke_unstructured_review_summary = smoke_unstructured_review_values.get("summary", {})
    smoke_unstructured_review_status = smoke_unstructured_review_values.get("status", "unknown")
    smoke_unstructured_review_rows = smoke_unstructured_review_summary.get("review_rows", 0)
    smoke_unstructured_review_ready_sources = smoke_unstructured_review_summary.get("ready_source_rows", 0)
    smoke_unstructured_review_filled = smoke_unstructured_review_summary.get("filled_value_rows", 0)
    smoke_unstructured_review_import_ready = smoke_unstructured_review_summary.get("import_ready_rows", 0)
    smoke_unstructured_review_invalid = smoke_unstructured_review_summary.get("invalid_source_rows", 0)
    smoke_source_value_import_summary = smoke_source_value_import.get("summary", {})
    smoke_source_value_import_status = smoke_source_value_import.get("status", "unknown")
    smoke_source_value_import_files = smoke_source_value_import_summary.get("source_value_files", 0)
    smoke_source_value_import_rows = smoke_source_value_import_summary.get("source_value_rows", 0)
    smoke_source_value_import_imported = smoke_source_value_import_summary.get("imported_rows", 0)
    smoke_source_value_import_errors = smoke_source_value_import_summary.get("error_count", 0)
    smoke_entry_apply_summary = smoke_entry_apply.get("summary", {})
    smoke_entry_apply_status = smoke_entry_apply.get("status", "unknown")
    smoke_entry_apply_applied = smoke_entry_apply_summary.get("applied_values", 0)
    smoke_entry_apply_errors = smoke_entry_apply_summary.get("error_count", 0)
    smoke_preflight_issue_counts = smoke_capture_preflight.get("issue_counts", {})
    smoke_preflight_status = smoke_capture_preflight.get("status", "unknown")
    smoke_preflight_ready = bool(smoke_capture_preflight.get("preflight_ready"))
    smoke_preflight_filled = smoke_capture_preflight.get("filled_task_count", 0)
    smoke_preflight_pending = smoke_capture_preflight.get("pending_task_count", 0)
    smoke_preflight_errors = smoke_preflight_issue_counts.get("error", 0)
    smoke_preflight_warnings = smoke_preflight_issue_counts.get("warning", 0)
    smoke_rehearsal_issue_counts = smoke_rehearsal.get("issue_counts", {})
    smoke_rehearsal_status = smoke_rehearsal.get("status", "unknown")
    smoke_rehearsal_preflight_status = smoke_rehearsal.get("preflight_status", "unknown")
    smoke_rehearsal_ready = bool(smoke_rehearsal.get("preflight_ready"))
    smoke_rehearsal_filled = smoke_rehearsal.get("filled_task_count", 0)
    smoke_rehearsal_pending = smoke_rehearsal.get("pending_task_count", 0)
    smoke_rehearsal_errors = smoke_rehearsal_issue_counts.get("error", 0)
    smoke_rehearsal_warnings = smoke_rehearsal_issue_counts.get("warning", 0)
    smoke_rehearsal_h_a_qc = smoke_rehearsal.get("h_a_qc_status", "-")
    smoke_rehearsal_zrc_validation = smoke_rehearsal.get("zrc_validation_status", "-")
    first_wave_rfq_dispatch_cockpit_summary = first_wave_rfq_dispatch_cockpit.get("summary", {})
    first_wave_post_dispatch_cockpit_summary = first_wave_post_dispatch.get("first_wave_cockpit_summary", {})
    second_wave_candidate_queue_summary = second_wave_candidate_queue.get("summary", {})
    second_wave_scope_lock_pack_summary = second_wave_scope_lock_pack.get("summary", {})
    zrc_phase_a_source_values_summary = zrc_phase_a_source_values.get("summary", {})
    zrc_phase_a_source_drop_summary = zrc_phase_a_source_drop.get("summary", {})
    zrc_phase_a_source_template_pack_summary = zrc_phase_a_source_template_pack.get("summary", {})
    zrc_phase_a_vendor_bundle_entry_sheet_summary = zrc_phase_a_vendor_bundle_entry_sheet.get("summary", {})
    zrc_phase_a_vendor_bundle_entry_apply_summary = zrc_phase_a_vendor_bundle_entry_apply.get("summary", {})
    zrc_phase_a_raw_csv_extraction_summary = zrc_phase_a_raw_csv_extraction.get("summary", {})
    zrc_phase_a_source_import_summary = zrc_phase_a_source_import.get("summary", {})
    zrc_phase_a_dispatch_manifest_summary = zrc_phase_a_rfq_dispatch_manifest.get("summary", {})
    zrc_phase_a_dispatch_archive_summary = zrc_phase_a_rfq_dispatch_archive.get("summary", {})
    zrc_phase_a_send_confirmation_entry_sheet_summary = zrc_phase_a_rfq_send_confirmation_entry_sheet.get("summary", {})
    zrc_phase_a_send_confirmation_entry_apply_summary = zrc_phase_a_rfq_send_confirmation_entry_apply.get("summary", {})
    zrc_phase_a_reply_action_summary = zrc_phase_a_rfq_reply_action_pack.get("summary", {})
    zrc_phase_a_send_cockpit_summary = zrc_phase_a_rfq_send_cockpit.get("summary", {})
    nhi_forward_source_values_summary = nhi_forward_source_values.get("summary", {})
    nhi_forward_source_drop_summary = nhi_forward_source_drop.get("summary", {})
    nhi_forward_source_template_pack_summary = nhi_forward_source_template_pack.get("summary", {})
    nhi_forward_raw_csv_extraction_summary = nhi_forward_raw_csv_extraction.get("summary", {})
    nhi_forward_source_import_summary = nhi_forward_source_import.get("summary", {})
    nhi_results_summary = nhi_results.get("summary", {})
    nhi_long_source_values_summary = nhi_long_source_values.get("summary", {})
    nhi_long_source_drop_summary = nhi_long_source_drop.get("summary", {})
    nhi_long_source_template_pack_summary = nhi_long_source_template_pack.get("summary", {})
    nhi_long_raw_csv_extraction_summary = nhi_long_raw_csv_extraction.get("summary", {})
    nhi_long_source_import_summary = nhi_long_source_import.get("summary", {})
    nhi_long_results_summary = nhi_long_results.get("summary", {})
    h_a_source_drop_summary = h_a_source_drop.get("summary", {})
    h_a_source_drop_status = h_a_source_drop.get("status", "unknown")
    h_a_source_drop_planned = h_a_source_drop_summary.get("planned_source_file_count", 0)
    h_a_source_drop_dirs = h_a_source_drop_summary.get("source_dir_count", 0)
    h_a_source_drop_existing = h_a_source_drop_summary.get("existing_source_file_count", 0)
    h_a_source_drop_missing = h_a_source_drop_summary.get("missing_source_file_count", 0)
    h_a_raw_csv_extraction_summary = h_a_raw_csv_extraction.get("summary", {})
    h_a_raw_csv_extraction_status = h_a_raw_csv_extraction.get("status", "unknown")
    h_a_raw_csv_extraction_files = h_a_raw_csv_extraction_summary.get("raw_csv_found", 0)
    h_a_raw_csv_extraction_rows = h_a_raw_csv_extraction_summary.get("extracted_rows", 0)
    h_a_raw_csv_extraction_errors = h_a_raw_csv_extraction_summary.get("error_count", 0)
    h_a_rfq_eml_summary = h_a_rfq_eml_drafts.get("summary", {})
    h_a_rfq_eml_integrity_summary = h_a_rfq_eml_integrity.get("summary", {})
    h_a_send_action_summary = h_a_rfq_send_action_pack.get("summary", {})
    h_a_dispatch_manifest_summary = h_a_rfq_dispatch_manifest.get("summary", {})
    h_a_contact_source_audit_summary = h_a_contact_source_audit.get("summary", {})
    h_a_send_confirmation_entry_sheet_summary = h_a_rfq_send_confirmation_entry_sheet.get("summary", {})
    h_a_send_confirmation_entry_apply_summary = h_a_rfq_send_confirmation_entry_apply.get("summary", {})
    h_a_reply_action_summary = h_a_rfq_reply_action_pack.get("summary", {})
    h_a_send_cockpit_summary = h_a_rfq_send_cockpit.get("summary", {})
    h_a_dispatch_archive_summary = h_a_rfq_dispatch_archive.get("summary", {})
    h_a_vendor_return_bundle = h_a_vendor_return.get("bundle_entry_sheet", {})
    h_a_vendor_bundle_entry_sheet_summary = h_a_vendor_bundle_entry_sheet.get("summary", {})
    h_a_vendor_bundle_entry_summary = h_a_vendor_bundle_entry_apply.get("summary", {})

    mission_state, state_reason, actions, gaps = build_actions(
        claim,
        ranking,
        h_a,
        h_a_merge,
        h_a_bench,
        h_a_qc,
        h_a_service,
        h_a_chain,
        h_a_sample_submission,
        h_a_split_scope,
        h_a_vendor,
        h_a_rfq,
        h_a_rfq_outbox,
        h_a_rfq_eml_drafts,
        h_a_rfq_eml_integrity,
        h_a_quote_tracker,
        h_a_rfq_send_action_pack,
        h_a_rfq_dispatch_manifest,
        h_a_rfq_reply_action_pack,
        h_a_rfq_send_cockpit,
        h_a_rfq_dispatch_archive,
        h_a_rfq_send_confirmation_intake,
        h_a_rfq_send_confirmation_entry_sheet,
        h_a_rfq_send_confirmation_entry_apply,
        h_a_rfq_reply_intake,
        h_a_rfq_send_log,
        h_a_rfq_reply_log,
        h_a_contact_plan,
        h_a_contact_source_audit,
        h_a_quote_selection,
        h_a_vendor_return,
        h_a_vendor_bundle_entry_sheet,
        h_a_vendor_bundle_entry_apply,
        next_rows,
        ladder,
    )
    nhi_forward_gaps = [
        f"NHI-PEDOT H-B/H-C package: {nhi_forward.get('status', 'unknown')}; rows={nhi_forward.get('row_count', 0)}",
        f"NHI-PEDOT H-B/H-C source values: {nhi_forward_source_values.get('status', 'unknown')}; rows={nhi_forward_source_values_summary.get('source_value_rows', 0)}; filled={nhi_forward_source_values_summary.get('filled_value_rows', 0)}; import_ready={nhi_forward_source_values_summary.get('import_ready_rows', 0)}",
        f"NHI-PEDOT H-B/H-C source drop plan: {nhi_forward_source_drop.get('status', 'unknown')}; planned_files={nhi_forward_source_drop_summary.get('planned_source_file_count', 0)}; dirs={nhi_forward_source_drop_summary.get('source_dir_count', 0)}; existing_files={nhi_forward_source_drop_summary.get('existing_source_file_count', 0)}; missing_files={nhi_forward_source_drop_summary.get('missing_source_file_count', 0)}",
        f"NHI-PEDOT H-B/H-C source file templates: {nhi_forward_source_template_pack.get('status', 'unknown')}; templates={nhi_forward_source_template_pack_summary.get('source_class_template_count', 0)}; target_files={nhi_forward_source_template_pack_summary.get('target_source_file_count', 0)}",
        f"NHI-PEDOT H-B/H-C raw CSV extraction: {nhi_forward_raw_csv_extraction.get('status', 'unknown')}; files={nhi_forward_raw_csv_extraction_summary.get('raw_csv_found', 0)}; rows={nhi_forward_raw_csv_extraction_summary.get('extracted_rows', 0)}; errors={nhi_forward_raw_csv_extraction_summary.get('error_count', 0)}",
        f"NHI-PEDOT H-B/H-C source import: {nhi_forward_source_import.get('status', 'unknown')}; rows={nhi_forward_source_import_summary.get('source_value_rows', 0)}; imported={nhi_forward_source_import_summary.get('imported_rows', 0)}; errors={nhi_forward_source_import_summary.get('error_count', 0)}",
        f"NHI-PEDOT coupon results: {nhi_results_summary.get('status', 'unknown')}; rows={nhi_results_summary.get('rows', 0)}",
        f"NHI-PEDOT long-duration source values: {nhi_long_source_values.get('status', 'unknown')}; rows={nhi_long_source_values_summary.get('source_value_rows', 0)}; filled={nhi_long_source_values_summary.get('filled_value_rows', 0)}; import_ready={nhi_long_source_values_summary.get('import_ready_rows', 0)}",
        f"NHI-PEDOT long-duration source drop plan: {nhi_long_source_drop.get('status', 'unknown')}; planned_files={nhi_long_source_drop_summary.get('planned_source_file_count', 0)}; dirs={nhi_long_source_drop_summary.get('source_dir_count', 0)}; existing_files={nhi_long_source_drop_summary.get('existing_source_file_count', 0)}; missing_files={nhi_long_source_drop_summary.get('missing_source_file_count', 0)}",
        f"NHI-PEDOT long-duration source file templates: {nhi_long_source_template_pack.get('status', 'unknown')}; templates={nhi_long_source_template_pack_summary.get('source_class_template_count', 0)}; target_files={nhi_long_source_template_pack_summary.get('target_source_file_count', 0)}",
        f"NHI-PEDOT long-duration raw CSV extraction: {nhi_long_raw_csv_extraction.get('status', 'unknown')}; files={nhi_long_raw_csv_extraction_summary.get('raw_csv_found', 0)}; rows={nhi_long_raw_csv_extraction_summary.get('extracted_rows', 0)}; errors={nhi_long_raw_csv_extraction_summary.get('error_count', 0)}",
        f"NHI-PEDOT long-duration source import: {nhi_long_source_import.get('status', 'unknown')}; rows={nhi_long_source_import_summary.get('source_value_rows', 0)}; imported={nhi_long_source_import_summary.get('imported_rows', 0)}; errors={nhi_long_source_import_summary.get('error_count', 0)}",
        f"NHI-PEDOT long-duration results: {nhi_long_results_summary.get('status', 'unknown')}; rows={nhi_long_results_summary.get('rows', 0)}",
    ]
    zrc_gaps = [
        f"ZRC-ND readiness: {zrc_readiness.get('readiness', 'unknown')}; suitable={str(bool(zrc_readiness.get('suitable'))).lower()}",
        f"ZRC-ND Phase A sentinel: {zrc_sentinel.get('status', 'unknown')}; rows={zrc_sentinel.get('rows', 0)}",
        f"ZRC-ND next measurements: {zrc_next.get('status', 'unknown')}; recommended_rows={len(zrc_next.get('recommended_rows', []))}",
        f"ZRC-ND Phase A source values: {zrc_phase_a_source_values.get('status', 'unknown')}; rows={zrc_phase_a_source_values_summary.get('source_value_rows', 0)}; filled={zrc_phase_a_source_values_summary.get('filled_value_rows', 0)}; import_ready={zrc_phase_a_source_values_summary.get('import_ready_rows', 0)}",
        f"ZRC-ND Phase A source drop plan: {zrc_phase_a_source_drop.get('status', 'unknown')}; planned_files={zrc_phase_a_source_drop_summary.get('planned_source_file_count', 0)}; dirs={zrc_phase_a_source_drop_summary.get('source_dir_count', 0)}; existing_files={zrc_phase_a_source_drop_summary.get('existing_source_file_count', 0)}; missing_files={zrc_phase_a_source_drop_summary.get('missing_source_file_count', 0)}",
        f"ZRC-ND Phase A source file templates: {zrc_phase_a_source_template_pack.get('status', 'unknown')}; templates={zrc_phase_a_source_template_pack_summary.get('source_class_template_count', 0)}; target_files={zrc_phase_a_source_template_pack_summary.get('target_source_file_count', 0)}",
        f"ZRC-ND Phase A vendor bundle entry sheet: {zrc_phase_a_vendor_bundle_entry_sheet.get('status', 'unknown')}; bundles={zrc_phase_a_vendor_bundle_entry_sheet_summary.get('bundle_rows', 0)}; ready={zrc_phase_a_vendor_bundle_entry_sheet_summary.get('ready_to_apply_rows', 0)}; blocked={zrc_phase_a_vendor_bundle_entry_sheet_summary.get('blocked_rows', 0)}",
        f"ZRC-ND Phase A vendor bundle entry apply: {zrc_phase_a_vendor_bundle_entry_apply.get('status', 'unknown')}; apply_rows={zrc_phase_a_vendor_bundle_entry_apply_summary.get('apply_rows', 0)}; bundles={zrc_phase_a_vendor_bundle_entry_apply_summary.get('applied_bundles', 0)}; source_rows={zrc_phase_a_vendor_bundle_entry_apply_summary.get('applied_source_value_rows', 0)}; errors={zrc_phase_a_vendor_bundle_entry_apply_summary.get('error_count', 0)}",
        f"ZRC-ND Phase A raw CSV extraction: {zrc_phase_a_raw_csv_extraction.get('status', 'unknown')}; files={zrc_phase_a_raw_csv_extraction_summary.get('raw_csv_found', 0)}; rows={zrc_phase_a_raw_csv_extraction_summary.get('extracted_rows', 0)}; errors={zrc_phase_a_raw_csv_extraction_summary.get('error_count', 0)}",
        f"ZRC-ND Phase A source import: {zrc_phase_a_source_import.get('status', 'unknown')}; rows={zrc_phase_a_source_import_summary.get('source_value_rows', 0)}; imported={zrc_phase_a_source_import_summary.get('imported_rows', 0)}; errors={zrc_phase_a_source_import_summary.get('error_count', 0)}",
        f"ZRC-ND Phase A service request: {zrc_phase_a_service.get('status', 'unknown')}; runs={zrc_phase_a_service.get('requested_matrix', {}).get('runs', 0)}",
        f"ZRC-ND Phase A sample handoff: {zrc_phase_a_chain.get('status', 'unknown')}; labels={zrc_phase_a_chain.get('sample_label_count', 0)}; custody_rows={zrc_phase_a_chain.get('chain_of_custody_row_count', 0)}",
        f"ZRC-ND Phase A delivery package: {zrc_phase_a_delivery.get('status', 'unknown')}; missing_files={len(zrc_phase_a_delivery.get('missing_required_file_ids', []))}",
        f"ZRC-ND Phase A vendor outreach: {zrc_phase_a_vendor.get('status', 'unknown')}; first_wave_contacts={len(zrc_phase_a_vendor.get('first_wave', []))}",
        f"ZRC-ND Phase A RFQ packet: {zrc_phase_a_rfq.get('status', 'unknown')}",
        f"ZRC-ND Phase A RFQ outbox: {zrc_phase_a_rfq_outbox.get('status', 'unknown')}; ready_to_send={zrc_phase_a_rfq_outbox.get('ready_to_send_count', 0)} of {zrc_phase_a_rfq_outbox.get('quote_request_count', 0)}",
        f"ZRC-ND Phase A quote tracker: {zrc_phase_a_quote_tracker.get('status', 'unknown')}",
        f"ZRC-ND Phase A RFQ send confirmation intake: {zrc_phase_a_rfq_send_confirmation_intake.get('status', 'unknown')}; files={zrc_phase_a_rfq_send_confirmation_intake.get('row_count', 0)}; applied={zrc_phase_a_rfq_send_confirmation_intake.get('applied_rows', 0)}; needs_review={zrc_phase_a_rfq_send_confirmation_intake.get('needs_review_rows', 0)}; bundle_matched={zrc_phase_a_rfq_send_confirmation_intake.get('bundle_hash_matched_rows', 0)}",
        f"ZRC-ND Phase A RFQ send confirmation entry sheet: {zrc_phase_a_rfq_send_confirmation_entry_sheet.get('status', 'unknown')}; rows={zrc_phase_a_send_confirmation_entry_sheet_summary.get('entry_rows', 0)}; source_files={zrc_phase_a_send_confirmation_entry_sheet_summary.get('source_file_present_rows', 0)}; ready={zrc_phase_a_send_confirmation_entry_sheet_summary.get('ready_to_apply_rows', 0)}; blocked={zrc_phase_a_send_confirmation_entry_sheet_summary.get('blocked_rows', 0)}",
        f"ZRC-ND Phase A RFQ send confirmation entry apply: {zrc_phase_a_rfq_send_confirmation_entry_apply.get('status', 'unknown')}; apply_rows={zrc_phase_a_send_confirmation_entry_apply_summary.get('apply_rows', 0)}; applied={zrc_phase_a_send_confirmation_entry_apply_summary.get('applied_rows', 0)}; blocked={zrc_phase_a_send_confirmation_entry_apply_summary.get('blocked_rows', 0)}",
        f"ZRC-ND Phase A RFQ send log: {zrc_phase_a_rfq_send_log.get('status', 'unknown')}; rows={zrc_phase_a_rfq_send_log.get('row_count', 0)}; sent={zrc_phase_a_rfq_send_log.get('sent_rows', 0)}; valid={zrc_phase_a_rfq_send_log.get('valid_sent_rows', 0)}; applied_dates={zrc_phase_a_rfq_send_log.get('applied_tracker_contact_dates', 0)}; errors={zrc_phase_a_rfq_send_log.get('error_count', 0)}",
        f"ZRC-ND Phase A RFQ reply intake: {zrc_phase_a_rfq_reply_intake.get('status', 'unknown')}; files={zrc_phase_a_rfq_reply_intake.get('row_count', 0)}; applied={zrc_phase_a_rfq_reply_intake.get('applied_rows', 0)}; needs_review={zrc_phase_a_rfq_reply_intake.get('needs_manual_review_rows', 0)}; needs_verified_send={zrc_phase_a_rfq_reply_intake.get('needs_verified_send_rows', 0)}",
        f"ZRC-ND Phase A RFQ reply log: {zrc_phase_a_rfq_reply_log.get('status', 'unknown')}; rows={zrc_phase_a_rfq_reply_log.get('row_count', 0)}; received={zrc_phase_a_rfq_reply_log.get('received_rows', 0)}; valid={zrc_phase_a_rfq_reply_log.get('valid_reply_rows', 0)}; applied_fields={zrc_phase_a_rfq_reply_log.get('applied_tracker_field_updates', 0)}; errors={zrc_phase_a_rfq_reply_log.get('error_count', 0)}",
        f"ZRC-ND Phase A vendor contact plan: {zrc_phase_a_contact_plan.get('status', 'unknown')}; ready_first_wave={zrc_phase_a_contact_plan.get('status_counts', {}).get('ready_to_send', 0)}; standby_second_wave={zrc_phase_a_contact_plan.get('status_counts', {}).get('standby_secondary_wave', 0)}; total={zrc_phase_a_contact_plan.get('row_count', 0)}",
        f"ZRC-ND Phase A RFQ dispatch manifest: {zrc_phase_a_rfq_dispatch_manifest.get('status', 'unknown')}; rows={zrc_phase_a_dispatch_manifest_summary.get('dispatch_rows', 0)}; ready={zrc_phase_a_dispatch_manifest_summary.get('ready_for_manual_dispatch_rows', 0)}; blocked={zrc_phase_a_dispatch_manifest_summary.get('blocked_rows', 0)}",
        f"ZRC-ND Phase A RFQ dispatch archive: {zrc_phase_a_rfq_dispatch_archive.get('status', 'unknown')}; files={zrc_phase_a_dispatch_archive_summary.get('included_files', 0)}; missing={zrc_phase_a_dispatch_archive_summary.get('missing_files', 0)}; hash_mismatches={zrc_phase_a_dispatch_archive_summary.get('hash_mismatch_files', 0)}; archive={zrc_phase_a_rfq_dispatch_archive.get('generated_artifacts', {}).get('archive', '')}",
        f"ZRC-ND Phase A RFQ reply action pack: {zrc_phase_a_rfq_reply_action_pack.get('status', 'unknown')}; rows={zrc_phase_a_reply_action_summary.get('action_rows', 0)}; waiting_send={zrc_phase_a_reply_action_summary.get('waiting_for_send_rows', 0)}; awaiting_reply={zrc_phase_a_reply_action_summary.get('awaiting_reply_rows', 0)}; ready_apply={zrc_phase_a_reply_action_summary.get('ready_for_reply_log_apply_rows', 0)}",
        f"ZRC-ND Phase A RFQ send cockpit: {zrc_phase_a_rfq_send_cockpit.get('status', 'unknown')}; rows={zrc_phase_a_send_cockpit_summary.get('vendor_rows', 0)}; ready={zrc_phase_a_send_cockpit_summary.get('ready_to_use_rows', 0)}; confirmations={zrc_phase_a_send_cockpit_summary.get('confirmation_files_present', 0)}; replies={zrc_phase_a_send_cockpit_summary.get('reply_files_present', 0)}; html={zrc_phase_a_rfq_send_cockpit.get('generated_artifacts', {}).get('html', '')}",
        f"ZRC-ND Phase A quote selection: {zrc_phase_a_quote_selection.get('status', 'unknown')}; replies={zrc_phase_a_quote_selection.get('reply_count', 0)}; source_backed_replies={zrc_phase_a_quote_selection.get('source_backed_reply_count', 0)}; shortlist={zrc_phase_a_quote_selection.get('shortlist_count', 0)}",
        f"ZRC-ND Phase A execution authorization log: {zrc_phase_a_execution_authorization.get('status', 'unknown')}; rows={zrc_phase_a_execution_authorization.get('row_count', 0)}; valid={zrc_phase_a_execution_authorization.get('valid_authorization_rows', 0)}; errors={zrc_phase_a_execution_authorization.get('error_count', 0)}",
        f"ZRC-ND Phase A execution release audit: {zrc_phase_a_execution_release.get('status', 'unknown')}; ready={str(bool(zrc_phase_a_execution_release.get('ready_for_execution_authorization'))).lower()}; released={str(bool(zrc_phase_a_execution_release.get('released_for_execution'))).lower()}; blockers={zrc_phase_a_execution_release.get('blocker_count', 0)}; authorization_blockers={zrc_phase_a_execution_release.get('authorization_blocker_count', 0)}",
        f"ZRC-ND Phase A vendor return intake: {zrc_phase_a_vendor_return.get('status', 'unknown')}; rows={zrc_phase_a_vendor_return.get('phase_a_measurements', {}).get('row_count', 0)}; export_files={zrc_phase_a_vendor_return.get('instrument_export_file_count', 0)}",
        f"ZRC-ND measurement merge: {zrc_measurement_merge.get('status', 'unknown')}; inserted={zrc_merge_stats.get('inserted', 0)}; updated={zrc_merge_stats.get('updated', 0)}; output_rows={zrc_merge_stats.get('total', 0)}",
        f"ZRC-ND run completeness: {zrc_run_completeness.get('status', 'unknown')}; measured_known={zrc_run_completeness.get('measured_known_rows', 0)} of {zrc_run_completeness.get('planned_rows', 0)}",
        f"ZRC-ND validation results: {zrc_result_summary.get('status', 'unknown')}; rows={zrc_result_summary.get('rows', 0)}",
    ]
    hybrid_gaps = [
        f"First-wave RFQ dispatch cockpit: {first_wave_rfq_dispatch_cockpit.get('status', 'unknown')}; rows={first_wave_rfq_dispatch_cockpit_summary.get('vendor_rows', 0)}; ready={first_wave_rfq_dispatch_cockpit_summary.get('ready_to_send_rows', 0)}; confirmations={first_wave_rfq_dispatch_cockpit_summary.get('confirmation_files_present', 0)}; replies={first_wave_rfq_dispatch_cockpit_summary.get('reply_files_present', 0)}",
        f"First-wave post-dispatch processing: {first_wave_post_dispatch.get('status', 'unknown')}; failed_commands={len(first_wave_post_dispatch.get('failed_command_ids', []))}; confirmations={first_wave_post_dispatch_cockpit_summary.get('confirmation_files_present', 0)}; replies={first_wave_post_dispatch_cockpit_summary.get('reply_files_present', 0)}",
        f"Second-wave candidate queue: {second_wave_candidate_queue.get('status', 'unknown')}; rows={second_wave_candidate_queue_summary.get('queue_rows', 0)}; ready_scope_lock={second_wave_candidate_queue_summary.get('ready_scope_lock_rows', 0)}; watch={second_wave_candidate_queue_summary.get('watch_rows', 0)}; hold={second_wave_candidate_queue_summary.get('hold_rows', 0)}",
        f"Second-wave scope-lock pack: {second_wave_scope_lock_pack.get('status', 'unknown')}; ready_candidates={second_wave_scope_lock_pack_summary.get('ready_candidate_count', 0)}; tasks={second_wave_scope_lock_pack_summary.get('task_count', 0)}; source_classes={second_wave_scope_lock_pack_summary.get('source_file_class_count', 0)}; claim_evidence_created={str(bool(second_wave_scope_lock_pack_summary.get('claim_evidence_created'))).lower()}",
        f"H-A RFQ send log: {h_a_rfq_send_log.get('status', 'unknown')}; rows={h_a_rfq_send_log.get('row_count', 0)}; sent={h_a_rfq_send_log.get('sent_rows', 0)}; valid={h_a_rfq_send_log.get('valid_sent_rows', 0)}; applied_dates={h_a_rfq_send_log.get('applied_tracker_contact_dates', 0)}; errors={h_a_rfq_send_log.get('error_count', 0)}",
        f"H-A RFQ reply log: {h_a_rfq_reply_log.get('status', 'unknown')}; rows={h_a_rfq_reply_log.get('row_count', 0)}; received={h_a_rfq_reply_log.get('received_rows', 0)}; valid={h_a_rfq_reply_log.get('valid_reply_rows', 0)}; applied_fields={h_a_rfq_reply_log.get('applied_tracker_field_updates', 0)}; errors={h_a_rfq_reply_log.get('error_count', 0)}",
        f"H-A execution authorization log: {h_a_execution_authorization.get('status', 'unknown')}; rows={h_a_execution_authorization.get('row_count', 0)}; valid={h_a_execution_authorization.get('valid_authorization_rows', 0)}; errors={h_a_execution_authorization.get('error_count', 0)}",
        f"H-A execution release audit: {h_a_execution_release.get('status', 'unknown')}; ready={str(bool(h_a_execution_release.get('ready_for_execution_authorization'))).lower()}; released={str(bool(h_a_execution_release.get('released_for_execution'))).lower()}; blockers={h_a_execution_release.get('blocker_count', 0)}; authorization_blockers={h_a_execution_release.get('authorization_blocker_count', 0)}",
        f"Hybrid measurement routing: {hybrid_status}; local_rows={hybrid_inhouse}; outsource_preferred_rows={hybrid_outsource}; provenance_rows={hybrid_provenance}; total_rows={hybrid_total}",
        f"Local capture pack: {local_capture_status}; tasks={local_capture_tasks}; local_tasks={local_capture_local}; outsource_tasks={local_capture_outsource}; provenance_tasks={local_capture_provenance}",
        f"Source-file manifest: {source_file_manifest_status}; allowed_roots={source_file_allowed_roots}; source_classes={source_file_expected_classes}",
        f"Source-file inventory: {source_file_inventory_status}; files={source_file_inventory_files}; refs={source_file_inventory_refs}; capture_refs={source_file_inventory_capture_refs}; filled_source_value_refs={source_file_inventory_source_value_refs}; missing_refs={source_file_inventory_missing}; unreferenced={source_file_inventory_unreferenced}",
        f"H-A source drop plan: {h_a_source_drop_status}; planned_files={h_a_source_drop_planned}; dirs={h_a_source_drop_dirs}; existing_files={h_a_source_drop_existing}; missing_files={h_a_source_drop_missing}",
        f"H-A raw CSV extraction: {h_a_raw_csv_extraction_status}; files={h_a_raw_csv_extraction_files}; rows={h_a_raw_csv_extraction_rows}; errors={h_a_raw_csv_extraction_errors}",
        f"Local capture preflight: {local_preflight_status}; ready={str(local_preflight_ready).lower()}; filled={local_preflight_filled}; pending={local_preflight_pending}; errors={local_preflight_errors}; warnings={local_preflight_warnings}",
        f"Smoke capture tranche: {smoke_status}; tasks={smoke_tasks}; local_or_record_tasks={smoke_local_or_record}; outsource_tasks={smoke_outsource}",
        f"Smoke execution queue: {smoke_queue_status}; rows={smoke_queue_rows}; h_a_rows={smoke_queue_h_a_rows}; zrc_rows={smoke_queue_zrc_rows}; awaiting={smoke_queue_awaiting}; source_ready={smoke_queue_source_ready}",
        f"Smoke entry sheet: {smoke_entry_sheet_status}; rows={smoke_entry_sheet_rows}; filled={smoke_entry_sheet_filled}; ready_to_apply={smoke_entry_sheet_ready}",
        f"Smoke source drop plan: {smoke_source_drop_status}; planned_files={smoke_source_drop_planned}; dirs={smoke_source_drop_dirs}; existing_files={smoke_source_drop_existing}; missing_files={smoke_source_drop_missing}",
        f"Smoke source values sheet: {smoke_source_values_sheet_status}; rows={smoke_source_values_sheet_rows}; starter={smoke_source_values_sheet_starter}; filled={smoke_source_values_sheet_filled}; import_ready={smoke_source_values_sheet_import_ready}",
        f"Smoke starter batch readiness: {smoke_starter_readiness_status}; rows={smoke_starter_rows}; ready={smoke_starter_ready}; blocked={smoke_starter_blocked}",
        f"Smoke starter execution pack: {smoke_starter_execution_pack_status}; rows={smoke_starter_execution_pack_rows}; dirs={smoke_starter_execution_pack_dirs}; existing_files={smoke_starter_execution_pack_existing}",
        f"Smoke starter raw-file template pack: {smoke_starter_template_pack_status}; rows={smoke_starter_template_pack_rows}; templates={smoke_starter_template_pack_templates}",
        f"Smoke raw CSV extraction: {smoke_raw_csv_extraction_status}; files={smoke_raw_csv_extraction_files}; rows={smoke_raw_csv_extraction_rows}; errors={smoke_raw_csv_extraction_errors}",
        f"Smoke unstructured source intake: {smoke_unstructured_intake_status}; rows={smoke_unstructured_intake_rows}; ready={smoke_unstructured_intake_ready}; missing={smoke_unstructured_intake_missing}; invalid={smoke_unstructured_intake_invalid}",
        f"Smoke unstructured review values: {smoke_unstructured_review_status}; rows={smoke_unstructured_review_rows}; ready_sources={smoke_unstructured_review_ready_sources}; filled={smoke_unstructured_review_filled}; import_ready={smoke_unstructured_review_import_ready}; invalid_sources={smoke_unstructured_review_invalid}",
        f"Smoke source value import: {smoke_source_value_import_status}; files={smoke_source_value_import_files}; rows={smoke_source_value_import_rows}; imported={smoke_source_value_import_imported}; errors={smoke_source_value_import_errors}",
        f"Smoke entry apply: {smoke_entry_apply_status}; applied={smoke_entry_apply_applied}; errors={smoke_entry_apply_errors}",
        f"Smoke capture preflight: {smoke_preflight_status}; ready={str(smoke_preflight_ready).lower()}; filled={smoke_preflight_filled}; pending={smoke_preflight_pending}; errors={smoke_preflight_errors}; warnings={smoke_preflight_warnings}",
        f"Smoke rehearsal: {smoke_rehearsal_status}; preflight={smoke_rehearsal_preflight_status}; ready={str(smoke_rehearsal_ready).lower()}; filled={smoke_rehearsal_filled}; pending={smoke_rehearsal_pending}; errors={smoke_rehearsal_errors}; warnings={smoke_rehearsal_warnings}; h_a_qc={smoke_rehearsal_h_a_qc}; zrc_validation={smoke_rehearsal_zrc_validation}",
    ]
    portfolio_bypass_gaps = [
        (
            "Portfolio bypass audit: "
            f"{portfolio_bypass.get('status', 'unknown')}; "
            f"audit_rows={bypass_summary.get('audit_rows', 0)}; "
            f"non_h_a_candidates={bypass_summary.get('non_h_a_candidate_rows', 0)}; "
            f"non_h_a_claim_ready={bypass_summary.get('non_h_a_claim_ready_rows', 0)}; "
            f"top_non_h_a={bypass_summary.get('top_non_h_a_candidate') or '-'}; "
            f"recommended_action={bypass_summary.get('recommended_action', '-')}"
        )
    ]
    if (
        bypass_summary.get("recommended_action") == "run_zrc_phase_a_real_measurements_before_any_non_h_a_claim"
        and zrc_phase_a_rfq_send_cockpit.get("status") == "zrc_phase_a_rfq_send_cockpit_ready_for_manual_send"
    ):
        zrc_parallel_actions = [
            action(
                0,
                "send_zrc_phase_a_rfq",
                "ZRC Phase A",
                "The portfolio bypass audit says the only current non-H-A branch still needs real ZRC Phase A measurements before any non-H-A claim.",
                "manual: use reports/zrc_nd_phase_a_rfq_send_cockpit.html or data/zrc_nd_phase_a_rfq_dispatch_archive/zrc_nd_phase_a_rfq_dispatch_archive.zip to send ready RFQs",
                "data/rfq_send_confirmation_files/zrc_phase_a",
                "Each sent ZRC Phase A vendor has a real sent-email export, web-form confirmation, PDF, or screenshot saved under data/rfq_send_confirmation_files/zrc_phase_a.",
            ),
            action(
                0,
                "intake_zrc_phase_a_rfq_send_confirmations",
                "ZRC Phase A",
                "Saved ZRC send confirmations need to be parsed or flagged before replies are trusted as source-backed.",
                "python3 scripts/intake_limina_rfq_send_confirmations.py --profile zrc_phase_a",
                "data/zrc_nd_phase_a_rfq_send_confirmation_intake.json",
                "The intake registers real confirmation files with matching bundle hashes or flags rows for human review.",
            ),
            action(
                0,
                "apply_zrc_phase_a_non_eml_send_confirmations",
                "ZRC Phase A",
                "Web-form/PDF/screenshot confirmations need a guarded manual entry path before the ZRC send log is trusted.",
                "run: python3 scripts/render_zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.py, then python3 scripts/apply_zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.py",
                "data/zrc_nd_phase_a_rfq_send_confirmation_entry_apply.json",
                "Non-EML ZRC confirmations are applied only when a real source file exists, current SHA-256 is recorded, bundle hash matches the dispatch manifest, and apply=yes is human-reviewed.",
            ),
            action(
                0,
                "apply_zrc_phase_a_rfq_send_log",
                "ZRC Phase A",
                "Verified send rows must be reflected into the ZRC quote tracker before reply intake and provider selection.",
                "python3 scripts/apply_limina_rfq_send_log.py --profile zrc_phase_a",
                "data/zrc_nd_phase_a_rfq_send_log.json",
                "The send log has valid sent rows and tracker contact dates for sent first-wave ZRC vendors.",
            ),
            action(
                0,
                "save_zrc_phase_a_rfq_replies",
                "ZRC Phase A",
                "Vendor replies are needed for execution selection but must be preserved as original source files.",
                "manual: save original replies under data/rfq_reply_files/zrc_phase_a",
                "data/rfq_reply_files/zrc_phase_a",
                "Every received vendor reply, quote PDF, proposal, or clarification email is saved at the path listed in reports/zrc_nd_phase_a_rfq_reply_action_pack.md.",
            ),
        ]
        actions = actions[:1] + zrc_parallel_actions + actions[1:]
        for index, item in enumerate(actions, start=1):
            item["rank"] = index
    if first_wave_rfq_dispatch_cockpit.get("status") in {
        "first_wave_rfq_dispatch_cockpit_ready_for_manual_send",
        "first_wave_rfq_dispatch_cockpit_has_confirmation_files",
    }:
        actions = [
            action(
                1,
                "use_first_wave_rfq_dispatch_cockpit",
                "sourcing",
                "The combined cockpit is the shortest path from prepared RFQ artifacts to real send confirmations for both active measurement branches.",
                "manual: open reports/limina_first_wave_rfq_dispatch_cockpit.html and send ready first-wave RFQs",
                "data/rfq_send_confirmation_files",
                "Real confirmation files are saved for sent H-A and ZRC vendors, then send-confirmation intake and send-log apply can advance the sourcing chain.",
            ),
            action(
                2,
                "process_first_wave_post_dispatch_files",
                "sourcing",
                "After any real send confirmation or vendor reply is saved, the combined processor runs both H-A and ZRC intake/apply/evaluate/audit chains.",
                "python3 scripts/process_limina_first_wave_post_dispatch.py",
                "reports/limina_first_wave_post_dispatch_processing.md",
                "Saved confirmations or replies are reflected into source-backed send/reply logs without creating measurement evidence.",
            ),
            *actions,
        ]
        for index, item in enumerate(actions, start=1):
            item["rank"] = index
    if second_wave_candidate_queue.get("status") in {
        "second_wave_candidate_queue_ready_while_first_wave_waits",
        "second_wave_candidate_queue_ready",
    }:
        second_wave_action = action(
            0,
            "review_second_wave_candidate_queue",
            "portfolio",
            "The first-wave measurement route is waiting on real confirmations/replies, so the highest-ranked non-active candidates can be scope-locked without creating suitability evidence.",
            "python3 scripts/render_limina_second_wave_candidate_queue.py",
            "reports/limina_second_wave_candidate_queue.md",
            "Second-wave candidates remain planning-only rows until a source-backed measurement package is created and the final claim audit still reports false.",
        )
        insert_at = 0
        for index, item in enumerate(actions):
            if item.get("action_id") == "process_first_wave_post_dispatch_files":
                insert_at = index + 1
                break
        actions = actions[:insert_at] + [second_wave_action] + actions[insert_at:]
        for index, item in enumerate(actions, start=1):
            item["rank"] = index
    if second_wave_scope_lock_pack.get("status") == "second_wave_scope_lock_pack_ready":
        scope_lock_action = action(
            0,
            "review_second_wave_scope_lock_pack",
            "portfolio",
            "The second-wave queue has been translated into concrete material-identity, trigger-boundary, and future source-class tasks.",
            "python3 scripts/render_limina_second_wave_scope_lock_pack.py",
            "reports/limina_second_wave_scope_lock_pack.md",
            "Scope-lock tasks are reviewed while claim_ready remains false and no task is treated as measured material evidence.",
        )
        insert_at = 0
        for index, item in enumerate(actions):
            if item.get("action_id") == "review_second_wave_candidate_queue":
                insert_at = index + 1
                break
        actions = actions[:insert_at] + [scope_lock_action] + actions[insert_at:]
        for index, item in enumerate(actions, start=1):
            item["rank"] = index
    return {
        "status": "cycle_state_built",
        "mission_state": mission_state,
        "state_reason": state_reason,
        "claim_ready": bool(claim.get("claim_ready")),
        "claim_status": claim.get("status"),
        "active_discovery_candidate": top.get("id"),
        "active_discovery_priority": top.get("priority"),
        "active_discovery_score": top.get("weighted_score"),
        "active_material_route": "ALG-LAM-PEDOT low-dose neural hydrogel interphase",
        "active_route_gate": "H-A" if mission_state.startswith("awaiting_real_h_a") else "adaptive",
        "first_wave_rfq_dispatch_cockpit_status": first_wave_rfq_dispatch_cockpit.get("status"),
        "first_wave_rfq_dispatch_cockpit_rows": first_wave_rfq_dispatch_cockpit_summary.get("vendor_rows", 0),
        "first_wave_rfq_dispatch_cockpit_ready_rows": first_wave_rfq_dispatch_cockpit_summary.get("ready_to_send_rows", 0),
        "first_wave_rfq_dispatch_cockpit_confirmations": first_wave_rfq_dispatch_cockpit_summary.get("confirmation_files_present", 0),
        "first_wave_rfq_dispatch_cockpit_replies": first_wave_rfq_dispatch_cockpit_summary.get("reply_files_present", 0),
        "first_wave_rfq_dispatch_cockpit_missing_messages": first_wave_rfq_dispatch_cockpit_summary.get("missing_message_files", 0),
        "first_wave_rfq_dispatch_cockpit_missing_bundles": first_wave_rfq_dispatch_cockpit_summary.get("missing_bundle_files", 0),
        "first_wave_rfq_dispatch_cockpit_html": first_wave_rfq_dispatch_cockpit.get("generated_artifacts", {}).get("html", ""),
        "first_wave_post_dispatch_status": first_wave_post_dispatch.get("status"),
        "first_wave_post_dispatch_failed_commands": len(first_wave_post_dispatch.get("failed_command_ids", [])),
        "first_wave_post_dispatch_confirmations": first_wave_post_dispatch_cockpit_summary.get("confirmation_files_present", 0),
        "first_wave_post_dispatch_replies": first_wave_post_dispatch_cockpit_summary.get("reply_files_present", 0),
        "second_wave_candidate_queue_status": second_wave_candidate_queue.get("status"),
        "second_wave_candidate_queue_rows": second_wave_candidate_queue_summary.get("queue_rows", 0),
        "second_wave_candidate_queue_ready_scope_lock_rows": second_wave_candidate_queue_summary.get("ready_scope_lock_rows", 0),
        "second_wave_candidate_queue_watch_rows": second_wave_candidate_queue_summary.get("watch_rows", 0),
        "second_wave_candidate_queue_hold_rows": second_wave_candidate_queue_summary.get("hold_rows", 0),
        "second_wave_scope_lock_pack_status": second_wave_scope_lock_pack.get("status"),
        "second_wave_scope_lock_pack_ready_candidates": second_wave_scope_lock_pack_summary.get("ready_candidate_count", 0),
        "second_wave_scope_lock_pack_tasks": second_wave_scope_lock_pack_summary.get("task_count", 0),
        "second_wave_scope_lock_pack_source_classes": second_wave_scope_lock_pack_summary.get("source_file_class_count", 0),
        "second_wave_scope_lock_pack_claim_evidence_created": bool(second_wave_scope_lock_pack_summary.get("claim_evidence_created")),
        "portfolio_bypass_status": portfolio_bypass.get("status"),
        "portfolio_bypass_non_h_a_claim_ready_rows": bypass_summary.get("non_h_a_claim_ready_rows", 0),
        "portfolio_bypass_non_h_a_candidate_rows": bypass_summary.get("non_h_a_candidate_rows", 0),
        "portfolio_bypass_top_non_h_a_candidate": bypass_summary.get("top_non_h_a_candidate"),
        "portfolio_bypass_recommended_action": bypass_summary.get("recommended_action"),
        "h_a_status": h_a.get("status"),
        "h_a_next_action": h_a.get("next_action"),
        "h_a_provenance": h_a.get("provenance", {}),
        "h_a_bench_status": h_a_bench.get("status"),
        "h_a_bench_task_count": h_a_bench.get("task_count"),
        "h_a_bench_blank_raw_entries_to_fill": h_a_bench.get("blank_raw_entries_to_fill"),
        "h_a_measurement_merge_status": h_a_merge.get("status"),
        "h_a_measurement_merge_stats": h_a_merge.get("stats", {}),
        "h_a_intake_qc_status": h_a_qc.get("status"),
        "h_a_intake_qc_ready": h_a_qc.get("intake_ready"),
        "h_a_intake_qc_issue_counts": h_a_qc.get("issue_counts", {}),
        "h_a_service_request_status": h_a_service.get("status"),
        "h_a_service_request_raw_entries": h_a_service.get("requested_matrix", {}).get("raw_entries", 0),
        "h_a_chain_of_custody_status": h_a_chain.get("status"),
        "h_a_sample_label_count": h_a_chain.get("sample_label_count", 0),
        "h_a_chain_of_custody_rows": h_a_chain.get("chain_of_custody_row_count", 0),
        "h_a_pending_transfer_rows": h_a_chain.get("pending_transfer_rows", 0),
        "h_a_sample_submission_status": h_a_sample_submission.get("status"),
        "h_a_sample_submission_shipping_status": h_a_sample_submission.get("shipping_status"),
        "h_a_split_scope_status": h_a_split_scope.get("status"),
        "h_a_split_scope_pair_count": h_a_split_scope.get("pair_count", 0),
        "h_a_split_scope_preferred_count": h_a_split_scope.get("preferred_pair_count", 0),
        "h_a_vendor_outreach_status": h_a_vendor.get("status"),
        "h_a_vendor_first_wave_count": len(h_a_vendor.get("first_wave", [])),
        "h_a_rfq_packet_status": h_a_rfq.get("status"),
        "h_a_rfq_outbox_status": h_a_rfq_outbox.get("status"),
        "h_a_rfq_outbox_ready_count": h_a_rfq_outbox.get("ready_to_send_count", 0),
        "h_a_rfq_outbox_quote_count": h_a_rfq_outbox.get("quote_request_count", 0),
        "h_a_rfq_eml_drafts_status": h_a_rfq_eml_drafts.get("status"),
        "h_a_rfq_eml_drafts_rows": h_a_rfq_eml_summary.get("draft_rows", 0),
        "h_a_rfq_eml_drafts_ready_rows": h_a_rfq_eml_summary.get("ready_to_open_rows", 0),
        "h_a_rfq_eml_drafts_missing_to_rows": h_a_rfq_eml_summary.get("missing_to_address_rows", 0),
        "h_a_rfq_eml_drafts_missing_bundle_rows": h_a_rfq_eml_summary.get("missing_bundle_rows", 0),
        "h_a_rfq_eml_integrity_status": h_a_rfq_eml_integrity.get("status"),
        "h_a_rfq_eml_integrity_rows": h_a_rfq_eml_integrity_summary.get("audit_rows", 0),
        "h_a_rfq_eml_integrity_pass_rows": h_a_rfq_eml_integrity_summary.get("pass_rows", 0),
        "h_a_rfq_eml_integrity_fail_rows": h_a_rfq_eml_integrity_summary.get("fail_rows", 0),
        "h_a_rfq_eml_integrity_attachment_mismatch_rows": h_a_rfq_eml_integrity_summary.get("attachment_mismatch_rows", 0),
        "h_a_quote_tracker_status": h_a_quote_tracker.get("status"),
        "h_a_rfq_send_action_pack_status": h_a_rfq_send_action_pack.get("status"),
        "h_a_rfq_send_action_pack_rows": h_a_send_action_summary.get("action_rows", 0),
        "h_a_rfq_send_action_pack_ready_rows": h_a_send_action_summary.get("ready_to_send_rows", 0),
        "h_a_rfq_send_action_pack_verified_rows": h_a_send_action_summary.get("sent_confirmation_verified_rows", 0),
        "h_a_rfq_send_action_pack_needs_confirmation_rows": h_a_send_action_summary.get("sent_needs_confirmation_rows", 0),
        "h_a_rfq_dispatch_manifest_status": h_a_rfq_dispatch_manifest.get("status"),
        "h_a_rfq_dispatch_manifest_rows": h_a_dispatch_manifest_summary.get("dispatch_rows", 0),
        "h_a_rfq_dispatch_manifest_ready_rows": h_a_dispatch_manifest_summary.get("ready_for_manual_dispatch_rows", 0),
        "h_a_rfq_dispatch_manifest_blocked_rows": h_a_dispatch_manifest_summary.get("blocked_rows", 0),
        "h_a_rfq_dispatch_manifest_bundle_match_rows": h_a_dispatch_manifest_summary.get("bundle_sha256_match_rows", 0),
        "h_a_rfq_send_cockpit_status": h_a_rfq_send_cockpit.get("status"),
        "h_a_rfq_send_cockpit_rows": h_a_send_cockpit_summary.get("vendor_rows", 0),
        "h_a_rfq_send_cockpit_ready_rows": h_a_send_cockpit_summary.get("ready_to_use_rows", 0),
        "h_a_rfq_send_cockpit_confirmations": h_a_send_cockpit_summary.get("confirmation_files_present", 0),
        "h_a_rfq_send_cockpit_replies": h_a_send_cockpit_summary.get("reply_files_present", 0),
        "h_a_rfq_send_cockpit_missing_eml": h_a_send_cockpit_summary.get("missing_eml_rows", 0),
        "h_a_rfq_send_cockpit_missing_bundle": h_a_send_cockpit_summary.get("missing_bundle_rows", 0),
        "h_a_rfq_send_cockpit_html": h_a_rfq_send_cockpit.get("generated_artifacts", {}).get("html", ""),
        "h_a_rfq_dispatch_archive_status": h_a_rfq_dispatch_archive.get("status"),
        "h_a_rfq_dispatch_archive_files": h_a_dispatch_archive_summary.get("included_files", 0),
        "h_a_rfq_dispatch_archive_missing_files": h_a_dispatch_archive_summary.get("missing_files", 0),
        "h_a_rfq_dispatch_archive_hash_mismatches": h_a_dispatch_archive_summary.get("hash_mismatch_files", 0),
        "h_a_rfq_dispatch_archive_sha256": h_a_dispatch_archive_summary.get("archive_sha256", ""),
        "h_a_rfq_dispatch_archive_path": h_a_rfq_dispatch_archive.get("generated_artifacts", {}).get("archive", ""),
        "h_a_rfq_send_confirmation_intake_status": h_a_rfq_send_confirmation_intake.get("status"),
        "h_a_rfq_send_confirmation_intake_files": h_a_rfq_send_confirmation_intake.get("row_count", 0),
        "h_a_rfq_send_confirmation_intake_applied_rows": h_a_rfq_send_confirmation_intake.get("applied_rows", 0),
        "h_a_rfq_send_confirmation_intake_needs_review_rows": h_a_rfq_send_confirmation_intake.get("needs_review_rows", 0),
        "h_a_rfq_send_confirmation_intake_bundle_matched_rows": h_a_rfq_send_confirmation_intake.get("bundle_hash_matched_rows", 0),
        "h_a_rfq_send_confirmation_entry_sheet_status": h_a_rfq_send_confirmation_entry_sheet.get("status"),
        "h_a_rfq_send_confirmation_entry_sheet_rows": h_a_send_confirmation_entry_sheet_summary.get("entry_rows", 0),
        "h_a_rfq_send_confirmation_entry_sheet_source_files": h_a_send_confirmation_entry_sheet_summary.get("source_file_present_rows", 0),
        "h_a_rfq_send_confirmation_entry_sheet_ready_rows": h_a_send_confirmation_entry_sheet_summary.get("ready_to_apply_rows", 0),
        "h_a_rfq_send_confirmation_entry_sheet_blocked_rows": h_a_send_confirmation_entry_sheet_summary.get("blocked_rows", 0),
        "h_a_rfq_send_confirmation_entry_apply_status": h_a_rfq_send_confirmation_entry_apply.get("status"),
        "h_a_rfq_send_confirmation_entry_apply_rows": h_a_send_confirmation_entry_apply_summary.get("apply_rows", 0),
        "h_a_rfq_send_confirmation_entry_apply_applied_rows": h_a_send_confirmation_entry_apply_summary.get("applied_rows", 0),
        "h_a_rfq_send_confirmation_entry_apply_blocked_rows": h_a_send_confirmation_entry_apply_summary.get("blocked_rows", 0),
        "h_a_rfq_send_log_status": h_a_rfq_send_log.get("status"),
        "h_a_rfq_send_log_rows": h_a_rfq_send_log.get("row_count", 0),
        "h_a_rfq_send_log_sent_rows": h_a_rfq_send_log.get("sent_rows", 0),
        "h_a_rfq_send_log_valid_sent_rows": h_a_rfq_send_log.get("valid_sent_rows", 0),
        "h_a_rfq_send_log_applied_dates": h_a_rfq_send_log.get("applied_tracker_contact_dates", 0),
        "h_a_rfq_send_log_errors": h_a_rfq_send_log.get("error_count", 0),
        "h_a_rfq_reply_log_status": h_a_rfq_reply_log.get("status"),
        "h_a_rfq_reply_log_rows": h_a_rfq_reply_log.get("row_count", 0),
        "h_a_rfq_reply_log_received_rows": h_a_rfq_reply_log.get("received_rows", 0),
        "h_a_rfq_reply_log_valid_rows": h_a_rfq_reply_log.get("valid_reply_rows", 0),
        "h_a_rfq_reply_log_applied_fields": h_a_rfq_reply_log.get("applied_tracker_field_updates", 0),
        "h_a_rfq_reply_log_errors": h_a_rfq_reply_log.get("error_count", 0),
        "h_a_rfq_reply_intake_status": h_a_rfq_reply_intake.get("status"),
        "h_a_rfq_reply_intake_files": h_a_rfq_reply_intake.get("row_count", 0),
        "h_a_rfq_reply_intake_applied_rows": h_a_rfq_reply_intake.get("applied_rows", 0),
        "h_a_rfq_reply_intake_needs_review_rows": h_a_rfq_reply_intake.get("needs_manual_review_rows", 0),
        "h_a_rfq_reply_intake_needs_verified_send_rows": h_a_rfq_reply_intake.get("needs_verified_send_rows", 0),
        "h_a_vendor_contact_source_audit_status": h_a_contact_source_audit.get("status"),
        "h_a_vendor_contact_source_audit_rows": h_a_contact_source_audit_summary.get("audit_rows", 0),
        "h_a_vendor_contact_source_audit_pass_rows": h_a_contact_source_audit_summary.get("pass_rows", 0),
        "h_a_vendor_contact_source_audit_fail_rows": h_a_contact_source_audit_summary.get("fail_rows", 0),
        "h_a_vendor_contact_source_audit_stale_rows": h_a_contact_source_audit_summary.get("stale_proof_rows", 0),
        "h_a_rfq_reply_action_pack_status": h_a_rfq_reply_action_pack.get("status"),
        "h_a_rfq_reply_action_pack_rows": h_a_reply_action_summary.get("action_rows", 0),
        "h_a_rfq_reply_action_pack_waiting_send_rows": h_a_reply_action_summary.get("waiting_for_send_rows", 0),
        "h_a_rfq_reply_action_pack_awaiting_reply_rows": h_a_reply_action_summary.get("awaiting_reply_rows", 0),
        "h_a_rfq_reply_action_pack_needs_source_rows": h_a_reply_action_summary.get("received_needs_source_file_rows", 0),
        "h_a_rfq_reply_action_pack_ready_apply_rows": h_a_reply_action_summary.get("ready_for_reply_log_apply_rows", 0),
        "h_a_vendor_contact_plan_status": h_a_contact_plan.get("status"),
        "h_a_vendor_contact_ready_count": h_a_contact_plan.get("status_counts", {}).get("ready_to_send", 0),
        "h_a_vendor_contact_standby_count": h_a_contact_plan.get("status_counts", {}).get("standby_secondary_wave", 0),
        "h_a_vendor_contact_row_count": h_a_contact_plan.get("row_count", 0),
        "h_a_quote_selection_status": h_a_quote_selection.get("status"),
        "h_a_quote_selection_sent_count": h_a_quote_selection.get("sent_count", 0),
        "h_a_quote_selection_reply_count": h_a_quote_selection.get("reply_count", 0),
        "h_a_quote_selection_source_backed_reply_count": h_a_quote_selection.get("source_backed_reply_count", 0),
        "h_a_quote_selection_shortlist_count": h_a_quote_selection.get("shortlist_count", 0),
        "h_a_execution_authorization_status": h_a_execution_authorization.get("status"),
        "h_a_execution_authorization_rows": h_a_execution_authorization.get("row_count", 0),
        "h_a_execution_authorization_valid_rows": h_a_execution_authorization.get("valid_authorization_rows", 0),
        "h_a_execution_authorization_errors": h_a_execution_authorization.get("error_count", 0),
        "h_a_execution_release_status": h_a_execution_release.get("status"),
        "h_a_execution_release_ready": bool(h_a_execution_release.get("ready_for_execution_authorization")),
        "h_a_execution_release_released": bool(h_a_execution_release.get("released_for_execution")),
        "h_a_execution_release_blockers": h_a_execution_release.get("blocker_count", 0),
        "h_a_execution_release_authorization_blockers": h_a_execution_release.get("authorization_blocker_count", 0),
        "h_a_vendor_return_status": h_a_vendor_return.get("status"),
        "h_a_vendor_return_raw_value_rows": h_a_vendor_return.get("raw_measurements", {}).get("value_row_count", 0),
        "h_a_vendor_return_bundle_rows": h_a_vendor_return_bundle.get("row_count", 0),
        "h_a_vendor_return_bundle_apply_rows": h_a_vendor_return_bundle.get("apply_row_count", 0),
        "h_a_vendor_return_export_files": h_a_vendor_return.get("instrument_export_file_count", 0),
        "h_a_vendor_bundle_entry_sheet_status": h_a_vendor_bundle_entry_sheet.get("status"),
        "h_a_vendor_bundle_entry_sheet_bundles": h_a_vendor_bundle_entry_sheet_summary.get("bundle_rows", 0),
        "h_a_vendor_bundle_entry_sheet_ready_rows": h_a_vendor_bundle_entry_sheet_summary.get("ready_to_apply_rows", 0),
        "h_a_vendor_bundle_entry_sheet_blocked_rows": h_a_vendor_bundle_entry_sheet_summary.get("blocked_rows", 0),
        "h_a_vendor_bundle_entry_apply_status": h_a_vendor_bundle_entry_apply.get("status"),
        "h_a_vendor_bundle_entry_apply_sheet_exists": bool(h_a_vendor_bundle_entry_summary.get("sheet_exists", False)),
        "h_a_vendor_bundle_entry_apply_bundles": h_a_vendor_bundle_entry_summary.get("applied_bundles", 0),
        "h_a_vendor_bundle_entry_apply_source_rows": h_a_vendor_bundle_entry_summary.get("applied_source_value_rows", 0),
        "h_a_vendor_bundle_entry_apply_errors": h_a_vendor_bundle_entry_summary.get("error_count", 0),
        "h_a_source_values_sheet_status": h_a_source_values_sheet.get("status"),
        "h_a_source_values_sheet_rows": h_a_source_values_sheet.get("summary", {}).get("source_value_rows", 0),
        "h_a_source_values_sheet_filled_rows": h_a_source_values_sheet.get("summary", {}).get("filled_value_rows", 0),
        "h_a_source_values_sheet_source_file_exists_rows": h_a_source_values_sheet.get("summary", {}).get("source_file_exists_rows", 0),
        "h_a_source_values_sheet_import_ready_rows": h_a_source_values_sheet.get("summary", {}).get("import_ready_rows", 0),
        "h_a_source_drop_status": h_a_source_drop_status,
        "h_a_source_drop_planned_files": h_a_source_drop_planned,
        "h_a_source_drop_dirs": h_a_source_drop_dirs,
        "h_a_source_drop_existing_files": h_a_source_drop_existing,
        "h_a_source_drop_missing_files": h_a_source_drop_missing,
        "h_a_raw_csv_extraction_status": h_a_raw_csv_extraction_status,
        "h_a_raw_csv_extraction_files": h_a_raw_csv_extraction_files,
        "h_a_raw_csv_extraction_rows": h_a_raw_csv_extraction_rows,
        "h_a_raw_csv_extraction_errors": h_a_raw_csv_extraction_errors,
        "h_a_source_value_import_status": h_a_source_value_import.get("status"),
        "h_a_source_value_import_files": h_a_source_value_import.get("summary", {}).get("source_value_files", 0),
        "h_a_source_value_import_rows": h_a_source_value_import.get("summary", {}).get("source_value_rows", 0),
        "h_a_source_value_import_imported_rows": h_a_source_value_import.get("summary", {}).get("imported_rows", 0),
        "h_a_source_value_import_errors": h_a_source_value_import.get("summary", {}).get("error_count", 0),
        "nhi_forward_status": nhi_forward.get("status"),
        "nhi_forward_rows": nhi_forward.get("row_count", 0),
        "nhi_forward_source_values_status": nhi_forward_source_values.get("status"),
        "nhi_forward_source_values_rows": nhi_forward_source_values_summary.get("source_value_rows", 0),
        "nhi_forward_source_values_filled_rows": nhi_forward_source_values_summary.get("filled_value_rows", 0),
        "nhi_forward_source_values_source_file_exists_rows": nhi_forward_source_values_summary.get("source_file_exists_rows", 0),
        "nhi_forward_source_values_import_ready_rows": nhi_forward_source_values_summary.get("import_ready_rows", 0),
        "nhi_forward_source_drop_status": nhi_forward_source_drop.get("status"),
        "nhi_forward_source_drop_planned_files": nhi_forward_source_drop_summary.get("planned_source_file_count", 0),
        "nhi_forward_source_drop_dirs": nhi_forward_source_drop_summary.get("source_dir_count", 0),
        "nhi_forward_source_drop_existing_files": nhi_forward_source_drop_summary.get("existing_source_file_count", 0),
        "nhi_forward_source_drop_missing_files": nhi_forward_source_drop_summary.get("missing_source_file_count", 0),
        "nhi_forward_source_template_pack_status": nhi_forward_source_template_pack.get("status"),
        "nhi_forward_source_template_pack_templates": nhi_forward_source_template_pack_summary.get("source_class_template_count", 0),
        "nhi_forward_source_template_pack_target_files": nhi_forward_source_template_pack_summary.get("target_source_file_count", 0),
        "nhi_forward_raw_csv_extraction_status": nhi_forward_raw_csv_extraction.get("status"),
        "nhi_forward_raw_csv_extraction_files": nhi_forward_raw_csv_extraction_summary.get("raw_csv_found", 0),
        "nhi_forward_raw_csv_extraction_rows": nhi_forward_raw_csv_extraction_summary.get("extracted_rows", 0),
        "nhi_forward_raw_csv_extraction_errors": nhi_forward_raw_csv_extraction_summary.get("error_count", 0),
        "nhi_forward_source_import_status": nhi_forward_source_import.get("status"),
        "nhi_forward_source_import_files": nhi_forward_source_import_summary.get("source_value_files", 0),
        "nhi_forward_source_import_rows": nhi_forward_source_import_summary.get("source_value_rows", 0),
        "nhi_forward_source_import_imported_rows": nhi_forward_source_import_summary.get("imported_rows", 0),
        "nhi_forward_source_import_errors": nhi_forward_source_import_summary.get("error_count", 0),
        "nhi_coupon_result_status": nhi_results_summary.get("status"),
        "nhi_coupon_result_rows": nhi_results_summary.get("rows", 0),
        "nhi_long_source_values_status": nhi_long_source_values.get("status"),
        "nhi_long_source_values_rows": nhi_long_source_values_summary.get("source_value_rows", 0),
        "nhi_long_source_values_filled_rows": nhi_long_source_values_summary.get("filled_value_rows", 0),
        "nhi_long_source_values_source_file_exists_rows": nhi_long_source_values_summary.get("source_file_exists_rows", 0),
        "nhi_long_source_values_import_ready_rows": nhi_long_source_values_summary.get("import_ready_rows", 0),
        "nhi_long_source_drop_status": nhi_long_source_drop.get("status"),
        "nhi_long_source_drop_planned_files": nhi_long_source_drop_summary.get("planned_source_file_count", 0),
        "nhi_long_source_drop_dirs": nhi_long_source_drop_summary.get("source_dir_count", 0),
        "nhi_long_source_drop_existing_files": nhi_long_source_drop_summary.get("existing_source_file_count", 0),
        "nhi_long_source_drop_missing_files": nhi_long_source_drop_summary.get("missing_source_file_count", 0),
        "nhi_long_source_template_pack_status": nhi_long_source_template_pack.get("status"),
        "nhi_long_source_template_pack_templates": nhi_long_source_template_pack_summary.get("source_class_template_count", 0),
        "nhi_long_source_template_pack_target_files": nhi_long_source_template_pack_summary.get("target_source_file_count", 0),
        "nhi_long_raw_csv_extraction_status": nhi_long_raw_csv_extraction.get("status"),
        "nhi_long_raw_csv_extraction_files": nhi_long_raw_csv_extraction_summary.get("raw_csv_found", 0),
        "nhi_long_raw_csv_extraction_rows": nhi_long_raw_csv_extraction_summary.get("extracted_rows", 0),
        "nhi_long_raw_csv_extraction_errors": nhi_long_raw_csv_extraction_summary.get("error_count", 0),
        "nhi_long_source_import_status": nhi_long_source_import.get("status"),
        "nhi_long_source_import_files": nhi_long_source_import_summary.get("source_value_files", 0),
        "nhi_long_source_import_rows": nhi_long_source_import_summary.get("source_value_rows", 0),
        "nhi_long_source_import_imported_rows": nhi_long_source_import_summary.get("imported_rows", 0),
        "nhi_long_source_import_errors": nhi_long_source_import_summary.get("error_count", 0),
        "nhi_long_result_status": nhi_long_results_summary.get("status"),
        "nhi_long_result_rows": nhi_long_results_summary.get("rows", 0),
        "zrc_readiness": zrc_readiness.get("readiness"),
        "zrc_suitable": bool(zrc_readiness.get("suitable")),
        "zrc_sentinel_status": zrc_sentinel.get("status"),
        "zrc_sentinel_rows": zrc_sentinel.get("rows", 0),
        "zrc_next_status": zrc_next.get("status"),
        "zrc_next_recommended_rows": len(zrc_next.get("recommended_rows", [])),
        "zrc_phase_a_source_values_status": zrc_phase_a_source_values.get("status"),
        "zrc_phase_a_source_values_rows": zrc_phase_a_source_values_summary.get("source_value_rows", 0),
        "zrc_phase_a_source_values_filled_rows": zrc_phase_a_source_values_summary.get("filled_value_rows", 0),
        "zrc_phase_a_source_values_import_ready_rows": zrc_phase_a_source_values_summary.get("import_ready_rows", 0),
        "zrc_phase_a_source_drop_status": zrc_phase_a_source_drop.get("status"),
        "zrc_phase_a_source_drop_planned_files": zrc_phase_a_source_drop_summary.get("planned_source_file_count", 0),
        "zrc_phase_a_source_drop_dirs": zrc_phase_a_source_drop_summary.get("source_dir_count", 0),
        "zrc_phase_a_source_drop_existing_files": zrc_phase_a_source_drop_summary.get("existing_source_file_count", 0),
        "zrc_phase_a_source_drop_missing_files": zrc_phase_a_source_drop_summary.get("missing_source_file_count", 0),
        "zrc_phase_a_source_template_pack_status": zrc_phase_a_source_template_pack.get("status"),
        "zrc_phase_a_source_template_pack_templates": zrc_phase_a_source_template_pack_summary.get("source_class_template_count", 0),
        "zrc_phase_a_source_template_pack_target_files": zrc_phase_a_source_template_pack_summary.get("target_source_file_count", 0),
        "zrc_phase_a_vendor_bundle_entry_sheet_status": zrc_phase_a_vendor_bundle_entry_sheet.get("status"),
        "zrc_phase_a_vendor_bundle_entry_sheet_bundles": zrc_phase_a_vendor_bundle_entry_sheet_summary.get("bundle_rows", 0),
        "zrc_phase_a_vendor_bundle_entry_sheet_ready_rows": zrc_phase_a_vendor_bundle_entry_sheet_summary.get("ready_to_apply_rows", 0),
        "zrc_phase_a_vendor_bundle_entry_sheet_blocked_rows": zrc_phase_a_vendor_bundle_entry_sheet_summary.get("blocked_rows", 0),
        "zrc_phase_a_vendor_bundle_entry_apply_status": zrc_phase_a_vendor_bundle_entry_apply.get("status"),
        "zrc_phase_a_vendor_bundle_entry_apply_rows": zrc_phase_a_vendor_bundle_entry_apply_summary.get("apply_rows", 0),
        "zrc_phase_a_vendor_bundle_entry_apply_bundles": zrc_phase_a_vendor_bundle_entry_apply_summary.get("applied_bundles", 0),
        "zrc_phase_a_vendor_bundle_entry_apply_source_rows": zrc_phase_a_vendor_bundle_entry_apply_summary.get("applied_source_value_rows", 0),
        "zrc_phase_a_vendor_bundle_entry_apply_errors": zrc_phase_a_vendor_bundle_entry_apply_summary.get("error_count", 0),
        "zrc_phase_a_raw_csv_extraction_status": zrc_phase_a_raw_csv_extraction.get("status"),
        "zrc_phase_a_raw_csv_extraction_files": zrc_phase_a_raw_csv_extraction_summary.get("raw_csv_found", 0),
        "zrc_phase_a_raw_csv_extraction_rows": zrc_phase_a_raw_csv_extraction_summary.get("extracted_rows", 0),
        "zrc_phase_a_raw_csv_extraction_errors": zrc_phase_a_raw_csv_extraction_summary.get("error_count", 0),
        "zrc_phase_a_source_import_status": zrc_phase_a_source_import.get("status"),
        "zrc_phase_a_source_import_rows": zrc_phase_a_source_import_summary.get("source_value_rows", 0),
        "zrc_phase_a_source_import_imported_rows": zrc_phase_a_source_import_summary.get("imported_rows", 0),
        "zrc_phase_a_source_import_errors": zrc_phase_a_source_import_summary.get("error_count", 0),
        "zrc_phase_a_service_status": zrc_phase_a_service.get("status"),
        "zrc_phase_a_service_runs": zrc_phase_a_service.get("requested_matrix", {}).get("runs", 0),
        "zrc_phase_a_chain_status": zrc_phase_a_chain.get("status"),
        "zrc_phase_a_sample_label_count": zrc_phase_a_chain.get("sample_label_count", 0),
        "zrc_phase_a_chain_rows": zrc_phase_a_chain.get("chain_of_custody_row_count", 0),
        "zrc_phase_a_pending_transfer_rows": zrc_phase_a_chain.get("pending_transfer_rows", 0),
        "zrc_phase_a_delivery_status": zrc_phase_a_delivery.get("status"),
        "zrc_phase_a_delivery_missing_files": len(zrc_phase_a_delivery.get("missing_required_file_ids", [])),
        "zrc_phase_a_vendor_outreach_status": zrc_phase_a_vendor.get("status"),
        "zrc_phase_a_vendor_first_wave_count": len(zrc_phase_a_vendor.get("first_wave", [])),
        "zrc_phase_a_rfq_status": zrc_phase_a_rfq.get("status"),
        "zrc_phase_a_rfq_outbox_status": zrc_phase_a_rfq_outbox.get("status"),
        "zrc_phase_a_rfq_outbox_ready_count": zrc_phase_a_rfq_outbox.get("ready_to_send_count", 0),
        "zrc_phase_a_rfq_outbox_quote_count": zrc_phase_a_rfq_outbox.get("quote_request_count", 0),
        "zrc_phase_a_quote_tracker_status": zrc_phase_a_quote_tracker.get("status"),
        "zrc_phase_a_rfq_send_confirmation_intake_status": zrc_phase_a_rfq_send_confirmation_intake.get("status"),
        "zrc_phase_a_rfq_send_confirmation_intake_files": zrc_phase_a_rfq_send_confirmation_intake.get("row_count", 0),
        "zrc_phase_a_rfq_send_confirmation_intake_applied_rows": zrc_phase_a_rfq_send_confirmation_intake.get("applied_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_intake_needs_review_rows": zrc_phase_a_rfq_send_confirmation_intake.get("needs_review_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_intake_bundle_matched_rows": zrc_phase_a_rfq_send_confirmation_intake.get("bundle_hash_matched_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_sheet_status": zrc_phase_a_rfq_send_confirmation_entry_sheet.get("status"),
        "zrc_phase_a_rfq_send_confirmation_entry_sheet_rows": zrc_phase_a_send_confirmation_entry_sheet_summary.get("entry_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_sheet_source_files": zrc_phase_a_send_confirmation_entry_sheet_summary.get("source_file_present_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_sheet_ready_rows": zrc_phase_a_send_confirmation_entry_sheet_summary.get("ready_to_apply_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_sheet_blocked_rows": zrc_phase_a_send_confirmation_entry_sheet_summary.get("blocked_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_apply_status": zrc_phase_a_rfq_send_confirmation_entry_apply.get("status"),
        "zrc_phase_a_rfq_send_confirmation_entry_apply_rows": zrc_phase_a_send_confirmation_entry_apply_summary.get("apply_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_apply_applied_rows": zrc_phase_a_send_confirmation_entry_apply_summary.get("applied_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_apply_blocked_rows": zrc_phase_a_send_confirmation_entry_apply_summary.get("blocked_rows", 0),
        "zrc_phase_a_rfq_send_log_status": zrc_phase_a_rfq_send_log.get("status"),
        "zrc_phase_a_rfq_send_log_rows": zrc_phase_a_rfq_send_log.get("row_count", 0),
        "zrc_phase_a_rfq_send_log_sent_rows": zrc_phase_a_rfq_send_log.get("sent_rows", 0),
        "zrc_phase_a_rfq_send_log_valid_sent_rows": zrc_phase_a_rfq_send_log.get("valid_sent_rows", 0),
        "zrc_phase_a_rfq_send_log_applied_dates": zrc_phase_a_rfq_send_log.get("applied_tracker_contact_dates", 0),
        "zrc_phase_a_rfq_send_log_errors": zrc_phase_a_rfq_send_log.get("error_count", 0),
        "zrc_phase_a_rfq_reply_intake_status": zrc_phase_a_rfq_reply_intake.get("status"),
        "zrc_phase_a_rfq_reply_intake_files": zrc_phase_a_rfq_reply_intake.get("row_count", 0),
        "zrc_phase_a_rfq_reply_intake_applied_rows": zrc_phase_a_rfq_reply_intake.get("applied_rows", 0),
        "zrc_phase_a_rfq_reply_intake_needs_review_rows": zrc_phase_a_rfq_reply_intake.get("needs_manual_review_rows", 0),
        "zrc_phase_a_rfq_reply_intake_needs_verified_send_rows": zrc_phase_a_rfq_reply_intake.get("needs_verified_send_rows", 0),
        "zrc_phase_a_rfq_reply_log_status": zrc_phase_a_rfq_reply_log.get("status"),
        "zrc_phase_a_rfq_reply_log_rows": zrc_phase_a_rfq_reply_log.get("row_count", 0),
        "zrc_phase_a_rfq_reply_log_received_rows": zrc_phase_a_rfq_reply_log.get("received_rows", 0),
        "zrc_phase_a_rfq_reply_log_valid_rows": zrc_phase_a_rfq_reply_log.get("valid_reply_rows", 0),
        "zrc_phase_a_rfq_reply_log_applied_fields": zrc_phase_a_rfq_reply_log.get("applied_tracker_field_updates", 0),
        "zrc_phase_a_rfq_reply_log_errors": zrc_phase_a_rfq_reply_log.get("error_count", 0),
        "zrc_phase_a_contact_plan_status": zrc_phase_a_contact_plan.get("status"),
        "zrc_phase_a_contact_ready_count": zrc_phase_a_contact_plan.get("status_counts", {}).get("ready_to_send", 0),
        "zrc_phase_a_contact_standby_count": zrc_phase_a_contact_plan.get("status_counts", {}).get("standby_secondary_wave", 0),
        "zrc_phase_a_contact_row_count": zrc_phase_a_contact_plan.get("row_count", 0),
        "zrc_phase_a_rfq_dispatch_manifest_status": zrc_phase_a_rfq_dispatch_manifest.get("status"),
        "zrc_phase_a_rfq_dispatch_manifest_rows": zrc_phase_a_dispatch_manifest_summary.get("dispatch_rows", 0),
        "zrc_phase_a_rfq_dispatch_manifest_ready_rows": zrc_phase_a_dispatch_manifest_summary.get("ready_for_manual_dispatch_rows", 0),
        "zrc_phase_a_rfq_dispatch_manifest_blocked_rows": zrc_phase_a_dispatch_manifest_summary.get("blocked_rows", 0),
        "zrc_phase_a_rfq_dispatch_archive_status": zrc_phase_a_rfq_dispatch_archive.get("status"),
        "zrc_phase_a_rfq_dispatch_archive_files": zrc_phase_a_dispatch_archive_summary.get("included_files", 0),
        "zrc_phase_a_rfq_dispatch_archive_missing_files": zrc_phase_a_dispatch_archive_summary.get("missing_files", 0),
        "zrc_phase_a_rfq_dispatch_archive_hash_mismatches": zrc_phase_a_dispatch_archive_summary.get("hash_mismatch_files", 0),
        "zrc_phase_a_rfq_dispatch_archive_path": zrc_phase_a_rfq_dispatch_archive.get("generated_artifacts", {}).get("archive", ""),
        "zrc_phase_a_rfq_dispatch_archive_sha256": zrc_phase_a_dispatch_archive_summary.get("archive_sha256", ""),
        "zrc_phase_a_rfq_reply_action_pack_status": zrc_phase_a_rfq_reply_action_pack.get("status"),
        "zrc_phase_a_rfq_reply_action_pack_rows": zrc_phase_a_reply_action_summary.get("action_rows", 0),
        "zrc_phase_a_rfq_reply_action_pack_waiting_send_rows": zrc_phase_a_reply_action_summary.get("waiting_for_send_rows", 0),
        "zrc_phase_a_rfq_reply_action_pack_awaiting_reply_rows": zrc_phase_a_reply_action_summary.get("awaiting_reply_rows", 0),
        "zrc_phase_a_rfq_reply_action_pack_needs_source_rows": zrc_phase_a_reply_action_summary.get("received_needs_source_file_rows", 0),
        "zrc_phase_a_rfq_reply_action_pack_ready_apply_rows": zrc_phase_a_reply_action_summary.get("ready_for_reply_log_apply_rows", 0),
        "zrc_phase_a_rfq_send_cockpit_status": zrc_phase_a_rfq_send_cockpit.get("status"),
        "zrc_phase_a_rfq_send_cockpit_rows": zrc_phase_a_send_cockpit_summary.get("vendor_rows", 0),
        "zrc_phase_a_rfq_send_cockpit_ready_rows": zrc_phase_a_send_cockpit_summary.get("ready_to_use_rows", 0),
        "zrc_phase_a_rfq_send_cockpit_confirmations": zrc_phase_a_send_cockpit_summary.get("confirmation_files_present", 0),
        "zrc_phase_a_rfq_send_cockpit_replies": zrc_phase_a_send_cockpit_summary.get("reply_files_present", 0),
        "zrc_phase_a_rfq_send_cockpit_missing_email": zrc_phase_a_send_cockpit_summary.get("missing_email_rows", 0),
        "zrc_phase_a_rfq_send_cockpit_missing_bundle": zrc_phase_a_send_cockpit_summary.get("missing_bundle_rows", 0),
        "zrc_phase_a_rfq_send_cockpit_html": zrc_phase_a_rfq_send_cockpit.get("generated_artifacts", {}).get("html", ""),
        "zrc_phase_a_quote_selection_status": zrc_phase_a_quote_selection.get("status"),
        "zrc_phase_a_quote_selection_sent_count": zrc_phase_a_quote_selection.get("sent_count", 0),
        "zrc_phase_a_quote_selection_reply_count": zrc_phase_a_quote_selection.get("reply_count", 0),
        "zrc_phase_a_quote_selection_source_backed_reply_count": zrc_phase_a_quote_selection.get("source_backed_reply_count", 0),
        "zrc_phase_a_quote_selection_shortlist_count": zrc_phase_a_quote_selection.get("shortlist_count", 0),
        "zrc_phase_a_execution_authorization_status": zrc_phase_a_execution_authorization.get("status"),
        "zrc_phase_a_execution_authorization_rows": zrc_phase_a_execution_authorization.get("row_count", 0),
        "zrc_phase_a_execution_authorization_valid_rows": zrc_phase_a_execution_authorization.get("valid_authorization_rows", 0),
        "zrc_phase_a_execution_authorization_errors": zrc_phase_a_execution_authorization.get("error_count", 0),
        "zrc_phase_a_execution_release_status": zrc_phase_a_execution_release.get("status"),
        "zrc_phase_a_execution_release_ready": bool(zrc_phase_a_execution_release.get("ready_for_execution_authorization")),
        "zrc_phase_a_execution_release_released": bool(zrc_phase_a_execution_release.get("released_for_execution")),
        "zrc_phase_a_execution_release_blockers": zrc_phase_a_execution_release.get("blocker_count", 0),
        "zrc_phase_a_execution_release_authorization_blockers": zrc_phase_a_execution_release.get("authorization_blocker_count", 0),
        "zrc_phase_a_vendor_return_status": zrc_phase_a_vendor_return.get("status"),
        "zrc_phase_a_vendor_return_rows": zrc_phase_a_vendor_return.get("phase_a_measurements", {}).get("row_count", 0),
        "zrc_phase_a_vendor_return_export_files": zrc_phase_a_vendor_return.get("instrument_export_file_count", 0),
        "zrc_measurement_merge_status": zrc_measurement_merge.get("status"),
        "zrc_measurement_merge_inserted": zrc_merge_stats.get("inserted", 0),
        "zrc_measurement_merge_updated": zrc_merge_stats.get("updated", 0),
        "zrc_measurement_merge_output_rows": zrc_merge_stats.get("total", 0),
        "zrc_run_completeness_status": zrc_run_completeness.get("status"),
        "zrc_run_completeness_measured_known_rows": zrc_run_completeness.get("measured_known_rows", 0),
        "zrc_run_completeness_planned_rows": zrc_run_completeness.get("planned_rows", 0),
        "zrc_validation_result_status": zrc_result_summary.get("status"),
        "zrc_validation_result_rows": zrc_result_summary.get("rows", 0),
        "hybrid_measurement_plan_status": hybrid_status,
        "hybrid_measurement_inhouse_rows": hybrid_inhouse,
        "hybrid_measurement_outsource_rows": hybrid_outsource,
        "hybrid_measurement_provenance_rows": hybrid_provenance,
        "hybrid_measurement_total_rows": hybrid_total,
        "local_capture_pack_status": local_capture_status,
        "local_capture_task_count": local_capture_tasks,
        "local_capture_local_tasks": local_capture_local,
        "local_capture_outsource_tasks": local_capture_outsource,
        "local_capture_provenance_tasks": local_capture_provenance,
        "source_file_manifest_status": source_file_manifest_status,
        "source_file_allowed_root_count": source_file_allowed_roots,
        "source_file_expected_class_count": source_file_expected_classes,
        "source_file_inventory_status": source_file_inventory_status,
        "source_file_inventory_file_count": source_file_inventory_files,
        "source_file_inventory_reference_count": source_file_inventory_refs,
        "source_file_inventory_capture_reference_count": source_file_inventory_capture_refs,
        "source_file_inventory_source_value_reference_count": source_file_inventory_source_value_refs,
        "source_file_inventory_missing_reference_count": source_file_inventory_missing,
        "source_file_inventory_unreferenced_file_count": source_file_inventory_unreferenced,
        "local_capture_preflight_status": local_preflight_status,
        "local_capture_preflight_ready": local_preflight_ready,
        "local_capture_preflight_filled_tasks": local_preflight_filled,
        "local_capture_preflight_pending_tasks": local_preflight_pending,
        "local_capture_preflight_errors": local_preflight_errors,
        "local_capture_preflight_warnings": local_preflight_warnings,
        "smoke_capture_tranche_status": smoke_status,
        "smoke_capture_task_count": smoke_tasks,
        "smoke_capture_local_or_record_tasks": smoke_local_or_record,
        "smoke_capture_outsource_tasks": smoke_outsource,
        "smoke_execution_queue_status": smoke_queue_status,
        "smoke_execution_queue_rows": smoke_queue_rows,
        "smoke_execution_queue_h_a_rows": smoke_queue_h_a_rows,
        "smoke_execution_queue_zrc_rows": smoke_queue_zrc_rows,
        "smoke_execution_queue_awaiting_rows": smoke_queue_awaiting,
        "smoke_execution_queue_source_ready_rows": smoke_queue_source_ready,
        "smoke_entry_sheet_status": smoke_entry_sheet_status,
        "smoke_entry_sheet_rows": smoke_entry_sheet_rows,
        "smoke_entry_sheet_ready_rows": smoke_entry_sheet_ready,
        "smoke_entry_sheet_filled_value_rows": smoke_entry_sheet_filled,
        "smoke_source_drop_status": smoke_source_drop_status,
        "smoke_source_drop_planned_files": smoke_source_drop_planned,
        "smoke_source_drop_dirs": smoke_source_drop_dirs,
        "smoke_source_drop_existing_files": smoke_source_drop_existing,
        "smoke_source_drop_missing_files": smoke_source_drop_missing,
        "smoke_source_values_sheet_status": smoke_source_values_sheet_status,
        "smoke_source_values_sheet_rows": smoke_source_values_sheet_rows,
        "smoke_source_values_sheet_starter_rows": smoke_source_values_sheet_starter,
        "smoke_source_values_sheet_filled_rows": smoke_source_values_sheet_filled,
        "smoke_source_values_sheet_import_ready_rows": smoke_source_values_sheet_import_ready,
        "smoke_starter_batch_readiness_status": smoke_starter_readiness_status,
        "smoke_starter_batch_rows": smoke_starter_rows,
        "smoke_starter_batch_ready_rows": smoke_starter_ready,
        "smoke_starter_batch_blocked_rows": smoke_starter_blocked,
        "smoke_starter_execution_pack_status": smoke_starter_execution_pack_status,
        "smoke_starter_execution_pack_rows": smoke_starter_execution_pack_rows,
        "smoke_starter_execution_pack_dirs": smoke_starter_execution_pack_dirs,
        "smoke_starter_execution_pack_existing_files": smoke_starter_execution_pack_existing,
        "smoke_starter_template_pack_status": smoke_starter_template_pack_status,
        "smoke_starter_template_pack_rows": smoke_starter_template_pack_rows,
        "smoke_starter_template_pack_templates": smoke_starter_template_pack_templates,
        "smoke_raw_csv_extraction_status": smoke_raw_csv_extraction_status,
        "smoke_raw_csv_extraction_files": smoke_raw_csv_extraction_files,
        "smoke_raw_csv_extraction_rows": smoke_raw_csv_extraction_rows,
        "smoke_raw_csv_extraction_errors": smoke_raw_csv_extraction_errors,
        "smoke_unstructured_intake_status": smoke_unstructured_intake_status,
        "smoke_unstructured_intake_rows": smoke_unstructured_intake_rows,
        "smoke_unstructured_intake_ready": smoke_unstructured_intake_ready,
        "smoke_unstructured_intake_missing": smoke_unstructured_intake_missing,
        "smoke_unstructured_intake_invalid": smoke_unstructured_intake_invalid,
        "smoke_unstructured_review_values_status": smoke_unstructured_review_status,
        "smoke_unstructured_review_values_rows": smoke_unstructured_review_rows,
        "smoke_unstructured_review_values_ready_sources": smoke_unstructured_review_ready_sources,
        "smoke_unstructured_review_values_filled_rows": smoke_unstructured_review_filled,
        "smoke_unstructured_review_values_import_ready_rows": smoke_unstructured_review_import_ready,
        "smoke_unstructured_review_values_invalid_sources": smoke_unstructured_review_invalid,
        "smoke_source_value_import_status": smoke_source_value_import_status,
        "smoke_source_value_import_files": smoke_source_value_import_files,
        "smoke_source_value_import_rows": smoke_source_value_import_rows,
        "smoke_source_value_import_imported_rows": smoke_source_value_import_imported,
        "smoke_source_value_import_errors": smoke_source_value_import_errors,
        "smoke_entry_apply_status": smoke_entry_apply_status,
        "smoke_entry_apply_applied_values": smoke_entry_apply_applied,
        "smoke_entry_apply_errors": smoke_entry_apply_errors,
        "smoke_capture_preflight_status": smoke_preflight_status,
        "smoke_capture_preflight_ready": smoke_preflight_ready,
        "smoke_capture_preflight_filled_tasks": smoke_preflight_filled,
        "smoke_capture_preflight_pending_tasks": smoke_preflight_pending,
        "smoke_capture_preflight_errors": smoke_preflight_errors,
        "smoke_capture_preflight_warnings": smoke_preflight_warnings,
        "smoke_rehearsal_status": smoke_rehearsal_status,
        "smoke_rehearsal_preflight_status": smoke_rehearsal_preflight_status,
        "smoke_rehearsal_preflight_ready": smoke_rehearsal_ready,
        "smoke_rehearsal_filled_tasks": smoke_rehearsal_filled,
        "smoke_rehearsal_pending_tasks": smoke_rehearsal_pending,
        "smoke_rehearsal_errors": smoke_rehearsal_errors,
        "smoke_rehearsal_warnings": smoke_rehearsal_warnings,
        "smoke_rehearsal_h_a_qc_status": smoke_rehearsal_h_a_qc,
        "smoke_rehearsal_zrc_validation_status": smoke_rehearsal_zrc_validation,
        "h_a_missing_field_summary": missing_field_summary(h_a),
        "next_measurement_status": next_rows.get("status"),
        "next_measurement_row_count": len(next_rows.get("recommended_rows", [])),
        "variant_ladder_top": ladder.get("items", [{}])[0].get("variant_id") if ladder.get("items") else None,
        "nhi_pedot_claim_blockers": nhi_audit.get("blockers", []),
        "all_candidate_blockers": blocker_summary(claim),
        "evidence_gaps": portfolio_bypass_gaps + gaps + nhi_forward_gaps + zrc_gaps + hybrid_gaps,
        "next_actions": actions,
        "completion_requirements": [
            "H-A acellular medium-integrity and physical-stability rows must be real, non-placeholder, non-synthetic measurements.",
            "H-B electrochemical/physical rows must prove the lead adds electrical value without instability.",
            "H-C neural viability, neurite/morphology, and MEA network rows must be non-inferior to controls.",
            "Long-duration CL1-like MEA/network follow-up must pass on real rows.",
            "The final limina_suitability_claim_audit must report claim_ready true for a candidate.",
        ],
    }


def render_report(state: dict[str, Any]) -> str:
    lines = [
        "# LIMINA Discovery Cycle State",
        "",
        "This report coordinates the current material-discovery loop. It is not a material suitability claim.",
        "",
        f"**Mission state:** `{state['mission_state']}`",
        f"**Reason:** {state['state_reason']}",
        f"**Claim ready:** `{state['claim_ready']}`",
        f"**Claim status:** `{state.get('claim_status', '-')}`",
        f"**Active candidate:** `{state.get('active_discovery_candidate', '-')}`",
        f"**Active priority:** `{state.get('active_discovery_priority', '-')}`",
        f"**Active score:** `{state.get('active_discovery_score', '-')}`",
        f"**First-wave RFQ dispatch cockpit:** `{state.get('first_wave_rfq_dispatch_cockpit_status', '-')}`; rows={state.get('first_wave_rfq_dispatch_cockpit_rows', '-')}; ready={state.get('first_wave_rfq_dispatch_cockpit_ready_rows', '-')}; confirmations={state.get('first_wave_rfq_dispatch_cockpit_confirmations', '-')}; replies={state.get('first_wave_rfq_dispatch_cockpit_replies', '-')}; html={state.get('first_wave_rfq_dispatch_cockpit_html', '-')}",
        f"**First-wave post-dispatch processing:** `{state.get('first_wave_post_dispatch_status', '-')}`; failed_commands={state.get('first_wave_post_dispatch_failed_commands', '-')}; confirmations={state.get('first_wave_post_dispatch_confirmations', '-')}; replies={state.get('first_wave_post_dispatch_replies', '-')}",
        f"**Second-wave candidate queue:** `{state.get('second_wave_candidate_queue_status', '-')}`; rows={state.get('second_wave_candidate_queue_rows', '-')}; ready_scope_lock={state.get('second_wave_candidate_queue_ready_scope_lock_rows', '-')}; watch={state.get('second_wave_candidate_queue_watch_rows', '-')}; hold={state.get('second_wave_candidate_queue_hold_rows', '-')}",
        f"**Second-wave scope-lock pack:** `{state.get('second_wave_scope_lock_pack_status', '-')}`; ready_candidates={state.get('second_wave_scope_lock_pack_ready_candidates', '-')}; tasks={state.get('second_wave_scope_lock_pack_tasks', '-')}; source_classes={state.get('second_wave_scope_lock_pack_source_classes', '-')}; claim_evidence_created={str(state.get('second_wave_scope_lock_pack_claim_evidence_created', '-')).lower()}",
        f"**Portfolio bypass audit:** `{state.get('portfolio_bypass_status', '-')}`; non_H-A_claim_ready={state.get('portfolio_bypass_non_h_a_claim_ready_rows', '-')}; top_non_H-A={state.get('portfolio_bypass_top_non_h_a_candidate') or '-'}",
        f"**H-A status:** `{state.get('h_a_status', '-')}`",
        f"**H-A bench sheet:** `{state.get('h_a_bench_status', '-')}`",
        f"**H-A raw merge:** `{state.get('h_a_measurement_merge_status', '-')}`",
        f"**H-A intake QC:** `{state.get('h_a_intake_qc_status', '-')}`",
        f"**H-A service request:** `{state.get('h_a_service_request_status', '-')}`",
        f"**H-A sample handoff:** `{state.get('h_a_chain_of_custody_status', '-')}`; labels={state.get('h_a_sample_label_count', '-')}; custody_rows={state.get('h_a_chain_of_custody_rows', '-')}",
        f"**H-A sample submission:** `{state.get('h_a_sample_submission_status', '-')}`; shipping={state.get('h_a_sample_submission_shipping_status', '-')}",
        f"**H-A split-scope plan:** `{state.get('h_a_split_scope_status', '-')}`; pairs={state.get('h_a_split_scope_pair_count', '-')}; preferred={state.get('h_a_split_scope_preferred_count', '-')}",
        f"**H-A vendor outreach:** `{state.get('h_a_vendor_outreach_status', '-')}`",
        f"**H-A RFQ packet:** `{state.get('h_a_rfq_packet_status', '-')}`",
        f"**H-A RFQ outbox:** `{state.get('h_a_rfq_outbox_status', '-')}`; ready={state.get('h_a_rfq_outbox_ready_count', '-')} / {state.get('h_a_rfq_outbox_quote_count', '-')}",
        f"**H-A RFQ EML drafts:** `{state.get('h_a_rfq_eml_drafts_status', '-')}`; rows={state.get('h_a_rfq_eml_drafts_rows', '-')}; ready={state.get('h_a_rfq_eml_drafts_ready_rows', '-')}; missing_to={state.get('h_a_rfq_eml_drafts_missing_to_rows', '-')}; missing_bundle={state.get('h_a_rfq_eml_drafts_missing_bundle_rows', '-')}",
        f"**H-A RFQ EML integrity audit:** `{state.get('h_a_rfq_eml_integrity_status', '-')}`; rows={state.get('h_a_rfq_eml_integrity_rows', '-')}; pass={state.get('h_a_rfq_eml_integrity_pass_rows', '-')}; fail={state.get('h_a_rfq_eml_integrity_fail_rows', '-')}; attachment_mismatch={state.get('h_a_rfq_eml_integrity_attachment_mismatch_rows', '-')}",
        f"**H-A quote tracker:** `{state.get('h_a_quote_tracker_status', '-')}`",
        f"**H-A RFQ send action pack:** `{state.get('h_a_rfq_send_action_pack_status', '-')}`; rows={state.get('h_a_rfq_send_action_pack_rows', '-')}; ready={state.get('h_a_rfq_send_action_pack_ready_rows', '-')}; verified={state.get('h_a_rfq_send_action_pack_verified_rows', '-')}; needs_confirmation={state.get('h_a_rfq_send_action_pack_needs_confirmation_rows', '-')}",
        f"**H-A RFQ dispatch manifest:** `{state.get('h_a_rfq_dispatch_manifest_status', '-')}`; rows={state.get('h_a_rfq_dispatch_manifest_rows', '-')}; ready={state.get('h_a_rfq_dispatch_manifest_ready_rows', '-')}; blocked={state.get('h_a_rfq_dispatch_manifest_blocked_rows', '-')}; bundle_matches={state.get('h_a_rfq_dispatch_manifest_bundle_match_rows', '-')}",
        f"**H-A RFQ send cockpit:** `{state.get('h_a_rfq_send_cockpit_status', '-')}`; rows={state.get('h_a_rfq_send_cockpit_rows', '-')}; ready={state.get('h_a_rfq_send_cockpit_ready_rows', '-')}; confirmations={state.get('h_a_rfq_send_cockpit_confirmations', '-')}; replies={state.get('h_a_rfq_send_cockpit_replies', '-')}; missing_eml={state.get('h_a_rfq_send_cockpit_missing_eml', '-')}; missing_bundle={state.get('h_a_rfq_send_cockpit_missing_bundle', '-')}; html={state.get('h_a_rfq_send_cockpit_html', '-')}",
        f"**H-A RFQ dispatch archive:** `{state.get('h_a_rfq_dispatch_archive_status', '-')}`; files={state.get('h_a_rfq_dispatch_archive_files', '-')}; missing={state.get('h_a_rfq_dispatch_archive_missing_files', '-')}; hash_mismatches={state.get('h_a_rfq_dispatch_archive_hash_mismatches', '-')}; archive={state.get('h_a_rfq_dispatch_archive_path', '-')}; sha256={state.get('h_a_rfq_dispatch_archive_sha256', '-')}",
        f"**H-A RFQ send confirmation intake:** `{state.get('h_a_rfq_send_confirmation_intake_status', '-')}`; files={state.get('h_a_rfq_send_confirmation_intake_files', '-')}; applied={state.get('h_a_rfq_send_confirmation_intake_applied_rows', '-')}; needs_review={state.get('h_a_rfq_send_confirmation_intake_needs_review_rows', '-')}; bundle_matched={state.get('h_a_rfq_send_confirmation_intake_bundle_matched_rows', '-')}",
        f"**H-A RFQ send confirmation entry sheet:** `{state.get('h_a_rfq_send_confirmation_entry_sheet_status', '-')}`; rows={state.get('h_a_rfq_send_confirmation_entry_sheet_rows', '-')}; source_files={state.get('h_a_rfq_send_confirmation_entry_sheet_source_files', '-')}; ready={state.get('h_a_rfq_send_confirmation_entry_sheet_ready_rows', '-')}; blocked={state.get('h_a_rfq_send_confirmation_entry_sheet_blocked_rows', '-')}",
        f"**H-A RFQ send confirmation entry apply:** `{state.get('h_a_rfq_send_confirmation_entry_apply_status', '-')}`; apply_rows={state.get('h_a_rfq_send_confirmation_entry_apply_rows', '-')}; applied={state.get('h_a_rfq_send_confirmation_entry_apply_applied_rows', '-')}; blocked={state.get('h_a_rfq_send_confirmation_entry_apply_blocked_rows', '-')}",
        f"**H-A RFQ send log:** `{state.get('h_a_rfq_send_log_status', '-')}`; rows={state.get('h_a_rfq_send_log_rows', '-')}; sent={state.get('h_a_rfq_send_log_sent_rows', '-')}; valid={state.get('h_a_rfq_send_log_valid_sent_rows', '-')}; applied_dates={state.get('h_a_rfq_send_log_applied_dates', '-')}; errors={state.get('h_a_rfq_send_log_errors', '-')}",
        f"**H-A RFQ reply intake:** `{state.get('h_a_rfq_reply_intake_status', '-')}`; files={state.get('h_a_rfq_reply_intake_files', '-')}; applied={state.get('h_a_rfq_reply_intake_applied_rows', '-')}; needs_review={state.get('h_a_rfq_reply_intake_needs_review_rows', '-')}; needs_verified_send={state.get('h_a_rfq_reply_intake_needs_verified_send_rows', '-')}",
        f"**H-A RFQ reply log:** `{state.get('h_a_rfq_reply_log_status', '-')}`; rows={state.get('h_a_rfq_reply_log_rows', '-')}; received={state.get('h_a_rfq_reply_log_received_rows', '-')}; valid={state.get('h_a_rfq_reply_log_valid_rows', '-')}; applied_fields={state.get('h_a_rfq_reply_log_applied_fields', '-')}; errors={state.get('h_a_rfq_reply_log_errors', '-')}",
        f"**H-A vendor contact source audit:** `{state.get('h_a_vendor_contact_source_audit_status', '-')}`; rows={state.get('h_a_vendor_contact_source_audit_rows', '-')}; pass={state.get('h_a_vendor_contact_source_audit_pass_rows', '-')}; fail={state.get('h_a_vendor_contact_source_audit_fail_rows', '-')}; stale={state.get('h_a_vendor_contact_source_audit_stale_rows', '-')}",
        f"**H-A RFQ reply action pack:** `{state.get('h_a_rfq_reply_action_pack_status', '-')}`; rows={state.get('h_a_rfq_reply_action_pack_rows', '-')}; waiting_send={state.get('h_a_rfq_reply_action_pack_waiting_send_rows', '-')}; awaiting_reply={state.get('h_a_rfq_reply_action_pack_awaiting_reply_rows', '-')}; needs_source={state.get('h_a_rfq_reply_action_pack_needs_source_rows', '-')}; ready_apply={state.get('h_a_rfq_reply_action_pack_ready_apply_rows', '-')}",
        f"**H-A vendor contact plan:** `{state.get('h_a_vendor_contact_plan_status', '-')}`; ready_first_wave={state.get('h_a_vendor_contact_ready_count', '-')}; standby_second_wave={state.get('h_a_vendor_contact_standby_count', '-')}; total={state.get('h_a_vendor_contact_row_count', '-')}",
        f"**H-A quote selection:** `{state.get('h_a_quote_selection_status', '-')}`; replies={state.get('h_a_quote_selection_reply_count', '-')}; source_backed_replies={state.get('h_a_quote_selection_source_backed_reply_count', '-')}; shortlisted={state.get('h_a_quote_selection_shortlist_count', '-')}",
        f"**H-A execution authorization log:** `{state.get('h_a_execution_authorization_status', '-')}`; rows={state.get('h_a_execution_authorization_rows', '-')}; valid={state.get('h_a_execution_authorization_valid_rows', '-')}; errors={state.get('h_a_execution_authorization_errors', '-')}",
        f"**H-A execution release audit:** `{state.get('h_a_execution_release_status', '-')}`; ready={str(state.get('h_a_execution_release_ready', False)).lower()}; released={str(state.get('h_a_execution_release_released', False)).lower()}; blockers={state.get('h_a_execution_release_blockers', '-')}; authorization_blockers={state.get('h_a_execution_release_authorization_blockers', '-')}",
        f"**H-A vendor return intake:** `{state.get('h_a_vendor_return_status', '-')}`; raw_value_rows={state.get('h_a_vendor_return_raw_value_rows', '-')}; bundle_rows={state.get('h_a_vendor_return_bundle_rows', '-')}; bundle_apply_rows={state.get('h_a_vendor_return_bundle_apply_rows', '-')}; exports={state.get('h_a_vendor_return_export_files', '-')}",
        f"**H-A vendor bundle entry sheet:** `{state.get('h_a_vendor_bundle_entry_sheet_status', '-')}`; bundles={state.get('h_a_vendor_bundle_entry_sheet_bundles', '-')}; ready={state.get('h_a_vendor_bundle_entry_sheet_ready_rows', '-')}; blocked={state.get('h_a_vendor_bundle_entry_sheet_blocked_rows', '-')}",
        f"**H-A vendor bundle entry return apply:** `{state.get('h_a_vendor_bundle_entry_apply_status', '-')}`; sheet_exists={str(state.get('h_a_vendor_bundle_entry_apply_sheet_exists', False)).lower()}; bundles={state.get('h_a_vendor_bundle_entry_apply_bundles', '-')}; source_rows={state.get('h_a_vendor_bundle_entry_apply_source_rows', '-')}; errors={state.get('h_a_vendor_bundle_entry_apply_errors', '-')}",
        f"**H-A source values sheet:** `{state.get('h_a_source_values_sheet_status', '-')}`; rows={state.get('h_a_source_values_sheet_rows', '-')}; filled={state.get('h_a_source_values_sheet_filled_rows', '-')}; source_files={state.get('h_a_source_values_sheet_source_file_exists_rows', '-')}; import_ready={state.get('h_a_source_values_sheet_import_ready_rows', '-')}",
        f"**H-A source drop plan:** `{state.get('h_a_source_drop_status', '-')}`; planned_files={state.get('h_a_source_drop_planned_files', '-')}; dirs={state.get('h_a_source_drop_dirs', '-')}; existing_files={state.get('h_a_source_drop_existing_files', '-')}; missing_files={state.get('h_a_source_drop_missing_files', '-')}",
        f"**H-A raw CSV extraction:** `{state.get('h_a_raw_csv_extraction_status', '-')}`; files={state.get('h_a_raw_csv_extraction_files', '-')}; rows={state.get('h_a_raw_csv_extraction_rows', '-')}; errors={state.get('h_a_raw_csv_extraction_errors', '-')}",
        f"**H-A source value import:** `{state.get('h_a_source_value_import_status', '-')}`; files={state.get('h_a_source_value_import_files', '-')}; rows={state.get('h_a_source_value_import_rows', '-')}; imported={state.get('h_a_source_value_import_imported_rows', '-')}; errors={state.get('h_a_source_value_import_errors', '-')}",
        f"**NHI-PEDOT H-B/H-C package:** `{state.get('nhi_forward_status', '-')}`; rows={state.get('nhi_forward_rows', '-')}",
        f"**NHI-PEDOT H-B/H-C source values:** `{state.get('nhi_forward_source_values_status', '-')}`; rows={state.get('nhi_forward_source_values_rows', '-')}; filled={state.get('nhi_forward_source_values_filled_rows', '-')}; source_files={state.get('nhi_forward_source_values_source_file_exists_rows', '-')}; import_ready={state.get('nhi_forward_source_values_import_ready_rows', '-')}",
        f"**NHI-PEDOT H-B/H-C source drop plan:** `{state.get('nhi_forward_source_drop_status', '-')}`; planned_files={state.get('nhi_forward_source_drop_planned_files', '-')}; dirs={state.get('nhi_forward_source_drop_dirs', '-')}; existing_files={state.get('nhi_forward_source_drop_existing_files', '-')}; missing_files={state.get('nhi_forward_source_drop_missing_files', '-')}",
        f"**NHI-PEDOT H-B/H-C source file templates:** `{state.get('nhi_forward_source_template_pack_status', '-')}`; templates={state.get('nhi_forward_source_template_pack_templates', '-')}; target_files={state.get('nhi_forward_source_template_pack_target_files', '-')}",
        f"**NHI-PEDOT H-B/H-C raw CSV extraction:** `{state.get('nhi_forward_raw_csv_extraction_status', '-')}`; files={state.get('nhi_forward_raw_csv_extraction_files', '-')}; rows={state.get('nhi_forward_raw_csv_extraction_rows', '-')}; errors={state.get('nhi_forward_raw_csv_extraction_errors', '-')}",
        f"**NHI-PEDOT H-B/H-C source import:** `{state.get('nhi_forward_source_import_status', '-')}`; files={state.get('nhi_forward_source_import_files', '-')}; rows={state.get('nhi_forward_source_import_rows', '-')}; imported={state.get('nhi_forward_source_import_imported_rows', '-')}; errors={state.get('nhi_forward_source_import_errors', '-')}",
        f"**NHI-PEDOT coupon results:** `{state.get('nhi_coupon_result_status', '-')}`; rows={state.get('nhi_coupon_result_rows', '-')}",
        f"**NHI-PEDOT long-duration source values:** `{state.get('nhi_long_source_values_status', '-')}`; rows={state.get('nhi_long_source_values_rows', '-')}; filled={state.get('nhi_long_source_values_filled_rows', '-')}; source_files={state.get('nhi_long_source_values_source_file_exists_rows', '-')}; import_ready={state.get('nhi_long_source_values_import_ready_rows', '-')}",
        f"**NHI-PEDOT long-duration source drop plan:** `{state.get('nhi_long_source_drop_status', '-')}`; planned_files={state.get('nhi_long_source_drop_planned_files', '-')}; dirs={state.get('nhi_long_source_drop_dirs', '-')}; existing_files={state.get('nhi_long_source_drop_existing_files', '-')}; missing_files={state.get('nhi_long_source_drop_missing_files', '-')}",
        f"**NHI-PEDOT long-duration source file templates:** `{state.get('nhi_long_source_template_pack_status', '-')}`; templates={state.get('nhi_long_source_template_pack_templates', '-')}; target_files={state.get('nhi_long_source_template_pack_target_files', '-')}",
        f"**NHI-PEDOT long-duration raw CSV extraction:** `{state.get('nhi_long_raw_csv_extraction_status', '-')}`; files={state.get('nhi_long_raw_csv_extraction_files', '-')}; rows={state.get('nhi_long_raw_csv_extraction_rows', '-')}; errors={state.get('nhi_long_raw_csv_extraction_errors', '-')}",
        f"**NHI-PEDOT long-duration source import:** `{state.get('nhi_long_source_import_status', '-')}`; files={state.get('nhi_long_source_import_files', '-')}; rows={state.get('nhi_long_source_import_rows', '-')}; imported={state.get('nhi_long_source_import_imported_rows', '-')}; errors={state.get('nhi_long_source_import_errors', '-')}",
        f"**NHI-PEDOT long-duration results:** `{state.get('nhi_long_result_status', '-')}`; rows={state.get('nhi_long_result_rows', '-')}",
        f"**Hybrid measurement routing:** `{state.get('hybrid_measurement_plan_status', '-')}`; local={state.get('hybrid_measurement_inhouse_rows', '-')}; outsource_preferred={state.get('hybrid_measurement_outsource_rows', '-')}; provenance={state.get('hybrid_measurement_provenance_rows', '-')}; total={state.get('hybrid_measurement_total_rows', '-')}",
        f"**Local capture pack:** `{state.get('local_capture_pack_status', '-')}`; tasks={state.get('local_capture_task_count', '-')}; local={state.get('local_capture_local_tasks', '-')}; outsource={state.get('local_capture_outsource_tasks', '-')}; provenance={state.get('local_capture_provenance_tasks', '-')}",
        f"**Source-file manifest:** `{state.get('source_file_manifest_status', '-')}`; allowed_roots={state.get('source_file_allowed_root_count', '-')}; source_classes={state.get('source_file_expected_class_count', '-')}",
        f"**Source-file inventory:** `{state.get('source_file_inventory_status', '-')}`; files={state.get('source_file_inventory_file_count', '-')}; refs={state.get('source_file_inventory_reference_count', '-')}; capture_refs={state.get('source_file_inventory_capture_reference_count', '-')}; filled_source_value_refs={state.get('source_file_inventory_source_value_reference_count', '-')}; missing_refs={state.get('source_file_inventory_missing_reference_count', '-')}; unreferenced={state.get('source_file_inventory_unreferenced_file_count', '-')}",
        f"**Local capture preflight:** `{state.get('local_capture_preflight_status', '-')}`; ready={str(state.get('local_capture_preflight_ready', False)).lower()}; filled={state.get('local_capture_preflight_filled_tasks', '-')}; pending={state.get('local_capture_preflight_pending_tasks', '-')}; errors={state.get('local_capture_preflight_errors', '-')}; warnings={state.get('local_capture_preflight_warnings', '-')}",
        f"**Smoke capture tranche:** `{state.get('smoke_capture_tranche_status', '-')}`; tasks={state.get('smoke_capture_task_count', '-')}; local_or_record={state.get('smoke_capture_local_or_record_tasks', '-')}; outsource={state.get('smoke_capture_outsource_tasks', '-')}",
        f"**Smoke execution queue:** `{state.get('smoke_execution_queue_status', '-')}`; rows={state.get('smoke_execution_queue_rows', '-')}; H-A={state.get('smoke_execution_queue_h_a_rows', '-')}; ZRC={state.get('smoke_execution_queue_zrc_rows', '-')}; awaiting={state.get('smoke_execution_queue_awaiting_rows', '-')}; source_ready={state.get('smoke_execution_queue_source_ready_rows', '-')}",
        f"**Smoke entry sheet:** `{state.get('smoke_entry_sheet_status', '-')}`; rows={state.get('smoke_entry_sheet_rows', '-')}; filled={state.get('smoke_entry_sheet_filled_value_rows', '-')}; ready_to_apply={state.get('smoke_entry_sheet_ready_rows', '-')}",
        f"**Smoke source drop plan:** `{state.get('smoke_source_drop_status', '-')}`; planned_files={state.get('smoke_source_drop_planned_files', '-')}; dirs={state.get('smoke_source_drop_dirs', '-')}; existing_files={state.get('smoke_source_drop_existing_files', '-')}; missing_files={state.get('smoke_source_drop_missing_files', '-')}",
        f"**Smoke source values sheet:** `{state.get('smoke_source_values_sheet_status', '-')}`; rows={state.get('smoke_source_values_sheet_rows', '-')}; starter={state.get('smoke_source_values_sheet_starter_rows', '-')}; filled={state.get('smoke_source_values_sheet_filled_rows', '-')}; import_ready={state.get('smoke_source_values_sheet_import_ready_rows', '-')}",
        f"**Smoke starter batch readiness:** `{state.get('smoke_starter_batch_readiness_status', '-')}`; rows={state.get('smoke_starter_batch_rows', '-')}; ready={state.get('smoke_starter_batch_ready_rows', '-')}; blocked={state.get('smoke_starter_batch_blocked_rows', '-')}",
        f"**Smoke starter execution pack:** `{state.get('smoke_starter_execution_pack_status', '-')}`; rows={state.get('smoke_starter_execution_pack_rows', '-')}; dirs={state.get('smoke_starter_execution_pack_dirs', '-')}; existing_files={state.get('smoke_starter_execution_pack_existing_files', '-')}",
        f"**Smoke starter raw-file templates:** `{state.get('smoke_starter_template_pack_status', '-')}`; rows={state.get('smoke_starter_template_pack_rows', '-')}; templates={state.get('smoke_starter_template_pack_templates', '-')}",
        f"**Smoke raw CSV extraction:** `{state.get('smoke_raw_csv_extraction_status', '-')}`; files={state.get('smoke_raw_csv_extraction_files', '-')}; rows={state.get('smoke_raw_csv_extraction_rows', '-')}; errors={state.get('smoke_raw_csv_extraction_errors', '-')}",
        f"**Smoke unstructured source intake:** `{state.get('smoke_unstructured_intake_status', '-')}`; rows={state.get('smoke_unstructured_intake_rows', '-')}; ready={state.get('smoke_unstructured_intake_ready', '-')}; missing={state.get('smoke_unstructured_intake_missing', '-')}; invalid={state.get('smoke_unstructured_intake_invalid', '-')}",
        f"**Smoke unstructured review values:** `{state.get('smoke_unstructured_review_values_status', '-')}`; rows={state.get('smoke_unstructured_review_values_rows', '-')}; ready_sources={state.get('smoke_unstructured_review_values_ready_sources', '-')}; filled={state.get('smoke_unstructured_review_values_filled_rows', '-')}; import_ready={state.get('smoke_unstructured_review_values_import_ready_rows', '-')}; invalid_sources={state.get('smoke_unstructured_review_values_invalid_sources', '-')}",
        f"**Smoke source value import:** `{state.get('smoke_source_value_import_status', '-')}`; files={state.get('smoke_source_value_import_files', '-')}; rows={state.get('smoke_source_value_import_rows', '-')}; imported={state.get('smoke_source_value_import_imported_rows', '-')}; errors={state.get('smoke_source_value_import_errors', '-')}",
        f"**Smoke entry apply:** `{state.get('smoke_entry_apply_status', '-')}`; applied={state.get('smoke_entry_apply_applied_values', '-')}; errors={state.get('smoke_entry_apply_errors', '-')}",
        f"**Smoke capture preflight:** `{state.get('smoke_capture_preflight_status', '-')}`; ready={str(state.get('smoke_capture_preflight_ready', False)).lower()}; filled={state.get('smoke_capture_preflight_filled_tasks', '-')}; pending={state.get('smoke_capture_preflight_pending_tasks', '-')}; errors={state.get('smoke_capture_preflight_errors', '-')}; warnings={state.get('smoke_capture_preflight_warnings', '-')}",
        f"**Smoke rehearsal:** `{state.get('smoke_rehearsal_status', '-')}`; preflight={state.get('smoke_rehearsal_preflight_status', '-')}; ready={str(state.get('smoke_rehearsal_preflight_ready', False)).lower()}; filled={state.get('smoke_rehearsal_filled_tasks', '-')}; pending={state.get('smoke_rehearsal_pending_tasks', '-')}; H-A_QC={state.get('smoke_rehearsal_h_a_qc_status', '-')}; ZRC_validation={state.get('smoke_rehearsal_zrc_validation_status', '-')}",
        f"**ZRC-ND readiness:** `{state.get('zrc_readiness', '-')}`; suitable={str(state.get('zrc_suitable', False)).lower()}",
        f"**ZRC-ND Phase A sentinel:** `{state.get('zrc_sentinel_status', '-')}`; rows={state.get('zrc_sentinel_rows', '-')}",
        f"**ZRC-ND next measurements:** `{state.get('zrc_next_status', '-')}`; recommended_rows={state.get('zrc_next_recommended_rows', '-')}",
        f"**ZRC-ND Phase A source values:** `{state.get('zrc_phase_a_source_values_status', '-')}`; rows={state.get('zrc_phase_a_source_values_rows', '-')}; filled={state.get('zrc_phase_a_source_values_filled_rows', '-')}; import_ready={state.get('zrc_phase_a_source_values_import_ready_rows', '-')}",
        f"**ZRC-ND Phase A source drop plan:** `{state.get('zrc_phase_a_source_drop_status', '-')}`; planned_files={state.get('zrc_phase_a_source_drop_planned_files', '-')}; dirs={state.get('zrc_phase_a_source_drop_dirs', '-')}; existing_files={state.get('zrc_phase_a_source_drop_existing_files', '-')}; missing_files={state.get('zrc_phase_a_source_drop_missing_files', '-')}",
        f"**ZRC-ND Phase A source file templates:** `{state.get('zrc_phase_a_source_template_pack_status', '-')}`; templates={state.get('zrc_phase_a_source_template_pack_templates', '-')}; target_files={state.get('zrc_phase_a_source_template_pack_target_files', '-')}",
        f"**ZRC-ND Phase A vendor bundle entry sheet:** `{state.get('zrc_phase_a_vendor_bundle_entry_sheet_status', '-')}`; bundles={state.get('zrc_phase_a_vendor_bundle_entry_sheet_bundles', '-')}; ready={state.get('zrc_phase_a_vendor_bundle_entry_sheet_ready_rows', '-')}; blocked={state.get('zrc_phase_a_vendor_bundle_entry_sheet_blocked_rows', '-')}",
        f"**ZRC-ND Phase A vendor bundle entry apply:** `{state.get('zrc_phase_a_vendor_bundle_entry_apply_status', '-')}`; apply_rows={state.get('zrc_phase_a_vendor_bundle_entry_apply_rows', '-')}; bundles={state.get('zrc_phase_a_vendor_bundle_entry_apply_bundles', '-')}; source_rows={state.get('zrc_phase_a_vendor_bundle_entry_apply_source_rows', '-')}; errors={state.get('zrc_phase_a_vendor_bundle_entry_apply_errors', '-')}",
        f"**ZRC-ND Phase A raw CSV extraction:** `{state.get('zrc_phase_a_raw_csv_extraction_status', '-')}`; files={state.get('zrc_phase_a_raw_csv_extraction_files', '-')}; rows={state.get('zrc_phase_a_raw_csv_extraction_rows', '-')}; errors={state.get('zrc_phase_a_raw_csv_extraction_errors', '-')}",
        f"**ZRC-ND Phase A source import:** `{state.get('zrc_phase_a_source_import_status', '-')}`; rows={state.get('zrc_phase_a_source_import_rows', '-')}; imported={state.get('zrc_phase_a_source_import_imported_rows', '-')}; errors={state.get('zrc_phase_a_source_import_errors', '-')}",
        f"**ZRC-ND Phase A service request:** `{state.get('zrc_phase_a_service_status', '-')}`; runs={state.get('zrc_phase_a_service_runs', '-')}",
        f"**ZRC-ND Phase A sample handoff:** `{state.get('zrc_phase_a_chain_status', '-')}`; labels={state.get('zrc_phase_a_sample_label_count', '-')}; custody_rows={state.get('zrc_phase_a_chain_rows', '-')}",
        f"**ZRC-ND Phase A delivery package:** `{state.get('zrc_phase_a_delivery_status', '-')}`; missing_files={state.get('zrc_phase_a_delivery_missing_files', '-')}",
        f"**ZRC-ND Phase A vendor outreach:** `{state.get('zrc_phase_a_vendor_outreach_status', '-')}`; first_wave={state.get('zrc_phase_a_vendor_first_wave_count', '-')}",
        f"**ZRC-ND Phase A RFQ packet:** `{state.get('zrc_phase_a_rfq_status', '-')}`",
        f"**ZRC-ND Phase A RFQ outbox:** `{state.get('zrc_phase_a_rfq_outbox_status', '-')}`; ready={state.get('zrc_phase_a_rfq_outbox_ready_count', '-')} / {state.get('zrc_phase_a_rfq_outbox_quote_count', '-')}",
        f"**ZRC-ND Phase A quote tracker:** `{state.get('zrc_phase_a_quote_tracker_status', '-')}`",
        f"**ZRC-ND Phase A RFQ send confirmation intake:** `{state.get('zrc_phase_a_rfq_send_confirmation_intake_status', '-')}`; files={state.get('zrc_phase_a_rfq_send_confirmation_intake_files', '-')}; applied={state.get('zrc_phase_a_rfq_send_confirmation_intake_applied_rows', '-')}; needs_review={state.get('zrc_phase_a_rfq_send_confirmation_intake_needs_review_rows', '-')}; bundle_matched={state.get('zrc_phase_a_rfq_send_confirmation_intake_bundle_matched_rows', '-')}",
        f"**ZRC-ND Phase A RFQ send confirmation entry sheet:** `{state.get('zrc_phase_a_rfq_send_confirmation_entry_sheet_status', '-')}`; rows={state.get('zrc_phase_a_rfq_send_confirmation_entry_sheet_rows', '-')}; source_files={state.get('zrc_phase_a_rfq_send_confirmation_entry_sheet_source_files', '-')}; ready={state.get('zrc_phase_a_rfq_send_confirmation_entry_sheet_ready_rows', '-')}; blocked={state.get('zrc_phase_a_rfq_send_confirmation_entry_sheet_blocked_rows', '-')}",
        f"**ZRC-ND Phase A RFQ send confirmation entry apply:** `{state.get('zrc_phase_a_rfq_send_confirmation_entry_apply_status', '-')}`; apply_rows={state.get('zrc_phase_a_rfq_send_confirmation_entry_apply_rows', '-')}; applied={state.get('zrc_phase_a_rfq_send_confirmation_entry_apply_applied_rows', '-')}; blocked={state.get('zrc_phase_a_rfq_send_confirmation_entry_apply_blocked_rows', '-')}",
        f"**ZRC-ND Phase A RFQ send log:** `{state.get('zrc_phase_a_rfq_send_log_status', '-')}`; rows={state.get('zrc_phase_a_rfq_send_log_rows', '-')}; sent={state.get('zrc_phase_a_rfq_send_log_sent_rows', '-')}; valid={state.get('zrc_phase_a_rfq_send_log_valid_sent_rows', '-')}; applied_dates={state.get('zrc_phase_a_rfq_send_log_applied_dates', '-')}; errors={state.get('zrc_phase_a_rfq_send_log_errors', '-')}",
        f"**ZRC-ND Phase A RFQ reply intake:** `{state.get('zrc_phase_a_rfq_reply_intake_status', '-')}`; files={state.get('zrc_phase_a_rfq_reply_intake_files', '-')}; applied={state.get('zrc_phase_a_rfq_reply_intake_applied_rows', '-')}; needs_review={state.get('zrc_phase_a_rfq_reply_intake_needs_review_rows', '-')}; needs_verified_send={state.get('zrc_phase_a_rfq_reply_intake_needs_verified_send_rows', '-')}",
        f"**ZRC-ND Phase A RFQ reply log:** `{state.get('zrc_phase_a_rfq_reply_log_status', '-')}`; rows={state.get('zrc_phase_a_rfq_reply_log_rows', '-')}; received={state.get('zrc_phase_a_rfq_reply_log_received_rows', '-')}; valid={state.get('zrc_phase_a_rfq_reply_log_valid_rows', '-')}; applied_fields={state.get('zrc_phase_a_rfq_reply_log_applied_fields', '-')}; errors={state.get('zrc_phase_a_rfq_reply_log_errors', '-')}",
        f"**ZRC-ND Phase A vendor contact plan:** `{state.get('zrc_phase_a_contact_plan_status', '-')}`; ready_first_wave={state.get('zrc_phase_a_contact_ready_count', '-')}; standby_second_wave={state.get('zrc_phase_a_contact_standby_count', '-')}; total={state.get('zrc_phase_a_contact_row_count', '-')}",
        f"**ZRC-ND Phase A RFQ dispatch manifest:** `{state.get('zrc_phase_a_rfq_dispatch_manifest_status', '-')}`; rows={state.get('zrc_phase_a_rfq_dispatch_manifest_rows', '-')}; ready={state.get('zrc_phase_a_rfq_dispatch_manifest_ready_rows', '-')}; blocked={state.get('zrc_phase_a_rfq_dispatch_manifest_blocked_rows', '-')}",
        f"**ZRC-ND Phase A RFQ dispatch archive:** `{state.get('zrc_phase_a_rfq_dispatch_archive_status', '-')}`; files={state.get('zrc_phase_a_rfq_dispatch_archive_files', '-')}; missing={state.get('zrc_phase_a_rfq_dispatch_archive_missing_files', '-')}; hash_mismatches={state.get('zrc_phase_a_rfq_dispatch_archive_hash_mismatches', '-')}; archive={state.get('zrc_phase_a_rfq_dispatch_archive_path', '-')}; sha256={state.get('zrc_phase_a_rfq_dispatch_archive_sha256', '-')}",
        f"**ZRC-ND Phase A RFQ reply action pack:** `{state.get('zrc_phase_a_rfq_reply_action_pack_status', '-')}`; rows={state.get('zrc_phase_a_rfq_reply_action_pack_rows', '-')}; waiting_send={state.get('zrc_phase_a_rfq_reply_action_pack_waiting_send_rows', '-')}; awaiting_reply={state.get('zrc_phase_a_rfq_reply_action_pack_awaiting_reply_rows', '-')}; needs_source={state.get('zrc_phase_a_rfq_reply_action_pack_needs_source_rows', '-')}; ready_apply={state.get('zrc_phase_a_rfq_reply_action_pack_ready_apply_rows', '-')}",
        f"**ZRC-ND Phase A RFQ send cockpit:** `{state.get('zrc_phase_a_rfq_send_cockpit_status', '-')}`; rows={state.get('zrc_phase_a_rfq_send_cockpit_rows', '-')}; ready={state.get('zrc_phase_a_rfq_send_cockpit_ready_rows', '-')}; confirmations={state.get('zrc_phase_a_rfq_send_cockpit_confirmations', '-')}; replies={state.get('zrc_phase_a_rfq_send_cockpit_replies', '-')}; missing_email={state.get('zrc_phase_a_rfq_send_cockpit_missing_email', '-')}; missing_bundle={state.get('zrc_phase_a_rfq_send_cockpit_missing_bundle', '-')}; html={state.get('zrc_phase_a_rfq_send_cockpit_html', '-')}",
        f"**ZRC-ND Phase A quote selection:** `{state.get('zrc_phase_a_quote_selection_status', '-')}`; replies={state.get('zrc_phase_a_quote_selection_reply_count', '-')}; source_backed_replies={state.get('zrc_phase_a_quote_selection_source_backed_reply_count', '-')}; shortlisted={state.get('zrc_phase_a_quote_selection_shortlist_count', '-')}",
        f"**ZRC-ND Phase A execution authorization log:** `{state.get('zrc_phase_a_execution_authorization_status', '-')}`; rows={state.get('zrc_phase_a_execution_authorization_rows', '-')}; valid={state.get('zrc_phase_a_execution_authorization_valid_rows', '-')}; errors={state.get('zrc_phase_a_execution_authorization_errors', '-')}",
        f"**ZRC-ND Phase A execution release audit:** `{state.get('zrc_phase_a_execution_release_status', '-')}`; ready={str(state.get('zrc_phase_a_execution_release_ready', False)).lower()}; released={str(state.get('zrc_phase_a_execution_release_released', False)).lower()}; blockers={state.get('zrc_phase_a_execution_release_blockers', '-')}; authorization_blockers={state.get('zrc_phase_a_execution_release_authorization_blockers', '-')}",
        f"**ZRC-ND Phase A vendor return intake:** `{state.get('zrc_phase_a_vendor_return_status', '-')}`; rows={state.get('zrc_phase_a_vendor_return_rows', '-')}; exports={state.get('zrc_phase_a_vendor_return_export_files', '-')}",
        f"**ZRC-ND measurement merge:** `{state.get('zrc_measurement_merge_status', '-')}`; inserted={state.get('zrc_measurement_merge_inserted', '-')}; updated={state.get('zrc_measurement_merge_updated', '-')}; output_rows={state.get('zrc_measurement_merge_output_rows', '-')}",
        f"**ZRC-ND run completeness:** `{state.get('zrc_run_completeness_status', '-')}`; measured_known={state.get('zrc_run_completeness_measured_known_rows', '-')} / {state.get('zrc_run_completeness_planned_rows', '-')}",
        f"**ZRC-ND validation results:** `{state.get('zrc_validation_result_status', '-')}`; rows={state.get('zrc_validation_result_rows', '-')}",
        "",
        "## Next Actions",
        "",
        "| Rank | Action | Stage | Command | Success criterion |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for item in state.get("next_actions", []):
        lines.append(
            f"| {item['rank']} | `{item['action_id']}` | {item['stage']} | "
            f"`{item['command']}` | {item['success_criterion']} |"
        )

    lines.extend([
        "",
        "## Evidence Gaps",
        "",
    ])
    gaps = state.get("evidence_gaps", [])
    if gaps:
        lines.extend(f"- {gap}" for gap in gaps)
    else:
        lines.append("- No gap summary was emitted.")

    missing = state.get("h_a_missing_field_summary", [])
    lines.extend([
        "",
        "## H-A Bench Sheet",
        "",
        f"- Task count: {state.get('h_a_bench_task_count', '-')}",
        f"- Blank raw entries to fill: {state.get('h_a_bench_blank_raw_entries_to_fill', '-')}",
    ])

    merge_stats = state.get("h_a_measurement_merge_stats", {})
    lines.extend([
        "",
        "## H-A Raw Measurement Merge",
        "",
        f"- Applied values: {merge_stats.get('applied_values', '-')}",
        f"- Unresolved targets: {merge_stats.get('unresolved_targets', '-')}",
        f"- Unknown run_id rows: {merge_stats.get('skipped_unknown_run_id', '-')}",
        f"- Unit warnings: {merge_stats.get('unit_warnings', '-')}",
    ])

    qc_counts = state.get("h_a_intake_qc_issue_counts", {})
    lines.extend([
        "",
        "## H-A Intake QC",
        "",
        f"- Intake ready: `{state.get('h_a_intake_qc_ready')}`",
        f"- Errors: {qc_counts.get('error', '-')}",
        f"- Warnings: {qc_counts.get('warning', '-')}",
    ])

    if missing:
        lines.extend([
            "",
            "## H-A Missing Field Hotspots",
            "",
            "| Field | Missing rows |",
            "| --- | ---: |",
        ])
        for row in missing:
            lines.append(f"| `{row['field']}` | {row['missing_rows']} |")

    blockers = state.get("nhi_pedot_claim_blockers", [])
    lines.extend([
        "",
        "## NHI-PEDOT Claim Blockers",
        "",
    ])
    if blockers:
        lines.extend(f"- {blocker}" for blocker in blockers)
    else:
        lines.append("- No NHI-PEDOT blockers listed in current claim audit.")

    lines.extend([
        "",
        "## Completion Requirements",
        "",
    ])
    lines.extend(f"- {item}" for item in state.get("completion_requirements", []))
    lines.extend([
        "",
        "## Boundary",
        "",
        "The active route remains a hypothesis until measured, non-synthetic rows pass all gates and the final claim audit turns true.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build LIMINA discovery cycle state.")
    parser.add_argument("--claim-audit", type=Path, default=DEFAULT_CLAIM_AUDIT)
    parser.add_argument("--ranking", type=Path, default=DEFAULT_RANKING)
    parser.add_argument("--portfolio-bypass", type=Path, default=DEFAULT_PORTFOLIO_BYPASS)
    parser.add_argument("--h-a", type=Path, default=DEFAULT_H_A)
    parser.add_argument("--h-a-merge", type=Path, default=DEFAULT_H_A_MERGE)
    parser.add_argument("--h-a-bench", type=Path, default=DEFAULT_H_A_BENCH)
    parser.add_argument("--h-a-qc", type=Path, default=DEFAULT_H_A_QC)
    parser.add_argument("--h-a-service", type=Path, default=DEFAULT_H_A_SERVICE)
    parser.add_argument("--h-a-chain", type=Path, default=DEFAULT_H_A_CHAIN)
    parser.add_argument("--h-a-sample-submission", type=Path, default=DEFAULT_H_A_SAMPLE_SUBMISSION)
    parser.add_argument("--h-a-split-scope", type=Path, default=DEFAULT_H_A_SPLIT_SCOPE)
    parser.add_argument("--h-a-vendor", type=Path, default=DEFAULT_H_A_VENDOR)
    parser.add_argument("--h-a-rfq", type=Path, default=DEFAULT_H_A_RFQ)
    parser.add_argument("--h-a-rfq-outbox", type=Path, default=DEFAULT_H_A_RFQ_OUTBOX)
    parser.add_argument("--h-a-rfq-eml-drafts", type=Path, default=DEFAULT_H_A_RFQ_EML_DRAFTS)
    parser.add_argument("--h-a-rfq-eml-integrity", type=Path, default=DEFAULT_H_A_RFQ_EML_INTEGRITY)
    parser.add_argument("--h-a-quote-tracker", type=Path, default=DEFAULT_H_A_QUOTE_TRACKER)
    parser.add_argument("--h-a-rfq-send-action-pack", type=Path, default=DEFAULT_H_A_RFQ_SEND_ACTION_PACK)
    parser.add_argument("--h-a-rfq-dispatch-manifest", type=Path, default=DEFAULT_H_A_RFQ_DISPATCH_MANIFEST)
    parser.add_argument("--h-a-rfq-reply-action-pack", type=Path, default=DEFAULT_H_A_RFQ_REPLY_ACTION_PACK)
    parser.add_argument("--h-a-rfq-send-cockpit", type=Path, default=DEFAULT_H_A_RFQ_SEND_COCKPIT)
    parser.add_argument("--h-a-rfq-dispatch-archive", type=Path, default=DEFAULT_H_A_RFQ_DISPATCH_ARCHIVE)
    parser.add_argument("--h-a-rfq-send-confirmation-intake", type=Path, default=DEFAULT_H_A_RFQ_SEND_CONFIRMATION_INTAKE)
    parser.add_argument("--h-a-rfq-send-confirmation-entry-sheet", type=Path, default=DEFAULT_H_A_RFQ_SEND_CONFIRMATION_ENTRY_SHEET)
    parser.add_argument("--h-a-rfq-send-confirmation-entry-apply", type=Path, default=DEFAULT_H_A_RFQ_SEND_CONFIRMATION_ENTRY_APPLY)
    parser.add_argument("--h-a-rfq-reply-intake", type=Path, default=DEFAULT_H_A_RFQ_REPLY_INTAKE)
    parser.add_argument("--h-a-rfq-send-log", type=Path, default=DEFAULT_H_A_RFQ_SEND_LOG)
    parser.add_argument("--h-a-rfq-reply-log", type=Path, default=DEFAULT_H_A_RFQ_REPLY_LOG)
    parser.add_argument("--h-a-contact-plan", type=Path, default=DEFAULT_H_A_CONTACT_PLAN)
    parser.add_argument("--h-a-contact-source-audit", type=Path, default=DEFAULT_H_A_CONTACT_SOURCE_AUDIT)
    parser.add_argument("--h-a-quote-selection", type=Path, default=DEFAULT_H_A_QUOTE_SELECTION)
    parser.add_argument("--h-a-execution-authorization", type=Path, default=DEFAULT_H_A_EXECUTION_AUTHORIZATION)
    parser.add_argument("--h-a-execution-release", type=Path, default=DEFAULT_H_A_EXECUTION_RELEASE)
    parser.add_argument("--h-a-vendor-return", type=Path, default=DEFAULT_H_A_VENDOR_RETURN)
    parser.add_argument("--h-a-vendor-bundle-entry-sheet", type=Path, default=DEFAULT_H_A_VENDOR_BUNDLE_ENTRY_SHEET)
    parser.add_argument("--h-a-vendor-bundle-entry-apply", type=Path, default=DEFAULT_H_A_VENDOR_BUNDLE_ENTRY_APPLY)
    parser.add_argument("--h-a-source-values-sheet", type=Path, default=DEFAULT_H_A_SOURCE_VALUES_SHEET)
    parser.add_argument("--h-a-source-drop", type=Path, default=DEFAULT_H_A_SOURCE_DROP)
    parser.add_argument("--h-a-raw-csv-extraction", type=Path, default=DEFAULT_H_A_RAW_CSV_EXTRACTION)
    parser.add_argument("--h-a-source-value-import", type=Path, default=DEFAULT_H_A_SOURCE_VALUE_IMPORT)
    parser.add_argument("--nhi-forward", type=Path, default=DEFAULT_NHI_FORWARD)
    parser.add_argument("--nhi-forward-source-values", type=Path, default=DEFAULT_NHI_FORWARD_SOURCE_VALUES)
    parser.add_argument("--nhi-forward-source-drop", type=Path, default=DEFAULT_NHI_FORWARD_SOURCE_DROP)
    parser.add_argument("--nhi-forward-source-template-pack", type=Path, default=DEFAULT_NHI_FORWARD_SOURCE_TEMPLATE_PACK)
    parser.add_argument("--nhi-forward-raw-csv-extraction", type=Path, default=DEFAULT_NHI_FORWARD_RAW_CSV_EXTRACTION)
    parser.add_argument("--nhi-forward-source-import", type=Path, default=DEFAULT_NHI_FORWARD_SOURCE_IMPORT)
    parser.add_argument("--nhi-results", type=Path, default=DEFAULT_NHI_RESULTS)
    parser.add_argument("--nhi-long-source-values", type=Path, default=DEFAULT_NHI_LONG_SOURCE_VALUES)
    parser.add_argument("--nhi-long-source-drop", type=Path, default=DEFAULT_NHI_LONG_SOURCE_DROP)
    parser.add_argument("--nhi-long-source-template-pack", type=Path, default=DEFAULT_NHI_LONG_SOURCE_TEMPLATE_PACK)
    parser.add_argument("--nhi-long-raw-csv-extraction", type=Path, default=DEFAULT_NHI_LONG_RAW_CSV_EXTRACTION)
    parser.add_argument("--nhi-long-source-import", type=Path, default=DEFAULT_NHI_LONG_SOURCE_IMPORT)
    parser.add_argument("--nhi-long-results", type=Path, default=DEFAULT_NHI_LONG_RESULTS)
    parser.add_argument("--next-measurements", type=Path, default=DEFAULT_NEXT)
    parser.add_argument("--variant-ladder", type=Path, default=DEFAULT_LADDER)
    parser.add_argument("--zrc-readiness", type=Path, default=DEFAULT_ZRC_READINESS)
    parser.add_argument("--zrc-sentinel", type=Path, default=DEFAULT_ZRC_SENTINEL)
    parser.add_argument("--zrc-next-measurements", type=Path, default=DEFAULT_ZRC_NEXT)
    parser.add_argument("--zrc-phase-a-source-values", type=Path, default=DEFAULT_ZRC_PHASE_A_SOURCE_VALUES)
    parser.add_argument("--zrc-phase-a-source-drop", type=Path, default=DEFAULT_ZRC_PHASE_A_SOURCE_DROP)
    parser.add_argument("--zrc-phase-a-source-template-pack", type=Path, default=DEFAULT_ZRC_PHASE_A_SOURCE_TEMPLATE_PACK)
    parser.add_argument("--zrc-phase-a-vendor-bundle-entry-sheet", type=Path, default=DEFAULT_ZRC_PHASE_A_VENDOR_BUNDLE_ENTRY_SHEET)
    parser.add_argument("--zrc-phase-a-vendor-bundle-entry-apply", type=Path, default=DEFAULT_ZRC_PHASE_A_VENDOR_BUNDLE_ENTRY_APPLY)
    parser.add_argument("--zrc-phase-a-raw-csv-extraction", type=Path, default=DEFAULT_ZRC_PHASE_A_RAW_CSV_EXTRACTION)
    parser.add_argument("--zrc-phase-a-source-import", type=Path, default=DEFAULT_ZRC_PHASE_A_SOURCE_IMPORT)
    parser.add_argument("--zrc-phase-a-service", type=Path, default=DEFAULT_ZRC_PHASE_A_SERVICE)
    parser.add_argument("--zrc-phase-a-chain", type=Path, default=DEFAULT_ZRC_PHASE_A_CHAIN)
    parser.add_argument("--zrc-phase-a-delivery", type=Path, default=DEFAULT_ZRC_PHASE_A_DELIVERY)
    parser.add_argument("--zrc-phase-a-vendor", type=Path, default=DEFAULT_ZRC_PHASE_A_VENDOR)
    parser.add_argument("--zrc-phase-a-rfq", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ)
    parser.add_argument("--zrc-phase-a-rfq-outbox", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ_OUTBOX)
    parser.add_argument("--zrc-phase-a-quote-tracker", type=Path, default=DEFAULT_ZRC_PHASE_A_QUOTE_TRACKER)
    parser.add_argument("--zrc-phase-a-rfq-send-confirmation-intake", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ_SEND_CONFIRMATION_INTAKE)
    parser.add_argument("--zrc-phase-a-rfq-send-confirmation-entry-sheet", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ_SEND_CONFIRMATION_ENTRY_SHEET)
    parser.add_argument("--zrc-phase-a-rfq-send-confirmation-entry-apply", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ_SEND_CONFIRMATION_ENTRY_APPLY)
    parser.add_argument("--zrc-phase-a-rfq-send-log", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ_SEND_LOG)
    parser.add_argument("--zrc-phase-a-rfq-reply-intake", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ_REPLY_INTAKE)
    parser.add_argument("--zrc-phase-a-rfq-reply-log", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ_REPLY_LOG)
    parser.add_argument("--zrc-phase-a-contact-plan", type=Path, default=DEFAULT_ZRC_PHASE_A_CONTACT_PLAN)
    parser.add_argument("--zrc-phase-a-rfq-dispatch-manifest", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ_DISPATCH_MANIFEST)
    parser.add_argument("--zrc-phase-a-rfq-dispatch-archive", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ_DISPATCH_ARCHIVE)
    parser.add_argument("--zrc-phase-a-rfq-reply-action-pack", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ_REPLY_ACTION_PACK)
    parser.add_argument("--zrc-phase-a-rfq-send-cockpit", type=Path, default=DEFAULT_ZRC_PHASE_A_RFQ_SEND_COCKPIT)
    parser.add_argument("--zrc-phase-a-quote-selection", type=Path, default=DEFAULT_ZRC_PHASE_A_QUOTE_SELECTION)
    parser.add_argument("--zrc-phase-a-execution-authorization", type=Path, default=DEFAULT_ZRC_PHASE_A_EXECUTION_AUTHORIZATION)
    parser.add_argument("--zrc-phase-a-execution-release", type=Path, default=DEFAULT_ZRC_PHASE_A_EXECUTION_RELEASE)
    parser.add_argument("--zrc-phase-a-vendor-return", type=Path, default=DEFAULT_ZRC_PHASE_A_VENDOR_RETURN)
    parser.add_argument("--zrc-measurement-merge", type=Path, default=DEFAULT_ZRC_MEASUREMENT_MERGE)
    parser.add_argument("--zrc-run-completeness", type=Path, default=DEFAULT_ZRC_RUN_COMPLETENESS)
    parser.add_argument("--zrc-validation-results", type=Path, default=DEFAULT_ZRC_VALIDATION_RESULTS)
    parser.add_argument("--hybrid-measurement-plan", type=Path, default=DEFAULT_HYBRID_MEASUREMENT_PLAN)
    parser.add_argument("--local-capture-pack", type=Path, default=DEFAULT_LOCAL_CAPTURE_PACK)
    parser.add_argument("--source-file-manifest", type=Path, default=DEFAULT_SOURCE_FILE_MANIFEST)
    parser.add_argument("--source-file-inventory", type=Path, default=DEFAULT_SOURCE_FILE_INVENTORY)
    parser.add_argument("--local-capture-preflight", type=Path, default=DEFAULT_LOCAL_CAPTURE_PREFLIGHT)
    parser.add_argument("--smoke-capture-tranche", type=Path, default=DEFAULT_SMOKE_CAPTURE_TRANCHE)
    parser.add_argument("--smoke-execution-queue", type=Path, default=DEFAULT_SMOKE_EXECUTION_QUEUE)
    parser.add_argument("--smoke-entry-sheet", type=Path, default=DEFAULT_SMOKE_ENTRY_SHEET)
    parser.add_argument("--smoke-source-drop", type=Path, default=DEFAULT_SMOKE_SOURCE_DROP)
    parser.add_argument("--smoke-source-values-sheet", type=Path, default=DEFAULT_SMOKE_SOURCE_VALUES_SHEET)
    parser.add_argument("--smoke-starter-readiness", type=Path, default=DEFAULT_SMOKE_STARTER_READINESS)
    parser.add_argument("--smoke-starter-execution-pack", type=Path, default=DEFAULT_SMOKE_STARTER_EXECUTION_PACK)
    parser.add_argument("--smoke-starter-template-pack", type=Path, default=DEFAULT_SMOKE_STARTER_TEMPLATE_PACK)
    parser.add_argument("--smoke-raw-csv-extraction", type=Path, default=DEFAULT_SMOKE_RAW_CSV_EXTRACTION)
    parser.add_argument("--smoke-unstructured-intake", type=Path, default=DEFAULT_SMOKE_UNSTRUCTURED_INTAKE)
    parser.add_argument("--smoke-unstructured-review-values", type=Path, default=DEFAULT_SMOKE_UNSTRUCTURED_REVIEW_VALUES)
    parser.add_argument("--smoke-source-value-import", type=Path, default=DEFAULT_SMOKE_SOURCE_VALUE_IMPORT)
    parser.add_argument("--smoke-entry-apply", type=Path, default=DEFAULT_SMOKE_ENTRY_APPLY)
    parser.add_argument("--smoke-capture-preflight", type=Path, default=DEFAULT_SMOKE_CAPTURE_PREFLIGHT)
    parser.add_argument("--smoke-rehearsal", type=Path, default=DEFAULT_SMOKE_REHEARSAL)
    parser.add_argument("--first-wave-rfq-dispatch-cockpit", type=Path, default=DEFAULT_FIRST_WAVE_RFQ_DISPATCH_COCKPIT)
    parser.add_argument("--first-wave-post-dispatch", type=Path, default=DEFAULT_FIRST_WAVE_POST_DISPATCH)
    parser.add_argument("--second-wave-candidate-queue", type=Path, default=DEFAULT_SECOND_WAVE_CANDIDATE_QUEUE)
    parser.add_argument("--second-wave-scope-lock-pack", type=Path, default=DEFAULT_SECOND_WAVE_SCOPE_LOCK_PACK)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state = build_state(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(state), encoding="utf-8")
    print(f"Mission state: {state['mission_state']}")
    print(f"Claim ready: {state['claim_ready']}")
    print(f"Active candidate: {state.get('active_discovery_candidate', '-')}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
