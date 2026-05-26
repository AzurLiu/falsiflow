#!/usr/bin/env python3
"""Audit whether ZRC-ND can be claimed as a suitable material technology."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CRITERIA = ROOT / "data" / "readiness_criteria.json"
DEFAULT_RESULTS = ROOT / "data" / "zrc_nd_validation_results.json"
DEFAULT_BIO_RESULTS = ROOT / "data" / "zrc_nd_bio_results.json"
DEFAULT_TECH = ROOT / "data" / "limina_material_technologies.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_readiness_audit.md"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def empty_results(aggregate_field: str) -> dict[str, Any]:
    return {
        "summary": {
            "status": "no_data",
            "rows": 0,
            "lead_rows": 0,
            "failed_rows": 0,
            "phase_coverage": [],
            aggregate_field: "not_evaluable",
        },
        "aggregate_gates": [],
        "evaluations": [],
    }


def load_results_or_empty(path: Path, aggregate_field: str) -> dict[str, Any]:
    if not path.exists():
        return empty_results(aggregate_field)
    return load_json(path)


def load_records(path: Path) -> list[dict[str, Any]]:
    value = load_json(path)
    if isinstance(value, dict):
        return [value]
    return value


def find_record(records: list[dict[str, Any]], record_id: str) -> dict[str, Any] | None:
    for record in records:
        if record.get("id") == record_id:
            return record
    return None


def audit(
    criteria: dict[str, Any],
    results: dict[str, Any],
    bio_results: dict[str, Any],
    technology: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = results.get("summary", {})
    bio_summary = bio_results.get("summary", {})
    non_cell = criteria["non_cell_validation_required"]
    biological = criteria["biological_followup_required"]

    phase_coverage = set(summary.get("phase_coverage", []))
    required_phases = set(non_cell["required_phase_coverage"])
    passed_lead_replicates = summary.get("passed_lead_replicates_by_phase", {})
    lead_rows = [
        row for row in results.get("evaluations", [])
        if row.get("variant_id") == criteria["lead_variant_id"]
    ]
    failed_lead_rows = [row for row in lead_rows if row.get("status") == "fail"]

    bio_phase_coverage = set(bio_summary.get("phase_coverage", []))
    bio_required_phases = set(biological["required_phase_coverage"])
    bio_passed_lead_replicates = bio_summary.get("passed_lead_replicates_by_phase", {})
    bio_lead_rows = [
        row for row in bio_results.get("evaluations", [])
        if row.get("variant_id") == criteria["lead_variant_id"]
    ]
    failed_bio_lead_rows = [row for row in bio_lead_rows if row.get("status") == "fail"]

    general_checks = [
        {
            "id": "technology_record_present",
            "status": "pass" if technology else "fail",
            "detail": "Technology record exists." if technology else "Technology record is missing.",
        },
    ]
    non_cell_checks = [
        {
            "id": "validation_result_status",
            "status": "pass" if summary.get("status") == non_cell["validation_result_status"] else "fail",
            "detail": f"Expected `{non_cell['validation_result_status']}`, observed `{summary.get('status', '<missing>')}`.",
        },
        {
            "id": "aggregate_lead_superiority",
            "status": "pass" if summary.get("aggregate_lead_superiority") == non_cell["aggregate_lead_superiority"] else "fail",
            "detail": f"Expected `{non_cell['aggregate_lead_superiority']}`, observed `{summary.get('aggregate_lead_superiority', '<missing>')}`.",
        },
        {
            "id": "phase_coverage",
            "status": "pass" if phase_coverage >= required_phases else "fail",
            "detail": (
                f"Required {sorted(required_phases)}, observed {sorted(phase_coverage)}."
            ),
        },
        {
            "id": "lead_replicate_coverage",
            "status": "pass" if all(
                len(passed_lead_replicates.get(phase, [])) >= non_cell["min_passed_lead_replicates_per_phase"]
                for phase in required_phases
            ) else "fail",
            "detail": (
                f"Required >= {non_cell['min_passed_lead_replicates_per_phase']} passed lead replicates per phase; "
                f"observed {passed_lead_replicates}."
            ),
        },
        {
            "id": "failed_lead_rows",
            "status": "pass" if len(failed_lead_rows) <= non_cell["allowed_failed_lead_rows"] else "fail",
            "detail": f"Failed lead rows: {len(failed_lead_rows)}.",
        },
    ]

    bio_checks = [
        {
            "id": "bio_result_status",
            "status": "pass" if bio_summary.get("status") == biological["bio_result_status"] else "fail",
            "detail": f"Expected `{biological['bio_result_status']}`, observed `{bio_summary.get('status', '<missing>')}`.",
        },
        {
            "id": "aggregate_bio_superiority",
            "status": "pass" if bio_summary.get("aggregate_bio_superiority") == biological["aggregate_bio_superiority"] else "fail",
            "detail": f"Expected `{biological['aggregate_bio_superiority']}`, observed `{bio_summary.get('aggregate_bio_superiority', '<missing>')}`.",
        },
        {
            "id": "bio_phase_coverage",
            "status": "pass" if bio_phase_coverage >= bio_required_phases else "fail",
            "detail": f"Required {sorted(bio_required_phases)}, observed {sorted(bio_phase_coverage)}.",
        },
        {
            "id": "bio_lead_replicate_coverage",
            "status": "pass" if all(
                len(bio_passed_lead_replicates.get(phase, [])) >= biological["min_passed_lead_replicates_per_phase"]
                for phase in bio_required_phases
            ) else "fail",
            "detail": (
                f"Required >= {biological['min_passed_lead_replicates_per_phase']} passed lead replicates per phase; "
                f"observed {bio_passed_lead_replicates}."
            ),
        },
        {
            "id": "failed_bio_lead_rows",
            "status": "pass" if len(failed_bio_lead_rows) <= biological["allowed_failed_lead_rows"] else "fail",
            "detail": f"Failed biological lead rows: {len(failed_bio_lead_rows)}.",
        },
    ]

    technology_present = all(check["status"] == "pass" for check in general_checks)
    non_cell_validated = all(check["status"] == "pass" for check in non_cell_checks)
    biological_validated = all(check["status"] == "pass" for check in bio_checks)
    suitable = technology_present and non_cell_validated and biological_validated

    if suitable:
        readiness = "suitable"
    elif non_cell_validated and not biological_validated and bio_summary.get("status") == "no_data":
        readiness = "non_cell_validated_biological_followup_required"
    elif non_cell_validated and not biological_validated:
        readiness = "non_cell_validated_biological_followup_incomplete"
    elif summary.get("status") == "no_data":
        readiness = "not_suitable_yet_no_measured_data"
    else:
        readiness = "not_suitable_yet"

    missing_evidence: list[str] = []
    if not technology_present:
        missing_evidence.append("Nominated technology record.")
    if not non_cell_validated:
        missing_evidence.append("Measured Phase A/B/C rows that pass non-cell validation gates.")
    if not biological_validated:
        missing_evidence.extend(criteria["suitability_required"]["required_biological_evidence"])

    return {
        "technology_id": criteria["technology_id"],
        "lead_variant_id": criteria["lead_variant_id"],
        "technology_status": technology.get("status") if technology else None,
        "readiness": readiness,
        "non_cell_validated": non_cell_validated,
        "biological_validated": biological_validated,
        "suitable": suitable,
        "checks": general_checks + non_cell_checks + bio_checks,
        "missing_evidence": missing_evidence,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# ZRC-ND Readiness Audit",
        "",
        f"**Technology:** `{result['technology_id']}`",
        f"**Lead variant:** `{result['lead_variant_id']}`",
        f"**Technology status:** `{result['technology_status']}`",
        f"**Readiness:** `{result['readiness']}`",
        f"**Non-cell validated:** `{str(result['non_cell_validated']).lower()}`",
        f"**Biological validated:** `{str(result['biological_validated']).lower()}`",
        f"**Suitable:** `{str(result['suitable']).lower()}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in result["checks"]:
        lines.append(f"| `{check['id']}` | `{check['status']}` | {check['detail']} |")

    lines.extend(["", "## Missing Evidence", ""])
    if result["missing_evidence"]:
        lines.extend(f"- {item}" for item in result["missing_evidence"])
    else:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit ZRC-ND readiness.")
    parser.add_argument("--criteria", type=Path, default=DEFAULT_CRITERIA)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--bio-results", type=Path, default=DEFAULT_BIO_RESULTS)
    parser.add_argument("--technology", type=Path, default=DEFAULT_TECH)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--json-out", type=Path, default=ROOT / "data" / "zrc_nd_readiness_audit.json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    criteria = load_json(args.criteria)
    results = load_results_or_empty(args.results, "aggregate_lead_superiority")
    bio_results = load_results_or_empty(args.bio_results, "aggregate_bio_superiority")
    technology = find_record(load_records(args.technology), criteria["technology_id"])
    audit_result = audit(criteria, results, bio_results, technology)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(audit_result, indent=2, sort_keys=True), encoding="utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_report(audit_result), encoding="utf-8")
    print(f"Readiness: {audit_result['readiness']}")
    print(f"Suitable: {audit_result['suitable']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
