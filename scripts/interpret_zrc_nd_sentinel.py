#!/usr/bin/env python3
"""Interpret the compact Phase A sentinel measurement batch."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS = ROOT / "data" / "zrc_nd_validation_runs_active.csv"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_sentinel_interpretation.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_sentinel_interpretation.md"

LEAD_ARTICLE = "lead_zrc_nd_3p5m_guard"
CONTROL_ARTICLE = "no_module_static_control"
MATERIAL_ARTICLES = {
    "lead_zrc_nd_3p5m_guard",
    "baseline_rc_3p5m_guard",
    "challenge_zrc_nd_10m_guard",
}
BASELINE_TIMEPOINTS = {"0 h", "0h", "0"}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def parse_float(row: dict[str, str] | None, field: str) -> float | None:
    if row is None:
        return None
    value = row.get(field, "")
    if value == "":
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


def row_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (row.get("phase", ""), row.get("timepoint", ""), row.get("replicate", ""))


def is_baseline(row: dict[str, str]) -> bool:
    return row.get("timepoint", "").strip().lower() in BASELINE_TIMEPOINTS


def control_index(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    return {
        row_key(row): row
        for row in rows
        if row.get("article_id") == CONTROL_ARTICLE
    }


def row_has_measurements(row: dict[str, str]) -> bool:
    required = [
        "pH_initial",
        "pH_final",
        "osmolality_initial_mOsm_kg",
        "osmolality_final_mOsm_kg",
        "conductivity_initial_mS_cm",
        "conductivity_final_mS_cm",
        "visible_precipitate",
    ]
    return all(row.get(field, "") != "" for field in required)


def evaluate_material_row(row: dict[str, str], control: dict[str, str] | None) -> dict[str, Any]:
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
    metrics = {
        "pH_delta_vs_control": p_h_delta_vs_control,
        "osmolality_fractional_change_vs_control": osmolality_change_vs_control,
        "conductivity_fractional_change_vs_control": conductivity_change_vs_control,
        "visible_precipitate": precipitate,
    }
    evaluable = (
        control is not None
        and row_has_measurements(row)
        and row_has_measurements(control)
        and all(value is not None for value in metrics.values())
    )
    if not evaluable:
        status = "not_evaluable"
    elif (
        abs(p_h_delta_vs_control) <= 0.10
        and abs(osmolality_change_vs_control) <= 0.05
        and abs(conductivity_change_vs_control) <= 0.05
        and not precipitate
    ):
        status = "pass"
    else:
        status = "fail"

    return {
        "run_id": row.get("run_id", ""),
        "article_id": row.get("article_id", ""),
        "variant_id": row.get("variant_id", ""),
        "timepoint": row.get("timepoint", ""),
        "replicate": row.get("replicate", ""),
        "control_run_id": control.get("run_id", "") if control else "",
        "status": status,
        "metrics": metrics,
    }


def interpret(rows: list[dict[str, str]]) -> dict[str, Any]:
    phase_a = [row for row in rows if row.get("phase") == "A"]
    measured = [row for row in phase_a if row.get("run_id")]
    controls = control_index(phase_a)
    material_rows = [
        row for row in measured
        if row.get("article_id") in MATERIAL_ARTICLES and not is_baseline(row)
    ]
    evaluations = [
        evaluate_material_row(row, controls.get(row_key(row)))
        for row in material_rows
    ]
    lead = [item for item in evaluations if item["article_id"] == LEAD_ARTICLE]
    failed = [item for item in evaluations if item["status"] == "fail"]
    not_evaluable = [item for item in evaluations if item["status"] == "not_evaluable"]
    lead_failed = [item for item in lead if item["status"] == "fail"]
    lead_passed = [item for item in lead if item["status"] == "pass"]

    if not measured:
        status = "no_sentinel_rows"
        next_action = "Generate and fill the Phase A sentinel packet."
    elif not_evaluable:
        status = "sentinel_needs_more_data"
        next_action = "Fill missing medium-integrity fields before interpreting the sentinel gate."
    elif lead_failed:
        status = "sentinel_lead_fails_stop"
        next_action = "Do not advance ZRC-ND-3.5M Guard; investigate blank drift, precipitate, rinsing, coating, or housing."
    elif lead_passed and failed:
        status = "sentinel_lead_passes_comparator_issue"
        next_action = "Continue lead cautiously; quarantine failed comparators and avoid using them for superiority claims until retested."
    elif lead_passed:
        status = "sentinel_passes_continue"
        next_action = "Continue to the next adaptive Phase A replicate batch; this is not yet suitability evidence."
    else:
        status = "sentinel_needs_more_data"
        next_action = "Add the lead gate-evaluable Phase A row and matched no-module control."

    return {
        "status": status,
        "next_action": next_action,
        "rows": len(measured),
        "material_rows": len(material_rows),
        "lead_gate_rows": len(lead),
        "failed_rows": len(failed),
        "not_evaluable_rows": len(not_evaluable),
        "evaluations": evaluations,
    }


def render_report(result: dict[str, Any], runs_path: Path) -> str:
    lines = [
        "# ZRC-ND Phase A Sentinel Interpretation",
        "",
        f"**Input:** `{runs_path}`",
        f"**Status:** `{result['status']}`",
        f"**Next action:** {result['next_action']}",
        f"**Rows:** {result['rows']}",
        f"**Material rows:** {result['material_rows']}",
        f"**Lead gate rows:** {result['lead_gate_rows']}",
        "",
        "## Row Interpretation",
        "",
        "| Run | Article | Timepoint | Status | pH dControl | Osm dControl | Cond dControl | Precipitate |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for item in result["evaluations"]:
        metrics = item["metrics"]
        lines.append(
            f"| `{item['run_id']}` | `{item['article_id']}` | {item['timepoint']} | `{item['status']}` | "
            f"{metrics['pH_delta_vs_control'] if metrics['pH_delta_vs_control'] is not None else '-'} | "
            f"{metrics['osmolality_fractional_change_vs_control'] if metrics['osmolality_fractional_change_vs_control'] is not None else '-'} | "
            f"{metrics['conductivity_fractional_change_vs_control'] if metrics['conductivity_fractional_change_vs_control'] is not None else '-'} | "
            f"{metrics['visible_precipitate'] if metrics['visible_precipitate'] is not None else '-'} |"
        )
    if not result["evaluations"]:
        lines.append("| - | - | - | - | - | - | - | - |")
    lines.extend([
        "",
        "## Scope Note",
        "",
        "This sentinel gate only checks Phase A material blank integrity. It can authorize the next non-cell batch, but it cannot prove material suitability.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interpret Phase A sentinel rows.")
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rows = load_csv(args.runs)
    result = interpret(rows)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result, args.runs), encoding="utf-8")
    print(f"Sentinel: {result['status']}")
    print(f"Next action: {result['next_action']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
