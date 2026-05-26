#!/usr/bin/env python3
"""Preflight local LIMINA capture templates before merge into evidence tables."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = ROOT / "data" / "limina_local_capture_tasks.csv"
DEFAULT_H_A_LOCAL = ROOT / "data" / "nhi_pedot_h_a_local_capture_template.csv"
DEFAULT_H_A_OUTSOURCE = ROOT / "data" / "nhi_pedot_h_a_osmolality_outsource_template.csv"
DEFAULT_ZRC_LOCAL = ROOT / "data" / "zrc_nd_phase_a_local_capture_template.csv"
DEFAULT_ZRC_OUTSOURCE = ROOT / "data" / "zrc_nd_phase_a_osmolality_outsource_template.csv"
DEFAULT_INSTRUMENTS = ROOT / "data" / "limina_local_instrument_register_template.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "limina_local_capture_preflight.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_local_capture_preflight.md"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BOOL_VALUES = {"true", "false", "yes", "no", "1", "0", "y", "n"}
NUMERIC_RANGES = {
    "temperature_c": (15.0, 45.0, "warning"),
    "pH": (6.5, 8.2, "warning"),
    "pH_initial": (6.5, 8.2, "warning"),
    "pH_final": (6.5, 8.2, "warning"),
    "osmolality": (200.0, 420.0, "warning"),
    "osmolality_initial_mOsm_kg": (200.0, 420.0, "warning"),
    "osmolality_final_mOsm_kg": (200.0, 420.0, "warning"),
    "conductivity": (1.0, 30.0, "warning"),
    "conductivity_initial_mS_cm": (1.0, 30.0, "warning"),
    "conductivity_final_mS_cm": (1.0, 30.0, "warning"),
    "swelling_fraction": (-0.5, 2.0, "error"),
    "delamination_score": (0.0, 5.0, "error"),
    "optical_transparency_fraction": (0.0, 1.0, "error"),
    "membrane_area_cm2": (0.0, 1000.0, "error"),
    "initial_volume_ml": (0.0, 1000.0, "error"),
    "exposure_time_h": (0.0, 10000.0, "error"),
}
BOOL_FIELDS = {"visible_precipitate", "visible_shedding"}
RECORD_INSTRUMENT_CLASSES = {"record_review", "bench_or_vendor_record"}
SOURCE_FILE_WEAK_MARKERS = {"email", "quote", "verbal", "capability", "phone_call"}
SOURCE_FILE_SPLIT_RE = re.compile(r"[;\n|]+")


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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def clean(value: Any) -> str:
    return str(value or "").strip()


def lower_contains(raw: str, markers: set[str]) -> bool:
    lowered = raw.lower()
    return any(marker in lowered for marker in markers)


def is_placeholder(raw: str) -> bool:
    return lower_contains(raw, set(PLACEHOLDER_MARKERS))


def is_synthetic(raw: str) -> bool:
    return lower_contains(raw, set(SYNTHETIC_MARKERS))


def parse_float(raw: str) -> float | None:
    try:
        return float(raw)
    except ValueError:
        return None


def valid_iso_date(raw: str) -> bool:
    if not DATE_RE.match(raw):
        return False
    try:
        date.fromisoformat(raw)
    except ValueError:
        return False
    return True


def add_issue(
    issues: list[dict[str, str]],
    severity: str,
    task: dict[str, str],
    field: str,
    message: str,
) -> None:
    issues.append({
        "severity": severity,
        "task_id": clean(task.get("task_id")),
        "branch": clean(task.get("branch")),
        "route": clean(task.get("route")),
        "run_id": clean(task.get("run_id")),
        "target_field": clean(task.get("target_field")),
        "field": field,
        "message": message,
    })


def task_key(task: dict[str, str]) -> tuple[str, str, str]:
    return (clean(task.get("branch")), clean(task.get("run_id")), clean(task.get("target_field")))


def row_key(branch: str, row: dict[str, str]) -> tuple[str, str]:
    return (branch, clean(row.get("run_id")))


def h_a_row_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (clean(row.get("run_id")), clean(row.get("sample_event")), clean(row.get("target_field")))


def task_is_in_template(task: dict[str, str], template_path: Path) -> bool:
    return clean(task.get("entry_file")) == rel(template_path)


def value_present(raw: str) -> bool:
    value = clean(raw)
    return bool(value) and not is_placeholder(value) and not is_synthetic(value)


def source_file_is_weak(raw: str, markers: set[str] | None = None) -> bool:
    lowered = clean(raw).lower()
    return any(marker in lowered for marker in (markers or SOURCE_FILE_WEAK_MARKERS))


def source_reject_markers(manifest: dict[str, Any]) -> set[str]:
    markers = set(SOURCE_FILE_WEAK_MARKERS)
    for item in manifest.get("rejected_source_markers", []):
        cleaned = clean(item).lower()
        if cleaned:
            markers.add(cleaned)
    return markers


def split_source_files(raw: str) -> list[str]:
    return [
        item.strip().strip("\"'")
        for item in SOURCE_FILE_SPLIT_RE.split(clean(raw))
        if item.strip().strip("\"'")
    ]


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


def allowed_source_roots(manifest: dict[str, Any]) -> list[Path]:
    roots: list[Path] = []
    for row in manifest.get("allowed_roots", []):
        raw = clean(row.get("path"))
        if not raw:
            continue
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = ROOT / path
        roots.append(path)
    return roots


def check_source_files(
    issues: list[dict[str, str]],
    task: dict[str, str],
    raw_source_file: str,
    manifest: dict[str, Any],
) -> None:
    refs = split_source_files(raw_source_file)
    if not refs:
        add_issue(issues, "error", task, "source_file", "source_file did not contain a parseable file path")
        return

    roots = allowed_source_roots(manifest)
    if not roots:
        add_issue(issues, "error", task, "source_file", "source_file manifest is missing allowed roots")
        return

    for ref in refs:
        if is_placeholder(ref):
            add_issue(issues, "error", task, "source_file", "source_file contains a placeholder marker")
            continue
        if is_synthetic(ref):
            add_issue(issues, "error", task, "source_file", "source_file contains a synthetic/fixture marker")
            continue
        path = resolve_source_path(ref)
        if not path.exists():
            add_issue(issues, "error", task, "source_file", f"source_file `{ref}` does not exist in the workspace/dropbox")
            continue
        if path.is_dir():
            add_issue(issues, "error", task, "source_file", f"source_file `{rel(path)}` is a directory; point to a concrete file")
            continue
        if not any(path_is_within(path, root) for root in roots):
            add_issue(
                issues,
                "error",
                task,
                "source_file",
                f"source_file `{rel(path)}` is outside allowed source-file roots",
            )


def instrument_statuses(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {
        clean(row.get("instrument_id")): row
        for row in rows
        if clean(row.get("instrument_id"))
    }


def check_value_shape(issues: list[dict[str, str]], task: dict[str, str], raw_value: str, raw_unit: str) -> None:
    value = clean(raw_value)
    field = clean(task.get("wide_field")) or clean(task.get("target_field"))
    unit = clean(raw_unit)
    if value == "":
        return
    if is_placeholder(value):
        add_issue(issues, "error", task, field, "value contains a placeholder marker")
    if is_synthetic(value):
        add_issue(issues, "error", task, field, "value contains a synthetic/fixture marker")
    if field in BOOL_FIELDS and value.lower() not in BOOL_VALUES:
        add_issue(issues, "error", task, field, "boolean value must be true/false, yes/no, 1/0, or y/n")
    if field in NUMERIC_RANGES:
        parsed = parse_float(value)
        if parsed is None:
            add_issue(issues, "error", task, field, "numeric field is not parseable")
        else:
            lower, upper, severity = NUMERIC_RANGES[field]
            if parsed < lower or parsed > upper:
                add_issue(issues, severity, task, field, f"value {parsed:g} is outside expected range [{lower:g}, {upper:g}]")
    expected_unit = clean(task.get("unit"))
    if expected_unit and unit and unit != expected_unit:
        add_issue(issues, "warning", task, "unit", f"unit `{unit}` differs from expected `{expected_unit}`")


def check_provenance(
    issues: list[dict[str, str]],
    task: dict[str, str],
    row: dict[str, str],
    instruments: dict[str, dict[str, str]],
    source_manifest: dict[str, Any],
) -> None:
    route = clean(task.get("route"))
    instrument_class = clean(task.get("instrument_class"))
    measured_at = clean(row.get("measured_at")) or clean(row.get("date"))
    operator = clean(row.get("operator_or_agent"))
    source_file = clean(row.get("source_file"))
    instrument_id = clean(row.get("instrument_id"))

    if measured_at and not valid_iso_date(measured_at.split("T", 1)[0].split(" ", 1)[0]):
        add_issue(issues, "error", task, "measured_at", "measurement date must start with YYYY-MM-DD")
    if not measured_at:
        add_issue(issues, "error", task, "measured_at", "filled value needs measured_at or date provenance")
    if not operator:
        add_issue(issues, "error", task, "operator_or_agent", "filled value needs operator_or_agent provenance")
    if not source_file:
        add_issue(issues, "error", task, "source_file", "filled value needs source_file provenance")
    elif is_placeholder(source_file):
        add_issue(issues, "error", task, "source_file", "source_file contains a placeholder marker")
    elif is_synthetic(source_file):
        add_issue(issues, "error", task, "source_file", "source_file contains a synthetic/fixture marker")
    elif source_file_is_weak(source_file, source_reject_markers(source_manifest)):
        add_issue(issues, "error", task, "source_file", "source_file cannot be only a quote/email/verbal capability note")
    else:
        check_source_files(issues, task, source_file, source_manifest)

    if route != "supplier_or_build_record" and instrument_class not in RECORD_INSTRUMENT_CLASSES:
        if not instrument_id:
            add_issue(issues, "error", task, "instrument_id", "measured field needs instrument_id")
        elif instrument_id not in instruments:
            add_issue(issues, "warning", task, "instrument_id", "instrument_id is not present in local instrument register")
        else:
            status = clean(instruments[instrument_id].get("status"))
            if status in {"needed_before_measurement", "pending", "unknown"}:
                add_issue(issues, "warning", task, "instrument_id", f"instrument register status is `{status}`")


def check_h_a_template(
    tasks: list[dict[str, str]],
    rows: list[dict[str, str]],
    template_path: Path,
    instruments: dict[str, dict[str, str]],
    source_manifest: dict[str, Any],
    issues: list[dict[str, str]],
) -> dict[str, int]:
    by_key = {h_a_row_key(row): row for row in rows}
    task_count = 0
    filled = 0
    for task in tasks:
        if clean(task.get("branch")) != "NHI-PEDOT H-A" or not task_is_in_template(task, template_path):
            continue
        task_count += 1
        key = (clean(task.get("run_id")), clean(task.get("sample_event")), clean(task.get("target_field")))
        row = by_key.get(key)
        if row is None:
            add_issue(issues, "error", task, "row", "task row is missing from template")
            continue
        raw_value = clean(row.get("value"))
        if not raw_value:
            continue
        filled += 1
        check_value_shape(issues, task, raw_value, clean(row.get("unit")))
        check_provenance(issues, task, row, instruments, source_manifest)
    return {"tasks": task_count, "filled": filled, "pending": task_count - filled}


def check_zrc_template(
    tasks: list[dict[str, str]],
    rows: list[dict[str, str]],
    template_path: Path,
    instruments: dict[str, dict[str, str]],
    source_manifest: dict[str, Any],
    issues: list[dict[str, str]],
) -> dict[str, int]:
    by_run = {row_key("ZRC-ND Phase A", row): row for row in rows}
    task_count = 0
    filled = 0
    for task in tasks:
        if clean(task.get("branch")) != "ZRC-ND Phase A" or not task_is_in_template(task, template_path):
            continue
        task_count += 1
        row = by_run.get(("ZRC-ND Phase A", clean(task.get("run_id"))))
        if row is None:
            add_issue(issues, "error", task, "row", "task row is missing from template")
            continue
        field = clean(task.get("wide_field")) or clean(task.get("target_field"))
        raw_value = clean(row.get(field))
        if not raw_value:
            continue
        filled += 1
        check_value_shape(issues, task, raw_value, "")
        check_provenance(issues, task, row, instruments, source_manifest)
    return {"tasks": task_count, "filled": filled, "pending": task_count - filled}


def summarize_issues(issues: list[dict[str, str]]) -> dict[str, int]:
    counts = Counter(issue["severity"] for issue in issues)
    return {"error": counts.get("error", 0), "warning": counts.get("warning", 0)}


def build_preflight(args: argparse.Namespace) -> dict[str, Any]:
    _task_fields, tasks = load_csv(args.tasks)
    _instrument_fields, instrument_rows = load_csv(args.instrument_register)
    _h_a_local_fields, h_a_local_rows = load_csv(args.h_a_local)
    _h_a_out_fields, h_a_out_rows = load_csv(args.h_a_outsource)
    _zrc_local_fields, zrc_local_rows = load_csv(args.zrc_local)
    _zrc_out_fields, zrc_out_rows = load_csv(args.zrc_outsource)
    source_manifest = load_json(args.source_manifest)
    instruments = instrument_statuses(instrument_rows)
    issues: list[dict[str, str]] = []

    summaries = {
        "h_a_local": check_h_a_template(tasks, h_a_local_rows, args.h_a_local, instruments, source_manifest, issues),
        "h_a_outsource": check_h_a_template(tasks, h_a_out_rows, args.h_a_outsource, instruments, source_manifest, issues),
        "zrc_local": check_zrc_template(tasks, zrc_local_rows, args.zrc_local, instruments, source_manifest, issues),
        "zrc_outsource": check_zrc_template(tasks, zrc_out_rows, args.zrc_outsource, instruments, source_manifest, issues),
    }
    counts = summarize_issues(issues)
    filled_total = sum(item["filled"] for item in summaries.values())
    task_total = sum(item["tasks"] for item in summaries.values())
    if counts["error"]:
        status = "local_capture_preflight_blocked"
    elif filled_total == 0:
        status = "local_capture_preflight_awaiting_entries"
    elif sum(item["pending"] for item in summaries.values()) > 0:
        status = "local_capture_preflight_partial"
    else:
        status = "local_capture_preflight_ready_to_merge"

    return {
        "status": status,
        "preflight_ready": status == "local_capture_preflight_ready_to_merge",
        "task_count": task_total,
        "filled_task_count": filled_total,
        "pending_task_count": task_total - filled_total,
        "issue_counts": counts,
        "template_summaries": summaries,
        "source_file_policy": {
            "manifest": rel(args.source_manifest),
            "status": source_manifest.get("status", "missing"),
            "must_exist": bool(source_manifest.get("policy", {}).get("must_exist")),
            "allowed_root_count": len(source_manifest.get("allowed_roots", [])),
            "expected_source_class_count": len(source_manifest.get("expected_source_classes", [])),
        },
        "inputs": {
            "tasks": rel(args.tasks),
            "h_a_local": rel(args.h_a_local),
            "h_a_outsource": rel(args.h_a_outsource),
            "zrc_local": rel(args.zrc_local),
            "zrc_outsource": rel(args.zrc_outsource),
            "instrument_register": rel(args.instrument_register),
            "source_manifest": rel(args.source_manifest),
        },
        "issues": issues,
        "boundary": "Preflight checks local capture entry quality and source-file existence only. It does not create measured evidence or a material suitability claim.",
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIMINA Local Capture Preflight",
        "",
        "This checks filled local/outsource capture templates before merge. It is not a material suitability claim.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Preflight ready:** `{result['preflight_ready']}`",
        f"**Filled tasks:** {result['filled_task_count']} / {result['task_count']}",
        f"**Pending tasks:** {result['pending_task_count']}",
        f"**Errors:** {result['issue_counts']['error']}",
        f"**Warnings:** {result['issue_counts']['warning']}",
        f"**Source-file policy:** `{result['source_file_policy']['status']}`; "
        f"allowed_roots={result['source_file_policy']['allowed_root_count']}; "
        f"source_classes={result['source_file_policy']['expected_source_class_count']}",
        "",
        "## Template Summaries",
        "",
        "| Template | Tasks | Filled | Pending |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, summary in result["template_summaries"].items():
        lines.append(f"| `{name}` | {summary['tasks']} | {summary['filled']} | {summary['pending']} |")
    lines.extend(["", "## Issues", ""])
    issues = result.get("issues", [])
    if not issues:
        lines.append("- No filled-row issues found.")
    else:
        lines.extend(["| Severity | Task | Branch | Run | Target | Field | Message |", "| --- | --- | --- | --- | --- | --- | --- |"])
        for issue in issues[:100]:
            lines.append(
                f"| `{issue['severity']}` | `{issue['task_id']}` | {issue['branch']} | "
                f"`{issue['run_id']}` | `{issue['target_field']}` | `{issue['field']}` | {issue['message']} |"
            )
        if len(issues) > 100:
            lines.append(f"| `info` | `-` | - | `-` | `-` | `-` | {len(issues) - 100} additional issues omitted. |")
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preflight LIMINA local capture templates before merge.")
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--h-a-local", type=Path, default=DEFAULT_H_A_LOCAL)
    parser.add_argument("--h-a-outsource", type=Path, default=DEFAULT_H_A_OUTSOURCE)
    parser.add_argument("--zrc-local", type=Path, default=DEFAULT_ZRC_LOCAL)
    parser.add_argument("--zrc-outsource", type=Path, default=DEFAULT_ZRC_OUTSOURCE)
    parser.add_argument("--instrument-register", type=Path, default=DEFAULT_INSTRUMENTS)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--strict-exit", action="store_true", help="Return non-zero if preflight is not ready to merge.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_preflight(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Local capture preflight: {result['status']}")
    print(f"Filled tasks: {result['filled_task_count']} / {result['task_count']}")
    print(f"Errors: {result['issue_counts']['error']}")
    print(f"Warnings: {result['issue_counts']['warning']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    if args.strict_exit and not result["preflight_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
