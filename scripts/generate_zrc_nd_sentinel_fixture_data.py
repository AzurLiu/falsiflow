#!/usr/bin/env python3
"""Generate synthetic Phase A sentinel rows for merge/evaluator regression."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "data" / "zrc_nd_phase_a_sentinel_template.csv"
DEFAULT_OUT = ROOT / "data" / "fixtures" / "zrc_nd_phase_a_sentinel_pass_fixture.csv"


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


def fill_row(row: dict[str, str]) -> dict[str, str]:
    article = row.get("article_id", "")
    is_zero = row.get("timepoint") == "0 h"
    row.update({
        "date": "2026-05-23",
        "operator_or_agent": "fixture",
        "membrane_lot": "fixture_membrane_lot" if article != "no_module_static_control" else "",
        "membrane_area_cm2": "1.0" if article != "no_module_static_control" else "",
        "prefilter_lot": "fixture_guard_lot" if article != "no_module_static_control" else "",
        "medium_name": "test_medium",
        "medium_lot": "fixture_medium_lot",
        "initial_volume_ml": "1.0",
        "flow_rate_ul_min": "0",
        "exposure_time_h": "0" if is_zero else "24",
        "temperature_c": "37",
        "pH_initial": "7.40",
        "osmolality_initial_mOsm_kg": "300",
        "conductivity_initial_mS_cm": "15.0",
        "visible_precipitate": "false",
        "notes": "synthetic phase A sentinel fixture only",
    })
    if is_zero:
        row.update({
            "pH_final": "7.40",
            "osmolality_final_mOsm_kg": "300",
            "conductivity_final_mS_cm": "15.0",
        })
    elif article == "no_module_static_control":
        row.update({
            "pH_final": "7.39",
            "osmolality_final_mOsm_kg": "301",
            "conductivity_final_mS_cm": "15.01",
        })
    elif article == "lead_zrc_nd_3p5m_guard":
        row.update({
            "pH_final": "7.37",
            "osmolality_final_mOsm_kg": "305",
            "conductivity_final_mS_cm": "15.30",
        })
    elif article == "baseline_rc_3p5m_guard":
        row.update({
            "pH_final": "7.38",
            "osmolality_final_mOsm_kg": "304",
            "conductivity_final_mS_cm": "15.20",
        })
    elif article == "challenge_zrc_nd_10m_guard":
        row.update({
            "pH_final": "7.36",
            "osmolality_final_mOsm_kg": "305",
            "conductivity_final_mS_cm": "15.25",
        })
    return row


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic ZRC-ND Phase A sentinel fixture.")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    fields, rows = load_csv(args.template)
    filled = [fill_row(dict(row)) for row in rows]
    write_csv(fields, filled, args.out)
    print(f"Generated {len(filled)} synthetic Phase A sentinel rows")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
