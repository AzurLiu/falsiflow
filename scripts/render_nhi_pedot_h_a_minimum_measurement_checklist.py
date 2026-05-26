#!/usr/bin/env python3
"""Render the minimum real-measurement checklist for NHI-PEDOT H-A."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCH = ROOT / "data" / "nhi_pedot_h_a_bench_sheet.json"
DEFAULT_QC = ROOT / "data" / "nhi_pedot_h_a_intake_qc.json"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_minimum_measurement_checklist.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_minimum_measurement_checklist.md"

FIELD_LABELS = {
    "date": "calendar date of the measurement event",
    "medium_name": "actual medium or CL1-proxy medium name",
    "medium_lot": "actual medium lot",
    "temperature_c": "measurement/incubation temperature in C",
    "pH_initial": "initial pH",
    "pH_final": "final pH",
    "osmolality_initial_mOsm_kg": "initial osmolality",
    "osmolality_final_mOsm_kg": "final osmolality",
    "conductivity_initial_mS_cm": "initial conductivity",
    "conductivity_final_mS_cm": "final conductivity",
    "visible_precipitate": "visible precipitate, true or false",
    "visible_shedding": "visible material shedding, true or false",
    "swelling_fraction": "fractional swelling",
    "delamination_score": "0 to 1 delamination score",
    "optical_transparency_fraction": "0 to 1 optical transparency fraction",
}

PROVENANCE_FIELDS = [
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "source_file",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def split_fields(value: str) -> list[str]:
    return [field for field in str(value).split(";") if field]


def qc_error_counts(qc: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for issue in qc.get("issues", []):
        if issue.get("severity") == "error":
            field = issue.get("field")
            if field:
                counts[field] += 1
    return counts


def missing_hotspots(qc: dict[str, Any]) -> list[dict[str, Any]]:
    counts = qc_error_counts(qc)
    return [{"field": field, "rows": rows} for field, rows in counts.most_common()]


def build_checklist(bench: dict[str, Any], qc: dict[str, Any]) -> dict[str, Any]:
    tasks = bench.get("tasks", [])
    articles: dict[str, dict[str, Any]] = {}
    field_counts: Counter[str] = Counter()
    timepoints_by_article: dict[str, list[str]] = defaultdict(list)

    for task in tasks:
        article_id = task.get("article_id", "")
        timepoint = task.get("timepoint", "")
        articles.setdefault(
            article_id,
            {
                "article_id": article_id,
                "article_role": task.get("article_role", ""),
                "pedot_pss_loading_fraction": task.get("pedot_pss_loading_fraction", ""),
                "hydrogel_matrix": task.get("hydrogel_matrix", ""),
                "run_ids": [],
                "timepoints": [],
                "acceptance_focus": task.get("acceptance_focus", ""),
                "stop_if": task.get("stop_if", ""),
            },
        )
        articles[article_id]["run_ids"].append(task.get("run_id", ""))
        if timepoint not in timepoints_by_article[article_id]:
            timepoints_by_article[article_id].append(timepoint)
        for field in split_fields(task.get("required_blank_fields", "")):
            field_counts[field] += 1

    for article_id, article in articles.items():
        article["timepoints"] = timepoints_by_article[article_id]

    qc_counts = qc_error_counts(qc)
    all_fields = sorted(
        set(field_counts) | set(qc_counts),
        key=lambda field: (-max(field_counts.get(field, 0), qc_counts.get(field, 0)), field),
    )
    required_fields = [
        {
            "field": field,
            "description": FIELD_LABELS.get(field, "required H-A intake field"),
            "rows": max(field_counts.get(field, 0), qc_counts.get(field, 0)),
        }
        for field in all_fields
        if field in FIELD_LABELS
    ]

    return {
        "status": "awaiting_real_measurements",
        "purpose": "Compact checklist for making the first NHI-PEDOT H-A sentinel interpretable.",
        "raw_measurement_template": bench.get("raw_path"),
        "active_runs": bench.get("runs_path"),
        "run_count": len(tasks),
        "blank_raw_entries_to_fill": bench.get("blank_raw_entries_to_fill", 0),
        "article_count": len(articles),
        "articles": list(articles.values()),
        "required_fields": required_fields,
        "provenance_fields_per_raw_row": PROVENANCE_FIELDS,
        "qc_status": qc.get("status", "unknown"),
        "qc_error_count": qc.get("issue_counts", {}).get("error", 0),
        "qc_warning_count": qc.get("issue_counts", {}).get("warning", 0),
        "qc_missing_hotspots": missing_hotspots(qc),
        "non_claim_boundary": (
            "This checklist prepares data entry only. The material remains a hypothesis until "
            "QC-clean real rows pass H-A, H-B, H-C, long follow-up, and the final claim audit."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# NHI-PEDOT H-A Minimum Real-Measurement Checklist",
        "",
        "This compresses the first acellular H-A sentinel into the smallest practical execution view. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**QC status:** `{result['qc_status']}`",
        f"**Runs:** {result['run_count']}",
        f"**Blank raw entries:** {result['blank_raw_entries_to_fill']}",
        f"**Raw template:** `{result['raw_measurement_template']}`",
        "",
        "## Article-Timepoint Matrix",
        "",
        "| Article | Role | Loading | Timepoints | Stop condition |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for article in result["articles"]:
        lines.append(
            f"| `{article['article_id']}` | {article['article_role']} | "
            f"{article['pedot_pss_loading_fraction']} | {', '.join(article['timepoints'])} | "
            f"{article['stop_if']} |"
        )

    lines.extend([
        "",
        "## Claim-Critical Fields",
        "",
        "| Field | Rows | Meaning |",
        "| --- | ---: | --- |",
    ])
    for item in result["required_fields"]:
        lines.append(f"| `{item['field']}` | {item['rows']} | {item['description']} |")

    lines.extend([
        "",
        "## Provenance Per Raw Row",
        "",
    ])
    lines.extend(f"- `{field}`" for field in result["provenance_fields_per_raw_row"])

    hotspots = result.get("qc_missing_hotspots", [])
    if hotspots:
        lines.extend([
            "",
            "## Current QC Hotspots",
            "",
            "| Field | Error rows |",
            "| --- | ---: |",
        ])
        for item in hotspots[:20]:
            lines.append(f"| `{item['field']}` | {item['rows']} |")

    lines.extend([
        "",
        "## After Filling Real Values",
        "",
        "```bash",
        "python3 scripts/run_limina_iteration.py",
        "```",
        "",
        "## Boundary",
        "",
        result["non_claim_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A minimum measurement checklist.")
    parser.add_argument("--bench", type=Path, default=DEFAULT_BENCH)
    parser.add_argument("--qc", type=Path, default=DEFAULT_QC)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_checklist(load_json(args.bench), load_json(args.qc))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Rendered H-A minimum measurement checklist: runs={result['run_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
