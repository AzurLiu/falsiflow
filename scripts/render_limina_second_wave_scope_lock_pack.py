#!/usr/bin/env python3
"""Render scope-lock tasks for ready second-wave LIMINA material candidates."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = ROOT / "data" / "limina_second_wave_candidate_queue.json"
DEFAULT_CANDIDATES = ROOT / "data" / "limina_discovery_candidates.json"
DEFAULT_JSON = ROOT / "data" / "limina_second_wave_scope_lock_pack.json"
DEFAULT_CSV = ROOT / "data" / "limina_second_wave_scope_lock_tasks.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_second_wave_scope_lock_pack.md"


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def candidate_lookup(records: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list):
        return {}
    return {str(record.get("id")): record for record in records if record.get("id")}


def slug(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value.lower()).strip("_")


def task(
    candidate_id: str,
    order: int,
    title: str,
    task_type: str,
    route: str,
    dependency: str,
    source_file_class: str,
    acceptance_criterion: str,
) -> dict[str, Any]:
    return {
        "task_id": f"{slug(candidate_id)}__{order:02d}_{slug(title)[:44]}",
        "candidate_id": candidate_id,
        "task_order": order,
        "title": title,
        "task_type": task_type,
        "route": route,
        "dependency": dependency,
        "source_file_class": source_file_class,
        "acceptance_criterion": acceptance_criterion,
        "claim_boundary": (
            "Scope-lock tasks define future source-backed measurements only; they are not "
            "measured evidence and cannot make a candidate suitable."
        ),
    }


def pda_anchor_tasks(row: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_id = row["candidate_id"]
    dependency = row["measurement_dependency"]
    return [
        task(
            candidate_id,
            1,
            "Lock primer and electrode-window identity",
            "scope_lock",
            "desk_review",
            dependency,
            "supplier_or_build_record",
            "Primer chemistry, MEA substrate, mask/window geometry, and hydrogel article identity are fixed before any measurement package is released.",
        ),
        task(
            candidate_id,
            2,
            "Define primer extract blank",
            "measurement_plan",
            "h_a_rescue_prereq",
            dependency,
            "bench_or_chain_of_custody_record",
            "Blank article has pH, osmolality, conductivity, visible shedding, swelling, delamination, and transparency fields mapped to source files.",
        ),
        task(
            candidate_id,
            3,
            "Bind H-B rescue electrochemical fields",
            "measurement_plan",
            "h_b_conditional",
            dependency,
            "electrochemical_or_mea_export",
            "1 kHz impedance, charge-storage proxy, impedance drift, and window-occlusion notes are listed as conditional H-B fields.",
        ),
        task(
            candidate_id,
            4,
            "Record rescue trigger boundary",
            "decision_gate",
            "portfolio",
            dependency,
            "bench_or_chain_of_custody_record",
            "Candidate can only advance if primary H-A is clean enough and measured failure mode points to delamination, adhesion, or window instability.",
        ),
    ]


def external_zwitterionic_tasks(row: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_id = row["candidate_id"]
    dependency = row["measurement_dependency"]
    return [
        task(
            candidate_id,
            1,
            "Lock coated surface placement",
            "scope_lock",
            "desk_review",
            dependency,
            "supplier_or_build_record",
            "Substrate, coating location, uncoated comparator, and membrane/housing exposure boundary are fixed before outreach or purchase.",
        ),
        task(
            candidate_id,
            2,
            "Define extract and medium integrity blank",
            "measurement_plan",
            "zrc_phase_a_comparator",
            dependency,
            "pH_meter_export_or_photo",
            "pH, osmolality, conductivity, turbidity/visible residue, and extractable-risk notes are mapped to source-backed fields.",
        ),
        task(
            candidate_id,
            3,
            "Bind fouling and protein recovery readouts",
            "measurement_plan",
            "zrc_phase_a_comparator",
            dependency,
            "biochemical_or_plate_reader_export",
            "BSA or albumin adsorption, BDNF/proxy recovery, flow resistance drift, and post-soak inspection are listed as required comparator fields.",
        ),
        task(
            candidate_id,
            4,
            "Record external-branch trigger boundary",
            "decision_gate",
            "portfolio",
            dependency,
            "bench_or_chain_of_custody_record",
            "Candidate can only advance if ZRC Phase A real data show adsorption, fouling, or housing-surface loss as a limiting failure mode.",
        ),
    ]


def generic_tasks(row: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_id = row["candidate_id"]
    dependency = row["measurement_dependency"]
    return [
        task(
            candidate_id,
            1,
            "Lock candidate material identity",
            "scope_lock",
            "desk_review",
            dependency,
            "supplier_or_build_record",
            "Material identity, formulation source, comparator, and open procurement risks are fixed before any measurement package is released.",
        ),
        task(
            candidate_id,
            2,
            "Define acellular witness coupon fields",
            "measurement_plan",
            "conditional_witness_coupon",
            dependency,
            "bench_or_chain_of_custody_record",
            "A tiny acellular coupon plan lists medium integrity, swelling, shedding, transparency, and impedance fields with source classes.",
        ),
    ]


def tasks_for(row: dict[str, Any]) -> list[dict[str, Any]]:
    lane = row.get("measurement_lane")
    candidate_id = str(row.get("candidate_id") or "")
    if lane == "cell_contact_anchor_rescue_coupon" or "pda_anchor" in candidate_id:
        return pda_anchor_tasks(row)
    if lane == "external_material_phase_a_comparator" or "all_dry_zwitterionic_external" in candidate_id:
        return external_zwitterionic_tasks(row)
    return generic_tasks(row)


def build_pack(queue: dict[str, Any], candidates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ready_rows = [
        row for row in queue.get("rows", [])
        if str(row.get("queue_decision", "")).startswith("ready_for_second_wave")
    ]
    all_tasks: list[dict[str, Any]] = []
    candidates_out = []
    for row in ready_rows:
        detail = candidates.get(str(row.get("candidate_id")), {})
        candidate_tasks = tasks_for(row)
        all_tasks.extend(candidate_tasks)
        candidates_out.append({
            "candidate_id": row.get("candidate_id"),
            "name": row.get("name"),
            "ranking_priority": row.get("ranking_priority"),
            "weighted_score": row.get("weighted_score"),
            "measurement_dependency": row.get("measurement_dependency"),
            "measurement_lane": row.get("measurement_lane"),
            "scope_lock_action": row.get("scope_lock_action"),
            "near_term_test": row.get("near_term_test"),
            "evidence_refs": detail.get("evidence_refs", row.get("evidence_refs", [])),
            "task_ids": [item["task_id"] for item in candidate_tasks],
        })

    if ready_rows:
        status = "second_wave_scope_lock_pack_ready"
    elif queue.get("status"):
        status = "second_wave_scope_lock_pack_waiting_for_ready_candidates"
    else:
        status = "second_wave_scope_lock_pack_waiting_for_queue"
    return {
        "status": status,
        "summary": {
            "ready_candidate_count": len(ready_rows),
            "task_count": len(all_tasks),
            "source_file_class_count": len({item["source_file_class"] for item in all_tasks}),
            "claim_evidence_created": False,
            "queue_status": queue.get("status", "unknown"),
        },
        "candidates": candidates_out,
        "tasks": all_tasks,
        "next_commands": [
            "python3 scripts/render_limina_second_wave_scope_lock_pack.py",
            "python3 scripts/run_limina_iteration.py",
        ],
    }


def write_csv(path: Path, tasks: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "task_id",
        "candidate_id",
        "task_order",
        "title",
        "task_type",
        "route",
        "dependency",
        "source_file_class",
        "acceptance_criterion",
        "claim_boundary",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in tasks:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def render_report(result: dict[str, Any], csv_path: Path) -> str:
    summary = result["summary"]
    lines = [
        "# LIMINA Second-Wave Scope-Lock Pack",
        "",
        "This pack turns ready second-wave candidates into concrete scope-lock tasks. It does not create material suitability evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Ready candidates:** {summary['ready_candidate_count']}",
        f"**Tasks:** {summary['task_count']}",
        f"**Source-file classes:** {summary['source_file_class_count']}",
        f"**Claim evidence created:** `{str(summary['claim_evidence_created']).lower()}`",
        f"**CSV:** `{rel(csv_path)}`",
        "",
        "## Candidates",
        "",
        "| Candidate | Lane | Dependency | Tasks |",
        "| --- | --- | --- | ---: |",
    ]
    for candidate in result["candidates"]:
        lines.append(
            f"| `{candidate['candidate_id']}` | `{candidate['measurement_lane']}` | "
            f"`{candidate['measurement_dependency']}` | {len(candidate['task_ids'])} |"
        )

    lines.extend(["", "## Tasks", "", "| Order | Candidate | Type | Route | Source class | Acceptance criterion |", "| ---: | --- | --- | --- | --- | --- |"])
    for item in result["tasks"]:
        lines.append(
            f"| {item['task_order']} | `{item['candidate_id']}` | `{item['task_type']}` | "
            f"`{item['route']}` | `{item['source_file_class']}` | {item['acceptance_criterion']} |"
        )

    lines.extend([
        "",
        "## Boundary",
        "",
        "- Scope lock means material identity, trigger rules, and future source classes are defined.",
        "- No task in this pack changes H-A, ZRC, H-B/H-C, long-duration, or claim-audit evidence.",
        "- The first suitable material still requires real measured rows and a final claim audit with `claim_ready=true`.",
        "",
        "## Next Commands",
        "",
    ])
    lines.extend(f"- `{command}`" for command in result.get("next_commands", []))
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA second-wave scope-lock pack.")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_pack(
        queue=load_json(args.queue),
        candidates=candidate_lookup(load_json(args.candidates)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, result["tasks"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result, args.csv_out), encoding="utf-8")
    print(f"Second-wave scope-lock pack: {result['status']}")
    print(f"Ready candidates: {result['summary']['ready_candidate_count']}")
    print(f"Tasks: {result['summary']['task_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
