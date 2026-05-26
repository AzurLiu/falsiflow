#!/usr/bin/env python3
"""Render a pre-send dispatch manifest for ZRC-ND Phase A RFQ outreach."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTACT_PLAN = ROOT / "data" / "zrc_nd_phase_a_vendor_contact_plan.json"
DEFAULT_OUTBOX = ROOT / "data" / "zrc_nd_phase_a_rfq_outbox_manifest.json"
DEFAULT_SEND_LOG = ROOT / "data" / "zrc_nd_phase_a_rfq_send_log.csv"
DEFAULT_TEMPLATE_DIR = ROOT / "data" / "rfq_send_confirmation_templates" / "zrc_phase_a"
DEFAULT_CSV = ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_manifest.csv"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_manifest.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_rfq_dispatch_manifest.md"

CSV_FIELDS = [
    "dispatch_order",
    "candidate_id",
    "vendor_name",
    "dispatch_status",
    "contact_plan_status",
    "outbox_send_status",
    "send_log_status",
    "primary_send_method",
    "recipient_or_form",
    "contact_url",
    "quote_url",
    "email_file",
    "email_exists",
    "email_sha256",
    "bundle_zip",
    "bundle_exists",
    "bundle_sha256_expected",
    "bundle_sha256_actual",
    "bundle_sha256_match",
    "attachment_count",
    "confirmation_source_file_to_save",
    "confirmation_template",
    "confirmation_template_exists",
    "sent_bundle_sha256_to_record",
    "manual_dispatch_step",
    "non_evidence_boundary",
]

NON_EVIDENCE_BOUNDARY = (
    "This ZRC-ND Phase A dispatch manifest only identifies files for manual RFQ outreach. "
    "It is not a send confirmation, quote reply, measurement result, or material suitability claim."
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
    return path if path.is_absolute() else ROOT / path


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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("candidate_id")): row for row in rows if clean(row.get("candidate_id"))}


def confirmation_template_text(row: dict[str, Any]) -> str:
    return "\n".join([
        f"# {row['vendor_name']} ZRC-ND Phase A RFQ Send Confirmation Notes",
        "",
        "This is a planning template only. Do not cite this file as `send_confirmation_source_file`.",
        "",
        "After a real email or web-form submission, save the original sent-email export, form confirmation page, PDF, or screenshot to:",
        "",
        f"`{row['confirmation_source_file_to_save']}`",
        "",
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
        "Then run:",
        "",
        "`python3 scripts/apply_limina_rfq_send_log.py --profile zrc_phase_a`",
        "",
        "Do not mark the row sent until the real submission has happened.",
        "",
    ])


def dispatch_status(row: dict[str, Any]) -> str:
    blockers: list[str] = []
    if row["contact_plan_status"] != "ready_to_send":
        blockers.append("contact_plan_not_ready")
    if row["outbox_send_status"] != "ready_to_send":
        blockers.append("outbox_not_ready")
    if not clean(row["recipient_or_form"]):
        blockers.append("missing_recipient_or_form")
    if row["email_exists"] != "true":
        blockers.append("missing_email_file")
    if row["bundle_exists"] != "true":
        blockers.append("missing_bundle")
    if row["bundle_sha256_match"] != "true":
        blockers.append("bundle_sha256_mismatch")
    if not clean(row["confirmation_source_file_to_save"]):
        blockers.append("missing_confirmation_save_path")
    return "ready_for_manual_dispatch" if not blockers else "blocked_" + "+".join(blockers)


def dispatch_step(row: dict[str, Any]) -> str:
    if row["dispatch_status"] != "ready_for_manual_dispatch":
        return "Resolve dispatch_status blockers before opening or sending this RFQ."
    return (
        f"Open {row['email_file']}, send or paste through {row['recipient_or_form']}, attach/upload "
        f"{row['bundle_zip']} with SHA-256 {row['sent_bundle_sha256_to_record']}, then save the original "
        f"sent-email export, form confirmation, PDF, or screenshot at {row['confirmation_source_file_to_save']}."
    )


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    contact_plan = load_json(args.contact_plan)
    outbox = load_json(args.outbox)
    send_rows = by_candidate(load_csv(args.send_log))
    outbox_rows = by_candidate(outbox.get("rows", []))
    args.template_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    first_wave = [
        row for row in contact_plan.get("rows", [])
        if clean(row.get("wave")) == "first_wave"
    ]
    for index, contact in enumerate(first_wave, start=1):
        candidate_id = clean(contact.get("candidate_id"))
        outbox_row = outbox_rows.get(candidate_id, {})
        send_row = send_rows.get(candidate_id, {})
        email_file = clean(outbox_row.get("email_file")) or clean(contact.get("email_file"))
        bundle_zip = clean(outbox_row.get("bundle_zip")) or clean(contact.get("bundle_zip"))
        bundle_expected = (
            clean(outbox_row.get("bundle_sha256"))
            or clean(contact.get("bundle_sha256"))
            or clean(send_row.get("expected_bundle_sha256"))
        )
        bundle_actual = sha256(bundle_zip)
        confirmation_save = (
            clean(send_row.get("send_confirmation_source_file"))
            or rel(ROOT / "data" / "rfq_send_confirmation_files" / "zrc_phase_a" / f"{candidate_id}_send_confirmation.txt")
        )
        template_path = args.template_dir / f"{candidate_id}_send_confirmation_template.md"
        row = {
            "dispatch_order": index,
            "candidate_id": candidate_id,
            "vendor_name": clean(contact.get("vendor_name")) or clean(outbox_row.get("vendor_name")),
            "dispatch_status": "",
            "contact_plan_status": clean(contact.get("contact_plan_status")),
            "outbox_send_status": clean(outbox_row.get("send_status")) or clean(contact.get("outbox_send_status")),
            "send_log_status": clean(send_row.get("send_status")) or "missing_send_log_row",
            "primary_send_method": clean(contact.get("primary_send_method")) or clean(send_row.get("send_method")),
            "recipient_or_form": clean(send_row.get("recipient_or_form")) or clean(contact.get("primary_email")) or clean(contact.get("quote_url")) or clean(contact.get("contact_url")),
            "contact_url": clean(contact.get("contact_url")),
            "quote_url": clean(contact.get("quote_url")),
            "email_file": email_file,
            "email_exists": str(file_exists(email_file)).lower(),
            "email_sha256": sha256(email_file),
            "bundle_zip": bundle_zip,
            "bundle_exists": str(file_exists(bundle_zip)).lower(),
            "bundle_sha256_expected": bundle_expected,
            "bundle_sha256_actual": bundle_actual,
            "bundle_sha256_match": str(bool(bundle_expected and bundle_actual == bundle_expected)).lower(),
            "attachment_count": clean(outbox_row.get("attachment_count")) or clean(send_row.get("attachment_count")),
            "confirmation_source_file_to_save": confirmation_save,
            "confirmation_template": rel(template_path),
            "confirmation_template_exists": "false",
            "sent_bundle_sha256_to_record": bundle_expected,
            "manual_dispatch_step": "",
            "non_evidence_boundary": NON_EVIDENCE_BOUNDARY,
        }
        row["dispatch_status"] = dispatch_status(row)
        row["manual_dispatch_step"] = dispatch_step(row)
        template_path.write_text(confirmation_template_text(row), encoding="utf-8")
        row["confirmation_template_exists"] = str(template_path.is_file()).lower()
        rows.append(row)

    ready = sum(1 for row in rows if row["dispatch_status"] == "ready_for_manual_dispatch")
    blocked = len(rows) - ready
    bundle_matches = sum(1 for row in rows if row["bundle_sha256_match"] == "true")
    status = "zrc_phase_a_rfq_dispatch_manifest_ready" if rows and blocked == 0 else "zrc_phase_a_rfq_dispatch_manifest_needs_attention"
    if not rows:
        status = "zrc_phase_a_rfq_dispatch_manifest_no_rows"
    return {
        "status": status,
        "purpose": "Pre-send manifest binding every ZRC-ND Phase A RFQ text file to its exact bundle, contact path, and confirmation-save path.",
        "summary": {
            "dispatch_rows": len(rows),
            "ready_for_manual_dispatch_rows": ready,
            "blocked_rows": blocked,
            "bundle_sha256_match_rows": bundle_matches,
            "email_file_present_rows": sum(1 for row in rows if row["email_exists"] == "true"),
            "confirmation_template_rows": sum(1 for row in rows if row["confirmation_template_exists"] == "true"),
        },
        "inputs": {
            "contact_plan": rel(args.contact_plan),
            "outbox": rel(args.outbox),
            "send_log": rel(args.send_log),
        },
        "generated_artifacts": {
            "csv": rel(args.csv_out),
            "json": rel(args.json_out),
            "report": rel(args.report),
            "template_dir": rel(args.template_dir),
        },
        "rows": rows,
        "boundary": NON_EVIDENCE_BOUNDARY,
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# ZRC-ND Phase A RFQ Dispatch Manifest",
        "",
        "This manifest binds the exact pre-send files for manual ZRC-ND Phase A RFQ outreach. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Dispatch rows:** {summary['dispatch_rows']}",
        f"**Ready for manual dispatch:** {summary['ready_for_manual_dispatch_rows']}",
        f"**Blocked rows:** {summary['blocked_rows']}",
        f"**Bundle SHA-256 matches:** {summary['bundle_sha256_match_rows']}",
        f"**Confirmation templates:** {summary['confirmation_template_rows']}",
        f"**CSV:** `{result['generated_artifacts']['csv']}`",
        "",
        "## Dispatch Rows",
        "",
        "| Order | Vendor | Status | Recipient/Form | Email text | Bundle SHA-256 | Confirmation save path |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        sha = row["bundle_sha256_expected"][:16] + "..." if row["bundle_sha256_expected"] else "-"
        lines.append(
            f"| {row['dispatch_order']} | {row['vendor_name']} | `{row['dispatch_status']}` | "
            f"`{row['recipient_or_form']}` | `{row['email_file']}` | `{sha}` | "
            f"`{row['confirmation_source_file_to_save']}` |"
        )

    lines.extend(["", "## Per-Row Manual Steps", ""])
    for row in result["rows"]:
        lines.append(f"- `{row['candidate_id']}`: {row['manual_dispatch_step']}")

    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render ZRC-ND Phase A RFQ dispatch manifest.")
    parser.add_argument("--contact-plan", type=Path, default=DEFAULT_CONTACT_PLAN)
    parser.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    parser.add_argument("--send-log", type=Path, default=DEFAULT_SEND_LOG)
    parser.add_argument("--template-dir", type=Path, default=DEFAULT_TEMPLATE_DIR)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_manifest(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"ZRC-ND Phase A RFQ dispatch manifest: {result['status']}")
    print(f"Ready rows: {result['summary']['ready_for_manual_dispatch_rows']} / {result['summary']['dispatch_rows']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
