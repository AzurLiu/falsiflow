#!/usr/bin/env python3
"""Render a LIMINA material technology dossier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "data" / "technology_schema.json"
DEFAULT_INPUT = ROOT / "data" / "limina_material_technologies.json"
DEFAULT_OUTPUT = ROOT / "reports" / "first_material_technology.md"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_record(record: dict[str, Any], schema: dict[str, Any]) -> None:
    missing = [
        field for field in schema["required_fields"]
        if field not in record or record[field] in ("", [], None)
    ]
    if missing:
        raise ValueError(f"{record.get('id', '<unknown>')} missing: {', '.join(missing)}")


def render(record: dict[str, Any]) -> str:
    lines = [
        f"# {record['name']}",
        "",
        f"**ID:** `{record['id']}`",
        f"**Priority lane:** `{record['priority_lane']}`",
        f"**Status:** `{record['status']}`",
        "",
        record["one_line"],
        "",
        "## Design Claim",
        "",
        record["design_claim"],
        "",
        "## Core Material Stack",
        "",
        "| Layer | Material | Function |",
        "| --- | --- | --- |",
    ]
    for item in record["core_material_stack"]:
        lines.append(f"| {item['layer']} | {item['material']} | {item['function']} |")

    lines.extend(["", "## Why This Is New For LIMINA", ""])
    lines.extend(f"- {item}" for item in record["why_it_is_new_for_limina"])

    lines.extend(["", "## Fit To Requirements", ""])
    for key, value in record["fit_to_requirements"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Validation Plan", ""])
    lines.extend(f"- {item}" for item in record["validation_plan"])

    lines.extend(["", "## Kill Criteria", ""])
    lines.extend(f"- {item}" for item in record["kill_criteria"])

    lines.extend(["", "## Open Questions", ""])
    lines.extend(f"- {item}" for item in record["open_questions"])

    lines.extend(["", "## Internal Score", ""])
    for key, value in record["score"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Evidence Refs", ""])
    lines.extend(f"- `{item}`" for item in record["evidence_refs"])
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a LIMINA material technology dossier.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--id", default=None, help="Technology id to render. Defaults to first record.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    schema = load_json(args.schema)
    records = load_json(args.input)
    if isinstance(records, dict):
        records = [records]
    if args.id:
        matches = [record for record in records if record.get("id") == args.id]
        if not matches:
            raise ValueError(f"No technology with id {args.id}")
        record = matches[0]
    else:
        record = records[0]
    validate_record(record, schema)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(record), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
