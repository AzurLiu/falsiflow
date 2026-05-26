#!/usr/bin/env python3
"""Regression checks for source-backed quote-selection guards."""

from __future__ import annotations

import json
from pathlib import Path

import evaluate_nhi_pedot_h_a_quote_replies as h_a
import evaluate_zrc_nd_phase_a_quote_replies as zrc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_quote_selection_source_guard_regression.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_quote_selection_source_guard_regression.md"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def rfq(fields: list[str]) -> dict:
    return {
        "active_candidate": "regression_candidate",
        "scoring_rubric": [
            {"criterion": field, "weight": 1}
            for field in fields
        ],
    }


def positive_row(fields: list[str], selected_decision: str = "") -> dict[str, str]:
    row = {
        "candidate_id": "vendor_a",
        "vendor_name": "Vendor A",
        "contact_date": "2026-05-24",
        "reply_date": "2026-05-25",
        "turnaround_days": "14",
        "quoted_cost": "1200 USD",
        "decision": selected_decision,
        "notes": "Regression fixture.",
    }
    for field in fields:
        row[field] = "yes"
    return row


def run_case() -> dict:
    h_a_fields = list(h_a.REVIEW_FIELDS)
    zrc_fields = list(zrc.REVIEW_FIELDS)
    no_source = {"valid_reply_candidate_ids": [], "valid_reply_rows": 0, "error_count": 0, "status": "empty"}
    h_a_source = {"valid_reply_candidate_ids": ["vendor_a"], "valid_reply_rows": 1, "error_count": 0, "status": "source_ok"}
    zrc_source = {"valid_reply_candidate_ids": ["vendor_a"], "valid_reply_rows": 1, "error_count": 0, "status": "source_ok"}

    h_a_unbacked = h_a.build_selection([positive_row(h_a_fields)], rfq(h_a_fields), no_source)
    h_a_backed = h_a.build_selection([positive_row(h_a_fields)], rfq(h_a_fields), h_a_source)
    h_a_selected_unbacked = h_a.build_selection(
        [positive_row(h_a_fields, selected_decision="selected_for_h_a")],
        rfq(h_a_fields),
        no_source,
    )

    zrc_unbacked = zrc.build_selection([positive_row(zrc_fields)], rfq(zrc_fields), no_source)
    zrc_backed = zrc.build_selection([positive_row(zrc_fields)], rfq(zrc_fields), zrc_source)
    zrc_selected_unbacked = zrc.build_selection(
        [positive_row(zrc_fields, selected_decision="selected_for_phase_a")],
        rfq(zrc_fields),
        no_source,
    )

    checks = {
        "h_a_unbacked_reply_needs_source_files": (
            h_a_unbacked["status"] == "quote_replies_need_source_files"
            and h_a_unbacked["shortlist_count"] == 0
            and h_a_unbacked["scored_rows"][0]["selection_decision"] == "reply_not_source_backed"
        ),
        "h_a_source_backed_reply_can_shortlist": (
            h_a_backed["status"] == "ready_to_select_provider"
            and h_a_backed["shortlist_count"] == 1
            and h_a_backed["source_backed_reply_count"] == 1
        ),
        "h_a_selected_without_source_is_not_selected": (
            h_a_selected_unbacked["selected_count"] == 0
            and h_a_selected_unbacked["scored_rows"][0]["selection_decision"] == "reply_not_source_backed"
        ),
        "zrc_unbacked_reply_needs_source_files": (
            zrc_unbacked["status"] == "quote_replies_need_source_files"
            and zrc_unbacked["shortlist_count"] == 0
            and zrc_unbacked["scored_rows"][0]["selection_decision"] == "reply_not_source_backed"
        ),
        "zrc_source_backed_reply_can_shortlist": (
            zrc_backed["status"] == "ready_to_select_provider"
            and zrc_backed["shortlist_count"] == 1
            and zrc_backed["source_backed_reply_count"] == 1
        ),
        "zrc_selected_without_source_is_not_selected": (
            zrc_selected_unbacked["selected_count"] == 0
            and zrc_selected_unbacked["scored_rows"][0]["selection_decision"] == "reply_not_source_backed"
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "h_a_unbacked_status": h_a_unbacked["status"],
        "h_a_backed_status": h_a_backed["status"],
        "zrc_unbacked_status": zrc_unbacked["status"],
        "zrc_backed_status": zrc_backed["status"],
    }


def render_report(result: dict) -> str:
    lines = [
        "# LIMINA Quote Selection Source Guard Regression",
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
        "This regression uses in-memory sourcing fixtures only. It does not create material evidence.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    result = run_case()
    write_json(DEFAULT_JSON, result)
    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text(render_report(result), encoding="utf-8")
    print(f"LIMINA quote-selection source guard regression: {result['status']}")
    print(f"Wrote {DEFAULT_JSON}")
    print(f"Wrote {DEFAULT_REPORT}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
