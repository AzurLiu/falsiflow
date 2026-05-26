#!/usr/bin/env python3
"""Generate synthetic raw NHI-PEDOT H-A fixtures for pipeline regression tests."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "data" / "nhi_pedot_h_a_raw_measurements_template.csv"
DEFAULT_PASS = ROOT / "data" / "fixtures" / "nhi_pedot_h_a_raw_full_pass_fixture.csv"
DEFAULT_FAIL = ROOT / "data" / "fixtures" / "nhi_pedot_h_a_raw_lead_fail_fixture.csv"


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


def value_for(row: dict[str, str], lead_fail: bool) -> str:
    run_id = row["run_id"]
    event = row["sample_event"]
    target = row["target_field"]
    is_lead_fail = lead_fail and "lead_nhi_pedot_low_loading-R1-24h" in run_id

    if event == "metadata":
        values = {
            "date": "2026-05-23",
            "medium_name": "CL1_proxy_medium_A",
            "medium_lot": "MED-LOT-001",
            "temperature_c": "37",
            "mea_coupon_id": f"{run_id}-coupon",
            "electrode_material": "MEA_witness_gold_or_ITO",
            "laminin_or_peptide_density": "EHS_laminin_lot_LAM-001",
            "sterilization_or_aseptic_protocol": "aseptic_preparation_lot_AP-001",
        }
        return values.get(target, "")

    if event == "initial":
        values = {
            "pH": "7.40",
            "osmolality": "300",
            "conductivity": "14.0",
        }
        return values.get(target, "")

    if event == "final":
        if is_lead_fail and target == "pH":
            return "7.72"
        values = {
            "pH": "7.41",
            "osmolality": "302",
            "conductivity": "14.1",
        }
        return values.get(target, "")

    if event == "physical_inspection":
        if is_lead_fail and target == "visible_shedding":
            return "true"
        values = {
            "visible_precipitate": "false",
            "visible_shedding": "false",
            "swelling_fraction": "0.05",
            "delamination_score": "0",
            "optical_transparency_fraction": "0.92",
        }
        return values.get(target, "")

    return ""


def build_rows(template_rows: list[dict[str, str]], lead_fail: bool) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for original in template_rows:
        row = dict(original)
        row["value"] = value_for(row, lead_fail)
        row["measured_at"] = "2026-05-23T09:00:00"
        row["operator_or_agent"] = "synthetic_fixture_operator"
        row["instrument_id"] = "synthetic_fixture_instrument"
        row["source_file"] = "synthetic_fixture_not_material_evidence.csv"
        row["notes"] = "synthetic_fixture_not_material_evidence"
        rows.append(row)
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic NHI-PEDOT H-A raw fixtures.")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--pass-out", type=Path, default=DEFAULT_PASS)
    parser.add_argument("--fail-out", type=Path, default=DEFAULT_FAIL)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    fields, template_rows = load_csv(args.template)
    pass_rows = build_rows(template_rows, lead_fail=False)
    fail_rows = build_rows(template_rows, lead_fail=True)
    write_csv(fields, pass_rows, args.pass_out)
    write_csv(fields, fail_rows, args.fail_out)
    print(f"Wrote {args.pass_out}")
    print(f"Wrote {args.fail_out}")
    print(f"Rows per fixture: {len(pass_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
