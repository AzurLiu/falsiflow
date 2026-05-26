#!/usr/bin/env python3
"""Render local capture templates from the LIMINA hybrid measurement plan."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HYBRID_PLAN = ROOT / "data" / "limina_hybrid_measurement_plan.json"
DEFAULT_H_A_RAW = ROOT / "data" / "nhi_pedot_h_a_raw_measurements_template.csv"
DEFAULT_ZRC_TEMPLATE = ROOT / "data" / "zrc_nd_phase_a_sentinel_template.csv"
DEFAULT_JSON = ROOT / "data" / "limina_local_capture_pack.json"
DEFAULT_TASKS = ROOT / "data" / "limina_local_capture_tasks.csv"
DEFAULT_H_A_LOCAL = ROOT / "data" / "nhi_pedot_h_a_local_capture_template.csv"
DEFAULT_H_A_OUTSOURCE = ROOT / "data" / "nhi_pedot_h_a_osmolality_outsource_template.csv"
DEFAULT_ZRC_LOCAL = ROOT / "data" / "zrc_nd_phase_a_local_capture_template.csv"
DEFAULT_ZRC_OUTSOURCE = ROOT / "data" / "zrc_nd_phase_a_osmolality_outsource_template.csv"
DEFAULT_INSTRUMENTS = ROOT / "data" / "limina_local_instrument_register_template.csv"
DEFAULT_QC = ROOT / "data" / "limina_local_capture_qc_checklist.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_local_capture_pack.md"

H_A_BRANCH = "NHI-PEDOT H-A"
ZRC_BRANCH = "ZRC-ND Phase A"
LOCAL_ROUTES = {"inhouse_ready", "supplier_or_build_record"}
OUTSOURCE_ROUTES = {"outsourced_preferred"}
ARTICLE_ONLY_ZRC_FIELDS = {"membrane_lot", "membrane_area_cm2", "prefilter_lot"}
ZRC_CAPTURE_METADATA_FIELDS = ["measured_at", "instrument_id", "source_file"]

TASK_FIELDS = [
    "task_id",
    "branch",
    "route",
    "run_id",
    "sample_event",
    "target_field",
    "wide_field",
    "unit",
    "instrument_class",
    "entry_file",
    "merge_command",
    "source_file_requirement",
    "value_required",
    "provenance_required",
    "notes",
]

INSTRUMENT_FIELDS = [
    "instrument_id",
    "instrument_class",
    "required_for_fields",
    "minimum_capability",
    "calibration_or_source_requirement",
    "output_file_required",
    "status",
    "owner_or_lab",
    "notes",
]

QC_FIELDS = [
    "check_id",
    "stage",
    "applies_to",
    "requirement",
    "fail_if",
    "owner",
    "status",
    "notes",
]

UNITS = {
    "date": "",
    "medium_name": "",
    "medium_lot": "",
    "operator_or_agent": "",
    "temperature_c": "C",
    "initial_volume_ml": "mL",
    "exposure_time_h": "h",
    "pH": "pH",
    "pH_initial": "pH",
    "pH_final": "pH",
    "conductivity": "mS/cm",
    "conductivity_initial_mS_cm": "mS/cm",
    "conductivity_final_mS_cm": "mS/cm",
    "osmolality": "mOsm/kg",
    "osmolality_initial_mOsm_kg": "mOsm/kg",
    "osmolality_final_mOsm_kg": "mOsm/kg",
    "visible_precipitate": "bool",
    "visible_shedding": "bool",
    "swelling_fraction": "fraction",
    "delamination_score": "score",
    "optical_transparency_fraction": "fraction",
    "membrane_lot": "",
    "membrane_area_cm2": "cm2",
    "prefilter_lot": "",
    "mea_coupon_id": "",
    "electrode_material": "",
    "laminin_or_peptide_density": "",
    "sterilization_or_aseptic_protocol": "",
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


def route_lookup(plan: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for row in plan.get("rows", []):
        branch = str(row.get("branch", ""))
        field = str(row.get("field", ""))
        if branch and field:
            lookup[(branch, field)] = row
    return lookup


def h_a_wide_field(sample_event: str, target: str) -> str:
    event = sample_event.strip().lower()
    if target == "pH":
        return "pH_initial" if event == "initial" else "pH_final" if event == "final" else target
    if target == "conductivity":
        return "conductivity_initial_mS_cm" if event == "initial" else "conductivity_final_mS_cm" if event == "final" else target
    if target == "osmolality":
        return "osmolality_initial_mOsm_kg" if event == "initial" else "osmolality_final_mOsm_kg" if event == "final" else target
    return target


def instrument_class(field: str, route: str) -> str:
    if route == "supplier_or_build_record":
        return "record_review"
    if "osmolality" in field:
        return "osmometer_or_external_lab"
    if field.startswith("pH") or field == "pH":
        return "calibrated_pH_meter"
    if "conductivity" in field:
        return "calibrated_conductivity_meter"
    if field == "temperature_c":
        return "temperature_probe_or_incubator_log"
    if field in {"visible_precipitate", "visible_shedding", "delamination_score", "optical_transparency_fraction"}:
        return "imaging_station_or_scoring_sheet"
    if field == "swelling_fraction":
        return "caliper_balance_or_image_analysis"
    if field in {"initial_volume_ml", "exposure_time_h"}:
        return "bench_log"
    return "bench_or_vendor_record"


def zrc_row_needs_field(row: dict[str, str], field: str) -> bool:
    if field not in ARTICLE_ONLY_ZRC_FIELDS:
        return True
    return row.get("article_id", "") != "no_module_static_control"


def merge_command(branch: str, route: str) -> str:
    if branch == H_A_BRANCH:
        if route in LOCAL_ROUTES:
            return (
                "python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py "
                "--raw data/nhi_pedot_h_a_local_capture_template.csv"
            )
        return (
            "python3 scripts/merge_nhi_pedot_h_a_raw_measurements.py "
            "--base data/nhi_pedot_h_a_runs_active.csv "
            "--raw data/nhi_pedot_h_a_osmolality_outsource_template.csv "
            "--out data/nhi_pedot_h_a_runs_active.csv"
        )
    if route in LOCAL_ROUTES:
        return (
            "python3 scripts/merge_zrc_nd_measurements.py "
            "--measurements data/zrc_nd_phase_a_local_capture_template.csv"
        )
    return (
        "python3 scripts/merge_zrc_nd_measurements.py "
        "--base data/zrc_nd_validation_runs_active.csv "
        "--measurements data/zrc_nd_phase_a_osmolality_outsource_template.csv "
        "--out data/zrc_nd_validation_runs_active.csv"
    )


def entry_file(branch: str, route: str) -> str:
    if branch == H_A_BRANCH:
        return rel(DEFAULT_H_A_LOCAL if route in LOCAL_ROUTES else DEFAULT_H_A_OUTSOURCE)
    return rel(DEFAULT_ZRC_LOCAL if route in LOCAL_ROUTES else DEFAULT_ZRC_OUTSOURCE)


def build_h_a_tasks(
    raw_rows: list[dict[str, str]],
    lookup: dict[tuple[str, str], dict[str, Any]],
    start_index: int,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    tasks: list[dict[str, Any]] = []
    local_rows: list[dict[str, str]] = []
    outsource_rows: list[dict[str, str]] = []
    for raw in raw_rows:
        field = raw.get("target_field", "").strip()
        if not field:
            continue
        plan_row = lookup.get((H_A_BRANCH, field), {})
        route = str(plan_row.get("route", "vendor_or_future_gate"))
        if route in LOCAL_ROUTES:
            local_rows.append(raw)
        elif route in OUTSOURCE_ROUTES:
            outsource_rows.append(raw)
        else:
            continue
        wide = h_a_wide_field(raw.get("sample_event", ""), field)
        tasks.append({
            "task_id": f"LC-{start_index + len(tasks):04d}",
            "branch": H_A_BRANCH,
            "route": route,
            "run_id": raw.get("run_id", ""),
            "sample_event": raw.get("sample_event", ""),
            "target_field": field,
            "wide_field": wide,
            "unit": raw.get("unit") or UNITS.get(wide, UNITS.get(field, "")),
            "instrument_class": instrument_class(wide, route),
            "entry_file": entry_file(H_A_BRANCH, route),
            "merge_command": merge_command(H_A_BRANCH, route),
            "source_file_requirement": plan_row.get("source_file_requirement", ""),
            "value_required": "yes",
            "provenance_required": "measured_at/operator_or_agent/source_file plus instrument_id for measured fields",
            "notes": "long_form_h_a_raw_entry",
        })
    return tasks, local_rows, outsource_rows


def build_zrc_tasks(
    zrc_rows: list[dict[str, str]],
    lookup: dict[tuple[str, str], dict[str, Any]],
    start_index: int,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    plan_rows = [
        row for (branch, _field), row in lookup.items()
        if branch == ZRC_BRANCH and row.get("route") in LOCAL_ROUTES | OUTSOURCE_ROUTES
    ]
    tasks: list[dict[str, Any]] = []
    local_fields: set[str] = set()
    outsource_fields: set[str] = set()
    for zrc in zrc_rows:
        run_id = zrc.get("run_id", "")
        if not run_id:
            continue
        for plan_row in plan_rows:
            field = str(plan_row.get("field", ""))
            route = str(plan_row.get("route", ""))
            if not field or not zrc_row_needs_field(zrc, field):
                continue
            if route in LOCAL_ROUTES:
                local_fields.add(field)
            elif route in OUTSOURCE_ROUTES:
                outsource_fields.add(field)
            tasks.append({
                "task_id": f"LC-{start_index + len(tasks):04d}",
                "branch": ZRC_BRANCH,
                "route": route,
                "run_id": run_id,
                "sample_event": zrc.get("timepoint", ""),
                "target_field": field,
                "wide_field": field,
                "unit": UNITS.get(field, ""),
                "instrument_class": instrument_class(field, route),
                "entry_file": entry_file(ZRC_BRANCH, route),
                "merge_command": merge_command(ZRC_BRANCH, route),
                "source_file_requirement": plan_row.get("source_file_requirement", ""),
                "value_required": "yes",
                "provenance_required": "operator_or_agent/date/source_file plus instrument_id if captured outside vendor report",
                "notes": "wide_zrc_phase_a_entry",
            })
    local_rows = project_zrc_rows(zrc_rows, local_fields)
    outsource_rows = project_zrc_rows(zrc_rows, outsource_fields)
    return tasks, local_rows, outsource_rows


def project_zrc_rows(rows: list[dict[str, str]], editable_fields: set[str]) -> list[dict[str, str]]:
    projected: list[dict[str, str]] = []
    for row in rows:
        output = dict(row)
        output["operator_or_agent"] = ""
        for field in editable_fields:
            output[field] = ""
        output["notes"] = ""
        projected.append(output)
    return projected


def instrument_rows() -> list[dict[str, str]]:
    return [
        {
            "instrument_id": "record_actual_pH_meter_id",
            "instrument_class": "calibrated_pH_meter",
            "required_for_fields": "pH,pH_initial,pH_final",
            "minimum_capability": "Calibrated pH measurement in culture-medium range.",
            "calibration_or_source_requirement": "Two- or three-point calibration on measurement day; preserve calibration log.",
            "output_file_required": "meter export, calibration log, or time-stamped display photo",
            "status": "needed_before_measurement",
            "owner_or_lab": "",
            "notes": "",
        },
        {
            "instrument_id": "record_actual_conductivity_meter_id",
            "instrument_class": "calibrated_conductivity_meter",
            "required_for_fields": "conductivity,conductivity_initial_mS_cm,conductivity_final_mS_cm",
            "minimum_capability": "mS/cm conductivity readout with calibration standard suitable for media.",
            "calibration_or_source_requirement": "Calibration or standard check on measurement day.",
            "output_file_required": "meter export, calibration log, or time-stamped display photo",
            "status": "needed_before_measurement",
            "owner_or_lab": "",
            "notes": "",
        },
        {
            "instrument_id": "record_actual_temperature_probe_or_incubator_id",
            "instrument_class": "temperature_probe_or_incubator_log",
            "required_for_fields": "temperature_c",
            "minimum_capability": "Temperature record at incubation or measurement time.",
            "calibration_or_source_requirement": "Probe ID or incubator log traceable to the measurement window.",
            "output_file_required": "incubator export, probe log, or time-stamped photo",
            "status": "needed_before_measurement",
            "owner_or_lab": "",
            "notes": "",
        },
        {
            "instrument_id": "record_actual_imaging_station_id",
            "instrument_class": "imaging_station_or_scoring_sheet",
            "required_for_fields": "visible_precipitate,visible_shedding,delamination_score,optical_transparency_fraction",
            "minimum_capability": "Consistent lightbox/stereoscope/microscope imaging with run_id traceability.",
            "calibration_or_source_requirement": "Use same lighting, scale, magnification, and scoring worksheet across rows.",
            "output_file_required": "image files plus scoring worksheet",
            "status": "needed_before_measurement",
            "owner_or_lab": "",
            "notes": "",
        },
        {
            "instrument_id": "record_actual_dimension_or_mass_method_id",
            "instrument_class": "caliper_balance_or_image_analysis",
            "required_for_fields": "swelling_fraction",
            "minimum_capability": "Pre/post dimension, area, or mass method applied consistently.",
            "calibration_or_source_requirement": "Record method, scale/caliper ID, or image-analysis workflow.",
            "output_file_required": "worksheet, export, or annotated images",
            "status": "needed_before_measurement",
            "owner_or_lab": "",
            "notes": "",
        },
        {
            "instrument_id": "external_or_local_osmometer_id",
            "instrument_class": "osmometer_or_external_lab",
            "required_for_fields": "osmolality,osmolality_initial_mOsm_kg,osmolality_final_mOsm_kg",
            "minimum_capability": "Osmolality in mOsm/kg with run_id reconciliation.",
            "calibration_or_source_requirement": "External report or local calibration record.",
            "output_file_required": "osmometer report/export",
            "status": "outsourced_preferred",
            "owner_or_lab": "",
            "notes": "Use only if real report/export is available.",
        },
    ]


def qc_rows() -> list[dict[str, str]]:
    return [
        {
            "check_id": "LC-QC-001",
            "stage": "pre_entry",
            "applies_to": "all templates",
            "requirement": "Every run_id must exactly match the generated template run_id.",
            "fail_if": "run_id is edited, missing, duplicated incorrectly, or invented.",
            "owner": "operator",
            "status": "pending_real_measurement",
            "notes": "",
        },
        {
            "check_id": "LC-QC-002",
            "stage": "provenance",
            "applies_to": "all measured fields",
            "requirement": "Every measured value must include measured_at, operator_or_agent, instrument_id, and source_file.",
            "fail_if": "any provenance field is blank, placeholder, synthetic, or not traceable to the row.",
            "owner": "operator",
            "status": "pending_real_measurement",
            "notes": "",
        },
        {
            "check_id": "LC-QC-003",
            "stage": "source_files",
            "applies_to": "all measured fields",
            "requirement": "source_file must point to raw export, image, worksheet, calibration log, or vendor report.",
            "fail_if": "source_file is only an email, quote, verbal note, capability claim, or blank.",
            "owner": "operator",
            "status": "pending_real_measurement",
            "notes": "",
        },
        {
            "check_id": "LC-QC-004",
            "stage": "units",
            "applies_to": "pH/conductivity/osmolality/temperature/swelling fields",
            "requirement": "Units must match the generated template or an accepted alias in the merge script.",
            "fail_if": "unit is missing where required or inconsistent with the target field.",
            "owner": "operator",
            "status": "pending_real_measurement",
            "notes": "",
        },
        {
            "check_id": "LC-QC-005",
            "stage": "visual_scoring",
            "applies_to": "visible_precipitate,visible_shedding,delamination_score,optical_transparency_fraction",
            "requirement": "Use the same imaging/scoring method across all matched rows.",
            "fail_if": "lighting, magnification, scoring rubric, or threshold changes without deviation log.",
            "owner": "operator",
            "status": "pending_real_measurement",
            "notes": "",
        },
        {
            "check_id": "LC-QC-006",
            "stage": "claim_guard",
            "applies_to": "all outputs",
            "requirement": "Do not treat local capture templates or partially filled rows as suitability evidence.",
            "fail_if": "claim_ready is inferred before evaluator gates and claim audit pass on real rows.",
            "owner": "agent",
            "status": "active_guard",
            "notes": "",
        },
    ]


def summarize(tasks: list[dict[str, Any]], h_a_local: list[dict[str, str]], h_a_out: list[dict[str, str]], zrc_local: list[dict[str, str]], zrc_out: list[dict[str, str]]) -> dict[str, Any]:
    route_counts = Counter(task["route"] for task in tasks)
    branch_counts = Counter(task["branch"] for task in tasks)
    return {
        "task_count": len(tasks),
        "route_counts": dict(route_counts),
        "branch_counts": dict(branch_counts),
        "h_a_local_entry_rows": len(h_a_local),
        "h_a_outsource_entry_rows": len(h_a_out),
        "zrc_local_template_rows": len(zrc_local),
        "zrc_outsource_template_rows": len(zrc_out),
        "ready_to_collect_local_rows": route_counts.get("inhouse_ready", 0),
        "ready_to_record_provenance_rows": route_counts.get("supplier_or_build_record", 0),
        "outsourced_preferred_rows": route_counts.get("outsourced_preferred", 0),
    }


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    plan = load_json(args.hybrid_plan)
    lookup = route_lookup(plan)
    h_a_fields, h_a_raw_rows = load_csv(args.h_a_raw)
    zrc_fields, zrc_rows = load_csv(args.zrc_template)
    if not h_a_fields:
        raise ValueError(f"No H-A raw template header found in {args.h_a_raw}")
    if not zrc_fields:
        raise ValueError(f"No ZRC-ND template header found in {args.zrc_template}")

    h_a_tasks, h_a_local, h_a_out = build_h_a_tasks(h_a_raw_rows, lookup, 1)
    zrc_tasks, zrc_local, zrc_out = build_zrc_tasks(zrc_rows, lookup, len(h_a_tasks) + 1)
    tasks = h_a_tasks + zrc_tasks
    summary = summarize(tasks, h_a_local, h_a_out, zrc_local, zrc_out)

    write_csv(args.tasks_csv, TASK_FIELDS, tasks)
    write_csv(args.h_a_local_csv, h_a_fields, h_a_local)
    write_csv(args.h_a_outsource_csv, h_a_fields, h_a_out)
    zrc_capture_fields = zrc_fields + [field for field in ZRC_CAPTURE_METADATA_FIELDS if field not in zrc_fields]
    write_csv(args.zrc_local_csv, zrc_capture_fields, zrc_local)
    write_csv(args.zrc_outsource_csv, zrc_capture_fields, zrc_out)
    write_csv(args.instrument_register, INSTRUMENT_FIELDS, instrument_rows())
    write_csv(args.qc_checklist, QC_FIELDS, qc_rows())

    return {
        "status": "local_capture_pack_ready",
        "purpose": "Turn the hybrid measurement routing plan into fillable local/outsource templates without claiming material suitability.",
        "source_artifacts": {
            "hybrid_plan": rel(args.hybrid_plan),
            "h_a_raw_template": rel(args.h_a_raw),
            "zrc_phase_a_template": rel(args.zrc_template),
        },
        "generated_artifacts": {
            "task_table": rel(args.tasks_csv),
            "h_a_local_capture_template": rel(args.h_a_local_csv),
            "h_a_osmolality_outsource_template": rel(args.h_a_outsource_csv),
            "zrc_local_capture_template": rel(args.zrc_local_csv),
            "zrc_osmolality_outsource_template": rel(args.zrc_outsource_csv),
            "instrument_register_template": rel(args.instrument_register),
            "qc_checklist": rel(args.qc_checklist),
        },
        "summary": summary,
        "merge_commands": [
            merge_command(H_A_BRANCH, "inhouse_ready"),
            merge_command(H_A_BRANCH, "outsourced_preferred"),
            merge_command(ZRC_BRANCH, "inhouse_ready"),
            merge_command(ZRC_BRANCH, "outsourced_preferred"),
        ],
        "boundary": "This pack is logistics and data-entry scaffolding only; it is not measured evidence until filled with real values and passed through QC, gate evaluators, and the final claim audit.",
    }


def render_report(pack: dict[str, Any]) -> str:
    summary = pack["summary"]
    artifacts = pack["generated_artifacts"]
    lines = [
        "# LIMINA Local Capture Pack",
        "",
        "This pack converts the hybrid measurement routing plan into fillable files. It is not measured evidence.",
        "",
        f"**Status:** `{pack['status']}`",
        f"**Tasks:** {summary['task_count']}",
        f"**Local measured tasks:** {summary['ready_to_collect_local_rows']}",
        f"**Provenance/build-record tasks:** {summary['ready_to_record_provenance_rows']}",
        f"**Outsource-preferred tasks:** {summary['outsourced_preferred_rows']}",
        "",
        "## Generated Files",
        "",
        "| File | Purpose |",
        "| --- | --- |",
        f"| `{artifacts['task_table']}` | Row-level task table with route, source-file requirement, and merge command. |",
        f"| `{artifacts['h_a_local_capture_template']}` | Fill local/provenance H-A long-form rows. |",
        f"| `{artifacts['h_a_osmolality_outsource_template']}` | Fill H-A osmolality rows from external osmometer/lab report. |",
        f"| `{artifacts['zrc_local_capture_template']}` | Fill ZRC-ND Phase A local/provenance wide rows. |",
        f"| `{artifacts['zrc_osmolality_outsource_template']}` | Fill ZRC-ND Phase A osmolality rows from external osmometer/lab report. |",
        f"| `{artifacts['instrument_register_template']}` | Record instrument IDs, calibration requirements, and owners. |",
        f"| `{artifacts['qc_checklist']}` | Pre-merge local QC checks that keep placeholders out of evidence. |",
        "",
        "## Entry Counts",
        "",
        "| Template | Rows |",
        "| --- | ---: |",
        f"| H-A local/provenance long-form rows | {summary['h_a_local_entry_rows']} |",
        f"| H-A outsource osmolality long-form rows | {summary['h_a_outsource_entry_rows']} |",
        f"| ZRC-ND local/provenance wide rows | {summary['zrc_local_template_rows']} |",
        f"| ZRC-ND outsource osmolality wide rows | {summary['zrc_outsource_template_rows']} |",
        "",
        "## Merge Commands After Real Values Exist",
        "",
    ]
    for command in pack["merge_commands"]:
        lines.extend(["```bash", command, "```", ""])
    lines.extend([
        "## Guardrails",
        "",
        "- Fill values only from real measurements, calibrated logs, source files, supplier records, or vendor reports.",
        "- Do not paste vendor capability replies or quotes into measurement fields.",
        "- Keep osmolality separate unless a calibrated local osmometer is available.",
        "- Run the normal iteration and claim guard after merging any real rows.",
        "",
        "## Boundary",
        "",
        pack["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA local capture pack.")
    parser.add_argument("--hybrid-plan", type=Path, default=DEFAULT_HYBRID_PLAN)
    parser.add_argument("--h-a-raw", type=Path, default=DEFAULT_H_A_RAW)
    parser.add_argument("--zrc-template", type=Path, default=DEFAULT_ZRC_TEMPLATE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--tasks-csv", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--h-a-local-csv", type=Path, default=DEFAULT_H_A_LOCAL)
    parser.add_argument("--h-a-outsource-csv", type=Path, default=DEFAULT_H_A_OUTSOURCE)
    parser.add_argument("--zrc-local-csv", type=Path, default=DEFAULT_ZRC_LOCAL)
    parser.add_argument("--zrc-outsource-csv", type=Path, default=DEFAULT_ZRC_OUTSOURCE)
    parser.add_argument("--instrument-register", type=Path, default=DEFAULT_INSTRUMENTS)
    parser.add_argument("--qc-checklist", type=Path, default=DEFAULT_QC)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pack = build_pack(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(pack, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(pack), encoding="utf-8")
    print(f"Local capture pack: {pack['status']}")
    print(f"Tasks: {pack['summary']['task_count']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
