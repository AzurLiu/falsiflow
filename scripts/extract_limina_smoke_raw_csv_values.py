#!/usr/bin/env python3
"""Extract source-backed LIMINA smoke values from existing raw CSV/TSV files."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXECUTION_PACK = ROOT / "data" / "limina_smoke_starter_execution_pack.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_VALUES = ROOT / "data" / "limina_smoke_raw_csv_extracted_values.csv"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_raw_csv_value_extraction.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_raw_csv_value_extraction.md"

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

RAW_SUFFIXES = {".csv", ".tsv"}

FIELD_VALUE_COLUMNS = {
    "pH": ["value", "pH_value", "ph_value", "measured_value", "reading", "result"],
    "conductivity": ["value", "conductivity_mS_cm", "conductivity", "measured_value", "reading", "result"],
    "osmolality": ["value", "osmolality_mOsm_kg", "osmolality", "measured_value", "reading", "result"],
    "temperature_c": ["value", "temperature_c", "temperature", "measured_value", "reading", "result"],
    "swelling_fraction": ["value", "swelling_fraction", "measured_value", "result"],
    "visible_precipitate": ["value", "score_or_boolean", "visible_precipitate", "result"],
    "visible_shedding": ["value", "score_or_boolean", "visible_shedding", "result"],
    "delamination_score": ["value", "score_or_boolean", "delamination_score", "result"],
    "optical_transparency_fraction": ["value", "score_or_boolean", "optical_transparency_fraction", "result"],
    "date": ["value", "date", "measured_at", "measurement_date"],
    "medium_name": ["value", "medium_name"],
    "medium_lot": ["value", "medium_lot", "lot"],
}

GENERIC_VALUE_COLUMNS = ["value", "measured_value", "reading", "result"]
MEASURED_AT_COLUMNS = ["measured_at", "measurement_date", "date", "timestamp", "covered_window_end"]
OPERATOR_COLUMNS = ["operator_or_agent", "operator", "operator_id", "technician", "reviewer", "vendor_or_lab"]
INSTRUMENT_COLUMNS = [
    "instrument_id",
    "pH_meter_id",
    "ph_meter_id",
    "conductivity_meter_id",
    "osmometer_id",
    "probe_or_incubator_id",
]
NOTES_COLUMNS = ["notes", "method_or_record_id", "calibration_record_id", "standard_check_record_id", "report_id"]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def clean(value: Any) -> str:
    return str(value or "").strip()


def lower_key(row: dict[str, str]) -> dict[str, str]:
    return {str(key).strip().lower(): clean(value) for key, value in row.items()}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def load_csv(path: Path, delimiter: str | None = None) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    dialect = {"delimiter": delimiter} if delimiter else {}
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, **dialect)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=VALUE_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in VALUE_FIELDS} for row in rows])


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


def add_issue(
    issues: list[dict[str, str]],
    severity: str,
    source_file: Path,
    queue_id: str,
    field: str,
    message: str,
) -> None:
    issues.append({
        "severity": severity,
        "source_file": rel(source_file),
        "queue_id": queue_id,
        "field": field,
        "message": message,
    })


def first_present(row: dict[str, str], columns: list[str]) -> str:
    direct = {key: clean(value) for key, value in row.items()}
    lowered = lower_key(row)
    for column in columns:
        value = direct.get(column)
        if clean(value):
            return clean(value)
        value = lowered.get(column.lower())
        if clean(value):
            return clean(value)
    return ""


def source_file_match(row: dict[str, str], source_file: Path) -> bool:
    expected = rel(source_file)
    basename = source_file.name
    for column in ["source_file_to_save_as", "source_file", "raw_source_file"]:
        value = first_present(row, [column])
        if not value:
            continue
        try:
            resolved = resolve_path(value)
            if resolved.resolve() == source_file.resolve():
                return True
        except OSError:
            pass
        if value == expected or value.endswith("/" + expected) or value == basename:
            return True
    return False


def matching_rows(csv_rows: list[dict[str, str]], plan: dict[str, str], source_file: Path) -> list[dict[str, str]]:
    queue_id = clean(plan.get("queue_id"))
    matches = [row for row in csv_rows if first_present(row, ["queue_id"]) == queue_id]
    if matches:
        return matches

    matches = [row for row in csv_rows if source_file_match(row, source_file)]
    if matches:
        return matches

    key = (
        clean(plan.get("run_id")),
        clean(plan.get("sample_event")),
        clean(plan.get("target_field")),
    )
    matches = [
        row for row in csv_rows
        if (
            first_present(row, ["run_id"]),
            first_present(row, ["sample_event"]),
            first_present(row, ["target_field"]),
        ) == key
    ]
    if matches:
        return matches

    return csv_rows if len(csv_rows) == 1 else []


def value_for(plan: dict[str, str], row: dict[str, str]) -> str:
    target_field = clean(plan.get("target_field"))
    columns = FIELD_VALUE_COLUMNS.get(target_field, [])
    if target_field and target_field not in columns:
        columns = [target_field, *columns]
    return first_present(row, [*columns, *GENERIC_VALUE_COLUMNS])


def row_notes(row: dict[str, str]) -> str:
    notes = [first_present(row, [column]) for column in NOTES_COLUMNS]
    return "; ".join(item for item in notes if item)


def raw_delimiter(source_file: Path) -> str:
    return "\t" if source_file.suffix.lower() == ".tsv" else ","


def validate_plan_source(source_file: Path, roots: list[Path], manifest: dict[str, Any], issues: list[dict[str, str]], queue_id: str) -> bool:
    ok = True
    if not any(path_is_within(source_file, root) for root in roots):
        add_issue(issues, "error", source_file, queue_id, "source_file", "raw CSV/TSV is outside allowed source-file roots")
        ok = False
    if has_rejected_marker(rel(source_file), manifest):
        add_issue(issues, "error", source_file, queue_id, "source_file", "source path contains a rejected marker")
        ok = False
    return ok


def extract_row(plan: dict[str, str], row: dict[str, str], source_file: Path, manifest: dict[str, Any], issues: list[dict[str, str]]) -> dict[str, str] | None:
    queue_id = clean(plan.get("queue_id"))
    value = value_for(plan, row)
    measured_at = first_present(row, MEASURED_AT_COLUMNS)
    operator = first_present(row, OPERATOR_COLUMNS)
    instrument = first_present(row, INSTRUMENT_COLUMNS)
    notes = row_notes(row)
    required = {
        "value": value,
        "measured_at": measured_at,
        "operator_or_agent": operator,
    }
    if clean(plan.get("instrument_required")).lower() == "true":
        required["instrument_id"] = instrument

    ok = True
    for field, field_value in required.items():
        if not clean(field_value):
            add_issue(issues, "error", source_file, queue_id, field, f"{field} is required in the raw CSV/TSV")
            ok = False
    for field, field_value in {
        "value": value,
        "measured_at": measured_at,
        "operator_or_agent": operator,
        "instrument_id": instrument,
        "notes": notes,
    }.items():
        if clean(field_value) and has_rejected_marker(clean(field_value), manifest):
            add_issue(issues, "error", source_file, queue_id, field, "field contains a rejected placeholder/synthetic/source marker")
            ok = False
    if not ok:
        return None
    return {
        "queue_id": queue_id,
        "run_id": clean(plan.get("run_id")),
        "sample_event": clean(plan.get("sample_event")),
        "target_field": clean(plan.get("target_field")),
        "value": value,
        "measured_at": measured_at,
        "operator_or_agent": operator,
        "instrument_id": instrument,
        "source_file": rel(source_file),
        "notes": notes,
        "apply": "yes",
    }


def extract_values(args: argparse.Namespace) -> dict[str, Any]:
    _fields, plan_rows = load_csv(args.execution_pack)
    manifest = load_json(args.source_manifest)
    roots = allowed_roots(manifest)
    extracted_rows: list[dict[str, str]] = []
    issues: list[dict[str, str]] = []
    seen_source_files: set[str] = set()
    raw_csv_found = 0
    raw_csv_missing = 0
    raw_csv_unsupported = 0
    ambiguous = 0

    for plan in plan_rows:
        queue_id = clean(plan.get("queue_id"))
        source_file = resolve_path(clean(plan.get("source_file")))
        suffix = source_file.suffix.lower()
        if suffix not in RAW_SUFFIXES:
            raw_csv_unsupported += 1
            continue
        if not source_file.exists():
            raw_csv_missing += 1
            continue
        raw_csv_found += 1
        seen_source_files.add(rel(source_file))
        if not source_file.is_file():
            add_issue(issues, "error", source_file, queue_id, "source_file", "source path exists but is not a file")
            continue
        if not validate_plan_source(source_file, roots, manifest, issues, queue_id):
            continue
        fields, csv_rows = load_csv(source_file, delimiter=raw_delimiter(source_file))
        if not fields:
            add_issue(issues, "error", source_file, queue_id, "header", "raw CSV/TSV has no header")
            continue
        matches = matching_rows(csv_rows, plan, source_file)
        if not matches:
            ambiguous += 1
            add_issue(issues, "error", source_file, queue_id, "row_locator", "raw CSV/TSV has multiple rows and none match queue_id, source_file, or run/sample/field")
            continue
        usable = [row for row in matches if any(clean(value) for value in row.values())]
        if len(usable) != 1:
            ambiguous += 1
            add_issue(issues, "error", source_file, queue_id, "row_locator", f"expected exactly one nonblank matching row, found {len(usable)}")
            continue
        extracted = extract_row(plan, usable[0], source_file, manifest, issues)
        if extracted:
            extracted_rows.append(extracted)

    write_csv(args.values_out, extracted_rows)
    counts = Counter(issue["severity"] for issue in issues)
    if counts.get("error", 0) and not extracted_rows:
        status = "smoke_raw_csv_value_extraction_blocked"
    elif counts.get("error", 0):
        status = "smoke_raw_csv_value_extraction_partial"
    elif extracted_rows:
        status = "smoke_raw_csv_value_extraction_ready"
    else:
        status = "smoke_raw_csv_value_extraction_no_raw_csv"

    return {
        "status": status,
        "summary": {
            "plan_rows": len(plan_rows),
            "raw_csv_found": raw_csv_found,
            "raw_csv_missing": raw_csv_missing,
            "raw_csv_unsupported": raw_csv_unsupported,
            "raw_csv_source_files": len(seen_source_files),
            "extracted_rows": len(extracted_rows),
            "ambiguous_rows": ambiguous,
            "error_count": counts.get("error", 0),
            "warning_count": counts.get("warning", 0),
        },
        "inputs": {
            "execution_pack": rel(args.execution_pack),
            "source_manifest": rel(args.source_manifest),
        },
        "generated_artifacts": {
            "values_out": rel(args.values_out),
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "source_files": sorted(seen_source_files),
        "extracted_rows": extracted_rows,
        "issues": issues,
        "boundary": (
            "This extractor reads only existing raw CSV/TSV files in allowed source-file roots. "
            "It writes a non-evidence value sidecar for the importer; missing files produce no synthetic rows."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Smoke Raw CSV Value Extraction",
        "",
        "This extracts source-backed values from existing raw CSV/TSV files. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Plan rows:** {summary['plan_rows']}",
        f"**Raw CSV/TSV files found:** {summary['raw_csv_found']}",
        f"**Raw CSV/TSV files missing:** {summary['raw_csv_missing']}",
        f"**Unsupported non-CSV rows:** {summary['raw_csv_unsupported']}",
        f"**Extracted rows:** {summary['extracted_rows']}",
        f"**Errors:** {summary['error_count']}",
        f"**Warnings:** {summary['warning_count']}",
        f"**Extracted value sidecar:** `{result['generated_artifacts']['values_out']}`",
        "",
        "## Source Files",
        "",
    ]
    if result["source_files"]:
        lines.extend(f"- `{path}`" for path in result["source_files"])
    else:
        lines.append("- No existing raw CSV/TSV source files found.")

    lines.extend(["", "## Extracted Rows", ""])
    if result["extracted_rows"]:
        lines.extend(["| Queue | Run | Field | Source file |", "| --- | --- | --- | --- |"])
        for row in result["extracted_rows"][:100]:
            lines.append(f"| `{row['queue_id']}` | `{row['run_id']}` | `{row['target_field']}` | `{row['source_file']}` |")
    else:
        lines.append("- No rows extracted.")

    lines.extend(["", "## Issues", ""])
    if result["issues"]:
        lines.extend(["| Severity | Source file | Queue | Field | Message |", "| --- | --- | --- | --- | --- |"])
        for issue in result["issues"][:120]:
            lines.append(
                f"| `{issue['severity']}` | `{issue['source_file']}` | `{issue['queue_id']}` | "
                f"`{issue['field']}` | {issue['message']} |"
            )
        if len(result["issues"]) > 120:
            lines.append(f"| `info` | `-` | `-` | `-` | {len(result['issues']) - 120} additional issues omitted. |")
    else:
        lines.append("- No extraction issues.")

    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract LIMINA smoke values from raw CSV/TSV files.")
    parser.add_argument("--execution-pack", type=Path, default=DEFAULT_EXECUTION_PACK)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--values-out", type=Path, default=DEFAULT_VALUES)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = extract_values(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps({key: value for key, value in result.items() if key != "extracted_rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Smoke raw CSV value extraction: {result['status']}")
    print(f"Raw CSV/TSV files found: {result['summary']['raw_csv_found']}")
    print(f"Extracted rows: {result['summary']['extracted_rows']}")
    print(f"Errors: {result['summary']['error_count']}")
    print(f"Wrote {args.values_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
