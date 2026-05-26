#!/usr/bin/env python3
"""Inventory and route unstructured LIMINA smoke starter source files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is optional in some runtimes.
    Image = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXECUTION_PACK = ROOT / "data" / "limina_smoke_starter_execution_pack.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_unstructured_source_intake.json"
DEFAULT_CSV = ROOT / "data" / "limina_smoke_unstructured_source_intake.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_unstructured_source_intake.md"

STRUCTURED_SUFFIXES = {".csv", ".tsv"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".heic"}
PDF_SUFFIXES = {".pdf"}

CSV_FIELDS = [
    "queue_id",
    "run_id",
    "sample_event",
    "target_field",
    "source_class",
    "source_file",
    "extension",
    "status",
    "exists",
    "size_bytes",
    "sha256",
    "validation",
    "image_width",
    "image_height",
    "extraction_mode",
    "value_to_extract",
    "required_metadata",
    "sidecar_hint",
    "issue",
]

VALUE_TO_EXTRACT = {
    "mea_coupon_id": "MEA/coupon/sample identifier",
    "electrode_material": "electrode material",
    "laminin_or_peptide_density": "coating density or recipe identifier",
    "sterilization_or_aseptic_protocol": "SOP, batch, or protocol identifier",
    "osmolality": "mOsm/kg value plus report/lab identifier",
    "visible_precipitate": "scored boolean",
    "visible_shedding": "scored boolean",
    "delamination_score": "numeric or ordinal score",
    "optical_transparency_fraction": "calculated transparency fraction",
}


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_validation(path: Path) -> tuple[str, str]:
    with path.open("rb") as handle:
        prefix = handle.read(8)
    if prefix.startswith(b"%PDF-"):
        return "pdf_header_ok", ""
    return "pdf_header_invalid", "PDF source does not start with a PDF header"


def image_validation(path: Path) -> tuple[str, str, str, str]:
    if Image is None:
        return "image_unchecked_pillow_unavailable", "", "", ""
    try:
        with Image.open(path) as image:
            width, height = image.size
            image.verify()
        return "image_open_ok", str(width), str(height), ""
    except Exception as exc:  # noqa: BLE001 - report validation failure without crashing intake.
        return "image_open_failed", "", "", str(exc)


def extraction_mode(source_class: str, suffix: str) -> str:
    if source_class == "osmometer_report_or_export" or suffix in PDF_SUFFIXES:
        return "manual_pdf_or_ocr_to_source_value_sidecar"
    if source_class == "image_or_scoring_worksheet" or suffix in IMAGE_SUFFIXES:
        return "manual_image_scoring_to_source_value_sidecar"
    return "manual_record_review_to_source_value_sidecar"


def sidecar_hint(row: dict[str, str]) -> str:
    return (
        "Append a row to data/limina_smoke_source_values.csv or a run-local limina_values.csv "
        f"with queue_id={clean(row.get('queue_id'))}, value, measured_at, operator_or_agent, "
        "instrument_id when required, source_file, notes, apply=yes."
    )


def intake_row(plan: dict[str, str], roots: list[Path], manifest: dict[str, Any]) -> dict[str, Any]:
    source_file = resolve_path(clean(plan.get("source_file")))
    suffix = source_file.suffix.lower()
    row: dict[str, Any] = {
        "queue_id": clean(plan.get("queue_id")),
        "run_id": clean(plan.get("run_id")),
        "sample_event": clean(plan.get("sample_event")),
        "target_field": clean(plan.get("target_field")),
        "source_class": clean(plan.get("source_class")),
        "source_file": rel(source_file),
        "extension": suffix,
        "status": "missing_source_file",
        "exists": "false",
        "size_bytes": "",
        "sha256": "",
        "validation": "not_run_missing_file",
        "image_width": "",
        "image_height": "",
        "extraction_mode": extraction_mode(clean(plan.get("source_class")), suffix),
        "value_to_extract": VALUE_TO_EXTRACT.get(clean(plan.get("target_field")), clean(plan.get("value_entry_hint"))),
        "required_metadata": clean(plan.get("required_source_metadata")),
        "sidecar_hint": sidecar_hint(plan),
        "issue": "",
    }
    if suffix in STRUCTURED_SUFFIXES:
        row["status"] = "structured_source_not_in_unstructured_intake"
        row["validation"] = "skipped_structured_csv_tsv"
        return row
    if not source_file.exists():
        return row
    row["exists"] = "true"
    if not source_file.is_file():
        row.update({"status": "invalid_source_file", "validation": "not_a_file", "issue": "Source path exists but is not a concrete file"})
        return row
    if not any(path_is_within(source_file, root) for root in roots):
        row.update({"status": "invalid_source_file", "validation": "outside_allowed_roots", "issue": "Source file is outside allowed roots"})
        return row
    if has_rejected_marker(rel(source_file), manifest):
        row.update({"status": "invalid_source_file", "validation": "rejected_marker_in_path", "issue": "Source file path contains a rejected marker"})
        return row

    stat = source_file.stat()
    row["size_bytes"] = stat.st_size
    row["sha256"] = sha256_file(source_file)
    if suffix in PDF_SUFFIXES:
        validation, issue = pdf_validation(source_file)
        row["validation"] = validation
        row["issue"] = issue
        row["status"] = "ready_for_value_extraction" if not issue else "invalid_source_file"
        return row
    if suffix in IMAGE_SUFFIXES:
        validation, width, height, issue = image_validation(source_file)
        row["validation"] = validation
        row["image_width"] = width
        row["image_height"] = height
        row["issue"] = issue
        row["status"] = "ready_for_value_extraction" if not issue else "invalid_source_file"
        return row

    row["validation"] = "unstructured_extension_not_validated"
    row["status"] = "ready_for_value_extraction"
    return row


def build_intake(args: argparse.Namespace) -> dict[str, Any]:
    _fields, plan_rows = load_csv(args.execution_pack)
    manifest = load_json(args.source_manifest)
    roots = allowed_roots(manifest)
    rows = [
        intake_row(plan, roots, manifest)
        for plan in plan_rows
        if resolve_path(clean(plan.get("source_file"))).suffix.lower() not in STRUCTURED_SUFFIXES
    ]
    status_counts: dict[str, int] = {}
    validation_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
        validation_counts[row["validation"]] = validation_counts.get(row["validation"], 0) + 1
    existing = status_counts.get("ready_for_value_extraction", 0) + status_counts.get("invalid_source_file", 0)
    invalid = status_counts.get("invalid_source_file", 0)
    ready = status_counts.get("ready_for_value_extraction", 0)
    if invalid:
        status = "smoke_unstructured_source_intake_has_invalid_files"
    elif ready:
        status = "smoke_unstructured_source_intake_ready_for_review"
    elif rows:
        status = "smoke_unstructured_source_intake_waiting_for_files"
    else:
        status = "smoke_unstructured_source_intake_no_unstructured_rows"

    return {
        "status": status,
        "summary": {
            "unstructured_plan_rows": len(rows),
            "existing_unstructured_files": existing,
            "ready_for_value_extraction": ready,
            "invalid_source_files": invalid,
            "missing_source_files": status_counts.get("missing_source_file", 0),
            "status_counts": status_counts,
            "validation_counts": validation_counts,
        },
        "inputs": {
            "execution_pack": rel(args.execution_pack),
            "source_manifest": rel(args.source_manifest),
        },
        "generated_artifacts": {
            "csv": rel(args.csv_out),
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "rows": rows,
        "boundary": (
            "This intake hashes and routes unstructured source files only. It does not extract or create "
            "measured values; value rows must still pass the source-value importer, preflight, merge/QC, gate evaluation, and claim audit."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Unstructured Source Intake",
        "",
        "This routes PDF/image/other non-CSV starter source files for value extraction. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Unstructured plan rows:** {summary['unstructured_plan_rows']}",
        f"**Existing unstructured files:** {summary['existing_unstructured_files']}",
        f"**Ready for value extraction:** {summary['ready_for_value_extraction']}",
        f"**Invalid source files:** {summary['invalid_source_files']}",
        f"**Missing source files:** {summary['missing_source_files']}",
        f"**CSV:** `{result['generated_artifacts']['csv']}`",
        "",
        "## Rows",
        "",
        "| Queue | Field | Source class | Status | Validation | Source file |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"][:100]:
        lines.append(
            f"| `{row['queue_id']}` | `{row['target_field']}` | `{row['source_class']}` | "
            f"`{row['status']}` | `{row['validation']}` | `{row['source_file']}` |"
        )
    if len(result["rows"]) > 100:
        lines.append(f"| `-` | `-` | `-` | `-` | `-` | {len(result['rows']) - 100} additional rows omitted. |")

    lines.extend([
        "",
        "## Extraction Contract",
        "",
        "- For PDF reports, read or OCR the real report and write the measured value to a source-value sidecar.",
        "- For images, score the image or use the image-analysis worksheet, then write the scored value to a source-value sidecar.",
        "- The sidecar must cite the raw PDF/image as `source_file`; the sidecar itself is never evidence.",
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Intake unstructured LIMINA smoke starter source files.")
    parser.add_argument("--execution-pack", type=Path, default=DEFAULT_EXECUTION_PACK)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_intake(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Smoke unstructured source intake: {result['status']}")
    print(f"Unstructured plan rows: {result['summary']['unstructured_plan_rows']}")
    print(f"Ready for value extraction: {result['summary']['ready_for_value_extraction']}")
    print(f"Invalid source files: {result['summary']['invalid_source_files']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
