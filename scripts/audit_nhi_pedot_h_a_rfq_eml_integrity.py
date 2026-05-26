#!/usr/bin/env python3
"""Audit NHI-PEDOT H-A RFQ .eml drafts before manual sending."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DRAFTS = ROOT / "data" / "nhi_pedot_h_a_rfq_eml_drafts.json"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_h_a_rfq_eml_integrity_audit.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_rfq_eml_integrity_audit.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_rfq_eml_integrity_audit.md"

CSV_FIELDS = [
    "candidate_id",
    "vendor_name",
    "audit_status",
    "eml_file",
    "eml_exists",
    "to_expected",
    "to_header",
    "to_match",
    "subject_expected",
    "subject_header",
    "subject_match",
    "x_candidate_header",
    "x_candidate_match",
    "non_evidence_header",
    "non_evidence_match",
    "bundle_zip",
    "bundle_exists",
    "bundle_sha256_expected",
    "bundle_sha256_actual",
    "bundle_file_match",
    "attachment_count",
    "zip_attachment_count",
    "matched_bundle_attachment",
    "matched_attachment_filename",
    "matched_attachment_sha256",
    "body_has_boundary",
    "body_has_bundle_sha256",
    "errors",
]

NON_EVIDENCE_BOUNDARY = (
    ".eml drafts are unsent outreach convenience files. They are not send confirmations, "
    "quote replies, measurement evidence, or material suitability evidence."
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def body_text(message: Any) -> str:
    chunks: list[str] = []
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_maintype() == "text":
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or "utf-8"
                chunks.append(payload.decode(charset, errors="replace"))
    elif message.get_content_maintype() == "text":
        payload = message.get_payload(decode=True)
        if payload is not None:
            charset = message.get_content_charset() or "utf-8"
            chunks.append(payload.decode(charset, errors="replace"))
    return "\n".join(chunks)


def attachment_records(message: Any) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for part in message.iter_attachments():
        payload = part.get_payload(decode=True) or b""
        records.append({
            "filename": clean(part.get_filename()),
            "content_type": clean(part.get_content_type()),
            "sha256": sha256_bytes(payload),
            "bytes": str(len(payload)),
        })
    return records


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    candidate_id = clean(row.get("candidate_id"))
    eml_file = clean(row.get("eml_file"))
    eml_path = workspace_path(eml_file)
    bundle_zip = clean(row.get("bundle_zip"))
    bundle_path = workspace_path(bundle_zip)
    expected_bundle_sha = clean(row.get("bundle_sha256"))
    expected_to = clean(row.get("to_address"))
    expected_subject = clean(row.get("subject"))
    eml_exists = eml_path.is_file()
    bundle_exists = bundle_path.is_file()
    bundle_sha_actual = sha256_file(bundle_path) if bundle_exists else ""

    if not eml_exists:
        errors.append("missing_eml_file")
    if not bundle_exists:
        errors.append("missing_bundle_file")
    if expected_bundle_sha and bundle_sha_actual and expected_bundle_sha != bundle_sha_actual:
        errors.append("bundle_file_sha_mismatch")

    message = None
    if eml_exists:
        with eml_path.open("rb") as handle:
            message = BytesParser(policy=policy.default).parse(handle)

    to_header = clean(message.get("To")) if message else ""
    subject_header = clean(message.get("Subject")) if message else ""
    x_candidate = clean(message.get("X-LIMINA-Candidate-ID")) if message else ""
    non_evidence = clean(message.get("X-LIMINA-Non-Evidence")) if message else ""
    text = body_text(message) if message else ""
    attachments = attachment_records(message) if message else []
    zip_attachments = [
        item for item in attachments
        if item["content_type"] == "application/zip" or item["filename"].endswith(".zip")
    ]
    matched = next((item for item in zip_attachments if item["sha256"] == expected_bundle_sha), {})

    checks = {
        "to_match": bool(expected_to and to_header == expected_to),
        "subject_match": bool(expected_subject and subject_header == expected_subject),
        "x_candidate_match": bool(candidate_id and x_candidate == candidate_id),
        "non_evidence_match": non_evidence.lower() == "true",
        "bundle_file_match": bool(expected_bundle_sha and bundle_sha_actual == expected_bundle_sha),
        "matched_bundle_attachment": bool(matched),
        "body_has_boundary": NON_EVIDENCE_BOUNDARY in text,
        "body_has_bundle_sha256": bool(expected_bundle_sha and expected_bundle_sha in text),
    }
    for key, ok in checks.items():
        if not ok:
            errors.append(key)

    status = "pass" if not errors else "fail"
    return {
        "candidate_id": candidate_id,
        "vendor_name": clean(row.get("vendor_name")),
        "audit_status": status,
        "eml_file": eml_file,
        "eml_exists": str(eml_exists).lower(),
        "to_expected": expected_to,
        "to_header": to_header,
        "to_match": str(checks["to_match"]).lower(),
        "subject_expected": expected_subject,
        "subject_header": subject_header,
        "subject_match": str(checks["subject_match"]).lower(),
        "x_candidate_header": x_candidate,
        "x_candidate_match": str(checks["x_candidate_match"]).lower(),
        "non_evidence_header": non_evidence,
        "non_evidence_match": str(checks["non_evidence_match"]).lower(),
        "bundle_zip": bundle_zip,
        "bundle_exists": str(bundle_exists).lower(),
        "bundle_sha256_expected": expected_bundle_sha,
        "bundle_sha256_actual": bundle_sha_actual,
        "bundle_file_match": str(checks["bundle_file_match"]).lower(),
        "attachment_count": len(attachments),
        "zip_attachment_count": len(zip_attachments),
        "matched_bundle_attachment": str(checks["matched_bundle_attachment"]).lower(),
        "matched_attachment_filename": clean(matched.get("filename")),
        "matched_attachment_sha256": clean(matched.get("sha256")),
        "body_has_boundary": str(checks["body_has_boundary"]).lower(),
        "body_has_bundle_sha256": str(checks["body_has_bundle_sha256"]).lower(),
        "errors": ";".join(errors),
    }


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    drafts = load_json(args.drafts)
    rows = [audit_row(row) for row in drafts.get("rows", [])]
    pass_rows = sum(1 for row in rows if row["audit_status"] == "pass")
    fail_rows = len(rows) - pass_rows
    missing_eml = sum(1 for row in rows if row["eml_exists"] != "true")
    missing_bundle = sum(1 for row in rows if row["bundle_exists"] != "true")
    attachment_mismatch = sum(1 for row in rows if row["matched_bundle_attachment"] != "true")
    status = "h_a_rfq_eml_integrity_ready"
    if not rows:
        status = "h_a_rfq_eml_integrity_no_rows"
    elif fail_rows:
        status = "h_a_rfq_eml_integrity_needs_attention"
    return {
        "status": status,
        "purpose": "Pre-send integrity audit for NHI-PEDOT H-A RFQ .eml drafts and attached vendor bundles.",
        "inputs": {
            "drafts": rel(args.drafts),
        },
        "generated_artifacts": {
            "csv": rel(args.csv_out),
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "summary": {
            "audit_rows": len(rows),
            "pass_rows": pass_rows,
            "fail_rows": fail_rows,
            "missing_eml_rows": missing_eml,
            "missing_bundle_rows": missing_bundle,
            "attachment_mismatch_rows": attachment_mismatch,
        },
        "rows": rows,
        "boundary": (
            "This audit only verifies draft-mail logistics. Passing rows are not send confirmations, "
            "quote replies, measurement evidence, provider authorization, or material suitability evidence."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A RFQ EML Integrity Audit",
        "",
        "This pre-send audit parses each local .eml draft and verifies recipient, subject, boundary headers, body markers, bundle file hash, and attached zip hash.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Rows:** {summary['audit_rows']}",
        f"**Pass:** {summary['pass_rows']}",
        f"**Fail:** {summary['fail_rows']}",
        f"**Missing EML:** {summary['missing_eml_rows']}",
        f"**Missing bundle:** {summary['missing_bundle_rows']}",
        f"**Attachment mismatch:** {summary['attachment_mismatch_rows']}",
        "",
        "## Rows",
        "",
        "| Vendor | Status | To | Subject | Bundle file | Attached bundle | Errors |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['vendor_name']} | `{row['audit_status']}` | `{row['to_match']}` | "
            f"`{row['subject_match']}` | `{row['bundle_file_match']}` | "
            f"`{row['matched_bundle_attachment']}` | `{row['errors'] or '-'}` |"
        )
    lines.extend([
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit NHI-PEDOT H-A RFQ EML draft integrity.")
    parser.add_argument("--drafts", type=Path, default=DEFAULT_DRAFTS)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_result(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    summary = result["summary"]
    print(f"H-A RFQ EML integrity audit: {result['status']}")
    print(f"Pass: {summary['pass_rows']} / {summary['audit_rows']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "h_a_rfq_eml_integrity_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
