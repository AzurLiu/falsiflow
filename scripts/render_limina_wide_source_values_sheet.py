#!/usr/bin/env python3
"""Render source-value sidecars for wide evaluator run tables."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

LOCATOR_FIELDS = {
    "run_id",
    "phase",
    "timepoint",
    "replicate",
    "article_id",
    "variant_id",
    "control_article_id",
    "gate_results",
    "source_file",
    "notes",
}
RECORD_FIELDS = {
    "date",
    "operator_or_agent",
    "medium_name",
    "medium_lot",
    "mea_coupon_id",
    "electrode_material",
    "hydrogel_matrix",
    "hydrogel_modulus_kpa",
    "hydrogel_thickness_um",
    "pedot_pss_loading_fraction",
    "pedot_pss_pre_rinse_protocol",
    "laminin_or_peptide_density",
    "crosslinking_protocol",
    "sterilization_or_aseptic_protocol",
    "membrane_lot",
    "mwco_kda",
    "membrane_area_cm2",
    "surface_modification",
    "prefilter_lot",
    "housing_material",
    "initial_volume_ml",
    "flow_rate_ul_min",
    "exposure_time_h",
    "cell_model",
    "culture_day",
    "medium_condition",
    "seeding_density",
}
IMAGE_FIELDS = {
    "visible_precipitate",
    "visible_shedding",
    "delamination_score",
    "optical_transparency_fraction",
    "electrode_window_access",
    "morphology_notes",
}
BIO_FIELDS = {
    "viability_fraction",
    "ldh_fold_control",
    "neurite_coverage_fraction",
    "mean_neurite_length_um",
    "viability_pct_hydrogel_control",
    "ldh_pct_hydrogel_control",
    "neurite_coverage_pct_hydrogel_control",
    "morphology_stress_score",
    "viability_metabolic_pct_control",
    "ldh_release_pct_control",
    "neurite_length_pct_control",
    "neurite_branching_pct_control",
    "cell_body_count_pct_control",
}
BIOCHEM_FIELDS = {
    "lactate_initial_mM",
    "lactate_final_mM",
    "ammonia_initial_uM",
    "ammonia_final_uM",
    "bdnf_initial_pg_ml",
    "bdnf_final_pg_ml",
    "ngf_initial_pg_ml",
    "ngf_final_pg_ml",
    "albumin_initial",
    "albumin_final",
    "transferrin_initial",
    "transferrin_final",
    "total_protein_initial",
    "total_protein_final",
}
FLOW_FIELDS = {
    "flow_resistance_initial",
    "flow_resistance_final",
    "bubble_events",
}
MEA_FIELDS = {
    "eis_1khz_initial_ohm",
    "eis_1khz_final_ohm",
    "eis_1khz_current_ohm",
    "eis_1khz_pct_hydrogel_control",
    "charge_storage_capacity_initial",
    "charge_storage_capacity_final",
    "charge_storage_capacity_current",
    "charge_storage_capacity_retention_fraction",
    "baseline_noise_uv",
    "electrode_yield_fraction",
    "spike_rate_hz",
    "burst_rate_hz",
    "electrode_yield_pct_hydrogel_control",
    "spike_rate_pct_hydrogel_control",
    "burst_rate_pct_hydrogel_control",
    "synchrony_pct_hydrogel_control",
    "network_spike_rate_pct_control",
    "burst_rate_pct_control",
    "synchrony_pct_control",
    "post_stim_spike_recovery_pct_pre",
    "post_stim_burst_recovery_pct_pre",
    "post_stim_impedance_degradation_pct",
}

CSV_FIELDS = [
    "profile",
    "run_id",
    "phase",
    "timepoint",
    "replicate",
    "article_id",
    "target_field",
    "value",
    "unit",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "source_file",
    "notes",
    "planned_value",
    "current_value",
    "source_class",
    "instrument_required",
    "recommended_source_file",
    "source_file_exists",
    "review_status",
    "missing_items",
    "capture_instruction",
]

PROFILES = {
    "nhi_forward": {
        "label": "NHI-PEDOT H-B/H-C",
        "plan": ROOT / "data" / "nhi_pedot_planned_runs.csv",
        "scope": ROOT / "data" / "nhi_pedot_forward_gate_rows.csv",
        "target": ROOT / "data" / "nhi_pedot_runs_template.csv",
        "csv": ROOT / "data" / "nhi_pedot_forward_source_values.csv",
        "json": ROOT / "data" / "nhi_pedot_forward_source_values_sheet.json",
        "report": ROOT / "reports" / "nhi_pedot_forward_source_values_sheet.md",
        "source_root": "data/source_files/full/nhi_pedot_forward",
        "status_prefix": "nhi_pedot_forward_source_values",
    },
    "nhi_long": {
        "label": "NHI-PEDOT long-duration",
        "plan": ROOT / "data" / "nhi_pedot_long_planned_runs.csv",
        "scope": None,
        "target": ROOT / "data" / "nhi_pedot_long_runs_template.csv",
        "csv": ROOT / "data" / "nhi_pedot_long_source_values.csv",
        "json": ROOT / "data" / "nhi_pedot_long_source_values_sheet.json",
        "report": ROOT / "reports" / "nhi_pedot_long_source_values_sheet.md",
        "source_root": "data/source_files/full/nhi_pedot_long",
        "status_prefix": "nhi_pedot_long_source_values",
    },
    "zrc_phase_a": {
        "label": "ZRC-ND Phase A",
        "plan": ROOT / "data" / "zrc_nd_phase_a_sentinel_template.csv",
        "scope": None,
        "target": ROOT / "data" / "zrc_nd_phase_a_vendor_return_inbox" / "completed_phase_a_measurements.csv",
        "csv": ROOT / "data" / "zrc_nd_phase_a_source_values.csv",
        "json": ROOT / "data" / "zrc_nd_phase_a_source_values_sheet.json",
        "report": ROOT / "reports" / "zrc_nd_phase_a_source_values_sheet.md",
        "source_root": "data/source_files/full/zrc_nd_phase_a",
        "status_prefix": "zrc_nd_phase_a_source_values",
    },
}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def clean(value: Any) -> str:
    return str(value or "").strip()


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path or not path.exists():
        return [], []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def row_key(row: dict[str, str]) -> str:
    return clean(row.get("run_id"))


def source_key(row: dict[str, str]) -> tuple[str, str]:
    return clean(row.get("run_id")), clean(row.get("target_field"))


def safe_name(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("_")


def source_class_for(field: str) -> str:
    if field in RECORD_FIELDS:
        return "bench_or_chain_of_custody_record"
    if field == "temperature_c":
        return "temperature_or_incubator_log"
    if field.startswith("pH"):
        return "pH_meter_export_or_photo"
    if "conductivity" in field:
        return "conductivity_meter_export_or_photo"
    if "osmolality" in field:
        return "osmometer_report_or_export"
    if field == "swelling_fraction":
        return "swelling_dimension_or_mass_worksheet"
    if field in IMAGE_FIELDS:
        return "image_or_scoring_worksheet"
    if field in BIO_FIELDS:
        return "biological_assay_or_imaging_export"
    if field in BIOCHEM_FIELDS:
        return "biochemical_or_plate_reader_export"
    if field in FLOW_FIELDS:
        return "pressure_flow_or_resistance_export"
    if field in MEA_FIELDS:
        return "electrochemical_or_mea_export"
    return "bench_or_chain_of_custody_record"


def source_suffix(source_class: str) -> str:
    if source_class in {"image_or_scoring_worksheet", "biological_assay_or_imaging_export"}:
        return ".png"
    if source_class == "osmometer_report_or_export":
        return ".pdf"
    return ".csv"


def instrument_required(field: str) -> bool:
    return source_class_for(field) not in {
        "bench_or_chain_of_custody_record",
        "supplier_or_build_record",
    }


def recommended_source_file(config: dict[str, Any], run_id: str, field: str) -> str:
    source_class = source_class_for(field)
    filename = f"{safe_name(field)}_{source_class}{source_suffix(source_class)}"
    return f"{config['source_root']}/{safe_name(run_id)}/{filename}"


def resolve_path(raw: str) -> Path:
    path = Path(clean(raw)).expanduser()
    return path if path.is_absolute() else ROOT / path


def target_fields_for_profile(profile: str, plan_fields: list[str], scope_rows: list[dict[str, str]]) -> dict[str, set[str]]:
    if profile == "nhi_forward":
        fields_by_run: dict[str, set[str]] = {}
        for row in scope_rows:
            run_id = row_key(row)
            required = {
                field
                for field in clean(row.get("required_fields")).split(";")
                if field and field not in LOCATOR_FIELDS
            }
            fields_by_run[run_id] = required
        return fields_by_run
    allowed = {field for field in plan_fields if field not in LOCATOR_FIELDS}
    return {row_key(row): set(allowed) for row in scope_rows}


def missing_items(row: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in ["value", "measured_at", "operator_or_agent", "source_file"]:
        if not clean(row.get(field)):
            missing.append(field)
    if clean(row.get("instrument_required")).lower() == "true" and not clean(row.get("instrument_id")):
        missing.append("instrument_id")
    if clean(row.get("source_file")) and not resolve_path(clean(row.get("source_file"))).is_file():
        missing.append("source_file_missing")
    return missing


def build_sheet(args: argparse.Namespace) -> dict[str, Any]:
    config = PROFILES[args.profile]
    plan_path = args.plan or config["plan"]
    scope_path = args.scope if args.scope is not None else config["scope"]
    target_path = args.target or config["target"]
    csv_path = args.csv_out or config["csv"]
    _plan_fields, plan_rows = load_csv(plan_path)
    _target_fields, target_rows = load_csv(target_path)
    _existing_fields, existing_rows = load_csv(csv_path)
    _scope_fields, raw_scope_rows = load_csv(scope_path) if scope_path else ([], [])
    scope_rows = raw_scope_rows if scope_path else plan_rows
    planned_by_run = {row_key(row): row for row in plan_rows if row_key(row)}
    target_by_run = {row_key(row): row for row in target_rows if row_key(row)}
    existing_by_key = {source_key(row): row for row in existing_rows if all(source_key(row))}
    fields_by_run = target_fields_for_profile(args.profile, _plan_fields, scope_rows)
    rows: list[dict[str, Any]] = []

    for run_id, fields in fields_by_run.items():
        planned = planned_by_run.get(run_id, {})
        current = target_by_run.get(run_id, {})
        if not planned:
            continue
        for field in sorted(fields):
            previous = existing_by_key.get((run_id, field), {})
            source_class = source_class_for(field)
            source_file = (
                clean(previous.get("source_file"))
                or recommended_source_file(config, run_id, field)
            )
            row = {
                "profile": args.profile,
                "run_id": run_id,
                "phase": clean(planned.get("phase")),
                "timepoint": clean(planned.get("timepoint")),
                "replicate": clean(planned.get("replicate")),
                "article_id": clean(planned.get("article_id")),
                "target_field": field,
                "value": clean(previous.get("value")),
                "unit": clean(previous.get("unit")),
                "measured_at": clean(previous.get("measured_at")),
                "operator_or_agent": clean(previous.get("operator_or_agent")),
                "instrument_id": clean(previous.get("instrument_id")),
                "source_file": source_file,
                "notes": clean(previous.get("notes")),
                "planned_value": clean(planned.get(field)),
                "current_value": clean(current.get(field)),
                "source_class": source_class,
                "instrument_required": str(instrument_required(field)).lower(),
                "recommended_source_file": recommended_source_file(config, run_id, field),
                "source_file_exists": str(resolve_path(source_file).is_file()).lower() if source_file else "false",
                "review_status": "",
                "missing_items": "",
                "capture_instruction": (
                    f"Enter the real {field} value for {run_id}, cite the raw source_file, "
                    "then run the matching wide source-value importer."
                ),
            }
            missing = missing_items(row)
            row["missing_items"] = ";".join(missing)
            if not clean(row["value"]):
                row["review_status"] = "awaiting_value_entry"
            elif missing:
                row["review_status"] = "blocked"
            else:
                row["review_status"] = "import_ready"
            rows.append(row)

    review_counts = Counter(row["review_status"] for row in rows)
    source_counts = Counter(row["source_class"] for row in rows)
    status_prefix = config["status_prefix"]
    status = f"{status_prefix}_sheet_ready" if rows else f"{status_prefix}_sheet_no_rows"
    return {
        "status": status,
        "profile": args.profile,
        "summary": {
            "source_value_rows": len(rows),
            "filled_value_rows": sum(1 for row in rows if clean(row.get("value"))),
            "source_file_exists_rows": sum(1 for row in rows if row["source_file_exists"] == "true"),
            "import_ready_rows": review_counts.get("import_ready", 0),
            "review_status_counts": dict(review_counts),
            "source_class_counts": dict(source_counts),
        },
        "inputs": {"plan": rel(plan_path), "scope": rel(scope_path) if scope_path else "", "target": rel(target_path)},
        "generated_artifacts": {"csv": rel(csv_path), "json": rel(args.json_out or config["json"]), "report": rel(args.report or config["report"])},
        "rows": rows,
        "boundary": "This source-values sheet is sidecar metadata only; it is not measured evidence.",
    }


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        f"# {PROFILES[result['profile']]['label']} Source Values Sheet",
        "",
        "This renders fillable, source-backed values for a wide evaluator run table. It is not measured evidence.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Rows:** {summary['source_value_rows']}",
        f"**Filled values:** {summary['filled_value_rows']}",
        f"**Rows with existing source files:** {summary['source_file_exists_rows']}",
        f"**Import-ready rows:** {summary['import_ready_rows']}",
        f"**CSV:** `{result['generated_artifacts']['csv']}`",
        "",
        "## Source Classes",
        "",
        "| Source class | Rows |",
        "| --- | ---: |",
    ]
    for source_class, count in sorted(summary["source_class_counts"].items()):
        lines.append(f"| `{source_class}` | {count} |")

    lines.extend([
        "",
        "## Rows",
        "",
        "| Run | Phase | Field | Review | Missing items | Source file |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for row in result["rows"][:80]:
        lines.append(
            f"| `{row['run_id']}` | `{row['phase']}` | `{row['target_field']}` | "
            f"`{row['review_status']}` | `{row['missing_items'] or '-'}` | `{md_cell(row['source_file'])}` |"
        )
    omitted = len(result["rows"]) - 80
    if omitted > 0:
        lines.append(f"| `-` | `-` | `-` | `-` | `-` | {omitted} additional rows omitted. |")
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a wide source-values sidecar.")
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--scope", type=Path)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--csv-out", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--report", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = PROFILES[args.profile]
    args.csv_out = args.csv_out or config["csv"]
    args.json_out = args.json_out or config["json"]
    args.report = args.report or config["report"]
    result = build_sheet(args)
    write_csv(args.csv_out, result["rows"])
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result), encoding="utf-8")
    print(f"{PROFILES[args.profile]['label']} source values sheet: {result['status']}")
    print(f"Rows: {result['summary']['source_value_rows']}")
    print(f"Import-ready rows: {result['summary']['import_ready_rows']}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
