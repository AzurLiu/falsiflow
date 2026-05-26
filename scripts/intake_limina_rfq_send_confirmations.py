#!/usr/bin/env python3
"""Intake source-backed RFQ send confirmations into the send log."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from apply_limina_rfq_send_log import (
    FIELDS as SEND_LOG_FIELDS,
    PROFILES,
    Profile,
    build_log_rows,
    existing_log_by_candidate,
    load_csv,
    load_json,
    outbox_by_candidate,
    rel,
    tracker_by_candidate,
    write_csv,
)


ROOT = Path(__file__).resolve().parents[1]
INTAKE_FIELDS = [
    "candidate_id",
    "vendor_name",
    "confirmation_file",
    "confirmation_sha256",
    "detected_by",
    "file_type",
    "from_address",
    "to_address",
    "subject",
    "sent_at",
    "message_id_or_confirmation",
    "attachment_bundle_sha256",
    "expected_bundle_sha256",
    "bundle_hash_match",
    "intake_status",
    "applied_to_send_log",
    "boundary",
]

NON_EVIDENCE_BOUNDARY = (
    "RFQ send confirmations only document outreach logistics. They are not material "
    "measurement evidence and cannot advance suitability gates without returned raw measurements."
)


def clean(value: Any) -> str:
    return str(value or "").strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def default_base(profile: Profile) -> str:
    if profile.status_prefix.endswith("_send_log"):
        return profile.status_prefix.removesuffix("_send_log") + "_send_confirmation_intake"
    return profile.status_prefix + "_confirmation_intake"


def default_csv(profile: Profile) -> Path:
    return ROOT / "data" / f"{default_base(profile)}.csv"


def default_json(profile: Profile) -> Path:
    return ROOT / "data" / f"{default_base(profile)}.json"


def default_report(profile: Profile) -> Path:
    return ROOT / "reports" / f"{default_base(profile)}.md"


def iter_confirmation_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    ignored = {"README.md", ".DS_Store"}
    return sorted(
        path for path in directory.rglob("*")
        if path.is_file() and path.name not in ignored
    )


def parse_email(path: Path):
    if path.suffix.lower() != ".eml":
        return None
    try:
        return BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    except Exception:
        return None


def parse_date(raw: str) -> str:
    if not clean(raw):
        return ""
    try:
        return parsedate_to_datetime(raw).isoformat()
    except (TypeError, ValueError, IndexError, AttributeError):
        return clean(raw)


def attachment_hashes(message) -> list[str]:
    if message is None:
        return []
    hashes: list[str] = []
    for part in message.walk():
        if part.is_multipart():
            continue
        filename = clean(part.get_filename())
        content_type = clean(part.get_content_type()).lower()
        if not (filename.lower().endswith(".zip") or content_type == "application/zip"):
            continue
        payload = part.get_payload(decode=True)
        if payload:
            hashes.append(sha256_bytes(payload))
    return hashes


def detect_candidate(
    path: Path,
    message,
    candidate_ids: set[str],
    outbox_rows: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    header = clean(message.get("X-LIMINA-Candidate-ID")) if message is not None else ""
    if header in candidate_ids:
        return header, "x_limina_candidate_id"
    name = path.stem.lower()
    for candidate_id in sorted(candidate_ids, key=len, reverse=True):
        if candidate_id.lower() in name:
            return candidate_id, "filename"
    subject = clean(message.get("Subject")) if message is not None else ""
    if subject:
        for candidate_id, row in outbox_rows.items():
            if subject == clean(row.get("subject")):
                return candidate_id, "subject"
    return "", "unmatched"


def intake_status(row: dict[str, str], message, matched_bundle: bool, zip_hashes: list[str]) -> str:
    if not row["candidate_id"]:
        return "unmatched_confirmation_file"
    if message is None:
        return "needs_manual_review_non_eml_confirmation"
    missing = [
        field for field in [
            "from_address",
            "to_address",
            "sent_at",
            "message_id_or_confirmation",
        ]
        if not clean(row.get(field))
    ]
    if missing:
        return "needs_manual_review_missing_" + "_".join(missing)
    if not matched_bundle:
        if zip_hashes:
            return "needs_manual_review_bundle_hash_mismatch"
        return "needs_manual_review_missing_bundle_attachment"
    return "ready_to_apply"


def append_note(existing: str, note: str) -> str:
    if not clean(existing):
        return note
    if note in existing:
        return existing
    return f"{existing}; {note}"


def build_result(profile: Profile, intake_csv: Path | None = None) -> dict[str, Any]:
    contacts = load_json(profile.contacts)
    outbox = load_json(profile.outbox)
    tracker_fields, tracker_rows_raw = load_csv(profile.tracker)
    _existing_fields, existing_rows_raw = load_csv(profile.csv_out)
    tracker = tracker_by_candidate(tracker_rows_raw)
    outbox_rows = outbox_by_candidate(outbox)
    rows, unknown_existing = build_log_rows(
        profile,
        contacts,
        outbox,
        tracker,
        existing_log_by_candidate(existing_rows_raw),
    )
    rows_by_id = {row["candidate_id"]: row for row in rows}
    candidate_ids = set(rows_by_id)
    intake_rows: list[dict[str, str]] = []
    applied_candidate_ids: set[str] = set()

    for path in iter_confirmation_files(profile.confirmation_dir):
        file_hash = sha256_file(path)
        message = parse_email(path)
        candidate_id, detected_by = detect_candidate(path, message, candidate_ids, outbox_rows)
        outbox_row = outbox_rows.get(candidate_id, {})
        expected_hash = clean(outbox_row.get("bundle_sha256"))
        zip_hashes = attachment_hashes(message)
        matched_hash = expected_hash if expected_hash in zip_hashes else ""
        row = {
            "candidate_id": candidate_id,
            "vendor_name": clean(outbox_row.get("vendor_name")) or clean(rows_by_id.get(candidate_id, {}).get("vendor_name")),
            "confirmation_file": rel(path),
            "confirmation_sha256": file_hash,
            "detected_by": detected_by,
            "file_type": path.suffix.lower().lstrip(".") or "unknown",
            "from_address": clean(message.get("From")) if message is not None else "",
            "to_address": clean(message.get("To")) if message is not None else "",
            "subject": clean(message.get("Subject")) if message is not None else "",
            "sent_at": parse_date(clean(message.get("Date")) if message is not None else ""),
            "message_id_or_confirmation": clean(message.get("Message-ID")) if message is not None else "",
            "attachment_bundle_sha256": matched_hash,
            "expected_bundle_sha256": expected_hash,
            "bundle_hash_match": str(bool(matched_hash)).lower(),
            "intake_status": "",
            "applied_to_send_log": "false",
            "boundary": NON_EVIDENCE_BOUNDARY,
        }
        row["intake_status"] = intake_status(row, message, bool(matched_hash), zip_hashes)
        send_log_row = rows_by_id.get(candidate_id)
        if (
            row["intake_status"] == "ready_to_apply"
            and send_log_row is not None
            and candidate_id not in applied_candidate_ids
            and clean(send_log_row.get("send_status")).lower().replace("-", "_") not in {"sent", "emailed", "submitted", "form_submitted"}
        ):
            send_log_row["send_status"] = "sent"
            send_log_row["sent_at"] = row["sent_at"]
            send_log_row["sent_by"] = row["from_address"]
            send_log_row["send_method"] = clean(send_log_row.get("send_method")) or "email"
            send_log_row["recipient_or_form"] = row["to_address"]
            send_log_row["message_id_or_confirmation"] = row["message_id_or_confirmation"]
            send_log_row["send_confirmation_source_file"] = row["confirmation_file"]
            send_log_row["send_confirmation_source_sha256"] = row["confirmation_sha256"]
            send_log_row["sent_bundle_sha256"] = row["attachment_bundle_sha256"]
            send_log_row["notes"] = append_note(
                send_log_row.get("notes", ""),
                f"auto_intake_from={row['confirmation_file']}",
            )
            applied_candidate_ids.add(candidate_id)
            row["applied_to_send_log"] = "true"
        elif row["intake_status"] == "ready_to_apply" and candidate_id in applied_candidate_ids:
            row["intake_status"] = "duplicate_ready_confirmation_not_applied"
        intake_rows.append(row)

    write_csv(profile.csv_out, SEND_LOG_FIELDS, rows)
    if intake_csv:
        write_csv(intake_csv, INTAKE_FIELDS, intake_rows)

    status_base = default_base(profile)
    applied_rows = sum(1 for row in intake_rows if row["applied_to_send_log"] == "true")
    ready_rows = sum(1 for row in intake_rows if row["intake_status"] == "ready_to_apply")
    review_rows = sum(1 for row in intake_rows if row["intake_status"].startswith("needs_manual_review"))
    unmatched_rows = sum(1 for row in intake_rows if row["intake_status"] == "unmatched_confirmation_file")
    if not intake_rows:
        status = f"{status_base}_waiting_for_confirmation_files"
    elif applied_rows and not review_rows and not unmatched_rows:
        status = f"{status_base}_applied"
    elif applied_rows:
        status = f"{status_base}_applied_with_review_items"
    else:
        status = f"{status_base}_needs_review"

    return {
        "status": status,
        "profile": profile.key,
        "label": profile.label,
        "purpose": "Scan original RFQ send confirmations and conservatively auto-fill send-log rows only when a sent .eml proves the expected bundle attachment.",
        "send_confirmation_dir": rel(profile.confirmation_dir),
        "send_log_csv": rel(profile.csv_out),
        "intake_csv": rel(intake_csv) if intake_csv else "",
        "row_count": len(intake_rows),
        "applied_rows": applied_rows,
        "ready_to_apply_rows": ready_rows,
        "needs_review_rows": review_rows,
        "unmatched_rows": unmatched_rows,
        "bundle_hash_matched_rows": sum(1 for row in intake_rows if row["bundle_hash_match"] == "true"),
        "unknown_existing_rows": unknown_existing,
        "tracker_field_count": len(tracker_fields),
        "rows": intake_rows,
        "boundary": NON_EVIDENCE_BOUNDARY,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['label']} RFQ Send Confirmation Intake",
        "",
        "This report scans original RFQ send confirmations. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Send confirmation directory:** `{result['send_confirmation_dir']}`",
        f"**Send log CSV:** `{result['send_log_csv']}`",
        f"**Intake CSV:** `{result['intake_csv']}`",
        f"**Files scanned:** {result['row_count']}",
        f"**Applied rows:** {result['applied_rows']}",
        f"**Needs review:** {result['needs_review_rows']}",
        f"**Unmatched:** {result['unmatched_rows']}",
        f"**Bundle hash matched:** {result['bundle_hash_matched_rows']}",
        "",
        "## Intake Rows",
        "",
        "| Candidate | File | Status | Bundle match | Applied |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['candidate_id'] or '-'}` | `{row['confirmation_file']}` | "
            f"`{row['intake_status']}` | `{row['bundle_hash_match']}` | `{row['applied_to_send_log']}` |"
        )
    lines.extend([
        "",
        "## Auto-Apply Rule",
        "",
        "A confirmation is auto-applied only when it is a sent `.eml`, maps to a known candidate, has From/To/Date/Message-ID headers, and includes a zip attachment whose SHA-256 matches the RFQ outbox bundle.",
        "",
        "Other confirmation files remain review items; they can still be used by filling the send log manually.",
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
    ])
    return "\n".join(lines)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Intake LIMINA RFQ send confirmations.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="h_a")
    parser.add_argument("--csv-out", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--report", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    profile = PROFILES[args.profile]
    csv_out = args.csv_out or default_csv(profile)
    json_out = args.json_out or default_json(profile)
    report = args.report or default_report(profile)
    result = build_result(profile, csv_out)
    write_json(json_out, result)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(result), encoding="utf-8")
    print(f"{profile.label} RFQ send confirmation intake: {result['status']}")
    print(f"Files scanned: {result['row_count']}")
    print(f"Applied rows: {result['applied_rows']}")
    print(f"Needs review: {result['needs_review_rows']}")
    print(f"Wrote {csv_out}")
    print(f"Wrote {json_out}")
    print(f"Wrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
