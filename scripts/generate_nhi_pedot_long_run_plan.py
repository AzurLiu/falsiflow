#!/usr/bin/env python3
"""Generate planned long-duration NHI-PEDOT follow-up rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "nhi_pedot_long_followup_package.json"
DEFAULT_OUT = ROOT / "data" / "nhi_pedot_long_planned_runs.csv"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_long_run_plan.md"

VARIANT_BY_ARTICLE = {
    "long_laminin_only_control": "laminin_only_mea",
    "long_hydrogel_laminin_control": "hydrogel_laminin_no_pedot",
    "long_lead_nhi_pedot_low_loading": "nhi_pedot_low_loading_laminin",
    "long_challenge_nhi_pedot_high_loading": "nhi_pedot_high_loading_laminin",
}
HYDROGEL_BY_ARTICLE = {
    "long_laminin_only_control": "none",
    "long_hydrogel_laminin_control": "candidate_soft_hydrogel",
    "long_lead_nhi_pedot_low_loading": "candidate_soft_hydrogel",
    "long_challenge_nhi_pedot_high_loading": "candidate_soft_hydrogel",
    "long_positive_toxicity_control": "assay_control",
}
PEDOT_LOADING_BY_ARTICLE = {
    "long_laminin_only_control": "0",
    "long_hydrogel_laminin_control": "0",
    "long_lead_nhi_pedot_low_loading": "low",
    "long_challenge_nhi_pedot_high_loading": "high",
    "long_positive_toxicity_control": "0",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_id(value: str) -> str:
    return (
        value.lower()
        .replace(" ", "")
        .replace("/", "_")
        .replace("-", "_")
        .replace(">", "gt")
    )


def culture_day(timepoint: str) -> str:
    token = timepoint.strip().split(" ")[0]
    return token if token.isdigit() else ""


def planned_rows(package: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    fields = package["data_capture_fields"]
    for phase in package["run_matrix"]:
        for article in phase["articles"]:
            for replicate in range(1, int(phase["minimum_replicates"]) + 1):
                for timepoint in phase["timepoints"]:
                    row = {field: "" for field in fields}
                    row.update({
                        "run_id": f"NHIPEDOT-LONG-{phase['phase']}-{article}-R{replicate}-{safe_id(timepoint)}",
                        "operator_or_agent": "limina",
                        "phase": phase["phase"],
                        "timepoint": timepoint,
                        "replicate": str(replicate),
                        "article_id": article,
                        "variant_id": VARIANT_BY_ARTICLE.get(article, ""),
                        "control_article_id": "long_hydrogel_laminin_control",
                        "cell_model": "neural_culture_model_tbd",
                        "culture_day": culture_day(timepoint),
                        "hydrogel_matrix": HYDROGEL_BY_ARTICLE.get(article, ""),
                        "pedot_pss_loading_fraction": PEDOT_LOADING_BY_ARTICLE.get(article, ""),
                        "laminin_or_peptide_density": "standard_laminin",
                    })
                    if article in {"long_laminin_only_control", "long_positive_toxicity_control"}:
                        row["control_article_id"] = "long_laminin_only_control"
                    rows.append(row)
    return rows


def write_csv(rows: list[dict[str, str]], fields: list[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def render_report(package: dict[str, Any], rows: list[dict[str, str]], out_path: Path) -> str:
    phase_counts: dict[str, int] = {}
    article_counts: dict[str, int] = {}
    for row in rows:
        phase_counts[row["phase"]] = phase_counts.get(row["phase"], 0) + 1
        article_counts[row["article_id"]] = article_counts.get(row["article_id"], 0) + 1
    lines = [
        "# NHI-PEDOT Long-Duration Planned Runs",
        "",
        f"**Follow-up package:** `{package['id']}`",
        f"**CSV:** `{out_path}`",
        f"**Total planned rows:** {len(rows)}",
        "",
        "These rows are measurement templates, not long-duration suitability evidence.",
        "",
        "## Phase Counts",
        "",
        "| Phase | Rows |",
        "| --- | ---: |",
    ]
    for phase in sorted(phase_counts):
        lines.append(f"| {phase} | {phase_counts[phase]} |")
    lines.extend(["", "## Article Counts", "", "| Article | Rows |", "| --- | ---: |"])
    for article in sorted(article_counts):
        lines.append(f"| `{article}` | {article_counts[article]} |")
    lines.extend([
        "",
        "## Entry Boundary",
        "",
        "Run this long-duration plan only after H-A/H-B/H-C coupon gates pass for the low-loading lead.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate NHI-PEDOT long-duration planned rows.")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package = load_json(args.package)
    rows = planned_rows(package)
    write_csv(rows, package["data_capture_fields"], args.out)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(package, rows, args.out), encoding="utf-8")
    print(f"Generated {len(rows)} long-duration planned rows")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
