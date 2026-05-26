#!/usr/bin/env python3
"""Regression checks for RFQ send-log application."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

from apply_limina_rfq_send_log import Profile, build_result


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_rfq_send_log_regression.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_rfq_send_log_regression.md"


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
        label="RFQ Send Log Regression",
        contacts=base / "contacts.json",
        outbox=base / "outbox.json",
        tracker=base / "tracker.csv",
        confirmation_dir=base / "send_confirmations",
        csv_out=base / "send_log.csv",
        json_out=base / "send_log.json",
        report=base / "send_log.md",
        status_prefix="regression_rfq_send_log",
    )


def seed(profile: Profile) -> None:
    for path in [profile.csv_out, profile.json_out, profile.report]:
        if path.exists():
            path.unlink()
    if profile.confirmation_dir.exists():
        for path in profile.confirmation_dir.glob("*"):
            if path.is_file():
                path.unlink()
    email = profile.csv_out.parent / "email.txt"
    bundle = profile.csv_out.parent / "bundle.zip"
    email.write_text("RFQ email body", encoding="utf-8")
    bundle.write_bytes(b"zip-placeholder")
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
            "bundle_sha256": "abc123",
            "attachment_count": 1,
            "send_status": "ready_to_send",
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


def mark_sent(profile: Profile, sent_hash: str = "abc123", create_confirmation: bool = True) -> None:
    rows = read_csv(profile.csv_out)
    confirmation_source = Path(rows[0].get("send_confirmation_source_file", ""))
    if not confirmation_source.is_absolute():
        confirmation_source = ROOT / confirmation_source
    if create_confirmation:
        confirmation_source.parent.mkdir(parents=True, exist_ok=True)
        confirmation_source.write_text("sent confirmation fixture", encoding="utf-8")
    rows[0].update({
        "send_status": "sent",
        "sent_at": "2026-05-24T09:30:00+08:00",
        "sent_by": "regression",
        "send_method": "email",
        "recipient_or_form": "rfq@example.test",
        "message_id_or_confirmation": "message-1",
        "send_confirmation_source_file": str(confirmation_source),
        "sent_bundle_sha256": sent_hash,
    })
    write_csv(profile.csv_out, list(rows[0]), rows)


def run_case() -> dict:
    with tempfile.TemporaryDirectory(prefix="limina_rfq_send_log_") as tmp:
        profile = make_profile(Path(tmp))
        seed(profile)
        initial = build_result(profile)
        initial_tracker = read_csv(profile.tracker)[0]
        mark_sent(profile)
        applied = build_result(profile)
        applied_tracker = read_csv(profile.tracker)[0]
        seed(profile)
        build_result(profile)
        mark_sent(profile, sent_hash="wrong-hash")
        rejected = build_result(profile)
        rejected_tracker = read_csv(profile.tracker)[0]
        seed(profile)
        build_result(profile)
        mark_sent(profile, create_confirmation=False)
        missing_confirmation = build_result(profile)
        missing_confirmation_tracker = read_csv(profile.tracker)[0]
    checks = {
        "initial_waits_without_sent_rows": initial["status"] == "regression_rfq_send_log_waiting_for_sent_entries",
        "initial_tracker_unchanged": initial_tracker["contact_date"] == "",
        "valid_send_applies_one_tracker_date": applied["applied_tracker_contact_dates"] == 1 and applied_tracker["contact_date"] == "2026-05-24",
        "valid_send_is_source_backed": applied["valid_sent_candidate_ids"] == ["vendor_a"],
        "bad_hash_rejected": rejected["status"] == "regression_rfq_send_log_has_errors" and rejected["error_count"] == 1,
        "bad_hash_does_not_apply_tracker_date": rejected_tracker["contact_date"] == "",
        "missing_confirmation_source_rejected": (
            missing_confirmation["status"] == "regression_rfq_send_log_has_errors"
            and missing_confirmation["error_count"] == 1
        ),
        "missing_confirmation_does_not_apply_tracker_date": missing_confirmation_tracker["contact_date"] == "",
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "initial_status": initial["status"],
        "applied_status": applied["status"],
        "rejected_status": rejected["status"],
        "missing_confirmation_status": missing_confirmation["status"],
    }


def render_report(result: dict) -> str:
    lines = [
        "# LIMINA RFQ Send Log Regression",
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
    print(f"LIMINA RFQ send-log regression: {result['status']}")
    print(f"Wrote {DEFAULT_JSON}")
    print(f"Wrote {DEFAULT_REPORT}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
