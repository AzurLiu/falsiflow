#!/usr/bin/env python3
"""Generate the NHI-PEDOT forward H-B/H-C gate package."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "nhi_pedot_validation_package.json"
DEFAULT_PLANNED = ROOT / "data" / "nhi_pedot_planned_runs.csv"
DEFAULT_H_A = ROOT / "data" / "nhi_pedot_h_a_sentinel_interpretation.json"
DEFAULT_LADDER = ROOT / "data" / "nhi_pedot_variant_ladder.json"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_forward_gate_package.json"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_forward_gate_rows.csv"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_forward_gate_package.md"

PHASES = ("H-B", "H-C")
FORWARD_ARTICLES = {
    "H-B": [
        "hydrogel_laminin_control",
        "lead_nhi_pedot_low_loading",
        "challenge_nhi_pedot_high_loading",
    ],
    "H-C": [
        "laminin_only_control",
        "hydrogel_laminin_control",
        "lead_nhi_pedot_low_loading",
        "challenge_nhi_pedot_high_loading",
    ],
}
PHASE_READOUT_FIELDS = {
    "H-B": [
        "swelling_fraction",
        "delamination_score",
        "optical_transparency_fraction",
        "eis_1khz_initial_ohm",
        "eis_1khz_final_ohm",
        "charge_storage_capacity_initial",
        "charge_storage_capacity_final",
    ],
    "H-C": [
        "cell_model",
        "seeding_density",
        "viability_fraction",
        "ldh_fold_control",
        "neurite_coverage_fraction",
        "mean_neurite_length_um",
        "electrode_yield_fraction",
        "spike_rate_hz",
        "burst_rate_hz",
    ],
}
COMMON_PROVENANCE_FIELDS = [
    "date",
    "operator_or_agent",
    "mea_coupon_id",
    "electrode_material",
    "hydrogel_matrix",
    "pedot_pss_loading_fraction",
    "pedot_pss_pre_rinse_protocol",
    "laminin_or_peptide_density",
    "crosslinking_protocol",
    "sterilization_or_aseptic_protocol",
    "medium_name",
    "medium_lot",
    "temperature_c",
    "source_file",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    fields = [
        "priority",
        "run_id",
        "phase",
        "timepoint",
        "replicate",
        "article_id",
        "variant_id",
        "control_article_id",
        "required_fields",
        "gate_focus",
        "activation_condition",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def package_gate_lookup(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {gate["id"]: gate for gate in package.get("acceptance_gates", [])}


def package_phase_lookup(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {phase["phase"]: phase for phase in package.get("run_matrix", [])}


def ladder_lookup(ladder: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["variant_id"]: item for item in ladder.get("items", []) if item.get("variant_id")}


def phase_gate_ids(phase: str) -> list[str]:
    if phase == "H-B":
        return ["physical_stability_gate", "electrochemical_benefit_gate"]
    if phase == "H-C":
        return ["neural_health_gate", "network_activity_gate"]
    return []


def sorted_forward_rows(planned: list[dict[str, str]], phase: str) -> list[dict[str, str]]:
    articles = set(FORWARD_ARTICLES[phase])
    phase_rows = [
        row for row in planned
        if row.get("phase") == phase
        and row.get("replicate") == "1"
        and row.get("article_id") in articles
    ]
    article_order = {article: index for index, article in enumerate(FORWARD_ARTICLES[phase])}
    time_order = {
        "pre-soak": 0,
        "24 h soak": 1,
        "72 h soak": 2,
        "post-cycling": 3,
        "24 h": 0,
        "7 d": 1,
        "14 d": 2,
    }
    return sorted(phase_rows, key=lambda row: (
        article_order.get(row.get("article_id", ""), 99),
        time_order.get(row.get("timepoint", ""), 99),
        row.get("run_id", ""),
    ))


def flatten_rows(planned: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    priority = 1
    for phase in PHASES:
        fields = ";".join(COMMON_PROVENANCE_FIELDS + PHASE_READOUT_FIELDS[phase])
        gate_focus = ";".join(phase_gate_ids(phase))
        default_activation = "after_H-A_pass" if phase == "H-B" else "after_H-B_pass"
        for row in sorted_forward_rows(planned, phase):
            activation = default_activation
            if phase == "H-C" and "28 d" in row.get("timepoint", ""):
                activation = "after_H-C_24h_7d_14d_early_gates_pass"
            rows.append({
                "priority": str(priority),
                "run_id": row.get("run_id", ""),
                "phase": phase,
                "timepoint": row.get("timepoint", ""),
                "replicate": row.get("replicate", ""),
                "article_id": row.get("article_id", ""),
                "variant_id": row.get("variant_id", ""),
                "control_article_id": row.get("control_article_id", ""),
                "required_fields": fields,
                "gate_focus": gate_focus,
                "activation_condition": activation,
            })
            priority += 1
    return rows


def build_package(
    validation_package: dict[str, Any],
    planned: list[dict[str, str]],
    h_a: dict[str, Any],
    ladder: dict[str, Any],
) -> dict[str, Any]:
    gates = package_gate_lookup(validation_package)
    phases = package_phase_lookup(validation_package)
    ladder_items = ladder_lookup(ladder)
    forward_rows = flatten_rows(planned)
    h_a_status = h_a.get("status", "unknown")
    h_a_ready = h_a_status in {
        "h_a_lead_passes_continue_h_b",
        "h_a_lead_passes_continue_challenge_boundary",
        "h_a_lead_passes_hydrogel_control_issue",
    }
    return {
        "status": "ready_to_activate_h_b" if h_a_ready else "preregistered_waiting_for_h_a",
        "purpose": "Pre-register the next H-B/H-C evidence gates for the ALG-LAM-PEDOT first-claim route.",
        "active_candidate": "limina_alg_lam_pedot_lowdose_v0_2",
        "parent_validation_package": validation_package.get("id"),
        "h_a_status": h_a_status,
        "activation_rule": "Run H-B only after H-A has QC-clean real rows and an H-A pass/continue status.",
        "rows": forward_rows,
        "row_count": len(forward_rows),
        "phase_packages": [
            {
                "phase": phase,
                "name": phases.get(phase, {}).get("name", ""),
                "activation_condition": "after_H-A_pass" if phase == "H-B" else "after_H-B_pass",
                "articles": FORWARD_ARTICLES[phase],
                "timepoints": phases.get(phase, {}).get("timepoints", []),
                "required_fields": COMMON_PROVENANCE_FIELDS + PHASE_READOUT_FIELDS[phase],
                "gate_ids": phase_gate_ids(phase),
                "gates": [
                    {
                        "id": gate_id,
                        "criterion": gates.get(gate_id, {}).get("criterion", ""),
                        "failure_response": gates.get(gate_id, {}).get("failure_response", ""),
                    }
                    for gate_id in phase_gate_ids(phase)
                ],
            }
            for phase in PHASES
        ],
        "variant_triggers": [
            {
                "variant_id": "alg_lam_pedot_0p9pct_midpoint",
                "trigger": ladder_items.get("alg_lam_pedot_0p9pct_midpoint", {}).get("trigger", "H-B borderline electrical benefit"),
            },
            {
                "variant_id": "pda_anchor_alg_lam_pedot_0p6pct",
                "trigger": ladder_items.get("pda_anchor_alg_lam_pedot_0p6pct", {}).get("trigger", "H-A/H-B mechanical-window instability with clean medium gates"),
            },
            {
                "variant_id": "alg_lam_pedot_0p3pct_safety_rescue",
                "trigger": ladder_items.get("alg_lam_pedot_0p3pct_safety_rescue", {}).get("trigger", "mild PEDOT-linked medium drift or shedding"),
            },
        ],
        "non_claim_boundary": (
            "This package is a preregistered next-step plan. It is not evidence and cannot support "
            "a material suitability claim without real measured rows and the final claim audit."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# NHI-PEDOT Forward H-B/H-C Gate Package",
        "",
        "This preregisters the next evidence gates after H-A. It is not measured evidence and not a material suitability claim.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result['active_candidate']}`",
        f"**H-A status:** `{result['h_a_status']}`",
        f"**Forward rows:** {result['row_count']}",
        f"**Activation rule:** {result['activation_rule']}",
        "",
        "## Phase Packages",
        "",
    ]
    for phase in result["phase_packages"]:
        lines.extend([
            f"### {phase['phase']} - {phase['name']}",
            "",
            f"- Activation: `{phase['activation_condition']}`",
            f"- Articles: {', '.join(f'`{article}`' for article in phase['articles'])}",
            f"- Timepoints: {', '.join(phase['timepoints'])}",
            f"- Required fields: {', '.join(f'`{field}`' for field in phase['required_fields'])}",
            "",
            "| Gate | Criterion | Failure response |",
            "| --- | --- | --- |",
        ])
        for gate in phase["gates"]:
            lines.append(f"| `{gate['id']}` | {gate['criterion']} | {gate['failure_response']} |")
        lines.append("")

    lines.extend([
        "## First Activated Rows",
        "",
        "| Priority | Phase | Run | Article | Timepoint | Activation | Gate focus |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ])
    for row in result["rows"]:
        lines.append(
            f"| {row['priority']} | {row['phase']} | `{row['run_id']}` | "
            f"`{row['article_id']}` | {row['timepoint']} | `{row['activation_condition']}` | "
            f"{row['gate_focus']} |"
        )

    lines.extend([
        "",
        "## Variant Triggers",
        "",
    ])
    lines.extend(f"- `{item['variant_id']}`: {item['trigger']}" for item in result["variant_triggers"])
    lines.extend([
        "",
        "## Boundary",
        "",
        result["non_claim_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate NHI-PEDOT forward H-B/H-C gate package.")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--planned", type=Path, default=DEFAULT_PLANNED)
    parser.add_argument("--h-a", type=Path, default=DEFAULT_H_A)
    parser.add_argument("--variant-ladder", type=Path, default=DEFAULT_LADDER)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_package(
        load_json(args.package),
        load_csv(args.planned),
        load_json(args.h_a),
        load_json(args.variant_ladder),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(result["rows"], args.csv_out)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"NHI-PEDOT forward gate package: {result['status']}")
    print(f"Rows: {result['row_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
