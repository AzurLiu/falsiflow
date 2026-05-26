#!/usr/bin/env python3
"""Apply reviewed non-EML H-A RFQ send confirmations into the send log."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHEET = ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.csv"
DEFAULT_SEND_LOG = ROOT / "data" / "nhi_pedot_h_a_rfq_send_log.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_entry_apply.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_rfq_send_confirmation_entry_apply.md"

SEND_LOG_FIELDS = [
    "candidate_id",
    "vendor_name",
    "wave",
    "send_status",
    "sent_at",
    "sent_by",
    "send_method",
    "recipient_or_form",
    "message_id_or_confirmation",
    "send_confirmation_source_file",
    "send_confirmation_source_sha256",
    "computed_send_confirmation_source_sha256",
    "sent_bundle_sha256",
    "email_file",
    "bundle_zip",
    "expected_bundle_sha256",
    "attachment_count",
    "tracker_contact_date",
    "tracker_reply_date",
    "tracker_decision",
    "notes",
]

SENT_STATUSES = {"sent", "submitted", "emailed", "form_submitted"}
NON_EVIDENCE_BOUNDARY = (
    "Applying RFQ send-confirmation entries updates outreach logistics only. It does not create "
    "measurement evidence or advance material suitability gates."
)


def clean(value: Any) -> str:
    return str(value or "").strip()


def truthy(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def normalized_status(raw: str) -> str:
    return clean(raw).lower().replace("-", "_").replace(" ", "_")


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


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("candidate_id")): row for row in rows if clean(row.get("candidate_id"))}


def append_note(existing: str, note: str) -> str:
    if not clean(existing):
        return note
    if note in existing:
        return existing
    return f"{existing}; {note}"


def validation_errors(sheet_row: dict[str, str], send_log_row: dict[str, str] | None) -> list[str]:
    errors: list[str] = []
    if send_log_row is None:
        errors.append("unknown_candidate_id")
    if normalized_status(sheet_row.get("send_status_to_apply", "")) not in SENT_STATUSES:
        errors.append("send_status_to_apply_invalid")
    for field in [
        "sent_at",
        "sent_by",
        "send_method",
        "recipient_or_form",
        "message_id_or_confirmation",
        "human_reviewed_by",
    ]:
        if not clean(sheet_row.get(field)):
            errors.append(f"{field}=missing")
    source_file = clean(sheet_row.get("send_confirmation_source_file"))
    if not file_exists(source_file):
        errors.append("send_confirmation_source_file=missing")
    current_hash = sha256(source_file)
    if not current_hash:
        errors.append("send_confirmation_source_sha256=current_missing")
    if current_hash and clean(sheet_row.get("send_confirmation_source_sha256_to_apply")) != current_hash:
        errors.append("send_confirmation_source_sha256=mismatch")
    expected = clean(sheet_row.get("expected_bundle_sha256"))
    sent = clean(sheet_row.get("sent_bundle_sha256_to_record"))
    if not expected:
        errors.append("expected_bundle_sha256=missing")
    if not sent:
        errors.append("sent_bundle_sha256_to_record=missing")
    elif expected and sent != expected:
        errors.append("sent_bundle_sha256_to_record=mismatch")
    if send_log_row and clean(send_log_row.get("expected_bundle_sha256")) and expected != clean(send_log_row.get("expected_bundle_sha256")):
        errors.append("expected_bundle_sha256=send_log_mismatch")
    return errors


def build_apply(args: argparse.Namespace) -> dict[str, Any]:
    _sheet_fields, sheet_rows = load_csv(args.sheet)
    send_log_fields, send_log_rows = load_csv(args.send_log)
    if not send_log_fields:
        send_log_fields = SEND_LOG_FIELDS
    send_log_by_id = by_candidate(send_log_rows)
    apply_rows = [row for row in sheet_rows if truthy(row.get("apply"))]
    results: list[dict[str, Any]] = []
    applied = 0

    for sheet_row in apply_rows:
        candidate_id = clean(sheet_row.get("candidate_id"))
        send_log_row = send_log_by_id.get(candidate_id)
        errors = validation_errors(sheet_row, send_log_row)
        current_hash = sha256(sheet_row.get("send_confirmation_source_file", ""))
        status = "applied" if not errors else "blocked"
        if send_log_row is not None and not errors:
            send_log_row["send_status"] = normalized_status(sheet_row["send_status_to_apply"])
            send_log_row["sent_at"] = clean(sheet_row["sent_at"])
            send_log_row["sent_by"] = clean(sheet_row["sent_by"])
            send_log_row["send_method"] = clean(sheet_row["send_method"])
            send_log_row["recipient_or_form"] = clean(sheet_row["recipient_or_form"])
            send_log_row["message_id_or_confirmation"] = clean(sheet_row["message_id_or_confirmation"])
            send_log_row["send_confirmation_source_file"] = clean(sheet_row["send_confirmation_source_file"])
            send_log_row["send_confirmation_source_sha256"] = current_hash
            send_log_row["computed_send_confirmation_source_sha256"] = current_hash
            send_log_row["sent_bundle_sha256"] = clean(sheet_row["sent_bundle_sha256_to_record"])
            send_log_row["notes"] = append_note(
                send_log_row.get("notes", ""),
                f"manual_confirmation_entry_reviewed_by={clean(sheet_row['human_reviewed_by'])}",
            )
            if clean(sheet_row.get("notes")):
                send_log_row["notes"] = append_note(send_log_row.get("notes", ""), clean(sheet_row["notes"]))
            applied += 1
        results.append({
            "candidate_id": candidate_id,
            "vendor_name": clean(sheet_row.get("vendor_name")),
            "apply_status": status,
            "send_confirmation_source_file": clean(sheet_row.get("send_confirmation_source_file")),
            "computed_send_confirmation_source_sha256": current_hash,
            "sent_bundle_sha256": clean(sheet_row.get("sent_bundle_sha256_to_record")),
            "errors": errors,
        })

    write_csv(args.send_log, send_log_fields, send_log_rows)
    blocked = len(results) - applied
    if not apply_rows:
        status = "h_a_rfq_send_confirmation_entry_apply_no_apply_rows"
    elif blocked:
        status = "h_a_rfq_send_confirmation_entry_apply_blocked"
    else:
        status = "h_a_rfq_send_confirmation_entry_apply_applied"
    return {
        "status": status,
        "purpose": "Apply reviewed non-EML H-A RFQ send confirmations into the send log without treating outreach as evidence.",
        "summary": {
            "sheet_rows": len(sheet_rows),
            "apply_rows": len(apply_rows),
            "applied_rows": applied,
            "blocked_rows": blocked,
            "error_count": sum(len(row["errors"]) for row in results),
        },
        "inputs": {
            "sheet": rel(args.sheet),
            "send_log": rel(args.send_log),
        },
        "generated_artifacts": {
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "rows": results,
        "boundary": NON_EVIDENCE_BOUNDARY,
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A RFQ Send Confirmation Entry Apply",
        "",
        "This report applies reviewed non-EML send confirmations to the RFQ send log. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Sheet rows:** {summary['sheet_rows']}",
        f"**Apply rows:** {summary['apply_rows']}",
        f"**Applied rows:** {summary['applied_rows']}",
        f"**Blocked rows:** {summary['blocked_rows']}",
        f"**Errors:** {summary['error_count']}",
        "",
        "## Rows",
        "",
        "| Vendor | Status | Source file | SHA-256 | Bundle SHA-256 | Errors |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        sha = row["computed_send_confirmation_source_sha256"][:16] + "..." if row["computed_send_confirmation_source_sha256"] else "-"
        bundle = row["sent_bundle_sha256"][:16] + "..." if row["sent_bundle_sha256"] else "-"
        errors = "; ".join(row["errors"]) if row["errors"] else "-"
        lines.append(
            f"| {row['vendor_name']} | `{row['apply_status']}` | `{row['send_confirmation_source_file']}` | "
            f"`{sha}` | `{bundle}` | `{errors}` |"
        )
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply H-A RFQ send-confirmation entry sheet.")
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--send-log", type=Path, default=DEFAULT_SEND_LOG)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_apply(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A RFQ send confirmation entry apply: {result['status']}")
    print(f"Applied: {result['summary']['applied_rows']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] != "h_a_rfq_send_confirmation_entry_apply_blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
