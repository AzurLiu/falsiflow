#!/usr/bin/env python3
"""Render an RFQ packet for ZRC-ND Phase A vendor/cooperator outreach."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTREACH = ROOT / "data" / "zrc_nd_phase_a_vendor_outreach.json"
DEFAULT_DELIVERY = ROOT / "data" / "zrc_nd_phase_a_delivery_package_manifest.json"
DEFAULT_SERVICE = ROOT / "data" / "zrc_nd_phase_a_service_request.json"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_rfq_packet.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_rfq_packet.md"

SCORING_RUBRIC = [
    {
        "criterion": "run_id_level_raw_data",
        "weight": 5,
        "pass_condition": "Vendor accepts one result per run_id/sample_event/test field and does not require pooled reporting.",
    },
    {
        "criterion": "phase_a_media_panel_coverage",
        "weight": 5,
        "pass_condition": "Vendor can report pH, osmolality, conductivity, and appearance/turbidity/visible precipitate, or clearly defines a split path for the missing field.",
    },
    {
        "criterion": "csv_schema_acceptance",
        "weight": 4,
        "pass_condition": "Vendor can fill or accept the ZRC-ND Phase A CSV without changing column names.",
    },
    {
        "criterion": "sample_handling_fit",
        "weight": 3,
        "pass_condition": "Vendor can handle nonclinical neural-medium aliquots exposed to regenerated-cellulose/module witness articles.",
    },
    {
        "criterion": "source_file_provenance",
        "weight": 3,
        "pass_condition": "Vendor can return raw exports, instrument reports, or stable filenames that reconcile to run_id/sample_id.",
    },
    {
        "criterion": "turnaround_and_cost",
        "weight": 2,
        "pass_condition": "Vendor can provide practical R&D quote, sample requirements, and turnaround for the 8-run Phase A package.",
    },
    {
        "criterion": "non_glp_scope_control",
        "weight": 2,
        "pass_condition": "Vendor can keep the first pass exploratory and avoid forcing a full GLP/E&L program before Phase A.",
    },
]

DISQUALIFIERS = [
    "Only returns pooled averages, certificates, or narrative feasibility opinions.",
    "Will not preserve run_id, sample_event, and target-field mapping.",
    "Cannot return raw exports, instrument reports, or traceable source files.",
    "Requires changing article identity, timepoints, membrane material, or control rows without a deviation log.",
    "Treats quote, supplier support, or vendor capability claims as final material suitability evidence.",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def file_list(delivery: dict[str, Any]) -> list[str]:
    return [item["path"] for item in delivery.get("package_files", []) if item.get("required") and item.get("exists")]


def candidate_scope(candidate: dict[str, Any]) -> str:
    service_type = candidate.get("service_type", "")
    if service_type in {"physicochemical_testing", "cell_culture_media_testing"}:
        return "Ask whether they can execute the full Phase A pH/osmolality/conductivity/appearance package or identify a split path for missing fields."
    if service_type == "osmolality_and_ph_testing":
        return "Use as focused pH/osmolality provider and ask whether conductivity is supported or must be split."
    if service_type == "polymer_and_extractables_testing":
        return "Use for custom chemistry or E&L escalation if Phase A shows drift, particulates, or extractables concern."
    if service_type == "membrane_supplier_application_support":
        return "Ask for membrane selection, rinse, lot documentation, and compatibility support; supplier guidance is not measurement evidence."
    return "Ask for feasibility against the exact ZRC-ND Phase A service request."


def email_subject(candidate: dict[str, Any]) -> str:
    return f"RFQ: non-GLP acellular ZRC-ND Phase A medium-integrity measurements ({candidate['name']})"


def email_body(candidate: dict[str, Any], service: dict[str, Any], attachments: list[str]) -> str:
    matrix = service.get("requested_matrix", {})
    questions = candidate.get("unknowns_to_ask", [])
    lines = [
        f"Hello {candidate['name']} team,",
        "",
        "I am requesting a feasibility review and non-GLP R&D quote for a small acellular medium-integrity measurement package.",
        "",
        "Study summary:",
        f"- Active material route: {service.get('active_candidate', 'limina_zrc_nd_v0_1')}",
        f"- Lead variant: {service.get('lead_variant_id', 'zrc_nd_3p5k_mpc_guard')}",
        f"- Runs: {matrix.get('runs', 8)}",
        f"- Sample events: {matrix.get('sample_events', 16)}",
        "- Articles: unmodified 3.5 kDa RC baseline, MPC-like 3.5 kDa lead, 10 kDa challenge, and no-module static control",
        "- Timepoints: 0 h and 24 h",
        "- Required outputs: pH, osmolality, conductivity, appearance/turbidity/visible precipitate, raw exports or instrument reports, and chain-of-custody by run_id",
        "",
        "Important constraint: we need one result per provided run_id/sample_event/test field. Pooled averages or narrative certificates alone will not satisfy the study.",
        "",
        "Could you please confirm:",
    ]
    lines.extend(f"- {question}" for question in questions)
    lines.extend([
        "- Whether you can fill or accept the provided Phase A CSV schema without changing column names",
        "- Minimum aliquot volume, sample container, and sample count requirements",
        "- Expected turnaround time, quote range, sample acceptance constraints, and whether SDS/lot documentation is required before shipping",
        "",
        "Attached/package files to review:",
    ])
    lines.extend(f"- {attachment}" for attachment in attachments)
    lines.extend([
        "",
        "This is exploratory R&D screening. We are not requesting a material suitability claim from the vendor; we only need traceable raw measurements to feed our internal Phase A gate.",
        "",
        "Thank you.",
    ])
    return "\n".join(lines)


def build_packet(outreach: dict[str, Any], delivery: dict[str, Any], service: dict[str, Any]) -> dict[str, Any]:
    attachments = file_list(delivery)
    quote_requests = [
        {
            "candidate_id": candidate["id"],
            "name": candidate["name"],
            "source_url": candidate["source_url"],
            "contact_url": candidate.get("contact_url", ""),
            "service_type": candidate["service_type"],
            "scope_instruction": candidate_scope(candidate),
            "subject": email_subject(candidate),
            "email_body": email_body(candidate, service, attachments),
            "unknowns_to_resolve": candidate.get("unknowns_to_ask", []),
        }
        for candidate in outreach.get("first_wave", [])
    ]
    return {
        "status": "ready_to_send_rfq" if outreach.get("status") == "ready_for_vendor_screening" else "outreach_not_ready",
        "purpose": "Per-candidate RFQ material for obtaining real ZRC-ND Phase A measurements.",
        "active_candidate": outreach.get("active_candidate"),
        "attachment_paths": attachments,
        "quote_requests": quote_requests,
        "scoring_rubric": SCORING_RUBRIC,
        "disqualifiers": DISQUALIFIERS,
        "scorecard_columns": [
            "candidate_id",
            "contact_date",
            "reply_date",
            "can_cover_full_phase_a",
            "needs_split_scope",
            "run_id_level_raw_data",
            "phase_a_media_panel_coverage",
            "csv_schema_acceptance",
            "sample_handling_fit",
            "source_file_provenance",
            "non_glp_scope_control",
            "turnaround_days",
            "quoted_cost",
            "decision",
            "notes",
        ],
        "non_claim_boundary": outreach.get("non_claim_boundary"),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# ZRC-ND Phase A RFQ Packet",
        "",
        "This packet provides per-candidate RFQ text and a quote scoring rubric. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result.get('active_candidate', '-')}`",
        f"**Quote requests:** {len(result.get('quote_requests', []))}",
        "",
        "## Attachments",
        "",
    ]
    lines.extend(f"- `{path}`" for path in result.get("attachment_paths", []))

    lines.extend(["", "## RFQ Score Rubric", "", "| Criterion | Weight | Pass condition |", "| --- | ---: | --- |"])
    for item in result["scoring_rubric"]:
        lines.append(f"| `{item['criterion']}` | {item['weight']} | {item['pass_condition']} |")

    lines.extend(["", "## Disqualifiers", ""])
    lines.extend(f"- {item}" for item in result["disqualifiers"])

    lines.extend(["", "## Scorecard Columns", "", "```text", ",".join(result["scorecard_columns"]), "```", "", "## Per-Candidate RFQs", ""])
    for request in result["quote_requests"]:
        lines.extend([
            f"### {request['name']}",
            "",
            f"- Candidate ID: `{request['candidate_id']}`",
            f"- Source: {request['source_url']}",
            f"- Contact: {request.get('contact_url') or '-'}",
            f"- Scope instruction: {request['scope_instruction']}",
            f"- Subject: {request['subject']}",
            "",
            "```text",
            request["email_body"],
            "```",
            "",
        ])

    lines.extend(["## Boundary", "", result["non_claim_boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render ZRC-ND Phase A RFQ packet.")
    parser.add_argument("--outreach", type=Path, default=DEFAULT_OUTREACH)
    parser.add_argument("--delivery", type=Path, default=DEFAULT_DELIVERY)
    parser.add_argument("--service", type=Path, default=DEFAULT_SERVICE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_packet(load_json(args.outreach), load_json(args.delivery), load_json(args.service))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"ZRC-ND Phase A RFQ packet: {result['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "ready_to_send_rfq" else 2


if __name__ == "__main__":
    raise SystemExit(main())
