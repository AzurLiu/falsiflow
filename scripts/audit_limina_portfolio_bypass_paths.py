#!/usr/bin/env python3
"""Audit whether any ranked LIMINA prospect can bypass the active H-A claim gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RANKING = ROOT / "data" / "limina_discovery_ranking.json"
DEFAULT_PORTFOLIO = ROOT / "data" / "limina_technology_portfolio.json"
DEFAULT_CLAIM_AUDIT = ROOT / "data" / "limina_suitability_claim_audit.json"
DEFAULT_JSON = ROOT / "data" / "limina_portfolio_bypass_audit.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_portfolio_bypass_audit.md"

NHI_PARENT = "limina_nhi_pedot_laminin_v0_1"
ZRC_PARENT = "limina_zrc_nd_v0_1"
CELL_LANE = "LIMINA-Cell-1"
EXTERNAL_LANE = "LIMINA-External-1"


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def first_sentence(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if ". " in text:
        return text.split(". ", 1)[0].strip() + "."
    if "; " in text:
        return text.split("; ", 1)[0].strip() + "."
    return text


def parent_for(item: dict[str, Any]) -> str:
    lane = str(item.get("lane", ""))
    if lane == EXTERNAL_LANE:
        return ZRC_PARENT
    return NHI_PARENT


def route_label(parent: str) -> str:
    if parent == ZRC_PARENT:
        return "ZRC-ND external-material branch"
    if parent == NHI_PARENT:
        return "NHI-PEDOT cell-contact branch"
    return parent


def claim_audits_by_parent(claim: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("technology_id")): item
        for item in claim.get("candidate_audits", [])
        if item.get("technology_id")
    }


def provenance_counts(audit: dict[str, Any]) -> str:
    parts = []
    for label, summary in audit.get("provenance", {}).items():
        parts.append(
            f"{label}={summary.get('measured_row_count', 0)}/{summary.get('row_count', 0)} measured"
        )
    return "; ".join(parts) or "-"


def blocking_reason(parent: str, audit: dict[str, Any]) -> str:
    blockers = [str(item) for item in audit.get("blockers", []) if str(item).strip()]
    if parent == NHI_PARENT:
        h_a_blockers = [item for item in blockers if "H-A" in item or "h_a" in item.lower()]
        lead = h_a_blockers[0] if h_a_blockers else blockers[0] if blockers else ""
        return first_sentence(lead) or (
            "Cell-contact prospects inherit the H-A/H-B/H-C and long-duration claim gates."
        )
    if parent == ZRC_PARENT:
        lead = blockers[0] if blockers else ""
        return first_sentence(lead) or "External branch needs ZRC-ND measured non-cell and biological gates."
    return first_sentence(blockers[0]) if blockers else "No claim audit entry for this parent branch."


def next_decisive_artifact(parent: str) -> str:
    if parent == ZRC_PARENT:
        return "reports/zrc_nd_phase_a_sentinel_packet.md"
    return "reports/nhi_pedot_h_a_rfq_send_cockpit.html"


def row_for(item: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    parent = parent_for(item)
    requires_h_a = parent == NHI_PARENT
    can_bypass_h_a = parent == ZRC_PARENT
    claim_ready = bool(audit.get("claim_ready"))
    if claim_ready and can_bypass_h_a:
        decision = "non_h_a_claim_path_ready"
    elif claim_ready:
        decision = "claim_ready_but_h_a_dependent"
    elif can_bypass_h_a:
        decision = "non_h_a_path_not_claim_ready"
    else:
        decision = "blocked_by_h_a_claim_gate"
    return {
        "rank": item.get("rank"),
        "prospect_id": item.get("id"),
        "prospect_name": item.get("name"),
        "lane": item.get("lane"),
        "priority": item.get("priority"),
        "weighted_score": item.get("weighted_score"),
        "parent_technology_id": parent,
        "parent_route": route_label(parent),
        "requires_h_a_before_claim": requires_h_a,
        "can_bypass_h_a": can_bypass_h_a,
        "claim_ready": claim_ready,
        "claim_decision": audit.get("decision", "missing_claim_audit"),
        "decision": decision,
        "provenance_counts": provenance_counts(audit),
        "blocking_reason": blocking_reason(parent, audit),
        "next_decisive_artifact": next_decisive_artifact(parent),
    }


def build_audit(args: argparse.Namespace) -> dict[str, Any]:
    ranking = load_json(args.ranking)
    portfolio = load_json(args.portfolio)
    claim = load_json(args.claim_audit)
    audits = claim_audits_by_parent(claim)
    rows = [
        row_for(item, audits.get(parent_for(item), {}))
        for item in ranking.get("items", [])
    ]
    bypass_ready = [row for row in rows if row["decision"] == "non_h_a_claim_path_ready"]
    non_h_a_rows = [row for row in rows if row["can_bypass_h_a"]]
    h_a_rows = [row for row in rows if row["requires_h_a_before_claim"]]
    top_non_h_a = non_h_a_rows[0] if non_h_a_rows else None
    if bypass_ready:
        status = "non_h_a_claim_path_ready"
        recommended_action = "review_non_h_a_claim_audit"
    elif top_non_h_a:
        status = "no_h_a_bypass_claim_ready"
        recommended_action = "run_zrc_phase_a_real_measurements_before_any_non_h_a_claim"
    else:
        status = "no_non_h_a_path_in_ranked_queue"
        recommended_action = "continue_active_h_a_measurement_path"
    return {
        "status": status,
        "claim_ready": bool(claim.get("claim_ready")),
        "portfolio_status": portfolio.get("status", "missing"),
        "portfolio_primary_next_branch": portfolio.get("primary_next_branch"),
        "active_discovery_candidate": ranking.get("top_candidate"),
        "active_discovery_priority": ranking.get("top_priority"),
        "audit_boundary": (
            "Discovery ranking and literature references can nominate prospects, but a bypass is only real "
            "when the parent claim audit has source-file-backed measured gates without relying on the H-A branch."
        ),
        "summary": {
            "audit_rows": len(rows),
            "h_a_dependent_rows": len(h_a_rows),
            "non_h_a_candidate_rows": len(non_h_a_rows),
            "claim_ready_rows": sum(1 for row in rows if row["claim_ready"]),
            "non_h_a_claim_ready_rows": len(bypass_ready),
            "top_non_h_a_candidate": top_non_h_a["prospect_id"] if top_non_h_a else None,
            "top_non_h_a_decision": top_non_h_a["decision"] if top_non_h_a else None,
            "recommended_action": recommended_action,
        },
        "rows": rows,
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Portfolio Bypass Audit",
        "",
        "This audit checks whether a ranked prospect can avoid the active NHI-PEDOT H-A gate and still support the first suitability claim. It is not a suitability claim.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Claim ready:** `{str(result['claim_ready']).lower()}`",
        f"**Portfolio status:** `{result['portfolio_status']}`",
        f"**Portfolio primary next branch:** `{result.get('portfolio_primary_next_branch') or '-'}`",
        f"**Active discovery candidate:** `{result.get('active_discovery_candidate') or '-'}`",
        f"**Non-H-A claim-ready rows:** `{summary['non_h_a_claim_ready_rows']}`",
        f"**Top non-H-A candidate:** `{summary.get('top_non_h_a_candidate') or '-'}`",
        f"**Recommended action:** `{summary['recommended_action']}`",
        "",
        "## Prospect Decisions",
        "",
        "| Rank | Prospect | Parent route | Requires H-A | Can bypass H-A | Decision | Provenance | Blocking reason |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row.get('rank', '-')} | `{row['prospect_id']}` | {row['parent_route']} | "
            f"`{str(row['requires_h_a_before_claim']).lower()}` | "
            f"`{str(row['can_bypass_h_a']).lower()}` | `{row['decision']}` | "
            f"{md_cell(row['provenance_counts'])} | {md_cell(row['blocking_reason'])} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Cell-contact prospects inherit the NHI-PEDOT H-A/H-B/H-C and long-duration measurement gates before a suitability claim.",
        "- The ZRC-ND external branch is the only ranked non-H-A path right now, but it still needs real Phase A/non-cell and biological measured provenance.",
        "- Literature-backed discovery ranking can prioritize experiments; it cannot replace source-file-backed measurement rows in the final claim audit.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit H-A bypass possibilities across ranked LIMINA prospects.")
    parser.add_argument("--ranking", type=Path, default=DEFAULT_RANKING)
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument("--claim-audit", type=Path, default=DEFAULT_CLAIM_AUDIT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_audit(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    summary = result["summary"]
    print(f"Portfolio bypass status: {result['status']}")
    print(f"Non-H-A claim-ready rows: {summary['non_h_a_claim_ready_rows']}")
    print(f"Top non-H-A candidate: {summary.get('top_non_h_a_candidate') or '-'}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
