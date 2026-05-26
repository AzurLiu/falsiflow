#!/usr/bin/env python3
"""Render the consolidated source-values sheet for LIMINA smoke capture."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENTRY_SHEET = ROOT / "data" / "limina_smoke_entry_sheet.csv"
DEFAULT_SOURCE_DROP_PLAN = ROOT / "data" / "limina_smoke_source_drop_plan.csv"
DEFAULT_SHEET = ROOT / "data" / "limina_smoke_source_values.csv"
DEFAULT_STARTER = ROOT / "data" / "limina_smoke_source_values_starter_batch.csv"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_source_values_sheet.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_source_values_sheet.md"

VALUE_FIELDS = [
    "queue_id",
    "run_id",
    "sample_event",
    "target_field",
    "value",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "source_file",
    "notes",
    "apply",
]
CONTEXT_FIELDS = [
    "priority",
    "batch",
    "branch",
    "route",
    "unit",
    "instrument_class",
    "instrument_required",
    "source_class",
    "recommended_round",
    "starter_batch",
    "source_dir",
    "source_file_exists",
    "source_file_requirement",
    "capture_instruction",
]
SHEET_FIELDS = [*VALUE_FIELDS, *CONTEXT_FIELDS]
RECORD_INSTRUMENT_CLASSES = {"record_review", "bench_or_vendor_record"}
STARTER_RUN_ID = "NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h"


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
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return ROOT / path


def existing_by_queue(path: Path) -> dict[str, dict[str, str]]:
    _fields, rows = load_csv(path)
    return {clean(row.get("queue_id")): row for row in rows if clean(row.get("queue_id"))}


def plan_by_queue(path: Path) -> dict[str, dict[str, str]]:
    _fields, rows = load_csv(path)
    return {clean(row.get("queue_id")): row for row in rows if clean(row.get("queue_id"))}


def instrument_required(row: dict[str, str]) -> bool:
    return clean(row.get("route")) != "supplier_or_build_record" and clean(row.get("instrument_class")) not in RECORD_INSTRUMENT_CLASSES


def recommended_round(row: dict[str, str]) -> str:
    if clean(row.get("run_id")) == STARTER_RUN_ID:
        return "R0_pipeline_debug_single_h_a_lead_24h"
    batch = clean(row.get("batch"))
    if batch in {"B0_HA_setup_records", "B1_HA_local_measurements"}:
        return "R1_h_a_local_and_records"
    if batch == "B2_HA_osmolality_external":
        return "R2_h_a_osmolality_external"
    if batch == "B3_ZRC_parallel_local":
        return "R3_zrc_local_and_records"
    if batch == "B4_ZRC_external_osmolality":
        return "R4_zrc_osmolality_external"
    return "R9_unclassified"


def entry_ready(row: dict[str, str]) -> bool:
    if not clean(row.get("value")):
        return False
    required = ["measured_at", "operator_or_agent", "source_file"]
    if row.get("instrument_required") == "true":
        required.append("instrument_id")
    if not all(clean(row.get(field)) for field in required):
        return False
    return resolve_path(clean(row.get("source_file"))).is_file()


def build_sheet(args: argparse.Namespace) -> dict[str, Any]:
    _entry_fields, entry_rows = load_csv(args.entry_sheet)
    existing = existing_by_queue(args.sheet)
    plan_rows = plan_by_queue(args.source_drop_plan)
    rows: list[dict[str, Any]] = []

    for entry in entry_rows:
        queue_id = clean(entry.get("queue_id"))
        previous = existing.get(queue_id, {})
        source_file = clean(previous.get("source_file")) or clean(entry.get("source_file")) or clean(entry.get("recommended_source_file"))
        plan = plan_rows.get(queue_id, {})
        round_id = recommended_round(entry)
        row = {
            "queue_id": queue_id,
            "run_id": clean(entry.get("run_id")),
            "sample_event": clean(entry.get("sample_event")),
            "target_field": clean(entry.get("target_field")),
            "value": clean(previous.get("value")),
            "measured_at": clean(previous.get("measured_at")),
            "operator_or_agent": clean(previous.get("operator_or_agent")),
            "instrument_id": clean(previous.get("instrument_id")),
            "source_file": source_file,
            "notes": clean(previous.get("notes")),
            "apply": clean(previous.get("apply")),
            "priority": clean(entry.get("priority")),
            "batch": clean(entry.get("batch")),
            "branch": clean(entry.get("branch")),
            "route": clean(entry.get("route")),
            "unit": clean(entry.get("unit")),
            "instrument_class": clean(entry.get("instrument_class")),
            "instrument_required": str(instrument_required(entry)).lower(),
            "source_class": clean(entry.get("source_class")),
            "recommended_round": round_id,
            "starter_batch": str(round_id == "R0_pipeline_debug_single_h_a_lead_24h").lower(),
            "source_dir": clean(plan.get("source_dir")) or rel(resolve_path(source_file).parent) if source_file else "",
            "source_file_exists": str(resolve_path(source_file).is_file()).lower() if source_file else "false",
            "source_file_requirement": clean(entry.get("source_file_requirement")),
            "capture_instruction": clean(entry.get("capture_instruction")),
        }
        rows.append(row)

    starter_rows = [row for row in rows if row["starter_batch"] == "true"]
    round_counts = Counter(row["recommended_round"] for row in rows)
    batch_counts = Counter(row["batch"] for row in rows)
    filled_rows = sum(1 for row in rows if clean(row.get("value")))
    source_file_exists = sum(1 for row in rows if row["source_file_exists"] == "true")
    import_ready = sum(1 for row in rows if entry_ready(row))
    return {
        "status": "smoke_source_values_sheet_ready" if rows else "smoke_source_values_sheet_no_rows",
        "summary": {
            "source_value_rows": len(rows),
            "starter_batch_rows": len(starter_rows),
            "filled_value_rows": filled_rows,
            "source_file_exists_rows": source_file_exists,
            "import_ready_rows": import_ready,
            "recommended_round_counts": dict(round_counts),
            "batch_counts": dict(batch_counts),
        },
        "inputs": {
            "entry_sheet": rel(args.entry_sheet),
            "source_drop_plan": rel(args.source_drop_plan),
        },
        "generated_artifacts": {
            "sheet": rel(args.sheet),
            "starter_batch": rel(args.starter),
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "rows": rows,
        "starter_rows": starter_rows,
        "boundary": (
            "This is a fillable intake sheet for source-backed values only. It is not a raw source file "
            "and does not count as measured evidence."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Source Values Sheet",
        "",
        "This renders the consolidated sheet read by the source-value importer. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Rows:** {summary['source_value_rows']}",
        f"**Starter batch rows:** {summary['starter_batch_rows']}",
        f"**Filled values:** {summary['filled_value_rows']}",
        f"**Rows with existing source files:** {summary['source_file_exists_rows']}",
        f"**Import-ready rows:** {summary['import_ready_rows']}",
        f"**Sheet:** `{result['generated_artifacts']['sheet']}`",
        f"**Starter batch:** `{result['generated_artifacts']['starter_batch']}`",
        "",
        "## Recommended Rounds",
        "",
        "| Round | Rows | Purpose |",
        "| --- | ---: | --- |",
    ]
    meanings = {
        "R0_pipeline_debug_single_h_a_lead_24h": "One 19-field lead 24h run to prove raw-file intake, importer, apply, preflight, and rehearsal wiring.",
        "R1_h_a_local_and_records": "H-A records plus local pH, conductivity, temperature, imaging, swelling, and stability rows.",
        "R2_h_a_osmolality_external": "H-A osmometer report/export rows.",
        "R3_zrc_local_and_records": "Parallel ZRC-ND records and local/source-record rows.",
        "R4_zrc_osmolality_external": "Parallel ZRC-ND osmometer report/export rows.",
    }
    for round_id, count in sorted(summary["recommended_round_counts"].items()):
        lines.append(f"| `{round_id}` | {count} | {meanings.get(round_id, '-')} |")

    lines.extend([
        "",
        "## Fill Contract",
        "",
        "- The importer reads `queue_id`, `value`, `measured_at`, `operator_or_agent`, `instrument_id`, `source_file`, `notes`, and `apply`.",
        "- `instrument_id` is required when `instrument_required=true`.",
        "- `source_file` must point to the raw export, report, image, or worksheet, not this source-values sheet.",
        "",
        "## Starter Rows",
        "",
        "| Queue | Run | Field | Instrument required | Source file |",
        "| --- | --- | --- | --- | --- |",
    ])
    for row in result["starter_rows"]:
        lines.append(
            f"| `{row['queue_id']}` | `{row['run_id']}` | `{row['target_field']}` | "
            f"`{row['instrument_required']}` | `{row['source_file']}` |"
        )

    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA smoke source-values sheet.")
    parser.add_argument("--entry-sheet", type=Path, default=DEFAULT_ENTRY_SHEET)
    parser.add_argument("--source-drop-plan", type=Path, default=DEFAULT_SOURCE_DROP_PLAN)
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--starter", type=Path, default=DEFAULT_STARTER)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_sheet(args)
    write_csv(args.sheet, result["rows"])
    write_csv(args.starter, result["starter_rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps({key: value for key, value in result.items() if key not in {"rows", "starter_rows"}}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Smoke source values sheet: {result['status']}")
    print(f"Rows: {result['summary']['source_value_rows']}")
    print(f"Starter rows: {result['summary']['starter_batch_rows']}")
    print(f"Import-ready rows: {result['summary']['import_ready_rows']}")
    print(f"Wrote {args.sheet}")
    print(f"Wrote {args.starter}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
