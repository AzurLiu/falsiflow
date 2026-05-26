#!/usr/bin/env python3
"""Validate cross-file LIMINA references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_records(path: Path) -> list[dict[str, Any]]:
    value = load_json(path)
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return value
    raise ValueError(f"{path} must contain a JSON object or list")


def evidence_ids() -> set[str]:
    return {record["id"] for record in load_records(ROOT / "data" / "evidence_records_seed.json")}


def check_refs(label: str, record: dict[str, Any], refs: list[str], known: set[str]) -> list[str]:
    errors = []
    for ref in refs:
        if ref.startswith("http"):
            continue
        if ref not in known:
            errors.append(f"{label} {record.get('id', '<unknown>')}: unknown evidence ref {ref}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LIMINA data references.")
    parser.add_argument("--report", type=Path, default=ROOT / "reports" / "data_validation.md")
    args = parser.parse_args()

    known = evidence_ids()
    errors: list[str] = []

    for record in load_records(ROOT / "data" / "external_material_candidates.json"):
        errors.extend(check_refs("external_candidate", record, record.get("evidence_refs", []), known))

    for record in load_records(ROOT / "data" / "limina_material_technologies.json"):
        errors.extend(check_refs("technology", record, record.get("evidence_refs", []), known))

    for record in load_records(ROOT / "data" / "limina_discovery_candidates.json"):
        errors.extend(check_refs("discovery_candidate", record, record.get("evidence_refs", []), known))

    for record in load_records(ROOT / "data" / "nhi_pedot_recipe_lock_v0_2.json"):
        errors.extend(check_refs("recipe_lock", record, record.get("evidence_refs", []), known))

    variant_ladder = ROOT / "data" / "nhi_pedot_variant_ladder.json"
    if variant_ladder.exists():
        record = load_json(variant_ladder)
        for item in record.get("items", []):
            refs = item.get("evidence_refs", "")
            if isinstance(refs, str):
                refs = [ref for ref in refs.split(";") if ref]
            errors.extend(check_refs("nhi_pedot_variant_ladder", item, refs, known))

    for record in load_records(ROOT / "data" / "nhi_pedot_alg_lam_protocol_v0_2.json"):
        refs = [record.get("source_evidence", "")]
        errors.extend(check_refs("protocol", record, refs, known))

    for record in load_records(ROOT / "data" / "zrc_nd_variants.json"):
        errors.extend(check_refs("zrc_nd_variant", record, record.get("evidence_refs", []), known))

    for record in load_records(ROOT / "data" / "zrc_nd_coating_routes.json"):
        errors.extend(check_refs("zrc_nd_coating_route", record, record.get("evidence_refs", []), known))

    validation_packages = [
        ROOT / "data" / "zrc_nd_3p5k_guard_validation_package.json",
        ROOT / "data" / "nhi_pedot_validation_package.json",
    ]
    for path in validation_packages:
        for record in load_records(path):
            errors.extend(check_refs("validation_package", record, record.get("source_refs", []), known))
            for spec in record.get("procurement_specs", []):
                errors.extend(check_refs("validation_package.procurement_spec", spec, spec.get("evidence_refs", []), known))
            for assay in record.get("assay_panel", []):
                errors.extend(check_refs("validation_package.assay", assay, assay.get("evidence_refs", []), known))

    for record in load_records(ROOT / "data" / "zrc_nd_biological_followup_package.json"):
        errors.extend(check_refs("biological_followup", record, record.get("source_refs", []), known))
        for assay in record.get("assay_panel", []):
            errors.extend(check_refs("biological_followup.assay", assay, assay.get("evidence_refs", []), known))

    for record in load_records(ROOT / "data" / "nhi_pedot_long_followup_package.json"):
        errors.extend(check_refs("biological_followup", record, record.get("source_refs", []), known))
        for assay in record.get("assay_panel", []):
            errors.extend(check_refs("biological_followup.assay", assay, assay.get("evidence_refs", []), known))

    for record in load_records(ROOT / "data" / "zrc_nd_bom.json"):
        errors.extend(check_refs("bom", record, record.get("source_refs", []), known))
        for item in record.get("items", []):
            errors.extend(check_refs("bom.item", item, item.get("evidence_refs", []), known))

    for path in [ROOT / "data" / "external1_baseline_experiment.json"]:
        record = load_json(path)
        evidence_like = [ref for ref in record.get("source_refs", []) if not ref.startswith("http")]
        errors.extend(check_refs("experiment", record, evidence_like, known))

    args.report.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# LIMINA Data Validation", ""]
    if errors:
        lines.append("Status: **fail**")
        lines.append("")
        lines.extend(f"- {error}" for error in errors)
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Validation failed with {len(errors)} error(s)")
        print(f"Wrote {args.report}")
        return 1

    lines.append("Status: **pass**")
    lines.append("")
    lines.append(
        f"Validated {len(known)} evidence ids against candidate, technology, "
        "discovery queue, NHI-PEDOT adaptive ladder, ZRC-ND variant, coating route, validation package, "
        "biological follow-up, BOM, and experiment references."
    )
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Validation passed for {len(known)} evidence ids")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
