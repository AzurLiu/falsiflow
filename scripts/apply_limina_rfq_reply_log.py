#!/usr/bin/env python3
"""Render and apply source-backed RFQ reply logs."""

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
    tracker: Path
    send_log: Path
    reply_dir: Path
    csv_out: Path
    json_out: Path
    report: Path
    status_prefix: str
    review_fields: tuple[str, ...]
    hard_required_fields: tuple[str, ...]
    selected_decision: str


H_A_REVIEW_FIELDS = (
    "can_cover_full_h_a",
    "needs_split_scope",
    "run_id_level_raw_data",
    "media_physicochemical_coverage",
    "coupon_physical_coverage",
    "csv_schema_acceptance",
    "bundle_entry_sheet_acceptance",
    "sample_handling_fit",
    "non_glp_scope_control",
)

ZRC_REVIEW_FIELDS = (
    "can_cover_full_phase_a",
    "needs_split_scope",
    "run_id_level_raw_data",
    "phase_a_media_panel_coverage",
    "csv_schema_acceptance",
    "sample_handling_fit",
    "source_file_provenance",
    "non_glp_scope_control",
)


PROFILES = {
    "h_a": Profile(
        key="h_a",
        label="NHI-PEDOT H-A",
        tracker=ROOT / "data" / "nhi_pedot_h_a_quote_tracker.csv",
        send_log=ROOT / "data" / "nhi_pedot_h_a_rfq_send_log.csv",
        reply_dir=ROOT / "data" / "rfq_reply_files" / "h_a",
        csv_out=ROOT / "data" / "nhi_pedot_h_a_rfq_reply_log.csv",
        json_out=ROOT / "data" / "nhi_pedot_h_a_rfq_reply_log.json",
        report=ROOT / "reports" / "nhi_pedot_h_a_rfq_reply_log.md",
        status_prefix="nhi_pedot_h_a_rfq_reply_log",
        review_fields=H_A_REVIEW_FIELDS,
        hard_required_fields=(
            "run_id_level_raw_data",
            "csv_schema_acceptance",
            "sample_handling_fit",
            "non_glp_scope_control",
        ),
        selected_decision="selected_for_h_a",
    ),
    "zrc_phase_a": Profile(
        key="zrc_phase_a",
        label="ZRC-ND Phase A",
        tracker=ROOT / "data" / "zrc_nd_phase_a_quote_tracker.csv",
        send_log=ROOT / "data" / "zrc_nd_phase_a_rfq_send_log.csv",
        reply_dir=ROOT / "data" / "rfq_reply_files" / "zrc_phase_a",
        csv_out=ROOT / "data" / "zrc_nd_phase_a_rfq_reply_log.csv",
        json_out=ROOT / "data" / "zrc_nd_phase_a_rfq_reply_log.json",
        report=ROOT / "reports" / "zrc_nd_phase_a_rfq_reply_log.md",
        status_prefix="zrc_nd_phase_a_rfq_reply_log",
        review_fields=ZRC_REVIEW_FIELDS,
        hard_required_fields=(
            "run_id_level_raw_data",
            "csv_schema_acceptance",
            "sample_handling_fit",
            "source_file_provenance",
            "non_glp_scope_control",
        ),
        selected_decision="selected_for_phase_a",
    ),
}


BASE_FIELDS = [
    "candidate_id",
    "vendor_name",
    "reply_status",
    "reply_at",
    "responder_name",
    "quote_id_or_reference",
    "reply_source_file",
    "reply_source_sha256",
    "computed_reply_source_sha256",
]

TAIL_FIELDS = [
    "turnaround_days",
    "quoted_cost",
    "decision",
    "notes",
    "tracker_contact_date",
    "tracker_reply_date",
    "tracker_decision",
]

REPLY_RECEIVED = {"received", "reply_received", "quote_received"}
REPLY_DECLINED = {"declined", "cannot_quote", "out_of_scope"}
REPLY_CLARIFICATION = {"clarification_received", "needs_clarification"}
REPLY_PENDING = {"", "awaiting_reply", "pending_reply", "not_sent_yet", "no_reply"}
KNOWN_STATUS = REPLY_RECEIVED | REPLY_DECLINED | REPLY_CLARIFICATION | REPLY_PENDING


