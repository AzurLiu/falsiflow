#!/usr/bin/env python3
"""Intake original RFQ reply files into reply logs without scoring them."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path
from typing import Any

from apply_limina_rfq_reply_log import (
    PROFILES,
    Profile,
    build_rows,
    by_candidate,
    fields_for,
    load_csv,
    normalize,
    rel,
    write_csv,
)


ROOT = Path(__file__).resolve().parents[1]
INTAKE_FIELDS = [
    "candidate_id",
    "vendor_name",
    "reply_file",
    "reply_sha256",
    "detected_by",
    "file_type",
    "from_address",
    "to_address",
    "subject",
    "reply_at",
    "message_id_or_reference",
    "send_verified",
    "intake_status",
    "applied_to_reply_log",
    "boundary",
]

SENT_STATUSES = {"sent", "submitted", "emailed", "form_submitted"}
PENDING_REPLY_STATUSES = {"", "awaiting_reply", "pending_reply", "not_sent_yet", "no_reply"}
NON_EVIDENCE_BOUNDARY = (
    "RFQ replies and quotes document sourcing and execution selection only. They are not "
    "material measurement evidence and cannot advance suitability gates without returned measured rows."
)


def clean(value: Any) -> str:
    return str(value or "").strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def default_base(profile: Profile) -> str:
    if profile.status_prefix.endswith("_reply_log"):
        return profile.status_prefix.removesuffix("_reply_log") + "_reply_intake"
    return profile.status_prefix + "_intake"


def default_csv(profile: Profile) -> Path:
    return ROOT / "data" / f"{default_base(profile)}.csv"


def default_json(profile: Profile) -> Path:
    return ROOT / "data" / f"{default_base(profile)}.json"


def default_report(profile: Profile) -> Path:
    return ROOT / "reports" / f"{default_base(profile)}.md"


def iter_reply_files(directory: Path) -> list[Path]:
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


def parse_sender(raw: str) -> str:
    name, address = parseaddr(raw)
    if name and address:
        return f"{name} <{address}>"
    return address or raw


def send_verified(send_row: dict[str, str], tracker_row: dict[str, str]) -> bool:
    status = normalize(send_row.get("send_status", ""))
    return status in SENT_STATUSES and bool(
        clean(send_row.get("computed_send_confirmation_source_sha256"))
        or clean(tracker_row.get("contact_date"))
    )


def detect_candidate(path: Path, message, candidate_ids: set[str], tracker: dict[str, dict[str, str]]) -> tuple[str, str]:
    header = clean(message.get("X-LIMINA-Candidate-ID")) if message is not None else ""
    if header in candidate_ids:
        return header, "x_limina_candidate_id"
    name = path.stem.lower()
    for candidate_id in sorted(candidate_ids, key=len, reverse=True):
        if candidate_id.lower() in name:
            return candidate_id, "filename"
    subject = clean(message.get("Subject")) if message is not None else ""
    if subject:
        lowered = subject.lower()
        for candidate_id, row in tracker.items():
            vendor = clean(row.get("vendor_name")).lower()
            if vendor and vendor in lowered:
                return candidate_id, "subject_vendor_name"
    return "", "unmatched"


def reply_pending(row: dict[str, str]) -> bool:
    return normalize(row.get("reply_status", "")) in PENDING_REPLY_STATUSES


def intake_status(row: dict[str, str], message, candidate_id: str, send_ok: bool) -> str:
    if not candidate_id:
        return "unmatched_reply_file"
    if message is None:
        return "needs_manual_review_non_eml_reply"
    missing = [
        field for field in ["from_address", "reply_at", "message_id_or_reference"]
        if not clean(row.get(field))
    ]
    if missing:
        return "needs_manual_review_missing_" + "_".join(missing)
    if not send_ok:
        return "needs_verified_send_before_reply_apply"
    return "ready_to_register_for_review"


def build_result(profile: Profile, intake_csv: Path | None = None) -> dict[str, Any]:
    tracker_fields, tracker_rows_raw = load_csv(profile.tracker)
    _send_fields, send_rows_raw = load_csv(profile.send_log)
    _prior_fields, prior_rows_raw = load_csv(profile.csv_out)
    tracker = by_candidate(tracker_rows_raw)
    send_by_id = by_candidate(send_rows_raw)
    prior = by_candidate(prior_rows_raw)
    rows = build_rows(profile, tracker, prior)
    rows_by_id = by_candidate(rows)
    candidate_ids = set(rows_by_id)
    intake_rows: list[dict[str, str]] = []
    applied_candidate_ids: set[str] = set()

    for path in iter_reply_files(profile.reply_dir):
        message = parse_email(path)
        candidate_id, detected_by = detect_candidate(path, message, candidate_ids, tracker)
        tracker_row = tracker.get(candidate_id, {})
        send_row = send_by_id.get(candidate_id, {})
        send_ok = send_verified(send_row, tracker_row)
        file_hash = sha256_file(path)
        row = {
            "candidate_id": candidate_id,
            "vendor_name": clean(tracker_row.get("vendor_name")) or clean(rows_by_id.get(candidate_id, {}).get("vendor_name")),
            "reply_file": rel(path),
            "reply_sha256": file_hash,
            "detected_by": detected_by,
            "file_type": path.suffix.lower().lstrip(".") or "unknown",
            "from_address": parse_sender(clean(message.get("From"))) if message is not None else "",
            "to_address": clean(message.get("To")) if message is not None else "",
            "subject": clean(message.get("Subject")) if message is not None else "",
            "reply_at": parse_date(clean(message.get("Date")) if message is not None else ""),
            "message_id_or_reference": clean(message.get("Message-ID")) if message is not None else "",
            "send_verified": str(send_ok).lower(),
            "intake_status": "",
            "applied_to_reply_log": "false",
            "boundary": NON_EVIDENCE_BOUNDARY,
        }
        row["intake_status"] = intake_status(row, message, candidate_id, send_ok)
        reply_row = rows_by_id.get(candidate_id)
        if (
            row["intake_status"] == "ready_to_register_for_review"
            and reply_row is not None
            and candidate_id not in applied_candidate_ids
            and reply_pending(reply_row)
        ):
            reply_row["reply_status"] = "clarification_received"
            reply_row["reply_at"] = row["reply_at"]
            reply_row["responder_name"] = row["from_address"]
            reply_row["quote_id_or_reference"] = row["message_id_or_reference"] or row["subject"]
            reply_row["reply_source_file"] = row["reply_file"]
            reply_row["reply_source_sha256"] = row["reply_sha256"]
            reply_row["notes"] = clean(reply_row.get("notes")) or "auto_intake_pending_human_review"
            applied_candidate_ids.add(candidate_id)
            row["applied_to_reply_log"] = "true"
        elif row["intake_status"] == "ready_to_register_for_review" and candidate_id in applied_candidate_ids:
            row["intake_status"] = "duplicate_ready_reply_not_applied"
        elif row["intake_status"] == "ready_to_register_for_review" and reply_row is not None and not reply_pending(reply_row):
            row["intake_status"] = "reply_log_already_has_non_pending_status"
        intake_rows.append(row)

    write_csv(profile.csv_out, fields_for(profile), rows)
    if intake_csv:
        write_csv(intake_csv, INTAKE_FIELDS, intake_rows)

    status_base = default_base(profile)
    applied_rows = sum(1 for row in intake_rows if row["applied_to_reply_log"] == "true")
    ready_rows = sum(1 for row in intake_rows if row["intake_status"] == "ready_to_register_for_review")
    review_rows = sum(1 for row in intake_rows if row["intake_status"].startswith("needs_manual_review"))
    unmatched_rows = sum(1 for row in intake_rows if row["intake_status"] == "unmatched_reply_file")
    needs_send_rows = sum(1 for row in intake_rows if row["intake_status"] == "needs_verified_send_before_reply_apply")
    if not intake_rows:
        status = f"{status_base}_waiting_for_reply_files"
    elif applied_rows and not review_rows and not unmatched_rows and not needs_send_rows:
        status = f"{status_base}_registered_for_review"
    elif applied_rows:
        status = f"{status_base}_registered_with_review_items"
    else:
        status = f"{status_base}_needs_review"

    return {
        "status": status,
        "profile": profile.key,
        "label": profile.label,
        "purpose": "Scan original RFQ reply files and conservatively register sent EML replies for human review without scoring or selecting providers.",
        "reply_file_dir": rel(profile.reply_dir),
        "reply_log_csv": rel(profile.csv_out),
        "intake_csv": rel(intake_csv) if intake_csv else "",
        "row_count": len(intake_rows),
        "applied_rows": applied_rows,
        "ready_to_register_rows": ready_rows,
        "needs_manual_review_rows": review_rows,
        "needs_verified_send_rows": needs_send_rows,
        "unmatched_rows": unmatched_rows,
        "tracker_field_count": len(tracker_fields),
        "rows": intake_rows,
        "boundary": NON_EVIDENCE_BOUNDARY,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['label']} RFQ Reply Intake",
        "",
        "This report scans original RFQ reply files. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Reply directory:** `{result['reply_file_dir']}`",
        f"**Reply log CSV:** `{result['reply_log_csv']}`",
        f"**Intake CSV:** `{result['intake_csv']}`",
        f"**Files scanned:** {result['row_count']}",
        f"**Applied rows:** {result['applied_rows']}",
        f"**Needs manual review:** {result['needs_manual_review_rows']}",
        f"**Needs verified send:** {result['needs_verified_send_rows']}",
        f"**Unmatched:** {result['unmatched_rows']}",
        "",
        "## Intake Rows",
        "",
        "| Candidate | File | Status | Send verified | Applied |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['candidate_id'] or '-'}` | `{row['reply_file']}` | "
            f"`{row['intake_status']}` | `{row['send_verified']}` | `{row['applied_to_reply_log']}` |"
        )
    lines.extend([
        "",
        "## Auto-Register Rule",
        "",
        "A reply is auto-registered only when it is a parsable `.eml`, maps to a known candidate, includes From/Date/Message-ID headers, and the matching RFQ send is verified.",
        "",
        "Registered replies are marked `clarification_received` for human review; review fields, scoring, shortlist, and provider selection remain manual/source-backed steps.",
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
    parser = argparse.ArgumentParser(description="Intake LIMINA RFQ replies.")
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
    print(f"{profile.label} RFQ reply intake: {result['status']}")
    print(f"Files scanned: {result['row_count']}")
    print(f"Applied rows: {result['applied_rows']}")
    print(f"Needs manual review: {result['needs_manual_review_rows']}")
    print(f"Wrote {csv_out}")
    print(f"Wrote {json_out}")
    print(f"Wrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
