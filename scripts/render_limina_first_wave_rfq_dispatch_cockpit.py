#!/usr/bin/env python3
"""Render one cockpit for first-wave H-A and ZRC RFQ dispatch."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_H_A_COCKPIT = ROOT / "data" / "nhi_pedot_h_a_rfq_send_cockpit.json"
DEFAULT_ZRC_COCKPIT = ROOT / "data" / "zrc_nd_phase_a_rfq_send_cockpit.json"
DEFAULT_H_A_ARCHIVE = ROOT / "data" / "nhi_pedot_h_a_rfq_dispatch_archive_manifest.json"
DEFAULT_ZRC_ARCHIVE = ROOT / "data" / "zrc_nd_phase_a_rfq_dispatch_archive_manifest.json"
DEFAULT_JSON = ROOT / "data" / "limina_first_wave_rfq_dispatch_cockpit.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_first_wave_rfq_dispatch_cockpit.md"
DEFAULT_HTML = ROOT / "reports" / "limina_first_wave_rfq_dispatch_cockpit.html"

READY_STATUSES = {"ready_to_send", "ready_for_manual_dispatch"}


def clean(value: Any) -> str:
    return str(value or "").strip()


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


def workspace_path(raw: str) -> Path:
    path = Path(clean(raw))
    return path if path.is_absolute() else ROOT / path


def file_exists(raw: str) -> bool:
    return bool(clean(raw)) and workspace_path(raw).is_file()


def file_href(raw: str) -> str:
    return workspace_path(raw).resolve().as_uri() if clean(raw) else ""


def pick(row: dict[str, Any], *names: str) -> str:
    for name in names:
        value = clean(row.get(name))
        if value:
            return value
    return ""


def normalize_rows(track_id: str, label: str, cockpit: dict[str, Any], archive: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(cockpit.get("rows", []), start=1):
        message_file = pick(row, "eml_draft_file", "email_file")
        message_label = "EML draft" if clean(row.get("eml_draft_file")) else "Email text"
        bundle = pick(row, "bundle_zip")
        confirmation = pick(row, "confirmation_source_file_to_save")
        reply = pick(row, "reply_source_file_to_save")
        send_status = pick(row, "send_action_status")
        dispatch_status = pick(row, "dispatch_status")
        message_exists = file_exists(message_file)
        bundle_exists = file_exists(bundle)
        ready = send_status in READY_STATUSES and dispatch_status == "ready_for_manual_dispatch" and message_exists and bundle_exists
        rows.append({
            "track_id": track_id,
            "track_label": label,
            "order": int(clean(row.get("send_order") or row.get("dispatch_order") or index) or index),
            "candidate_id": pick(row, "candidate_id"),
            "vendor_name": pick(row, "vendor_name"),
            "send_action_status": send_status,
            "dispatch_status": dispatch_status,
            "reply_action_status": pick(row, "reply_action_status"),
            "primary_send_method": pick(row, "primary_send_method"),
            "recipient_or_form": pick(row, "recipient_or_form"),
            "contact_url": pick(row, "contact_url"),
            "quote_url": pick(row, "quote_url"),
            "message_file": message_file,
            "message_label": message_label,
            "message_exists": message_exists,
            "bundle_zip": bundle,
            "bundle_exists": bundle_exists,
            "bundle_sha256": pick(row, "bundle_sha256"),
            "confirmation_source_file_to_save": confirmation,
            "confirmation_file_exists": file_exists(confirmation),
            "confirmation_template": pick(row, "confirmation_template"),
            "reply_source_file_to_save": reply,
            "reply_file_exists": file_exists(reply),
            "reply_template": pick(row, "reply_template"),
            "ready_for_manual_send": ready,
            "archive_path": archive.get("generated_artifacts", {}).get("archive", ""),
            "archive_sha256": archive.get("summary", {}).get("archive_sha256", ""),
        })
    return rows


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    h_a_cockpit = load_json(args.h_a_cockpit)
    zrc_cockpit = load_json(args.zrc_cockpit)
    h_a_archive = load_json(args.h_a_archive)
    zrc_archive = load_json(args.zrc_archive)
    rows = [
        *normalize_rows("h_a", "NHI-PEDOT H-A", h_a_cockpit, h_a_archive),
        *normalize_rows("zrc_phase_a", "ZRC-ND Phase A", zrc_cockpit, zrc_archive),
    ]
    ready_rows = [row for row in rows if row["ready_for_manual_send"]]
    missing_messages = sum(1 for row in rows if row["send_action_status"] in READY_STATUSES and not row["message_exists"])
    missing_bundles = sum(1 for row in rows if row["send_action_status"] in READY_STATUSES and not row["bundle_exists"])
    confirmation_files = sum(1 for row in rows if row["confirmation_file_exists"])
    reply_files = sum(1 for row in rows if row["reply_file_exists"])
    if not rows:
        status = "first_wave_rfq_dispatch_cockpit_no_rows"
    elif missing_messages or missing_bundles:
        status = "first_wave_rfq_dispatch_cockpit_missing_local_files"
    elif confirmation_files:
        status = "first_wave_rfq_dispatch_cockpit_has_confirmation_files"
    elif ready_rows:
        status = "first_wave_rfq_dispatch_cockpit_ready_for_manual_send"
    else:
        status = "first_wave_rfq_dispatch_cockpit_waiting_for_context"

    track_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        stats = track_counts.setdefault(row["track_id"], {"rows": 0, "ready": 0, "confirmations": 0, "replies": 0})
        stats["rows"] += 1
        stats["ready"] += int(bool(row["ready_for_manual_send"]))
        stats["confirmations"] += int(bool(row["confirmation_file_exists"]))
        stats["replies"] += int(bool(row["reply_file_exists"]))

    return {
        "status": status,
        "purpose": "Unified dispatch surface for the first H-A and ZRC RFQ sends needed to unlock real measurement evidence.",
        "summary": {
            "track_count": len(track_counts),
            "vendor_rows": len(rows),
            "ready_to_send_rows": len(ready_rows),
            "missing_message_files": missing_messages,
            "missing_bundle_files": missing_bundles,
            "confirmation_files_present": confirmation_files,
            "reply_files_present": reply_files,
            "h_a_cockpit_status": h_a_cockpit.get("status", "unknown"),
            "zrc_phase_a_cockpit_status": zrc_cockpit.get("status", "unknown"),
            "h_a_archive_status": h_a_archive.get("status", "unknown"),
            "zrc_phase_a_archive_status": zrc_archive.get("status", "unknown"),
            "track_counts": track_counts,
        },
        "inputs": {
            "h_a_cockpit": rel(args.h_a_cockpit),
            "zrc_cockpit": rel(args.zrc_cockpit),
            "h_a_archive": rel(args.h_a_archive),
            "zrc_archive": rel(args.zrc_archive),
        },
        "generated_artifacts": {
            "json": rel(args.json_out),
            "report": rel(args.report),
            "html": rel(args.html_out),
        },
        "rows": sorted(rows, key=lambda row: (row["track_id"] != "h_a", row["order"])),
        "next_commands": [
            "python3 scripts/process_limina_first_wave_post_dispatch.py",
            "python3 scripts/run_limina_iteration.py",
        ],
        "boundary": (
            "This cockpit is dispatch scaffolding only. It does not send RFQs, create send confirmations, create measurements, "
            "select providers, authorize execution, or support any material suitability claim."
        ),
    }


def md_path(path: str) -> str:
    return f"`{path}`" if clean(path) else "-"


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA First-Wave RFQ Dispatch Cockpit",
        "",
        "This report combines the H-A and ZRC Phase A RFQ send surfaces. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Tracks:** {summary['track_count']}",
        f"**Vendor rows:** {summary['vendor_rows']}",
        f"**Ready to send:** {summary['ready_to_send_rows']}",
        f"**Missing message files:** {summary['missing_message_files']}",
        f"**Missing bundles:** {summary['missing_bundle_files']}",
        f"**Confirmation files present:** {summary['confirmation_files_present']}",
        f"**Reply files present:** {summary['reply_files_present']}",
        f"**HTML:** `{result['generated_artifacts']['html']}`",
        "",
        "## Track Status",
        "",
        f"- H-A cockpit: `{summary['h_a_cockpit_status']}`; archive=`{summary['h_a_archive_status']}`",
        f"- ZRC Phase A cockpit: `{summary['zrc_phase_a_cockpit_status']}`; archive=`{summary['zrc_phase_a_archive_status']}`",
        "",
        "## Dispatch Rows",
        "",
        "| Track | Order | Vendor | Send status | Dispatch | Message | Bundle | Confirmation path | Reply path |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['track_label']} | {row['order']} | {row['vendor_name']} | `{row['send_action_status']}` | "
            f"`{row['dispatch_status']}` | {md_path(row['message_file'])} | {md_path(row['bundle_zip'])} | "
            f"{md_path(row['confirmation_source_file_to_save'])} | {md_path(row['reply_source_file_to_save'])} |"
        )
    lines.extend(["", "## Commands After Real Files Are Saved", ""])
    lines.extend(f"- `{command}`" for command in result["next_commands"])
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def link_html(path: str, label: str) -> str:
    if not clean(path):
        return '<span class="muted">-</span>'
    return f'<a href="{html.escape(file_href(path), quote=True)}">{html.escape(label)}</a>'


def path_block(path: str) -> str:
    if not clean(path):
        return '<span class="muted">-</span>'
    return (
        f'<code>{html.escape(path)}</code>'
        f'<button type="button" data-copy="{html.escape(path, quote=True)}">Copy</button>'
    )


def badge(value: str) -> str:
    token = clean(value) or "unknown"
    css = "badge"
    if "ready" in token:
        css += " ready"
    elif "missing" in token or "blocked" in token:
        css += " warn"
    elif "confirmation" in token:
        css += " wait"
    return f'<span class="{css}">{html.escape(token)}</span>'


def render_html(result: dict[str, Any]) -> str:
    summary = result["summary"]
    rows = []
    for row in result["rows"]:
        contact = link_html(row["contact_url"], "Contact") if row["contact_url"] else ""
        quote = link_html(row["quote_url"], "Quote") if row["quote_url"] and row["quote_url"] != row["contact_url"] else ""
        rows.append(f"""
        <section class="vendor">
          <div class="vendor-head">
            <div>
              <div class="track">{html.escape(row['track_label'])} #{html.escape(str(row['order']))}</div>
              <h2>{html.escape(row['vendor_name'])}</h2>
            </div>
            <div>{badge(row['send_action_status'])} {badge(row['dispatch_status'])}</div>
          </div>
          <div class="grid">
            <div><span>Recipient/Form</span><strong>{html.escape(row['recipient_or_form'])}</strong><div class="links">{contact} {quote}</div></div>
            <div><span>{html.escape(row['message_label'])}</span>{path_block(row['message_file'])}{link_html(row['message_file'], 'Open')}</div>
            <div><span>Bundle</span>{path_block(row['bundle_zip'])}{link_html(row['bundle_zip'], 'Open')}<small>{html.escape(row['bundle_sha256'])}</small></div>
            <div><span>Confirmation Save Path</span>{path_block(row['confirmation_source_file_to_save'])}</div>
            <div><span>Reply Save Path</span>{path_block(row['reply_source_file_to_save'])}</div>
            <div><span>Archive</span>{path_block(row['archive_path'])}{link_html(row['archive_path'], 'Open')}<small>{html.escape(row['archive_sha256'])}</small></div>
          </div>
        </section>
        """)
    commands = "".join(f"<li><code>{html.escape(command)}</code></li>" for command in result["next_commands"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LIMINA First-Wave RFQ Dispatch Cockpit</title>
  <style>
    :root {{ color-scheme: light; --ink:#17211d; --muted:#64706b; --line:#d8ded9; --paper:#fbfcfb; --ready:#0f6b4f; --warn:#9a4d00; --wait:#716100; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--paper); }}
    header {{ position: sticky; top: 0; z-index: 2; display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 18px 24px; border-bottom: 1px solid var(--line); background: rgba(251,252,251,.96); }}
    h1 {{ margin: 0; font-size: 20px; letter-spacing: 0; }}
    h2 {{ margin: 2px 0 0; font-size: 17px; letter-spacing: 0; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 18px 18px 36px; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1px; border-bottom: 1px solid var(--line); background: var(--line); }}
    .metric {{ background: white; padding: 14px 18px; min-width: 0; }}
    .metric span, .grid span, .track, small {{ display: block; color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }}
    .metric strong {{ font-size: 22px; }}
    .vendor {{ background: white; border: 1px solid var(--line); border-radius: 8px; margin: 14px 0; overflow: hidden; }}
    .vendor-head {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 16px; border-bottom: 1px solid var(--line); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1px; background: var(--line); }}
    .grid > div {{ background: white; padding: 13px 16px; min-width: 0; }}
    code {{ display: block; margin: 5px 0; padding: 7px 8px; border: 1px solid var(--line); border-radius: 6px; white-space: normal; overflow-wrap: anywhere; background: #f6f8f6; }}
    button {{ border: 1px solid var(--line); background: #fff; border-radius: 6px; padding: 6px 8px; cursor: pointer; }}
    a {{ color: #174f7a; display: inline-block; margin-right: 8px; }}
    .badge {{ display: inline-block; max-width: 100%; margin-left: 6px; padding: 4px 8px; border-radius: 999px; border: 1px solid var(--line); overflow-wrap: anywhere; }}
    .badge.ready {{ color: var(--ready); border-color: #9fcab7; background: #eef8f3; }}
    .badge.warn {{ color: var(--warn); border-color: #e1b47c; background: #fff7eb; }}
    .badge.wait {{ color: var(--wait); border-color: #d8cc7c; background: #fffbe5; }}
    .commands {{ border-top: 1px solid var(--line); margin-top: 24px; padding-top: 16px; }}
    .muted {{ color: var(--muted); }}
  </style>
</head>
<body>
  <header>
    <h1>LIMINA First-Wave RFQ Dispatch Cockpit</h1>
    {badge(result['status'])}
  </header>
  <section class="summary" aria-label="Summary">
    <div class="metric"><span>Tracks</span><strong>{summary['track_count']}</strong></div>
    <div class="metric"><span>Vendors</span><strong>{summary['vendor_rows']}</strong></div>
    <div class="metric"><span>Ready to send</span><strong>{summary['ready_to_send_rows']}</strong></div>
    <div class="metric"><span>Confirmations</span><strong>{summary['confirmation_files_present']}</strong></div>
    <div class="metric"><span>Replies</span><strong>{summary['reply_files_present']}</strong></div>
    <div class="metric"><span>Missing messages</span><strong>{summary['missing_message_files']}</strong></div>
    <div class="metric"><span>Missing bundles</span><strong>{summary['missing_bundle_files']}</strong></div>
  </section>
  <main>
    {''.join(rows)}
    <section class="commands">
      <h2>Commands After Real Files Are Saved</h2>
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
        const previous = button.textContent;
        button.textContent = 'Copied';
        setTimeout(() => {{ button.textContent = previous; }}, 900);
      }} catch (error) {{
        button.textContent = 'Copy failed';
      }}
    }});
  </script>
</body>
</html>
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render unified first-wave RFQ dispatch cockpit.")
    parser.add_argument("--h-a-cockpit", type=Path, default=DEFAULT_H_A_COCKPIT)
    parser.add_argument("--zrc-cockpit", type=Path, default=DEFAULT_ZRC_COCKPIT)
    parser.add_argument("--h-a-archive", type=Path, default=DEFAULT_H_A_ARCHIVE)
    parser.add_argument("--zrc-archive", type=Path, default=DEFAULT_ZRC_ARCHIVE)
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
    print(f"First-wave RFQ dispatch cockpit: {result['status']}")
    print(f"Ready to send: {result['summary']['ready_to_send_rows']} / {result['summary']['vendor_rows']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    print(f"Wrote {args.html_out}")
    return 0 if result["status"] != "first_wave_rfq_dispatch_cockpit_missing_local_files" else 2


if __name__ == "__main__":
    raise SystemExit(main())
