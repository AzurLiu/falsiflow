#!/usr/bin/env python3
"""Extract wide source-value rows from existing raw CSV/TSV files."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS
from render_limina_wide_source_values_sheet import CSV_FIELDS, PROFILES, clean, instrument_required, rel


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
RAW_SUFFIXES = {".csv", ".tsv"}

FIELD_VALUE_ALIASES = {
    "date": ["value", "date", "measured_at", "measurement_date"],
    "operator_or_agent": ["value", "operator_or_agent", "operator", "operator_id", "technician", "reviewer"],
    "temperature_c": ["value", "temperature_c", "temperature", "measured_value", "reading", "result"],
    "pH_initial": ["value", "pH_initial", "pH_value", "ph_value", "measured_value", "reading", "result"],
    "pH_final": ["value", "pH_final", "pH_value", "ph_value", "measured_value", "reading", "result"],
    "osmolality_initial_mOsm_kg": ["value", "osmolality_initial_mOsm_kg", "osmolality_mOsm_kg", "osmolality", "measured_value", "reading", "result"],
    "osmolality_final_mOsm_kg": ["value", "osmolality_final_mOsm_kg", "osmolality_mOsm_kg", "osmolality", "measured_value", "reading", "result"],
    "conductivity_initial_mS_cm": ["value", "conductivity_initial_mS_cm", "conductivity_mS_cm", "conductivity", "measured_value", "reading", "result"],
    "conductivity_final_mS_cm": ["value", "conductivity_final_mS_cm", "conductivity_mS_cm", "conductivity", "measured_value", "reading", "result"],
    "flow_resistance_initial": ["value", "flow_resistance_initial", "flow_resistance", "pressure_drop", "measured_value", "result"],
    "flow_resistance_final": ["value", "flow_resistance_final", "flow_resistance", "pressure_drop", "measured_value", "result"],
    "bubble_events": ["value", "bubble_events", "bubble_event_count", "score_or_boolean", "result"],
    "visible_precipitate": ["value", "visible_precipitate", "score_or_boolean", "result"],
}
GENERIC_VALUE_COLUMNS = [
    "value",
    "measured_value",
    "reading",
    "result",
    "calculated_concentration",
    "raw_signal",
    "score_or_boolean",
]
MEASURED_AT_COLUMNS = ["measured_at", "measurement_date", "date", "timestamp", "covered_window_end"]
OPERATOR_COLUMNS = ["operator_or_agent", "operator", "operator_id", "technician", "reviewer", "vendor_or_lab"]
INSTRUMENT_COLUMNS = [
    "instrument_id",
    "pH_meter_id",
    "ph_meter_id",
    "conductivity_meter_id",
    "osmometer_id",
    "instrument_or_vendor_report_id",
    "instrument_id_or_fixture",
    "probe_or_incubator_id",
    "temperature_source",
    "camera_or_scoring_sheet_id",
]
NOTES_COLUMNS = [
    "notes",
    "method_or_record_id",
    "calibration_record_id",
    "standard_check_record_id",
    "calibration_or_standard_curve_id",
    "report_id",
    "record_id",
    "inspection_method",
]


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


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def raw_delimiter(source_file: Path) -> str:
    return "\t" if source_file.suffix.lower() == ".tsv" else ","


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
    lowered = clean(raw).lower()
    return any(marker in lowered for marker in rejected_markers(manifest))


def add_issue(
    issues: list[dict[str, str]],
    severity: str,
    source_file: Path,
    run_id: str,
    target_field: str,
    field: str,
    message: str,
) -> None:
    issues.append({
        "severity": severity,
        "source_file": rel(source_file),
        "run_id": run_id,
        "target_field": target_field,
        "field": field,
        "message": message,
    })


def lower_key(row: dict[str, str]) -> dict[str, str]:
    return {str(key).strip().lower(): clean(value) for key, value in row.items()}


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


def matching_rows(csv_rows: list[dict[str, str]], plan: dict[str, str]) -> list[dict[str, str]]:
    run_id = clean(plan.get("run_id"))
    target_field = clean(plan.get("target_field"))
    matches = [
        row for row in csv_rows
        if first_present(row, ["run_id"]) == run_id and first_present(row, ["target_field"]) == target_field
    ]
    if matches:
        return matches
    run_matches = [row for row in csv_rows if first_present(row, ["run_id"]) == run_id]
    if len(run_matches) == 1:
        return run_matches
    return csv_rows if len(csv_rows) == 1 else []


def value_for(plan: dict[str, str], row: dict[str, str]) -> str:
    target_field = clean(plan.get("target_field"))
    columns = FIELD_VALUE_ALIASES.get(target_field, [])
    if target_field and target_field not in columns:
        columns = [target_field, *columns]
    return first_present(row, [*columns, *GENERIC_VALUE_COLUMNS])


def row_notes(row: dict[str, str]) -> str:
    notes = [first_present(row, [column]) for column in NOTES_COLUMNS]
    return "; ".join(item for item in notes if item)


def validate_plan_source(source_file: Path, roots: list[Path], manifest: dict[str, Any], issues: list[dict[str, str]], plan: dict[str, str]) -> bool:
    ok = True
    if not any(path_is_within(source_file, root) for root in roots):
        add_issue(issues, "error", source_file, clean(plan.get("run_id")), clean(plan.get("target_field")), "source_file", "raw CSV/TSV is outside allowed source-file roots")
        ok = False
    if has_rejected_marker(rel(source_file), manifest):
        add_issue(issues, "error", source_file, clean(plan.get("run_id")), clean(plan.get("target_field")), "source_file", "source path contains a rejected marker")
        ok = False
    return ok


def extract_row(plan: dict[str, str], row: dict[str, str], source_file: Path, manifest: dict[str, Any], issues: list[dict[str, str]]) -> dict[str, str] | None:
    run_id = clean(plan.get("run_id"))
    target_field = clean(plan.get("target_field"))
    value = value_for(plan, row)
    measured_at = first_present(row, MEASURED_AT_COLUMNS)
    operator = first_present(row, OPERATOR_COLUMNS)
    instrument = first_present(row, INSTRUMENT_COLUMNS)
    notes = row_notes(row)
    required = {"value": value, "measured_at": measured_at, "operator_or_agent": operator}
    if instrument_required(target_field):
        required["instrument_id"] = instrument

    ok = True
    for field, field_value in required.items():
        if not clean(field_value):
            add_issue(issues, "error", source_file, run_id, target_field, field, f"{field} is required in the raw CSV/TSV")
            ok = False
    for field, field_value in {
        "value": value,
        "measured_at": measured_at,
        "operator_or_agent": operator,
        "instrument_id": instrument,
        "notes": notes,
    }.items():
        if clean(field_value) and has_rejected_marker(field_value, manifest):
            add_issue(issues, "error", source_file, run_id, target_field, field, "field contains a rejected placeholder/synthetic/source marker")
            ok = False
    if not ok:
        return None

    extracted = {field: clean(plan.get(field)) for field in CSV_FIELDS}
    extracted.update({
        "value": value,
        "measured_at": measured_at,
        "operator_or_agent": operator,
        "instrument_id": instrument,
        "source_file": rel(source_file),
        "notes": notes,
    })
    return extracted


def default_values_out(profile: str) -> Path:
    config = PROFILES[profile]
    return config["csv"].with_name(config["csv"].stem.replace("_source_values", "_raw_csv_extracted_values") + ".csv")


def default_json_out(profile: str) -> Path:
    config = PROFILES[profile]
    return config["json"].with_name(config["json"].stem.replace("_source_values_sheet", "_raw_csv_value_extraction") + ".json")


def default_report(profile: str) -> Path:
    config = PROFILES[profile]
    return config["report"].with_name(config["report"].stem.replace("_source_values_sheet", "_raw_csv_value_extraction") + ".md")


def extract_values(args: argparse.Namespace) -> dict[str, Any]:
    config = PROFILES[args.profile]
    source_values = args.source_values or config["csv"]
    _fields, plan_rows = load_csv(source_values)
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
            add_issue(issues, "error", source_file, clean(plan.get("run_id")), clean(plan.get("target_field")), "source_file", "source path exists but is not a file")
            continue
        if not validate_plan_source(source_file, roots, manifest, issues, plan):
            continue
        fields, csv_rows = load_csv(source_file, delimiter=raw_delimiter(source_file))
        if not fields:
            add_issue(issues, "error", source_file, clean(plan.get("run_id")), clean(plan.get("target_field")), "header", "raw CSV/TSV has no header")
            continue
        matches = matching_rows(csv_rows, plan)
        if not matches:
            ambiguous += 1
            add_issue(issues, "error", source_file, clean(plan.get("run_id")), clean(plan.get("target_field")), "row_locator", "raw CSV/TSV has multiple rows and none match run_id and target_field")
            continue
        usable = [row for row in matches if any(clean(value) for value in row.values())]
        if len(usable) != 1:
            ambiguous += 1
            add_issue(issues, "error", source_file, clean(plan.get("run_id")), clean(plan.get("target_field")), "row_locator", f"expected exactly one nonblank matching row, found {len(usable)}")
            continue
        extracted = extract_row(plan, usable[0], source_file, manifest, issues)
        if extracted:
            extracted_rows.append(extracted)

    write_csv(args.values_out, extracted_rows)
    counts = Counter(issue["severity"] for issue in issues)
    status_prefix = config["status_prefix"].replace("_source_values", "_raw_csv_value_extraction")
    if counts.get("error", 0) and not extracted_rows:
        status = f"{status_prefix}_blocked"
    elif counts.get("error", 0):
        status = f"{status_prefix}_partial"
    elif extracted_rows:
        status = f"{status_prefix}_ready"
    else:
        status = f"{status_prefix}_no_raw_csv"

    return {
        "status": status,
        "profile": args.profile,
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
            "source_values": rel(source_values),
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
            "It writes a non-evidence source-value sidecar for the wide importer; missing files produce no synthetic rows."
        ),
    }


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    label = PROFILES[result["profile"]]["label"]
    lines = [
        f"# {label} Raw CSV Value Extraction",
        "",
        f"This extracts source-backed {label} values from existing raw CSV/TSV files. It is not measured evidence.",
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
        lines.extend(["| Run | Field | Source file |", "| --- | --- | --- |"])
        for row in result["extracted_rows"][:100]:
            lines.append(f"| `{row['run_id']}` | `{row['target_field']}` | `{row['source_file']}` |")
    else:
        lines.append("- No rows extracted.")

    lines.extend(["", "## Issues", ""])
    if result["issues"]:
        lines.extend(["| Severity | Source file | Run | Field | Message |", "| --- | --- | --- | --- | --- |"])
        for issue in result["issues"][:120]:
            lines.append(
                f"| `{issue['severity']}` | `{issue['source_file']}` | `{issue['run_id']}` | "
                f"`{issue['field']}` | {md_cell(issue['message'])} |"
            )
        if len(result["issues"]) > 120:
            lines.append(f"| `info` | `-` | `-` | `-` | {len(result['issues']) - 120} additional issues omitted. |")
    else:
        lines.append("- No extraction issues.")

    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract wide source-values from raw CSV/TSV files.")
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--source-values", type=Path)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--values-out", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--report", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.values_out = args.values_out or default_values_out(args.profile)
    args.json_out = args.json_out or default_json_out(args.profile)
    args.report = args.report or default_report(args.profile)
    result = extract_values(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps({key: value for key, value in result.items() if key != "extracted_rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"{PROFILES[args.profile]['label']} raw CSV value extraction: {result['status']}")
    print(f"Raw CSV/TSV files found: {result['summary']['raw_csv_found']}")
    print(f"Extracted rows: {result['summary']['extracted_rows']}")
    print(f"Errors: {result['summary']['error_count']}")
    print(f"Wrote {args.values_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
