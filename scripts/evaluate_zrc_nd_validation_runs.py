#!/usr/bin/env python3
"""Evaluate ZRC-ND validation run rows against package gates.

The evaluator treats measured data as evidence only when it can compare a test
article against the matched no-module control. With an empty or missing run CSV,
it writes a template and reports that no experimental evidence exists yet.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "zrc_nd_3p5k_guard_validation_package.json"
DEFAULT_RUNS = ROOT / "data" / "zrc_nd_validation_runs_active.csv"
DEFAULT_RESULTS = ROOT / "data" / "zrc_nd_validation_results.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_validation_results.md"

LEAD_VARIANT = "zrc_nd_3p5k_mpc_guard"
BASELINE_VARIANT = "zrc_nd_3p5k_unmodified_guard"
CHALLENGE_VARIANT = "zrc_nd_10k_mpc_guard"
CONTROL_ARTICLES = {"no_module_static_control", "bulk_exchange_reference"}
REQUIRED_PHASES = {"A", "B", "C"}
REQUIRED_GATES_BY_PHASE = {
    "A": {"blank_integrity_gate"},
    "B": {
        "blank_integrity_gate",
        "factor_retention_gate",
        "waste_clearance_gate",
        "fouling_stability_gate",
    },
    "C": {
        "blank_integrity_gate",
        "factor_retention_gate",
        "waste_clearance_gate",
        "fouling_stability_gate",
    },
}

RETENTION_FIELDS = {
    "bdnf": ("bdnf_initial_pg_ml", "bdnf_final_pg_ml"),
    "ngf": ("ngf_initial_pg_ml", "ngf_final_pg_ml"),
    "albumin": ("albumin_initial", "albumin_final"),
    "transferrin": ("transferrin_initial", "transferrin_final"),
    "total_protein": ("total_protein_initial", "total_protein_final"),
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_template(package: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=package["data_capture_fields"])
        writer.writeheader()


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def parse_float(row: dict[str, str] | None, field: str) -> float | None:
    if row is None:
        return None
    value = row.get(field, "")
    if value in ("", None):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def pct_change(initial: float | None, final: float | None) -> float | None:
    if initial is None or final is None or initial == 0:
        return None
    return (final - initial) / initial


def delta(initial: float | None, final: float | None) -> float | None:
    if initial is None or final is None:
        return None
    return final - initial


def clearance(row: dict[str, str] | None, initial_field: str, final_field: str) -> float | None:
    change = pct_change(parse_float(row, initial_field), parse_float(row, final_field))
    if change is None:
        return None
    return -change


def recovery(row: dict[str, str] | None, prefix: str) -> float | None:
    initial_field, final_field = RETENTION_FIELDS[prefix]
    initial = parse_float(row, initial_field)
    final = parse_float(row, final_field)
    if initial is None or final is None or initial == 0:
        return None
    return final / initial


def visible_precipitate(row: dict[str, str] | None) -> bool | None:
    if row is None:
        return None
    value = row.get("visible_precipitate", "").strip().lower()
    if value in ("", "na", "n/a", "unknown"):
        return None
    return value in ("yes", "true", "1", "y")


def pass_fail(value: bool | None) -> str:
    if value is None:
        return "not_evaluable"
    return "pass" if value else "fail"


def is_baseline_timepoint(row: dict[str, str]) -> bool:
    return row.get("timepoint", "").strip().lower() in {"0 h", "0h", "0"}


def required_gates_for_phase(phase: str) -> set[str]:
    return REQUIRED_GATES_BY_PHASE.get(phase, set().union(*REQUIRED_GATES_BY_PHASE.values()))


def row_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (row.get("phase", ""), row.get("timepoint", ""), row.get("replicate", ""))


def control_index(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    controls: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        if row.get("article_id") == "no_module_static_control":
            controls[row_key(row)] = row
    return controls


def ratio(value: float | None, control_value: float | None) -> float | None:
    if value is None or control_value is None or control_value == 0:
        return None
    return value / control_value


def mean_or_none(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return mean(clean)


def evaluate_row(row: dict[str, str], control: dict[str, str] | None = None) -> dict[str, Any]:
    article_id = row.get("article_id", "")
    is_control = article_id in CONTROL_ARTICLES
    is_baseline = is_baseline_timepoint(row)

    p_h_delta = delta(parse_float(row, "pH_initial"), parse_float(row, "pH_final"))
    control_p_h_delta = delta(parse_float(control, "pH_initial"), parse_float(control, "pH_final"))
    p_h_delta_vs_control = None
    if p_h_delta is not None and control_p_h_delta is not None:
        p_h_delta_vs_control = p_h_delta - control_p_h_delta

    osmolality_change = pct_change(
        parse_float(row, "osmolality_initial_mOsm_kg"),
        parse_float(row, "osmolality_final_mOsm_kg"),
    )
    control_osmolality_change = pct_change(
        parse_float(control, "osmolality_initial_mOsm_kg"),
        parse_float(control, "osmolality_final_mOsm_kg"),
    )
    osmolality_change_vs_control = None
    if osmolality_change is not None and control_osmolality_change is not None:
        osmolality_change_vs_control = osmolality_change - control_osmolality_change

    conductivity_change = pct_change(
        parse_float(row, "conductivity_initial_mS_cm"),
        parse_float(row, "conductivity_final_mS_cm"),
    )
    control_conductivity_change = pct_change(
        parse_float(control, "conductivity_initial_mS_cm"),
        parse_float(control, "conductivity_final_mS_cm"),
    )
    conductivity_change_vs_control = None
    if conductivity_change is not None and control_conductivity_change is not None:
        conductivity_change_vs_control = conductivity_change - control_conductivity_change

    precipitate = visible_precipitate(row)
    blank_values = [p_h_delta_vs_control, osmolality_change_vs_control, conductivity_change_vs_control]
    blank_evaluable = all(value is not None for value in blank_values) and precipitate is not None
    blank_pass = None
    if blank_evaluable:
        blank_pass = (
            abs(p_h_delta_vs_control) <= 0.10
            and abs(osmolality_change_vs_control) <= 0.05
            and abs(conductivity_change_vs_control) <= 0.05
            and not precipitate
        )

    raw_recoveries = {prefix: recovery(row, prefix) for prefix in RETENTION_FIELDS}
    control_recoveries = {prefix: recovery(control, prefix) for prefix in RETENTION_FIELDS}
    normalized_recoveries = {
        prefix: ratio(raw_recoveries[prefix], control_recoveries[prefix])
        for prefix in RETENTION_FIELDS
    }
    retention_evaluable = all(value is not None for value in normalized_recoveries.values())
    retention_pass = None
    if retention_evaluable:
        retention_pass = all(value >= 0.90 for value in normalized_recoveries.values() if value is not None)

    lactate_clearance = clearance(row, "lactate_initial_mM", "lactate_final_mM")
    control_lactate_clearance = clearance(control, "lactate_initial_mM", "lactate_final_mM")
    ammonia_clearance = clearance(row, "ammonia_initial_uM", "ammonia_final_uM")
    control_ammonia_clearance = clearance(control, "ammonia_initial_uM", "ammonia_final_uM")
    net_lactate_clearance = None
    net_ammonia_clearance = None
    if lactate_clearance is not None and control_lactate_clearance is not None:
        net_lactate_clearance = lactate_clearance - control_lactate_clearance
    if ammonia_clearance is not None and control_ammonia_clearance is not None:
        net_ammonia_clearance = ammonia_clearance - control_ammonia_clearance
    clearance_evaluable = net_lactate_clearance is not None and net_ammonia_clearance is not None
    clearance_pass = None
    if clearance_evaluable:
        clearance_pass = net_lactate_clearance >= 0.25 and net_ammonia_clearance >= 0.25

    flow_change = pct_change(
        parse_float(row, "flow_resistance_initial"),
        parse_float(row, "flow_resistance_final"),
    )
    fouling_pass = None
    if flow_change is not None:
        fouling_pass = abs(flow_change) <= 0.20

    gate_results = {
        "blank_integrity_gate": pass_fail(blank_pass),
        "factor_retention_gate": pass_fail(retention_pass),
        "waste_clearance_gate": pass_fail(clearance_pass),
        "fouling_stability_gate": pass_fail(fouling_pass),
        "lead_superiority_gate": "not_evaluable",
    }
    if is_control:
        gate_results = {key: "not_evaluable" for key in gate_results}
        status = "control"
    elif is_baseline:
        gate_results = {key: "not_evaluable" for key in gate_results}
        status = "baseline"
    else:
        required_gates = required_gates_for_phase(row.get("phase", ""))
        required_statuses = [gate_results[gate] for gate in sorted(required_gates)]
        failed = any(value == "fail" for value in required_statuses)
        passed = required_statuses and all(value == "pass" for value in required_statuses)
        status = "fail" if failed else "pass_partial" if passed else "not_evaluable"

    return {
        "run_id": row.get("run_id", ""),
        "article_id": article_id,
        "variant_id": row.get("variant_id", ""),
        "control_run_id": "" if is_control else control.get("run_id", "") if control else "",
        "phase": row.get("phase", ""),
        "timepoint": row.get("timepoint", ""),
        "replicate": row.get("replicate", ""),
        "metrics": {
            "pH_delta": p_h_delta,
            "pH_delta_vs_control": p_h_delta_vs_control,
            "osmolality_fractional_change": osmolality_change,
            "osmolality_fractional_change_vs_control": osmolality_change_vs_control,
            "conductivity_fractional_change": conductivity_change,
            "conductivity_fractional_change_vs_control": conductivity_change_vs_control,
            "raw_recoveries": raw_recoveries,
            "control_recoveries": control_recoveries,
            "normalized_recoveries": normalized_recoveries,
            "lactate_clearance_fraction": lactate_clearance,
            "net_lactate_clearance_vs_control": net_lactate_clearance,
            "ammonia_clearance_fraction": ammonia_clearance,
            "net_ammonia_clearance_vs_control": net_ammonia_clearance,
            "flow_resistance_fractional_change": flow_change,
        },
        "gate_results": gate_results,
        "status": status,
    }


def min_normalized_retention(evaluation: dict[str, Any]) -> float | None:
    recoveries = evaluation["metrics"]["normalized_recoveries"]
    values = [value for value in recoveries.values() if value is not None]
    if not values:
        return None
    return min(values)


def abs_flow_change(evaluation: dict[str, Any]) -> float | None:
    value = evaluation["metrics"]["flow_resistance_fractional_change"]
    if value is None:
        return None
    return abs(value)


def aggregate_lead_superiority(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    by_key_variant = {
        (item["phase"], item["timepoint"], item["replicate"], item["variant_id"]): item
        for item in evaluations
        if item.get("variant_id") and item.get("status") != "baseline"
    }
    matched_groups: list[dict[str, dict[str, Any]]] = []
    for phase, timepoint, replicate, variant in by_key_variant:
        if variant != LEAD_VARIANT:
            continue
        group = {
            "lead": by_key_variant.get((phase, timepoint, replicate, LEAD_VARIANT)),
            "baseline": by_key_variant.get((phase, timepoint, replicate, BASELINE_VARIANT)),
            "challenge": by_key_variant.get((phase, timepoint, replicate, CHALLENGE_VARIANT)),
        }
        if group["lead"] and (group["baseline"] or group["challenge"]):
            matched_groups.append(group)

    lead_retention = [min_normalized_retention(group["lead"]) for group in matched_groups]
    baseline_retention = [
        min_normalized_retention(group["baseline"]) for group in matched_groups
        if group.get("baseline")
    ]
    challenge_retention = [
        min_normalized_retention(group["challenge"]) for group in matched_groups
        if group.get("challenge")
    ]
    lead_flow = [abs_flow_change(group["lead"]) for group in matched_groups]
    baseline_flow = [
        abs_flow_change(group["baseline"]) for group in matched_groups
        if group.get("baseline")
    ]

    metrics = {
        "matched_groups": len(matched_groups),
        "lead_min_retention_mean": mean_or_none(lead_retention),
        "baseline_min_retention_mean": mean_or_none(baseline_retention),
        "challenge_min_retention_mean": mean_or_none(challenge_retention),
        "lead_abs_flow_change_mean": mean_or_none(lead_flow),
        "baseline_abs_flow_change_mean": mean_or_none(baseline_flow),
    }

    lead_vs_baseline = None
    if metrics["lead_min_retention_mean"] is not None and metrics["baseline_min_retention_mean"] is not None:
        lead_vs_baseline = metrics["lead_min_retention_mean"] >= metrics["baseline_min_retention_mean"] + 0.02
    if (
        not lead_vs_baseline
        and metrics["lead_abs_flow_change_mean"] is not None
        and metrics["baseline_abs_flow_change_mean"] is not None
    ):
        lead_vs_baseline = metrics["lead_abs_flow_change_mean"] <= metrics["baseline_abs_flow_change_mean"] - 0.05

    lead_vs_challenge = None
    if metrics["lead_min_retention_mean"] is not None and metrics["challenge_min_retention_mean"] is not None:
        lead_vs_challenge = metrics["lead_min_retention_mean"] >= metrics["challenge_min_retention_mean"] + 0.02

    if lead_vs_baseline is None or lead_vs_challenge is None:
        status = "not_evaluable"
    elif lead_vs_baseline and lead_vs_challenge:
        status = "pass"
    else:
        status = "fail"

    return {
        "gate": "lead_superiority_gate",
        "status": status,
        "lead_vs_baseline": pass_fail(lead_vs_baseline),
        "lead_vs_challenge": pass_fail(lead_vs_challenge),
        "metrics": metrics,
    }


def apply_aggregate_gates(
    evaluations: list[dict[str, Any]],
    aggregate: dict[str, Any],
) -> list[dict[str, Any]]:
    for item in evaluations:
        if item.get("variant_id") == LEAD_VARIANT:
            item["gate_results"]["lead_superiority_gate"] = aggregate["status"]
            if item["status"] not in {"control", "baseline"}:
                if item["status"] == "fail" or aggregate["status"] == "fail":
                    item["status"] = "fail"
                elif item["status"] == "pass_partial" and aggregate["status"] == "pass":
                    item["status"] = "pass"
                else:
                    item["status"] = "not_evaluable"
    return evaluations


def summarize(evaluations: list[dict[str, Any]], aggregate: dict[str, Any]) -> dict[str, Any]:
    if not evaluations:
        return {
            "status": "no_data",
            "rows": 0,
            "lead_rows": 0,
            "failed_rows": 0,
            "fully_or_partially_passing_rows": 0,
            "phase_coverage": [],
            "passed_lead_replicates_by_phase": {},
            "aggregate_lead_superiority": aggregate["status"],
        }

    failed = [item for item in evaluations if item["status"] == "fail"]
    passing = [item for item in evaluations if item["status"] in {"pass", "pass_partial"}]
    lead_rows = [
        item for item in evaluations
        if item.get("variant_id") == LEAD_VARIANT and item.get("status") != "baseline"
    ]
    lead_failures = [item for item in lead_rows if item["status"] == "fail"]
    lead_not_evaluable = [item for item in lead_rows if item["status"] == "not_evaluable"]
    phase_coverage = sorted({item["phase"] for item in lead_rows if item["status"] == "pass"})
    passed_lead_replicates_by_phase = {
        phase: sorted({
            item["replicate"] for item in lead_rows
            if item["phase"] == phase and item["status"] == "pass"
        })
        for phase in phase_coverage
    }

    if not lead_rows:
        status = "needs_more_data"
    elif lead_failures:
        status = "lead_has_failures"
    elif lead_not_evaluable or aggregate["status"] == "not_evaluable":
        status = "needs_more_data"
    elif set(phase_coverage) >= REQUIRED_PHASES:
        status = "lead_passes_non_cell_gates"
    else:
        status = "lead_pass_partial"

    return {
        "status": status,
        "rows": len(evaluations),
        "lead_rows": len(lead_rows),
        "failed_rows": len(failed),
        "fully_or_partially_passing_rows": len(passing),
        "phase_coverage": phase_coverage,
        "passed_lead_replicates_by_phase": passed_lead_replicates_by_phase,
        "aggregate_lead_superiority": aggregate["status"],
    }


def write_results(
    evaluations: list[dict[str, Any]],
    aggregate: dict[str, Any],
    summary: dict[str, Any],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"summary": summary, "aggregate_gates": [aggregate], "evaluations": evaluations}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def render_report(
    summary: dict[str, Any],
    aggregate: dict[str, Any],
    evaluations: list[dict[str, Any]],
    runs_path: Path,
) -> str:
    def required_failed_gates(item: dict[str, Any]) -> list[str]:
        if item["status"] in {"control", "baseline"}:
            return []
        required = set(required_gates_for_phase(item["phase"]))
        if item.get("variant_id") == LEAD_VARIANT:
            required.add("lead_superiority_gate")
        return [
            gate for gate, value in item["gate_results"].items()
            if gate in required and value == "fail"
        ]

    lines = [
        "# ZRC-ND Validation Results",
        "",
        f"**Input:** `{runs_path}`",
        f"**Status:** `{summary['status']}`",
        f"**Rows evaluated:** {summary['rows']}",
        f"**Lead rows:** {summary['lead_rows']}",
        f"**Failed rows:** {summary['failed_rows']}",
        f"**Lead phase coverage:** {', '.join(summary['phase_coverage']) if summary['phase_coverage'] else '-'}",
        f"**Passed lead replicates by phase:** `{summary.get('passed_lead_replicates_by_phase', {})}`",
        "",
        "## Aggregate Gates",
        "",
        "| Gate | Status | Detail |",
        "| --- | --- | --- |",
        (
            f"| `{aggregate['gate']}` | `{aggregate['status']}` | "
            f"lead_vs_baseline={aggregate['lead_vs_baseline']}; "
            f"lead_vs_challenge={aggregate['lead_vs_challenge']}; "
            f"matched_groups={aggregate['metrics']['matched_groups']} |"
        ),
        "",
    ]
    if not evaluations:
        lines.extend([
            "No measured run rows are available yet. The CSV template has been created so measured data can be added without changing the evaluator.",
            "",
        ])
        return "\n".join(lines)

    lines.extend([
        "## Row Results",
        "",
        "| Run | Article | Variant | Control | Phase | Timepoint | Status | Failed gates |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ])
    for item in evaluations:
        failed_gates = required_failed_gates(item)
        failed_text = ", ".join(failed_gates) if failed_gates else "-"
        lines.append(
            f"| `{item['run_id']}` | `{item['article_id']}` | `{item['variant_id']}` | "
            f"`{item['control_run_id']}` | {item['phase']} | {item['timepoint']} | "
            f"`{item['status']}` | {failed_text} |"
        )
    lines.append("")
    return "\n".join(lines)


def evaluate_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    controls = control_index(rows)
    evaluations = [
        evaluate_row(row, controls.get(row_key(row)))
        for row in rows
    ]
    aggregate = aggregate_lead_superiority(evaluations)
    evaluations = apply_aggregate_gates(evaluations, aggregate)
    summary = summarize(evaluations, aggregate)
    return evaluations, aggregate, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate ZRC-ND validation runs.")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package = load_json(args.package)
    if not args.runs.exists():
        write_template(package, args.runs)
    rows = load_rows(args.runs)
    evaluations, aggregate, summary = evaluate_rows(rows)
    write_results(evaluations, aggregate, summary, args.results)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(summary, aggregate, evaluations, args.runs), encoding="utf-8")
    print(f"Evaluated {summary['rows']} row(s): {summary['status']}")
    print(f"Wrote {args.results}")
    print(f"Wrote {args.report}")
    if not rows:
        print(f"Template ready at {args.runs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
