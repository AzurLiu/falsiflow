#!/usr/bin/env python3
"""Render a pre-send dispatch manifest for NHI-PEDOT H-A RFQ drafts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEND_QUEUE = ROOT / "data" / "nhi_pedot_h_a_rfq_send_action_queue.csv"
DEFAULT_EML_INTEGRITY = ROOT / "data" / "nhi_pedot_h_a_rfq_eml_integrity_audit.csv"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_h_a_rfq_dispatch_manifest.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_rfq_dispatch_manifest.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_rfq_dispatch_manifest.md"

CSV_FIELDS = [
    "dispatch_order",
    "candidate_id",
    "vendor_name",
    "dispatch_status",
    "send_action_status",
    "primary_send_method",
    "recipient_or_form",
    "contact_url",
    "quote_url",
    "eml_file",
    "eml_exists",
    "eml_sha256",
    "eml_integrity_status",
    "eml_integrity_errors",
    "bundle_zip",
    "bundle_exists",
    "bundle_sha256_expected",
    "bundle_sha256_actual",
    "bundle_sha256_match",
    "attached_bundle_verified",
    "matched_attachment_filename",
    "confirmation_source_file_to_save",
    "confirmation_template",
    "confirmation_template_exists",
    "sent_bundle_sha256_to_record",
    "manual_dispatch_step",
    "non_evidence_boundary",
]

NON_EVIDENCE_BOUNDARY = (
    "This dispatch manifest only identifies files for manual RFQ outreach. "
    "It is not a send confirmation, quote reply, measurement result, or material suitability claim."
)


def clean(value: Any) -> str:
    return str(value or "").strip()


def truthy(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y", "pass"}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def workspace_path(raw: str) -> Path:
    path = Path(clean(raw))
    if path.is_absolute():
        return path
    return ROOT / path


def file_exists(raw: str) -> bool:
    return bool(clean(raw)) and workspace_path(raw).is_file()


def sha256(raw: str) -> str:
    if not file_exists(raw):
        return ""
    path = workspace_path(raw)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("candidate_id")): row for row in rows if clean(row.get("candidate_id"))}


def dispatch_step(row: dict[str, Any]) -> str:
    if row["dispatch_status"] != "ready_for_manual_dispatch":
        return "Resolve the dispatch_status blockers before opening or sending this draft."
    return (
        f"Open {row['eml_file']}, confirm To={row['recipient_or_form']} and attached bundle "
        f"{row['bundle_zip']} with SHA-256 {row['sent_bundle_sha256_to_record']}, send manually, then save "
        f"the original sent-email export, form confirmation, PDF, or screenshot at "
        f"{row['confirmation_source_file_to_save']}."
    )


def row_status(row: dict[str, Any]) -> str:
    blockers: list[str] = []
    if clean(row["send_action_status"]) != "ready_to_send":
        blockers.append("send_action_not_ready")
    if not clean(row["recipient_or_form"]):
        blockers.append("missing_recipient_or_form")
    if not truthy(row["eml_exists"]):
        blockers.append("missing_eml")
    if clean(row["eml_integrity_status"]) != "pass":
        blockers.append("eml_integrity_not_pass")
    if not truthy(row["bundle_exists"]):
        blockers.append("missing_bundle")
    if not truthy(row["bundle_sha256_match"]):
        blockers.append("bundle_sha256_mismatch")
    if not truthy(row["attached_bundle_verified"]):
        blockers.append("attached_bundle_not_verified")
    if not clean(row["confirmation_source_file_to_save"]):
        blockers.append("missing_confirmation_save_path")
    if not truthy(row["confirmation_template_exists"]):
        blockers.append("missing_confirmation_template")
    return "ready_for_manual_dispatch" if not blockers else "blocked_" + "+".join(blockers)


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    send_rows = load_csv(args.send_queue)
    audit_rows = by_candidate(load_csv(args.eml_integrity))
    rows: list[dict[str, Any]] = []

    for index, send_row in enumerate(send_rows, start=1):
        candidate_id = clean(send_row.get("candidate_id"))
        audit_row = audit_rows.get(candidate_id, {})
        eml_file = clean(send_row.get("eml_draft_file"))
        bundle_zip = clean(send_row.get("bundle_zip"))
        bundle_expected = clean(send_row.get("bundle_sha256")) or clean(audit_row.get("bundle_sha256_expected"))
        bundle_actual = sha256(bundle_zip)
        row = {
            "dispatch_order": clean(send_row.get("send_order")) or index,
            "candidate_id": candidate_id,
            "vendor_name": clean(send_row.get("vendor_name")),
            "dispatch_status": "",
            "send_action_status": clean(send_row.get("send_action_status")),
            "primary_send_method": clean(send_row.get("primary_send_method")),
            "recipient_or_form": clean(send_row.get("recipient_or_form")),
            "contact_url": clean(send_row.get("contact_url")),
            "quote_url": clean(send_row.get("quote_url")),
            "eml_file": eml_file,
            "eml_exists": str(file_exists(eml_file)).lower(),
            "eml_sha256": sha256(eml_file),
            "eml_integrity_status": clean(audit_row.get("audit_status")) or "not_audited",
            "eml_integrity_errors": clean(audit_row.get("errors")),
            "bundle_zip": bundle_zip,
            "bundle_exists": str(file_exists(bundle_zip)).lower(),
            "bundle_sha256_expected": bundle_expected,
            "bundle_sha256_actual": bundle_actual,
            "bundle_sha256_match": str(bool(bundle_expected and bundle_actual == bundle_expected)).lower(),
            "attached_bundle_verified": str(
                clean(audit_row.get("audit_status")) == "pass"
                and truthy(audit_row.get("matched_bundle_attachment"))
                and truthy(audit_row.get("bundle_file_match"))
            ).lower(),
            "matched_attachment_filename": clean(audit_row.get("matched_attachment_filename")),
            "confirmation_source_file_to_save": clean(send_row.get("confirmation_source_file_to_save")),
            "confirmation_template": clean(send_row.get("confirmation_template")),
            "confirmation_template_exists": str(file_exists(send_row.get("confirmation_template", ""))).lower(),
            "sent_bundle_sha256_to_record": clean(send_row.get("sent_bundle_sha256_to_record")) or bundle_expected,
            "manual_dispatch_step": "",
            "non_evidence_boundary": NON_EVIDENCE_BOUNDARY,
        }
        row["dispatch_status"] = row_status(row)
        row["manual_dispatch_step"] = dispatch_step(row)
        rows.append(row)

    ready_rows = sum(1 for row in rows if row["dispatch_status"] == "ready_for_manual_dispatch")
    blocked_rows = len(rows) - ready_rows
    integrity_pass = sum(1 for row in rows if row["eml_integrity_status"] == "pass")
    bundle_matches = sum(1 for row in rows if truthy(row["bundle_sha256_match"]))
    status = "h_a_rfq_dispatch_manifest_ready" if rows and blocked_rows == 0 else "h_a_rfq_dispatch_manifest_needs_attention"
    if not rows:
        status = "h_a_rfq_dispatch_manifest_no_rows"

    return {
        "status": status,
        "purpose": "Pre-send manifest binding every H-A RFQ draft to the exact audited bundle, recipient, and confirmation-file save path.",
        "summary": {
            "dispatch_rows": len(rows),
            "ready_for_manual_dispatch_rows": ready_rows,
            "blocked_rows": blocked_rows,
            "eml_integrity_pass_rows": integrity_pass,
            "bundle_sha256_match_rows": bundle_matches,
        },
        "inputs": {
            "send_queue": rel(args.send_queue),
            "eml_integrity": rel(args.eml_integrity),
        },
        "generated_artifacts": {
            "csv": rel(args.csv_out),
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "rows": rows,
        "boundary": NON_EVIDENCE_BOUNDARY,
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# NHI-PEDOT H-A RFQ Dispatch Manifest",
        "",
        "This manifest binds the exact pre-send files for manual H-A RFQ outreach. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Dispatch rows:** {summary['dispatch_rows']}",
        f"**Ready for manual dispatch:** {summary['ready_for_manual_dispatch_rows']}",
        f"**Blocked rows:** {summary['blocked_rows']}",
        f"**EML integrity pass:** {summary['eml_integrity_pass_rows']}",
        f"**Bundle SHA-256 matches:** {summary['bundle_sha256_match_rows']}",
        f"**CSV:** `{result['generated_artifacts']['csv']}`",
        "",
        "## Dispatch Rows",
        "",
        "| Order | Vendor | Status | Recipient/Form | EML | Bundle SHA-256 | Confirmation save path |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        sha = row["bundle_sha256_expected"][:16] + "..." if row["bundle_sha256_expected"] else "-"
        lines.append(
            f"| {row['dispatch_order']} | {row['vendor_name']} | `{row['dispatch_status']}` | "
            f"`{row['recipient_or_form']}` | `{row['eml_file']}` | `{sha}` | "
            f"`{row['confirmation_source_file_to_save']}` |"
        )

    lines.extend([
        "",
        "## Per-Row Manual Steps",
        "",
    ])
    for row in result["rows"]:
        lines.extend([
            f"### {row['vendor_name']}",
            "",
            f"- Dispatch status: `{row['dispatch_status']}`",
            f"- EML SHA-256: `{row['eml_sha256'] or '-'}`",
            f"- Bundle SHA-256: `{row['bundle_sha256_actual'] or '-'}`",
            f"- Attached bundle verified: `{row['attached_bundle_verified']}`",
            f"- Step: {row['manual_dispatch_step']}",
            "",
        ])

    lines.extend(["## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A RFQ dispatch manifest.")
    parser.add_argument("--send-queue", type=Path, default=DEFAULT_SEND_QUEUE)
    parser.add_argument("--eml-integrity", type=Path, default=DEFAULT_EML_INTEGRITY)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_manifest(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A RFQ dispatch manifest: {result['status']}")
    print(f"Ready for manual dispatch: {result['summary']['ready_for_manual_dispatch_rows']} / {result['summary']['dispatch_rows']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "h_a_rfq_dispatch_manifest_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
