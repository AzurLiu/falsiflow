#!/usr/bin/env python3
"""Audit readiness of the LIMINA smoke starter batch."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_VALUES = ROOT / "data" / "limina_smoke_source_values.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_starter_batch_readiness.json"
DEFAULT_CSV = ROOT / "data" / "limina_smoke_starter_batch_readiness.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_starter_batch_readiness.md"
STARTER_ROUND = "R0_pipeline_debug_single_h_a_lead_24h"
SOURCE_SPLIT_CHARS = [";", "|", "\n"]

CSV_FIELDS = [
    "queue_id",
    "run_id",
    "sample_event",
    "target_field",
    "branch",
    "batch",
    "instrument_required",
    "value_status",
    "metadata_status",
    "source_status",
    "ready_for_import",
    "missing_items",
    "source_file",
    "source_file_requirement",
    "capture_instruction",
]


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


def rejected_markers(manifest: dict[str, Any]) -> set[str]:
    markers = set(PLACEHOLDER_MARKERS) | set(SYNTHETIC_MARKERS)
    markers.update(clean(item).lower() for item in manifest.get("rejected_source_markers", []) if clean(item))
    return markers


def has_rejected_marker(raw: str, manifest: dict[str, Any]) -> bool:
    lowered = raw.lower()
    return any(marker in lowered for marker in rejected_markers(manifest))


def source_file_errors(raw: str, manifest: dict[str, Any], source_values_path: Path) -> list[str]:
    errors: list[str] = []
    refs = split_refs(raw)
    if not refs:
        return ["source_file"]
    roots = allowed_roots(manifest)
    if not roots:
        return ["source_manifest_allowed_roots"]
    for ref in refs:
        if has_rejected_marker(ref, manifest):
            errors.append("source_file_rejected_marker")
            continue
        path = resolve_path(ref)
        if not path.exists():
            errors.append("source_file_missing")
            continue
        if not path.is_file():
            errors.append("source_file_not_file")
            continue
        if path.resolve() == source_values_path.resolve():
            errors.append("source_file_is_values_sheet")
            continue
        if not any(path_is_within(path, root) for root in roots):
            errors.append("source_file_outside_allowed_roots")
    return sorted(set(errors))


def row_missing_items(row: dict[str, str], manifest: dict[str, Any], source_values_path: Path) -> list[str]:
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
    missing.extend(source_file_errors(clean(row.get("source_file")), manifest, source_values_path))
    return sorted(set(missing))


def build_audit(args: argparse.Namespace) -> dict[str, Any]:
    _fields, rows = load_csv(args.source_values)
    manifest = load_json(args.source_manifest)
    starter_rows = [row for row in rows if clean(row.get("recommended_round")) == STARTER_ROUND or clean(row.get("starter_batch")).lower() == "true"]
    audit_rows: list[dict[str, Any]] = []

    for row in starter_rows:
        missing = row_missing_items(row, manifest, args.source_values)
        source_missing = [item for item in missing if item.startswith("source_")]
        metadata_missing = [item for item in missing if item in {"measured_at", "operator_or_agent", "instrument_id"} or item.endswith("_rejected_marker")]
        value_missing = any(item == "value" or item == "value_rejected_marker" for item in missing)
        audit_rows.append({
            "queue_id": clean(row.get("queue_id")),
            "run_id": clean(row.get("run_id")),
            "sample_event": clean(row.get("sample_event")),
            "target_field": clean(row.get("target_field")),
            "branch": clean(row.get("branch")),
            "batch": clean(row.get("batch")),
            "instrument_required": clean(row.get("instrument_required")),
            "value_status": "ready" if not value_missing else "missing_or_rejected",
            "metadata_status": "ready" if not metadata_missing else "missing_or_rejected",
            "source_status": "ready" if not source_missing else "missing_or_rejected",
            "ready_for_import": str(not missing).lower(),
            "missing_items": ";".join(missing),
            "source_file": clean(row.get("source_file")),
            "source_file_requirement": clean(row.get("source_file_requirement")),
            "capture_instruction": clean(row.get("capture_instruction")),
        })

    missing_counts: Counter[str] = Counter()
    for row in audit_rows:
        missing_counts.update(item for item in row["missing_items"].split(";") if item)

    ready_rows = sum(1 for row in audit_rows if row["ready_for_import"] == "true")
    filled_rows = sum(1 for row in starter_rows if clean(row.get("value")))
    source_file_exists_rows = sum(
        1
        for row in starter_rows
        if clean(row.get("source_file")) and all(resolve_path(ref).is_file() for ref in split_refs(clean(row.get("source_file"))))
    )
    status = "smoke_starter_batch_no_rows"
    if audit_rows and ready_rows == len(audit_rows):
        status = "smoke_starter_batch_ready_for_import"
    elif audit_rows and filled_rows:
        status = "smoke_starter_batch_partial"
    elif audit_rows:
        status = "smoke_starter_batch_awaiting_values"

    return {
        "status": status,
        "summary": {
            "starter_rows": len(audit_rows),
            "ready_for_import_rows": ready_rows,
            "filled_value_rows": filled_rows,
            "source_file_exists_rows": source_file_exists_rows,
            "blocked_rows": len(audit_rows) - ready_rows,
            "missing_item_counts": dict(missing_counts),
        },
        "inputs": {
            "source_values": rel(args.source_values),
            "source_manifest": rel(args.source_manifest),
            "starter_round": STARTER_ROUND,
        },
        "generated_artifacts": {
            "json": rel(args.json_out),
            "csv": rel(args.csv_out),
            "report": rel(args.report),
        },
        "rows": audit_rows,
        "post_ready_command": "python3 scripts/run_limina_iteration.py",
        "boundary": "Starter readiness only checks whether rows can be imported. It is not measured evidence and cannot satisfy any material suitability claim.",
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Starter Batch Readiness",
        "",
        "This audits the 19-row starter batch for import readiness. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Starter rows:** {summary['starter_rows']}",
        f"**Ready for import:** {summary['ready_for_import_rows']}",
        f"**Filled values:** {summary['filled_value_rows']}",
        f"**Rows with existing source files:** {summary['source_file_exists_rows']}",
        f"**Blocked rows:** {summary['blocked_rows']}",
        "",
        "## Missing Items",
        "",
    ]
    if summary["missing_item_counts"]:
        lines.extend(["| Missing item | Rows |", "| --- | ---: |"])
        for item, count in sorted(summary["missing_item_counts"].items()):
            lines.append(f"| `{item}` | {count} |")
    else:
        lines.append("- No missing items.")

    lines.extend([
        "",
        "## Starter Rows",
        "",
        "| Queue | Field | Ready | Missing items | Source file |",
        "| --- | --- | --- | --- | --- |",
    ])
    for row in result["rows"]:
        lines.append(
            f"| `{row['queue_id']}` | `{row['target_field']}` | `{row['ready_for_import']}` | "
            f"`{row['missing_items']}` | `{row['source_file']}` |"
        )

    lines.extend([
        "",
        "## When Ready",
        "",
        "```bash",
        result["post_ready_command"],
        "```",
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit LIMINA smoke starter batch readiness.")
    parser.add_argument("--source-values", type=Path, default=DEFAULT_SOURCE_VALUES)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_audit(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, result["rows"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Smoke starter batch readiness: {result['status']}")
    print(f"Starter rows: {result['summary']['starter_rows']}")
    print(f"Ready for import: {result['summary']['ready_for_import_rows']}")
    print(f"Blocked rows: {result['summary']['blocked_rows']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
