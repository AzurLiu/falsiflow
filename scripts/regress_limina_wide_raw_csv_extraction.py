#!/usr/bin/env python3
"""Regression checks for wide raw CSV value extraction."""

from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path

from extract_limina_wide_raw_csv_values import extract_values


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_wide_raw_csv_extraction_regression.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_wide_raw_csv_extraction_regression.md"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def args_for(base: Path, source_values: Path, values_out: Path) -> argparse.Namespace:
    manifest = base / "manifest.json"
    write_json(manifest, {
        "allowed_roots": [{"path": str(base / "source_files")}],
        "rejected_source_markers": ["synthetic_fixture_not_material_evidence"],
    })
    return argparse.Namespace(
        profile="zrc_phase_a",
        source_values=source_values,
        source_manifest=manifest,
        values_out=values_out,
        json_out=base / "result.json",
        report=base / "result.md",
    )


def source_row(source_file: Path, target_field: str = "pH_initial") -> dict[str, str]:
    return {
        "profile": "zrc_phase_a",
        "run_id": "run_a",
        "phase": "A",
        "timepoint": "0 h",
        "replicate": "1",
        "article_id": "article_a",
        "target_field": target_field,
        "unit": "pH" if target_field == "pH_initial" else "",
        "source_file": str(source_file),
        "source_class": "pH_meter_export_or_photo",
    }


def run_case() -> dict:
    with tempfile.TemporaryDirectory(prefix="limina_wide_raw_csv_extraction_") as tmp:
        base = Path(tmp)
        source_dir = base / "source_files" / "full" / "zrc_phase_a"
        raw = source_dir / "run_a_ph.csv"
        raw.parent.mkdir(parents=True, exist_ok=True)

        no_raw_values = base / "no_raw_source_values.csv"
        write_csv(no_raw_values, ["profile", "run_id", "phase", "timepoint", "replicate", "article_id", "target_field", "unit", "source_file", "source_class"], [
            source_row(source_dir / "missing.csv")
        ])
        no_raw = extract_values(args_for(base, no_raw_values, base / "no_raw_out.csv"))

        source_values = base / "source_values.csv"
        write_csv(raw, ["value", "measured_at", "operator_or_agent", "pH_meter_id"], [{
            "value": "7.18",
            "measured_at": "2026-05-24T11:00:00+08:00",
            "operator_or_agent": "regression",
            "pH_meter_id": "ph-meter-1",
        }])
        write_csv(source_values, ["profile", "run_id", "phase", "timepoint", "replicate", "article_id", "target_field", "unit", "source_file", "source_class"], [
            source_row(raw)
        ])
        extracted = extract_values(args_for(base, source_values, base / "extracted.csv"))

        write_csv(raw, ["run_id", "target_field", "value", "measured_at", "operator_or_agent", "pH_meter_id"], [
            {
                "run_id": "run_a",
                "target_field": "pH_initial",
                "value": "synthetic_fixture_not_material_evidence",
                "measured_at": "2026-05-24T11:00:00+08:00",
                "operator_or_agent": "regression",
                "pH_meter_id": "ph-meter-1",
            }
        ])
        rejected = extract_values(args_for(base, source_values, base / "rejected.csv"))

    checks = {
        "missing_raw_csv_is_not_synthetic": (
            no_raw["status"] == "zrc_nd_phase_a_raw_csv_value_extraction_no_raw_csv"
            and no_raw["summary"]["extracted_rows"] == 0
        ),
        "valid_raw_csv_extracts_one_row": (
            extracted["status"] == "zrc_nd_phase_a_raw_csv_value_extraction_ready"
            and extracted["summary"]["extracted_rows"] == 1
            and extracted["extracted_rows"][0]["value"] == "7.18"
        ),
        "placeholder_value_rejected": (
            rejected["status"] == "zrc_nd_phase_a_raw_csv_value_extraction_blocked"
            and rejected["summary"]["error_count"] == 1
            and rejected["summary"]["extracted_rows"] == 0
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "no_raw_status": no_raw["status"],
        "extracted_status": extracted["status"],
        "rejected_status": rejected["status"],
    }


def render_report(result: dict) -> str:
    lines = [
        "# LIMINA Wide Raw CSV Extraction Regression",
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
    print(f"LIMINA wide raw CSV extraction regression: {result['status']}")
    print(f"Wrote {DEFAULT_JSON}")
    print(f"Wrote {DEFAULT_REPORT}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
