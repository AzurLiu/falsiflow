#!/usr/bin/env python3
"""Regression checks for RFQ send-confirmation intake."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
from email import policy
from email.message import EmailMessage
from pathlib import Path

from apply_limina_rfq_send_log import FIELDS, Profile, build_result as apply_send_log
from intake_limina_rfq_send_confirmations import build_result as intake_confirmations


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_rfq_send_confirmation_intake_regression.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_rfq_send_confirmation_intake_regression.md"


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
        label="RFQ Send Confirmation Intake Regression",
        contacts=base / "contacts.json",
        outbox=base / "outbox.json",
        tracker=base / "tracker.csv",
        confirmation_dir=base / "send_confirmations",
        csv_out=base / "send_log.csv",
        json_out=base / "send_log.json",
        report=base / "send_log.md",
        status_prefix="regression_rfq_send_log",
    )


def seed(profile: Profile, bundle_bytes: bytes = b"zip-placeholder") -> str:
    profile.confirmation_dir.mkdir(parents=True, exist_ok=True)
    for path in profile.confirmation_dir.glob("*"):
        if path.is_file():
            path.unlink()
    for path in [profile.csv_out, profile.json_out, profile.report]:
        if path.exists():
            path.unlink()
    email = profile.csv_out.parent / "email.txt"
    bundle = profile.csv_out.parent / "bundle.zip"
    email.write_text("RFQ email body", encoding="utf-8")
    bundle.write_bytes(bundle_bytes)
    expected_hash = hashlib.sha256(bundle_bytes).hexdigest()
    write_json(profile.contacts, {
        "contacts": [{
            "candidate_id": "vendor_a",
            "vendor_name": "Vendor A",
            "wave": "first_wave",
            "primary_send_method": "email",
            "primary_email": "rfq@example.test",
        }]
    })
    write_json(profile.outbox, {
        "rows": [{
            "candidate_id": "vendor_a",
            "vendor_name": "Vendor A",
            "email_file": str(email),
            "bundle_zip": str(bundle),
            "bundle_sha256": expected_hash,
            "attachment_count": 1,
            "send_status": "ready_to_send",
            "subject": "RFQ: regression fixture",
        }]
    })
    write_csv(profile.tracker, ["candidate_id", "vendor_name", "contact_date", "reply_date", "decision", "notes"], [{
        "candidate_id": "vendor_a",
        "vendor_name": "Vendor A",
        "contact_date": "",
        "reply_date": "",
        "decision": "pending_outreach",
        "notes": "",
    }])
    write_csv(profile.csv_out, FIELDS, [])
    return expected_hash


def write_sent_eml(profile: Profile, attachment: bytes, include_candidate_header: bool = True) -> Path:
    msg = EmailMessage(policy=policy.SMTP)
    msg["From"] = "sender@example.test"
    msg["To"] = "rfq@example.test"
    msg["Date"] = "Sun, 24 May 2026 09:30:00 +0800"
    msg["Message-ID"] = "<message-1@example.test>"
    msg["Subject"] = "RFQ: regression fixture"
    if include_candidate_header:
        msg["X-LIMINA-Candidate-ID"] = "vendor_a"
    msg.set_content("Sent RFQ fixture.")
    msg.add_attachment(attachment, maintype="application", subtype="zip", filename="bundle.zip")
    path = profile.confirmation_dir / "vendor_a_send_confirmation.eml"
    path.write_bytes(msg.as_bytes(policy=policy.SMTP))
    return path


def run_case() -> dict:
    with tempfile.TemporaryDirectory(prefix="limina_rfq_send_confirmation_intake_") as tmp:
        base = Path(tmp)
        profile = make_profile(base)
        expected_hash = seed(profile)
        no_files = intake_confirmations(profile, base / "intake_empty.csv")
        no_file_log = apply_send_log(profile)

        write_sent_eml(profile, b"zip-placeholder")
        applied = intake_confirmations(profile, base / "intake_applied.csv")
        applied_log = apply_send_log(profile)
        applied_tracker = read_csv(profile.tracker)[0]
        applied_rows = read_csv(profile.csv_out)

        seed(profile)
        write_sent_eml(profile, b"wrong-attachment")
        wrong_bundle = intake_confirmations(profile, base / "intake_wrong_bundle.csv")
        wrong_bundle_log = apply_send_log(profile)
        wrong_bundle_tracker = read_csv(profile.tracker)[0]

        seed(profile)
        text_confirmation = profile.confirmation_dir / "vendor_a_send_confirmation.txt"
        text_confirmation.write_text("web form confirmation fixture", encoding="utf-8")
        text_review = intake_confirmations(profile, base / "intake_text.csv")
        text_log = apply_send_log(profile)

    checks = {
        "no_files_waits": no_files["status"] == "regression_rfq_send_confirmation_intake_waiting_for_confirmation_files",
        "no_files_send_log_stays_pending": no_file_log["sent_rows"] == 0,
        "valid_eml_applies_one_row": applied["applied_rows"] == 1,
        "valid_eml_matches_expected_bundle": applied["bundle_hash_matched_rows"] == 1,
        "valid_eml_send_log_applies_tracker_date": applied_log["valid_sent_candidate_ids"] == ["vendor_a"] and applied_tracker["contact_date"] == "2026-05-24",
        "valid_eml_records_expected_bundle_hash": applied_rows[0]["sent_bundle_sha256"] == expected_hash,
        "wrong_bundle_needs_review": wrong_bundle["needs_review_rows"] == 1 and wrong_bundle["applied_rows"] == 0,
        "wrong_bundle_does_not_apply_tracker": wrong_bundle_log["sent_rows"] == 0 and wrong_bundle_tracker["contact_date"] == "",
        "text_confirmation_needs_manual_review": text_review["needs_review_rows"] == 1 and text_review["applied_rows"] == 0,
        "text_confirmation_does_not_mark_sent": text_log["sent_rows"] == 0,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "applied_status": applied["status"],
        "wrong_bundle_status": wrong_bundle["status"],
        "text_review_status": text_review["status"],
    }


def render_report(result: dict) -> str:
    lines = [
        "# LIMINA RFQ Send Confirmation Intake Regression",
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
        "This regression uses temporary outreach fixtures only. It does not create material evidence.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    result = run_case()
    write_json(DEFAULT_JSON, result)
    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text(render_report(result), encoding="utf-8")
    print(f"LIMINA RFQ send-confirmation intake regression: {result['status']}")
    print(f"Wrote {DEFAULT_JSON}")
    print(f"Wrote {DEFAULT_REPORT}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
