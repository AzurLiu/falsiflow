#!/usr/bin/env python3
"""Render sendable RFQ outbox bundles for ZRC-ND Phase A measurement vendors."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RFQ = ROOT / "data" / "zrc_nd_phase_a_rfq_packet.json"
DEFAULT_DELIVERY = ROOT / "data" / "zrc_nd_phase_a_delivery_package_manifest.json"
DEFAULT_OUTBOX_DIR = ROOT / "data" / "zrc_nd_phase_a_rfq_outbox"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_rfq_outbox_manifest.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_rfq_outbox.md"
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)

ATTACHMENT_FIELDS = ["path", "exists", "bytes", "sha256", "role"]
OUTBOX_FIELDS = [
    "candidate_id",
    "vendor_name",
    "source_url",
    "contact_url",
    "subject",
    "email_file",
    "bundle_zip",
    "bundle_bytes",
    "bundle_sha256",
    "attachment_count",
    "send_status",
]

NON_EVIDENCE_BOUNDARY = (
    "RFQ emails, vendor capability replies, supplier guidance, and quote packages are sourcing artifacts only. "
    "They do not count as material evidence until real returned measurements pass LIMINA QC."
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
    return cleaned or "vendor"


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_size(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    return path.stat().st_size


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def delivery_roles(delivery: dict[str, Any]) -> dict[str, str]:
    return {
        item.get("path", ""): item.get("role", "")
        for item in delivery.get("package_files", [])
        if item.get("path")
    }


def attachment_rows(rfq: dict[str, Any], delivery: dict[str, Any]) -> list[dict[str, Any]]:
    roles = delivery_roles(delivery)
    rows = []
    for path in rfq.get("attachment_paths", []):
        absolute = ROOT / path
        rows.append({
            "path": path,
            "exists": str(absolute.exists()).lower(),
            "bytes": file_size(absolute) if absolute.exists() else "",
            "sha256": sha256(absolute) or "",
            "role": roles.get(path, ""),
        })
    return rows


def email_text(request: dict[str, Any]) -> str:
    return "\n".join([
        f"To: {request.get('name', 'vendor')} team",
        f"Source URL: {request.get('source_url', '')}",
        f"Contact URL: {request.get('contact_url', '')}",
        f"Subject: {request.get('subject', '')}",
        "",
        request.get("email_body", ""),
        "",
        "Boundary:",
        NON_EVIDENCE_BOUNDARY,
        "",
    ])


def write_vendor_email(outbox_dir: Path, request: dict[str, Any]) -> Path:
    email_dir = outbox_dir / "emails"
    email_dir.mkdir(parents=True, exist_ok=True)
    candidate_id = safe_id(str(request.get("candidate_id", "vendor")))
    path = email_dir / f"{candidate_id}_rfq_email.txt"
    path.write_text(email_text(request), encoding="utf-8")
    return path


def add_file_to_zip(bundle: zipfile.ZipFile, path: Path, arcname: str) -> None:
    info = zipfile.ZipInfo(arcname, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    bundle.writestr(info, path.read_bytes())


def write_bundle(outbox_dir: Path, request: dict[str, Any], email_path: Path, attachment_manifest: Path, attachments: list[str]) -> Path:
    package_dir = outbox_dir / "vendor_packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    candidate_id = safe_id(str(request.get("candidate_id", "vendor")))
    zip_path = package_dir / f"{candidate_id}_zrc_nd_phase_a_rfq_bundle.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        add_file_to_zip(bundle, email_path, f"email/{email_path.name}")
        add_file_to_zip(bundle, attachment_manifest, f"manifest/{attachment_manifest.name}")
        for attachment in attachments:
            absolute = ROOT / attachment
            if absolute.exists() and absolute.is_file():
                add_file_to_zip(bundle, absolute, f"attachments/{attachment}")
    return zip_path


def render_outbox(rfq: dict[str, Any], delivery: dict[str, Any], outbox_dir: Path) -> dict[str, Any]:
    attachments = list(rfq.get("attachment_paths", []))
    attachment_manifest = outbox_dir / "attachment_manifest.csv"
    manifest_rows = attachment_rows(rfq, delivery)
    write_csv(attachment_manifest, ATTACHMENT_FIELDS, manifest_rows)

    missing = [row["path"] for row in manifest_rows if row["exists"] != "true"]
    delivery_missing = delivery.get("missing_required_file_ids", [])
    rows = []
    for request in rfq.get("quote_requests", []):
        email_path = write_vendor_email(outbox_dir, request)
        zip_path = write_bundle(outbox_dir, request, email_path, attachment_manifest, attachments)
        rows.append({
            "candidate_id": request.get("candidate_id", ""),
            "vendor_name": request.get("name", ""),
            "source_url": request.get("source_url", ""),
            "contact_url": request.get("contact_url", ""),
            "subject": request.get("subject", ""),
            "email_file": rel(email_path),
            "bundle_zip": rel(zip_path),
            "bundle_bytes": file_size(zip_path) or "",
            "bundle_sha256": sha256(zip_path) or "",
            "attachment_count": len(attachments) - len(missing),
            "send_status": "ready_to_send" if not missing and not delivery_missing else "missing_attachments",
        })

    outbox_csv = outbox_dir / "rfq_outbox.csv"
    write_csv(outbox_csv, OUTBOX_FIELDS, rows)
    ready_count = sum(1 for row in rows if row["send_status"] == "ready_to_send")
    return {
        "status": (
            "ready_to_send_outbox"
            if rfq.get("status") == "ready_to_send_rfq" and rows and ready_count == len(rows) and not missing and not delivery_missing
            else "outbox_needs_attention"
        ),
        "purpose": "Vendor-specific RFQ emails and zip bundles for sending the real ZRC-ND Phase A measurement request.",
        "active_candidate": rfq.get("active_candidate"),
        "quote_request_count": len(rows),
        "ready_to_send_count": ready_count,
        "attachment_count": len(attachments),
        "missing_attachment_paths": missing,
        "delivery_missing_required_file_ids": delivery_missing,
        "outbox_dir": rel(outbox_dir),
        "attachment_manifest": rel(attachment_manifest),
        "outbox_csv": rel(outbox_csv),
        "rows": rows,
        "send_steps": [
            "Open the vendor-specific email text file.",
            "Attach the matching vendor zip bundle when emailing or upload the bundle through the vendor form if available.",
            "Send through the user's email account or official vendor contact form.",
            "Record contact_date in data/zrc_nd_phase_a_quote_tracker.csv.",
            "Paste any reply into the quote tracker before selecting an execution path.",
        ],
        "non_evidence_boundary": NON_EVIDENCE_BOUNDARY,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# ZRC-ND Phase A RFQ Outbox",
        "",
        "This outbox turns the Phase A RFQ packet into vendor-specific emails and zip bundles. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result.get('active_candidate', '-')}`",
        f"**Quote requests:** {result['quote_request_count']}",
        f"**Ready to send:** {result['ready_to_send_count']} / {result['quote_request_count']}",
        f"**Attachment count:** {result['attachment_count']}",
        "",
        "## Outbox Files",
        "",
        f"- Outbox directory: `{result['outbox_dir']}`",
        f"- Attachment manifest: `{result['attachment_manifest']}`",
        f"- Outbox CSV: `{result['outbox_csv']}`",
        "",
        "## Vendor Bundles",
        "",
        "| Vendor | Email | Bundle | Bytes | SHA256 | Status |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in result["rows"]:
        sha = row["bundle_sha256"][:16] + "..." if row["bundle_sha256"] else "-"
        lines.append(
            f"| {row['vendor_name']} | `{row['email_file']}` | `{row['bundle_zip']}` | "
            f"{row['bundle_bytes']} | `{sha}` | `{row['send_status']}` |"
        )

    lines.extend(["", "## Send Steps", ""])
    lines.extend(f"- {step}" for step in result["send_steps"])

    if result["missing_attachment_paths"] or result["delivery_missing_required_file_ids"]:
        lines.extend(["", "## Missing Items", ""])
        for path in result["missing_attachment_paths"]:
            lines.append(f"- Missing attachment path: `{path}`")
        for item in result["delivery_missing_required_file_ids"]:
            lines.append(f"- Delivery manifest missing required file ID: `{item}`")

    lines.extend(["", "## Boundary", "", result["non_evidence_boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render ZRC-ND Phase A RFQ outbox bundles.")
    parser.add_argument("--rfq", type=Path, default=DEFAULT_RFQ)
    parser.add_argument("--delivery", type=Path, default=DEFAULT_DELIVERY)
    parser.add_argument("--outbox-dir", type=Path, default=DEFAULT_OUTBOX_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = render_outbox(load_json(args.rfq), load_json(args.delivery), args.outbox_dir)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"ZRC-ND Phase A RFQ outbox: {result['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "ready_to_send_outbox" else 2


if __name__ == "__main__":
    raise SystemExit(main())
