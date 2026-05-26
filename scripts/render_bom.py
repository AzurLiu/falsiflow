#!/usr/bin/env python3
"""Render a LIMINA BOM JSON into Markdown."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "zrc_nd_bom.json"
DEFAULT_SCHEMA = ROOT / "data" / "bom_schema.json"
DEFAULT_OUTPUT = ROOT / "reports" / "zrc_nd_bom.md"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_bom(bom: dict[str, Any], schema: dict[str, Any]) -> None:
    missing = [
        field for field in schema["required_fields"]
        if field not in bom or bom[field] in ("", [], None)
    ]
    if missing:
        raise ValueError(f"{bom.get('id', '<unknown>')} missing fields: {', '.join(missing)}")


def refs_text(item: dict[str, Any]) -> str:
    refs = item.get("evidence_refs", [])
    return ", ".join(f"`{ref}`" for ref in refs) if refs else "-"


def source_text(item: dict[str, Any]) -> str:
    url = item.get("anchor_source_url", "")
    if not url:
        return "-"
    return f"[source]({url})"


def render(bom: dict[str, Any]) -> str:
    lines = [
        f"# {bom['title']}",
        "",
        f"**ID:** `{bom['id']}`",
        f"**Parent validation package:** `{bom['parent_validation_package']}`",
        "",
        "## Objective",
        "",
        bom["objective"],
        "",
        "## Items",
        "",
    ]

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in bom["items"]:
        grouped[item["category"]].append(item)

    for category in sorted(grouped):
        lines.extend([
            f"### {category.replace('_', ' ').title()}",
            "",
            "| ID | Role | Required spec | Anchor | Reject if | Evidence |",
            "| --- | --- | --- | --- | --- | --- |",
        ])
        for item in grouped[category]:
            anchor = f"{item['anchor_product']} {source_text(item)}"
            lines.append(
                f"| `{item['id']}` | {item['role']} | {item['required_spec']} | "
                f"{anchor} | {item['reject_if']} | {refs_text(item)} |"
            )
        lines.append("")

    lines.extend(["## Source Refs", ""])
    lines.extend(f"- `{ref}`" for ref in bom["source_refs"])
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a LIMINA BOM.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    bom = load_json(args.input)
    schema = load_json(args.schema)
    validate_bom(bom, schema)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(bom), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
