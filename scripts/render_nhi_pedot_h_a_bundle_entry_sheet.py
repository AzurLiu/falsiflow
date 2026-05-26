#!/usr/bin/env python3
"""Render a consolidated fillable bundle sheet for NHI-PEDOT H-A source values."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE_MANIFEST = ROOT / "data" / "nhi_pedot_h_a_source_unlock_bundle_manifest.csv"
DEFAULT_SOURCE_VALUES = ROOT / "data" / "nhi_pedot_h_a_source_values.csv"
DEFAULT_SHEET = ROOT / "data" / "nhi_pedot_h_a_bundle_entry_sheet.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_bundle_entry_sheet.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_bundle_entry_sheet.md"

VALUE_FIELDS = [
    "date",
    "medium_lot",
    "medium_name",
    "temperature_c",
    "mea_coupon_id",
    "electrode_material",
    "laminin_or_peptide_density",
    "sterilization_or_aseptic_protocol",
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
]
VALUE_COLUMNS = [f"value_{field}" for field in VALUE_FIELDS]
USER_FIELDS = [
    "apply",
    "source_file",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "notes",
    *VALUE_COLUMNS,
]
SHEET_FIELDS = [
    "bundle_id",
    *USER_FIELDS,
    "priority",
    "run_id",
    "article_id",
    "timepoint",
    "source_class",
    "target_fields",
    "target_value_columns",
    "source_value_rows",
    "instrument_required",
    "source_file_requirement",
    "source_file_exists",
    "allowed_source_file",
    "entry_status",
    "missing_items",
    "operator_action",
]


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
        writer = csv.DictWriter(handle, fieldnames=SHEET_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in SHEET_FIELDS} for row in rows])


def resolve_path(raw: str) -> Path:
    path = Path(clean(raw)).expanduser()
    return path if path.is_absolute() else ROOT / path


def truthy(raw: str) -> bool:
    return clean(raw).lower() in {"true", "yes", "1", "y"}


def existing_entry_rows(path: Path) -> dict[str, dict[str, str]]:
    _fields, rows = load_csv(path)
    return {clean(row.get("bundle_id")): row for row in rows if clean(row.get("bundle_id"))}


def source_groups(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        run_id = clean(row.get("run_id"))
        source_class = clean(row.get("source_class"))
        if run_id and source_class:
            groups[(run_id, source_class)].append(row)
    return groups


def value_key(row: dict[str, str]) -> str:
    return clean(row.get("wide_field")) or clean(row.get("target_field"))


def target_value_columns(rows: list[dict[str, str]]) -> list[str]:
    columns = []
    seen: set[str] = set()
    for row in rows:
        key = value_key(row)
        column = f"value_{key}" if key else ""
        if column in VALUE_COLUMNS and column not in seen:
            seen.add(column)
            columns.append(column)
    return columns


def entry_missing_items(row: dict[str, Any], columns: list[str]) -> list[str]:
    missing: list[str] = []
    for field in ["measured_at", "operator_or_agent", "source_file"]:
        if not clean(row.get(field)):
            missing.append(field)
    if truthy(row.get("instrument_required", "")) and not clean(row.get("instrument_id")):
        missing.append("instrument_id")
    for column in columns:
        if not clean(row.get(column)):
            missing.append(column)
    if clean(row.get("source_file")) and not resolve_path(clean(row.get("source_file"))).is_file():
        missing.append("source_file_missing")
    return missing


def entry_status(row: dict[str, Any], columns: list[str]) -> str:
    applied = truthy(row.get("apply", ""))
    has_any_value = any(clean(row.get(column)) for column in columns)
    if not applied and not has_any_value:
        return "awaiting_bundle_entry"
    missing = entry_missing_items(row, columns)
    if applied and not missing:
        return "ready_to_apply"
    if has_any_value or applied:
        return "blocked"
    return "awaiting_bundle_entry"


def build_sheet(args: argparse.Namespace) -> dict[str, Any]:
    bundle_fields, bundle_rows = load_csv(args.bundle_manifest)
    _source_fields, source_rows = load_csv(args.source_values)
    existing = existing_entry_rows(args.sheet)
    groups = source_groups(source_rows)
    rows: list[dict[str, Any]] = []
    required_bundle_fields = {
        "bundle_id",
        "run_id",
        "source_class",
        "consolidated_source_file",
        "instrument_required",
    }
    missing_required = sorted(required_bundle_fields - set(bundle_fields))

    for bundle in bundle_rows:
        bundle_id = clean(bundle.get("bundle_id"))
        previous = existing.get(bundle_id, {})
        grouped_source_rows = groups.get((clean(bundle.get("run_id")), clean(bundle.get("source_class"))), [])
        columns = target_value_columns(grouped_source_rows)
        source_file = clean(previous.get("source_file")) or clean(bundle.get("consolidated_source_file"))
        row = {
            "bundle_id": bundle_id,
            "apply": clean(previous.get("apply")),
            "source_file": source_file,
            "measured_at": clean(previous.get("measured_at")),
            "operator_or_agent": clean(previous.get("operator_or_agent")),
            "instrument_id": clean(previous.get("instrument_id")),
            "notes": clean(previous.get("notes")),
            "priority": clean(bundle.get("priority")),
            "run_id": clean(bundle.get("run_id")),
            "article_id": clean(bundle.get("article_id")),
            "timepoint": clean(bundle.get("timepoint")),
            "source_class": clean(bundle.get("source_class")),
            "target_fields": clean(bundle.get("target_fields")),
            "target_value_columns": ";".join(columns),
            "source_value_rows": clean(bundle.get("source_value_rows")) or str(len(grouped_source_rows)),
            "instrument_required": clean(bundle.get("instrument_required")),
            "source_file_requirement": clean(bundle.get("source_file_requirement")),
            "source_file_exists": str(resolve_path(source_file).is_file()).lower() if source_file else "false",
            "allowed_source_file": clean(bundle.get("allowed_source_file")),
            "operator_action": (
                "Fill only real measured/reviewed values, put the raw source file at source_file, "
                "then set apply=yes and run scripts/apply_nhi_pedot_h_a_bundle_entry_sheet.py."
            ),
        }
        for column in VALUE_COLUMNS:
            row[column] = clean(previous.get(column))
        missing = entry_missing_items(row, columns)
        row["missing_items"] = ";".join(missing)
        row["entry_status"] = entry_status(row, columns)
        rows.append(row)

    status_counts = Counter(row["entry_status"] for row in rows)
    source_class_counts = Counter(row["source_class"] for row in rows)
    ready_rows = status_counts.get("ready_to_apply", 0)
    filled_bundle_rows = sum(1 for row in rows if any(clean(row.get(column)) for column in VALUE_COLUMNS))
    status = "h_a_bundle_entry_sheet_ready"
    if missing_required:
        status = "h_a_bundle_entry_sheet_missing_bundle_columns"
    elif not rows:
        status = "h_a_bundle_entry_sheet_no_bundles"
    return {
        "status": status,
        "summary": {
            "bundle_rows": len(rows),
            "filled_bundle_rows": filled_bundle_rows,
            "ready_to_apply_rows": ready_rows,
            "blocked_rows": status_counts.get("blocked", 0),
            "source_file_exists_rows": sum(1 for row in rows if row["source_file_exists"] == "true"),
            "missing_required_columns": missing_required,
            "entry_status_counts": dict(status_counts),
            "source_class_counts": dict(source_class_counts),
        },
        "inputs": {
            "bundle_manifest": rel(args.bundle_manifest),
            "source_values": rel(args.source_values),
        },
        "generated_artifacts": {
            "sheet": rel(args.sheet),
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "rows": rows,
        "post_fill_command": "python3 scripts/apply_nhi_pedot_h_a_bundle_entry_sheet.py",
        "boundary": (
            "This sheet only consolidates source-value entry across H-A bundles. It is not measured evidence; "
            "the apply step, source-value importer, merge, QC, gates, and claim audit still control evidence status."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A Bundle Entry Sheet",
        "",
        "This is a consolidated fillable sheet for H-A raw-file bundles. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Bundle rows:** {summary['bundle_rows']}",
        f"**Filled bundle rows:** {summary['filled_bundle_rows']}",
        f"**Ready to apply:** {summary['ready_to_apply_rows']}",
        f"**Rows with existing source files:** {summary['source_file_exists_rows']}",
        f"**CSV:** `{result['generated_artifacts']['sheet']}`",
        "",
        "## Source Classes",
        "",
        "| Source class | Bundles |",
        "| --- | ---: |",
    ]
    for source_class, count in sorted(summary["source_class_counts"].items()):
        lines.append(f"| `{source_class}` | {count} |")
    lines.extend([
        "",
        "## How To Use",
        "",
        "- Fill the relevant `value_*` columns for a bundle from the real raw file, report, image, or worksheet.",
        "- Fill `measured_at`, `operator_or_agent`, `instrument_id` when required, and `source_file`.",
        "- Put the actual raw source file at `source_file`, then set `apply=yes` for that bundle.",
        "",
        "## After Filling",
        "",
        "```bash",
        result["post_fill_command"],
        "python3 scripts/run_limina_iteration.py",
        "```",
        "",
        "## First 40 Bundles",
        "",
        "| Bundle | Run | Source class | Status | Missing items | Value columns |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for row in result["rows"][:40]:
        lines.append(
            f"| `{row['bundle_id']}` | `{row['run_id']}` | `{row['source_class']}` | "
            f"`{row['entry_status']}` | `{row['missing_items']}` | `{row['target_value_columns']}` |"
        )
    remaining = len(result["rows"]) - 40
    if remaining > 0:
        lines.append(f"| `-` | `-` | `-` | `-` | `-` | {remaining} additional bundles in CSV. |")
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A bundle entry sheet.")
    parser.add_argument("--bundle-manifest", type=Path, default=DEFAULT_BUNDLE_MANIFEST)
    parser.add_argument("--source-values", type=Path, default=DEFAULT_SOURCE_VALUES)
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_sheet(args)
    write_csv(args.sheet, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A bundle entry sheet: {result['status']}")
    print(f"Bundles: {result['summary']['bundle_rows']}")
    print(f"Ready to apply: {result['summary']['ready_to_apply_rows']}")
    print(f"Wrote {args.sheet}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "h_a_bundle_entry_sheet_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
