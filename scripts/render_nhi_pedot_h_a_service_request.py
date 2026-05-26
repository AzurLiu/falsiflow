#!/usr/bin/env python3
"""Render a vendor/cooperator service request for real NHI-PEDOT H-A measurements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKLIST = ROOT / "data" / "nhi_pedot_h_a_minimum_measurement_checklist.json"
DEFAULT_BENCH = ROOT / "data" / "nhi_pedot_h_a_bench_sheet.json"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_service_request.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_service_request.md"

CORE_DELIVERABLES = [
    {
        "id": "raw_measurement_csv",
        "name": "Completed long-form raw measurement CSV",
        "acceptance": "All 228 raw entries have values, measured_at, operator_or_agent, instrument_id, source_file, and notes when relevant.",
        "target_path": "data/nhi_pedot_h_a_raw_measurements_template.csv",
    },
    {
        "id": "bundle_entry_sheet",
        "name": "Completed one-row-per-source-file bundle entry sheet",
        "acceptance": "Preferred compact return path: fill one row per raw-file bundle, set apply=yes, and cite the returned source file for each bundle.",
        "target_path": "data/nhi_pedot_h_a_vendor_return_inbox/completed_bundle_entry_sheet.csv",
    },
    {
        "id": "sample_chain_of_custody",
        "name": "Sample/coupon chain of custody",
        "acceptance": "Each coupon/well maps to one run_id, sample_id, container ID, article_id, timepoint, replicate, medium lot, and preparation batch.",
        "target_path": "data/nhi_pedot_h_a_chain_of_custody.csv",
    },
    {
        "id": "instrument_export_bundle",
        "name": "Instrument exports and images",
        "acceptance": "Raw pH, osmolality, conductivity, and imaging/inspection exports are preserved with file names referenced in source_file.",
        "target_path": "external_lab_exports/",
    },
    {
        "id": "deviation_log",
        "name": "Deviation log",
        "acceptance": "Any substitution in medium, electrode coupon, hydrogel batch, incubation time, temperature, or instrument calibration is listed explicitly.",
        "target_path": "reports/nhi_pedot_h_a_deviation_log.md",
    },
]

REQUIRED_CAPABILITIES = [
    "Acellular soak/incubation of MEA witness coupons or equivalent electrode-window coupons at 37 C.",
    "pH measurement before and after each timepoint.",
    "Osmolality measurement before and after each timepoint.",
    "Conductivity measurement before and after each timepoint.",
    "Brightfield or stereoscope imaging sufficient to score shedding, delamination, swelling, and transparency.",
    "Lot-level provenance for medium, hydrogel reagents, electrode coupons, laminin or peptide source, and sterilization/aseptic handling.",
]

REJECTION_RULES = [
    "Do not replace missing values with pending, record_actual, TBD, unknown, synthetic, fixture, or not_evidence markers.",
    "Do not average across coupons before data entry; enter one row per run_id/sample_event/target_field.",
    "Do not omit no-coating controls; matched controls are required for pH, osmolality, and conductivity drift decisions.",
    "Do not interpret H-A as a suitability claim; it only authorizes or blocks H-B/H-C follow-up.",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def field_rows(checklist: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(checklist.get("required_fields", []), key=lambda item: item.get("field", ""))


def build_request(checklist: dict[str, Any], bench: dict[str, Any]) -> dict[str, Any]:
    tasks = bench.get("tasks", [])
    articles = checklist.get("articles", [])
    timepoints = unique([task.get("timepoint", "") for task in tasks])
    article_ids = [article.get("article_id", "") for article in articles]
    stop_rules = [
        {
            "article_id": article.get("article_id", ""),
            "role": article.get("article_role", ""),
            "stop_if": article.get("stop_if", ""),
            "acceptance_focus": article.get("acceptance_focus", ""),
        }
        for article in articles
    ]
    return {
        "status": "ready_to_request_real_measurements",
        "purpose": "Turn the current H-A blocker into a compact service request for real acellular measurements.",
        "active_candidate": "limina_alg_lam_pedot_lowdose_v0_2",
        "non_claim_boundary": checklist.get("non_claim_boundary", ""),
        "requested_matrix": {
            "runs": len(tasks),
            "articles": article_ids,
            "timepoints": timepoints,
            "raw_entries": bench.get("blank_raw_entries_to_fill", checklist.get("blank_raw_entries_to_fill", 0)),
            "replicates": unique([task.get("replicate", "") for task in tasks]),
        },
        "required_capabilities": REQUIRED_CAPABILITIES,
        "deliverables": CORE_DELIVERABLES,
        "required_fields": field_rows(checklist),
        "provenance_fields_per_raw_row": checklist.get("provenance_fields_per_raw_row", []),
        "stop_rules": stop_rules,
        "rejection_rules": REJECTION_RULES,
        "current_qc": {
            "status": checklist.get("qc_status", "unknown"),
            "errors": checklist.get("qc_error_count", 0),
            "warnings": checklist.get("qc_warning_count", 0),
            "missing_hotspots": checklist.get("qc_missing_hotspots", []),
        },
        "source_artifacts": {
            "raw_measurement_template": checklist.get("raw_measurement_template"),
            "internal_bundle_entry_sheet": "data/nhi_pedot_h_a_bundle_entry_sheet.csv",
            "vendor_bundle_entry_sheet": "data/nhi_pedot_h_a_vendor_return_inbox/completed_bundle_entry_sheet.csv",
            "vendor_bundle_entry_report": "reports/nhi_pedot_h_a_vendor_bundle_entry_sheet.md",
            "source_unlock_bundle_manifest": "data/nhi_pedot_h_a_source_unlock_bundle_manifest.csv",
            "active_runs": checklist.get("active_runs"),
            "bench_sheet": str(DEFAULT_BENCH.relative_to(ROOT)),
            "minimum_checklist": str(DEFAULT_CHECKLIST.relative_to(ROOT)),
        },
        "post_delivery_commands": [
            "python3 scripts/render_nhi_pedot_h_a_vendor_return_intake.py",
            "python3 scripts/render_nhi_pedot_h_a_vendor_bundle_entry_sheet.py",
            "python3 scripts/apply_nhi_pedot_h_a_vendor_bundle_entry_return.py --sheet data/nhi_pedot_h_a_vendor_return_inbox/completed_bundle_entry_sheet.csv",
            "python3 scripts/import_nhi_pedot_h_a_source_values.py",
            "python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py",
            "python3 scripts/qc_nhi_pedot_h_a_intake.py --strict-exit",
            "python3 scripts/interpret_nhi_pedot_h_a_sentinel.py",
            "python3 scripts/audit_limina_suitability_claim.py",
        ],
    }


def render_report(result: dict[str, Any]) -> str:
    matrix = result["requested_matrix"]
    qc = result["current_qc"]
    lines = [
        "# NHI-PEDOT H-A Real-Measurement Service Request",
        "",
        "This packet is written for an external lab, collaborator, or bench operator. It requests real acellular H-A measurements only; it is not a suitability claim.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result['active_candidate']}`",
        f"**Runs:** {matrix['runs']}",
        f"**Raw entries requested:** {matrix['raw_entries']}",
        f"**Current QC:** `{qc['status']}`; errors={qc['errors']}; warnings={qc['warnings']}",
        "",
        "## Requested Matrix",
        "",
        f"- Articles: {', '.join(f'`{item}`' for item in matrix['articles'])}",
        f"- Timepoints: {', '.join(matrix['timepoints'])}",
        f"- Replicates: {', '.join(matrix['replicates'])}",
        "",
        "## Required Capabilities",
        "",
    ]
    lines.extend(f"- {item}" for item in result["required_capabilities"])
    lines.extend([
        "",
        "## Deliverables",
        "",
        "| Deliverable | Acceptance | Target artifact |",
        "| --- | --- | --- |",
    ])
    for item in result["deliverables"]:
        lines.append(f"| {item['name']} | {item['acceptance']} | `{item['target_path']}` |")

    lines.extend([
        "",
        "## Required Fields",
        "",
        "| Field | Rows | Description |",
        "| --- | ---: | --- |",
    ])
    for item in result["required_fields"]:
        lines.append(f"| `{item['field']}` | {item['rows']} | {item['description']} |")

    lines.extend([
        "",
        "## Stop Rules",
        "",
        "| Article | Role | Stop or branch condition |",
        "| --- | --- | --- |",
    ])
    for item in result["stop_rules"]:
        lines.append(f"| `{item['article_id']}` | {item['role']} | {item['stop_if']} |")

    lines.extend([
        "",
        "## Rejection Rules",
        "",
    ])
    lines.extend(f"- {item}" for item in result["rejection_rules"])

    lines.extend([
        "",
        "## Source Artifacts",
        "",
    ])
    for label, path in result["source_artifacts"].items():
        lines.append(f"- {label}: `{path}`")

    lines.extend([
        "",
        "## After Delivery",
        "",
        "Run these commands after the completed raw-measurement CSV is placed back into the workspace:",
        "",
        "```bash",
        *result["post_delivery_commands"],
        "```",
        "",
        "## Boundary",
        "",
        result["non_claim_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render the NHI-PEDOT H-A real-measurement service request.")
    parser.add_argument("--checklist", type=Path, default=DEFAULT_CHECKLIST)
    parser.add_argument("--bench", type=Path, default=DEFAULT_BENCH)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_request(load_json(args.checklist), load_json(args.bench))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Rendered H-A service request: runs={result['requested_matrix']['runs']} raw_entries={result['requested_matrix']['raw_entries']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
