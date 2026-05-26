#!/usr/bin/env python3
"""Render a compact H-A vendor-return bundle-entry sheet."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from render_nhi_pedot_h_a_bundle_entry_sheet import (
    DEFAULT_BUNDLE_MANIFEST,
    DEFAULT_SOURCE_VALUES,
    SHEET_FIELDS,
    VALUE_COLUMNS,
    build_sheet as build_base_sheet,
    clean,
    entry_missing_items,
    entry_status,
    existing_entry_rows,
    rel,
    write_csv,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHEET = ROOT / "data" / "nhi_pedot_h_a_vendor_return_inbox" / "completed_bundle_entry_sheet.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_vendor_bundle_entry_sheet.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_vendor_bundle_entry_sheet.md"
DEFAULT_EXPORT_ROOT = ROOT / "data" / "nhi_pedot_h_a_vendor_return_inbox" / "external_lab_exports"

BOUNDARY = (
    "This sheet only prepares a vendor-return scaffold for H-A source-bundle values. It is not measured evidence; "
    "the vendor-return apply step, source-value importer, merge, QC, H-A interpretation, and claim audit still control evidence status."
)


def safe_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", clean(value)).strip("._-")
    return cleaned or "unknown"


def vendor_source_file(row: dict[str, Any], export_root: Path) -> str:
    current = clean(row.get("source_file"))
    filename = Path(current).name if current else f"h_a_{safe_part(clean(row.get('source_class')))}_vendor_return.csv"
    return rel(export_root / safe_part(clean(row.get("run_id"))) / filename)


def target_columns(row: dict[str, Any]) -> list[str]:
    return [column for column in clean(row.get("target_value_columns")).split(";") if column]


def recalc_summary(rows: list[dict[str, Any]], missing_required: list[str]) -> dict[str, Any]:
    status_counts = Counter(row["entry_status"] for row in rows)
    source_class_counts = Counter(row["source_class"] for row in rows)
    return {
        "bundle_rows": len(rows),
        "value_columns": len(VALUE_COLUMNS),
        "filled_bundle_rows": sum(1 for row in rows if any(clean(row.get(column)) for column in VALUE_COLUMNS)),
        "ready_to_apply_rows": status_counts.get("ready_to_apply", 0),
        "blocked_rows": status_counts.get("blocked", 0),
        "source_file_exists_rows": sum(1 for row in rows if row["source_file_exists"] == "true"),
        "missing_required_columns": missing_required,
        "entry_status_counts": dict(status_counts),
        "source_class_counts": dict(source_class_counts),
    }


def status_for_base(base_status: str) -> str:
    if base_status == "h_a_bundle_entry_sheet_ready":
        return "h_a_vendor_bundle_entry_sheet_ready"
    if base_status == "h_a_bundle_entry_sheet_missing_bundle_columns":
        return "h_a_vendor_bundle_entry_sheet_missing_bundle_columns"
    if base_status == "h_a_bundle_entry_sheet_no_bundles":
        return "h_a_vendor_bundle_entry_sheet_no_bundles"
    return "h_a_vendor_bundle_entry_sheet_unknown"


def build_vendor_sheet(args: argparse.Namespace) -> dict[str, Any]:
    base = build_base_sheet(args)
    previous_rows = existing_entry_rows(args.sheet)
    post_fill_command = f"python3 scripts/apply_nhi_pedot_h_a_vendor_bundle_entry_return.py --sheet {rel(args.sheet)}"

    for row in base["rows"]:
        previous = previous_rows.get(clean(row.get("bundle_id")), {})
        default_source = vendor_source_file(row, args.export_root)
        if not clean(previous.get("source_file")):
            row["source_file"] = default_source
        row["allowed_source_file"] = default_source
        row["source_file_exists"] = str((ROOT / clean(row.get("source_file"))).is_file()).lower() if clean(row.get("source_file")) else "false"
        row["operator_action"] = (
            "Place the real vendor export/report/image/worksheet at source_file, fill only real measured/reviewed values, "
            f"then set apply=yes and run {post_fill_command}."
        )
        columns = target_columns(row)
        row["missing_items"] = ";".join(entry_missing_items(row, columns))
        row["entry_status"] = entry_status(row, columns)

    missing_required = base.get("summary", {}).get("missing_required_columns", [])
    base["status"] = status_for_base(base.get("status", ""))
    base["summary"] = recalc_summary(base["rows"], missing_required)
    base["inputs"]["export_root"] = rel(args.export_root)
    base["generated_artifacts"] = {
        "sheet": rel(args.sheet),
        "json": rel(args.json_out),
        "report": rel(args.report),
    }
    base["post_fill_command"] = post_fill_command
    base["boundary"] = BOUNDARY
    return base


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A Vendor Bundle Entry Sheet",
        "",
        "This is a compact fillable sheet for H-A vendor-return source bundles. It is not measured evidence.",
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
        "python3 scripts/import_nhi_pedot_h_a_source_values.py",
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
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A vendor bundle-entry sheet.")
    parser.add_argument("--bundle-manifest", type=Path, default=DEFAULT_BUNDLE_MANIFEST)
    parser.add_argument("--source-values", type=Path, default=DEFAULT_SOURCE_VALUES)
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--export-root", type=Path, default=DEFAULT_EXPORT_ROOT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_vendor_sheet(args)
    write_csv(args.sheet, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A vendor bundle entry sheet: {result['status']}")
    print(f"Bundles: {result['summary']['bundle_rows']}")
    print(f"Ready to apply: {result['summary']['ready_to_apply_rows']}")
    print(f"Wrote {args.sheet}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "h_a_vendor_bundle_entry_sheet_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
