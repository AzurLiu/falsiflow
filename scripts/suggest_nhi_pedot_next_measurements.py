#!/usr/bin/env python3
"""Suggest the next adaptive NHI-PEDOT measurement batch."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLANNED = ROOT / "data" / "nhi_pedot_planned_runs.csv"
DEFAULT_RUNS = ROOT / "data" / "nhi_pedot_runs_template.csv"
DEFAULT_RESULTS = ROOT / "data" / "nhi_pedot_results.json"
DEFAULT_OUT = ROOT / "data" / "nhi_pedot_next_measurements.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_next_measurements.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_next_measurements.md"

PHASE_ORDER = ["H-A", "H-B", "H-C"]
PHASE_ARTICLES = {
    "H-A": [
        "no_coating_mea_control",
        "hydrogel_laminin_control",
        "lead_nhi_pedot_low_loading",
        "challenge_nhi_pedot_high_loading",
    ],
    "H-B": [
        "hydrogel_laminin_control",
        "lead_nhi_pedot_low_loading",
        "challenge_nhi_pedot_high_loading",
    ],
    "H-C": [
        "laminin_only_control",
        "hydrogel_laminin_control",
        "lead_nhi_pedot_low_loading",
        "challenge_nhi_pedot_high_loading",
    ],
}
PHASE_TIMEPOINTS = {
    "H-A": {"0 h", "24 h", "72 h"},
    "H-B": {"pre-soak", "24 h soak", "72 h soak", "post-cycling"},
    "H-C": {"24 h", "7 d", "14 d"},
}
READOUT_GROUPS = {
    "H-A": "medium_integrity;physical_stability",
    "H-B": "physical_stability;electrochemical_interface",
    "H-C": "neural_viability;neurite_and_morphology;network_activity",
}
MUST_HAVE_FIELDS = {
    "H-A": [
        "pH_initial",
        "pH_final",
        "osmolality_initial_mOsm_kg",
        "osmolality_final_mOsm_kg",
        "conductivity_initial_mS_cm",
        "conductivity_final_mS_cm",
        "visible_precipitate",
        "visible_shedding",
        "swelling_fraction",
        "delamination_score",
        "optical_transparency_fraction",
    ],
    "H-B": [
        "swelling_fraction",
        "delamination_score",
        "optical_transparency_fraction",
        "eis_1khz_initial_ohm",
        "eis_1khz_final_ohm",
        "charge_storage_capacity_initial",
        "charge_storage_capacity_final",
    ],
    "H-C": [
        "viability_fraction",
        "ldh_fold_control",
        "neurite_coverage_fraction",
        "mean_neurite_length_um",
        "electrode_yield_fraction",
        "spike_rate_hz",
        "burst_rate_hz",
    ],
}

STOP_ACTIONS = [
    "Do not advance NHI-PEDOT lead to H-B/H-C while lead failures remain unresolved.",
    "Branch by failed gate: reduce PEDOT:PSS loading, change hydrogel matrix/crosslinking, strengthen rinse/neutralization, or demote to hydrogel-laminin control.",
    "Repeat H-A sentinel after remediation before exposing live neural cultures.",
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
    raw = results.get("summary", {}).get("passed_lead_replicates_by_phase", {})
    return {phase: set(str(value) for value in values) for phase, values in raw.items()}


def candidate_rows(
    planned: list[dict[str, str]],
    measured: set[str],
    phase: str,
    replicate: str,
) -> list[dict[str, str]]:
    articles = set(PHASE_ARTICLES[phase])
    article_order = {article: index for index, article in enumerate(PHASE_ARTICLES[phase])}
    timepoints = PHASE_TIMEPOINTS[phase]
    timepoint_order = {timepoint: index for index, timepoint in enumerate(
        [timepoint for timepoint in ["0 h", "pre-soak", "24 h", "24 h soak", "72 h", "72 h soak", "post-cycling", "7 d", "14 d"] if timepoint in timepoints]
    )}
    rows = [
        row for row in planned
        if row.get("phase") == phase
        and row.get("replicate") == replicate
        and row.get("article_id") in articles
        and row.get("timepoint") in timepoints
        and row.get("run_id") not in measured
    ]
    return sorted(rows, key=lambda row: (
        article_order.get(row.get("article_id", ""), 99),
        timepoint_order.get(row.get("timepoint", ""), 99),
        row.get("run_id", ""),
    ))


def annotate(rows: list[dict[str, str]], reason: str) -> list[dict[str, str]]:
    annotated = []
    for index, row in enumerate(rows, start=1):
        phase = row.get("phase", "")
        annotated.append({
            "priority": str(index),
            "run_id": row.get("run_id", ""),
            "phase": phase,
            "timepoint": row.get("timepoint", ""),
            "replicate": row.get("replicate", ""),
            "article_id": row.get("article_id", ""),
            "variant_id": row.get("variant_id", ""),
            "readout_groups": READOUT_GROUPS.get(phase, ""),
            "recommendation_reason": reason,
            "must_have_fields": ";".join(MUST_HAVE_FIELDS.get(phase, [])),
        })
    return annotated


def common_fields(results: dict[str, Any]) -> dict[str, Any]:
    summary = results.get("summary", {})
    reps = passed_replicates(results)
    return {
        "results_status": summary.get("status", "no_data"),
        "min_passed_lead_replicates_per_phase": int(summary.get("min_passed_lead_replicates_per_phase", 3)),
        "passed_lead_replicates_by_phase": {phase: sorted(values) for phase, values in reps.items()},
        "remediation_actions": [],
    }


def suggest(
    planned: list[dict[str, str]],
    runs: list[dict[str, str]],
    results: dict[str, Any],
    max_rows: int,
) -> dict[str, Any]:
    measured = measured_ids(runs)
    common = common_fields(results)
    results_status = common["results_status"]
    passed = passed_replicates(results)

    if results_status == "lead_has_failures":
        return {
            **common,
            "status": "stop_nhi_pedot_lead_failed_gates",
            "reason": "lead_has_failures",
            "recommended_rows": [],
            "remediation_actions": STOP_ACTIONS,
        }

    if results_status == "nhi_pedot_passes_gates":
        return {
            **common,
            "status": "nhi_pedot_coupon_gates_complete",
            "reason": "all_h_a_h_b_h_c_lead_replicates_passed",
            "recommended_rows": [],
            "remediation_actions": [
                "Design a longer CL1-like MEA network stability pilot; do not treat coupon fixtures as final suitability evidence.",
            ],
        }

    if measured and results_status == "no_data":
        return {
            **common,
            "status": "evaluate_measured_nhi_pedot_rows_first",
            "reason": "measured_rows_exist_but_results_no_data",
            "recommended_rows": [],
            "remediation_actions": [
                "Run evaluate_nhi_pedot_runs.py on the measured active-runs CSV before selecting more rows.",
            ],
        }

    if not measured:
        reason = "phase_h_a_sentinel_no_measured_rows"
        rows = candidate_rows(planned, measured, "H-A", "1")
        return {
            **common,
            "status": "needs_h_a_sentinel",
            "reason": reason,
            "recommended_rows": annotate(rows[:max_rows], reason),
        }

    min_reps = common["min_passed_lead_replicates_per_phase"]
    for phase in PHASE_ORDER:
        phase_passed = passed.get(phase, set())
        if len(phase_passed) >= min_reps:
            continue
        for replicate in ["1", "2", "3"]:
            if replicate in phase_passed:
                continue
            rows = candidate_rows(planned, measured, phase, replicate)
            if rows:
                reason = f"complete_phase_{phase}_replicate_{replicate}"
                return {
                    **common,
                    "status": "needs_more_nhi_pedot_measurements",
                    "reason": reason,
                    "recommended_rows": annotate(rows[:max_rows], reason),
                }

    return {
        **common,
        "status": "nhi_pedot_measurement_recommendations_complete",
        "reason": "replicate_coverage_satisfied_or_no_unmeasured_rows",
        "recommended_rows": [],
    }


def render_report(result: dict[str, Any], out_csv: Path) -> str:
    lines = [
        "# NHI-PEDOT Next Measurements",
        "",
        f"**Status:** `{result['status']}`",
        f"**Reason:** `{result['reason']}`",
        f"**Evaluator status:** `{result['results_status']}`",
        f"**Output CSV:** `{out_csv}`",
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

    rows = result["recommended_rows"]
    lines.extend(["", "## Recommended Rows", ""])
    if not rows:
        lines.extend([
            "No NHI-PEDOT measurement rows are recommended by this selector.",
            "",
        ])
        return "\n".join(lines)

    lines.extend([
        "| Priority | Run | Phase | Timepoint | Replicate | Article | Readouts |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ])
    for row in rows:
        lines.append(
            f"| {row['priority']} | `{row['run_id']}` | {row['phase']} | {row['timepoint']} | "
            f"{row['replicate']} | `{row['article_id']}` | {row['readout_groups']} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- H-A sentinel rows are the first decisive acellular material-contact check.",
        "- H-B/H-C must not start if H-A lead rows fail medium-integrity or physical-stability gates.",
        "- A real suitability claim still requires measured data; synthetic fixtures are evaluator regressions only.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Suggest next NHI-PEDOT measurements.")
    parser.add_argument("--planned", type=Path, default=DEFAULT_PLANNED)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-rows", type=int, default=16)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = suggest(
        load_csv(args.planned),
        load_csv(args.runs),
        load_json(args.results),
        args.max_rows,
    )
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
