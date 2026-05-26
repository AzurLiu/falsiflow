#!/usr/bin/env python3
"""Render a fillable source-value sheet for formal NHI-PEDOT H-A raw rows."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from merge_nhi_pedot_h_a_raw_measurements import RAW_FIELDS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "data" / "nhi_pedot_h_a_raw_measurements_template.csv"
DEFAULT_TASKS = ROOT / "data" / "limina_local_capture_tasks.csv"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_h_a_source_values.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_source_values_sheet.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_source_values_sheet.md"

H_A_BRANCH = "NHI-PEDOT H-A"
CSV_FIELDS = [
    *RAW_FIELDS,
    "route",
    "wide_field",
    "instrument_class",
    "instrument_required",
    "source_class",
    "recommended_source_file",
    "source_file_exists",
    "source_file_requirement",
    "review_status",
    "missing_items",
    "capture_instruction",
]
RECORD_INSTRUMENT_CLASSES = {"record_review", "bench_or_vendor_record"}
SOURCE_CLASS_EXTENSIONS = {
    "bench_or_chain_of_custody_record": ".csv",
    "conductivity_meter_export_or_photo": ".csv",
    "image_or_scoring_worksheet": ".png",
    "osmometer_report_or_export": ".pdf",
    "pH_meter_export_or_photo": ".csv",
    "supplier_or_build_record": ".pdf",
    "swelling_dimension_or_mass_worksheet": ".csv",
    "temperature_or_incubator_log": ".csv",
}
SUPPLIER_FIELDS = {
    "mea_coupon_id",
    "electrode_material",
    "laminin_or_peptide_density",
    "sterilization_or_aseptic_protocol",
}
BENCH_FIELDS = {"date", "medium_name", "medium_lot"}
IMAGE_FIELDS = {"visible_precipitate", "visible_shedding", "delamination_score", "optical_transparency_fraction"}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def clean(value: Any) -> str:
    return str(value or "").strip()


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def row_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (clean(row.get("run_id")), clean(row.get("sample_event")), clean(row.get("target_field")))


def by_key(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    return {row_key(row): row for row in rows if all(row_key(row))}


def task_lookup(path: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    _fields, rows = load_csv(path)
    return {row_key(row): row for row in rows if clean(row.get("branch")) == H_A_BRANCH and all(row_key(row))}


def source_class_for(target_field: str) -> str:
    if target_field in BENCH_FIELDS:
        return "bench_or_chain_of_custody_record"
    if target_field in SUPPLIER_FIELDS:
        return "supplier_or_build_record"
    if target_field == "temperature_c":
        return "temperature_or_incubator_log"
    if target_field in {"pH", "pH_initial", "pH_final"}:
        return "pH_meter_export_or_photo"
    if "conductivity" in target_field:
        return "conductivity_meter_export_or_photo"
    if "osmolality" in target_field:
        return "osmometer_report_or_export"
    if target_field == "swelling_fraction":
        return "swelling_dimension_or_mass_worksheet"
    if target_field in IMAGE_FIELDS:
        return "image_or_scoring_worksheet"
    return "bench_or_chain_of_custody_record"


def route_for(target_field: str, task: dict[str, str]) -> str:
    route = clean(task.get("route"))
    if route:
        return route
    if "osmolality" in target_field:
        return "outsourced_preferred"
    if target_field in BENCH_FIELDS | SUPPLIER_FIELDS:
        return "supplier_or_build_record"
    return "inhouse_ready"


def instrument_class_for(target_field: str, route: str, task: dict[str, str]) -> str:
    instrument_class = clean(task.get("instrument_class"))
    if instrument_class:
        return instrument_class
    if route == "supplier_or_build_record" or target_field in BENCH_FIELDS | SUPPLIER_FIELDS:
        return "record_review"
    if target_field == "temperature_c":
        return "temperature_probe_or_incubator_log"
    if target_field in {"pH", "pH_initial", "pH_final"}:
        return "calibrated_pH_meter"
    if "conductivity" in target_field:
        return "calibrated_conductivity_meter"
    if "osmolality" in target_field:
        return "osmometer_or_external_lab"
    if target_field == "swelling_fraction":
        return "caliper_balance_or_image_analysis"
    if target_field in IMAGE_FIELDS:
        return "imaging_station_or_scoring_sheet"
    return "bench_log"


def instrument_required(route: str, instrument_class: str) -> bool:
    return route != "supplier_or_build_record" and instrument_class not in RECORD_INSTRUMENT_CLASSES


def safe_name(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("_")


def recommended_source_file(row: dict[str, str], route: str, source_class: str) -> str:
    run_id = safe_name(clean(row.get("run_id")))
    sample_event = safe_name(clean(row.get("sample_event")))
    target = safe_name(clean(row.get("target_field")))
    suffix = SOURCE_CLASS_EXTENSIONS.get(source_class, ".csv")
    filename = f"{sample_event}_{target}_{source_class}{suffix}"
    if route == "outsourced_preferred" or source_class == "osmometer_report_or_export":
        return f"data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports/{run_id}/{filename}"
    if source_class == "supplier_or_build_record":
        return f"data/source_files/build_records/h_a/{run_id}/{filename}"
    if source_class == "bench_or_chain_of_custody_record":
        return f"data/source_files/bench_records/h_a/{run_id}/{filename}"
    return f"data/source_files/full/h_a/{run_id}/{filename}"


def resolve_path(raw: str) -> Path:
    path = Path(clean(raw)).expanduser()
    if path.is_absolute():
        return path
    return ROOT / path


def missing_items(row: dict[str, str]) -> list[str]:
    missing: list[str] = []
    for field in ["value", "measured_at", "operator_or_agent", "source_file"]:
        if not clean(row.get(field)):
            missing.append(field)
    if clean(row.get("instrument_required")).lower() == "true" and not clean(row.get("instrument_id")):
        missing.append("instrument_id")
    if clean(row.get("source_file")) and not resolve_path(clean(row.get("source_file"))).is_file():
        missing.append("source_file_missing")
    return missing


def build_sheet(args: argparse.Namespace) -> dict[str, Any]:
    _raw_fields, raw_rows = load_csv(args.raw)
    _existing_fields, existing_rows = load_csv(args.csv_out)
    existing = by_key(existing_rows)
    tasks = task_lookup(args.tasks)
    rows: list[dict[str, Any]] = []

    for raw in raw_rows:
        key = row_key(raw)
        if not all(key):
            continue
        previous = existing.get(key, {})
        task = tasks.get(key, {})
        target_field = clean(raw.get("target_field"))
        source_class = source_class_for(target_field)
        route = route_for(target_field, task)
        instrument_class = instrument_class_for(target_field, route, task)
        required = instrument_required(route, instrument_class)
        recommended = recommended_source_file(raw, route, source_class)
        source_file = clean(previous.get("source_file")) or clean(raw.get("source_file")) or recommended
        row = {
            **{field: clean(previous.get(field)) or clean(raw.get(field)) for field in RAW_FIELDS},
            "source_file": source_file,
            "route": route,
            "wide_field": clean(task.get("wide_field")),
            "instrument_class": instrument_class,
            "instrument_required": str(required).lower(),
            "source_class": source_class,
            "recommended_source_file": recommended,
            "source_file_exists": str(resolve_path(source_file).is_file()).lower() if source_file else "false",
            "source_file_requirement": clean(task.get("source_file_requirement")),
            "review_status": "",
            "missing_items": "",
            "capture_instruction": (
                f"Enter only the real value for {clean(raw.get('run_id'))} {clean(raw.get('sample_event'))} "
                f"{target_field}, citing the raw source_file. Run import then run_limina_iteration.py."
            ),
        }
        missing = missing_items(row)
        row["missing_items"] = ";".join(missing)
        if not clean(row.get("value")):
            row["review_status"] = "awaiting_value_entry"
        elif missing:
            row["review_status"] = "blocked"
        else:
            row["review_status"] = "import_ready"
        rows.append(row)

    review_counts = Counter(row["review_status"] for row in rows)
    source_class_counts = Counter(row["source_class"] for row in rows)
    status = "h_a_source_values_sheet_ready" if rows else "h_a_source_values_sheet_no_rows"
    return {
        "status": status,
        "summary": {
            "source_value_rows": len(rows),
            "filled_value_rows": sum(1 for row in rows if clean(row.get("value"))),
            "source_file_exists_rows": sum(1 for row in rows if row["source_file_exists"] == "true"),
            "import_ready_rows": review_counts.get("import_ready", 0),
            "review_status_counts": dict(review_counts),
            "source_class_counts": dict(source_class_counts),
        },
        "inputs": {"raw": rel(args.raw), "tasks": rel(args.tasks)},
        "generated_artifacts": {"csv": rel(args.csv_out), "json": rel(args.json_out), "report": rel(args.report)},
        "rows": rows,
        "boundary": (
            "This is a fillable sidecar for formal H-A raw rows. It is not measured evidence; "
            "rows count only after import, merge, source-file validation, H-A QC, gate interpretation, and claim audit."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A Source Values Sheet",
        "",
        "This renders a fillable source-backed sidecar for formal H-A raw rows. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Rows:** {summary['source_value_rows']}",
        f"**Filled values:** {summary['filled_value_rows']}",
        f"**Rows with existing source files:** {summary['source_file_exists_rows']}",
        f"**Import-ready rows:** {summary['import_ready_rows']}",
        f"**CSV:** `{result['generated_artifacts']['csv']}`",
        "",
        "## Source Classes",
        "",
        "| Source class | Rows |",
        "| --- | ---: |",
    ]
    for source_class, count in sorted(summary["source_class_counts"].items()):
        lines.append(f"| `{source_class}` | {count} |")
    lines.extend([
        "",
        "## Rows",
        "",
        "| Run | Event | Field | Review | Missing items | Source file |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for row in result["rows"][:120]:
        lines.append(
            f"| `{row['run_id']}` | `{row['sample_event']}` | `{row['target_field']}` | "
            f"`{row['review_status']}` | `{row['missing_items']}` | `{row['source_file']}` |"
        )
    if len(result["rows"]) > 120:
        lines.append(f"| `-` | `-` | `-` | `-` | `-` | {len(result['rows']) - 120} additional rows omitted. |")
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A source values sheet.")
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_sheet(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A source values sheet: {result['status']}")
    print(f"Rows: {result['summary']['source_value_rows']}")
    print(f"Import-ready rows: {result['summary']['import_ready_rows']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
