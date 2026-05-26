#!/usr/bin/env python3
"""Render the LIMINA source-file manifest and auditable drop locations."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "data" / "limina_source_file_manifest.json"
DEFAULT_CSV = ROOT / "data" / "limina_source_file_manifest.csv"
DEFAULT_REPORT = ROOT / "reports" / "limina_source_file_manifest.md"
DEFAULT_README = ROOT / "data" / "source_files" / "README.md"

ROOT_ROWS = [
    {
        "root_id": "local_h_a_full",
        "path": "data/source_files/full/h_a",
        "scope": "NHI-PEDOT H-A full local capture",
        "purpose": "Local instrument exports, photos, worksheets, calibration logs, and bench records for the full H-A matrix.",
    },
    {
        "root_id": "local_zrc_full",
        "path": "data/source_files/full/zrc_nd_phase_a",
        "scope": "ZRC-ND Phase A full local capture",
        "purpose": "Local records and instrument outputs for the full ZRC-ND Phase A matrix.",
    },
    {
        "root_id": "local_nhi_forward_full",
        "path": "data/source_files/full/nhi_pedot_forward",
        "scope": "NHI-PEDOT H-B/H-C full local capture",
        "purpose": "Local instrument exports, images, worksheets, and biological assay records for NHI-PEDOT H-B/H-C coupon gates.",
    },
    {
        "root_id": "local_nhi_long_full",
        "path": "data/source_files/full/nhi_pedot_long",
        "scope": "NHI-PEDOT long-duration full local capture",
        "purpose": "Long-duration MEA, neural health, stimulus-recovery, imaging, and material-integrity records for NHI-PEDOT.",
    },
    {
        "root_id": "local_zrc_bio_full",
        "path": "data/source_files/full/zrc_nd_bio",
        "scope": "ZRC-ND biological follow-up full local capture",
        "purpose": "Biological assay records, imaging, MEA outputs, and worksheets for ZRC-ND conditioned-medium follow-up gates.",
    },
    {
        "root_id": "smoke_h_a",
        "path": "data/source_files/smoke/h_a",
        "scope": "NHI-PEDOT H-A smoke capture",
        "purpose": "Minimal source files for the smoke-tranche H-A pipeline rehearsal.",
    },
    {
        "root_id": "smoke_zrc",
        "path": "data/source_files/smoke/zrc_nd_phase_a",
        "scope": "ZRC-ND Phase A smoke capture",
        "purpose": "Minimal source files for the smoke-tranche ZRC-ND pipeline rehearsal.",
    },
    {
        "root_id": "calibration_logs",
        "path": "data/source_files/calibration_logs",
        "scope": "shared measurement provenance",
        "purpose": "Calibration or standard-check files referenced by pH, conductivity, temperature, osmometer, image, mass, or dimension records.",
    },
    {
        "root_id": "bench_records",
        "path": "data/source_files/bench_records",
        "scope": "shared local capture",
        "purpose": "Bench logs, pipetting worksheets, chain-of-custody exports, and operator worksheets.",
    },
    {
        "root_id": "build_records",
        "path": "data/source_files/build_records",
        "scope": "supplier/build provenance",
        "purpose": "Recipe records, supplier CoAs, sample labels, coating logs, and build sheets.",
    },
    {
        "root_id": "h_a_vendor_exports",
        "path": "data/nhi_pedot_h_a_vendor_return_inbox/external_lab_exports",
        "scope": "NHI-PEDOT H-A vendor/cooperator returns",
        "purpose": "Original external lab exports, reports, images, and worksheets referenced by returned H-A rows.",
    },
    {
        "root_id": "zrc_vendor_exports",
        "path": "data/zrc_nd_phase_a_vendor_return_inbox/external_lab_exports",
        "scope": "ZRC-ND Phase A vendor/cooperator returns",
        "purpose": "Original external lab exports, reports, images, and worksheets referenced by returned ZRC-ND rows.",
    },
]

SOURCE_CLASS_ROWS = [
    {
        "source_class": "pH_meter_export_or_photo",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.png;.jpg;.jpeg;.heic",
        "required_metadata": "run_id, measurement date, instrument_id or calibration record",
        "task_signals": "pH,pH_initial,pH_final",
        "recommended_roots": "local_h_a_full;local_nhi_forward_full;local_nhi_long_full;smoke_h_a;calibration_logs;h_a_vendor_exports;zrc_vendor_exports",
        "notes": "Raw meter export is preferred; display photo must be time-stamped or paired with a worksheet.",
    },
    {
        "source_class": "conductivity_meter_export_or_photo",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.png;.jpg;.jpeg;.heic",
        "required_metadata": "run_id, measurement date, instrument_id or standard-check record",
        "task_signals": "conductivity,conductivity_initial_mS_cm,conductivity_final_mS_cm",
        "recommended_roots": "local_h_a_full;local_nhi_forward_full;local_nhi_long_full;smoke_h_a;calibration_logs;h_a_vendor_exports;zrc_vendor_exports",
        "notes": "Include calibration or standard-check evidence for media-range measurements.",
    },
    {
        "source_class": "osmometer_report_or_export",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.png;.jpg;.jpeg",
        "required_metadata": "run_id, mOsm/kg value, vendor or osmometer identifier",
        "task_signals": "osmolality,osmolality_initial_mOsm_kg,osmolality_final_mOsm_kg",
        "recommended_roots": "h_a_vendor_exports;zrc_vendor_exports;local_h_a_full;local_nhi_forward_full;local_nhi_long_full;smoke_h_a;smoke_zrc;calibration_logs",
        "notes": "External lab report/export must reconcile each returned value to a run_id.",
    },
    {
        "source_class": "temperature_or_incubator_log",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.png;.jpg;.jpeg;.heic",
        "required_metadata": "run_id or batch window, date/time, temperature source",
        "task_signals": "temperature_c",
        "recommended_roots": "local_h_a_full;local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;smoke_h_a;bench_records;h_a_vendor_exports;zrc_vendor_exports",
        "notes": "A single incubator log can support multiple run_ids if the covered time window is explicit.",
    },
    {
        "source_class": "image_or_scoring_worksheet",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.png;.jpg;.jpeg;.heic;.tif;.tiff",
        "required_metadata": "run_id, imaging/scoring method, operator or vendor",
        "task_signals": "visible_precipitate,visible_shedding,delamination_score,optical_transparency_fraction",
        "recommended_roots": "local_h_a_full;local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;smoke_h_a;smoke_zrc;bench_records;h_a_vendor_exports;zrc_vendor_exports",
        "notes": "Keep raw images plus the scoring worksheet or vendor image-analysis report.",
    },
    {
        "source_class": "swelling_dimension_or_mass_worksheet",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.png;.jpg;.jpeg",
        "required_metadata": "run_id, pre/post measurement basis, method, operator",
        "task_signals": "swelling_fraction,membrane_area_cm2,initial_volume_ml",
        "recommended_roots": "local_h_a_full;local_nhi_forward_full;local_nhi_long_full;smoke_h_a;smoke_zrc;bench_records;h_a_vendor_exports;zrc_vendor_exports",
        "notes": "Worksheet must show enough raw dimensions, area, volume, or mass to reproduce the reported value.",
    },
    {
        "source_class": "bench_or_chain_of_custody_record",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.md;.png;.jpg;.jpeg",
        "required_metadata": "run_id or sample_id, operator, date, transfer or exposure event",
        "task_signals": "date,medium_name,medium_lot,operator_or_agent,exposure_time_h",
        "recommended_roots": "bench_records;build_records;local_h_a_full;local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;smoke_h_a;smoke_zrc;h_a_vendor_exports;zrc_vendor_exports",
        "notes": "Used for setup metadata and transfer provenance; not a substitute for instrument output when a measured value is present.",
    },
    {
        "source_class": "supplier_or_build_record",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.md;.png;.jpg;.jpeg",
        "required_metadata": "lot, recipe, CoA, label, or build identifier",
        "task_signals": "membrane_lot,prefilter_lot,electrode_material,laminin_or_peptide_density,sterilization_or_aseptic_protocol",
        "recommended_roots": "build_records;bench_records;local_zrc_full;local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;smoke_zrc;h_a_vendor_exports;zrc_vendor_exports",
        "notes": "Supplier/build records are provenance only; they do not become performance evidence by themselves.",
    },
    {
        "source_class": "electrochemical_or_mea_export",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.png;.jpg;.jpeg",
        "required_metadata": "run_id, measurement date, instrument_id, channel/electrode mapping, and analysis method",
        "task_signals": "eis_1khz,charge_storage_capacity,spike_rate,burst_rate,synchrony,electrode_yield,baseline_noise,post_stim",
        "recommended_roots": "local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;calibration_logs",
        "notes": "Keep raw MEA/electrochemical export plus the analysis worksheet when values are derived.",
    },
    {
        "source_class": "biological_assay_or_imaging_export",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.png;.jpg;.jpeg;.tif;.tiff",
        "required_metadata": "run_id, culture model, assay date, operator or vendor, instrument_id or imaging/export method",
        "task_signals": "viability,ldh,neurite,morphology,cell_body_count,cell_model,seeding_density",
        "recommended_roots": "local_nhi_forward_full;local_nhi_long_full;local_zrc_bio_full;bench_records",
        "notes": "Assay summaries must cite raw plate-reader, imaging, or MEA-derived files, not transcribed notes alone.",
    },
    {
        "source_class": "biochemical_or_plate_reader_export",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.png;.jpg;.jpeg",
        "required_metadata": "run_id, analyte, assay date, instrument_id or vendor report id, calibration/standard curve record",
        "task_signals": "lactate,ammonia,bdnf,ngf,albumin,transferrin,total_protein",
        "recommended_roots": "local_zrc_full;local_zrc_bio_full;zrc_vendor_exports;calibration_logs",
        "notes": "Keep raw analyzer, plate-reader, ELISA, or vendor chemistry export with enough metadata to reconcile each analyte to run_id.",
    },
    {
        "source_class": "pressure_flow_or_resistance_export",
        "accepted_extensions": ".csv;.tsv;.xlsx;.pdf;.png;.jpg;.jpeg",
        "required_metadata": "run_id, flow/pressure method, instrument_id, time window, calculation method",
        "task_signals": "flow_resistance,flow_rate,bubble_events",
        "recommended_roots": "local_zrc_full;zrc_vendor_exports;bench_records",
        "notes": "Flow resistance and bubble-event records must preserve raw pressure/flow or imaging/inspection evidence, not only pass/fail transcription.",
    },
]

REJECTED_SOURCE_MARKERS = [
    "email",
    "quote",
    "verbal",
    "capability",
    "phone_call",
    "synthetic",
    "fixture",
    "placeholder",
]

CSV_FIELDS = [
    "record_type",
    "id",
    "path_or_class",
    "scope",
    "purpose_or_metadata",
    "accepted_extensions",
    "recommended_roots",
    "notes",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def ensure_roots(rows: list[dict[str, str]]) -> None:
    for row in rows:
        (ROOT / row["path"]).mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in CSV_FIELDS} for row in rows])


def csv_rows(manifest: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in manifest["allowed_roots"]:
        rows.append({
            "record_type": "allowed_root",
            "id": item["root_id"],
            "path_or_class": item["path"],
            "scope": item["scope"],
            "purpose_or_metadata": item["purpose"],
            "accepted_extensions": "",
            "recommended_roots": "",
            "notes": "",
        })
    for item in manifest["expected_source_classes"]:
        rows.append({
            "record_type": "source_class",
            "id": item["source_class"],
            "path_or_class": item["task_signals"],
            "scope": "filled capture row source_file",
            "purpose_or_metadata": item["required_metadata"],
            "accepted_extensions": item["accepted_extensions"],
            "recommended_roots": item["recommended_roots"],
            "notes": item["notes"],
        })
    return rows


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    ensure_roots(ROOT_ROWS)
    return {
        "status": "source_file_manifest_ready",
        "allowed_roots": ROOT_ROWS,
        "expected_source_classes": SOURCE_CLASS_ROWS,
        "rejected_source_markers": REJECTED_SOURCE_MARKERS,
        "policy": {
            "must_exist": True,
            "must_be_file": True,
            "must_be_inside_allowed_root": True,
            "relative_paths_resolve_from": rel(ROOT),
            "multi_file_separator": "semicolon, pipe, or newline",
            "not_evidence": "Emails, quotes, verbal notes, vendor capability replies, fixtures, synthetic data, and placeholders are never measured evidence.",
        },
        "generated_artifacts": {
            "json": rel(args.json_out),
            "csv": rel(args.csv_out),
            "readme": rel(args.readme),
            "report": rel(args.report),
        },
        "boundary": "This manifest is a provenance guardrail. It creates drop locations and policy only; it does not create measured evidence.",
    }


def render_readme(manifest: dict[str, Any]) -> str:
    lines = [
        "# LIMINA Source Files",
        "",
        "Place real raw exports, photos, reports, worksheets, calibration logs, and build records here before filling `source_file` fields.",
        "",
        "Do not use emails, quotes, verbal notes, capability claims, synthetic fixtures, or placeholder files as measured evidence.",
        "",
        "## Allowed Roots",
        "",
    ]
    for row in manifest["allowed_roots"]:
        lines.append(f"- `{row['path']}`: {row['purpose']}")
    lines.extend(["", "Run `python3 scripts/preflight_limina_local_capture.py` after entries are filled.", ""])
    return "\n".join(lines)


def render_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# LIMINA Source-File Manifest",
        "",
        "This manifest defines where auditable source files must live before local/outsource capture rows can pass preflight.",
        "",
        f"**Status:** `{manifest['status']}`",
        f"**Allowed roots:** {len(manifest['allowed_roots'])}",
        f"**Expected source classes:** {len(manifest['expected_source_classes'])}",
        "",
        "## Allowed Roots",
        "",
        "| Root | Path | Scope | Purpose |",
        "| --- | --- | --- | --- |",
    ]
    for row in manifest["allowed_roots"]:
        lines.append(f"| `{row['root_id']}` | `{row['path']}` | {row['scope']} | {row['purpose']} |")
    lines.extend([
        "",
        "## Source Classes",
        "",
        "| Source class | Task signals | Required metadata | Recommended roots |",
        "| --- | --- | --- | --- |",
    ])
    for row in manifest["expected_source_classes"]:
        lines.append(
            f"| `{row['source_class']}` | `{row['task_signals']}` | "
            f"{row['required_metadata']} | `{row['recommended_roots']}` |"
        )
    lines.extend([
        "",
        "## Rejected Sources",
        "",
        "- " + ", ".join(f"`{item}`" for item in manifest["rejected_source_markers"]),
        "",
        "## Boundary",
        "",
        manifest["boundary"],
        "",
    ])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render LIMINA source-file manifest and drop locations.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--readme", type=Path, default=DEFAULT_README)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = build_manifest(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.csv_out, csv_rows(manifest))
    args.readme.parent.mkdir(parents=True, exist_ok=True)
    args.readme.write_text(render_readme(manifest), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(manifest), encoding="utf-8")
    print(f"Source-file manifest: {manifest['status']}")
    print(f"Allowed roots: {len(manifest['allowed_roots'])}")
    print(f"Expected source classes: {len(manifest['expected_source_classes'])}")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
