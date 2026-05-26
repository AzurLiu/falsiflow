#!/usr/bin/env python3
"""Render and apply RFQ send logs without treating outreach as evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Profile:
    key: str
    label: str
    contacts: Path
    outbox: Path
    tracker: Path
    confirmation_dir: Path
    csv_out: Path
    json_out: Path
    report: Path
    status_prefix: str


PROFILES = {
    "h_a": Profile(
        key="h_a",
        label="NHI-PEDOT H-A",
        contacts=ROOT / "data" / "nhi_pedot_h_a_vendor_contact_channels.json",
        outbox=ROOT / "data" / "nhi_pedot_h_a_rfq_outbox_manifest.json",
        tracker=ROOT / "data" / "nhi_pedot_h_a_quote_tracker.csv",
        confirmation_dir=ROOT / "data" / "rfq_send_confirmation_files" / "h_a",
        csv_out=ROOT / "data" / "nhi_pedot_h_a_rfq_send_log.csv",
        json_out=ROOT / "data" / "nhi_pedot_h_a_rfq_send_log.json",
        report=ROOT / "reports" / "nhi_pedot_h_a_rfq_send_log.md",
        status_prefix="nhi_pedot_h_a_rfq_send_log",
    ),
    "zrc_phase_a": Profile(
        key="zrc_phase_a",
        label="ZRC-ND Phase A",
        contacts=ROOT / "data" / "zrc_nd_phase_a_vendor_contact_channels.json",
        outbox=ROOT / "data" / "zrc_nd_phase_a_rfq_outbox_manifest.json",
        tracker=ROOT / "data" / "zrc_nd_phase_a_quote_tracker.csv",
        confirmation_dir=ROOT / "data" / "rfq_send_confirmation_files" / "zrc_phase_a",
        csv_out=ROOT / "data" / "zrc_nd_phase_a_rfq_send_log.csv",
        json_out=ROOT / "data" / "zrc_nd_phase_a_rfq_send_log.json",
        report=ROOT / "reports" / "zrc_nd_phase_a_rfq_send_log.md",
        status_prefix="zrc_nd_phase_a_rfq_send_log",
    ),
}


FIELDS = [
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

USER_FIELDS = {
    "send_status",
    "sent_at",
    "sent_by",
    "send_method",
    "recipient_or_form",
    "message_id_or_confirmation",
    "send_confirmation_source_file",
    "send_confirmation_source_sha256",
    "sent_bundle_sha256",
    "notes",
}

SENT = {"sent", "submitted", "emailed", "form_submitted"}
NON_SENT = {"", "pending_send", "needs_attention", "do_not_send", "paused"}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def workspace_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


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


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_confirmation_readme(profile: Profile) -> Path:
    profile.confirmation_dir.mkdir(parents=True, exist_ok=True)
    path = profile.confirmation_dir / "README.md"
    text = "\n".join([
        f"# {profile.label} RFQ Send Confirmation Files",
        "",
        "Place original RFQ send confirmations here: sent-email exports, web-form confirmation PDFs, screenshots, or saved confirmation pages.",
        "These files document outreach logistics only. They are not material measurement evidence.",
        "",
        "After adding a confirmation file, fill the matching row in the RFQ send log and rerun:",
        "",
        "```bash",
        f"python3 scripts/apply_limina_rfq_send_log.py --profile {profile.key}",
        "python3 scripts/run_limina_iteration.py",
        "```",
        "",
    ])
    if not path.exists():
        path.write_text(text, encoding="utf-8")
    return path


def contact_by_candidate(contacts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row.get("candidate_id", ""): row
        for row in contacts.get("contacts", [])
        if row.get("candidate_id")
    }


def outbox_by_candidate(outbox: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row.get("candidate_id", ""): row
        for row in outbox.get("rows", [])
        if row.get("candidate_id")
    }


def tracker_by_candidate(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("candidate_id", ""): row for row in rows if row.get("candidate_id")}


def existing_log_by_candidate(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("candidate_id", ""): row for row in rows if row.get("candidate_id")}


def default_recipient(contact: dict[str, Any], outbox_row: dict[str, Any]) -> str:
    return (
        contact.get("primary_email")
        or contact.get("quote_url")
        or contact.get("contact_url")
        or outbox_row.get("contact_url")
        or ""
    )


def confirmation_file_default(profile: Profile, candidate_id: str) -> str:
    return rel(profile.confirmation_dir / f"{candidate_id}_send_confirmation.txt")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_log_rows(
    profile: Profile,
    contacts: dict[str, Any],
    outbox: dict[str, Any],
    tracker: dict[str, dict[str, str]],
    existing: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    contacts_by_id = contact_by_candidate(contacts)
    outbox_rows = outbox_by_candidate(outbox)
    rows = []
    for candidate_id, outbox_row in outbox_rows.items():
        contact = contacts_by_id.get(candidate_id, {})
        tracker_row = tracker.get(candidate_id, {})
        prior = existing.get(candidate_id, {})
        row = {
            "candidate_id": candidate_id,
            "vendor_name": outbox_row.get("vendor_name") or contact.get("vendor_name", ""),
            "wave": contact.get("wave", "first_wave"),
            "send_status": "pending_send",
            "sent_at": "",
            "sent_by": "",
            "send_method": contact.get("primary_send_method", ""),
            "recipient_or_form": default_recipient(contact, outbox_row),
            "message_id_or_confirmation": "",
            "send_confirmation_source_file": confirmation_file_default(profile, candidate_id),
            "send_confirmation_source_sha256": "",
            "computed_send_confirmation_source_sha256": "",
            "sent_bundle_sha256": "",
            "email_file": outbox_row.get("email_file", ""),
            "bundle_zip": outbox_row.get("bundle_zip", ""),
            "expected_bundle_sha256": outbox_row.get("bundle_sha256", ""),
            "attachment_count": str(outbox_row.get("attachment_count", "")),
            "tracker_contact_date": tracker_row.get("contact_date", ""),
            "tracker_reply_date": tracker_row.get("reply_date", ""),
            "tracker_decision": tracker_row.get("decision", ""),
            "notes": "",
        }
        for field in USER_FIELDS:
            if prior.get(field, "").strip():
                row[field] = prior[field]
        source = row.get("send_confirmation_source_file", "").strip()
        if source:
            source_path = workspace_path(source)
            if source_path.exists() and source_path.is_file():
                row["computed_send_confirmation_source_sha256"] = sha256_file(source_path)
        rows.append(row)

    known_ids = set(outbox_rows)
    unknown_existing = [
        row for candidate_id, row in existing.items()
        if candidate_id not in known_ids
    ]
    return rows, unknown_existing


def normalized_status(row: dict[str, str]) -> str:
    return row.get("send_status", "").strip().lower().replace(" ", "_").replace("-", "_")


def contact_date(sent_at: str) -> str:
    value = sent_at.strip()
    if len(value) >= 10 and value[4:5] == "-" and value[7:8] == "-":
        return value[:10]
    return value


def validate_sent_row(row: dict[str, str], tracker: dict[str, dict[str, str]]) -> list[str]:
    errors = []
    for field in [
        "sent_at",
        "sent_by",
        "send_method",
        "recipient_or_form",
        "message_id_or_confirmation",
        "send_confirmation_source_file",
    ]:
        if not row.get(field, "").strip():
            errors.append(f"{field}=missing")
    source = row.get("send_confirmation_source_file", "").strip()
    if source:
        source_path = workspace_path(source)
        if not source_path.exists() or not source_path.is_file():
            errors.append("send_confirmation_source_file=missing")
        else:
            computed = sha256_file(source_path)
            supplied = row.get("send_confirmation_source_sha256", "").strip()
            if supplied and supplied != computed:
                errors.append("send_confirmation_source_sha256=mismatch")
    if not row.get("expected_bundle_sha256", "").strip():
        errors.append("expected_bundle_sha256=missing")
    sent_hash = row.get("sent_bundle_sha256", "").strip()
    expected_hash = row.get("expected_bundle_sha256", "").strip()
    if sent_hash and expected_hash and sent_hash != expected_hash:
        errors.append("sent_bundle_sha256=mismatch")
    if row.get("email_file", "").strip() and not workspace_path(row["email_file"]).exists():
        errors.append("email_file=missing")
    if row.get("bundle_zip", "").strip() and not workspace_path(row["bundle_zip"]).exists():
        errors.append("bundle_zip=missing")
    if row.get("candidate_id", "") not in tracker:
        errors.append("tracker_row=missing")
    return errors


def update_tracker(
    tracker_path: Path,
    tracker_fields: list[str],
    tracker_rows: list[dict[str, str]],
    sent_rows: list[dict[str, str]],
) -> tuple[int, list[dict[str, str]]]:
    tracker = tracker_by_candidate(tracker_rows)
    updated = 0
    warnings = []
    for row in sent_rows:
        candidate_id = row["candidate_id"]
        tracker_row = tracker.get(candidate_id)
        if not tracker_row:
            continue
        new_date = contact_date(row.get("sent_at", ""))
        old_date = tracker_row.get("contact_date", "").strip()
        if not old_date:
            tracker_row["contact_date"] = new_date
            updated += 1
        elif old_date != new_date:
            warnings.append({
                "candidate_id": candidate_id,
                "issue": "tracker_contact_date_differs_from_send_log",
                "tracker_contact_date": old_date,
                "send_log_contact_date": new_date,
            })
    if updated:
        write_csv(tracker_path, tracker_fields, tracker_rows)
    return updated, warnings


def build_result(profile: Profile) -> dict[str, Any]:
    readme = write_confirmation_readme(profile)
    contacts = load_json(profile.contacts)
    outbox = load_json(profile.outbox)
    tracker_fields, tracker_rows_raw = load_csv(profile.tracker)
    existing_fields, existing_rows_raw = load_csv(profile.csv_out)
    tracker = tracker_by_candidate(tracker_rows_raw)
    rows, unknown_existing = build_log_rows(
        profile,
        contacts,
        outbox,
        tracker,
        existing_log_by_candidate(existing_rows_raw),
    )
    write_csv(profile.csv_out, FIELDS, rows)

    errors = []
    valid_sent_rows = []
    pending_count = 0
    for row in rows:
        status = normalized_status(row)
        if status in SENT:
            row_errors = validate_sent_row(row, tracker)
            if row_errors:
                errors.append({
                    "candidate_id": row["candidate_id"],
                    "vendor_name": row["vendor_name"],
                    "errors": row_errors,
                })
            else:
                valid_sent_rows.append(row)
        elif status in NON_SENT:
            pending_count += 1
        else:
            errors.append({
                "candidate_id": row["candidate_id"],
                "vendor_name": row["vendor_name"],
                "errors": [f"send_status=unrecognized:{row.get('send_status', '')}"],
            })

    updated, warnings = (0, [])
    if not errors and valid_sent_rows and tracker_fields and "contact_date" in tracker_fields:
        updated, warnings = update_tracker(profile.tracker, tracker_fields, tracker_rows_raw, valid_sent_rows)
    elif valid_sent_rows and "contact_date" not in tracker_fields:
        errors.append({
            "candidate_id": "",
            "vendor_name": "",
            "errors": ["tracker_contact_date_column=missing"],
        })

    if errors:
        status = f"{profile.status_prefix}_has_errors"
    elif updated:
        status = f"{profile.status_prefix}_applied"
    elif valid_sent_rows:
        status = f"{profile.status_prefix}_sent_rows_already_reflected"
    else:
        status = f"{profile.status_prefix}_waiting_for_sent_entries"

    return {
        "status": status,
        "profile": profile.key,
        "label": profile.label,
        "purpose": "Track real RFQ send confirmations and safely apply verified send dates to the quote tracker.",
        "send_log_csv": rel(profile.csv_out),
        "send_confirmation_dir": rel(profile.confirmation_dir),
        "send_confirmation_readme": rel(readme),
        "tracker_csv": rel(profile.tracker),
        "row_count": len(rows),
        "pending_rows": pending_count,
        "sent_rows": sum(1 for row in rows if normalized_status(row) in SENT),
        "valid_sent_rows": len(valid_sent_rows),
        "valid_sent_candidate_ids": [row["candidate_id"] for row in valid_sent_rows],
        "valid_sent_summaries": [
            {
                "candidate_id": row["candidate_id"],
                "vendor_name": row["vendor_name"],
                "sent_at": row.get("sent_at", ""),
                "send_method": row.get("send_method", ""),
                "recipient_or_form": row.get("recipient_or_form", ""),
                "message_id_or_confirmation": row.get("message_id_or_confirmation", ""),
                "send_confirmation_source_file": row.get("send_confirmation_source_file", ""),
                "computed_send_confirmation_source_sha256": row.get("computed_send_confirmation_source_sha256", ""),
                "bundle_zip": row.get("bundle_zip", ""),
                "sent_bundle_sha256": row.get("sent_bundle_sha256", ""),
            }
            for row in valid_sent_rows
        ],
        "applied_tracker_contact_dates": updated,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "unknown_existing_rows": unknown_existing,
        "field_contract": {
            "send_status_values": sorted(SENT | {value for value in NON_SENT if value}),
            "required_when_sent": [
                "sent_at",
                "sent_by",
                "send_method",
                "recipient_or_form",
                "message_id_or_confirmation",
                "send_confirmation_source_file",
            ],
            "hash_rule": "If sent_bundle_sha256 is supplied, it must match expected_bundle_sha256 from the RFQ outbox manifest.",
            "confirmation_hash_rule": "If send_confirmation_source_sha256 is supplied, it must match the current SHA-256 of send_confirmation_source_file.",
        },
        "non_evidence_boundary": (
            "RFQ send logs and quote trackers only document execution logistics. "
            "They are not material evidence and cannot advance suitability gates without returned measured rows."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['label']} RFQ Send Log",
        "",
        "This report validates RFQ send confirmations. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Send log CSV:** `{result['send_log_csv']}`",
        f"**Send confirmation directory:** `{result['send_confirmation_dir']}`",
        f"**Tracker CSV:** `{result['tracker_csv']}`",
        f"**Rows:** {result['row_count']}",
        f"**Pending rows:** {result['pending_rows']}",
        f"**Sent rows:** {result['sent_rows']}",
        f"**Valid sent rows:** {result['valid_sent_rows']}",
        f"**Applied tracker contact dates:** {result['applied_tracker_contact_dates']}",
        f"**Errors:** {result['error_count']}",
        f"**Warnings:** {result['warning_count']}",
        "",
        "## Required When Sent",
        "",
    ]
    lines.extend(f"- `{field}`" for field in result["field_contract"]["required_when_sent"])
    if result["valid_sent_summaries"]:
        lines.extend([
            "",
            "## Valid Sent Rows",
            "",
            "| Candidate | Vendor | Sent at | Method | Confirmation source |",
            "| --- | --- | --- | --- | --- |",
        ])
        for row in result["valid_sent_summaries"]:
            lines.append(
                f"| `{row['candidate_id']}` | {row['vendor_name']} | "
                f"{row['sent_at']} | {row['send_method']} | `{row['send_confirmation_source_file']}` |"
            )
    lines.extend([
        "",
        "## Send Status Values",
        "",
    ])
    lines.extend(f"- `{value}`" for value in result["field_contract"]["send_status_values"])
    if result["errors"]:
        lines.extend([
            "",
            "## Errors",
            "",
        ])
        for row in result["errors"]:
            lines.append(
                f"- `{row.get('candidate_id', '-')}` {row.get('vendor_name', '-')}: "
                + ", ".join(f"`{item}`" for item in row.get("errors", []))
            )
    if result["warnings"]:
        lines.extend([
            "",
            "## Warnings",
            "",
        ])
        for row in result["warnings"]:
            lines.append(
                f"- `{row.get('candidate_id', '-')}`: `{row.get('issue', '-')}` "
                f"tracker={row.get('tracker_contact_date', '-')} log={row.get('send_log_contact_date', '-')}"
            )
    lines.extend([
        "",
        "## Next Step",
        "",
        "Fill a row as `sent` only after a real email/form submission has been made and an original confirmation file has been saved. Rerun this script, then rerun the iteration.",
        "",
        "## Boundary",
        "",
        result["non_evidence_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render/apply LIMINA RFQ send logs.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="h_a")
    parser.add_argument("--csv-out", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--report", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    base = PROFILES[args.profile]
    profile = Profile(
        key=base.key,
        label=base.label,
        contacts=base.contacts,
        outbox=base.outbox,
        tracker=base.tracker,
        confirmation_dir=base.confirmation_dir,
        csv_out=args.csv_out or base.csv_out,
        json_out=args.json_out or base.json_out,
        report=args.report or base.report,
        status_prefix=base.status_prefix,
    )
    result = build_result(profile)
    profile.json_out.parent.mkdir(parents=True, exist_ok=True)
    profile.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    profile.report.parent.mkdir(parents=True, exist_ok=True)
    profile.report.write_text(render_report(result), encoding="utf-8")
    print(f"{profile.label} RFQ send log: {result['status']}")
    print(f"Rows: {result['row_count']}")
    print(f"Sent rows: {result['sent_rows']}")
    print(f"Applied tracker contact dates: {result['applied_tracker_contact_dates']}")
    print(f"Errors: {result['error_count']}")
    print(f"Wrote {profile.csv_out}")
    print(f"Wrote {profile.json_out}")
    print(f"Wrote {profile.report}")
    return 0 if result["error_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
