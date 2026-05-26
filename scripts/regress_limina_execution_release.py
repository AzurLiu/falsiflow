#!/usr/bin/env python3
"""Regression checks for LIMINA execution-release audit guards."""

from __future__ import annotations

import json
from pathlib import Path

from audit_limina_execution_release import Profile, build_audit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_execution_release_regression.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_execution_release_regression.md"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def profile() -> Profile:
    base = ROOT / "tmp" / "regression"
    return Profile(
        key="regression",
        label="Execution Release Regression",
        gate_label="Regression Gate",
        delivery=base / "delivery.json",
        quote_selection=base / "quote_selection.json",
        send_log=base / "send_log.json",
        reply_log=base / "reply_log.json",
        authorization_log=base / "authorization_log.json",
        chain=base / "chain.json",
        sample_submission=base / "sample_submission.json",
        vendor_return=base / "vendor_return.json",
        json_out=base / "execution_release.json",
        report=base / "execution_release.md",
        status_prefix="regression_execution_release",
        selected_decision="selected_for_regression",
    )


def delivery_ready() -> dict:
    return {"status": "ready_to_send", "missing_required_file_ids": []}


def chain_ready() -> dict:
    return {
        "status": "ready_for_sample_handoff",
        "sample_label_count": 4,
        "chain_of_custody_row_count": 4,
    }


def sample_submission_ready() -> dict:
    return {
        "status": "sample_submission_precheck_ready",
        "shipping_status": "do_not_ship_until_vendor_confirms_quote_sample_acceptance_sds_and_custody",
    }


def vendor_return_waiting() -> dict:
    return {"status": "vendor_return_waiting_for_files"}


def logs(sent_ids: list[str], reply_ids: list[str]) -> tuple[dict, dict]:
    return (
        {
            "status": "send_log_ok",
            "error_count": 0,
            "valid_sent_rows": len(sent_ids),
            "valid_sent_candidate_ids": sent_ids,
        },
        {
            "status": "reply_log_ok",
            "error_count": 0,
            "valid_reply_rows": len(reply_ids),
            "valid_reply_candidate_ids": reply_ids,
        },
    )


def authorization(ids: list[str], errors: int = 0) -> dict:
    return {
        "status": "authorization_ok" if ids and errors == 0 else "authorization_waiting",
        "error_count": errors,
        "valid_authorization_rows": len(ids),
        "valid_authorized_candidate_ids": ids,
    }


def quote_selection(selected: bool, source_backed: bool) -> dict:
    decision = "selected_for_regression" if selected else "shortlist_for_regression"
    return {
        "status": "provider_selected_waiting_for_measurements" if selected else "ready_to_select_provider",
        "reply_log_errors": 0,
        "selected_count": 1 if selected else 0,
        "source_backed_reply_count": 1 if source_backed else 0,
        "scored_rows": [{
            "candidate_id": "vendor_a",
            "vendor_name": "Vendor A",
            "selection_decision": decision,
            "source_backed_reply": source_backed,
        }],
    }


def audit_case(
    selected: bool,
    source_backed: bool,
    sent_ids: list[str],
    reply_ids: list[str],
    authorized_ids: list[str],
) -> dict:
    send_log, reply_log = logs(sent_ids, reply_ids)
    return build_audit(
        profile(),
        delivery_ready(),
        quote_selection(selected, source_backed),
        send_log,
        reply_log,
        authorization(authorized_ids),
        chain_ready(),
        sample_submission_ready(),
        vendor_return_waiting(),
    )


def run_case() -> dict:
    no_selection = audit_case(selected=False, source_backed=True, sent_ids=[], reply_ids=[], authorized_ids=[])
    ready = audit_case(selected=True, source_backed=True, sent_ids=["vendor_a"], reply_ids=["vendor_a"], authorized_ids=[])
    released = audit_case(selected=True, source_backed=True, sent_ids=["vendor_a"], reply_ids=["vendor_a"], authorized_ids=["vendor_a"])
    unbacked_selection = audit_case(selected=True, source_backed=False, sent_ids=["vendor_a"], reply_ids=[], authorized_ids=[])
    unsent_selection = audit_case(selected=True, source_backed=True, sent_ids=[], reply_ids=["vendor_a"], authorized_ids=[])

    checks = {
        "no_source_backed_selected_provider_blocks": (
            no_selection["status"] == "regression_execution_release_blocked_no_source_backed_provider_selection"
            and not no_selection["ready_for_execution_authorization"]
        ),
        "source_backed_selected_provider_can_reach_authorization_ready": (
            ready["status"] == "regression_execution_release_ready_for_human_authorization"
            and ready["ready_for_execution_authorization"]
            and not ready["released_for_execution"]
            and any(row["code"] == "selected_provider_has_valid_execution_authorization" for row in ready["authorization_blockers"])
        ),
        "valid_authorization_releases_execution": (
            released["status"] == "regression_execution_release_released_for_execution"
            and released["ready_for_execution_authorization"]
            and released["released_for_execution"]
            and released["physical_shipment_allowed"]
        ),
        "selected_without_source_backing_blocks": (
            unbacked_selection["status"] == "regression_execution_release_blocked_no_source_backed_provider_selection"
            and unbacked_selection["source_backed_selected_provider_count"] == 0
        ),
        "selected_provider_must_have_verified_send_log": (
            unsent_selection["status"] == "regression_execution_release_blocked"
            and any(row["code"] == "selected_provider_has_verified_send_log" for row in unsent_selection["blockers"])
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "no_selection_status": no_selection["status"],
        "ready_status": ready["status"],
        "released_status": released["status"],
        "unbacked_selection_status": unbacked_selection["status"],
        "unsent_selection_status": unsent_selection["status"],
    }


def render_report(result: dict) -> str:
    lines = [
        "# LIMINA Execution Release Regression",
        "",
        f"**Status:** `{result['status']}`",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{key}`: {str(value).lower()}" for key, value in result["checks"].items())
    lines.extend([
        "",
        "## Boundary",
        "",
        "This regression uses in-memory sourcing fixtures only. It does not create material evidence or release samples.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    result = run_case()
    write_json(DEFAULT_JSON, result)
    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text(render_report(result), encoding="utf-8")
    print(f"LIMINA execution-release regression: {result['status']}")
    print(f"Wrote {DEFAULT_JSON}")
    print(f"Wrote {DEFAULT_REPORT}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
