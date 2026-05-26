#!/usr/bin/env python3
"""Generate synthetic NHI-PEDOT fixture rows for evaluator regression tests."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLANNED = ROOT / "data" / "nhi_pedot_planned_runs.csv"
DEFAULT_PASS = ROOT / "data" / "fixtures" / "nhi_pedot_runs_full_pass_fixture.csv"
DEFAULT_FAIL = ROOT / "data" / "fixtures" / "nhi_pedot_runs_lead_fail_fixture.csv"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def set_medium_pass(row: dict[str, str]) -> None:
    row.update({
        "date": "synthetic_fixture_not_evidence",
        "medium_name": "synthetic_neural_medium",
        "medium_lot": "fixture",
        "temperature_c": "37",
        "pH_initial": "7.40",
        "pH_final": "7.41",
        "osmolality_initial_mOsm_kg": "300",
        "osmolality_final_mOsm_kg": "302",
        "conductivity_initial_mS_cm": "14.0",
        "conductivity_final_mS_cm": "14.1",
        "visible_precipitate": "false",
        "visible_shedding": "false",
    })


def set_physical_pass(row: dict[str, str]) -> None:
    row.update({
        "hydrogel_modulus_kpa": "3.0",
        "hydrogel_thickness_um": "80",
        "swelling_fraction": "0.05",
        "delamination_score": "0",
        "optical_transparency_fraction": "0.92",
    })


def set_electrochemical(row: dict[str, str]) -> None:
    article = row["article_id"]
    values = {
        "no_coating_mea_control": ("1200", "1150", "0.5", "0.5"),
        "laminin_only_control": ("1100", "1050", "0.6", "0.6"),
        "hydrogel_laminin_control": ("950", "900", "0.8", "0.8"),
        "lead_nhi_pedot_low_loading": ("850", "620", "0.9", "1.20"),
        "challenge_nhi_pedot_high_loading": ("750", "520", "1.0", "1.45"),
    }
    initial_eis, final_eis, initial_csc, final_csc = values.get(article, values["hydrogel_laminin_control"])
    row.update({
        "eis_1khz_initial_ohm": initial_eis,
        "eis_1khz_final_ohm": final_eis,
        "charge_storage_capacity_initial": initial_csc,
        "charge_storage_capacity_final": final_csc,
    })


def set_neural(row: dict[str, str]) -> None:
    article = row["article_id"]
    values = {
        "laminin_only_control": ("0.93", "1.0", "0.70", "205", "0.78", "1.80", "0.35"),
        "hydrogel_laminin_control": ("0.95", "1.0", "0.75", "220", "0.80", "2.00", "0.40"),
        "lead_nhi_pedot_low_loading": ("0.96", "1.0", "0.78", "230", "0.83", "2.10", "0.42"),
        "challenge_nhi_pedot_high_loading": ("0.92", "1.05", "0.74", "215", "0.79", "1.95", "0.39"),
    }
    viability, ldh, neurite, length, electrode_yield, spike, burst = values.get(
        article,
        values["hydrogel_laminin_control"],
    )
    row.update({
        "cell_model": "synthetic_hiPSC_cortical_neuron_fixture",
        "seeding_density": "synthetic",
        "viability_fraction": viability,
        "ldh_fold_control": ldh,
        "neurite_coverage_fraction": neurite,
        "mean_neurite_length_um": length,
        "electrode_yield_fraction": electrode_yield,
        "spike_rate_hz": spike,
        "burst_rate_hz": burst,
    })


def build_rows(planned: list[dict[str, str]], lead_fail: bool) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for original in planned:
        row = dict(original)
        phase = row["phase"]
        set_medium_pass(row)
        set_physical_pass(row)
        if phase == "H-B":
            set_electrochemical(row)
        if phase == "H-C":
            set_neural(row)
        if lead_fail and row["article_id"] == "lead_nhi_pedot_low_loading" and phase == "H-A" and row["timepoint"] == "24 h":
            row["pH_final"] = "7.75"
            row["visible_shedding"] = "true"
        row["notes"] = "synthetic_fixture_not_material_evidence"
        rows.append(row)
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic NHI-PEDOT fixtures.")
    parser.add_argument("--planned", type=Path, default=DEFAULT_PLANNED)
    parser.add_argument("--pass-out", type=Path, default=DEFAULT_PASS)
    parser.add_argument("--fail-out", type=Path, default=DEFAULT_FAIL)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    planned = load_csv(args.planned)
    pass_rows = build_rows(planned, lead_fail=False)
    fail_rows = build_rows(planned, lead_fail=True)
    write_csv(pass_rows, args.pass_out)
    write_csv(fail_rows, args.fail_out)
    print(f"Wrote {args.pass_out}")
    print(f"Wrote {args.fail_out}")
    print(f"Rows per fixture: {len(pass_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
