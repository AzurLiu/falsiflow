#!/usr/bin/env python3
"""Generate a compact NHI-PEDOT H-A sentinel data-entry packet."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "data" / "nhi_pedot_validation_package.json"
DEFAULT_PLANNED = ROOT / "data" / "nhi_pedot_planned_runs.csv"
DEFAULT_NEXT = ROOT / "data" / "nhi_pedot_next_measurements.csv"
DEFAULT_RECIPE_LOCK = ROOT / "data" / "nhi_pedot_recipe_lock_v0_2.json"
DEFAULT_TEMPLATE = ROOT / "data" / "nhi_pedot_h_a_sentinel_template.csv"
DEFAULT_MANIFEST = ROOT / "data" / "nhi_pedot_h_a_sentinel_sample_manifest.csv"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_sentinel_packet.md"

SAMPLE_EVENTS = ["initial", "final", "physical_inspection"]
READOUTS = [
    "pH",
    "osmolality",
    "conductivity",
    "visible_precipitate",
    "visible_shedding",
    "swelling_fraction",
    "delamination_score",
    "optical_transparency_fraction",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = load_json(path)
    return value if isinstance(value, dict) else {}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(rows: list[dict[str, str]], fields: list[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def planned_by_id(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["run_id"]: row for row in rows if row.get("run_id")}


def apply_recipe_lock(row: dict[str, str], recipe_lock: dict[str, Any]) -> None:
    if not recipe_lock:
        return
    article_id = row.get("article_id", "")
    overrides = recipe_lock.get("template_defaults", {}).get(article_id, {})
    for field, value in overrides.items():
        if field in row:
            row[field] = str(value)
    notes = row.get("notes", "")
    lock_id = recipe_lock.get("id", "")
    if lock_id and lock_id not in notes:
        row["notes"] = f"{notes};{lock_id}" if notes else lock_id


def template_rows(
    package: dict[str, Any],
    planned: dict[str, dict[str, str]],
    next_rows: list[dict[str, str]],
    recipe_lock: dict[str, Any],
) -> list[dict[str, str]]:
    fields = package["data_capture_fields"]
    rows: list[dict[str, str]] = []
    for next_row in next_rows:
        run_id = next_row["run_id"]
        planned_row = planned.get(run_id, {})
        row = {field: "" for field in fields}
        for field in fields:
            if planned_row.get(field, "") != "":
                row[field] = planned_row[field]
        row.update({
            "run_id": run_id,
            "operator_or_agent": "limina",
            "phase": next_row.get("phase", planned_row.get("phase", "")),
            "timepoint": next_row.get("timepoint", planned_row.get("timepoint", "")),
            "replicate": next_row.get("replicate", planned_row.get("replicate", "")),
            "article_id": next_row.get("article_id", planned_row.get("article_id", "")),
            "variant_id": next_row.get("variant_id", planned_row.get("variant_id", "")),
            "notes": "nhi_pedot_h_a_sentinel_pending_real_measurement",
        })
        apply_recipe_lock(row, recipe_lock)
        rows.append(row)
    return rows


def sample_manifest_rows(next_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for next_row in next_rows:
        for event in SAMPLE_EVENTS:
            rows.append({
                "sample_id": f"{next_row['run_id']}-{event}",
                "run_id": next_row["run_id"],
                "sample_event": event,
                "phase": next_row["phase"],
                "timepoint": next_row["timepoint"],
                "replicate": next_row["replicate"],
                "article_id": next_row["article_id"],
                "readouts": ";".join(READOUTS),
                "handoff_notes": "record coupon/well id, image before and after soak, then enter numeric fields in template",
            })
    return rows


def render_report(
    next_rows: list[dict[str, str]],
    template_path: Path,
    manifest_path: Path,
    recipe_lock: dict[str, Any],
) -> str:
    lines = [
        "# NHI-PEDOT H-A Sentinel Packet",
        "",
        f"**Data-entry template:** `{template_path}`",
        f"**Sample manifest:** `{manifest_path}`",
        f"**Rows:** {len(next_rows)}",
        f"**Recipe lock:** `{recipe_lock.get('id', '-')}`",
        "",
        "This packet is for the first acellular direct-contact sentinel. It is not evidence until real measurements are entered.",
        "",
        "## Measurement Rows",
        "",
        "| Run | Timepoint | Article | Readouts |",
        "| --- | --- | --- | --- |",
    ]
    for row in next_rows:
        lines.append(
            f"| `{row['run_id']}` | {row['timepoint']} | `{row['article_id']}` | {row['readout_groups']} |"
        )

    lines.extend([
        "",
        "## H-A Gate",
        "",
        "- Compare medium-integrity drift to the matched `no_coating_mea_control` row with the same timepoint and replicate.",
        "- Pass requires material-driven pH drift <= 0.10 pH units versus no-coating control.",
        "- Pass requires osmolality and conductivity drift <= 5 percent versus no-coating control.",
        "- Pass requires no visible precipitate, no visible shedding, swelling <= 20 percent, delamination score <= 0.5, and optical transparency >= 0.80.",
        "- If the lead fails H-A, do not advance to H-B electrochemistry or H-C neural culture.",
        "",
        "## Recipe Lock",
        "",
    ])
    if recipe_lock:
        targets = recipe_lock.get("design_targets", {})
        lines.extend([
            f"- Candidate: `{recipe_lock.get('candidate_id', '-')}`",
            f"- Hydrogel matrix: `{targets.get('hydrogel_matrix', '-')}`",
            f"- Conductive phase: {targets.get('conductive_phase', '-')}",
            f"- First-claim boundary: {targets.get('first_claim_boundary', '-')}",
            "- Replace `record_exact` labels with actual formulation/process values before treating rows as measured evidence.",
            "",
        ])
    else:
        lines.extend(["- No recipe lock file was provided.", ""])

    lines.extend([
        "## After Measurement",
        "",
        "1. Fill the data-entry template with real values.",
        "2. Use the template as an active runs CSV for `evaluate_nhi_pedot_runs.py`.",
        "3. Re-run `suggest_nhi_pedot_next_measurements.py` to decide whether to continue, repeat, or stop.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate NHI-PEDOT H-A sentinel packet.")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--planned", type=Path, default=DEFAULT_PLANNED)
    parser.add_argument("--next", type=Path, default=DEFAULT_NEXT)
    parser.add_argument("--recipe-lock", type=Path, default=DEFAULT_RECIPE_LOCK)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package = load_json(args.package)
    recipe_lock = load_optional_json(args.recipe_lock)
    planned = planned_by_id(load_csv(args.planned))
    next_rows = load_csv(args.next)
    rows = template_rows(package, planned, next_rows, recipe_lock)
    manifest = sample_manifest_rows(next_rows)
    write_csv(rows, package["data_capture_fields"], args.template)
    fields = list(manifest[0]) if manifest else [
        "sample_id",
        "run_id",
        "sample_event",
        "phase",
        "timepoint",
        "replicate",
        "article_id",
        "readouts",
        "handoff_notes",
    ]
    write_csv(manifest, fields, args.manifest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(next_rows, args.template, args.manifest, recipe_lock), encoding="utf-8")
    print(f"Generated {len(rows)} NHI-PEDOT H-A sentinel template rows")
    print(f"Generated {len(manifest)} sample manifest rows")
    print(f"Wrote {args.template}")
    print(f"Wrote {args.manifest}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
