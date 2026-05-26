#!/usr/bin/env python3
"""Render official contact plan for sending ZRC-ND Phase A RFQ bundles."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTACTS = ROOT / "data" / "zrc_nd_phase_a_vendor_contact_channels.json"
DEFAULT_OUTBOX = ROOT / "data" / "zrc_nd_phase_a_rfq_outbox_manifest.json"
DEFAULT_TRACKER = ROOT / "data" / "zrc_nd_phase_a_quote_tracker.csv"
DEFAULT_CSV = ROOT / "data" / "zrc_nd_phase_a_vendor_contact_plan.csv"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_vendor_contact_plan.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_vendor_contact_plan.md"

FIELDS = [
    "wave",
    "candidate_id",
    "vendor_name",
    "primary_send_method",
    "primary_email",
    "secondary_emails",
    "phone",
    "contact_url",
    "quote_url",
    "sample_submission_url",
    "source_url",
    "source_note",
    "email_file",
    "bundle_zip",
    "bundle_sha256",
    "outbox_send_status",
    "tracker_contact_date",
    "tracker_reply_date",
    "tracker_decision",
    "contact_plan_status",
    "send_note",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def load_tracker(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row.get("candidate_id", ""): row for row in csv.DictReader(handle) if row.get("candidate_id")}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def outbox_by_candidate(outbox: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row.get("candidate_id", ""): row for row in outbox.get("rows", []) if row.get("candidate_id")}


def plan_status(contact: dict[str, Any], outbox_row: dict[str, Any], tracker_row: dict[str, str]) -> str:
    if contact.get("wave", "first_wave") != "first_wave" and not outbox_row:
        return "standby_secondary_wave"
    if tracker_row.get("reply_date"):
        return "reply_received"
    if tracker_row.get("contact_date"):
        return "sent_waiting_reply"
    if outbox_row.get("send_status") != "ready_to_send":
        return "outbox_not_ready"
    if not contact.get("primary_email") and not contact.get("contact_url") and not contact.get("quote_url"):
        return "missing_contact_channel"
    return "ready_to_send"


def build_plan(contacts: dict[str, Any], outbox: dict[str, Any], tracker: dict[str, dict[str, str]]) -> dict[str, Any]:
    outbox_rows = outbox_by_candidate(outbox)
    rows = []
    for contact in contacts.get("contacts", []):
        candidate_id = contact.get("candidate_id", "")
        outbox_row = outbox_rows.get(candidate_id, {})
        tracker_row = tracker.get(candidate_id, {})
        rows.append({
            "wave": contact.get("wave", "first_wave"),
            "candidate_id": candidate_id,
            "vendor_name": contact.get("vendor_name", outbox_row.get("vendor_name", "")),
            "primary_send_method": contact.get("primary_send_method", ""),
            "primary_email": contact.get("primary_email", ""),
            "secondary_emails": "; ".join(contact.get("secondary_emails", [])),
            "phone": contact.get("phone", ""),
            "contact_url": contact.get("contact_url", ""),
            "quote_url": contact.get("quote_url", ""),
            "sample_submission_url": contact.get("sample_submission_url", ""),
            "source_url": contact.get("source_url", ""),
            "source_note": contact.get("source_note", ""),
            "email_file": outbox_row.get("email_file", ""),
            "bundle_zip": outbox_row.get("bundle_zip", ""),
            "bundle_sha256": outbox_row.get("bundle_sha256", ""),
            "outbox_send_status": outbox_row.get("send_status", "missing_outbox_row"),
            "tracker_contact_date": tracker_row.get("contact_date", ""),
            "tracker_reply_date": tracker_row.get("reply_date", ""),
            "tracker_decision": tracker_row.get("decision", ""),
            "contact_plan_status": plan_status(contact, outbox_row, tracker_row),
            "send_note": contact.get("send_note", ""),
        })
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["contact_plan_status"]] = status_counts.get(row["contact_plan_status"], 0) + 1
    required_rows = [row for row in rows if row["contact_plan_status"] != "standby_secondary_wave"]
    ready_or_sent = sum(
        count
        for status, count in status_counts.items()
        if status in {"ready_to_send", "sent_waiting_reply", "reply_received"}
    )
    return {
        "status": "contact_plan_ready" if required_rows and ready_or_sent == len(required_rows) else "contact_plan_needs_attention",
        "purpose": "Official contact channels and send checklist for ZRC-ND Phase A first-wave RFQ bundles plus standby secondary-wave options.",
        "active_candidate": contacts.get("active_candidate", outbox.get("active_candidate")),
        "last_checked": contacts.get("last_checked"),
        "row_count": len(rows),
        "status_counts": status_counts,
        "rows": rows,
        "send_instructions": [
            "Use the contact_url or quote_url when a vendor requires a form.",
            "Use primary_email when direct email is accepted; attach the matching bundle_zip.",
            "After sending, enter contact_date in data/zrc_nd_phase_a_quote_tracker.csv and rerun the iteration.",
            "Do not ship samples until the vendor confirms scope, sample acceptance, custody fields, and quote number if required.",
            "Do not treat a contact reply as evidence; only real returned measurements can move Phase A.",
        ],
        "source_boundary": contacts.get("non_evidence_boundary", ""),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# ZRC-ND Phase A Vendor Contact Plan",
        "",
        "This plan maps RFQ outbox bundles to official vendor contact channels. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result.get('active_candidate', '-')}`",
        f"**Last checked:** `{result.get('last_checked', '-')}`",
        f"**Rows:** {result['row_count']}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(result.get("status_counts", {}).items()):
        lines.append(f"- `{status}`: {count}")

    lines.extend(["", "## Contact Rows", "", "| Wave | Vendor | Method | Email | Contact | Bundle | Status |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for row in result["rows"]:
        contact_link = row["quote_url"] or row["contact_url"]
        bundle = row["bundle_zip"] or "-"
        lines.append(
            f"| `{row['wave']}` | {row['vendor_name']} | `{row['primary_send_method']}` | "
            f"`{row['primary_email'] or '-'}` | {contact_link or '-'} | "
            f"`{bundle}` | `{row['contact_plan_status']}` |"
        )

    lines.extend(["", "## Send Instructions", ""])
    lines.extend(f"- {item}" for item in result["send_instructions"])

    lines.extend(["", "## Source Notes", ""])
    for row in result["rows"]:
        lines.extend([
            f"### {row['vendor_name']}",
            "",
            f"- Phone: {row['phone'] or '-'}",
            f"- Secondary emails: {row['secondary_emails'] or '-'}",
            f"- Sample submission URL: {row['sample_submission_url'] or '-'}",
            f"- Source URL: {row['source_url'] or '-'}",
            f"- Source note: {row['source_note'] or '-'}",
            f"- Send note: {row['send_note'] or '-'}",
            "",
        ])

    lines.extend(["## Boundary", "", result.get("source_boundary", ""), ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render ZRC-ND Phase A vendor contact plan.")
    parser.add_argument("--contacts", type=Path, default=DEFAULT_CONTACTS)
    parser.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    parser.add_argument("--tracker", type=Path, default=DEFAULT_TRACKER)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_plan(load_json(args.contacts), load_json(args.outbox), load_tracker(args.tracker))
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"ZRC-ND Phase A vendor contact plan: {result['status']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "contact_plan_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
