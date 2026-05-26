#!/usr/bin/env python3
"""Generate planned biological follow-up run rows for ZRC-ND."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "zrc_nd_biological_followup_package.json"
DEFAULT_OUT = ROOT / "data" / "zrc_nd_bio_planned_runs.csv"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_bio_run_plan.md"


VARIANT_BY_ARTICLE = {
    "bio_lead_zrc_nd_3p5m_guard": "zrc_nd_3p5k_mpc_guard",
    "bio_baseline_rc_3p5m_guard": "zrc_nd_3p5k_unmodified_guard",
    "bio_challenge_zrc_nd_10m_guard": "zrc_nd_10k_mpc_guard",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_timepoint_id(timepoint: str) -> str:
    return timepoint.lower().replace(" ", "").replace("/", "_").replace("-", "_")


def planned_rows(package: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    fields = package["data_capture_fields"]
    for phase in package["run_matrix"]:
        for article in phase["articles"]:
            for replicate in range(1, int(phase["minimum_replicates"]) + 1):
                for timepoint in phase["timepoints"]:
                    row = {field: "" for field in fields}
                    row.update({
                        "run_id": f"ZRCND-BIO-{phase['phase']}-{article}-R{replicate}-{safe_timepoint_id(timepoint)}",
                        "operator_or_agent": "limina",
                        "phase": phase["phase"],
                        "timepoint": timepoint,
                        "replicate": str(replicate),
                        "article_id": article,
                        "variant_id": VARIANT_BY_ARTICLE.get(article, ""),
                        "control_article_id": "bio_no_module_control",
                        "cell_model": "neural_culture_model_tbd",
                        "medium_condition": "conditioned_medium_or_proxy",
                    })
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
        "# ZRC-ND Biological Planned Runs",
        "",
        f"**Biological package:** `{package['id']}`",
        f"**CSV:** `{out_path}`",
        f"**Total planned rows:** {len(rows)}",
        "",
        "These rows are a measurement template, not biological results.",
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
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate ZRC-ND biological planned runs.")
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
    print(f"Generated {len(rows)} biological planned rows")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
