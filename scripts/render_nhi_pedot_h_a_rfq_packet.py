#!/usr/bin/env python3
"""Render an RFQ packet for NHI-PEDOT H-A vendor/cooperator outreach."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTREACH = ROOT / "data" / "nhi_pedot_h_a_vendor_outreach.json"
DEFAULT_DELIVERY = ROOT / "data" / "nhi_pedot_h_a_delivery_package_manifest.json"
DEFAULT_SERVICE = ROOT / "data" / "nhi_pedot_h_a_service_request.json"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_rfq_packet.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_rfq_packet.md"

SCORING_RUBRIC = [
    {
        "criterion": "run_id_level_raw_data",
        "weight": 5,
        "pass_condition": "Vendor accepts one result per run_id/sample_event/target_field and does not require pooled reporting.",
    },
    {
        "criterion": "media_physicochemical_coverage",
        "weight": 4,
        "pass_condition": "Vendor can report pH, osmolality, and conductivity before/after the requested timepoints, or clearly names a partner/subcontract path.",
    },
    {
        "criterion": "coupon_physical_coverage",
        "weight": 4,
        "pass_condition": "Vendor can report swelling fraction, visible precipitate, shedding, delamination score, optical transparency, and supporting images.",
    },
    {
        "criterion": "csv_schema_acceptance",
        "weight": 4,
        "pass_condition": "Vendor can fill or accept either the LIMINA raw-measurement CSV or the compact bundle-entry CSV without changing column names.",
    },
    {
        "criterion": "bundle_entry_sheet_acceptance",
        "weight": 2,
        "pass_condition": "Vendor can use the compact one-row-per-source-file bundle sheet when one raw export/report supports multiple values.",
    },
    {
        "criterion": "sample_handling_fit",
        "weight": 3,
        "pass_condition": "Vendor can handle neural medium, alginate/laminin/PEDOT:PSS coupons, 37 C timing, and chain-of-custody constraints.",
    },
    {
        "criterion": "turnaround_and_cost",
        "weight": 2,
        "pass_condition": "Vendor can provide a practical R&D quote and turnaround for the 12-run/228-entry package.",
    },
    {
        "criterion": "non_glp_scope_control",
        "weight": 2,
        "pass_condition": "Vendor can keep the first pass as exploratory R&D and not force a full GLP/ISO program before H-A.",
    },
]

DISQUALIFIERS = [
    "Only returns pooled averages or narrative pass/fail certificates.",
    "Will not preserve run_id, sample_event, and target_field mapping.",
    "Cannot return source files or raw exports for provenance.",
    "Requires replacing the requested material stack or timepoints without a documented deviation log.",
    "Treats vendor capability claims as final material suitability evidence.",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def file_list(delivery: dict[str, Any]) -> list[str]:
    return [
        item["path"]
        for item in delivery.get("package_files", [])
        if item.get("required") and item.get("exists")
    ]


def candidate_scope(candidate: dict[str, Any]) -> str:
    service_type = candidate.get("service_type", "")
    if service_type in {"custom_biomaterials_characterization", "hydrogel_characterization"}:
        return "Ask whether they can execute the full H-A package or pair with a media physicochemical lab."
    if service_type in {"media_physicochemical_testing", "cell_culture_media_testing"}:
        return "Ask for pH/osmolality/conductivity on all pre/post aliquots and whether they can add appearance/clarity notes."
    if service_type == "microscopy_and_image_analysis":
        return "Use as an imaging add-on for coupon swelling, transparency, shedding, and delamination if media testing is split."
    if service_type == "iso_10993_chemical_characterization":
        return "Hold for E&L escalation after H-A or if vendors identify leachables as the primary risk."
    return "Ask for feasibility against the exact H-A service request."


def email_subject(candidate: dict[str, Any]) -> str:
    return f"RFQ: non-GLP acellular hydrogel-coupon H-A measurements ({candidate['name']})"


def email_body(candidate: dict[str, Any], service: dict[str, Any], attachments: list[str]) -> str:
    matrix = service.get("requested_matrix", {})
    questions = candidate.get("unknowns_to_ask", [])
    lines = [
        f"Hello {candidate['name']} team,",
        "",
        "I am requesting a feasibility review and non-GLP R&D quote for a small acellular biomaterials measurement package.",
        "",
        "Study summary:",
        f"- Active material route: {service.get('active_candidate', 'limina_alg_lam_pedot_lowdose_v0_2')}",
        f"- Runs: {matrix.get('runs', 12)}",
        f"- Raw measurement entries requested: {matrix.get('raw_entries', 228)}",
        "- Articles: no-coating control, alginate-laminin hydrogel control, low-loading ALG-LAM-PEDOT lead, high-loading boundary comparator",
        "- Timepoints: 0 h, 24 h, 72 h",
        "- Required outputs: sample-level pH, osmolality, conductivity, visible precipitate, visible shedding, swelling fraction, delamination score, optical transparency fraction, raw exports/images, and chain-of-custody by run_id",
        "",
        "Important constraint: we need one result per provided run_id/sample_event/target_field. Pooled averages or narrative certificates alone will not satisfy the study. The compact bundle entry sheet is preferred when one raw export/report supports multiple values.",
        "",
        "Could you please confirm:",
    ]
    lines.extend(f"- {question}" for question in questions)
    lines.extend([
        "- Whether you can fill or accept the provided raw-measurement CSV or compact bundle-entry CSV schema without changing column names",
        "- Minimum sample volume/coupon count requirements",
        "- Expected turnaround time, quote range, and any sample-prep constraints",
        "",
        "Attached/package files to review:",
    ])
    lines.extend(f"- {attachment}" for attachment in attachments)
    lines.extend([
        "",
        "This is exploratory R&D screening. We are not requesting a material suitability claim from the vendor; we only need traceable raw measurements to feed our internal QC gates.",
        "",
        "Thank you.",
    ])
    return "\n".join(lines)


def build_packet(outreach: dict[str, Any], delivery: dict[str, Any], service: dict[str, Any]) -> dict[str, Any]:
    attachments = file_list(delivery)
    first_wave = outreach.get("first_wave", [])
    quote_requests = [
        {
            "candidate_id": candidate["id"],
            "name": candidate["name"],
            "source_url": candidate["source_url"],
            "service_type": candidate["service_type"],
            "scope_instruction": candidate_scope(candidate),
            "subject": email_subject(candidate),
            "email_body": email_body(candidate, service, attachments),
            "unknowns_to_resolve": candidate.get("unknowns_to_ask", []),
        }
        for candidate in first_wave
    ]
    return {
        "status": "ready_to_send_rfq" if outreach.get("status") == "ready_for_vendor_screening" else "outreach_not_ready",
        "purpose": "Per-candidate RFQ material for obtaining real NHI-PEDOT H-A measurements.",
        "active_candidate": outreach.get("active_candidate"),
        "attachment_paths": attachments,
        "quote_requests": quote_requests,
        "scoring_rubric": SCORING_RUBRIC,
        "disqualifiers": DISQUALIFIERS,
        "scorecard_columns": [
            "candidate_id",
            "contact_date",
            "reply_date",
            "can_cover_full_h_a",
            "needs_split_scope",
            "run_id_level_raw_data",
            "media_physicochemical_coverage",
            "coupon_physical_coverage",
            "csv_schema_acceptance",
            "bundle_entry_sheet_acceptance",
            "sample_handling_fit",
            "turnaround_days",
            "quoted_cost",
            "decision",
            "notes",
        ],
        "non_claim_boundary": outreach.get("non_claim_boundary"),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# NHI-PEDOT H-A RFQ Packet",
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

    lines.extend([
        "",
        "## RFQ Score Rubric",
        "",
        "| Criterion | Weight | Pass condition |",
        "| --- | ---: | --- |",
    ])
    for item in result["scoring_rubric"]:
        lines.append(f"| `{item['criterion']}` | {item['weight']} | {item['pass_condition']} |")

    lines.extend([
        "",
        "## Disqualifiers",
        "",
    ])
    lines.extend(f"- {item}" for item in result["disqualifiers"])

    lines.extend([
        "",
        "## Scorecard Columns",
        "",
        "```text",
        ",".join(result["scorecard_columns"]),
        "```",
        "",
        "## Per-Candidate RFQs",
        "",
    ])
    for request in result["quote_requests"]:
        lines.extend([
            f"### {request['name']}",
            "",
            f"- Candidate ID: `{request['candidate_id']}`",
            f"- Source: {request['source_url']}",
            f"- Scope instruction: {request['scope_instruction']}",
            f"- Subject: {request['subject']}",
            "",
            "```text",
            request["email_body"],
            "```",
            "",
        ])

    lines.extend([
        "## Boundary",
        "",
        result["non_claim_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A RFQ packet.")
    parser.add_argument("--outreach", type=Path, default=DEFAULT_OUTREACH)
    parser.add_argument("--delivery", type=Path, default=DEFAULT_DELIVERY)
    parser.add_argument("--service", type=Path, default=DEFAULT_SERVICE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_packet(
        load_json(args.outreach),
        load_json(args.delivery),
        load_json(args.service),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A RFQ packet: {result['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "ready_to_send_rfq" else 2


if __name__ == "__main__":
    raise SystemExit(main())
