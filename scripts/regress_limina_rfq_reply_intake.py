#!/usr/bin/env python3
"""Regression checks for RFQ reply intake."""

from __future__ import annotations

import csv
import json
import tempfile
from email import policy
from email.message import EmailMessage
from pathlib import Path

from apply_limina_rfq_reply_log import H_A_REVIEW_FIELDS, Profile, build_result as apply_reply_log
from apply_limina_rfq_send_log import FIELDS as SEND_FIELDS
from intake_limina_rfq_replies import build_result as intake_replies


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_rfq_reply_intake_regression.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_rfq_reply_intake_regression.md"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def make_profile(base: Path) -> Profile:
    return Profile(
        key="regression",
        label="RFQ Reply Intake Regression",
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


def tracker_fields() -> list[str]:
    return [
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


def seed(profile: Profile, verified_send: bool) -> None:
    profile.reply_dir.mkdir(parents=True, exist_ok=True)
    for path in profile.reply_dir.glob("*"):
        if path.is_file():
            path.unlink()
    for path in [profile.csv_out, profile.json_out, profile.report]:
        if path.exists():
            path.unlink()
    write_csv(profile.tracker, tracker_fields(), [{
        "candidate_id": "vendor_a",
        "vendor_name": "Vendor A",
        "contact_date": "2026-05-24" if verified_send else "",
        "decision": "pending_outreach",
    }])
    write_csv(profile.send_log, SEND_FIELDS, [{
        "candidate_id": "vendor_a",
        "vendor_name": "Vendor A",
        "wave": "first_wave",
        "send_status": "sent" if verified_send else "pending_send",
        "sent_at": "2026-05-24T09:30:00+08:00" if verified_send else "",
        "sent_by": "sender@example.test" if verified_send else "",
        "send_method": "email",
        "recipient_or_form": "rfq@example.test",
        "message_id_or_confirmation": "message-1",
        "send_confirmation_source_file": "confirmation.eml" if verified_send else "",
        "send_confirmation_source_sha256": "abc123" if verified_send else "",
        "computed_send_confirmation_source_sha256": "abc123" if verified_send else "",
        "sent_bundle_sha256": "bundle123" if verified_send else "",
        "email_file": "email.txt",
        "bundle_zip": "bundle.zip",
        "expected_bundle_sha256": "bundle123",
        "attachment_count": "1",
        "tracker_contact_date": "2026-05-24" if verified_send else "",
        "tracker_decision": "pending_outreach",
    }])
    apply_reply_log(profile)


def write_reply_eml(profile: Profile, include_candidate_header: bool = True) -> Path:
    msg = EmailMessage(policy=policy.SMTP)
    msg["From"] = "Vendor A <reply@example.test>"
    msg["To"] = "sender@example.test"
    msg["Date"] = "Sun, 24 May 2026 13:05:00 +0800"
    msg["Message-ID"] = "<reply-1@example.test>"
    msg["Subject"] = "Re: RFQ: regression fixture"
    if include_candidate_header:
        msg["X-LIMINA-Candidate-ID"] = "vendor_a"
    msg.set_content("Thanks, we can review this RFQ. Please see initial feasibility comments.")
    path = profile.reply_dir / "vendor_a_reply.eml"
    path.write_bytes(msg.as_bytes(policy=policy.SMTP))
    return path


def run_case() -> dict:
    with tempfile.TemporaryDirectory(prefix="limina_rfq_reply_intake_") as tmp:
        base = Path(tmp)
        profile = make_profile(base)

        seed(profile, verified_send=True)
        no_files = intake_replies(profile, base / "intake_empty.csv")
        no_files_log = apply_reply_log(profile)

        write_reply_eml(profile)
        applied = intake_replies(profile, base / "intake_applied.csv")
        applied_rows = read_csv(profile.csv_out)
        applied_log = apply_reply_log(profile)
        applied_tracker = read_csv(profile.tracker)[0]

        seed(profile, verified_send=False)
        write_reply_eml(profile)
        unverified = intake_replies(profile, base / "intake_unverified.csv")
        unverified_rows = read_csv(profile.csv_out)
        unverified_log = apply_reply_log(profile)

        seed(profile, verified_send=True)
        text_reply = profile.reply_dir / "vendor_a_reply.txt"
        text_reply.write_text("Plain text reply requiring manual review.", encoding="utf-8")
        text_review = intake_replies(profile, base / "intake_text.csv")
        text_log = apply_reply_log(profile)

    checks = {
        "no_files_waits": no_files["status"] == "regression_rfq_reply_intake_waiting_for_reply_files",
        "no_files_reply_log_stays_pending": no_files_log["received_rows"] == 0,
        "valid_eml_registers_one_row": applied["applied_rows"] == 1,
        "valid_eml_marks_clarification_for_review": applied_rows[0]["reply_status"] == "clarification_received",
        "valid_eml_apply_updates_tracker_but_not_selection_fields": (
            applied_log["valid_reply_candidate_ids"] == ["vendor_a"]
            and applied_tracker["reply_date"] == "2026-05-24"
            and applied_tracker["decision"] == "needs_reply_clarification"
            and applied_tracker["run_id_level_raw_data"] == ""
        ),
        "unverified_send_does_not_apply": (
            unverified["needs_verified_send_rows"] == 1
            and unverified["applied_rows"] == 0
            and unverified_rows[0]["reply_status"] == "not_sent_yet"
            and unverified_log["received_rows"] == 0
        ),
        "text_reply_needs_manual_review": text_review["needs_manual_review_rows"] == 1 and text_review["applied_rows"] == 0,
        "text_reply_does_not_mark_received": text_log["received_rows"] == 0,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "applied_status": applied["status"],
        "unverified_status": unverified["status"],
        "text_review_status": text_review["status"],
    }


def render_report(result: dict) -> str:
    lines = [
        "# LIMINA RFQ Reply Intake Regression",
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
        "This regression uses temporary RFQ reply fixtures only. It does not create material evidence or select providers.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    result = run_case()
    write_json(DEFAULT_JSON, result)
    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text(render_report(result), encoding="utf-8")
    print(f"LIMINA RFQ reply intake regression: {result['status']}")
    print(f"Wrote {DEFAULT_JSON}")
    print(f"Wrote {DEFAULT_REPORT}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
