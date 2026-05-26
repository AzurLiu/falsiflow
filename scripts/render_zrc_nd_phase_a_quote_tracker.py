#!/usr/bin/env python3
"""Render a quote-response tracker for ZRC-ND Phase A RFQ replies."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RFQ = ROOT / "data" / "zrc_nd_phase_a_rfq_packet.json"
DEFAULT_CSV = ROOT / "data" / "zrc_nd_phase_a_quote_tracker.csv"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_quote_tracker.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_quote_tracker.md"

DEFAULT_FIELDS = [
    "candidate_id",
    "vendor_name",
    "contact_date",
    "reply_date",
    "can_cover_full_phase_a",
    "needs_split_scope",
    "run_id_level_raw_data",
    "phase_a_media_panel_coverage",
    "csv_schema_acceptance",
    "sample_handling_fit",
    "source_file_provenance",
    "non_glp_scope_control",
    "turnaround_days",
    "quoted_cost",
    "decision",
    "notes",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def load_existing_rows(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", newline="", encoding="utf-8") as handle:
        return {row.get("candidate_id", ""): row for row in csv.DictReader(handle) if row.get("candidate_id")}


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    normalized = {field: row.get(field, "") for field in DEFAULT_FIELDS}
    if not normalized["decision"]:
        normalized["decision"] = "pending_outreach"
    return normalized


def tracker_rows(rfq: dict[str, Any], existing: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for item in rfq.get("quote_requests", []):
        default = {
            "candidate_id": item.get("candidate_id", ""),
            "vendor_name": item.get("name", ""),
            "contact_date": "",
            "reply_date": "",
            "can_cover_full_phase_a": "",
            "needs_split_scope": "",
            "run_id_level_raw_data": "",
            "phase_a_media_panel_coverage": "",
            "csv_schema_acceptance": "",
            "sample_handling_fit": "",
            "source_file_provenance": "",
            "non_glp_scope_control": "",
            "turnaround_days": "",
            "quoted_cost": "",
            "decision": "pending_outreach",
            "notes": "",
        }
        prior = existing.get(default["candidate_id"], {})
        merged = {**default, **{key: value for key, value in prior.items() if value}}
        merged["vendor_name"] = default["vendor_name"] or merged.get("vendor_name", "")
        rows.append(normalize_row(merged))
    return rows


def tracker_status(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "no_quote_rows"
    if any(row.get("decision") == "selected_for_phase_a" for row in rows):
        return "vendor_selected_waiting_for_measurements"
    if any(row.get("reply_date") for row in rows):
        return "quote_replies_received"
    if any(row.get("contact_date") for row in rows):
        return "awaiting_vendor_replies"
    return "pending_outreach"


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DEFAULT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def build_tracker(rfq: dict[str, Any], rows: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "status": tracker_status(rows),
        "purpose": "Track RFQ replies and decide which vendor/cooperator can generate claimable ZRC-ND Phase A measurement rows.",
        "active_candidate": rfq.get("active_candidate"),
        "row_count": len(rows),
        "fields": DEFAULT_FIELDS,
        "rows": rows,
        "scoring_rubric": rfq.get("scoring_rubric", []),
        "disqualifiers": rfq.get("disqualifiers", []),
        "decision_rules": [
            "Reject any response that cannot preserve run_id-level raw data.",
            "Prefer one provider only if it covers pH, osmolality, conductivity, and appearance without losing source-file provenance.",
            "Use split scope if pH/osmolality and conductivity must be produced by different providers, but keep the same run_id labels.",
            "Do not proceed without CSV schema acceptance or an explicit mapping back to the LIMINA Phase A template.",
            "Do not treat quote responses or supplier guidance as material evidence; only returned measured rows can advance gates.",
            "Rerunning this tracker preserves existing contact dates, replies, decisions, and notes by candidate_id.",
        ],
    }


def render_report(result: dict[str, Any], csv_path: Path) -> str:
    lines = [
        "# ZRC-ND Phase A Quote Tracker",
        "",
        "This tracker is for RFQ responses. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result.get('active_candidate', '-')}`",
        f"**Tracker CSV:** `{csv_path}`",
        f"**Rows:** {result['row_count']}",
        "",
        "## Decision Rules",
        "",
    ]
    lines.extend(f"- {item}" for item in result["decision_rules"])

    lines.extend(["", "## Pending Vendors", "", "| Candidate | Vendor | Decision | Notes |", "| --- | --- | --- | --- |"])
    for row in result["rows"]:
        lines.append(f"| `{row['candidate_id']}` | {row['vendor_name']} | `{row['decision']}` | {row['notes'] or '-'} |")

    lines.extend(["", "## Disqualifiers", ""])
    lines.extend(f"- {item}" for item in result["disqualifiers"])
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render ZRC-ND Phase A quote tracker.")
    parser.add_argument("--rfq", type=Path, default=DEFAULT_RFQ)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rfq = load_json(args.rfq)
    rows = tracker_rows(rfq, load_existing_rows(args.csv_out))
    write_csv(rows, args.csv_out)
    result = build_tracker(rfq, rows)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result, args.csv_out), encoding="utf-8")
    print(f"ZRC-ND Phase A quote tracker: {result['status']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
