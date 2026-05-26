#!/usr/bin/env python3
"""Select the next LIMINA material-technology branch to advance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TECHNOLOGIES = ROOT / "data" / "limina_material_technologies.json"
DEFAULT_READINESS = ROOT / "data" / "zrc_nd_readiness_audit.json"
DEFAULT_SENTINEL = ROOT / "data" / "zrc_nd_sentinel_interpretation.json"
DEFAULT_DISCOVERY_RANKING = ROOT / "data" / "limina_discovery_ranking.json"
DEFAULT_NHI_H_A = ROOT / "data" / "nhi_pedot_h_a_sentinel_interpretation.json"
DEFAULT_NHI_H_A_SERVICE = ROOT / "data" / "nhi_pedot_h_a_service_request.json"
DEFAULT_NHI_RESULTS = ROOT / "data" / "nhi_pedot_results.json"
DEFAULT_NHI_LONG_RESULTS = ROOT / "data" / "nhi_pedot_long_results.json"
DEFAULT_JSON = ROOT / "data" / "limina_technology_portfolio.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_technology_portfolio.md"

VALIDATION_PACKAGES = {
    "limina_zrc_nd_v0_1": [
        ROOT / "data" / "zrc_nd_3p5k_guard_validation_package.json",
        ROOT / "data" / "zrc_nd_biological_followup_package.json",
    ],
    "limina_nhi_pedot_laminin_v0_1": [
        ROOT / "data" / "nhi_pedot_validation_package.json",
        ROOT / "data" / "nhi_pedot_long_followup_package.json",
    ],
}


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_records(path: Path) -> list[dict[str, Any]]:
    value = load_json(path)
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def package_status(technology_id: str) -> dict[str, Any]:
    paths = VALIDATION_PACKAGES.get(technology_id, [])
    present = [path for path in paths if path.exists()]
    return {
        "expected": [str(path.relative_to(ROOT)) for path in paths],
        "present": [str(path.relative_to(ROOT)) for path in present],
        "all_present": len(paths) > 0 and len(paths) == len(present),
    }


def score_value(record: dict[str, Any]) -> float:
    raw = record.get("score", {}).get("weighted_internal_score", 0)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def top_discovery_item(ranking: dict[str, Any]) -> dict[str, Any]:
    items = ranking.get("items", [])
    if items:
        return items[0]
    return {
        "id": ranking.get("top_candidate"),
        "priority": ranking.get("top_priority"),
    }


def discovery_promotes_nhi(ranking: dict[str, Any]) -> bool:
    top = top_discovery_item(ranking)
    candidate_id = str(top.get("id", ""))
    return (
        top.get("priority") == "promote_now"
        and candidate_id in {
            "limina_alg_lam_pedot_lowdose_v0_2",
            "limina_nhi_pedot_laminin_v0_1",
        }
    )


def zrc_decision(
    record: dict[str, Any],
    readiness: dict[str, Any],
    sentinel: dict[str, Any],
) -> dict[str, Any]:
    sentinel_status = sentinel.get("status", "missing")
    readiness_status = readiness.get("readiness", "unknown")
    if readiness.get("suitable") is True:
        status = "readiness_gates_passed_claim_audit_required"
        priority = 0
        action = (
            "Run the final suitability claim audit; readiness gates report suitable, "
            "but portfolio cannot declare suitability without claimable source-file provenance."
        )
    elif sentinel_status == "sentinel_lead_fails_stop":
        status = "stopped_by_phase_a_sentinel"
        priority = 3
        action = "Run remediation branch; do not advance ZRC-ND lead until the blank-integrity failure is resolved."
    elif sentinel_status in {"missing", "no_sentinel_rows"}:
        status = "active_needs_phase_a_sentinel"
        priority = 1
        action = "Fill the 8-row Phase A sentinel packet and re-run sentinel interpretation before more non-cell work."
    elif sentinel_status == "sentinel_needs_more_data":
        status = "active_complete_sentinel_fields"
        priority = 1
        action = "Complete missing sentinel medium-integrity fields before selecting Phase A replicate 2."
    elif sentinel_status == "sentinel_passes_continue":
        status = "active_continue_non_cell_validation"
        priority = 1
        action = "Advance to the next adaptive non-cell batch, then require Phase A/B/C coverage before biological follow-up."
    elif sentinel_status == "sentinel_lead_passes_comparator_issue":
        status = "active_quarantine_comparator"
        priority = 1
        action = "Continue lead cautiously while retesting failed comparators outside superiority claims."
    else:
        status = "active_uncertain_sentinel_state"
        priority = 2
        action = "Inspect sentinel output before selecting later rows."

    return {
        "technology_id": record["id"],
        "name": record["name"],
        "priority_lane": record.get("priority_lane", ""),
        "technology_status": record.get("status", ""),
        "portfolio_status": status,
        "portfolio_priority": priority,
        "weighted_internal_score": score_value(record),
        "readiness_status": readiness_status,
        "sentinel_status": sentinel_status,
        "validation_packages": package_status(record["id"]),
        "next_action": action,
        "proof_boundary": "Not suitable until the final claim audit verifies measured non-cell and biological provenance.",
    }


def generic_cell_contact_decision(
    record: dict[str, Any],
    ranking: dict[str, Any],
    h_a: dict[str, Any],
    h_a_service: dict[str, Any],
    nhi_results: dict[str, Any],
    nhi_long_results: dict[str, Any],
) -> dict[str, Any]:
    packages = package_status(record["id"])
    h_a_status = h_a.get("status", "missing")
    h_a_service_status = h_a_service.get("status", "missing")
    active_nhi_route = discovery_promotes_nhi(ranking)
    nhi_status = nhi_results.get("summary", {}).get("status", "missing")
    nhi_long_status = nhi_long_results.get("summary", {}).get("status", "missing")
    if record.get("id") == "limina_nhi_pedot_laminin_v0_1" and nhi_long_status == "nhi_pedot_long_passes_gates":
        status = "long_gates_passed_claim_audit_required"
        priority = 0
        action = (
            "Run the final suitability claim audit for the active ALG-LAM-PEDOT candidate; "
            "long-duration gates report pass, but source-file provenance still controls the claim."
        )
    elif record.get("id") == "limina_nhi_pedot_laminin_v0_1" and h_a_status == "h_a_lead_fails_stop":
        status = "stopped_by_nhi_pedot_h_a"
        priority = 3
        action = "Stop lead advancement and branch by measured H-A failure mode before any H-B/H-C work."
    elif record.get("id") == "limina_nhi_pedot_laminin_v0_1" and nhi_long_status == "nhi_pedot_long_has_failures":
        status = "stopped_by_nhi_pedot_long_followup"
        priority = 3
        action = "Stop suitability claim; branch by failed long-duration gate before repeating coupon or long-culture work."
    elif (
        record.get("id") == "limina_nhi_pedot_laminin_v0_1"
        and active_nhi_route
        and h_a_status in {"h_a_invalid_provenance", "h_a_no_sentinel_rows", "h_a_sentinel_needs_more_data", "missing"}
    ):
        status = "active_needs_h_a_real_measurements"
        priority = 1
        action = (
            "Use the H-A service request to obtain real acellular medium/physical rows for the promoted "
            "ALG-LAM-PEDOT route before advancing H-B/H-C."
        )
    elif (
        record.get("id") == "limina_nhi_pedot_laminin_v0_1"
        and h_a_status in {
            "h_a_lead_passes_continue_h_b",
            "h_a_lead_passes_continue_challenge_boundary",
            "h_a_lead_passes_hydrogel_control_issue",
        }
        and nhi_status in {"missing", "no_data", "needs_more_data"}
    ):
        status = "active_h_a_passed_needs_h_b_h_c"
        priority = 1
        action = "Activate the preregistered H-B/H-C forward package; suitability remains unproven until measured coupon and long-duration gates pass."
    elif record.get("id") == "limina_nhi_pedot_laminin_v0_1" and nhi_status == "nhi_pedot_passes_gates":
        status = "cell_contact_coupon_gates_passed_needs_long_pilot"
        priority = 1
        action = "Design a longer CL1-like MEA network stability pilot; do not claim final suitability yet."
    elif record.get("id") == "limina_nhi_pedot_laminin_v0_1" and nhi_status == "lead_has_failures":
        status = "stopped_by_nhi_pedot_evaluator"
        priority = 3
        action = "Stop lead advancement and branch by failed gate: reduce PEDOT:PSS loading, change matrix, or demote to hydrogel-laminin control."
    elif record.get("id") == "limina_nhi_pedot_laminin_v0_1" and nhi_status == "needs_more_data":
        status = "parallel_continue_coupon_validation"
        priority = 2
        action = "Complete missing H-A/H-B/H-C measured rows before any cell-contact suitability claim."
    elif packages["all_present"]:
        status = "parallel_ready_for_acellular_validation"
        priority = 2
        action = "Prepare H-A acellular blank/extract and H-B electrochemical coupon measurements while ZRC-ND sentinel is pending."
    else:
        status = "parallel_needs_validation_package"
        priority = 4
        action = "Create a validation package before wet or simulated advancement."

    return {
        "technology_id": record["id"],
        "name": record["name"],
        "priority_lane": record.get("priority_lane", ""),
        "technology_status": record.get("status", ""),
        "portfolio_status": status,
        "portfolio_priority": priority,
        "weighted_internal_score": score_value(record),
        "readiness_status": (
            f"h_a={h_a_status};h_a_service={h_a_service_status};coupon={nhi_status};long={nhi_long_status}"
            if record.get("id") == "limina_nhi_pedot_laminin_v0_1"
            else "not_audited_yet"
        ),
        "sentinel_status": "not_applicable",
        "validation_packages": packages,
        "next_action": action,
        "proof_boundary": "Not suitable until final claim audit verifies H-A/H-B/H-C and long-duration source-file provenance.",
    }


def build_portfolio(
    technologies: list[dict[str, Any]],
    readiness: dict[str, Any],
    sentinel: dict[str, Any],
    ranking: dict[str, Any],
    h_a: dict[str, Any],
    h_a_service: dict[str, Any],
    nhi_results: dict[str, Any],
    nhi_long_results: dict[str, Any],
) -> dict[str, Any]:
    branches: list[dict[str, Any]] = []
    for record in technologies:
        if record.get("id") == "limina_zrc_nd_v0_1":
            branches.append(zrc_decision(record, readiness, sentinel))
        else:
            branches.append(generic_cell_contact_decision(record, ranking, h_a, h_a_service, nhi_results, nhi_long_results))

    branches.sort(key=lambda item: (item["portfolio_priority"], -item["weighted_internal_score"]))
    claim_audit_required = any(
        str(item["portfolio_status"]).endswith("_claim_audit_required")
        for item in branches
    )
    return {
        "status": "claim_audit_required" if claim_audit_required else "no_suitable_material_yet",
        "active_discovery_candidate": top_discovery_item(ranking).get("id"),
        "active_discovery_priority": top_discovery_item(ranking).get("priority"),
        "primary_next_branch": branches[0]["technology_id"] if branches else None,
        "branches": branches,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIMINA Technology Portfolio",
        "",
        f"**Portfolio status:** `{result['status']}`",
        f"**Active discovery candidate:** `{result.get('active_discovery_candidate') or '-'}`",
        f"**Active discovery priority:** `{result.get('active_discovery_priority') or '-'}`",
        f"**Primary next branch:** `{result['primary_next_branch']}`",
        "",
        "## Branch Decisions",
        "",
        "| Priority | Technology | Lane | Status | Score | Next action |",
        "| ---: | --- | --- | --- | ---: | --- |",
    ]
    for item in result["branches"]:
        lines.append(
            f"| {item['portfolio_priority']} | `{item['technology_id']}` | {item['priority_lane']} | "
            f"`{item['portfolio_status']}` | {item['weighted_internal_score']:.2f} | {item['next_action']} |"
        )

    lines.extend(["", "## Validation Packages", ""])
    for item in result["branches"]:
        packages = item["validation_packages"]
        present = ", ".join(f"`{path}`" for path in packages["present"]) or "-"
        expected = ", ".join(f"`{path}`" for path in packages["expected"]) or "-"
        lines.extend([
            f"### {item['technology_id']}",
            "",
            f"- All present: `{str(packages['all_present']).lower()}`",
            f"- Present: {present}",
            f"- Expected: {expected}",
            f"- Proof boundary: {item['proof_boundary']}",
            "",
        ])

    lines.extend([
        "## Interpretation",
        "",
        "- Portfolio priority is a workflow selector, not a suitability score.",
        "- A branch can be high priority because it is the next cheapest decisive test, even if it is not experimentally proven.",
        "- `suitable` remains false until `limina_suitability_claim_audit` reports `claim_ready=true` with source-file-backed measured rows.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Select next LIMINA material-technology branch.")
    parser.add_argument("--technologies", type=Path, default=DEFAULT_TECHNOLOGIES)
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--sentinel", type=Path, default=DEFAULT_SENTINEL)
    parser.add_argument("--discovery-ranking", type=Path, default=DEFAULT_DISCOVERY_RANKING)
    parser.add_argument("--nhi-h-a", type=Path, default=DEFAULT_NHI_H_A)
    parser.add_argument("--nhi-h-a-service", type=Path, default=DEFAULT_NHI_H_A_SERVICE)
    parser.add_argument("--nhi-results", type=Path, default=DEFAULT_NHI_RESULTS)
    parser.add_argument("--nhi-long-results", type=Path, default=DEFAULT_NHI_LONG_RESULTS)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_portfolio(
        load_records(args.technologies),
        load_json(args.readiness),
        load_json(args.sentinel),
        load_json(args.discovery_ranking),
        load_json(args.nhi_h_a),
        load_json(args.nhi_h_a_service),
        load_json(args.nhi_results),
        load_json(args.nhi_long_results),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Portfolio: {result['status']}")
    print(f"Primary next branch: {result['primary_next_branch']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
