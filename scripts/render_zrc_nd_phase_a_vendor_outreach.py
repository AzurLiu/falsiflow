#!/usr/bin/env python3
"""Render vendor/cooperator outreach brief for ZRC-ND Phase A measurements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "zrc_nd_phase_a_vendor_candidates.json"
DEFAULT_SERVICE = ROOT / "data" / "zrc_nd_phase_a_service_request.json"
DEFAULT_DELIVERY = ROOT / "data" / "zrc_nd_phase_a_delivery_package_manifest.json"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_vendor_outreach.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_vendor_outreach_brief.md"

QUESTION_BANK = [
    "Can you accept nonclinical acellular neural-medium aliquots exposed to small membrane/module witness articles?",
    "Can you preserve one result per LIMINA run_id rather than returning pooled averages?",
    "Can you report pH, osmolality, conductivity, and appearance/turbidity/visible precipitate for every requested row?",
    "If conductivity is not available, can you identify whether the sample may be returned or paired with a second lab while preserving run_id labels?",
    "Can you fill or accept the provided Phase A CSV schema without changing column names?",
    "What minimum aliquot volume, sample count, container, and turnaround time are required?",
    "What handling constraints apply to regenerated-cellulose membranes, guard filters, COC/COP/PEEK modules, and neural-medium proxies?",
    "Can you return raw exports or instrument reports with stable filenames that can be reconciled to run_id?",
    "Can this be scoped as exploratory non-GLP R&D rather than a full regulated E&L or product-release program?",
    "What sample acceptance, SDS, chain-of-custody, and quote-number requirements must be met before shipping?"
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def candidate_by_id(candidates: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in candidates.get("candidates", [])}


def ranked_candidates(candidates: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = candidate_by_id(candidates)
    ranked = [by_id[item] for item in candidates.get("recommended_first_outreach_order", []) if item in by_id]
    ranked_ids = {row["id"] for row in ranked}
    remaining = [item for item in candidates.get("candidates", []) if item["id"] not in ranked_ids]
    return ranked + remaining


def build_outreach(candidates: dict[str, Any], service: dict[str, Any], delivery: dict[str, Any]) -> dict[str, Any]:
    ranked = ranked_candidates(candidates)
    return {
        "status": "ready_for_vendor_screening" if delivery.get("status") == "ready_to_send" else "package_not_ready",
        "purpose": "Shortlist external service options for returning real ZRC-ND Phase A measurement rows.",
        "active_candidate": candidates.get("active_candidate", service.get("active_candidate")),
        "last_checked": candidates.get("last_checked"),
        "delivery_package_status": delivery.get("status", "unknown"),
        "service_request_status": service.get("status", "unknown"),
        "requested_matrix": service.get("requested_matrix", {}),
        "outreach_strategy": candidates.get("outreach_strategy", []),
        "question_bank": QUESTION_BANK,
        "ranked_candidates": ranked,
        "first_wave": ranked[:4],
        "secondary_wave": ranked[4:],
        "non_claim_boundary": candidates.get("non_claim_boundary"),
    }


def markdown_link(name: str, url: str) -> str:
    return f"[{name}]({url})" if url else name


def render_report(result: dict[str, Any]) -> str:
    matrix = result.get("requested_matrix", {})
    lines = [
        "# ZRC-ND Phase A Vendor Outreach Brief",
        "",
        "This brief screens external services that may return real Phase A acellular measurements. It is not a purchase recommendation and not material evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result['active_candidate']}`",
        f"**Last checked:** `{result['last_checked']}`",
        f"**Service request:** `{result['service_request_status']}`",
        f"**Delivery package:** `{result['delivery_package_status']}`",
        f"**Runs:** {matrix.get('runs', '-')}",
        f"**Sample events:** {matrix.get('sample_events', '-')}",
        "",
        "## Outreach Strategy",
        "",
    ]
    lines.extend(f"- {item}" for item in result["outreach_strategy"])
    lines.extend([
        "",
        "## First-Wave Contacts",
        "",
        "| Candidate | Fit | Likely covers | Main risk | Source |",
        "| --- | --- | --- | --- | --- |",
    ])
    for item in result["first_wave"]:
        lines.append(
            f"| `{item['id']}` | {item['fit_for_phase_a']} | "
            f"{', '.join(item.get('likely_covers', []))} | {item['risk']} | "
            f"{markdown_link(item['name'], item['source_url'])} |"
        )

    lines.extend([
        "",
        "## Secondary/Escalation Contacts",
        "",
        "| Candidate | Fit | Use only if | Source |",
        "| --- | --- | --- | --- |",
    ])
    for item in result["secondary_wave"]:
        lines.append(
            f"| `{item['id']}` | {item['fit_for_phase_a']} | {item['risk']} | "
            f"{markdown_link(item['name'], item['source_url'])} |"
        )

    lines.extend(["", "## Questions To Send", ""])
    lines.extend(f"- {item}" for item in result["question_bank"])

    lines.extend(["", "## Candidate Details", ""])
    for item in result["ranked_candidates"]:
        lines.extend([
            f"### {item['name']}",
            "",
            f"- Source: {markdown_link(item['source_url'], item['source_url'])}",
            f"- Contact: {markdown_link(item.get('contact_url', ''), item.get('contact_url', ''))}",
            f"- Service type: `{item['service_type']}`",
            f"- Evidence from source: {item['evidence_from_source']}",
            f"- Likely covers: {', '.join(item.get('likely_covers', []))}",
            "- Unknowns to ask:",
        ])
        lines.extend(f"  - {question}" for question in item.get("unknowns_to_ask", []))
        lines.extend([f"- Risk: {item['risk']}", ""])

    lines.extend(["## Boundary", "", result["non_claim_boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render ZRC-ND Phase A vendor outreach brief.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--service-request", type=Path, default=DEFAULT_SERVICE)
    parser.add_argument("--delivery-package", type=Path, default=DEFAULT_DELIVERY)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_outreach(load_json(args.input), load_json(args.service_request), load_json(args.delivery_package))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"ZRC-ND Phase A vendor outreach: {result['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "ready_for_vendor_screening" else 2


if __name__ == "__main__":
    raise SystemExit(main())
