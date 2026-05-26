#!/usr/bin/env python3
"""Generate planned run rows for the NHI-PEDOT validation package."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "nhi_pedot_validation_package.json"
DEFAULT_OUT = ROOT / "data" / "nhi_pedot_planned_runs.csv"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_run_plan.md"

ARTICLE_DEFAULTS = {
    "no_coating_mea_control": {
        "variant_id": "",
        "hydrogel_matrix": "none",
        "pedot_pss_loading_fraction": "0",
        "laminin_or_peptide_density": "standard_control_or_none",
    },
    "laminin_only_control": {
        "variant_id": "laminin_only_mea",
        "hydrogel_matrix": "none",
        "pedot_pss_loading_fraction": "0",
        "laminin_or_peptide_density": "standard_laminin",
    },
    "hydrogel_laminin_control": {
        "variant_id": "hydrogel_laminin_no_pedot",
        "hydrogel_matrix": "candidate_soft_hydrogel",
        "pedot_pss_loading_fraction": "0",
        "laminin_or_peptide_density": "standard_laminin",
    },
    "lead_nhi_pedot_low_loading": {
        "variant_id": "nhi_pedot_low_loading_laminin",
        "hydrogel_matrix": "candidate_soft_hydrogel",
        "pedot_pss_loading_fraction": "low",
        "laminin_or_peptide_density": "standard_laminin",
    },
    "challenge_nhi_pedot_high_loading": {
        "variant_id": "nhi_pedot_high_loading_laminin",
        "hydrogel_matrix": "candidate_soft_hydrogel",
        "pedot_pss_loading_fraction": "high",
        "laminin_or_peptide_density": "standard_laminin",
    },
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


def planned_rows(package: dict[str, Any]) -> list[dict[str, str]]:
    fields = package["data_capture_fields"]
    rows: list[dict[str, str]] = []
    for phase in package["run_matrix"]:
        phase_id = phase["phase"]
        for article_id in phase["articles"]:
            defaults = ARTICLE_DEFAULTS.get(article_id, {})
            for replicate in range(1, int(phase["minimum_replicates"]) + 1):
                for timepoint in phase["timepoints"]:
                    row = {field: "" for field in fields}
                    row.update({
                        "run_id": f"NHIPEDOT-{phase_id}-{article_id}-R{replicate}-{safe_id(timepoint)}",
                        "operator_or_agent": "limina",
                        "phase": phase_id,
                        "timepoint": timepoint,
                        "replicate": str(replicate),
                        "article_id": article_id,
                        "variant_id": defaults.get("variant_id", ""),
                        "control_article_id": "hydrogel_laminin_control",
                        "hydrogel_matrix": defaults.get("hydrogel_matrix", ""),
                        "pedot_pss_loading_fraction": defaults.get("pedot_pss_loading_fraction", ""),
                        "laminin_or_peptide_density": defaults.get("laminin_or_peptide_density", ""),
                    })
                    if article_id in {"no_coating_mea_control", "laminin_only_control"}:
                        row["control_article_id"] = "no_coating_mea_control"
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
        "# NHI-PEDOT Planned Runs",
        "",
        f"**Validation package:** `{package['id']}`",
        f"**CSV:** `{out_path}`",
        f"**Total planned rows:** {len(rows)}",
        "",
        "These rows are measurement templates, not experimental results.",
        "",
        "## Phase Counts",
        "",
        "| Phase | Rows |",
        "| --- | ---: |",
    ]
    for phase in sorted(phase_counts):
        lines.append(f"| {phase} | {phase_counts[phase]} |")

    lines.extend([
        "",
        "## Article Counts",
        "",
        "| Article | Rows |",
        "| --- | ---: |",
    ])
    for article in sorted(article_counts):
        lines.append(f"| `{article}` | {article_counts[article]} |")

    lines.extend([
        "",
        "## First Decisive Batch",
        "",
        "Start with Phase H-A rows only. If material blank, swelling, shedding, or medium-integrity gates fail, do not run H-B or H-C.",
        "",
        "## Notes",
        "",
        "- H-A verifies the material is not a medium-chemistry problem before live-cell exposure.",
        "- H-B verifies PEDOT:PSS adds measurable electrochemical value after culture-medium soak.",
        "- H-C is biological and should only start after H-A/H-B pass.",
        "- The run IDs are deterministic so measured rows can be merged and audited across iterations.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate NHI-PEDOT planned run rows.")
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
    print(f"Generated {len(rows)} planned rows")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
