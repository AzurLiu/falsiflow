#!/usr/bin/env python3
"""Apply filled ZRC-ND Phase A vendor bundle-entry rows into source values."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS
from render_limina_wide_source_values_sheet import clean, instrument_required, rel


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHEET = ROOT / "data" / "zrc_nd_phase_a_vendor_return_inbox" / "completed_bundle_entry_sheet.csv"
DEFAULT_SOURCE_VALUES = ROOT / "data" / "zrc_nd_phase_a_source_values.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_vendor_bundle_entry_apply.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_vendor_bundle_entry_apply.md"

SOURCE_SPLIT_CHARS = [";", "|", "\n"]
TRUTHY = {"true", "yes", "1", "y"}
BASE_REQUIRED_FIELDS = {
    "bundle_id",
    "apply",
    "source_file",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "run_id",
    "source_class",
    "target_value_columns",
}
SOURCE_REQUIRED_FIELDS = {"run_id", "target_field", "source_class", "instrument_required"}

BOUNDARY = (
    "This apply step only copies human-reviewed, source-file-backed ZRC-ND Phase A bundle values into the source-values sheet. "
    "The importer, merge, gates, readiness audit, and claim audit still decide whether anything is real material evidence."
)


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


def truthy(raw: str) -> bool:
    return clean(raw).lower() in TRUTHY


def split_refs(raw: str) -> list[str]:
    refs = [clean(raw).strip("\"'")]
    for char in SOURCE_SPLIT_CHARS:
        expanded: list[str] = []
        for ref in refs:
            expanded.extend(part.strip().strip("\"'") for part in ref.split(char))
        refs = expanded
    return [ref for ref in refs if ref]


def resolve_path(raw: str) -> Path:
    path = Path(clean(raw)).expanduser()
    return path if path.is_absolute() else ROOT / path


def source_candidates(ref: str, sheet_path: Path) -> list[Path]:
    path = Path(clean(ref)).expanduser()
    if path.is_absolute():
        return [path]
    return [ROOT / ref, sheet_path.parent / ref]


def resolve_existing_source(ref: str, sheet_path: Path) -> Path:
    for candidate in source_candidates(ref, sheet_path):
        if candidate.exists():
            return candidate
    return resolve_path(ref)


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


def rejected_markers(manifest: dict[str, Any]) -> set[str]:
    markers = {marker.lower() for marker in PLACEHOLDER_MARKERS}
    markers.update(marker.lower() for marker in SYNTHETIC_MARKERS)
    markers.update(clean(item).lower() for item in manifest.get("rejected_source_markers", []) if clean(item))
    return markers


def has_rejected_marker(raw: str, manifest: dict[str, Any]) -> bool:
    lowered = clean(raw).lower()
    return any(marker in lowered for marker in rejected_markers(manifest))


def validate_source_files(raw: str, sheet_path: Path, source_values: Path, manifest: dict[str, Any]) -> list[str]:
    refs = split_refs(raw)
    if not refs:
        return ["source_file is required"]
    roots = allowed_roots(manifest)
    if not roots:
        return ["source manifest has no allowed roots"]
    errors: list[str] = []
    for ref in refs:
        if has_rejected_marker(ref, manifest):
            errors.append(f"source_file `{ref}` contains a rejected marker")
            continue
        path = resolve_existing_source(ref, sheet_path)
        if not path.exists():
            errors.append(f"source_file `{ref}` does not exist")
            continue
        if not path.is_file():
            errors.append(f"source_file `{rel(path)}` is not a concrete file")
            continue
        if path.resolve() in {sheet_path.resolve(), source_values.resolve()}:
            errors.append("source_file cannot cite a source-value or bundle-entry sidecar")
            continue
        if not any(path_is_within(path, root) for root in roots):
            errors.append(f"source_file `{rel(path)}` is outside allowed roots")
    return errors


def source_groups(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        run_id = clean(row.get("run_id"))
        source_class = clean(row.get("source_class"))
        if run_id and source_class:
            groups[(run_id, source_class)].append(row)
    return groups


def add_issue(
    issues: list[dict[str, str]],
    severity: str,
    row: dict[str, str],
    field: str,
    message: str,
) -> None:
    issues.append({
        "severity": severity,
        "bundle_id": clean(row.get("bundle_id")),
        "run_id": clean(row.get("run_id")),
        "source_class": clean(row.get("source_class")),
        "field": field,
        "message": message,
    })


def value_column(target_field: str) -> str:
    return f"value_{target_field}"


def row_requires_instrument(rows: list[dict[str, str]], entry: dict[str, str]) -> bool:
    if truthy(entry.get("instrument_required", "")):
        return True
    return any(
        truthy(row.get("instrument_required", "")) or instrument_required(clean(row.get("target_field")))
        for row in rows
    )


def validate_entry(
    row: dict[str, str],
    source_rows: list[dict[str, str]],
    sheet_fields: list[str],
    sheet_path: Path,
    source_values: Path,
    manifest: dict[str, Any],
    issues: list[dict[str, str]],
) -> bool:
    ok = True
    for field in ["measured_at", "operator_or_agent", "instrument_id", "source_file", "notes", *sheet_fields]:
        if clean(row.get(field)) and has_rejected_marker(clean(row.get(field)), manifest):
            add_issue(issues, "error", row, field, "entry contains placeholder/synthetic/rejected marker")
            ok = False
    for field in ["measured_at", "operator_or_agent"]:
        if not clean(row.get(field)):
            add_issue(issues, "error", row, field, f"{field} is required")
            ok = False
    if row_requires_instrument(source_rows, row) and not clean(row.get("instrument_id")):
        add_issue(issues, "error", row, "instrument_id", "instrument_id is required for this bundle")
        ok = False
    for message in validate_source_files(clean(row.get("source_file")), sheet_path, source_values, manifest):
        add_issue(issues, "error", row, "source_file", message)
        ok = False
    seen_columns: set[str] = set()
    for source_row in source_rows:
        target_field = clean(source_row.get("target_field"))
        column = value_column(target_field)
        if column not in sheet_fields:
            add_issue(issues, "error", row, "target_value_columns", f"missing value column for {target_field}")
            ok = False
            continue
        seen_columns.add(column)
        if not clean(row.get(column)):
            add_issue(issues, "error", row, column, "value is required for this bundled source-value row")
            ok = False
        elif has_rejected_marker(clean(row.get(column)), manifest):
            add_issue(issues, "error", row, column, "value contains a rejected placeholder/synthetic marker")
            ok = False
    if not seen_columns:
        add_issue(issues, "error", row, "bundle_id", "bundle has no matching source-value rows")
        ok = False
    return ok


def apply_entries(args: argparse.Namespace) -> dict[str, Any]:
    sheet_fields, sheet_rows = load_csv(args.sheet)
    source_fields, source_rows = load_csv(args.source_values)
    manifest = load_json(args.source_manifest)
    groups = source_groups(source_rows)
    issues: list[dict[str, str]] = []
    applied_bundles: list[dict[str, str]] = []
    planned_updates: list[tuple[dict[str, str], dict[str, str], str]] = []
    skipped_apply_no = 0
    duplicate_bundle_ids: set[str] = set()
    seen_bundle_ids: set[str] = set()

    if not sheet_fields:
        add_issue(issues, "error", {"bundle_id": "-"}, "sheet", "bundle entry sheet is missing or empty")
    else:
        missing = sorted(BASE_REQUIRED_FIELDS - set(sheet_fields))
        if missing:
            add_issue(issues, "error", {"bundle_id": "-"}, "header", f"sheet missing columns: {', '.join(missing)}")
    missing_source = sorted(SOURCE_REQUIRED_FIELDS - set(source_fields))
    if missing_source:
        add_issue(issues, "error", {"bundle_id": "-"}, "header", f"source-values sheet missing columns: {', '.join(missing_source)}")

    value_columns = [field for field in sheet_fields if field.startswith("value_")]
    for entry in sheet_rows:
        if not truthy(entry.get("apply", "")):
            skipped_apply_no += 1
            continue
        bundle_id = clean(entry.get("bundle_id"))
        if bundle_id in seen_bundle_ids:
            duplicate_bundle_ids.add(bundle_id)
            add_issue(issues, "error", entry, "bundle_id", "duplicate apply row for bundle_id")
            continue
        seen_bundle_ids.add(bundle_id)
        run_id = clean(entry.get("run_id"))
        source_class = clean(entry.get("source_class"))
        matching_source_rows = groups.get((run_id, source_class), [])
        if not validate_entry(entry, matching_source_rows, value_columns, args.sheet, args.source_values, manifest, issues):
            continue
        for source_row in matching_source_rows:
            column = value_column(clean(source_row.get("target_field")))
            planned_updates.append((source_row, entry, column))
        applied_bundles.append({
            "bundle_id": bundle_id,
            "run_id": run_id,
            "source_class": source_class,
            "source_file": clean(entry.get("source_file")),
            "source_value_rows": str(len(matching_source_rows)),
        })

    counts = Counter(issue["severity"] for issue in issues)
    if planned_updates and not counts.get("error", 0):
        for source_row, entry, column in planned_updates:
            source_row["value"] = clean(entry.get(column))
            source_row["measured_at"] = clean(entry.get("measured_at"))
            source_row["operator_or_agent"] = clean(entry.get("operator_or_agent"))
            source_row["instrument_id"] = clean(entry.get("instrument_id"))
            source_row["source_file"] = clean(entry.get("source_file"))
            source_row["notes"] = clean(entry.get("notes"))
            source_row["source_file_exists"] = "true"
            source_row["review_status"] = "import_ready"
            source_row["missing_items"] = ""
        write_csv(args.source_values, source_fields, source_rows)

    applied_value_rows = len(planned_updates)
    if counts.get("error", 0):
        status = "zrc_phase_a_vendor_bundle_entry_apply_blocked"
    elif applied_value_rows:
        status = "zrc_phase_a_vendor_bundle_entry_apply_applied"
    else:
        status = "zrc_phase_a_vendor_bundle_entry_apply_no_apply_rows"
    return {
        "status": status,
        "summary": {
            "sheet_rows": len(sheet_rows),
            "apply_rows": len(seen_bundle_ids),
            "applied_bundles": 0 if counts.get("error", 0) else len(applied_bundles),
            "applied_source_value_rows": 0 if counts.get("error", 0) else applied_value_rows,
            "skipped_apply_no_rows": skipped_apply_no,
            "duplicate_apply_rows": len(duplicate_bundle_ids),
            "error_count": counts.get("error", 0),
            "warning_count": counts.get("warning", 0),
        },
        "inputs": {
            "sheet": rel(args.sheet),
            "source_values": rel(args.source_values),
            "source_manifest": rel(args.source_manifest),
        },
        "applied_bundles": [] if counts.get("error", 0) else applied_bundles,
        "issues": issues,
        "updated_source_values": rel(args.source_values) if planned_updates and not counts.get("error", 0) else "",
        "boundary": BOUNDARY,
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# ZRC-ND Phase A Vendor Bundle Entry Apply",
        "",
        "This applies filled vendor bundle-entry rows into the ZRC-ND Phase A source-values sheet. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Sheet rows:** {summary['sheet_rows']}",
        f"**Apply rows:** {summary['apply_rows']}",
        f"**Applied bundles:** {summary['applied_bundles']}",
        f"**Applied source-value rows:** {summary['applied_source_value_rows']}",
        f"**Skipped non-apply rows:** {summary['skipped_apply_no_rows']}",
        f"**Errors:** {summary['error_count']}",
        f"**Warnings:** {summary['warning_count']}",
        "",
        "## Applied Bundles",
        "",
    ]
    if not result["applied_bundles"]:
        lines.append("- No bundles applied.")
    else:
        lines.extend(["| Bundle | Run | Source class | Rows | Source file |", "| --- | --- | --- | ---: | --- |"])
        for row in result["applied_bundles"][:80]:
            lines.append(
                f"| `{row['bundle_id']}` | `{row['run_id']}` | `{row['source_class']}` | "
                f"{row['source_value_rows']} | `{row['source_file']}` |"
            )
    lines.extend(["", "## Issues", ""])
    if not result["issues"]:
        lines.append("- No apply issues.")
    else:
        lines.extend(["| Severity | Bundle | Run | Source class | Field | Message |", "| --- | --- | --- | --- | --- | --- |"])
        for issue in result["issues"][:100]:
            lines.append(
                f"| `{issue['severity']}` | `{issue['bundle_id']}` | `{issue['run_id']}` | "
                f"`{issue['source_class']}` | `{issue['field']}` | {issue['message']} |"
            )
        if len(result["issues"]) > 100:
            lines.append(f"| `info` | `-` | `-` | `-` | `-` | {len(result['issues']) - 100} additional issues omitted. |")
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply ZRC-ND Phase A vendor bundle-entry sheet.")
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--source-values", type=Path, default=DEFAULT_SOURCE_VALUES)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = apply_entries(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"ZRC-ND Phase A vendor bundle entry apply: {result['status']}")
    print(f"Applied bundles: {result['summary']['applied_bundles']}")
    print(f"Applied source-value rows: {result['summary']['applied_source_value_rows']}")
    print(f"Errors: {result['summary']['error_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["summary"]["error_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
