#!/usr/bin/env python3
"""Render sample-submission and safety-disclosure pack for NHI-PEDOT H-A RFQs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECIPE = ROOT / "data" / "nhi_pedot_recipe_lock_v0_2.json"
DEFAULT_SERVICE = ROOT / "data" / "nhi_pedot_h_a_service_request.json"
DEFAULT_CHAIN = ROOT / "data" / "nhi_pedot_h_a_chain_of_custody.json"
DEFAULT_CONTACTS = ROOT / "data" / "nhi_pedot_h_a_vendor_contact_channels.json"
DEFAULT_COMPONENT_CSV = ROOT / "data" / "nhi_pedot_h_a_material_disclosure.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_sample_submission_pack.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_sample_submission_pack.md"

COMPONENT_FIELDS = [
    "component",
    "role",
    "planned_description",
    "actual_lot_required",
    "sds_required_before_shipping",
    "hazard_or_handling_note",
]

VENDOR_FIELDS = [
    "candidate_id",
    "vendor_name",
    "quote_or_contact_url",
    "sample_submission_url",
    "pre_ship_status",
    "pre_ship_action",
]

NON_SDS_BOUNDARY = (
    "This pack is a nonclinical R&D material disclosure and shipping-readiness checklist. "
    "It is not a certified SDS, toxicology opinion, biological safety approval, or material evidence."
)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def component_rows(recipe: dict[str, Any]) -> list[dict[str, str]]:
    targets = recipe.get("design_targets", {})
    return [
        {
            "component": "MEA witness coupon or equivalent electrode-window coupon",
            "role": "device-contact substrate/control surface",
            "planned_description": "Actual coupon material, geometry, and surface treatment must be recorded before shipment.",
            "actual_lot_required": "yes",
            "sds_required_before_shipping": "vendor_dependent",
            "hazard_or_handling_note": "No electronics need to be powered; disclose substrate material and any cleaning/sterilization residues.",
        },
        {
            "component": "Sodium alginate",
            "role": "hydrogel matrix",
            "planned_description": targets.get("hydrogel_matrix", "2 percent w/v alginate hydrogel matrix"),
            "actual_lot_required": "yes",
            "sds_required_before_shipping": "yes",
            "hazard_or_handling_note": "Provide supplier SDS and lot; keep dry powder handling separate from hydrated coupon shipment notes.",
        },
        {
            "component": "Calcium sulfate dihydrate",
            "role": "ionic crosslinker",
            "planned_description": "183 mM calcium sulfate dihydrate dispersed in 1x DMEM for gelation.",
            "actual_lot_required": "yes",
            "sds_required_before_shipping": "yes",
            "hazard_or_handling_note": "Provide supplier SDS and final preparation batch ID.",
        },
        {
            "component": "DMEM or DMEM/F12 / CL1-proxy medium",
            "role": "crosslinking and soak medium",
            "planned_description": "Actual medium name and lot must be entered in H-A rows; no live cells are included.",
            "actual_lot_required": "yes",
            "sds_required_before_shipping": "yes",
            "hazard_or_handling_note": "Disclose all supplements if used; do not send biohazardous or cell-containing material.",
        },
        {
            "component": "PEDOT:PSS dispersion",
            "role": "conductive phase",
            "planned_description": targets.get("conductive_phase", "0.6 wt percent PEDOT:PSS lead and 1.2 wt percent boundary comparator"),
            "actual_lot_required": "yes",
            "sds_required_before_shipping": "yes",
            "hazard_or_handling_note": "Provide supplier SDS, loading fraction, pre-rinse/conditioning record, and whether free dispersion is present in shipped aliquots.",
        },
        {
            "component": "Laminin or equivalent cell-adhesion cue",
            "role": "neural cell-contact cue retained above or within hydrogel",
            "planned_description": targets.get("presentation", "EHS laminin or equivalent laminin cue"),
            "actual_lot_required": "yes",
            "sds_required_before_shipping": "yes",
            "hazard_or_handling_note": "Disclose biological source if applicable; no live cells or human subject material should be included.",
        },
        {
            "component": "Acellular soak aliquots",
            "role": "media physicochemical test article",
            "planned_description": "Pre/post aliquots for pH, osmolality, conductivity, and appearance after 0 h, 24 h, and 72 h H-A soaks.",
            "actual_lot_required": "yes",
            "sds_required_before_shipping": "vendor_dependent",
            "hazard_or_handling_note": "Confirm volume, container, temperature, and no-biohazard acceptance with vendor before shipment.",
        },
    ]


def contact_items(contacts: dict[str, Any]) -> list[dict[str, Any]]:
    if contacts.get("rows"):
        return contacts.get("rows", [])
    return contacts.get("contacts", [])


def vendor_rows(contacts: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for item in contact_items(contacts):
        rows.append({
            "candidate_id": item.get("candidate_id", ""),
            "vendor_name": item.get("vendor_name") or item.get("name", ""),
            "quote_or_contact_url": item.get("quote_url") or item.get("contact_url", ""),
            "sample_submission_url": item.get("sample_submission_url", ""),
            "pre_ship_status": "do_not_ship_until_vendor_confirms",
            "pre_ship_action": item.get("send_note", "Confirm sample acceptance, sample count, volume, SDS, and quote number before shipment."),
        })
    return rows


def build_pack(
    recipe: dict[str, Any],
    service: dict[str, Any],
    chain: dict[str, Any],
    contacts: dict[str, Any],
) -> dict[str, Any]:
    matrix = service.get("requested_matrix", {})
    rows = component_rows(recipe)
    vendors = vendor_rows(contacts)
    return {
        "status": "sample_submission_precheck_ready" if rows and vendors else "sample_submission_inputs_missing",
        "purpose": "Prepare vendor-facing sample composition, nonclinical status, and pre-shipment questions for the NHI-PEDOT H-A RFQ.",
        "active_candidate": recipe.get("candidate_id", service.get("active_candidate")),
        "protocol_id": recipe.get("protocol_id"),
        "nonclinical_statement": "Planned H-A samples are nonclinical R&D, acellular medium/coupon samples with no live cells and no intended human or animal use.",
        "shipping_status": "do_not_ship_until_vendor_confirms_quote_sample_acceptance_sds_and_custody",
        "requested_runs": matrix.get("runs", 0),
        "requested_raw_entries": matrix.get("raw_entries", 0),
        "sample_label_count": chain.get("sample_label_count", 0),
        "chain_of_custody_rows": chain.get("chain_of_custody_row_count", 0),
        "sample_event_count": chain.get("chain_of_custody_row_count", 0),
        "component_rows": rows,
        "vendor_pre_ship_rows": vendors,
        "pre_ship_questions": [
            "Will you accept acellular neural-medium soak aliquots and hydrated hydrogel/MEA witness coupons as nonclinical R&D samples?",
            "What minimum aliquot volume and coupon count are required for pH, osmolality, conductivity, and imaging/inspection?",
            "Which supplier SDS files, lot numbers, and preparation-batch records are required before shipment?",
            "Do you require a quote number, sample submission form, purchase order, or project ID before samples are sent?",
            "What container, temperature, timing, and chain-of-custody requirements apply to 0 h, 24 h, and 72 h samples?",
            "Can returned files preserve run_id, sample_event, target_field, source_file, and instrument export provenance?",
        ],
        "rejection_rules": [
            "Do not ship any live cells, human subject material, animal tissue, or unknown biological material.",
            "Do not ship hydrated PEDOT:PSS/alginate/laminin samples until the vendor confirms SDS and sample acceptance requirements.",
            "Do not treat vendor acceptance, quote numbers, or sample-submission forms as measured evidence.",
            "Do not substitute vendor-proposed pooled reporting for LIMINA run_id-level raw data without a documented rejection or split-scope decision.",
        ],
        "outputs": {
            "component_csv": str(DEFAULT_COMPONENT_CSV.relative_to(ROOT)),
            "json": str(DEFAULT_JSON.relative_to(ROOT)),
            "report": str(DEFAULT_REPORT.relative_to(ROOT)),
        },
        "boundary": NON_SDS_BOUNDARY,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# NHI-PEDOT H-A Sample Submission Pack",
        "",
        "This pack prepares vendor sample-submission questions and material disclosure. It is not measured evidence and not a certified SDS.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result.get('active_candidate', '-')}`",
        f"**Protocol:** `{result.get('protocol_id', '-')}`",
        f"**Shipping status:** `{result['shipping_status']}`",
        f"**Runs:** {result['requested_runs']}",
        f"**Raw entries:** {result['requested_raw_entries']}",
        f"**Sample labels:** {result['sample_label_count']}",
        f"**Custody rows:** {result['chain_of_custody_rows']}",
        "",
        "## Nonclinical Statement",
        "",
        result["nonclinical_statement"],
        "",
        "## Material Disclosure",
        "",
        "| Component | Role | Actual lot? | SDS before shipping? | Handling note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result["component_rows"]:
        lines.append(
            f"| {row['component']} | {row['role']} | `{row['actual_lot_required']}` | "
            f"`{row['sds_required_before_shipping']}` | {row['hazard_or_handling_note']} |"
        )

    lines.extend([
        "",
        "## Vendor Pre-Ship Actions",
        "",
        "| Vendor | Contact/quote URL | Sample submission URL | Status | Action |",
        "| --- | --- | --- | --- | --- |",
    ])
    for row in result["vendor_pre_ship_rows"]:
        lines.append(
            f"| {row['vendor_name']} | {row['quote_or_contact_url'] or '-'} | "
            f"{row['sample_submission_url'] or '-'} | `{row['pre_ship_status']}` | {row['pre_ship_action']} |"
        )

    lines.extend([
        "",
        "## Pre-Ship Questions",
        "",
    ])
    lines.extend(f"- {item}" for item in result["pre_ship_questions"])

    lines.extend([
        "",
        "## Rejection Rules",
        "",
    ])
    lines.extend(f"- {item}" for item in result["rejection_rules"])

    lines.extend([
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A sample submission pack.")
    parser.add_argument("--recipe", type=Path, default=DEFAULT_RECIPE)
    parser.add_argument("--service", type=Path, default=DEFAULT_SERVICE)
    parser.add_argument("--chain", type=Path, default=DEFAULT_CHAIN)
    parser.add_argument("--contacts", type=Path, default=DEFAULT_CONTACTS)
    parser.add_argument("--component-csv", type=Path, default=DEFAULT_COMPONENT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_pack(
        load_json(args.recipe),
        load_json(args.service),
        load_json(args.chain),
        load_json(args.contacts),
    )
    write_csv(args.component_csv, COMPONENT_FIELDS, result["component_rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A sample submission pack: {result['status']}")
    print(f"Wrote {args.component_csv}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "sample_submission_precheck_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
