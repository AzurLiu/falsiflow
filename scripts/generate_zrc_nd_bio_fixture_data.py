#!/usr/bin/env python3
"""Generate synthetic biological follow-up fixture rows for evaluator checks."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data" / "zrc_nd_biological_followup_package.json"
TEMPLATE = ROOT / "data" / "zrc_nd_bio_runs_template.csv"
OUT = ROOT / "data" / "fixtures" / "zrc_nd_bio_runs_full_pass_fixture.csv"

VARIANT_BY_ARTICLE = {
    "bio_lead_zrc_nd_3p5m_guard": "zrc_nd_3p5k_mpc_guard",
    "bio_baseline_rc_3p5m_guard": "zrc_nd_3p5k_unmodified_guard",
    "bio_challenge_zrc_nd_10m_guard": "zrc_nd_10k_mpc_guard",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_header() -> list[str]:
    if TEMPLATE.exists():
        with TEMPLATE.open("r", newline="", encoding="utf-8") as handle:
            return next(csv.reader(handle))
    return list(load_json(PACKAGE)["data_capture_fields"])


def base_row(
    header: list[str],
    phase: str,
    timepoint: str,
    replicate: int,
    article: str,
) -> dict[str, str]:
    row = {field: "" for field in header}
    exposure_time = timepoint.split()[0] if timepoint else ""
    row.update({
        "run_id": f"fixture-{phase}-{article}-R{replicate}-{timepoint.replace(' ', '')}",
        "date": "2026-05-23",
        "operator_or_agent": "fixture",
        "phase": phase,
        "timepoint": timepoint,
        "replicate": str(replicate),
        "article_id": article,
        "variant_id": VARIANT_BY_ARTICLE.get(article, ""),
        "control_article_id": "bio_no_module_control",
        "cell_model": "synthetic_neural_culture_proxy",
        "medium_condition": "synthetic_conditioned_medium",
        "exposure_time_h": exposure_time,
        "morphology_notes": "synthetic fixture only",
        "notes": "synthetic fixture only; not material evidence",
    })
    return row


def apply_d1_metrics(row: dict[str, str]) -> None:
    article = row["article_id"]
    if article == "bio_no_module_control":
        row.update({"viability_metabolic_pct_control": "100", "ldh_release_pct_control": "100"})
    elif article == "bio_lead_zrc_nd_3p5m_guard":
        row.update({"viability_metabolic_pct_control": "96", "ldh_release_pct_control": "104"})
    elif article == "bio_baseline_rc_3p5m_guard":
        row.update({"viability_metabolic_pct_control": "95", "ldh_release_pct_control": "106"})
    elif article == "bio_challenge_zrc_nd_10m_guard":
        row.update({"viability_metabolic_pct_control": "88", "ldh_release_pct_control": "132"})
    elif article == "bio_positive_toxicity_control":
        row.update({"viability_metabolic_pct_control": "45", "ldh_release_pct_control": "240"})


def apply_d2_metrics(row: dict[str, str]) -> None:
    article = row["article_id"]
    if article == "bio_no_module_control":
        row.update({
            "neurite_length_pct_control": "100",
            "neurite_branching_pct_control": "100",
            "cell_body_count_pct_control": "100",
        })
    elif article == "bio_lead_zrc_nd_3p5m_guard":
        row.update({
            "neurite_length_pct_control": "94",
            "neurite_branching_pct_control": "93",
            "cell_body_count_pct_control": "96",
        })
    elif article == "bio_baseline_rc_3p5m_guard":
        row.update({
            "neurite_length_pct_control": "95",
            "neurite_branching_pct_control": "94",
            "cell_body_count_pct_control": "97",
        })
    elif article == "bio_challenge_zrc_nd_10m_guard":
        row.update({
            "neurite_length_pct_control": "82",
            "neurite_branching_pct_control": "80",
            "cell_body_count_pct_control": "88",
        })


def apply_d3_metrics(row: dict[str, str]) -> None:
    article = row["article_id"]
    if article == "bio_no_module_control":
        row.update({
            "network_spike_rate_pct_control": "100",
            "burst_rate_pct_control": "100",
            "synchrony_pct_control": "100",
        })
    elif article == "bio_lead_zrc_nd_3p5m_guard":
        row.update({
            "network_spike_rate_pct_control": "98",
            "burst_rate_pct_control": "102",
            "synchrony_pct_control": "96",
        })
    elif article == "bio_baseline_rc_3p5m_guard":
        row.update({
            "network_spike_rate_pct_control": "100",
            "burst_rate_pct_control": "98",
            "synchrony_pct_control": "101",
        })
    elif article == "bio_challenge_zrc_nd_10m_guard":
        row.update({
            "network_spike_rate_pct_control": "150",
            "burst_rate_pct_control": "65",
            "synchrony_pct_control": "60",
        })


def make_rows(header: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    d1_articles = [
        "bio_no_module_control",
        "bio_lead_zrc_nd_3p5m_guard",
        "bio_baseline_rc_3p5m_guard",
        "bio_challenge_zrc_nd_10m_guard",
        "bio_positive_toxicity_control",
    ]
    d23_articles = [
        "bio_no_module_control",
        "bio_lead_zrc_nd_3p5m_guard",
        "bio_baseline_rc_3p5m_guard",
        "bio_challenge_zrc_nd_10m_guard",
    ]
    for replicate in range(1, 4):
        for timepoint in ["24 h", "72 h"]:
            for article in d1_articles:
                row = base_row(header, "D1", timepoint, replicate, article)
                apply_d1_metrics(row)
                rows.append(row)
        for article in d23_articles:
            row = base_row(header, "D2", "72 h", replicate, article)
            apply_d2_metrics(row)
            rows.append(row)
        for article in d23_articles:
            row = base_row(header, "D3", "72 h", replicate, article)
            apply_d3_metrics(row)
            rows.append(row)
    return rows


def main() -> int:
    header = load_header()
    rows = make_rows(header)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} synthetic biological fixture rows")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
