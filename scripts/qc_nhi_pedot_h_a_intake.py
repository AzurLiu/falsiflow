#!/usr/bin/env python3
"""Quality-control NHI-PEDOT H-A rows before gate interpretation."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS, provenance
from interpret_nhi_pedot_h_a_sentinel import (
    EXPECTED_ARTICLES,
    EXPECTED_TIMEPOINTS,
    MATERIAL_ARTICLES,
    NO_COATING_CONTROL,
    PHASE,
    REQUIRED_FIELDS,
    missing_expected_rows,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS = ROOT / "data" / "nhi_pedot_h_a_sentinel_template.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_intake_qc.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_intake_qc.md"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BOOL_FIELDS = {"visible_precipitate", "visible_shedding"}
BOOL_VALUES = {"true", "false", "yes", "no", "1", "0", "y", "n"}
NUMERIC_RULES = {
    "temperature_c": (15.0, 45.0, "warning"),
    "pH_initial": (6.5, 8.2, "warning"),
    "pH_final": (6.5, 8.2, "warning"),
    "osmolality_initial_mOsm_kg": (200.0, 420.0, "warning"),
    "osmolality_final_mOsm_kg": (200.0, 420.0, "warning"),
    "conductivity_initial_mS_cm": (1.0, 30.0, "warning"),
    "conductivity_final_mS_cm": (1.0, 30.0, "warning"),
    "swelling_fraction": (-0.5, 2.0, "error"),
    "delamination_score": (0.0, 5.0, "error"),
    "optical_transparency_fraction": (0.0, 1.0, "error"),
}
RECOMMENDED_PROVENANCE_FIELDS = [
    "date",
    "operator_or_agent",
    "mea_coupon_id",
    "electrode_material",
    "medium_name",
    "medium_lot",
    "temperature_c",
]
SOURCE_SPLIT_CHARS = [";", "|", "\n"]


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def value(row: dict[str, str], field: str) -> str:
    return str(row.get(field, "")).strip()


def is_placeholder(raw: str) -> bool:
    lowered = raw.lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def is_synthetic(raw: str) -> bool:
    lowered = raw.lower()
    return any(marker in lowered for marker in SYNTHETIC_MARKERS)


def split_source_files(raw: str) -> list[str]:
    refs = [raw.strip().strip("\"'")]
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
        raw = value(row, "path")
        if not raw:
            continue
        path = Path(raw)
        if not path.is_absolute():
            path = ROOT / path
        roots.append(path)
    return roots


def has_rejected_source_marker(raw: str, manifest: dict[str, Any]) -> bool:
    markers = set(PLACEHOLDER_MARKERS) | set(SYNTHETIC_MARKERS)
    markers.update(value({"item": item}, "item").lower() for item in manifest.get("rejected_source_markers", []) if value({"item": item}, "item"))
    lowered = raw.lower()
    return any(marker in lowered for marker in markers)


def parse_float(raw: str) -> float | None:
    if raw == "":
        return None
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


def h_a_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if value(row, "phase") == PHASE and value(row, "run_id")]


def row_label(row: dict[str, str], index: int) -> str:
    return value(row, "run_id") or f"row_{index}"


def add_issue(
    issues: list[dict[str, str]],
    severity: str,
    run_id: str,
    field: str,
    message: str,
) -> None:
    issues.append({
        "severity": severity,
        "run_id": run_id,
        "field": field,
        "message": message,
    })


def check_row_shape(row: dict[str, str], index: int, issues: list[dict[str, str]]) -> None:
    run_id = row_label(row, index)
    for field in REQUIRED_FIELDS:
        raw = value(row, field)
        if raw == "":
            add_issue(issues, "error", run_id, field, "required field is blank")
        elif is_placeholder(raw):
            add_issue(issues, "error", run_id, field, "field still contains a placeholder marker")
        elif is_synthetic(raw):
            add_issue(issues, "error", run_id, field, "field contains a synthetic/fixture marker")

    for field in RECOMMENDED_PROVENANCE_FIELDS:
        if field in REQUIRED_FIELDS:
            continue
        if field in row and value(row, field) == "":
            add_issue(issues, "warning", run_id, field, "recommended provenance field is blank")

    raw_date = value(row, "date")
    if raw_date and not valid_iso_date(raw_date):
        add_issue(issues, "error", run_id, "date", "date must use YYYY-MM-DD")

    for field in BOOL_FIELDS:
        raw = value(row, field).lower()
        if raw and raw not in BOOL_VALUES:
            add_issue(issues, "error", run_id, field, "boolean field must be true/false, yes/no, 1/0, or y/n")

    for field, (lower, upper, severity) in NUMERIC_RULES.items():
        raw = value(row, field)
        if raw == "":
            continue
        parsed = parse_float(raw)
        if parsed is None:
            add_issue(issues, "error", run_id, field, "numeric field is not parseable")
            continue
        if parsed < lower or parsed > upper:
            add_issue(
                issues,
                severity,
                run_id,
                field,
                f"value {parsed:g} is outside expected intake range [{lower:g}, {upper:g}]",
            )


def check_expected_rows(rows: list[dict[str, str]], issues: list[dict[str, str]]) -> None:
    missing = missing_expected_rows(rows)
    for key in missing:
        add_issue(issues, "error", key, "expected_row", "expected H-A sentinel row is missing")


def check_controls(rows: list[dict[str, str]], issues: list[dict[str, str]]) -> None:
    keys = {
        (
            value(row, "phase"),
            value(row, "timepoint"),
            value(row, "replicate"),
            value(row, "article_id"),
        )
        for row in rows
    }
    for index, row in enumerate(rows, start=1):
        if value(row, "article_id") not in MATERIAL_ARTICLES:
            continue
        control_key = (PHASE, value(row, "timepoint"), value(row, "replicate"), NO_COATING_CONTROL)
        if control_key not in keys:
            add_issue(
                issues,
                "error",
                row_label(row, index),
                "control_article_id",
                f"matched {NO_COATING_CONTROL} row is missing for timepoint/replicate",
            )


def check_medium_lot_consistency(rows: list[dict[str, str]], issues: list[dict[str, str]]) -> None:
    lots_by_timepoint: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        lot = value(row, "medium_lot")
        if not lot or is_placeholder(lot):
            continue
        key = (value(row, "timepoint"), value(row, "replicate"))
        lots_by_timepoint.setdefault(key, set()).add(lot)
    for (timepoint, replicate), lots in sorted(lots_by_timepoint.items()):
        if len(lots) > 1:
            add_issue(
                issues,
                "warning",
                f"{PHASE}|{timepoint}|R{replicate}",
                "medium_lot",
                "multiple medium lots in matched comparison set; verify this was intentional",
            )


def check_source_files(rows: list[dict[str, str]], manifest: dict[str, Any], issues: list[dict[str, str]]) -> None:
    roots = allowed_roots(manifest)
    for index, row in enumerate(rows, start=1):
        run_id = row_label(row, index)
        refs = split_source_files(value(row, "source_file"))
        if not refs:
            continue
        for ref in refs:
            if has_rejected_source_marker(ref, manifest):
                add_issue(issues, "error", run_id, "source_file", f"source_file `{ref}` contains a rejected marker")
                continue
            path = resolve_path(ref)
            if not path.exists():
                add_issue(issues, "error", run_id, "source_file", f"source_file `{ref}` does not exist")
                continue
            if not path.is_file():
                add_issue(issues, "error", run_id, "source_file", f"source_file `{ref}` is not a concrete file")
                continue
            if not roots:
                add_issue(issues, "error", run_id, "source_file", "source manifest has no allowed roots")
                continue
            if not any(path_is_within(path, root) for root in roots):
                add_issue(issues, "error", run_id, "source_file", f"source_file `{ref}` is outside allowed roots")


def summarize_issues(issues: list[dict[str, str]]) -> dict[str, int]:
    counts = {"error": 0, "warning": 0}
    for issue in issues:
        if issue["severity"] in counts:
            counts[issue["severity"]] += 1
    return counts


def build_qc(rows: list[dict[str, str]], path: Path, source_manifest: Path = DEFAULT_SOURCE_MANIFEST) -> dict[str, Any]:
    selected = h_a_rows(rows)
    manifest = load_json(source_manifest)
    issues: list[dict[str, str]] = []
    for index, row in enumerate(selected, start=1):
        check_row_shape(row, index, issues)
    check_expected_rows(selected, issues)
    check_controls(selected, issues)
    check_medium_lot_consistency(selected, issues)
    check_source_files(selected, manifest, issues)
    counts = summarize_issues(issues)
    source = provenance(path)
    intake_ready = (
        counts["error"] == 0
        and source.get("claimable_measurement_source") is True
        and source.get("measured_row_count") == source.get("row_count")
        and source.get("row_count", 0) >= len(EXPECTED_ARTICLES) * len(EXPECTED_TIMEPOINTS)
    )
    status = "h_a_intake_ready" if intake_ready else "h_a_intake_not_ready"
    return {
        "status": status,
        "intake_ready": intake_ready,
        "runs_path": str(path),
        "source_manifest": str(source_manifest),
        "row_count": len(selected),
        "expected_row_count": len(EXPECTED_ARTICLES) * len(EXPECTED_TIMEPOINTS),
        "issue_counts": counts,
        "issues": issues,
        "provenance": source,
        "next_action": (
            "Run interpret_nhi_pedot_h_a_sentinel.py."
            if intake_ready
            else "Resolve QC errors, remove placeholders, and enter real measured provenance before interpretation."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# NHI-PEDOT H-A Intake QC",
        "",
        "This checks whether H-A rows are suitable for gate interpretation. It does not judge material suitability.",
        "",
        f"**Input:** `{result['runs_path']}`",
        f"**Status:** `{result['status']}`",
        f"**Intake ready:** `{result['intake_ready']}`",
        f"**Rows:** {result['row_count']} / expected {result['expected_row_count']}",
        f"**Errors:** {result['issue_counts']['error']}",
        f"**Warnings:** {result['issue_counts']['warning']}",
        f"**Next action:** {result['next_action']}",
        "",
        "## Provenance",
        "",
        f"- Measured rows: {result['provenance'].get('measured_row_count', 0)}",
        f"- Placeholder rows: {result['provenance'].get('placeholder_row_count', 0)}",
        f"- Synthetic rows: {result['provenance'].get('synthetic_row_count', 0)}",
        f"- Claimable measurement source: `{result['provenance'].get('claimable_measurement_source')}`",
        "",
        "## Issues",
        "",
    ]
    issues = result.get("issues", [])
    if not issues:
        lines.append("No QC issues found.")
        lines.append("")
        return "\n".join(lines)

    lines.extend([
        "| Severity | Run | Field | Message |",
        "| --- | --- | --- | --- |",
    ])
    for issue in issues[:80]:
        lines.append(
            f"| `{issue['severity']}` | `{issue['run_id']}` | `{issue['field']}` | {issue['message']} |"
        )
    if len(issues) > 80:
        lines.append(f"| `info` | `-` | `-` | {len(issues) - 80} additional issues omitted from report. |")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QC NHI-PEDOT H-A intake rows.")
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--strict-exit",
        action="store_true",
        help="Return non-zero when intake is not ready. Default writes reports and exits 0.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_qc(load_csv(args.runs), args.runs, args.source_manifest)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A intake QC: {result['status']}")
    print(f"Errors: {result['issue_counts']['error']}")
    print(f"Warnings: {result['issue_counts']['warning']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    if args.strict_exit and not result["intake_ready"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
