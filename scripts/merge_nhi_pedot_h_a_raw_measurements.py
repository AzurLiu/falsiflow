#!/usr/bin/env python3
"""Merge raw NHI-PEDOT H-A measurements into an active runs CSV."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS, provenance
from interpret_nhi_pedot_h_a_sentinel import REQUIRED_FIELDS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = ROOT / "data" / "nhi_pedot_h_a_sentinel_template.csv"
DEFAULT_RAW = ROOT / "data" / "nhi_pedot_h_a_raw_measurements_template.csv"
DEFAULT_OUT = ROOT / "data" / "nhi_pedot_h_a_runs_active.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_measurement_merge.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_measurement_merge.md"

RAW_FIELDS = [
    "run_id",
    "sample_event",
    "target_field",
    "value",
    "unit",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "source_file",
    "notes",
]
INITIAL_FIELDS = {
    "ph": "pH_initial",
    "p_h": "pH_initial",
    "osmolality": "osmolality_initial_mOsm_kg",
    "conductivity": "conductivity_initial_mS_cm",
}
FINAL_FIELDS = {
    "ph": "pH_final",
    "p_h": "pH_final",
    "osmolality": "osmolality_final_mOsm_kg",
    "conductivity": "conductivity_final_mS_cm",
}
DIRECT_ALIASES = {
    "pH_initial": "pH_initial",
    "pH_final": "pH_final",
    "osmolality_initial": "osmolality_initial_mOsm_kg",
    "osmolality_final": "osmolality_final_mOsm_kg",
    "conductivity_initial": "conductivity_initial_mS_cm",
    "conductivity_final": "conductivity_final_mS_cm",
}
EXPECTED_UNITS = {
    "pH_initial": {"", "ph", "pH"},
    "pH_final": {"", "ph", "pH"},
    "osmolality_initial_mOsm_kg": {"mOsm/kg", "mOsm_kg", "mOsm kg-1", "mOsm"},
    "osmolality_final_mOsm_kg": {"mOsm/kg", "mOsm_kg", "mOsm kg-1", "mOsm"},
    "conductivity_initial_mS_cm": {"mS/cm", "mS_cm", "mS cm-1"},
    "conductivity_final_mS_cm": {"mS/cm", "mS_cm", "mS cm-1"},
    "temperature_c": {"C", "degC", "celsius", ""},
    "swelling_fraction": {"fraction", "", "%"},
    "optical_transparency_fraction": {"fraction", "", "%"},
    "delamination_score": {"score", ""},
    "visible_precipitate": {"bool", "boolean", ""},
    "visible_shedding": {"bool", "boolean", ""},
}
PENDING_MARKER = "nhi_pedot_h_a_sentinel_pending_real_measurement"
MERGED_MARKER = "nhi_pedot_h_a_raw_measurements_merged"
RAW_FIXTURE_MARKER = "synthetic_fixture_raw_measurement_not_evidence"
SOURCE_SPLIT_CHARS = [";", "|", "\n"]


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(fields: list[str], rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def clean_key(value: str) -> str:
    return value.strip().replace(" ", "_")


def parse_measured_date(measured_at: str) -> str:
    raw = measured_at.strip()
    if not raw:
        return ""
    head = raw.split("T", 1)[0].split(" ", 1)[0]
    try:
        return date.fromisoformat(head).isoformat()
    except ValueError:
        return ""


def resolve_target(raw: dict[str, str], output_fields: set[str]) -> tuple[str, str]:
    target = raw.get("target_field", "").strip()
    event = raw.get("sample_event", "").strip().lower()
    if not target:
        return "", "missing target_field"
    if target in output_fields:
        return target, ""
    if target in DIRECT_ALIASES:
        return DIRECT_ALIASES[target], ""
    normalized = clean_key(target).lower()
    if event in {"initial", "baseline", "pre", "pre_soak", "pre-soak", "0h", "0_h"}:
        if normalized in INITIAL_FIELDS:
            return INITIAL_FIELDS[normalized], ""
    if event in {"final", "post", "post_soak", "post-soak", "24h", "72h"}:
        if normalized in FINAL_FIELDS:
            return FINAL_FIELDS[normalized], ""
    if normalized in INITIAL_FIELDS and not event:
        return "", f"target_field {target} needs sample_event initial/final"
    return "", f"target_field {target} does not map to an output column"


def parse_number(raw: str) -> float | None:
    try:
        return float(raw)
    except ValueError:
        return None


def normalize_value(target: str, value: str, unit: str) -> tuple[str, str]:
    raw = value.strip()
    raw_unit = unit.strip()
    if raw == "":
        return "", "blank value"
    expected = EXPECTED_UNITS.get(target)
    if expected is not None and raw_unit not in expected:
        return raw, f"unit {raw_unit or '<blank>'} is unusual for {target}"
    if target.endswith("_fraction") and raw_unit == "%":
        parsed = parse_number(raw)
        if parsed is None:
            return raw, f"value {raw} is not numeric for percent conversion"
        return f"{parsed / 100:.6g}", ""
    return raw, ""


def has_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def has_synthetic_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SYNTHETIC_MARKERS)


def split_source_files(raw: str) -> list[str]:
    refs = [raw.strip().strip("\"'")]
    for char in SOURCE_SPLIT_CHARS:
        expanded: list[str] = []
        for ref in refs:
            expanded.extend(part.strip().strip("\"'") for part in ref.split(char))
        refs = expanded
    return [ref for ref in refs if ref]


def append_source_files(row: dict[str, str], raw_source_file: str) -> bool:
    existing = split_source_files(row.get("source_file", ""))
    changed = False
    for ref in split_source_files(raw_source_file):
        if ref not in existing:
            existing.append(ref)
            changed = True
    if changed:
        row["source_file"] = ";".join(existing)
    return changed


def path_has_fixture_marker(path: Path | None) -> bool:
    if path is None:
        return False
    lowered_name = path.name.lower()
    lowered_parts = {part.lower() for part in path.parts}
    return "fixture" in lowered_name or "fixtures" in lowered_parts


def raw_row_has_synthetic_marker(raw: dict[str, str]) -> bool:
    return any(has_synthetic_marker(str(value)) for value in raw.values())


def append_note(row: dict[str, str], note: str) -> bool:
    notes = [part for part in row.get("notes", "").split(";") if part]
    if note in notes:
        return False
    notes.append(note)
    row["notes"] = ";".join(notes)
    return True


def row_has_unresolved_placeholders(row: dict[str, str], ignore_notes: bool = False) -> bool:
    for field, raw in row.items():
        if ignore_notes and field == "notes":
            continue
        value = str(raw)
        if has_placeholder(value) or has_synthetic_marker(value):
            return True
    return False


def required_fields_complete(row: dict[str, str]) -> bool:
    return all(str(row.get(field, "")).strip() for field in REQUIRED_FIELDS)


def update_notes(row: dict[str, str]) -> None:
    notes = row.get("notes", "")
    parts = [part for part in notes.split(";") if part and part != PENDING_MARKER]
    if required_fields_complete(row) and not row_has_unresolved_placeholders(row, ignore_notes=True):
        if MERGED_MARKER not in parts:
            parts.append(MERGED_MARKER)
        row["notes"] = ";".join(parts)


def apply_raw_rows(
    fields: list[str],
    base_rows: list[dict[str, str]],
    raw_rows: list[dict[str, str]],
    raw_path: Path | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    if "source_file" not in fields:
        fields = [*fields, "source_file"]
    by_id = {row.get("run_id", ""): {field: row.get(field, "") for field in fields} for row in base_rows if row.get("run_id")}
    output_fields = set(fields)
    raw_path_fixture = path_has_fixture_marker(raw_path)
    stats: dict[str, Any] = {
        "raw_rows": len(raw_rows),
        "applied_values": 0,
        "skipped_blank_values": 0,
        "skipped_missing_run_id": 0,
        "skipped_unknown_run_id": 0,
        "unresolved_targets": 0,
        "unit_warnings": 0,
        "operator_updates": 0,
        "date_updates": 0,
        "source_file_updates": 0,
        "synthetic_marker_propagations": 0,
        "issues": [],
    }
    for index, raw in enumerate(raw_rows, start=1):
        run_id = raw.get("run_id", "").strip()
        if not run_id:
            stats["skipped_missing_run_id"] += 1
            continue
        row = by_id.get(run_id)
        if row is None:
            stats["skipped_unknown_run_id"] += 1
            stats["issues"].append({
                "raw_row": index,
                "run_id": run_id,
                "severity": "error",
                "message": "run_id not present in base H-A template",
            })
            continue
        raw_is_synthetic = raw_path_fixture or raw_row_has_synthetic_marker(raw)
        if raw_is_synthetic and append_note(row, RAW_FIXTURE_MARKER):
            stats["synthetic_marker_propagations"] += 1
        target, issue = resolve_target(raw, output_fields)
        if issue:
            stats["unresolved_targets"] += 1
            stats["issues"].append({
                "raw_row": index,
                "run_id": run_id,
                "severity": "error",
                "message": issue,
            })
            continue
        normalized, unit_issue = normalize_value(target, raw.get("value", ""), raw.get("unit", ""))
        if not normalized:
            stats["skipped_blank_values"] += 1
            continue
        if unit_issue:
            stats["unit_warnings"] += 1
            stats["issues"].append({
                "raw_row": index,
                "run_id": run_id,
                "severity": "warning",
                "message": unit_issue,
            })
        row[target] = normalized
        stats["applied_values"] += 1

        operator = raw.get("operator_or_agent", "").strip()
        if operator and row.get("operator_or_agent", "") != operator:
            row["operator_or_agent"] = operator
            stats["operator_updates"] += 1

        measured_date = parse_measured_date(raw.get("measured_at", ""))
        if measured_date and not row.get("date", "").strip():
            row["date"] = measured_date
            stats["date_updates"] += 1
        if append_source_files(row, raw.get("source_file", "")):
            stats["source_file_updates"] += 1

    for row in by_id.values():
        update_notes(row)

    rows = [by_id[key] for key in sorted(by_id)]
    stats["output_rows"] = len(rows)
    return rows, stats


def raw_template_rows(base_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    template: list[dict[str, str]] = []
    metadata = [
        ("metadata", "date", ""),
        ("metadata", "medium_name", ""),
        ("metadata", "medium_lot", ""),
        ("metadata", "temperature_c", "C"),
        ("metadata", "mea_coupon_id", ""),
        ("metadata", "electrode_material", ""),
        ("metadata", "laminin_or_peptide_density", ""),
        ("metadata", "sterilization_or_aseptic_protocol", ""),
    ]
    measurements = [
        ("initial", "pH", "pH"),
        ("initial", "osmolality", "mOsm/kg"),
        ("initial", "conductivity", "mS/cm"),
        ("final", "pH", "pH"),
        ("final", "osmolality", "mOsm/kg"),
        ("final", "conductivity", "mS/cm"),
        ("physical_inspection", "visible_precipitate", "bool"),
        ("physical_inspection", "visible_shedding", "bool"),
        ("physical_inspection", "swelling_fraction", "fraction"),
        ("physical_inspection", "delamination_score", "score"),
        ("physical_inspection", "optical_transparency_fraction", "fraction"),
    ]
    for row in base_rows:
        run_id = row.get("run_id", "")
        if not run_id:
            continue
        for event, target, unit in metadata + measurements:
            template.append({
                "run_id": run_id,
                "sample_event": event,
                "target_field": target,
                "value": "",
                "unit": unit,
                "measured_at": "",
                "operator_or_agent": "",
                "instrument_id": "",
                "source_file": "",
                "notes": "",
            })
    return template


def render_report(stats: dict[str, Any], raw_path: Path, out_path: Path, source: dict[str, Any]) -> str:
    lines = [
        "# NHI-PEDOT H-A Measurement Merge",
        "",
        f"**Raw measurements:** `{raw_path}`",
        f"**Output active runs:** `{out_path}`",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Raw rows | {stats['raw_rows']} |",
        f"| Applied values | {stats['applied_values']} |",
        f"| Blank values skipped | {stats['skipped_blank_values']} |",
        f"| Missing run_id rows skipped | {stats['skipped_missing_run_id']} |",
        f"| Unknown run_id rows skipped | {stats['skipped_unknown_run_id']} |",
        f"| Unresolved targets | {stats['unresolved_targets']} |",
        f"| Unit warnings | {stats['unit_warnings']} |",
        f"| Operator updates | {stats['operator_updates']} |",
        f"| Date updates | {stats['date_updates']} |",
        f"| Source-file updates | {stats['source_file_updates']} |",
        f"| Synthetic marker propagations | {stats['synthetic_marker_propagations']} |",
        f"| Output rows | {stats['output_rows']} |",
        "",
        "## Output Provenance",
        "",
        f"- Measured rows: {source.get('measured_row_count', 0)}",
        f"- Placeholder rows: {source.get('placeholder_row_count', 0)}",
        f"- Synthetic rows: {source.get('synthetic_row_count', 0)}",
        f"- Claimable measurement source: `{source.get('claimable_measurement_source')}`",
        "",
    ]
    issues = stats.get("issues", [])
    if issues:
        lines.extend([
            "## Merge Issues",
            "",
            "| Severity | Raw row | Run | Message |",
            "| --- | ---: | --- | --- |",
        ])
        for issue in issues[:80]:
            lines.append(
                f"| `{issue['severity']}` | {issue['raw_row']} | `{issue['run_id']}` | {issue['message']} |"
            )
        if len(issues) > 80:
            lines.append(f"| `info` | - | `-` | {len(issues) - 80} additional issues omitted. |")
        lines.append("")
    lines.extend([
        "## Next Step",
        "",
        "Run intake QC on the active runs file:",
        "",
        "```bash",
        f"python3 scripts/qc_nhi_pedot_h_a_intake.py --runs {out_path}",
        "```",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge raw NHI-PEDOT H-A measurements.")
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--init-raw-template", action="store_true", help="Write a blank long-form raw measurement template.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    fields, base_rows = load_csv(args.base)
    if not fields:
        raise ValueError(f"No CSV header found in {args.base}")
    if "source_file" not in fields:
        fields = [*fields, "source_file"]

    if args.init_raw_template or not args.raw.exists():
        write_csv(RAW_FIELDS, raw_template_rows(base_rows), args.raw)

    raw_fields, raw_rows = load_csv(args.raw)
    if raw_fields and raw_fields != RAW_FIELDS:
        missing = [field for field in RAW_FIELDS if field not in raw_fields]
        if missing:
            raise ValueError(f"{args.raw} is missing raw fields: {', '.join(missing)}")

    rows, stats = apply_raw_rows(fields, base_rows, raw_rows, args.raw)
    write_csv(fields, rows, args.out)
    source = provenance(args.out)
    result = {
        "status": "merged",
        "raw_measurements": str(args.raw),
        "output_runs": str(args.out),
        "stats": stats,
        "output_provenance": source,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(stats, args.raw, args.out, source), encoding="utf-8")
    print(
        "Merged H-A raw measurements: "
        f"applied={stats['applied_values']} unresolved={stats['unresolved_targets']} "
        f"unknown_run_ids={stats['skipped_unknown_run_id']}"
    )
    print(f"Wrote {args.raw}")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
