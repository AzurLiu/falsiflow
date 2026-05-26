#!/usr/bin/env python3
"""Render LIMINA experiment design JSON into Markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "external1_baseline_experiment.json"
DEFAULT_SCHEMA = ROOT / "data" / "experiment_schema.json"
DEFAULT_OUTPUT = ROOT / "reports" / "external1_baseline_experiment.md"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_experiment(experiment: dict[str, Any], schema: dict[str, Any]) -> None:
    missing = [
        field for field in schema["required_fields"]
        if field not in experiment or experiment[field] in ("", [], None)
    ]
    if missing:
        raise ValueError(f"{experiment.get('id', '<unknown>')} missing fields: {', '.join(missing)}")


def bullet_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def render(experiment: dict[str, Any]) -> str:
    lines = [
        f"# {experiment['title']}",
        "",
        f"**ID:** `{experiment['id']}`",
        f"**Priority lane:** `{experiment['priority_lane']}`",
        "",
        "## Objective",
        "",
        experiment["objective"],
        "",
        "## Hypothesis",
        "",
        experiment["hypothesis"],
        "",
        "## Scope",
        "",
    ]

    for key, value in experiment["scope"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend([
        "",
        "## Test Articles",
        "",
        "| ID | Name | Rationale | Expected trade-off |",
        "| --- | --- | --- | --- |",
    ])
    for item in experiment["test_articles"]:
        lines.append(
            f"| `{item['id']}` | {item['name']} | {item['rationale']} | "
            f"{item['expected_tradeoff']} |"
        )

    lines.extend([
        "",
        "## Controls",
        "",
        "| ID | Control | Purpose |",
        "| --- | --- | --- |",
    ])
    for item in experiment["controls"]:
        lines.append(f"| `{item['id']}` | {item['name']} | {item['purpose']} |")

    lines.extend(["", "## Readouts", ""])
    for group, readouts in experiment["readouts"].items():
        lines.append(f"### {group.replace('_', ' ').title()}")
        lines.append("")
        lines.extend(bullet_list(readouts))
        lines.append("")

    lines.extend([
        "## Decision Gates",
        "",
        "| Gate | Criterion | Failure response |",
        "| --- | --- | --- |",
    ])
    for gate in experiment["decision_gates"]:
        lines.append(f"| `{gate['id']}` | {gate['criterion']} | {gate['failure_response']} |")

    lines.extend([
        "",
        "## Risk Controls",
        "",
        "| Risk | Detection |",
        "| --- | --- |",
    ])
    for item in experiment["risk_controls"]:
        lines.append(f"| {item['risk']} | {item['detection']} |")

    lines.extend([
        "",
        "## Next Decisions",
        "",
        "| Condition | Action |",
        "| --- | --- |",
    ])
    for item in experiment["next_decisions"]:
        lines.append(f"| {item['condition']} | {item['action']} |")

    lines.extend(["", "## Source Refs", ""])
    lines.extend([f"- `{ref}`" for ref in experiment["source_refs"]])
    lines.append("")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a LIMINA experiment plan.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    experiment = load_json(args.input)
    schema = load_json(args.schema)
    validate_experiment(experiment, schema)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(experiment), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
