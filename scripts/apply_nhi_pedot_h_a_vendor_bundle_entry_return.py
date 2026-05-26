#!/usr/bin/env python3
"""Apply a returned H-A bundle-entry sheet from the vendor return inbox."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from apply_nhi_pedot_h_a_bundle_entry_sheet import (
    DEFAULT_BUNDLE_MANIFEST,
    DEFAULT_SOURCE_MANIFEST,
    DEFAULT_SOURCE_VALUES,
    apply_entries,
    rel,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RETURN_SHEET = ROOT / "data" / "nhi_pedot_h_a_vendor_return_inbox" / "completed_bundle_entry_sheet.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_vendor_bundle_entry_apply.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_vendor_bundle_entry_apply.md"

NON_EVIDENCE_BOUNDARY = (
    "This step only applies a returned compact bundle-entry sheet into source-value rows. "
    "The source-value importer, merge, QC, H-A interpretation, and claim audit still decide whether the rows are real evidence."
)


def status_for_apply(apply_result: dict[str, Any]) -> str:
    status = apply_result.get("status", "")
    if status == "h_a_bundle_entry_apply_applied":
        return "h_a_vendor_bundle_entry_return_applied"
    if status == "h_a_bundle_entry_apply_blocked":
        return "h_a_vendor_bundle_entry_return_blocked"
    if status == "h_a_bundle_entry_apply_no_apply_rows":
        return "h_a_vendor_bundle_entry_return_no_apply_rows"
    return "h_a_vendor_bundle_entry_return_unknown"


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    if not args.sheet.exists():
        return {
            "status": "h_a_vendor_bundle_entry_return_waiting_for_sheet",
            "summary": {
                "sheet_exists": False,
                "applied_bundles": 0,
                "applied_source_value_rows": 0,
                "error_count": 0,
                "warning_count": 0,
            },
            "inputs": {
                "sheet": rel(args.sheet),
                "bundle_manifest": rel(args.bundle_manifest),
                "source_values": rel(args.source_values),
                "source_manifest": rel(args.source_manifest),
            },
            "apply_result": {},
            "boundary": NON_EVIDENCE_BOUNDARY,
        }

    apply_args = argparse.Namespace(
        sheet=args.sheet,
        bundle_manifest=args.bundle_manifest,
        source_values=args.source_values,
        source_manifest=args.source_manifest,
        json_out=args.json_out,
        report=args.report,
    )
    apply_result = apply_entries(apply_args)
    summary = apply_result.get("summary", {})
    return {
        "status": status_for_apply(apply_result),
        "summary": {
            "sheet_exists": True,
            "applied_bundles": summary.get("applied_bundles", 0),
            "applied_source_value_rows": summary.get("applied_source_value_rows", 0),
            "skipped_apply_no_rows": summary.get("skipped_apply_no_rows", 0),
            "error_count": summary.get("error_count", 0),
            "warning_count": summary.get("warning_count", 0),
        },
        "inputs": {
            "sheet": rel(args.sheet),
            "bundle_manifest": rel(args.bundle_manifest),
            "source_values": rel(args.source_values),
            "source_manifest": rel(args.source_manifest),
        },
        "applied_bundles": apply_result.get("applied_bundles", []),
        "issues": apply_result.get("issues", []),
        "updated_source_values": apply_result.get("updated_source_values", ""),
        "apply_result_status": apply_result.get("status", ""),
        "boundary": NON_EVIDENCE_BOUNDARY,
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A Vendor Bundle Entry Apply",
        "",
        "This applies a returned compact bundle-entry sheet from the vendor return inbox. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Returned sheet:** `{result['inputs']['sheet']}`",
        f"**Sheet exists:** `{str(summary['sheet_exists']).lower()}`",
        f"**Applied bundles:** {summary['applied_bundles']}",
        f"**Applied source-value rows:** {summary['applied_source_value_rows']}",
        f"**Errors:** {summary['error_count']}",
        f"**Warnings:** {summary['warning_count']}",
        "",
        "## Applied Bundles",
        "",
    ]
    applied = result.get("applied_bundles", [])
    if not applied:
        lines.append("- No vendor bundle-entry rows applied.")
    else:
        lines.extend(["| Bundle | Run | Source class | Rows | Source file |", "| --- | --- | --- | ---: | --- |"])
        for row in applied[:80]:
            lines.append(
                f"| `{row['bundle_id']}` | `{row['run_id']}` | `{row['source_class']}` | "
                f"{row['source_value_rows']} | `{row['source_file']}` |"
            )
    issues = result.get("issues", [])
    lines.extend(["", "## Issues", ""])
    if not issues:
        lines.append("- No apply issues.")
    else:
        lines.extend(["| Severity | Bundle | Run | Source class | Field | Message |", "| --- | --- | --- | --- | --- | --- |"])
        for issue in issues[:100]:
            lines.append(
                f"| `{issue['severity']}` | `{issue['bundle_id']}` | `{issue['run_id']}` | "
                f"`{issue['source_class']}` | `{issue['field']}` | {issue['message']} |"
            )
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply returned NHI-PEDOT H-A bundle entry sheet.")
    parser.add_argument("--sheet", type=Path, default=DEFAULT_RETURN_SHEET)
    parser.add_argument("--bundle-manifest", type=Path, default=DEFAULT_BUNDLE_MANIFEST)
    parser.add_argument("--source-values", type=Path, default=DEFAULT_SOURCE_VALUES)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_result(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A vendor bundle entry return apply: {result['status']}")
    print(f"Applied bundles: {result['summary']['applied_bundles']}")
    print(f"Applied source-value rows: {result['summary']['applied_source_value_rows']}")
    print(f"Errors: {result['summary']['error_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["summary"]["error_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
