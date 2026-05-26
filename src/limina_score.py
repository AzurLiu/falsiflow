#!/usr/bin/env python3
"""Scoring utilities for LIMINA candidate material technologies."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: dict[str, Any]
    weighted_score: float
    gate_failures: list[str]

    @property
    def id(self) -> str:
        return str(self.candidate["id"])

    @property
    def name(self) -> str:
        return str(self.candidate["name"])

    @property
    def priority(self) -> str:
        if self.gate_failures:
            return "hold"
        if self.weighted_score >= 4.2:
            return "top"
        if self.weighted_score >= 3.7:
            return "high"
        if self.weighted_score >= 3.2:
            return "watch"
        return "low"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def score_candidate(candidate: dict[str, Any], profile: dict[str, Any]) -> ScoredCandidate:
    scores = candidate.get("scores", {})
    weights = profile["weights"]

    missing = [name for name in weights if name not in scores]
    if missing:
        raise ValueError(f"{candidate.get('id', '<unknown>')} missing scores: {', '.join(missing)}")

    weighted_score = sum(float(scores[name]) * float(weight) for name, weight in weights.items())
    gate_failures = []
    for gate in profile.get("gates", []):
        field = gate["field"]
        minimum = float(gate["minimum"])
        if float(scores[field]) < minimum:
            gate_failures.append(f"{field} below {minimum:g}: {gate['reason']}")

    return ScoredCandidate(
        candidate=candidate,
        weighted_score=round(weighted_score, 3),
        gate_failures=gate_failures,
    )


def score_all(candidates: list[dict[str, Any]], profile: dict[str, Any]) -> list[ScoredCandidate]:
    scored = [score_candidate(candidate, profile) for candidate in candidates]
    return sorted(scored, key=lambda item: (bool(item.gate_failures), -item.weighted_score, item.name))


def to_markdown(scored: list[ScoredCandidate]) -> str:
    lines = [
        "# LIMINA Candidate Ranking",
        "",
        "| Rank | Priority | Score | Candidate | Main risks |",
        "| ---: | --- | ---: | --- | --- |",
    ]
    for index, item in enumerate(scored, start=1):
        risks = "; ".join(item.candidate.get("known_risks", []))
        lines.append(
            f"| {index} | {item.priority} | {item.weighted_score:.3f} | "
            f"{item.name} | {risks} |"
        )

    lines.append("")
    lines.append("## Gate Holds")
    holds = [item for item in scored if item.gate_failures]
    if not holds:
        lines.append("")
        lines.append("No candidates failed the current gates.")
    else:
        for item in holds:
            lines.append("")
            lines.append(f"- **{item.name}**")
            for failure in item.gate_failures:
                lines.append(f"  - {failure}")

    return "\n".join(lines) + "\n"
