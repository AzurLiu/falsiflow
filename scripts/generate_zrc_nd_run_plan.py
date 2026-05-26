#!/usr/bin/env python3
"""Generate planned run rows for the ZRC-ND validation package."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "zrc_nd_3p5k_guard_validation_package.json"
DEFAULT_OUT = ROOT / "data" / "zrc_nd_planned_runs.csv"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_run_plan.md"


ARTICLE_DEFAULTS = {
    "lead_zrc_nd_3p5m_guard": {
        "variant_id": "zrc_nd_3p5k_mpc_guard",
        "mwco_kda": "3.5",
        "surface_modification": "pda_polympc_surface_only",
        "housing_material": "coc_cop",
    },
    "baseline_rc_3p5m_guard": {
        "variant_id": "zrc_nd_3p5k_unmodified_guard",
        "mwco_kda": "3.5",
        "surface_modification": "none",
        "housing_material": "coc_cop",
    },
    "challenge_zrc_nd_10m_guard": {
        "variant_id": "zrc_nd_10k_mpc_guard",
        "mwco_kda": "10",
        "surface_modification": "pda_polympc_surface_only",
        "housing_material": "coc_cop",
    },
    "no_module_static_control": {
        "variant_id": "",
        "mwco_kda": "",
        "surface_modification": "none",
        "housing_material": "none",
    },
    "bulk_exchange_reference": {
        "variant_id": "",
        "mwco_kda": "",
        "surface_modification": "none",
        "housing_material": "none",
    },
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_timepoint_id(timepoint: str) -> str:
    return (
        timepoint.lower()
        .replace(" ", "")
        .replace("/", "_")
        .replace("-", "_")
        .replace(">", "gt")
    )


def planned_rows(package: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    fields = package["data_capture_fields"]
    for phase in package["run_matrix"]:
        phase_id = phase["phase"]
        timepoints = [
            timepoint for timepoint in phase["timepoints"]
            if not timepoint.lower().startswith("repeat")
        ]
        for article_id in phase["articles"]:
            defaults = ARTICLE_DEFAULTS.get(article_id, {})
            for replicate in range(1, int(phase["minimum_replicates"]) + 1):
                for timepoint in timepoints:
                    row = {field: "" for field in fields}
                    row.update({
                        "run_id": (
                            f"ZRCND-{phase_id}-{article_id}-"
                            f"R{replicate}-{safe_timepoint_id(timepoint)}"
                        ),
                        "operator_or_agent": "limina",
                        "phase": phase_id,
                        "timepoint": timepoint,
                        "replicate": str(replicate),
                        "article_id": article_id,
                        "variant_id": defaults.get("variant_id", ""),
                        "control_article_id": "no_module_static_control",
                        "mwco_kda": defaults.get("mwco_kda", ""),
                        "surface_modification": defaults.get("surface_modification", ""),
                        "housing_material": defaults.get("housing_material", ""),
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
        "# ZRC-ND Planned Runs",
        "",
        f"**Validation package:** `{package['id']}`",
        f"**CSV:** `{out_path}`",
        f"**Total planned rows:** {len(rows)}",
        "",
        "These rows are a measurement template, not experimental results.",
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
        "## Notes",
        "",
        "- Numeric measurement fields are intentionally blank until actual Phase A/B/C data exist.",
        "- Conditional repeat-exposure rows are not generated; add them after Phase C fouling results justify repetition.",
        "- The run IDs are deterministic so measured rows can be compared across iterations.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate ZRC-ND planned run rows.")
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
