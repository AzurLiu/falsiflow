#!/usr/bin/env python3
"""Screen ZRC-ND zwitterionic coating routes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "zrc_nd_coating_routes.json"
DEFAULT_SCORES = ROOT / "data" / "zrc_nd_coating_route_scores.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_coating_route_screen.md"


WEIGHTS = {
    "pore_preservation": 0.24,
    "antifouling_evidence": 0.20,
    "cellulose_relevance": 0.16,
    "implementation_feasibility": 0.12,
    "extractables_safety": 0.12,
    "coating_durability": 0.10,
    "novelty_upside": 0.06,
}

GATES = {
    "pore_preservation": 0.70,
    "antifouling_evidence": 0.65,
    "implementation_feasibility": 0.55,
    "extractables_safety": 0.55,
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def score_route(route: dict[str, Any]) -> dict[str, Any]:
    metrics = route["metrics"]
    composite = sum(metrics[key] * weight for key, weight in WEIGHTS.items())
    gate_failures = [
        key for key, minimum in GATES.items()
        if metrics[key] < minimum
    ]
    status = "lead_route" if not gate_failures and composite >= 0.70 else "screen"
    if route["route_class"] == "no_coating_control":
        status = "control"
    return {
        "id": route["id"],
        "name": route["name"],
        "route_class": route["route_class"],
        "chemistry": route["chemistry"],
        "intended_role": route["intended_role"],
        "metrics": metrics,
        "composite_score": round(composite, 3),
        "gate_failures": gate_failures,
        "status": status,
        "advantages": route["advantages"],
        "risks": route["risks"],
        "evidence_refs": route.get("evidence_refs", []),
    }


def rank_routes(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = [score_route(route) for route in routes]
    return sorted(
        scored,
        key=lambda item: (
            item["status"] == "control",
            bool(item["gate_failures"]),
            -item["composite_score"],
            item["name"],
        ),
    )


def render_report(scored: list[dict[str, Any]]) -> str:
    lead = scored[0]
    lines = [
        "# ZRC-ND Coating Route Screen",
        "",
        "This is a route-prioritization model, not evidence that a coating is safe or effective in neural medium.",
        "",
        f"**Lead route:** `{lead['id']}` - {lead['name']}",
        f"**Lead score:** {lead['composite_score']:.3f}",
        "",
        "## Ranking",
        "",
        "| Rank | Status | Score | Route | Class | Gate failures |",
        "| ---: | --- | ---: | --- | --- | --- |",
    ]
    for index, item in enumerate(scored, start=1):
        failures = ", ".join(item["gate_failures"]) if item["gate_failures"] else "-"
        lines.append(
            f"| {index} | {item['status']} | {item['composite_score']:.3f} | "
            f"{item['name']} | {item['route_class']} | {failures} |"
        )

    lines.extend([
        "",
        "## Lead Route Detail",
        "",
        f"**Chemistry:** {lead['chemistry']}",
        "",
        f"**Intended role:** {lead['intended_role']}",
        "",
        "### Metrics",
        "",
    ])
    for key, value in lead["metrics"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "### Advantages", ""])
    lines.extend(f"- {item}" for item in lead["advantages"])
    lines.extend(["", "### Risks", ""])
    lines.extend(f"- {item}" for item in lead["risks"])
    lines.extend(["", "### Evidence Refs", ""])
    lines.extend(f"- `{item}`" for item in lead["evidence_refs"])

    lines.extend([
        "",
        "## Interpretation",
        "",
        (
            "For the first ZRC-ND-3.5M Guard coupon run, the coating route should "
            "protect the 3.5 kDa membrane pores before it tries to maximize coating "
            "density. The selected PDA/polyMPC controlled-deposition route is therefore "
            "a practical first coating route, while unmodified RC remains a mandatory "
            "baseline and PMMMSi MPC-silane remains the advanced durability backup."
        ),
        "",
        "## Required Next Evidence",
        "",
        "- Coupon-level BDNF/NGF and albumin recovery after coating.",
        "- Measured lactate/ammonium exchange before and after coating.",
        "- Fresh-medium extractables and pH/conductivity/osmolality drift for PDA/polyMPC.",
        "- Fouling drift versus unmodified RC in protein-rich conditioned-medium proxy.",
        "",
        "## Weights",
        "",
    ])
    for key, value in WEIGHTS.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Gates", ""])
    for key, value in GATES.items():
        lines.append(f"- `{key}` >= {value}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Screen ZRC-ND coating routes.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    routes = load_json(args.input)
    scored = rank_routes(routes)
    args.scores.parent.mkdir(parents=True, exist_ok=True)
    args.scores.write_text(json.dumps(scored, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(scored), encoding="utf-8")
    print(f"Lead coating route: {scored[0]['id']} ({scored[0]['composite_score']:.3f})")
    print(f"Wrote {args.scores}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
