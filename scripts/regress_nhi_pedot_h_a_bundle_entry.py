#!/usr/bin/env python3
"""Regression checks for H-A bundle entry rendering and application."""

from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path

from apply_nhi_pedot_h_a_bundle_entry_sheet import apply_entries
from render_nhi_pedot_h_a_bundle_entry_sheet import SHEET_FIELDS, build_sheet


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_bundle_entry_regression.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_bundle_entry_regression.md"


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
        "route": "inhouse_ready",
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
    bundle_manifest: Path,
    source_values: Path,
    sheet: Path,
    manifest: Path,
    json_out: Path,
    report: Path,
) -> argparse.Namespace:
    return argparse.Namespace(
        bundle_manifest=bundle_manifest,
        source_values=source_values,
        sheet=sheet,
        source_manifest=manifest,
        json_out=json_out,
        report=report,
    )


def run_case() -> dict:
    with tempfile.TemporaryDirectory(prefix="nhi_h_a_bundle_entry_") as tmp:
        base = Path(tmp)
        source_file = base / "source_files" / "full" / "h_a" / "run_a" / "pH_export.csv"
        bundle_manifest = base / "bundle_manifest.csv"
        source_values = base / "source_values.csv"
        sheet = base / "bundle_entry.csv"
        manifest = base / "manifest.json"
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
        write_json(manifest, {"allowed_roots": [{"path": str(base / "source_files")}]})
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
            "consolidated_source_file": str(source_file),
            "target_fields": "pH",
            "source_value_rows": "2",
            "instrument_required": "true",
            "source_file_requirement": "Meter export.",
            "existing_source_file": "false",
            "allowed_source_file": "true",
            "operator_action": "fixture",
        }])
        write_csv(source_values, source_fields, [
            source_row("initial", "pH", "pH_initial", str(source_file)),
            source_row("final", "pH", "pH_final", str(source_file)),
        ])

        render_args = args_for(bundle_manifest, source_values, sheet, manifest, base / "render.json", base / "render.md")
        rendered = build_sheet(render_args)
        write_csv(sheet, SHEET_FIELDS, [{
            **rendered["rows"][0],
            "apply": "",
        }])
        before = source_values.read_text(encoding="utf-8")
        no_apply = apply_entries(args_for(bundle_manifest, source_values, sheet, manifest, base / "no_apply.json", base / "no_apply.md"))
        unchanged_after_no_apply = source_values.read_text(encoding="utf-8") == before

        source_file.parent.mkdir(parents=True, exist_ok=True)
        write_csv(source_file, ["value", "measured_at", "operator_or_agent", "instrument_id"], [{
            "value": "7.20",
            "measured_at": "2026-05-24T11:00:00+08:00",
            "operator_or_agent": "regression",
            "instrument_id": "pH-1",
        }])
        entry = rendered["rows"][0]
        entry.update({
            "apply": "yes",
            "measured_at": "2026-05-24T11:00:00+08:00",
            "operator_or_agent": "regression",
            "instrument_id": "pH-1",
            "source_file": str(source_file),
            "value_pH_initial": "7.20",
            "value_pH_final": "7.05",
        })
        write_csv(sheet, SHEET_FIELDS, [entry])
        applied = apply_entries(args_for(bundle_manifest, source_values, sheet, manifest, base / "applied.json", base / "applied.md"))
        applied_rows = load_rows(source_values)

    checks = {
        "rendered_one_bundle_row": rendered["summary"]["bundle_rows"] == 1,
        "rendered_initial_and_final_value_columns": rendered["rows"][0]["target_value_columns"] == "value_pH_initial;value_pH_final",
        "no_apply_does_not_mutate_source_values": (
            no_apply["status"] == "h_a_bundle_entry_apply_no_apply_rows"
            and unchanged_after_no_apply
        ),
        "valid_bundle_updates_two_source_rows": (
            applied["status"] == "h_a_bundle_entry_apply_applied"
            and applied["summary"]["applied_source_value_rows"] == 2
            and [row["value"] for row in applied_rows] == ["7.20", "7.05"]
            and all(row["review_status"] == "import_ready" for row in applied_rows)
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "no_apply_status": no_apply["status"],
        "applied_status": applied["status"],
    }


def render_report(result: dict) -> str:
    lines = [
        "# NHI-PEDOT H-A Bundle Entry Regression",
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
    print(f"NHI-PEDOT H-A bundle entry regression: {result['status']}")
    print(f"Wrote {DEFAULT_JSON}")
    print(f"Wrote {DEFAULT_REPORT}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
