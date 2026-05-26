#!/usr/bin/env python3
"""Render one fillable sheet for LIMINA smoke measurements."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = ROOT / "data" / "limina_smoke_execution_queue.json"
DEFAULT_SHEET = ROOT / "data" / "limina_smoke_entry_sheet.csv"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_entry_sheet.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_entry_sheet.md"

USER_FIELDS = [
    "apply",
    "value",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "source_file",
    "notes",
]
SHEET_FIELDS = [
    "queue_id",
    *USER_FIELDS,
    "priority",
    "batch",
    "branch",
    "route",
    "run_id",
    "sample_event",
    "target_field",
    "unit",
    "instrument_class",
    "entry_file",
    "row_locator",
    "source_class",
    "source_file_requirement",
    "recommended_source_file",
    "capture_instruction",
    "current_value_status",
    "provenance_status",
]
RECORD_INSTRUMENT_CLASSES = {"record_review", "bench_or_vendor_record"}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def clean(value: Any) -> str:
    return str(value or "").strip()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


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


def requires_instrument(row: dict[str, Any]) -> bool:
    return clean(row.get("route")) != "supplier_or_build_record" and clean(row.get("instrument_class")) not in RECORD_INSTRUMENT_CLASSES


def existing_entry_rows(path: Path) -> dict[str, dict[str, str]]:
    _fields, rows = load_csv(path)
    return {clean(row.get("queue_id")): row for row in rows if clean(row.get("queue_id"))}


def entry_ready(row: dict[str, Any]) -> bool:
    if clean(row.get("apply")).lower() in {"no", "false", "0", "skip"}:
        return False
    if not clean(row.get("value")):
        return False
    required = ["measured_at", "operator_or_agent", "source_file"]
    if requires_instrument(row):
        required.append("instrument_id")
    return all(clean(row.get(field)) for field in required)


def build_sheet(args: argparse.Namespace) -> dict[str, Any]:
    queue_doc = load_json(args.queue)
    queue_rows = queue_doc.get("queue", [])
    existing = existing_entry_rows(args.sheet)
    rows: list[dict[str, Any]] = []
    for queue_row in queue_rows:
        queue_id = clean(queue_row.get("queue_id"))
        previous = existing.get(queue_id, {})
        row = {
            "queue_id": queue_id,
            "apply": clean(previous.get("apply")) or "yes",
            "value": clean(previous.get("value")),
            "measured_at": clean(previous.get("measured_at")),
            "operator_or_agent": clean(previous.get("operator_or_agent")),
            "instrument_id": clean(previous.get("instrument_id")),
            "source_file": clean(previous.get("source_file")) or clean(previous.get("recommended_source_file")),
            "notes": clean(previous.get("notes")),
        }
        for field in SHEET_FIELDS:
            if field not in row:
                row[field] = clean(queue_row.get(field))
        if not row["source_file"]:
            row["source_file"] = clean(queue_row.get("recommended_source_file"))
        rows.append(row)

    filled_value_rows = sum(1 for row in rows if clean(row.get("value")))
    filled_source_rows = sum(1 for row in rows if clean(row.get("source_file")))
    ready_rows = sum(1 for row in rows if entry_ready(row))
    skipped_rows = sum(1 for row in rows if clean(row.get("apply")).lower() in {"no", "false", "0", "skip"})
    return {
        "status": "smoke_entry_sheet_ready",
        "summary": {
            "entry_rows": len(rows),
            "filled_value_rows": filled_value_rows,
            "filled_source_file_rows": filled_source_rows,
            "ready_to_apply_rows": ready_rows,
            "skipped_rows": skipped_rows,
            "blocked_value_rows": max(0, filled_value_rows - ready_rows),
        },
        "source_queue": {
            "path": rel(args.queue),
            "status": queue_doc.get("status", "missing"),
            "queue_row_count": queue_doc.get("summary", {}).get("queue_row_count", 0),
        },
        "generated_artifacts": {
            "sheet": rel(args.sheet),
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "rows": rows,
        "post_fill_command": "python3 scripts/apply_limina_smoke_entry_sheet.py",
        "boundary": "This sheet is a fillable intake surface only. Values require real source files and downstream preflight before they can reach any evidence gate.",
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Entry Sheet",
        "",
        "This is the single fillable intake sheet for smoke-tranche values. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Rows:** {summary['entry_rows']}",
        f"**Filled values:** {summary['filled_value_rows']}",
        f"**Ready to apply:** {summary['ready_to_apply_rows']}",
        f"**Blocked value rows:** {summary['blocked_value_rows']}",
        f"**Sheet:** `{result['generated_artifacts']['sheet']}`",
        "",
        "## How To Use",
        "",
        "- Fill `value`, `measured_at`, `operator_or_agent`, `instrument_id` when required, and `source_file`.",
        "- Put the actual raw file, image, worksheet, report, or calibration log at the `source_file` path.",
        "- Leave `apply=yes` for rows that should be written back to the smoke templates.",
        "",
        "## After Filling",
        "",
        "```bash",
        result["post_fill_command"],
        "python3 scripts/run_limina_iteration.py",
        "```",
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA smoke entry sheet.")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_sheet(args)
    write_csv(args.sheet, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Smoke entry sheet: {result['status']}")
    print(f"Rows: {result['summary']['entry_rows']}")
    print(f"Ready to apply: {result['summary']['ready_to_apply_rows']}")
    print(f"Wrote {args.sheet}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
