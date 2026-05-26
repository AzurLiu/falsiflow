#!/usr/bin/env python3
"""Render send-ready .eml drafts for NHI-PEDOT H-A RFQ outreach without sending them."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from email.message import EmailMessage
from email import policy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RFQ = ROOT / "data" / "nhi_pedot_h_a_rfq_packet.json"
DEFAULT_CONTACT_PLAN = ROOT / "data" / "nhi_pedot_h_a_vendor_contact_plan.json"
DEFAULT_OUTBOX = ROOT / "data" / "nhi_pedot_h_a_rfq_outbox_manifest.json"
DEFAULT_DRAFT_DIR = ROOT / "data" / "nhi_pedot_h_a_rfq_outbox" / "eml_drafts"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_h_a_rfq_eml_drafts.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_rfq_eml_drafts.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_rfq_eml_drafts.md"

CSV_FIELDS = [
    "candidate_id",
    "vendor_name",
    "to_address",
    "subject",
    "eml_file",
    "eml_bytes",
    "eml_sha256",
    "bundle_zip",
    "bundle_sha256",
    "bundle_attached",
    "contact_url",
    "quote_url",
    "draft_status",
    "boundary",
]

NON_EVIDENCE_BOUNDARY = (
    ".eml drafts are unsent outreach convenience files. They are not send confirmations, "
    "quote replies, measurement evidence, or material suitability evidence."
)
EML_POLICY = policy.SMTP.clone(max_line_length=998)


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("candidate_id")): row for row in rows if clean(row.get("candidate_id"))}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() and path.is_file() else 0


def workspace_path(raw: str) -> Path:
    path = Path(clean(raw))
    return path if path.is_absolute() else ROOT / path


def safe_filename(candidate_id: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in candidate_id).strip("_") or "vendor"


def recipient(contact: dict[str, Any]) -> str:
    return clean(contact.get("primary_email"))


def body_text(request: dict[str, Any], outbox_row: dict[str, Any], contact: dict[str, Any]) -> str:
    parts = [
        clean(request.get("email_body")),
        "",
        "---",
        f"LIMINA candidate_id: {clean(request.get('candidate_id'))}",
        f"Vendor source URL: {clean(request.get('source_url'))}",
        f"Bundle zip attached: {clean(outbox_row.get('bundle_zip'))}",
        f"Bundle SHA-256: {clean(outbox_row.get('bundle_sha256'))}",
    ]
    if clean(contact.get("contact_url")):
        parts.append(f"Official contact URL: {clean(contact.get('contact_url'))}")
    parts.extend([
        "",
        "Boundary:",
        NON_EVIDENCE_BOUNDARY,
        "",
    ])
    return "\n".join(parts)


def make_message(request: dict[str, Any], outbox_row: dict[str, Any], contact: dict[str, Any]) -> EmailMessage:
    msg = EmailMessage(policy=EML_POLICY)
    to_address = recipient(contact)
    if to_address:
        msg["To"] = to_address
    msg["Subject"] = clean(request.get("subject"))
    msg["X-LIMINA-Candidate-ID"] = clean(request.get("candidate_id"))
    msg["X-LIMINA-Non-Evidence"] = "true"
    msg.set_content(body_text(request, outbox_row, contact))
    bundle_path = workspace_path(clean(outbox_row.get("bundle_zip")))
    if bundle_path.exists() and bundle_path.is_file():
        msg.add_attachment(
            bundle_path.read_bytes(),
            maintype="application",
            subtype="zip",
            filename=bundle_path.name,
        )
    return msg


def render_drafts(args: argparse.Namespace) -> dict[str, Any]:
    rfq = load_json(args.rfq)
    contact_plan = load_json(args.contact_plan)
    outbox = load_json(args.outbox)
    requests = by_candidate(rfq.get("quote_requests", []))
    outbox_rows = by_candidate(outbox.get("rows", []))
    args.draft_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    first_wave_contacts = [
        row for row in contact_plan.get("rows", [])
        if clean(row.get("wave")) == "first_wave"
    ]
    for contact in first_wave_contacts:
        candidate_id = clean(contact.get("candidate_id"))
        request = requests.get(candidate_id, {})
        outbox_row = outbox_rows.get(candidate_id, {})
        to_address = recipient(contact)
        bundle_path = workspace_path(clean(outbox_row.get("bundle_zip")))
        eml_path = args.draft_dir / f"{safe_filename(candidate_id)}_rfq_draft.eml"
        status = "ready_to_open"
        bundle_attached = False
        if not request:
            status = "missing_rfq_request"
        elif not to_address:
            status = "missing_primary_email"
        elif not bundle_path.exists() or not bundle_path.is_file():
            status = "missing_bundle_zip"
        else:
            msg = make_message(request, outbox_row, contact)
            eml_path.write_bytes(msg.as_bytes(policy=EML_POLICY))
            bundle_attached = True
        eml_exists = status == "ready_to_open" and eml_path.exists() and eml_path.is_file()
        rows.append({
            "candidate_id": candidate_id,
            "vendor_name": clean(request.get("name")) or clean(contact.get("vendor_name")),
            "to_address": to_address,
            "subject": clean(request.get("subject")),
            "eml_file": rel(eml_path) if eml_exists else "",
            "eml_bytes": file_size(eml_path) if eml_exists else "",
            "eml_sha256": sha256(eml_path) if eml_exists else "",
            "bundle_zip": clean(outbox_row.get("bundle_zip")),
            "bundle_sha256": clean(outbox_row.get("bundle_sha256")),
            "bundle_attached": str(bundle_attached).lower(),
            "contact_url": clean(contact.get("contact_url")),
            "quote_url": clean(contact.get("quote_url")),
            "draft_status": status,
            "boundary": NON_EVIDENCE_BOUNDARY,
        })

    ready = sum(1 for row in rows if row["draft_status"] == "ready_to_open")
    missing_to = sum(1 for row in rows if row["draft_status"] == "missing_primary_email")
    missing_bundle = sum(1 for row in rows if row["draft_status"] == "missing_bundle_zip")
    missing_request = sum(1 for row in rows if row["draft_status"] == "missing_rfq_request")
    status = "h_a_rfq_eml_drafts_ready" if rows and ready == len(rows) else "h_a_rfq_eml_drafts_needs_attention"
    if not rows:
        status = "h_a_rfq_eml_drafts_no_requests"
    return {
        "status": status,
        "purpose": "Local .eml drafts for first-wave NHI-PEDOT H-A RFQ outreach. The drafts are not sent automatically.",
        "active_candidate": rfq.get("active_candidate") or contact_plan.get("active_candidate"),
        "summary": {
            "draft_rows": len(rows),
            "ready_to_open_rows": ready,
            "need_attention_rows": len(rows) - ready,
            "missing_to_address_rows": missing_to,
            "missing_bundle_rows": missing_bundle,
            "missing_rfq_request_rows": missing_request,
        },
        "inputs": {
            "rfq": rel(args.rfq),
            "contact_plan": rel(args.contact_plan),
            "outbox": rel(args.outbox),
        },
        "generated_artifacts": {
            "draft_dir": rel(args.draft_dir),
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
        "# NHI-PEDOT H-A RFQ EML Drafts",
        "",
        "This renders local .eml draft files for first-wave RFQ outreach. It does not send email and is not evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result.get('active_candidate', '-')}`",
        f"**Draft rows:** {summary['draft_rows']}",
        f"**Ready to open:** {summary['ready_to_open_rows']}",
        f"**Need attention:** {summary['need_attention_rows']}",
        f"**Missing recipient:** {summary['missing_to_address_rows']}",
        f"**Missing bundle:** {summary['missing_bundle_rows']}",
        f"**Draft directory:** `{result['generated_artifacts']['draft_dir']}`",
        "",
        "## Drafts",
        "",
        "| Vendor | To | Status | EML file | Bundle attached | Contact | Quote |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['vendor_name']} | `{row['to_address'] or '-'}` | `{row['draft_status']}` | "
            f"`{row['eml_file'] or '-'}` | `{row['bundle_attached']}` | "
            f"{row['contact_url'] or '-'} | {row['quote_url'] or '-'} |"
        )
    lines.extend([
        "",
        "## Use",
        "",
        "Opening an `.eml` does not send it. Open each draft in the user's mail client, review recipient/body/attachment, send manually, then save the real sent-email or form confirmation in the send confirmation directory.",
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A RFQ .eml drafts.")
    parser.add_argument("--rfq", type=Path, default=DEFAULT_RFQ)
    parser.add_argument("--contact-plan", type=Path, default=DEFAULT_CONTACT_PLAN)
    parser.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    parser.add_argument("--draft-dir", type=Path, default=DEFAULT_DRAFT_DIR)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = render_drafts(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A RFQ EML drafts: {result['status']}")
    print(f"Ready to open: {result['summary']['ready_to_open_rows']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "h_a_rfq_eml_drafts_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
