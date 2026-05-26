#!/usr/bin/env python3
"""Render sample labels and chain-of-custody blanks for the NHI-PEDOT H-A package."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLE_MANIFEST = ROOT / "data" / "nhi_pedot_h_a_sentinel_sample_manifest.csv"
DEFAULT_SERVICE = ROOT / "data" / "nhi_pedot_h_a_service_request.json"
DEFAULT_LABELS = ROOT / "data" / "nhi_pedot_h_a_sample_labels.csv"
DEFAULT_CUSTODY = ROOT / "data" / "nhi_pedot_h_a_chain_of_custody.csv"
DEFAULT_JSON = ROOT / "data" / "nhi_pedot_h_a_chain_of_custody.json"
DEFAULT_REPORT = ROOT / "reports" / "nhi_pedot_h_a_chain_of_custody.md"

CONTENTS_NOTE = "nonclinical R&D acellular medium/coupon sample; no live cells"
HANDLING_NOTE = (
    "Keep sample identity and timepoint separated; record actual storage, transfer, "
    "and receipt conditions before entering measurements."
)
NON_EVIDENCE_BOUNDARY = (
    "Pending or blank transfer logs are not evidence. Only returned raw measurement "
    "rows with real values, provenance, and source files can count toward H-A."
)

LABEL_FIELDS = [
    "sample_id",
    "run_id",
    "article_id",
    "timepoint",
    "sample_event",
    "replicate",
    "planned_container_id",
    "condition",
    "storage_handling_notes",
    "contents_note",
    "required_readouts",
]

CUSTODY_FIELDS = [
    "chain_id",
    "sample_id",
    "run_id",
    "article_id",
    "timepoint",
    "sample_event",
    "replicate",
    "planned_container_id",
    "prepared_by",
    "prepared_at",
    "preparation_batch_id",
    "medium_name",
    "medium_lot",
    "coupon_or_well_id",
    "released_by",
    "released_at",
    "carrier_or_transfer_method",
    "received_by",
    "received_at",
    "condition_on_receipt",
    "storage_location",
    "source_file_returned",
    "deviation_notes",
    "transfer_status",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def article_roles(service: dict[str, Any]) -> dict[str, str]:
    roles = {}
    for item in service.get("stop_rules", []):
        article_id = item.get("article_id")
        role = item.get("role")
        if article_id and role:
            roles[str(article_id)] = str(role)
    return roles


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")


def container_id(index: int, row: dict[str, str]) -> str:
    article = slug(row.get("article_id", ""))[:18].upper()
    timepoint = slug(row.get("timepoint", "")).upper()
    event = slug(row.get("sample_event", ""))[:12].upper()
    return f"H-A-{index:02d}-{article}-{timepoint}-{event}"


def build_labels(samples: list[dict[str, str]], service: dict[str, Any]) -> list[dict[str, str]]:
    roles = article_roles(service)
    labels = []
    for index, row in enumerate(samples, start=1):
        article_id = row.get("article_id", "")
        labels.append({
            "sample_id": row.get("sample_id", ""),
            "run_id": row.get("run_id", ""),
            "article_id": article_id,
            "timepoint": row.get("timepoint", ""),
            "sample_event": row.get("sample_event", ""),
            "replicate": row.get("replicate", ""),
            "planned_container_id": container_id(index, row),
            "condition": roles.get(article_id, "H-A acellular coupon or medium-control condition"),
            "storage_handling_notes": HANDLING_NOTE,
            "contents_note": CONTENTS_NOTE,
            "required_readouts": row.get("readouts", ""),
        })
    return labels


def build_custody(labels: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for index, row in enumerate(labels, start=1):
        rows.append({
            "chain_id": f"NHI-PEDOT-H-A-COC-{index:03d}",
            "sample_id": row["sample_id"],
            "run_id": row["run_id"],
            "article_id": row["article_id"],
            "timepoint": row["timepoint"],
            "sample_event": row["sample_event"],
            "replicate": row["replicate"],
            "planned_container_id": row["planned_container_id"],
            "prepared_by": "",
            "prepared_at": "",
            "preparation_batch_id": "",
            "medium_name": "",
            "medium_lot": "",
            "coupon_or_well_id": "",
            "released_by": "",
            "released_at": "",
            "carrier_or_transfer_method": "",
            "received_by": "",
            "received_at": "",
            "condition_on_receipt": "",
            "storage_location": "",
            "source_file_returned": "",
            "deviation_notes": "",
            "transfer_status": "pending_real_transfer",
        })
    return rows


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def build_result(
    samples: list[dict[str, str]],
    labels: list[dict[str, str]],
    custody: list[dict[str, str]],
    service: dict[str, Any],
    labels_out: Path,
    custody_out: Path,
    json_out: Path,
    report: Path,
) -> dict[str, Any]:
    unique_runs = sorted({row.get("run_id", "") for row in samples if row.get("run_id")})
    articles = sorted({row.get("article_id", "") for row in samples if row.get("article_id")})
    pending_transfer_rows = sum(1 for row in custody if row.get("transfer_status") == "pending_real_transfer")
    return {
        "status": "ready_for_sample_handoff" if samples and labels and custody else "missing_sample_manifest_rows",
        "purpose": "Sample labels and blank chain-of-custody rows for the real NHI-PEDOT H-A measurement handoff.",
        "active_candidate": service.get("active_candidate", "limina_alg_lam_pedot_lowdose_v0_2"),
        "service_request_status": service.get("status", "unknown"),
        "sample_manifest_rows": len(samples),
        "sample_label_count": len(labels),
        "chain_of_custody_row_count": len(custody),
        "unique_run_count": len(unique_runs),
        "article_ids": articles,
        "pending_transfer_rows": pending_transfer_rows,
        "outputs": {
            "sample_labels_csv": rel(labels_out),
            "chain_of_custody_csv": rel(custody_out),
            "json": rel(json_out),
            "report": rel(report),
        },
        "blank_fields_to_complete": [
            field
            for field in CUSTODY_FIELDS
            if field
            not in {
                "chain_id",
                "sample_id",
                "run_id",
                "article_id",
                "timepoint",
                "sample_event",
                "replicate",
                "planned_container_id",
                "transfer_status",
            }
        ],
        "rejection_rules": [
            "Do not treat a label row, planned container ID, or blank custody row as measured evidence.",
            "Do not pool samples or collapse initial/final/physical-inspection events before raw data entry.",
            "Do not replace missing transfer fields with pending, TBD, unknown, synthetic, or fixture markers.",
            "Do not accept returned measurement rows unless source_file links back to instrument export or image files.",
        ],
        "non_evidence_boundary": NON_EVIDENCE_BOUNDARY,
    }


def render_report(result: dict[str, Any], labels: list[dict[str, str]]) -> str:
    lines = [
        "# NHI-PEDOT H-A Sample Labels and Chain of Custody",
        "",
        "This packet prepares sample handoff for real acellular H-A measurements. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Active candidate:** `{result['active_candidate']}`",
        f"**Service request:** `{result['service_request_status']}`",
        f"**Sample labels:** {result['sample_label_count']}",
        f"**Chain-of-custody rows:** {result['chain_of_custody_row_count']}",
        f"**Unique H-A runs:** {result['unique_run_count']}",
        f"**Pending transfers:** {result['pending_transfer_rows']}",
        "",
        "## Output Files",
        "",
        "| Artifact | Path |",
        "| --- | --- |",
    ]
    for label, path in result["outputs"].items():
        lines.append(f"| `{label}` | `{path}` |")

    lines.extend([
        "",
        "## Label Preview",
        "",
        "| Container | Sample | Article | Timepoint | Event | Condition |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for row in labels[:12]:
        lines.append(
            f"| `{row['planned_container_id']}` | `{row['sample_id']}` | "
            f"`{row['article_id']}` | {row['timepoint']} | `{row['sample_event']}` | {row['condition']} |"
        )

    lines.extend([
        "",
        "## Blank Fields To Complete During Transfer",
        "",
    ])
    lines.extend(f"- `{field}`" for field in result["blank_fields_to_complete"])

    lines.extend([
        "",
        "## Rejection Rules",
        "",
    ])
    lines.extend(f"- {item}" for item in result["rejection_rules"])

    lines.extend([
        "",
        "## Boundary",
        "",
        result["non_evidence_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NHI-PEDOT H-A sample labels and chain of custody.")
    parser.add_argument("--sample-manifest", type=Path, default=DEFAULT_SAMPLE_MANIFEST)
    parser.add_argument("--service-request", type=Path, default=DEFAULT_SERVICE)
    parser.add_argument("--labels-out", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--custody-out", type=Path, default=DEFAULT_CUSTODY)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    samples = load_rows(args.sample_manifest)
    service = load_json(args.service_request)
    labels = build_labels(samples, service)
    custody = build_custody(labels)
    result = build_result(
        samples,
        labels,
        custody,
        service,
        args.labels_out,
        args.custody_out,
        args.json_out,
        args.report,
    )

    write_rows(args.labels_out, LABEL_FIELDS, labels)
    write_rows(args.custody_out, CUSTODY_FIELDS, custody)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result, labels), encoding="utf-8")
    print(f"H-A chain of custody: {result['status']}")
    print(f"Wrote {args.labels_out}")
    print(f"Wrote {args.custody_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if result["status"] == "ready_for_sample_handoff" else 2


if __name__ == "__main__":
    raise SystemExit(main())
