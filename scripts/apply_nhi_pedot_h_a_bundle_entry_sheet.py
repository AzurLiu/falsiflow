#!/usr/bin/env python3
"""Apply filled NHI-PEDOT H-A bundle entry rows into the H-A source-values sheet."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHEET = ROOT / "data" / "nhi_pedot_h_a_bundle_entry_sheet.csv"
DEFAULT_BUNDLE_MANIFEST = ROOT / "data" / "nhi_pedot_h_a_source_unlock_bundle_manifest.csv"
DEFAULT_SOURCE_VALUES = ROOT / "data" / "nhi_pedot_h_a_source_values.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_bundle_entry_apply.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_bundle_entry_apply.md"

VALUE_FIELDS = [
    "date",
    "medium_lot",
    "medium_name",
    "temperature_c",
    "mea_coupon_id",
    "electrode_material",
    "laminin_or_peptide_density",
    "sterilization_or_aseptic_protocol",
    "pH_initial",
    "pH_final",
    "osmolality_initial_mOsm_kg",
    "osmolality_final_mOsm_kg",
    "conductivity_initial_mS_cm",
    "conductivity_final_mS_cm",
    "visible_precipitate",
    "visible_shedding",
    "swelling_fraction",
    "delamination_score",
    "optical_transparency_fraction",
]
VALUE_COLUMNS = [f"value_{field}" for field in VALUE_FIELDS]
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


def truthy(raw: str) -> bool:
    return clean(raw).lower() in {"true", "yes", "1", "y"}


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
    errors: list[str] = []
    refs = split_refs(raw)
    if not refs:
        return ["source_file is required"]
    roots = allowed_roots(manifest)
    if not roots:
        return ["source manifest has no allowed roots"]
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


def bundle_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {clean(row.get("bundle_id")): row for row in rows if clean(row.get("bundle_id"))}


def source_groups(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        run_id = clean(row.get("run_id"))
        source_class = clean(row.get("source_class"))
        if run_id and source_class:
            groups[(run_id, source_class)].append(row)
    return groups


def source_value_key(row: dict[str, str]) -> str:
    return clean(row.get("wide_field")) or clean(row.get("target_field"))


def source_value_column(row: dict[str, str]) -> str:
    key = source_value_key(row)
    return f"value_{key}" if key else ""


def row_requires_instrument(rows: list[dict[str, str]], bundle: dict[str, str]) -> bool:
    if truthy(bundle.get("instrument_required", "")):
        return True
    return any(truthy(row.get("instrument_required", "")) for row in rows)


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


def validate_entry(
    row: dict[str, str],
    bundle: dict[str, str],
    source_rows: list[dict[str, str]],
    sheet_path: Path,
    source_values: Path,
    manifest: dict[str, Any],
    issues: list[dict[str, str]],
) -> bool:
    ok = True
    for field in ["measured_at", "operator_or_agent", "instrument_id", "source_file", "notes", *VALUE_COLUMNS]:
        if clean(row.get(field)) and has_rejected_marker(clean(row.get(field)), manifest):
            add_issue(issues, "error", row, field, "entry contains placeholder/synthetic/rejected marker")
            ok = False
    for field in ["measured_at", "operator_or_agent"]:
        if not clean(row.get(field)):
            add_issue(issues, "error", row, field, f"{field} is required")
            ok = False
    if row_requires_instrument(source_rows, bundle) and not clean(row.get("instrument_id")):
        add_issue(issues, "error", row, "instrument_id", "instrument_id is required for this bundle")
        ok = False
    for message in validate_source_files(clean(row.get("source_file")), sheet_path, source_values, manifest):
        add_issue(issues, "error", row, "source_file", message)
        ok = False
    seen_columns: set[str] = set()
    for source_row in source_rows:
        column = source_value_column(source_row)
        if column not in VALUE_COLUMNS:
            add_issue(issues, "error", row, "target_value_columns", f"missing supported value column for {source_value_key(source_row)}")
            ok = False
            continue
        seen_columns.add(column)
        if not clean(row.get(column)):
            add_issue(issues, "error", row, column, "value is required for this bundled source-value row")
            ok = False
    if not seen_columns:
        add_issue(issues, "error", row, "bundle_id", "bundle has no matching source-value rows")
        ok = False
    return ok


def apply_entries(args: argparse.Namespace) -> dict[str, Any]:
    sheet_fields, sheet_rows = load_csv(args.sheet)
    bundle_fields, bundle_rows = load_csv(args.bundle_manifest)
    source_fields, source_rows = load_csv(args.source_values)
    manifest = load_json(args.source_manifest)
    bundles = bundle_lookup(bundle_rows)
    groups = source_groups(source_rows)
    issues: list[dict[str, str]] = []
    applied_bundles: list[dict[str, str]] = []
    applied_value_rows = 0
    skipped_apply_no = 0
    duplicate_bundle_ids: set[str] = set()
    seen_bundle_ids: set[str] = set()
    required_sheet_fields = {"bundle_id", "apply", "source_file", "measured_at", "operator_or_agent", "instrument_id", *VALUE_COLUMNS}
    required_source_fields = {"run_id", "sample_event", "target_field", "source_class", "wide_field"}

    if not sheet_fields:
        add_issue(issues, "error", {"bundle_id": "-"}, "sheet", "bundle entry sheet is missing or empty")
    else:
        missing = sorted(required_sheet_fields - set(sheet_fields))
        if missing:
            add_issue(issues, "error", {"bundle_id": "-"}, "header", f"sheet missing columns: {', '.join(missing)}")
    missing_bundle = sorted({"bundle_id", "run_id", "source_class", "instrument_required"} - set(bundle_fields))
    if missing_bundle:
        add_issue(issues, "error", {"bundle_id": "-"}, "header", f"bundle manifest missing columns: {', '.join(missing_bundle)}")
    missing_source = sorted(required_source_fields - set(source_fields))
    if missing_source:
        add_issue(issues, "error", {"bundle_id": "-"}, "header", f"source-values sheet missing columns: {', '.join(missing_source)}")

    planned_updates: list[tuple[dict[str, str], dict[str, str], str]] = []
    for entry in sheet_rows:
        bundle_id = clean(entry.get("bundle_id"))
        if not truthy(entry.get("apply", "")):
            skipped_apply_no += 1
            continue
        if bundle_id in seen_bundle_ids:
            duplicate_bundle_ids.add(bundle_id)
            add_issue(issues, "error", entry, "bundle_id", "duplicate apply row for bundle_id")
            continue
        seen_bundle_ids.add(bundle_id)
        bundle = bundles.get(bundle_id)
        if bundle is None:
            add_issue(issues, "error", entry, "bundle_id", "bundle_id is not present in the unlock manifest")
            continue
        merged = {**bundle, **entry}
        source_class = clean(bundle.get("source_class"))
        run_id = clean(bundle.get("run_id"))
        matching_source_rows = groups.get((run_id, source_class), [])
        if not validate_entry(merged, bundle, matching_source_rows, args.sheet, args.source_values, manifest, issues):
            continue
        for source_row in matching_source_rows:
            column = source_value_column(source_row)
            planned_updates.append((source_row, merged, column))
        applied_bundles.append({
            "bundle_id": bundle_id,
            "run_id": run_id,
            "source_class": source_class,
            "source_file": clean(merged.get("source_file")),
            "source_value_rows": str(len(matching_source_rows)),
        })
        applied_value_rows += len(matching_source_rows)

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

    if counts.get("error", 0):
        status = "h_a_bundle_entry_apply_blocked"
    elif applied_value_rows:
        status = "h_a_bundle_entry_apply_applied"
    else:
        status = "h_a_bundle_entry_apply_no_apply_rows"
    return {
        "status": status,
        "summary": {
            "sheet_rows": len(sheet_rows),
            "applied_bundles": 0 if counts.get("error", 0) else len(applied_bundles),
            "applied_source_value_rows": 0 if counts.get("error", 0) else applied_value_rows,
            "skipped_apply_no_rows": skipped_apply_no,
            "duplicate_apply_rows": len(duplicate_bundle_ids),
            "error_count": counts.get("error", 0),
            "warning_count": counts.get("warning", 0),
        },
        "inputs": {
            "sheet": rel(args.sheet),
            "bundle_manifest": rel(args.bundle_manifest),
            "source_values": rel(args.source_values),
            "source_manifest": rel(args.source_manifest),
        },
        "applied_bundles": [] if counts.get("error", 0) else applied_bundles,
        "issues": issues,
        "updated_source_values": rel(args.source_values) if planned_updates and not counts.get("error", 0) else "",
        "boundary": (
            "This apply step only copies user-entered, source-file-backed bundle values into the H-A source-values sheet. "
            "The importer, merge, QC, gates, and claim audit still decide whether anything is real evidence."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A Bundle Entry Apply",
        "",
        "This applies filled bundle-entry rows into the H-A source-values sheet. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
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
    parser = argparse.ArgumentParser(description="Apply NHI-PEDOT H-A bundle entry sheet.")
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--bundle-manifest", type=Path, default=DEFAULT_BUNDLE_MANIFEST)
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
    print(f"H-A bundle entry apply: {result['status']}")
    print(f"Applied bundles: {result['summary']['applied_bundles']}")
    print(f"Applied source-value rows: {result['summary']['applied_source_value_rows']}")
    print(f"Errors: {result['summary']['error_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["summary"]["error_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
