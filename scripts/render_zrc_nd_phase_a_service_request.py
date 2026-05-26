#!/usr/bin/env python3
"""Render a real-measurement service request for the ZRC-ND Phase A sentinel."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "zrc_nd_3p5k_guard_validation_package.json"
DEFAULT_NEXT = ROOT / "data" / "zrc_nd_next_measurements.json"
DEFAULT_TEMPLATE = ROOT / "data" / "zrc_nd_phase_a_sentinel_template.csv"
DEFAULT_MANIFEST = ROOT / "data" / "zrc_nd_phase_a_sentinel_sample_manifest.csv"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_service_request.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_service_request.md"

PHASE_A_REQUIRED_FIELDS = [
    {
        "field": "date",
        "rows": 8,
        "description": "Measurement date for each Phase A sentinel row.",
    },
    {
        "field": "membrane_lot",
        "rows": 6,
        "description": "Actual lot for every membrane or module-exposed article; leave blank only for no-module controls.",
    },
    {
        "field": "membrane_area_cm2",
        "rows": 6,
        "description": "Exposed membrane area for baseline, lead, and 10 kDa challenge articles.",
    },
    {
        "field": "prefilter_lot",
        "rows": 6,
        "description": "Guard prefilter lot if present, or explicit none/not_applicable when omitted.",
    },
    {
        "field": "medium_name",
        "rows": 8,
        "description": "Fresh complete neuronal medium or closest CL1-like medium proxy.",
    },
    {
        "field": "medium_lot",
        "rows": 8,
        "description": "Actual medium lot shared with control rows where possible.",
    },
    {
        "field": "initial_volume_ml",
        "rows": 8,
        "description": "Starting medium volume for normalization and drift interpretation.",
    },
    {
        "field": "exposure_time_h",
        "rows": 8,
        "description": "Actual exposure duration; must match the run timepoint within deviation-log tolerance.",
    },
    {
        "field": "temperature_c",
        "rows": 8,
        "description": "Actual incubation or measurement temperature.",
    },
    {
        "field": "pH_initial",
        "rows": 8,
        "description": "Initial pH before exposure or matched start measurement.",
    },
    {
        "field": "pH_final",
        "rows": 8,
        "description": "Final pH at the run timepoint.",
    },
    {
        "field": "osmolality_initial_mOsm_kg",
        "rows": 8,
        "description": "Initial osmolality in matched medium.",
    },
    {
        "field": "osmolality_final_mOsm_kg",
        "rows": 8,
        "description": "Final osmolality at the run timepoint.",
    },
    {
        "field": "conductivity_initial_mS_cm",
        "rows": 8,
        "description": "Initial conductivity in matched medium.",
    },
    {
        "field": "conductivity_final_mS_cm",
        "rows": 8,
        "description": "Final conductivity at the run timepoint.",
    },
    {
        "field": "visible_precipitate",
        "rows": 8,
        "description": "yes/no visible precipitate, turbidity, bubble, or extractables concern.",
    },
]

CORE_DELIVERABLES = [
    {
        "id": "completed_phase_a_template",
        "name": "Completed ZRC-ND Phase A sentinel CSV",
        "acceptance": "All 8 run rows have real values for the required medium-integrity and provenance fields.",
        "target_path": "data/zrc_nd_phase_a_sentinel_template.csv",
    },
    {
        "id": "completed_chain_of_custody",
        "name": "Sample/module chain of custody",
        "acceptance": "Every initial/final sample event maps to a run_id, sample_id, article_id, module/cup/tube ID, medium lot, and receipt condition.",
        "target_path": "data/zrc_nd_phase_a_chain_of_custody.csv",
    },
    {
        "id": "instrument_export_bundle",
        "name": "Instrument exports and inspection images",
        "acceptance": "Raw pH, osmolality, conductivity, and visual-inspection files are preserved and named in the deviation or return log.",
        "target_path": "external_lab_exports/zrc_nd_phase_a/",
    },
    {
        "id": "deviation_log",
        "name": "Deviation log",
        "acceptance": "Any substitution in membrane, housing, guard, medium, exposure time, temperature, rinse, or instrument calibration is listed explicitly.",
        "target_path": "reports/zrc_nd_phase_a_deviation_log.md",
    },
]

REQUIRED_CAPABILITIES = [
    "Acellular 37 C or matched-temperature medium exposure of small membrane/module witness articles.",
    "Matched no-module control handling for the same timepoints and medium lot.",
    "pH measurement before and after each row.",
    "Osmolality measurement before and after each row.",
    "Conductivity measurement before and after each row.",
    "Visual inspection for precipitate, turbidity, bubbles, color shift, or obvious extractables.",
    "Lot-level provenance for membrane, guard, housing, rinse/preconditioning, and medium.",
]

REJECTION_RULES = [
    "Do not enter pending, TBD, unknown, synthetic, fixture, or not_evidence markers as measured values.",
    "Do not pool the baseline, lead, challenge, or no-module rows before data entry.",
    "Do not advance Phase B/C or biological follow-up if the lead Phase A blank-integrity gate fails.",
    "Do not treat Phase A as a suitability claim; it only authorizes or blocks later ZRC-ND validation rows.",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def build_request(
    package: dict[str, Any],
    next_state: dict[str, Any],
    template_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, str]],
) -> dict[str, Any]:
    article_ids = unique([row.get("article_id", "") for row in template_rows])
    timepoints = unique([row.get("timepoint", "") for row in template_rows])
    replicates = unique([row.get("replicate", "") for row in template_rows])
    sample_events = unique([row.get("sample_event", "") for row in manifest_rows])
    return {
        "status": "ready_to_request_real_phase_a_measurements" if template_rows else "missing_phase_a_template_rows",
        "purpose": "Turn the ZRC-ND external-material Phase A blocker into a compact service request for real acellular medium-integrity measurements.",
        "active_candidate": "limina_zrc_nd_v0_1",
        "lead_variant_id": package.get("lead_variant_id", "zrc_nd_3p5k_mpc_guard"),
        "sentinel_selector_status": next_state.get("status", "unknown"),
        "sentinel_reason": next_state.get("reason", "unknown"),
        "requested_matrix": {
            "runs": len(template_rows),
            "sample_events": len(manifest_rows),
            "articles": article_ids,
            "timepoints": timepoints,
            "replicates": replicates,
            "sample_event_types": sample_events,
        },
        "required_capabilities": REQUIRED_CAPABILITIES,
        "deliverables": CORE_DELIVERABLES,
        "required_fields": PHASE_A_REQUIRED_FIELDS,
        "acceptance_gate": {
            "id": "zrc_nd_phase_a_blank_integrity_gate",
            "criterion": (
                "Material-driven pH drift must be <= 0.10 pH units versus matched no-module control; "
                "osmolality and conductivity drift must be <= 5 percent versus control; no visible precipitate "
                "or unresolved turbidity/extractables concern."
            ),
        },
        "article_roles": [
            {
                "article_id": item.get("id", ""),
                "role": item.get("role", ""),
                "description": item.get("description", ""),
            }
            for item in package.get("test_articles", [])
            if item.get("id", "") in article_ids
        ],
        "rejection_rules": REJECTION_RULES,
        "source_artifacts": {
            "phase_a_template": str(DEFAULT_TEMPLATE.relative_to(ROOT)),
            "sample_manifest": str(DEFAULT_MANIFEST.relative_to(ROOT)),
            "sentinel_packet": "reports/zrc_nd_phase_a_sentinel_packet.md",
            "next_measurements": "reports/zrc_nd_next_measurements.md",
            "validation_package": str(DEFAULT_PACKAGE.relative_to(ROOT)),
        },
        "post_delivery_commands": [
            "python3 scripts/merge_zrc_nd_measurements.py",
            "python3 scripts/interpret_zrc_nd_sentinel.py",
            "python3 scripts/evaluate_zrc_nd_validation_runs.py --runs data/zrc_nd_validation_runs_active.csv",
            "python3 scripts/suggest_zrc_nd_next_measurements.py --runs data/zrc_nd_validation_runs_active.csv",
            "python3 scripts/audit_zrc_nd_readiness.py",
            "python3 scripts/audit_limina_suitability_claim.py",
        ],
        "non_claim_boundary": (
            "Phase A is a material-blank front-door gate for the external cartridge branch. "
            "It cannot prove CL1 suitability without later Phase B/C non-cell and biological rows."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    matrix = result["requested_matrix"]
    gate = result["acceptance_gate"]
    lines = [
        "# ZRC-ND Phase A Real-Measurement Service Request",
        "",
        "This packet is for an external lab, collaborator, or bench operator. It requests real acellular Phase A measurements only; it is not a suitability claim.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result['active_candidate']}`",
        f"**Lead variant:** `{result['lead_variant_id']}`",
        f"**Sentinel selector:** `{result['sentinel_selector_status']}`; reason=`{result['sentinel_reason']}`",
        f"**Runs:** {matrix['runs']}",
        f"**Sample events:** {matrix['sample_events']}",
        "",
        "## Requested Matrix",
        "",
        f"- Articles: {', '.join(f'`{item}`' for item in matrix['articles'])}",
        f"- Timepoints: {', '.join(matrix['timepoints'])}",
        f"- Replicates: {', '.join(matrix['replicates'])}",
        f"- Sample event types: {', '.join(matrix['sample_event_types'])}",
        "",
        "## Required Capabilities",
        "",
    ]
    lines.extend(f"- {item}" for item in result["required_capabilities"])
    lines.extend([
        "",
        "## Acceptance Gate",
        "",
        f"- `{gate['id']}`: {gate['criterion']}",
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
        "## Article Roles",
        "",
        "| Article | Role | Description |",
        "| --- | --- | --- |",
    ])
    for item in result["article_roles"]:
        lines.append(f"| `{item['article_id']}` | {item['role']} | {item['description']} |")

    lines.extend(["", "## Rejection Rules", ""])
    lines.extend(f"- {item}" for item in result["rejection_rules"])

    lines.extend(["", "## Source Artifacts", ""])
    for label, path in result["source_artifacts"].items():
        lines.append(f"- {label}: `{path}`")

    lines.extend([
        "",
        "## After Delivery",
        "",
        "Run these commands after the completed Phase A CSV is placed back into the workspace:",
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
    parser = argparse.ArgumentParser(description="Render the ZRC-ND Phase A real-measurement service request.")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--next", type=Path, default=DEFAULT_NEXT)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--sample-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_request(
        load_json(args.package),
        load_json(args.next),
        load_rows(args.template),
        load_rows(args.sample_manifest),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"ZRC-ND Phase A service request: {result['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "ready_to_request_real_phase_a_measurements" else 2


if __name__ == "__main__":
    raise SystemExit(main())
