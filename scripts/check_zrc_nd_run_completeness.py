#!/usr/bin/env python3
"""Check measured ZRC-ND run rows against the planned non-cell validation queue."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLANNED = ROOT / "data" / "zrc_nd_planned_runs.csv"
DEFAULT_RUNS = ROOT / "data" / "zrc_nd_validation_runs_active.csv"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_run_completeness.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_run_completeness.md"

CONTROL_ARTICLES = {"no_module_static_control", "bulk_exchange_reference"}
BASELINE_TIMEPOINTS = {"0 h", "0h", "0"}
CORE_FIELDS = [
    "date",
    "operator_or_agent",
    "medium_name",
    "medium_lot",
    "initial_volume_ml",
    "exposure_time_h",
    "temperature_c",
]
ARTICLE_FIELDS = ["membrane_lot", "membrane_area_cm2", "prefilter_lot", "housing_material"]
BLANK_FIELDS = [
    "pH_initial",
    "pH_final",
    "osmolality_initial_mOsm_kg",
    "osmolality_final_mOsm_kg",
    "conductivity_initial_mS_cm",
    "conductivity_final_mS_cm",
    "visible_precipitate",
]
CLEARANCE_FIELDS = ["lactate_initial_mM", "lactate_final_mM", "ammonia_initial_uM", "ammonia_final_uM"]
RETENTION_FIELDS = [
    "bdnf_initial_pg_ml",
    "bdnf_final_pg_ml",
    "ngf_initial_pg_ml",
    "ngf_final_pg_ml",
    "albumin_initial",
    "albumin_final",
    "transferrin_initial",
    "transferrin_final",
    "total_protein_initial",
    "total_protein_final",
]
FOULING_FIELDS = ["flow_resistance_initial", "flow_resistance_final", "bubble_events"]


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def is_blank(value: str | None) -> bool:
    return value is None or value == ""


def is_baseline(row: dict[str, str]) -> bool:
    return row.get("timepoint", "").strip().lower() in BASELINE_TIMEPOINTS


def required_fields(row: dict[str, str]) -> list[str]:
    fields = list(CORE_FIELDS)
    if row.get("article_id") not in CONTROL_ARTICLES:
        fields.extend(ARTICLE_FIELDS)
    fields.extend(BLANK_FIELDS)
    if row.get("phase") in {"B", "C"} and not is_baseline(row):
        fields.extend(CLEARANCE_FIELDS)
        fields.extend(RETENTION_FIELDS)
        fields.extend(FOULING_FIELDS)
    return sorted(dict.fromkeys(fields))


def key(row: dict[str, str]) -> tuple[str, str, str]:
    return (row.get("phase", ""), row.get("timepoint", ""), row.get("replicate", ""))


def check(planned: list[dict[str, str]], runs: list[dict[str, str]]) -> dict[str, Any]:
    planned_by_id = {row["run_id"]: row for row in planned if row.get("run_id")}
    measured = [row for row in runs if row.get("run_id")]
    measured_ids = [row["run_id"] for row in measured]
    counts = Counter(measured_ids)
    duplicate_ids = sorted(run_id for run_id, count in counts.items() if count > 1)
    unknown_ids = sorted(run_id for run_id in set(measured_ids) if run_id not in planned_by_id)
    measured_known = [row for row in measured if row["run_id"] in planned_by_id]
    missing_run_ids = sorted(set(planned_by_id) - {row["run_id"] for row in measured_known})

    row_issues = []
    for row in measured_known:
        planned_row = planned_by_id[row["run_id"]]
        merged = {**planned_row, **{field: value for field, value in row.items() if not is_blank(value)}}
        missing_fields = [field for field in required_fields(planned_row) if is_blank(merged.get(field))]
        if missing_fields:
            row_issues.append({
                "run_id": row["run_id"],
                "phase": planned_row.get("phase", ""),
                "timepoint": planned_row.get("timepoint", ""),
                "article_id": planned_row.get("article_id", ""),
                "missing_fields": missing_fields,
            })

    control_keys = {
        key(row) for row in measured_known
        if row.get("article_id") == "no_module_static_control"
    }
    missing_controls = []
    for row in measured_known:
        planned_row = planned_by_id[row["run_id"]]
        if planned_row.get("article_id") in CONTROL_ARTICLES or is_baseline(planned_row):
            continue
        if key(planned_row) not in control_keys:
            missing_controls.append({
                "run_id": row["run_id"],
                "control_key": "|".join(key(planned_row)),
            })

    gate_evaluable_planned = [
        row for row in planned
        if row.get("article_id") not in CONTROL_ARTICLES and not is_baseline(row)
    ]
    gate_evaluable_measured = [
        row for row in measured_known
        if planned_by_id[row["run_id"]].get("article_id") not in CONTROL_ARTICLES
        and not is_baseline(planned_by_id[row["run_id"]])
    ]

    if not measured:
        status = "no_measured_rows"
    elif duplicate_ids or unknown_ids:
        status = "structural_issues"
    elif row_issues or missing_controls or missing_run_ids:
        status = "incomplete"
    else:
        status = "complete"

    return {
        "status": status,
        "planned_rows": len(planned_by_id),
        "measured_rows": len(measured),
        "measured_known_rows": len(measured_known),
        "missing_run_rows": len(missing_run_ids),
        "gate_evaluable_planned_rows": len(gate_evaluable_planned),
        "gate_evaluable_measured_rows": len(gate_evaluable_measured),
        "duplicate_run_ids": duplicate_ids,
        "unknown_run_ids": unknown_ids,
        "missing_run_ids_sample": missing_run_ids[:25],
        "row_issues": row_issues[:50],
        "missing_controls": missing_controls[:50],
    }


def render(result: dict[str, Any], planned_path: Path, runs_path: Path) -> str:
    lines = [
        "# ZRC-ND Run Completeness Check",
        "",
        f"**Planned rows:** `{planned_path}`",
        f"**Measured rows:** `{runs_path}`",
        f"**Status:** `{result['status']}`",
        f"**Measured/planned:** {result['measured_known_rows']} / {result['planned_rows']}",
        f"**Gate-evaluable measured/planned:** {result['gate_evaluable_measured_rows']} / {result['gate_evaluable_planned_rows']}",
        "",
        "## Structural Issues",
        "",
        f"- Duplicate run IDs: {len(result['duplicate_run_ids'])}",
        f"- Unknown run IDs: {len(result['unknown_run_ids'])}",
        f"- Missing planned run rows: {result['missing_run_rows']}",
        f"- Rows with missing required fields: {len(result['row_issues'])}",
        f"- Gate-evaluable rows missing matched controls: {len(result['missing_controls'])}",
        "",
    ]
    if result["missing_run_ids_sample"]:
        lines.extend(["## Missing Run Sample", ""])
        lines.extend(f"- `{run_id}`" for run_id in result["missing_run_ids_sample"])
        lines.append("")
    if result["row_issues"]:
        lines.extend(["## Row Field Issues", "", "| Run | Phase | Timepoint | Article | Missing fields |", "| --- | --- | --- | --- | --- |"])
        for issue in result["row_issues"]:
            lines.append(
                f"| `{issue['run_id']}` | {issue['phase']} | {issue['timepoint']} | "
                f"`{issue['article_id']}` | {', '.join(issue['missing_fields'])} |"
            )
        lines.append("")
    if result["missing_controls"]:
        lines.extend(["## Missing Matched Controls", "", "| Run | Required control key |", "| --- | --- |"])
        for issue in result["missing_controls"]:
            lines.append(f"| `{issue['run_id']}` | `{issue['control_key']}` |")
        lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check ZRC-ND non-cell run completeness.")
    parser.add_argument("--planned", type=Path, default=DEFAULT_PLANNED)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    planned = load_csv(args.planned)
    runs = load_csv(args.runs)
    result = check(planned, runs)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render(result, args.planned, args.runs), encoding="utf-8")
    print(f"Completeness: {result['status']}")
    print(f"Measured/planned: {result['measured_known_rows']} / {result['planned_rows']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
