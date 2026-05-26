#!/usr/bin/env python3
"""Render a compact ZRC-ND Phase A vendor bundle-entry sheet."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from render_limina_wide_source_values_sheet import clean, instrument_required, rel, safe_name, source_suffix


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_VALUES = ROOT / "data" / "zrc_nd_phase_a_source_values.csv"
DEFAULT_SHEET = ROOT / "data" / "zrc_nd_phase_a_vendor_return_inbox" / "completed_bundle_entry_sheet.csv"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_vendor_bundle_entry_sheet.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_vendor_bundle_entry_sheet.md"
DEFAULT_EXPORT_ROOT = ROOT / "data" / "zrc_nd_phase_a_vendor_return_inbox" / "external_lab_exports"

BASE_FIELDS = [
    "bundle_id",
    "apply",
    "source_file",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "notes",
]

METADATA_FIELDS = [
    "priority",
    "run_id",
    "phase",
    "timepoint",
    "replicate",
    "article_id",
    "source_class",
    "target_fields",
    "target_value_columns",
    "source_value_rows",
    "instrument_required",
    "source_file_exists",
    "allowed_source_file",
    "entry_status",
    "missing_items",
    "operator_action",
]

TRUTHY = {"true", "yes", "1", "y"}

BOUNDARY = (
    "This sheet only consolidates ZRC-ND Phase A vendor-return value entry. It is not measured evidence; "
    "the apply step, source-value importer, merge, sentinel interpretation, readiness audit, and claim audit still control evidence status."
)


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def resolve_path(raw: str) -> Path:
    path = Path(clean(raw)).expanduser()
    return path if path.is_absolute() else ROOT / path


def truthy(raw: str) -> bool:
    return clean(raw).lower() in TRUTHY


def source_groups(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        run_id = clean(row.get("run_id"))
        source_class = clean(row.get("source_class"))
        if run_id and source_class:
            groups[(run_id, source_class)].append(row)
    return groups


def target_fields(rows: list[dict[str, str]]) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        field = clean(row.get("target_field"))
        if field and field not in seen:
            seen.add(field)
            fields.append(field)
    return sorted(fields)


def value_columns(fields: list[str]) -> list[str]:
    return [f"value_{field}" for field in fields]


def all_value_fields(rows: list[dict[str, str]]) -> list[str]:
    return value_columns(target_fields(rows))


def default_source_file(export_root: Path, run_id: str, source_class: str) -> str:
    suffix = source_suffix(source_class)
    path = export_root / safe_name(run_id) / f"{safe_name(source_class)}_vendor_return_bundle{suffix}"
    return rel(path)


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
    apply_requested = truthy(row.get("apply", ""))
    has_any_value = any(clean(row.get(column)) for column in columns)
    missing = entry_missing_items(row, columns)
    if apply_requested and not missing:
        return "ready_to_apply"
    if apply_requested or has_any_value:
        return "blocked"
    return "awaiting_bundle_entry"


def existing_rows(path: Path) -> dict[str, dict[str, str]]:
    _fields, rows = load_csv(path)
    return {clean(row.get("bundle_id")): row for row in rows if clean(row.get("bundle_id"))}


def build_sheet(args: argparse.Namespace) -> dict[str, Any]:
    source_fields, source_rows = load_csv(args.source_values)
    existing = existing_rows(args.sheet)
    all_value_columns = all_value_fields(source_rows)
    fields = [*BASE_FIELDS, *all_value_columns, *METADATA_FIELDS]
    groups = source_groups(source_rows)
    rows: list[dict[str, Any]] = []
    missing_source_columns = sorted(
        {"run_id", "phase", "timepoint", "replicate", "article_id", "target_field", "source_class", "instrument_required"}
        - set(source_fields)
    )

    for index, ((run_id, source_class), grouped) in enumerate(sorted(groups.items()), start=1):
        previous = existing.get(f"{safe_name(run_id)}__{safe_name(source_class)}", {})
        targets = target_fields(grouped)
        columns = value_columns(targets)
        source_file = clean(previous.get("source_file")) or default_source_file(args.export_root, run_id, source_class)
        first = grouped[0]
        requires_instrument = any(
            truthy(row.get("instrument_required", "")) or instrument_required(clean(row.get("target_field")))
            for row in grouped
        )
        row: dict[str, Any] = {
            "bundle_id": f"{safe_name(run_id)}__{safe_name(source_class)}",
            "apply": clean(previous.get("apply")),
            "source_file": source_file,
            "measured_at": clean(previous.get("measured_at")),
            "operator_or_agent": clean(previous.get("operator_or_agent")),
            "instrument_id": clean(previous.get("instrument_id")),
            "notes": clean(previous.get("notes")),
            "priority": str(index),
            "run_id": run_id,
            "phase": clean(first.get("phase")),
            "timepoint": clean(first.get("timepoint")),
            "replicate": clean(first.get("replicate")),
            "article_id": clean(first.get("article_id")),
            "source_class": source_class,
            "target_fields": ";".join(targets),
            "target_value_columns": ";".join(columns),
            "source_value_rows": str(len(grouped)),
            "instrument_required": str(requires_instrument).lower(),
            "source_file_exists": str(resolve_path(source_file).is_file()).lower() if source_file else "false",
            "allowed_source_file": default_source_file(args.export_root, run_id, source_class),
            "operator_action": (
                "Place the real vendor export/report in source_file, fill only real values, "
                "then set apply=yes and run scripts/apply_zrc_nd_phase_a_vendor_bundle_entry_sheet.py."
            ),
        }
        for column in all_value_columns:
            row[column] = clean(previous.get(column))
        missing = entry_missing_items(row, columns)
        row["missing_items"] = ";".join(missing)
        row["entry_status"] = entry_status(row, columns)
        rows.append(row)

    status_counts = Counter(row["entry_status"] for row in rows)
    source_class_counts = Counter(row["source_class"] for row in rows)
    filled_bundle_rows = sum(1 for row in rows if any(clean(row.get(column)) for column in all_value_columns))
    status = "zrc_phase_a_vendor_bundle_entry_sheet_ready"
    if missing_source_columns:
        status = "zrc_phase_a_vendor_bundle_entry_sheet_missing_source_columns"
    elif not rows:
        status = "zrc_phase_a_vendor_bundle_entry_sheet_no_bundles"

    return {
        "status": status,
        "summary": {
            "bundle_rows": len(rows),
            "value_columns": len(all_value_columns),
            "filled_bundle_rows": filled_bundle_rows,
            "ready_to_apply_rows": status_counts.get("ready_to_apply", 0),
            "blocked_rows": status_counts.get("blocked", 0),
            "source_file_exists_rows": sum(1 for row in rows if row["source_file_exists"] == "true"),
            "missing_source_columns": missing_source_columns,
            "entry_status_counts": dict(status_counts),
            "source_class_counts": dict(source_class_counts),
        },
        "inputs": {
            "source_values": rel(args.source_values),
            "export_root": rel(args.export_root),
        },
        "generated_artifacts": {
            "sheet": rel(args.sheet),
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "rows": rows,
        "fields": fields,
        "post_fill_command": "python3 scripts/apply_zrc_nd_phase_a_vendor_bundle_entry_sheet.py",
        "boundary": BOUNDARY,
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# ZRC-ND Phase A Vendor Bundle Entry Sheet",
        "",
        "This is a compact fillable sheet for ZRC-ND Phase A vendor-return source bundles. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Bundle rows:** {summary['bundle_rows']}",
        f"**Value columns:** {summary['value_columns']}",
        f"**Filled bundle rows:** {summary['filled_bundle_rows']}",
        f"**Ready to apply:** {summary['ready_to_apply_rows']}",
        f"**Blocked rows:** {summary['blocked_rows']}",
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
        "- Put the real vendor export/report/image/worksheet at `source_file`.",
        "- Fill the matching `value_*` columns from that real source file.",
        "- Fill `measured_at`, `operator_or_agent`, and `instrument_id` when required.",
        "- Set `apply=yes` only after human review.",
        "",
        "## After Filling",
        "",
        "```bash",
        result["post_fill_command"],
        "python3 scripts/import_limina_wide_source_values.py --profile zrc_phase_a",
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
    parser = argparse.ArgumentParser(description="Render ZRC-ND Phase A vendor bundle-entry sheet.")
    parser.add_argument("--source-values", type=Path, default=DEFAULT_SOURCE_VALUES)
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--export-root", type=Path, default=DEFAULT_EXPORT_ROOT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_sheet(args)
    write_csv(args.sheet, result["fields"], result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps({key: value for key, value in result.items() if key not in {"rows", "fields"}}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"ZRC-ND Phase A vendor bundle entry sheet: {result['status']}")
    print(f"Bundles: {result['summary']['bundle_rows']}")
    print(f"Ready to apply: {result['summary']['ready_to_apply_rows']}")
    print(f"Wrote {args.sheet}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "zrc_phase_a_vendor_bundle_entry_sheet_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
