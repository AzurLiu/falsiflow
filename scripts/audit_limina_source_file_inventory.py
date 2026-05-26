#!/usr/bin/env python3
"""Inventory LIMINA source files and reconcile capture-template references."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "limina_source_file_inventory.json"
DEFAULT_CSV = ROOT / "data" / "limina_source_file_inventory.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_source_file_inventory.md"

DEFAULT_CAPTURE_FILES = [
    ROOT / "data" / "nhi_pedot_h_a_local_capture_template.csv",
    ROOT / "data" / "nhi_pedot_h_a_osmolality_outsource_template.csv",
    ROOT / "data" / "zrc_nd_phase_a_local_capture_template.csv",
    ROOT / "data" / "zrc_nd_phase_a_osmolality_outsource_template.csv",
    ROOT / "data" / "nhi_pedot_h_a_smoke_local_capture_template.csv",
    ROOT / "data" / "nhi_pedot_h_a_smoke_osmolality_outsource_template.csv",
    ROOT / "data" / "zrc_nd_phase_a_smoke_local_capture_template.csv",
    ROOT / "data" / "zrc_nd_phase_a_smoke_osmolality_outsource_template.csv",
]
DEFAULT_SOURCE_VALUE_FILES = [
    ROOT / "data" / "nhi_pedot_h_a_source_values.csv",
    ROOT / "data" / "nhi_pedot_forward_source_values.csv",
    ROOT / "data" / "nhi_pedot_long_source_values.csv",
    ROOT / "data" / "zrc_nd_phase_a_source_values.csv",
    ROOT / "data" / "limina_smoke_source_values.csv",
    ROOT / "data" / "limina_smoke_unstructured_review_values.csv",
]

SOURCE_FILE_SPLIT_RE = re.compile(r"[;\n|]+")
CSV_FIELDS = ["path", "root_id", "size_bytes", "sha256", "extension", "referenced_by_count"]


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


def resolve_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return ROOT / path


def split_source_files(raw: str) -> list[str]:
    return [
        item.strip().strip("\"'")
        for item in SOURCE_FILE_SPLIT_RE.split(clean(raw))
        if item.strip().strip("\"'")
    ]


def allowed_roots(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in manifest.get("allowed_roots", []):
        raw_path = clean(row.get("path"))
        if not raw_path:
            continue
        rows.append({
            "root_id": clean(row.get("root_id")) or raw_path,
            "path": resolve_path(raw_path),
            "scope": clean(row.get("scope")),
        })
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_files(roots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for root in roots:
        root_path = root["path"]
        if not root_path.exists():
            continue
        for path in sorted(item for item in root_path.rglob("*") if item.is_file()):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            stat = path.stat()
            rows.append({
                "path": rel(path),
                "root_id": root["root_id"],
                "size_bytes": stat.st_size,
                "sha256": sha256_file(path),
                "extension": path.suffix.lower(),
                "referenced_by_count": 0,
            })
    return rows


def source_references(capture_files: list[Path]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for path in capture_files:
        _fields, rows = load_csv(path)
        for index, row in enumerate(rows, start=2):
            raw = clean(row.get("source_file"))
            if not raw:
                continue
            for ref in split_source_files(raw):
                refs.append({
                    "reference_type": "capture_template",
                    "capture_file": rel(path),
                    "line": str(index),
                    "run_id": clean(row.get("run_id")),
                    "target_field": clean(row.get("target_field")),
                    "source_file": ref,
                    "resolved_path": rel(resolve_path(ref)),
                })
    return refs


def filled_source_value_references(source_value_files: list[Path]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for path in source_value_files:
        _fields, rows = load_csv(path)
        for index, row in enumerate(rows, start=2):
            if not clean(row.get("value")):
                continue
            raw = clean(row.get("source_file"))
            if not raw:
                continue
            for ref in split_source_files(raw):
                refs.append({
                    "reference_type": "filled_source_value",
                    "capture_file": rel(path),
                    "line": str(index),
                    "run_id": clean(row.get("run_id")),
                    "target_field": clean(row.get("target_field")),
                    "source_file": ref,
                    "resolved_path": rel(resolve_path(ref)),
                })
    return refs


def build_inventory(args: argparse.Namespace) -> dict[str, Any]:
    manifest = load_json(args.manifest)
    roots = allowed_roots(manifest)
    files = inventory_files(roots)
    capture_refs = source_references(args.capture_files)
    source_value_refs = filled_source_value_references(args.source_value_files)
    refs = [*capture_refs, *source_value_refs]
    files_by_path = {row["path"]: row for row in files}

    missing_refs = []
    for ref in refs:
        resolved = ref["resolved_path"]
        if resolved in files_by_path:
            files_by_path[resolved]["referenced_by_count"] += 1
        else:
            missing_refs.append(ref)

    unreferenced_files = [row for row in files if row["referenced_by_count"] == 0]
    if missing_refs:
        status = "source_file_inventory_missing_references"
    elif files:
        status = "source_file_inventory_ready"
    else:
        status = "source_file_inventory_empty"

    return {
        "status": status,
        "manifest_status": manifest.get("status", "missing"),
        "summary": {
            "allowed_root_count": len(roots),
            "file_count": len(files),
            "source_reference_count": len(refs),
            "capture_template_reference_count": len(capture_refs),
            "filled_source_value_reference_count": len(source_value_refs),
            "missing_reference_count": len(missing_refs),
            "unreferenced_file_count": len(unreferenced_files),
        },
        "source_files": files,
        "missing_references": missing_refs,
        "unreferenced_files": unreferenced_files,
        "inputs": {
            "manifest": rel(args.manifest),
            "capture_files": [rel(path) for path in args.capture_files],
            "source_value_files": [rel(path) for path in args.source_value_files],
        },
        "boundary": "This inventory records files and hashes only. A file becomes measured evidence only when a filled row passes preflight, merge/QC, gate evaluation, and claim audit.",
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Source-File Inventory",
        "",
        "This report inventories raw source files and reconciles capture-template `source_file` references. It is not a material suitability claim.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Manifest status:** `{result['manifest_status']}`",
        f"**Files:** {summary['file_count']}",
        f"**Source references:** {summary['source_reference_count']}",
        f"**Capture-template references:** {summary['capture_template_reference_count']}",
        f"**Filled source-value references:** {summary['filled_source_value_reference_count']}",
        f"**Missing references:** {summary['missing_reference_count']}",
        f"**Unreferenced files:** {summary['unreferenced_file_count']}",
        "",
        "## Files",
        "",
    ]
    files = result.get("source_files", [])
    if not files:
        lines.append("- No files found under allowed source-file roots.")
    else:
        lines.extend(["| Path | Root | Bytes | SHA-256 | Referenced by |", "| --- | --- | ---: | --- | ---: |"])
        for row in files[:100]:
            lines.append(
                f"| `{row['path']}` | `{row['root_id']}` | {row['size_bytes']} | "
                f"`{row['sha256']}` | {row['referenced_by_count']} |"
            )
        if len(files) > 100:
            lines.append(f"| `-` | `-` | 0 | `{len(files) - 100} additional files omitted` | 0 |")

    lines.extend(["", "## Missing References", ""])
    missing = result.get("missing_references", [])
    if not missing:
        lines.append("- No missing source_file references found.")
    else:
        lines.extend(["| Type | File | Line | Run | Field | Source file |", "| --- | --- | ---: | --- | --- | --- |"])
        for row in missing[:100]:
            lines.append(
                f"| `{row['reference_type']}` | `{row['capture_file']}` | {row['line']} | "
                f"`{row['run_id']}` | `{row['target_field']}` | `{row['source_file']}` |"
            )
        if len(missing) > 100:
            lines.append(f"| `-` | `-` | 0 | `-` | `-` | `{len(missing) - 100} additional missing references omitted` |")

    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit LIMINA source-file inventory.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--capture-files", type=Path, nargs="*", default=DEFAULT_CAPTURE_FILES)
    parser.add_argument("--source-value-files", type=Path, nargs="*", default=DEFAULT_SOURCE_VALUE_FILES)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_inventory(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, result["source_files"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Source-file inventory: {result['status']}")
    print(f"Files: {result['summary']['file_count']}")
    print(f"Missing references: {result['summary']['missing_reference_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
