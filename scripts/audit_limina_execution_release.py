#!/usr/bin/env python3
"""Audit whether LIMINA sourcing is ready for human execution authorization."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Profile:
    key: str
    label: str
    gate_label: str
    delivery: Path
    quote_selection: Path
    send_log: Path
    reply_log: Path
    authorization_log: Path
    chain: Path
    sample_submission: Path | None
    vendor_return: Path
    json_out: Path
    report: Path
    status_prefix: str
    selected_decision: str


PROFILES = {
    "h_a": Profile(
        key="h_a",
        label="NHI-PEDOT H-A",
        gate_label="H-A",
        delivery=ROOT / "data" / "nhi_pedot_h_a_delivery_package_manifest.json",
        quote_selection=ROOT / "data" / "nhi_pedot_h_a_quote_selection.json",
        send_log=ROOT / "data" / "nhi_pedot_h_a_rfq_send_log.json",
        reply_log=ROOT / "data" / "nhi_pedot_h_a_rfq_reply_log.json",
        authorization_log=ROOT / "data" / "nhi_pedot_h_a_execution_authorization_log.json",
        chain=ROOT / "data" / "nhi_pedot_h_a_chain_of_custody.json",
        sample_submission=ROOT / "data" / "nhi_pedot_h_a_sample_submission_pack.json",
        vendor_return=ROOT / "data" / "nhi_pedot_h_a_vendor_return_intake.json",
        json_out=ROOT / "data" / "nhi_pedot_h_a_execution_release_audit.json",
        report=ROOT / "reports" / "nhi_pedot_h_a_execution_release_audit.md",
        status_prefix="nhi_pedot_h_a_execution_release",
        selected_decision="selected_for_h_a",
    ),
    "zrc_phase_a": Profile(
        key="zrc_phase_a",
        label="ZRC-ND Phase A",
        gate_label="ZRC-ND Phase A",
        delivery=ROOT / "data" / "zrc_nd_phase_a_delivery_package_manifest.json",
        quote_selection=ROOT / "data" / "zrc_nd_phase_a_quote_selection.json",
        send_log=ROOT / "data" / "zrc_nd_phase_a_rfq_send_log.json",
        reply_log=ROOT / "data" / "zrc_nd_phase_a_rfq_reply_log.json",
        authorization_log=ROOT / "data" / "zrc_nd_phase_a_execution_authorization_log.json",
        chain=ROOT / "data" / "zrc_nd_phase_a_chain_of_custody.json",
        sample_submission=None,
        vendor_return=ROOT / "data" / "zrc_nd_phase_a_vendor_return_intake.json",
        json_out=ROOT / "data" / "zrc_nd_phase_a_execution_release_audit.json",
        report=ROOT / "reports" / "zrc_nd_phase_a_execution_release_audit.md",
        status_prefix="zrc_nd_phase_a_execution_release",
        selected_decision="selected_for_phase_a",
    ),
}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def string_set(values: list[Any]) -> set[str]:
    return {str(value) for value in values if str(value)}


def selected_rows(quote_selection: dict[str, Any], selected_decision: str) -> list[dict[str, Any]]:
    return [
        row for row in quote_selection.get("scored_rows", [])
        if row.get("selection_decision") == selected_decision
    ]


def add_check(
    checklist: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    code: str,
    passed: bool,
    blocking: bool,
    detail: str,
) -> None:
    row = {
        "code": code,
        "passed": passed,
        "blocking": blocking,
        "detail": detail,
    }
    checklist.append(row)
    if blocking and not passed:
        blockers.append(row)


def status_for(
    profile: Profile,
    blockers: list[dict[str, Any]],
    released_for_execution: bool,
    ready_for_authorization: bool,
) -> str:
    codes = {row["code"] for row in blockers}
    if "source_backed_provider_selected" in codes:
        return f"{profile.status_prefix}_blocked_no_source_backed_provider_selection"
    if blockers:
        return f"{profile.status_prefix}_blocked"
    if released_for_execution:
        return f"{profile.status_prefix}_released_for_execution"
    if ready_for_authorization:
        return f"{profile.status_prefix}_ready_for_human_authorization"
    return f"{profile.status_prefix}_waiting_for_authorization_context"


def build_audit(
    profile: Profile,
    delivery: dict[str, Any],
    quote_selection: dict[str, Any],
    send_log: dict[str, Any],
    reply_log: dict[str, Any],
    authorization_log: dict[str, Any],
    chain: dict[str, Any],
    sample_submission: dict[str, Any],
    vendor_return: dict[str, Any],
) -> dict[str, Any]:
    checklist: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    authorization_checks: list[dict[str, Any]] = []
    authorization_blockers: list[dict[str, Any]] = []

    missing_delivery_files = delivery.get("missing_required_file_ids", [])
    delivery_ready = delivery.get("status") == "ready_to_send" and not missing_delivery_files
    add_check(
        checklist,
        blockers,
        "delivery_package_ready",
        delivery_ready,
        True,
        f"status={delivery.get('status', 'unknown')}; missing_required_files={len(missing_delivery_files)}",
    )

    quote_errors = int(quote_selection.get("reply_log_errors", 0) or 0)
    add_check(
        checklist,
        blockers,
        "quote_selection_has_no_reply_log_errors",
        quote_errors == 0,
        True,
        f"reply_log_errors={quote_errors}; status={quote_selection.get('status', 'unknown')}",
    )

    send_errors = int(send_log.get("error_count", 0) or 0)
    add_check(
        checklist,
        blockers,
        "rfq_send_log_has_no_errors",
        send_errors == 0,
        True,
        f"errors={send_errors}; status={send_log.get('status', 'unknown')}",
    )

    reply_errors = int(reply_log.get("error_count", 0) or 0)
    add_check(
        checklist,
        blockers,
        "rfq_reply_log_has_no_errors",
        reply_errors == 0,
        True,
        f"errors={reply_errors}; status={reply_log.get('status', 'unknown')}",
    )

    selected = selected_rows(quote_selection, profile.selected_decision)
    selected_ids = [str(row.get("candidate_id", "")) for row in selected if row.get("candidate_id")]
    source_backed_selected = [
        row for row in selected
        if row.get("source_backed_reply") is True and row.get("candidate_id")
    ]
    source_backed_selected_ids = [str(row["candidate_id"]) for row in source_backed_selected]
    add_check(
        checklist,
        blockers,
        "source_backed_provider_selected",
        bool(source_backed_selected_ids),
        True,
        (
            f"selected={len(selected_ids)}; "
            f"source_backed_selected={len(source_backed_selected_ids)}; "
            f"selected_ids={','.join(selected_ids) or '-'}"
        ),
    )

    valid_sent_ids = string_set(send_log.get("valid_sent_candidate_ids", []))
    if source_backed_selected_ids:
        missing_sent = sorted(set(source_backed_selected_ids) - valid_sent_ids)
        add_check(
            checklist,
            blockers,
            "selected_provider_has_verified_send_log",
            not missing_sent,
            True,
            (
                f"selected_source_backed_ids={','.join(source_backed_selected_ids)}; "
                f"valid_sent_ids={','.join(sorted(valid_sent_ids)) or '-'}; "
                f"missing_sent={','.join(missing_sent) or '-'}"
            ),
        )
    else:
        add_check(
            checklist,
            blockers,
            "selected_provider_has_verified_send_log",
            False,
            False,
            "waiting for a source-backed selected provider before send-log matching is meaningful",
        )

    valid_reply_ids = string_set(reply_log.get("valid_reply_candidate_ids", []))
    if source_backed_selected_ids:
        missing_reply = sorted(set(source_backed_selected_ids) - valid_reply_ids)
        add_check(
            checklist,
            blockers,
            "selected_provider_has_source_backed_reply_file",
            not missing_reply,
            True,
            (
                f"selected_source_backed_ids={','.join(source_backed_selected_ids)}; "
                f"valid_reply_ids={','.join(sorted(valid_reply_ids)) or '-'}; "
                f"missing_reply={','.join(missing_reply) or '-'}"
            ),
        )
    else:
        add_check(
            checklist,
            blockers,
            "selected_provider_has_source_backed_reply_file",
            False,
            False,
            "waiting for a source-backed selected provider before reply-file matching is meaningful",
        )

    labels = int(chain.get("sample_label_count", 0) or 0)
    custody_rows = int(chain.get("chain_of_custody_row_count", 0) or 0)
    add_check(
        checklist,
        blockers,
        "chain_of_custody_template_ready",
        labels > 0 and custody_rows > 0,
        True,
        f"status={chain.get('status', 'unknown')}; labels={labels}; custody_rows={custody_rows}",
    )

    if profile.sample_submission is not None:
        submission_status = sample_submission.get("status", "unknown")
        shipping_status = sample_submission.get("shipping_status", "unknown")
        add_check(
            checklist,
            blockers,
            "sample_submission_precheck_present",
            submission_status != "unknown",
            True,
            f"status={submission_status}; shipping_status={shipping_status}",
        )
        add_check(
            checklist,
            blockers,
            "sample_submission_shipping_not_self_released",
            not str(shipping_status).startswith("do_not_ship"),
            False,
            (
                f"shipping_status={shipping_status}; this static precheck remains a "
                "human shipment stop until provider acceptance, SDS, custody, and authorization are recorded"
            ),
        )

    vendor_status = vendor_return.get("status", "unknown")
    add_check(
        checklist,
        blockers,
        "vendor_return_files_not_required_for_execution_release",
        True,
        False,
        f"status={vendor_status}; returned measurement files are checked after execution, not before authorization",
    )

    ready_for_authorization = not blockers
    authorization_errors = int(authorization_log.get("error_count", 0) or 0)
    add_check(
        authorization_checks,
        authorization_blockers,
        "execution_authorization_log_has_no_errors",
        authorization_errors == 0,
        True,
        f"errors={authorization_errors}; status={authorization_log.get('status', 'unknown')}",
    )
    valid_authorized_ids = string_set(authorization_log.get("valid_authorized_candidate_ids", []))
    if source_backed_selected_ids:
        missing_authorization = sorted(set(source_backed_selected_ids) - valid_authorized_ids)
        add_check(
            authorization_checks,
            authorization_blockers,
            "selected_provider_has_valid_execution_authorization",
            not missing_authorization,
            True,
            (
                f"selected_source_backed_ids={','.join(source_backed_selected_ids)}; "
                f"valid_authorized_ids={','.join(sorted(valid_authorized_ids)) or '-'}; "
                f"missing_authorization={','.join(missing_authorization) or '-'}"
            ),
        )
    else:
        add_check(
            authorization_checks,
            authorization_blockers,
            "selected_provider_has_valid_execution_authorization",
            False,
            False,
            "waiting for a source-backed selected provider before authorization matching is meaningful",
        )

    released_for_execution = ready_for_authorization and not authorization_blockers and bool(source_backed_selected_ids)
    status = status_for(profile, blockers, released_for_execution, ready_for_authorization)
    next_action = (
        "Send RFQs, preserve original replies, fill the reply log, and select a source-backed provider."
        if any(row["code"] == "source_backed_provider_selected" for row in blockers)
        else (
            "Resolve blocking checklist items before execution authorization."
            if blockers
            else (
                "Execution is released by a valid human authorization log; proceed to custody-controlled execution and returned-file intake."
                if released_for_execution
                else "Fill the execution authorization log with a source-backed authorization record before samples move."
            )
        )
    )

    return {
        "status": status,
        "profile": profile.key,
        "label": profile.label,
        "gate_label": profile.gate_label,
        "purpose": "Audit sourcing and package readiness before any sample shipment or outsourced execution authorization.",
        "ready_for_execution_authorization": ready_for_authorization,
        "released_for_execution": released_for_execution,
        "physical_shipment_allowed": released_for_execution,
        "manual_authorization_required": True,
        "selected_decision": profile.selected_decision,
        "selected_provider_count": len(selected_ids),
        "source_backed_selected_provider_count": len(source_backed_selected_ids),
        "selected_candidate_ids": selected_ids,
        "source_backed_selected_candidate_ids": source_backed_selected_ids,
        "valid_sent_candidate_ids": sorted(valid_sent_ids),
        "valid_reply_candidate_ids": sorted(valid_reply_ids),
        "valid_authorized_candidate_ids": sorted(valid_authorized_ids),
        "blocker_count": len(blockers),
        "blockers": blockers,
        "authorization_blocker_count": len(authorization_blockers),
        "authorization_blockers": authorization_blockers,
        "checklist": checklist,
        "authorization_checks": authorization_checks,
        "next_action": next_action,
        "inputs": {
            "delivery_package": rel(profile.delivery),
            "quote_selection": rel(profile.quote_selection),
            "rfq_send_log": rel(profile.send_log),
            "rfq_reply_log": rel(profile.reply_log),
            "execution_authorization_log": rel(profile.authorization_log),
            "chain_of_custody": rel(profile.chain),
            "sample_submission": rel(profile.sample_submission) if profile.sample_submission else "",
            "vendor_return": rel(profile.vendor_return),
        },
        "non_evidence_boundary": (
            "Execution release status is logistics control only. It is not measured material evidence, "
            "does not release samples by itself, and cannot advance suitability gates without returned "
            "real measurement rows and source files."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['label']} Execution Release Audit",
        "",
        "This report audits whether sourcing is ready for human execution authorization. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Ready for human execution authorization:** `{str(result['ready_for_execution_authorization']).lower()}`",
        f"**Released for execution:** `{str(result['released_for_execution']).lower()}`",
        f"**Physical shipment allowed:** `{str(result['physical_shipment_allowed']).lower()}`",
        f"**Selected providers:** {result['selected_provider_count']}",
        f"**Source-backed selected providers:** {result['source_backed_selected_provider_count']}",
        f"**Blockers:** {result['blocker_count']}",
        f"**Authorization blockers:** {result['authorization_blocker_count']}",
        "",
        "## Checklist",
        "",
        "| Check | Passed | Blocking | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for row in result["checklist"]:
        lines.append(
            f"| `{row['code']}` | `{str(row['passed']).lower()}` | "
            f"`{str(row['blocking']).lower()}` | {row['detail']} |"
        )

    lines.extend([
        "",
        "## Authorization Checks",
        "",
        "| Check | Passed | Blocking | Detail |",
        "| --- | --- | --- | --- |",
    ])
    for row in result["authorization_checks"]:
        lines.append(
            f"| `{row['code']}` | `{str(row['passed']).lower()}` | "
            f"`{str(row['blocking']).lower()}` | {row['detail']} |"
        )

    lines.extend(["", "## Blockers", ""])
    if result["blockers"]:
        lines.extend(
            f"- `{row['code']}`: {row['detail']}"
            for row in result["blockers"]
        )
    else:
        lines.append("- No pre-authorization checklist failures.")

    lines.extend(["", "## Authorization Blockers", ""])
    if result["authorization_blockers"]:
        lines.extend(
            f"- `{row['code']}`: {row['detail']}"
            for row in result["authorization_blockers"]
        )
    else:
        lines.append("- No authorization blockers.")

    lines.extend([
        "",
        "## Next Action",
        "",
        result["next_action"],
        "",
        "## Boundary",
        "",
        result["non_evidence_boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit LIMINA execution-release readiness.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="h_a")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--report", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    base = PROFILES[args.profile]
    profile = Profile(
        key=base.key,
        label=base.label,
        gate_label=base.gate_label,
        delivery=base.delivery,
        quote_selection=base.quote_selection,
        send_log=base.send_log,
        reply_log=base.reply_log,
        authorization_log=base.authorization_log,
        chain=base.chain,
        sample_submission=base.sample_submission,
        vendor_return=base.vendor_return,
        json_out=args.json_out or base.json_out,
        report=args.report or base.report,
        status_prefix=base.status_prefix,
        selected_decision=base.selected_decision,
    )
    result = build_audit(
        profile,
        load_json(profile.delivery),
        load_json(profile.quote_selection),
        load_json(profile.send_log),
        load_json(profile.reply_log),
        load_json(profile.authorization_log),
        load_json(profile.chain),
        load_json(profile.sample_submission),
        load_json(profile.vendor_return),
    )
    profile.json_out.parent.mkdir(parents=True, exist_ok=True)
    profile.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    profile.report.parent.mkdir(parents=True, exist_ok=True)
    profile.report.write_text(render_report(result), encoding="utf-8")
    print(f"{profile.label} execution release audit: {result['status']}")
    print(f"Ready for authorization: {str(result['ready_for_execution_authorization']).lower()}")
    print(f"Released for execution: {str(result['released_for_execution']).lower()}")
    print(f"Blockers: {result['blocker_count']}")
    print(f"Wrote {profile.json_out}")
    print(f"Wrote {profile.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
