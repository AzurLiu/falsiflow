#!/usr/bin/env python3
"""Regression checks for H-A vendor bundle-entry return application."""

from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path

from apply_nhi_pedot_h_a_vendor_bundle_entry_return import build_result
from render_nhi_pedot_h_a_bundle_entry_sheet import SHEET_FIELDS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_vendor_bundle_entry_return_regression.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_vendor_bundle_entry_return_regression.md"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def source_row(sample_event: str, target_field: str, wide_field: str, source_file: str) -> dict[str, str]:
    return {
        "run_id": "run_a",
        "sample_event": sample_event,
        "target_field": target_field,
        "value": "",
        "unit": "pH",
        "measured_at": "",
        "operator_or_agent": "",
        "instrument_id": "",
        "source_file": source_file,
        "notes": "",
        "route": "outsourced",
        "wide_field": wide_field,
        "instrument_class": "calibrated_pH_meter",
        "instrument_required": "true",
        "source_class": "pH_meter_export_or_photo",
        "recommended_source_file": source_file,
        "source_file_exists": "false",
        "source_file_requirement": "Meter export.",
        "review_status": "awaiting_value_entry",
        "missing_items": "value;measured_at;operator_or_agent;instrument_id;source_file_missing",
        "capture_instruction": "fixture",
    }


def args_for(
    sheet: Path,
    bundle_manifest: Path,
    source_values: Path,
    source_manifest: Path,
    json_out: Path,
    report: Path,
) -> argparse.Namespace:
    return argparse.Namespace(
        sheet=sheet,
        bundle_manifest=bundle_manifest,
        source_values=source_values,
        source_manifest=source_manifest,
        json_out=json_out,
        report=report,
    )


def run_case() -> dict:
    with tempfile.TemporaryDirectory(prefix="nhi_h_a_vendor_bundle_entry_return_") as tmp:
        base = Path(tmp)
        return_dir = base / "vendor_return"
        export = return_dir / "external_lab_exports" / "run_a" / "pH_export.csv"
        sheet = return_dir / "completed_bundle_entry_sheet.csv"
        bundle_manifest = base / "bundle_manifest.csv"
        source_values = base / "source_values.csv"
        source_manifest = base / "manifest.json"
        source_fields = [
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
            "route",
            "wide_field",
            "instrument_class",
            "instrument_required",
            "source_class",
            "recommended_source_file",
            "source_file_exists",
            "source_file_requirement",
            "review_status",
            "missing_items",
            "capture_instruction",
        ]
        write_json(source_manifest, {"allowed_roots": [{"path": str(return_dir / "external_lab_exports")}]})
        write_csv(bundle_manifest, [
            "bundle_id",
            "priority",
            "run_id",
            "article_id",
            "timepoint",
            "source_class",
            "consolidated_source_file",
            "target_fields",
            "source_value_rows",
            "instrument_required",
            "source_file_requirement",
            "existing_source_file",
            "allowed_source_file",
            "operator_action",
        ], [{
            "bundle_id": "H-A-BUNDLE-001",
            "priority": "2",
            "run_id": "run_a",
            "article_id": "fixture",
            "timepoint": "0h",
            "source_class": "pH_meter_export_or_photo",
            "consolidated_source_file": str(export),
            "target_fields": "pH",
            "source_value_rows": "2",
            "instrument_required": "true",
            "source_file_requirement": "Meter export.",
            "existing_source_file": "false",
            "allowed_source_file": "true",
            "operator_action": "fixture",
        }])
        write_csv(source_values, source_fields, [
            source_row("initial", "pH", "pH_initial", "external_lab_exports/run_a/pH_export.csv"),
            source_row("final", "pH", "pH_final", "external_lab_exports/run_a/pH_export.csv"),
        ])

        no_sheet = build_result(args_for(
            sheet,
            bundle_manifest,
            source_values,
            source_manifest,
            base / "no_sheet.json",
            base / "no_sheet.md",
        ))
        unchanged_after_no_sheet = all(row["value"] == "" for row in load_rows(source_values))

        export.parent.mkdir(parents=True, exist_ok=True)
        write_csv(export, ["value", "measured_at", "operator_or_agent", "instrument_id"], [{
            "value": "7.20",
            "measured_at": "2026-05-24T11:00:00+08:00",
            "operator_or_agent": "regression",
            "instrument_id": "pH-1",
        }])
        write_csv(sheet, SHEET_FIELDS, [{
            "bundle_id": "H-A-BUNDLE-001",
            "apply": "yes",
            "source_file": "external_lab_exports/run_a/pH_export.csv",
            "measured_at": "2026-05-24T11:00:00+08:00",
            "operator_or_agent": "regression",
            "instrument_id": "pH-1",
            "notes": "vendor return record",
            "value_pH_initial": "7.20",
            "value_pH_final": "7.05",
        }])
        applied = build_result(args_for(
            sheet,
            bundle_manifest,
            source_values,
            source_manifest,
            base / "applied.json",
            base / "applied.md",
        ))
        applied_rows = load_rows(source_values)

    checks = {
        "missing_sheet_waits_without_mutation": (
            no_sheet["status"] == "h_a_vendor_bundle_entry_return_waiting_for_sheet"
            and unchanged_after_no_sheet
        ),
        "valid_return_sheet_applies": (
            applied["status"] == "h_a_vendor_bundle_entry_return_applied"
            and applied["summary"]["applied_source_value_rows"] == 2
        ),
        "valid_return_sheet_marks_source_values_import_ready": (
            [row["value"] for row in applied_rows] == ["7.20", "7.05"]
            and all(row["review_status"] == "import_ready" for row in applied_rows)
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "no_sheet_status": no_sheet["status"],
        "applied_status": applied["status"],
        "applied_issues": applied.get("issues", [])[:20],
    }


def render_report(result: dict) -> str:
    lines = [
        "# NHI-PEDOT H-A Vendor Bundle Entry Return Regression",
        "",
        f"**Status:** `{result['status']}`",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{key}`: {str(value).lower()}" for key, value in result["checks"].items())
    lines.extend([
        "",
        "## Boundary",
        "",
        "This regression uses temporary CSV fixtures only. It does not create material evidence.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    result = run_case()
    write_json(DEFAULT_JSON, result)
    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text(render_report(result), encoding="utf-8")
    print(f"NHI-PEDOT H-A vendor bundle-entry return regression: {result['status']}")
    print(f"Wrote {DEFAULT_JSON}")
    print(f"Wrote {DEFAULT_REPORT}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
