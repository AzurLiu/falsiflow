#!/usr/bin/env python3
"""Interpret the compact NHI-PEDOT H-A sentinel measurement batch."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import PLACEHOLDER_MARKERS, SYNTHETIC_MARKERS, provenance
from evaluate_nhi_pedot_runs import (
    BASELINE_TIMEPOINTS,
    HYDROGEL_CONTROL,
    LEAD_ARTICLE,
    NO_COATING_CONTROL,
    evaluate_blank_gate,
    evaluate_physical_gate,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS = ROOT / "data" / "nhi_pedot_h_a_sentinel_template.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_sentinel_interpretation.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_sentinel_interpretation.md"

PHASE = "H-A"
CHALLENGE_ARTICLE = "challenge_nhi_pedot_high_loading"
MATERIAL_ARTICLES = {
    HYDROGEL_CONTROL,
    LEAD_ARTICLE,
    CHALLENGE_ARTICLE,
}
EXPECTED_ARTICLES = [
    NO_COATING_CONTROL,
    HYDROGEL_CONTROL,
    LEAD_ARTICLE,
    CHALLENGE_ARTICLE,
]
EXPECTED_TIMEPOINTS = ["0 h", "24 h", "72 h"]
REQUIRED_FIELDS = [
    "date",
    "operator_or_agent",
    "medium_name",
    "medium_lot",
    "temperature_c",
    "pH_initial",
    "pH_final",
    "osmolality_initial_mOsm_kg",
    "osmolality_final_mOsm_kg",
    "conductivity_initial_mS_cm",
    "conductivity_final_mS_cm",
    "visible_precipitate",
    "visible_shedding",
    "swelling_fraction",
    "delamination_score",
    "optical_transparency_fraction",
    "source_file",
]
SOURCE_SPLIT_CHARS = [";", "|", "\n"]


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def resolve_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return ROOT / path


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def allowed_roots(manifest: dict[str, Any]) -> list[Path]:
    roots: list[Path] = []
    for row in manifest.get("allowed_roots", []):
        raw = str(row.get("path", "")).strip()
        if not raw:
            continue
        path = Path(raw)
        if not path.is_absolute():
            path = ROOT / path
        roots.append(path)
    return roots


def split_source_files(raw: str) -> list[str]:
    refs = [raw.strip().strip("\"'")]
    for char in SOURCE_SPLIT_CHARS:
        expanded: list[str] = []
        for ref in refs:
            expanded.extend(part.strip().strip("\"'") for part in ref.split(char))
        refs = expanded
    return [ref for ref in refs if ref]


def has_rejected_marker(raw: str, manifest: dict[str, Any]) -> bool:
    markers = set(PLACEHOLDER_MARKERS) | set(SYNTHETIC_MARKERS)
    markers.update(str(item).strip().lower() for item in manifest.get("rejected_source_markers", []) if str(item).strip())
    lowered = raw.lower()
    return any(marker in lowered for marker in markers)


def row_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("phase", ""),
        row.get("timepoint", ""),
        row.get("replicate", ""),
        row.get("article_id", ""),
    )


def is_baseline(row: dict[str, str]) -> bool:
    return row.get("timepoint", "").strip().lower() in BASELINE_TIMEPOINTS


def phase_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("phase") == PHASE and row.get("run_id")]


def index_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, str]]:
    return {row_key(row): row for row in rows}


def missing_expected_rows(rows: list[dict[str, str]]) -> list[str]:
    present = {row_key(row) for row in rows}
    missing = []
    for article in EXPECTED_ARTICLES:
        for timepoint in EXPECTED_TIMEPOINTS:
            key = (PHASE, timepoint, "1", article)
            if key not in present:
                missing.append("|".join(key))
    return missing


def missing_required_fields(row: dict[str, str]) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not row.get(field, "").strip()]


def source_file_issues(rows: list[dict[str, str]], manifest_path: Path) -> list[dict[str, str]]:
    manifest = load_json(manifest_path)
    roots = allowed_roots(manifest)
    issues: list[dict[str, str]] = []
    for row in rows:
        run_id = row.get("run_id", "")
        for ref in split_source_files(row.get("source_file", "")):
            if has_rejected_marker(ref, manifest):
                issues.append({
                    "run_id": run_id,
                    "source_file": ref,
                    "message": "source_file contains a rejected placeholder/synthetic/source marker",
                })
                continue
            path = resolve_path(ref)
            if not path.exists():
                issues.append({"run_id": run_id, "source_file": ref, "message": "source_file does not exist"})
                continue
            if not path.is_file():
                issues.append({"run_id": run_id, "source_file": ref, "message": "source_file is not a concrete file"})
                continue
            if not roots:
                issues.append({"run_id": run_id, "source_file": ref, "message": "source manifest has no allowed roots"})
                continue
            if not any(path_is_within(path, root) for root in roots):
                issues.append({"run_id": run_id, "source_file": ref, "message": "source_file is outside allowed roots"})
    return issues


def required_field_report(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    missing = []
    for row in rows:
        fields = missing_required_fields(row)
        if fields:
            missing.append({
                "run_id": row.get("run_id", ""),
                "article_id": row.get("article_id", ""),
                "timepoint": row.get("timepoint", ""),
                "missing_fields": fields,
            })
    return missing


def evaluate_material_row(
    row: dict[str, str],
    indexed: dict[tuple[str, str, str, str], dict[str, str]],
) -> dict[str, Any]:
    control = indexed.get((PHASE, row.get("timepoint", ""), row.get("replicate", ""), NO_COATING_CONTROL))
    blank_status, blank_metrics = evaluate_blank_gate(row, control)
    physical_status, physical_metrics = evaluate_physical_gate(row)
    if is_baseline(row):
        status = "baseline"
    elif "fail" in {blank_status, physical_status}:
        status = "fail"
    elif blank_status == "pass" and physical_status == "pass":
        status = "pass"
    else:
        status = "not_evaluable"
    return {
        "run_id": row.get("run_id", ""),
        "article_id": row.get("article_id", ""),
        "variant_id": row.get("variant_id", ""),
        "timepoint": row.get("timepoint", ""),
        "replicate": row.get("replicate", ""),
        "control_run_id": control.get("run_id", "") if control else "",
        "status": status,
        "gate_results": {
            "blank_integrity_gate": blank_status,
            "physical_stability_gate": physical_status,
        },
        "metrics": {
            **blank_metrics,
            **physical_metrics,
        },
    }


def sentinel_decision(evaluations: list[dict[str, Any]]) -> tuple[str, str]:
    gate_rows = [item for item in evaluations if item["status"] != "baseline"]
    lead_rows = [item for item in gate_rows if item["article_id"] == LEAD_ARTICLE]
    hydrogel_rows = [item for item in gate_rows if item["article_id"] == HYDROGEL_CONTROL]
    challenge_rows = [item for item in gate_rows if item["article_id"] == CHALLENGE_ARTICLE]
    not_evaluable = [item for item in gate_rows if item["status"] == "not_evaluable"]
    lead_failed = [item for item in lead_rows if item["status"] == "fail"]
    lead_passed = [item for item in lead_rows if item["status"] == "pass"]
    hydrogel_failed = [item for item in hydrogel_rows if item["status"] == "fail"]
    challenge_failed = [item for item in challenge_rows if item["status"] == "fail"]

    if not_evaluable:
        return (
            "h_a_sentinel_needs_more_data",
            "Fill missing H-A readouts or matched no-coating controls before deciding whether to continue.",
        )
    if lead_failed:
        return (
            "h_a_lead_fails_stop",
            "Do not advance ALG-LAM-PEDOT to H-B or H-C; branch by failed medium-integrity or physical-stability gate.",
        )
    if not lead_passed:
        return (
            "h_a_sentinel_needs_lead_rows",
            "Add gate-evaluable non-baseline lead rows at 24 h and 72 h with matched no-coating controls.",
        )
    if hydrogel_failed:
        return (
            "h_a_lead_passes_hydrogel_control_issue",
            "Lead rows pass, but hydrogel-only control fails; repeat or resolve matrix-control failure before H-C live-cell exposure.",
        )
    if challenge_failed:
        return (
            "h_a_lead_passes_continue_challenge_boundary",
            "Lead rows pass; high-loading challenge failed and should remain a boundary comparator, not a promoted article.",
        )
    return (
        "h_a_lead_passes_continue_h_b",
        "Lead H-A rows pass. Continue to H-B electrochemical/physical stability; this is still not suitability evidence.",
    )


def interpret(rows: list[dict[str, str]], runs_path: Path, source_manifest: Path = DEFAULT_SOURCE_MANIFEST) -> dict[str, Any]:
    h_a_rows = phase_rows(rows)
    source = provenance(runs_path)
    if source["row_count"] == 0:
        return {
            "status": "h_a_no_sentinel_rows",
            "next_action": "Generate and fill the recipe-locked H-A sentinel packet.",
            "provenance": source,
            "missing_expected_rows": [],
            "missing_required_fields": [],
            "source_file_issues": [],
            "evaluations": [],
        }
    if source["synthetic_row_count"] > 0 or source["placeholder_row_count"] > 0:
        return {
            "status": "h_a_invalid_provenance",
            "next_action": "Replace fixture, pending, and record_actual/record_lot placeholders with real measured provenance before interpreting H-A.",
            "provenance": source,
            "missing_expected_rows": missing_expected_rows(h_a_rows),
            "missing_required_fields": required_field_report(h_a_rows),
            "source_file_issues": [],
            "evaluations": [],
        }

    missing_rows = missing_expected_rows(h_a_rows)
    missing_fields = required_field_report(h_a_rows)
    if missing_rows or missing_fields:
        return {
            "status": "h_a_sentinel_needs_more_data",
            "next_action": "Complete the expected H-A row set and required medium/physical readouts before gate interpretation.",
            "provenance": source,
            "missing_expected_rows": missing_rows,
            "missing_required_fields": missing_fields,
            "source_file_issues": [],
            "evaluations": [],
        }

    source_issues = source_file_issues(h_a_rows, source_manifest)
    if source_issues:
        return {
            "status": "h_a_invalid_source_files",
            "next_action": "Replace missing, rejected, or out-of-policy H-A source_file references with real raw source files before gate interpretation.",
            "provenance": source,
            "missing_expected_rows": missing_rows,
            "missing_required_fields": missing_fields,
            "source_file_issues": source_issues,
            "evaluations": [],
        }

    indexed = index_rows(h_a_rows)
    material_rows = [
        row for row in h_a_rows
        if row.get("article_id") in MATERIAL_ARTICLES
    ]
    evaluations = [evaluate_material_row(row, indexed) for row in material_rows]
    status, next_action = sentinel_decision(evaluations)
    return {
        "status": status,
        "next_action": next_action,
        "provenance": source,
        "missing_expected_rows": missing_rows,
        "missing_required_fields": missing_fields,
        "source_file_issues": [],
        "evaluations": evaluations,
    }


def format_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def render_report(result: dict[str, Any], runs_path: Path) -> str:
    source = result["provenance"]
    lines = [
        "# NHI-PEDOT H-A Sentinel Interpretation",
        "",
        f"**Input:** `{runs_path}`",
        f"**Status:** `{result['status']}`",
        f"**Next action:** {result['next_action']}",
        f"**Rows:** {source['row_count']}",
        f"**Measured rows:** {source['measured_row_count']}",
        f"**Synthetic rows:** {source['synthetic_row_count']}",
        f"**Placeholder rows:** {source['placeholder_row_count']}",
        "",
    ]

    if result["missing_expected_rows"]:
        lines.extend(["## Missing Expected Rows", ""])
        lines.extend(f"- `{item}`" for item in result["missing_expected_rows"])
        lines.append("")

    if result["missing_required_fields"]:
        lines.extend([
            "## Missing Required Fields",
            "",
            "| Run | Article | Timepoint | Missing fields |",
            "| --- | --- | --- | --- |",
        ])
        for item in result["missing_required_fields"]:
            lines.append(
                f"| `{item['run_id']}` | `{item['article_id']}` | {item['timepoint']} | "
                f"{', '.join(f'`{field}`' for field in item['missing_fields'])} |"
            )
        lines.append("")

    if result.get("source_file_issues"):
        lines.extend([
            "## Source File Issues",
            "",
            "| Run | Source file | Message |",
            "| --- | --- | --- |",
        ])
        for item in result["source_file_issues"][:80]:
            lines.append(f"| `{item['run_id']}` | `{item['source_file']}` | {item['message']} |")
        if len(result["source_file_issues"]) > 80:
            lines.append(f"| `-` | `-` | {len(result['source_file_issues']) - 80} additional issues omitted. |")
        lines.append("")

    lines.extend([
        "## Row Interpretation",
        "",
        "| Run | Article | Timepoint | Status | Blank | Physical | pH dControl | Osm dControl | Cond dControl | Swelling | Delamination | Transparency |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for item in result["evaluations"]:
        metrics = item["metrics"]
        gates = item["gate_results"]
        lines.append(
            f"| `{item['run_id']}` | `{item['article_id']}` | {item['timepoint']} | `{item['status']}` | "
            f"`{gates['blank_integrity_gate']}` | `{gates['physical_stability_gate']}` | "
            f"{format_value(metrics['pH_delta_vs_no_coating'])} | "
            f"{format_value(metrics['osmolality_fractional_change_vs_no_coating'])} | "
            f"{format_value(metrics['conductivity_fractional_change_vs_no_coating'])} | "
            f"{format_value(metrics['swelling_fraction'])} | "
            f"{format_value(metrics['delamination_score'])} | "
            f"{format_value(metrics['optical_transparency_fraction'])} |"
        )
    if not result["evaluations"]:
        lines.append("| - | - | - | - | - | - | - | - | - | - | - | - |")

    lines.extend([
        "",
        "## Scope Note",
        "",
        "- H-A only checks acellular medium integrity and physical stability.",
        "- A pass can authorize H-B electrochemical testing, but cannot support a suitability claim.",
        "- Claim readiness still requires non-synthetic H-A/H-B/H-C and long-duration measured rows.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interpret NHI-PEDOT H-A sentinel rows.")
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = interpret(load_csv(args.runs), args.runs, args.source_manifest)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result, args.runs), encoding="utf-8")
    print(f"NHI-PEDOT H-A sentinel: {result['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
