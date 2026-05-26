#!/usr/bin/env python3
"""Merge measured ZRC-ND rows into an evaluator-ready runs CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "data" / "zrc_nd_validation_runs_template.csv"
DEFAULT_MEASUREMENTS = ROOT / "data" / "zrc_nd_phase_a_vendor_return_inbox" / "completed_phase_a_measurements.csv"
DEFAULT_OUT = ROOT / "data" / "zrc_nd_validation_runs_active.csv"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_measurement_merge.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_measurement_merge.md"
SCAFFOLD_FIELDS = {
    "run_id",
    "phase",
    "timepoint",
    "replicate",
    "article_id",
    "variant_id",
    "control_article_id",
    "mwco_kda",
    "surface_modification",
    "housing_material",
    "gate_results",
    "notes",
}


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(fields: list[str], rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def has_merge_signal(row: dict[str, str]) -> bool:
    return any(
        str(value).strip()
        for field, value in row.items()
        if field not in SCAFFOLD_FIELDS
    )


def merge_rows(fields: list[str], base_rows: list[dict[str, str]], measured_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    by_id = {row["run_id"]: {field: row.get(field, "") for field in fields} for row in base_rows if row.get("run_id")}
    inserted = 0
    updated = 0
    skipped = 0
    for measured in measured_rows:
        run_id = measured.get("run_id", "")
        if not run_id:
            skipped += 1
            continue
        clean = {field: measured.get(field, "") for field in fields}
        if not has_merge_signal(clean):
            skipped += 1
            continue
        if run_id in by_id:
            merged = by_id[run_id]
            changed = False
            for field, value in clean.items():
                if value != "" and merged.get(field, "") != value:
                    merged[field] = value
                    changed = True
            if changed:
                updated += 1
            else:
                skipped += 1
        else:
            by_id[run_id] = clean
            inserted += 1
    rows = sorted(by_id.values(), key=lambda row: row.get("run_id", ""))
    return rows, {"inserted": inserted, "updated": updated, "skipped": skipped, "total": len(rows)}


def summarize(base: Path, measurements: Path, out: Path, stats: dict[str, int], measured_rows: list[dict[str, str]]) -> dict[str, object]:
    if not measurements.exists():
        status = "awaiting_measurement_file"
    elif not measured_rows:
        status = "awaiting_measurement_rows"
    elif stats["inserted"] or stats["updated"]:
        status = "merged_measurements"
    else:
        status = "no_mergeable_measurements"
    return {
        "status": status,
        "base": str(base),
        "measurements": str(measurements),
        "output": str(out),
        "measurement_file_exists": measurements.exists(),
        "measurement_rows": len(measured_rows),
        "stats": stats,
    }


def render_report(result: dict[str, object]) -> str:
    stats = result["stats"]
    return "\n".join([
        "# ZRC-ND Measurement Merge",
        "",
        f"**Status:** `{result['status']}`",
        f"**Base:** `{result['base']}`",
        f"**Measurements:** `{result['measurements']}`",
        f"**Measurement file exists:** `{str(result['measurement_file_exists']).lower()}`",
        f"**Measurement rows:** {result['measurement_rows']}",
        f"**Output:** `{result['output']}`",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Inserted rows | {stats['inserted']} |",
        f"| Updated rows | {stats['updated']} |",
        f"| Skipped rows | {stats['skipped']} |",
        f"| Output rows | {stats['total']} |",
        "",
        "The output is evaluator-ready, but suitability still depends on gate evaluation and readiness audit results.",
        "",
    ])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge ZRC-ND measured rows.")
    parser.add_argument("--base", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--measurements", type=Path, default=DEFAULT_MEASUREMENTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    base_fields, base_rows = load_csv(args.base)
    measurement_fields, measured_rows = load_csv(args.measurements)
    fields = base_fields or measurement_fields
    if not fields:
        raise ValueError("No CSV header found in base or measurements.")
    rows, stats = merge_rows(fields, base_rows, measured_rows)
    write_csv(fields, rows, args.out)
    result = summarize(args.base, args.measurements, args.out, stats, measured_rows)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Merged measurements: inserted={stats['inserted']} updated={stats['updated']} skipped={stats['skipped']}")
    print(f"Status: {result['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