def fields_for(profile: Profile) -> list[str]:
    return [*BASE_FIELDS, *profile.review_fields, *TAIL_FIELDS]


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


def write_reply_readme(profile: Profile) -> Path:
    profile.reply_dir.mkdir(parents=True, exist_ok=True)
    path = profile.reply_dir / "README.md"
    text = "\n".join([
        f"# {profile.label} RFQ Reply Files",
        "",
        "Place original vendor/cooperator RFQ replies here: email exports, PDFs, quote forms, or saved web-form confirmations.",
        "These files document sourcing logistics only. They are not material measurement evidence.",
        "",
        "After adding a reply file, fill the matching row in the RFQ reply log and rerun:",
        "",
        "```bash",
        f"python3 scripts/apply_limina_rfq_reply_log.py --profile {profile.key}",
        "python3 scripts/run_limina_iteration.py",
        "```",
        "",
    ])
    if not path.exists():
        path.write_text(text, encoding="utf-8")
    return path


def by_candidate(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("candidate_id", ""): row for row in rows if row.get("candidate_id")}


def normalize(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def date_part(value: str) -> str:
    text = value.strip()
    if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
        return text[:10]
    return text


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reply_file_default(profile: Profile, candidate_id: str) -> str:
    return rel(profile.reply_dir / f"{candidate_id}_reply.txt")


def build_rows(profile: Profile, tracker: dict[str, dict[str, str]], prior: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    fields = fields_for(profile)
    for candidate_id, tracker_row in tracker.items():
        row = {field: "" for field in fields}
        row.update({
            "candidate_id": candidate_id,
            "vendor_name": tracker_row.get("vendor_name", ""),
            "reply_status": "awaiting_reply" if tracker_row.get("contact_date") else "not_sent_yet",
            "reply_source_file": reply_file_default(profile, candidate_id),
            "tracker_contact_date": tracker_row.get("contact_date", ""),
            "tracker_reply_date": tracker_row.get("reply_date", ""),
            "tracker_decision": tracker_row.get("decision", ""),
        })
        for field in [*BASE_FIELDS, *profile.review_fields, *TAIL_FIELDS]:
            value = prior.get(candidate_id, {}).get(field, "")
            if value.strip() and field not in {"computed_reply_source_sha256", "tracker_contact_date", "tracker_reply_date", "tracker_decision"}:
                row[field] = value
        source = row.get("reply_source_file", "").strip()
        if source:
            source_path = workspace_path(source)
            if source_path.exists() and source_path.is_file():
                row["computed_reply_source_sha256"] = sha256_file(source_path)
        rows.append(row)
    return rows


def row_has_received_status(row: dict[str, str]) -> bool:
    return normalize(row.get("reply_status", "")) in (REPLY_RECEIVED | REPLY_DECLINED | REPLY_CLARIFICATION)


def validate_reply_row(profile: Profile, row: dict[str, str], tracker: dict[str, dict[str, str]]) -> list[str]:
    errors = []
    status = normalize(row.get("reply_status", ""))
    if status not in KNOWN_STATUS:
        return [f"reply_status=unrecognized:{row.get('reply_status', '')}"]
    if status in REPLY_PENDING:
        return []
    if row.get("candidate_id", "") not in tracker:
        errors.append("tracker_row=missing")
    if not tracker.get(row.get("candidate_id", ""), {}).get("contact_date", "").strip():
        errors.append("tracker_contact_date=missing")
    for field in ["reply_at", "responder_name", "reply_source_file"]:
        if not row.get(field, "").strip():
            errors.append(f"{field}=missing")
    source = row.get("reply_source_file", "").strip()
    if source:
        source_path = workspace_path(source)
        if not source_path.exists() or not source_path.is_file():
            errors.append("reply_source_file=missing")
        else:
            computed = sha256_file(source_path)
            supplied = row.get("reply_source_sha256", "").strip()
            if supplied and supplied != computed:
                errors.append("reply_source_sha256=mismatch")
    if status in REPLY_RECEIVED:
        missing = [field for field in profile.review_fields if not row.get(field, "").strip()]
        if missing:
            errors.extend(f"{field}=missing" for field in missing)
    return errors


def prepared_tracker_updates(profile: Profile, row: dict[str, str]) -> dict[str, str]:
    status = normalize(row.get("reply_status", ""))
    updates: dict[str, str] = {
        "reply_date": date_part(row.get("reply_at", "")),
        "turnaround_days": row.get("turnaround_days", ""),
        "quoted_cost": row.get("quoted_cost", ""),
        "notes": row.get("notes", ""),
    }
    decision = row.get("decision", "").strip()
    if not decision:
        if status in REPLY_DECLINED:
            decision = "vendor_declined"
        elif status in REPLY_CLARIFICATION:
            decision = "needs_reply_clarification"
        else:
            decision = "reply_received_pending_review"
    updates["decision"] = decision
    for field in profile.review_fields:
        value = row.get(field, "").strip()
        if not value and status in REPLY_DECLINED:
            value = "no"
        updates[field] = value
    return updates


def update_tracker(
    profile: Profile,
    tracker_fields: list[str],
    tracker_rows: list[dict[str, str]],
    valid_rows: list[dict[str, str]],
) -> tuple[int, list[dict[str, str]], list[dict[str, str]]]:
    tracker = by_candidate(tracker_rows)
    changed = 0
    errors = []
    warnings = []
    required_update_fields = {"reply_date", "turnaround_days", "quoted_cost", "decision", "notes", *profile.review_fields}
    missing_columns = sorted(required_update_fields - set(tracker_fields))
    if missing_columns:
        return 0, [{"candidate_id": "", "vendor_name": "", "errors": [f"tracker_column_missing:{field}" for field in missing_columns]}], []
    for row in valid_rows:
        target = tracker.get(row["candidate_id"])
        if not target:
            continue
        updates = prepared_tracker_updates(profile, row)
        for field, new_value in updates.items():
            if not new_value:
                continue
            old_value = target.get(field, "")
            if old_value and old_value != new_value:
                warnings.append({
                    "candidate_id": row["candidate_id"],
                    "field": field,
                    "old_value": old_value,
                    "new_value": new_value,
                    "issue": "tracker_value_overwritten_by_source_backed_reply",
                })
            if old_value != new_value:
                target[field] = new_value
                changed += 1
    if changed:
        write_csv(profile.tracker, tracker_fields, tracker_rows)
    return changed, errors, warnings


def build_result(profile: Profile) -> dict[str, Any]:
    readme = write_reply_readme(profile)
    tracker_fields, tracker_rows_raw = load_csv(profile.tracker)
    _, prior_rows_raw = load_csv(profile.csv_out)
    tracker = by_candidate(tracker_rows_raw)
    rows = build_rows(profile, tracker, by_candidate(prior_rows_raw))
    fields = fields_for(profile)
    write_csv(profile.csv_out, fields, rows)

    errors = []
    valid_rows = []
    pending_count = 0
    received_count = 0
    for row in rows:
        status = normalize(row.get("reply_status", ""))
        if status in REPLY_PENDING:
            pending_count += 1
            continue
        if row_has_received_status(row):
            received_count += 1
        row_errors = validate_reply_row(profile, row, tracker)
        if row_errors:
            errors.append({
                "candidate_id": row.get("candidate_id", ""),
                "vendor_name": row.get("vendor_name", ""),
                "errors": row_errors,
            })
        else:
            valid_rows.append(row)

    applied, update_errors, warnings = (0, [], [])
    if not errors and valid_rows:
        applied, update_errors, warnings = update_tracker(profile, tracker_fields, tracker_rows_raw, valid_rows)
        errors.extend(update_errors)

    if errors:
        status = f"{profile.status_prefix}_has_errors"
    elif applied:
        status = f"{profile.status_prefix}_applied"
    elif valid_rows:
        status = f"{profile.status_prefix}_replies_already_reflected"
    else:
        status = f"{profile.status_prefix}_waiting_for_reply_files"

    return {
        "status": status,
        "profile": profile.key,
        "label": profile.label,
        "purpose": "Track source-backed RFQ replies and safely apply parsed reply fields to the quote tracker.",
        "reply_log_csv": rel(profile.csv_out),
        "reply_file_dir": rel(profile.reply_dir),
        "reply_file_readme": rel(readme),
        "tracker_csv": rel(profile.tracker),
        "row_count": len(rows),
        "pending_rows": pending_count,
        "received_rows": received_count,
        "valid_reply_rows": len(valid_rows),
        "valid_reply_candidate_ids": [row["candidate_id"] for row in valid_rows],
        "valid_reply_summaries": [
            {
                "candidate_id": row["candidate_id"],
                "vendor_name": row["vendor_name"],
                "reply_status": row.get("reply_status", ""),
                "reply_at": row.get("reply_at", ""),
                "reply_source_file": row.get("reply_source_file", ""),
                "computed_reply_source_sha256": row.get("computed_reply_source_sha256", ""),
            }
            for row in valid_rows
        ],
        "applied_tracker_field_updates": applied,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "review_fields": list(profile.review_fields),
        "hard_required_fields": list(profile.hard_required_fields),
        "field_contract": {
            "reply_status_values": sorted(KNOWN_STATUS - {""}),
            "required_when_received": ["reply_at", "responder_name", "reply_source_file", *profile.review_fields],
            "required_when_declined": ["reply_at", "responder_name", "reply_source_file"],
            "hash_rule": "If reply_source_sha256 is supplied, it must match the current SHA-256 of reply_source_file.",
        },
        "non_evidence_boundary": (
            "RFQ reply logs and quote trackers document sourcing and execution selection only. "
            "They are not material evidence and cannot advance suitability gates without returned measured rows."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['label']} RFQ Reply Log",
        "",
        "This report validates source-backed RFQ replies. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Reply log CSV:** `{result['reply_log_csv']}`",
        f"**Reply file directory:** `{result['reply_file_dir']}`",
        f"**Tracker CSV:** `{result['tracker_csv']}`",
        f"**Rows:** {result['row_count']}",
        f"**Pending rows:** {result['pending_rows']}",
        f"**Received rows:** {result['received_rows']}",
        f"**Valid reply rows:** {result['valid_reply_rows']}",
        f"**Applied tracker field updates:** {result['applied_tracker_field_updates']}",
        f"**Errors:** {result['error_count']}",
        f"**Warnings:** {result['warning_count']}",
        "",
        "## Required When Received",
        "",
    ]
    lines.extend(f"- `{field}`" for field in result["field_contract"]["required_when_received"])
    lines.extend(["", "## Reply Status Values", ""])
    lines.extend(f"- `{value}`" for value in result["field_contract"]["reply_status_values"])
    if result["errors"]:
        lines.extend(["", "## Errors", ""])
        for row in result["errors"]:
            lines.append(
                f"- `{row.get('candidate_id', '-')}` {row.get('vendor_name', '-')}: "
                + ", ".join(f"`{item}`" for item in row.get("errors", []))
            )
    if result["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for row in result["warnings"]:
            lines.append(
                f"- `{row.get('candidate_id', '-')}` `{row.get('field', '-')}`: "
                f"{row.get('old_value', '-')} -> {row.get('new_value', '-')}"
            )
    lines.extend([
        "",
        "## Next Step",
        "",
        "After a real RFQ reply arrives, save the original reply file in the reply directory, fill the matching row, rerun this script, then rerun the iteration.",
        "",
        "## Boundary",
        "",
        result["non_evidence_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render/apply LIMINA RFQ reply logs.")
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
        tracker=base.tracker,
        send_log=base.send_log,
        reply_dir=base.reply_dir,
        csv_out=args.csv_out or base.csv_out,
        json_out=args.json_out or base.json_out,
        report=args.report or base.report,
        status_prefix=base.status_prefix,
        review_fields=base.review_fields,
        hard_required_fields=base.hard_required_fields,
        selected_decision=base.selected_decision,
    )
    result = build_result(profile)
    profile.json_out.parent.mkdir(parents=True, exist_ok=True)
    profile.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    profile.report.parent.mkdir(parents=True, exist_ok=True)
    profile.report.write_text(render_report(result), encoding="utf-8")
    print(f"{profile.label} RFQ reply log: {result['status']}")
    print(f"Rows: {result['row_count']}")
    print(f"Received rows: {result['received_rows']}")
    print(f"Applied tracker field updates: {result['applied_tracker_field_updates']}")
    print(f"Errors: {result['error_count']}")
    print(f"Wrote {profile.csv_out}")
    print(f"Wrote {profile.json_out}")
    print(f"Wrote {profile.report}")
    return 0 if result["error_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
