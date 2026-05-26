#!/usr/bin/env python3
"""Render an actionable reply-intake pack for NHI-PEDOT H-A RFQ replies."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPLY_LOG = ROOT / "data" / "nhi_pedot_h_a_rfq_reply_log.csv"
DEFAULT_SEND_LOG = ROOT / "data" / "nhi_pedot_h_a_rfq_send_log.csv"
DEFAULT_TRACKER = ROOT / "data" / "nhi_pedot_h_a_quote_tracker.csv"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_h_a_rfq_reply_action_queue.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_rfq_reply_action_pack.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_rfq_reply_action_pack.md"
DEFAULT_TEMPLATE_DIR = ROOT / "data" / "rfq_reply_review_templates" / "h_a"
DEFAULT_REPLY_DIR = ROOT / "data" / "rfq_reply_files" / "h_a"

SENT_STATUSES = {"sent", "submitted", "emailed", "form_submitted"}
RECEIVED_STATUSES = {"received", "reply_received", "quote_received", "clarification_received", "needs_clarification", "declined", "cannot_quote", "out_of_scope"}
PENDING_REPLY_STATUSES = {"", "awaiting_reply", "pending_reply", "not_sent_yet", "no_reply"}
REVIEW_FIELDS = [
    "can_cover_full_h_a",
    "needs_split_scope",
    "run_id_level_raw_data",
    "media_physicochemical_coverage",
    "coupon_physical_coverage",
    "csv_schema_acceptance",
    "bundle_entry_sheet_acceptance",
    "sample_handling_fit",
    "non_glp_scope_control",
]
HARD_REQUIRED = [
    "run_id_level_raw_data",
    "csv_schema_acceptance",
    "sample_handling_fit",
    "non_glp_scope_control",
]
CSV_FIELDS = [
    "candidate_id",
    "vendor_name",
    "reply_action_status",
    "send_status",
    "sent_at",
    "tracker_contact_date",
    "reply_status",
    "reply_at",
    "reply_source_file_to_save",
    "reply_template",
    "required_review_fields",
    "hard_required_fields",
    "missing_review_fields",
    "selection_decision",
    "quoted_cost",
    "turnaround_days",
    "next_action",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def clean(value: object) -> str:
    return str(value or "").strip()


def normalize(value: str) -> str:
    return clean(value).lower().replace(" ", "_").replace("-", "_")


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def by_candidate(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {clean(row.get("candidate_id")): row for row in rows if clean(row.get("candidate_id"))}


def workspace_file_exists(raw: str) -> bool:
    if not clean(raw):
        return False
    path = Path(clean(raw))
    if not path.is_absolute():
        path = ROOT / path
    return path.exists() and path.is_file()


def reply_file_path(candidate_id: str, reply_row: dict[str, str], reply_dir: Path) -> str:
    existing = clean(reply_row.get("reply_source_file"))
    if existing:
        return existing
    return rel(reply_dir / f"{candidate_id}_reply.txt")


def sent_has_source(send_row: dict[str, str], tracker_row: dict[str, str]) -> bool:
    status = normalize(send_row.get("send_status", ""))
    return status in SENT_STATUSES and bool(clean(send_row.get("computed_send_confirmation_source_sha256")) or clean(tracker_row.get("contact_date")))


def missing_review_fields(reply_row: dict[str, str]) -> list[str]:
    return [field for field in REVIEW_FIELDS if not clean(reply_row.get(field))]


def action_status(reply_row: dict[str, str], send_row: dict[str, str], tracker_row: dict[str, str], reply_path: str) -> str:
    reply_status = normalize(reply_row.get("reply_status", ""))
    if reply_status in RECEIVED_STATUSES:
        if not workspace_file_exists(reply_path):
            return "received_needs_source_file"
        if missing_review_fields(reply_row) and reply_status not in {"declined", "cannot_quote", "out_of_scope"}:
            return "received_needs_review_fields"
        return "ready_for_reply_log_apply"
    if sent_has_source(send_row, tracker_row):
        return "awaiting_vendor_reply"
    if normalize(send_row.get("send_status", "")) in SENT_STATUSES:
        return "sent_needs_send_confirmation"
    return "waiting_for_rfq_send"


def next_action_for(status: str) -> str:
    if status == "waiting_for_rfq_send":
        return "Send the RFQ first, then save a real send confirmation and apply the send log."
    if status == "sent_needs_send_confirmation":
        return "Save/apply the real send confirmation before treating any reply as source-backed."
    if status == "awaiting_vendor_reply":
        return "When the vendor replies, save the original email/PDF/page and run RFQ reply intake."
    if status == "received_needs_source_file":
        return "Save the original vendor reply at reply_source_file, then rerun the reply-log validator."
    if status == "received_needs_review_fields":
        return "Fill all review fields from the source-backed reply, then rerun the reply-log validator."
    if status == "ready_for_reply_log_apply":
        return "Run apply_limina_rfq_reply_log.py, evaluate quote replies, then select or reject the provider."
    return "Review this row before proceeding."


def render_reply_template(row: dict[str, object]) -> str:
    lines = [
        f"# {row['vendor_name']} H-A RFQ Reply Review Notes",
        "",
        "This is a planning template only. Do not cite this file as `reply_source_file`.",
        "",
        "After a real vendor reply arrives, save the original email export, quote PDF, attached proposal, or confirmation page to:",
        "",
        f"`{row['reply_source_file_to_save']}`",
        "",
        "The intake script can register the matching row in `data/nhi_pedot_h_a_rfq_reply_log.csv` for review.",
        "Use these fields if manual review is needed:",
        "",
        f"- `candidate_id`: `{row['candidate_id']}`",
        "- `reply_status`: `quote_received`, `received`, `clarification_received`, `declined`, or `cannot_quote`",
        "- `reply_at`: timestamp or date of the vendor reply",
        "- `responder_name`: sender/person/team name",
        "- `quote_id_or_reference`: quote ID, ticket, email subject, or proposal reference",
        f"- `reply_source_file`: `{row['reply_source_file_to_save']}`",
        "",
        "Review fields to extract from the original reply:",
    ]
    lines.extend(f"- `{field}`" for field in REVIEW_FIELDS)
    lines.extend([
        "",
        "Hard required fields for execution selection:",
    ])
    lines.extend(f"- `{field}`" for field in HARD_REQUIRED)
    lines.extend([
        "",
        "Do not select a provider unless the reply is source-backed and preserves run_id-level raw data.",
        "",
        "After saving the real reply, run:",
        "",
        "`python3 scripts/intake_limina_rfq_replies.py --profile h_a`",
        "",
        "Then run:",
        "",
        "`python3 scripts/apply_limina_rfq_reply_log.py --profile h_a`",
        "",
    ])
    return "\n".join(lines)


def write_templates(template_dir: Path, rows: list[dict[str, object]]) -> None:
    template_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        path = template_dir / f"{row['candidate_id']}_reply_review_template.md"
        path.write_text(render_reply_template(row), encoding="utf-8")
        row["reply_template"] = rel(path)


def build_pack(args: argparse.Namespace) -> dict[str, object]:
    _reply_fields, reply_rows = load_csv(args.reply_log)
    _send_fields, send_rows = load_csv(args.send_log)
    _tracker_fields, tracker_rows = load_csv(args.tracker)
    send_by_id = by_candidate(send_rows)
    tracker_by_id = by_candidate(tracker_rows)
    rows: list[dict[str, object]] = []

    for reply_row in reply_rows:
        candidate_id = clean(reply_row.get("candidate_id"))
        send_row = send_by_id.get(candidate_id, {})
        tracker_row = tracker_by_id.get(candidate_id, {})
        reply_path = reply_file_path(candidate_id, reply_row, args.reply_dir)
        status = action_status(reply_row, send_row, tracker_row, reply_path)
        row = {
            "candidate_id": candidate_id,
            "vendor_name": clean(reply_row.get("vendor_name")) or clean(tracker_row.get("vendor_name")),
            "reply_action_status": status,
            "send_status": clean(send_row.get("send_status")) or "missing_send_log_row",
            "sent_at": clean(send_row.get("sent_at")),
            "tracker_contact_date": clean(tracker_row.get("contact_date")),
            "reply_status": clean(reply_row.get("reply_status")),
            "reply_at": clean(reply_row.get("reply_at")),
            "reply_source_file_to_save": reply_path,
            "reply_template": "",
            "required_review_fields": ";".join(REVIEW_FIELDS),
            "hard_required_fields": ";".join(HARD_REQUIRED),
            "missing_review_fields": ";".join(missing_review_fields(reply_row)),
            "selection_decision": clean(tracker_row.get("decision")),
            "quoted_cost": clean(reply_row.get("quoted_cost")),
            "turnaround_days": clean(reply_row.get("turnaround_days")),
            "next_action": next_action_for(status),
        }
        rows.append(row)

    write_templates(args.template_dir, rows)
    status_counts = Counter(clean(row["reply_action_status"]) for row in rows)
    status = "h_a_rfq_reply_action_pack_ready"
    if not rows:
        status = "h_a_rfq_reply_action_pack_no_rows"
    elif status_counts.get("waiting_for_rfq_send", 0) == len(rows):
        status = "h_a_rfq_reply_action_pack_waiting_for_send"

    return {
        "status": status,
        "purpose": "Action queue for preserving source-backed vendor replies and turning them into provider-selection inputs.",
        "summary": {
            "action_rows": len(rows),
            "waiting_for_send_rows": status_counts.get("waiting_for_rfq_send", 0),
            "awaiting_reply_rows": status_counts.get("awaiting_vendor_reply", 0),
            "received_needs_source_file_rows": status_counts.get("received_needs_source_file", 0),
            "received_needs_review_fields_rows": status_counts.get("received_needs_review_fields", 0),
            "ready_for_reply_log_apply_rows": status_counts.get("ready_for_reply_log_apply", 0),
            "status_counts": dict(status_counts),
        },
        "inputs": {
            "reply_log": rel(args.reply_log),
            "send_log": rel(args.send_log),
            "tracker": rel(args.tracker),
        },
        "generated_artifacts": {
            "csv": rel(args.csv_out),
            "json": rel(args.json_out),
            "report": rel(args.report),
            "template_dir": rel(args.template_dir),
        },
        "rows": rows,
        "boundary": (
            "This reply action pack is sourcing logistics only. Vendor replies and quotes can authorize execution, "
            "but only returned measurement files can become material evidence."
        ),
    }


def render_report(result: dict[str, object]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A RFQ Reply Action Pack",
        "",
        "This pack guides source-backed RFQ reply intake and provider selection. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Action rows:** {summary['action_rows']}",
        f"**Waiting for send:** {summary['waiting_for_send_rows']}",
        f"**Awaiting reply:** {summary['awaiting_reply_rows']}",
        f"**Needs source file:** {summary['received_needs_source_file_rows']}",
        f"**Needs review fields:** {summary['received_needs_review_fields_rows']}",
        f"**Ready for reply-log apply:** {summary['ready_for_reply_log_apply_rows']}",
        f"**CSV:** `{result['generated_artifacts']['csv']}`",
        f"**Reply review templates:** `{result['generated_artifacts']['template_dir']}`",
        "",
        "## Action Queue",
        "",
        "| Vendor | Status | Reply source file to save | Missing review fields | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        missing = clean(row.get("missing_review_fields")) or "-"
        lines.append(
            f"| {row['vendor_name']} | `{row['reply_action_status']}` | "
            f"`{row['reply_source_file_to_save']}` | `{missing}` | {row['next_action']} |"
        )
    lines.extend([
        "",
        "## Hard Required Selection Fields",
        "",
    ])
    lines.extend(f"- `{field}`" for field in HARD_REQUIRED)
    lines.extend([
        "",
        "## After A Reply Arrives",
        "",
        "1. Save the original vendor reply at the listed `reply_source_file` path.",
        "2. Run `python3 scripts/intake_limina_rfq_replies.py --profile h_a`.",
        "3. Run `python3 scripts/apply_limina_rfq_reply_log.py --profile h_a`.",
        "4. Run `python3 scripts/evaluate_nhi_pedot_h_a_quote_replies.py` and then the full iteration.",
        "",
        "## Boundary",
        "",
        str(result["boundary"]),
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A RFQ reply action pack.")
    parser.add_argument("--reply-log", type=Path, default=DEFAULT_REPLY_LOG)
    parser.add_argument("--send-log", type=Path, default=DEFAULT_SEND_LOG)
    parser.add_argument("--tracker", type=Path, default=DEFAULT_TRACKER)
    parser.add_argument("--reply-dir", type=Path, default=DEFAULT_REPLY_DIR)
    parser.add_argument("--template-dir", type=Path, default=DEFAULT_TEMPLATE_DIR)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_pack(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A RFQ reply action pack: {result['status']}")
    print(f"Action rows: {result['summary']['action_rows']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] in {"h_a_rfq_reply_action_pack_ready", "h_a_rfq_reply_action_pack_waiting_for_send"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
