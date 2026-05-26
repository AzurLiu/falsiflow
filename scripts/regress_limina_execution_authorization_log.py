#!/usr/bin/env python3
"""Regression checks for LIMINA execution authorization logs."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
from pathlib import Path

from apply_limina_execution_authorization_log import Profile, build_result


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_execution_authorization_log_regression.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_execution_authorization_log_regression.md"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_profile(base: Path, source_backed: bool = True) -> Profile:
    quote_selection = base / "quote_selection.json"
    write_json(quote_selection, {
        "status": "provider_selected_waiting_for_measurements",
        "scored_rows": [{
            "candidate_id": "vendor_a",
            "vendor_name": "Vendor A",
            "selection_decision": "selected_for_regression",
            "source_backed_reply": source_backed,
        }],
    })
    return Profile(
        key="regression",
        label="Execution Authorization Regression",
        quote_selection=quote_selection,
        csv_out=base / "authorization_log.csv",
        json_out=base / "authorization_log.json",
        report=base / "authorization_log.md",
        status_prefix="regression_execution_authorization",
        selected_decision="selected_for_regression",
    )


def fill_authorization(profile: Profile, source_file: Path, source_hash: str = "") -> None:
    rows = read_csv(profile.csv_out)
    rows[0].update({
        "authorization_status": "authorized",
        "authorized_at": "2026-05-24T10:00:00+08:00",
        "authorized_by": "regression",
        "authorization_basis": "source-backed quote and package review",
        "provider_acceptance_reference": "quote-1",
        "sds_review_reference": "sds-review-1",
        "custody_release_reference": "custody-1",
        "scope_review_reference": "scope-1",
        "sample_count_authorized": "4",
        "shipment_or_execution_window": "2026-05-25/2026-05-31",
        "authorization_source_file": str(source_file),
        "authorization_source_sha256": source_hash,
    })
    write_csv(profile.csv_out, rows)


def run_case() -> dict:
    with tempfile.TemporaryDirectory(prefix="limina_execution_authorization_") as tmp:
        base = Path(tmp)
        profile = make_profile(base)
        initial = build_result(profile)

        source = base / "authorization.txt"
        source.write_text("approved execution authorization fixture", encoding="utf-8")
        fill_authorization(profile, source)
        authorized = build_result(profile)

        fill_authorization(profile, source, source_hash="bad-hash")
        bad_hash = build_result(profile)

        unbacked_profile = make_profile(base / "unbacked", source_backed=False)
        build_result(unbacked_profile)
        unbacked_source = base / "unbacked" / "authorization.txt"
        unbacked_source.write_text("unbacked approval fixture", encoding="utf-8")
        fill_authorization(unbacked_profile, unbacked_source, source_hash=sha256(unbacked_source))
        unbacked = build_result(unbacked_profile)

    checks = {
        "initial_waits_for_authorization": (
            initial["status"] == "regression_execution_authorization_waiting_for_human_authorization"
            and initial["valid_authorization_rows"] == 0
        ),
        "valid_authorization_is_accepted": (
            authorized["status"] == "regression_execution_authorization_authorized"
            and authorized["valid_authorized_candidate_ids"] == ["vendor_a"]
        ),
        "bad_hash_rejected": (
            bad_hash["status"] == "regression_execution_authorization_has_errors"
            and bad_hash["error_count"] == 1
        ),
        "unbacked_selected_provider_rejected": (
            unbacked["status"] == "regression_execution_authorization_has_errors"
            and any(
                "selected_source_backed_provider=missing" in row.get("errors", [])
                for row in unbacked["errors"]
            )
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "initial_status": initial["status"],
        "authorized_status": authorized["status"],
        "bad_hash_status": bad_hash["status"],
        "unbacked_status": unbacked["status"],
    }


def render_report(result: dict) -> str:
    lines = [
        "# LIMINA Execution Authorization Log Regression",
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
        "This regression uses temporary authorization fixtures only. It does not create material evidence or release real samples.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    result = run_case()
    write_json(DEFAULT_JSON, result)
    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text(render_report(result), encoding="utf-8")
    print(f"LIMINA execution authorization log regression: {result['status']}")
    print(f"Wrote {DEFAULT_JSON}")
    print(f"Wrote {DEFAULT_REPORT}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
