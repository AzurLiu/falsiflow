#!/usr/bin/env python3
"""Generate a synthetic failing Phase A sentinel fixture."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASS = ROOT / "data" / "fixtures" / "zrc_nd_phase_a_sentinel_pass_fixture.csv"
DEFAULT_OUT = ROOT / "data" / "fixtures" / "zrc_nd_phase_a_sentinel_fail_fixture.csv"


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(fields: list[str], rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_fail(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    for row in rows:
        if row.get("article_id") == "lead_zrc_nd_3p5m_guard" and row.get("timepoint") == "24 h":
            row["pH_final"] = "7.12"
            row["osmolality_final_mOsm_kg"] = "330"
            row["conductivity_final_mS_cm"] = "16.5"
            row["visible_precipitate"] = "true"
            row["notes"] = "synthetic failing sentinel fixture only"
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate failing ZRC-ND Phase A sentinel fixture.")
    parser.add_argument("--input", type=Path, default=DEFAULT_PASS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    fields, rows = load_csv(args.input)
    failed = make_fail(rows)
    write_csv(fields, failed, args.out)
    print(f"Generated {len(failed)} synthetic failing Phase A sentinel rows")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
