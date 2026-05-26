#!/usr/bin/env python3
"""Generate synthetic ZRC-ND validation fixtures for evaluator regression tests."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data" / "zrc_nd_validation_runs_template.csv"
OUT = ROOT / "data" / "fixtures" / "zrc_nd_validation_runs_full_pass_fixture.csv"


def load_header() -> list[str]:
    with TEMPLATE.open("r", newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def safe_timepoint_id(timepoint: str) -> str:
    return timepoint.lower().replace(" ", "")


def base_row(
    header: list[str],
    phase: str,
    article: str,
    variant: str,
    replicate: int,
    timepoint: str = "24 h",
) -> dict[str, str]:
    row = {field: "" for field in header}
    row.update({
        "run_id": f"fixture-{phase}-{article}-R{replicate}-{safe_timepoint_id(timepoint)}",
        "operator_or_agent": "fixture",
        "phase": phase,
        "timepoint": timepoint,
        "replicate": str(replicate),
        "article_id": article,
        "variant_id": variant,
        "control_article_id": "no_module_static_control",
        "medium_name": "test_medium",
        "medium_lot": "fixture",
        "initial_volume_ml": "1.0",
        "flow_rate_ul_min": "100",
        "exposure_time_h": "24",
        "temperature_c": "37",
        "pH_initial": "7.40",
        "pH_final": "7.37",
        "osmolality_initial_mOsm_kg": "300",
        "osmolality_final_mOsm_kg": "305",
        "conductivity_initial_mS_cm": "15",
        "conductivity_final_mS_cm": "15.30",
        "lactate_initial_mM": "10",
        "lactate_final_mM": "7.0",
        "ammonia_initial_uM": "1000",
        "ammonia_final_uM": "700",
        "bdnf_initial_pg_ml": "100",
        "bdnf_final_pg_ml": "96",
        "ngf_initial_pg_ml": "100",
        "ngf_final_pg_ml": "95",
        "albumin_initial": "100",
        "albumin_final": "98",
        "transferrin_initial": "100",
        "transferrin_final": "97",
        "total_protein_initial": "100",
        "total_protein_final": "97",
        "flow_resistance_initial": "1.0",
        "flow_resistance_final": "1.08",
        "bubble_events": "0",
        "visible_precipitate": "false",
        "notes": "synthetic fixture only",
    })
    return row


def make_baseline_snapshot(row: dict[str, str]) -> dict[str, str]:
    row.update({
        "exposure_time_h": "0",
        "pH_final": row["pH_initial"],
        "osmolality_final_mOsm_kg": row["osmolality_initial_mOsm_kg"],
        "conductivity_final_mS_cm": row["conductivity_initial_mS_cm"],
        "lactate_final_mM": row["lactate_initial_mM"],
        "ammonia_final_uM": row["ammonia_initial_uM"],
        "bdnf_final_pg_ml": row["bdnf_initial_pg_ml"],
        "ngf_final_pg_ml": row["ngf_initial_pg_ml"],
        "albumin_final": row["albumin_initial"],
        "transferrin_final": row["transferrin_initial"],
        "total_protein_final": row["total_protein_initial"],
        "flow_resistance_final": row["flow_resistance_initial"],
    })
    return row


def control_row(header: list[str], phase: str, replicate: int, timepoint: str = "24 h") -> dict[str, str]:
    row = base_row(header, phase, "no_module_static_control", "", replicate, timepoint)
    row.update({
        "mwco_kda": "0",
        "surface_modification": "none",
        "housing_material": "none",
        "pH_final": "7.39",
        "osmolality_final_mOsm_kg": "301",
        "conductivity_final_mS_cm": "15.01",
        "lactate_final_mM": "9.8",
        "ammonia_final_uM": "990",
        "bdnf_final_pg_ml": "98",
        "ngf_final_pg_ml": "98",
        "albumin_final": "99",
        "transferrin_final": "99",
        "total_protein_final": "99",
        "flow_resistance_final": "1.01",
    })
    return make_baseline_snapshot(row) if timepoint == "0 h" else row


def lead_row(header: list[str], phase: str, replicate: int, timepoint: str = "24 h") -> dict[str, str]:
    row = base_row(header, phase, "lead_zrc_nd_3p5m_guard", "zrc_nd_3p5k_mpc_guard", replicate, timepoint)
    row.update({
        "mwco_kda": "3.5",
        "surface_modification": "pda_polympc_surface_only",
        "housing_material": "coc_cop",
    })
    return make_baseline_snapshot(row) if timepoint == "0 h" else row


def baseline_row(header: list[str], phase: str, replicate: int, timepoint: str = "24 h") -> dict[str, str]:
    row = base_row(header, phase, "baseline_rc_3p5m_guard", "zrc_nd_3p5k_unmodified_guard", replicate, timepoint)
    row.update({
        "mwco_kda": "3.5",
        "surface_modification": "none",
        "housing_material": "coc_cop",
        "lactate_final_mM": "7.5",
        "ammonia_final_uM": "760",
        "bdnf_final_pg_ml": "94",
        "ngf_final_pg_ml": "94",
        "albumin_final": "97",
        "transferrin_final": "96",
        "total_protein_final": "96",
        "flow_resistance_final": "1.16",
    })
    return make_baseline_snapshot(row) if timepoint == "0 h" else row


def challenge_row(header: list[str], phase: str, replicate: int, timepoint: str = "24 h") -> dict[str, str]:
    row = base_row(header, phase, "challenge_zrc_nd_10m_guard", "zrc_nd_10k_mpc_guard", replicate, timepoint)
    row.update({
        "mwco_kda": "10",
        "surface_modification": "pda_polympc_surface_only",
        "housing_material": "coc_cop",
        "lactate_final_mM": "6.6",
        "ammonia_final_uM": "650",
        "bdnf_final_pg_ml": "84",
        "ngf_final_pg_ml": "85",
        "albumin_final": "91",
        "transferrin_final": "90",
        "total_protein_final": "90",
        "flow_resistance_final": "1.09",
    })
    return make_baseline_snapshot(row) if timepoint == "0 h" else row


def main() -> int:
    header = load_header()
    rows = []
    for phase in ["A", "B", "C"]:
        for replicate in range(1, 4):
            rows.extend([
                control_row(header, phase, replicate, "0 h"),
                lead_row(header, phase, replicate, "0 h"),
                baseline_row(header, phase, replicate, "0 h"),
                challenge_row(header, phase, replicate, "0 h"),
            ])
            rows.extend([
                control_row(header, phase, replicate),
                lead_row(header, phase, replicate),
                baseline_row(header, phase, replicate),
                challenge_row(header, phase, replicate),
            ])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} synthetic fixture rows")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
