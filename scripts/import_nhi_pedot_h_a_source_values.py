#!/usr/bin/env python3
"""Import validated H-A source-value sidecars into the formal raw template."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS
from merge_nhi_pedot_h_a_raw_measurements import RAW_FIELDS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "data" / "nhi_pedot_h_a_raw_measurements_template.csv"
DEFAULT_SOURCE_VALUES = ROOT / "data" / "nhi_pedot_h_a_source_values.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_source_value_import.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_source_value_import.md"
DEFAULT_VALUE_GLOBS = [
    "data/nhi_pedot_h_a_raw_csv_extracted_values.csv",
    "data/nhi_pedot_h_a_vendor_return_inbox/completed_raw_measurements.csv",
]
SOURCE_SPLIT_CHARS = [";", "|", "\n"]
RECORD_INSTRUMENT_CLASSES = {"record_review", "bench_or_vendor_record"}
USER_FIELDS = ["value", "measured_at", "operator_or_agent", "instrument_id", "source_file", "notes"]
FILLABLE_VALUE_FIELDS = ["value", "measured_at", "operator_or_agent", "instrument_id", "notes"]


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


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def row_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (clean(row.get("run_id")), clean(row.get("sample_event")), clean(row.get("target_field")))


def raw_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    return {row_key(row): row for row in rows if all(row_key(row))}


def split_source_files(raw: str) -> list[str]:
    refs = [clean(raw).strip("\"'")]
    for char in SOURCE_SPLIT_CHARS:
        expanded: list[str] = []
        for ref in refs:
            expanded.extend(part.strip().strip("\"'") for part in ref.split(char))
        refs = expanded
    return [ref for ref in refs if ref]


def resolve_path(raw: str) -> Path:
    path = Path(clean(raw)).expanduser()
    if path.is_absolute():
        return path
    return ROOT / path


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
        if not path.is_absolute():
            path = ROOT / path
        roots.append(path)
    return roots


def rejected_markers(manifest: dict[str, Any]) -> set[str]:
    markers = set(PLACEHOLDER_MARKERS) | set(SYNTHETIC_MARKERS)
    markers.update(clean(item).lower() for item in manifest.get("rejected_source_markers", []) if clean(item))
    return markers


def has_rejected_marker(raw: str, manifest: dict[str, Any]) -> bool:
    lowered = raw.lower()
    return any(marker in lowered for marker in rejected_markers(manifest))


def add_issue(
    issues: list[dict[str, str]],
    severity: str,
    value_file: Path,
    row_number: int,
    field: str,
    message: str,
    row: dict[str, str] | None = None,
) -> None:
    issues.append({
        "severity": severity,
        "value_file": rel(value_file),
        "row_number": str(row_number),
        "run_id": clean((row or {}).get("run_id")),
        "sample_event": clean((row or {}).get("sample_event")),
        "target_field": clean((row or {}).get("target_field")),
        "field": field,
        "message": message,
    })


def source_candidates(ref: str, value_file: Path) -> list[Path]:
    path = Path(ref).expanduser()
    if path.is_absolute():
        return [path]
    return [
        ROOT / ref,
        value_file.parent / ref,
        ROOT / "data" / "nhi_pedot_h_a_vendor_return_inbox" / "external_lab_exports" / ref,
    ]


def resolve_existing_source(ref: str, value_file: Path) -> Path:
    for candidate in source_candidates(ref, value_file):
        if candidate.exists():
            return candidate
    return resolve_path(ref)


def validate_source_files(raw: str, value_file: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    refs = split_source_files(raw)
    if not refs:
        return ["source_file is required"]
    roots = allowed_roots(manifest)
    if not roots:
        return ["source manifest has no allowed roots"]
    for ref in refs:
        if has_rejected_marker(ref, manifest):
            errors.append(f"source_file `{ref}` contains a rejected marker")
            continue
        path = resolve_existing_source(ref, value_file)
        if not path.exists():
            errors.append(f"source_file `{ref}` does not exist")
            continue
        if not path.is_file():
            errors.append(f"source_file `{rel(path)}` is not a concrete file")
            continue
        if path.resolve() == value_file.resolve():
            errors.append("source_file cannot cite the source-value sidecar itself")
            continue
        if not any(path_is_within(path, root) for root in roots):
            errors.append(f"source_file `{rel(path)}` is outside allowed roots")
    return errors


def instrument_required(row: dict[str, str]) -> bool:
    raw = clean(row.get("instrument_required")).lower()
    if raw in {"true", "yes", "1"}:
        return True
    if raw in {"false", "no", "0"}:
        return False
    instrument_class = clean(row.get("instrument_class"))
    if instrument_class:
        return instrument_class not in RECORD_INSTRUMENT_CLASSES
    target = clean(row.get("target_field"))
    return target not in {"date", "medium_name", "medium_lot", "mea_coupon_id", "electrode_material", "laminin_or_peptide_density", "sterilization_or_aseptic_protocol"}


def discover_value_files(args: argparse.Namespace) -> list[Path]:
    files: list[Path] = []
    explicit = args.value_file or []
    for raw in explicit:
        path = raw.expanduser()
        files.append(path if path.is_absolute() else ROOT / path)
    if not explicit:
        if args.source_values.exists():
            files.append(args.source_values)
        for pattern in args.values_glob:
            files.extend(ROOT.glob(pattern))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return sorted(unique, key=lambda item: rel(item))


def read_value_rows(value_files: list[Path], issues: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value_file in value_files:
        if not value_file.exists():
            add_issue(issues, "error", value_file, 0, "value_file", "value file does not exist")
            continue
        fields, csv_rows = load_csv(value_file)
        missing = [field for field in ["run_id", "sample_event", "target_field", "value", "measured_at", "operator_or_agent", "source_file"] if field not in fields]
        if missing:
            add_issue(issues, "error", value_file, 0, "header", f"missing required columns: {', '.join(missing)}")
            continue
        for index, row in enumerate(csv_rows, start=2):
            if not any(clean(row.get(field)) for field in FILLABLE_VALUE_FIELDS):
                rows.append({"row": row, "value_file": value_file, "row_number": index, "blank": True})
                continue
            rows.append({"row": row, "value_file": value_file, "row_number": index, "blank": False})
    return rows


def validate_value_row(
    row: dict[str, str],
    value_file: Path,
    row_number: int,
    manifest: dict[str, Any],
    issues: list[dict[str, str]],
) -> bool:
    ok = True
    for field in ["run_id", "sample_event", "target_field", *USER_FIELDS]:
        if has_rejected_marker(clean(row.get(field)), manifest):
            add_issue(issues, "error", value_file, row_number, field, "field contains a rejected placeholder/synthetic/source marker", row)
            ok = False
    for field in ["value", "measured_at", "operator_or_agent"]:
        if not clean(row.get(field)):
            add_issue(issues, "error", value_file, row_number, field, f"{field} is required", row)
            ok = False
    if instrument_required(row) and not clean(row.get("instrument_id")):
        add_issue(issues, "error", value_file, row_number, "instrument_id", "instrument_id is required for this H-A row", row)
        ok = False
    for message in validate_source_files(clean(row.get("source_file")), value_file, manifest):
        add_issue(issues, "error", value_file, row_number, "source_file", message, row)
        ok = False
    return ok


def import_values(args: argparse.Namespace) -> dict[str, Any]:
    raw_fields, raw_rows = load_csv(args.raw)
    if "source_file" not in raw_fields:
        raw_fields = [*raw_fields, "source_file"]
    lookup = raw_lookup(raw_rows)
    manifest = load_json(args.source_manifest)
    value_files = discover_value_files(args)
    issues: list[dict[str, str]] = []
    value_records = read_value_rows(value_files, issues)
    imported_rows: list[dict[str, str]] = []
    blank_rows = 0
    unchanged_rows = 0

    for record in value_records:
        value_file = record["value_file"]
        row_number = record["row_number"]
        row = record["row"]
        if record.get("blank"):
            blank_rows += 1
            continue
        key = row_key(row)
        target = lookup.get(key)
        if target is None:
            add_issue(issues, "error", value_file, row_number, "row_locator", "row does not match the H-A raw template", row)
            continue
        if not validate_value_row(row, value_file, row_number, manifest, issues):
            continue
        changed = False
        for field in ["value", "unit", "measured_at", "operator_or_agent", "instrument_id", "source_file", "notes"]:
            new_value = clean(row.get(field))
            if field == "unit" and not new_value:
                continue
            if clean(target.get(field)) != new_value:
                target[field] = new_value
                changed = True
        if not changed:
            unchanged_rows += 1
        imported_rows.append({
            "run_id": key[0],
            "sample_event": key[1],
            "target_field": key[2],
            "value_file": rel(value_file),
            "row_number": str(row_number),
            "source_file": clean(row.get("source_file")),
            "changed": str(changed).lower(),
        })

    if imported_rows and raw_fields:
        write_csv(args.raw, raw_fields, raw_rows)

    counts = Counter(issue["severity"] for issue in issues)
    if not value_files:
        status = "h_a_source_value_import_no_value_files"
    elif counts.get("error", 0) and not imported_rows:
        status = "h_a_source_value_import_blocked"
    elif imported_rows and counts.get("error", 0):
        status = "h_a_source_value_import_updated_with_issues"
    elif imported_rows:
        status = "h_a_source_value_import_updated"
    else:
        status = "h_a_source_value_import_no_importable_rows"

    return {
        "status": status,
        "summary": {
            "source_value_files": len(value_files),
            "source_value_rows": len(value_records),
            "imported_rows": len(imported_rows),
            "changed_rows": sum(1 for row in imported_rows if row["changed"] == "true"),
            "unchanged_rows": unchanged_rows,
            "skipped_blank_rows": blank_rows,
            "error_count": counts.get("error", 0),
            "warning_count": counts.get("warning", 0),
        },
        "inputs": {"raw": rel(args.raw), "source_manifest": rel(args.source_manifest), "value_globs": list(args.values_glob)},
        "source_value_files": [rel(path) for path in value_files],
        "imported_rows": imported_rows,
        "issues": issues,
        "accepted_sidecar_schema": RAW_FIELDS,
        "boundary": (
            "This importer only copies source-file-backed H-A values into the formal raw template. "
            "It does not create evidence; merge, source-file validation, H-A QC, interpretation, and claim audit still control the gate."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A Source Value Import",
        "",
        "This imports source-backed H-A sidecar values into the formal raw template. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Source value files:** {summary['source_value_files']}",
        f"**Source value rows:** {summary['source_value_rows']}",
        f"**Imported rows:** {summary['imported_rows']}",
        f"**Changed rows:** {summary['changed_rows']}",
        f"**Errors:** {summary['error_count']}",
        f"**Warnings:** {summary['warning_count']}",
        "",
        "## Value Files",
        "",
    ]
    lines.extend(f"- `{path}`" for path in result["source_value_files"]) if result["source_value_files"] else lines.append("- No value files found.")
    lines.extend(["", "## Imported Rows", ""])
    if not result["imported_rows"]:
        lines.append("- No rows imported.")
    else:
        lines.extend(["| Run | Event | Field | Changed | Source file |", "| --- | --- | --- | --- | --- |"])
        for row in result["imported_rows"][:100]:
            lines.append(
                f"| `{row['run_id']}` | `{row['sample_event']}` | `{row['target_field']}` | "
                f"`{row['changed']}` | `{row['source_file']}` |"
            )
    lines.extend(["", "## Issues", ""])
    if not result["issues"]:
        lines.append("- No import issues.")
    else:
        lines.extend(["| Severity | File | Row | Run | Field | Message |", "| --- | --- | ---: | --- | --- | --- |"])
        for issue in result["issues"][:120]:
            lines.append(
                f"| `{issue['severity']}` | `{issue['value_file']}` | {issue['row_number']} | "
                f"`{issue['run_id']}` | `{issue['field']}` | {issue['message']} |"
            )
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import NHI-PEDOT H-A source-value sidecars.")
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--source-values", type=Path, default=DEFAULT_SOURCE_VALUES)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--value-file", type=Path, action="append")
    parser.add_argument("--values-glob", action="append", default=list(DEFAULT_VALUE_GLOBS))
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = import_values(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A source value import: {result['status']}")
    print(f"Source value files: {result['summary']['source_value_files']}")
    print(f"Imported rows: {result['summary']['imported_rows']}")
    print(f"Errors: {result['summary']['error_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
