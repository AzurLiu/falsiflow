#!/usr/bin/env python3
"""Audit first-wave NHI-PEDOT H-A vendor contact channels against source proofs."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTACT_PLAN = ROOT / "data" / "nhi_pedot_h_a_vendor_contact_plan.json"
DEFAULT_PROOFS = ROOT / "data" / "nhi_pedot_h_a_vendor_contact_source_proofs.csv"
DEFAULT_CSV = ROOT / "data" / "nhi_pedot_h_a_vendor_contact_source_audit.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_vendor_contact_source_audit.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_vendor_contact_source_audit.md"

CSV_FIELDS = [
    "candidate_id",
    "vendor_name",
    "audit_status",
    "proof_status",
    "contact_plan_status",
    "source_url",
    "source_domain",
    "verified_at",
    "proof_age_days",
    "primary_email_match",
    "contact_url_match",
    "quote_url_match",
    "sample_submission_url_match",
    "phone_match",
    "source_supports_quote_route",
    "errors",
]

MAX_PROOF_AGE_DAYS = 60
OFFICIAL_DOMAIN_SUFFIXES = {
    "materials_metric": ("materialsmetric.com",),
    "the_osmolality_lab": ("theosmolalitylab.com",),
    "cambridge_polymer_group_hydrogel": ("campoly.com",),
    "sigmaaldrich_media_testing": ("sigmaaldrich.com", "merckmillipore.com"),
}
NON_EVIDENCE_BOUNDARY = (
    "Vendor contact-source audits are sourcing controls only. They are not send confirmations, "
    "quote replies, measurements, or material suitability evidence."
)


def clean(value: Any) -> str:
    return str(value or "").strip()


def truthy(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y", "pass"}


def normalize_email(value: str) -> str:
    return clean(value).lower()


def normalize_url(value: str) -> str:
    raw = clean(value)
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{scheme}://{netloc}{path}"


def normalize_phone(value: str) -> str:
    return "".join(char for char in clean(value) if char.isdigit())


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


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


def domain_matches(candidate_id: str, source_url: str, source_domain: str) -> bool:
    expected = OFFICIAL_DOMAIN_SUFFIXES.get(candidate_id, ())
    parsed_domain = urlparse(source_url).netloc.lower().removeprefix("www.")
    declared_domain = clean(source_domain).lower().removeprefix("www.")
    return any(
        parsed_domain.endswith(suffix) and declared_domain.endswith(suffix)
        for suffix in expected
    )


def proof_age_days(raw: str, today: date) -> int | None:
    if not clean(raw):
        return None
    try:
        return (today - date.fromisoformat(clean(raw))).days
    except ValueError:
        return None


def phone_matches(plan_phone: str, proof_phone: str) -> bool:
    plan_digits = normalize_phone(plan_phone)
    proof_digits = [normalize_phone(item) for item in clean(proof_phone).split(";") if normalize_phone(item)]
    if not plan_digits or not proof_digits:
        return False
    return plan_digits in proof_digits or any(plan_digits.endswith(item) or item.endswith(plan_digits) for item in proof_digits)


def compare_url(plan_value: str, proof_value: str) -> bool:
    if not clean(plan_value) or not clean(proof_value):
        return False
    return normalize_url(plan_value) == normalize_url(proof_value)


def build_row(plan_row: dict[str, Any], proof_row: dict[str, str], today: date) -> dict[str, Any]:
    candidate_id = clean(plan_row.get("candidate_id"))
    errors: list[str] = []
    age = proof_age_days(proof_row.get("verified_at", ""), today)
    proof_status = "proof_ok"
    if not proof_row:
        proof_status = "missing_proof"
        errors.append("missing_proof")
    else:
        if not domain_matches(candidate_id, clean(proof_row.get("source_url")), clean(proof_row.get("source_domain"))):
            errors.append("source_domain_not_official_for_candidate")
        if age is None:
            errors.append("invalid_verified_at")
        elif age < 0:
            errors.append("verified_at_in_future")
        elif age > MAX_PROOF_AGE_DAYS:
            errors.append("proof_stale")
    primary_email_match = normalize_email(plan_row.get("primary_email", "")) == normalize_email(proof_row.get("observed_primary_email", ""))
    contact_url_match = compare_url(plan_row.get("contact_url", ""), proof_row.get("observed_contact_url", ""))
    quote_url_match = compare_url(plan_row.get("quote_url", ""), proof_row.get("observed_quote_url", ""))
    sample_plan = clean(plan_row.get("sample_submission_url"))
    sample_proof = clean(proof_row.get("observed_sample_submission_url"))
    sample_match = (not sample_plan and not sample_proof) or compare_url(sample_plan, sample_proof)
    phone_match = phone_matches(plan_row.get("phone", ""), proof_row.get("observed_phone", ""))
    source_supports_quote = truthy(proof_row.get("source_supports_quote_route"))

    checks = {
        "primary_email_match": primary_email_match,
        "contact_url_match": contact_url_match,
        "quote_url_match": quote_url_match,
        "sample_submission_url_match": sample_match,
        "phone_match": phone_match,
        "source_supports_quote_route": source_supports_quote,
    }
    for name, passed in checks.items():
        if not passed:
            errors.append(name)
    if clean(plan_row.get("contact_plan_status")) != "ready_to_send":
        errors.append("contact_plan_not_ready_to_send")

    if errors and proof_status == "proof_ok":
        proof_status = "proof_needs_review"
    return {
        "candidate_id": candidate_id,
        "vendor_name": clean(plan_row.get("vendor_name")) or clean(proof_row.get("vendor_name")),
        "audit_status": "pass" if not errors else "fail",
        "proof_status": proof_status,
        "contact_plan_status": clean(plan_row.get("contact_plan_status")),
        "source_url": clean(proof_row.get("source_url")),
        "source_domain": clean(proof_row.get("source_domain")),
        "verified_at": clean(proof_row.get("verified_at")),
        "proof_age_days": "" if age is None else age,
        "primary_email_match": str(primary_email_match).lower(),
        "contact_url_match": str(contact_url_match).lower(),
        "quote_url_match": str(quote_url_match).lower(),
        "sample_submission_url_match": str(sample_match).lower(),
        "phone_match": str(phone_match).lower(),
        "source_supports_quote_route": str(source_supports_quote).lower(),
        "errors": ";".join(errors),
    }


def build_audit(args: argparse.Namespace) -> dict[str, Any]:
    contact_plan = load_json(args.contact_plan)
    proof_rows = by_candidate(load_csv(args.proofs))
    today = date.today()
    first_wave_rows = [
        row for row in contact_plan.get("rows", [])
        if clean(row.get("wave")) == "first_wave"
    ]
    rows = [build_row(row, proof_rows.get(clean(row.get("candidate_id")), {}), today) for row in first_wave_rows]
    pass_rows = sum(1 for row in rows if row["audit_status"] == "pass")
    fail_rows = len(rows) - pass_rows
    stale_rows = sum(1 for row in rows if "proof_stale" in clean(row["errors"]))
    missing_rows = sum(1 for row in rows if row["proof_status"] == "missing_proof")
    status = "h_a_vendor_contact_source_audit_ready" if rows and fail_rows == 0 else "h_a_vendor_contact_source_audit_needs_attention"
    if not rows:
        status = "h_a_vendor_contact_source_audit_no_first_wave_rows"
    return {
        "status": status,
        "purpose": "Audit first-wave NHI-PEDOT H-A RFQ contact channels against official-source proof rows before manual dispatch.",
        "summary": {
            "audit_rows": len(rows),
            "pass_rows": pass_rows,
            "fail_rows": fail_rows,
            "missing_proof_rows": missing_rows,
            "stale_proof_rows": stale_rows,
            "max_proof_age_days": MAX_PROOF_AGE_DAYS,
        },
        "inputs": {
            "contact_plan": rel(args.contact_plan),
            "proofs": rel(args.proofs),
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
        "# NHI-PEDOT H-A Vendor Contact Source Audit",
        "",
        "This audit checks first-wave RFQ contact channels against source-proof rows. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Audit rows:** {summary['audit_rows']}",
        f"**Pass:** {summary['pass_rows']}",
        f"**Fail:** {summary['fail_rows']}",
        f"**Missing proof rows:** {summary['missing_proof_rows']}",
        f"**Stale proof rows:** {summary['stale_proof_rows']}",
        "",
        "## Rows",
        "",
        "| Vendor | Status | Proof | Source | Email | Contact | Quote | Sample | Phone | Errors |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['vendor_name']} | `{row['audit_status']}` | `{row['proof_status']}` | "
            f"{row['source_url'] or '-'} | `{row['primary_email_match']}` | `{row['contact_url_match']}` | "
            f"`{row['quote_url_match']}` | `{row['sample_submission_url_match']}` | `{row['phone_match']}` | "
            f"`{row['errors'] or '-'}` |"
        )
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit NHI-PEDOT H-A vendor contact source proofs.")
    parser.add_argument("--contact-plan", type=Path, default=DEFAULT_CONTACT_PLAN)
    parser.add_argument("--proofs", type=Path, default=DEFAULT_PROOFS)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_audit(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"H-A vendor contact source audit: {result['status']}")
    print(f"Pass: {result['summary']['pass_rows']} / {result['summary']['audit_rows']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "h_a_vendor_contact_source_audit_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
