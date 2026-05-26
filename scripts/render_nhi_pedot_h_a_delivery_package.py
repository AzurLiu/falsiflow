#!/usr/bin/env python3
"""Render a manifest for the NHI-PEDOT H-A real-measurement delivery package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_delivery_package_manifest.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_delivery_package_manifest.md"

PACKAGE_FILES = [
    {
        "id": "service_request",
        "path": "reports/nhi_pedot_h_a_service_request.md",
        "role": "Primary lab/cooperator request: matrix, deliverables, capabilities, stop rules, and rejection rules.",
        "required": True,
    },
    {
        "id": "raw_measurement_template",
        "path": "data/nhi_pedot_h_a_raw_measurements_template.csv",
        "role": "The long-form CSV to fill with real instrument and inspection values.",
        "required": True,
    },
    {
        "id": "bundle_entry_sheet",
        "path": "data/nhi_pedot_h_a_bundle_entry_sheet.csv",
        "role": "Preferred compact CSV for returning one row per raw-file bundle; it expands into the source-values sheet after validation.",
        "required": True,
    },
    {
        "id": "bundle_entry_report",
        "path": "reports/nhi_pedot_h_a_bundle_entry_sheet.md",
        "role": "Human-readable instructions for filling the compact H-A bundle entry sheet.",
        "required": True,
    },
    {
        "id": "source_unlock_bundle_manifest",
        "path": "data/nhi_pedot_h_a_source_unlock_bundle_manifest.csv",
        "role": "Machine-readable manifest mapping run_id/source_class bundles to consolidated source-file paths and target fields.",
        "required": True,
    },
    {
        "id": "source_unlock_pack",
        "path": "reports/nhi_pedot_h_a_source_unlock_pack.md",
        "role": "Human-readable overview of required H-A raw-file bundles and source classes.",
        "required": True,
    },
    {
        "id": "sentinel_packet",
        "path": "reports/nhi_pedot_h_a_sentinel_packet.md",
        "role": "Recipe-locked H-A sentinel packet and sample handling context.",
        "required": True,
    },
    {
        "id": "sample_manifest",
        "path": "data/nhi_pedot_h_a_sentinel_sample_manifest.csv",
        "role": "Sample-level manifest tying run_id to sample_event, article, timepoint, and readouts.",
        "required": True,
    },
    {
        "id": "sample_labels",
        "path": "data/nhi_pedot_h_a_sample_labels.csv",
        "role": "Printable/transferable label rows with sample IDs, planned container IDs, article IDs, and handling notes.",
        "required": True,
    },
    {
        "id": "chain_of_custody_csv",
        "path": "data/nhi_pedot_h_a_chain_of_custody.csv",
        "role": "Blank chain-of-custody transfer rows to complete during preparation, release, receipt, and return.",
        "required": True,
    },
    {
        "id": "chain_of_custody_report",
        "path": "reports/nhi_pedot_h_a_chain_of_custody.md",
        "role": "Human-readable sample handoff instructions, blank fields, and rejection rules.",
        "required": True,
    },
    {
        "id": "sample_submission_pack",
        "path": "reports/nhi_pedot_h_a_sample_submission_pack.md",
        "role": "Vendor-facing nonclinical sample-submission precheck, material disclosure, pre-ship questions, and shipping boundary.",
        "required": True,
    },
    {
        "id": "split_scope_plan",
        "path": "reports/nhi_pedot_h_a_split_scope_plan.md",
        "role": "Fallback execution plan for splitting media chemistry and coupon physical/imaging readouts across vendors.",
        "required": True,
    },
    {
        "id": "split_scope_plan_csv",
        "path": "data/nhi_pedot_h_a_split_scope_plan.csv",
        "role": "Machine-readable split-scope vendor pairings, field assignments, shared requirements, and decisions.",
        "required": True,
    },
    {
        "id": "material_disclosure_csv",
        "path": "data/nhi_pedot_h_a_material_disclosure.csv",
        "role": "Machine-readable component disclosure checklist for sample submission and SDS readiness.",
        "required": True,
    },
    {
        "id": "bench_sheet",
        "path": "reports/nhi_pedot_h_a_bench_sheet.md",
        "role": "Operator-facing bench sheet with task order and stop criteria.",
        "required": True,
    },
    {
        "id": "minimum_checklist",
        "path": "reports/nhi_pedot_h_a_minimum_measurement_checklist.md",
        "role": "Compact checklist of claim-critical fields and current QC hotspots.",
        "required": True,
    },
    {
        "id": "recipe_protocol",
        "path": "reports/nhi_pedot_alg_lam_protocol.md",
        "role": "Recipe-specific ALG-LAM-PEDOT protocol handoff.",
        "required": True,
    },
    {
        "id": "recipe_lock",
        "path": "data/nhi_pedot_recipe_lock_v0_2.json",
        "role": "Machine-readable recipe lock that defines the active lead and controls.",
        "required": True,
    },
    {
        "id": "next_measurements",
        "path": "reports/nhi_pedot_next_measurements.md",
        "role": "Current recommended H-A measurement rows.",
        "required": True,
    },
]

RETURN_FILES = [
    {
        "id": "completed_raw_measurement_csv",
        "path": "data/nhi_pedot_h_a_raw_measurements_template.csv",
        "acceptance": "Same schema as the package template, with all requested real values and provenance fields filled.",
    },
    {
        "id": "completed_bundle_entry_sheet",
        "path": "data/nhi_pedot_h_a_bundle_entry_sheet.csv",
        "acceptance": "Preferred compact return option: filled value_* columns, measured_at, operator_or_agent, instrument_id where required, source_file, and apply=yes for each completed raw-file bundle.",
    },
    {
        "id": "instrument_exports",
        "path": "external_lab_exports/",
        "acceptance": "Original pH, osmolality, conductivity, chain-of-custody, build, and image/inspection files referenced by source_file.",
    },
    {
        "id": "completed_chain_of_custody",
        "path": "data/nhi_pedot_h_a_chain_of_custody.csv",
        "acceptance": "Prepared/released/received fields, actual medium lot, coupon or well ID, condition on receipt, and transfer deviations filled for every returned sample row.",
    },
    {
        "id": "deviation_log",
        "path": "reports/nhi_pedot_h_a_deviation_log.md",
        "acceptance": "Lists every deviation from recipe, timing, instrument, sample, medium, or storage assumptions.",
    },
]


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_size(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    return path.stat().st_size


def describe_file(item: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / item["path"]
    return {
        **item,
        "exists": path.exists(),
        "bytes": file_size(path),
        "sha256": sha256(path),
    }


def build_manifest() -> dict[str, Any]:
    files = [describe_file(item) for item in PACKAGE_FILES]
    missing_required = [item["id"] for item in files if item["required"] and not item["exists"]]
    return {
        "status": "ready_to_send" if not missing_required else "missing_required_files",
        "purpose": "Manifest for the current real-measurement package needed to unblock the ALG-LAM-PEDOT H-A gate.",
        "active_candidate": "limina_alg_lam_pedot_lowdose_v0_2",
        "package_files": files,
        "missing_required_file_ids": missing_required,
        "expected_return_files": RETURN_FILES,
        "post_return_verification": [
            "python3 scripts/render_nhi_pedot_h_a_vendor_return_intake.py",
            "python3 scripts/apply_nhi_pedot_h_a_bundle_entry_sheet.py",
            "python3 scripts/import_nhi_pedot_h_a_source_values.py",
            "python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py",
            "python3 scripts/qc_nhi_pedot_h_a_intake.py --strict-exit",
            "python3 scripts/interpret_nhi_pedot_h_a_sentinel.py",
            "python3 scripts/run_limina_iteration.py",
        ],
        "non_claim_boundary": "This manifest only packages the measurement request. Suitability still requires real rows to pass H-A, H-B, H-C, long follow-up, and the final claim audit.",
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# NHI-PEDOT H-A Delivery Package Manifest",
        "",
        "This manifest tracks the files needed to request real acellular H-A measurements. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result['active_candidate']}`",
        "",
        "## Package Files",
        "",
        "| ID | Required | Exists | Bytes | SHA256 | Role | Path |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for item in result["package_files"]:
        sha = item["sha256"][:16] + "..." if item.get("sha256") else "-"
        lines.append(
            f"| `{item['id']}` | `{str(item['required']).lower()}` | "
            f"`{str(item['exists']).lower()}` | {item['bytes'] if item['bytes'] is not None else '-'} | "
            f"`{sha}` | {item['role']} | `{item['path']}` |"
        )

    lines.extend([
        "",
        "## Expected Return Files",
        "",
        "| ID | Path | Acceptance |",
        "| --- | --- | --- |",
    ])
    for item in result["expected_return_files"]:
        lines.append(f"| `{item['id']}` | `{item['path']}` | {item['acceptance']} |")

    lines.extend([
        "",
        "## Post-Return Verification",
        "",
        "```bash",
        *result["post_return_verification"],
        "```",
        "",
        "## Boundary",
        "",
        result["non_claim_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A delivery package manifest.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_manifest()
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A delivery package: {result['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "ready_to_send" else 2


if __name__ == "__main__":
    raise SystemExit(main())
