#!/usr/bin/env python3
"""Generate an execution queue and sample manifest for ZRC-ND non-cell validation."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "zrc_nd_3p5k_guard_validation_package.json"
DEFAULT_PLANNED = ROOT / "data" / "zrc_nd_planned_runs.csv"
DEFAULT_QUEUE = ROOT / "data" / "zrc_nd_execution_queue.csv"
DEFAULT_MANIFEST = ROOT / "data" / "zrc_nd_sample_manifest.csv"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_execution_queue.md"

PHASE_ORDER = {"A": 1, "B": 2, "C": 3}
CONTROL_ARTICLES = {"no_module_static_control", "bulk_exchange_reference"}
BASELINE_TIMEPOINTS = {"0 h", "0h", "0"}

CORE_FIELDS = [
    "date",
    "operator_or_agent",
    "medium_name",
    "medium_lot",
    "initial_volume_ml",
    "exposure_time_h",
    "temperature_c",
]
ARTICLE_FIELDS = ["membrane_lot", "membrane_area_cm2", "prefilter_lot", "housing_material"]
BLANK_FIELDS = [
    "pH_initial",
    "pH_final",
    "osmolality_initial_mOsm_kg",
    "osmolality_final_mOsm_kg",
    "conductivity_initial_mS_cm",
    "conductivity_final_mS_cm",
    "visible_precipitate",
]
RETENTION_FIELDS = [
    "bdnf_initial_pg_ml",
    "bdnf_final_pg_ml",
    "ngf_initial_pg_ml",
    "ngf_final_pg_ml",
    "albumin_initial",
    "albumin_final",
    "transferrin_initial",
    "transferrin_final",
    "total_protein_initial",
    "total_protein_final",
]
CLEARANCE_FIELDS = [
    "lactate_initial_mM",
    "lactate_final_mM",
    "ammonia_initial_uM",
    "ammonia_final_uM",
]
FOULING_FIELDS = ["flow_resistance_initial", "flow_resistance_final", "bubble_events"]

READOUT_GROUPS_BY_PHASE = {
    "A": ["medium_integrity"],
    "B": ["medium_integrity", "waste_clearance", "factor_retention", "module_performance"],
    "C": ["medium_integrity", "waste_clearance", "factor_retention", "module_performance"],
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def is_baseline(row: dict[str, str]) -> bool:
    return row.get("timepoint", "").strip().lower() in BASELINE_TIMEPOINTS


def gate_role(row: dict[str, str]) -> str:
    if row.get("article_id") == "bulk_exchange_reference":
        return "process_reference"
    if row.get("article_id") == "no_module_static_control":
        return "matched_control"
    if is_baseline(row):
        return "baseline_snapshot"
    return "gate_evaluable"


def required_fields(row: dict[str, str]) -> list[str]:
    fields = list(CORE_FIELDS)
    if row.get("article_id") not in CONTROL_ARTICLES:
        fields.extend(ARTICLE_FIELDS)
    fields.extend(BLANK_FIELDS)
    if row.get("phase") in {"B", "C"}:
        fields.extend(CLEARANCE_FIELDS)
        fields.extend(RETENTION_FIELDS)
        fields.extend(FOULING_FIELDS)
    return sorted(dict.fromkeys(fields))


def readout_groups(row: dict[str, str]) -> list[str]:
    return READOUT_GROUPS_BY_PHASE.get(row.get("phase", ""), ["medium_integrity"])


def queue_rows(planned_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    sorted_rows = sorted(
        planned_rows,
        key=lambda row: (
            PHASE_ORDER.get(row.get("phase", ""), 99),
            int(row.get("replicate") or 0),
            row.get("article_id", ""),
            row.get("timepoint", ""),
        ),
    )
    for index, row in enumerate(sorted_rows, start=1):
        role = gate_role(row)
        rows.append({
            "queue_order": str(index),
            "run_id": row.get("run_id", ""),
            "phase": row.get("phase", ""),
            "timepoint": row.get("timepoint", ""),
            "replicate": row.get("replicate", ""),
            "article_id": row.get("article_id", ""),
            "variant_id": row.get("variant_id", ""),
            "gate_role": role,
            "readout_groups": ";".join(readout_groups(row)),
            "must_have_fields": ";".join(required_fields(row)),
            "matched_control_key": f"{row.get('phase', '')}|{row.get('timepoint', '')}|{row.get('replicate', '')}",
        })
    return rows


def sample_manifest_rows(queue: list[dict[str, str]]) -> list[dict[str, str]]:
    samples: list[dict[str, str]] = []
    for row in queue:
        for event in ["initial", "final"]:
            samples.append({
                "sample_id": f"{row['run_id']}-{event}",
                "run_id": row["run_id"],
                "sample_event": event,
                "phase": row["phase"],
                "timepoint": row["timepoint"],
                "replicate": row["replicate"],
                "article_id": row["article_id"],
                "readout_groups": row["readout_groups"],
                "storage_or_handoff": "record local sample location and assay plate/well before analysis",
            })
    return samples


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_report(package: dict[str, Any], queue: list[dict[str, str]], manifest: list[dict[str, str]]) -> str:
    phase_counts: dict[str, int] = {}
    role_counts: dict[str, int] = {}
    first_phase_a = [
        row for row in queue
        if row["phase"] == "A" and row["gate_role"] in {"matched_control", "gate_evaluable"}
    ]
    for row in queue:
        phase_counts[row["phase"]] = phase_counts.get(row["phase"], 0) + 1
        role_counts[row["gate_role"]] = role_counts.get(row["gate_role"], 0) + 1

    lines = [
        "# ZRC-ND Non-Cell Execution Queue",
        "",
        f"**Validation package:** `{package['id']}`",
        f"**Lead variant:** `{package['lead_variant_id']}`",
        f"**Queue rows:** {len(queue)}",
        f"**Sample manifest rows:** {len(manifest)}",
        "",
        "This is an execution scaffold for non-cell media-chemistry validation. It is not experimental evidence.",
        "",
        "## Queue Counts",
        "",
        "| Phase | Rows |",
        "| --- | ---: |",
    ]
    for phase in sorted(phase_counts):
        lines.append(f"| {phase} | {phase_counts[phase]} |")
    lines.extend(["", "| Role | Rows |", "| --- | ---: |"])
    for role in sorted(role_counts):
        lines.append(f"| `{role}` | {role_counts[role]} |")

    lines.extend([
        "",
        "## First Evidence-Unlocking Tranche",
        "",
        "Phase A should be filled before Phase B/C and before any biological follow-up. The rows below are the first gate-relevant tranche.",
        "",
        "| Queue | Run | Article | Timepoint | Replicate | Required readouts |",
        "| ---: | --- | --- | --- | --- | --- |",
    ])
    for row in first_phase_a[:16]:
        lines.append(
            f"| {row['queue_order']} | `{row['run_id']}` | `{row['article_id']}` | "
            f"{row['timepoint']} | {row['replicate']} | {row['readout_groups']} |"
        )

    lines.extend([
        "",
        "## Data Integrity Rules",
        "",
        "- Every gate-evaluable row needs a matched `no_module_static_control` row with the same phase, timepoint, and replicate.",
        "- `0 h` rows are baseline snapshots; they are useful for traceability but must not be counted as material pass/fail evidence.",
        "- Phase A unlocks only blank-integrity evidence. Phase B/C carry waste-clearance, factor-retention, and fouling evidence.",
        "- Synthetic fixture rows are allowed only for evaluator regression; real suitability requires measured rows in the validation template.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate ZRC-ND execution queue.")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--planned", type=Path, default=DEFAULT_PLANNED)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package = load_json(args.package)
    planned = load_csv(args.planned)
    queue = queue_rows(planned)
    manifest = sample_manifest_rows(queue)
    write_csv(queue, args.queue)
    write_csv(manifest, args.manifest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(package, queue, manifest), encoding="utf-8")
    print(f"Generated {len(queue)} execution queue rows")
    print(f"Generated {len(manifest)} sample manifest rows")
    print(f"Wrote {args.queue}")
    print(f"Wrote {args.manifest}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
