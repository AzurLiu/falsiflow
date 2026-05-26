#!/usr/bin/env python3
"""Evaluate NHI-PEDOT validation run rows against package gates."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "nhi_pedot_validation_package.json"
DEFAULT_RUNS = ROOT / "data" / "nhi_pedot_runs_template.csv"
DEFAULT_RESULTS = ROOT / "data" / "nhi_pedot_results.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_results.md"

LEAD_ARTICLE = "lead_nhi_pedot_low_loading"
HYDROGEL_CONTROL = "hydrogel_laminin_control"
NO_COATING_CONTROL = "no_coating_mea_control"
CONTROL_ARTICLES = {
    "no_coating_mea_control",
    "laminin_only_control",
    "hydrogel_laminin_control",
}
REQUIRED_PHASES = {"H-A", "H-B", "H-C"}
BASELINE_TIMEPOINTS = {"0 h", "0h", "0", "pre-soak", "presoak"}
REQUIRED_GATES_BY_PHASE = {
    "H-A": {"blank_integrity_gate", "physical_stability_gate"},
    "H-B": {"physical_stability_gate", "electrochemical_benefit_gate"},
    "H-C": {"neural_health_gate", "network_activity_gate"},
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
        return [dict(row) for row in csv.DictReader(handle)]


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


def parse_bool(row: dict[str, str] | None, field: str) -> bool | None:
    if row is None:
        return None
    value = row.get(field, "").strip().lower()
    if value in {"", "na", "n/a", "unknown"}:
        return None
    return value in {"yes", "true", "1", "y"}


def pct_change(initial: float | None, final: float | None) -> float | None:
    if initial is None or final is None or initial == 0:
        return None
    return (final - initial) / initial


def delta(initial: float | None, final: float | None) -> float | None:
    if initial is None or final is None:
        return None
    return final - initial


def ratio(value: float | None, control_value: float | None) -> float | None:
    if value is None or control_value is None or control_value == 0:
        return None
    return value / control_value


def pass_fail(value: bool | None) -> str:
    if value is None:
        return "not_evaluable"
    return "pass" if value else "fail"


def is_baseline_timepoint(row: dict[str, str]) -> bool:
    return row.get("timepoint", "").strip().lower() in BASELINE_TIMEPOINTS


def row_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("phase", ""),
        row.get("timepoint", ""),
        row.get("replicate", ""),
        row.get("article_id", ""),
    )


def index_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, str]]:
    return {row_key(row): row for row in rows if row.get("run_id")}


def matched(
    rows: dict[tuple[str, str, str, str], dict[str, str]],
    row: dict[str, str],
    article_id: str,
) -> dict[str, str] | None:
    return rows.get((
        row.get("phase", ""),
        row.get("timepoint", ""),
        row.get("replicate", ""),
        article_id,
    ))


def evaluate_blank_gate(row: dict[str, str], control: dict[str, str] | None) -> tuple[str, dict[str, Any]]:
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

    precipitate = parse_bool(row, "visible_precipitate")
    shedding = parse_bool(row, "visible_shedding")
    values = [p_h_delta_vs_control, osmolality_change_vs_control, conductivity_change_vs_control, precipitate, shedding]
    blank_pass = None
    if all(value is not None for value in values):
        blank_pass = (
            abs(p_h_delta_vs_control) <= 0.10
            and abs(osmolality_change_vs_control) <= 0.05
            and abs(conductivity_change_vs_control) <= 0.05
            and not precipitate
            and not shedding
        )
    return pass_fail(blank_pass), {
        "pH_delta_vs_no_coating": p_h_delta_vs_control,
        "osmolality_fractional_change_vs_no_coating": osmolality_change_vs_control,
        "conductivity_fractional_change_vs_no_coating": conductivity_change_vs_control,
        "visible_precipitate": precipitate,
        "visible_shedding": shedding,
    }


def evaluate_physical_gate(row: dict[str, str]) -> tuple[str, dict[str, Any]]:
    swelling = parse_float(row, "swelling_fraction")
    delamination = parse_float(row, "delamination_score")
    transparency = parse_float(row, "optical_transparency_fraction")
    values = [swelling, delamination, transparency]
    physical_pass = None
    if all(value is not None for value in values):
        physical_pass = (
            abs(swelling) <= 0.20
            and delamination <= 0.50
            and transparency >= 0.80
        )
    return pass_fail(physical_pass), {
        "swelling_fraction": swelling,
        "delamination_score": delamination,
        "optical_transparency_fraction": transparency,
    }


def evaluate_electrochemical_gate(row: dict[str, str], control: dict[str, str] | None) -> tuple[str, dict[str, Any]]:
    eis_final = parse_float(row, "eis_1khz_final_ohm")
    control_eis_final = parse_float(control, "eis_1khz_final_ohm")
    csc_final = parse_float(row, "charge_storage_capacity_final")
    control_csc_final = parse_float(control, "charge_storage_capacity_final")
    eis_ratio = ratio(eis_final, control_eis_final)
    csc_ratio = ratio(csc_final, control_csc_final)
    electrochemical_pass = None
    if eis_ratio is not None or csc_ratio is not None:
        electrochemical_pass = (
            (eis_ratio is not None and eis_ratio <= 0.75)
            or (csc_ratio is not None and csc_ratio >= 1.25)
        )
    return pass_fail(electrochemical_pass), {
        "eis_1khz_final_ohm": eis_final,
        "eis_1khz_ratio_vs_hydrogel": eis_ratio,
        "charge_storage_capacity_final": csc_final,
        "charge_storage_capacity_ratio_vs_hydrogel": csc_ratio,
    }


def evaluate_neural_health_gate(row: dict[str, str], control: dict[str, str] | None) -> tuple[str, dict[str, Any]]:
    viability = parse_float(row, "viability_fraction")
    ldh = parse_float(row, "ldh_fold_control")
    neurite = parse_float(row, "neurite_coverage_fraction")
    neurite_length = parse_float(row, "mean_neurite_length_um")
    viability_ratio = ratio(viability, parse_float(control, "viability_fraction"))
    ldh_ratio = ratio(ldh, parse_float(control, "ldh_fold_control"))
    neurite_ratio = ratio(neurite, parse_float(control, "neurite_coverage_fraction"))
    neurite_length_ratio = ratio(neurite_length, parse_float(control, "mean_neurite_length_um"))
    values = [viability, ldh, neurite, viability_ratio, ldh_ratio, neurite_ratio, neurite_length_ratio]
    health_pass = None
    if all(value is not None for value in values):
        health_pass = (
            viability >= 0.80
            and viability_ratio >= 0.90
            and ldh_ratio <= 1.20
            and neurite_ratio >= 0.90
            and neurite_length_ratio >= 0.90
        )
    return pass_fail(health_pass), {
        "viability_fraction": viability,
        "viability_ratio_vs_hydrogel": viability_ratio,
        "ldh_fold_control": ldh,
        "ldh_ratio_vs_hydrogel": ldh_ratio,
        "neurite_coverage_fraction": neurite,
        "neurite_coverage_ratio_vs_hydrogel": neurite_ratio,
        "mean_neurite_length_um": neurite_length,
        "mean_neurite_length_ratio_vs_hydrogel": neurite_length_ratio,
    }


def evaluate_network_gate(row: dict[str, str], control: dict[str, str] | None) -> tuple[str, dict[str, Any]]:
    electrode_yield = parse_float(row, "electrode_yield_fraction")
    spike_rate = parse_float(row, "spike_rate_hz")
    burst_rate = parse_float(row, "burst_rate_hz")
    electrode_yield_ratio = ratio(electrode_yield, parse_float(control, "electrode_yield_fraction"))
    spike_rate_ratio = ratio(spike_rate, parse_float(control, "spike_rate_hz"))
    burst_rate_ratio = ratio(burst_rate, parse_float(control, "burst_rate_hz"))
    network_pass = None
    if all(value is not None for value in [electrode_yield_ratio, spike_rate_ratio, burst_rate_ratio]):
        network_pass = (
            electrode_yield_ratio >= 0.90
            and spike_rate_ratio >= 0.90
            and burst_rate_ratio >= 0.80
        )
    return pass_fail(network_pass), {
        "electrode_yield_fraction": electrode_yield,
        "electrode_yield_ratio_vs_hydrogel": electrode_yield_ratio,
        "spike_rate_hz": spike_rate,
        "spike_rate_ratio_vs_hydrogel": spike_rate_ratio,
        "burst_rate_hz": burst_rate,
        "burst_rate_ratio_vs_hydrogel": burst_rate_ratio,
    }


def evaluate_row(row: dict[str, str], rows_by_key: dict[tuple[str, str, str, str], dict[str, str]]) -> dict[str, Any]:
    blank_control = matched(rows_by_key, row, NO_COATING_CONTROL)
    hydrogel_control = matched(rows_by_key, row, HYDROGEL_CONTROL)
    blank_status, blank_metrics = evaluate_blank_gate(row, blank_control)
    physical_status, physical_metrics = evaluate_physical_gate(row)
    electro_status, electro_metrics = evaluate_electrochemical_gate(row, hydrogel_control)
    neural_status, neural_metrics = evaluate_neural_health_gate(row, hydrogel_control)
    network_status, network_metrics = evaluate_network_gate(row, hydrogel_control)
    gate_results = {
        "blank_integrity_gate": blank_status,
        "physical_stability_gate": physical_status,
        "electrochemical_benefit_gate": electro_status,
        "neural_health_gate": neural_status,
        "network_activity_gate": network_status,
    }
    article_id = row.get("article_id", "")
    if is_baseline_timepoint(row):
        status = "baseline"
    elif article_id in CONTROL_ARTICLES:
        status = "control"
    else:
        required = REQUIRED_GATES_BY_PHASE.get(row.get("phase", ""), set())
        required_values = [gate_results[gate] for gate in sorted(required)]
        failed = any(value == "fail" for value in required_values)
        passed = bool(required_values) and all(value == "pass" for value in required_values)
        status = "fail" if failed else "pass" if passed else "not_evaluable"

    return {
        "run_id": row.get("run_id", ""),
        "article_id": article_id,
        "variant_id": row.get("variant_id", ""),
        "phase": row.get("phase", ""),
        "timepoint": row.get("timepoint", ""),
        "replicate": row.get("replicate", ""),
        "blank_control_run_id": blank_control.get("run_id", "") if blank_control else "",
        "hydrogel_control_run_id": hydrogel_control.get("run_id", "") if hydrogel_control else "",
        "gate_results": gate_results,
        "metrics": {
            **blank_metrics,
            **physical_metrics,
            **electro_metrics,
            **neural_metrics,
            **network_metrics,
        },
        "status": status,
    }


def summarize(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    measured = [item for item in evaluations if item["run_id"]]
    lead_rows = [
        item for item in measured
        if item["article_id"] == LEAD_ARTICLE and item["status"] not in {"baseline", "control"}
    ]
    failed_lead = [item for item in lead_rows if item["status"] == "fail"]
    passed_lead = [item for item in lead_rows if item["status"] == "pass"]
    coverage = sorted({item["phase"] for item in passed_lead})
    passed_reps: dict[str, set[str]] = {}
    for item in passed_lead:
        passed_reps.setdefault(item["phase"], set()).add(str(item["replicate"]))
    passed_reps_json = {phase: sorted(values) for phase, values in passed_reps.items()}
    min_reps_met = all(len(passed_reps.get(phase, set())) >= 3 for phase in REQUIRED_PHASES)
    phase_coverage_met = REQUIRED_PHASES.issubset(set(coverage))

    if not measured:
        status = "no_data"
    elif failed_lead:
        status = "lead_has_failures"
    elif phase_coverage_met and min_reps_met:
        status = "nhi_pedot_passes_gates"
    else:
        status = "needs_more_data"

    return {
        "status": status,
        "rows": len(measured),
        "lead_rows": len(lead_rows),
        "failed_lead_rows": len(failed_lead),
        "passed_lead_rows": len(passed_lead),
        "phase_coverage": coverage,
        "passed_lead_replicates_by_phase": passed_reps_json,
        "required_phases": sorted(REQUIRED_PHASES),
        "min_passed_lead_replicates_per_phase": 3,
    }


def render_report(result: dict[str, Any], runs_path: Path) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT Validation Results",
        "",
        f"**Input runs:** `{runs_path}`",
        f"**Status:** `{summary['status']}`",
        f"**Rows:** {summary['rows']}",
        f"**Lead rows:** {summary['lead_rows']}",
        f"**Failed lead rows:** {summary['failed_lead_rows']}",
        "",
        "## Phase Coverage",
        "",
        "| Phase | Passed lead replicates |",
        "| --- | --- |",
    ]
    coverage = summary["passed_lead_replicates_by_phase"]
    for phase in sorted(REQUIRED_PHASES):
        values = coverage.get(phase, [])
        lines.append(f"| {phase} | {', '.join(values) if values else '-'} |")

    lines.extend([
        "",
        "## Lead Row Evaluations",
        "",
        "| Run | Phase | Timepoint | Replicate | Status | Gates |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    lead_items = [item for item in result["evaluations"] if item["article_id"] == LEAD_ARTICLE]
    for item in lead_items:
        gates = ", ".join(f"{gate}={status}" for gate, status in item["gate_results"].items())
        lines.append(
            f"| `{item['run_id']}` | {item['phase']} | {item['timepoint']} | "
            f"{item['replicate']} | `{item['status']}` | {gates} |"
        )
    if not lead_items:
        lines.append("| - | - | - | - | - | - |")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- `nhi_pedot_passes_gates` requires three passed lead replicates in H-A, H-B, and H-C.",
        "- Synthetic fixtures exercise the evaluator only; they do not count as material evidence.",
        "- A real suitability claim still needs measured rows and a later long-duration CL1-like network stability decision.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate NHI-PEDOT validation runs.")
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
    rows_by_key = index_rows(rows)
    evaluations = [
        evaluate_row(row, rows_by_key)
        for row in rows
        if row.get("run_id")
    ]
    result = {
        "summary": summarize(evaluations),
        "evaluations": evaluations,
    }
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result, args.runs), encoding="utf-8")
    print(f"NHI-PEDOT: {result['summary']['status']}")
    print(f"Wrote {args.results}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
