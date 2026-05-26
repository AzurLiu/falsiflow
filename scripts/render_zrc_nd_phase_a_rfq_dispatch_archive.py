#!/usr/bin/env python3
"""Render a single dispatch archive for ZRC-ND Phase A RFQ outreach."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DISPATCH_MANIFEST = ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_manifest.json"
DEFAULT_ARCHIVE = ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_archive" / "zrc_nd_phase_a_rfq_dispatch_archive.zip"
DEFAULT_CSV = ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_archive_manifest.csv"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_archive_manifest.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_rfq_dispatch_archive_manifest.md"
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)

SUPPORT_FILES = [
    ("dispatch_manifest_report", "reports/zrc_nd_phase_a_rfq_dispatch_manifest.md", "00_manifest/zrc_nd_phase_a_rfq_dispatch_manifest.md"),
    ("dispatch_manifest_csv", "data/zrc_nd_phase_a_rfq_dispatch_manifest.csv", "00_manifest/zrc_nd_phase_a_rfq_dispatch_manifest.csv"),
    ("rfq_packet_report", "reports/zrc_nd_phase_a_rfq_packet.md", "00_manifest/zrc_nd_phase_a_rfq_packet.md"),
    ("rfq_outbox_report", "reports/zrc_nd_phase_a_rfq_outbox.md", "00_manifest/zrc_nd_phase_a_rfq_outbox.md"),
    ("vendor_contact_plan", "reports/zrc_nd_phase_a_vendor_contact_plan.md", "00_manifest/zrc_nd_phase_a_vendor_contact_plan.md"),
    ("service_request", "reports/zrc_nd_phase_a_service_request.md", "00_manifest/zrc_nd_phase_a_service_request.md"),
    ("chain_of_custody", "reports/zrc_nd_phase_a_chain_of_custody.md", "00_manifest/zrc_nd_phase_a_chain_of_custody.md"),
    ("delivery_package", "reports/zrc_nd_phase_a_delivery_package_manifest.md", "00_manifest/zrc_nd_phase_a_delivery_package_manifest.md"),
    ("confirmation_entry_sheet", "reports/zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.md", "00_manifest/zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.md"),
    ("confirmation_entry_apply", "reports/zrc_nd_phase_a_rfq_send_confirmation_entry_apply.md", "00_manifest/zrc_nd_phase_a_rfq_send_confirmation_entry_apply.md"),
    ("send_log", "reports/zrc_nd_phase_a_rfq_send_log.md", "00_manifest/zrc_nd_phase_a_rfq_send_log.md"),
    ("reply_log", "reports/zrc_nd_phase_a_rfq_reply_log.md", "00_manifest/zrc_nd_phase_a_rfq_reply_log.md"),
]

CSV_FIELDS = [
    "role",
    "candidate_id",
    "vendor_name",
    "source_path",
    "archive_path",
    "source_exists",
    "source_bytes",
    "source_sha256",
    "expected_sha256",
    "sha256_match",
    "required",
    "errors",
]

NON_EVIDENCE_BOUNDARY = (
    "The ZRC-ND Phase A RFQ dispatch archive is a convenience package for manual outreach only. "
    "It is not a send confirmation, vendor reply, measurement result, or material suitability claim."
)


def clean(value: Any) -> str:
    return str(value or "").strip()


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", clean(value)).strip("_")
    return slug or "vendor"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def workspace_path(raw: str) -> Path:
    path = Path(clean(raw))
    return path if path.is_absolute() else ROOT / path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def file_row(
    role: str,
    source_path: str,
    archive_path: str,
    candidate_id: str = "",
    vendor_name: str = "",
    expected_sha256: str = "",
    required: bool = True,
) -> dict[str, Any]:
    path = workspace_path(source_path)
    exists = path.exists() and path.is_file()
    actual_sha = sha256_file(path) if exists else ""
    errors: list[str] = []
    if required and not exists:
        errors.append("missing_source_file")
    if expected_sha256 and actual_sha and expected_sha256 != actual_sha:
        errors.append("sha256_mismatch")
    return {
        "role": role,
        "candidate_id": candidate_id,
        "vendor_name": vendor_name,
        "source_path": rel(path) if exists else source_path,
        "archive_path": archive_path,
        "source_exists": str(exists).lower(),
        "source_bytes": path.stat().st_size if exists else "",
        "source_sha256": actual_sha,
        "expected_sha256": expected_sha256,
        "sha256_match": str(bool(actual_sha and (not expected_sha256 or expected_sha256 == actual_sha))).lower(),
        "required": str(required).lower(),
        "errors": ";".join(errors),
    }


def add_file(bundle: zipfile.ZipFile, source: Path, arcname: str) -> None:
    info = zipfile.ZipInfo(arcname, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    bundle.writestr(info, source.read_bytes())


def add_text(bundle: zipfile.ZipFile, arcname: str, text: str) -> None:
    info = zipfile.ZipInfo(arcname, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    bundle.writestr(info, text.encode("utf-8"))


def archive_readme(result: dict[str, Any]) -> str:
    summary = result["summary"]
    return "\n".join([
        "# ZRC-ND Phase A RFQ Dispatch Archive",
        "",
        "This archive contains local files for manually sending first-wave ZRC-ND Phase A RFQs.",
        "",
        f"- Status: `{result['status']}`",
        f"- Vendor rows: {summary['vendor_rows']}",
        f"- Included files: {summary['included_files']}",
        f"- Missing files: {summary['missing_files']}",
        f"- Hash mismatches: {summary['hash_mismatch_files']}",
        "",
        "Use the files in `vendors/` to send or paste the RFQ text and attach/upload the matching bundle.",
        "After each real send, save the original sent-email export, web-form confirmation, PDF, or screenshot at the path listed in the dispatch manifest.",
        "",
        "Boundary:",
        NON_EVIDENCE_BOUNDARY,
        "",
    ])


def build_archive(args: argparse.Namespace) -> dict[str, Any]:
    dispatch = load_json(args.dispatch_manifest)
    rows: list[dict[str, Any]] = []

    for role, source, arcname in SUPPORT_FILES:
        rows.append(file_row(role, source, arcname))

    dispatch_rows = dispatch.get("rows", [])
    for dispatch_row in dispatch_rows:
        candidate_id = clean(dispatch_row.get("candidate_id"))
        vendor_name = clean(dispatch_row.get("vendor_name"))
        prefix = f"vendors/{clean(dispatch_row.get('dispatch_order')) or 'x'}_{safe_slug(candidate_id)}"
        rows.append(file_row(
            "vendor_email_text",
            clean(dispatch_row.get("email_file")),
            f"{prefix}/email/{Path(clean(dispatch_row.get('email_file'))).name}",
            candidate_id,
            vendor_name,
            clean(dispatch_row.get("email_sha256")),
        ))
        rows.append(file_row(
            "vendor_bundle",
            clean(dispatch_row.get("bundle_zip")),
            f"{prefix}/bundle/{Path(clean(dispatch_row.get('bundle_zip'))).name}",
            candidate_id,
            vendor_name,
            clean(dispatch_row.get("bundle_sha256_expected")),
        ))
        rows.append(file_row(
            "send_confirmation_template",
            clean(dispatch_row.get("confirmation_template")),
            f"{prefix}/confirmation/{Path(clean(dispatch_row.get('confirmation_template'))).name}",
            candidate_id,
            vendor_name,
        ))

    missing_files = sum(1 for row in rows if row["required"] == "true" and row["source_exists"] != "true")
    hash_mismatches = sum(1 for row in rows if "sha256_mismatch" in clean(row["errors"]))
    status = "zrc_phase_a_rfq_dispatch_archive_ready" if dispatch_rows and not missing_files and not hash_mismatches else "zrc_phase_a_rfq_dispatch_archive_needs_attention"
    if not dispatch_rows:
        status = "zrc_phase_a_rfq_dispatch_archive_no_dispatch_rows"

    args.archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for row in rows:
            if row["source_exists"] == "true":
                add_file(bundle, workspace_path(row["source_path"]), row["archive_path"])
        manifest_lines = [",".join(CSV_FIELDS)]
        for row in rows:
            manifest_lines.append(",".join('"' + clean(row.get(field)).replace('"', '""') + '"' for field in CSV_FIELDS))
        add_text(bundle, "00_manifest/archive_manifest.csv", "\n".join(manifest_lines) + "\n")
        result_stub = {
            "status": status,
            "summary": {
                "vendor_rows": len(dispatch_rows),
                "included_files": sum(1 for row in rows if row["source_exists"] == "true"),
                "missing_files": missing_files,
                "hash_mismatch_files": hash_mismatches,
            },
        }
        add_text(bundle, "README.md", archive_readme(result_stub))

    archive_sha = sha256_file(args.archive)
    result = {
        "status": status,
        "purpose": "Single archive for manually sending first-wave ZRC-ND Phase A RFQ text files and bundles.",
        "summary": {
            "vendor_rows": len(dispatch_rows),
            "manifest_rows": len(rows),
            "included_files": sum(1 for row in rows if row["source_exists"] == "true"),
            "missing_files": missing_files,
            "hash_mismatch_files": hash_mismatches,
            "archive_bytes": args.archive.stat().st_size,
            "archive_sha256": archive_sha,
        },
        "inputs": {
            "dispatch_manifest": rel(args.dispatch_manifest),
        },
        "generated_artifacts": {
            "archive": rel(args.archive),
            "csv": rel(args.csv_out),
            "json": rel(args.json_out),
            "report": rel(args.report),
        },
        "rows": rows,
        "boundary": NON_EVIDENCE_BOUNDARY,
    }
    return result


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# ZRC-ND Phase A RFQ Dispatch Archive Manifest",
        "",
        "This manifest describes the single archive for manual ZRC-ND Phase A RFQ outreach. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Archive:** `{result['generated_artifacts']['archive']}`",
        f"**Archive SHA-256:** `{summary['archive_sha256']}`",
        f"**Vendor rows:** {summary['vendor_rows']}",
        f"**Manifest rows:** {summary['manifest_rows']}",
        f"**Included files:** {summary['included_files']}",
        f"**Missing files:** {summary['missing_files']}",
        f"**Hash mismatches:** {summary['hash_mismatch_files']}",
        "",
        "## Files",
        "",
        "| Role | Vendor | Source | Archive path | Exists | SHA-256 match | Errors |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['role']}` | {row['vendor_name'] or '-'} | `{row['source_path']}` | "
            f"`{row['archive_path']}` | `{row['source_exists']}` | `{row['sha256_match']}` | "
            f"{row['errors'] or '-'} |"
        )

    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render ZRC-ND Phase A RFQ dispatch archive.")
    parser.add_argument("--dispatch-manifest", type=Path, default=DEFAULT_DISPATCH_MANIFEST)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_archive(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"ZRC-ND Phase A RFQ dispatch archive: {result['status']}")
    print(f"Archive SHA-256: {result['summary']['archive_sha256']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
