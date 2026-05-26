#!/usr/bin/env python3
"""Generate synthetic NHI-PEDOT long-follow-up fixture rows."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLANNED = ROOT / "data" / "nhi_pedot_long_planned_runs.csv"
DEFAULT_PASS = ROOT / "data" / "fixtures" / "nhi_pedot_long_full_pass_fixture.csv"
DEFAULT_FAIL = ROOT / "data" / "fixtures" / "nhi_pedot_long_lead_fail_fixture.csv"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def set_material(row: dict[str, str]) -> None:
    row.update({
        "date": "synthetic_fixture_not_evidence",
        "visible_shedding": "false",
        "swelling_fraction": "0.04",
        "delamination_score": "0",
        "optical_transparency_fraction": "0.90",
        "electrode_window_access": "true",
    })


def set_electrochemical(row: dict[str, str]) -> None:
    article = row["article_id"]
    pct = {
        "long_laminin_only_control": "115",
        "long_hydrogel_laminin_control": "100",
        "long_lead_nhi_pedot_low_loading": "70",
        "long_challenge_nhi_pedot_high_loading": "60",
    }.get(article, "100")
    row.update({
        "eis_1khz_initial_ohm": "900",
        "eis_1khz_current_ohm": "940",
        "eis_1khz_pct_hydrogel_control": pct,
        "charge_storage_capacity_initial": "1.0",
        "charge_storage_capacity_current": "0.92",
        "charge_storage_capacity_retention_fraction": "0.92",
        "baseline_noise_uv": "8",
    })


def set_neural(row: dict[str, str]) -> None:
    article = row["article_id"]
    values = {
        "long_laminin_only_control": ("96", "100", "92", "0", "96", "96", "94", "95"),
        "long_hydrogel_laminin_control": ("100", "100", "100", "0", "100", "100", "100", "100"),
        "long_lead_nhi_pedot_low_loading": ("98", "100", "98", "0", "98", "102", "101", "100"),
        "long_challenge_nhi_pedot_high_loading": ("86", "115", "88", "1", "88", "90", "88", "90"),
        "long_positive_toxicity_control": ("40", "250", "20", "3", "15", "10", "8", "10"),
    }
    viability, ldh, neurite, stress, electrode_yield, spike, burst, synchrony = values.get(
        article,
        values["long_hydrogel_laminin_control"],
    )
    row.update({
        "viability_pct_hydrogel_control": viability,
        "ldh_pct_hydrogel_control": ldh,
        "neurite_coverage_pct_hydrogel_control": neurite,
        "morphology_stress_score": stress,
        "electrode_yield_pct_hydrogel_control": electrode_yield,
        "spike_rate_pct_hydrogel_control": spike,
        "burst_rate_pct_hydrogel_control": burst,
        "synchrony_pct_hydrogel_control": synchrony,
    })


def set_stim(row: dict[str, str]) -> None:
    article = row["article_id"]
    values = {
        "long_laminin_only_control": ("88", "87", "15"),
        "long_hydrogel_laminin_control": ("90", "90", "12"),
        "long_lead_nhi_pedot_low_loading": ("92", "91", "10"),
        "long_challenge_nhi_pedot_high_loading": ("84", "83", "22"),
    }
    spike_recovery, burst_recovery, impedance_degradation = values.get(
        article,
        values["long_hydrogel_laminin_control"],
    )
    row.update({
        "post_stim_spike_recovery_pct_pre": spike_recovery,
        "post_stim_burst_recovery_pct_pre": burst_recovery,
        "post_stim_impedance_degradation_pct": impedance_degradation,
    })


def build_rows(planned: list[dict[str, str]], lead_fail: bool) -> list[dict[str, str]]:
    rows = []
    for original in planned:
        row = dict(original)
        phase = row["phase"]
        set_material(row)
        if phase == "L1":
            set_electrochemical(row)
        if phase == "L2":
            set_neural(row)
        if phase == "L3":
            set_stim(row)
        if lead_fail and row["article_id"] == "long_lead_nhi_pedot_low_loading" and phase == "L2" and row["timepoint"] == "28 d":
            row["viability_pct_hydrogel_control"] = "70"
            row["spike_rate_pct_hydrogel_control"] = "35"
            row["morphology_stress_score"] = "3"
        row["notes"] = "synthetic_fixture_not_material_evidence"
        rows.append(row)
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic NHI-PEDOT long fixtures.")
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
