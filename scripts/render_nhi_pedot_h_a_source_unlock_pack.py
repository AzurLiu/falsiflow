#!/usr/bin/env python3
"""Render a consolidated source-file handoff pack for NHI-PEDOT H-A."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_VALUES = ROOT / "data" / "nhi_pedot_h_a_source_values.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_source_unlock_pack.json"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_h_a_source_unlock_bundle_manifest.csv"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_source_unlock_pack.md"

CSV_FIELDS = [
    "bundle_id",
    "priority",
    "run_id",
    "article_id",
    "timepoint",
    "source_class",
    "consolidated_source_file",
    "target_fields",
    "source_value_rows",
    "instrument_required",
    "source_file_requirement",
    "existing_source_file",
    "allowed_source_file",
    "operator_action",
]

SOURCE_CLASS_PRIORITY = {
    "bench_or_chain_of_custody_record": 1,
    "supplier_or_build_record": 1,
    "temperature_or_incubator_log": 1,
    "pH_meter_export_or_photo": 2,
    "osmometer_report_or_export": 2,
    "conductivity_meter_export_or_photo": 2,
    "image_or_scoring_worksheet": 3,
    "swelling_dimension_or_mass_worksheet": 3,
}

SOURCE_CLASS_FILENAMES = {
    "bench_or_chain_of_custody_record": "h_a_metadata_chain_of_custody_record.csv",
    "supplier_or_build_record": "h_a_build_or_supplier_record.pdf",
    "temperature_or_incubator_log": "h_a_temperature_or_incubator_log.csv",
    "pH_meter_export_or_photo": "h_a_pH_meter_export_or_photo.csv",
    "osmometer_report_or_export": "h_a_osmolality_report_or_export.pdf",
    "conductivity_meter_export_or_photo": "h_a_conductivity_meter_export_or_photo.csv",
    "image_or_scoring_worksheet": "h_a_physical_inspection_scoring_worksheet.csv",
    "swelling_dimension_or_mass_worksheet": "h_a_swelling_dimension_or_mass_worksheet.csv",
}


def clean(value: Any) -> str:
    return str(value or "").strip()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def resolve_path(raw: str) -> Path:
    path = Path(clean(raw)).expanduser()
    return path if path.is_absolute() else ROOT / path


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def allowed_roots(manifest: dict[str, Any]) -> list[Path]:
    roots: list[Path] = []
    for row in manifest.get("allowed_roots", []):
        raw = clean(row.get("path"))
        if not raw:
            continue
        path = Path(raw)
        roots.append(path if path.is_absolute() else ROOT / path)
    return roots


def parse_run_id(run_id: str) -> tuple[str, str]:
    marker = "-R1-"
    if marker not in run_id:
        return run_id, ""
    prefix, timepoint = run_id.split(marker, 1)
    article = prefix.replace("NHIPEDOT-H-A-", "")
    return article, timepoint.replace("_", " ")


def source_file_for(run_id: str, source_class: str) -> str:
    filename = SOURCE_CLASS_FILENAMES.get(source_class, f"h_a_{source_class}.csv")
    if source_class == "bench_or_chain_of_custody_record":
        return f"data/source_files/bench_records/h_a/{run_id}/{filename}"
    if source_class == "supplier_or_build_record":
        return f"data/source_files/build_records/h_a/{run_id}/{filename}"
    if source_class == "osmometer_report_or_export":
        return f"data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports/{run_id}/{filename}"
    return f"data/source_files/full/h_a/{run_id}/{filename}"


def truthy(raw: str) -> bool:
    return clean(raw).lower() in {"true", "yes", "1"}


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    fields, rows = load_csv(args.source_values)
    manifest = load_json(args.source_manifest)
    roots = allowed_roots(manifest)
    required = {"run_id", "target_field", "source_class", "instrument_required", "source_file_requirement"}
    missing_fields = sorted(required - set(fields))
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        run_id = clean(row.get("run_id"))
        source_class = clean(row.get("source_class"))
        if run_id and source_class:
            groups[(run_id, source_class)].append(row)

    bundle_rows: list[dict[str, Any]] = []
    for index, ((run_id, source_class), grouped_rows) in enumerate(sorted(groups.items()), start=1):
        article_id, timepoint = parse_run_id(run_id)
        source_file = source_file_for(run_id, source_class)
        source_path = resolve_path(source_file)
        allowed = bool(roots) and any(path_is_within(source_path, root) for root in roots)
        target_fields = sorted({clean(row.get("target_field")) for row in grouped_rows if clean(row.get("target_field"))})
        requirements = sorted({clean(row.get("source_file_requirement")) for row in grouped_rows if clean(row.get("source_file_requirement"))})
        instrument_required = any(truthy(row.get("instrument_required", "")) for row in grouped_rows)
        priority = SOURCE_CLASS_PRIORITY.get(source_class, 4)
        bundle_rows.append({
            "bundle_id": f"H-A-BUNDLE-{index:03d}",
            "priority": priority,
            "run_id": run_id,
            "article_id": article_id,
            "timepoint": timepoint,
            "source_class": source_class,
            "consolidated_source_file": source_file,
            "target_fields": ";".join(target_fields),
            "source_value_rows": len(grouped_rows),
            "instrument_required": str(instrument_required).lower(),
            "source_file_requirement": " / ".join(requirements),
            "existing_source_file": str(source_path.is_file()).lower(),
            "allowed_source_file": str(allowed).lower(),
            "operator_action": (
                "Place the real raw export/report/worksheet at this path, then cite this same path "
                "for each listed target_field in data/nhi_pedot_h_a_source_values.csv."
            ),
        })

    class_counts = Counter(row["source_class"] for row in bundle_rows)
    priority_counts = Counter(str(row["priority"]) for row in bundle_rows)
    existing = sum(1 for row in bundle_rows if row["existing_source_file"] == "true")
    allowed_count = sum(1 for row in bundle_rows if row["allowed_source_file"] == "true")
    status = "h_a_source_unlock_pack_ready"
    if missing_fields:
        status = "h_a_source_unlock_pack_missing_source_columns"
    elif bundle_rows and allowed_count != len(bundle_rows):
        status = "h_a_source_unlock_pack_has_disallowed_paths"
    elif not bundle_rows:
        status = "h_a_source_unlock_pack_no_rows"

    return {
        "status": status,
        "boundary": (
            "This handoff pack consolidates required source-file delivery paths only. It does not create "
            "measured evidence; importers and claim audit still require real files and real values."
        ),
        "summary": {
            "source_value_rows": len(rows),
            "bundle_count": len(bundle_rows),
            "existing_bundle_files": existing,
            "missing_bundle_files": len(bundle_rows) - existing,
            "allowed_bundle_files": allowed_count,
            "source_class_counts": dict(class_counts),
            "priority_counts": dict(priority_counts),
            "missing_required_columns": missing_fields,
        },
        "inputs": {
            "source_values": rel(args.source_values),
            "source_manifest": rel(args.source_manifest),
        },
        "generated_artifacts": {
            "json": rel(args.json_out),
            "csv": rel(args.csv_out),
            "report": rel(args.report),
        },
        "bundles": bundle_rows,
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A Source Unlock Pack",
        "",
        "This groups H-A source-value rows into consolidated raw-file handoff bundles. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Source-value rows:** {summary['source_value_rows']}",
        f"**Consolidated bundles:** {summary['bundle_count']}",
        f"**Existing bundle files:** {summary['existing_bundle_files']}",
        f"**Missing bundle files:** {summary['missing_bundle_files']}",
        "",
        "## Bundle Priorities",
        "",
        "| Priority | Meaning | Bundles |",
        "| ---: | --- | ---: |",
        f"| 1 | setup, custody, build, and incubation provenance | {summary['priority_counts'].get('1', 0)} |",
        f"| 2 | pH, osmolality, and conductivity exports | {summary['priority_counts'].get('2', 0)} |",
        f"| 3 | physical inspection, swelling, delamination, and transparency records | {summary['priority_counts'].get('3', 0)} |",
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
        "## First 40 Bundles",
        "",
        "| Priority | Run | Source class | Rows unlocked | Target fields | Consolidated source file |",
        "| ---: | --- | --- | ---: | --- | --- |",
    ])
    for row in result["bundles"][:40]:
        lines.append(
            f"| {row['priority']} | `{row['run_id']}` | `{row['source_class']}` | "
            f"{row['source_value_rows']} | `{row['target_fields']}` | `{row['consolidated_source_file']}` |"
        )
    remaining = len(result["bundles"]) - 40
    if remaining > 0:
        lines.append(f"| - | - | - | - | - | {remaining} additional bundles in CSV. |")

    lines.extend([
        "",
        "## How To Use",
        "",
        "1. Place the real raw export, report, image, worksheet, or chain-of-custody file at the consolidated source path.",
        "2. Fill `value`, `measured_at`, `operator_or_agent`, and `instrument_id` when required in `data/nhi_pedot_h_a_source_values.csv`.",
        "3. Cite the same consolidated source path for every listed target field that the raw file actually supports.",
        "4. Run `python3 scripts/run_limina_iteration.py` and let the importer, QC, H-A gate, and claim audit decide what is real.",
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A consolidated source unlock pack.")
    parser.add_argument("--source-values", type=Path, default=DEFAULT_SOURCE_VALUES)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_pack(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, result["bundles"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    summary = result["summary"]
    print(f"H-A source unlock bundles: {summary['bundle_count']} for {summary['source_value_rows']} source-value rows")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "h_a_source_unlock_pack_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
