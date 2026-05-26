#!/usr/bin/env python3
"""Render an actionable send pack for NHI-PEDOT H-A RFQ outbox bundles."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTACT_PLAN = ROOT / "data" / "nhi_pedot_h_a_vendor_contact_plan.json"
DEFAULT_OUTBOX = ROOT / "data" / "nhi_pedot_h_a_rfq_outbox_manifest.json"
DEFAULT_EML_DRAFTS = ROOT / "data" / "nhi_pedot_h_a_rfq_eml_drafts.json"
DEFAULT_SEND_LOG = ROOT / "data" / "nhi_pedot_h_a_rfq_send_log.csv"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_h_a_rfq_send_action_queue.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_rfq_send_action_pack.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_rfq_send_action_pack.md"
DEFAULT_TEMPLATE_DIR = ROOT / "data" / "rfq_send_confirmation_templates" / "h_a"
DEFAULT_CONFIRMATION_DIR = ROOT / "data" / "rfq_send_confirmation_files" / "h_a"

SENT_STATUSES = {"sent", "submitted", "emailed", "form_submitted"}
READY_STATUSES = {"ready_to_send"}
CSV_FIELDS = [
    "send_order",
    "candidate_id",
    "vendor_name",
    "send_action_status",
    "primary_send_method",
    "recipient_or_form",
    "contact_url",
    "quote_url",
    "email_file",
    "eml_draft_file",
    "eml_draft_status",
    "bundle_zip",
    "bundle_sha256",
    "attachment_count",
    "send_log_csv",
    "send_log_status",
    "sent_at",
    "confirmation_source_file_to_save",
    "confirmation_template",
    "sent_bundle_sha256_to_record",
    "tracker_contact_date",
    "tracker_reply_date",
    "next_action",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def clean(value: Any) -> str:
    return str(value or "").strip()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


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
    return clean(raw).lower().replace(" ", "_").replace("-", "_")


def workspace_exists(raw: str) -> bool:
    if not clean(raw):
        return False
    path = Path(clean(raw))
    if not path.is_absolute():
        path = ROOT / path
    return path.exists() and path.is_file()


def default_recipient(contact: dict[str, Any], send_log: dict[str, str]) -> str:
    return (
        clean(send_log.get("recipient_or_form"))
        or clean(contact.get("primary_email"))
        or clean(contact.get("quote_url"))
        or clean(contact.get("contact_url"))
    )


def confirmation_path(candidate_id: str, send_log: dict[str, str], confirmation_dir: Path) -> str:
    existing = clean(send_log.get("send_confirmation_source_file"))
    if existing:
        return existing
    return rel(confirmation_dir / f"{candidate_id}_send_confirmation.txt")


def send_action_status(contact: dict[str, Any], outbox: dict[str, Any], send_log: dict[str, str]) -> str:
    log_status = normalized_status(clean(send_log.get("send_status")))
    if log_status in SENT_STATUSES:
        if clean(send_log.get("computed_send_confirmation_source_sha256")):
            return "sent_confirmation_verified"
        return "sent_needs_confirmation_file"
    contact_status = clean(contact.get("contact_plan_status"))
    outbox_status = clean(outbox.get("send_status"))
    if contact_status in READY_STATUSES and outbox_status == "ready_to_send":
        if workspace_exists(clean(outbox.get("email_file"))) and workspace_exists(clean(outbox.get("bundle_zip"))):
            return "ready_to_send"
        return "missing_outbox_file"
    return contact_status or outbox_status or "not_ready"


def next_action_for(status: str, eml_draft_file: str = "") -> str:
    if status == "ready_to_send":
        if clean(eml_draft_file):
            return "Open the prepared .eml draft, review recipient/body/attached bundle, send manually, save the original confirmation, then run send-confirmation intake."
        return "Send the prepared email or form, attach the bundle zip, save the original confirmation, then run send-confirmation intake."
    if status == "sent_needs_confirmation_file":
        return "Save the original sent-email/form confirmation at the recorded confirmation path, then rerun send-confirmation intake and the send-log validator."
    if status == "sent_confirmation_verified":
        return "Wait for a source-backed vendor reply, save it, then run RFQ reply intake."
    if status == "missing_outbox_file":
        return "Regenerate the RFQ outbox before attempting to send."
    return "Resolve the contact-plan or outbox status before sending."


def render_confirmation_template(row: dict[str, Any]) -> str:
    lines = [
        f"# {row['vendor_name']} H-A RFQ Send Confirmation Notes",
        "",
        "This is a planning template only. Do not cite this file as `send_confirmation_source_file`.",
        "",
        "After a real email or web-form submission, save the original sent-email export, form confirmation page, PDF, or screenshot to:",
        "",
        f"`{row['confirmation_source_file_to_save']}`",
        "",
        "The intake script can fill the matching row in `data/nhi_pedot_h_a_rfq_send_log.csv` when the saved confirmation proves the expected bundle.",
        "Use these fields if manual review is needed:",
        "",
        f"- `candidate_id`: `{row['candidate_id']}`",
        "- `send_status`: `sent`, `emailed`, `submitted`, or `form_submitted`",
        "- `sent_at`: ISO timestamp or date of the actual submission",
        "- `sent_by`: human sender/account",
        f"- `send_method`: `{row['primary_send_method']}`",
        f"- `recipient_or_form`: `{row['recipient_or_form']}`",
        "- `message_id_or_confirmation`: message ID, ticket ID, quote request ID, or form confirmation text",
        f"- `send_confirmation_source_file`: `{row['confirmation_source_file_to_save']}`",
        f"- `sent_bundle_sha256`: `{row['sent_bundle_sha256_to_record']}`",
        "",
        "After saving the real confirmation, run:",
        "",
        "`python3 scripts/intake_limina_rfq_send_confirmations.py --profile h_a`",
        "",
        "Then run:",
        "",
        "`python3 scripts/apply_limina_rfq_send_log.py --profile h_a`",
        "",
        "Do not mark the row sent until the real submission has happened.",
        "",
    ]
    return "\n".join(lines)


def write_templates(template_dir: Path, rows: list[dict[str, Any]]) -> None:
    template_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        path = template_dir / f"{row['candidate_id']}_send_confirmation_template.md"
        path.write_text(render_confirmation_template(row), encoding="utf-8")
        row["confirmation_template"] = rel(path)


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    contact_plan = load_json(args.contact_plan)
    outbox = load_json(args.outbox)
    eml_drafts = load_json(args.eml_drafts)
    _send_fields, send_rows = load_csv(args.send_log)
    outbox_by_id = by_candidate(outbox.get("rows", []))
    eml_by_id = by_candidate(eml_drafts.get("rows", []))
    send_by_id = by_candidate(send_rows)
    rows: list[dict[str, Any]] = []

    first_wave_ready = [
        row for row in contact_plan.get("rows", [])
        if clean(row.get("wave")) == "first_wave"
    ]
    for index, contact in enumerate(first_wave_ready, start=1):
        candidate_id = clean(contact.get("candidate_id"))
        outbox_row = outbox_by_id.get(candidate_id, {})
        eml_row = eml_by_id.get(candidate_id, {})
        send_log = send_by_id.get(candidate_id, {})
        status = send_action_status(contact, outbox_row, send_log)
        eml_draft_file = clean(eml_row.get("eml_file"))
        row = {
            "send_order": index,
            "candidate_id": candidate_id,
            "vendor_name": clean(contact.get("vendor_name")) or clean(outbox_row.get("vendor_name")),
            "send_action_status": status,
            "primary_send_method": clean(contact.get("primary_send_method")) or clean(send_log.get("send_method")),
            "recipient_or_form": default_recipient(contact, send_log),
            "contact_url": clean(contact.get("contact_url")),
            "quote_url": clean(contact.get("quote_url")),
            "email_file": clean(outbox_row.get("email_file")) or clean(send_log.get("email_file")),
            "eml_draft_file": eml_draft_file,
            "eml_draft_status": clean(eml_row.get("draft_status")) or "missing_eml_draft_row",
            "bundle_zip": clean(outbox_row.get("bundle_zip")) or clean(send_log.get("bundle_zip")),
            "bundle_sha256": clean(outbox_row.get("bundle_sha256")) or clean(send_log.get("expected_bundle_sha256")),
            "attachment_count": clean(outbox_row.get("attachment_count")) or clean(send_log.get("attachment_count")),
            "send_log_csv": rel(args.send_log),
            "send_log_status": clean(send_log.get("send_status")) or "missing_send_log_row",
            "sent_at": clean(send_log.get("sent_at")),
            "confirmation_source_file_to_save": confirmation_path(candidate_id, send_log, args.confirmation_dir),
            "confirmation_template": "",
            "sent_bundle_sha256_to_record": clean(outbox_row.get("bundle_sha256")) or clean(send_log.get("expected_bundle_sha256")),
            "tracker_contact_date": clean(contact.get("tracker_contact_date")),
            "tracker_reply_date": clean(contact.get("tracker_reply_date")),
            "next_action": next_action_for(status, eml_draft_file),
        }
        rows.append(row)

    write_templates(args.template_dir, rows)
    status_counts = Counter(row["send_action_status"] for row in rows)
    eml_ready = sum(1 for row in rows if row["eml_draft_status"] == "ready_to_open" and clean(row["eml_draft_file"]))
    eml_missing = len(rows) - eml_ready
    ready_to_send = status_counts.get("ready_to_send", 0)
    missing_outbox = status_counts.get("missing_outbox_file", 0)
    status = "h_a_rfq_send_action_pack_ready"
    if not rows:
        status = "h_a_rfq_send_action_pack_no_first_wave_rows"
    elif missing_outbox:
        status = "h_a_rfq_send_action_pack_missing_outbox_files"
    elif not ready_to_send and not any(row["send_action_status"].startswith("sent_") for row in rows):
        status = "h_a_rfq_send_action_pack_not_ready"

    return {
        "status": status,
        "purpose": "One actionable checklist for sending first-wave NHI-PEDOT H-A RFQ bundles and recording real send confirmations.",
        "active_candidate": contact_plan.get("active_candidate") or outbox.get("active_candidate"),
        "summary": {
            "action_rows": len(rows),
            "ready_to_send_rows": ready_to_send,
            "sent_confirmation_verified_rows": status_counts.get("sent_confirmation_verified", 0),
            "sent_needs_confirmation_rows": status_counts.get("sent_needs_confirmation_file", 0),
            "missing_outbox_file_rows": missing_outbox,
            "eml_draft_ready_rows": eml_ready,
            "eml_draft_missing_rows": eml_missing,
            "status_counts": dict(status_counts),
        },
        "inputs": {
            "contact_plan": rel(args.contact_plan),
            "outbox": rel(args.outbox),
            "eml_drafts": rel(args.eml_drafts),
            "send_log": rel(args.send_log),
        },
        "generated_artifacts": {
            "csv": rel(args.csv_out),
            "json": rel(args.json_out),
            "report": rel(args.report),
            "template_dir": rel(args.template_dir),
        },
        "rows": rows,
        "boundary": (
            "This send action pack is logistics scaffolding only. It must not be used as evidence; "
            "only real returned measurement files can advance H-A gates."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A RFQ Send Action Pack",
        "",
        "This pack turns the first-wave RFQ outbox into an actionable send checklist. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result.get('active_candidate', '-')}`",
        f"**Action rows:** {summary['action_rows']}",
        f"**Ready to send:** {summary['ready_to_send_rows']}",
        f"**Sent confirmations verified:** {summary['sent_confirmation_verified_rows']}",
        f"**Sent rows needing confirmation file:** {summary['sent_needs_confirmation_rows']}",
        f"**EML drafts ready:** {summary['eml_draft_ready_rows']}",
        f"**CSV:** `{result['generated_artifacts']['csv']}`",
        f"**Confirmation templates:** `{result['generated_artifacts']['template_dir']}`",
        "",
        "## Action Queue",
        "",
        "| Order | Vendor | Status | Recipient/Form | EML draft | Email | Bundle | Confirmation file to save |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['send_order']} | {row['vendor_name']} | `{row['send_action_status']}` | "
            f"`{row['recipient_or_form']}` | `{row['eml_draft_file'] or '-'}` | "
            f"`{row['email_file']}` | `{row['bundle_zip']}` | "
            f"`{row['confirmation_source_file_to_save']}` |"
        )

    lines.extend([
        "",
        "## After Sending",
        "",
        "1. Save the real sent-email export, web-form confirmation, PDF, or screenshot at the listed confirmation path.",
        "2. Run `python3 scripts/intake_limina_rfq_send_confirmations.py --profile h_a`.",
        "3. Run `python3 scripts/apply_limina_rfq_send_log.py --profile h_a`.",
        "4. Run `python3 scripts/run_limina_iteration.py`.",
        "",
        "## Per-Vendor Notes",
        "",
    ])
    for row in result["rows"]:
        lines.extend([
            f"### {row['vendor_name']}",
            "",
            f"- Send method: `{row['primary_send_method']}`",
            f"- Recipient or form: `{row['recipient_or_form']}`",
            f"- EML draft: `{row['eml_draft_file'] or '-'}`",
            f"- EML draft status: `{row['eml_draft_status']}`",
            f"- Bundle SHA-256 to record: `{row['sent_bundle_sha256_to_record']}`",
            f"- Confirmation template: `{row['confirmation_template']}`",
            f"- Next action: {row['next_action']}",
            "",
        ])

    lines.extend(["## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A RFQ send action pack.")
    parser.add_argument("--contact-plan", type=Path, default=DEFAULT_CONTACT_PLAN)
    parser.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    parser.add_argument("--eml-drafts", type=Path, default=DEFAULT_EML_DRAFTS)
    parser.add_argument("--send-log", type=Path, default=DEFAULT_SEND_LOG)
    parser.add_argument("--template-dir", type=Path, default=DEFAULT_TEMPLATE_DIR)
    parser.add_argument("--confirmation-dir", type=Path, default=DEFAULT_CONFIRMATION_DIR)
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
    print(f"H-A RFQ send action pack: {result['status']}")
    print(f"Ready to send: {result['summary']['ready_to_send_rows']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "h_a_rfq_send_action_pack_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
