#!/usr/bin/env python3
"""Regression test for filled source-value references in source-file inventory."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from audit_limina_source_file_inventory import DEFAULT_MANIFEST, build_inventory


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_source_value_inventory_regression.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_source_value_inventory_regression.md"

FIELDS = [
    "run_id",
    "sample_event",
    "target_field",
    "value",
    "unit",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "source_file",
]


def write_source_values(path: Path) -> None:
    rows = [
        {
            "run_id": "INV-REG-001",
            "sample_event": "initial",
            "target_field": "pH",
            "value": "7.2",
            "unit": "pH",
            "measured_at": "2026-05-24T00:00:00Z",
            "operator_or_agent": "inventory_regression",
            "instrument_id": "pH-meter-regression",
            "source_file": "data/source_files/full/h_a/inventory_regression/missing_pH_export.csv",
        },
        {
            "run_id": "INV-REG-002",
            "sample_event": "initial",
            "target_field": "conductivity",
            "value": "",
            "unit": "mS/cm",
            "measured_at": "",
            "operator_or_agent": "",
            "instrument_id": "",
            "source_file": "data/source_files/full/h_a/inventory_regression/blank_row_should_not_count.csv",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run_regression() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="limina_source_value_inventory_") as tmp:
        source_values = Path(tmp) / "source_values.csv"
        write_source_values(source_values)
        result = build_inventory(SimpleNamespace(
            manifest=DEFAULT_MANIFEST,
            capture_files=[],
            source_value_files=[source_values],
        ))
    summary = result["summary"]
    checks = {
        "filled_source_value_reference_count_is_one": summary.get("filled_source_value_reference_count") == 1,
        "blank_source_value_row_ignored": summary.get("source_reference_count") == 1,
        "missing_reference_detected": summary.get("missing_reference_count") == 1,
        "status_reports_missing_reference": result.get("status") == "source_file_inventory_missing_references",
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "inventory_summary": summary,
        "missing_references": result.get("missing_references", []),
        "boundary": (
            "This regression uses temporary source-value rows only. It does not create source files "
            "or measured material evidence."
        ),
    }


def render_report(result: dict[str, object]) -> str:
    checks = result["checks"]
    summary = result["inventory_summary"]
    lines = [
        "# LIMINA Source-Value Inventory Regression",
        "",
        "This verifies that filled source-value rows are inventoried and missing source files are caught.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Source references:** {summary.get('source_reference_count')}",
        f"**Filled source-value references:** {summary.get('filled_source_value_reference_count')}",
        f"**Missing references:** {summary.get('missing_reference_count')}",
        "",
        "## Checks",
        "",
        "| Check | Pass |",
        "| --- | --- |",
    ]
    for name, passed in checks.items():
        lines.append(f"| `{name}` | `{str(passed).lower()}` |")
    lines.extend(["", "## Boundary", "", str(result["boundary"]), ""])
    return "\n".join(lines)


def main() -> int:
    result = run_regression()
    DEFAULT_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text(render_report(result), encoding="utf-8")
    print(f"LIMINA source-value inventory regression: {result['status']}")
    print(f"Wrote {DEFAULT_JSON}")
    print(f"Wrote {DEFAULT_REPORT}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
