#!/usr/bin/env python3
"""Suggest the next adaptive ZRC-ND non-cell measurement batch."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = ROOT / "data" / "zrc_nd_execution_queue.csv"
DEFAULT_RUNS = ROOT / "data" / "zrc_nd_validation_runs_active.csv"
DEFAULT_RESULTS = ROOT / "data" / "zrc_nd_validation_results.json"
DEFAULT_CRITERIA = ROOT / "data" / "readiness_criteria.json"
DEFAULT_SENTINEL = ROOT / "data" / "zrc_nd_sentinel_interpretation.json"
DEFAULT_OUT = ROOT / "data" / "zrc_nd_next_measurements.csv"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_next_measurements.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_next_measurements.md"

PHASE_ORDER = ["A", "B", "C"]
PHASE_ARTICLES = {
    "A": [
        "no_module_static_control",
        "lead_zrc_nd_3p5m_guard",
        "baseline_rc_3p5m_guard",
        "challenge_zrc_nd_10m_guard",
    ],
    "B": [
        "no_module_static_control",
        "lead_zrc_nd_3p5m_guard",
        "baseline_rc_3p5m_guard",
        "challenge_zrc_nd_10m_guard",
    ],
    "C": [
        "no_module_static_control",
        "lead_zrc_nd_3p5m_guard",
        "baseline_rc_3p5m_guard",
        "bulk_exchange_reference",
    ],
}
SENTINEL_TIMEPOINTS = {"0 h", "24 h"}

LEAD_SENTINEL_STOP_ACTIONS = [
    "Do not start Phase B/C non-cell rows or any biological Phase D rows for the lead article.",
    "Inspect the lead blank-integrity drift components: housing, membrane rinse/preconditioning, PDA/polyMPC coating, guard filter, and medium lot.",
    "Repeat Phase A sentinel with no-module control, baseline_rc_3p5m_guard, and lead_zrc_nd_3p5m_guard after the suspected drift source is isolated.",
    "If baseline_rc_3p5m_guard passes while the lead fails, demote the PDA/polyMPC coating route and branch to zrc_nd_3p5k_unmodified_guard.",
    "If all material rows fail against the no-module control, treat housing/rinsing/medium handling as the primary failure mode before changing membrane chemistry.",
]

COMPARATOR_QUARANTINE_ACTIONS = [
    "Continue lead-only advancement cautiously, but quarantine failed comparators from superiority claims until retested.",
    "Retest the failed comparator with a fresh article lot and matched no-module control before using it as a benchmark.",
]


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else [
        "priority",
        "run_id",
        "phase",
        "timepoint",
        "replicate",
        "article_id",
        "variant_id",
        "gate_role",
        "readout_groups",
        "recommendation_reason",
        "must_have_fields",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def measured_ids(rows: list[dict[str, str]]) -> set[str]:
    return {row["run_id"] for row in rows if row.get("run_id")}


def passed_replicates(results: dict[str, Any]) -> dict[str, set[str]]:
    summary = results.get("summary", {})
    raw = summary.get("passed_lead_replicates_by_phase", {})
    return {phase: set(str(value) for value in values) for phase, values in raw.items()}


def candidate_rows(
    queue: list[dict[str, str]],
    measured: set[str],
    phase: str,
    replicate: str,
    mode: str,
) -> list[dict[str, str]]:
    articles = set(PHASE_ARTICLES[phase])
    rows = [
        row for row in queue
        if row.get("phase") == phase
        and row.get("replicate") == replicate
        and row.get("article_id") in articles
        and row.get("run_id") not in measured
    ]
    if mode == "adaptive":
        rows = [row for row in rows if row.get("timepoint") in SENTINEL_TIMEPOINTS]
    return sorted(rows, key=lambda row: int(row.get("queue_order") or 0))


def annotate(rows: list[dict[str, str]], reason: str) -> list[dict[str, str]]:
    annotated: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        annotated.append({
            "priority": str(index),
            "run_id": row.get("run_id", ""),
            "phase": row.get("phase", ""),
            "timepoint": row.get("timepoint", ""),
            "replicate": row.get("replicate", ""),
            "article_id": row.get("article_id", ""),
            "variant_id": row.get("variant_id", ""),
            "gate_role": row.get("gate_role", ""),
            "readout_groups": row.get("readout_groups", ""),
            "recommendation_reason": reason,
            "must_have_fields": row.get("must_have_fields", ""),
        })
    return annotated


def common_result_fields(
    results: dict[str, Any],
    criteria: dict[str, Any],
    mode: str,
    sentinel: dict[str, Any],
) -> dict[str, Any]:
    summary = results.get("summary", {})
    reps = passed_replicates(results)
    min_reps = int(criteria["non_cell_validation_required"]["min_passed_lead_replicates_per_phase"])
    return {
        "mode": mode,
        "results_status": summary.get("status", "no_data"),
        "min_passed_lead_replicates_per_phase": min_reps,
        "passed_lead_replicates_by_phase": {phase: sorted(values) for phase, values in reps.items()},
        "sentinel_status": sentinel.get("status", "missing"),
        "sentinel_next_action": sentinel.get("next_action", ""),
        "remediation_actions": [],
    }


def block_for_sentinel_status(
    sentinel: dict[str, Any],
    common: dict[str, Any],
    measured: set[str],
) -> dict[str, Any] | None:
    status = sentinel.get("status", "missing")
    if status == "sentinel_lead_fails_stop":
        return {
            **common,
            "status": "stop_non_cell_measurements_lead_failed_sentinel",
            "reason": status,
            "recommended_rows": [],
            "remediation_actions": LEAD_SENTINEL_STOP_ACTIONS,
        }
    if status == "sentinel_needs_more_data":
        return {
            **common,
            "status": "complete_sentinel_before_more_measurements",
            "reason": status,
            "recommended_rows": [],
            "remediation_actions": [
                "Fill every required Phase A medium-integrity field for the lead article and matched no-module control.",
                "Re-run the sentinel interpreter before selecting Phase A replicate 2 or any Phase B/C rows.",
            ],
        }
    if measured and status in {"missing", "no_sentinel_rows"}:
        return {
            **common,
            "status": "interpret_sentinel_before_more_measurements",
            "reason": status,
            "recommended_rows": [],
            "remediation_actions": [
                "Run the sentinel interpreter on the measured Phase A rows and pass its JSON into this selector.",
                "Do not use evaluator replicate coverage as a substitute for the Phase A material-blank gate.",
            ],
        }
    return None


def suggest(
    queue: list[dict[str, str]],
    runs: list[dict[str, str]],
    results: dict[str, Any],
    criteria: dict[str, Any],
    sentinel: dict[str, Any],
    mode: str,
    max_rows: int,
) -> dict[str, Any]:
    measured = measured_ids(runs)
    reps = passed_replicates(results)
    common = common_result_fields(results, criteria, mode, sentinel)
    min_reps = common["min_passed_lead_replicates_per_phase"]
    sentinel_block = block_for_sentinel_status(sentinel, common, measured)
    if sentinel_block is not None:
        return sentinel_block

    if not measured:
        rows = candidate_rows(queue, measured, "A", "1", "adaptive")
        reason = "phase_a_sentinel_no_measured_rows"
        return {
            **common,
            "status": "needs_phase_a_sentinel",
            "reason": reason,
            "recommended_rows": annotate(rows[:max_rows], reason),
        }

    for phase in PHASE_ORDER:
        passed = reps.get(phase, set())
        if len(passed) >= min_reps:
            continue
        for replicate in ["1", "2", "3"]:
            if replicate in passed:
                continue
            rows = candidate_rows(queue, measured, phase, replicate, mode)
            if rows:
                reason = f"complete_phase_{phase}_replicate_{replicate}"
                result = {
                    **common,
                    "status": "needs_more_non_cell_measurements",
                    "reason": reason,
                    "recommended_rows": annotate(rows[:max_rows], reason),
                }
                if sentinel.get("status") == "sentinel_lead_passes_comparator_issue":
                    result["remediation_actions"] = COMPARATOR_QUARANTINE_ACTIONS
                return result

    return {
        **common,
        "status": "non_cell_measurement_recommendations_complete",
        "reason": "non_cell_replicate_coverage_satisfied",
        "recommended_rows": [],
    }


def render_report(result: dict[str, Any], out_csv: Path) -> str:
    rows = result["recommended_rows"]
    lines = [
        "# ZRC-ND Next Measurements",
        "",
        f"**Status:** `{result['status']}`",
        f"**Mode:** `{result['mode']}`",
        f"**Reason:** `{result['reason']}`",
        f"**Evaluator status:** `{result['results_status']}`",
        f"**Sentinel status:** `{result.get('sentinel_status', 'missing')}`",
        f"**Sentinel next action:** {result.get('sentinel_next_action') or '-'}",
        f"**Output CSV:** `{out_csv}`",
        "",
        "## Sentinel Gate",
        "",
        "The Phase A material-blank sentinel is a front-door gate for adaptive non-cell advancement.",
        "",
        f"- Status: `{result.get('sentinel_status', 'missing')}`",
        f"- Action: {result.get('sentinel_next_action') or '-'}",
        "",
        "## Replicate Coverage",
        "",
        f"Required passed lead replicates per phase: {result['min_passed_lead_replicates_per_phase']}",
        "",
        "| Phase | Passed lead replicates |",
        "| --- | --- |",
    ]
    coverage = result["passed_lead_replicates_by_phase"]
    for phase in PHASE_ORDER:
        values = coverage.get(phase, [])
        lines.append(f"| {phase} | {', '.join(values) if values else '-'} |")

    actions = result.get("remediation_actions", [])
    if actions:
        lines.extend(["", "## Remediation Or Branch Actions", ""])
        lines.extend([f"- {action}" for action in actions])

    lines.extend(["", "## Recommended Rows", ""])
    if not rows:
        lines.append("No non-cell measurement rows are recommended by this selector.")
        lines.append("")
        return "\n".join(lines)

    lines.extend([
        "| Priority | Run | Phase | Timepoint | Replicate | Article | Role | Readouts |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- |",
    ])
    for row in rows:
        lines.append(
            f"| {row['priority']} | `{row['run_id']}` | {row['phase']} | {row['timepoint']} | "
            f"{row['replicate']} | `{row['article_id']}` | `{row['gate_role']}` | {row['readout_groups']} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- `adaptive` mode recommends a small, high-information batch first; it is not enough for a suitability claim.",
        "- A suitability claim still requires the readiness audit to pass with measured non-cell and biological rows.",
        "- Keep all recommended rows tied to their deterministic `run_id` so evaluator and completeness checks can reuse them.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Suggest next ZRC-ND non-cell measurements.")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--criteria", type=Path, default=DEFAULT_CRITERIA)
    parser.add_argument("--sentinel", type=Path, default=DEFAULT_SENTINEL)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--mode", choices=["adaptive", "claim-complete"], default="adaptive")
    parser.add_argument("--max-rows", type=int, default=16)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    queue = load_csv(args.queue)
    runs = load_csv(args.runs)
    results = load_json(args.results)
    criteria = load_json(args.criteria)
    sentinel = load_json(args.sentinel)
    result = suggest(queue, runs, results, criteria, sentinel, args.mode, args.max_rows)
    write_csv(result["recommended_rows"], args.out)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result, args.out), encoding="utf-8")
    print(f"Recommendation: {result['status']}")
    print(f"Recommended rows: {len(result['recommended_rows'])}")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
