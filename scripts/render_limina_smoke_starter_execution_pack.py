#!/usr/bin/env python3
"""Render an execution pack for the LIMINA smoke starter batch."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_VALUES = ROOT / "data" / "limina_smoke_source_values.csv"
DEFAULT_STARTER_READINESS = ROOT / "data" / "limina_smoke_starter_batch_readiness.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_starter_execution_pack.json"
DEFAULT_CSV = ROOT / "data" / "limina_smoke_starter_execution_pack.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_starter_execution_pack.md"
STARTER_ROUND = "R0_pipeline_debug_single_h_a_lead_24h"

CSV_FIELDS = [
    "sequence",
    "queue_id",
    "run_id",
    "sample_event",
    "target_field",
    "unit",
    "source_class",
    "source_file",
    "source_dir",
    "source_file_exists",
    "accepted_extensions",
    "required_source_metadata",
    "value_entry_hint",
    "instrument_required",
    "instrument_class",
    "ready_for_import",
    "missing_items",
    "operator_action",
]

VALUE_HINTS = {
    "date": "Record the actual measurement or exposure date in ISO format.",
    "medium_name": "Record the exact medium name from the bottle, CoA, or chain-of-custody record.",
    "medium_lot": "Record the exact lot identifier from source documentation.",
    "temperature_c": "Record the measured temperature in Celsius.",
    "mea_coupon_id": "Record the exact MEA/coupon/sample identifier.",
    "electrode_material": "Record the exact electrode material from the build or supplier record.",
    "laminin_or_peptide_density": "Record the actual coating density or recipe identifier.",
    "sterilization_or_aseptic_protocol": "Record the exact SOP, batch, or protocol identifier.",
    "pH": "Record the measured pH value from a calibrated meter or reconciled display photo.",
    "osmolality": "Record the measured osmolality in mOsm/kg from the osmometer report.",
    "conductivity": "Record the measured conductivity in mS/cm.",
    "visible_precipitate": "Record the actual scored boolean from the image or worksheet.",
    "visible_shedding": "Record the actual scored boolean from the image or worksheet.",
    "swelling_fraction": "Record the calculated swelling fraction from raw dimensions or mass.",
    "delamination_score": "Record the actual score from the image/scoring worksheet.",
    "optical_transparency_fraction": "Record the calculated transparency fraction from image analysis.",
}


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


def resolve_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return ROOT / path


def source_class_lookup(manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {
        clean(row.get("source_class")): row
        for row in manifest.get("expected_source_classes", [])
        if clean(row.get("source_class"))
    }


def readiness_lookup(path: Path) -> dict[str, dict[str, str]]:
    _fields, rows = load_csv(path)
    return {clean(row.get("queue_id")): row for row in rows if clean(row.get("queue_id"))}


def starter_rows(path: Path) -> list[dict[str, str]]:
    _fields, rows = load_csv(path)
    return [
        row
        for row in rows
        if clean(row.get("recommended_round")) == STARTER_ROUND or clean(row.get("starter_batch")).lower() == "true"
    ]


def operator_action(row: dict[str, str], source_meta: dict[str, str]) -> str:
    field = clean(row.get("target_field"))
    source_file = clean(row.get("source_file"))
    metadata = clean(source_meta.get("required_metadata"))
    return (
        f"Place the real source file at `{source_file}`, verify it includes {metadata or 'run_id, date/time, and method metadata'}, "
        f"then fill queue_id `{clean(row.get('queue_id'))}` in data/limina_smoke_source_values.csv."
    )


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    values = starter_rows(args.source_values)
    readiness = readiness_lookup(args.starter_readiness)
    manifest = load_json(args.source_manifest)
    classes = source_class_lookup(manifest)
    pack_rows: list[dict[str, Any]] = []

    for index, row in enumerate(values, start=1):
        source_class = clean(row.get("source_class"))
        source_meta = classes.get(source_class, {})
        source_file = clean(row.get("source_file"))
        source_path = resolve_path(source_file) if source_file else Path()
        ready = readiness.get(clean(row.get("queue_id")), {})
        pack_rows.append({
            "sequence": index,
            "queue_id": clean(row.get("queue_id")),
            "run_id": clean(row.get("run_id")),
            "sample_event": clean(row.get("sample_event")),
            "target_field": clean(row.get("target_field")),
            "unit": clean(row.get("unit")),
            "source_class": source_class,
            "source_file": source_file,
            "source_dir": rel(source_path.parent) if source_file else "",
            "source_file_exists": str(source_path.is_file()).lower() if source_file else "false",
            "accepted_extensions": clean(source_meta.get("accepted_extensions")),
            "required_source_metadata": clean(source_meta.get("required_metadata")),
            "value_entry_hint": VALUE_HINTS.get(clean(row.get("target_field")), "Record the actual measured or documented value from the source file."),
            "instrument_required": clean(row.get("instrument_required")),
            "instrument_class": clean(row.get("instrument_class")),
            "ready_for_import": clean(ready.get("ready_for_import")) or "false",
            "missing_items": clean(ready.get("missing_items")),
            "operator_action": operator_action(row, source_meta),
        })

    source_class_counts = Counter(row["source_class"] for row in pack_rows)
    source_dirs = {row["source_dir"] for row in pack_rows if row["source_dir"]}
    existing_files = sum(1 for row in pack_rows if row["source_file_exists"] == "true")
    ready_rows = sum(1 for row in pack_rows if row["ready_for_import"] == "true")
    status = "smoke_starter_execution_pack_ready" if pack_rows else "smoke_starter_execution_pack_no_rows"
    return {
        "status": status,
        "summary": {
            "starter_rows": len(pack_rows),
            "source_dir_count": len(source_dirs),
            "source_file_exists_rows": existing_files,
            "ready_for_import_rows": ready_rows,
            "blocked_rows": len(pack_rows) - ready_rows,
            "source_class_counts": dict(source_class_counts),
        },
        "inputs": {
            "source_values": rel(args.source_values),
            "starter_readiness": rel(args.starter_readiness),
            "source_manifest": rel(args.source_manifest),
        },
        "generated_artifacts": {
            "json": rel(args.json_out),
            "csv": rel(args.csv_out),
            "report": rel(args.report),
        },
        "rows": pack_rows,
        "post_fill_commands": [
            "python3 scripts/audit_limina_smoke_starter_batch_readiness.py",
            "python3 scripts/run_limina_iteration.py",
        ],
        "boundary": "This execution pack is an operational checklist only. It does not create raw files, measured rows, or material-suitability evidence.",
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Starter Execution Pack",
        "",
        "This is the execution checklist for the 19-row starter batch. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Starter rows:** {summary['starter_rows']}",
        f"**Source directories:** {summary['source_dir_count']}",
        f"**Existing source files:** {summary['source_file_exists_rows']}",
        f"**Ready for import:** {summary['ready_for_import_rows']}",
        f"**Blocked rows:** {summary['blocked_rows']}",
        f"**CSV:** `{result['generated_artifacts']['csv']}`",
        "",
        "## Source Classes",
        "",
        "| Source class | Rows |",
        "| --- | ---: |",
    ]
    for source_class, count in sorted(summary["source_class_counts"].items()):
        lines.append(f"| `{source_class}` | {count} |")

    lines.extend([
        "",
        "## File Checklist",
        "",
        "| Seq | Queue | Field | Source class | Exists | Required metadata | Source file |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ])
    for row in result["rows"]:
        lines.append(
            f"| {row['sequence']} | `{row['queue_id']}` | `{row['target_field']}` | `{row['source_class']}` | "
            f"`{row['source_file_exists']}` | {row['required_source_metadata']} | `{row['source_file']}` |"
        )

    lines.extend([
        "",
        "## Post-Fill Commands",
        "",
    ])
    lines.extend(f"```bash\n{command}\n```" for command in result["post_fill_commands"])
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA smoke starter execution pack.")
    parser.add_argument("--source-values", type=Path, default=DEFAULT_SOURCE_VALUES)
    parser.add_argument("--starter-readiness", type=Path, default=DEFAULT_STARTER_READINESS)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_pack(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, result["rows"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Smoke starter execution pack: {result['status']}")
    print(f"Starter rows: {result['summary']['starter_rows']}")
    print(f"Ready for import: {result['summary']['ready_for_import_rows']}")
    print(f"Blocked rows: {result['summary']['blocked_rows']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
