#!/usr/bin/env python3
"""Render a manifest for the ZRC-ND Phase A real-measurement package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_delivery_package_manifest.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_delivery_package_manifest.md"

PACKAGE_FILES = [
    {
        "id": "service_request",
        "path": "reports/zrc_nd_phase_a_service_request.md",
        "role": "Primary Phase A lab/cooperator request: matrix, deliverables, acceptance gate, and rejection rules.",
        "required": True,
    },
    {
        "id": "phase_a_template",
        "path": "data/zrc_nd_phase_a_sentinel_template.csv",
        "role": "The 8-row Phase A CSV to fill with real medium-integrity measurements.",
        "required": True,
    },
    {
        "id": "sentinel_packet",
        "path": "reports/zrc_nd_phase_a_sentinel_packet.md",
        "role": "Human-readable Phase A sentinel packet and gate description.",
        "required": True,
    },
    {
        "id": "sample_manifest",
        "path": "data/zrc_nd_phase_a_sentinel_sample_manifest.csv",
        "role": "Sample-level manifest tying run_id to sample_event, article, timepoint, and readouts.",
        "required": True,
    },
    {
        "id": "sample_labels",
        "path": "data/zrc_nd_phase_a_sample_labels.csv",
        "role": "Printable/transferable labels with sample IDs, planned container IDs, article IDs, and handling notes.",
        "required": True,
    },
    {
        "id": "chain_of_custody_csv",
        "path": "data/zrc_nd_phase_a_chain_of_custody.csv",
        "role": "Blank chain-of-custody transfer rows to complete during preparation, release, receipt, and return.",
        "required": True,
    },
    {
        "id": "chain_of_custody_report",
        "path": "reports/zrc_nd_phase_a_chain_of_custody.md",
        "role": "Human-readable sample handoff instructions, blank fields, and rejection rules.",
        "required": True,
    },
    {
        "id": "next_measurements",
        "path": "reports/zrc_nd_next_measurements.md",
        "role": "Current adaptive selector output showing why Phase A is the next ZRC-ND batch.",
        "required": True,
    },
    {
        "id": "validation_package",
        "path": "data/zrc_nd_3p5k_guard_validation_package.json",
        "role": "Machine-readable validation package defining articles, assays, fields, and gates.",
        "required": True,
    },
    {
        "id": "run_plan",
        "path": "reports/zrc_nd_run_plan.md",
        "role": "Full non-cell run plan context; Phase A is the current first sentinel subset.",
        "required": True,
    },
]

RETURN_FILES = [
    {
        "id": "completed_phase_a_csv",
        "path": "data/zrc_nd_phase_a_sentinel_template.csv",
        "acceptance": "Same schema as the package template, with all requested real values and provenance fields filled.",
    },
    {
        "id": "instrument_exports",
        "path": "external_lab_exports/zrc_nd_phase_a/",
        "acceptance": "Original pH, osmolality, conductivity, and inspection files reconciled to run_id or sample_id.",
    },
    {
        "id": "completed_chain_of_custody",
        "path": "data/zrc_nd_phase_a_chain_of_custody.csv",
        "acceptance": "Prepared/released/received fields, actual lot IDs, module/tube IDs, condition on receipt, and deviations filled.",
    },
    {
        "id": "deviation_log",
        "path": "reports/zrc_nd_phase_a_deviation_log.md",
        "acceptance": "Lists every deviation from membrane, module, guard, medium, timing, temperature, rinse, or instrument assumptions.",
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
        "purpose": "Manifest for the real-measurement package needed to unblock the ZRC-ND external-material Phase A sentinel.",
        "active_candidate": "limina_zrc_nd_v0_1",
        "package_files": files,
        "missing_required_file_ids": missing_required,
        "expected_return_files": RETURN_FILES,
        "post_return_verification": [
            "python3 scripts/merge_zrc_nd_measurements.py",
            "python3 scripts/interpret_zrc_nd_sentinel.py",
            "python3 scripts/evaluate_zrc_nd_validation_runs.py --runs data/zrc_nd_validation_runs_active.csv",
            "python3 scripts/suggest_zrc_nd_next_measurements.py --runs data/zrc_nd_validation_runs_active.csv",
            "python3 scripts/audit_zrc_nd_readiness.py",
            "python3 scripts/run_limina_iteration.py",
        ],
        "non_claim_boundary": "This manifest only packages the Phase A measurement request. ZRC-ND suitability still requires real Phase A/B/C rows, biological follow-up, readiness audit pass, and final claim audit.",
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# ZRC-ND Phase A Delivery Package Manifest",
        "",
        "This manifest tracks the files needed to request real acellular Phase A measurements. It is not measured evidence.",
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
    parser = argparse.ArgumentParser(description="Render ZRC-ND Phase A delivery package manifest.")
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
    print(f"ZRC-ND Phase A delivery package: {result['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "ready_to_send" else 2


if __name__ == "__main__":
    raise SystemExit(main())
