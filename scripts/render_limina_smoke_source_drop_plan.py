#!/usr/bin/env python3
"""Create source-file drop directories for the LIMINA smoke entry sheet."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENTRY_SHEET = ROOT / "data" / "limina_smoke_entry_sheet.csv"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_source_drop_plan.json"
DEFAULT_CSV = ROOT / "data" / "limina_smoke_source_drop_plan.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_source_drop_plan.md"

CSV_FIELDS = [
    "queue_id",
    "branch",
    "batch",
    "run_id",
    "sample_event",
    "target_field",
    "source_class",
    "source_file",
    "source_dir",
    "source_file_exists",
    "value_filled",
    "ready_for_apply",
    "source_file_requirement",
    "capture_instruction",
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
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def resolve_source_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return ROOT / path


def is_ready_for_apply(row: dict[str, str]) -> bool:
    if clean(row.get("apply")).lower() in {"no", "false", "0", "skip"}:
        return False
    if not clean(row.get("value")):
        return False
    required = ["measured_at", "operator_or_agent", "source_file"]
    if clean(row.get("route")) != "supplier_or_build_record" and clean(row.get("instrument_class")) not in {
        "record_review",
        "bench_or_vendor_record",
    }:
        required.append("instrument_id")
    return all(clean(row.get(field)) for field in required)


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    _fields, rows = load_csv(args.entry_sheet)
    plan_rows: list[dict[str, Any]] = []
    created_dirs: set[str] = set()
    missing_dirs: set[str] = set()

    for row in rows:
        source_file = clean(row.get("source_file")) or clean(row.get("recommended_source_file"))
        if not source_file:
            continue
        source_path = resolve_source_path(source_file)
        source_dir = source_path.parent
        before = source_dir.exists()
        source_dir.mkdir(parents=True, exist_ok=True)
        if not before:
            created_dirs.add(rel(source_dir))
        if not source_path.exists():
            missing_dirs.add(rel(source_dir))
        plan_rows.append({
            "queue_id": clean(row.get("queue_id")),
            "branch": clean(row.get("branch")),
            "batch": clean(row.get("batch")),
            "run_id": clean(row.get("run_id")),
            "sample_event": clean(row.get("sample_event")),
            "target_field": clean(row.get("target_field")),
            "source_class": clean(row.get("source_class")),
            "source_file": rel(source_path),
            "source_dir": rel(source_dir),
            "source_file_exists": str(source_path.is_file()).lower(),
            "value_filled": str(bool(clean(row.get("value")))).lower(),
            "ready_for_apply": str(is_ready_for_apply(row)).lower(),
            "source_file_requirement": clean(row.get("source_file_requirement")),
            "capture_instruction": clean(row.get("capture_instruction")),
        })

    branch_counts = Counter(row["branch"] for row in plan_rows)
    batch_counts = Counter(row["batch"] for row in plan_rows)
    run_dirs = {row["source_dir"] for row in plan_rows}
    existing_files = sum(1 for row in plan_rows if row["source_file_exists"] == "true")
    ready_rows = sum(1 for row in plan_rows if row["ready_for_apply"] == "true")
    status = "smoke_source_drop_plan_ready"
    if not plan_rows:
        status = "smoke_source_drop_plan_no_rows"
    return {
        "status": status,
        "summary": {
            "planned_source_file_count": len(plan_rows),
            "source_dir_count": len(run_dirs),
            "created_source_dir_count": len(created_dirs),
            "existing_source_file_count": existing_files,
            "missing_source_file_count": len(plan_rows) - existing_files,
            "ready_for_apply_rows": ready_rows,
            "h_a_rows": branch_counts.get("NHI-PEDOT H-A", 0),
            "zrc_rows": branch_counts.get("ZRC-ND Phase A", 0),
            "batch_counts": dict(batch_counts),
        },
        "inputs": {
            "entry_sheet": rel(args.entry_sheet),
        },
        "generated_artifacts": {
            "json": rel(args.json_out),
            "csv": rel(args.csv_out),
            "report": rel(args.report),
        },
        "created_source_dirs": sorted(created_dirs),
        "source_dirs_missing_files": sorted(missing_dirs),
        "rows": plan_rows,
        "boundary": "This creates directories and a source-file plan only. It does not create raw measurement files or measured evidence.",
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Source Drop Plan",
        "",
        "This creates the concrete drop directories for source files referenced by the smoke entry sheet. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Planned source files:** {summary['planned_source_file_count']}",
        f"**Source directories:** {summary['source_dir_count']}",
        f"**Created directories this run:** {summary['created_source_dir_count']}",
        f"**Existing source files:** {summary['existing_source_file_count']}",
        f"**Missing source files:** {summary['missing_source_file_count']}",
        f"**Ready-for-apply rows:** {summary['ready_for_apply_rows']}",
        "",
        "## Batches",
        "",
        "| Batch | Planned source files |",
        "| --- | ---: |",
    ]
    for batch, count in sorted(summary["batch_counts"].items()):
        lines.append(f"| `{batch}` | {count} |")

    lines.extend([
        "",
        "## First 40 Planned Files",
        "",
        "| Queue | Run | Field | Exists | Source file |",
        "| --- | --- | --- | --- | --- |",
    ])
    for row in result["rows"][:40]:
        lines.append(
            f"| `{row['queue_id']}` | `{row['run_id']}` | `{row['target_field']}` | "
            f"`{row['source_file_exists']}` | `{row['source_file']}` |"
        )
    if len(result["rows"]) > 40:
        lines.append(f"| `-` | `-` | `-` | `-` | {len(result['rows']) - 40} additional planned files in CSV. |")

    lines.extend([
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA smoke source-file drop plan.")
    parser.add_argument("--entry-sheet", type=Path, default=DEFAULT_ENTRY_SHEET)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_plan(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, result["rows"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Smoke source drop plan: {result['status']}")
    print(f"Planned source files: {result['summary']['planned_source_file_count']}")
    print(f"Created directories: {result['summary']['created_source_dir_count']}")
    print(f"Existing source files: {result['summary']['existing_source_file_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
