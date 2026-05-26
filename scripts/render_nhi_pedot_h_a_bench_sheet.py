#!/usr/bin/env python3
"""Render a compact bench sheet for NHI-PEDOT H-A measurements."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS
from interpret_nhi_pedot_h_a_sentinel import (
    CHALLENGE_ARTICLE,
    EXPECTED_ARTICLES,
    EXPECTED_TIMEPOINTS,
    HYDROGEL_CONTROL,
    LEAD_ARTICLE,
    NO_COATING_CONTROL,
    REQUIRED_FIELDS,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS = ROOT / "data" / "nhi_pedot_h_a_runs_active.csv"
DEFAULT_RAW = ROOT / "data" / "nhi_pedot_h_a_raw_measurements_template.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_bench_sheet.json"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_h_a_bench_sheet.csv"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_bench_sheet.md"

FIELDS = [
    "sequence",
    "run_id",
    "article_id",
    "timepoint",
    "replicate",
    "article_role",
    "pedot_pss_loading_fraction",
    "hydrogel_matrix",
    "raw_entries_to_fill",
    "required_blank_fields",
    "placeholder_fields",
    "metadata_to_record",
    "initial_measurements",
    "final_measurements",
    "physical_inspection",
    "acceptance_focus",
    "stop_if",
]
ARTICLE_ORDER = {
    NO_COATING_CONTROL: 0,
    HYDROGEL_CONTROL: 1,
    LEAD_ARTICLE: 2,
    CHALLENGE_ARTICLE: 3,
}
ARTICLE_ROLES = {
    NO_COATING_CONTROL: "matched medium/device control",
    HYDROGEL_CONTROL: "soft matrix control",
    LEAD_ARTICLE: "0.6 wt percent PEDOT:PSS lead",
    CHALLENGE_ARTICLE: "1.2 wt percent PEDOT:PSS boundary comparator",
}
TIMEPOINT_ORDER = {timepoint: index for index, timepoint in enumerate(EXPECTED_TIMEPOINTS)}
METADATA_FIELDS = [
    "date",
    "operator_or_agent",
    "mea_coupon_id",
    "electrode_material",
    "medium_name",
    "medium_lot",
    "temperature_c",
    "laminin_or_peptide_density",
    "sterilization_or_aseptic_protocol",
]
INITIAL_FIELDS = ["pH_initial", "osmolality_initial_mOsm_kg", "conductivity_initial_mS_cm"]
FINAL_FIELDS = ["pH_final", "osmolality_final_mOsm_kg", "conductivity_final_mS_cm"]
INSPECTION_FIELDS = [
    "visible_precipitate",
    "visible_shedding",
    "swelling_fraction",
    "delamination_score",
    "optical_transparency_fraction",
]


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def value(row: dict[str, str], field: str) -> str:
    return str(row.get(field, "")).strip()


def has_placeholder(raw: str) -> bool:
    lowered = raw.lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def expected_h_a_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = [
        row for row in rows
        if value(row, "phase") == "H-A"
        and value(row, "article_id") in EXPECTED_ARTICLES
        and value(row, "timepoint") in EXPECTED_TIMEPOINTS
        and value(row, "replicate") == "1"
    ]
    return sorted(
        selected,
        key=lambda row: (
            ARTICLE_ORDER.get(value(row, "article_id"), 99),
            TIMEPOINT_ORDER.get(value(row, "timepoint"), 99),
            value(row, "run_id"),
        ),
    )


def raw_counts(raw_rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in raw_rows:
        run_id = value(row, "run_id")
        if not run_id:
            continue
        if value(row, "value"):
            continue
        counts[run_id] = counts.get(run_id, 0) + 1
    return counts


def semicolon(items: list[str]) -> str:
    return ";".join(items)


def blank_fields(row: dict[str, str], fields: list[str]) -> list[str]:
    return [field for field in fields if not value(row, field)]


def placeholder_fields(row: dict[str, str]) -> list[str]:
    return [field for field, raw in row.items() if value(row, field) and has_placeholder(str(raw))]


def acceptance_focus(row: dict[str, str]) -> str:
    article = value(row, "article_id")
    if article == NO_COATING_CONTROL:
        return "baseline pH/osmolality/conductivity drift and visual/physical inspection"
    if article == HYDROGEL_CONTROL:
        return "matrix-only medium drift, swelling, delamination, and transparency versus no-coating control"
    if article == LEAD_ARTICLE:
        return "lead medium drift <= controls plus no shedding, swelling <=0.20, delamination <=0.5, transparency >=0.80"
    if article == CHALLENGE_ARTICLE:
        return "upper-loading boundary; failures constrain dose-response but do not stop lead if lead passes"
    return "H-A medium integrity and physical stability"


def stop_if(row: dict[str, str]) -> str:
    article = value(row, "article_id")
    if article == LEAD_ARTICLE:
        return "lead shows pH drift >0.10 vs control, osmolality/conductivity drift >5%, shedding, swelling >0.20, delamination >0.5, or transparency <0.80"
    if article == HYDROGEL_CONTROL:
        return "hydrogel-only matrix fails, because PEDOT interpretation becomes confounded"
    if article == CHALLENGE_ARTICLE:
        return "treat challenge as boundary only if it fails; do not promote to H-C"
    return "control is unstable or missing, because matched comparisons become invalid"


def build_tasks(runs: list[dict[str, str]], raw_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    counts = raw_counts(raw_rows)
    tasks: list[dict[str, str]] = []
    for sequence, row in enumerate(expected_h_a_rows(runs), start=1):
        run_id = value(row, "run_id")
        tasks.append({
            "sequence": str(sequence),
            "run_id": run_id,
            "article_id": value(row, "article_id"),
            "timepoint": value(row, "timepoint"),
            "replicate": value(row, "replicate"),
            "article_role": ARTICLE_ROLES.get(value(row, "article_id"), "H-A article"),
            "pedot_pss_loading_fraction": value(row, "pedot_pss_loading_fraction"),
            "hydrogel_matrix": value(row, "hydrogel_matrix"),
            "raw_entries_to_fill": str(counts.get(run_id, 0)),
            "required_blank_fields": semicolon(blank_fields(row, REQUIRED_FIELDS)),
            "placeholder_fields": semicolon(placeholder_fields(row)),
            "metadata_to_record": semicolon(METADATA_FIELDS),
            "initial_measurements": semicolon(INITIAL_FIELDS),
            "final_measurements": semicolon(FINAL_FIELDS),
            "physical_inspection": semicolon(INSPECTION_FIELDS),
            "acceptance_focus": acceptance_focus(row),
            "stop_if": stop_if(row),
        })
    return tasks


def render_report(tasks: list[dict[str, str]], runs_path: Path, raw_path: Path, csv_path: Path) -> str:
    total_raw = sum(int(row["raw_entries_to_fill"]) for row in tasks)
    lead = [row for row in tasks if row["article_id"] == LEAD_ARTICLE]
    lines = [
        "# NHI-PEDOT H-A Bench Sheet",
        "",
        "This is a compact wet-bench task list for the first acellular H-A sentinel. It is not measured evidence.",
        "",
        f"**Active runs:** `{runs_path}`",
        f"**Raw measurement template:** `{raw_path}`",
        f"**Bench CSV:** `{csv_path}`",
        f"**Run tasks:** {len(tasks)}",
        f"**Blank raw entries to fill:** {total_raw}",
        "",
        "## Bench Tasks",
        "",
        "| Seq | Run | Article | Timepoint | Raw entries | Required blanks | Placeholder fields |",
        "| ---: | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in tasks:
        lines.append(
            f"| {row['sequence']} | `{row['run_id']}` | `{row['article_id']}` | {row['timepoint']} | "
            f"{row['raw_entries_to_fill']} | {row['required_blank_fields'] or '-'} | {row['placeholder_fields'] or '-'} |"
        )
    lines.extend([
        "",
        "## Gate Focus",
        "",
        "- Compare each material row against the matched no-coating control at the same timepoint and replicate.",
        "- Pass requires material-driven pH drift <= 0.10 pH units versus control.",
        "- Pass requires osmolality and conductivity drift <= 5 percent versus control.",
        "- Pass requires no visible precipitate, no visible shedding, swelling <= 0.20, delamination <= 0.5, and transparency >= 0.80.",
        "- Do not advance to H-B or H-C if any lead row fails H-A.",
        "",
        "## Lead Rows",
        "",
    ])
    for row in lead:
        lines.append(f"- `{row['run_id']}`: {row['acceptance_focus']}")
    lines.extend([
        "",
        "## Next Commands",
        "",
        "```bash",
        "python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py",
        "python3 scripts/qc_nhi_pedot_h_a_intake.py --runs data/nhi_pedot_h_a_runs_active.csv",
        "python3 scripts/interpret_nhi_pedot_h_a_sentinel.py --runs data/nhi_pedot_h_a_runs_active.csv",
        "```",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render compact NHI-PEDOT H-A bench sheet.")
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    _, runs = load_csv(args.runs)
    _, raw_rows = load_csv(args.raw)
    tasks = build_tasks(runs, raw_rows)
    result = {
        "status": "rendered",
        "runs_path": str(args.runs),
        "raw_path": str(args.raw),
        "task_count": len(tasks),
        "blank_raw_entries_to_fill": sum(int(row["raw_entries_to_fill"]) for row in tasks),
        "lead_run_ids": [row["run_id"] for row in tasks if row["article_id"] == LEAD_ARTICLE],
        "tasks": tasks,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(tasks, args.csv_out)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(tasks, args.runs, args.raw, args.csv_out), encoding="utf-8")
    print(f"Rendered H-A bench sheet: tasks={len(tasks)} blank_raw_entries={result['blank_raw_entries_to_fill']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
