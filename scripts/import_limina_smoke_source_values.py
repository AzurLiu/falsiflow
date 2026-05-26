#!/usr/bin/env python3
"""Import LIMINA smoke source-value sidecars into the smoke entry sheet."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENTRY_SHEET = ROOT / "data" / "limina_smoke_entry_sheet.csv"
DEFAULT_SOURCE_DROP_PLAN = ROOT / "data" / "limina_smoke_source_drop_plan.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_CONSOLIDATED_VALUES = ROOT / "data" / "limina_smoke_source_values.csv"
DEFAULT_RAW_CSV_EXTRACTED_VALUES = ROOT / "data" / "limina_smoke_raw_csv_extracted_values.csv"
DEFAULT_UNSTRUCTURED_REVIEW_VALUES = ROOT / "data" / "limina_smoke_unstructured_review_values.csv"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_source_value_import.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_source_value_import.md"
DEFAULT_VALUE_GLOBS = [
    "data/source_files/smoke/h_a/**/limina_values.csv",
    "data/source_files/smoke/zrc_nd_phase_a/**/limina_values.csv",
]

USER_FIELDS = [
    "apply",
    "value",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "source_file",
    "notes",
]
FILLABLE_VALUE_FIELDS = [
    "value",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "notes",
    "apply",
]
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
SOURCE_SPLIT_CHARS = [";", "|", "\n"]


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


def lower_contains(raw: str, markers: set[str]) -> bool:
    lowered = raw.lower()
    return any(marker in lowered for marker in markers)


def rejected_markers(manifest: dict[str, Any]) -> set[str]:
    markers = set(PLACEHOLDER_MARKERS) | set(SYNTHETIC_MARKERS)
    markers.update(clean(item).lower() for item in manifest.get("rejected_source_markers", []) if clean(item))
    return markers


def has_rejected_marker(raw: str, manifest: dict[str, Any]) -> bool:
    return lower_contains(raw, rejected_markers(manifest))


def split_refs(raw: str) -> list[str]:
    refs = [clean(raw).strip("\"'")]
    for char in SOURCE_SPLIT_CHARS:
        expanded: list[str] = []
        for ref in refs:
            expanded.extend(part.strip().strip("\"'") for part in ref.split(char))
        refs = expanded
    return [ref for ref in refs if ref]


def resolve_path(raw: str) -> Path:
    path = Path(raw).expanduser()
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
        "queue_id": clean((row or {}).get("queue_id")),
        "run_id": clean((row or {}).get("run_id")),
        "sample_event": clean((row or {}).get("sample_event")),
        "target_field": clean((row or {}).get("target_field")),
        "field": field,
        "message": message,
    })


def validate_source_files(raw: str, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    refs = split_refs(raw)
    if not refs:
        return ["source_file is blank; each imported row must cite the raw export, report, image, or worksheet"]
    roots = allowed_roots(manifest)
    if not roots:
        return ["source manifest has no allowed roots"]
    for ref in refs:
        if has_rejected_marker(ref, manifest):
            errors.append(f"source_file `{ref}` contains a rejected marker")
            continue
        path = resolve_path(ref)
        if not path.exists():
            errors.append(f"source_file `{ref}` does not exist")
            continue
        if not path.is_file():
            errors.append(f"source_file `{rel(path)}` is not a concrete file")
            continue
        if not any(path_is_within(path, root) for root in roots):
            errors.append(f"source_file `{rel(path)}` is outside allowed roots")
    return errors


def discover_value_files(args: argparse.Namespace) -> list[Path]:
    discovered: list[Path] = []
    explicit = args.value_file or []
    for raw in explicit:
        path = raw.expanduser()
        if not path.is_absolute():
            path = ROOT / path
        discovered.append(path)
    if not explicit:
        if DEFAULT_CONSOLIDATED_VALUES.exists():
            discovered.append(DEFAULT_CONSOLIDATED_VALUES)
        if DEFAULT_RAW_CSV_EXTRACTED_VALUES.exists():
            discovered.append(DEFAULT_RAW_CSV_EXTRACTED_VALUES)
        if DEFAULT_UNSTRUCTURED_REVIEW_VALUES.exists():
            discovered.append(DEFAULT_UNSTRUCTURED_REVIEW_VALUES)
        for pattern in args.values_glob:
            discovered.extend(ROOT.glob(pattern))

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in discovered:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return sorted(unique, key=lambda item: rel(item))


def entry_lookup(rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], dict[tuple[str, str, str], list[dict[str, str]]]]:
    by_queue = {clean(row.get("queue_id")): row for row in rows if clean(row.get("queue_id"))}
    by_tuple: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (clean(row.get("run_id")), clean(row.get("sample_event")), clean(row.get("target_field")))
        if all(key):
            by_tuple.setdefault(key, []).append(row)
    return by_queue, by_tuple


def plan_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {clean(row.get("queue_id")): row for row in rows if clean(row.get("queue_id"))}


def locate_entry(
    value_row: dict[str, str],
    by_queue: dict[str, dict[str, str]],
    by_tuple: dict[tuple[str, str, str], list[dict[str, str]]],
    issues: list[dict[str, str]],
    value_file: Path,
    row_number: int,
) -> dict[str, str] | None:
    queue_id = clean(value_row.get("queue_id"))
    if queue_id:
        entry = by_queue.get(queue_id)
        if entry is None:
            add_issue(issues, "error", value_file, row_number, "queue_id", "queue_id is not present in the smoke entry sheet", value_row)
        return entry

    key = (clean(value_row.get("run_id")), clean(value_row.get("sample_event")), clean(value_row.get("target_field")))
    if not all(key):
        add_issue(
            issues,
            "error",
            value_file,
            row_number,
            "queue_id",
            "row needs queue_id or the complete run_id + sample_event + target_field locator",
            value_row,
        )
        return None
    matches = by_tuple.get(key, [])
    if not matches:
        add_issue(issues, "error", value_file, row_number, "row_locator", "locator does not match any smoke entry-sheet row", value_row)
        return None
    if len(matches) > 1:
        add_issue(issues, "error", value_file, row_number, "row_locator", "locator is ambiguous; use queue_id", value_row)
        return None
    return matches[0]


def validate_value_row(
    value_row: dict[str, str],
    entry: dict[str, str],
    planned: dict[str, str] | None,
    manifest: dict[str, Any],
    value_file: Path,
    row_number: int,
    issues: list[dict[str, str]],
) -> bool:
    ok = True
    for field in ["queue_id", "run_id", "sample_event", "target_field", *USER_FIELDS]:
        if has_rejected_marker(clean(value_row.get(field)), manifest):
            add_issue(issues, "error", value_file, row_number, field, "import row contains a rejected placeholder/synthetic/source marker", value_row)
            ok = False
    if not clean(value_row.get("value")):
        add_issue(issues, "error", value_file, row_number, "value", "value is required", value_row)
        ok = False
    for field in ["measured_at", "operator_or_agent"]:
        if not clean(value_row.get(field)):
            add_issue(issues, "error", value_file, row_number, field, f"{field} is required", value_row)
            ok = False
    if clean(entry.get("route")) != "supplier_or_build_record" and clean(entry.get("instrument_class")) not in {"record_review", "bench_or_vendor_record"}:
        if not clean(value_row.get("instrument_id")):
            add_issue(issues, "error", value_file, row_number, "instrument_id", "instrument_id is required for measured rows", value_row)
            ok = False

    source_file = clean(value_row.get("source_file"))
    for message in validate_source_files(source_file, manifest):
        add_issue(issues, "error", value_file, row_number, "source_file", message, value_row)
        ok = False
    for ref in split_refs(source_file):
        source_path = resolve_path(ref)
        if source_path.exists() and source_path.resolve() == value_file.resolve():
            add_issue(
                issues,
                "error",
                value_file,
                row_number,
                "source_file",
                "source_file cannot cite the source-value sidecar itself; cite the raw export, report, image, or worksheet",
                value_row,
            )
            ok = False

    if planned and source_file:
        planned_dir = clean(planned.get("source_dir"))
        if planned_dir:
            source_paths = [resolve_path(ref) for ref in split_refs(source_file)]
            planned_path = resolve_path(planned_dir)
            if source_paths and not any(path_is_within(path, planned_path) for path in source_paths if path.exists()):
                add_issue(
                    issues,
                    "warning",
                    value_file,
                    row_number,
                    "source_file",
                    f"source_file is valid but not inside the planned row drop directory `{planned_dir}`",
                    value_row,
                )
    return ok


def read_value_rows(value_files: list[Path], issues: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value_file in value_files:
        if not value_file.exists():
            add_issue(issues, "error", value_file, 0, "value_file", "value file does not exist")
            continue
        fields, csv_rows = load_csv(value_file)
        missing = [field for field in ["value", "measured_at", "operator_or_agent", "source_file"] if field not in fields]
        has_locator = "queue_id" in fields or all(field in fields for field in ["run_id", "sample_event", "target_field"])
        if missing or not has_locator:
            if missing:
                add_issue(issues, "error", value_file, 0, "header", f"missing required columns: {', '.join(missing)}")
            if not has_locator:
                add_issue(issues, "error", value_file, 0, "header", "missing queue_id or run_id + sample_event + target_field locator columns")
            continue
        for index, row in enumerate(csv_rows, start=2):
            if not any(clean(row.get(field)) for field in VALUE_FIELDS):
                rows.append({"row": row, "value_file": value_file, "row_number": index, "blank": True})
                continue
            if not any(clean(row.get(field)) for field in FILLABLE_VALUE_FIELDS):
                rows.append({"row": row, "value_file": value_file, "row_number": index, "blank": True})
                continue
            rows.append({"row": row, "value_file": value_file, "row_number": index, "blank": False})
    return rows


def apply_value(entry: dict[str, str], value_row: dict[str, str]) -> bool:
    changed = False
    updates = {
        "apply": clean(value_row.get("apply")) or clean(entry.get("apply")) or "yes",
        "value": clean(value_row.get("value")),
        "measured_at": clean(value_row.get("measured_at")),
        "operator_or_agent": clean(value_row.get("operator_or_agent")),
        "instrument_id": clean(value_row.get("instrument_id")),
        "source_file": clean(value_row.get("source_file")),
        "notes": clean(value_row.get("notes")),
    }
    for field, value in updates.items():
        if clean(entry.get(field)) != value:
            entry[field] = value
            changed = True
    return changed


def import_values(args: argparse.Namespace) -> dict[str, Any]:
    entry_fields, entry_rows = load_csv(args.entry_sheet)
    _plan_fields, plan_rows = load_csv(args.source_drop_plan)
    manifest = load_json(args.source_manifest)
    value_files = discover_value_files(args)
    issues: list[dict[str, str]] = []
    imported_rows: list[dict[str, str]] = []
    blank_rows = 0
    unchanged_rows = 0

    if not entry_rows:
        add_issue(issues, "error", args.entry_sheet, 0, "entry_sheet", "smoke entry sheet has no rows")
    if not entry_fields:
        add_issue(issues, "error", args.entry_sheet, 0, "entry_sheet", "smoke entry sheet is missing")

    by_queue, by_tuple = entry_lookup(entry_rows)
    plans = plan_lookup(plan_rows)
    value_records = read_value_rows(value_files, issues)

    for record in value_records:
        value_file = record["value_file"]
        row_number = record["row_number"]
        value_row = record["row"]
        if record.get("blank"):
            blank_rows += 1
            continue
        entry = locate_entry(value_row, by_queue, by_tuple, issues, value_file, row_number)
        if entry is None:
            continue
        queue_id = clean(entry.get("queue_id"))
        planned = plans.get(queue_id)
        if not validate_value_row(value_row, entry, planned, manifest, value_file, row_number, issues):
            continue
        changed = apply_value(entry, value_row)
        if not changed:
            unchanged_rows += 1
        imported_rows.append({
            "queue_id": queue_id,
            "run_id": clean(entry.get("run_id")),
            "sample_event": clean(entry.get("sample_event")),
            "target_field": clean(entry.get("target_field")),
            "value_file": rel(value_file),
            "row_number": str(row_number),
            "source_file": clean(value_row.get("source_file")),
            "changed": str(changed).lower(),
        })

    if imported_rows and entry_fields:
        write_csv(args.entry_sheet, entry_fields, entry_rows)

    counts = Counter(issue["severity"] for issue in issues)
    if not value_files:
        status = "smoke_source_value_import_no_value_files"
    elif counts.get("error", 0) and not imported_rows:
        status = "smoke_source_value_import_blocked"
    elif imported_rows and counts.get("error", 0):
        status = "smoke_source_value_import_updated_with_issues"
    elif imported_rows:
        status = "smoke_source_value_import_updated"
    else:
        status = "smoke_source_value_import_no_importable_rows"

    return {
        "status": status,
        "summary": {
            "source_value_files": len(value_files),
            "source_value_rows": len(value_records),
            "imported_rows": len(imported_rows),
            "changed_rows": sum(1 for row in imported_rows if row["changed"] == "true"),
            "unchanged_rows": unchanged_rows,
            "skipped_blank_rows": blank_rows,
            "invalid_rows": counts.get("error", 0),
            "error_count": counts.get("error", 0),
            "warning_count": counts.get("warning", 0),
        },
        "inputs": {
            "entry_sheet": rel(args.entry_sheet),
            "source_drop_plan": rel(args.source_drop_plan),
            "source_manifest": rel(args.source_manifest),
            "value_globs": list(args.values_glob),
        },
        "source_value_files": [rel(path) for path in value_files],
        "imported_rows": imported_rows,
        "issues": issues,
        "accepted_sidecar_schema": VALUE_FIELDS,
        "boundary": (
            "This importer only copies real, source-file-backed values into the smoke entry sheet. "
            "It does not create measured evidence; apply, preflight, merge, QC, and claim audit still control the gate."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Source Value Import",
        "",
        "This report imports source-value sidecars into the smoke entry sheet. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Source value files:** {summary['source_value_files']}",
        f"**Source value rows:** {summary['source_value_rows']}",
        f"**Imported rows:** {summary['imported_rows']}",
        f"**Changed rows:** {summary['changed_rows']}",
        f"**Errors:** {summary['error_count']}",
        f"**Warnings:** {summary['warning_count']}",
        "",
        "## Accepted Sidecar Columns",
        "",
        "`queue_id` is preferred. Alternatively use `run_id`, `sample_event`, and `target_field` together.",
        "",
        "```text",
        ",".join(result["accepted_sidecar_schema"]),
        "```",
        "",
        "## Value Files",
        "",
    ]
    if result["source_value_files"]:
        lines.extend(f"- `{path}`" for path in result["source_value_files"])
    else:
        lines.append("- No source value files found.")

    lines.extend(["", "## Imported Rows", ""])
    if not result["imported_rows"]:
        lines.append("- No rows imported.")
    else:
        lines.extend(["| Queue | Run | Field | Changed | Source file |", "| --- | --- | --- | --- | --- |"])
        for row in result["imported_rows"][:100]:
            lines.append(
                f"| `{row['queue_id']}` | `{row['run_id']}` | `{row['target_field']}` | "
                f"`{row['changed']}` | `{row['source_file']}` |"
            )
        if len(result["imported_rows"]) > 100:
            lines.append(f"| `-` | `-` | `-` | `-` | {len(result['imported_rows']) - 100} additional rows omitted. |")

    lines.extend(["", "## Issues", ""])
    if not result["issues"]:
        lines.append("- No import issues.")
    else:
        lines.extend(["| Severity | File | Row | Queue | Field | Message |", "| --- | --- | ---: | --- | --- | --- |"])
        for issue in result["issues"][:120]:
            lines.append(
                f"| `{issue['severity']}` | `{issue['value_file']}` | {issue['row_number']} | "
                f"`{issue['queue_id']}` | `{issue['field']}` | {issue['message']} |"
            )
        if len(result["issues"]) > 120:
            lines.append(f"| `info` | `-` | 0 | `-` | `-` | {len(result['issues']) - 120} additional issues omitted. |")

    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import LIMINA smoke source-value sidecars.")
    parser.add_argument("--entry-sheet", type=Path, default=DEFAULT_ENTRY_SHEET)
    parser.add_argument("--source-drop-plan", type=Path, default=DEFAULT_SOURCE_DROP_PLAN)
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
    print(f"Smoke source value import: {result['status']}")
    print(f"Source value files: {result['summary']['source_value_files']}")
    print(f"Imported rows: {result['summary']['imported_rows']}")
    print(f"Errors: {result['summary']['error_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
