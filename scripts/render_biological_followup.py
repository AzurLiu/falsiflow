#!/usr/bin/env python3
"""Render the ZRC-ND biological follow-up package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "zrc_nd_biological_followup_package.json"
DEFAULT_SCHEMA = ROOT / "data" / "biological_followup_schema.json"
DEFAULT_OUTPUT = ROOT / "reports" / "zrc_nd_biological_followup_package.md"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_package(package: dict[str, Any], schema: dict[str, Any]) -> None:
    missing = [
        field for field in schema["required_fields"]
        if field not in package or package[field] in ("", [], None)
    ]
    if missing:
        raise ValueError(f"{package.get('id', '<unknown>')} missing fields: {', '.join(missing)}")


def refs_text(item: dict[str, Any]) -> str:
    refs = item.get("evidence_refs", [])
    return ", ".join(f"`{ref}`" for ref in refs) if refs else "-"


def render(package: dict[str, Any]) -> str:
    lines = [
        f"# {package['title']}",
        "",
        f"**ID:** `{package['id']}`",
        f"**Parent validation package:** `{package['parent_validation_package']}`",
        f"**Lead variant:** `{package['lead_variant_id']}`",
        "",
        "## Objective",
        "",
        package["objective"],
        "",
        "## Scope",
        "",
    ]
    for key, value in package["scope"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Test Articles", "", "| ID | Variant | Role |", "| --- | --- | --- |"])
    for item in package["test_articles"]:
        variant = item["variant_id"] if item["variant_id"] else "-"
        lines.append(f"| `{item['id']}` | `{variant}` | {item['role']} |")

    lines.extend(["", "## Run Matrix", ""])
    for phase in package["run_matrix"]:
        lines.extend([
            f"### {phase['phase']}: {phase['name']}",
            "",
            f"**Purpose:** {phase['purpose']}",
            "",
            f"**Articles:** {', '.join(f'`{item}`' for item in phase['articles'])}",
            "",
            f"**Minimum replicates:** {phase['minimum_replicates']}",
            "",
            f"**Timepoints:** {', '.join(phase['timepoints'])}",
            "",
            f"**Must pass before:** {phase['must_pass_before']}",
            "",
        ])

    lines.extend(["## Assay Panel", "", "| ID | Readout | Method | Evidence |", "| --- | --- | --- | --- |"])
    for assay in package["assay_panel"]:
        lines.append(f"| `{assay['id']}` | {assay['readout']} | {assay['method_class']} | {refs_text(assay)} |")

    lines.extend(["", "## Acceptance Gates", "", "| Gate | Criterion | Failure response |", "| --- | --- | --- |"])
    for gate in package["acceptance_gates"]:
        lines.append(f"| `{gate['id']}` | {gate['criterion']} | {gate['failure_response']} |")

    lines.extend(["", "## Data Capture Fields", ""])
    lines.extend(f"- `{field}`" for field in package["data_capture_fields"])
    lines.extend(["", "## Source Refs", ""])
    lines.extend(f"- `{ref}`" for ref in package["source_refs"])
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render ZRC-ND biological follow-up package.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package = load_json(args.input)
    schema = load_json(args.schema)
    validate_package(package, schema)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(package), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
