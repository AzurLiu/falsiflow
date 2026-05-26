#!/usr/bin/env python3
"""Run a smoke-only LIMINA capture rehearsal without touching active evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREFLIGHT = ROOT / "data" / "limina_smoke_capture_preflight.json"
DEFAULT_JSON = ROOT / "data" / "limina_smoke_rehearsal.json"
DEFAULT_REPORT = ROOT / "reports" / "limina_smoke_rehearsal.md"
DEFAULT_WORKDIR = ROOT / "data" / "smoke_rehearsal"
DEFAULT_REPORT_DIR = ROOT / "reports" / "smoke_rehearsal"


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


def run_command(command_id: str, argv: list[str]) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, *argv],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "id": command_id,
        "argv": argv,
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def tail(text: str, limit: int = 6) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines[-limit:])


def rehearsal_commands(workdir: Path, report_dir: Path) -> list[tuple[str, list[str]]]:
    h_a_runs = workdir / "nhi_pedot_h_a_smoke_runs.csv"
    h_a_local_merge_json = workdir / "nhi_pedot_h_a_smoke_local_merge.json"
    h_a_outsource_merge_json = workdir / "nhi_pedot_h_a_smoke_outsource_merge.json"
    zrc_runs = workdir / "zrc_nd_phase_a_smoke_runs.csv"
    zrc_local_merge_json = workdir / "zrc_nd_phase_a_smoke_local_merge.json"
    zrc_outsource_merge_json = workdir / "zrc_nd_phase_a_smoke_outsource_merge.json"
    return [
        (
            "merge_h_a_smoke_local",
            [
                "scripts/merge_nhi_pedot_h_a_raw_measurements.py",
                "--base",
                "data/nhi_pedot_h_a_sentinel_template.csv",
                "--raw",
                "data/nhi_pedot_h_a_smoke_local_capture_template.csv",
                "--out",
                rel(h_a_runs),
                "--json-out",
                rel(h_a_local_merge_json),
                "--report",
                rel(report_dir / "nhi_pedot_h_a_smoke_local_merge.md"),
            ],
        ),
        (
            "merge_h_a_smoke_osmolality",
            [
                "scripts/merge_nhi_pedot_h_a_raw_measurements.py",
                "--base",
                rel(h_a_runs),
                "--raw",
                "data/nhi_pedot_h_a_smoke_osmolality_outsource_template.csv",
                "--out",
                rel(h_a_runs),
                "--json-out",
                rel(h_a_outsource_merge_json),
                "--report",
                rel(report_dir / "nhi_pedot_h_a_smoke_osmolality_merge.md"),
            ],
        ),
        (
            "qc_h_a_smoke",
            [
                "scripts/qc_nhi_pedot_h_a_intake.py",
                "--runs",
                rel(h_a_runs),
                "--json-out",
                rel(workdir / "nhi_pedot_h_a_smoke_intake_qc.json"),
                "--report",
                rel(report_dir / "nhi_pedot_h_a_smoke_intake_qc.md"),
            ],
        ),
        (
            "interpret_h_a_smoke",
            [
                "scripts/interpret_nhi_pedot_h_a_sentinel.py",
                "--runs",
                rel(h_a_runs),
                "--json-out",
                rel(workdir / "nhi_pedot_h_a_smoke_sentinel_interpretation.json"),
                "--report",
                rel(report_dir / "nhi_pedot_h_a_smoke_sentinel_interpretation.md"),
            ],
        ),
        (
            "merge_zrc_smoke_local",
            [
                "scripts/merge_zrc_nd_measurements.py",
                "--base",
                "data/zrc_nd_validation_runs_template.csv",
                "--measurements",
                "data/zrc_nd_phase_a_smoke_local_capture_template.csv",
                "--out",
                rel(zrc_runs),
                "--json-out",
                rel(zrc_local_merge_json),
                "--report",
                rel(report_dir / "zrc_nd_phase_a_smoke_local_merge.md"),
            ],
        ),
        (
            "merge_zrc_smoke_osmolality",
            [
                "scripts/merge_zrc_nd_measurements.py",
                "--base",
                rel(zrc_runs),
                "--measurements",
                "data/zrc_nd_phase_a_smoke_osmolality_outsource_template.csv",
                "--out",
                rel(zrc_runs),
                "--json-out",
                rel(zrc_outsource_merge_json),
                "--report",
                rel(report_dir / "zrc_nd_phase_a_smoke_osmolality_merge.md"),
            ],
        ),
        (
            "check_zrc_smoke_completeness",
            [
                "scripts/check_zrc_nd_run_completeness.py",
                "--runs",
                rel(zrc_runs),
                "--json-out",
                rel(workdir / "zrc_nd_phase_a_smoke_run_completeness.json"),
                "--report",
                rel(report_dir / "zrc_nd_phase_a_smoke_run_completeness.md"),
            ],
        ),
        (
            "interpret_zrc_smoke",
            [
                "scripts/interpret_zrc_nd_sentinel.py",
                "--runs",
                rel(zrc_runs),
                "--json-out",
                rel(workdir / "zrc_nd_phase_a_smoke_sentinel_interpretation.json"),
                "--report",
                rel(report_dir / "zrc_nd_phase_a_smoke_sentinel_interpretation.md"),
            ],
        ),
        (
            "evaluate_zrc_smoke",
            [
                "scripts/evaluate_zrc_nd_validation_runs.py",
                "--runs",
                rel(zrc_runs),
                "--results",
                rel(workdir / "zrc_nd_phase_a_smoke_validation_results.json"),
                "--report",
                rel(report_dir / "zrc_nd_phase_a_smoke_validation_results.md"),
            ],
        ),
    ]


def build_rehearsal(args: argparse.Namespace) -> dict[str, Any]:
    preflight = load_json(args.preflight)
    args.workdir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    preflight_status = preflight.get("status", "missing_preflight")
    preflight_ready = bool(preflight.get("preflight_ready"))
    if not preflight_ready:
        return {
            "status": "smoke_rehearsal_waiting_for_preflight",
            "preflight_status": preflight_status,
            "preflight_ready": False,
            "filled_task_count": preflight.get("filled_task_count", 0),
            "pending_task_count": preflight.get("pending_task_count", 0),
            "issue_counts": preflight.get("issue_counts", {}),
            "commands": [],
            "generated_artifacts": {},
            "boundary": "No smoke merge rehearsal was run because the smoke capture preflight is not ready.",
        }

    commands = []
    for command_id, argv in rehearsal_commands(args.workdir, args.report_dir):
        outcome = run_command(command_id, argv)
        commands.append(outcome)
        if outcome["returncode"] != 0:
            break

    failed = [item for item in commands if item["returncode"] != 0]
    h_a_qc = load_json(args.workdir / "nhi_pedot_h_a_smoke_intake_qc.json")
    h_a_interpretation = load_json(args.workdir / "nhi_pedot_h_a_smoke_sentinel_interpretation.json")
    zrc_completeness = load_json(args.workdir / "zrc_nd_phase_a_smoke_run_completeness.json")
    zrc_interpretation = load_json(args.workdir / "zrc_nd_phase_a_smoke_sentinel_interpretation.json")
    zrc_results = load_json(args.workdir / "zrc_nd_phase_a_smoke_validation_results.json")
    zrc_summary = zrc_results.get("summary", {})

    if failed:
        status = "smoke_rehearsal_failed"
    else:
        status = "smoke_rehearsal_completed_not_claim_evidence"

    return {
        "status": status,
        "preflight_status": preflight_status,
        "preflight_ready": True,
        "filled_task_count": preflight.get("filled_task_count", 0),
        "pending_task_count": preflight.get("pending_task_count", 0),
        "issue_counts": preflight.get("issue_counts", {}),
        "commands": commands,
        "h_a_qc_status": h_a_qc.get("status", "unknown"),
        "h_a_qc_intake_ready": bool(h_a_qc.get("intake_ready")),
        "h_a_interpretation_status": h_a_interpretation.get("status", "unknown"),
        "zrc_completeness_status": zrc_completeness.get("status", "unknown"),
        "zrc_interpretation_status": zrc_interpretation.get("status", "unknown"),
        "zrc_validation_status": zrc_summary.get("status", "unknown"),
        "generated_artifacts": {
            "h_a_smoke_runs": rel(args.workdir / "nhi_pedot_h_a_smoke_runs.csv"),
            "zrc_smoke_runs": rel(args.workdir / "zrc_nd_phase_a_smoke_runs.csv"),
            "h_a_qc_report": rel(args.report_dir / "nhi_pedot_h_a_smoke_intake_qc.md"),
            "h_a_interpretation_report": rel(args.report_dir / "nhi_pedot_h_a_smoke_sentinel_interpretation.md"),
            "zrc_completeness_report": rel(args.report_dir / "zrc_nd_phase_a_smoke_run_completeness.md"),
            "zrc_interpretation_report": rel(args.report_dir / "zrc_nd_phase_a_smoke_sentinel_interpretation.md"),
            "zrc_validation_report": rel(args.report_dir / "zrc_nd_phase_a_smoke_validation_results.md"),
        },
        "boundary": "Smoke rehearsal outputs are temporary pipeline checks. They do not write active evidence tables and cannot support a suitability claim.",
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIMINA Smoke Rehearsal",
        "",
        "This runs a smoke-only merge/QC/evaluation rehearsal after smoke preflight is ready. It is not a material suitability claim.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Preflight status:** `{result['preflight_status']}`",
        f"**Preflight ready:** `{result['preflight_ready']}`",
        f"**Filled tasks:** {result['filled_task_count']}",
        f"**Pending tasks:** {result['pending_task_count']}",
        f"**Errors:** {result.get('issue_counts', {}).get('error', 0)}",
        f"**Warnings:** {result.get('issue_counts', {}).get('warning', 0)}",
        "",
    ]
    if not result.get("commands"):
        lines.extend([
            "## Rehearsal",
            "",
            "- Merge/QC/evaluation commands were not run because smoke preflight is not ready.",
            "",
            "## Boundary",
            "",
            result["boundary"],
            "",
        ])
        return "\n".join(lines)

    lines.extend([
        "## Smoke Gate Outputs",
        "",
        f"- H-A QC: `{result.get('h_a_qc_status', '-')}`; intake_ready={str(result.get('h_a_qc_intake_ready', False)).lower()}",
        f"- H-A interpretation: `{result.get('h_a_interpretation_status', '-')}`",
        f"- ZRC completeness: `{result.get('zrc_completeness_status', '-')}`",
        f"- ZRC sentinel: `{result.get('zrc_interpretation_status', '-')}`",
        f"- ZRC validation: `{result.get('zrc_validation_status', '-')}`",
        "",
        "## Generated Artifacts",
        "",
        "| Artifact | Path |",
        "| --- | --- |",
    ])
    for name, path in result.get("generated_artifacts", {}).items():
        lines.append(f"| `{name}` | `{path}` |")

    lines.extend([
        "",
        "## Commands",
        "",
        "| Command | Return | Seconds |",
        "| --- | ---: | ---: |",
    ])
    for item in result["commands"]:
        lines.append(f"| `{item['id']}` | {item['returncode']} | {item['elapsed_seconds']:.3f} |")

    lines.extend(["", "## Command Output Tail", ""])
    for item in result["commands"]:
        output = tail("\n".join(part for part in [item["stdout"], item["stderr"]] if part))
        if not output:
            continue
        lines.extend([f"### {item['id']}", "", "```text", output, "```", ""])
    lines.extend(["## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run LIMINA smoke-only merge/QC/evaluation rehearsal.")
    parser.add_argument("--preflight", type=Path, default=DEFAULT_PREFLIGHT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--workdir", type=Path, default=DEFAULT_WORKDIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_rehearsal(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"Smoke rehearsal: {result['status']}")
    print(f"Preflight: {result['preflight_status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
