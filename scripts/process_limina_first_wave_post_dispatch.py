#!/usr/bin/env python3
"""Process saved first-wave RFQ confirmations and replies for H-A and ZRC."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_first_wave_post_dispatch_processing.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_first_wave_post_dispatch_processing.md"

COMMANDS = [
    {
        "id": "intake_h_a_send_confirmations",
        "track": "h_a",
        "argv": ["scripts/intake_limina_rfq_send_confirmations.py", "--profile", "h_a"],
        "purpose": "Register source-backed H-A sent-email or web-form confirmations.",
    },
    {
        "id": "render_h_a_non_eml_confirmation_sheet",
        "track": "h_a",
        "argv": ["scripts/render_nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.py"],
        "purpose": "Refresh guarded H-A manual-confirmation rows for non-EML confirmations.",
    },
    {
        "id": "apply_h_a_non_eml_confirmation_sheet",
        "track": "h_a",
        "argv": ["scripts/apply_nhi_pedot_h_a_rfq_send_confirmation_entry_sheet.py"],
        "purpose": "Apply reviewed H-A non-EML confirmation entries into the send log.",
    },
    {
        "id": "apply_h_a_send_log",
        "track": "h_a",
        "argv": ["scripts/apply_limina_rfq_send_log.py", "--profile", "h_a"],
        "purpose": "Apply verified H-A send rows into the quote tracker.",
    },
    {
        "id": "intake_h_a_replies",
        "track": "h_a",
        "argv": ["scripts/intake_limina_rfq_replies.py", "--profile", "h_a"],
        "purpose": "Register original H-A reply source files for review.",
    },
    {
        "id": "apply_h_a_reply_log",
        "track": "h_a",
        "argv": ["scripts/apply_limina_rfq_reply_log.py", "--profile", "h_a"],
        "purpose": "Apply reviewed H-A reply fields into the quote tracker.",
    },
    {
        "id": "evaluate_h_a_quotes",
        "track": "h_a",
        "argv": ["scripts/evaluate_nhi_pedot_h_a_quote_replies.py"],
        "purpose": "Evaluate source-backed H-A quote replies for provider selection.",
    },
    {
        "id": "apply_h_a_execution_authorization",
        "track": "h_a",
        "argv": ["scripts/apply_limina_execution_authorization_log.py", "--profile", "h_a"],
        "purpose": "Validate any H-A execution authorization records.",
    },
    {
        "id": "audit_h_a_execution_release",
        "track": "h_a",
        "argv": ["scripts/audit_limina_execution_release.py", "--profile", "h_a"],
        "purpose": "Check whether H-A execution can be released after provider selection and authorization.",
    },
    {
        "id": "check_h_a_vendor_return",
        "track": "h_a",
        "argv": ["scripts/render_nhi_pedot_h_a_vendor_return_intake.py"],
        "purpose": "Check whether real H-A return files are ready for merge/QC.",
    },
    {
        "id": "intake_zrc_send_confirmations",
        "track": "zrc_phase_a",
        "argv": ["scripts/intake_limina_rfq_send_confirmations.py", "--profile", "zrc_phase_a"],
        "purpose": "Register source-backed ZRC sent-email or web-form confirmations.",
    },
    {
        "id": "render_zrc_non_eml_confirmation_sheet",
        "track": "zrc_phase_a",
        "argv": ["scripts/render_zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.py"],
        "purpose": "Refresh guarded ZRC manual-confirmation rows for non-EML confirmations.",
    },
    {
        "id": "apply_zrc_non_eml_confirmation_sheet",
        "track": "zrc_phase_a",
        "argv": ["scripts/apply_zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.py"],
        "purpose": "Apply reviewed ZRC non-EML confirmation entries into the send log.",
    },
    {
        "id": "apply_zrc_send_log",
        "track": "zrc_phase_a",
        "argv": ["scripts/apply_limina_rfq_send_log.py", "--profile", "zrc_phase_a"],
        "purpose": "Apply verified ZRC send rows into the quote tracker.",
    },
    {
        "id": "intake_zrc_replies",
        "track": "zrc_phase_a",
        "argv": ["scripts/intake_limina_rfq_replies.py", "--profile", "zrc_phase_a"],
        "purpose": "Register original ZRC reply source files for review.",
    },
    {
        "id": "apply_zrc_reply_log",
        "track": "zrc_phase_a",
        "argv": ["scripts/apply_limina_rfq_reply_log.py", "--profile", "zrc_phase_a"],
        "purpose": "Apply reviewed ZRC reply fields into the quote tracker.",
    },
    {
        "id": "evaluate_zrc_quotes",
        "track": "zrc_phase_a",
        "argv": ["scripts/evaluate_zrc_nd_phase_a_quote_replies.py"],
        "purpose": "Evaluate source-backed ZRC quote replies for provider selection.",
    },
    {
        "id": "apply_zrc_execution_authorization",
        "track": "zrc_phase_a",
        "argv": ["scripts/apply_limina_execution_authorization_log.py", "--profile", "zrc_phase_a"],
        "purpose": "Validate any ZRC execution authorization records.",
    },
    {
        "id": "audit_zrc_execution_release",
        "track": "zrc_phase_a",
        "argv": ["scripts/audit_limina_execution_release.py", "--profile", "zrc_phase_a"],
        "purpose": "Check whether ZRC execution can be released after provider selection and authorization.",
    },
    {
        "id": "check_zrc_vendor_return",
        "track": "zrc_phase_a",
        "argv": ["scripts/render_zrc_nd_phase_a_vendor_return_intake.py"],
        "purpose": "Check whether real ZRC return files are ready for merge/QC.",
    },
    {
        "id": "refresh_first_wave_cockpit",
        "track": "combined",
        "argv": ["scripts/render_limina_first_wave_rfq_dispatch_cockpit.py"],
        "purpose": "Refresh the combined dispatch cockpit after processing saved files.",
    },
]

TRACK_FILES = {
    "h_a": {
        "send_intake": ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_intake.json",
        "send_entry": ROOT / "data" / "nhi_pedot_h_a_rfq_send_confirmation_entry_apply.json",
        "send_log": ROOT / "data" / "nhi_pedot_h_a_rfq_send_log.json",
        "reply_intake": ROOT / "data" / "nhi_pedot_h_a_rfq_reply_intake.json",
        "reply_log": ROOT / "data" / "nhi_pedot_h_a_rfq_reply_log.json",
        "quote_selection": ROOT / "data" / "nhi_pedot_h_a_quote_selection.json",
        "execution_release": ROOT / "data" / "nhi_pedot_h_a_execution_release_audit.json",
        "vendor_return": ROOT / "data" / "nhi_pedot_h_a_vendor_return_intake.json",
    },
    "zrc_phase_a": {
        "send_intake": ROOT / "data" / "zrc_nd_phase_a_rfq_send_confirmation_intake.json",
        "send_entry": ROOT / "data" / "zrc_nd_phase_a_rfq_send_confirmation_entry_apply.json",
        "send_log": ROOT / "data" / "zrc_nd_phase_a_rfq_send_log.json",
        "reply_intake": ROOT / "data" / "zrc_nd_phase_a_rfq_reply_intake.json",
        "reply_log": ROOT / "data" / "zrc_nd_phase_a_rfq_reply_log.json",
        "quote_selection": ROOT / "data" / "zrc_nd_phase_a_quote_selection.json",
        "execution_release": ROOT / "data" / "zrc_nd_phase_a_execution_release_audit.json",
        "vendor_return": ROOT / "data" / "zrc_nd_phase_a_vendor_return_intake.json",
    },
}


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


def run_command(item: dict[str, Any]) -> dict[str, Any]:
    argv = [sys.executable, *item["argv"]]
    started = time.perf_counter()
    completed = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "id": item["id"],
        "track": item["track"],
        "argv": item["argv"],
        "purpose": item["purpose"],
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "stdout_tail": tail(completed.stdout),
        "stderr_tail": tail(completed.stderr),
    }


def tail(text: str, limit: int = 8) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines[-limit:])


def track_summary(track: str, files: dict[str, Path]) -> dict[str, Any]:
    send_intake = load_json(files["send_intake"])
    send_entry = load_json(files["send_entry"])
    send_log = load_json(files["send_log"])
    reply_intake = load_json(files["reply_intake"])
    reply_log = load_json(files["reply_log"])
    quote_selection = load_json(files["quote_selection"])
    execution_release = load_json(files["execution_release"])
    vendor_return = load_json(files["vendor_return"])
    send_entry_summary = send_entry.get("summary", {})
    return {
        "track": track,
        "send_intake_status": send_intake.get("status", "unknown"),
        "send_intake_files": send_intake.get("row_count", 0),
        "send_intake_applied": send_intake.get("applied_rows", 0),
        "send_intake_needs_review": send_intake.get("needs_review_rows", 0),
        "send_entry_status": send_entry.get("status", "unknown"),
        "send_entry_apply_rows": send_entry_summary.get("apply_rows", 0),
        "send_entry_applied": send_entry_summary.get("applied_rows", 0),
        "send_entry_blocked": send_entry_summary.get("blocked_rows", 0),
        "send_log_status": send_log.get("status", "unknown"),
        "send_log_rows": send_log.get("row_count", 0),
        "send_log_sent": send_log.get("sent_rows", 0),
        "send_log_valid": send_log.get("valid_sent_rows", 0),
        "reply_intake_status": reply_intake.get("status", "unknown"),
        "reply_intake_files": reply_intake.get("row_count", 0),
        "reply_intake_applied": reply_intake.get("applied_rows", 0),
        "reply_intake_needs_review": reply_intake.get("needs_manual_review_rows", 0),
        "reply_log_status": reply_log.get("status", "unknown"),
        "reply_log_rows": reply_log.get("row_count", 0),
        "reply_log_received": reply_log.get("received_rows", 0),
        "reply_log_valid": reply_log.get("valid_reply_rows", 0),
        "quote_selection_status": quote_selection.get("status", "unknown"),
        "quote_selection_replies": quote_selection.get("reply_count", 0),
        "quote_selection_source_backed": quote_selection.get("source_backed_reply_count", 0),
        "quote_selection_shortlist": quote_selection.get("shortlist_count", 0),
        "execution_release_status": execution_release.get("status", "unknown"),
        "execution_release_ready": bool(execution_release.get("ready_for_execution_authorization")),
        "execution_released": bool(execution_release.get("released_for_execution")),
        "vendor_return_status": vendor_return.get("status", "unknown"),
    }


def status_for(result: dict[str, Any]) -> str:
    if result["failed_command_ids"]:
        return "first_wave_post_dispatch_processing_failed"
    summaries = result["track_summaries"]
    confirmations = sum(item["send_intake_files"] for item in summaries)
    valid_sends = sum(item["send_log_valid"] for item in summaries)
    replies = sum(item["reply_intake_files"] for item in summaries)
    source_backed_replies = sum(item["quote_selection_source_backed"] for item in summaries)
    shortlist = sum(item["quote_selection_shortlist"] for item in summaries)
    released = any(item["execution_released"] for item in summaries)
    if released:
        return "first_wave_post_dispatch_execution_released"
    if shortlist:
        return "first_wave_post_dispatch_ready_for_execution_authorization"
    if source_backed_replies:
        return "first_wave_post_dispatch_has_source_backed_replies"
    if replies:
        return "first_wave_post_dispatch_has_replies_needing_review"
    if valid_sends:
        return "first_wave_post_dispatch_waiting_for_vendor_replies"
    if confirmations:
        return "first_wave_post_dispatch_has_confirmations_needing_review"
    return "first_wave_post_dispatch_waiting_for_real_send_confirmations"


def build_result(commands: list[dict[str, Any]]) -> dict[str, Any]:
    first_wave = load_json(ROOT / "data" / "limina_first_wave_rfq_dispatch_cockpit.json")
    track_summaries = [track_summary(track, files) for track, files in TRACK_FILES.items()]
    failed = [item["id"] for item in commands if item["returncode"] != 0]
    result = {
        "status": "pending",
        "purpose": "Process real first-wave RFQ send confirmations and replies after manual dispatch.",
        "failed_command_ids": failed,
        "first_wave_cockpit_status": first_wave.get("status", "unknown"),
        "first_wave_cockpit_summary": first_wave.get("summary", {}),
        "track_summaries": track_summaries,
        "commands": commands,
        "generated_artifacts": {
            "json": "data/limina_first_wave_post_dispatch_processing.json",
            "report": "reports/limina_first_wave_post_dispatch_processing.md",
        },
        "next_commands": [
            "python3 scripts/process_limina_first_wave_post_dispatch.py",
            "python3 scripts/run_limina_iteration.py",
        ],
        "boundary": (
            "This processing step handles outreach and sourcing artifacts only. It does not create measurements, "
            "authorize execution, or support a material suitability claim without real returned measurement rows."
        ),
    }
    result["status"] = status_for(result)
    return result


def render_report(result: dict[str, Any]) -> str:
    summary = result["first_wave_cockpit_summary"]
    lines = [
        "# LIMINA First-Wave Post-Dispatch Processing",
        "",
        "This report processes saved RFQ confirmations and replies. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**First-wave cockpit:** `{result['first_wave_cockpit_status']}`; rows={summary.get('vendor_rows', 0)}; ready={summary.get('ready_to_send_rows', 0)}; confirmations={summary.get('confirmation_files_present', 0)}; replies={summary.get('reply_files_present', 0)}",
        f"**Failed commands:** {len(result['failed_command_ids'])}",
        "",
        "## Track Summaries",
        "",
        "| Track | Send intake | Send log | Reply intake | Reply log | Quote selection | Execution release | Vendor return |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in result["track_summaries"]:
        lines.append(
            f"| `{item['track']}` | `{item['send_intake_status']}`; files={item['send_intake_files']}; applied={item['send_intake_applied']}; review={item['send_intake_needs_review']} | "
            f"`{item['send_log_status']}`; sent={item['send_log_sent']}; valid={item['send_log_valid']} | "
            f"`{item['reply_intake_status']}`; files={item['reply_intake_files']}; applied={item['reply_intake_applied']}; review={item['reply_intake_needs_review']} | "
            f"`{item['reply_log_status']}`; received={item['reply_log_received']}; valid={item['reply_log_valid']} | "
            f"`{item['quote_selection_status']}`; replies={item['quote_selection_replies']}; source_backed={item['quote_selection_source_backed']}; shortlist={item['quote_selection_shortlist']} | "
            f"`{item['execution_release_status']}`; ready={str(item['execution_release_ready']).lower()}; released={str(item['execution_released']).lower()} | "
            f"`{item['vendor_return_status']}` |"
        )
    lines.extend(["", "## Commands Run", "", "| Command | Return | Purpose |", "| --- | ---: | --- |"])
    for item in result["commands"]:
        lines.append(f"| `{item['id']}` | {item['returncode']} | {item['purpose']} |")
    lines.extend(["", "## Next Commands", ""])
    lines.extend(f"- `{command}`" for command in result["next_commands"])
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process first-wave RFQ confirmations and replies.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    commands = [run_command(item) for item in COMMANDS]
    result = build_result(commands)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"First-wave post-dispatch processing: {result['status']}")
    print(f"Failed commands: {len(result['failed_command_ids'])}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0 if not result["failed_command_ids"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
