#!/usr/bin/env python3
"""Design the next NHI-PEDOT formulation ladder for adaptive validation."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECIPE_LOCK = ROOT / "data" / "nhi_pedot_recipe_lock_v0_2.json"
DEFAULT_DISCOVERY_RANKING = ROOT / "data" / "limina_discovery_ranking.json"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_variant_ladder.json"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_variant_ladder.csv"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_variant_ladder.md"

FIELDS = [
    "rank",
    "variant_id",
    "role",
    "trigger",
    "hydrogel_matrix",
    "pedot_pss_loading_fraction",
    "anchoring_or_surface_prep",
    "conditioning",
    "primary_readouts",
    "expected_information",
    "advance_if",
    "stop_if",
    "evidence_refs",
    "weighted_utility",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def discovery_item(ranking: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    for item in ranking.get("items", []):
        if item.get("id") == candidate_id:
            return item
    return {}


def build_ladder(recipe_lock: dict[str, Any], ranking: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_id = recipe_lock.get("candidate_id", "limina_alg_lam_pedot_lowdose_v0_2")
    lead_item = discovery_item(ranking, candidate_id)
    base_refs = recipe_lock.get("evidence_refs", []) or lead_item.get("evidence_refs", [])
    defaults = recipe_lock.get("template_defaults", {})
    lead_defaults = defaults.get("lead_nhi_pedot_low_loading", {})
    hydrogel_defaults = defaults.get("hydrogel_laminin_control", {})
    challenge_defaults = defaults.get("challenge_nhi_pedot_high_loading", {})

    base_matrix = str(lead_defaults.get("hydrogel_matrix", "alginate_laminin_2pct_wv_caso4_dmem_pedotpss"))
    base_conditioning = str(lead_defaults.get("pedot_pss_pre_rinse_protocol", "overnight_medium_conditioning_before_measurement"))
    hydrogel_matrix = str(hydrogel_defaults.get("hydrogel_matrix", "alginate_laminin_2pct_wv_caso4_dmem"))
    lead_loading = as_float(lead_defaults.get("pedot_pss_loading_fraction"), 0.006)
    high_loading = as_float(challenge_defaults.get("pedot_pss_loading_fraction"), 0.012)

    ladder = [
        {
            "variant_id": "alg_lam_hydrogel_no_pedot_control",
            "role": "matched negative material baseline",
            "trigger": "always_pair_with_every_H-A_or_H-B_batch",
            "hydrogel_matrix": hydrogel_matrix,
            "pedot_pss_loading_fraction": 0.0,
            "anchoring_or_surface_prep": "none_or_same_mea_baseline_as_lead",
            "conditioning": "same_medium_soak_as_lead",
            "primary_readouts": "pH;osmolality;conductivity;swelling;delamination;transparency;EIS_baseline_if_H-B",
            "expected_information": "Separates hydrogel/laminin effects from PEDOT:PSS-specific drift and electrical benefit.",
            "advance_if": "Lead beats this control electrically while remaining non-inferior on H-A physical and medium gates.",
            "stop_if": "Hydrogel-only control itself causes medium drift, swelling, or delamination.",
            "evidence_refs": base_refs,
            "safety_prior": 0.88,
            "electrical_prior": 0.15,
            "novelty_prior": 0.20,
            "accessibility_prior": 0.95,
            "proof_gap_penalty": 0.05,
        },
        {
            "variant_id": "alg_lam_pedot_0p3pct_safety_rescue",
            "role": "low-dose safety rescue",
            "trigger": "use_if_0p6pct_lead_has_mild_H-A_drift_or_shedding_without_hydrogel_control_failure",
            "hydrogel_matrix": base_matrix,
            "pedot_pss_loading_fraction": round(lead_loading / 2, 4),
            "anchoring_or_surface_prep": "none_initially",
            "conditioning": "extended_medium_conditioning_overnight_plus_medium_exchange",
            "primary_readouts": "pH;osmolality;conductivity;visible_shedding;swelling;transparency;EIS_if_blank_passes",
            "expected_information": "Tests whether the failure is PEDOT:PSS dose-dependent and recoverable without changing the matrix.",
            "advance_if": "H-A drift resolves and H-B still shows at least a modest impedance or charge-storage gain.",
            "stop_if": "Any PEDOT:PSS loading continues to fail medium-integrity or shedding gates.",
            "evidence_refs": base_refs,
            "safety_prior": 0.78,
            "electrical_prior": 0.42,
            "novelty_prior": 0.32,
            "accessibility_prior": 0.90,
            "proof_gap_penalty": 0.10,
        },
        {
            "variant_id": "alg_lam_pedot_0p6pct_lead",
            "role": "current first-claim lead",
            "trigger": "primary_H-A_then_H-B_then_H-C_route",
            "hydrogel_matrix": base_matrix,
            "pedot_pss_loading_fraction": lead_loading,
            "anchoring_or_surface_prep": "none_initially",
            "conditioning": base_conditioning,
            "primary_readouts": "H-A_medium_integrity;H-A_physical_stability;H-B_EIS;H-B_charge_storage;H-C_neural_health_if_H-A_H-B_pass",
            "expected_information": "Directly tests the literature-anchored cell-culture loading in the LIMINA geometry.",
            "advance_if": "Passes H-A, improves H-B electrical metrics versus hydrogel control, then remains non-inferior in H-C.",
            "stop_if": "Fails H-A blank integrity, sheds, delaminates, or loses optical access.",
            "evidence_refs": base_refs,
            "safety_prior": 0.70,
            "electrical_prior": 0.70,
            "novelty_prior": 0.45,
            "accessibility_prior": 0.88,
            "proof_gap_penalty": 0.12,
        },
        {
            "variant_id": "alg_lam_pedot_0p9pct_midpoint",
            "role": "dose-response midpoint",
            "trigger": "use_if_0p6pct_passes_H-A_but_H-B_electrical_benefit_is_borderline",
            "hydrogel_matrix": base_matrix,
            "pedot_pss_loading_fraction": round((lead_loading + high_loading) / 2, 4),
            "anchoring_or_surface_prep": "none_initially",
            "conditioning": base_conditioning,
            "primary_readouts": "H-A_medium_integrity;transparency;EIS;charge_storage;CV_drift",
            "expected_information": "Maps the benefit-versus-instability slope before jumping to the high-loading challenge.",
            "advance_if": "Electrical benefit clears threshold without new H-A failures versus 0.6 wt percent.",
            "stop_if": "Transparency, swelling, or medium drift worsens before meaningful electrical gain appears.",
            "evidence_refs": base_refs,
            "safety_prior": 0.58,
            "electrical_prior": 0.80,
            "novelty_prior": 0.48,
            "accessibility_prior": 0.84,
            "proof_gap_penalty": 0.16,
        },
        {
            "variant_id": "alg_lam_pedot_1p2pct_upper_boundary",
            "role": "high-loading boundary challenge",
            "trigger": "use_as_boundary_not_first_claim_lead",
            "hydrogel_matrix": base_matrix,
            "pedot_pss_loading_fraction": high_loading,
            "anchoring_or_surface_prep": "none_initially",
            "conditioning": base_conditioning,
            "primary_readouts": "H-A_shedding;H-A_transparency;H-B_EIS;H-B_charge_storage;CV_stability",
            "expected_information": "Defines the upper conductivity/stability boundary and protects against overpromoting the lead.",
            "advance_if": "Only as a comparator; do not promote to H-C unless it is unexpectedly clean and biologically justified.",
            "stop_if": "Any medium drift, opacity, shedding, swelling, or delamination appears.",
            "evidence_refs": base_refs,
            "safety_prior": 0.42,
            "electrical_prior": 0.88,
            "novelty_prior": 0.50,
            "accessibility_prior": 0.82,
            "proof_gap_penalty": 0.22,
        },
        {
            "variant_id": "pda_anchor_alg_lam_pedot_0p6pct",
            "role": "adhesion/window rescue",
            "trigger": "use_if_unanchored_0p6pct_passes_medium_gates_but_fails_delamination_or_window_stability",
            "hydrogel_matrix": base_matrix,
            "pedot_pss_loading_fraction": lead_loading,
            "anchoring_or_surface_prep": "polydopamine_or_oxygen_plasma_primer_record_exact_process",
            "conditioning": "same_as_lead_plus_primer_extract_blank",
            "primary_readouts": "primer_extract;delamination;electrode_window_occlusion;transparency;EIS",
            "expected_information": "Tests whether the failure mode is mechanical attachment rather than material biology.",
            "advance_if": "Delamination resolves without new extract or medium drift and electrode windows remain inspectable.",
            "stop_if": "Primer adds medium drift, opacity, or extract toxicity risk.",
            "evidence_refs": [
                *base_refs,
                "gelma_pedot_micropatterning_2026",
                "neuronal_network_material_biocompatibility_mea_2013",
            ],
            "safety_prior": 0.55,
            "electrical_prior": 0.72,
            "novelty_prior": 0.58,
            "accessibility_prior": 0.62,
            "proof_gap_penalty": 0.20,
        },
        {
            "variant_id": "alg_gel_pedot_ppy_acellular_comparator",
            "role": "high-conductivity comparator only",
            "trigger": "use_after_ALG-LAM-PEDOT_baseline_if_H-B_needs_wider_conductive_hydrogel_context",
            "hydrogel_matrix": "alginate_gelatin_pedot_or_ppy_record_exact_recipe",
            "pedot_pss_loading_fraction": "record_exact",
            "anchoring_or_surface_prep": "not_first_claim_route",
            "conditioning": "extractables_first_medium_conditioning",
            "primary_readouts": "extract_pH;osmolality;conductivity;visible_shedding;EIS;charge_storage;transparency",
            "expected_information": "Benchmarks how much electrical upside is possible with a riskier conductive hydrogel family.",
            "advance_if": "Only to acellular comparator status unless extract and neural gates are later designed.",
            "stop_if": "Any PPy/PEDOT residue, opacity, shedding, or medium drift exceeds ALG-LAM-PEDOT.",
            "evidence_refs": [
                "alg_gel_pedot_ppy_biointerface_2026",
                "conductive_hydrogels_2025",
                "iso_10993_5_cytotoxicity_extract_fda",
            ],
            "safety_prior": 0.38,
            "electrical_prior": 0.92,
            "novelty_prior": 0.62,
            "accessibility_prior": 0.45,
            "proof_gap_penalty": 0.32,
        },
    ]

    for row in ladder:
        weighted = (
            0.30 * as_float(row["safety_prior"], 0)
            + 0.25 * as_float(row["electrical_prior"], 0)
            + 0.15 * as_float(row["novelty_prior"], 0)
            + 0.20 * as_float(row["accessibility_prior"], 0)
            - 0.10 * as_float(row["proof_gap_penalty"], 0)
        )
        row["weighted_utility"] = round(weighted, 3)

    return sorted(ladder, key=lambda row: (-as_float(row["weighted_utility"], 0), row["variant_id"]))


def export_rows(ladder: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for rank, row in enumerate(ladder, start=1):
        rows.append({
            "rank": str(rank),
            "variant_id": str(row["variant_id"]),
            "role": str(row["role"]),
            "trigger": str(row["trigger"]),
            "hydrogel_matrix": str(row["hydrogel_matrix"]),
            "pedot_pss_loading_fraction": str(row["pedot_pss_loading_fraction"]),
            "anchoring_or_surface_prep": str(row["anchoring_or_surface_prep"]),
            "conditioning": str(row["conditioning"]),
            "primary_readouts": str(row["primary_readouts"]),
            "expected_information": str(row["expected_information"]),
            "advance_if": str(row["advance_if"]),
            "stop_if": str(row["stop_if"]),
            "evidence_refs": ";".join(row.get("evidence_refs", [])),
            "weighted_utility": f"{as_float(row['weighted_utility'], 0):.3f}",
        })
    return rows


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def render_report(rows: list[dict[str, str]], recipe_lock: dict[str, Any], ranking: dict[str, Any]) -> str:
    top = ranking.get("top_candidate", "-")
    lines = [
        "# NHI-PEDOT Variant Ladder",
        "",
        "This is an adaptive design ladder, not measured evidence and not a suitability claim.",
        "",
        f"**Recipe lock:** `{recipe_lock.get('id', '-')}`",
        f"**Discovery top candidate:** `{top}`",
        f"**Rows:** {len(rows)}",
        "",
        "## Ranked Variant Ladder",
        "",
        "| Rank | Utility | Variant | Role | Trigger | Primary readouts |",
        "| ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['rank']} | {row['weighted_utility']} | `{row['variant_id']}` | "
            f"{row['role']} | {row['trigger']} | {row['primary_readouts']} |"
        )

    lines.extend([
        "",
        "## Decision Logic",
        "",
        "- Keep `alg_lam_pedot_0p6pct_lead` as the first-claim route until real H-A/H-B/H-C data contradict it.",
        "- Use `alg_lam_pedot_0p3pct_safety_rescue` only if the lead shows mild PEDOT-linked H-A drift while hydrogel-only controls remain clean.",
        "- Use `alg_lam_pedot_0p9pct_midpoint` only if the lead passes H-A but H-B electrical benefit is borderline.",
        "- Use `pda_anchor_alg_lam_pedot_0p6pct` only if medium integrity is clean and the dominant failure is delamination or electrode-window instability.",
        "- Keep Alg-Gel PEDOT/PPy as an acellular comparator; it cannot displace the lead without its own extract and neural network gates.",
        "",
        "## Hard Boundary",
        "",
        "No row in this ladder can support a suitability claim until the corresponding non-synthetic measurement rows pass the active LIMINA gates.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Design adaptive NHI-PEDOT formulation ladder.")
    parser.add_argument("--recipe-lock", type=Path, default=DEFAULT_RECIPE_LOCK)
    parser.add_argument("--ranking", type=Path, default=DEFAULT_DISCOVERY_RANKING)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    recipe_lock = load_json(args.recipe_lock)
    ranking = load_json(args.ranking)
    ladder = build_ladder(recipe_lock, ranking)
    rows = export_rows(ladder)

    result = {
        "status": "designed",
        "claim_boundary": "variant ladder is not measured evidence",
        "recipe_lock": recipe_lock.get("id"),
        "top_discovery_candidate": ranking.get("top_candidate"),
        "items": rows,
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(rows, args.csv_out)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(rows, recipe_lock, ranking), encoding="utf-8")

    print(f"Designed {len(rows)} NHI-PEDOT variant ladder rows")
    print(f"Top variant: {rows[0]['variant_id'] if rows else '-'}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
