#!/usr/bin/env python3
"""Render an execution queue for the LIMINA smoke capture tranche."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = ROOT / "data" / "limina_smoke_capture_tasks.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_H_A_LOCAL = ROOT / "data" / "nhi_pedot_h_a_smoke_local_capture_template.csv"
DEFAULT_H_A_OUTSOURCE = ROOT / "data" / "nhi_pedot_h_a_smoke_osmolality_outsource_template.csv"
DEFAULT_ZRC_LOCAL = ROOT / "data" / "zrc_nd_phase_a_smoke_local_capture_template.csv"
DEFAULT_ZRC_OUTSOURCE = ROOT / "data" / "zrc_nd_phase_a_smoke_osmolality_outsource_template.csv"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_execution_queue.json"
DEFAULT_CSV = ROOT / "data" / "limina_smoke_execution_queue.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_execution_queue.md"

H_A_BRANCH = "NHI-PEDOT H-A"
ZRC_BRANCH = "ZRC-ND Phase A"
H_A_SMOKE_ROOT = "data/source_files/smoke/h_a"
ZRC_SMOKE_ROOT = "data/source_files/smoke/zrc_nd_phase_a"
SOURCE_FILE_SPLIT_RE = re.compile(r"[;\n|]+")

CSV_FIELDS = [
    "queue_id",
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
    "current_value_status",
    "provenance_status",
    "source_class",
    "source_file_requirement",
    "recommended_source_file",
    "capture_instruction",
    "post_fill_check",
]


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
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def sanitize(raw: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", clean(raw))
    return value.strip("_") or "blank"


def resolve_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return ROOT / path


def split_source_files(raw: str) -> list[str]:
    return [
        item.strip().strip("\"'")
        for item in SOURCE_FILE_SPLIT_RE.split(clean(raw))
        if item.strip().strip("\"'")
    ]


def source_files_exist(raw: str) -> bool:
    refs = split_source_files(raw)
    return bool(refs) and all(resolve_path(ref).is_file() for ref in refs)


def h_a_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (clean(row.get("run_id")), clean(row.get("sample_event")), clean(row.get("target_field")))


def template_rows_by_file(args: argparse.Namespace) -> dict[str, list[dict[str, str]]]:
    return {
        rel(args.h_a_local): load_csv(args.h_a_local)[1],
        rel(args.h_a_outsource): load_csv(args.h_a_outsource)[1],
        rel(args.zrc_local): load_csv(args.zrc_local)[1],
        rel(args.zrc_outsource): load_csv(args.zrc_outsource)[1],
    }


def source_class_for_task(task: dict[str, str]) -> str:
    field = clean(task.get("wide_field")) or clean(task.get("target_field"))
    instrument_class = clean(task.get("instrument_class"))
    requirement = clean(task.get("source_file_requirement")).lower()
    if "osmolality" in field or "osmometer" in instrument_class or "osmometer" in requirement:
        return "osmometer_report_or_export"
    if "conductivity" in field:
        return "conductivity_meter_export_or_photo"
    if field in {"pH", "pH_initial", "pH_final"}:
        return "pH_meter_export_or_photo"
    if field == "temperature_c":
        return "temperature_or_incubator_log"
    if field in {"visible_precipitate", "visible_shedding", "delamination_score", "optical_transparency_fraction"}:
        return "image_or_scoring_worksheet"
    if field in {"swelling_fraction", "membrane_area_cm2", "initial_volume_ml"}:
        return "swelling_dimension_or_mass_worksheet"
    if field in {
        "membrane_lot",
        "prefilter_lot",
        "electrode_material",
        "laminin_or_peptide_density",
        "sterilization_or_aseptic_protocol",
        "mea_coupon_id",
    }:
        return "supplier_or_build_record"
    return "bench_or_chain_of_custody_record"


def default_extension(source_class: str) -> str:
    if source_class in {"image_or_scoring_worksheet"}:
        return "png"
    if source_class in {"pH_meter_export_or_photo", "conductivity_meter_export_or_photo"}:
        return "csv"
    if source_class in {"osmometer_report_or_export", "supplier_or_build_record"}:
        return "pdf"
    return "csv"


def recommended_source_file(task: dict[str, str], source_class: str) -> str:
    root = H_A_SMOKE_ROOT if clean(task.get("branch")) == H_A_BRANCH else ZRC_SMOKE_ROOT
    run_id = sanitize(clean(task.get("run_id")))
    event = sanitize(clean(task.get("sample_event")) or "row")
    field = sanitize(clean(task.get("wide_field")) or clean(task.get("target_field")))
    ext = default_extension(source_class)
    return f"{root}/{run_id}/{event}_{field}_{source_class}.{ext}"


def capture_instruction(task: dict[str, str], source_class: str) -> str:
    field = clean(task.get("target_field"))
    branch = clean(task.get("branch"))
    route = clean(task.get("route"))
    if branch == H_A_BRANCH:
        base = "Fill the matching long-form row value plus measured_at, operator_or_agent, instrument_id when measured, and source_file."
    else:
        base = "Fill the target wide-field value on the run_id row; append all supporting files to the row-level source_file field separated by semicolons."
    if route == "outsourced_preferred":
        return f"Obtain external report/export for {field}; {base}"
    if source_class == "supplier_or_build_record":
        return f"Record build/supplier provenance for {field}; {base}"
    return f"Capture {field} with {clean(task.get('instrument_class'))}; {base}"


def task_batch(task: dict[str, str]) -> str:
    branch = clean(task.get("branch"))
    route = clean(task.get("route"))
    source_class = source_class_for_task(task)
    if branch == H_A_BRANCH and route == "outsourced_preferred":
        return "B2_HA_osmolality_external"
    if branch == H_A_BRANCH and source_class in {"supplier_or_build_record", "bench_or_chain_of_custody_record"}:
        return "B0_HA_setup_records"
    if branch == H_A_BRANCH:
        return "B1_HA_local_measurements"
    if route == "outsourced_preferred":
        return "B4_ZRC_external_osmolality"
    return "B3_ZRC_parallel_local"


def task_priority(task: dict[str, str]) -> int:
    batch = task_batch(task)
    if batch.startswith("B0"):
        return 1
    if batch.startswith("B1"):
        return 2
    if batch.startswith("B2"):
        return 3
    if batch.startswith("B3"):
        return 4
    return 5


def row_for_task(task: dict[str, str], rows_by_file: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    entry_file = clean(task.get("entry_file"))
    rows = rows_by_file.get(entry_file, [])
    branch = clean(task.get("branch"))
    if branch == H_A_BRANCH:
        key = (clean(task.get("run_id")), clean(task.get("sample_event")), clean(task.get("target_field")))
        return next((row for row in rows if h_a_key(row) == key), {})
    run_id = clean(task.get("run_id"))
    return next((row for row in rows if clean(row.get("run_id")) == run_id), {})


def current_value(task: dict[str, str], row: dict[str, str]) -> str:
    if clean(task.get("branch")) == H_A_BRANCH:
        return clean(row.get("value"))
    field = clean(task.get("wide_field")) or clean(task.get("target_field"))
    return clean(row.get(field))


def value_status(task: dict[str, str], row: dict[str, str]) -> str:
    value = current_value(task, row)
    if not value:
        return "awaiting_value"
    if not clean(row.get("source_file")):
        return "filled_missing_source_file"
    if not source_files_exist(clean(row.get("source_file"))):
        return "filled_source_file_not_found"
    return "filled_source_file_present"


def provenance_status(row: dict[str, str], requires_instrument: bool) -> str:
    missing = []
    if not clean(row.get("measured_at")) and not clean(row.get("date")):
        missing.append("measured_at_or_date")
    if not clean(row.get("operator_or_agent")):
        missing.append("operator_or_agent")
    if not clean(row.get("source_file")):
        missing.append("source_file")
    if requires_instrument and not clean(row.get("instrument_id")):
        missing.append("instrument_id")
    if missing:
        return "missing_" + "+".join(missing)
    if not source_files_exist(clean(row.get("source_file"))):
        return "source_file_not_found"
    return "provenance_ready_for_preflight"


def build_queue(args: argparse.Namespace) -> dict[str, Any]:
    _task_fields, tasks = load_csv(args.tasks)
    source_manifest = load_json(args.source_manifest)
    rows_by_file = template_rows_by_file(args)
    queue_rows: list[dict[str, Any]] = []
    for index, task in enumerate(tasks, start=1):
        source_class = source_class_for_task(task)
        row = row_for_task(task, rows_by_file)
        route = clean(task.get("route"))
        instrument_class = clean(task.get("instrument_class"))
        requires_instrument = route != "supplier_or_build_record" and instrument_class not in {
            "record_review",
            "bench_or_vendor_record",
        }
        row_locator = (
            f"{clean(task.get('run_id'))}|{clean(task.get('sample_event'))}|{clean(task.get('target_field'))}"
            if clean(task.get("branch")) == H_A_BRANCH
            else f"{clean(task.get('run_id'))}|{clean(task.get('wide_field')) or clean(task.get('target_field'))}"
        )
        queue_rows.append({
            "queue_id": f"SQ-{index:04d}",
            "priority": task_priority(task),
            "batch": task_batch(task),
            "branch": clean(task.get("branch")),
            "route": route,
            "run_id": clean(task.get("run_id")),
            "sample_event": clean(task.get("sample_event")),
            "target_field": clean(task.get("target_field")),
            "unit": clean(task.get("unit")),
            "instrument_class": clean(task.get("instrument_class")),
            "entry_file": clean(task.get("entry_file")),
            "row_locator": row_locator,
            "current_value_status": value_status(task, row),
            "provenance_status": provenance_status(row, requires_instrument) if row else "template_row_missing",
            "source_class": source_class,
            "source_file_requirement": clean(task.get("source_file_requirement")),
            "recommended_source_file": recommended_source_file(task, source_class),
            "capture_instruction": capture_instruction(task, source_class),
            "post_fill_check": "python3 scripts/run_limina_iteration.py",
        })

    branch_counts = Counter(row["branch"] for row in queue_rows)
    batch_counts = Counter(row["batch"] for row in queue_rows)
    status_counts = Counter(row["current_value_status"] for row in queue_rows)
    provenance_counts = Counter(row["provenance_status"] for row in queue_rows)
    return {
        "status": "smoke_execution_queue_ready",
        "purpose": "Convert the smoke capture tranche into field-level execution rows with source-file destinations and post-fill checks.",
        "summary": {
            "queue_row_count": len(queue_rows),
            "branch_counts": dict(branch_counts),
            "batch_counts": dict(batch_counts),
            "value_status_counts": dict(status_counts),
            "provenance_status_counts": dict(provenance_counts),
            "h_a_rows": branch_counts.get(H_A_BRANCH, 0),
            "zrc_rows": branch_counts.get(ZRC_BRANCH, 0),
            "awaiting_value_rows": status_counts.get("awaiting_value", 0),
            "source_ready_rows": status_counts.get("filled_source_file_present", 0),
        },
        "source_manifest": {
            "path": rel(args.source_manifest),
            "status": source_manifest.get("status", "missing"),
            "allowed_root_count": len(source_manifest.get("allowed_roots", [])),
        },
        "generated_artifacts": {
            "json": rel(args.json_out),
            "csv": rel(args.csv_out),
            "report": rel(args.report),
        },
        "queue": queue_rows,
        "post_fill_commands": [
            (
                "python3 scripts/preflight_limina_local_capture.py "
                "--tasks data/limina_smoke_capture_tasks.csv "
                "--h-a-local data/nhi_pedot_h_a_smoke_local_capture_template.csv "
                "--h-a-outsource data/nhi_pedot_h_a_smoke_osmolality_outsource_template.csv "
                "--zrc-local data/zrc_nd_phase_a_smoke_local_capture_template.csv "
                "--zrc-outsource data/zrc_nd_phase_a_smoke_osmolality_outsource_template.csv "
                "--json-out data/limina_smoke_capture_preflight.json "
                "--report reports/limina_smoke_capture_preflight.md"
            ),
            "python3 scripts/run_limina_smoke_rehearsal.py",
            "python3 scripts/run_limina_iteration.py",
        ],
        "boundary": "This queue is execution scaffolding only. It cannot satisfy a material suitability claim without real source files, QC-clean rows, gate passes, and claim_ready=true.",
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Execution Queue",
        "",
        "This converts the smoke tranche into field-level measurement/provenance work items. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Rows:** {summary['queue_row_count']}",
        f"**H-A rows:** {summary['h_a_rows']}",
        f"**ZRC-ND rows:** {summary['zrc_rows']}",
        f"**Awaiting values:** {summary['awaiting_value_rows']}",
        f"**Source-ready rows:** {summary['source_ready_rows']}",
        f"**Source manifest:** `{result['source_manifest']['status']}`; allowed_roots={result['source_manifest']['allowed_root_count']}",
        "",
        "## Batches",
        "",
        "| Batch | Rows | Meaning |",
        "| --- | ---: | --- |",
    ]
    meanings = {
        "B0_HA_setup_records": "H-A setup, medium, lot, build, and custody records.",
        "B1_HA_local_measurements": "H-A local pH, conductivity, temperature, imaging, swelling, and stability readouts.",
        "B2_HA_osmolality_external": "H-A osmometer report/export rows.",
        "B3_ZRC_parallel_local": "Parallel ZRC-ND local/source-record smoke rows.",
        "B4_ZRC_external_osmolality": "Parallel ZRC-ND osmometer report/export rows.",
    }
    for batch, count in sorted(summary["batch_counts"].items()):
        lines.append(f"| `{batch}` | {count} | {meanings.get(batch, '-')} |")

    lines.extend([
        "",
        "## First 40 Queue Rows",
        "",
        "| Priority | Queue | Batch | Branch | Run | Event | Field | Status | Recommended source file |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
    ])
    for row in result["queue"][:40]:
        lines.append(
            f"| {row['priority']} | `{row['queue_id']}` | `{row['batch']}` | {row['branch']} | "
            f"`{row['run_id']}` | `{row['sample_event']}` | `{row['target_field']}` | "
            f"`{row['current_value_status']}` | `{row['recommended_source_file']}` |"
        )
    if len(result["queue"]) > 40:
        lines.append(f"| 0 | `-` | `-` | - | `-` | `-` | `-` | `-` | {len(result['queue']) - 40} additional rows in CSV. |")

    lines.extend([
        "",
        "## Post-Fill Commands",
        "",
    ])
    lines.extend(f"```bash\n{command}\n```" for command in result["post_fill_commands"])
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA smoke execution queue.")
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--h-a-local", type=Path, default=DEFAULT_H_A_LOCAL)
    parser.add_argument("--h-a-outsource", type=Path, default=DEFAULT_H_A_OUTSOURCE)
    parser.add_argument("--zrc-local", type=Path, default=DEFAULT_ZRC_LOCAL)
    parser.add_argument("--zrc-outsource", type=Path, default=DEFAULT_ZRC_OUTSOURCE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_queue(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, result["queue"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Smoke execution queue: {result['status']}")
    print(f"Rows: {result['summary']['queue_row_count']}")
    print(f"Awaiting values: {result['summary']['awaiting_value_rows']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
