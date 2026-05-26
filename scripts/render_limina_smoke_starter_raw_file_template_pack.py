#!/usr/bin/env python3
"""Render source-class raw-file templates for the LIMINA smoke starter batch."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXECUTION_PACK = ROOT / "data" / "limina_smoke_starter_execution_pack.csv"
DEFAULT_TEMPLATE_DIR = ROOT / "data" / "limina_smoke_starter_raw_file_templates"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_starter_raw_file_template_pack.json"
DEFAULT_CSV = ROOT / "data" / "limina_smoke_starter_raw_file_template_manifest.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_starter_raw_file_template_pack.md"

MANIFEST_FIELDS = [
    "source_class",
    "template_file",
    "starter_row_count",
    "target_source_files",
    "accepted_extensions",
    "required_source_metadata",
    "template_columns",
    "boundary",
]

COMMON_COLUMNS = [
    "queue_id",
    "run_id",
    "sample_event",
    "target_field",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "value",
    "unit",
    "source_file_to_save_as",
    "method_or_record_id",
    "notes",
]

SOURCE_CLASS_COLUMNS = {
    "bench_or_chain_of_custody_record": [
        "record_type",
        "record_id",
        "sample_id",
        "medium_name",
        "medium_lot",
        "transfer_or_exposure_event",
    ],
    "conductivity_meter_export_or_photo": [
        "conductivity_mS_cm",
        "conductivity_meter_id",
        "standard_check_record_id",
        "temperature_c",
    ],
    "image_or_scoring_worksheet": [
        "image_file_name",
        "imaging_method",
        "scoring_method",
        "score_or_boolean",
        "reviewer",
    ],
    "osmometer_report_or_export": [
        "osmolality_mOsm_kg",
        "osmometer_id",
        "report_id",
        "vendor_or_lab",
    ],
    "pH_meter_export_or_photo": [
        "pH_value",
        "pH_meter_id",
        "calibration_record_id",
        "temperature_c",
    ],
    "supplier_or_build_record": [
        "supplier_or_builder",
        "lot",
        "recipe_or_coa_id",
        "batch_id",
        "label_or_build_record_id",
    ],
    "swelling_dimension_or_mass_worksheet": [
        "pre_measurement",
        "post_measurement",
        "measurement_basis",
        "calculation",
        "swelling_fraction",
    ],
    "temperature_or_incubator_log": [
        "temperature_c",
        "temperature_source",
        "covered_window_start",
        "covered_window_end",
        "probe_or_incubator_id",
    ],
}


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


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def template_columns(source_class: str) -> list[str]:
    extra = SOURCE_CLASS_COLUMNS.get(source_class, [])
    columns = [*COMMON_COLUMNS]
    for column in extra:
        if column not in columns:
            columns.append(column)
    return columns


def template_name(source_class: str) -> str:
    safe = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in source_class)
    return f"{safe}.csv"


def row_for_template(row: dict[str, str], fields: list[str]) -> dict[str, str]:
    values = {
        "queue_id": clean(row.get("queue_id")),
        "run_id": clean(row.get("run_id")),
        "sample_event": clean(row.get("sample_event")),
        "target_field": clean(row.get("target_field")),
        "unit": clean(row.get("unit")),
        "source_file_to_save_as": clean(row.get("source_file")),
    }
    return {field: values.get(field, "") for field in fields}


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    _fields, rows = load_csv(args.execution_pack)
    by_class: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        source_class = clean(row.get("source_class"))
        if source_class:
            by_class.setdefault(source_class, []).append(row)

    manifest_rows: list[dict[str, Any]] = []
    generated_templates: list[str] = []
    args.template_dir.mkdir(parents=True, exist_ok=True)
    class_dir = args.template_dir / "source_class_templates"
    class_dir.mkdir(parents=True, exist_ok=True)

    for source_class, class_rows in sorted(by_class.items()):
        fields_for_class = template_columns(source_class)
        template_path = class_dir / template_name(source_class)
        write_csv(template_path, fields_for_class, [row_for_template(row, fields_for_class) for row in class_rows])
        generated_templates.append(rel(template_path))
        target_files = [clean(row.get("source_file")) for row in class_rows if clean(row.get("source_file"))]
        first = class_rows[0] if class_rows else {}
        manifest_rows.append({
            "source_class": source_class,
            "template_file": rel(template_path),
            "starter_row_count": len(class_rows),
            "target_source_files": ";".join(target_files),
            "accepted_extensions": clean(first.get("accepted_extensions")),
            "required_source_metadata": clean(first.get("required_source_metadata")),
            "template_columns": ";".join(fields_for_class),
            "boundary": "Template only; copy or export real instrument/report/worksheet data to the target source_file path.",
        })

    ext_counts = Counter()
    for row in rows:
        source_file = clean(row.get("source_file"))
        suffix = Path(source_file).suffix.lower() if source_file else ""
        ext_counts[suffix or "none"] += 1

    return {
        "status": "smoke_starter_raw_file_template_pack_ready" if manifest_rows else "smoke_starter_raw_file_template_pack_no_rows",
        "summary": {
            "starter_rows": len(rows),
            "source_class_template_count": len(manifest_rows),
            "template_manifest_rows": len(manifest_rows),
            "generated_template_files": len(generated_templates),
            "target_extension_counts": dict(ext_counts),
        },
        "inputs": {
            "execution_pack": rel(args.execution_pack),
        },
        "generated_artifacts": {
            "template_dir": rel(args.template_dir),
            "json": rel(args.json_out),
            "csv": rel(args.csv_out),
            "report": rel(args.report),
        },
        "templates": generated_templates,
        "manifest_rows": manifest_rows,
        "boundary": (
            "Templates are outside allowed source-file roots and are never measured evidence. "
            "Only real files placed at the target source_file paths can support a measured row."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Starter Raw File Template Pack",
        "",
        "This pack provides source-class CSV templates for the 19-row starter batch. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Starter rows covered:** {summary['starter_rows']}",
        f"**Source-class templates:** {summary['source_class_template_count']}",
        f"**Template directory:** `{result['generated_artifacts']['template_dir']}`",
        "",
        "## Target Extensions",
        "",
        "| Extension | Starter rows |",
        "| --- | ---: |",
    ]
    for extension, count in sorted(summary["target_extension_counts"].items()):
        lines.append(f"| `{extension}` | {count} |")

    lines.extend([
        "",
        "## Templates",
        "",
        "| Source class | Rows | Template | Required source metadata |",
        "| --- | ---: | --- | --- |",
    ])
    for row in result["manifest_rows"]:
        lines.append(
            f"| `{row['source_class']}` | {row['starter_row_count']} | "
            f"`{row['template_file']}` | {row['required_source_metadata']} |"
        )

    lines.extend([
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA starter raw-file template pack.")
    parser.add_argument("--execution-pack", type=Path, default=DEFAULT_EXECUTION_PACK)
    parser.add_argument("--template-dir", type=Path, default=DEFAULT_TEMPLATE_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_pack(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps({key: value for key, value in result.items() if key != "manifest_rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_csv(args.csv_out, MANIFEST_FIELDS, result["manifest_rows"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Smoke starter raw-file template pack: {result['status']}")
    print(f"Starter rows covered: {result['summary']['starter_rows']}")
    print(f"Source-class templates: {result['summary']['source_class_template_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
