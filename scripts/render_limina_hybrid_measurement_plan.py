#!/usr/bin/env python3
"""Render a hybrid in-house/vendor measurement plan for LIMINA gates."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_H_A_SERVICE = ROOT / "data" / "nhi_pedot_h_a_service_request.json"
DEFAULT_H_A_RAW = ROOT / "data" / "nhi_pedot_h_a_raw_measurements_template.csv"
DEFAULT_ZRC_SERVICE = ROOT / "data" / "zrc_nd_phase_a_service_request.json"
DEFAULT_JSON = ROOT / "data" / "limina_hybrid_measurement_plan.json"
DEFAULT_CSV = ROOT / "data" / "limina_hybrid_measurement_plan.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_hybrid_measurement_plan.md"

CSV_FIELDS = [
    "branch",
    "field",
    "rows",
    "route",
    "route_label",
    "evidence_requirement",
    "source_file_requirement",
    "operator_hint",
    "notes",
]

ROUTE_ORDER = [
    "inhouse_ready",
    "outsourced_preferred",
    "supplier_or_build_record",
    "vendor_or_future_gate",
]

ROUTE_LABELS = {
    "inhouse_ready": "Can be captured locally or by a simple bench operator if calibrated instruments/images are available.",
    "outsourced_preferred": "Prefer external lab unless a calibrated instrument is already available locally.",
    "supplier_or_build_record": "Record from supplier, fabrication batch, or chain-of-custody rather than analytical testing.",
    "vendor_or_future_gate": "Not required for the current front-door gate or likely needs later specialist testing.",
}

FIELD_RULES = {
    "date": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "ISO date for the actual measurement or sample-handling event.",
        "source_file_requirement": "Bench sheet, vendor report, or chain-of-custody CSV.",
        "operator_hint": "bench_or_vendor",
    },
    "operator_or_agent": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "Named operator, lab, or automation agent that produced the value.",
        "source_file_requirement": "Bench sheet, vendor report, or chain-of-custody CSV.",
        "operator_hint": "bench_or_vendor",
    },
    "medium_name": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "Exact medium or CL1-proxy medium name.",
        "source_file_requirement": "Medium bottle photo, lot CoA, or chain-of-custody record.",
        "operator_hint": "bench_or_vendor",
    },
    "medium_lot": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "Exact medium lot used for matched article/control rows.",
        "source_file_requirement": "Lot CoA, bottle label image, or chain-of-custody record.",
        "operator_hint": "bench_or_vendor",
    },
    "temperature_c": {
        "route": "inhouse_ready",
        "evidence_requirement": "Actual incubation or measurement temperature in C.",
        "source_file_requirement": "Incubator log, probe export, or time-stamped photo.",
        "operator_hint": "local_bench",
    },
    "initial_volume_ml": {
        "route": "inhouse_ready",
        "evidence_requirement": "Starting medium volume per row.",
        "source_file_requirement": "Pipetting worksheet or balance/volume log.",
        "operator_hint": "local_bench",
    },
    "exposure_time_h": {
        "route": "inhouse_ready",
        "evidence_requirement": "Actual elapsed exposure time for the row.",
        "source_file_requirement": "Incubation start/stop log or vendor report.",
        "operator_hint": "local_bench",
    },
    "pH_initial": {
        "route": "inhouse_ready",
        "evidence_requirement": "Calibrated pH measurement before exposure or matched start measurement.",
        "source_file_requirement": "Meter export, calibration log, or time-stamped display photo.",
        "operator_hint": "local_bench_or_vendor",
    },
    "pH_final": {
        "route": "inhouse_ready",
        "evidence_requirement": "Calibrated pH measurement after the row timepoint.",
        "source_file_requirement": "Meter export, calibration log, or time-stamped display photo.",
        "operator_hint": "local_bench_or_vendor",
    },
    "pH": {
        "route": "inhouse_ready",
        "evidence_requirement": "Calibrated pH measurement for the specified H-A sample event.",
        "source_file_requirement": "Meter export, calibration log, or time-stamped display photo reconciled to run_id.",
        "operator_hint": "local_bench_or_vendor",
    },
    "conductivity_initial_mS_cm": {
        "route": "inhouse_ready",
        "evidence_requirement": "Calibrated conductivity before exposure or matched start measurement.",
        "source_file_requirement": "Conductivity meter export, calibration log, or display photo.",
        "operator_hint": "local_bench_or_vendor",
    },
    "conductivity_final_mS_cm": {
        "route": "inhouse_ready",
        "evidence_requirement": "Calibrated conductivity after the row timepoint.",
        "source_file_requirement": "Conductivity meter export, calibration log, or display photo.",
        "operator_hint": "local_bench_or_vendor",
    },
    "conductivity": {
        "route": "inhouse_ready",
        "evidence_requirement": "Calibrated conductivity for the specified H-A sample event.",
        "source_file_requirement": "Conductivity meter export, calibration log, or display photo reconciled to run_id.",
        "operator_hint": "local_bench_or_vendor",
    },
    "osmolality_initial_mOsm_kg": {
        "route": "outsourced_preferred",
        "evidence_requirement": "Measured osmolality before exposure or matched start measurement.",
        "source_file_requirement": "Osmometer report/export reconciled to run_id.",
        "operator_hint": "vendor_or_equipped_lab",
    },
    "osmolality_final_mOsm_kg": {
        "route": "outsourced_preferred",
        "evidence_requirement": "Measured osmolality after the row timepoint.",
        "source_file_requirement": "Osmometer report/export reconciled to run_id.",
        "operator_hint": "vendor_or_equipped_lab",
    },
    "osmolality": {
        "route": "outsourced_preferred",
        "evidence_requirement": "Measured osmolality for the specified H-A sample event.",
        "source_file_requirement": "Osmometer report/export reconciled to run_id.",
        "operator_hint": "vendor_or_equipped_lab",
    },
    "visible_precipitate": {
        "route": "inhouse_ready",
        "evidence_requirement": "Boolean precipitate/turbidity/extractables concern scored from inspection.",
        "source_file_requirement": "Time-stamped image or vendor inspection report.",
        "operator_hint": "local_bench_or_vendor",
    },
    "visible_shedding": {
        "route": "inhouse_ready",
        "evidence_requirement": "Boolean visible material shedding score.",
        "source_file_requirement": "Time-stamped image or microscopy/stereoscope export.",
        "operator_hint": "local_bench_or_vendor",
    },
    "swelling_fraction": {
        "route": "inhouse_ready",
        "evidence_requirement": "Fractional swelling from pre/post dimensions or mass using the same method across rows.",
        "source_file_requirement": "Image analysis export, caliper log, or mass/dimension worksheet.",
        "operator_hint": "local_bench_or_materials_lab",
    },
    "delamination_score": {
        "route": "inhouse_ready",
        "evidence_requirement": "0 to 1 delamination score using the preregistered H-A rubric.",
        "source_file_requirement": "Image plus scoring worksheet or vendor image-analysis report.",
        "operator_hint": "local_bench_or_materials_lab",
    },
    "optical_transparency_fraction": {
        "route": "inhouse_ready",
        "evidence_requirement": "0 to 1 transparency estimate from a consistent imaging/lightbox method.",
        "source_file_requirement": "Image-analysis export or vendor microscopy report.",
        "operator_hint": "local_bench_or_materials_lab",
    },
    "membrane_lot": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "Actual membrane/module lot for exposed ZRC-ND articles.",
        "source_file_requirement": "Supplier label, CoA, build sheet, or chain-of-custody record.",
        "operator_hint": "fabrication_or_supplier_record",
    },
    "membrane_area_cm2": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "Exposed membrane area used for normalization.",
        "source_file_requirement": "Build drawing, measurement worksheet, or supplier documentation.",
        "operator_hint": "fabrication_or_supplier_record",
    },
    "prefilter_lot": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "Guard prefilter lot or explicit none/not_applicable.",
        "source_file_requirement": "Supplier label, build sheet, or chain-of-custody record.",
        "operator_hint": "fabrication_or_supplier_record",
    },
    "mea_coupon_id": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "Traceable MEA or coupon identifier for the exposed article.",
        "source_file_requirement": "Build sheet, sample label, or chain-of-custody record.",
        "operator_hint": "fabrication_or_supplier_record",
    },
    "electrode_material": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "Actual electrode/coupon substrate material used for the row.",
        "source_file_requirement": "Supplier documentation, build sheet, or sample label record.",
        "operator_hint": "fabrication_or_supplier_record",
    },
    "laminin_or_peptide_density": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "Applied laminin or adhesion-peptide target density or documented formulation value.",
        "source_file_requirement": "Recipe record, supplier CoA, coating log, or build sheet.",
        "operator_hint": "fabrication_or_supplier_record",
    },
    "sterilization_or_aseptic_protocol": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "Actual sterilization or aseptic-handling protocol applied to the article.",
        "source_file_requirement": "SOP identifier, batch record, or chain-of-custody record.",
        "operator_hint": "fabrication_or_supplier_record",
    },
    "housing_material": {
        "route": "supplier_or_build_record",
        "evidence_requirement": "Housing material for exposed module/witness articles.",
        "source_file_requirement": "Build sheet or supplier documentation.",
        "operator_hint": "fabrication_or_supplier_record",
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


def load_h_a_target_counts(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not path.exists():
        return counts
    with path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            field = row.get("target_field", "").strip()
            if field:
                counts[field] += 1
    return counts


def required_field_map(service: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item.get("field", ""): item
        for item in service.get("required_fields", [])
        if item.get("field")
    }


def route_for_field(field: str) -> dict[str, str]:
    return {
        "route": "vendor_or_future_gate",
        "evidence_requirement": "Specialist or later-gate value; do not enter placeholder values.",
        "source_file_requirement": "Vendor report, instrument export, or later-gate run file.",
        "operator_hint": "vendor_or_later_gate",
        **FIELD_RULES.get(field, {}),
    }


def build_row(branch: str, field: str, rows: int, description: str = "") -> dict[str, Any]:
    rule = route_for_field(field)
    return {
        "branch": branch,
        "field": field,
        "rows": rows,
        "route": rule["route"],
        "route_label": ROUTE_LABELS[rule["route"]],
        "evidence_requirement": rule["evidence_requirement"],
        "source_file_requirement": rule["source_file_requirement"],
        "operator_hint": rule["operator_hint"],
        "notes": description,
    }


def sorted_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (row["branch"], ROUTE_ORDER.index(row["route"]), row["field"]),
    )


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_branch: dict[str, dict[str, Any]] = {}
    for branch in sorted({row["branch"] for row in rows}):
        branch_rows = [row for row in rows if row["branch"] == branch]
        route_counts: dict[str, dict[str, int]] = {}
        for route in ROUTE_ORDER:
            routed = [row for row in branch_rows if row["route"] == route]
            route_counts[route] = {
                "field_count": len(routed),
                "row_count": sum(int(row["rows"]) for row in routed),
            }
        by_branch[branch] = {
            "field_count": len(branch_rows),
            "row_count": sum(int(row["rows"]) for row in branch_rows),
            "route_counts": route_counts,
        }
    route_totals: dict[str, dict[str, int]] = {}
    for route in ROUTE_ORDER:
        routed = [row for row in rows if row["route"] == route]
        route_totals[route] = {
            "field_count": len(routed),
            "row_count": sum(int(row["rows"]) for row in routed),
        }
    return {
        "branch_count": len(by_branch),
        "field_count": len(rows),
        "row_count": sum(int(row["rows"]) for row in rows),
        "by_branch": by_branch,
        "route_totals": route_totals,
    }


def build_plan(h_a_service: dict[str, Any], h_a_counts: Counter[str], zrc_service: dict[str, Any]) -> dict[str, Any]:
    h_a_required = required_field_map(h_a_service)
    zrc_required = required_field_map(zrc_service)
    rows: list[dict[str, Any]] = []
    for field, count in h_a_counts.items():
        description = str(h_a_required.get(field, {}).get("description", ""))
        rows.append(build_row("NHI-PEDOT H-A", field, int(count), description))
    for field, item in zrc_required.items():
        rows.append(build_row("ZRC-ND Phase A", field, int(item.get("rows", 0)), str(item.get("description", ""))))
    rows = sorted_rows(rows)
    summary = summarize_rows(rows)
    return {
        "status": "hybrid_measurement_plan_ready",
        "purpose": "Reduce time-to-real-evidence by separating locally capturable fields from vendor-preferred fields.",
        "h_a_active_candidate": h_a_service.get("active_candidate"),
        "zrc_active_candidate": zrc_service.get("active_candidate"),
        "source_artifacts": {
            "h_a_service_request": rel(DEFAULT_H_A_SERVICE),
            "h_a_raw_template": rel(DEFAULT_H_A_RAW),
            "zrc_phase_a_service_request": rel(DEFAULT_ZRC_SERVICE),
        },
        "summary": summary,
        "rows": rows,
        "execution_notes": [
            "Local capture can reduce vendor scope, but every local value still needs measured_at, operator_or_agent, instrument_id, and source_file provenance.",
            "Osmolality is kept as outsourced_preferred because it commonly requires a dedicated osmometer; use a local instrument only if it is calibrated and produces traceable output.",
            "Supplier/build records do not prove compatibility by themselves; they only remove provenance blockers.",
            "Never enter phone photos, emails, or vendor capability replies as material evidence unless they contain real run-level measured values.",
        ],
        "non_claim_boundary": "This plan only routes work. Suitability remains false until real, non-synthetic rows pass gate evaluators and the final claim audit.",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def render_report(plan: dict[str, Any]) -> str:
    summary = plan["summary"]
    lines = [
        "# LIMINA Hybrid Measurement Plan",
        "",
        "This plan separates locally capturable fields from vendor-preferred fields. It is not measured evidence.",
        "",
        f"**Status:** `{plan['status']}`",
        f"**NHI-PEDOT candidate:** `{plan.get('h_a_active_candidate', '-')}`",
        f"**ZRC-ND candidate:** `{plan.get('zrc_active_candidate', '-')}`",
        f"**Field rows routed:** {summary['row_count']}",
        "",
        "## Route Totals",
        "",
        "| Route | Fields | Rows | Meaning |",
        "| --- | ---: | ---: | --- |",
    ]
    for route in ROUTE_ORDER:
        counts = summary["route_totals"][route]
        lines.append(
            f"| `{route}` | {counts['field_count']} | {counts['row_count']} | {ROUTE_LABELS[route]} |"
        )

    lines.extend(["", "## Branch Summary", "", "| Branch | Fields | Rows | Local rows | Outsource-preferred rows | Provenance rows |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for branch, item in summary["by_branch"].items():
        routes = item["route_counts"]
        lines.append(
            f"| {branch} | {item['field_count']} | {item['row_count']} | "
            f"{routes['inhouse_ready']['row_count']} | "
            f"{routes['outsourced_preferred']['row_count']} | "
            f"{routes['supplier_or_build_record']['row_count']} |"
        )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in plan["rows"]:
        grouped[row["branch"]].append(row)
    for branch, branch_rows in grouped.items():
        lines.extend(["", f"## {branch}", "", "| Field | Rows | Route | Evidence requirement | Source file requirement |", "| --- | ---: | --- | --- | --- |"])
        for row in branch_rows:
            lines.append(
                f"| `{row['field']}` | {row['rows']} | `{row['route']}` | "
                f"{row['evidence_requirement']} | {row['source_file_requirement']} |"
            )

    lines.extend(["", "## Execution Notes", ""])
    lines.extend(f"- {item}" for item in plan["execution_notes"])
    lines.extend(["", "## Boundary", "", plan["non_claim_boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA hybrid measurement plan.")
    parser.add_argument("--h-a-service", type=Path, default=DEFAULT_H_A_SERVICE)
    parser.add_argument("--h-a-raw", type=Path, default=DEFAULT_H_A_RAW)
    parser.add_argument("--zrc-service", type=Path, default=DEFAULT_ZRC_SERVICE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    plan = build_plan(
        load_json(args.h_a_service),
        load_h_a_target_counts(args.h_a_raw),
        load_json(args.zrc_service),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, plan["rows"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(plan), encoding="utf-8")
    print(f"Hybrid measurement plan: {plan['status']}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
