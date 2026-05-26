#!/usr/bin/env python3
"""Rank LIMINA discovery prospects for the next material-technology push."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "data" / "limina_discovery_candidates.json"
DEFAULT_PROFILE = ROOT / "data" / "limina_discovery_scoring_profile.json"
DEFAULT_EVIDENCE = ROOT / "data" / "evidence_records_seed.json"
DEFAULT_JSON = ROOT / "data" / "limina_discovery_ranking.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_discovery_ranking.md"


@dataclass(frozen=True)
class RankedProspect:
    record: dict[str, Any]
    weighted_score: float
    gate_failures: list[str]

    @property
    def priority(self) -> str:
        if self.gate_failures:
            return "hold"
        if self.weighted_score >= 4.1:
            return "promote_now"
        if self.weighted_score >= 3.5:
            return "parallel_screen"
        if self.weighted_score >= 3.0:
            return "watch"
        return "deprioritize"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def evidence_lookup(path: Path) -> dict[str, dict[str, Any]]:
    records = load_json(path)
    return {record["id"]: record for record in records}


def score_record(record: dict[str, Any], profile: dict[str, Any]) -> RankedProspect:
    weights = profile["weights"]
    scores = record.get("scores", {})
    missing = [field for field in weights if field not in scores]
    if missing:
        raise ValueError(f"{record.get('id', '<unknown>')} missing scores: {', '.join(missing)}")
    weighted_score = sum(float(scores[field]) * float(weight) for field, weight in weights.items())
    gate_failures = []
    for gate in profile.get("gates", []):
        field = gate["field"]
        if float(scores.get(field, 0)) < float(gate["minimum"]):
            gate_failures.append(f"{field} below {gate['minimum']}: {gate['reason']}")
    return RankedProspect(record=record, weighted_score=round(weighted_score, 3), gate_failures=gate_failures)


def rank(records: list[dict[str, Any]], profile: dict[str, Any]) -> list[RankedProspect]:
    ranked = [score_record(record, profile) for record in records]
    return sorted(ranked, key=lambda item: (bool(item.gate_failures), -item.weighted_score, item.record["name"]))


def evidence_links(refs: list[str], known: dict[str, dict[str, Any]]) -> str:
    links = []
    for ref in refs:
        record = known.get(ref)
        if record:
            links.append(f"[{ref}]({record['source_url']})")
        else:
            links.append(f"`{ref}`")
    return ", ".join(links) or "-"


def export_json(ranked: list[RankedProspect]) -> dict[str, Any]:
    top = ranked[0] if ranked else None
    return {
        "status": "ranked",
        "top_candidate": top.record["id"] if top else None,
        "top_priority": top.priority if top else None,
        "items": [
            {
                "rank": index,
                "id": item.record["id"],
                "name": item.record["name"],
                "lane": item.record["lane"],
                "status": item.record["status"],
                "priority": item.priority,
                "weighted_score": item.weighted_score,
                "gate_failures": item.gate_failures,
                "near_term_test": item.record["near_term_test"],
                "evidence_refs": item.record.get("evidence_refs", []),
                "known_risks": item.record.get("known_risks", []),
            }
            for index, item in enumerate(ranked, start=1)
        ],
    }


def render_report(ranked: list[RankedProspect], known: dict[str, dict[str, Any]]) -> str:
    lines = [
        "# LIMINA Discovery Ranking",
        "",
        "This ranks material-technology prospects by how quickly they can generate defensible evidence toward the first suitability claim. It is not a suitability claim.",
        "",
    ]
    if ranked:
        top = ranked[0]
        lines.extend([
            f"**Top prospect:** `{top.record['id']}`",
            f"**Priority:** `{top.priority}`",
            f"**Weighted score:** `{top.weighted_score:.3f}`",
            "",
        ])

    lines.extend([
        "## Ranked Prospects",
        "",
        "| Rank | Priority | Score | Prospect | Lane | Near-term test | Main risks |",
        "| ---: | --- | ---: | --- | --- | --- | --- |",
    ])
    for index, item in enumerate(ranked, start=1):
        risks = "; ".join(item.record.get("known_risks", []))
        lines.append(
            f"| {index} | `{item.priority}` | {item.weighted_score:.3f} | "
            f"`{item.record['id']}` | {item.record['lane']} | {item.record['near_term_test']} | {risks} |"
        )

    lines.extend(["", "## Evidence And Rationale", ""])
    for item in ranked:
        lines.extend([
            f"### {item.record['id']}",
            "",
            f"- Name: {item.record['name']}",
            f"- Status: `{item.record['status']}`",
            f"- Why it matters: {item.record['why_it_matters']}",
            f"- Evidence: {evidence_links(item.record.get('evidence_refs', []), known)}",
        ])
        if item.gate_failures:
            lines.append("- Gate failures:")
            lines.extend(f"  - {failure}" for failure in item.gate_failures)
        else:
            lines.append("- Gate failures: none.")
        lines.append("")

    lines.extend([
        "## Interpretation",
        "",
        "- The queue promotes `limina_alg_lam_pedot_lowdose_v0_2` because it has the clearest direct neural-culture evidence and can reuse the existing NHI-PEDOT gates.",
        "- New 2026 electronic-ECM, anisotropic S-PEDOT/PSBMA, Alg-Gel PEDOT/PPy, MLMEA/organoid-electrode, and zwitterionic-mechanics leads expand the exploration space but remain behind the first-claim route until extractables, stability, fabrication access, and direct neuronal-network gates are measured.",
        "- High-novelty hydrogels and 3D organoid architectures remain valuable, but they are behind the first-claim path until procurement, simplified witness coupons, extract chemistry, and neural culture compatibility are clearer.",
        "- ZRC-ND still remains the external-material branch; the all-dry zwitterionic coating is a rescue/enhancement option if sentinel data show fouling or adsorption.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rank LIMINA discovery material prospects.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    records = load_json(args.candidates)
    profile = load_json(args.profile)
    known = evidence_lookup(args.evidence)
    ranked = rank(records, profile)
    result = export_json(ranked)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(ranked, known), encoding="utf-8")
    print(f"Top discovery prospect: {result['top_candidate']}")
    print(f"Priority: {result['top_priority']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
