#!/usr/bin/env python3
"""Render a guarded entry sheet for non-EML H-A RFQ send confirmations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEND_ACTION_QUEUE = ROOT / "data" / "nhi_pedot_h_a_rfq_send_action_queue.csv"
DEFAULT_SEND_LOG = ROOT / "data" / "nhi_pedot_h_a_rfq_send_log.csv"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.md"

CSV_FIELDS = [
    "candidate_id",
    "vendor_name",
    "entry_status",
    "send_log_status",
    "send_confirmation_source_file",
    "source_file_exists",
    "computed_send_confirmation_source_sha256",
    "send_confirmation_source_sha256_to_apply",
    "expected_bundle_sha256",
    "sent_bundle_sha256_to_record",
    "send_status_to_apply",
    "sent_at",
    "sent_by",
    "send_method",
    "recipient_or_form",
    "message_id_or_confirmation",
    "human_reviewed_by",
    "apply",
    "notes",
    "boundary",
]

SENT_STATUSES = {"sent", "submitted", "emailed", "form_submitted"}
NON_EVIDENCE_BOUNDARY = (
    "Manual RFQ send-confirmation entries document outreach logistics only. They are not quote replies, "
    "measurements, or material suitability evidence."
)


def clean(value: Any) -> str:
    return str(value or "").strip()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def workspace_path(raw: str) -> Path:
    path = Path(clean(raw))
    if path.is_absolute():
        return path
    return ROOT / path


def file_exists(raw: str) -> bool:
    return bool(clean(raw)) and workspace_path(raw).is_file()


def sha256(raw: str) -> str:
    if not file_exists(raw):
        return ""
    digest = hashlib.sha256()
    with workspace_path(raw).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("candidate_id")): row for row in rows if clean(row.get("candidate_id"))}


def normalized_status(raw: str) -> str:
    return clean(raw).lower().replace("-", "_").replace(" ", "_")


def entry_status(row: dict[str, Any]) -> str:
    if normalized_status(row["send_log_status"]) in SENT_STATUSES:
        return "already_sent_in_send_log"
    if clean(row["apply"]).lower() == "yes":
        missing = [
            field for field in [
                "sent_at",
                "sent_by",
                "send_method",
                "recipient_or_form",
                "message_id_or_confirmation",
                "human_reviewed_by",
            ]
            if not clean(row.get(field))
        ]
        if missing:
            return "apply_blocked_missing_" + "_".join(missing)
        if not file_exists(row["send_confirmation_source_file"]):
            return "apply_blocked_missing_source_file"
        if clean(row["computed_send_confirmation_source_sha256"]) != clean(row["send_confirmation_source_sha256_to_apply"]):
            return "apply_blocked_source_sha256_mismatch"
        if clean(row["sent_bundle_sha256_to_record"]) != clean(row["expected_bundle_sha256"]):
            return "apply_blocked_bundle_sha256_mismatch"
        if normalized_status(row["send_status_to_apply"]) not in SENT_STATUSES:
            return "apply_blocked_invalid_send_status"
        return "ready_to_apply_manual_confirmation"
    if file_exists(row["send_confirmation_source_file"]):
        return "source_file_present_waiting_for_review"
    return "waiting_for_confirmation_file"


def build_sheet(args: argparse.Namespace) -> dict[str, Any]:
    _send_fields, send_rows = load_csv(args.send_action_queue)
    _log_fields, send_log_rows = load_csv(args.send_log)
    _existing_fields, existing_rows = load_csv(args.csv_out)
    log_by_id = by_candidate(send_log_rows)
    existing_by_id = by_candidate(existing_rows)
    rows: list[dict[str, Any]] = []

    for send_row in send_rows:
        candidate_id = clean(send_row.get("candidate_id"))
        prior = existing_by_id.get(candidate_id, {})
        log_row = log_by_id.get(candidate_id, {})
        source_file = clean(prior.get("send_confirmation_source_file")) or clean(send_row.get("confirmation_source_file_to_save"))
        computed_hash = sha256(source_file)
        row = {
            "candidate_id": candidate_id,
            "vendor_name": clean(send_row.get("vendor_name")),
            "entry_status": "",
            "send_log_status": clean(log_row.get("send_status")) or clean(send_row.get("send_log_status")),
            "send_confirmation_source_file": source_file,
            "source_file_exists": str(file_exists(source_file)).lower(),
            "computed_send_confirmation_source_sha256": computed_hash,
            "send_confirmation_source_sha256_to_apply": clean(prior.get("send_confirmation_source_sha256_to_apply")) or computed_hash,
            "expected_bundle_sha256": clean(send_row.get("bundle_sha256")) or clean(log_row.get("expected_bundle_sha256")),
            "sent_bundle_sha256_to_record": clean(prior.get("sent_bundle_sha256_to_record")) or clean(send_row.get("sent_bundle_sha256_to_record")),
            "send_status_to_apply": clean(prior.get("send_status_to_apply")) or "sent",
            "sent_at": clean(prior.get("sent_at")),
            "sent_by": clean(prior.get("sent_by")),
            "send_method": clean(prior.get("send_method")) or clean(send_row.get("primary_send_method")),
            "recipient_or_form": clean(prior.get("recipient_or_form")) or clean(send_row.get("recipient_or_form")),
            "message_id_or_confirmation": clean(prior.get("message_id_or_confirmation")),
            "human_reviewed_by": clean(prior.get("human_reviewed_by")),
            "apply": clean(prior.get("apply")) or "no",
            "notes": clean(prior.get("notes")),
            "boundary": NON_EVIDENCE_BOUNDARY,
        }
        row["entry_status"] = entry_status(row)
        rows.append(row)

    ready_rows = sum(1 for row in rows if row["entry_status"] == "ready_to_apply_manual_confirmation")
    source_present_rows = sum(1 for row in rows if row["source_file_exists"] == "true")
    waiting_rows = sum(1 for row in rows if row["entry_status"] == "waiting_for_confirmation_file")
    blocked_rows = sum(1 for row in rows if row["entry_status"].startswith("apply_blocked"))
    already_sent_rows = sum(1 for row in rows if row["entry_status"] == "already_sent_in_send_log")
    if ready_rows:
        status = "h_a_rfq_send_confirmation_entry_sheet_ready_to_apply"
    elif blocked_rows:
        status = "h_a_rfq_send_confirmation_entry_sheet_needs_attention"
    elif already_sent_rows:
        status = "h_a_rfq_send_confirmation_entry_sheet_sent_rows_present"
    else:
        status = "h_a_rfq_send_confirmation_entry_sheet_waiting_for_confirmation_files"

    return {
        "status": status,
        "purpose": "Guarded manual-entry sheet for non-EML H-A RFQ send confirmations such as web-form confirmations, PDFs, screenshots, or saved pages.",
        "summary": {
            "entry_rows": len(rows),
            "source_file_present_rows": source_present_rows,
            "ready_to_apply_rows": ready_rows,
            "blocked_rows": blocked_rows,
            "waiting_for_confirmation_file_rows": waiting_rows,
            "already_sent_rows": already_sent_rows,
        },
        "inputs": {
            "send_action_queue": rel(args.send_action_queue),
            "send_log": rel(args.send_log),
            "existing_sheet": rel(args.csv_out),
        },
        "generated_artifacts": {
            "csv": rel(args.csv_out),
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "rows": rows,
        "boundary": NON_EVIDENCE_BOUNDARY,
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A RFQ Send Confirmation Entry Sheet",
        "",
        "This sheet is for source-backed manual review of non-EML send confirmations. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Rows:** {summary['entry_rows']}",
        f"**Source files present:** {summary['source_file_present_rows']}",
        f"**Ready to apply:** {summary['ready_to_apply_rows']}",
        f"**Blocked:** {summary['blocked_rows']}",
        f"**Waiting for confirmation files:** {summary['waiting_for_confirmation_file_rows']}",
        f"**CSV:** `{result['generated_artifacts']['csv']}`",
        "",
        "## Rows",
        "",
        "| Vendor | Status | Source file | Current SHA-256 | Apply | Sent at | Confirmation ID |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        sha = row["computed_send_confirmation_source_sha256"][:16] + "..." if row["computed_send_confirmation_source_sha256"] else "-"
        lines.append(
            f"| {row['vendor_name']} | `{row['entry_status']}` | `{row['send_confirmation_source_file']}` | "
            f"`{sha}` | `{row['apply']}` | `{row['sent_at'] or '-'}` | `{row['message_id_or_confirmation'] or '-'}` |"
        )
    lines.extend([
        "",
        "## Apply Rule",
        "",
        "Set `apply=yes` only after a real confirmation file exists, `sent_at`, `sent_by`, `message_id_or_confirmation`, and `human_reviewed_by` are filled, and `sent_bundle_sha256_to_record` equals `expected_bundle_sha256`.",
        "",
        "Then run:",
        "",
        "`python3 scripts/apply_nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.py`",
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render H-A RFQ send-confirmation entry sheet.")
    parser.add_argument("--send-action-queue", type=Path, default=DEFAULT_SEND_ACTION_QUEUE)
    parser.add_argument("--send-log", type=Path, default=DEFAULT_SEND_LOG)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_sheet(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A RFQ send confirmation entry sheet: {result['status']}")
    print(f"Ready to apply: {result['summary']['ready_to_apply_rows']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if not result["status"].endswith("_needs_attention") else 2


if __name__ == "__main__":
    raise SystemExit(main())
