#!/usr/bin/env python3
"""Render source-class raw-file templates for formal LIMINA source-value intake."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"

PROFILES = {
    "h_a": {
        "label": "NHI-PEDOT H-A",
        "source_values": ROOT / "data" / "nhi_pedot_h_a_source_values.csv",
        "template_dir": ROOT / "data" / "limina_source_file_templates" / "h_a",
        "json": ROOT / "data" / "nhi_pedot_h_a_source_file_template_pack.json",
        "csv": ROOT / "data" / "nhi_pedot_h_a_source_file_template_manifest.csv",
        "report": ROOT / "reports" / "nhi_pedot_h_a_source_file_template_pack.md",
        "status_prefix": "nhi_pedot_h_a_source_file_template_pack",
    },
    "nhi_forward": {
        "label": "NHI-PEDOT H-B/H-C",
        "source_values": ROOT / "data" / "nhi_pedot_forward_source_values.csv",
        "template_dir": ROOT / "data" / "limina_source_file_templates" / "nhi_forward",
        "json": ROOT / "data" / "nhi_pedot_forward_source_file_template_pack.json",
        "csv": ROOT / "data" / "nhi_pedot_forward_source_file_template_manifest.csv",
        "report": ROOT / "reports" / "nhi_pedot_forward_source_file_template_pack.md",
        "status_prefix": "nhi_pedot_forward_source_file_template_pack",
    },
    "nhi_long": {
        "label": "NHI-PEDOT long-duration",
        "source_values": ROOT / "data" / "nhi_pedot_long_source_values.csv",
        "template_dir": ROOT / "data" / "limina_source_file_templates" / "nhi_long",
        "json": ROOT / "data" / "nhi_pedot_long_source_file_template_pack.json",
        "csv": ROOT / "data" / "nhi_pedot_long_source_file_template_manifest.csv",
        "report": ROOT / "reports" / "nhi_pedot_long_source_file_template_pack.md",
        "status_prefix": "nhi_pedot_long_source_file_template_pack",
    },
    "zrc_phase_a": {
        "label": "ZRC-ND Phase A",
        "source_values": ROOT / "data" / "zrc_nd_phase_a_source_values.csv",
        "template_dir": ROOT / "data" / "limina_source_file_templates" / "zrc_phase_a",
        "json": ROOT / "data" / "zrc_nd_phase_a_source_file_template_pack.json",
        "csv": ROOT / "data" / "zrc_nd_phase_a_source_file_template_manifest.csv",
        "report": ROOT / "reports" / "zrc_nd_phase_a_source_file_template_pack.md",
        "status_prefix": "zrc_nd_phase_a_source_file_template_pack",
    },
}

MANIFEST_FIELDS = [
    "profile",
    "source_class",
    "template_file",
    "template_row_count",
    "target_source_files",
    "accepted_extensions",
    "required_source_metadata",
    "template_columns",
    "boundary",
]

COMMON_COLUMNS = [
    "profile",
    "run_id",
    "phase",
    "sample_event",
    "target_field",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "value",
    "unit",
    "source_file_to_save_as",
    "source_file_requirement",
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
    "electrochemical_or_mea_export": [
        "mea_or_potentiostat_id",
        "channel_or_electrode_id",
        "analysis_method",
        "raw_export_file_id",
        "eis_1khz_ohm",
        "charge_storage_capacity",
        "baseline_noise_uv",
        "electrode_yield_fraction",
        "spike_rate_hz",
        "burst_rate_hz",
        "synchrony",
    ],
    "biological_assay_or_imaging_export": [
        "assay_type",
        "cell_model",
        "culture_day",
        "plate_or_image_id",
        "reader_or_imager_id",
        "viability_fraction",
        "ldh_fold_control",
        "neurite_metric",
        "morphology_score",
    ],
    "biochemical_or_plate_reader_export": [
        "analyte",
        "assay_or_method",
        "instrument_or_vendor_report_id",
        "calibration_or_standard_curve_id",
        "raw_signal",
        "calculated_concentration",
        "dilution_factor",
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
    "pressure_flow_or_resistance_export": [
        "flow_rate_ul_min",
        "pressure_drop",
        "flow_resistance",
        "instrument_id_or_fixture",
        "covered_window_start",
        "covered_window_end",
        "bubble_event_count",
        "inspection_method",
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def safe_name(raw: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in raw).strip("_")


def source_file(row: dict[str, str]) -> str:
    return clean(row.get("source_file")) or clean(row.get("recommended_source_file"))


def template_name(source_class: str) -> str:
    return f"{safe_name(source_class)}.csv"


def template_columns(source_class: str) -> list[str]:
    columns = [*COMMON_COLUMNS]
    for column in SOURCE_CLASS_COLUMNS.get(source_class, []):
        if column not in columns:
            columns.append(column)
    return columns


def source_class_metadata(manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for row in manifest.get("expected_source_classes", []):
        source_class = clean(row.get("source_class"))
        if source_class:
            rows[source_class] = {
                "accepted_extensions": clean(row.get("accepted_extensions")),
                "required_source_metadata": clean(row.get("required_metadata")),
            }
    return rows


def row_for_template(profile: str, row: dict[str, str], fields: list[str]) -> dict[str, str]:
    values = {
        "profile": profile,
        "run_id": clean(row.get("run_id")),
        "phase": clean(row.get("phase")),
        "sample_event": clean(row.get("sample_event")),
        "target_field": clean(row.get("target_field")),
        "unit": clean(row.get("unit")),
        "source_file_to_save_as": source_file(row),
        "source_file_requirement": clean(row.get("source_file_requirement")),
    }
    return {field: values.get(field, "") for field in fields}


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    config = PROFILES[args.profile]
    _fields, rows = load_csv(args.source_values)
    manifest = load_json(args.source_manifest)
    metadata = source_class_metadata(manifest)
    by_class: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        source_class = clean(row.get("source_class"))
        if source_class and source_file(row):
            by_class.setdefault(source_class, []).append(row)

    args.template_dir.mkdir(parents=True, exist_ok=True)
    class_dir = args.template_dir / "source_class_templates"
    class_dir.mkdir(parents=True, exist_ok=True)
    generated_templates: list[str] = []
    manifest_rows: list[dict[str, str]] = []

    for source_class, class_rows in sorted(by_class.items()):
        columns = template_columns(source_class)
        template_path = class_dir / template_name(source_class)
        write_csv(template_path, columns, [row_for_template(args.profile, row, columns) for row in class_rows])
        generated_templates.append(rel(template_path))
        class_meta = metadata.get(source_class, {})
        manifest_rows.append({
            "profile": args.profile,
            "source_class": source_class,
            "template_file": rel(template_path),
            "template_row_count": str(len(class_rows)),
            "target_source_files": ";".join(source_file(row) for row in class_rows),
            "accepted_extensions": class_meta.get("accepted_extensions", ""),
            "required_source_metadata": class_meta.get("required_source_metadata", ""),
            "template_columns": ";".join(columns),
            "boundary": "Template only; copy or export real instrument/report/worksheet data to the target source_file path.",
        })

    ext_counts = Counter(Path(source_file(row)).suffix.lower() or "none" for row in rows if source_file(row))
    class_counts = Counter(clean(row.get("source_class")) for row in rows if clean(row.get("source_class")) and source_file(row))
    status_prefix = config["status_prefix"]
    status = f"{status_prefix}_ready" if manifest_rows else f"{status_prefix}_no_rows"
    return {
        "status": status,
        "profile": args.profile,
        "label": config["label"],
        "summary": {
            "source_value_rows": len(rows),
            "source_class_template_count": len(manifest_rows),
            "template_manifest_rows": len(manifest_rows),
            "generated_template_files": len(generated_templates),
            "target_source_file_count": sum(class_counts.values()),
            "target_extension_counts": dict(ext_counts),
            "source_class_counts": dict(class_counts),
        },
        "inputs": {
            "source_values": rel(args.source_values),
            "source_manifest": rel(args.source_manifest),
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
            "Only real files placed at target source_file paths can support measured rows."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        f"# {result['label']} Source File Template Pack",
        "",
        "This pack provides source-class templates for real raw exports, reports, and worksheets. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Source-value rows covered:** {summary['source_value_rows']}",
        f"**Source-class templates:** {summary['source_class_template_count']}",
        f"**Target source files:** {summary['target_source_file_count']}",
        f"**Template directory:** `{result['generated_artifacts']['template_dir']}`",
        "",
        "## Target Extensions",
        "",
        "| Extension | Target files |",
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
            f"| `{row['source_class']}` | {row['template_row_count']} | "
            f"`{row['template_file']}` | {row['required_source_metadata']} |"
        )

    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render formal LIMINA source-file template packs.")
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-values", type=Path)
    parser.add_argument("--template-dir", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--csv-out", type=Path)
    parser.add_argument("--report", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = PROFILES[args.profile]
    args.source_values = args.source_values or config["source_values"]
    args.template_dir = args.template_dir or config["template_dir"]
    args.json_out = args.json_out or config["json"]
    args.csv_out = args.csv_out or config["csv"]
    args.report = args.report or config["report"]
    result = build_pack(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({key: value for key, value in result.items() if key != "manifest_rows"}, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, MANIFEST_FIELDS, result["manifest_rows"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Source file template pack: {result['status']}")
    print(f"Source-class templates: {result['summary']['source_class_template_count']}")
    print(f"Target source files: {result['summary']['target_source_file_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
