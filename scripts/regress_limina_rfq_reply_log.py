#!/usr/bin/env python3
"""Regression checks for source-backed RFQ reply-log application."""

from __future__ import annotations

import csv
import json
import shutil
import tempfile
from pathlib import Path

from apply_limina_rfq_reply_log import H_A_REVIEW_FIELDS, Profile, build_result


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_rfq_reply_log_regression.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_rfq_reply_log_regression.md"


TRACKER_FIELDS = [
    "candidate_id",
    "vendor_name",
    "contact_date",
    "reply_date",
    *H_A_REVIEW_FIELDS,
    "turnaround_days",
    "quoted_cost",
    "decision",
    "notes",
]


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def make_profile(base: Path) -> Profile:
    return Profile(
        key="regression",
        label="RFQ Reply Log Regression",
        tracker=base / "tracker.csv",
        send_log=base / "send_log.csv",
        reply_dir=base / "reply_files",
        csv_out=base / "reply_log.csv",
        json_out=base / "reply_log.json",
        report=base / "reply_log.md",
        status_prefix="regression_rfq_reply_log",
        review_fields=H_A_REVIEW_FIELDS,
        hard_required_fields=(
            "run_id_level_raw_data",
            "csv_schema_acceptance",
            "sample_handling_fit",
            "non_glp_scope_control",
        ),
        selected_decision="selected_for_h_a",
    )


def seed(profile: Profile) -> None:
    for path in [profile.csv_out, profile.json_out, profile.report]:
        if path.exists():
            path.unlink()
    if profile.reply_dir.exists():
        shutil.rmtree(profile.reply_dir)
    write_csv(profile.tracker, TRACKER_FIELDS, [{
        "candidate_id": "vendor_a",
        "vendor_name": "Vendor A",
        "contact_date": "2026-05-24",
        "reply_date": "",
        "can_cover_full_h_a": "",
        "needs_split_scope": "",
        "run_id_level_raw_data": "",
        "media_physicochemical_coverage": "",
        "coupon_physical_coverage": "",
        "csv_schema_acceptance": "",
        "sample_handling_fit": "",
        "non_glp_scope_control": "",
        "turnaround_days": "",
        "quoted_cost": "",
        "decision": "pending_outreach",
        "notes": "",
    }])


def mark_received(profile: Profile, source_exists: bool = True) -> None:
    rows = read_csv(profile.csv_out)
    source = profile.reply_dir / "vendor_a_reply.txt"
    if source_exists:
        profile.reply_dir.mkdir(parents=True, exist_ok=True)
        source.write_text("Vendor A can cover the RFQ with source-backed deliverables.", encoding="utf-8")
    rows[0].update({
        "reply_status": "quote_received",
        "reply_at": "2026-05-25T11:00:00+08:00",
        "responder_name": "Vendor A Sales",
        "reply_source_file": str(source),
        "can_cover_full_h_a": "yes",
        "needs_split_scope": "no",
        "run_id_level_raw_data": "yes",
        "media_physicochemical_coverage": "yes",
        "coupon_physical_coverage": "yes",
        "csv_schema_acceptance": "yes",
        "bundle_entry_sheet_acceptance": "yes",
        "sample_handling_fit": "yes",
        "non_glp_scope_control": "yes",
        "turnaround_days": "14",
        "quoted_cost": "1200 USD",
        "decision": "reply_received_pending_review",
        "notes": "Regression fixture reply.",
    })
    write_csv(profile.csv_out, list(rows[0]), rows)


def run_case() -> dict:
    with tempfile.TemporaryDirectory(prefix="limina_rfq_reply_log_") as tmp:
        profile = make_profile(Path(tmp))
        seed(profile)
        initial = build_result(profile)
        initial_tracker = read_csv(profile.tracker)[0]
        mark_received(profile)
        applied = build_result(profile)
        applied_tracker = read_csv(profile.tracker)[0]
        seed(profile)
        build_result(profile)
        mark_received(profile, source_exists=False)
        rejected = build_result(profile)
        rejected_tracker = read_csv(profile.tracker)[0]
    checks = {
        "initial_waits_without_reply_files": initial["status"] == "regression_rfq_reply_log_waiting_for_reply_files",
        "initial_tracker_unchanged": initial_tracker["reply_date"] == "",
        "valid_reply_applies_tracker_fields": (
            applied["status"] == "regression_rfq_reply_log_applied"
            and applied_tracker["reply_date"] == "2026-05-25"
            and applied_tracker["run_id_level_raw_data"] == "yes"
            and applied_tracker["csv_schema_acceptance"] == "yes"
        ),
        "missing_source_rejected": rejected["status"] == "regression_rfq_reply_log_has_errors" and rejected["error_count"] == 1,
        "missing_source_does_not_apply_tracker": rejected_tracker["reply_date"] == "",
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "initial_status": initial["status"],
        "applied_status": applied["status"],
        "rejected_status": rejected["status"],
    }


def render_report(result: dict) -> str:
    lines = [
        "# LIMINA RFQ Reply Log Regression",
        "",
        f"**Status:** `{result['status']}`",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{key}`: {str(value).lower()}" for key, value in result["checks"].items())
    lines.extend([
        "",
        "## Boundary",
        "",
        "This regression uses temporary sourcing fixtures only. It does not create material evidence.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    result = run_case()
    write_json(DEFAULT_JSON, result)
    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text(render_report(result), encoding="utf-8")
    print(f"LIMINA RFQ reply-log regression: {result['status']}")
    print(f"Wrote {DEFAULT_JSON}")
    print(f"Wrote {DEFAULT_REPORT}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
