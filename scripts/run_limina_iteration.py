#!/usr/bin/env python3
"""Run one local dry-lab LIMINA discovery iteration."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_iteration_state.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_iteration_state.md"


COMMANDS = [
    {
        "id": "import_evidence",
        "stage": "evidence",
        "argv": ["scripts/import_evidence.py"],
        "purpose": "Refresh the evidence register and optional DuckDB index.",
        "artifact": "reports/evidence_register.md",
    },
    {
        "id": "validate_data_refs",
        "stage": "evidence",
        "argv": ["scripts/validate_limina_data.py"],
        "purpose": "Reject missing evidence references across candidates, protocols, and validation packages.",
        "artifact": "reports/data_validation.md",
    },
    {
        "id": "rank_discovery_candidates",
        "stage": "candidate_selection",
        "argv": ["scripts/rank_limina_discovery_candidates.py"],
        "purpose": "Refresh the active material-technology ranking.",
        "artifact": "reports/limina_discovery_ranking.md",
    },
    {
        "id": "render_alg_lam_protocol",
        "stage": "candidate_handoff",
        "argv": ["scripts/render_nhi_pedot_protocol.py"],
        "purpose": "Refresh the recipe-specific ALG-LAM-PEDOT protocol handoff.",
        "artifact": "reports/nhi_pedot_alg_lam_protocol.md",
    },
    {
        "id": "render_source_file_manifest",
        "stage": "source_file_guard",
        "argv": ["scripts/render_limina_source_file_manifest.py"],
        "purpose": "Refresh allowed source-file roots and policy before any source-backed import runs.",
        "artifact": "reports/limina_source_file_manifest.md",
    },
    {
        "id": "render_h_a_source_values_sheet",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_source_values_sheet.py"],
        "purpose": "Render a fillable source-backed sidecar for formal H-A raw rows.",
        "artifact": "reports/nhi_pedot_h_a_source_values_sheet.md",
    },
    {
        "id": "render_h_a_source_drop_plan",
        "stage": "h_a_intake",
        "argv": ["scripts/render_limina_source_value_drop_plan.py", "--profile", "h_a"],
        "purpose": "Create allowed H-A source-file drop directories and a missing-file plan before import.",
        "artifact": "reports/nhi_pedot_h_a_source_drop_plan.md",
    },
    {
        "id": "render_h_a_source_unlock_pack",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_source_unlock_pack.py"],
        "purpose": "Group H-A source-value rows into consolidated raw-file handoff bundles.",
        "artifact": "reports/nhi_pedot_h_a_source_unlock_pack.md",
    },
    {
        "id": "render_h_a_bundle_entry_sheet",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_bundle_entry_sheet.py"],
        "purpose": "Render a consolidated one-row-per-bundle H-A entry sheet while preserving user-entered values.",
        "artifact": "reports/nhi_pedot_h_a_bundle_entry_sheet.md",
    },
    {
        "id": "render_h_a_vendor_bundle_entry_sheet",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_vendor_bundle_entry_sheet.py"],
        "purpose": "Render a vendor-return H-A bundle-entry sheet in the return inbox while preserving provider-entered values.",
        "artifact": "reports/nhi_pedot_h_a_vendor_bundle_entry_sheet.md",
    },
    {
        "id": "apply_h_a_bundle_entry_sheet",
        "stage": "h_a_intake",
        "argv": ["scripts/apply_nhi_pedot_h_a_bundle_entry_sheet.py"],
        "purpose": "Apply validated H-A bundle-entry rows into the source-values sheet without creating evidence.",
        "artifact": "reports/nhi_pedot_h_a_bundle_entry_apply.md",
    },
    {
        "id": "apply_h_a_vendor_bundle_entry_return",
        "stage": "h_a_intake",
        "argv": ["scripts/apply_nhi_pedot_h_a_vendor_bundle_entry_return.py"],
        "purpose": "Apply a returned compact H-A bundle-entry sheet from the vendor inbox when present.",
        "artifact": "reports/nhi_pedot_h_a_vendor_bundle_entry_apply.md",
    },
    {
        "id": "render_h_a_source_file_template_pack",
        "stage": "h_a_intake",
        "argv": ["scripts/render_limina_source_file_template_pack.py", "--profile", "h_a"],
        "purpose": "Render source-class raw-file templates for H-A source files without creating evidence.",
        "artifact": "reports/nhi_pedot_h_a_source_file_template_pack.md",
    },
    {
        "id": "extract_h_a_raw_csv_values",
        "stage": "h_a_intake",
        "argv": ["scripts/extract_nhi_pedot_h_a_raw_csv_values.py"],
        "purpose": "Extract source-backed H-A values from existing raw CSV/TSV source files into an importer sidecar.",
        "artifact": "reports/nhi_pedot_h_a_raw_csv_value_extraction.md",
    },
    {
        "id": "import_h_a_source_values",
        "stage": "h_a_intake",
        "argv": ["scripts/import_nhi_pedot_h_a_source_values.py"],
        "purpose": "Import valid source-file-backed H-A sidecar rows into the formal raw template before merge.",
        "artifact": "reports/nhi_pedot_h_a_source_value_import.md",
    },
    {
        "id": "merge_h_a_raw_measurements",
        "stage": "h_a_intake",
        "argv": ["scripts/merge_nhi_pedot_h_a_raw_measurements.py"],
        "purpose": "Merge any filled long-form H-A raw measurements into the active run table.",
        "artifact": "reports/nhi_pedot_h_a_measurement_merge.md",
    },
    {
        "id": "render_h_a_bench_sheet",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_bench_sheet.py"],
        "purpose": "Refresh the compact H-A bench sheet from the active run table and raw template.",
        "artifact": "reports/nhi_pedot_h_a_bench_sheet.md",
    },
    {
        "id": "qc_h_a_intake",
        "stage": "h_a_intake",
        "argv": ["scripts/qc_nhi_pedot_h_a_intake.py"],
        "purpose": "Check whether H-A rows have real, claimable measured provenance.",
        "artifact": "reports/nhi_pedot_h_a_intake_qc.md",
    },
    {
        "id": "render_h_a_minimum_checklist",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_minimum_measurement_checklist.py"],
        "purpose": "Compress the H-A work into a minimum real-measurement checklist.",
        "artifact": "reports/nhi_pedot_h_a_minimum_measurement_checklist.md",
    },
    {
        "id": "render_h_a_service_request",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_service_request.py"],
        "purpose": "Render a vendor/cooperator service request for real H-A measurements.",
        "artifact": "reports/nhi_pedot_h_a_service_request.md",
    },
    {
        "id": "render_h_a_chain_of_custody",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_chain_of_custody.py"],
        "purpose": "Render sample labels and chain-of-custody blanks for real H-A sample transfer.",
        "artifact": "reports/nhi_pedot_h_a_chain_of_custody.md",
    },
    {
        "id": "render_h_a_sample_submission_pack",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_sample_submission_pack.py"],
        "purpose": "Render material disclosure and pre-shipment questions for vendor sample submission.",
        "artifact": "reports/nhi_pedot_h_a_sample_submission_pack.md",
    },
    {
        "id": "render_h_a_split_scope_plan",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_split_scope_plan.py"],
        "purpose": "Render fallback vendor pairings for split media chemistry and coupon physical/imaging execution.",
        "artifact": "reports/nhi_pedot_h_a_split_scope_plan.md",
    },
    {
        "id": "render_h_a_delivery_package",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_delivery_package.py"],
        "purpose": "Render a sendable H-A package manifest with checksums and return-file expectations.",
        "artifact": "reports/nhi_pedot_h_a_delivery_package_manifest.md",
    },
    {
        "id": "render_h_a_vendor_outreach",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_vendor_outreach.py"],
        "purpose": "Render a vendor/cooperator screening brief for real H-A measurement execution.",
        "artifact": "reports/nhi_pedot_h_a_vendor_outreach_brief.md",
    },
    {
        "id": "render_h_a_rfq_packet",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_rfq_packet.py"],
        "purpose": "Render per-vendor RFQ text, attachment list, disqualifiers, and quote scoring rubric.",
        "artifact": "reports/nhi_pedot_h_a_rfq_packet.md",
    },
    {
        "id": "render_h_a_rfq_outbox",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_rfq_outbox.py"],
        "purpose": "Render vendor-specific RFQ email files and zip bundles for the H-A measurement request.",
        "artifact": "reports/nhi_pedot_h_a_rfq_outbox.md",
    },
    {
        "id": "render_h_a_quote_tracker",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_quote_tracker.py"],
        "purpose": "Render a blank tracker for vendor quote replies and selection decisions.",
        "artifact": "reports/nhi_pedot_h_a_quote_tracker.md",
    },
    {
        "id": "intake_h_a_rfq_send_confirmations",
        "stage": "h_a_intake",
        "argv": ["scripts/intake_limina_rfq_send_confirmations.py", "--profile", "h_a"],
        "purpose": "Scan original H-A RFQ send confirmations and auto-fill send-log rows only when a sent EML proves the expected bundle attachment.",
        "artifact": "reports/nhi_pedot_h_a_rfq_send_confirmation_intake.md",
    },
    {
        "id": "render_h_a_rfq_send_confirmation_entry_sheet",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.py"],
        "purpose": "Render a guarded entry sheet for non-EML H-A RFQ send confirmations such as web-form confirmations, PDFs, screenshots, or saved pages.",
        "artifact": "reports/nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.md",
    },
    {
        "id": "apply_h_a_rfq_send_confirmation_entry_sheet",
        "stage": "h_a_intake",
        "argv": ["scripts/apply_nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.py"],
        "purpose": "Apply human-reviewed non-EML H-A RFQ send confirmations into the send log without treating outreach as evidence.",
        "artifact": "reports/nhi_pedot_h_a_rfq_send_confirmation_entry_apply.md",
    },
    {
        "id": "apply_h_a_rfq_send_log",
        "stage": "h_a_intake",
        "argv": ["scripts/apply_limina_rfq_send_log.py", "--profile", "h_a"],
        "purpose": "Render/apply verified H-A RFQ send confirmations into the quote tracker without treating outreach as evidence.",
        "artifact": "reports/nhi_pedot_h_a_rfq_send_log.md",
    },
    {
        "id": "intake_h_a_rfq_replies",
        "stage": "h_a_intake",
        "argv": ["scripts/intake_limina_rfq_replies.py", "--profile", "h_a"],
        "purpose": "Scan original H-A RFQ reply EML files and register verified-send replies for human review without scoring them.",
        "artifact": "reports/nhi_pedot_h_a_rfq_reply_intake.md",
    },
    {
        "id": "apply_h_a_rfq_reply_log",
        "stage": "h_a_intake",
        "argv": ["scripts/apply_limina_rfq_reply_log.py", "--profile", "h_a"],
        "purpose": "Render/apply source-backed H-A RFQ replies into the quote tracker without treating replies as measurement evidence.",
        "artifact": "reports/nhi_pedot_h_a_rfq_reply_log.md",
    },
    {
        "id": "render_h_a_vendor_contact_plan",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_vendor_contact_plan.py"],
        "purpose": "Render official contact channels for sending RFQ outbox bundles and tracking replies.",
        "artifact": "reports/nhi_pedot_h_a_vendor_contact_plan.md",
    },
    {
        "id": "audit_h_a_vendor_contact_sources",
        "stage": "h_a_intake",
        "argv": ["scripts/audit_nhi_pedot_h_a_vendor_contact_sources.py"],
        "purpose": "Audit first-wave H-A RFQ contact channels against official-source proof rows before manual dispatch.",
        "artifact": "reports/nhi_pedot_h_a_vendor_contact_source_audit.md",
    },
    {
        "id": "render_h_a_rfq_eml_drafts",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_rfq_eml_drafts.py"],
        "purpose": "Render attached EML drafts for first-wave H-A RFQ sends without sending them.",
        "artifact": "reports/nhi_pedot_h_a_rfq_eml_drafts.md",
    },
    {
        "id": "audit_h_a_rfq_eml_integrity",
        "stage": "h_a_intake",
        "argv": ["scripts/audit_nhi_pedot_h_a_rfq_eml_integrity.py"],
        "purpose": "Parse every H-A RFQ EML draft and verify recipient, boundary headers, bundle hash, and attached zip hash before manual sending.",
        "artifact": "reports/nhi_pedot_h_a_rfq_eml_integrity_audit.md",
    },
    {
        "id": "render_h_a_rfq_send_action_pack",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_rfq_send_action_pack.py"],
        "purpose": "Render an actionable first-wave RFQ send queue with confirmation-file instructions.",
        "artifact": "reports/nhi_pedot_h_a_rfq_send_action_pack.md",
    },
    {
        "id": "render_h_a_rfq_dispatch_manifest",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_rfq_dispatch_manifest.py"],
        "purpose": "Bind each first-wave H-A RFQ draft to the exact audited bundle, recipient, and confirmation-save path before manual dispatch.",
        "artifact": "reports/nhi_pedot_h_a_rfq_dispatch_manifest.md",
    },
    {
        "id": "render_h_a_rfq_reply_action_pack",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_rfq_reply_action_pack.py"],
        "purpose": "Render an actionable source-backed RFQ reply intake queue for provider selection.",
        "artifact": "reports/nhi_pedot_h_a_rfq_reply_action_pack.md",
    },
    {
        "id": "render_h_a_rfq_send_cockpit",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_rfq_send_cockpit.py"],
        "purpose": "Render a single local cockpit for opening H-A RFQ drafts and preserving real send/reply source files.",
        "artifact": "reports/nhi_pedot_h_a_rfq_send_cockpit.md",
    },
    {
        "id": "render_h_a_rfq_dispatch_archive",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_rfq_dispatch_archive.py"],
        "purpose": "Render a single audited archive containing H-A RFQ drafts, bundles, manifests, contact audits, cockpit, and confirmation templates for manual dispatch.",
        "artifact": "reports/nhi_pedot_h_a_rfq_dispatch_archive_manifest.md",
    },
    {
        "id": "evaluate_h_a_quote_replies",
        "stage": "h_a_intake",
        "argv": ["scripts/evaluate_nhi_pedot_h_a_quote_replies.py"],
        "purpose": "Score any RFQ replies for H-A execution selection without treating quotes as evidence.",
        "artifact": "reports/nhi_pedot_h_a_quote_selection.md",
    },
    {
        "id": "apply_h_a_execution_authorization_log",
        "stage": "h_a_intake",
        "argv": ["scripts/apply_limina_execution_authorization_log.py", "--profile", "h_a"],
        "purpose": "Render/validate human H-A execution authorization records without treating authorization as evidence.",
        "artifact": "reports/nhi_pedot_h_a_execution_authorization_log.md",
    },
    {
        "id": "audit_h_a_execution_release",
        "stage": "h_a_intake",
        "argv": ["scripts/audit_limina_execution_release.py", "--profile", "h_a"],
        "purpose": "Block H-A sample or outsourced execution release until a source-backed selected provider is verified.",
        "artifact": "reports/nhi_pedot_h_a_execution_release_audit.md",
    },
    {
        "id": "render_h_a_vendor_return_intake",
        "stage": "h_a_intake",
        "argv": ["scripts/render_nhi_pedot_h_a_vendor_return_intake.py"],
        "purpose": "Check the vendor-return inbox for real H-A measurement files ready for merge/QC.",
        "artifact": "reports/nhi_pedot_h_a_vendor_return_intake.md",
    },
    {
        "id": "interpret_h_a_sentinel",
        "stage": "h_a_gate",
        "argv": ["scripts/interpret_nhi_pedot_h_a_sentinel.py"],
        "purpose": "Interpret H-A only if provenance is acceptable; otherwise keep the blocker explicit.",
        "artifact": "reports/nhi_pedot_h_a_sentinel_interpretation.md",
    },
    {
        "id": "refresh_next_measurements",
        "stage": "h_a_next_actions",
        "argv": ["scripts/suggest_nhi_pedot_next_measurements.py"],
        "purpose": "Refresh the next H-A measurement selector.",
        "artifact": "reports/nhi_pedot_next_measurements.md",
    },
    {
        "id": "refresh_h_a_packet",
        "stage": "h_a_next_actions",
        "argv": ["scripts/generate_nhi_pedot_sentinel_packet.py"],
        "purpose": "Regenerate the H-A sentinel packet for real measurement entry.",
        "artifact": "reports/nhi_pedot_h_a_sentinel_packet.md",
    },
    {
        "id": "design_variant_ladder",
        "stage": "adaptive_design",
        "argv": ["scripts/design_nhi_pedot_variant_ladder.py"],
        "purpose": "Refresh the predeclared rescue and comparator ladder.",
        "artifact": "reports/nhi_pedot_variant_ladder.md",
    },
    {
        "id": "generate_forward_gate_package",
        "stage": "forward_evidence",
        "argv": ["scripts/generate_nhi_pedot_forward_gate_package.py"],
        "purpose": "Pre-register H-B/H-C gate rows and decision triggers after H-A.",
        "artifact": "reports/nhi_pedot_forward_gate_package.md",
    },
    {
        "id": "render_nhi_forward_source_values_sheet",
        "stage": "forward_evidence",
        "argv": ["scripts/render_limina_wide_source_values_sheet.py", "--profile", "nhi_forward"],
        "purpose": "Render a source-file-backed sidecar for NHI-PEDOT H-B/H-C wide run rows.",
        "artifact": "reports/nhi_pedot_forward_source_values_sheet.md",
    },
    {
        "id": "render_nhi_forward_source_drop_plan",
        "stage": "forward_evidence",
        "argv": ["scripts/render_limina_source_value_drop_plan.py", "--profile", "nhi_forward"],
        "purpose": "Create allowed H-B/H-C source-file drop directories and a missing-file plan before import.",
        "artifact": "reports/nhi_pedot_forward_source_drop_plan.md",
    },
    {
        "id": "render_nhi_forward_source_file_template_pack",
        "stage": "forward_evidence",
        "argv": ["scripts/render_limina_source_file_template_pack.py", "--profile", "nhi_forward"],
        "purpose": "Render source-class raw-file templates for H-B/H-C source files without creating evidence.",
        "artifact": "reports/nhi_pedot_forward_source_file_template_pack.md",
    },
    {
        "id": "extract_nhi_forward_raw_csv_values",
        "stage": "forward_evidence",
        "argv": ["scripts/extract_limina_wide_raw_csv_values.py", "--profile", "nhi_forward"],
        "purpose": "Extract NHI-PEDOT H-B/H-C source values from existing raw CSV/TSV files in allowed source-file roots.",
        "artifact": "reports/nhi_pedot_forward_raw_csv_value_extraction.md",
    },
    {
        "id": "import_nhi_forward_source_values",
        "stage": "forward_evidence",
        "argv": ["scripts/import_limina_wide_source_values.py", "--profile", "nhi_forward"],
        "purpose": "Import valid source-file-backed H-B/H-C values into the NHI-PEDOT evaluator table.",
        "artifact": "reports/nhi_pedot_forward_source_values_import.md",
    },
    {
        "id": "evaluate_nhi_coupon_runs",
        "stage": "forward_evidence",
        "argv": ["scripts/evaluate_nhi_pedot_runs.py"],
        "purpose": "Refresh NHI-PEDOT coupon gate results from the current evaluator table.",
        "artifact": "reports/nhi_pedot_results.md",
    },
    {
        "id": "render_nhi_long_source_values_sheet",
        "stage": "long_duration_evidence",
        "argv": ["scripts/render_limina_wide_source_values_sheet.py", "--profile", "nhi_long"],
        "purpose": "Render a source-file-backed sidecar for NHI-PEDOT long-duration wide run rows.",
        "artifact": "reports/nhi_pedot_long_source_values_sheet.md",
    },
    {
        "id": "render_nhi_long_source_drop_plan",
        "stage": "long_duration_evidence",
        "argv": ["scripts/render_limina_source_value_drop_plan.py", "--profile", "nhi_long"],
        "purpose": "Create allowed long-duration source-file drop directories and a missing-file plan before import.",
        "artifact": "reports/nhi_pedot_long_source_drop_plan.md",
    },
    {
        "id": "render_nhi_long_source_file_template_pack",
        "stage": "long_duration_evidence",
        "argv": ["scripts/render_limina_source_file_template_pack.py", "--profile", "nhi_long"],
        "purpose": "Render source-class raw-file templates for long-duration source files without creating evidence.",
        "artifact": "reports/nhi_pedot_long_source_file_template_pack.md",
    },
    {
        "id": "extract_nhi_long_raw_csv_values",
        "stage": "long_duration_evidence",
        "argv": ["scripts/extract_limina_wide_raw_csv_values.py", "--profile", "nhi_long"],
        "purpose": "Extract NHI-PEDOT long-duration source values from existing raw CSV/TSV files in allowed source-file roots.",
        "artifact": "reports/nhi_pedot_long_raw_csv_value_extraction.md",
    },
    {
        "id": "import_nhi_long_source_values",
        "stage": "long_duration_evidence",
        "argv": ["scripts/import_limina_wide_source_values.py", "--profile", "nhi_long"],
        "purpose": "Import valid source-file-backed long-duration values into the NHI-PEDOT long evaluator table.",
        "artifact": "reports/nhi_pedot_long_source_values_import.md",
    },
    {
        "id": "evaluate_nhi_long_runs",
        "stage": "long_duration_evidence",
        "argv": ["scripts/evaluate_nhi_pedot_long_runs.py"],
        "purpose": "Refresh NHI-PEDOT long-duration gate results from the current evaluator table.",
        "artifact": "reports/nhi_pedot_long_results.md",
    },
    {
        "id": "interpret_zrc_phase_a_sentinel",
        "stage": "zrc_phase_a",
        "argv": ["scripts/interpret_zrc_nd_sentinel.py"],
        "purpose": "Refresh the ZRC-ND Phase A sentinel interpretation without treating blank rows as evidence.",
        "artifact": "reports/zrc_nd_sentinel_interpretation.md",
    },
    {
        "id": "suggest_zrc_next_measurements",
        "stage": "zrc_phase_a",
        "argv": ["scripts/suggest_zrc_nd_next_measurements.py"],
        "purpose": "Refresh the adaptive ZRC-ND external-material next measurement selector.",
        "artifact": "reports/zrc_nd_next_measurements.md",
    },
    {
        "id": "generate_zrc_phase_a_packet",
        "stage": "zrc_phase_a",
        "argv": ["scripts/generate_zrc_nd_sentinel_packet.py"],
        "purpose": "Regenerate the 8-row ZRC-ND Phase A sentinel data-entry packet.",
        "artifact": "reports/zrc_nd_phase_a_sentinel_packet.md",
    },
    {
        "id": "render_zrc_phase_a_source_values_sheet",
        "stage": "zrc_phase_a",
        "argv": ["scripts/render_limina_wide_source_values_sheet.py", "--profile", "zrc_phase_a"],
        "purpose": "Render a source-file-backed sidecar for ZRC-ND Phase A wide measurement rows.",
        "artifact": "reports/zrc_nd_phase_a_source_values_sheet.md",
    },
    {
        "id": "render_zrc_phase_a_source_drop_plan",
        "stage": "zrc_phase_a",
        "argv": ["scripts/render_limina_source_value_drop_plan.py", "--profile", "zrc_phase_a"],
        "purpose": "Create allowed ZRC-ND Phase A source-file drop directories and a missing-file plan before import.",
        "artifact": "reports/zrc_nd_phase_a_source_drop_plan.md",
    },
    {
        "id": "render_zrc_phase_a_source_file_template_pack",
        "stage": "zrc_phase_a",
        "argv": ["scripts/render_limina_source_file_template_pack.py", "--profile", "zrc_phase_a"],
        "purpose": "Render source-class raw-file templates for ZRC-ND Phase A source files without creating evidence.",
        "artifact": "reports/zrc_nd_phase_a_source_file_template_pack.md",
    },
    {
        "id": "render_zrc_phase_a_vendor_bundle_entry_sheet",
        "stage": "zrc_phase_a",
        "argv": ["scripts/render_zrc_nd_phase_a_vendor_bundle_entry_sheet.py"],
        "purpose": "Render a compact one-row-per-run/source-class ZRC-ND Phase A vendor return sheet while preserving user-entered values.",
        "artifact": "reports/zrc_nd_phase_a_vendor_bundle_entry_sheet.md",
    },
    {
        "id": "apply_zrc_phase_a_vendor_bundle_entry_sheet",
        "stage": "zrc_phase_a",
        "argv": ["scripts/apply_zrc_nd_phase_a_vendor_bundle_entry_sheet.py"],
        "purpose": "Apply reviewed ZRC-ND Phase A vendor bundle-entry rows into the source-values sheet without creating evidence.",
        "artifact": "reports/zrc_nd_phase_a_vendor_bundle_entry_apply.md",
    },
    {
        "id": "extract_zrc_phase_a_raw_csv_values",
        "stage": "zrc_phase_a",
        "argv": ["scripts/extract_limina_wide_raw_csv_values.py", "--profile", "zrc_phase_a"],
        "purpose": "Extract ZRC-ND Phase A source values from existing raw CSV/TSV files in allowed source-file roots.",
        "artifact": "reports/zrc_nd_phase_a_raw_csv_value_extraction.md",
    },
    {
        "id": "import_zrc_phase_a_source_values",
        "stage": "zrc_phase_a",
        "argv": ["scripts/import_limina_wide_source_values.py", "--profile", "zrc_phase_a"],
        "purpose": "Import valid source-file-backed ZRC-ND Phase A values into the vendor-return measurement CSV.",
        "artifact": "reports/zrc_nd_phase_a_source_values_import.md",
    },
    {
        "id": "render_zrc_phase_a_service_request",
        "stage": "zrc_phase_a",
        "argv": ["scripts/render_zrc_nd_phase_a_service_request.py"],
        "purpose": "Render a service request for real ZRC-ND Phase A medium-integrity measurements.",
        "artifact": "reports/zrc_nd_phase_a_service_request.md",
    },
    {
        "id": "render_hybrid_measurement_plan",
        "stage": "measurement_routing",
        "argv": ["scripts/render_limina_hybrid_measurement_plan.py"],
        "purpose": "Split H-A and ZRC-ND Phase A fields into local, outsourced, and provenance-only measurement routes.",
        "artifact": "reports/limina_hybrid_measurement_plan.md",
    },
    {
        "id": "render_local_capture_pack",
        "stage": "measurement_routing",
        "argv": ["scripts/render_limina_local_capture_pack.py"],
        "purpose": "Render fillable local/outsource capture templates, instrument register, and QC checklist.",
        "artifact": "reports/limina_local_capture_pack.md",
    },
    {
        "id": "audit_source_file_inventory",
        "stage": "measurement_routing",
        "argv": ["scripts/audit_limina_source_file_inventory.py"],
        "purpose": "Inventory source-file dropboxes, hash raw files, and reconcile capture-template source_file references.",
        "artifact": "reports/limina_source_file_inventory.md",
    },
    {
        "id": "regress_source_value_inventory",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_limina_source_value_inventory.py"],
        "purpose": "Verify filled source-value rows are reconciled by source-file inventory and blank rows are ignored.",
        "artifact": "reports/limina_source_value_inventory_regression.md",
    },
    {
        "id": "regress_h_a_raw_csv_extraction",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_nhi_pedot_h_a_raw_csv_extraction.py"],
        "purpose": "Verify H-A raw CSV extraction only accepts real source files and rejects placeholder-looking values.",
        "artifact": "reports/nhi_pedot_h_a_raw_csv_extraction_regression.md",
    },
    {
        "id": "regress_h_a_bundle_entry",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_nhi_pedot_h_a_bundle_entry.py"],
        "purpose": "Verify H-A bundle entry sheets do not mutate source values unless valid source-backed rows are applied.",
        "artifact": "reports/nhi_pedot_h_a_bundle_entry_regression.md",
    },
    {
        "id": "regress_h_a_vendor_bundle_entry_return",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_nhi_pedot_h_a_vendor_bundle_entry_return.py"],
        "purpose": "Verify returned compact H-A bundle-entry sheets only update source values when source-backed.",
        "artifact": "reports/nhi_pedot_h_a_vendor_bundle_entry_return_regression.md",
    },
    {
        "id": "regress_wide_raw_csv_extraction",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_limina_wide_raw_csv_extraction.py"],
        "purpose": "Verify wide raw CSV extraction only accepts real source files and rejects placeholder-looking values.",
        "artifact": "reports/limina_wide_raw_csv_extraction_regression.md",
    },
    {
        "id": "regress_rfq_send_log",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_limina_rfq_send_log.py"],
        "purpose": "Verify RFQ send logs only update quote trackers with valid real send confirmations.",
        "artifact": "reports/limina_rfq_send_log_regression.md",
    },
    {
        "id": "regress_rfq_send_confirmation_intake",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_limina_rfq_send_confirmation_intake.py"],
        "purpose": "Verify RFQ send-confirmation intake only auto-applies sent EML files with matching bundle attachments.",
        "artifact": "reports/limina_rfq_send_confirmation_intake_regression.md",
    },
    {
        "id": "regress_rfq_reply_intake",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_limina_rfq_reply_intake.py"],
        "purpose": "Verify RFQ reply intake only registers parsable EML replies after verified sends and does not auto-score providers.",
        "artifact": "reports/limina_rfq_reply_intake_regression.md",
    },
    {
        "id": "regress_rfq_reply_log",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_limina_rfq_reply_log.py"],
        "purpose": "Verify RFQ reply logs only update quote trackers with source-backed replies.",
        "artifact": "reports/limina_rfq_reply_log_regression.md",
    },
    {
        "id": "regress_quote_selection_source_guard",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_limina_quote_selection_source_guard.py"],
        "purpose": "Verify quote selection cannot shortlist or select providers from unbacked tracker replies.",
        "artifact": "reports/limina_quote_selection_source_guard_regression.md",
    },
    {
        "id": "regress_execution_release",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_limina_execution_release.py"],
        "purpose": "Verify execution release remains blocked until a source-backed selected provider has verified send and reply records.",
        "artifact": "reports/limina_execution_release_regression.md",
    },
    {
        "id": "regress_execution_authorization_log",
        "stage": "measurement_routing",
        "argv": ["scripts/regress_limina_execution_authorization_log.py"],
        "purpose": "Verify execution authorization logs require source-backed selected providers and source-file-backed authorization records.",
        "artifact": "reports/limina_execution_authorization_log_regression.md",
    },
    {
        "id": "preflight_local_capture",
        "stage": "measurement_routing",
        "argv": ["scripts/preflight_limina_local_capture.py"],
        "purpose": "Check filled local/outsource capture templates before any merge into evaluator tables.",
        "artifact": "reports/limina_local_capture_preflight.md",
    },
    {
        "id": "render_smoke_capture_tranche",
        "stage": "measurement_routing",
        "argv": ["scripts/render_limina_smoke_capture_tranche.py"],
        "purpose": "Render the smallest useful capture tranche for real-measurement pipeline rehearsal and early red flags.",
        "artifact": "reports/limina_smoke_capture_tranche.md",
    },
    {
        "id": "render_smoke_execution_queue",
        "stage": "measurement_routing",
        "argv": ["scripts/render_limina_smoke_execution_queue.py"],
        "purpose": "Turn smoke-tranche rows into a source-file-aware execution queue for real capture.",
        "artifact": "reports/limina_smoke_execution_queue.md",
    },
    {
        "id": "render_smoke_entry_sheet",
        "stage": "measurement_routing",
        "argv": ["scripts/render_limina_smoke_entry_sheet.py"],
        "purpose": "Render a single fillable smoke entry sheet while preserving any user-entered values.",
        "artifact": "reports/limina_smoke_entry_sheet.md",
    },
    {
        "id": "render_smoke_source_drop_plan",
        "stage": "measurement_routing",
        "argv": ["scripts/render_limina_smoke_source_drop_plan.py"],
        "purpose": "Create source-file drop directories and a missing-file plan for the smoke entry sheet.",
        "artifact": "reports/limina_smoke_source_drop_plan.md",
    },
    {
        "id": "render_smoke_source_values_sheet",
        "stage": "measurement_routing",
        "argv": ["scripts/render_limina_smoke_source_values_sheet.py"],
        "purpose": "Render a consolidated source-values sheet and starter batch for real smoke measurements.",
        "artifact": "reports/limina_smoke_source_values_sheet.md",
    },
    {
        "id": "audit_smoke_starter_batch_readiness",
        "stage": "measurement_routing",
        "argv": ["scripts/audit_limina_smoke_starter_batch_readiness.py"],
        "purpose": "Audit whether the 19-row smoke starter batch has real values and source files ready for import.",
        "artifact": "reports/limina_smoke_starter_batch_readiness.md",
    },
    {
        "id": "render_smoke_starter_execution_pack",
        "stage": "measurement_routing",
        "argv": ["scripts/render_limina_smoke_starter_execution_pack.py"],
        "purpose": "Render the operational file checklist for the 19-row smoke starter batch.",
        "artifact": "reports/limina_smoke_starter_execution_pack.md",
    },
    {
        "id": "render_smoke_starter_raw_file_template_pack",
        "stage": "measurement_routing",
        "argv": ["scripts/render_limina_smoke_starter_raw_file_template_pack.py"],
        "purpose": "Render source-class raw-file templates outside source-file roots for the starter batch.",
        "artifact": "reports/limina_smoke_starter_raw_file_template_pack.md",
    },
    {
        "id": "extract_smoke_raw_csv_values",
        "stage": "measurement_routing",
        "argv": ["scripts/extract_limina_smoke_raw_csv_values.py"],
        "purpose": "Extract source-backed values from existing raw CSV/TSV starter files without creating evidence.",
        "artifact": "reports/limina_smoke_raw_csv_value_extraction.md",
    },
    {
        "id": "intake_smoke_unstructured_sources",
        "stage": "measurement_routing",
        "argv": ["scripts/intake_limina_smoke_unstructured_sources.py"],
        "purpose": "Hash and route existing PDF/image starter source files for value extraction without creating evidence.",
        "artifact": "reports/limina_smoke_unstructured_source_intake.md",
    },
    {
        "id": "render_smoke_unstructured_review_values",
        "stage": "measurement_routing",
        "argv": ["scripts/render_limina_smoke_unstructured_review_values.py"],
        "purpose": "Render fillable source-value rows for manually extracting values from existing unstructured starter files.",
        "artifact": "reports/limina_smoke_unstructured_review_values.md",
    },
    {
        "id": "import_smoke_source_values",
        "stage": "measurement_routing",
        "argv": ["scripts/import_limina_smoke_source_values.py"],
        "purpose": "Import real source-file-backed value sidecars into the smoke entry sheet before validation and apply.",
        "artifact": "reports/limina_smoke_source_value_import.md",
    },
    {
        "id": "apply_smoke_entry_sheet",
        "stage": "measurement_routing",
        "argv": ["scripts/apply_limina_smoke_entry_sheet.py"],
        "purpose": "Apply validated filled smoke entry-sheet rows into the H-A/ZRC smoke templates.",
        "artifact": "reports/limina_smoke_entry_apply.md",
    },
    {
        "id": "refresh_smoke_execution_queue_after_entry_apply",
        "stage": "measurement_routing",
        "argv": ["scripts/render_limina_smoke_execution_queue.py"],
        "purpose": "Refresh smoke queue statuses after entry-sheet application and before preflight.",
        "artifact": "reports/limina_smoke_execution_queue.md",
    },
    {
        "id": "preflight_smoke_capture",
        "stage": "measurement_routing",
        "argv": [
            "scripts/preflight_limina_local_capture.py",
            "--tasks",
            "data/limina_smoke_capture_tasks.csv",
            "--h-a-local",
            "data/nhi_pedot_h_a_smoke_local_capture_template.csv",
            "--h-a-outsource",
            "data/nhi_pedot_h_a_smoke_osmolality_outsource_template.csv",
            "--zrc-local",
            "data/zrc_nd_phase_a_smoke_local_capture_template.csv",
            "--zrc-outsource",
            "data/zrc_nd_phase_a_smoke_osmolality_outsource_template.csv",
            "--json-out",
            "data/limina_smoke_capture_preflight.json",
            "--report",
            "reports/limina_smoke_capture_preflight.md",
        ],
        "purpose": "Check whether the smoke tranche is filled well enough for a merge rehearsal.",
        "artifact": "reports/limina_smoke_capture_preflight.md",
    },
    {
        "id": "run_smoke_rehearsal",
        "stage": "measurement_routing",
        "argv": ["scripts/run_limina_smoke_rehearsal.py"],
        "purpose": "Run smoke-only merge/QC/evaluation rehearsal into temporary files when preflight is ready.",
        "artifact": "reports/limina_smoke_rehearsal.md",
    },
    {
        "id": "render_zrc_phase_a_chain_of_custody",
        "stage": "zrc_phase_a",
        "argv": ["scripts/render_zrc_nd_phase_a_chain_of_custody.py"],
        "purpose": "Render ZRC-ND Phase A sample labels and chain-of-custody blanks.",
        "artifact": "reports/zrc_nd_phase_a_chain_of_custody.md",
    },
    {
        "id": "render_zrc_phase_a_delivery_package",
        "stage": "zrc_phase_a",
        "argv": ["scripts/render_zrc_nd_phase_a_delivery_package.py"],
        "purpose": "Render a sendable ZRC-ND Phase A delivery package manifest.",
        "artifact": "reports/zrc_nd_phase_a_delivery_package_manifest.md",
    },
    {
        "id": "render_zrc_phase_a_vendor_outreach",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/render_zrc_nd_phase_a_vendor_outreach.py"],
        "purpose": "Render vendor/cooperator screening for real ZRC-ND Phase A measurement execution.",
        "artifact": "reports/zrc_nd_phase_a_vendor_outreach_brief.md",
    },
    {
        "id": "render_zrc_phase_a_rfq_packet",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/render_zrc_nd_phase_a_rfq_packet.py"],
        "purpose": "Render per-vendor ZRC-ND Phase A RFQ text and scoring rubric.",
        "artifact": "reports/zrc_nd_phase_a_rfq_packet.md",
    },
    {
        "id": "render_zrc_phase_a_rfq_outbox",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/render_zrc_nd_phase_a_rfq_outbox.py"],
        "purpose": "Render vendor-specific ZRC-ND Phase A RFQ email files and zip bundles.",
        "artifact": "reports/zrc_nd_phase_a_rfq_outbox.md",
    },
    {
        "id": "render_zrc_phase_a_quote_tracker",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/render_zrc_nd_phase_a_quote_tracker.py"],
        "purpose": "Render a tracker for ZRC-ND Phase A RFQ replies and execution selection.",
        "artifact": "reports/zrc_nd_phase_a_quote_tracker.md",
    },
    {
        "id": "render_zrc_phase_a_vendor_contact_plan",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/render_zrc_nd_phase_a_vendor_contact_plan.py"],
        "purpose": "Render official contact channels for ZRC-ND Phase A RFQ bundles.",
        "artifact": "reports/zrc_nd_phase_a_vendor_contact_plan.md",
    },
    {
        "id": "render_zrc_phase_a_rfq_dispatch_manifest",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/render_zrc_nd_phase_a_rfq_dispatch_manifest.py"],
        "purpose": "Bind each ZRC-ND Phase A RFQ text file to the exact bundle, contact path, and confirmation-save path before manual dispatch.",
        "artifact": "reports/zrc_nd_phase_a_rfq_dispatch_manifest.md",
    },
    {
        "id": "intake_zrc_phase_a_rfq_send_confirmations",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/intake_limina_rfq_send_confirmations.py", "--profile", "zrc_phase_a"],
        "purpose": "Scan saved ZRC-ND Phase A send confirmations and conservatively register source-backed outreach.",
        "artifact": "reports/zrc_nd_phase_a_rfq_send_confirmation_intake.md",
    },
    {
        "id": "render_zrc_phase_a_rfq_send_confirmation_entry_sheet",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/render_zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.py"],
        "purpose": "Render guarded manual-entry rows for non-EML ZRC-ND Phase A send confirmations such as web-form screenshots or PDFs.",
        "artifact": "reports/zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.md",
    },
    {
        "id": "apply_zrc_phase_a_rfq_send_confirmation_entry_sheet",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/apply_zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.py"],
        "purpose": "Apply reviewed non-EML ZRC-ND Phase A send confirmations into the RFQ send log without treating outreach as evidence.",
        "artifact": "reports/zrc_nd_phase_a_rfq_send_confirmation_entry_apply.md",
    },
    {
        "id": "apply_zrc_phase_a_rfq_send_log",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/apply_limina_rfq_send_log.py", "--profile", "zrc_phase_a"],
        "purpose": "Render/apply verified ZRC-ND Phase A RFQ send confirmations into the quote tracker without treating outreach as evidence.",
        "artifact": "reports/zrc_nd_phase_a_rfq_send_log.md",
    },
    {
        "id": "intake_zrc_phase_a_rfq_replies",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/intake_limina_rfq_replies.py", "--profile", "zrc_phase_a"],
        "purpose": "Scan saved ZRC-ND Phase A vendor replies and conservatively register source-backed replies for review.",
        "artifact": "reports/zrc_nd_phase_a_rfq_reply_intake.md",
    },
    {
        "id": "apply_zrc_phase_a_rfq_reply_log",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/apply_limina_rfq_reply_log.py", "--profile", "zrc_phase_a"],
        "purpose": "Render/apply source-backed ZRC-ND Phase A RFQ replies into the quote tracker without treating replies as measurement evidence.",
        "artifact": "reports/zrc_nd_phase_a_rfq_reply_log.md",
    },
    {
        "id": "render_zrc_phase_a_rfq_dispatch_archive",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/render_zrc_nd_phase_a_rfq_dispatch_archive.py"],
        "purpose": "Render a single archive containing ZRC-ND Phase A RFQ text files, bundles, manifests, and confirmation templates for manual dispatch.",
        "artifact": "reports/zrc_nd_phase_a_rfq_dispatch_archive_manifest.md",
    },
    {
        "id": "render_zrc_phase_a_rfq_reply_action_pack",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/render_zrc_nd_phase_a_rfq_reply_action_pack.py"],
        "purpose": "Render source-backed reply intake/review checklist for ZRC-ND Phase A RFQ responses.",
        "artifact": "reports/zrc_nd_phase_a_rfq_reply_action_pack.md",
    },
    {
        "id": "render_zrc_phase_a_rfq_send_cockpit",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/render_zrc_nd_phase_a_rfq_send_cockpit.py"],
        "purpose": "Render a single local cockpit for manual ZRC-ND Phase A RFQ dispatch and source-file follow-through.",
        "artifact": "reports/zrc_nd_phase_a_rfq_send_cockpit.md",
    },
    {
        "id": "render_first_wave_rfq_dispatch_cockpit",
        "stage": "sourcing",
        "argv": ["scripts/render_limina_first_wave_rfq_dispatch_cockpit.py"],
        "purpose": "Render one combined H-A and ZRC first-wave RFQ dispatch cockpit for the real-measurement unlock step.",
        "artifact": "reports/limina_first_wave_rfq_dispatch_cockpit.md",
    },
    {
        "id": "process_first_wave_post_dispatch",
        "stage": "sourcing",
        "argv": ["scripts/process_limina_first_wave_post_dispatch.py"],
        "purpose": "Process saved first-wave RFQ confirmations and replies across H-A and ZRC without treating sourcing artifacts as evidence.",
        "artifact": "reports/limina_first_wave_post_dispatch_processing.md",
    },
    {
        "id": "evaluate_zrc_phase_a_quote_replies",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/evaluate_zrc_nd_phase_a_quote_replies.py"],
        "purpose": "Score any ZRC-ND Phase A RFQ replies without treating quotes as evidence.",
        "artifact": "reports/zrc_nd_phase_a_quote_selection.md",
    },
    {
        "id": "apply_zrc_phase_a_execution_authorization_log",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/apply_limina_execution_authorization_log.py", "--profile", "zrc_phase_a"],
        "purpose": "Render/validate human ZRC-ND Phase A execution authorization records without treating authorization as evidence.",
        "artifact": "reports/zrc_nd_phase_a_execution_authorization_log.md",
    },
    {
        "id": "audit_zrc_phase_a_execution_release",
        "stage": "zrc_phase_a_sourcing",
        "argv": ["scripts/audit_limina_execution_release.py", "--profile", "zrc_phase_a"],
        "purpose": "Block ZRC-ND Phase A sample or outsourced execution release until a source-backed selected provider is verified.",
        "artifact": "reports/zrc_nd_phase_a_execution_release_audit.md",
    },
    {
        "id": "render_zrc_phase_a_vendor_return_intake",
        "stage": "zrc_phase_a_intake",
        "argv": ["scripts/render_zrc_nd_phase_a_vendor_return_intake.py"],
        "purpose": "Check the ZRC-ND Phase A vendor-return inbox before merge/QC.",
        "artifact": "reports/zrc_nd_phase_a_vendor_return_intake.md",
    },
    {
        "id": "merge_zrc_phase_a_measurements",
        "stage": "zrc_phase_a_intake",
        "argv": ["scripts/merge_zrc_nd_measurements.py"],
        "purpose": "Merge returned ZRC-ND Phase A measurement rows into the active validation CSV.",
        "artifact": "reports/zrc_nd_measurement_merge.md",
    },
    {
        "id": "check_zrc_run_completeness",
        "stage": "zrc_phase_a_intake",
        "argv": ["scripts/check_zrc_nd_run_completeness.py"],
        "purpose": "Check whether active ZRC-ND non-cell rows are complete enough for gate interpretation.",
        "artifact": "reports/zrc_nd_run_completeness.md",
    },
    {
        "id": "evaluate_zrc_validation_runs",
        "stage": "zrc_phase_a_gate",
        "argv": ["scripts/evaluate_zrc_nd_validation_runs.py"],
        "purpose": "Evaluate the active ZRC-ND non-cell run table after any returned rows are merged.",
        "artifact": "reports/zrc_nd_validation_results.md",
    },
    {
        "id": "refresh_zrc_phase_a_sentinel_after_merge",
        "stage": "zrc_phase_a_gate",
        "argv": ["scripts/interpret_zrc_nd_sentinel.py"],
        "purpose": "Refresh the Phase A sentinel interpretation from the active ZRC-ND run table.",
        "artifact": "reports/zrc_nd_sentinel_interpretation.md",
    },
    {
        "id": "refresh_zrc_next_measurements_after_merge",
        "stage": "zrc_phase_a_next_actions",
        "argv": ["scripts/suggest_zrc_nd_next_measurements.py"],
        "purpose": "Refresh adaptive ZRC-ND measurement recommendations from the active run table and latest sentinel.",
        "artifact": "reports/zrc_nd_next_measurements.md",
    },
    {
        "id": "audit_zrc_readiness",
        "stage": "zrc_claim_guard",
        "argv": ["scripts/audit_zrc_nd_readiness.py"],
        "purpose": "Refresh the ZRC-ND readiness audit while preserving the no-measured-data blocker.",
        "artifact": "reports/zrc_nd_readiness_audit.md",
    },
    {
        "id": "select_portfolio_branch",
        "stage": "portfolio",
        "argv": ["scripts/select_limina_next_technology.py"],
        "purpose": "Refresh the portfolio branch selector across NHI-PEDOT and ZRC-ND.",
        "artifact": "reports/limina_technology_portfolio.md",
    },
    {
        "id": "render_second_wave_candidate_queue",
        "stage": "portfolio",
        "argv": ["scripts/render_limina_second_wave_candidate_queue.py"],
        "purpose": "Render the highest-value second-wave candidate scope-lock queue without bypassing first-wave evidence gates.",
        "artifact": "reports/limina_second_wave_candidate_queue.md",
    },
    {
        "id": "render_second_wave_scope_lock_pack",
        "stage": "portfolio",
        "argv": ["scripts/render_limina_second_wave_scope_lock_pack.py"],
        "purpose": "Turn ready second-wave candidates into material-identity and future source-class scope-lock tasks.",
        "artifact": "reports/limina_second_wave_scope_lock_pack.md",
    },
    {
        "id": "audit_claim_readiness",
        "stage": "claim_guard",
        "argv": ["scripts/audit_limina_suitability_claim.py"],
        "purpose": "Check whether any branch can support a first material suitability claim.",
        "artifact": "reports/limina_suitability_claim_audit.md",
    },
    {
        "id": "audit_portfolio_bypass_paths",
        "stage": "claim_guard",
        "argv": ["scripts/audit_limina_portfolio_bypass_paths.py"],
        "purpose": "Check whether any ranked prospect can bypass the active H-A gate and still satisfy the claim audit boundary.",
        "artifact": "reports/limina_portfolio_bypass_audit.md",
    },
    {
        "id": "regress_portfolio_claim_boundary",
        "stage": "claim_guard",
        "argv": ["scripts/regress_limina_portfolio_claim_boundary.py"],
        "purpose": "Verify the portfolio selector cannot declare suitability before the final claim audit.",
        "artifact": "reports/limina_portfolio_claim_boundary_regression.md",
    },
    {
        "id": "regress_source_file_claim_guard",
        "stage": "claim_guard",
        "argv": ["scripts/regress_limina_source_file_claim_guard.py"],
        "purpose": "Verify measured-looking rows without valid source_file provenance cannot become claimable.",
        "artifact": "reports/limina_source_file_claim_guard_regression.md",
    },
    {
        "id": "summarize_cycle_state",
        "stage": "cycle_state",
        "argv": ["scripts/run_limina_discovery_cycle.py"],
        "purpose": "Write the final next-action report for this iteration.",
        "artifact": "reports/limina_discovery_cycle_state.md",
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def run_command(item: dict[str, Any]) -> dict[str, Any]:
    argv = [sys.executable, *item["argv"]]
    started = time.perf_counter()
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    elapsed = round(time.perf_counter() - started, 3)
    return {
        "id": item["id"],
        "stage": item["stage"],
        "argv": argv,
        "purpose": item["purpose"],
        "artifact": item["artifact"],
        "returncode": completed.returncode,
        "elapsed_seconds": elapsed,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def tail(text: str, limit: int = 6) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines[-limit:])


def summarize(commands: list[dict[str, Any]]) -> dict[str, Any]:
    ranking = load_json(ROOT / "data" / "limina_discovery_ranking.json")
    claim = load_json(ROOT / "data" / "limina_suitability_claim_audit.json")
    portfolio_bypass = load_json(ROOT / "data" / "limina_portfolio_bypass_audit.json")
    cycle = load_json(ROOT / "data" / "limina_discovery_cycle_state.json")
    h_a = load_json(ROOT / "data" / "nhi_pedot_h_a_sentinel_interpretation.json")
    h_a_qc = load_json(ROOT / "data" / "nhi_pedot_h_a_intake_qc.json")
    h_a_merge = load_json(ROOT / "data" / "nhi_pedot_h_a_measurement_merge.json")
    h_a_source_values_sheet = load_json(ROOT / "data" / "nhi_pedot_h_a_source_values_sheet.json")
    h_a_source_drop = load_json(ROOT / "data" / "nhi_pedot_h_a_source_drop_plan.json")
    h_a_source_unlock_pack = load_json(ROOT / "data" / "nhi_pedot_h_a_source_unlock_pack.json")
    h_a_bundle_entry_sheet = load_json(ROOT / "data" / "nhi_pedot_h_a_bundle_entry_sheet.json")
    h_a_vendor_bundle_entry_sheet = load_json(ROOT / "data" / "nhi_pedot_h_a_vendor_bundle_entry_sheet.json")
    h_a_bundle_entry_apply = load_json(ROOT / "data" / "nhi_pedot_h_a_bundle_entry_apply.json")
    h_a_vendor_bundle_entry_apply = load_json(ROOT / "data" / "nhi_pedot_h_a_vendor_bundle_entry_apply.json")
    h_a_source_template_pack = load_json(ROOT / "data" / "nhi_pedot_h_a_source_file_template_pack.json")
    h_a_raw_csv_extraction = load_json(ROOT / "data" / "nhi_pedot_h_a_raw_csv_value_extraction.json")
    h_a_source_value_import = load_json(ROOT / "data" / "nhi_pedot_h_a_source_value_import.json")
    bench = load_json(ROOT / "data" / "nhi_pedot_h_a_bench_sheet.json")
    service = load_json(ROOT / "data" / "nhi_pedot_h_a_service_request.json")
    chain = load_json(ROOT / "data" / "nhi_pedot_h_a_chain_of_custody.json")
    submission = load_json(ROOT / "data" / "nhi_pedot_h_a_sample_submission_pack.json")
    split_scope = load_json(ROOT / "data" / "nhi_pedot_h_a_split_scope_plan.json")
    delivery = load_json(ROOT / "data" / "nhi_pedot_h_a_delivery_package_manifest.json")
    vendor = load_json(ROOT / "data" / "nhi_pedot_h_a_vendor_outreach.json")
    rfq = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_packet.json")
    rfq_outbox = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_outbox_manifest.json")
    quote_tracker = load_json(ROOT / "data" / "nhi_pedot_h_a_quote_tracker.json")
    rfq_send_confirmation_intake = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_intake.json")
    rfq_send_confirmation_entry_sheet = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.json")
    rfq_send_confirmation_entry_apply = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_entry_apply.json")
    rfq_send_log = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_send_log.json")
    rfq_reply_intake = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_reply_intake.json")
    rfq_reply_log = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_reply_log.json")
    contact_plan = load_json(ROOT / "data" / "nhi_pedot_h_a_vendor_contact_plan.json")
    contact_source_audit = load_json(ROOT / "data" / "nhi_pedot_h_a_vendor_contact_source_audit.json")
    rfq_eml_drafts = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_eml_drafts.json")
    rfq_eml_integrity = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_eml_integrity_audit.json")
    rfq_send_action_pack = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_send_action_pack.json")
    rfq_dispatch_manifest = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_dispatch_manifest.json")
    rfq_reply_action_pack = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_reply_action_pack.json")
    rfq_send_cockpit = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_send_cockpit.json")
    rfq_dispatch_archive = load_json(ROOT / "data" / "nhi_pedot_h_a_rfq_dispatch_archive_manifest.json")
    first_wave_rfq_dispatch_cockpit = load_json(ROOT / "data" / "limina_first_wave_rfq_dispatch_cockpit.json")
    first_wave_post_dispatch = load_json(ROOT / "data" / "limina_first_wave_post_dispatch_processing.json")
    second_wave_candidate_queue = load_json(ROOT / "data" / "limina_second_wave_candidate_queue.json")
    second_wave_scope_lock_pack = load_json(ROOT / "data" / "limina_second_wave_scope_lock_pack.json")
    quote_selection = load_json(ROOT / "data" / "nhi_pedot_h_a_quote_selection.json")
    execution_authorization = load_json(ROOT / "data" / "nhi_pedot_h_a_execution_authorization_log.json")
    execution_release = load_json(ROOT / "data" / "nhi_pedot_h_a_execution_release_audit.json")
    vendor_return = load_json(ROOT / "data" / "nhi_pedot_h_a_vendor_return_intake.json")
    forward = load_json(ROOT / "data" / "nhi_pedot_forward_gate_package.json")
    nhi_forward_source_values = load_json(ROOT / "data" / "nhi_pedot_forward_source_values_sheet.json")
    nhi_forward_source_drop = load_json(ROOT / "data" / "nhi_pedot_forward_source_drop_plan.json")
    nhi_forward_source_template_pack = load_json(ROOT / "data" / "nhi_pedot_forward_source_file_template_pack.json")
    nhi_forward_raw_csv_extraction = load_json(ROOT / "data" / "nhi_pedot_forward_raw_csv_value_extraction.json")
    nhi_forward_source_import = load_json(ROOT / "data" / "nhi_pedot_forward_source_values_import.json")
    nhi_results = load_json(ROOT / "data" / "nhi_pedot_results.json")
    nhi_long_source_values = load_json(ROOT / "data" / "nhi_pedot_long_source_values_sheet.json")
    nhi_long_source_drop = load_json(ROOT / "data" / "nhi_pedot_long_source_drop_plan.json")
    nhi_long_source_template_pack = load_json(ROOT / "data" / "nhi_pedot_long_source_file_template_pack.json")
    nhi_long_raw_csv_extraction = load_json(ROOT / "data" / "nhi_pedot_long_raw_csv_value_extraction.json")
    nhi_long_source_import = load_json(ROOT / "data" / "nhi_pedot_long_source_values_import.json")
    nhi_long_results = load_json(ROOT / "data" / "nhi_pedot_long_results.json")
    zrc_readiness = load_json(ROOT / "data" / "zrc_nd_readiness_audit.json")
    zrc_sentinel = load_json(ROOT / "data" / "zrc_nd_sentinel_interpretation.json")
    zrc_next = load_json(ROOT / "data" / "zrc_nd_next_measurements.json")
    zrc_phase_a_source_values = load_json(ROOT / "data" / "zrc_nd_phase_a_source_values_sheet.json")
    zrc_phase_a_source_drop = load_json(ROOT / "data" / "zrc_nd_phase_a_source_drop_plan.json")
    zrc_phase_a_source_template_pack = load_json(ROOT / "data" / "zrc_nd_phase_a_source_file_template_pack.json")
    zrc_phase_a_vendor_bundle_entry_sheet = load_json(ROOT / "data" / "zrc_nd_phase_a_vendor_bundle_entry_sheet.json")
    zrc_phase_a_vendor_bundle_entry_apply = load_json(ROOT / "data" / "zrc_nd_phase_a_vendor_bundle_entry_apply.json")
    zrc_phase_a_raw_csv_extraction = load_json(ROOT / "data" / "zrc_nd_phase_a_raw_csv_value_extraction.json")
    zrc_phase_a_source_import = load_json(ROOT / "data" / "zrc_nd_phase_a_source_values_import.json")
    zrc_service = load_json(ROOT / "data" / "zrc_nd_phase_a_service_request.json")
    zrc_chain = load_json(ROOT / "data" / "zrc_nd_phase_a_chain_of_custody.json")
    zrc_delivery = load_json(ROOT / "data" / "zrc_nd_phase_a_delivery_package_manifest.json")
    zrc_vendor = load_json(ROOT / "data" / "zrc_nd_phase_a_vendor_outreach.json")
    zrc_rfq = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_packet.json")
    zrc_rfq_outbox = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_outbox_manifest.json")
    zrc_quote_tracker = load_json(ROOT / "data" / "zrc_nd_phase_a_quote_tracker.json")
    zrc_rfq_send_confirmation_intake = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_send_confirmation_intake.json")
    zrc_rfq_send_confirmation_entry_sheet = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.json")
    zrc_rfq_send_confirmation_entry_apply = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_send_confirmation_entry_apply.json")
    zrc_rfq_send_log = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_send_log.json")
    zrc_rfq_reply_intake = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_reply_intake.json")
    zrc_rfq_reply_log = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_reply_log.json")
    zrc_contact_plan = load_json(ROOT / "data" / "zrc_nd_phase_a_vendor_contact_plan.json")
    zrc_dispatch_manifest = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_manifest.json")
    zrc_dispatch_archive = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_archive_manifest.json")
    zrc_reply_action_pack = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_reply_action_pack.json")
    zrc_send_cockpit = load_json(ROOT / "data" / "zrc_nd_phase_a_rfq_send_cockpit.json")
    zrc_quote_selection = load_json(ROOT / "data" / "zrc_nd_phase_a_quote_selection.json")
    zrc_execution_authorization = load_json(ROOT / "data" / "zrc_nd_phase_a_execution_authorization_log.json")
    zrc_execution_release = load_json(ROOT / "data" / "zrc_nd_phase_a_execution_release_audit.json")
    zrc_vendor_return = load_json(ROOT / "data" / "zrc_nd_phase_a_vendor_return_intake.json")
    zrc_merge = load_json(ROOT / "data" / "zrc_nd_measurement_merge.json")
    zrc_completeness = load_json(ROOT / "data" / "zrc_nd_run_completeness.json")
    zrc_results = load_json(ROOT / "data" / "zrc_nd_validation_results.json")
    hybrid = load_json(ROOT / "data" / "limina_hybrid_measurement_plan.json")
    local_capture = load_json(ROOT / "data" / "limina_local_capture_pack.json")
    source_manifest = load_json(ROOT / "data" / "limina_source_file_manifest.json")
    source_inventory = load_json(ROOT / "data" / "limina_source_file_inventory.json")
    local_preflight = load_json(ROOT / "data" / "limina_local_capture_preflight.json")
    smoke = load_json(ROOT / "data" / "limina_smoke_capture_tranche.json")
    smoke_queue = load_json(ROOT / "data" / "limina_smoke_execution_queue.json")
    smoke_entry_sheet = load_json(ROOT / "data" / "limina_smoke_entry_sheet.json")
    smoke_source_drop = load_json(ROOT / "data" / "limina_smoke_source_drop_plan.json")
    smoke_source_values_sheet = load_json(ROOT / "data" / "limina_smoke_source_values_sheet.json")
    smoke_starter_readiness = load_json(ROOT / "data" / "limina_smoke_starter_batch_readiness.json")
    smoke_starter_execution_pack = load_json(ROOT / "data" / "limina_smoke_starter_execution_pack.json")
    smoke_starter_template_pack = load_json(ROOT / "data" / "limina_smoke_starter_raw_file_template_pack.json")
    smoke_raw_csv_extraction = load_json(ROOT / "data" / "limina_smoke_raw_csv_value_extraction.json")
    smoke_unstructured_intake = load_json(ROOT / "data" / "limina_smoke_unstructured_source_intake.json")
    smoke_unstructured_review_values = load_json(ROOT / "data" / "limina_smoke_unstructured_review_values.json")
    smoke_source_value_import = load_json(ROOT / "data" / "limina_smoke_source_value_import.json")
    smoke_entry_apply = load_json(ROOT / "data" / "limina_smoke_entry_apply.json")
    smoke_preflight = load_json(ROOT / "data" / "limina_smoke_capture_preflight.json")
    smoke_rehearsal = load_json(ROOT / "data" / "limina_smoke_rehearsal.json")
    failed = [item for item in commands if item["returncode"] != 0]
    provenance = h_a.get("provenance", {})
    issue_counts = h_a_qc.get("issue_counts", {})
    merge_stats = h_a_merge.get("stats", {})
    h_a_source_values_sheet_summary = h_a_source_values_sheet.get("summary", {})
    h_a_source_drop_summary = h_a_source_drop.get("summary", {})
    h_a_source_unlock_pack_summary = h_a_source_unlock_pack.get("summary", {})
    h_a_bundle_entry_sheet_summary = h_a_bundle_entry_sheet.get("summary", {})
    h_a_vendor_bundle_entry_sheet_summary = h_a_vendor_bundle_entry_sheet.get("summary", {})
    h_a_bundle_entry_apply_summary = h_a_bundle_entry_apply.get("summary", {})
    h_a_vendor_bundle_entry_apply_summary = h_a_vendor_bundle_entry_apply.get("summary", {})
    h_a_source_template_pack_summary = h_a_source_template_pack.get("summary", {})
    h_a_raw_csv_extraction_summary = h_a_raw_csv_extraction.get("summary", {})
    h_a_source_value_import_summary = h_a_source_value_import.get("summary", {})
    zrc_merge_stats = zrc_merge.get("stats", {})
    zrc_result_summary = zrc_results.get("summary", {})
    hybrid_summary = hybrid.get("summary", {})
    hybrid_routes = hybrid_summary.get("route_totals", {})
    local_capture_summary = local_capture.get("summary", {})
    local_preflight_issue_counts = local_preflight.get("issue_counts", {})
    source_inventory_summary = source_inventory.get("summary", {})
    smoke_summary = smoke.get("summary", {})
    smoke_queue_summary = smoke_queue.get("summary", {})
    smoke_entry_sheet_summary = smoke_entry_sheet.get("summary", {})
    smoke_source_drop_summary = smoke_source_drop.get("summary", {})
    smoke_source_values_sheet_summary = smoke_source_values_sheet.get("summary", {})
    smoke_starter_readiness_summary = smoke_starter_readiness.get("summary", {})
    smoke_starter_execution_pack_summary = smoke_starter_execution_pack.get("summary", {})
    smoke_starter_template_pack_summary = smoke_starter_template_pack.get("summary", {})
    smoke_raw_csv_extraction_summary = smoke_raw_csv_extraction.get("summary", {})
    smoke_unstructured_intake_summary = smoke_unstructured_intake.get("summary", {})
    smoke_unstructured_review_values_summary = smoke_unstructured_review_values.get("summary", {})
    smoke_source_value_import_summary = smoke_source_value_import.get("summary", {})
    smoke_entry_apply_summary = smoke_entry_apply.get("summary", {})
    smoke_preflight_issue_counts = smoke_preflight.get("issue_counts", {})
    smoke_rehearsal_issue_counts = smoke_rehearsal.get("issue_counts", {})
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
    zrc_phase_a_source_values_summary = zrc_phase_a_source_values.get("summary", {})
    zrc_phase_a_source_drop_summary = zrc_phase_a_source_drop.get("summary", {})
    zrc_phase_a_source_template_pack_summary = zrc_phase_a_source_template_pack.get("summary", {})
    zrc_phase_a_vendor_bundle_entry_sheet_summary = zrc_phase_a_vendor_bundle_entry_sheet.get("summary", {})
    zrc_phase_a_vendor_bundle_entry_apply_summary = zrc_phase_a_vendor_bundle_entry_apply.get("summary", {})
    zrc_phase_a_raw_csv_extraction_summary = zrc_phase_a_raw_csv_extraction.get("summary", {})
    zrc_phase_a_source_import_summary = zrc_phase_a_source_import.get("summary", {})
    zrc_dispatch_manifest_summary = zrc_dispatch_manifest.get("summary", {})
    zrc_dispatch_archive_summary = zrc_dispatch_archive.get("summary", {})
    zrc_send_confirmation_entry_sheet_summary = zrc_rfq_send_confirmation_entry_sheet.get("summary", {})
    zrc_send_confirmation_entry_apply_summary = zrc_rfq_send_confirmation_entry_apply.get("summary", {})
    zrc_reply_action_summary = zrc_reply_action_pack.get("summary", {})
    zrc_send_cockpit_summary = zrc_send_cockpit.get("summary", {})
    rfq_send_confirmation_intake_summary = rfq_send_confirmation_intake
    rfq_send_confirmation_entry_sheet_summary = rfq_send_confirmation_entry_sheet.get("summary", {})
    rfq_send_confirmation_entry_apply_summary = rfq_send_confirmation_entry_apply.get("summary", {})
    contact_source_audit_summary = contact_source_audit.get("summary", {})
    rfq_eml_drafts_summary = rfq_eml_drafts.get("summary", {})
    rfq_eml_integrity_summary = rfq_eml_integrity.get("summary", {})
    rfq_send_action_pack_summary = rfq_send_action_pack.get("summary", {})
    rfq_dispatch_manifest_summary = rfq_dispatch_manifest.get("summary", {})
    rfq_reply_action_pack_summary = rfq_reply_action_pack.get("summary", {})
    rfq_send_cockpit_summary = rfq_send_cockpit.get("summary", {})
    rfq_dispatch_archive_summary = rfq_dispatch_archive.get("summary", {})
    first_wave_rfq_dispatch_cockpit_summary = first_wave_rfq_dispatch_cockpit.get("summary", {})
    first_wave_post_dispatch_cockpit_summary = first_wave_post_dispatch.get("first_wave_cockpit_summary", {})
    second_wave_candidate_queue_summary = second_wave_candidate_queue.get("summary", {})
    second_wave_scope_lock_pack_summary = second_wave_scope_lock_pack.get("summary", {})
    portfolio_bypass_summary = portfolio_bypass.get("summary", {})
    return {
        "status": "failed" if failed else "completed",
        "failed_command_ids": [item["id"] for item in failed],
        "top_candidate": ranking.get("top_candidate"),
        "top_priority": ranking.get("top_priority"),
        "claim_ready": bool(claim.get("claim_ready")),
        "claim_status": claim.get("status", "unknown"),
        "portfolio_bypass_status": portfolio_bypass.get("status", "unknown"),
        "portfolio_bypass_non_h_a_claim_ready_rows": portfolio_bypass_summary.get("non_h_a_claim_ready_rows", 0),
        "portfolio_bypass_top_non_h_a_candidate": portfolio_bypass_summary.get("top_non_h_a_candidate"),
        "portfolio_bypass_recommended_action": portfolio_bypass_summary.get("recommended_action", "-"),
        "mission_state": cycle.get("mission_state", "unknown"),
        "mission_reason": cycle.get("state_reason", "unknown"),
        "h_a_status": h_a.get("status", "unknown"),
        "h_a_measured_rows": provenance.get("measured_row_count", 0),
        "h_a_total_rows": provenance.get("row_count", 0),
        "h_a_placeholder_rows": provenance.get("placeholder_row_count", 0),
        "h_a_synthetic_rows": provenance.get("synthetic_row_count", 0),
        "h_a_qc_status": h_a_qc.get("status", "unknown"),
        "h_a_qc_errors": issue_counts.get("error", 0),
        "h_a_qc_warnings": issue_counts.get("warning", 0),
        "h_a_source_values_sheet_status": h_a_source_values_sheet.get("status", "unknown"),
        "h_a_source_values_sheet_rows": h_a_source_values_sheet_summary.get("source_value_rows", 0),
        "h_a_source_values_sheet_filled_rows": h_a_source_values_sheet_summary.get("filled_value_rows", 0),
        "h_a_source_values_sheet_source_file_exists_rows": h_a_source_values_sheet_summary.get("source_file_exists_rows", 0),
        "h_a_source_values_sheet_import_ready_rows": h_a_source_values_sheet_summary.get("import_ready_rows", 0),
        "h_a_source_drop_status": h_a_source_drop.get("status", "unknown"),
        "h_a_source_drop_planned_files": h_a_source_drop_summary.get("planned_source_file_count", 0),
        "h_a_source_drop_dirs": h_a_source_drop_summary.get("source_dir_count", 0),
        "h_a_source_drop_existing_files": h_a_source_drop_summary.get("existing_source_file_count", 0),
        "h_a_source_drop_missing_files": h_a_source_drop_summary.get("missing_source_file_count", 0),
        "h_a_source_unlock_pack_status": h_a_source_unlock_pack.get("status", "unknown"),
        "h_a_source_unlock_pack_source_rows": h_a_source_unlock_pack_summary.get("source_value_rows", 0),
        "h_a_source_unlock_pack_bundles": h_a_source_unlock_pack_summary.get("bundle_count", 0),
        "h_a_source_unlock_pack_existing_files": h_a_source_unlock_pack_summary.get("existing_bundle_files", 0),
        "h_a_source_unlock_pack_missing_files": h_a_source_unlock_pack_summary.get("missing_bundle_files", 0),
        "h_a_bundle_entry_sheet_status": h_a_bundle_entry_sheet.get("status", "unknown"),
        "h_a_bundle_entry_sheet_rows": h_a_bundle_entry_sheet_summary.get("bundle_rows", 0),
        "h_a_bundle_entry_sheet_filled_rows": h_a_bundle_entry_sheet_summary.get("filled_bundle_rows", 0),
        "h_a_bundle_entry_sheet_ready_rows": h_a_bundle_entry_sheet_summary.get("ready_to_apply_rows", 0),
        "h_a_bundle_entry_sheet_existing_files": h_a_bundle_entry_sheet_summary.get("source_file_exists_rows", 0),
        "h_a_vendor_bundle_entry_sheet_status": h_a_vendor_bundle_entry_sheet.get("status", "unknown"),
        "h_a_vendor_bundle_entry_sheet_rows": h_a_vendor_bundle_entry_sheet_summary.get("bundle_rows", 0),
        "h_a_vendor_bundle_entry_sheet_ready_rows": h_a_vendor_bundle_entry_sheet_summary.get("ready_to_apply_rows", 0),
        "h_a_vendor_bundle_entry_sheet_blocked_rows": h_a_vendor_bundle_entry_sheet_summary.get("blocked_rows", 0),
        "h_a_vendor_bundle_entry_sheet_existing_files": h_a_vendor_bundle_entry_sheet_summary.get("source_file_exists_rows", 0),
        "h_a_bundle_entry_apply_status": h_a_bundle_entry_apply.get("status", "unknown"),
        "h_a_bundle_entry_apply_bundles": h_a_bundle_entry_apply_summary.get("applied_bundles", 0),
        "h_a_bundle_entry_apply_source_rows": h_a_bundle_entry_apply_summary.get("applied_source_value_rows", 0),
        "h_a_bundle_entry_apply_errors": h_a_bundle_entry_apply_summary.get("error_count", 0),
        "h_a_vendor_bundle_entry_apply_status": h_a_vendor_bundle_entry_apply.get("status", "unknown"),
        "h_a_vendor_bundle_entry_apply_sheet_exists": bool(h_a_vendor_bundle_entry_apply_summary.get("sheet_exists")),
        "h_a_vendor_bundle_entry_apply_bundles": h_a_vendor_bundle_entry_apply_summary.get("applied_bundles", 0),
        "h_a_vendor_bundle_entry_apply_source_rows": h_a_vendor_bundle_entry_apply_summary.get("applied_source_value_rows", 0),
        "h_a_vendor_bundle_entry_apply_errors": h_a_vendor_bundle_entry_apply_summary.get("error_count", 0),
        "h_a_source_template_pack_status": h_a_source_template_pack.get("status", "unknown"),
        "h_a_source_template_pack_templates": h_a_source_template_pack_summary.get("source_class_template_count", 0),
        "h_a_source_template_pack_target_files": h_a_source_template_pack_summary.get("target_source_file_count", 0),
        "h_a_raw_csv_extraction_status": h_a_raw_csv_extraction.get("status", "unknown"),
        "h_a_raw_csv_extraction_files": h_a_raw_csv_extraction_summary.get("raw_csv_found", 0),
        "h_a_raw_csv_extraction_rows": h_a_raw_csv_extraction_summary.get("extracted_rows", 0),
        "h_a_raw_csv_extraction_errors": h_a_raw_csv_extraction_summary.get("error_count", 0),
        "h_a_source_value_import_status": h_a_source_value_import.get("status", "unknown"),
        "h_a_source_value_import_files": h_a_source_value_import_summary.get("source_value_files", 0),
        "h_a_source_value_import_rows": h_a_source_value_import_summary.get("source_value_rows", 0),
        "h_a_source_value_import_imported_rows": h_a_source_value_import_summary.get("imported_rows", 0),
        "h_a_source_value_import_errors": h_a_source_value_import_summary.get("error_count", 0),
        "h_a_merge_applied_values": merge_stats.get("applied_values", 0),
        "h_a_merge_unresolved_targets": merge_stats.get("unresolved_targets", 0),
        "h_a_bench_tasks": bench.get("task_count", 0),
        "h_a_blank_raw_entries_to_fill": bench.get("blank_raw_entries_to_fill", 0),
        "h_a_service_request_status": service.get("status", "unknown"),
        "h_a_service_request_raw_entries": service.get("requested_matrix", {}).get("raw_entries", 0),
        "h_a_chain_of_custody_status": chain.get("status", "unknown"),
        "h_a_sample_label_count": chain.get("sample_label_count", 0),
        "h_a_chain_of_custody_rows": chain.get("chain_of_custody_row_count", 0),
        "h_a_pending_transfer_rows": chain.get("pending_transfer_rows", 0),
        "h_a_sample_submission_status": submission.get("status", "unknown"),
        "h_a_sample_submission_shipping_status": submission.get("shipping_status", "unknown"),
        "h_a_split_scope_status": split_scope.get("status", "unknown"),
        "h_a_split_scope_pair_count": split_scope.get("pair_count", 0),
        "h_a_split_scope_preferred_count": split_scope.get("preferred_pair_count", 0),
        "h_a_delivery_package_status": delivery.get("status", "unknown"),
        "h_a_delivery_package_missing_files": len(delivery.get("missing_required_file_ids", [])),
        "h_a_vendor_outreach_status": vendor.get("status", "unknown"),
        "h_a_vendor_first_wave_count": len(vendor.get("first_wave", [])),
        "h_a_rfq_packet_status": rfq.get("status", "unknown"),
        "h_a_rfq_outbox_status": rfq_outbox.get("status", "unknown"),
        "h_a_rfq_outbox_ready_count": rfq_outbox.get("ready_to_send_count", 0),
        "h_a_rfq_outbox_quote_count": rfq_outbox.get("quote_request_count", 0),
        "h_a_quote_tracker_status": quote_tracker.get("status", "unknown"),
        "h_a_rfq_send_confirmation_intake_status": rfq_send_confirmation_intake.get("status", "unknown"),
        "h_a_rfq_send_confirmation_intake_files": rfq_send_confirmation_intake_summary.get("row_count", 0),
        "h_a_rfq_send_confirmation_intake_applied": rfq_send_confirmation_intake_summary.get("applied_rows", 0),
        "h_a_rfq_send_confirmation_intake_needs_review": rfq_send_confirmation_intake_summary.get("needs_review_rows", 0),
        "h_a_rfq_send_confirmation_intake_bundle_matched": rfq_send_confirmation_intake_summary.get("bundle_hash_matched_rows", 0),
        "h_a_rfq_send_confirmation_entry_sheet_status": rfq_send_confirmation_entry_sheet.get("status", "unknown"),
        "h_a_rfq_send_confirmation_entry_sheet_rows": rfq_send_confirmation_entry_sheet_summary.get("entry_rows", 0),
        "h_a_rfq_send_confirmation_entry_sheet_source_files": rfq_send_confirmation_entry_sheet_summary.get("source_file_present_rows", 0),
        "h_a_rfq_send_confirmation_entry_sheet_ready": rfq_send_confirmation_entry_sheet_summary.get("ready_to_apply_rows", 0),
        "h_a_rfq_send_confirmation_entry_sheet_blocked": rfq_send_confirmation_entry_sheet_summary.get("blocked_rows", 0),
        "h_a_rfq_send_confirmation_entry_apply_status": rfq_send_confirmation_entry_apply.get("status", "unknown"),
        "h_a_rfq_send_confirmation_entry_apply_apply_rows": rfq_send_confirmation_entry_apply_summary.get("apply_rows", 0),
        "h_a_rfq_send_confirmation_entry_apply_applied": rfq_send_confirmation_entry_apply_summary.get("applied_rows", 0),
        "h_a_rfq_send_confirmation_entry_apply_blocked": rfq_send_confirmation_entry_apply_summary.get("blocked_rows", 0),
        "h_a_rfq_send_log_status": rfq_send_log.get("status", "unknown"),
        "h_a_rfq_send_log_rows": rfq_send_log.get("row_count", 0),
        "h_a_rfq_send_log_sent_rows": rfq_send_log.get("sent_rows", 0),
        "h_a_rfq_send_log_valid_sent_rows": rfq_send_log.get("valid_sent_rows", 0),
        "h_a_rfq_send_log_applied_dates": rfq_send_log.get("applied_tracker_contact_dates", 0),
        "h_a_rfq_send_log_errors": rfq_send_log.get("error_count", 0),
        "h_a_rfq_reply_intake_status": rfq_reply_intake.get("status", "unknown"),
        "h_a_rfq_reply_intake_files": rfq_reply_intake.get("row_count", 0),
        "h_a_rfq_reply_intake_applied": rfq_reply_intake.get("applied_rows", 0),
        "h_a_rfq_reply_intake_needs_review": rfq_reply_intake.get("needs_manual_review_rows", 0),
        "h_a_rfq_reply_intake_needs_verified_send": rfq_reply_intake.get("needs_verified_send_rows", 0),
        "h_a_rfq_reply_log_status": rfq_reply_log.get("status", "unknown"),
        "h_a_rfq_reply_log_rows": rfq_reply_log.get("row_count", 0),
        "h_a_rfq_reply_log_received_rows": rfq_reply_log.get("received_rows", 0),
        "h_a_rfq_reply_log_valid_rows": rfq_reply_log.get("valid_reply_rows", 0),
        "h_a_rfq_reply_log_applied_fields": rfq_reply_log.get("applied_tracker_field_updates", 0),
        "h_a_rfq_reply_log_errors": rfq_reply_log.get("error_count", 0),
        "h_a_vendor_contact_plan_status": contact_plan.get("status", "unknown"),
        "h_a_vendor_contact_ready_count": contact_plan.get("status_counts", {}).get("ready_to_send", 0),
        "h_a_vendor_contact_standby_count": contact_plan.get("status_counts", {}).get("standby_secondary_wave", 0),
        "h_a_vendor_contact_row_count": contact_plan.get("row_count", 0),
        "h_a_vendor_contact_source_audit_status": contact_source_audit.get("status", "unknown"),
        "h_a_vendor_contact_source_audit_rows": contact_source_audit_summary.get("audit_rows", 0),
        "h_a_vendor_contact_source_audit_pass_rows": contact_source_audit_summary.get("pass_rows", 0),
        "h_a_vendor_contact_source_audit_fail_rows": contact_source_audit_summary.get("fail_rows", 0),
        "h_a_vendor_contact_source_audit_stale_rows": contact_source_audit_summary.get("stale_proof_rows", 0),
        "h_a_rfq_eml_drafts_status": rfq_eml_drafts.get("status", "unknown"),
        "h_a_rfq_eml_drafts_rows": rfq_eml_drafts_summary.get("draft_rows", 0),
        "h_a_rfq_eml_drafts_ready_rows": rfq_eml_drafts_summary.get("ready_to_open_rows", 0),
        "h_a_rfq_eml_drafts_missing_to_rows": rfq_eml_drafts_summary.get("missing_to_address_rows", 0),
        "h_a_rfq_eml_drafts_missing_bundle_rows": rfq_eml_drafts_summary.get("missing_bundle_rows", 0),
        "h_a_rfq_eml_integrity_status": rfq_eml_integrity.get("status", "unknown"),
        "h_a_rfq_eml_integrity_rows": rfq_eml_integrity_summary.get("audit_rows", 0),
        "h_a_rfq_eml_integrity_pass_rows": rfq_eml_integrity_summary.get("pass_rows", 0),
        "h_a_rfq_eml_integrity_fail_rows": rfq_eml_integrity_summary.get("fail_rows", 0),
        "h_a_rfq_eml_integrity_attachment_mismatch_rows": rfq_eml_integrity_summary.get("attachment_mismatch_rows", 0),
        "h_a_rfq_send_action_pack_status": rfq_send_action_pack.get("status", "unknown"),
        "h_a_rfq_send_action_rows": rfq_send_action_pack_summary.get("action_rows", 0),
        "h_a_rfq_send_action_ready_rows": rfq_send_action_pack_summary.get("ready_to_send_rows", 0),
        "h_a_rfq_send_action_verified_rows": rfq_send_action_pack_summary.get("sent_confirmation_verified_rows", 0),
        "h_a_rfq_send_action_needs_confirmation_rows": rfq_send_action_pack_summary.get("sent_needs_confirmation_rows", 0),
        "h_a_rfq_dispatch_manifest_status": rfq_dispatch_manifest.get("status", "unknown"),
        "h_a_rfq_dispatch_manifest_rows": rfq_dispatch_manifest_summary.get("dispatch_rows", 0),
        "h_a_rfq_dispatch_manifest_ready_rows": rfq_dispatch_manifest_summary.get("ready_for_manual_dispatch_rows", 0),
        "h_a_rfq_dispatch_manifest_blocked_rows": rfq_dispatch_manifest_summary.get("blocked_rows", 0),
        "h_a_rfq_dispatch_manifest_bundle_match_rows": rfq_dispatch_manifest_summary.get("bundle_sha256_match_rows", 0),
        "h_a_rfq_reply_action_pack_status": rfq_reply_action_pack.get("status", "unknown"),
        "h_a_rfq_reply_action_rows": rfq_reply_action_pack_summary.get("action_rows", 0),
        "h_a_rfq_reply_action_waiting_for_send": rfq_reply_action_pack_summary.get("waiting_for_send_rows", 0),
        "h_a_rfq_reply_action_awaiting_reply": rfq_reply_action_pack_summary.get("awaiting_reply_rows", 0),
        "h_a_rfq_reply_action_needs_source_file": rfq_reply_action_pack_summary.get("received_needs_source_file_rows", 0),
        "h_a_rfq_reply_action_ready_to_apply": rfq_reply_action_pack_summary.get("ready_for_reply_log_apply_rows", 0),
        "h_a_rfq_send_cockpit_status": rfq_send_cockpit.get("status", "unknown"),
        "h_a_rfq_send_cockpit_rows": rfq_send_cockpit_summary.get("vendor_rows", 0),
        "h_a_rfq_send_cockpit_ready_rows": rfq_send_cockpit_summary.get("ready_to_use_rows", 0),
        "h_a_rfq_send_cockpit_confirmations": rfq_send_cockpit_summary.get("confirmation_files_present", 0),
        "h_a_rfq_send_cockpit_replies": rfq_send_cockpit_summary.get("reply_files_present", 0),
        "h_a_rfq_send_cockpit_missing_eml": rfq_send_cockpit_summary.get("missing_eml_rows", 0),
        "h_a_rfq_send_cockpit_missing_bundle": rfq_send_cockpit_summary.get("missing_bundle_rows", 0),
        "h_a_rfq_send_cockpit_html": rfq_send_cockpit.get("generated_artifacts", {}).get("html", ""),
        "h_a_rfq_dispatch_archive_status": rfq_dispatch_archive.get("status", "unknown"),
        "h_a_rfq_dispatch_archive_files": rfq_dispatch_archive_summary.get("included_files", 0),
        "h_a_rfq_dispatch_archive_missing_files": rfq_dispatch_archive_summary.get("missing_files", 0),
        "h_a_rfq_dispatch_archive_hash_mismatches": rfq_dispatch_archive_summary.get("hash_mismatch_files", 0),
        "h_a_rfq_dispatch_archive_sha256": rfq_dispatch_archive_summary.get("archive_sha256", ""),
        "h_a_rfq_dispatch_archive_path": rfq_dispatch_archive.get("generated_artifacts", {}).get("archive", ""),
        "first_wave_rfq_dispatch_cockpit_status": first_wave_rfq_dispatch_cockpit.get("status", "unknown"),
        "first_wave_rfq_dispatch_cockpit_rows": first_wave_rfq_dispatch_cockpit_summary.get("vendor_rows", 0),
        "first_wave_rfq_dispatch_cockpit_ready_rows": first_wave_rfq_dispatch_cockpit_summary.get("ready_to_send_rows", 0),
        "first_wave_rfq_dispatch_cockpit_confirmations": first_wave_rfq_dispatch_cockpit_summary.get("confirmation_files_present", 0),
        "first_wave_rfq_dispatch_cockpit_replies": first_wave_rfq_dispatch_cockpit_summary.get("reply_files_present", 0),
        "first_wave_rfq_dispatch_cockpit_missing_messages": first_wave_rfq_dispatch_cockpit_summary.get("missing_message_files", 0),
        "first_wave_rfq_dispatch_cockpit_missing_bundles": first_wave_rfq_dispatch_cockpit_summary.get("missing_bundle_files", 0),
        "first_wave_rfq_dispatch_cockpit_html": first_wave_rfq_dispatch_cockpit.get("generated_artifacts", {}).get("html", ""),
        "first_wave_post_dispatch_status": first_wave_post_dispatch.get("status", "unknown"),
        "first_wave_post_dispatch_failed_commands": len(first_wave_post_dispatch.get("failed_command_ids", [])),
        "first_wave_post_dispatch_confirmations": first_wave_post_dispatch_cockpit_summary.get("confirmation_files_present", 0),
        "first_wave_post_dispatch_replies": first_wave_post_dispatch_cockpit_summary.get("reply_files_present", 0),
        "second_wave_candidate_queue_status": second_wave_candidate_queue.get("status", "unknown"),
        "second_wave_candidate_queue_rows": second_wave_candidate_queue_summary.get("queue_rows", 0),
        "second_wave_candidate_queue_ready_scope_lock_rows": second_wave_candidate_queue_summary.get("ready_scope_lock_rows", 0),
        "second_wave_candidate_queue_watch_rows": second_wave_candidate_queue_summary.get("watch_rows", 0),
        "second_wave_candidate_queue_hold_rows": second_wave_candidate_queue_summary.get("hold_rows", 0),
        "second_wave_scope_lock_pack_status": second_wave_scope_lock_pack.get("status", "unknown"),
        "second_wave_scope_lock_pack_ready_candidates": second_wave_scope_lock_pack_summary.get("ready_candidate_count", 0),
        "second_wave_scope_lock_pack_tasks": second_wave_scope_lock_pack_summary.get("task_count", 0),
        "second_wave_scope_lock_pack_source_classes": second_wave_scope_lock_pack_summary.get("source_file_class_count", 0),
        "second_wave_scope_lock_pack_claim_evidence_created": bool(second_wave_scope_lock_pack_summary.get("claim_evidence_created")),
        "h_a_quote_selection_status": quote_selection.get("status", "unknown"),
        "h_a_quote_selection_sent_count": quote_selection.get("sent_count", 0),
        "h_a_quote_selection_reply_count": quote_selection.get("reply_count", 0),
        "h_a_quote_selection_source_backed_reply_count": quote_selection.get("source_backed_reply_count", 0),
        "h_a_quote_selection_shortlist_count": quote_selection.get("shortlist_count", 0),
        "h_a_execution_authorization_status": execution_authorization.get("status", "unknown"),
        "h_a_execution_authorization_rows": execution_authorization.get("row_count", 0),
        "h_a_execution_authorization_valid_rows": execution_authorization.get("valid_authorization_rows", 0),
        "h_a_execution_authorization_errors": execution_authorization.get("error_count", 0),
        "h_a_execution_release_status": execution_release.get("status", "unknown"),
        "h_a_execution_release_ready": bool(execution_release.get("ready_for_execution_authorization")),
        "h_a_execution_release_released": bool(execution_release.get("released_for_execution")),
        "h_a_execution_release_blockers": execution_release.get("blocker_count", 0),
        "h_a_execution_release_authorization_blockers": execution_release.get("authorization_blocker_count", 0),
        "h_a_vendor_return_status": vendor_return.get("status", "unknown"),
        "h_a_vendor_return_raw_value_rows": vendor_return.get("raw_measurements", {}).get("value_row_count", 0),
        "h_a_vendor_return_bundle_entry_rows": vendor_return.get("bundle_entry_sheet", {}).get("row_count", 0),
        "h_a_vendor_return_bundle_entry_apply_rows": vendor_return.get("bundle_entry_sheet", {}).get("apply_row_count", 0),
        "h_a_vendor_return_export_files": vendor_return.get("instrument_export_file_count", 0),
        "forward_gate_status": forward.get("status", "unknown"),
        "forward_gate_rows": forward.get("row_count", 0),
        "nhi_forward_source_values_status": nhi_forward_source_values.get("status", "unknown"),
        "nhi_forward_source_values_rows": nhi_forward_source_values_summary.get("source_value_rows", 0),
        "nhi_forward_source_values_filled_rows": nhi_forward_source_values_summary.get("filled_value_rows", 0),
        "nhi_forward_source_values_import_ready_rows": nhi_forward_source_values_summary.get("import_ready_rows", 0),
        "nhi_forward_source_drop_status": nhi_forward_source_drop.get("status", "unknown"),
        "nhi_forward_source_drop_planned_files": nhi_forward_source_drop_summary.get("planned_source_file_count", 0),
        "nhi_forward_source_drop_dirs": nhi_forward_source_drop_summary.get("source_dir_count", 0),
        "nhi_forward_source_drop_existing_files": nhi_forward_source_drop_summary.get("existing_source_file_count", 0),
        "nhi_forward_source_drop_missing_files": nhi_forward_source_drop_summary.get("missing_source_file_count", 0),
        "nhi_forward_source_template_pack_status": nhi_forward_source_template_pack.get("status", "unknown"),
        "nhi_forward_source_template_pack_templates": nhi_forward_source_template_pack_summary.get("source_class_template_count", 0),
        "nhi_forward_source_template_pack_target_files": nhi_forward_source_template_pack_summary.get("target_source_file_count", 0),
        "nhi_forward_raw_csv_extraction_status": nhi_forward_raw_csv_extraction.get("status", "unknown"),
        "nhi_forward_raw_csv_extraction_files": nhi_forward_raw_csv_extraction_summary.get("raw_csv_found", 0),
        "nhi_forward_raw_csv_extraction_rows": nhi_forward_raw_csv_extraction_summary.get("extracted_rows", 0),
        "nhi_forward_raw_csv_extraction_errors": nhi_forward_raw_csv_extraction_summary.get("error_count", 0),
        "nhi_forward_source_import_status": nhi_forward_source_import.get("status", "unknown"),
        "nhi_forward_source_import_rows": nhi_forward_source_import_summary.get("source_value_rows", 0),
        "nhi_forward_source_import_imported_rows": nhi_forward_source_import_summary.get("imported_rows", 0),
        "nhi_forward_source_import_errors": nhi_forward_source_import_summary.get("error_count", 0),
        "nhi_coupon_result_status": nhi_results_summary.get("status", "unknown"),
        "nhi_coupon_result_rows": nhi_results_summary.get("rows", 0),
        "nhi_long_source_values_status": nhi_long_source_values.get("status", "unknown"),
        "nhi_long_source_values_rows": nhi_long_source_values_summary.get("source_value_rows", 0),
        "nhi_long_source_values_filled_rows": nhi_long_source_values_summary.get("filled_value_rows", 0),
        "nhi_long_source_values_import_ready_rows": nhi_long_source_values_summary.get("import_ready_rows", 0),
        "nhi_long_source_drop_status": nhi_long_source_drop.get("status", "unknown"),
        "nhi_long_source_drop_planned_files": nhi_long_source_drop_summary.get("planned_source_file_count", 0),
        "nhi_long_source_drop_dirs": nhi_long_source_drop_summary.get("source_dir_count", 0),
        "nhi_long_source_drop_existing_files": nhi_long_source_drop_summary.get("existing_source_file_count", 0),
        "nhi_long_source_drop_missing_files": nhi_long_source_drop_summary.get("missing_source_file_count", 0),
        "nhi_long_source_template_pack_status": nhi_long_source_template_pack.get("status", "unknown"),
        "nhi_long_source_template_pack_templates": nhi_long_source_template_pack_summary.get("source_class_template_count", 0),
        "nhi_long_source_template_pack_target_files": nhi_long_source_template_pack_summary.get("target_source_file_count", 0),
        "nhi_long_raw_csv_extraction_status": nhi_long_raw_csv_extraction.get("status", "unknown"),
        "nhi_long_raw_csv_extraction_files": nhi_long_raw_csv_extraction_summary.get("raw_csv_found", 0),
        "nhi_long_raw_csv_extraction_rows": nhi_long_raw_csv_extraction_summary.get("extracted_rows", 0),
        "nhi_long_raw_csv_extraction_errors": nhi_long_raw_csv_extraction_summary.get("error_count", 0),
        "nhi_long_source_import_status": nhi_long_source_import.get("status", "unknown"),
        "nhi_long_source_import_rows": nhi_long_source_import_summary.get("source_value_rows", 0),
        "nhi_long_source_import_imported_rows": nhi_long_source_import_summary.get("imported_rows", 0),
        "nhi_long_source_import_errors": nhi_long_source_import_summary.get("error_count", 0),
        "nhi_long_result_status": nhi_long_results_summary.get("status", "unknown"),
        "nhi_long_result_rows": nhi_long_results_summary.get("rows", 0),
        "zrc_readiness": zrc_readiness.get("readiness", "unknown"),
        "zrc_suitable": bool(zrc_readiness.get("suitable")),
        "zrc_sentinel_status": zrc_sentinel.get("status", "unknown"),
        "zrc_sentinel_rows": zrc_sentinel.get("rows", 0),
        "zrc_next_status": zrc_next.get("status", "unknown"),
        "zrc_next_recommended_rows": len(zrc_next.get("recommended_rows", [])),
        "zrc_phase_a_source_values_status": zrc_phase_a_source_values.get("status", "unknown"),
        "zrc_phase_a_source_values_rows": zrc_phase_a_source_values_summary.get("source_value_rows", 0),
        "zrc_phase_a_source_values_filled_rows": zrc_phase_a_source_values_summary.get("filled_value_rows", 0),
        "zrc_phase_a_source_values_import_ready_rows": zrc_phase_a_source_values_summary.get("import_ready_rows", 0),
        "zrc_phase_a_source_drop_status": zrc_phase_a_source_drop.get("status", "unknown"),
        "zrc_phase_a_source_drop_planned_files": zrc_phase_a_source_drop_summary.get("planned_source_file_count", 0),
        "zrc_phase_a_source_drop_dirs": zrc_phase_a_source_drop_summary.get("source_dir_count", 0),
        "zrc_phase_a_source_drop_existing_files": zrc_phase_a_source_drop_summary.get("existing_source_file_count", 0),
        "zrc_phase_a_source_drop_missing_files": zrc_phase_a_source_drop_summary.get("missing_source_file_count", 0),
        "zrc_phase_a_source_template_pack_status": zrc_phase_a_source_template_pack.get("status", "unknown"),
        "zrc_phase_a_source_template_pack_templates": zrc_phase_a_source_template_pack_summary.get("source_class_template_count", 0),
        "zrc_phase_a_source_template_pack_target_files": zrc_phase_a_source_template_pack_summary.get("target_source_file_count", 0),
        "zrc_phase_a_vendor_bundle_entry_sheet_status": zrc_phase_a_vendor_bundle_entry_sheet.get("status", "unknown"),
        "zrc_phase_a_vendor_bundle_entry_sheet_bundles": zrc_phase_a_vendor_bundle_entry_sheet_summary.get("bundle_rows", 0),
        "zrc_phase_a_vendor_bundle_entry_sheet_ready_rows": zrc_phase_a_vendor_bundle_entry_sheet_summary.get("ready_to_apply_rows", 0),
        "zrc_phase_a_vendor_bundle_entry_sheet_blocked_rows": zrc_phase_a_vendor_bundle_entry_sheet_summary.get("blocked_rows", 0),
        "zrc_phase_a_vendor_bundle_entry_apply_status": zrc_phase_a_vendor_bundle_entry_apply.get("status", "unknown"),
        "zrc_phase_a_vendor_bundle_entry_apply_rows": zrc_phase_a_vendor_bundle_entry_apply_summary.get("apply_rows", 0),
        "zrc_phase_a_vendor_bundle_entry_apply_bundles": zrc_phase_a_vendor_bundle_entry_apply_summary.get("applied_bundles", 0),
        "zrc_phase_a_vendor_bundle_entry_apply_source_rows": zrc_phase_a_vendor_bundle_entry_apply_summary.get("applied_source_value_rows", 0),
        "zrc_phase_a_vendor_bundle_entry_apply_errors": zrc_phase_a_vendor_bundle_entry_apply_summary.get("error_count", 0),
        "zrc_phase_a_raw_csv_extraction_status": zrc_phase_a_raw_csv_extraction.get("status", "unknown"),
        "zrc_phase_a_raw_csv_extraction_files": zrc_phase_a_raw_csv_extraction_summary.get("raw_csv_found", 0),
        "zrc_phase_a_raw_csv_extraction_rows": zrc_phase_a_raw_csv_extraction_summary.get("extracted_rows", 0),
        "zrc_phase_a_raw_csv_extraction_errors": zrc_phase_a_raw_csv_extraction_summary.get("error_count", 0),
        "zrc_phase_a_source_import_status": zrc_phase_a_source_import.get("status", "unknown"),
        "zrc_phase_a_source_import_rows": zrc_phase_a_source_import_summary.get("source_value_rows", 0),
        "zrc_phase_a_source_import_imported_rows": zrc_phase_a_source_import_summary.get("imported_rows", 0),
        "zrc_phase_a_source_import_errors": zrc_phase_a_source_import_summary.get("error_count", 0),
        "zrc_phase_a_service_status": zrc_service.get("status", "unknown"),
        "zrc_phase_a_service_runs": zrc_service.get("requested_matrix", {}).get("runs", 0),
        "zrc_phase_a_chain_status": zrc_chain.get("status", "unknown"),
        "zrc_phase_a_sample_label_count": zrc_chain.get("sample_label_count", 0),
        "zrc_phase_a_chain_rows": zrc_chain.get("chain_of_custody_row_count", 0),
        "zrc_phase_a_pending_transfer_rows": zrc_chain.get("pending_transfer_rows", 0),
        "zrc_phase_a_delivery_status": zrc_delivery.get("status", "unknown"),
        "zrc_phase_a_delivery_missing_files": len(zrc_delivery.get("missing_required_file_ids", [])),
        "zrc_phase_a_vendor_outreach_status": zrc_vendor.get("status", "unknown"),
        "zrc_phase_a_vendor_first_wave_count": len(zrc_vendor.get("first_wave", [])),
        "zrc_phase_a_rfq_status": zrc_rfq.get("status", "unknown"),
        "zrc_phase_a_rfq_outbox_status": zrc_rfq_outbox.get("status", "unknown"),
        "zrc_phase_a_rfq_outbox_ready_count": zrc_rfq_outbox.get("ready_to_send_count", 0),
        "zrc_phase_a_rfq_outbox_quote_count": zrc_rfq_outbox.get("quote_request_count", 0),
        "zrc_phase_a_quote_tracker_status": zrc_quote_tracker.get("status", "unknown"),
        "zrc_phase_a_rfq_send_confirmation_intake_status": zrc_rfq_send_confirmation_intake.get("status", "unknown"),
        "zrc_phase_a_rfq_send_confirmation_intake_files": zrc_rfq_send_confirmation_intake.get("row_count", 0),
        "zrc_phase_a_rfq_send_confirmation_intake_applied_rows": zrc_rfq_send_confirmation_intake.get("applied_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_intake_needs_review_rows": zrc_rfq_send_confirmation_intake.get("needs_review_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_intake_bundle_matched_rows": zrc_rfq_send_confirmation_intake.get("bundle_hash_matched_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_sheet_status": zrc_rfq_send_confirmation_entry_sheet.get("status", "unknown"),
        "zrc_phase_a_rfq_send_confirmation_entry_sheet_rows": zrc_send_confirmation_entry_sheet_summary.get("entry_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_sheet_source_files": zrc_send_confirmation_entry_sheet_summary.get("source_file_present_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_sheet_ready_rows": zrc_send_confirmation_entry_sheet_summary.get("ready_to_apply_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_sheet_blocked_rows": zrc_send_confirmation_entry_sheet_summary.get("blocked_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_apply_status": zrc_rfq_send_confirmation_entry_apply.get("status", "unknown"),
        "zrc_phase_a_rfq_send_confirmation_entry_apply_rows": zrc_send_confirmation_entry_apply_summary.get("apply_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_apply_applied_rows": zrc_send_confirmation_entry_apply_summary.get("applied_rows", 0),
        "zrc_phase_a_rfq_send_confirmation_entry_apply_blocked_rows": zrc_send_confirmation_entry_apply_summary.get("blocked_rows", 0),
        "zrc_phase_a_rfq_send_log_status": zrc_rfq_send_log.get("status", "unknown"),
        "zrc_phase_a_rfq_send_log_rows": zrc_rfq_send_log.get("row_count", 0),
        "zrc_phase_a_rfq_send_log_sent_rows": zrc_rfq_send_log.get("sent_rows", 0),
        "zrc_phase_a_rfq_send_log_valid_sent_rows": zrc_rfq_send_log.get("valid_sent_rows", 0),
        "zrc_phase_a_rfq_send_log_applied_dates": zrc_rfq_send_log.get("applied_tracker_contact_dates", 0),
        "zrc_phase_a_rfq_send_log_errors": zrc_rfq_send_log.get("error_count", 0),
        "zrc_phase_a_rfq_reply_intake_status": zrc_rfq_reply_intake.get("status", "unknown"),
        "zrc_phase_a_rfq_reply_intake_files": zrc_rfq_reply_intake.get("row_count", 0),
        "zrc_phase_a_rfq_reply_intake_applied_rows": zrc_rfq_reply_intake.get("applied_rows", 0),
        "zrc_phase_a_rfq_reply_intake_needs_review_rows": zrc_rfq_reply_intake.get("needs_manual_review_rows", 0),
        "zrc_phase_a_rfq_reply_intake_needs_verified_send_rows": zrc_rfq_reply_intake.get("needs_verified_send_rows", 0),
        "zrc_phase_a_rfq_reply_log_status": zrc_rfq_reply_log.get("status", "unknown"),
        "zrc_phase_a_rfq_reply_log_rows": zrc_rfq_reply_log.get("row_count", 0),
        "zrc_phase_a_rfq_reply_log_received_rows": zrc_rfq_reply_log.get("received_rows", 0),
        "zrc_phase_a_rfq_reply_log_valid_rows": zrc_rfq_reply_log.get("valid_reply_rows", 0),
        "zrc_phase_a_rfq_reply_log_applied_fields": zrc_rfq_reply_log.get("applied_tracker_field_updates", 0),
        "zrc_phase_a_rfq_reply_log_errors": zrc_rfq_reply_log.get("error_count", 0),
        "zrc_phase_a_contact_plan_status": zrc_contact_plan.get("status", "unknown"),
        "zrc_phase_a_contact_ready_count": zrc_contact_plan.get("status_counts", {}).get("ready_to_send", 0),
        "zrc_phase_a_contact_standby_count": zrc_contact_plan.get("status_counts", {}).get("standby_secondary_wave", 0),
        "zrc_phase_a_contact_row_count": zrc_contact_plan.get("row_count", 0),
        "zrc_phase_a_rfq_dispatch_manifest_status": zrc_dispatch_manifest.get("status", "unknown"),
        "zrc_phase_a_rfq_dispatch_manifest_rows": zrc_dispatch_manifest_summary.get("dispatch_rows", 0),
        "zrc_phase_a_rfq_dispatch_manifest_ready_rows": zrc_dispatch_manifest_summary.get("ready_for_manual_dispatch_rows", 0),
        "zrc_phase_a_rfq_dispatch_manifest_blocked_rows": zrc_dispatch_manifest_summary.get("blocked_rows", 0),
        "zrc_phase_a_rfq_dispatch_archive_status": zrc_dispatch_archive.get("status", "unknown"),
        "zrc_phase_a_rfq_dispatch_archive_files": zrc_dispatch_archive_summary.get("included_files", 0),
        "zrc_phase_a_rfq_dispatch_archive_missing_files": zrc_dispatch_archive_summary.get("missing_files", 0),
        "zrc_phase_a_rfq_dispatch_archive_hash_mismatches": zrc_dispatch_archive_summary.get("hash_mismatch_files", 0),
        "zrc_phase_a_rfq_dispatch_archive_sha256": zrc_dispatch_archive_summary.get("archive_sha256", ""),
        "zrc_phase_a_rfq_dispatch_archive_path": zrc_dispatch_archive.get("generated_artifacts", {}).get("archive", ""),
        "zrc_phase_a_rfq_reply_action_pack_status": zrc_reply_action_pack.get("status", "unknown"),
        "zrc_phase_a_rfq_reply_action_pack_rows": zrc_reply_action_summary.get("action_rows", 0),
        "zrc_phase_a_rfq_reply_action_pack_waiting_send_rows": zrc_reply_action_summary.get("waiting_for_send_rows", 0),
        "zrc_phase_a_rfq_reply_action_pack_awaiting_reply_rows": zrc_reply_action_summary.get("awaiting_reply_rows", 0),
        "zrc_phase_a_rfq_reply_action_pack_needs_source_rows": zrc_reply_action_summary.get("received_needs_source_file_rows", 0),
        "zrc_phase_a_rfq_reply_action_pack_ready_apply_rows": zrc_reply_action_summary.get("ready_for_reply_log_apply_rows", 0),
        "zrc_phase_a_rfq_send_cockpit_status": zrc_send_cockpit.get("status", "unknown"),
        "zrc_phase_a_rfq_send_cockpit_rows": zrc_send_cockpit_summary.get("vendor_rows", 0),
        "zrc_phase_a_rfq_send_cockpit_ready_rows": zrc_send_cockpit_summary.get("ready_to_use_rows", 0),
        "zrc_phase_a_rfq_send_cockpit_confirmations": zrc_send_cockpit_summary.get("confirmation_files_present", 0),
        "zrc_phase_a_rfq_send_cockpit_replies": zrc_send_cockpit_summary.get("reply_files_present", 0),
        "zrc_phase_a_rfq_send_cockpit_missing_email": zrc_send_cockpit_summary.get("missing_email_rows", 0),
        "zrc_phase_a_rfq_send_cockpit_missing_bundle": zrc_send_cockpit_summary.get("missing_bundle_rows", 0),
        "zrc_phase_a_rfq_send_cockpit_html": zrc_send_cockpit.get("generated_artifacts", {}).get("html", ""),
        "zrc_phase_a_quote_selection_status": zrc_quote_selection.get("status", "unknown"),
        "zrc_phase_a_quote_selection_sent_count": zrc_quote_selection.get("sent_count", 0),
        "zrc_phase_a_quote_selection_reply_count": zrc_quote_selection.get("reply_count", 0),
        "zrc_phase_a_quote_selection_source_backed_reply_count": zrc_quote_selection.get("source_backed_reply_count", 0),
        "zrc_phase_a_quote_selection_shortlist_count": zrc_quote_selection.get("shortlist_count", 0),
        "zrc_phase_a_execution_authorization_status": zrc_execution_authorization.get("status", "unknown"),
        "zrc_phase_a_execution_authorization_rows": zrc_execution_authorization.get("row_count", 0),
        "zrc_phase_a_execution_authorization_valid_rows": zrc_execution_authorization.get("valid_authorization_rows", 0),
        "zrc_phase_a_execution_authorization_errors": zrc_execution_authorization.get("error_count", 0),
        "zrc_phase_a_execution_release_status": zrc_execution_release.get("status", "unknown"),
        "zrc_phase_a_execution_release_ready": bool(zrc_execution_release.get("ready_for_execution_authorization")),
        "zrc_phase_a_execution_release_released": bool(zrc_execution_release.get("released_for_execution")),
        "zrc_phase_a_execution_release_blockers": zrc_execution_release.get("blocker_count", 0),
        "zrc_phase_a_execution_release_authorization_blockers": zrc_execution_release.get("authorization_blocker_count", 0),
        "zrc_phase_a_vendor_return_status": zrc_vendor_return.get("status", "unknown"),
        "zrc_phase_a_vendor_return_rows": zrc_vendor_return.get("phase_a_measurements", {}).get("row_count", 0),
        "zrc_phase_a_vendor_return_export_files": zrc_vendor_return.get("instrument_export_file_count", 0),
        "zrc_measurement_merge_status": zrc_merge.get("status", "unknown"),
        "zrc_measurement_merge_inserted": zrc_merge_stats.get("inserted", 0),
        "zrc_measurement_merge_updated": zrc_merge_stats.get("updated", 0),
        "zrc_measurement_merge_output_rows": zrc_merge_stats.get("total", 0),
        "zrc_run_completeness_status": zrc_completeness.get("status", "unknown"),
        "zrc_run_completeness_measured_known_rows": zrc_completeness.get("measured_known_rows", 0),
        "zrc_run_completeness_planned_rows": zrc_completeness.get("planned_rows", 0),
        "zrc_validation_result_status": zrc_result_summary.get("status", "unknown"),
        "zrc_validation_result_rows": zrc_result_summary.get("rows", 0),
        "hybrid_measurement_plan_status": hybrid.get("status", "unknown"),
        "hybrid_measurement_inhouse_rows": hybrid_routes.get("inhouse_ready", {}).get("row_count", 0),
        "hybrid_measurement_outsource_rows": hybrid_routes.get("outsourced_preferred", {}).get("row_count", 0),
        "hybrid_measurement_provenance_rows": hybrid_routes.get("supplier_or_build_record", {}).get("row_count", 0),
        "hybrid_measurement_total_rows": hybrid_summary.get("row_count", 0),
        "local_capture_pack_status": local_capture.get("status", "unknown"),
        "local_capture_task_count": local_capture_summary.get("task_count", 0),
        "local_capture_local_tasks": local_capture_summary.get("ready_to_collect_local_rows", 0),
        "local_capture_provenance_tasks": local_capture_summary.get("ready_to_record_provenance_rows", 0),
        "local_capture_outsource_tasks": local_capture_summary.get("outsourced_preferred_rows", 0),
        "source_file_manifest_status": source_manifest.get("status", "unknown"),
        "source_file_allowed_root_count": len(source_manifest.get("allowed_roots", [])),
        "source_file_expected_class_count": len(source_manifest.get("expected_source_classes", [])),
        "source_file_inventory_status": source_inventory.get("status", "unknown"),
        "source_file_inventory_file_count": source_inventory_summary.get("file_count", 0),
        "source_file_inventory_reference_count": source_inventory_summary.get("source_reference_count", 0),
        "source_file_inventory_capture_reference_count": source_inventory_summary.get("capture_template_reference_count", 0),
        "source_file_inventory_source_value_reference_count": source_inventory_summary.get("filled_source_value_reference_count", 0),
        "source_file_inventory_missing_reference_count": source_inventory_summary.get("missing_reference_count", 0),
        "source_file_inventory_unreferenced_file_count": source_inventory_summary.get("unreferenced_file_count", 0),
        "local_capture_preflight_status": local_preflight.get("status", "unknown"),
        "local_capture_preflight_ready": bool(local_preflight.get("preflight_ready")),
        "local_capture_preflight_filled_tasks": local_preflight.get("filled_task_count", 0),
        "local_capture_preflight_pending_tasks": local_preflight.get("pending_task_count", 0),
        "local_capture_preflight_errors": local_preflight_issue_counts.get("error", 0),
        "local_capture_preflight_warnings": local_preflight_issue_counts.get("warning", 0),
        "smoke_capture_tranche_status": smoke.get("status", "unknown"),
        "smoke_capture_task_count": smoke_summary.get("task_count", 0),
        "smoke_capture_local_or_record_tasks": smoke_summary.get("local_or_record_tasks", 0),
        "smoke_capture_outsource_tasks": smoke_summary.get("outsourced_preferred_tasks", 0),
        "smoke_execution_queue_status": smoke_queue.get("status", "unknown"),
        "smoke_execution_queue_rows": smoke_queue_summary.get("queue_row_count", 0),
        "smoke_execution_queue_h_a_rows": smoke_queue_summary.get("h_a_rows", 0),
        "smoke_execution_queue_zrc_rows": smoke_queue_summary.get("zrc_rows", 0),
        "smoke_execution_queue_awaiting_rows": smoke_queue_summary.get("awaiting_value_rows", 0),
        "smoke_execution_queue_source_ready_rows": smoke_queue_summary.get("source_ready_rows", 0),
        "smoke_entry_sheet_status": smoke_entry_sheet.get("status", "unknown"),
        "smoke_entry_sheet_rows": smoke_entry_sheet_summary.get("entry_rows", 0),
        "smoke_entry_sheet_ready_rows": smoke_entry_sheet_summary.get("ready_to_apply_rows", 0),
        "smoke_entry_sheet_filled_value_rows": smoke_entry_sheet_summary.get("filled_value_rows", 0),
        "smoke_source_drop_status": smoke_source_drop.get("status", "unknown"),
        "smoke_source_drop_planned_files": smoke_source_drop_summary.get("planned_source_file_count", 0),
        "smoke_source_drop_dirs": smoke_source_drop_summary.get("source_dir_count", 0),
        "smoke_source_drop_existing_files": smoke_source_drop_summary.get("existing_source_file_count", 0),
        "smoke_source_drop_missing_files": smoke_source_drop_summary.get("missing_source_file_count", 0),
        "smoke_source_values_sheet_status": smoke_source_values_sheet.get("status", "unknown"),
        "smoke_source_values_sheet_rows": smoke_source_values_sheet_summary.get("source_value_rows", 0),
        "smoke_source_values_sheet_starter_rows": smoke_source_values_sheet_summary.get("starter_batch_rows", 0),
        "smoke_source_values_sheet_filled_rows": smoke_source_values_sheet_summary.get("filled_value_rows", 0),
        "smoke_source_values_sheet_import_ready_rows": smoke_source_values_sheet_summary.get("import_ready_rows", 0),
        "smoke_starter_batch_readiness_status": smoke_starter_readiness.get("status", "unknown"),
        "smoke_starter_batch_rows": smoke_starter_readiness_summary.get("starter_rows", 0),
        "smoke_starter_batch_ready_rows": smoke_starter_readiness_summary.get("ready_for_import_rows", 0),
        "smoke_starter_batch_blocked_rows": smoke_starter_readiness_summary.get("blocked_rows", 0),
        "smoke_starter_execution_pack_status": smoke_starter_execution_pack.get("status", "unknown"),
        "smoke_starter_execution_pack_rows": smoke_starter_execution_pack_summary.get("starter_rows", 0),
        "smoke_starter_execution_pack_dirs": smoke_starter_execution_pack_summary.get("source_dir_count", 0),
        "smoke_starter_execution_pack_existing_files": smoke_starter_execution_pack_summary.get("source_file_exists_rows", 0),
        "smoke_starter_template_pack_status": smoke_starter_template_pack.get("status", "unknown"),
        "smoke_starter_template_pack_rows": smoke_starter_template_pack_summary.get("starter_rows", 0),
        "smoke_starter_template_pack_templates": smoke_starter_template_pack_summary.get("source_class_template_count", 0),
        "smoke_raw_csv_extraction_status": smoke_raw_csv_extraction.get("status", "unknown"),
        "smoke_raw_csv_extraction_files": smoke_raw_csv_extraction_summary.get("raw_csv_found", 0),
        "smoke_raw_csv_extraction_rows": smoke_raw_csv_extraction_summary.get("extracted_rows", 0),
        "smoke_raw_csv_extraction_errors": smoke_raw_csv_extraction_summary.get("error_count", 0),
        "smoke_unstructured_intake_status": smoke_unstructured_intake.get("status", "unknown"),
        "smoke_unstructured_intake_rows": smoke_unstructured_intake_summary.get("unstructured_plan_rows", 0),
        "smoke_unstructured_intake_ready": smoke_unstructured_intake_summary.get("ready_for_value_extraction", 0),
        "smoke_unstructured_intake_missing": smoke_unstructured_intake_summary.get("missing_source_files", 0),
        "smoke_unstructured_intake_invalid": smoke_unstructured_intake_summary.get("invalid_source_files", 0),
        "smoke_unstructured_review_values_status": smoke_unstructured_review_values.get("status", "unknown"),
        "smoke_unstructured_review_values_rows": smoke_unstructured_review_values_summary.get("review_rows", 0),
        "smoke_unstructured_review_values_ready_sources": smoke_unstructured_review_values_summary.get("ready_source_rows", 0),
        "smoke_unstructured_review_values_filled_rows": smoke_unstructured_review_values_summary.get("filled_value_rows", 0),
        "smoke_unstructured_review_values_import_ready_rows": smoke_unstructured_review_values_summary.get("import_ready_rows", 0),
        "smoke_unstructured_review_values_invalid_sources": smoke_unstructured_review_values_summary.get("invalid_source_rows", 0),
        "smoke_source_value_import_status": smoke_source_value_import.get("status", "unknown"),
        "smoke_source_value_import_files": smoke_source_value_import_summary.get("source_value_files", 0),
        "smoke_source_value_import_rows": smoke_source_value_import_summary.get("source_value_rows", 0),
        "smoke_source_value_import_imported_rows": smoke_source_value_import_summary.get("imported_rows", 0),
        "smoke_source_value_import_errors": smoke_source_value_import_summary.get("error_count", 0),
        "smoke_entry_apply_status": smoke_entry_apply.get("status", "unknown"),
        "smoke_entry_apply_applied_values": smoke_entry_apply_summary.get("applied_values", 0),
        "smoke_entry_apply_errors": smoke_entry_apply_summary.get("error_count", 0),
        "smoke_capture_preflight_status": smoke_preflight.get("status", "unknown"),
        "smoke_capture_preflight_ready": bool(smoke_preflight.get("preflight_ready")),
        "smoke_capture_preflight_filled_tasks": smoke_preflight.get("filled_task_count", 0),
        "smoke_capture_preflight_pending_tasks": smoke_preflight.get("pending_task_count", 0),
        "smoke_capture_preflight_errors": smoke_preflight_issue_counts.get("error", 0),
        "smoke_capture_preflight_warnings": smoke_preflight_issue_counts.get("warning", 0),
        "smoke_rehearsal_status": smoke_rehearsal.get("status", "unknown"),
        "smoke_rehearsal_preflight_status": smoke_rehearsal.get("preflight_status", "unknown"),
        "smoke_rehearsal_preflight_ready": bool(smoke_rehearsal.get("preflight_ready")),
        "smoke_rehearsal_filled_tasks": smoke_rehearsal.get("filled_task_count", 0),
        "smoke_rehearsal_pending_tasks": smoke_rehearsal.get("pending_task_count", 0),
        "smoke_rehearsal_errors": smoke_rehearsal_issue_counts.get("error", 0),
        "smoke_rehearsal_warnings": smoke_rehearsal_issue_counts.get("warning", 0),
        "smoke_rehearsal_h_a_qc_status": smoke_rehearsal.get("h_a_qc_status", "-"),
        "smoke_rehearsal_zrc_validation_status": smoke_rehearsal.get("zrc_validation_status", "-"),
        "next_action_boundary": (
            "No suitability claim is allowed until real, non-placeholder, non-synthetic "
            "measured rows pass the required gates."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Local Iteration State",
        "",
        "This report records one local dry-lab discovery iteration. It is not a material suitability claim.",
        "",
        f"**Run timestamp:** `{result['run_timestamp_utc']}`",
        f"**Iteration status:** `{summary['status']}`",
        f"**Top candidate:** `{summary['top_candidate'] or '-'}`",
        f"**Top priority:** `{summary['top_priority'] or '-'}`",
        f"**Mission state:** `{summary['mission_state']}`",
        f"**Claim ready:** `{str(summary['claim_ready']).lower()}`",
        f"**Claim status:** `{summary['claim_status']}`",
        f"**Portfolio bypass audit:** `{summary['portfolio_bypass_status']}`; non_H-A_claim_ready={summary['portfolio_bypass_non_h_a_claim_ready_rows']}; top_non_H-A={summary['portfolio_bypass_top_non_h_a_candidate'] or '-'}",
        "",
        "## Current Gate State",
        "",
        "| Area | Value |",
        "| --- | --- |",
        f"| H-A status | `{summary['h_a_status']}` |",
        f"| H-A measured rows | {summary['h_a_measured_rows']} / {summary['h_a_total_rows']} |",
        f"| H-A placeholder rows | {summary['h_a_placeholder_rows']} |",
        f"| H-A synthetic rows | {summary['h_a_synthetic_rows']} |",
        f"| H-A QC | `{summary['h_a_qc_status']}`; errors={summary['h_a_qc_errors']}; warnings={summary['h_a_qc_warnings']} |",
        f"| H-A source values sheet | `{summary['h_a_source_values_sheet_status']}`; rows={summary['h_a_source_values_sheet_rows']}; filled={summary['h_a_source_values_sheet_filled_rows']}; source-files={summary['h_a_source_values_sheet_source_file_exists_rows']}; import-ready={summary['h_a_source_values_sheet_import_ready_rows']} |",
        f"| H-A source drop plan | `{summary['h_a_source_drop_status']}`; planned files={summary['h_a_source_drop_planned_files']}; dirs={summary['h_a_source_drop_dirs']}; existing files={summary['h_a_source_drop_existing_files']}; missing files={summary['h_a_source_drop_missing_files']} |",
        f"| H-A source unlock pack | `{summary['h_a_source_unlock_pack_status']}`; source rows={summary['h_a_source_unlock_pack_source_rows']}; bundles={summary['h_a_source_unlock_pack_bundles']}; existing files={summary['h_a_source_unlock_pack_existing_files']}; missing files={summary['h_a_source_unlock_pack_missing_files']} |",
        f"| H-A bundle entry sheet | `{summary['h_a_bundle_entry_sheet_status']}`; bundles={summary['h_a_bundle_entry_sheet_rows']}; filled={summary['h_a_bundle_entry_sheet_filled_rows']}; ready-to-apply={summary['h_a_bundle_entry_sheet_ready_rows']}; existing files={summary['h_a_bundle_entry_sheet_existing_files']} |",
        f"| H-A vendor bundle entry sheet | `{summary['h_a_vendor_bundle_entry_sheet_status']}`; bundles={summary['h_a_vendor_bundle_entry_sheet_rows']}; ready={summary['h_a_vendor_bundle_entry_sheet_ready_rows']}; blocked={summary['h_a_vendor_bundle_entry_sheet_blocked_rows']}; existing files={summary['h_a_vendor_bundle_entry_sheet_existing_files']} |",
        f"| H-A bundle entry apply | `{summary['h_a_bundle_entry_apply_status']}`; bundles={summary['h_a_bundle_entry_apply_bundles']}; source rows={summary['h_a_bundle_entry_apply_source_rows']}; errors={summary['h_a_bundle_entry_apply_errors']} |",
        f"| H-A vendor bundle entry return apply | `{summary['h_a_vendor_bundle_entry_apply_status']}`; sheet-exists={str(summary['h_a_vendor_bundle_entry_apply_sheet_exists']).lower()}; bundles={summary['h_a_vendor_bundle_entry_apply_bundles']}; source rows={summary['h_a_vendor_bundle_entry_apply_source_rows']}; errors={summary['h_a_vendor_bundle_entry_apply_errors']} |",
        f"| H-A source file templates | `{summary['h_a_source_template_pack_status']}`; templates={summary['h_a_source_template_pack_templates']}; target files={summary['h_a_source_template_pack_target_files']} |",
        f"| H-A raw CSV extraction | `{summary['h_a_raw_csv_extraction_status']}`; files={summary['h_a_raw_csv_extraction_files']}; rows={summary['h_a_raw_csv_extraction_rows']}; errors={summary['h_a_raw_csv_extraction_errors']} |",
        f"| H-A source value import | `{summary['h_a_source_value_import_status']}`; files={summary['h_a_source_value_import_files']}; rows={summary['h_a_source_value_import_rows']}; imported={summary['h_a_source_value_import_imported_rows']}; errors={summary['h_a_source_value_import_errors']} |",
        f"| Raw merge | applied={summary['h_a_merge_applied_values']}; unresolved={summary['h_a_merge_unresolved_targets']} |",
        f"| Bench sheet | tasks={summary['h_a_bench_tasks']}; blank raw entries={summary['h_a_blank_raw_entries_to_fill']} |",
        f"| H-A service request | `{summary['h_a_service_request_status']}`; raw entries={summary['h_a_service_request_raw_entries']} |",
        f"| Hybrid measurement routing | `{summary['hybrid_measurement_plan_status']}`; local={summary['hybrid_measurement_inhouse_rows']}; outsource-preferred={summary['hybrid_measurement_outsource_rows']}; provenance={summary['hybrid_measurement_provenance_rows']}; total={summary['hybrid_measurement_total_rows']} |",
        f"| Local capture pack | `{summary['local_capture_pack_status']}`; tasks={summary['local_capture_task_count']}; local={summary['local_capture_local_tasks']}; outsource={summary['local_capture_outsource_tasks']}; provenance={summary['local_capture_provenance_tasks']} |",
        f"| Source-file manifest | `{summary['source_file_manifest_status']}`; allowed roots={summary['source_file_allowed_root_count']}; source classes={summary['source_file_expected_class_count']} |",
        f"| Source-file inventory | `{summary['source_file_inventory_status']}`; files={summary['source_file_inventory_file_count']}; refs={summary['source_file_inventory_reference_count']}; capture refs={summary['source_file_inventory_capture_reference_count']}; filled source-value refs={summary['source_file_inventory_source_value_reference_count']}; missing refs={summary['source_file_inventory_missing_reference_count']}; unreferenced={summary['source_file_inventory_unreferenced_file_count']} |",
        f"| Local capture preflight | `{summary['local_capture_preflight_status']}`; ready={str(summary['local_capture_preflight_ready']).lower()}; filled={summary['local_capture_preflight_filled_tasks']}; pending={summary['local_capture_preflight_pending_tasks']}; errors={summary['local_capture_preflight_errors']}; warnings={summary['local_capture_preflight_warnings']} |",
        f"| Smoke capture tranche | `{summary['smoke_capture_tranche_status']}`; tasks={summary['smoke_capture_task_count']}; local_or_record={summary['smoke_capture_local_or_record_tasks']}; outsource={summary['smoke_capture_outsource_tasks']} |",
        f"| Smoke execution queue | `{summary['smoke_execution_queue_status']}`; rows={summary['smoke_execution_queue_rows']}; H-A={summary['smoke_execution_queue_h_a_rows']}; ZRC={summary['smoke_execution_queue_zrc_rows']}; awaiting={summary['smoke_execution_queue_awaiting_rows']}; source-ready={summary['smoke_execution_queue_source_ready_rows']} |",
        f"| Smoke entry sheet | `{summary['smoke_entry_sheet_status']}`; rows={summary['smoke_entry_sheet_rows']}; filled={summary['smoke_entry_sheet_filled_value_rows']}; ready-to-apply={summary['smoke_entry_sheet_ready_rows']} |",
        f"| Smoke source drop plan | `{summary['smoke_source_drop_status']}`; planned files={summary['smoke_source_drop_planned_files']}; dirs={summary['smoke_source_drop_dirs']}; existing files={summary['smoke_source_drop_existing_files']}; missing files={summary['smoke_source_drop_missing_files']} |",
        f"| Smoke source values sheet | `{summary['smoke_source_values_sheet_status']}`; rows={summary['smoke_source_values_sheet_rows']}; starter={summary['smoke_source_values_sheet_starter_rows']}; filled={summary['smoke_source_values_sheet_filled_rows']}; import-ready={summary['smoke_source_values_sheet_import_ready_rows']} |",
        f"| Smoke starter batch readiness | `{summary['smoke_starter_batch_readiness_status']}`; rows={summary['smoke_starter_batch_rows']}; ready={summary['smoke_starter_batch_ready_rows']}; blocked={summary['smoke_starter_batch_blocked_rows']} |",
        f"| Smoke starter execution pack | `{summary['smoke_starter_execution_pack_status']}`; rows={summary['smoke_starter_execution_pack_rows']}; dirs={summary['smoke_starter_execution_pack_dirs']}; existing files={summary['smoke_starter_execution_pack_existing_files']} |",
        f"| Smoke starter raw-file templates | `{summary['smoke_starter_template_pack_status']}`; rows={summary['smoke_starter_template_pack_rows']}; templates={summary['smoke_starter_template_pack_templates']} |",
        f"| Smoke raw CSV extraction | `{summary['smoke_raw_csv_extraction_status']}`; files={summary['smoke_raw_csv_extraction_files']}; rows={summary['smoke_raw_csv_extraction_rows']}; errors={summary['smoke_raw_csv_extraction_errors']} |",
        f"| Smoke unstructured source intake | `{summary['smoke_unstructured_intake_status']}`; rows={summary['smoke_unstructured_intake_rows']}; ready={summary['smoke_unstructured_intake_ready']}; missing={summary['smoke_unstructured_intake_missing']}; invalid={summary['smoke_unstructured_intake_invalid']} |",
        f"| Smoke unstructured review values | `{summary['smoke_unstructured_review_values_status']}`; rows={summary['smoke_unstructured_review_values_rows']}; ready_sources={summary['smoke_unstructured_review_values_ready_sources']}; filled={summary['smoke_unstructured_review_values_filled_rows']}; import-ready={summary['smoke_unstructured_review_values_import_ready_rows']}; invalid_sources={summary['smoke_unstructured_review_values_invalid_sources']} |",
        f"| Smoke source value import | `{summary['smoke_source_value_import_status']}`; files={summary['smoke_source_value_import_files']}; rows={summary['smoke_source_value_import_rows']}; imported={summary['smoke_source_value_import_imported_rows']}; errors={summary['smoke_source_value_import_errors']} |",
        f"| Smoke entry apply | `{summary['smoke_entry_apply_status']}`; applied={summary['smoke_entry_apply_applied_values']}; errors={summary['smoke_entry_apply_errors']} |",
        f"| Smoke capture preflight | `{summary['smoke_capture_preflight_status']}`; ready={str(summary['smoke_capture_preflight_ready']).lower()}; filled={summary['smoke_capture_preflight_filled_tasks']}; pending={summary['smoke_capture_preflight_pending_tasks']}; errors={summary['smoke_capture_preflight_errors']}; warnings={summary['smoke_capture_preflight_warnings']} |",
        f"| Smoke rehearsal | `{summary['smoke_rehearsal_status']}`; preflight={summary['smoke_rehearsal_preflight_status']}; ready={str(summary['smoke_rehearsal_preflight_ready']).lower()}; filled={summary['smoke_rehearsal_filled_tasks']}; pending={summary['smoke_rehearsal_pending_tasks']}; H-A_QC={summary['smoke_rehearsal_h_a_qc_status']}; ZRC_validation={summary['smoke_rehearsal_zrc_validation_status']} |",
        f"| H-A sample handoff | `{summary['h_a_chain_of_custody_status']}`; labels={summary['h_a_sample_label_count']}; custody rows={summary['h_a_chain_of_custody_rows']}; pending transfers={summary['h_a_pending_transfer_rows']} |",
        f"| H-A sample submission | `{summary['h_a_sample_submission_status']}`; shipping={summary['h_a_sample_submission_shipping_status']} |",
        f"| H-A split-scope plan | `{summary['h_a_split_scope_status']}`; pairs={summary['h_a_split_scope_pair_count']}; preferred={summary['h_a_split_scope_preferred_count']} |",
        f"| H-A delivery package | `{summary['h_a_delivery_package_status']}`; missing files={summary['h_a_delivery_package_missing_files']} |",
        f"| H-A vendor outreach | `{summary['h_a_vendor_outreach_status']}`; first-wave contacts={summary['h_a_vendor_first_wave_count']} |",
        f"| H-A RFQ packet | `{summary['h_a_rfq_packet_status']}` |",
        f"| H-A RFQ outbox | `{summary['h_a_rfq_outbox_status']}`; ready={summary['h_a_rfq_outbox_ready_count']} / {summary['h_a_rfq_outbox_quote_count']} |",
        f"| H-A quote tracker | `{summary['h_a_quote_tracker_status']}` |",
        f"| H-A RFQ send confirmation intake | `{summary['h_a_rfq_send_confirmation_intake_status']}`; files={summary['h_a_rfq_send_confirmation_intake_files']}; applied={summary['h_a_rfq_send_confirmation_intake_applied']}; needs-review={summary['h_a_rfq_send_confirmation_intake_needs_review']}; bundle-matched={summary['h_a_rfq_send_confirmation_intake_bundle_matched']} |",
        f"| H-A RFQ send confirmation entry sheet | `{summary['h_a_rfq_send_confirmation_entry_sheet_status']}`; rows={summary['h_a_rfq_send_confirmation_entry_sheet_rows']}; source-files={summary['h_a_rfq_send_confirmation_entry_sheet_source_files']}; ready={summary['h_a_rfq_send_confirmation_entry_sheet_ready']}; blocked={summary['h_a_rfq_send_confirmation_entry_sheet_blocked']} |",
        f"| H-A RFQ send confirmation entry apply | `{summary['h_a_rfq_send_confirmation_entry_apply_status']}`; apply rows={summary['h_a_rfq_send_confirmation_entry_apply_apply_rows']}; applied={summary['h_a_rfq_send_confirmation_entry_apply_applied']}; blocked={summary['h_a_rfq_send_confirmation_entry_apply_blocked']} |",
        f"| H-A RFQ send log | `{summary['h_a_rfq_send_log_status']}`; rows={summary['h_a_rfq_send_log_rows']}; sent={summary['h_a_rfq_send_log_sent_rows']}; valid={summary['h_a_rfq_send_log_valid_sent_rows']}; applied dates={summary['h_a_rfq_send_log_applied_dates']}; errors={summary['h_a_rfq_send_log_errors']} |",
        f"| H-A RFQ reply intake | `{summary['h_a_rfq_reply_intake_status']}`; files={summary['h_a_rfq_reply_intake_files']}; applied={summary['h_a_rfq_reply_intake_applied']}; needs-review={summary['h_a_rfq_reply_intake_needs_review']}; needs-verified-send={summary['h_a_rfq_reply_intake_needs_verified_send']} |",
        f"| H-A RFQ reply log | `{summary['h_a_rfq_reply_log_status']}`; rows={summary['h_a_rfq_reply_log_rows']}; received={summary['h_a_rfq_reply_log_received_rows']}; valid={summary['h_a_rfq_reply_log_valid_rows']}; applied fields={summary['h_a_rfq_reply_log_applied_fields']}; errors={summary['h_a_rfq_reply_log_errors']} |",
        f"| H-A vendor contact plan | `{summary['h_a_vendor_contact_plan_status']}`; ready first-wave={summary['h_a_vendor_contact_ready_count']}; standby second-wave={summary['h_a_vendor_contact_standby_count']}; total={summary['h_a_vendor_contact_row_count']} |",
        f"| H-A vendor contact source audit | `{summary['h_a_vendor_contact_source_audit_status']}`; rows={summary['h_a_vendor_contact_source_audit_rows']}; pass={summary['h_a_vendor_contact_source_audit_pass_rows']}; fail={summary['h_a_vendor_contact_source_audit_fail_rows']}; stale={summary['h_a_vendor_contact_source_audit_stale_rows']} |",
        f"| H-A RFQ EML drafts | `{summary['h_a_rfq_eml_drafts_status']}`; rows={summary['h_a_rfq_eml_drafts_rows']}; ready={summary['h_a_rfq_eml_drafts_ready_rows']}; missing-to={summary['h_a_rfq_eml_drafts_missing_to_rows']}; missing-bundle={summary['h_a_rfq_eml_drafts_missing_bundle_rows']} |",
        f"| H-A RFQ EML integrity audit | `{summary['h_a_rfq_eml_integrity_status']}`; rows={summary['h_a_rfq_eml_integrity_rows']}; pass={summary['h_a_rfq_eml_integrity_pass_rows']}; fail={summary['h_a_rfq_eml_integrity_fail_rows']}; attachment-mismatch={summary['h_a_rfq_eml_integrity_attachment_mismatch_rows']} |",
        f"| H-A RFQ send action pack | `{summary['h_a_rfq_send_action_pack_status']}`; rows={summary['h_a_rfq_send_action_rows']}; ready={summary['h_a_rfq_send_action_ready_rows']}; verified={summary['h_a_rfq_send_action_verified_rows']}; needs-confirmation={summary['h_a_rfq_send_action_needs_confirmation_rows']} |",
        f"| H-A RFQ dispatch manifest | `{summary['h_a_rfq_dispatch_manifest_status']}`; rows={summary['h_a_rfq_dispatch_manifest_rows']}; ready={summary['h_a_rfq_dispatch_manifest_ready_rows']}; blocked={summary['h_a_rfq_dispatch_manifest_blocked_rows']}; bundle-matches={summary['h_a_rfq_dispatch_manifest_bundle_match_rows']} |",
        f"| H-A RFQ reply action pack | `{summary['h_a_rfq_reply_action_pack_status']}`; rows={summary['h_a_rfq_reply_action_rows']}; waiting-send={summary['h_a_rfq_reply_action_waiting_for_send']}; awaiting-reply={summary['h_a_rfq_reply_action_awaiting_reply']}; needs-source={summary['h_a_rfq_reply_action_needs_source_file']}; ready-apply={summary['h_a_rfq_reply_action_ready_to_apply']} |",
        f"| H-A RFQ send cockpit | `{summary['h_a_rfq_send_cockpit_status']}`; rows={summary['h_a_rfq_send_cockpit_rows']}; ready={summary['h_a_rfq_send_cockpit_ready_rows']}; confirmations={summary['h_a_rfq_send_cockpit_confirmations']}; replies={summary['h_a_rfq_send_cockpit_replies']}; missing-eml={summary['h_a_rfq_send_cockpit_missing_eml']}; missing-bundle={summary['h_a_rfq_send_cockpit_missing_bundle']}; html=`{summary['h_a_rfq_send_cockpit_html']}` |",
        f"| H-A RFQ dispatch archive | `{summary['h_a_rfq_dispatch_archive_status']}`; files={summary['h_a_rfq_dispatch_archive_files']}; missing={summary['h_a_rfq_dispatch_archive_missing_files']}; hash-mismatches={summary['h_a_rfq_dispatch_archive_hash_mismatches']}; archive=`{summary['h_a_rfq_dispatch_archive_path']}`; sha256=`{summary['h_a_rfq_dispatch_archive_sha256']}` |",
        f"| First-wave RFQ dispatch cockpit | `{summary['first_wave_rfq_dispatch_cockpit_status']}`; rows={summary['first_wave_rfq_dispatch_cockpit_rows']}; ready={summary['first_wave_rfq_dispatch_cockpit_ready_rows']}; confirmations={summary['first_wave_rfq_dispatch_cockpit_confirmations']}; replies={summary['first_wave_rfq_dispatch_cockpit_replies']}; missing-messages={summary['first_wave_rfq_dispatch_cockpit_missing_messages']}; missing-bundles={summary['first_wave_rfq_dispatch_cockpit_missing_bundles']}; html=`{summary['first_wave_rfq_dispatch_cockpit_html']}` |",
        f"| First-wave post-dispatch processing | `{summary['first_wave_post_dispatch_status']}`; failed commands={summary['first_wave_post_dispatch_failed_commands']}; confirmations={summary['first_wave_post_dispatch_confirmations']}; replies={summary['first_wave_post_dispatch_replies']} |",
        f"| Second-wave candidate queue | `{summary['second_wave_candidate_queue_status']}`; rows={summary['second_wave_candidate_queue_rows']}; ready-scope-lock={summary['second_wave_candidate_queue_ready_scope_lock_rows']}; watch={summary['second_wave_candidate_queue_watch_rows']}; hold={summary['second_wave_candidate_queue_hold_rows']} |",
        f"| Second-wave scope-lock pack | `{summary['second_wave_scope_lock_pack_status']}`; ready candidates={summary['second_wave_scope_lock_pack_ready_candidates']}; tasks={summary['second_wave_scope_lock_pack_tasks']}; source classes={summary['second_wave_scope_lock_pack_source_classes']}; claim evidence created={str(summary['second_wave_scope_lock_pack_claim_evidence_created']).lower()} |",
        f"| H-A quote selection | `{summary['h_a_quote_selection_status']}`; sent={summary['h_a_quote_selection_sent_count']}; replies={summary['h_a_quote_selection_reply_count']}; source-backed replies={summary['h_a_quote_selection_source_backed_reply_count']}; shortlisted={summary['h_a_quote_selection_shortlist_count']} |",
        f"| H-A execution authorization log | `{summary['h_a_execution_authorization_status']}`; rows={summary['h_a_execution_authorization_rows']}; valid={summary['h_a_execution_authorization_valid_rows']}; errors={summary['h_a_execution_authorization_errors']} |",
        f"| H-A execution release audit | `{summary['h_a_execution_release_status']}`; ready={str(summary['h_a_execution_release_ready']).lower()}; released={str(summary['h_a_execution_release_released']).lower()}; blockers={summary['h_a_execution_release_blockers']}; authorization blockers={summary['h_a_execution_release_authorization_blockers']} |",
        f"| H-A vendor return intake | `{summary['h_a_vendor_return_status']}`; raw value rows={summary['h_a_vendor_return_raw_value_rows']}; bundle rows={summary['h_a_vendor_return_bundle_entry_rows']}; bundle apply rows={summary['h_a_vendor_return_bundle_entry_apply_rows']}; export files={summary['h_a_vendor_return_export_files']} |",
        f"| Forward H-B/H-C package | `{summary['forward_gate_status']}`; rows={summary['forward_gate_rows']} |",
        f"| Forward H-B/H-C source values | `{summary['nhi_forward_source_values_status']}`; rows={summary['nhi_forward_source_values_rows']}; filled={summary['nhi_forward_source_values_filled_rows']}; import-ready={summary['nhi_forward_source_values_import_ready_rows']} |",
        f"| Forward H-B/H-C source drop plan | `{summary['nhi_forward_source_drop_status']}`; planned files={summary['nhi_forward_source_drop_planned_files']}; dirs={summary['nhi_forward_source_drop_dirs']}; existing files={summary['nhi_forward_source_drop_existing_files']}; missing files={summary['nhi_forward_source_drop_missing_files']} |",
        f"| Forward H-B/H-C source file templates | `{summary['nhi_forward_source_template_pack_status']}`; templates={summary['nhi_forward_source_template_pack_templates']}; target files={summary['nhi_forward_source_template_pack_target_files']} |",
        f"| Forward H-B/H-C raw CSV extraction | `{summary['nhi_forward_raw_csv_extraction_status']}`; files={summary['nhi_forward_raw_csv_extraction_files']}; rows={summary['nhi_forward_raw_csv_extraction_rows']}; errors={summary['nhi_forward_raw_csv_extraction_errors']} |",
        f"| Forward H-B/H-C source import | `{summary['nhi_forward_source_import_status']}`; rows={summary['nhi_forward_source_import_rows']}; imported={summary['nhi_forward_source_import_imported_rows']}; errors={summary['nhi_forward_source_import_errors']} |",
        f"| NHI-PEDOT coupon results | `{summary['nhi_coupon_result_status']}`; rows={summary['nhi_coupon_result_rows']} |",
        f"| Long-duration source values | `{summary['nhi_long_source_values_status']}`; rows={summary['nhi_long_source_values_rows']}; filled={summary['nhi_long_source_values_filled_rows']}; import-ready={summary['nhi_long_source_values_import_ready_rows']} |",
        f"| Long-duration source drop plan | `{summary['nhi_long_source_drop_status']}`; planned files={summary['nhi_long_source_drop_planned_files']}; dirs={summary['nhi_long_source_drop_dirs']}; existing files={summary['nhi_long_source_drop_existing_files']}; missing files={summary['nhi_long_source_drop_missing_files']} |",
        f"| Long-duration source file templates | `{summary['nhi_long_source_template_pack_status']}`; templates={summary['nhi_long_source_template_pack_templates']}; target files={summary['nhi_long_source_template_pack_target_files']} |",
        f"| Long-duration raw CSV extraction | `{summary['nhi_long_raw_csv_extraction_status']}`; files={summary['nhi_long_raw_csv_extraction_files']}; rows={summary['nhi_long_raw_csv_extraction_rows']}; errors={summary['nhi_long_raw_csv_extraction_errors']} |",
        f"| Long-duration source import | `{summary['nhi_long_source_import_status']}`; rows={summary['nhi_long_source_import_rows']}; imported={summary['nhi_long_source_import_imported_rows']}; errors={summary['nhi_long_source_import_errors']} |",
        f"| NHI-PEDOT long results | `{summary['nhi_long_result_status']}`; rows={summary['nhi_long_result_rows']} |",
        f"| ZRC-ND readiness | `{summary['zrc_readiness']}`; suitable={str(summary['zrc_suitable']).lower()} |",
        f"| ZRC-ND Phase A sentinel | `{summary['zrc_sentinel_status']}`; rows={summary['zrc_sentinel_rows']} |",
        f"| ZRC-ND next measurements | `{summary['zrc_next_status']}`; recommended rows={summary['zrc_next_recommended_rows']} |",
        f"| ZRC-ND Phase A source values | `{summary['zrc_phase_a_source_values_status']}`; rows={summary['zrc_phase_a_source_values_rows']}; filled={summary['zrc_phase_a_source_values_filled_rows']}; import-ready={summary['zrc_phase_a_source_values_import_ready_rows']} |",
        f"| ZRC-ND Phase A source drop plan | `{summary['zrc_phase_a_source_drop_status']}`; planned files={summary['zrc_phase_a_source_drop_planned_files']}; dirs={summary['zrc_phase_a_source_drop_dirs']}; existing files={summary['zrc_phase_a_source_drop_existing_files']}; missing files={summary['zrc_phase_a_source_drop_missing_files']} |",
        f"| ZRC-ND Phase A source file templates | `{summary['zrc_phase_a_source_template_pack_status']}`; templates={summary['zrc_phase_a_source_template_pack_templates']}; target files={summary['zrc_phase_a_source_template_pack_target_files']} |",
        f"| ZRC-ND Phase A vendor bundle entry sheet | `{summary['zrc_phase_a_vendor_bundle_entry_sheet_status']}`; bundles={summary['zrc_phase_a_vendor_bundle_entry_sheet_bundles']}; ready={summary['zrc_phase_a_vendor_bundle_entry_sheet_ready_rows']}; blocked={summary['zrc_phase_a_vendor_bundle_entry_sheet_blocked_rows']} |",
        f"| ZRC-ND Phase A vendor bundle entry apply | `{summary['zrc_phase_a_vendor_bundle_entry_apply_status']}`; apply rows={summary['zrc_phase_a_vendor_bundle_entry_apply_rows']}; bundles={summary['zrc_phase_a_vendor_bundle_entry_apply_bundles']}; source rows={summary['zrc_phase_a_vendor_bundle_entry_apply_source_rows']}; errors={summary['zrc_phase_a_vendor_bundle_entry_apply_errors']} |",
        f"| ZRC-ND Phase A raw CSV extraction | `{summary['zrc_phase_a_raw_csv_extraction_status']}`; files={summary['zrc_phase_a_raw_csv_extraction_files']}; rows={summary['zrc_phase_a_raw_csv_extraction_rows']}; errors={summary['zrc_phase_a_raw_csv_extraction_errors']} |",
        f"| ZRC-ND Phase A source import | `{summary['zrc_phase_a_source_import_status']}`; rows={summary['zrc_phase_a_source_import_rows']}; imported={summary['zrc_phase_a_source_import_imported_rows']}; errors={summary['zrc_phase_a_source_import_errors']} |",
        f"| ZRC-ND Phase A service request | `{summary['zrc_phase_a_service_status']}`; runs={summary['zrc_phase_a_service_runs']} |",
        f"| ZRC-ND Phase A sample handoff | `{summary['zrc_phase_a_chain_status']}`; labels={summary['zrc_phase_a_sample_label_count']}; custody rows={summary['zrc_phase_a_chain_rows']}; pending transfers={summary['zrc_phase_a_pending_transfer_rows']} |",
        f"| ZRC-ND Phase A delivery package | `{summary['zrc_phase_a_delivery_status']}`; missing files={summary['zrc_phase_a_delivery_missing_files']} |",
        f"| ZRC-ND Phase A vendor outreach | `{summary['zrc_phase_a_vendor_outreach_status']}`; first-wave contacts={summary['zrc_phase_a_vendor_first_wave_count']} |",
        f"| ZRC-ND Phase A RFQ packet | `{summary['zrc_phase_a_rfq_status']}` |",
        f"| ZRC-ND Phase A RFQ outbox | `{summary['zrc_phase_a_rfq_outbox_status']}`; ready={summary['zrc_phase_a_rfq_outbox_ready_count']} / {summary['zrc_phase_a_rfq_outbox_quote_count']} |",
        f"| ZRC-ND Phase A quote tracker | `{summary['zrc_phase_a_quote_tracker_status']}` |",
        f"| ZRC-ND Phase A RFQ send confirmation intake | `{summary['zrc_phase_a_rfq_send_confirmation_intake_status']}`; files={summary['zrc_phase_a_rfq_send_confirmation_intake_files']}; applied={summary['zrc_phase_a_rfq_send_confirmation_intake_applied_rows']}; needs-review={summary['zrc_phase_a_rfq_send_confirmation_intake_needs_review_rows']}; bundle-matched={summary['zrc_phase_a_rfq_send_confirmation_intake_bundle_matched_rows']} |",
        f"| ZRC-ND Phase A RFQ send confirmation entry sheet | `{summary['zrc_phase_a_rfq_send_confirmation_entry_sheet_status']}`; rows={summary['zrc_phase_a_rfq_send_confirmation_entry_sheet_rows']}; source-files={summary['zrc_phase_a_rfq_send_confirmation_entry_sheet_source_files']}; ready={summary['zrc_phase_a_rfq_send_confirmation_entry_sheet_ready_rows']}; blocked={summary['zrc_phase_a_rfq_send_confirmation_entry_sheet_blocked_rows']} |",
        f"| ZRC-ND Phase A RFQ send confirmation entry apply | `{summary['zrc_phase_a_rfq_send_confirmation_entry_apply_status']}`; apply rows={summary['zrc_phase_a_rfq_send_confirmation_entry_apply_rows']}; applied={summary['zrc_phase_a_rfq_send_confirmation_entry_apply_applied_rows']}; blocked={summary['zrc_phase_a_rfq_send_confirmation_entry_apply_blocked_rows']} |",
        f"| ZRC-ND Phase A RFQ send log | `{summary['zrc_phase_a_rfq_send_log_status']}`; rows={summary['zrc_phase_a_rfq_send_log_rows']}; sent={summary['zrc_phase_a_rfq_send_log_sent_rows']}; valid={summary['zrc_phase_a_rfq_send_log_valid_sent_rows']}; applied dates={summary['zrc_phase_a_rfq_send_log_applied_dates']}; errors={summary['zrc_phase_a_rfq_send_log_errors']} |",
        f"| ZRC-ND Phase A RFQ reply intake | `{summary['zrc_phase_a_rfq_reply_intake_status']}`; files={summary['zrc_phase_a_rfq_reply_intake_files']}; applied={summary['zrc_phase_a_rfq_reply_intake_applied_rows']}; needs-review={summary['zrc_phase_a_rfq_reply_intake_needs_review_rows']}; needs-verified-send={summary['zrc_phase_a_rfq_reply_intake_needs_verified_send_rows']} |",
        f"| ZRC-ND Phase A RFQ reply log | `{summary['zrc_phase_a_rfq_reply_log_status']}`; rows={summary['zrc_phase_a_rfq_reply_log_rows']}; received={summary['zrc_phase_a_rfq_reply_log_received_rows']}; valid={summary['zrc_phase_a_rfq_reply_log_valid_rows']}; applied fields={summary['zrc_phase_a_rfq_reply_log_applied_fields']}; errors={summary['zrc_phase_a_rfq_reply_log_errors']} |",
        f"| ZRC-ND Phase A vendor contact plan | `{summary['zrc_phase_a_contact_plan_status']}`; ready first-wave={summary['zrc_phase_a_contact_ready_count']}; standby second-wave={summary['zrc_phase_a_contact_standby_count']}; total={summary['zrc_phase_a_contact_row_count']} |",
        f"| ZRC-ND Phase A RFQ dispatch manifest | `{summary['zrc_phase_a_rfq_dispatch_manifest_status']}`; rows={summary['zrc_phase_a_rfq_dispatch_manifest_rows']}; ready={summary['zrc_phase_a_rfq_dispatch_manifest_ready_rows']}; blocked={summary['zrc_phase_a_rfq_dispatch_manifest_blocked_rows']} |",
        f"| ZRC-ND Phase A RFQ dispatch archive | `{summary['zrc_phase_a_rfq_dispatch_archive_status']}`; files={summary['zrc_phase_a_rfq_dispatch_archive_files']}; missing={summary['zrc_phase_a_rfq_dispatch_archive_missing_files']}; hash-mismatches={summary['zrc_phase_a_rfq_dispatch_archive_hash_mismatches']}; archive=`{summary['zrc_phase_a_rfq_dispatch_archive_path']}`; sha256=`{summary['zrc_phase_a_rfq_dispatch_archive_sha256']}` |",
        f"| ZRC-ND Phase A RFQ reply action pack | `{summary['zrc_phase_a_rfq_reply_action_pack_status']}`; rows={summary['zrc_phase_a_rfq_reply_action_pack_rows']}; waiting-send={summary['zrc_phase_a_rfq_reply_action_pack_waiting_send_rows']}; awaiting-reply={summary['zrc_phase_a_rfq_reply_action_pack_awaiting_reply_rows']}; needs-source={summary['zrc_phase_a_rfq_reply_action_pack_needs_source_rows']}; ready-apply={summary['zrc_phase_a_rfq_reply_action_pack_ready_apply_rows']} |",
        f"| ZRC-ND Phase A RFQ send cockpit | `{summary['zrc_phase_a_rfq_send_cockpit_status']}`; rows={summary['zrc_phase_a_rfq_send_cockpit_rows']}; ready={summary['zrc_phase_a_rfq_send_cockpit_ready_rows']}; confirmations={summary['zrc_phase_a_rfq_send_cockpit_confirmations']}; replies={summary['zrc_phase_a_rfq_send_cockpit_replies']}; missing-email={summary['zrc_phase_a_rfq_send_cockpit_missing_email']}; missing-bundle={summary['zrc_phase_a_rfq_send_cockpit_missing_bundle']}; html=`{summary['zrc_phase_a_rfq_send_cockpit_html']}` |",
        f"| ZRC-ND Phase A quote selection | `{summary['zrc_phase_a_quote_selection_status']}`; sent={summary['zrc_phase_a_quote_selection_sent_count']}; replies={summary['zrc_phase_a_quote_selection_reply_count']}; source-backed replies={summary['zrc_phase_a_quote_selection_source_backed_reply_count']}; shortlisted={summary['zrc_phase_a_quote_selection_shortlist_count']} |",
        f"| ZRC-ND Phase A execution authorization log | `{summary['zrc_phase_a_execution_authorization_status']}`; rows={summary['zrc_phase_a_execution_authorization_rows']}; valid={summary['zrc_phase_a_execution_authorization_valid_rows']}; errors={summary['zrc_phase_a_execution_authorization_errors']} |",
        f"| ZRC-ND Phase A execution release audit | `{summary['zrc_phase_a_execution_release_status']}`; ready={str(summary['zrc_phase_a_execution_release_ready']).lower()}; released={str(summary['zrc_phase_a_execution_release_released']).lower()}; blockers={summary['zrc_phase_a_execution_release_blockers']}; authorization blockers={summary['zrc_phase_a_execution_release_authorization_blockers']} |",
        f"| ZRC-ND Phase A vendor return intake | `{summary['zrc_phase_a_vendor_return_status']}`; rows={summary['zrc_phase_a_vendor_return_rows']}; export files={summary['zrc_phase_a_vendor_return_export_files']} |",
        f"| ZRC-ND measurement merge | `{summary['zrc_measurement_merge_status']}`; inserted={summary['zrc_measurement_merge_inserted']}; updated={summary['zrc_measurement_merge_updated']}; output rows={summary['zrc_measurement_merge_output_rows']} |",
        f"| ZRC-ND run completeness | `{summary['zrc_run_completeness_status']}`; measured known={summary['zrc_run_completeness_measured_known_rows']} / {summary['zrc_run_completeness_planned_rows']} |",
        f"| ZRC-ND validation results | `{summary['zrc_validation_result_status']}`; rows={summary['zrc_validation_result_rows']} |",
        "",
        "## Interpretation",
        "",
        f"- {summary['mission_reason']}",
        f"- {summary['next_action_boundary']}",
        "",
        "## Commands",
        "",
        "| Command | Stage | Return | Seconds | Artifact |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for item in result["commands"]:
        lines.append(
            f"| `{item['id']}` | `{item['stage']}` | {item['returncode']} | "
            f"{item['elapsed_seconds']:.3f} | `{item['artifact']}` |"
        )

    lines.extend(["", "## Command Output Tail", ""])
    for item in result["commands"]:
        output = tail("\n".join(part for part in [item["stdout"], item["stderr"]] if part))
        if not output:
            continue
        lines.extend([f"### {item['id']}", "", "```text", output, "```", ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one local LIMINA dry-lab iteration.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    commands = []
    for item in COMMANDS:
        outcome = run_command(item)
        commands.append(outcome)
        print(f"{outcome['id']}: returncode={outcome['returncode']} elapsed={outcome['elapsed_seconds']:.3f}s")
        if outcome["returncode"] != 0:
            break

    result = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(ROOT),
        "summary": summarize(commands),
        "commands": commands,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Wrote {rel(args.json_out)}")
    print(f"Wrote {rel(args.report)}")
    return 1 if result["summary"]["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
