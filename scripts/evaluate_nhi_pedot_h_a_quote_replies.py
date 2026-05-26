#!/usr/bin/env python3
"""Score NHI-PEDOT H-A quote replies without treating them as evidence."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACKER_CSV = ROOT / "data" / "nhi_pedot_h_a_quote_tracker.csv"
DEFAULT_RFQ = ROOT / "data" / "nhi_pedot_h_a_rfq_packet.json"
DEFAULT_REPLY_LOG = ROOT / "data" / "nhi_pedot_h_a_rfq_reply_log.json"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_quote_selection.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_quote_selection.md"

NEGATIVE = {"no", "false", "n", "0", "cannot", "not_supported", "unsupported", "reject"}
PARTIAL = {"partial", "split", "needs_split", "subcontract", "maybe", "limited"}
POSITIVE = {"yes", "true", "y", "1", "can", "supported", "accepts", "covered"}

HARD_REQUIRED = [
    "run_id_level_raw_data",
    "csv_schema_acceptance",
    "sample_handling_fit",
    "non_glp_scope_control",
]

REVIEW_FIELDS = [
    "can_cover_full_h_a",
    "needs_split_scope",
    "run_id_level_raw_data",
    "media_physicochemical_coverage",
    "coupon_physical_coverage",
    "csv_schema_acceptance",
    "bundle_entry_sheet_acceptance",
    "sample_handling_fit",
    "non_glp_scope_control",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def value_score(value: str, weight: int) -> tuple[float, str]:
    normalized = normalize(value)
    if not normalized:
        return 0.0, "unknown"
    if normalized in POSITIVE:
        return float(weight), "pass"
    if normalized in PARTIAL:
        return float(weight) * 0.5, "partial"
    if normalized in NEGATIVE:
        return 0.0, "fail"
    return 0.0, "unparsed"


def rubric_weights(rfq: dict[str, Any]) -> dict[str, int]:
    return {
        item.get("criterion", ""): int(item.get("weight", 0))
        for item in rfq.get("scoring_rubric", [])
        if item.get("criterion")
    }


def valid_reply_ids(reply_log: dict[str, Any]) -> set[str]:
    return {
        str(candidate_id)
        for candidate_id in reply_log.get("valid_reply_candidate_ids", [])
        if str(candidate_id)
    }


def score_row(row: dict[str, str], weights: dict[str, int], source_backed_ids: set[str]) -> dict[str, Any]:
    field_scores = []
    total = 0.0
    possible = 0.0
    hard_failures = []
    unknown_required = []
    for field, weight in weights.items():
        value = row.get(field, "")
        score, verdict = value_score(value, weight)
        total += score
        possible += weight
        field_scores.append({
            "field": field,
            "value": value,
            "weight": weight,
            "score": score,
            "verdict": verdict,
        })
        if field in HARD_REQUIRED:
            if verdict in {"fail", "unparsed"}:
                hard_failures.append(field)
            elif verdict == "unknown":
                unknown_required.append(field)

    missing_review_fields = [field for field in REVIEW_FIELDS if not row.get(field, "").strip()]
    has_reply = bool(row.get("reply_date", "").strip())
    contact_sent = bool(row.get("contact_date", "").strip())
    normalized_decision = normalize(row.get("decision", ""))
    source_backed_reply = row.get("candidate_id", "") in source_backed_ids
    decision = "pending_outreach"
    if not contact_sent:
        decision = "pending_outreach"
    elif not has_reply:
        decision = "awaiting_reply"
    elif not source_backed_reply:
        decision = "reply_not_source_backed"
    elif normalized_decision == "selected_for_h_a":
        decision = "selected_for_h_a"
    elif hard_failures:
        decision = "reject_hard_failure"
    elif unknown_required or missing_review_fields:
        decision = "needs_reply_clarification"
    elif possible and total / possible >= 0.70:
        decision = "shortlist_for_h_a_execution"
    else:
        decision = "hold_or_split_scope"

    return {
        "candidate_id": row.get("candidate_id", ""),
        "vendor_name": row.get("vendor_name", ""),
        "contact_date": row.get("contact_date", ""),
        "reply_date": row.get("reply_date", ""),
        "tracker_decision": row.get("decision", ""),
        "selection_decision": decision,
        "source_backed_reply": source_backed_reply,
        "source_backing_status": "source_backed" if source_backed_reply else ("missing_source_backing" if has_reply else "not_applicable"),
        "score": round(total, 2),
        "possible_score": round(possible, 2),
        "score_fraction": round(total / possible, 3) if possible else 0,
        "hard_failures": hard_failures,
        "unknown_required_fields": unknown_required,
        "missing_review_fields": missing_review_fields,
        "turnaround_days": row.get("turnaround_days", ""),
        "quoted_cost": row.get("quoted_cost", ""),
        "notes": row.get("notes", ""),
        "field_scores": field_scores,
    }


def build_selection(rows: list[dict[str, str]], rfq: dict[str, Any], reply_log: dict[str, Any]) -> dict[str, Any]:
    weights = rubric_weights(rfq)
    source_backed_ids = valid_reply_ids(reply_log)
    scored = [score_row(row, weights, source_backed_ids) for row in rows]
    selected = [row for row in scored if row["selection_decision"] == "selected_for_h_a"]
    shortlisted = [row for row in scored if row["selection_decision"] == "shortlist_for_h_a_execution"]
    replies = [row for row in scored if row["reply_date"]]
    source_backed_replies = [row for row in scored if row["source_backed_reply"]]
    sent = [row for row in scored if row["contact_date"]]
    if selected:
        status = "provider_selected_waiting_for_measurements"
    elif shortlisted:
        status = "ready_to_select_provider"
    elif replies and len(source_backed_replies) < len(replies):
        status = "quote_replies_need_source_files"
    elif replies:
        status = "quote_replies_need_review"
    elif sent:
        status = "awaiting_vendor_replies"
    else:
        status = "pending_outreach"
    ranked = sorted(scored, key=lambda row: (row["score_fraction"], row["score"]), reverse=True)
    return {
        "status": status,
        "purpose": "Score RFQ replies for H-A execution selection without treating quotes as material evidence.",
        "active_candidate": rfq.get("active_candidate"),
        "row_count": len(rows),
        "sent_count": len(sent),
        "reply_count": len(replies),
        "source_backed_reply_count": len(source_backed_replies),
        "shortlist_count": len(shortlisted),
        "selected_count": len(selected),
        "reply_log_status": reply_log.get("status", "unknown"),
        "reply_log_valid_rows": reply_log.get("valid_reply_rows", 0),
        "reply_log_errors": reply_log.get("error_count", 0),
        "hard_required_fields": HARD_REQUIRED,
        "scored_rows": ranked,
        "non_evidence_boundary": "Quote replies and vendor selection can authorize measurement execution only; they do not count as H-A data or material suitability evidence.",
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# NHI-PEDOT H-A Quote Selection",
        "",
        "This report scores vendor RFQ replies for execution selection. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result.get('active_candidate', '-')}`",
        f"**Rows:** {result['row_count']}",
        f"**Sent:** {result['sent_count']}",
        f"**Replies:** {result['reply_count']}",
        f"**Source-backed replies:** {result['source_backed_reply_count']}",
        f"**Shortlisted:** {result['shortlist_count']}",
        f"**Selected:** {result['selected_count']}",
        f"**Reply log:** `{result['reply_log_status']}`; valid={result['reply_log_valid_rows']}; errors={result['reply_log_errors']}",
        "",
        "## Ranked Rows",
        "",
        "| Vendor | Decision | Source-backed reply | Score | Hard failures | Missing review fields |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in result["scored_rows"]:
        hard = ", ".join(row["hard_failures"]) or "-"
        missing = ", ".join(row["missing_review_fields"][:6]) or "-"
        if len(row["missing_review_fields"]) > 6:
            missing += ", ..."
        lines.append(
            f"| {row['vendor_name']} | `{row['selection_decision']}` | "
            f"`{row['source_backing_status']}` | "
            f"{row['score']} / {row['possible_score']} | {hard} | {missing} |"
        )

    lines.extend([
        "",
        "## Hard Required Fields",
        "",
    ])
    lines.extend(f"- `{field}`" for field in result["hard_required_fields"])

    lines.extend([
        "",
        "## Boundary",
        "",
        result["non_evidence_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate NHI-PEDOT H-A quote replies.")
    parser.add_argument("--tracker", type=Path, default=DEFAULT_TRACKER_CSV)
    parser.add_argument("--rfq", type=Path, default=DEFAULT_RFQ)
    parser.add_argument("--reply-log", type=Path, default=DEFAULT_REPLY_LOG)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_selection(load_rows(args.tracker), load_json(args.rfq), load_json(args.reply_log))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A quote selection: {result['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
