#!/usr/bin/env python3
"""Render a local cockpit for manually sending ZRC-ND Phase A RFQ text files."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DISPATCH_MANIFEST = ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_manifest.json"
DEFAULT_DISPATCH_ARCHIVE = ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_archive_manifest.json"
DEFAULT_REPLY_ACTION_PACK = ROOT / "data" / "zrc_nd_phase_a_rfq_reply_action_pack.json"
DEFAULT_REPLY_ACTION_QUEUE = ROOT / "data" / "zrc_nd_phase_a_rfq_reply_action_queue.csv"
DEFAULT_SEND_LOG = ROOT / "data" / "zrc_nd_phase_a_rfq_send_log.csv"
DEFAULT_REPLY_LOG = ROOT / "data" / "zrc_nd_phase_a_rfq_reply_log.csv"
DEFAULT_SEND_CONFIRMATION_INTAKE = ROOT / "data" / "zrc_nd_phase_a_rfq_send_confirmation_intake.json"
DEFAULT_SEND_CONFIRMATION_ENTRY_SHEET = ROOT / "data" / "zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.json"
DEFAULT_SEND_CONFIRMATION_ENTRY_APPLY = ROOT / "data" / "zrc_nd_phase_a_rfq_send_confirmation_entry_apply.json"
DEFAULT_REPLY_INTAKE = ROOT / "data" / "zrc_nd_phase_a_rfq_reply_intake.json"
DEFAULT_JSON = ROOT / "data" / "zrc_nd_phase_a_rfq_send_cockpit.json"
DEFAULT_REPORT = ROOT / "reports" / "zrc_nd_phase_a_rfq_send_cockpit.md"
DEFAULT_HTML = ROOT / "reports" / "zrc_nd_phase_a_rfq_send_cockpit.html"

SENT_STATUSES = {"sent", "submitted", "emailed", "form_submitted"}


def clean(value: Any) -> str:
    return str(value or "").strip()


def normalize(value: str) -> str:
    return clean(value).lower().replace(" ", "_").replace("-", "_")


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


def workspace_path(raw: str) -> Path:
    path = Path(clean(raw))
    return path if path.is_absolute() else ROOT / path


def file_exists(raw: str) -> bool:
    return bool(clean(raw)) and workspace_path(raw).is_file()


def file_href(raw: str) -> str:
    if not clean(raw):
        return ""
    return workspace_path(raw).resolve().as_uri()


def by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("candidate_id")): row for row in rows if clean(row.get("candidate_id"))}


def send_status_for(manifest_row: dict[str, Any], send_row: dict[str, str]) -> str:
    raw_status = normalize(send_row.get("send_status", ""))
    if raw_status in SENT_STATUSES:
        if clean(send_row.get("computed_send_confirmation_source_sha256")):
            return "sent_confirmation_verified"
        return "sent_needs_confirmation_file"
    dispatch_status = clean(manifest_row.get("dispatch_status"))
    if dispatch_status == "ready_for_manual_dispatch":
        return "ready_for_manual_dispatch"
    return dispatch_status or "not_ready"


def next_action_for(row: dict[str, Any]) -> str:
    status = row["send_action_status"]
    if status == "ready_for_manual_dispatch":
        return "Open the email text, send or paste it through the listed recipient/form with the exact bundle, then save a real confirmation file."
    if status == "sent_needs_confirmation_file":
        return "Save the original confirmation at the listed path, rerun send-confirmation intake, then apply the send log."
    if status == "sent_confirmation_verified":
        return "Wait for a source-backed vendor reply, save it, then run RFQ reply intake."
    return "Resolve dispatch blockers before sending this RFQ."


def build_rows(
    manifest_rows: list[dict[str, Any]],
    send_rows: list[dict[str, str]],
    reply_rows: list[dict[str, str]],
    reply_action_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    send_by_id = by_candidate(send_rows)
    reply_by_id = by_candidate(reply_rows)
    reply_action_by_id = by_candidate(reply_action_rows)
    rows: list[dict[str, Any]] = []
    for manifest_row in manifest_rows:
        candidate_id = clean(manifest_row.get("candidate_id"))
        send_row = send_by_id.get(candidate_id, {})
        reply_row = reply_by_id.get(candidate_id, {})
        reply_action = reply_action_by_id.get(candidate_id, {})
        email_file = clean(manifest_row.get("email_file"))
        bundle_zip = clean(manifest_row.get("bundle_zip"))
        confirmation_file = clean(send_row.get("send_confirmation_source_file")) or clean(manifest_row.get("confirmation_source_file_to_save"))
        reply_file = clean(reply_row.get("reply_source_file")) or clean(reply_action.get("reply_source_file_to_save"))
        row = {
            "dispatch_order": manifest_row.get("dispatch_order", len(rows) + 1),
            "candidate_id": candidate_id,
            "vendor_name": clean(manifest_row.get("vendor_name")),
            "send_action_status": send_status_for(manifest_row, send_row),
            "dispatch_status": clean(manifest_row.get("dispatch_status")),
            "reply_action_status": clean(reply_action.get("reply_action_status")),
            "send_log_status": clean(send_row.get("send_status")) or "missing_send_log_row",
            "reply_log_status": clean(reply_row.get("reply_status")) or "missing_reply_log_row",
            "primary_send_method": clean(manifest_row.get("primary_send_method")) or clean(send_row.get("send_method")),
            "recipient_or_form": clean(manifest_row.get("recipient_or_form")) or clean(send_row.get("recipient_or_form")),
            "contact_url": clean(manifest_row.get("contact_url")),
            "quote_url": clean(manifest_row.get("quote_url")),
            "email_file": email_file,
            "email_exists": file_exists(email_file),
            "bundle_zip": bundle_zip,
            "bundle_exists": file_exists(bundle_zip),
            "bundle_sha256": clean(manifest_row.get("bundle_sha256_expected")) or clean(send_row.get("expected_bundle_sha256")),
            "bundle_sha256_match": clean(manifest_row.get("bundle_sha256_match")),
            "attachment_count": clean(manifest_row.get("attachment_count")),
            "confirmation_source_file_to_save": confirmation_file,
            "confirmation_file_exists": file_exists(confirmation_file),
            "confirmation_template": clean(manifest_row.get("confirmation_template")),
            "reply_source_file_to_save": reply_file,
            "reply_file_exists": file_exists(reply_file),
            "reply_template": clean(reply_action.get("reply_template")),
            "manual_dispatch_step": clean(manifest_row.get("manual_dispatch_step")),
            "next_action": "",
        }
        row["next_action"] = next_action_for(row)
        rows.append(row)
    return rows


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    dispatch_manifest = load_json(args.dispatch_manifest)
    dispatch_archive = load_json(args.dispatch_archive)
    reply_action_pack = load_json(args.reply_action_pack)
    send_confirmation_intake = load_json(args.send_confirmation_intake)
    send_confirmation_entry_sheet = load_json(args.send_confirmation_entry_sheet)
    send_confirmation_entry_apply = load_json(args.send_confirmation_entry_apply)
    reply_intake = load_json(args.reply_intake)
    rows = build_rows(
        dispatch_manifest.get("rows", []),
        load_csv(args.send_log),
        load_csv(args.reply_log),
        load_csv(args.reply_action_queue),
    )

    ready_to_use = [
        row for row in rows
        if row["send_action_status"] == "ready_for_manual_dispatch"
        and row["email_exists"]
        and row["bundle_exists"]
    ]
    missing_email = sum(1 for row in rows if row["send_action_status"] == "ready_for_manual_dispatch" and not row["email_exists"])
    missing_bundle = sum(1 for row in rows if row["send_action_status"] == "ready_for_manual_dispatch" and not row["bundle_exists"])
    confirmation_files = sum(1 for row in rows if row["confirmation_file_exists"])
    reply_files = sum(1 for row in rows if row["reply_file_exists"])
    verified = sum(1 for row in rows if row["send_action_status"] == "sent_confirmation_verified")
    dispatch_ready = sum(1 for row in rows if row["dispatch_status"] == "ready_for_manual_dispatch")
    dispatch_blocked = sum(1 for row in rows if row["dispatch_status"] != "ready_for_manual_dispatch")

    if not rows:
        status = "zrc_phase_a_rfq_send_cockpit_no_rows"
    elif missing_email or missing_bundle:
        status = "zrc_phase_a_rfq_send_cockpit_missing_local_files"
    elif confirmation_files:
        status = "zrc_phase_a_rfq_send_cockpit_has_confirmation_files"
    elif ready_to_use:
        status = "zrc_phase_a_rfq_send_cockpit_ready_for_manual_send"
    else:
        status = "zrc_phase_a_rfq_send_cockpit_waiting_for_context"

    archive_summary = dispatch_archive.get("summary", {})
    reply_action_summary = reply_action_pack.get("summary", {})
    entry_sheet_summary = send_confirmation_entry_sheet.get("summary", {})
    entry_apply_summary = send_confirmation_entry_apply.get("summary", {})
    return {
        "status": status,
        "purpose": "Single local handoff surface for manually sending first-wave ZRC-ND Phase A RFQs and preserving source confirmations/replies.",
        "summary": {
            "vendor_rows": len(rows),
            "ready_to_use_rows": len(ready_to_use),
            "missing_email_rows": missing_email,
            "missing_bundle_rows": missing_bundle,
            "confirmation_files_present": confirmation_files,
            "reply_files_present": reply_files,
            "sent_confirmation_verified_rows": verified,
            "dispatch_manifest_status": dispatch_manifest.get("status", "unknown"),
            "dispatch_manifest_ready_rows": dispatch_ready,
            "dispatch_manifest_blocked_rows": dispatch_blocked,
            "dispatch_archive_status": dispatch_archive.get("status", "unknown"),
            "dispatch_archive_path": dispatch_archive.get("generated_artifacts", {}).get("archive", ""),
            "dispatch_archive_sha256": archive_summary.get("archive_sha256", ""),
            "send_confirmation_intake_status": send_confirmation_intake.get("status", "unknown"),
            "send_confirmation_intake_files": send_confirmation_intake.get("row_count", 0),
            "send_confirmation_entry_sheet_status": send_confirmation_entry_sheet.get("status", "unknown"),
            "send_confirmation_entry_sheet_rows": entry_sheet_summary.get("entry_rows", 0),
            "send_confirmation_entry_sheet_ready_rows": entry_sheet_summary.get("ready_to_apply_rows", 0),
            "send_confirmation_entry_sheet_blocked_rows": entry_sheet_summary.get("blocked_rows", 0),
            "send_confirmation_entry_apply_status": send_confirmation_entry_apply.get("status", "unknown"),
            "send_confirmation_entry_apply_rows": entry_apply_summary.get("apply_rows", 0),
            "send_confirmation_entry_apply_applied_rows": entry_apply_summary.get("applied_rows", 0),
            "send_confirmation_entry_apply_blocked_rows": entry_apply_summary.get("blocked_rows", 0),
            "reply_intake_status": reply_intake.get("status", "unknown"),
            "reply_intake_files": reply_intake.get("row_count", 0),
            "reply_action_pack_status": reply_action_pack.get("status", "unknown"),
            "reply_action_waiting_for_send_rows": reply_action_summary.get("waiting_for_send_rows", 0),
            "reply_action_awaiting_reply_rows": reply_action_summary.get("awaiting_reply_rows", 0),
            "reply_action_ready_apply_rows": reply_action_summary.get("ready_for_reply_log_apply_rows", 0),
        },
        "inputs": {
            "dispatch_manifest": rel(args.dispatch_manifest),
            "dispatch_archive": rel(args.dispatch_archive),
            "reply_action_pack": rel(args.reply_action_pack),
            "reply_action_queue": rel(args.reply_action_queue),
            "send_log": rel(args.send_log),
            "reply_log": rel(args.reply_log),
            "send_confirmation_intake": rel(args.send_confirmation_intake),
            "send_confirmation_entry_sheet": rel(args.send_confirmation_entry_sheet),
            "send_confirmation_entry_apply": rel(args.send_confirmation_entry_apply),
            "reply_intake": rel(args.reply_intake),
        },
        "generated_artifacts": {
            "json": rel(args.json_out),
            "report": rel(args.report),
            "html": rel(args.html_out),
        },
        "rows": rows,
        "next_commands": [
            "python3 scripts/intake_limina_rfq_send_confirmations.py --profile zrc_phase_a",
            "python3 scripts/render_zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.py",
            "python3 scripts/apply_zrc_nd_phase_a_rfq_send_confirmation_entry_sheet.py",
            "python3 scripts/apply_limina_rfq_send_log.py --profile zrc_phase_a",
            "python3 scripts/intake_limina_rfq_replies.py --profile zrc_phase_a",
            "python3 scripts/apply_limina_rfq_reply_log.py --profile zrc_phase_a",
            "python3 scripts/evaluate_zrc_nd_phase_a_quote_replies.py",
            "python3 scripts/run_limina_iteration.py",
        ],
        "boundary": (
            "This cockpit is logistics scaffolding only. It does not send email, create measurement evidence, "
            "select a provider, authorize execution, or advance material suitability gates."
        ),
    }


def md_link(path: str) -> str:
    return f"`{path}`" if clean(path) else "-"


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# ZRC-ND Phase A RFQ Send Cockpit",
        "",
        "This cockpit collects the files needed for manual first-wave ZRC-ND Phase A RFQ dispatch. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Vendor rows:** {summary['vendor_rows']}",
        f"**Ready to use:** {summary['ready_to_use_rows']}",
        f"**Missing email text:** {summary['missing_email_rows']}",
        f"**Missing bundles:** {summary['missing_bundle_rows']}",
        f"**Dispatch manifest:** `{summary['dispatch_manifest_status']}`; ready={summary['dispatch_manifest_ready_rows']}; blocked={summary['dispatch_manifest_blocked_rows']}",
        f"**Dispatch archive:** `{summary['dispatch_archive_status']}`; archive=`{summary['dispatch_archive_path']}`; sha256=`{summary['dispatch_archive_sha256']}`",
        f"**Confirmation files present:** {summary['confirmation_files_present']}",
        f"**Reply files present:** {summary['reply_files_present']}",
        f"**Confirmation entry sheet:** `{summary['send_confirmation_entry_sheet_status']}`; rows={summary['send_confirmation_entry_sheet_rows']}; ready={summary['send_confirmation_entry_sheet_ready_rows']}; blocked={summary['send_confirmation_entry_sheet_blocked_rows']}",
        f"**Confirmation entry apply:** `{summary['send_confirmation_entry_apply_status']}`; apply_rows={summary['send_confirmation_entry_apply_rows']}; applied={summary['send_confirmation_entry_apply_applied_rows']}; blocked={summary['send_confirmation_entry_apply_blocked_rows']}",
        f"**Reply action pack:** `{summary['reply_action_pack_status']}`; waiting_send={summary['reply_action_waiting_for_send_rows']}; awaiting_reply={summary['reply_action_awaiting_reply_rows']}; ready_apply={summary['reply_action_ready_apply_rows']}",
        f"**HTML:** `{result['generated_artifacts']['html']}`",
        "",
        "## Send Rows",
        "",
        "| Order | Vendor | Status | Dispatch | Reply action | Recipient/Form | Email | Bundle | Confirmation | Reply file |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['dispatch_order']} | {row['vendor_name']} | `{row['send_action_status']}` | "
            f"`{row['dispatch_status']}` | `{row['reply_action_status']}` | `{row['recipient_or_form']}` | "
            f"{md_link(row['email_file'])} | {md_link(row['bundle_zip'])} | "
            f"{md_link(row['confirmation_source_file_to_save'])} | {md_link(row['reply_source_file_to_save'])} |"
        )
    lines.extend(["", "## Commands After Saving Real Files", ""])
    lines.extend(f"- `{command}`" for command in result["next_commands"])
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def link_html(path: str, label: str) -> str:
    if not clean(path):
        return '<span class="muted">-</span>'
    return f'<a class="link" href="{html.escape(file_href(path), quote=True)}">{html.escape(label)}</a>'


def copy_button(value: str, label: str = "Copy") -> str:
    if not clean(value):
        return ""
    return (
        f'<button type="button" class="copy" data-copy="{html.escape(value, quote=True)}">'
        f"{html.escape(label)}</button>"
    )


def badge(value: str) -> str:
    token = clean(value) or "unknown"
    css = "badge"
    if token in {"ready_for_manual_dispatch", "zrc_phase_a_rfq_send_cockpit_ready_for_manual_send"}:
        css += " ready"
    elif "waiting" in token or "pending" in token or "awaiting" in token:
        css += " wait"
    elif "missing" in token or "error" in token or "blocked" in token or "needs" in token:
        css += " warn"
    elif "verified" in token or "applied" in token:
        css += " done"
    return f'<span class="{css}">{html.escape(token)}</span>'


def path_block(path: str) -> str:
    if not clean(path):
        return '<span class="muted">-</span>'
    return f'<code>{html.escape(path)}</code>{copy_button(path)}'


def render_html(result: dict[str, Any]) -> str:
    summary = result["summary"]
    row_blocks = []
    for row in result["rows"]:
        contact = link_html(row["contact_url"], "Contact") if row["contact_url"] else ""
        quote = link_html(row["quote_url"], "Quote") if row["quote_url"] and row["quote_url"] != row["contact_url"] else ""
        row_blocks.append(f"""
        <section class="vendor">
          <div class="vendor-head">
            <div>
              <div class="order">#{html.escape(str(row['dispatch_order']))}</div>
              <h2>{html.escape(row['vendor_name'])}</h2>
            </div>
            <div class="status-stack">
              {badge(row['send_action_status'])}
              {badge(row['dispatch_status'])}
              {badge(row['reply_action_status'])}
            </div>
          </div>
          <div class="grid">
            <div class="field"><span>Recipient/Form</span><strong>{html.escape(row['recipient_or_form'])}</strong>{copy_button(row['recipient_or_form'])}</div>
            <div class="field"><span>Contact</span><strong>{contact} {quote}</strong></div>
            <div class="field"><span>Email Text</span><strong>{link_html(row['email_file'], "Open email")}</strong>{path_block(row['email_file'])}<small>{'exists' if row['email_exists'] else 'missing'}</small></div>
            <div class="field"><span>Bundle</span><strong>{link_html(row['bundle_zip'], "Open bundle")}</strong>{path_block(row['bundle_zip'])}<small>{'exists' if row['bundle_exists'] else 'missing'}</small></div>
            <div class="field"><span>Bundle SHA-256</span>{path_block(row['bundle_sha256'])}<small>manifest match: {html.escape(row['bundle_sha256_match'] or 'unknown')}</small></div>
            <div class="field"><span>Save Confirmation To</span>{path_block(row['confirmation_source_file_to_save'])}<small>{'present' if row['confirmation_file_exists'] else 'awaiting real file'}</small></div>
            <div class="field"><span>Confirmation Template</span><strong>{link_html(row['confirmation_template'], "Open template")}</strong>{path_block(row['confirmation_template'])}</div>
            <div class="field"><span>Save Reply To</span>{path_block(row['reply_source_file_to_save'])}<small>{'present' if row['reply_file_exists'] else 'awaiting reply'}</small></div>
          </div>
          <p class="next">{html.escape(row['next_action'])}</p>
        </section>
        """)
    commands = "\n".join(
        f'<li><code>{html.escape(command)}</code>{copy_button(command)}</li>'
        for command in result["next_commands"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ZRC-ND Phase A RFQ Send Cockpit</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #17202c;
      --muted: #667085;
      --line: #d7dde6;
      --accent: #116d77;
      --good: #16724a;
      --wait: #785d14;
      --warn: #a33f31;
      --shadow: 0 1px 2px rgba(16, 24, 40, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      padding: 24px 28px 14px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 26px;
      line-height: 1.15;
      font-weight: 700;
      letter-spacing: 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
      gap: 10px;
      padding: 14px 28px;
      border-bottom: 1px solid var(--line);
      background: #edf3f4;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      box-shadow: var(--shadow);
      min-height: 68px;
    }}
    .metric span, .field span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 4px;
    }}
    .metric strong {{
      font-size: 22px;
      line-height: 1.1;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 18px 20px 36px;
    }}
    .vendor, .commands {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 16px;
      margin-bottom: 14px;
    }}
    .vendor-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 12px;
      margin-bottom: 12px;
    }}
    .order {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 3px;
    }}
    h2 {{
      margin: 0;
      font-size: 18px;
      line-height: 1.25;
      letter-spacing: 0;
    }}
    .status-stack {{
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 6px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 6px;
      padding: 3px 8px;
      border: 1px solid var(--line);
      background: #f2f4f7;
      color: var(--ink);
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .badge.ready {{ background: #e7f5f2; border-color: #b6ded5; color: var(--accent); }}
    .badge.wait {{ background: #fff7df; border-color: #ecd68b; color: var(--wait); }}
    .badge.warn {{ background: #fff0ed; border-color: #f1b3a8; color: var(--warn); }}
    .badge.done {{ background: #e9f6ef; border-color: #b8dfca; color: var(--good); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .field {{
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fbfcfd;
    }}
    .field strong {{
      display: block;
      min-height: 24px;
      font-size: 14px;
      overflow-wrap: anywhere;
    }}
    .field small {{
      display: block;
      margin-top: 6px;
      color: var(--muted);
      font-weight: 600;
    }}
    code {{
      display: block;
      max-width: 100%;
      margin: 6px 0 0;
      color: #263343;
      background: #eef1f5;
      border: 1px solid #dde3ea;
      border-radius: 6px;
      padding: 6px;
      font: 12px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      overflow-wrap: anywhere;
    }}
    .link {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 700;
    }}
    .link:hover {{ text-decoration: underline; }}
    button.copy {{
      margin-top: 7px;
      min-height: 28px;
      border: 1px solid #b9c2cf;
      border-radius: 6px;
      background: #ffffff;
      color: #2a3545;
      font: 12px/1 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-weight: 700;
      padding: 0 9px;
      cursor: pointer;
    }}
    button.copy:hover {{ border-color: var(--accent); color: var(--accent); }}
    .next {{
      margin: 12px 0 0;
      color: #334155;
      font-weight: 600;
    }}
    .commands h2 {{ margin-bottom: 8px; }}
    .commands ol {{
      margin: 0;
      padding-left: 22px;
    }}
    .commands li {{ margin: 8px 0; }}
    .muted {{ color: var(--muted); }}
    @media (max-width: 1000px) {{
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 650px) {{
      header {{ padding: 20px 16px 12px; }}
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); padding: 12px 16px; }}
      main {{ padding: 14px 12px 28px; }}
      .vendor-head {{ display: block; }}
      .status-stack {{ justify-content: flex-start; margin-top: 10px; }}
      .grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 22px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>ZRC-ND Phase A RFQ Send Cockpit</h1>
    {badge(result['status'])}
  </header>
  <section class="summary" aria-label="Summary">
    <div class="metric"><span>Vendors</span><strong>{summary['vendor_rows']}</strong></div>
    <div class="metric"><span>Ready to use</span><strong>{summary['ready_to_use_rows']}</strong></div>
    <div class="metric"><span>Confirmations</span><strong>{summary['confirmation_files_present']}</strong></div>
    <div class="metric"><span>Replies</span><strong>{summary['reply_files_present']}</strong></div>
    <div class="metric"><span>Dispatch ready</span><strong>{summary['dispatch_manifest_ready_rows']}</strong></div>
    <div class="metric"><span>Awaiting replies</span><strong>{summary['reply_action_awaiting_reply_rows']}</strong></div>
    <div class="metric"><span>Missing email</span><strong>{summary['missing_email_rows']}</strong></div>
    <div class="metric"><span>Missing bundles</span><strong>{summary['missing_bundle_rows']}</strong></div>
  </section>
  <main>
    {''.join(row_blocks)}
    <section class="commands">
      <h2>Commands After Saving Real Files</h2>
      <ol>{commands}</ol>
    </section>
    <p class="muted">{html.escape(result['boundary'])}</p>
  </main>
  <script>
    document.addEventListener('click', async (event) => {{
      const button = event.target.closest('[data-copy]');
      if (!button) return;
      try {{
        await navigator.clipboard.writeText(button.dataset.copy);
        const oldText = button.textContent;
        button.textContent = 'Copied';
        setTimeout(() => {{ button.textContent = oldText; }}, 900);
      }} catch (error) {{
        button.textContent = 'Copy failed';
      }}
    }});
  </script>
</body>
</html>
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render ZRC-ND Phase A RFQ send cockpit.")
    parser.add_argument("--dispatch-manifest", type=Path, default=DEFAULT_DISPATCH_MANIFEST)
    parser.add_argument("--dispatch-archive", type=Path, default=DEFAULT_DISPATCH_ARCHIVE)
    parser.add_argument("--reply-action-pack", type=Path, default=DEFAULT_REPLY_ACTION_PACK)
    parser.add_argument("--reply-action-queue", type=Path, default=DEFAULT_REPLY_ACTION_QUEUE)
    parser.add_argument("--send-log", type=Path, default=DEFAULT_SEND_LOG)
    parser.add_argument("--reply-log", type=Path, default=DEFAULT_REPLY_LOG)
    parser.add_argument("--send-confirmation-intake", type=Path, default=DEFAULT_SEND_CONFIRMATION_INTAKE)
    parser.add_argument("--send-confirmation-entry-sheet", type=Path, default=DEFAULT_SEND_CONFIRMATION_ENTRY_SHEET)
    parser.add_argument("--send-confirmation-entry-apply", type=Path, default=DEFAULT_SEND_CONFIRMATION_ENTRY_APPLY)
    parser.add_argument("--reply-intake", type=Path, default=DEFAULT_REPLY_INTAKE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--html-out", type=Path, default=DEFAULT_HTML)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_result(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    args.html_out.parent.mkdir(parents=True, exist_ok=True)
    args.html_out.write_text(render_html(result), encoding="utf-8")
    print(f"ZRC-ND Phase A RFQ send cockpit: {result['status']}")
    print(f"Ready to use: {result['summary']['ready_to_use_rows']} / {result['summary']['vendor_rows']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    print(f"Wrote {args.html_out}")
    return 0 if result["status"] in {"zrc_phase_a_rfq_send_cockpit_ready_for_manual_send", "zrc_phase_a_rfq_send_cockpit_has_confirmation_files"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
