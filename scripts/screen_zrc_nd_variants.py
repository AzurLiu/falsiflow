#!/usr/bin/env python3
"""Screen ZRC-ND design variants with an explicit heuristic model.

The model is not a physical prediction. It is a transparent prioritization
tool for deciding which material-stack variant should be tested first.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "zrc_nd_variants.json"
DEFAULT_SCORES = ROOT / "data" / "zrc_nd_variant_scores.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_variant_screen.md"


MWCO = {
    1.0: {"clearance": 0.35, "retention": 0.99, "small_signal_retention": 0.97},
    3.5: {"clearance": 0.62, "retention": 0.96, "small_signal_retention": 0.90},
    10.0: {"clearance": 0.78, "retention": 0.84, "small_signal_retention": 0.72},
    20.0: {"clearance": 0.90, "retention": 0.62, "small_signal_retention": 0.45},
}

SURFACE = {
    "none": {
        "fouling_control": 0.55,
        "retention_delta": 0.00,
        "clearance_multiplier": 1.00,
        "leachable_safety": 0.85,
        "integration": 0.95,
        "novelty": 0.35,
    },
    "mpc_like_zwitterionic": {
        "fouling_control": 0.86,
        "retention_delta": 0.04,
        "clearance_multiplier": 0.94,
        "leachable_safety": 0.70,
        "integration": 0.70,
        "novelty": 0.88,
    },
}

PREFILTER = {
    "none": {
        "debris_control": 0.35,
        "retention_delta": 0.00,
        "clearance_multiplier": 1.00,
        "integration": 0.95,
    },
    "low_binding_pes_sfca": {
        "debris_control": 0.82,
        "retention_delta": -0.02,
        "clearance_multiplier": 0.97,
        "integration": 0.84,
    },
}

HOUSING = {
    "coc_cop": {"leachable_safety": 0.82, "integration": 0.82},
    "peek": {"leachable_safety": 0.86, "integration": 0.72},
}

WEIGHTS = {
    "waste_clearance": 0.20,
    "factor_retention": 0.24,
    "fouling_control": 0.14,
    "leachable_safety": 0.14,
    "integration": 0.10,
    "monitorability": 0.08,
    "novelty": 0.10,
}

GATES = {
    "waste_clearance": 0.50,
    "factor_retention": 0.90,
    "leachable_safety": 0.65,
    "integration": 0.58,
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_variant(variant: dict[str, Any]) -> dict[str, Any]:
    mwco = MWCO[float(variant["mwco_kda"])]
    surface = SURFACE[variant["surface_modification"]]
    prefilter = PREFILTER[variant["prefilter"]]
    housing = HOUSING[variant["housing"]]

    waste_clearance = clamp(
        mwco["clearance"]
        * surface["clearance_multiplier"]
        * prefilter["clearance_multiplier"]
    )
    factor_retention = clamp(
        mwco["retention"]
        + surface["retention_delta"]
        + prefilter["retention_delta"]
    )
    fouling_control = clamp(
        max(surface["fouling_control"], 0.60)
        + 0.04 * (prefilter["debris_control"] > 0.75)
    )
    leachable_safety = clamp(
        0.45 * surface["leachable_safety"]
        + 0.45 * housing["leachable_safety"]
        + 0.10 * (0.80 if variant["prefilter"] != "none" else 0.90)
    )
    integration = clamp(
        0.45 * surface["integration"]
        + 0.35 * prefilter["integration"]
        + 0.20 * housing["integration"]
    )
    monitorability = clamp(0.45 + 0.10 * len(variant.get("monitoring", [])))
    novelty = clamp(
        0.60 * surface["novelty"]
        + 0.25 * (0.80 if variant["prefilter"] != "none" else 0.45)
        + 0.15 * (0.80 if float(variant["mwco_kda"]) in {3.5, 10.0} else 0.55)
    )

    metrics = {
        "waste_clearance": round(waste_clearance, 3),
        "factor_retention": round(factor_retention, 3),
        "fouling_control": round(fouling_control, 3),
        "leachable_safety": round(leachable_safety, 3),
        "integration": round(integration, 3),
        "monitorability": round(monitorability, 3),
        "novelty": round(novelty, 3),
    }
    composite = sum(metrics[key] * weight for key, weight in WEIGHTS.items())
    gate_failures = [
        key for key, minimum in GATES.items()
        if metrics[key] < minimum
    ]

    return {
        "id": variant["id"],
        "name": variant["name"],
        "parent_technology": variant["parent_technology"],
        "mwco_kda": variant["mwco_kda"],
        "surface_modification": variant["surface_modification"],
        "prefilter": variant["prefilter"],
        "metrics": metrics,
        "composite_score": round(composite, 3),
        "gate_failures": gate_failures,
        "lead_status": "lead" if not gate_failures and composite >= 0.78 else "screen",
        "design_intent": variant["design_intent"],
        "evidence_refs": variant.get("evidence_refs", []),
    }


def rank_variants(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = [score_variant(variant) for variant in variants]
    return sorted(
        scored,
        key=lambda item: (bool(item["gate_failures"]), -item["composite_score"], item["name"]),
    )


def render_report(scored: list[dict[str, Any]]) -> str:
    lead = scored[0]
    lines = [
        "# ZRC-ND Variant Screen",
        "",
        "This is a heuristic design-prioritization model, not an experimental result.",
        "",
        f"**Lead variant:** `{lead['id']}` - {lead['name']}",
        f"**Lead score:** {lead['composite_score']:.3f}",
        "",
        "## Ranking",
        "",
        "Rows are ordered by gate pass first, then composite score.",
        "",
        "| Rank | Status | Score | Variant | MWCO | Surface | Gate failures |",
        "| ---: | --- | ---: | --- | ---: | --- | --- |",
    ]
    for index, item in enumerate(scored, start=1):
        failures = ", ".join(item["gate_failures"]) if item["gate_failures"] else "-"
        lines.append(
            f"| {index} | {item['lead_status']} | {item['composite_score']:.3f} | "
            f"{item['name']} | {item['mwco_kda']} | {item['surface_modification']} | {failures} |"
        )

    lines.extend([
        "",
        "## Lead Metric Detail",
        "",
        f"**Design intent:** {lead['design_intent']}",
        "",
    ])
    for key, value in lead["metrics"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend([
        "",
        "## Lead Evidence Refs",
        "",
    ])
    lines.extend(f"- `{item}`" for item in lead["evidence_refs"])

    lines.extend([
        "",
        "## Model Weights",
        "",
    ])
    for key, value in WEIGHTS.items():
        lines.append(f"- `{key}`: {value}")

    lines.extend([
        "",
        "## Gates",
        "",
    ])
    for key, value in GATES.items():
        lines.append(f"- `{key}` >= {value}")

    lines.extend([
        "",
        "## Interpretation",
        "",
        (
            "The lead favors 3.5 kDa regenerated cellulose because the model treats "
            "trophic-factor retention as more important than maximum waste clearance "
            "for the first neural-medium cartridge. The MPC-like zwitterionic layer "
            "raises fouling control and protein-retention confidence, but it remains "
            "a validation risk because coating chemistry can change permeability and "
            "introduce extractables."
        ),
        "",
        "## Required Next Evidence",
        "",
        "- Measured lactate and ammonium clearance for 3.5 kDa versus 10 kDa RC.",
        "- BDNF/NGF or proxy trophic-factor recovery across unmodified and zwitterionic surfaces.",
        "- Fresh-medium blank extractables, pH, osmolality, and conductivity drift.",
        "- Fouling/flow-resistance drift in protein-rich conditioned medium.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Screen ZRC-ND material-stack variants.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    variants = load_json(args.input)
    scored = rank_variants(variants)
    args.scores.parent.mkdir(parents=True, exist_ok=True)
    args.scores.write_text(json.dumps(scored, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(scored), encoding="utf-8")
    print(f"Lead variant: {scored[0]['id']} ({scored[0]['composite_score']:.3f})")
    print(f"Wrote {args.scores}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
