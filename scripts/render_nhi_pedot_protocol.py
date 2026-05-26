#!/usr/bin/env python3
"""Render the recipe-specific ALG-LAM-PEDOT protocol handoff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "data" / "nhi_pedot_alg_lam_protocol_v0_2.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_alg_lam_protocol.md"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_mapping(title: str, values: dict[str, Any]) -> list[str]:
    lines = [f"## {title}", "", "| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        lines.append(f"| `{key}` | {str(value)} |")
    lines.append("")
    return lines


def render_defaults(defaults: dict[str, dict[str, str]]) -> list[str]:
    lines = ["## H-A Template Defaults", ""]
    for article_id, values in defaults.items():
        lines.extend([f"### {article_id}", "", "| Field | Value |", "| --- | --- |"])
        for key, value in values.items():
            lines.append(f"| `{key}` | {value} |")
        lines.append("")
    return lines


def render_report(protocol: dict[str, Any]) -> str:
    lines = [
        "# ALG-LAM-PEDOT Protocol Handoff",
        "",
        f"**Protocol:** `{protocol['id']}`",
        f"**Candidate:** `{protocol['candidate_id']}`",
        f"**Source evidence:** `{protocol['source_evidence']}`",
        f"**Source URL:** {protocol['source_url']}",
        "",
        protocol["purpose"],
        "",
    ]
    lines.extend(render_mapping("Literature Recipe Anchor", protocol["literature_recipe_anchor"]))
    lines.extend(render_defaults(protocol["limina_h_a_defaults"]))
    lines.extend([
        "## Fields That Must Become Real Measurements",
        "",
    ])
    lines.extend(f"- `{field}`" for field in protocol["fields_that_must_be_replaced_by_real_measurement"])
    lines.append("")
    lines.extend(render_mapping("H-A Interpretation", protocol["h_a_interpretation"]))
    lines.extend([
        "## Boundary",
        "",
        "- These defaults are protocol scaffolding, not evidence.",
        "- Rows still fail claim provenance until dates, lots, coupon IDs, measured media chemistry, and physical readouts are filled with real values.",
        "- The low-loading lead is the first-claim path; the high-loading article is a stress comparator.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT ALG-LAM protocol.")
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    protocol = load_json(args.protocol)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(protocol), encoding="utf-8")
    print(f"Rendered protocol: {protocol['id']}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
