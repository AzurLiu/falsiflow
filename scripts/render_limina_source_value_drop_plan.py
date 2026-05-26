#!/usr/bin/env python3
"""Create source-file drop directories for formal LIMINA source-value sheets."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"

PROFILES = {
    "h_a": {
        "label": "NHI-PEDOT H-A",
        "source_values": ROOT / "data" / "nhi_pedot_h_a_source_values.csv",
        "csv": ROOT / "data" / "nhi_pedot_h_a_source_drop_plan.csv",
        "json": ROOT / "data" / "nhi_pedot_h_a_source_drop_plan.json",
        "report": ROOT / "reports" / "nhi_pedot_h_a_source_drop_plan.md",
        "status_prefix": "nhi_pedot_h_a_source_drop_plan",
    },
    "nhi_forward": {
        "label": "NHI-PEDOT H-B/H-C",
        "source_values": ROOT / "data" / "nhi_pedot_forward_source_values.csv",
        "csv": ROOT / "data" / "nhi_pedot_forward_source_drop_plan.csv",
        "json": ROOT / "data" / "nhi_pedot_forward_source_drop_plan.json",
        "report": ROOT / "reports" / "nhi_pedot_forward_source_drop_plan.md",
        "status_prefix": "nhi_pedot_forward_source_drop_plan",
    },
    "nhi_long": {
        "label": "NHI-PEDOT long-duration",
        "source_values": ROOT / "data" / "nhi_pedot_long_source_values.csv",
        "csv": ROOT / "data" / "nhi_pedot_long_source_drop_plan.csv",
        "json": ROOT / "data" / "nhi_pedot_long_source_drop_plan.json",
        "report": ROOT / "reports" / "nhi_pedot_long_source_drop_plan.md",
        "status_prefix": "nhi_pedot_long_source_drop_plan",
    },
    "zrc_phase_a": {
        "label": "ZRC-ND Phase A",
        "source_values": ROOT / "data" / "zrc_nd_phase_a_source_values.csv",
        "csv": ROOT / "data" / "zrc_nd_phase_a_source_drop_plan.csv",
        "json": ROOT / "data" / "zrc_nd_phase_a_source_drop_plan.json",
        "report": ROOT / "reports" / "zrc_nd_phase_a_source_drop_plan.md",
        "status_prefix": "zrc_nd_phase_a_source_drop_plan",
    },
}

CSV_FIELDS = [
    "profile",
    "run_id",
    "phase",
    "sample_event",
    "target_field",
    "source_class",
    "source_file",
    "source_dir",
    "source_dir_status",
    "source_file_exists",
    "source_file_allowed",
    "value_filled",
    "import_ready",
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


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


def source_path_for(row: dict[str, str]) -> Path | None:
    source_file = clean(row.get("source_file")) or clean(row.get("recommended_source_file"))
    if not source_file:
        return None
    return resolve_path(source_file)


def source_file_requirement(row: dict[str, str]) -> str:
    return clean(row.get("source_file_requirement"))


def import_ready(row: dict[str, str]) -> bool:
    status = clean(row.get("review_status")).lower()
    if status:
        return status == "import_ready"
    return all(clean(row.get(field)) for field in ["value", "measured_at", "operator_or_agent", "source_file"])


def create_source_dir(source_dir: Path, allowed: bool) -> str:
    if not allowed:
        return "not_created_outside_allowed_roots"
    before = source_dir.exists()
    source_dir.mkdir(parents=True, exist_ok=True)
    if before:
        return "already_exists"
    return "created"


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    config = PROFILES[args.profile]
    _fields, rows = load_csv(args.source_values)
    manifest = load_json(args.source_manifest)
    roots = allowed_roots(manifest)
    plan_rows: list[dict[str, Any]] = []

    for row in rows:
        source_path = source_path_for(row)
        if source_path is None:
            continue
        allowed = bool(roots) and any(path_is_within(source_path, root) for root in roots)
        dir_status = create_source_dir(source_path.parent, allowed and not args.no_create)
        if args.no_create and allowed:
            dir_status = "not_created_dry_run"
        plan_rows.append({
            "profile": args.profile,
            "run_id": clean(row.get("run_id")),
            "phase": clean(row.get("phase")),
            "sample_event": clean(row.get("sample_event")),
            "target_field": clean(row.get("target_field")),
            "source_class": clean(row.get("source_class")),
            "source_file": rel(source_path),
            "source_dir": rel(source_path.parent),
            "source_dir_status": dir_status,
            "source_file_exists": str(source_path.is_file()).lower(),
            "source_file_allowed": str(allowed).lower(),
            "value_filled": str(bool(clean(row.get("value")))).lower(),
            "import_ready": str(import_ready(row)).lower(),
            "source_file_requirement": source_file_requirement(row),
            "capture_instruction": clean(row.get("capture_instruction")),
        })

    status_prefix = config["status_prefix"]
    source_dirs = {row["source_dir"] for row in plan_rows}
    counts = Counter(row["source_dir_status"] for row in plan_rows)
    class_counts = Counter(row["source_class"] for row in plan_rows)
    existing_files = sum(1 for row in plan_rows if row["source_file_exists"] == "true")
    allowed_files = sum(1 for row in plan_rows if row["source_file_allowed"] == "true")
    status = f"{status_prefix}_ready" if plan_rows else f"{status_prefix}_no_rows"
    if plan_rows and allowed_files != len(plan_rows):
        status = f"{status_prefix}_has_disallowed_paths"
    return {
        "status": status,
        "profile": args.profile,
        "label": config["label"],
        "summary": {
            "planned_source_file_count": len(plan_rows),
            "source_dir_count": len(source_dirs),
            "created_source_dir_count": counts.get("created", 0),
            "existing_source_file_count": existing_files,
            "missing_source_file_count": len(plan_rows) - existing_files,
            "allowed_source_file_count": allowed_files,
            "import_ready_rows": sum(1 for row in plan_rows if row["import_ready"] == "true"),
            "filled_value_rows": sum(1 for row in plan_rows if row["value_filled"] == "true"),
            "source_dir_status_counts": dict(counts),
            "source_class_counts": dict(class_counts),
        },
        "inputs": {
            "source_values": rel(args.source_values),
            "source_manifest": rel(args.source_manifest),
        },
        "generated_artifacts": {
            "json": rel(args.json_out),
            "csv": rel(args.csv_out),
            "report": rel(args.report),
        },
        "rows": plan_rows,
        "boundary": (
            "This creates allowed source-file directories and a missing-file plan only. "
            "It does not create raw measurement files or measured evidence."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        f"# {result['label']} Source Drop Plan",
        "",
        "This report lists concrete source-file paths for formal source-value intake. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Planned source files:** {summary['planned_source_file_count']}",
        f"**Source directories:** {summary['source_dir_count']}",
        f"**Created directories this run:** {summary['created_source_dir_count']}",
        f"**Existing source files:** {summary['existing_source_file_count']}",
        f"**Missing source files:** {summary['missing_source_file_count']}",
        f"**Filled values:** {summary['filled_value_rows']}",
        f"**Import-ready rows:** {summary['import_ready_rows']}",
        "",
        "## Source Classes",
        "",
        "| Source class | Planned files |",
        "| --- | ---: |",
    ]
    for source_class, count in sorted(summary["source_class_counts"].items()):
        lines.append(f"| `{source_class or '-'}` | {count} |")

    lines.extend([
        "",
        "## First 40 Planned Files",
        "",
        "| Run | Field | Exists | Allowed | Source file |",
        "| --- | --- | --- | --- | --- |",
    ])
    for row in result["rows"][:40]:
        lines.append(
            f"| `{row['run_id']}` | `{row['target_field']}` | `{row['source_file_exists']}` | "
            f"`{row['source_file_allowed']}` | `{row['source_file']}` |"
        )
    if len(result["rows"]) > 40:
        lines.append(f"| `-` | `-` | `-` | `-` | {len(result['rows']) - 40} additional planned files in CSV. |")

    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a source-value source-file drop plan.")
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-values", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--csv-out", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--no-create", action="store_true", help="Render plan without creating directories.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = PROFILES[args.profile]
    args.source_values = args.source_values or config["source_values"]
    args.json_out = args.json_out or config["json"]
    args.csv_out = args.csv_out or config["csv"]
    args.report = args.report or config["report"]
    result = build_plan(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, result["rows"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Source drop plan: {result['status']}")
    print(f"Planned source files: {result['summary']['planned_source_file_count']}")
    print(f"Created directories: {result['summary']['created_source_dir_count']}")
    print(f"Existing source files: {result['summary']['existing_source_file_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
