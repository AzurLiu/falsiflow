#!/usr/bin/env python3
"""Render and validate LIMINA human execution-authorization logs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Profile:
    key: str
    label: str
    quote_selection: Path
    csv_out: Path
    json_out: Path
    report: Path
    status_prefix: str
    selected_decision: str


PROFILES = {
    "h_a": Profile(
        key="h_a",
        label="NHI-PEDOT H-A",
        quote_selection=ROOT / "data" / "nhi_pedot_h_a_quote_selection.json",
        csv_out=ROOT / "data" / "nhi_pedot_h_a_execution_authorization_log.csv",
        json_out=ROOT / "data" / "nhi_pedot_h_a_execution_authorization_log.json",
        report=ROOT / "reports" / "nhi_pedot_h_a_execution_authorization_log.md",
        status_prefix="nhi_pedot_h_a_execution_authorization",
        selected_decision="selected_for_h_a",
    ),
    "zrc_phase_a": Profile(
        key="zrc_phase_a",
        label="ZRC-ND Phase A",
        quote_selection=ROOT / "data" / "zrc_nd_phase_a_quote_selection.json",
        csv_out=ROOT / "data" / "zrc_nd_phase_a_execution_authorization_log.csv",
        json_out=ROOT / "data" / "zrc_nd_phase_a_execution_authorization_log.json",
        report=ROOT / "reports" / "zrc_nd_phase_a_execution_authorization_log.md",
        status_prefix="zrc_nd_phase_a_execution_authorization",
        selected_decision="selected_for_phase_a",
    ),
}


FIELDS = [
    "candidate_id",
    "vendor_name",
    "authorization_status",
    "authorized_at",
    "authorized_by",
    "authorization_basis",
    "provider_acceptance_reference",
    "sds_review_reference",
    "custody_release_reference",
    "scope_review_reference",
    "sample_count_authorized",
    "shipment_or_execution_window",
    "authorization_source_file",
    "authorization_source_sha256",
    "computed_authorization_source_sha256",
    "notes",
]

USER_FIELDS = {
    "authorization_status",
    "authorized_at",
    "authorized_by",
    "authorization_basis",
    "provider_acceptance_reference",
    "sds_review_reference",
    "custody_release_reference",
    "scope_review_reference",
    "sample_count_authorized",
    "shipment_or_execution_window",
    "authorization_source_file",
    "authorization_source_sha256",
    "notes",
}

AUTHORIZED = {"authorized", "approved", "release_authorized"}
NON_AUTHORIZED = {"", "pending_authorization", "not_authorized", "hold", "revoked"}
KNOWN_STATUS = AUTHORIZED | NON_AUTHORIZED


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def workspace_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def normalize(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def by_candidate(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("candidate_id", ""): row for row in rows if row.get("candidate_id")}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_rows(quote_selection: dict[str, Any], selected_decision: str) -> list[dict[str, Any]]:
    return [
        row for row in quote_selection.get("scored_rows", [])
        if row.get("selection_decision") == selected_decision
    ]


def build_rows(profile: Profile, quote_selection: dict[str, Any], prior: dict[str, dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    selected = selected_rows(quote_selection, profile.selected_decision)
    rows: list[dict[str, str]] = []
    for selected_row in selected:
        candidate_id = str(selected_row.get("candidate_id", ""))
        if not candidate_id:
            continue
        row = {field: "" for field in FIELDS}
        row.update({
            "candidate_id": candidate_id,
            "vendor_name": str(selected_row.get("vendor_name", "")),
            "authorization_status": "pending_authorization",
            "authorization_source_file": rel(ROOT / "data" / "execution_authorization_files" / profile.key / f"{candidate_id}_authorization.txt"),
        })
        prior_row = prior.get(candidate_id, {})
        for field in USER_FIELDS:
            if prior_row.get(field, "").strip():
                row[field] = prior_row[field]
        source = row.get("authorization_source_file", "").strip()
        if source:
            source_path = workspace_path(source)
            if source_path.exists() and source_path.is_file():
                row["computed_authorization_source_sha256"] = sha256_file(source_path)
        rows.append(row)

    known_ids = {row.get("candidate_id", "") for row in rows}
    unknown_prior_ids = sorted(candidate_id for candidate_id in prior if candidate_id not in known_ids)
    return rows, unknown_prior_ids


def validate_authorized_row(row: dict[str, str], selected_source_backed_ids: set[str]) -> list[str]:
    errors = []
    candidate_id = row.get("candidate_id", "")
    if candidate_id not in selected_source_backed_ids:
        errors.append("selected_source_backed_provider=missing")
    for field in [
        "authorized_at",
        "authorized_by",
        "authorization_basis",
        "provider_acceptance_reference",
        "custody_release_reference",
        "scope_review_reference",
        "sample_count_authorized",
        "shipment_or_execution_window",
        "authorization_source_file",
    ]:
        if not row.get(field, "").strip():
            errors.append(f"{field}=missing")
    source = row.get("authorization_source_file", "").strip()
    if source:
        source_path = workspace_path(source)
        if not source_path.exists() or not source_path.is_file():
            errors.append("authorization_source_file=missing")
        else:
            computed = sha256_file(source_path)
            supplied = row.get("authorization_source_sha256", "").strip()
            if supplied and supplied != computed:
                errors.append("authorization_source_sha256=mismatch")
    return errors


def build_result(profile: Profile) -> dict[str, Any]:
    quote_selection = load_json(profile.quote_selection)
    _, prior_rows_raw = load_csv(profile.csv_out)
    prior = by_candidate(prior_rows_raw)
    rows, unknown_prior_ids = build_rows(profile, quote_selection, prior)
    write_csv(profile.csv_out, rows)

    selected = selected_rows(quote_selection, profile.selected_decision)
    selected_ids = {
        str(row.get("candidate_id", ""))
        for row in selected
        if row.get("candidate_id")
    }
    selected_source_backed_ids = {
        str(row.get("candidate_id", ""))
        for row in selected
        if row.get("candidate_id") and row.get("source_backed_reply") is True
    }

    errors = []
    valid_authorizations = []
    pending_count = 0
    authorized_count = 0
    for row in rows:
        status = normalize(row.get("authorization_status", ""))
        if status not in KNOWN_STATUS:
            errors.append({
                "candidate_id": row.get("candidate_id", ""),
                "vendor_name": row.get("vendor_name", ""),
                "errors": [f"authorization_status=unrecognized:{row.get('authorization_status', '')}"],
            })
            continue
        if status in AUTHORIZED:
            authorized_count += 1
            row_errors = validate_authorized_row(row, selected_source_backed_ids)
            if row_errors:
                errors.append({
                    "candidate_id": row.get("candidate_id", ""),
                    "vendor_name": row.get("vendor_name", ""),
                    "errors": row_errors,
                })
            else:
                valid_authorizations.append(row)
        else:
            pending_count += 1

    if errors:
        status = f"{profile.status_prefix}_has_errors"
    elif valid_authorizations:
        status = f"{profile.status_prefix}_authorized"
    elif rows:
        status = f"{profile.status_prefix}_waiting_for_human_authorization"
    else:
        status = f"{profile.status_prefix}_waiting_for_selected_provider"

    return {
        "status": status,
        "profile": profile.key,
        "label": profile.label,
        "purpose": "Validate human execution authorization without treating authorization as measured material evidence.",
        "authorization_log_csv": rel(profile.csv_out),
        "quote_selection": rel(profile.quote_selection),
        "row_count": len(rows),
        "selected_provider_count": len(selected_ids),
        "source_backed_selected_provider_count": len(selected_source_backed_ids),
        "pending_rows": pending_count,
        "authorized_rows": authorized_count,
        "valid_authorization_rows": len(valid_authorizations),
        "valid_authorized_candidate_ids": [row["candidate_id"] for row in valid_authorizations],
        "valid_authorization_summaries": [
            {
                "candidate_id": row["candidate_id"],
                "vendor_name": row["vendor_name"],
                "authorized_at": row.get("authorized_at", ""),
                "authorized_by": row.get("authorized_by", ""),
                "authorization_source_file": row.get("authorization_source_file", ""),
                "computed_authorization_source_sha256": row.get("computed_authorization_source_sha256", ""),
            }
            for row in valid_authorizations
        ],
        "error_count": len(errors),
        "errors": errors,
        "unknown_prior_candidate_ids": unknown_prior_ids,
        "field_contract": {
            "authorization_status_values": sorted(KNOWN_STATUS - {""}),
            "required_when_authorized": [
                "authorized_at",
                "authorized_by",
                "authorization_basis",
                "provider_acceptance_reference",
                "custody_release_reference",
                "scope_review_reference",
                "sample_count_authorized",
                "shipment_or_execution_window",
                "authorization_source_file",
            ],
            "hash_rule": "If authorization_source_sha256 is supplied, it must match the current SHA-256 of authorization_source_file.",
        },
        "non_evidence_boundary": (
            "Execution authorization is a logistics control. It does not count as material evidence "
            "and cannot advance suitability gates without returned real measurements and source files."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['label']} Execution Authorization Log",
        "",
        "This report validates human authorization for outsourced execution or sample movement. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Authorization log CSV:** `{result['authorization_log_csv']}`",
        f"**Rows:** {result['row_count']}",
        f"**Selected providers:** {result['selected_provider_count']}",
        f"**Source-backed selected providers:** {result['source_backed_selected_provider_count']}",
        f"**Authorized rows:** {result['authorized_rows']}",
        f"**Valid authorizations:** {result['valid_authorization_rows']}",
        f"**Errors:** {result['error_count']}",
        "",
        "## Required When Authorized",
        "",
    ]
    lines.extend(f"- `{field}`" for field in result["field_contract"]["required_when_authorized"])
    if result["valid_authorization_summaries"]:
        lines.extend([
            "",
            "## Valid Authorizations",
            "",
            "| Candidate | Vendor | Authorized at | Authorized by | Source file |",
            "| --- | --- | --- | --- | --- |",
        ])
        for row in result["valid_authorization_summaries"]:
            lines.append(
                f"| `{row['candidate_id']}` | {row['vendor_name']} | "
                f"{row['authorized_at']} | {row['authorized_by']} | `{row['authorization_source_file']}` |"
            )
    if result["errors"]:
        lines.extend(["", "## Errors", ""])
        for row in result["errors"]:
            lines.append(
                f"- `{row.get('candidate_id', '-')}` {row.get('vendor_name', '-')}: "
                + ", ".join(f"`{item}`" for item in row.get("errors", []))
            )
    lines.extend([
        "",
        "## Boundary",
        "",
        result["non_evidence_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render/apply LIMINA execution authorization logs.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="h_a")
    parser.add_argument("--csv-out", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--report", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    base = PROFILES[args.profile]
    profile = Profile(
        key=base.key,
        label=base.label,
        quote_selection=base.quote_selection,
        csv_out=args.csv_out or base.csv_out,
        json_out=args.json_out or base.json_out,
        report=args.report or base.report,
        status_prefix=base.status_prefix,
        selected_decision=base.selected_decision,
    )
    result = build_result(profile)
    profile.json_out.parent.mkdir(parents=True, exist_ok=True)
    profile.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    profile.report.parent.mkdir(parents=True, exist_ok=True)
    profile.report.write_text(render_report(result), encoding="utf-8")
    print(f"{profile.label} execution authorization log: {result['status']}")
    print(f"Rows: {result['row_count']}")
    print(f"Valid authorizations: {result['valid_authorization_rows']}")
    print(f"Errors: {result['error_count']}")
    print(f"Wrote {profile.csv_out}")
    print(f"Wrote {profile.json_out}")
    print(f"Wrote {profile.report}")
    return 0 if result["error_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
