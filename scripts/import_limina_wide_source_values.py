#!/usr/bin/env python3
"""Import validated wide source-value sidecars into evaluator run CSVs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS
from render_limina_wide_source_values_sheet import PROFILES, clean, instrument_required, rel


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
USER_FIELDS = ["value", "measured_at", "operator_or_agent", "instrument_id", "source_file", "notes"]
FILLABLE_VALUE_FIELDS = ["value", "measured_at", "operator_or_agent", "instrument_id", "notes"]
SOURCE_SPLIT_CHARS = [";", "|", "\n"]


def default_raw_csv_extracted_values(profile: str) -> Path:
    config = PROFILES[profile]
    return config["csv"].with_name(config["csv"].stem.replace("_source_values", "_raw_csv_extracted_values") + ".csv")


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
        "target_field": clean((row or {}).get("target_field")),
        "field": field,
        "message": message,
    })


def source_candidates(ref: str, value_file: Path) -> list[Path]:
    path = Path(ref).expanduser()
    if path.is_absolute():
        return [path]
    return [ROOT / ref, value_file.parent / ref]


def resolve_existing_source(ref: str, value_file: Path) -> Path:
    for candidate in source_candidates(ref, value_file):
        if candidate.exists():
            return candidate
    return resolve_path(ref)


def validate_source_files(raw: str, value_file: Path, manifest: dict[str, Any]) -> list[str]:
    refs = split_source_files(raw)
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


def parse_measured_date(raw: str) -> str:
    value = clean(raw)
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return value[:10] if len(value) >= 10 else value


def append_unique(existing_raw: str, new_raw: str) -> str:
    existing = split_source_files(existing_raw)
    for ref in split_source_files(new_raw):
        if ref not in existing:
            existing.append(ref)
    return ";".join(existing)


def discover_value_files(args: argparse.Namespace) -> list[Path]:
    files: list[Path] = []
    explicit = args.value_file or []
    config = PROFILES[args.profile]
    if explicit:
        files.extend(path if path.is_absolute() else ROOT / path for path in explicit)
    else:
        files.append(args.source_values or config["csv"])
        if args.source_values is None:
            extracted_values = default_raw_csv_extracted_values(args.profile)
            if extracted_values.exists():
                files.append(extracted_values)
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return sorted(unique, key=rel)


def row_key(row: dict[str, str]) -> str:
    return clean(row.get("run_id"))


def plan_lookup(path: Path) -> dict[str, dict[str, str]]:
    _fields, rows = load_csv(path)
    return {row_key(row): row for row in rows if row_key(row)}


def read_value_rows(value_files: list[Path], issues: list[dict[str, str]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for value_file in value_files:
        if not value_file.exists():
            add_issue(issues, "error", value_file, 0, "value_file", "value file does not exist")
            continue
        fields, rows = load_csv(value_file)
        missing = [
            field
            for field in ["run_id", "target_field", "value", "measured_at", "operator_or_agent", "source_file"]
            if field not in fields
        ]
        if missing:
            add_issue(issues, "error", value_file, 0, "header", f"missing required columns: {', '.join(missing)}")
            continue
        for index, row in enumerate(rows, start=2):
            blank = not any(clean(row.get(field)) for field in FILLABLE_VALUE_FIELDS)
            records.append({"row": row, "value_file": value_file, "row_number": index, "blank": blank})
    return records


def validate_value_row(
    row: dict[str, str],
    value_file: Path,
    row_number: int,
    manifest: dict[str, Any],
    fields: list[str],
    issues: list[dict[str, str]],
) -> bool:
    ok = True
    target_field = clean(row.get("target_field"))
    if target_field not in fields:
        add_issue(issues, "error", value_file, row_number, "target_field", "target_field is not in target wide CSV", row)
        ok = False
    for field in ["run_id", "target_field", *USER_FIELDS]:
        if has_rejected_marker(clean(row.get(field)), manifest):
            add_issue(issues, "error", value_file, row_number, field, "field contains a rejected placeholder/synthetic/source marker", row)
            ok = False
    for field in ["value", "measured_at", "operator_or_agent"]:
        if not clean(row.get(field)):
            add_issue(issues, "error", value_file, row_number, field, f"{field} is required", row)
            ok = False
    if instrument_required(target_field) and not clean(row.get("instrument_id")):
        add_issue(issues, "error", value_file, row_number, "instrument_id", "instrument_id is required for this row", row)
        ok = False
    for message in validate_source_files(clean(row.get("source_file")), value_file, manifest):
        add_issue(issues, "error", value_file, row_number, "source_file", message, row)
        ok = False
    return ok


def import_values(args: argparse.Namespace) -> dict[str, Any]:
    config = PROFILES[args.profile]
    target_path = args.target or config["target"]
    plan_path = args.plan or config["plan"]
    fields, target_rows = load_csv(target_path)
    plan_fields, plan_rows = load_csv(plan_path)
    if not fields:
        fields = list(plan_fields)
    plan = {row_key(row): row for row in plan_rows if row_key(row)}
    if "source_file" not in fields:
        fields = [*fields, "source_file"]
    target_by_run = {row_key(row): row for row in target_rows if row_key(row)}
    manifest = load_json(args.source_manifest)
    issues: list[dict[str, str]] = []
    value_files = discover_value_files(args)
    value_records = read_value_rows(value_files, issues)
    imported_rows: list[dict[str, str]] = []
    blank_rows = 0
    unchanged_rows = 0

    for record in value_records:
        value_file = record["value_file"]
        row_number = record["row_number"]
        row = record["row"]
        if record["blank"]:
            blank_rows += 1
            continue
        run_id = clean(row.get("run_id"))
        planned = plan.get(run_id)
        if planned is None:
            add_issue(issues, "error", value_file, row_number, "run_id", "run_id does not match the planned run table", row)
            continue
        if not validate_value_row(row, value_file, row_number, manifest, fields, issues):
            continue
        target = target_by_run.get(run_id)
        if target is None:
            target = {field: clean(planned.get(field)) for field in fields}
            target_by_run[run_id] = target
            target_rows.append(target)
        target_field = clean(row.get("target_field"))
        value = clean(row.get("value"))
        changed = clean(target.get(target_field)) != value
        target[target_field] = value
        if target_field == "date" or not clean(target.get("date")):
            target["date"] = value if target_field == "date" else parse_measured_date(clean(row.get("measured_at")))
        if target_field == "operator_or_agent":
            target["operator_or_agent"] = value
        elif clean(row.get("operator_or_agent")):
            target["operator_or_agent"] = clean(row.get("operator_or_agent"))
        target["source_file"] = append_unique(clean(target.get("source_file")), clean(row.get("source_file")))
        note = clean(row.get("notes"))
        if note:
            target["notes"] = ";".join(part for part in [clean(target.get("notes")), note] if part)
        if changed:
            imported_rows.append({
                "run_id": run_id,
                "target_field": target_field,
                "value_file": rel(value_file),
                "row_number": str(row_number),
                "source_file": clean(row.get("source_file")),
                "changed": "true",
            })
        else:
            unchanged_rows += 1
            imported_rows.append({
                "run_id": run_id,
                "target_field": target_field,
                "value_file": rel(value_file),
                "row_number": str(row_number),
                "source_file": clean(row.get("source_file")),
                "changed": "false",
            })

    if imported_rows:
        write_csv(target_path, fields, target_rows)

    counts = Counter(issue["severity"] for issue in issues)
    status_prefix = config["status_prefix"].replace("_source_values", "_source_value_import")
    if not value_files:
        status = f"{status_prefix}_no_value_files"
    elif counts.get("error", 0):
        status = f"{status_prefix}_blocked_by_errors"
    elif imported_rows:
        status = f"{status_prefix}_imported"
    else:
        status = f"{status_prefix}_no_importable_rows"
    return {
        "status": status,
        "profile": args.profile,
        "summary": {
            "source_value_files": len(value_files),
            "source_value_rows": len(value_records),
            "blank_rows": blank_rows,
            "imported_rows": len(imported_rows),
            "unchanged_rows": unchanged_rows,
            "error_count": counts.get("error", 0),
            "warning_count": counts.get("warning", 0),
        },
        "inputs": {"target": rel(target_path), "plan": rel(plan_path), "source_manifest": rel(args.source_manifest)},
        "value_files": [rel(path) for path in value_files],
        "imported_rows": imported_rows,
        "issues": issues,
        "boundary": "This importer only moves source-file-backed values into evaluator CSVs; it does not create measured evidence.",
    }


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        f"# {PROFILES[result['profile']]['label']} Source Value Import",
        "",
        "This imports validated source-value rows into a wide evaluator CSV. It is not measured evidence by itself.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Source value files:** {summary['source_value_files']}",
        f"**Rows:** {summary['source_value_rows']}",
        f"**Imported rows:** {summary['imported_rows']}",
        f"**Errors:** {summary['error_count']}",
        "",
    ]
    if result["issues"]:
        lines.extend([
            "## Issues",
            "",
            "| Severity | File | Row | Run | Field | Message |",
            "| --- | --- | ---: | --- | --- | --- |",
        ])
        for issue in result["issues"][:80]:
            lines.append(
                f"| `{issue['severity']}` | `{issue['value_file']}` | {issue['row_number']} | "
                f"`{issue['run_id'] or '-'}` | `{issue['field']}` | {md_cell(issue['message'])} |"
            )
        omitted = len(result["issues"]) - 80
        if omitted > 0:
            lines.append(f"| `info` | `-` | 0 | `-` | `-` | {omitted} additional issues omitted. |")
        lines.append("")
    lines.extend([
        "## Boundary",
        "",
        result["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import wide source-values into evaluator run CSVs.")
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--source-values", type=Path)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--value-file", type=Path, action="append")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--report", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = PROFILES[args.profile]
    args.json_out = args.json_out or Path(str(config["json"]).replace("_sheet.json", "_import.json"))
    args.report = args.report or Path(str(config["report"]).replace("_sheet.md", "_import.md"))
    result = import_values(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"{PROFILES[args.profile]['label']} source value import: {result['status']}")
    print(f"Source value files: {result['summary']['source_value_files']}")
    print(f"Imported rows: {result['summary']['imported_rows']}")
    print(f"Errors: {result['summary']['error_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["summary"]["error_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
