#!/usr/bin/env python3
"""Render a second-wave material candidate queue while first-wave evidence waits."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RANKING = ROOT / "data" / "limina_discovery_ranking.json"
DEFAULT_CANDIDATES = ROOT / "data" / "limina_discovery_candidates.json"
DEFAULT_PORTFOLIO = ROOT / "data" / "limina_technology_portfolio.json"
DEFAULT_FIRST_WAVE = ROOT / "data" / "limina_first_wave_post_dispatch_processing.json"
DEFAULT_JSON = ROOT / "data" / "limina_second_wave_candidate_queue.json"
DEFAULT_CSV = ROOT / "data" / "limina_second_wave_candidate_queue.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_second_wave_candidate_queue.md"

ACTIVE_BRANCH_DISCOVERY_IDS = {
    "limina_nhi_pedot_laminin_v0_1": {
        "limina_alg_lam_pedot_lowdose_v0_2",
    },
    "limina_zrc_nd_v0_1": set(),
}

QUEUE_PRIORITIES = {"parallel_screen", "watch", "hold"}


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def candidate_lookup(records: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list):
        return {}
    return {str(record.get("id")): record for record in records if record.get("id")}


def active_discovery_ids(portfolio: dict[str, Any]) -> set[str]:
    active = {str(portfolio.get("active_discovery_candidate") or "")}
    for branch in portfolio.get("branches", []):
        branch_id = str(branch.get("technology_id") or "")
        active.add(branch_id)
        active.update(ACTIVE_BRANCH_DISCOVERY_IDS.get(branch_id, set()))
    return {item for item in active if item}


def first_wave_counts(first_wave: dict[str, Any]) -> dict[str, int]:
    summary = first_wave.get("first_wave_cockpit_summary", {})
    return {
        "confirmations": int(summary.get("confirmation_files_present", 0) or 0),
        "replies": int(summary.get("reply_files_present", 0) or 0),
        "failed_commands": len(first_wave.get("failed_command_ids", [])),
    }


def dependency_hint(item: dict[str, Any], details: dict[str, Any]) -> str:
    text = " ".join([
        str(item.get("near_term_test", "")),
        str(details.get("near_term_test", "")),
        str(details.get("why_it_matters", "")),
    ]).lower()
    if "after the acellular h-a" in text or "after alg-lam-pedot h-a" in text or "h-a blank passes" in text:
        return "requires_primary_h_a_blank_pass"
    if "after zrc" in text or "phase a sentinel" in text:
        return "requires_zrc_phase_a_failure_mode"
    if "after safer pedot" in text or "after alg-lam-pedot" in text:
        return "requires_primary_pedot_baseline"
    if "literature-watch" in text or "watch until" in text:
        return "requires_formulation_access_and_replication"
    return "scope_lock_can_start_now"


def decision_for(item: dict[str, Any], details: dict[str, Any]) -> str:
    priority = str(item.get("priority") or "")
    failures = item.get("gate_failures") or []
    dependency = dependency_hint(item, details)
    if failures:
        return "hold_until_discovery_gate_failure_resolved"
    if priority == "parallel_screen":
        if dependency == "scope_lock_can_start_now":
            return "ready_for_second_wave_scope_lock"
        return "ready_for_second_wave_scope_lock_measurement_dependency"
    if priority == "watch":
        return "watch_after_primary_gate_data"
    return "hold_for_horizon_scan"


def measurement_lane(item: dict[str, Any], details: dict[str, Any]) -> str:
    lane = str(item.get("lane") or details.get("lane") or "")
    candidate_id = str(item.get("id") or "")
    name = str(item.get("name") or "").lower()
    if "external" in lane.lower() or "zwitterionic_external" in candidate_id:
        return "external_material_phase_a_comparator"
    if "pda" in candidate_id or "anchor" in name:
        return "cell_contact_anchor_rescue_coupon"
    if "pedot" in candidate_id or "hydrogel" in candidate_id:
        return "cell_contact_acellular_witness_coupon"
    return "desk_feasibility_then_witness_coupon"


def build_queue(
    ranking: dict[str, Any],
    candidates: dict[str, dict[str, Any]],
    portfolio: dict[str, Any],
    first_wave: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    active_ids = active_discovery_ids(portfolio)
    rows: list[dict[str, Any]] = []
    for ranked in ranking.get("items", []):
        candidate_id = str(ranked.get("id") or "")
        if not candidate_id or candidate_id in active_ids:
            continue
        priority = str(ranked.get("priority") or "")
        if priority not in QUEUE_PRIORITIES:
            continue
        details = candidates.get(candidate_id, {})
        dependency = dependency_hint(ranked, details)
        decision = decision_for(ranked, details)
        row = {
            "queue_rank": len(rows) + 1,
            "candidate_id": candidate_id,
            "name": ranked.get("name") or details.get("name") or "",
            "lane": ranked.get("lane") or details.get("lane") or "",
            "ranking_priority": priority,
            "weighted_score": ranked.get("weighted_score", 0),
            "queue_decision": decision,
            "measurement_lane": measurement_lane(ranked, details),
            "measurement_dependency": dependency,
            "near_term_test": ranked.get("near_term_test") or details.get("near_term_test") or "",
            "scope_lock_action": scope_lock_action(ranked, details, dependency),
            "risk_count": len(ranked.get("known_risks", []) or details.get("known_risks", []) or []),
            "gate_failure_count": len(ranked.get("gate_failures", []) or []),
            "gate_failures": ranked.get("gate_failures", []),
            "evidence_refs": details.get("evidence_refs", ranked.get("evidence_refs", [])),
            "known_risks": ranked.get("known_risks", details.get("known_risks", [])),
            "non_claim_boundary": (
                "Second-wave queue rows are planning artifacts only; they do not create measured "
                "source-file evidence or material suitability."
            ),
        }
        rows.append(row)
        if len(rows) >= limit:
            break

    counts = first_wave_counts(first_wave)
    ready_rows = [row for row in rows if str(row["queue_decision"]).startswith("ready_for_second_wave")]
    watch_rows = [row for row in rows if row["queue_decision"] == "watch_after_primary_gate_data"]
    hold_rows = [row for row in rows if str(row["queue_decision"]).startswith("hold")]
    if ready_rows and counts["confirmations"] == 0 and counts["replies"] == 0:
        status = "second_wave_candidate_queue_ready_while_first_wave_waits"
    elif ready_rows:
        status = "second_wave_candidate_queue_ready"
    elif rows:
        status = "second_wave_candidate_queue_watch_only"
    else:
        status = "no_second_wave_candidate_queue"

    return {
        "status": status,
        "summary": {
            "queue_rows": len(rows),
            "ready_scope_lock_rows": len(ready_rows),
            "watch_rows": len(watch_rows),
            "hold_rows": len(hold_rows),
            "first_wave_confirmations": counts["confirmations"],
            "first_wave_replies": counts["replies"],
            "first_wave_failed_commands": counts["failed_commands"],
            "active_discovery_ids_excluded": sorted(active_ids),
        },
        "rows": rows,
        "next_commands": [
            "python3 scripts/render_limina_second_wave_candidate_queue.py",
            "python3 scripts/run_limina_iteration.py",
        ],
    }


def scope_lock_action(item: dict[str, Any], details: dict[str, Any], dependency: str) -> str:
    lane = measurement_lane(item, details)
    if lane == "cell_contact_anchor_rescue_coupon":
        return (
            "Lock the PDA/primer chemistry, electrode-window mask, extract-blank fields, "
            "and single-coupon H-A/H-B rescue trigger before any live-cell work."
        )
    if lane == "external_material_phase_a_comparator":
        return (
            "Lock coated-surface placement, fouling/adsorption readouts, extract-blank fields, "
            "and ZRC Phase A trigger before procurement or coating outreach."
        )
    if dependency == "requires_formulation_access_and_replication":
        return (
            "Keep as literature watch; require formulation access, independent replication, "
            "and extract chemistry before queueing a witness coupon."
        )
    return (
        "Lock material identity, procurement route, source-file classes, and a tiny acellular "
        "witness-coupon acceptance table."
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "queue_rank",
        "candidate_id",
        "name",
        "lane",
        "ranking_priority",
        "weighted_score",
        "queue_decision",
        "measurement_lane",
        "measurement_dependency",
        "scope_lock_action",
        "near_term_test",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def render_report(result: dict[str, Any], csv_path: Path) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Second-Wave Candidate Queue",
        "",
        "This queue keeps material discovery moving while first-wave H-A/ZRC sourcing waits for real confirmations, replies, and measurements. It is not a suitability claim.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Rows:** {summary['queue_rows']}",
        f"**Ready for scope lock:** {summary['ready_scope_lock_rows']}",
        f"**Watch rows:** {summary['watch_rows']}",
        f"**Hold rows:** {summary['hold_rows']}",
        f"**First-wave confirmations:** {summary['first_wave_confirmations']}",
        f"**First-wave replies:** {summary['first_wave_replies']}",
        f"**CSV:** `{rel(csv_path)}`",
        "",
        "## Queue",
        "",
        "| Rank | Decision | Priority | Score | Candidate | Dependency | Scope action |",
        "| ---: | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['queue_rank']} | `{row['queue_decision']}` | `{row['ranking_priority']}` | "
            f"{float(row['weighted_score']):.3f} | `{row['candidate_id']}` | "
            f"`{row['measurement_dependency']}` | {row['scope_lock_action']} |"
        )

    lines.extend(["", "## Candidate Notes", ""])
    for row in result["rows"]:
        risks = "; ".join(row.get("known_risks", [])) or "-"
        evidence = ", ".join(f"`{ref}`" for ref in row.get("evidence_refs", [])) or "-"
        failures = "; ".join(row.get("gate_failures", [])) or "none"
        lines.extend([
            f"### {row['candidate_id']}",
            "",
            f"- Name: {row['name']}",
            f"- Measurement lane: `{row['measurement_lane']}`",
            f"- Near-term test: {row['near_term_test']}",
            f"- Evidence refs: {evidence}",
            f"- Gate failures: {failures}",
            f"- Known risks: {risks}",
            "",
        ])

    lines.extend([
        "## Boundary",
        "",
        "- A second-wave row can justify scope locking, procurement scouting, or a witness-coupon plan.",
        "- It cannot bypass H-A, ZRC Phase A, source-file provenance, or the final suitability claim audit.",
        "- If a first-wave branch returns real measurements, rerun the full iteration before promoting any second-wave candidate.",
        "",
        "## Next Commands",
        "",
    ])
    lines.extend(f"- `{command}`" for command in result.get("next_commands", []))
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA second-wave candidate queue.")
    parser.add_argument("--ranking", type=Path, default=DEFAULT_RANKING)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument("--first-wave", type=Path, default=DEFAULT_FIRST_WAVE)
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_queue(
        ranking=load_json(args.ranking),
        candidates=candidate_lookup(load_json(args.candidates)),
        portfolio=load_json(args.portfolio),
        first_wave=load_json(args.first_wave),
        limit=args.limit,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, result["rows"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result, args.csv_out), encoding="utf-8")
    print(f"Second-wave candidate queue: {result['status']}")
    print(f"Rows: {result['summary']['queue_rows']}")
    print(f"Ready for scope lock: {result['summary']['ready_scope_lock_rows']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
