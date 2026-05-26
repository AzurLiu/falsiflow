#!/usr/bin/env python3
"""Evaluate ZRC-ND biological follow-up rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "zrc_nd_biological_followup_package.json"
DEFAULT_RUNS = ROOT / "data" / "zrc_nd_bio_runs_template.csv"
DEFAULT_RESULTS = ROOT / "data" / "zrc_nd_bio_results.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_bio_results.md"

LEAD_VARIANT = "zrc_nd_3p5k_mpc_guard"
BASELINE_VARIANT = "zrc_nd_3p5k_unmodified_guard"
CHALLENGE_VARIANT = "zrc_nd_10k_mpc_guard"
REQUIRED_PHASES = {"D1", "D2", "D3"}
CONTROL_ARTICLES = {"bio_no_module_control", "bio_positive_toxicity_control"}


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


def pass_fail(value: bool | None) -> str:
    if value is None:
        return "not_evaluable"
    return "pass" if value else "fail"


def in_range(value: float | None, low: float, high: float) -> bool | None:
    if value is None:
        return None
    return low <= value <= high


def evaluate_row(row: dict[str, str]) -> dict[str, Any]:
    article_id = row.get("article_id", "")
    is_control = article_id in CONTROL_ARTICLES

    viability = parse_float(row, "viability_metabolic_pct_control")
    ldh = parse_float(row, "ldh_release_pct_control")
    neurite = parse_float(row, "neurite_length_pct_control")
    branching = parse_float(row, "neurite_branching_pct_control")
    cell_count = parse_float(row, "cell_body_count_pct_control")
    spike = parse_float(row, "network_spike_rate_pct_control")
    burst = parse_float(row, "burst_rate_pct_control")
    synchrony = parse_float(row, "synchrony_pct_control")

    viability_pass = None
    if viability is not None and ldh is not None:
        viability_pass = viability >= 90 and ldh <= 120

    morphology_pass = None
    if neurite is not None and branching is not None and cell_count is not None:
        morphology_pass = neurite >= 85 and branching >= 85 and cell_count >= 90

    function_values = [in_range(value, 70, 130) for value in [spike, burst, synchrony]]
    function_pass = None
    if all(value is not None for value in function_values):
        function_pass = all(function_values)

    gates = {
        "bio_viability_gate": pass_fail(viability_pass),
        "bio_morphology_gate": pass_fail(morphology_pass),
        "bio_function_gate": pass_fail(function_pass),
        "bio_superiority_gate": "not_evaluable",
    }
    if is_control:
        gates = {key: "not_evaluable" for key in gates}
        status = "control"
    else:
        failed = any(value == "fail" for value in gates.values())
        local = [value for key, value in gates.items() if key != "bio_superiority_gate"]
        passed = local and all(value in {"pass", "not_evaluable"} for value in local) and any(value == "pass" for value in local)
        status = "fail" if failed else "pass_partial" if passed else "not_evaluable"

    return {
        "run_id": row.get("run_id", ""),
        "article_id": article_id,
        "variant_id": row.get("variant_id", ""),
        "phase": row.get("phase", ""),
        "timepoint": row.get("timepoint", ""),
        "replicate": row.get("replicate", ""),
        "metrics": {
            "viability_metabolic_pct_control": viability,
            "ldh_release_pct_control": ldh,
            "neurite_length_pct_control": neurite,
            "neurite_branching_pct_control": branching,
            "cell_body_count_pct_control": cell_count,
            "network_spike_rate_pct_control": spike,
            "burst_rate_pct_control": burst,
            "synchrony_pct_control": synchrony,
        },
        "gate_results": gates,
        "status": status,
    }


def aggregate_superiority(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    lead = [item for item in evaluations if item.get("variant_id") == LEAD_VARIANT]
    baseline = [item for item in evaluations if item.get("variant_id") == BASELINE_VARIANT]
    challenge = [item for item in evaluations if item.get("variant_id") == CHALLENGE_VARIANT]

    def mean_metric(rows: list[dict[str, Any]], field: str) -> float | None:
        values = [row["metrics"].get(field) for row in rows if row["metrics"].get(field) is not None]
        if not values:
            return None
        return mean(values)

    def row_min_metric(row: dict[str, Any], fields: list[str]) -> float | None:
        values = [row["metrics"].get(field) for field in fields if row["metrics"].get(field) is not None]
        if not values:
            return None
        return min(values)

    def mean_derived(rows: list[dict[str, Any]], fields: list[str]) -> float | None:
        values = [row_min_metric(row, fields) for row in rows]
        clean = [value for value in values if value is not None]
        if not clean:
            return None
        return mean(clean)

    def function_stability(row: dict[str, Any]) -> float | None:
        values = [
            row["metrics"].get("network_spike_rate_pct_control"),
            row["metrics"].get("burst_rate_pct_control"),
            row["metrics"].get("synchrony_pct_control"),
        ]
        clean = [value for value in values if value is not None]
        if not clean:
            return None
        return mean(100 - abs(value - 100) for value in clean)

    def mean_function_stability(rows: list[dict[str, Any]]) -> float | None:
        values = [function_stability(row) for row in rows]
        clean = [value for value in values if value is not None]
        if not clean:
            return None
        return mean(clean)

    def any_failed(rows: list[dict[str, Any]], gates: set[str]) -> bool:
        for row in rows:
            for gate, status in row.get("gate_results", {}).items():
                if gate in gates and status == "fail":
                    return True
        return False

    def any_passed(rows: list[dict[str, Any]], gates: set[str]) -> bool:
        for row in rows:
            for gate, status in row.get("gate_results", {}).items():
                if gate in gates and status == "pass":
                    return True
        return False

    lead_viability = mean_metric(lead, "viability_metabolic_pct_control")
    baseline_viability = mean_metric(baseline, "viability_metabolic_pct_control")
    challenge_viability = mean_metric(challenge, "viability_metabolic_pct_control")
    morphology_fields = [
        "neurite_length_pct_control",
        "neurite_branching_pct_control",
        "cell_body_count_pct_control",
    ]
    lead_morphology = mean_derived(lead, morphology_fields)
    baseline_morphology = mean_derived(baseline, morphology_fields)
    challenge_morphology = mean_derived(challenge, morphology_fields)
    lead_function_stability = mean_function_stability(lead)
    challenge_function_stability = mean_function_stability(challenge)

    lead_vs_baseline = None
    baseline_checks = []
    if lead_viability is not None and baseline_viability is not None:
        baseline_checks.append(lead_viability >= baseline_viability - 5)
    if lead_morphology is not None and baseline_morphology is not None:
        baseline_checks.append(lead_morphology >= baseline_morphology - 5)
    if baseline_checks:
        lead_vs_baseline = any(baseline_checks)

    lead_vs_challenge = None
    challenge_checks = []
    if lead_viability is not None and challenge_viability is not None:
        challenge_checks.append(lead_viability >= challenge_viability + 5)
    if lead_morphology is not None and challenge_morphology is not None:
        challenge_checks.append(lead_morphology >= challenge_morphology + 5)
    if lead_function_stability is not None and challenge_function_stability is not None:
        challenge_checks.append(lead_function_stability >= challenge_function_stability + 5)
    challenge_gate_failed = any_failed(challenge, {"bio_morphology_gate", "bio_function_gate"})
    lead_gate_passed = any_passed(lead, {"bio_morphology_gate", "bio_function_gate"})
    if challenge_gate_failed and lead_gate_passed:
        challenge_checks.append(True)
    if challenge_checks:
        lead_vs_challenge = any(challenge_checks)

    if lead_vs_baseline is None or lead_vs_challenge is None:
        status = "not_evaluable"
    elif lead_vs_baseline and lead_vs_challenge:
        status = "pass"
    else:
        status = "fail"

    return {
        "gate": "bio_superiority_gate",
        "status": status,
        "lead_vs_baseline": pass_fail(lead_vs_baseline),
        "lead_vs_challenge": pass_fail(lead_vs_challenge),
        "metrics": {
            "lead_viability_mean": lead_viability,
            "baseline_viability_mean": baseline_viability,
            "challenge_viability_mean": challenge_viability,
            "lead_morphology_min_mean": lead_morphology,
            "baseline_morphology_min_mean": baseline_morphology,
            "challenge_morphology_min_mean": challenge_morphology,
            "lead_function_stability_mean": lead_function_stability,
            "challenge_function_stability_mean": challenge_function_stability,
        },
    }


def apply_aggregate(evaluations: list[dict[str, Any]], aggregate: dict[str, Any]) -> list[dict[str, Any]]:
    for item in evaluations:
        if item.get("variant_id") == LEAD_VARIANT:
            item["gate_results"]["bio_superiority_gate"] = aggregate["status"]
            failed = any(value == "fail" for value in item["gate_results"].values())
            passed = all(value in {"pass", "not_evaluable"} for value in item["gate_results"].values()) and aggregate["status"] == "pass"
            item["status"] = "fail" if failed else "pass" if passed else "not_evaluable"
    return evaluations


def summarize(evaluations: list[dict[str, Any]], aggregate: dict[str, Any]) -> dict[str, Any]:
    if not evaluations:
        return {
            "status": "no_data",
            "rows": 0,
            "lead_rows": 0,
            "failed_rows": 0,
            "phase_coverage": [],
            "passed_lead_replicates_by_phase": {},
            "aggregate_bio_superiority": aggregate["status"],
        }
    lead_rows = [item for item in evaluations if item.get("variant_id") == LEAD_VARIANT]
    failed_rows = [item for item in evaluations if item.get("status") == "fail"]
    failed_lead = [item for item in lead_rows if item.get("status") == "fail"]
    unevaluable_lead = [item for item in lead_rows if item.get("status") == "not_evaluable"]
    phase_coverage = sorted({item["phase"] for item in lead_rows if item.get("status") == "pass"})
    passed_lead_replicates_by_phase = {
        phase: sorted({
            item["replicate"] for item in lead_rows
            if item["phase"] == phase and item.get("status") == "pass"
        })
        for phase in phase_coverage
    }
    if failed_lead:
        status = "bio_followup_has_failures"
    elif not lead_rows or unevaluable_lead or aggregate["status"] == "not_evaluable":
        status = "needs_more_data"
    elif set(phase_coverage) >= REQUIRED_PHASES:
        status = "bio_followup_passes_gates"
    else:
        status = "bio_followup_partial"
    return {
        "status": status,
        "rows": len(evaluations),
        "lead_rows": len(lead_rows),
        "failed_rows": len(failed_rows),
        "phase_coverage": phase_coverage,
        "passed_lead_replicates_by_phase": passed_lead_replicates_by_phase,
        "aggregate_bio_superiority": aggregate["status"],
    }


def render_report(summary: dict[str, Any], aggregate: dict[str, Any], evaluations: list[dict[str, Any]], runs_path: Path) -> str:
    lines = [
        "# ZRC-ND Biological Follow-Up Results",
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
        f"| `{aggregate['gate']}` | `{aggregate['status']}` | lead_vs_baseline={aggregate['lead_vs_baseline']}; lead_vs_challenge={aggregate['lead_vs_challenge']} |",
        "",
    ]
    if not evaluations:
        lines.extend(["No biological follow-up rows are available yet.", ""])
        return "\n".join(lines)
    lines.extend(["## Row Results", "", "| Run | Article | Variant | Phase | Timepoint | Status | Failed gates |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for item in evaluations:
        failed = [gate for gate, value in item["gate_results"].items() if value == "fail"]
        lines.append(
            f"| `{item['run_id']}` | `{item['article_id']}` | `{item['variant_id']}` | "
            f"{item['phase']} | {item['timepoint']} | `{item['status']}` | {', '.join(failed) if failed else '-'} |"
        )
    lines.append("")
    return "\n".join(lines)


def evaluate_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    evaluations = [evaluate_row(row) for row in rows]
    aggregate = aggregate_superiority(evaluations)
    evaluations = apply_aggregate(evaluations, aggregate)
    summary = summarize(evaluations, aggregate)
    return evaluations, aggregate, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate ZRC-ND biological follow-up runs.")
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
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps({"summary": summary, "aggregate_gates": [aggregate], "evaluations": evaluations}, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(summary, aggregate, evaluations, args.runs), encoding="utf-8")
    print(f"Evaluated {summary['rows']} biological row(s): {summary['status']}")
    print(f"Wrote {args.results}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
