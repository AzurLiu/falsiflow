#!/usr/bin/env python3
"""Evaluate long-duration NHI-PEDOT follow-up rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "nhi_pedot_long_followup_package.json"
DEFAULT_RUNS = ROOT / "data" / "nhi_pedot_long_runs_template.csv"
DEFAULT_RESULTS = ROOT / "data" / "nhi_pedot_long_results.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_long_results.md"

LEAD_VARIANT = "nhi_pedot_low_loading_laminin"
HYDROGEL_VARIANT = "hydrogel_laminin_no_pedot"
CHALLENGE_VARIANT = "nhi_pedot_high_loading_laminin"
CONTROL_ARTICLES = {"long_laminin_only_control", "long_hydrogel_laminin_control", "long_positive_toxicity_control"}
REQUIRED_PHASES = {"L1", "L2", "L3"}
BASELINE_TIMEPOINTS = {"0 d", "0d", "pre-stim", "prestim"}
REQUIRED_GATES_BY_PHASE = {
    "L1": {"long_material_integrity_gate", "long_electrochemical_stability_gate"},
    "L2": {"long_material_integrity_gate", "long_neural_health_gate", "long_network_stability_gate"},
    "L3": {"long_stimulus_recovery_gate"},
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


def parse_float(row: dict[str, str], field: str) -> float | None:
    value = row.get(field, "")
    if value in ("", None):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_bool(row: dict[str, str], field: str) -> bool | None:
    value = row.get(field, "").strip().lower()
    if value in {"", "na", "n/a", "unknown"}:
        return None
    return value in {"yes", "true", "1", "y"}


def pass_fail(value: bool | None) -> str:
    if value is None:
        return "not_evaluable"
    return "pass" if value else "fail"


def in_range(value: float | None, low: float, high: float) -> bool | None:
    if value is None:
        return None
    return low <= value <= high


def fractional_drift(initial: float | None, current: float | None) -> float | None:
    if initial is None or current is None or initial == 0:
        return None
    return (current - initial) / initial


def is_baseline(row: dict[str, str]) -> bool:
    return row.get("timepoint", "").strip().lower() in BASELINE_TIMEPOINTS


def evaluate_row(row: dict[str, str]) -> dict[str, Any]:
    shedding = parse_bool(row, "visible_shedding")
    window_access = parse_bool(row, "electrode_window_access")
    swelling = parse_float(row, "swelling_fraction")
    delamination = parse_float(row, "delamination_score")
    transparency = parse_float(row, "optical_transparency_fraction")

    material_integrity = None
    if all(value is not None for value in [shedding, window_access, swelling, delamination, transparency]):
        material_integrity = (
            not shedding
            and bool(window_access)
            and abs(swelling) <= 0.20
            and delamination <= 0.50
            and transparency >= 0.75
        )

    impedance_initial = parse_float(row, "eis_1khz_initial_ohm")
    impedance_current = parse_float(row, "eis_1khz_current_ohm")
    impedance_drift = fractional_drift(impedance_initial, impedance_current)
    impedance_pct_hydrogel = parse_float(row, "eis_1khz_pct_hydrogel_control")
    csc_retention = parse_float(row, "charge_storage_capacity_retention_fraction")
    electrochemical = None
    if (impedance_drift is not None or impedance_pct_hydrogel is not None) and csc_retention is not None:
        electrochemical = (
            (impedance_drift is not None and abs(impedance_drift) <= 0.25)
            or (impedance_pct_hydrogel is not None and impedance_pct_hydrogel <= 80)
        ) and csc_retention >= 0.80

    viability = parse_float(row, "viability_pct_hydrogel_control")
    ldh = parse_float(row, "ldh_pct_hydrogel_control")
    neurite = parse_float(row, "neurite_coverage_pct_hydrogel_control")
    stress = parse_float(row, "morphology_stress_score")
    neural_health = None
    if all(value is not None for value in [viability, ldh, neurite, stress]):
        neural_health = viability >= 90 and ldh <= 120 and neurite >= 85 and stress <= 1

    electrode_yield = parse_float(row, "electrode_yield_pct_hydrogel_control")
    spike = parse_float(row, "spike_rate_pct_hydrogel_control")
    burst = parse_float(row, "burst_rate_pct_hydrogel_control")
    synchrony = parse_float(row, "synchrony_pct_hydrogel_control")
    network_checks = [
        electrode_yield is not None and electrode_yield >= 90,
        in_range(spike, 70, 130),
        in_range(burst, 70, 130),
        in_range(synchrony, 70, 130),
    ]
    network = None
    if all(value is not None for value in network_checks):
        network = all(network_checks)

    spike_recovery = parse_float(row, "post_stim_spike_recovery_pct_pre")
    burst_recovery = parse_float(row, "post_stim_burst_recovery_pct_pre")
    impedance_degradation = parse_float(row, "post_stim_impedance_degradation_pct")
    stimulus_recovery = None
    if all(value is not None for value in [spike_recovery, burst_recovery, impedance_degradation]):
        stimulus_recovery = spike_recovery >= 85 and burst_recovery >= 85 and impedance_degradation <= 20

    gates = {
        "long_material_integrity_gate": pass_fail(material_integrity),
        "long_electrochemical_stability_gate": pass_fail(electrochemical),
        "long_neural_health_gate": pass_fail(neural_health),
        "long_network_stability_gate": pass_fail(network),
        "long_stimulus_recovery_gate": pass_fail(stimulus_recovery),
        "long_superiority_gate": "not_evaluable",
    }

    if row.get("article_id") in CONTROL_ARTICLES:
        status = "control"
    elif is_baseline(row):
        status = "baseline"
    else:
        required = REQUIRED_GATES_BY_PHASE.get(row.get("phase", ""), set())
        required_values = [gates[gate] for gate in sorted(required)]
        failed = any(value == "fail" for value in required_values)
        passed = bool(required_values) and all(value == "pass" for value in required_values)
        status = "fail" if failed else "pass_partial" if passed else "not_evaluable"

    return {
        "run_id": row.get("run_id", ""),
        "article_id": row.get("article_id", ""),
        "variant_id": row.get("variant_id", ""),
        "phase": row.get("phase", ""),
        "timepoint": row.get("timepoint", ""),
        "replicate": row.get("replicate", ""),
        "metrics": {
            "visible_shedding": shedding,
            "swelling_fraction": swelling,
            "delamination_score": delamination,
            "optical_transparency_fraction": transparency,
            "electrode_window_access": window_access,
            "eis_1khz_fractional_drift": impedance_drift,
            "eis_1khz_pct_hydrogel_control": impedance_pct_hydrogel,
            "charge_storage_capacity_retention_fraction": csc_retention,
            "viability_pct_hydrogel_control": viability,
            "ldh_pct_hydrogel_control": ldh,
            "neurite_coverage_pct_hydrogel_control": neurite,
            "morphology_stress_score": stress,
            "electrode_yield_pct_hydrogel_control": electrode_yield,
            "spike_rate_pct_hydrogel_control": spike,
            "burst_rate_pct_hydrogel_control": burst,
            "synchrony_pct_hydrogel_control": synchrony,
            "post_stim_spike_recovery_pct_pre": spike_recovery,
            "post_stim_burst_recovery_pct_pre": burst_recovery,
            "post_stim_impedance_degradation_pct": impedance_degradation,
        },
        "gate_results": gates,
        "status": status,
    }


def mean_metric(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [row["metrics"].get(field) for row in rows if row["metrics"].get(field) is not None]
    if not values:
        return None
    return mean(values)


def aggregate_superiority(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    lead = [item for item in evaluations if item.get("variant_id") == LEAD_VARIANT and not is_eval_baseline(item)]
    hydrogel = [item for item in evaluations if item.get("variant_id") == HYDROGEL_VARIANT and not is_eval_baseline(item)]
    challenge = [item for item in evaluations if item.get("variant_id") == CHALLENGE_VARIANT and not is_eval_baseline(item)]

    lead_eis = mean_metric(lead, "eis_1khz_pct_hydrogel_control")
    lead_viability = mean_metric(lead, "viability_pct_hydrogel_control")
    lead_network = mean_metric(lead, "spike_rate_pct_hydrogel_control")
    lead_burst = mean_metric(lead, "burst_rate_pct_hydrogel_control")
    lead_stim_recovery = mean_metric(lead, "post_stim_spike_recovery_pct_pre")
    hydrogel_viability = mean_metric(hydrogel, "viability_pct_hydrogel_control")
    challenge_viability = mean_metric(challenge, "viability_pct_hydrogel_control")

    lead_noninferior_hydrogel = None
    hydrogel_checks = []
    if lead_viability is not None and hydrogel_viability is not None:
        hydrogel_checks.append(lead_viability >= hydrogel_viability - 5)
    if lead_network is not None:
        hydrogel_checks.append(70 <= lead_network <= 130)
    if lead_burst is not None:
        hydrogel_checks.append(70 <= lead_burst <= 130)
    if hydrogel_checks:
        lead_noninferior_hydrogel = all(hydrogel_checks)

    lead_adds_electrical_value = None
    if lead_eis is not None:
        lead_adds_electrical_value = lead_eis <= 80

    high_loading_not_safer = None
    if lead_viability is not None and challenge_viability is not None:
        high_loading_not_safer = lead_viability >= challenge_viability - 2

    stimulus_recovery_ok = None
    if lead_stim_recovery is not None:
        stimulus_recovery_ok = lead_stim_recovery >= 85

    checks = [
        lead_noninferior_hydrogel,
        lead_adds_electrical_value,
        high_loading_not_safer,
        stimulus_recovery_ok,
    ]
    if any(value is None for value in checks):
        status = "not_evaluable"
    elif all(checks):
        status = "pass"
    else:
        status = "fail"

    return {
        "gate": "long_superiority_gate",
        "status": status,
        "lead_noninferior_hydrogel": pass_fail(lead_noninferior_hydrogel),
        "lead_adds_electrical_value": pass_fail(lead_adds_electrical_value),
        "high_loading_not_safer": pass_fail(high_loading_not_safer),
        "stimulus_recovery_ok": pass_fail(stimulus_recovery_ok),
        "metrics": {
            "lead_eis_pct_hydrogel_mean": lead_eis,
            "lead_viability_pct_hydrogel_mean": lead_viability,
            "lead_spike_pct_hydrogel_mean": lead_network,
            "lead_burst_pct_hydrogel_mean": lead_burst,
            "lead_post_stim_spike_recovery_mean": lead_stim_recovery,
            "hydrogel_viability_pct_hydrogel_mean": hydrogel_viability,
            "challenge_viability_pct_hydrogel_mean": challenge_viability,
        },
    }


def is_eval_baseline(item: dict[str, Any]) -> bool:
    return item.get("status") == "baseline"


def apply_aggregate(evaluations: list[dict[str, Any]], aggregate: dict[str, Any]) -> list[dict[str, Any]]:
    for item in evaluations:
        if item.get("variant_id") != LEAD_VARIANT:
            continue
        item["gate_results"]["long_superiority_gate"] = aggregate["status"]
        if item.get("status") in {"baseline", "control"}:
            continue
        failed = any(value == "fail" for value in item["gate_results"].values())
        required = REQUIRED_GATES_BY_PHASE.get(item.get("phase", ""), set()) | {"long_superiority_gate"}
        passed = all(item["gate_results"].get(gate) == "pass" for gate in required)
        item["status"] = "fail" if failed else "pass" if passed else "not_evaluable"
    return evaluations


def summarize(evaluations: list[dict[str, Any]], aggregate: dict[str, Any]) -> dict[str, Any]:
    if not evaluations:
        return {
            "status": "no_data",
            "rows": 0,
            "lead_rows": 0,
            "failed_lead_rows": 0,
            "phase_coverage": [],
            "passed_lead_replicates_by_phase": {},
            "aggregate_long_superiority": aggregate["status"],
        }
    lead_rows = [
        item for item in evaluations
        if item.get("variant_id") == LEAD_VARIANT and item.get("status") != "baseline"
    ]
    failed_lead = [item for item in lead_rows if item.get("status") == "fail"]
    passed_lead = [item for item in lead_rows if item.get("status") == "pass"]
    unevaluable_lead = [item for item in lead_rows if item.get("status") == "not_evaluable"]
    phase_coverage = sorted({item["phase"] for item in passed_lead})
    passed_reps = {
        phase: sorted({
            item["replicate"] for item in passed_lead
            if item["phase"] == phase
        })
        for phase in phase_coverage
    }
    min_reps_met = all(len(set(passed_reps.get(phase, []))) >= 3 for phase in REQUIRED_PHASES)
    coverage_met = REQUIRED_PHASES.issubset(set(phase_coverage))
    if failed_lead:
        status = "nhi_pedot_long_has_failures"
    elif aggregate["status"] == "not_evaluable" or unevaluable_lead:
        status = "needs_more_data"
    elif coverage_met and min_reps_met and aggregate["status"] == "pass":
        status = "nhi_pedot_long_passes_gates"
    else:
        status = "nhi_pedot_long_partial"
    return {
        "status": status,
        "rows": len(evaluations),
        "lead_rows": len(lead_rows),
        "failed_lead_rows": len(failed_lead),
        "passed_lead_rows": len(passed_lead),
        "phase_coverage": phase_coverage,
        "passed_lead_replicates_by_phase": passed_reps,
        "required_phases": sorted(REQUIRED_PHASES),
        "min_passed_lead_replicates_per_phase": 3,
        "aggregate_long_superiority": aggregate["status"],
    }


def render_report(result: dict[str, Any], runs_path: Path) -> str:
    summary = result["summary"]
    aggregate = result["aggregate_gates"][0]
    lines = [
        "# NHI-PEDOT Long-Duration Results",
        "",
        f"**Input runs:** `{runs_path}`",
        f"**Status:** `{summary['status']}`",
        f"**Rows:** {summary['rows']}",
        f"**Lead rows:** {summary['lead_rows']}",
        f"**Failed lead rows:** {summary['failed_lead_rows']}",
        f"**Aggregate superiority:** `{summary['aggregate_long_superiority']}`",
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
        "## Aggregate Gate",
        "",
        "| Gate | Status | Detail |",
        "| --- | --- | --- |",
        (
            f"| `{aggregate['gate']}` | `{aggregate['status']}` | "
            f"lead_noninferior_hydrogel={aggregate['lead_noninferior_hydrogel']}; "
            f"lead_adds_electrical_value={aggregate['lead_adds_electrical_value']}; "
            f"high_loading_not_safer={aggregate['high_loading_not_safer']}; "
            f"stimulus_recovery_ok={aggregate['stimulus_recovery_ok']} |"
        ),
        "",
        "## Lead Row Evaluations",
        "",
        "| Run | Phase | Timepoint | Replicate | Status | Gates |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    lead_items = [item for item in result["evaluations"] if item.get("variant_id") == LEAD_VARIANT]
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
        "- `nhi_pedot_long_passes_gates` is the first state that can support a NHI-PEDOT suitability claim.",
        "- It still depends on measured rows; synthetic rows are evaluator regressions only.",
        "- Production CL1 integration remains a separate engineering constraint after material suitability.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate NHI-PEDOT long-duration follow-up rows.")
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
    evaluations = [evaluate_row(row) for row in rows if row.get("run_id")]
    aggregate = aggregate_superiority(evaluations)
    evaluations = apply_aggregate(evaluations, aggregate)
    result = {
        "summary": summarize(evaluations, aggregate),
        "aggregate_gates": [aggregate],
        "evaluations": evaluations,
    }
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result, args.runs), encoding="utf-8")
    print(f"NHI-PEDOT long: {result['summary']['status']}")
    print(f"Wrote {args.results}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
