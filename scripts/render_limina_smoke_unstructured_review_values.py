#!/usr/bin/env python3
"""Render fillable source-value rows for unstructured LIMINA smoke sources."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INTAKE = ROOT / "data" / "limina_smoke_unstructured_source_intake.csv"
DEFAULT_EXECUTION_PACK = ROOT / "data" / "limina_smoke_starter_execution_pack.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_CSV = ROOT / "data" / "limina_smoke_unstructured_review_values.csv"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_unstructured_review_values.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_unstructured_review_values.md"

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
    "source_class",
    "instrument_required",
    "instrument_class",
    "source_status",
    "source_ready",
    "source_validation",
    "source_size_bytes",
    "source_sha256",
    "image_width",
    "image_height",
    "extraction_mode",
    "value_to_extract",
    "required_metadata",
    "review_status",
    "missing_items",
    "review_instruction",
]
CSV_FIELDS = [*VALUE_FIELDS, *CONTEXT_FIELDS]
READY_SOURCE_STATUS = "ready_for_value_extraction"


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


def by_queue(path: Path) -> dict[str, dict[str, str]]:
    _fields, rows = load_csv(path)
    return {clean(row.get("queue_id")): row for row in rows if clean(row.get("queue_id"))}


def rejected_markers(manifest: dict[str, Any]) -> set[str]:
    markers = set(PLACEHOLDER_MARKERS) | set(SYNTHETIC_MARKERS)
    markers.update(clean(item).lower() for item in manifest.get("rejected_source_markers", []) if clean(item))
    return markers


def has_rejected_marker(raw: str, manifest: dict[str, Any]) -> bool:
    lowered = raw.lower()
    return any(marker in lowered for marker in rejected_markers(manifest))


def review_instruction(row: dict[str, str], source_row: dict[str, str]) -> str:
    instrument_clause = " Fill instrument_id because this row requires an instrument." if row["instrument_required"] == "true" else ""
    return (
        f"Read or OCR `{row['source_file']}` and enter the actual {clean(source_row.get('value_to_extract')) or 'value'}; "
        "include measured_at, operator_or_agent, notes, and apply=yes."
        f"{instrument_clause} Do not cite this review sheet as source_file."
    )


def missing_items(row: dict[str, str], manifest: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in ["value", "measured_at", "operator_or_agent"]:
        value = clean(row.get(field))
        if not value:
            missing.append(field)
        elif has_rejected_marker(value, manifest):
            missing.append(f"{field}_rejected_marker")

    if clean(row.get("instrument_required")).lower() == "true":
        value = clean(row.get("instrument_id"))
        if not value:
            missing.append("instrument_id")
        elif has_rejected_marker(value, manifest):
            missing.append("instrument_id_rejected_marker")

    source_file = clean(row.get("source_file"))
    if not source_file:
        missing.append("source_file")
    elif has_rejected_marker(source_file, manifest):
        missing.append("source_file_rejected_marker")

    if clean(row.get("source_status")) != READY_SOURCE_STATUS:
        missing.append(f"source_{clean(row.get('source_status')) or 'not_ready'}")

    notes = clean(row.get("notes"))
    if notes and has_rejected_marker(notes, manifest):
        missing.append("notes_rejected_marker")

    return sorted(set(missing))


def build_review_values(args: argparse.Namespace) -> dict[str, Any]:
    _intake_fields, intake_rows = load_csv(args.intake)
    existing = by_queue(args.csv_out)
    pack_rows = by_queue(args.execution_pack)
    manifest = load_json(args.source_manifest)
    rows: list[dict[str, str]] = []

    for source_row in intake_rows:
        queue_id = clean(source_row.get("queue_id"))
        previous = existing.get(queue_id, {})
        pack = pack_rows.get(queue_id, {})
        source_status = clean(source_row.get("status"))
        row = {
            "queue_id": queue_id,
            "run_id": clean(source_row.get("run_id")),
            "sample_event": clean(source_row.get("sample_event")),
            "target_field": clean(source_row.get("target_field")),
            "value": clean(previous.get("value")),
            "measured_at": clean(previous.get("measured_at")),
            "operator_or_agent": clean(previous.get("operator_or_agent")),
            "instrument_id": clean(previous.get("instrument_id")),
            "source_file": clean(source_row.get("source_file")),
            "notes": clean(previous.get("notes")),
            "apply": clean(previous.get("apply")),
            "source_class": clean(source_row.get("source_class")),
            "instrument_required": clean(pack.get("instrument_required")),
            "instrument_class": clean(pack.get("instrument_class")),
            "source_status": source_status,
            "source_ready": str(source_status == READY_SOURCE_STATUS).lower(),
            "source_validation": clean(source_row.get("validation")),
            "source_size_bytes": clean(source_row.get("size_bytes")),
            "source_sha256": clean(source_row.get("sha256")),
            "image_width": clean(source_row.get("image_width")),
            "image_height": clean(source_row.get("image_height")),
            "extraction_mode": clean(source_row.get("extraction_mode")),
            "value_to_extract": clean(source_row.get("value_to_extract")),
            "required_metadata": clean(source_row.get("required_metadata")),
            "review_status": "",
            "missing_items": "",
            "review_instruction": "",
        }
        missing = missing_items(row, manifest)
        row["missing_items"] = ";".join(missing)
        if source_status != READY_SOURCE_STATUS:
            row["review_status"] = "awaiting_source_file"
        elif not clean(row.get("value")):
            row["review_status"] = "awaiting_value_entry"
        elif missing:
            row["review_status"] = "blocked"
        else:
            row["review_status"] = "import_ready"
        row["review_instruction"] = review_instruction(row, source_row)
        rows.append(row)

    status_counts = Counter(row["source_status"] for row in rows)
    review_counts = Counter(row["review_status"] for row in rows)
    missing_counts: Counter[str] = Counter()
    for row in rows:
        missing_counts.update(item for item in row["missing_items"].split(";") if item)

    ready_sources = status_counts.get(READY_SOURCE_STATUS, 0)
    missing_sources = status_counts.get("missing_source_file", 0)
    invalid_sources = status_counts.get("invalid_source_file", 0)
    filled_rows = sum(1 for row in rows if clean(row.get("value")))
    import_ready = review_counts.get("import_ready", 0)

    if invalid_sources:
        status = "smoke_unstructured_review_values_has_invalid_sources"
    elif import_ready:
        status = "smoke_unstructured_review_values_import_ready"
    elif filled_rows:
        status = "smoke_unstructured_review_values_partial"
    elif ready_sources:
        status = "smoke_unstructured_review_values_awaiting_value_entry"
    elif rows:
        status = "smoke_unstructured_review_values_waiting_for_source_files"
    else:
        status = "smoke_unstructured_review_values_no_rows"

    return {
        "status": status,
        "summary": {
            "review_rows": len(rows),
            "ready_source_rows": ready_sources,
            "missing_source_rows": missing_sources,
            "invalid_source_rows": invalid_sources,
            "filled_value_rows": filled_rows,
            "import_ready_rows": import_ready,
            "source_status_counts": dict(status_counts),
            "review_status_counts": dict(review_counts),
            "missing_item_counts": dict(missing_counts),
        },
        "inputs": {
            "intake": rel(args.intake),
            "execution_pack": rel(args.execution_pack),
            "source_manifest": rel(args.source_manifest),
        },
        "generated_artifacts": {
            "csv": rel(args.csv_out),
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "rows": rows,
        "accepted_import_schema": VALUE_FIELDS,
        "boundary": (
            "This review-values sheet is a fillable sidecar for manually extracted values from existing "
            "PDF/image/other unstructured source files. It is not measured evidence and cannot support a "
            "claim unless the cited raw source file and filled values pass the importer, preflight, merge/QC, "
            "gate evaluation, and claim audit."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Unstructured Review Values",
        "",
        "This renders fillable source-value rows for unstructured starter source files. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Review rows:** {summary['review_rows']}",
        f"**Ready source rows:** {summary['ready_source_rows']}",
        f"**Missing source rows:** {summary['missing_source_rows']}",
        f"**Invalid source rows:** {summary['invalid_source_rows']}",
        f"**Filled values:** {summary['filled_value_rows']}",
        f"**Import-ready rows:** {summary['import_ready_rows']}",
        f"**CSV:** `{result['generated_artifacts']['csv']}`",
        "",
        "## Fill Contract",
        "",
        "- Fill only values read from real existing PDF/image/other source files listed in `source_file`.",
        "- Keep `source_file` pointed at the raw source file, not this review-values sheet.",
        "- The importer reads only the accepted source-value columns; context columns are operator guidance.",
        "",
        "```text",
        ",".join(result["accepted_import_schema"]),
        "```",
        "",
        "## Review Rows",
        "",
        "| Queue | Field | Source status | Review status | Missing items | Source file |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"][:100]:
        lines.append(
            f"| `{row['queue_id']}` | `{row['target_field']}` | `{row['source_status']}` | "
            f"`{row['review_status']}` | `{row['missing_items']}` | `{row['source_file']}` |"
        )
    if len(result["rows"]) > 100:
        lines.append(f"| `-` | `-` | `-` | `-` | `-` | {len(result['rows']) - 100} additional rows omitted. |")

    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA smoke unstructured review-value rows.")
    parser.add_argument("--intake", type=Path, default=DEFAULT_INTAKE)
    parser.add_argument("--execution-pack", type=Path, default=DEFAULT_EXECUTION_PACK)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_review_values(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Smoke unstructured review values: {result['status']}")
    print(f"Review rows: {result['summary']['review_rows']}")
    print(f"Ready source rows: {result['summary']['ready_source_rows']}")
    print(f"Import-ready rows: {result['summary']['import_ready_rows']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
