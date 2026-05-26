#!/usr/bin/env python3
"""Render a minimum smoke capture tranche for the LIMINA evidence pipeline."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = ROOT / "data" / "limina_local_capture_tasks.csv"
DEFAULT_H_A_LOCAL = ROOT / "data" / "nhi_pedot_h_a_local_capture_template.csv"
DEFAULT_H_A_OUTSOURCE = ROOT / "data" / "nhi_pedot_h_a_osmolality_outsource_template.csv"
DEFAULT_ZRC_LOCAL = ROOT / "data" / "zrc_nd_phase_a_local_capture_template.csv"
DEFAULT_ZRC_OUTSOURCE = ROOT / "data" / "zrc_nd_phase_a_osmolality_outsource_template.csv"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_capture_tranche.json"
DEFAULT_TASKS_OUT = ROOT / "data" / "limina_smoke_capture_tasks.csv"
DEFAULT_H_A_LOCAL_OUT = ROOT / "data" / "nhi_pedot_h_a_smoke_local_capture_template.csv"
DEFAULT_H_A_OUTSOURCE_OUT = ROOT / "data" / "nhi_pedot_h_a_smoke_osmolality_outsource_template.csv"
DEFAULT_ZRC_LOCAL_OUT = ROOT / "data" / "zrc_nd_phase_a_smoke_local_capture_template.csv"
DEFAULT_ZRC_OUTSOURCE_OUT = ROOT / "data" / "zrc_nd_phase_a_smoke_osmolality_outsource_template.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_capture_tranche.md"

H_A_SMOKE_RUN_IDS = {
    "NHIPEDOT-H-A-no_coating_mea_control-R1-0h",
    "NHIPEDOT-H-A-no_coating_mea_control-R1-24h",
    "NHIPEDOT-H-A-hydrogel_laminin_control-R1-0h",
    "NHIPEDOT-H-A-hydrogel_laminin_control-R1-24h",
    "NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-0h",
    "NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h",
}
ZRC_SMOKE_RUN_IDS = {
    "ZRCND-A-no_module_static_control-R1-0h",
    "ZRCND-A-no_module_static_control-R1-24h",
    "ZRCND-A-lead_zrc_nd_3p5m_guard-R1-0h",
    "ZRCND-A-lead_zrc_nd_3p5m_guard-R1-24h",
}
ENTRY_FILE_REMAP = {
    "data/nhi_pedot_h_a_local_capture_template.csv": "data/nhi_pedot_h_a_smoke_local_capture_template.csv",
    "data/nhi_pedot_h_a_osmolality_outsource_template.csv": "data/nhi_pedot_h_a_smoke_osmolality_outsource_template.csv",
    "data/zrc_nd_phase_a_local_capture_template.csv": "data/zrc_nd_phase_a_smoke_local_capture_template.csv",
    "data/zrc_nd_phase_a_osmolality_outsource_template.csv": "data/zrc_nd_phase_a_smoke_osmolality_outsource_template.csv",
}
MERGE_COMMAND_REMAP = {
    "data/nhi_pedot_h_a_local_capture_template.csv": "data/nhi_pedot_h_a_smoke_local_capture_template.csv",
    "data/nhi_pedot_h_a_osmolality_outsource_template.csv": "data/nhi_pedot_h_a_smoke_osmolality_outsource_template.csv",
    "data/zrc_nd_phase_a_local_capture_template.csv": "data/zrc_nd_phase_a_smoke_local_capture_template.csv",
    "data/zrc_nd_phase_a_osmolality_outsource_template.csv": "data/zrc_nd_phase_a_smoke_osmolality_outsource_template.csv",
}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def smoke_run_ids(branch: str) -> set[str]:
    if branch == "NHI-PEDOT H-A":
        return H_A_SMOKE_RUN_IDS
    if branch == "ZRC-ND Phase A":
        return ZRC_SMOKE_RUN_IDS
    return set()


def remap_task(row: dict[str, str]) -> dict[str, str]:
    updated = dict(row)
    entry = updated.get("entry_file", "")
    if entry in ENTRY_FILE_REMAP:
        updated["entry_file"] = ENTRY_FILE_REMAP[entry]
    command = updated.get("merge_command", "")
    for old, new in MERGE_COMMAND_REMAP.items():
        command = command.replace(old, new)
    updated["merge_command"] = command
    updated["notes"] = ";".join(part for part in [updated.get("notes", ""), "smoke_tranche_not_claim_evidence"] if part)
    return updated


def filter_tasks(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = []
    for row in rows:
        branch = row.get("branch", "")
        if row.get("run_id", "") in smoke_run_ids(branch):
            selected.append(remap_task(row))
    return selected


def filter_long_rows(rows: list[dict[str, str]], run_ids: set[str]) -> list[dict[str, str]]:
    return [dict(row) for row in rows if row.get("run_id", "") in run_ids]


def filter_wide_rows(rows: list[dict[str, str]], run_ids: set[str]) -> list[dict[str, str]]:
    return [dict(row) for row in rows if row.get("run_id", "") in run_ids]


def summarize(tasks: list[dict[str, str]], h_a_local: list[dict[str, str]], h_a_out: list[dict[str, str]], zrc_local: list[dict[str, str]], zrc_out: list[dict[str, str]]) -> dict[str, Any]:
    route_counts = Counter(row.get("route", "") for row in tasks)
    branch_counts = Counter(row.get("branch", "") for row in tasks)
    return {
        "task_count": len(tasks),
        "route_counts": dict(route_counts),
        "branch_counts": dict(branch_counts),
        "h_a_smoke_run_count": len(H_A_SMOKE_RUN_IDS),
        "zrc_smoke_run_count": len(ZRC_SMOKE_RUN_IDS),
        "h_a_local_entry_rows": len(h_a_local),
        "h_a_outsource_entry_rows": len(h_a_out),
        "zrc_local_template_rows": len(zrc_local),
        "zrc_outsource_template_rows": len(zrc_out),
        "local_or_record_tasks": route_counts.get("inhouse_ready", 0) + route_counts.get("supplier_or_build_record", 0),
        "outsourced_preferred_tasks": route_counts.get("outsourced_preferred", 0),
    }


def build_tranche(args: argparse.Namespace) -> dict[str, Any]:
    task_fields, task_rows = load_csv(args.tasks)
    h_a_local_fields, h_a_local_rows = load_csv(args.h_a_local)
    h_a_out_fields, h_a_out_rows = load_csv(args.h_a_outsource)
    zrc_local_fields, zrc_local_rows = load_csv(args.zrc_local)
    zrc_out_fields, zrc_out_rows = load_csv(args.zrc_outsource)
    if not task_fields:
        raise ValueError(f"No task header found in {args.tasks}")

    tasks = filter_tasks(task_rows)
    h_a_local = filter_long_rows(h_a_local_rows, H_A_SMOKE_RUN_IDS)
    h_a_out = filter_long_rows(h_a_out_rows, H_A_SMOKE_RUN_IDS)
    zrc_local = filter_wide_rows(zrc_local_rows, ZRC_SMOKE_RUN_IDS)
    zrc_out = filter_wide_rows(zrc_out_rows, ZRC_SMOKE_RUN_IDS)

    write_csv(args.tasks_out, task_fields, tasks)
    write_csv(args.h_a_local_out, h_a_local_fields, h_a_local)
    write_csv(args.h_a_outsource_out, h_a_out_fields, h_a_out)
    write_csv(args.zrc_local_out, zrc_local_fields, zrc_local)
    write_csv(args.zrc_outsource_out, zrc_out_fields, zrc_out)

    return {
        "status": "smoke_capture_tranche_ready",
        "purpose": "Create the smallest useful real-measurement tranche for validating capture, preflight, merge, and early red-flag detection.",
        "smoke_scope": {
            "h_a_run_ids": sorted(H_A_SMOKE_RUN_IDS),
            "zrc_run_ids": sorted(ZRC_SMOKE_RUN_IDS),
            "claim_boundary": "This tranche is intentionally incomplete for H-A/ZRC suitability claims.",
        },
        "generated_artifacts": {
            "tasks": rel(args.tasks_out),
            "h_a_local_capture_template": rel(args.h_a_local_out),
            "h_a_osmolality_outsource_template": rel(args.h_a_outsource_out),
            "zrc_local_capture_template": rel(args.zrc_local_out),
            "zrc_osmolality_outsource_template": rel(args.zrc_outsource_out),
        },
        "preflight_command": (
            "python3 scripts/preflight_limina_local_capture.py "
            "--tasks data/limina_smoke_capture_tasks.csv "
            "--h-a-local data/nhi_pedot_h_a_smoke_local_capture_template.csv "
            "--h-a-outsource data/nhi_pedot_h_a_smoke_osmolality_outsource_template.csv "
            "--zrc-local data/zrc_nd_phase_a_smoke_local_capture_template.csv "
            "--zrc-outsource data/zrc_nd_phase_a_smoke_osmolality_outsource_template.csv "
            "--json-out data/limina_smoke_capture_preflight.json "
            "--report reports/limina_smoke_capture_preflight.md"
        ),
        "summary": summarize(tasks, h_a_local, h_a_out, zrc_local, zrc_out),
        "boundary": "Passing this smoke tranche only proves the data pipeline and may reveal early red flags. It cannot satisfy the final material-discovery objective.",
    }


def render_report(tranche: dict[str, Any]) -> str:
    summary = tranche["summary"]
    artifacts = tranche["generated_artifacts"]
    lines = [
        "# LIMINA Smoke Capture Tranche",
        "",
        "This is a small real-measurement tranche for pipeline rehearsal and early red flags. It is not a material suitability claim.",
        "",
        f"**Status:** `{tranche['status']}`",
        f"**Tasks:** {summary['task_count']}",
        f"**H-A smoke runs:** {summary['h_a_smoke_run_count']}",
        f"**ZRC-ND smoke runs:** {summary['zrc_smoke_run_count']}",
        f"**Local/record tasks:** {summary['local_or_record_tasks']}",
        f"**Outsource-preferred tasks:** {summary['outsourced_preferred_tasks']}",
        "",
        "## Generated Files",
        "",
        "| File | Purpose |",
        "| --- | --- |",
        f"| `{artifacts['tasks']}` | Smoke-only task table. |",
        f"| `{artifacts['h_a_local_capture_template']}` | H-A local/record smoke rows. |",
        f"| `{artifacts['h_a_osmolality_outsource_template']}` | H-A osmolality smoke rows. |",
        f"| `{artifacts['zrc_local_capture_template']}` | ZRC-ND local/record smoke rows. |",
        f"| `{artifacts['zrc_osmolality_outsource_template']}` | ZRC-ND osmolality smoke rows. |",
        "",
        "## Entry Counts",
        "",
        "| Template | Rows |",
        "| --- | ---: |",
        f"| H-A local/record long-form rows | {summary['h_a_local_entry_rows']} |",
        f"| H-A osmolality outsource rows | {summary['h_a_outsource_entry_rows']} |",
        f"| ZRC-ND local/record wide rows | {summary['zrc_local_template_rows']} |",
        f"| ZRC-ND osmolality outsource rows | {summary['zrc_outsource_template_rows']} |",
        "",
        "## Smoke Preflight",
        "",
        "```bash",
        tranche["preflight_command"],
        "```",
        "",
        "## Boundary",
        "",
        tranche["boundary"],
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA smoke capture tranche.")
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--h-a-local", type=Path, default=DEFAULT_H_A_LOCAL)
    parser.add_argument("--h-a-outsource", type=Path, default=DEFAULT_H_A_OUTSOURCE)
    parser.add_argument("--zrc-local", type=Path, default=DEFAULT_ZRC_LOCAL)
    parser.add_argument("--zrc-outsource", type=Path, default=DEFAULT_ZRC_OUTSOURCE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--tasks-out", type=Path, default=DEFAULT_TASKS_OUT)
    parser.add_argument("--h-a-local-out", type=Path, default=DEFAULT_H_A_LOCAL_OUT)
    parser.add_argument("--h-a-outsource-out", type=Path, default=DEFAULT_H_A_OUTSOURCE_OUT)
    parser.add_argument("--zrc-local-out", type=Path, default=DEFAULT_ZRC_LOCAL_OUT)
    parser.add_argument("--zrc-outsource-out", type=Path, default=DEFAULT_ZRC_OUTSOURCE_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    tranche = build_tranche(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(tranche, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(tranche), encoding="utf-8")
    print(f"Smoke capture tranche: {tranche['status']}")
    print(f"Tasks: {tranche['summary']['task_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
