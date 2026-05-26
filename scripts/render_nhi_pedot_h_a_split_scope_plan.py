#!/usr/bin/env python3
"""Render split-scope H-A execution plan for NHI-PEDOT vendors."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "data" / "nhi_pedot_h_a_vendor_candidates.json"
DEFAULT_SERVICE = ROOT / "data" / "nhi_pedot_h_a_service_request.json"
DEFAULT_CONTACTS = ROOT / "data" / "nhi_pedot_h_a_vendor_contact_channels.json"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_h_a_split_scope_plan.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_split_scope_plan.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_split_scope_plan.md"

CSV_FIELDS = [
    "pair_id",
    "media_candidate_id",
    "media_vendor",
    "coupon_candidate_id",
    "coupon_vendor",
    "pair_role",
    "score",
    "media_scope",
    "coupon_scope",
    "shared_requirements",
    "decision",
    "media_contact_status",
    "coupon_contact_status",
]

MEDIA_TYPES = {"media_physicochemical_testing", "cell_culture_media_testing"}
COUPON_TYPES = {"hydrogel_characterization", "microscopy_and_image_analysis", "custom_biomaterials_characterization"}
INTEGRATED_TYPES = {"custom_biomaterials_characterization"}

MEDIA_FIELDS = [
    "date",
    "medium_name",
    "medium_lot",
    "temperature_c",
    "pH_initial",
    "pH_final",
    "osmolality_initial_mOsm_kg",
    "osmolality_final_mOsm_kg",
    "conductivity_initial_mS_cm",
    "conductivity_final_mS_cm",
    "visible_precipitate",
]

COUPON_FIELDS = [
    "mea_coupon_id",
    "electrode_material",
    "visible_shedding",
    "swelling_fraction",
    "delamination_score",
    "optical_transparency_fraction",
    "image_source_file",
]

SHARED_REQUIREMENTS = [
    "Both vendors must preserve LIMINA run_id and sample_event labels.",
    "Both vendors must return source_file names that resolve to instrument exports or image files.",
    "One operator must reconcile completed_raw_measurements.csv before merge.",
    "Chain-of-custody must identify which vendor handled each sample_event.",
    "Split scope cannot change timepoints, articles, or replicates without a deviation log.",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def candidate_order(candidates: dict[str, Any]) -> dict[str, int]:
    return {
        candidate_id: index
        for index, candidate_id in enumerate(candidates.get("recommended_first_outreach_order", []), start=1)
    }


def contact_status(contacts: dict[str, Any]) -> dict[str, str]:
    status = {}
    for row in contacts.get("contacts", []):
        candidate_id = row.get("candidate_id")
        if candidate_id:
            has_channel = bool(row.get("primary_email") or row.get("contact_url") or row.get("quote_url"))
            status[candidate_id] = "contact_ready" if has_channel else "missing_contact"
    return status


def score_media(candidate: dict[str, Any]) -> int:
    covers = {item.lower() for item in candidate.get("likely_covers", [])}
    score = 0
    if "ph" in covers:
        score += 3
    if "osmolality" in covers:
        score += 3
    if "conductivity" in covers:
        score += 3
    if "appearance" in covers:
        score += 1
    if candidate.get("service_type") == "media_physicochemical_testing":
        score += 2
    return score


def score_coupon(candidate: dict[str, Any]) -> int:
    covers = {item.lower() for item in candidate.get("likely_covers", [])}
    score = 0
    if any("swelling" in item or "swell" in item for item in covers):
        score += 3
    if any("microscopy" in item or "imaging" in item for item in covers):
        score += 3
    if any("hydrogel" in item for item in covers):
        score += 2
    if candidate.get("service_type") == "hydrogel_characterization":
        score += 2
    if candidate.get("service_type") == "custom_biomaterials_characterization":
        score += 2
    return score


def build_pair(
    media: dict[str, Any],
    coupon: dict[str, Any],
    order: dict[str, int],
    contacts: dict[str, str],
) -> dict[str, Any]:
    media_id = media.get("id", "")
    coupon_id = coupon.get("id", "")
    rank_bonus = max(0, 8 - order.get(media_id, 8)) + max(0, 8 - order.get(coupon_id, 8))
    contact_bonus = (2 if contacts.get(media_id) == "contact_ready" else 0) + (2 if contacts.get(coupon_id) == "contact_ready" else 0)
    score = score_media(media) + score_coupon(coupon) + rank_bonus + contact_bonus
    role = "split_scope"
    if media_id == coupon_id:
        role = "integrated_or_prime_with_subcontract"
    media_contact_status = contacts.get(media_id, "not_in_contact_plan")
    coupon_contact_status = contacts.get(coupon_id, "not_in_contact_plan")
    contacts_ready = media_contact_status == "contact_ready" and coupon_contact_status == "contact_ready"
    if score >= 18 and contacts_ready:
        decision = "preferred_split_scope"
    elif score >= 18:
        decision = "secondary_needs_contact_plan"
    else:
        decision = "hold_for_reply_or_secondary_wave"
    return {
        "pair_id": f"{media_id}__{coupon_id}",
        "media_candidate_id": media_id,
        "media_vendor": media.get("name", ""),
        "coupon_candidate_id": coupon_id,
        "coupon_vendor": coupon.get("name", ""),
        "pair_role": role,
        "score": score,
        "media_scope": "; ".join(MEDIA_FIELDS),
        "coupon_scope": "; ".join(COUPON_FIELDS),
        "shared_requirements": "; ".join(SHARED_REQUIREMENTS),
        "decision": decision,
        "media_contact_status": media_contact_status,
        "coupon_contact_status": coupon_contact_status,
    }


def build_plan(candidates: dict[str, Any], service: dict[str, Any], contacts: dict[str, Any]) -> dict[str, Any]:
    items = candidates.get("candidates", [])
    media_candidates = [item for item in items if item.get("service_type") in MEDIA_TYPES]
    coupon_candidates = [item for item in items if item.get("service_type") in COUPON_TYPES]
    integrated = [item for item in items if item.get("service_type") in INTEGRATED_TYPES]
    order = candidate_order(candidates)
    statuses = contact_status(contacts)

    pairs = []
    for media in media_candidates:
        for coupon in coupon_candidates:
            pairs.append(build_pair(media, coupon, order, statuses))
    for candidate in integrated:
        pairs.append(build_pair(candidate, candidate, order, statuses))

    pairs = sorted(pairs, key=lambda row: (row["score"], row["pair_role"] == "integrated_or_prime_with_subcontract"), reverse=True)
    preferred = [row for row in pairs if row["decision"] == "preferred_split_scope"]
    matrix = service.get("requested_matrix", {})
    return {
        "status": "split_scope_plan_ready" if pairs else "split_scope_no_pairs",
        "purpose": "Fallback execution plan if no single vendor can cover all H-A media and coupon readouts.",
        "active_candidate": candidates.get("active_candidate", service.get("active_candidate")),
        "requested_runs": matrix.get("runs", 0),
        "requested_raw_entries": matrix.get("raw_entries", 0),
        "media_fields": MEDIA_FIELDS,
        "coupon_fields": COUPON_FIELDS,
        "shared_requirements": SHARED_REQUIREMENTS,
        "pair_count": len(pairs),
        "preferred_pair_count": len(preferred),
        "pairs": pairs,
        "operating_rules": [
            "Prefer one integrated provider only if it preserves run_id-level raw rows and source files.",
            "Use split scope when media chemistry and coupon imaging/physical scoring are stronger at different vendors.",
            "Assign media fields and coupon fields explicitly before shipment; do not let either vendor pool across run_id.",
            "Merge both vendors into one completed_raw_measurements.csv before LIMINA QC.",
            "A split-scope plan authorizes execution logistics only; it is not material evidence.",
        ],
        "non_evidence_boundary": candidates.get("non_claim_boundary", ""),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# NHI-PEDOT H-A Split-Scope Execution Plan",
        "",
        "This plan is a fallback if one vendor cannot cover all H-A readouts. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result.get('active_candidate', '-')}`",
        f"**Runs:** {result['requested_runs']}",
        f"**Raw entries:** {result['requested_raw_entries']}",
        f"**Pairs:** {result['pair_count']}",
        f"**Preferred pairs:** {result['preferred_pair_count']}",
        "",
        "## Field Split",
        "",
        f"- Media fields: {', '.join(f'`{field}`' for field in result['media_fields'])}",
        f"- Coupon fields: {', '.join(f'`{field}`' for field in result['coupon_fields'])}",
        "",
        "## Preferred Pairings",
        "",
        "| Pair | Media vendor | Coupon vendor | Role | Score | Decision |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in result["pairs"][:10]:
        lines.append(
            f"| `{row['pair_id']}` | {row['media_vendor']} | {row['coupon_vendor']} | "
            f"`{row['pair_role']}` | {row['score']} | `{row['decision']}` |"
        )

    lines.extend([
        "",
        "## Shared Requirements",
        "",
    ])
    lines.extend(f"- {item}" for item in result["shared_requirements"])

    lines.extend([
        "",
        "## Operating Rules",
        "",
    ])
    lines.extend(f"- {item}" for item in result["operating_rules"])

    lines.extend([
        "",
        "## Boundary",
        "",
        result["non_evidence_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A split-scope execution plan.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--service", type=Path, default=DEFAULT_SERVICE)
    parser.add_argument("--contacts", type=Path, default=DEFAULT_CONTACTS)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_plan(load_json(args.candidates), load_json(args.service), load_json(args.contacts))
    write_csv(args.csv_out, result["pairs"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A split-scope plan: {result['status']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "split_scope_plan_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
