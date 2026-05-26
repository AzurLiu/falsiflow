#!/usr/bin/env python3
"""Audit whether any LIMINA material technology is ready for a suitability claim."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORTFOLIO = ROOT / "data" / "limina_technology_portfolio.json"
DEFAULT_ZRC_READINESS = ROOT / "data" / "zrc_nd_readiness_audit.json"
DEFAULT_ZRC_RUNS = ROOT / "data" / "zrc_nd_validation_runs_active.csv"
DEFAULT_ZRC_BIO_RUNS = ROOT / "data" / "zrc_nd_bio_runs_template.csv"
DEFAULT_NHI_RESULTS = ROOT / "data" / "nhi_pedot_results.json"
DEFAULT_NHI_RUNS = ROOT / "data" / "nhi_pedot_runs_template.csv"
DEFAULT_NHI_H_A = ROOT / "data" / "nhi_pedot_h_a_sentinel_interpretation.json"
DEFAULT_NHI_H_A_RUNS = ROOT / "data" / "nhi_pedot_h_a_runs_active.csv"
DEFAULT_NHI_FORWARD = ROOT / "data" / "nhi_pedot_forward_gate_package.json"
DEFAULT_NHI_LONG_RESULTS = ROOT / "data" / "nhi_pedot_long_results.json"
DEFAULT_NHI_LONG_RUNS = ROOT / "data" / "nhi_pedot_long_runs_template.csv"
DEFAULT_SOURCE_MANIFEST = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_JSON = ROOT / "data" / "limina_suitability_claim_audit.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_suitability_claim_audit.md"

SYNTHETIC_MARKERS = (
    "synthetic_fixture",
    "not_evidence",
    "fixture",
    "material_evidence=false",
    "fixture_not_material",
    "fixture_not_evidence",
)
PLACEHOLDER_MARKERS = (
    "pending_real_measurement",
    "record_exact",
    "record_actual",
    "record_lot",
    "to_be_recorded",
    "tbd",
    "unknown",
    "not_measured",
)
FIXTURE_PATH_MARKERS = {"fixtures"}
REQUIRED_PROVENANCE_FIELDS = ("date", "operator_or_agent")
REQUIRED_SOURCE_FILE_FIELD = "source_file"

ZRC_TECHNOLOGY_ID = "limina_zrc_nd_v0_1"
NHI_TECHNOLOGY_ID = "limina_nhi_pedot_laminin_v0_1"
NHI_H_A_PASS_STATUSES = {
    "h_a_lead_passes_continue_h_b",
    "h_a_lead_passes_continue_challenge_boundary",
    "h_a_lead_passes_hydrogel_control_issue",
}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json_or_empty(path: Path) -> dict[str, Any]:
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


def allowed_source_roots(manifest: dict[str, Any]) -> list[Path]:
    roots: list[Path] = []
    for row in manifest.get("allowed_roots", []):
        raw = str(row.get("path", "")).strip()
        if not raw:
            continue
        path = Path(raw)
        roots.append(path if path.is_absolute() else ROOT / path)
    return roots


def split_source_files(raw: str) -> list[str]:
    refs = [raw.strip().strip("\"'")]
    for char in [";", "|", "\n"]:
        expanded: list[str] = []
        for ref in refs:
            expanded.extend(part.strip().strip("\"'") for part in ref.split(char))
        refs = expanded
    return [ref for ref in refs if ref]


def rejected_source_markers(manifest: dict[str, Any]) -> set[str]:
    markers = set(SYNTHETIC_MARKERS) | set(PLACEHOLDER_MARKERS)
    markers.update(str(item).strip().lower() for item in manifest.get("rejected_source_markers", []) if str(item).strip())
    return markers


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def rows_with_run_id(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("run_id", "").strip()]


def path_has_fixture_marker(path: Path) -> bool:
    lowered_name = path.name.lower()
    parts = {part.lower() for part in path.parts}
    return "fixture" in lowered_name or bool(parts & FIXTURE_PATH_MARKERS)


def row_marker_hits(row: dict[str, str]) -> list[str]:
    hits: list[str] = []
    for field, value in row.items():
        lowered = str(value).lower()
        for marker in SYNTHETIC_MARKERS:
            if marker in lowered:
                hits.append(f"{field}={marker}")
    return sorted(set(hits))


def row_placeholder_hits(row: dict[str, str]) -> list[str]:
    hits: list[str] = []
    for field in REQUIRED_PROVENANCE_FIELDS:
        if field in row and not row.get(field, "").strip():
            hits.append(f"{field}=missing")
    if not row.get(REQUIRED_SOURCE_FILE_FIELD, "").strip():
        hits.append(f"{REQUIRED_SOURCE_FILE_FIELD}=missing")
    for field, value in row.items():
        lowered = str(value).lower()
        for marker in PLACEHOLDER_MARKERS:
            if marker in lowered:
                hits.append(f"{field}={marker}")
    return sorted(set(hits))


def source_file_issues(row: dict[str, str], manifest: dict[str, Any]) -> list[str]:
    roots = allowed_source_roots(manifest)
    markers = rejected_source_markers(manifest)
    issues: list[str] = []
    for ref in split_source_files(row.get(REQUIRED_SOURCE_FILE_FIELD, "")):
        lowered = ref.lower()
        if any(marker in lowered for marker in markers):
            issues.append(f"{ref}: rejected source marker")
            continue
        resolved = resolve_path(ref)
        if not resolved.exists():
            issues.append(f"{ref}: source file does not exist")
            continue
        if not resolved.is_file():
            issues.append(f"{ref}: source path is not a file")
            continue
        if not roots:
            issues.append(f"{ref}: source manifest has no allowed roots")
            continue
        if not any(path_is_within(resolved, root) for root in roots):
            issues.append(f"{ref}: source file is outside allowed roots")
    return issues


def provenance(path: Path, source_manifest: Path = DEFAULT_SOURCE_MANIFEST) -> dict[str, Any]:
    rows = rows_with_run_id(load_csv_rows(path))
    path_fixture = path_has_fixture_marker(path)
    manifest = load_json_or_empty(source_manifest)
    synthetic_rows = []
    placeholder_rows = []
    source_issue_rows = []
    invalid_row_numbers: set[int] = set()
    for index, row in enumerate(rows, start=1):
        hits = row_marker_hits(row)
        if path_fixture or hits:
            invalid_row_numbers.add(index)
            synthetic_rows.append({
                "row_number": index,
                "run_id": row.get("run_id", f"row_{index}"),
                "markers": hits or ["fixture_path"],
            })
        placeholder_hits = row_placeholder_hits(row)
        if placeholder_hits:
            invalid_row_numbers.add(index)
            placeholder_rows.append({
                "row_number": index,
                "run_id": row.get("run_id", f"row_{index}"),
                "markers": placeholder_hits,
            })
        source_issues = source_file_issues(row, manifest)
        if source_issues:
            invalid_row_numbers.add(index)
            source_issue_rows.append({
                "row_number": index,
                "run_id": row.get("run_id", f"row_{index}"),
                "issues": source_issues,
            })
    return {
        "path": rel(path),
        "exists": path.exists(),
        "row_count": len(rows),
        "measured_row_count": len(rows) - len(invalid_row_numbers),
        "path_fixture_marker": path_fixture,
        "synthetic_row_count": len(synthetic_rows),
        "synthetic_examples": synthetic_rows[:8],
        "placeholder_row_count": len(placeholder_rows),
        "placeholder_examples": placeholder_rows[:8],
        "source_file_issue_count": len(source_issue_rows),
        "source_file_issue_examples": source_issue_rows[:8],
        "claimable_measurement_source": (
            bool(rows) and not synthetic_rows and not placeholder_rows and not source_issue_rows
        ),
    }


def result_status(result: dict[str, Any]) -> str:
    return str(result.get("summary", {}).get("status", "missing"))


def result_rows(result: dict[str, Any]) -> int:
    raw = result.get("summary", {}).get("rows", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def add_provenance_blockers(blockers: list[str], label: str, summary: dict[str, Any]) -> None:
    if not summary["exists"]:
        blockers.append(f"{label} CSV is missing.")
    if summary["measured_row_count"] == 0:
        blockers.append(f"{label} has no measured run rows.")
    if summary["synthetic_row_count"] > 0:
        blockers.append(f"{label} contains synthetic or fixture-marked rows.")
    if summary["placeholder_row_count"] > 0:
        blockers.append(f"{label} contains placeholder or pending-measurement rows.")
    if summary.get("source_file_issue_count", 0) > 0:
        blockers.append(f"{label} contains missing, rejected, or out-of-policy source_file references.")


def add_row_count_blocker(
    blockers: list[str],
    label: str,
    result: dict[str, Any],
    source: dict[str, Any],
) -> None:
    rows_in_result = result_rows(result)
    if rows_in_result > 0 and source["measured_row_count"] != rows_in_result:
        blockers.append(
            f"{label} result row count ({rows_in_result}) does not match CSV rows "
            f"({source['measured_row_count']})."
        )


def audit_zrc(readiness: dict[str, Any], non_cell_source: dict[str, Any], bio_source: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    suitable = readiness.get("suitable") is True
    if not suitable:
        blockers.append(
            "ZRC-ND readiness audit is not suitable; measured non-cell and biological gates are incomplete."
        )
    add_provenance_blockers(blockers, "ZRC-ND non-cell source", non_cell_source)
    add_provenance_blockers(blockers, "ZRC-ND biological source", bio_source)
    claim_ready = suitable and non_cell_source["claimable_measurement_source"] and bio_source["claimable_measurement_source"]
    return {
        "technology_id": ZRC_TECHNOLOGY_ID,
        "claim_candidate_id": ZRC_TECHNOLOGY_ID,
        "claim_ready": claim_ready,
        "decision": "claim_ready" if claim_ready else "not_claim_ready",
        "evidence_status": {
            "readiness": readiness.get("readiness", "missing"),
            "suitable": suitable,
        },
        "provenance": {
            "non_cell": non_cell_source,
            "biological": bio_source,
        },
        "blockers": blockers,
    }


def audit_nhi(
    coupon_results: dict[str, Any],
    coupon_source: dict[str, Any],
    h_a_result: dict[str, Any],
    h_a_source: dict[str, Any],
    forward_package: dict[str, Any],
    long_results: dict[str, Any],
    long_source: dict[str, Any],
    active_candidate_id: str | None,
) -> dict[str, Any]:
    blockers: list[str] = []
    coupon_status = result_status(coupon_results)
    h_a_status = str(h_a_result.get("status", "missing"))
    forward_status = str(forward_package.get("status", "missing"))
    long_status = result_status(long_results)
    if h_a_status not in NHI_H_A_PASS_STATUSES:
        blockers.append(
            f"NHI-PEDOT H-A sentinel is `{h_a_status}`, not a QC-clean pass/continue status."
        )
    if coupon_status != "nhi_pedot_passes_gates":
        blockers.append(f"NHI-PEDOT coupon gates are `{coupon_status}`, not `nhi_pedot_passes_gates`.")
    if forward_status == "preregistered_waiting_for_h_a":
        blockers.append("NHI-PEDOT H-B/H-C forward gate package is preregistered and waiting for H-A, not measured evidence.")
    elif forward_status == "missing":
        blockers.append("NHI-PEDOT H-B/H-C forward gate package is missing.")
    if long_status != "nhi_pedot_long_passes_gates":
        blockers.append(
            f"NHI-PEDOT long-duration gates are `{long_status}`, not `nhi_pedot_long_passes_gates`."
        )
    add_provenance_blockers(blockers, "NHI-PEDOT H-A sentinel source", h_a_source)
    add_provenance_blockers(blockers, "NHI-PEDOT coupon source", coupon_source)
    add_provenance_blockers(blockers, "NHI-PEDOT long-duration source", long_source)
    add_row_count_blocker(blockers, "NHI-PEDOT coupon", coupon_results, coupon_source)
    add_row_count_blocker(blockers, "NHI-PEDOT long-duration", long_results, long_source)

    claim_ready = (
        h_a_status in NHI_H_A_PASS_STATUSES
        and coupon_status == "nhi_pedot_passes_gates"
        and long_status == "nhi_pedot_long_passes_gates"
        and h_a_source["claimable_measurement_source"]
        and coupon_source["claimable_measurement_source"]
        and long_source["claimable_measurement_source"]
        and result_rows(coupon_results) == coupon_source["measured_row_count"]
        and result_rows(long_results) == long_source["measured_row_count"]
    )
    return {
        "technology_id": NHI_TECHNOLOGY_ID,
        "claim_candidate_id": active_candidate_id or NHI_TECHNOLOGY_ID,
        "claim_ready": claim_ready,
        "decision": "claim_ready" if claim_ready else "not_claim_ready",
        "evidence_status": {
            "h_a_status": h_a_status,
            "h_a_measured_rows": h_a_source["measured_row_count"],
            "forward_status": forward_status,
            "forward_rows": forward_package.get("row_count", 0),
            "coupon_status": coupon_status,
            "coupon_result_rows": result_rows(coupon_results),
            "long_status": long_status,
            "long_result_rows": result_rows(long_results),
        },
        "provenance": {
            "h_a_sentinel": h_a_source,
            "coupon": coupon_source,
            "long_duration": long_source,
        },
        "blockers": blockers,
    }


def build_audit(args: argparse.Namespace) -> dict[str, Any]:
    portfolio = load_json_or_empty(args.portfolio)
    active_candidate_id = portfolio.get("active_discovery_candidate")
    if portfolio.get("primary_next_branch") != NHI_TECHNOLOGY_ID:
        active_candidate_id = None
    zrc = audit_zrc(
        load_json_or_empty(args.zrc_readiness),
        provenance(args.zrc_runs, args.source_manifest),
        provenance(args.zrc_bio_runs, args.source_manifest),
    )
    nhi = audit_nhi(
        load_json_or_empty(args.nhi_results),
        provenance(args.nhi_runs, args.source_manifest),
        load_json_or_empty(args.nhi_h_a),
        provenance(args.nhi_h_a_runs, args.source_manifest),
        load_json_or_empty(args.nhi_forward),
        load_json_or_empty(args.nhi_long_results),
        provenance(args.nhi_long_runs, args.source_manifest),
        active_candidate_id,
    )
    candidates = [item for item in [zrc, nhi] if item["claim_ready"]]
    claim_candidate = candidates[0].get("claim_candidate_id") if candidates else None
    claim_parent = candidates[0]["technology_id"] if candidates else None
    return {
        "status": "suitable_material_claim_ready" if claim_candidate else "no_suitable_material_claim_ready",
        "claim_ready": bool(claim_candidate),
        "claim_candidate": claim_candidate,
        "claim_parent_technology": claim_parent,
        "portfolio_status": portfolio.get("status", "missing"),
        "portfolio_primary_next_branch": portfolio.get("primary_next_branch"),
        "active_discovery_candidate": portfolio.get("active_discovery_candidate"),
        "claim_boundary": (
            "Portfolio status selects workflow priority. Suitability claims require passing gates plus "
            "claimable non-synthetic measurement provenance."
        ),
        "candidate_audits": [zrc, nhi],
    }


def md_bool(value: bool) -> str:
    return str(value).lower()


def md_cell(value: Any) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def provenance_label(item: dict[str, Any]) -> str:
    return (
        f"{item['measured_row_count']}/{item['row_count']} measured rows; "
        f"synthetic={item['synthetic_row_count']}; "
        f"placeholder={item['placeholder_row_count']}; "
        f"source_file_issues={item.get('source_file_issue_count', 0)}; "
        f"claimable={md_bool(item['claimable_measurement_source'])}"
    )


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIMINA Suitability Claim Audit",
        "",
        f"**Claim ready:** `{md_bool(result['claim_ready'])}`",
        f"**Claim candidate:** `{result['claim_candidate'] or '-'}`",
        f"**Claim parent technology:** `{result.get('claim_parent_technology') or '-'}`",
        f"**Active discovery candidate:** `{result.get('active_discovery_candidate') or '-'}`",
        f"**Portfolio status:** `{result['portfolio_status']}`",
        f"**Portfolio primary next branch:** `{result['portfolio_primary_next_branch'] or '-'}`",
        "",
        "## Candidate Decisions",
        "",
        "| Technology | Claim candidate | Decision | Evidence status | Provenance | Blockers |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in result["candidate_audits"]:
        evidence = ", ".join(f"{key}={value}" for key, value in item["evidence_status"].items())
        provenance_bits = [
            f"{label}={provenance_label(summary)}"
            for label, summary in item["provenance"].items()
        ]
        blockers = "; ".join(item["blockers"]) if item["blockers"] else "None."
        lines.append(
            f"| `{item['technology_id']}` | `{item.get('claim_candidate_id', item['technology_id'])}` | "
            f"`{item['decision']}` | {md_cell(evidence)} | "
            f"{md_cell('; '.join(provenance_bits))} | {md_cell(blockers)} |"
        )

    lines.extend([
        "",
        "## Provenance Inputs",
        "",
        "| Technology | Source | Path | Rows | Measured rows | Synthetic rows | Placeholder rows | Source-file issues | Claimable source | Examples |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ])
    for item in result["candidate_audits"]:
        for label, summary in item["provenance"].items():
            examples = ", ".join(
                example["run_id"]
                for example in summary["synthetic_examples"] + summary["placeholder_examples"]
            ) or "-"
            lines.append(
                f"| `{item['technology_id']}` | {label} | `{summary['path']}` | "
                f"{summary['row_count']} | {summary['measured_row_count']} | "
                f"{summary['synthetic_row_count']} | {summary['placeholder_row_count']} | "
                f"{summary.get('source_file_issue_count', 0)} | "
                f"`{md_bool(summary['claimable_measurement_source'])}` | {md_cell(examples)} |"
            )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- This audit is the gate for saying LIMINA has found a suitable material technology.",
        "- Synthetic fixtures can prove evaluator logic, but they are rejected as material evidence.",
        "- Template rows with missing dates, `pending_real_measurement`, `record_exact`, `record_actual`, or `record_lot` placeholders are rejected until replaced by measured provenance.",
        "- A future claim requires passing gate status and CSV provenance with non-synthetic measured rows that cite existing source_file records under the source-file manifest.",
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit LIMINA suitability claim readiness.")
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument("--zrc-readiness", type=Path, default=DEFAULT_ZRC_READINESS)
    parser.add_argument("--zrc-runs", type=Path, default=DEFAULT_ZRC_RUNS)
    parser.add_argument("--zrc-bio-runs", type=Path, default=DEFAULT_ZRC_BIO_RUNS)
    parser.add_argument("--nhi-results", type=Path, default=DEFAULT_NHI_RESULTS)
    parser.add_argument("--nhi-runs", type=Path, default=DEFAULT_NHI_RUNS)
    parser.add_argument("--nhi-h-a", type=Path, default=DEFAULT_NHI_H_A)
    parser.add_argument("--nhi-h-a-runs", type=Path, default=DEFAULT_NHI_H_A_RUNS)
    parser.add_argument("--nhi-forward", type=Path, default=DEFAULT_NHI_FORWARD)
    parser.add_argument("--nhi-long-results", type=Path, default=DEFAULT_NHI_LONG_RESULTS)
    parser.add_argument("--nhi-long-runs", type=Path, default=DEFAULT_NHI_LONG_RUNS)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_audit(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Claim ready: {result['claim_ready']}")
    print(f"Status: {result['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
