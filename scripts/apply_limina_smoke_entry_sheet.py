#!/usr/bin/env python3
"""Apply filled LIMINA smoke entry-sheet rows into smoke capture templates."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHEET = ROOT / "data" / "limina_smoke_entry_sheet.csv"
DEFAULT_QUEUE = ROOT / "data" / "limina_smoke_execution_queue.json"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_H_A_LOCAL = ROOT / "data" / "nhi_pedot_h_a_smoke_local_capture_template.csv"
DEFAULT_H_A_OUTSOURCE = ROOT / "data" / "nhi_pedot_h_a_smoke_osmolality_outsource_template.csv"
DEFAULT_ZRC_LOCAL = ROOT / "data" / "zrc_nd_phase_a_smoke_local_capture_template.csv"
DEFAULT_ZRC_OUTSOURCE = ROOT / "data" / "zrc_nd_phase_a_smoke_osmolality_outsource_template.csv"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_entry_apply.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_entry_apply.md"

H_A_BRANCH = "NHI-PEDOT H-A"
RECORD_INSTRUMENT_CLASSES = {"record_review", "bench_or_vendor_record"}
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


def has_placeholder_or_synthetic(raw: str) -> bool:
    return lower_contains(raw, set(PLACEHOLDER_MARKERS)) or lower_contains(raw, set(SYNTHETIC_MARKERS))


def split_refs(raw: str) -> list[str]:
    refs = [clean(raw).strip("\"'")]
    for char in SOURCE_SPLIT_CHARS:
        expanded = []
        for ref in refs:
            expanded.extend(part.strip().strip("\"'") for part in ref.split(char))
        refs = expanded
    return [ref for ref in refs if ref]


def resolve_source_path(raw: str) -> Path:
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


def source_files_valid(raw: str, manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    refs = split_refs(raw)
    if not refs:
        return False, ["source_file is blank"]
    roots = allowed_roots(manifest)
    if not roots:
        return False, ["source manifest has no allowed roots"]
    for ref in refs:
        if has_placeholder_or_synthetic(ref):
            errors.append(f"source_file `{ref}` contains placeholder/synthetic marker")
            continue
        path = resolve_source_path(ref)
        if not path.exists():
            errors.append(f"source_file `{ref}` does not exist")
            continue
        if not path.is_file():
            errors.append(f"source_file `{rel(path)}` is not a concrete file")
            continue
        if not any(path_is_within(path, root) for root in roots):
            errors.append(f"source_file `{rel(path)}` is outside allowed roots")
    return not errors, errors


def append_unique(existing: str, value: str) -> str:
    parts = split_refs(existing)
    for ref in split_refs(value):
        if ref not in parts:
            parts.append(ref)
    return ";".join(parts)


def h_a_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (clean(row.get("run_id")), clean(row.get("sample_event")), clean(row.get("target_field")))


def queue_by_id(queue_doc: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {clean(row.get("queue_id")): row for row in queue_doc.get("queue", []) if clean(row.get("queue_id"))}


def requires_instrument(row: dict[str, str]) -> bool:
    return clean(row.get("route")) != "supplier_or_build_record" and clean(row.get("instrument_class")) not in RECORD_INSTRUMENT_CLASSES


def add_issue(
    issues: list[dict[str, str]],
    severity: str,
    row: dict[str, str],
    field: str,
    message: str,
) -> None:
    issues.append({
        "severity": severity,
        "queue_id": clean(row.get("queue_id")),
        "branch": clean(row.get("branch")),
        "run_id": clean(row.get("run_id")),
        "target_field": clean(row.get("target_field")),
        "field": field,
        "message": message,
    })


def validate_entry(row: dict[str, str], queue_row: dict[str, str], manifest: dict[str, Any], issues: list[dict[str, str]]) -> bool:
    ok = True
    for field in ["value", "measured_at", "operator_or_agent", "instrument_id", "source_file", "notes"]:
        if has_placeholder_or_synthetic(clean(row.get(field))):
            add_issue(issues, "error", row, field, "entry contains placeholder or synthetic marker")
            ok = False
    if not clean(row.get("measured_at")):
        add_issue(issues, "error", row, "measured_at", "filled entry needs measured_at")
        ok = False
    if not clean(row.get("operator_or_agent")):
        add_issue(issues, "error", row, "operator_or_agent", "filled entry needs operator_or_agent")
        ok = False
    if requires_instrument(queue_row) and not clean(row.get("instrument_id")):
        add_issue(issues, "error", row, "instrument_id", "filled measured entry needs instrument_id")
        ok = False
    valid_sources, source_errors = source_files_valid(clean(row.get("source_file")), manifest)
    if not valid_sources:
        ok = False
        for message in source_errors:
            add_issue(issues, "error", row, "source_file", message)
    return ok


def update_h_a_row(target: dict[str, str], entry: dict[str, str]) -> None:
    target["value"] = clean(entry.get("value"))
    if clean(entry.get("measured_at")):
        target["measured_at"] = clean(entry.get("measured_at"))
    if clean(entry.get("operator_or_agent")):
        target["operator_or_agent"] = clean(entry.get("operator_or_agent"))
    target["instrument_id"] = clean(entry.get("instrument_id"))
    target["source_file"] = clean(entry.get("source_file"))
    target["notes"] = clean(entry.get("notes"))


def update_zrc_row(target: dict[str, str], queue_row: dict[str, str], entry: dict[str, str]) -> None:
    field = clean(queue_row.get("target_field"))
    target[field] = clean(entry.get("value"))
    if field == "date" and clean(entry.get("value")):
        target["date"] = clean(entry.get("value"))
    if not clean(target.get("measured_at")):
        target["measured_at"] = clean(entry.get("measured_at"))
    if not clean(target.get("date")) and clean(entry.get("measured_at")):
        target["date"] = clean(entry.get("measured_at")).split("T", 1)[0].split(" ", 1)[0]
    if not clean(target.get("operator_or_agent")):
        target["operator_or_agent"] = clean(entry.get("operator_or_agent"))
    if not clean(target.get("instrument_id")):
        target["instrument_id"] = clean(entry.get("instrument_id"))
    target["source_file"] = append_unique(clean(target.get("source_file")), clean(entry.get("source_file")))
    target["notes"] = append_unique(clean(target.get("notes")), clean(entry.get("notes")))


def build_template_maps(args: argparse.Namespace) -> dict[str, dict[str, Any]]:
    maps = {}
    for path in [args.h_a_local, args.h_a_outsource, args.zrc_local, args.zrc_outsource]:
        fields, rows = load_csv(path)
        maps[rel(path)] = {"path": path, "fields": fields, "rows": rows}
    return maps


def apply_entries(args: argparse.Namespace) -> dict[str, Any]:
    _sheet_fields, sheet_rows = load_csv(args.sheet)
    queue_doc = load_json(args.queue)
    manifest = load_json(args.source_manifest)
    queue_lookup = queue_by_id(queue_doc)
    template_maps = build_template_maps(args)
    issues: list[dict[str, str]] = []
    applied = 0
    skipped_blank = 0
    skipped_apply_no = 0
    skipped_invalid = 0
    skipped_missing_target = 0

    for entry in sheet_rows:
        if clean(entry.get("apply")).lower() in {"no", "false", "0", "skip"}:
            skipped_apply_no += 1
            continue
        if not clean(entry.get("value")):
            skipped_blank += 1
            continue
        queue_id = clean(entry.get("queue_id"))
        queue_row = queue_lookup.get(queue_id)
        if not queue_row:
            add_issue(issues, "error", entry, "queue_id", "queue_id is not present in smoke execution queue")
            skipped_invalid += 1
            continue
        merged = {**queue_row, **entry}
        if not validate_entry(merged, queue_row, manifest, issues):
            skipped_invalid += 1
            continue
        template = template_maps.get(clean(queue_row.get("entry_file")))
        if not template:
            add_issue(issues, "error", merged, "entry_file", "entry_file is not one of the configured smoke templates")
            skipped_missing_target += 1
            continue
        rows = template["rows"]
        if clean(queue_row.get("branch")) == H_A_BRANCH:
            key = (clean(queue_row.get("run_id")), clean(queue_row.get("sample_event")), clean(queue_row.get("target_field")))
            target = next((row for row in rows if h_a_key(row) == key), None)
            if target is None:
                add_issue(issues, "error", merged, "row_locator", "matching H-A template row was not found")
                skipped_missing_target += 1
                continue
            update_h_a_row(target, merged)
        else:
            run_id = clean(queue_row.get("run_id"))
            target = next((row for row in rows if clean(row.get("run_id")) == run_id), None)
            if target is None:
                add_issue(issues, "error", merged, "row_locator", "matching ZRC template row was not found")
                skipped_missing_target += 1
                continue
            update_zrc_row(target, queue_row, merged)
        applied += 1

    if applied:
        for item in template_maps.values():
            write_csv(item["path"], item["fields"], item["rows"])

    counts = Counter(issue["severity"] for issue in issues)
    if counts.get("error", 0):
        status = "smoke_entry_apply_blocked"
    elif applied:
        status = "smoke_entry_apply_applied"
    else:
        status = "smoke_entry_apply_no_filled_rows"
    return {
        "status": status,
        "summary": {
            "sheet_rows": len(sheet_rows),
            "applied_values": applied,
            "skipped_blank_rows": skipped_blank,
            "skipped_apply_no_rows": skipped_apply_no,
            "skipped_invalid_rows": skipped_invalid,
            "skipped_missing_target_rows": skipped_missing_target,
            "error_count": counts.get("error", 0),
            "warning_count": counts.get("warning", 0),
        },
        "inputs": {
            "sheet": rel(args.sheet),
            "queue": rel(args.queue),
            "source_manifest": rel(args.source_manifest),
        },
        "updated_templates": [rel(item["path"]) for item in template_maps.values()] if applied else [],
        "issues": issues,
        "boundary": "Applying an entry sheet only copies user-entered values into smoke templates. Downstream preflight, rehearsal, QC, gates, and claim audit still control evidence status.",
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Entry Apply",
        "",
        "This report applies filled smoke entry-sheet rows into smoke templates. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Applied values:** {summary['applied_values']}",
        f"**Blank rows skipped:** {summary['skipped_blank_rows']}",
        f"**Invalid rows skipped:** {summary['skipped_invalid_rows']}",
        f"**Errors:** {summary['error_count']}",
        f"**Warnings:** {summary['warning_count']}",
        "",
        "## Issues",
        "",
    ]
    if not result["issues"]:
        lines.append("- No apply issues.")
    else:
        lines.extend(["| Severity | Queue | Run | Field | Message |", "| --- | --- | --- | --- | --- |"])
        for issue in result["issues"][:100]:
            lines.append(
                f"| `{issue['severity']}` | `{issue['queue_id']}` | `{issue['run_id']}` | "
                f"`{issue['field']}` | {issue['message']} |"
            )
        if len(result["issues"]) > 100:
            lines.append(f"| `info` | `-` | `-` | `-` | {len(result['issues']) - 100} additional issues omitted. |")
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply LIMINA smoke entry sheet.")
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--h-a-local", type=Path, default=DEFAULT_H_A_LOCAL)
    parser.add_argument("--h-a-outsource", type=Path, default=DEFAULT_H_A_OUTSOURCE)
    parser.add_argument("--zrc-local", type=Path, default=DEFAULT_ZRC_LOCAL)
    parser.add_argument("--zrc-outsource", type=Path, default=DEFAULT_ZRC_OUTSOURCE)
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
    print(f"Smoke entry apply: {result['status']}")
    print(f"Applied values: {result['summary']['applied_values']}")
    print(f"Errors: {result['summary']['error_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
