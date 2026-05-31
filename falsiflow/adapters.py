"""Adapters that translate existing project sidecars into Falsiflow inputs."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .core import write_csv


EVIDENCE_FIELDS = [
    "gate_id",
    "candidate_id",
    "sample_id",
    "field",
    "value",
    "source_file",
    "measured_at",
    "operator_or_agent",
    "instrument_id",
    "notes",
]

PHASE_TO_GATE = {
    "H-A": "h_a_medium_stability",
    "H-B": "h_b_electrical_interface",
    "H-C": "h_c_network_response",
}

GATE_TITLES = {
    "h_a_medium_stability": "H-A medium stability and physical integrity",
    "h_b_electrical_interface": "H-B electrical and physical interface benefit",
    "h_c_network_response": "H-C cell and network response",
}

DEFAULT_PLACEHOLDERS = [
    "pending_real_measurement",
    "record_actual",
    "record_exact",
    "record_lot",
    "source_file_missing",
    "to_be_recorded",
    "not_measured",
]

ADAPTER_PROFILES: dict[str, dict[str, object]] = {
    "generic-wide": {
        "description": "Generic wide CSV with sample_id plus measured value columns.",
        "kind": "wide-csv",
        "sample_id_column": "sample_id",
        "gate_id_column": "",
        "candidate_id_column": "",
        "source_file_column": "",
        "measured_at_column": "",
        "operator_or_agent_column": "",
        "instrument_id_column": "",
        "notes_column": "",
        "exclude_columns": [],
    },
    "vendor-measurement": {
        "description": "Vendor or external-lab measurement return with sample, source file, contact, instrument, and notes columns.",
        "kind": "wide-csv",
        "sample_id_column": "sample",
        "gate_id_column": "",
        "candidate_id_column": "article",
        "source_file_column": "source_file",
        "measured_at_column": "measured_at",
        "operator_or_agent_column": "vendor_contact",
        "instrument_id_column": "instrument_id",
        "notes_column": "notes",
        "exclude_columns": ["vendor", "quote_id", "work_order"],
    },
    "instrument-export": {
        "description": "Instrument export with sample_id, timestamp, operator, instrument_id, raw_file, and measured columns.",
        "kind": "wide-csv",
        "sample_id_column": "sample_id",
        "gate_id_column": "",
        "candidate_id_column": "candidate_id",
        "source_file_column": "raw_file",
        "measured_at_column": "timestamp",
        "operator_or_agent_column": "operator",
        "instrument_id_column": "instrument_id",
        "notes_column": "notes",
        "exclude_columns": ["run_id", "method", "batch_id"],
    },
    "plate-reader": {
        "description": "Plate-reader style export with well_id, read_at, operator, plate_reader_id, raw_file, and assay columns.",
        "kind": "wide-csv",
        "sample_id_column": "well_id",
        "gate_id_column": "",
        "candidate_id_column": "sample_name",
        "source_file_column": "raw_file",
        "measured_at_column": "read_at",
        "operator_or_agent_column": "operator",
        "instrument_id_column": "plate_reader_id",
        "notes_column": "notes",
        "exclude_columns": ["plate_id", "assay_id", "well_id"],
    },
    "ai-eval": {
        "description": "AI eval JSON, JSONL, or metric CSV plus an optional manifest, mapped to the ai_claim_evaluation template.",
        "kind": "eval-artifact",
    },
    "local-llm-eval": {
        "description": "Local or private LLM eval artifacts with model/runtime manifest metadata, mapped to the ai_claim_evaluation template.",
        "kind": "eval-artifact",
    },
    "rag-eval": {
        "description": "RAG eval JSON, JSONL, or metric CSV plus an optional manifest, mapped to the rag_quality_gate template.",
        "kind": "eval-artifact",
    },
}

EVAL_IMPORT_PROFILE_NAMES = {"ai-eval", "local-llm-eval", "rag-eval"}


def adapter_profile_names() -> list[str]:
    return sorted(ADAPTER_PROFILES)


def adapter_profile_kind(profile: str) -> str:
    if profile not in ADAPTER_PROFILES:
        raise ValueError(f"Unknown adapter profile `{profile}`. Expected one of: {', '.join(adapter_profile_names())}.")
    return str(ADAPTER_PROFILES[profile].get("kind", "wide-csv"))


def adapter_profile_summary() -> list[dict[str, object]]:
    return [
        {
            "profile": name,
            **profile,
        }
        for name, profile in sorted(ADAPTER_PROFILES.items())
    ]


def resolve_wide_adapter_settings(
    profile: str,
    sample_id_column: str,
    exclude_columns: list[str],
    gate_id_column: str,
    candidate_id_column: str,
    source_file_column: str,
    measured_at_column: str,
    operator_or_agent_column: str,
    instrument_id_column: str,
    notes_column: str,
) -> dict[str, object]:
    if profile not in ADAPTER_PROFILES:
        raise ValueError(f"Unknown adapter profile `{profile}`. Expected one of: {', '.join(adapter_profile_names())}.")
    profile_data = ADAPTER_PROFILES[profile]
    if str(profile_data.get("kind", "wide-csv")) != "wide-csv":
        raise ValueError(f"Adapter profile `{profile}` imports eval artifacts and cannot be used as a wide CSV profile.")

    def column(name: str, override: str) -> str:
        return clean(override) or clean(profile_data.get(name, ""))

    profile_excludes = [str(item) for item in profile_data.get("exclude_columns", []) if str(item)]
    merged_excludes = list(dict.fromkeys([*profile_excludes, *exclude_columns]))
    settings = {
        "profile": profile,
        "profile_description": str(profile_data.get("description", "")),
        "sample_id_column": column("sample_id_column", sample_id_column),
        "gate_id_column": column("gate_id_column", gate_id_column),
        "candidate_id_column": column("candidate_id_column", candidate_id_column),
        "source_file_column": column("source_file_column", source_file_column),
        "measured_at_column": column("measured_at_column", measured_at_column),
        "operator_or_agent_column": column("operator_or_agent_column", operator_or_agent_column),
        "instrument_id_column": column("instrument_id_column", instrument_id_column),
        "notes_column": column("notes_column", notes_column),
        "exclude_columns": merged_excludes,
    }
    if not settings["sample_id_column"]:
        raise ValueError(f"Adapter profile `{profile}` does not define a sample_id_column and no --sample-id-column override was provided.")
    return settings


def rule(field: str, operator: str, value: Any, reason: str, **filters: Any) -> dict[str, Any]:
    payload = {
        "field": field,
        "operator": operator,
        "value": value,
        "reason": reason,
    }
    payload.update({key: val for key, val in filters.items() if val})
    return payload


def derived(field: str, operation: str, **refs: str) -> dict[str, str]:
    payload = {"field": field, "operation": operation}
    payload.update(refs)
    return payload


def add_if_fields_present(
    gate: dict[str, Any],
    available_fields: set[str],
    required_fields: set[str],
    derived_field: dict[str, Any] | None = None,
    acceptance_rule: dict[str, Any] | None = None,
) -> None:
    if not required_fields <= available_fields:
        return
    if derived_field is not None:
        gate.setdefault("derived_fields", []).append(derived_field)
    if acceptance_rule is not None:
        gate.setdefault("acceptance_rules", []).append(acceptance_rule)


def apply_limina_scientific_overlay(gate: dict[str, Any], available_fields: set[str]) -> None:
    gate_id = str(gate.get("id", ""))
    if gate_id == "h_a_medium_stability":
        add_if_fields_present(
            gate,
            available_fields,
            {"initial.pH", "final.pH"},
            derived("ph_drift_abs", "abs_delta", left="final.pH", right="initial.pH"),
            rule("ph_drift_abs", "<=", 0.10, "H-A pH drift must remain within 0.10 pH units."),
        )
        add_if_fields_present(
            gate,
            available_fields,
            {"initial.osmolality", "final.osmolality"},
            derived(
                "osmolality_drift_pct",
                "abs_pct_change",
                before="initial.osmolality",
                after="final.osmolality",
            ),
            rule("osmolality_drift_pct", "<=", 5, "H-A osmolality drift must remain within 5 percent."),
        )
        add_if_fields_present(
            gate,
            available_fields,
            {"initial.conductivity", "final.conductivity"},
            derived(
                "conductivity_drift_pct",
                "abs_pct_change",
                before="initial.conductivity",
                after="final.conductivity",
            ),
            rule("conductivity_drift_pct", "<=", 5, "H-A conductivity drift must remain within 5 percent."),
        )
        add_if_fields_present(
            gate,
            available_fields,
            {"physical_inspection.visible_precipitate"},
            acceptance_rule=rule(
                "physical_inspection.visible_precipitate",
                "==",
                False,
                "H-A must show no visible precipitate.",
            ),
        )
        add_if_fields_present(
            gate,
            available_fields,
            {"physical_inspection.visible_shedding"},
            acceptance_rule=rule(
                "physical_inspection.visible_shedding",
                "==",
                False,
                "H-A must show no visible shedding.",
            ),
        )
        add_if_fields_present(
            gate,
            available_fields,
            {"physical_inspection.swelling_fraction"},
            acceptance_rule=rule(
                "physical_inspection.swelling_fraction",
                "<=",
                0.20,
                "H-A swelling must remain below 20 percent.",
            ),
        )
    if gate_id == "h_b_electrical_interface":
        add_if_fields_present(
            gate,
            available_fields,
            {"eis_1khz_initial_ohm", "eis_1khz_final_ohm"},
            derived(
                "eis_1khz_reduction_pct",
                "reduction_pct",
                before="eis_1khz_initial_ohm",
                after="eis_1khz_final_ohm",
            ),
            rule(
                "eis_1khz_reduction_pct",
                ">=",
                25,
                "Lead H-B electrical readout must improve impedance by at least 25 percent.",
                candidate_id_contains="lead_nhi_pedot_low_loading",
            ),
        )
        add_if_fields_present(
            gate,
            available_fields,
            {"charge_storage_capacity_initial", "charge_storage_capacity_final"},
            derived(
                "charge_storage_gain_pct",
                "gain_pct",
                before="charge_storage_capacity_initial",
                after="charge_storage_capacity_final",
            ),
            rule(
                "charge_storage_gain_pct",
                ">=",
                15,
                "Lead H-B electrical readout must improve charge storage by at least 15 percent.",
                candidate_id_contains="lead_nhi_pedot_low_loading",
            ),
        )
        for field, op, value, reason in [
            ("swelling_fraction", "<=", 0.20, "H-B swelling must remain below 20 percent."),
            ("delamination_score", "<=", 0, "H-B must show no delamination."),
            ("optical_transparency_fraction", ">=", 0.80, "H-B transparency must remain inspectable."),
        ]:
            add_if_fields_present(gate, available_fields, {field}, acceptance_rule=rule(field, op, value, reason))
    if gate_id == "h_c_network_response":
        for field, op, value, reason in [
            ("viability_fraction", ">=", 0.85, "H-C lead viability must remain non-inferior enough to continue."),
            ("ldh_fold_control", "<=", 1.20, "H-C lead cytotoxicity must not materially exceed control."),
            ("electrode_yield_fraction", ">=", 0.80, "H-C lead electrode yield must remain acceptable."),
        ]:
            add_if_fields_present(
                gate,
                available_fields,
                {field},
                acceptance_rule=rule(
                    field,
                    op,
                    value,
                    reason,
                    candidate_id_contains="lead_nhi_pedot_low_loading",
                ),
            )


def clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def infer_phase(row: dict[str, str]) -> str:
    phase = clean(row.get("phase"))
    if phase:
        return phase
    run_id = clean(row.get("run_id"))
    for phase_id in PHASE_TO_GATE:
        if f"-{phase_id}-" in run_id:
            return phase_id
    return ""


def infer_gate_id(row: dict[str, str], default_gate: str) -> str:
    return PHASE_TO_GATE.get(infer_phase(row), default_gate)


def infer_candidate_id(row: dict[str, str], default_candidate: str) -> str:
    for field in ["variant_id", "article_id", "candidate_id"]:
        value = clean(row.get(field))
        if value:
            return value
    run_id = clean(row.get("run_id"))
    match = re.match(r"^NHIPEDOT-H-[ABC]-(.+?)-R\d+", run_id)
    if not match:
        match = re.match(r"^NHIPEDOT-LONG-[^-]+-(.+?)-R\d+", run_id)
    return match.group(1) if match else default_candidate


def infer_field_id(row: dict[str, str]) -> str:
    target = clean(row.get("target_field") or row.get("field"))
    sample_event = clean(row.get("sample_event"))
    if sample_event:
        return f"{sample_event}.{target}"
    return target


def limina_source_value_to_evidence(
    row: dict[str, str],
    default_candidate: str,
    default_gate: str,
) -> dict[str, str] | None:
    sample_id = clean(row.get("run_id") or row.get("sample_id"))
    field_id = infer_field_id(row)
    gate_id = infer_gate_id(row, default_gate)
    if not sample_id or not field_id or not gate_id:
        return None
    return {
        "gate_id": gate_id,
        "candidate_id": infer_candidate_id(row, default_candidate),
        "sample_id": sample_id,
        "field": field_id,
        "value": clean(row.get("value")),
        "source_file": clean(row.get("source_file")),
        "measured_at": clean(row.get("measured_at")),
        "operator_or_agent": clean(row.get("operator_or_agent")),
        "instrument_id": clean(row.get("instrument_id")),
        "notes": clean(row.get("notes")),
    }


def convert_limina_source_values(
    inputs: list[Path],
    default_candidate: str,
    default_gate: str,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    evidence_rows: list[dict[str, str]] = []
    skipped_rows = 0
    input_summaries = []
    for path in inputs:
        rows = read_csv(path)
        before = len(evidence_rows)
        for row in rows:
            evidence = limina_source_value_to_evidence(row, default_candidate, default_gate)
            if evidence is None:
                skipped_rows += 1
                continue
            evidence_rows.append(evidence)
        input_summaries.append({
            "path": str(path),
            "input_rows": len(rows),
            "evidence_rows": len(evidence_rows) - before,
        })
    return evidence_rows, {
        "status": "converted",
        "inputs": input_summaries,
        "evidence_rows": len(evidence_rows),
        "skipped_rows": skipped_rows,
        "gates": sorted({row["gate_id"] for row in evidence_rows}),
    }


def convert_wide_lab_csv(
    inputs: list[Path],
    gate_id: str,
    candidate_id: str,
    sample_id_column: str,
    field_columns: list[str],
    exclude_columns: list[str],
    gate_id_column: str,
    candidate_id_column: str,
    source_file: str,
    source_file_column: str,
    measured_at: str,
    measured_at_column: str,
    operator_or_agent: str,
    operator_or_agent_column: str,
    instrument_id: str,
    instrument_id_column: str,
    notes: str,
    notes_column: str,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    evidence_rows: list[dict[str, str]] = []
    skipped_rows = 0
    skipped_values = 0
    input_summaries = []

    for path in inputs:
        rows = read_csv(path)
        before = len(evidence_rows)
        if field_columns:
            value_columns = field_columns
        else:
            excluded = {
                sample_id_column,
                gate_id_column,
                candidate_id_column,
                source_file_column,
                measured_at_column,
                operator_or_agent_column,
                instrument_id_column,
                notes_column,
                *exclude_columns,
            }
            value_columns = [column for column in rows[0].keys() if column and column not in excluded] if rows else []

        for row in rows:
            sample_id = clean(row.get(sample_id_column))
            if not sample_id:
                skipped_rows += 1
                continue
            row_gate = clean(row.get(gate_id_column)) if gate_id_column else ""
            row_candidate = clean(row.get(candidate_id_column)) if candidate_id_column else ""
            row_source = clean(row.get(source_file_column)) if source_file_column else ""
            row_measured_at = clean(row.get(measured_at_column)) if measured_at_column else ""
            row_operator = clean(row.get(operator_or_agent_column)) if operator_or_agent_column else ""
            row_instrument = clean(row.get(instrument_id_column)) if instrument_id_column else ""
            row_notes = clean(row.get(notes_column)) if notes_column else ""
            for field in value_columns:
                value = clean(row.get(field))
                if not value:
                    skipped_values += 1
                    continue
                evidence_rows.append({
                    "gate_id": row_gate or gate_id,
                    "candidate_id": row_candidate or candidate_id,
                    "sample_id": sample_id,
                    "field": field,
                    "value": value,
                    "source_file": row_source or source_file or str(path),
                    "measured_at": row_measured_at or measured_at,
                    "operator_or_agent": row_operator or operator_or_agent,
                    "instrument_id": row_instrument or instrument_id,
                    "notes": row_notes or notes,
                })
        input_summaries.append({
            "path": str(path),
            "input_rows": len(rows),
            "value_columns": value_columns,
            "evidence_rows": len(evidence_rows) - before,
        })

    return evidence_rows, {
        "status": "converted",
        "inputs": input_summaries,
        "evidence_rows": len(evidence_rows),
        "skipped_rows": skipped_rows,
        "skipped_values": skipped_values,
        "gates": sorted({row["gate_id"] for row in evidence_rows}),
    }


def write_wide_lab_conversion(
    inputs: list[Path],
    evidence_out: Path,
    summary_out: Path | None,
    profile: str,
    gate_id: str,
    candidate_id: str,
    sample_id_column: str,
    field_columns: list[str],
    exclude_columns: list[str],
    gate_id_column: str,
    candidate_id_column: str,
    source_file: str,
    source_file_column: str,
    measured_at: str,
    measured_at_column: str,
    operator_or_agent: str,
    operator_or_agent_column: str,
    instrument_id: str,
    instrument_id_column: str,
    notes: str,
    notes_column: str,
) -> dict[str, Any]:
    settings = resolve_wide_adapter_settings(
        profile=profile,
        sample_id_column=sample_id_column,
        exclude_columns=exclude_columns,
        gate_id_column=gate_id_column,
        candidate_id_column=candidate_id_column,
        source_file_column=source_file_column,
        measured_at_column=measured_at_column,
        operator_or_agent_column=operator_or_agent_column,
        instrument_id_column=instrument_id_column,
        notes_column=notes_column,
    )
    evidence_rows, summary = convert_wide_lab_csv(
        inputs=inputs,
        gate_id=gate_id,
        candidate_id=candidate_id,
        sample_id_column=str(settings["sample_id_column"]),
        field_columns=field_columns,
        exclude_columns=[str(item) for item in settings["exclude_columns"]],
        gate_id_column=str(settings["gate_id_column"]),
        candidate_id_column=str(settings["candidate_id_column"]),
        source_file=source_file,
        source_file_column=str(settings["source_file_column"]),
        measured_at=measured_at,
        measured_at_column=str(settings["measured_at_column"]),
        operator_or_agent=operator_or_agent,
        operator_or_agent_column=str(settings["operator_or_agent_column"]),
        instrument_id=instrument_id,
        instrument_id_column=str(settings["instrument_id_column"]),
        notes=notes,
        notes_column=str(settings["notes_column"]),
    )
    write_csv(evidence_out, evidence_rows, EVIDENCE_FIELDS)
    summary["evidence_out"] = str(evidence_out)
    summary["adapter_profile"] = profile
    summary["adapter_profile_description"] = settings["profile_description"]
    summary["adapter_settings"] = settings
    if summary_out is not None:
        summary_out.parent.mkdir(parents=True, exist_ok=True)
        summary_out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return data


def load_eval_records(inputs: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for path in inputs:
        suffix = path.suffix.lower()
        before = len(records)
        if suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    loaded = json.loads(line)
                    if not isinstance(loaded, dict):
                        raise ValueError(f"Expected JSON object per line in {path}:{line_number}.")
                    records.append(loaded)
        elif suffix == ".json":
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                records.extend(item for item in loaded if isinstance(item, dict))
            elif isinstance(loaded, dict):
                for key in ["records", "rows", "results", "items"]:
                    nested = loaded.get(key)
                    if isinstance(nested, list):
                        records.extend(item for item in nested if isinstance(item, dict))
                        break
                records.append(loaded)
            else:
                raise ValueError(f"Expected JSON object or list in {path}.")
        elif suffix == ".csv":
            records.extend(read_csv(path))
        else:
            raise ValueError(f"Unsupported eval artifact extension `{suffix}` for {path}; use .json, .jsonl, or .csv.")
        summaries.append({"path": str(path), "input_records": len(records) - before})
    return records, summaries


def first_clean(mapping: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, (dict, list)):
            continue
        text = clean(value)
        if text:
            return text
    return ""


def first_record_value(records: list[dict[str, Any]], keys: list[str]) -> str:
    for record in records:
        value = first_clean(record, keys)
        if value:
            return value
    return ""


def truth_recorded(mapping: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            if value.strip():
                return "true"
        elif value not in (None, "", [], {}):
            return "true"
    return "false"


def add_metric_values(metrics: dict[str, dict[str, str]], candidate_id: str, values: Any) -> None:
    if not isinstance(values, dict):
        return
    bucket = metrics.setdefault(candidate_id, {})
    for field, value in values.items():
        if isinstance(value, (dict, list)):
            continue
        text = clean(value)
        if text:
            bucket[str(field)] = text


def collect_eval_metrics(records: list[dict[str, Any]], manifest: dict[str, Any], candidate_id: str, baseline_id: str) -> dict[str, dict[str, str]]:
    metrics: dict[str, dict[str, str]] = {}
    for source in [manifest, *records]:
        add_metric_values(metrics, candidate_id, source.get("candidate_metrics"))
        add_metric_values(metrics, baseline_id, source.get("baseline_metrics"))
        add_metric_values(metrics, candidate_id, source.get("metrics"))
        for nested_key in ["retrieval", "answer", "source_coverage", "quality", "safety"]:
            add_metric_values(metrics, candidate_id, source.get(nested_key))

        metric = first_clean(source, ["metric", "field", "name"])
        value = first_clean(source, ["value", "score"])
        if metric and value:
            row_candidate = first_clean(source, ["candidate_id", "model_id", "system_id", "rag_id"])
            if not row_candidate:
                role = first_clean(source, ["role", "record_type", "kind"]).lower()
                row_candidate = baseline_id if "baseline" in role else candidate_id
            metrics.setdefault(row_candidate, {})[metric] = value
    return metrics


def evidence_row(
    gate_id: str,
    candidate_id: str,
    sample_id: str,
    field: str,
    value: str,
    source_file: str,
    measured_at: str,
    operator_or_agent: str,
    instrument_id: str,
    notes: str,
) -> dict[str, str]:
    return {
        "gate_id": gate_id,
        "candidate_id": candidate_id,
        "sample_id": sample_id,
        "field": field,
        "value": value,
        "source_file": source_file,
        "measured_at": measured_at,
        "operator_or_agent": operator_or_agent,
        "instrument_id": instrument_id,
        "notes": notes,
    }


def eval_source_file(source_file: str, inputs: list[Path]) -> str:
    if source_file:
        return source_file
    if inputs:
        return inputs[0].name
    return ""


def ai_eval_rows(
    records: list[dict[str, Any]],
    manifest: dict[str, Any],
    profile: str,
    inputs: list[Path],
    source_file: str,
    measured_at: str,
    operator_or_agent: str,
    instrument_id: str,
    notes: str,
    sample_id: str,
    candidate_id: str,
    baseline_candidate_id: str,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    run_id = sample_id or first_clean(manifest, ["eval_run_id", "run_id", "sample_id"]) or first_record_value(records, ["eval_run_id", "run_id", "sample_id"]) or "eval_run_001"
    candidate = candidate_id or first_clean(manifest, ["candidate_id", "candidate_model_id", "model_id"]) or "candidate_model"
    baseline = baseline_candidate_id or first_clean(manifest, ["baseline_candidate_id", "baseline_model_id", "baseline_id"]) or "baseline_model"
    src = eval_source_file(source_file, inputs)
    at = measured_at or first_clean(manifest, ["measured_at", "evaluated_at", "timestamp"])
    operator = operator_or_agent or first_clean(manifest, ["operator_or_agent", "evaluator", "operator", "agent"]) or "falsiflow_eval_import"
    instrument = instrument_id or first_clean(manifest, ["instrument_id", "harness_id", "evaluator_version", "runtime"]) or "eval_harness"
    base_notes = notes or ADAPTER_PROFILES[profile]["description"]
    metrics = collect_eval_metrics(records, manifest, candidate, baseline)

    rows = [
        evidence_row("eval_provenance", candidate, run_id, "dataset_version_recorded", truth_recorded(manifest, ["dataset_version", "dataset_id", "dataset_hash", "eval_set_version"]), src, at, operator, instrument, "Dataset or eval-set version from eval manifest."),
        evidence_row("eval_provenance", candidate, run_id, "prompt_set_hash_recorded", truth_recorded(manifest, ["prompt_set_hash", "task_set_hash", "query_set_hash"]), src, at, operator, instrument, "Prompt, task, or query set hash from eval manifest."),
        evidence_row("eval_provenance", candidate, run_id, "candidate_model_version_recorded", truth_recorded(manifest, ["candidate_model_version", "candidate_model_revision", "candidate_model_id", "model_id", "model_file_hash"]), src, at, operator, instrument, "Candidate model version or local model file hash from manifest."),
        evidence_row("eval_provenance", candidate, run_id, "baseline_model_version_recorded", truth_recorded(manifest, ["baseline_model_version", "baseline_model_revision", "baseline_model_id", "baseline_id"]), src, at, operator, instrument, "Baseline model version from manifest."),
        evidence_row("eval_provenance", candidate, run_id, "evaluator_version_recorded", truth_recorded(manifest, ["evaluator_version", "eval_harness_version", "judge_version"]), src, at, operator, instrument, "Evaluator or judge version from manifest."),
    ]
    for actor in [candidate, baseline]:
        for field in ["exact_match_rate", "hallucination_rate", "safety_policy_failure_rate", "evaluated_item_count"]:
            value = metrics.get(actor, {}).get(field, "")
            if value:
                rows.append(evidence_row("benchmark_quality", actor, run_id, field, value, src, at, operator, instrument, f"{field} imported from eval artifact."))
    rows.extend([
        evidence_row("reproducibility_package", candidate, run_id, "eval_script_hash_recorded", truth_recorded(manifest, ["eval_script_hash", "eval_script_sha256", "harness_commit"]), src, at, operator, instrument, "Evaluation script or harness hash from manifest."),
        evidence_row("reproducibility_package", candidate, run_id, "random_seed_logged", truth_recorded(manifest, ["random_seed", "seed", "decode_params", "temperature"]), src, at, operator, instrument, "Seed or deterministic decode settings from manifest."),
        evidence_row("reproducibility_package", candidate, run_id, "raw_outputs_archived", truth_recorded(manifest, ["raw_outputs_uri", "raw_outputs_path", "raw_outputs_sha256", "artifact_uri"]), src, at, operator, instrument, "Raw outputs artifact from manifest."),
        evidence_row("reproducibility_package", candidate, run_id, "human_spotcheck_passed", truth_recorded(manifest, ["human_spotcheck_passed", "spotcheck_report_uri", "spotcheck_passed"]), src, at, operator, instrument, "Human spotcheck record from manifest."),
        evidence_row("reproducibility_package", candidate, run_id, "regression_ci_run_recorded", truth_recorded(manifest, ["regression_ci_run", "ci_run_url", "ci_run_id"]), src, at, operator, instrument, "Regression CI run from manifest."),
    ])
    local_metadata = {
        "runtime": first_clean(manifest, ["runtime", "runtime_name", "engine"]),
        "model_file_hash": first_clean(manifest, ["model_file_hash", "model_sha256", "gguf_sha256"]),
        "quantization": first_clean(manifest, ["quantization", "quantization_method"]),
        "adapter_hash": first_clean(manifest, ["adapter_hash", "lora_hash"]),
        "decode_params": first_clean(manifest, ["decode_params", "sampling_params"]),
    }
    return rows, {
        "sample_id": run_id,
        "candidate_id": candidate,
        "baseline_candidate_id": baseline,
        "local_model_metadata": {key: value for key, value in local_metadata.items() if value},
        "metric_candidates": sorted(metrics),
        "notes": str(base_notes),
    }


def rag_eval_rows(
    records: list[dict[str, Any]],
    manifest: dict[str, Any],
    profile: str,
    inputs: list[Path],
    source_file: str,
    measured_at: str,
    operator_or_agent: str,
    instrument_id: str,
    notes: str,
    sample_id: str,
    candidate_id: str,
    baseline_candidate_id: str,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    run_id = sample_id or first_clean(manifest, ["rag_eval_run_id", "eval_run_id", "run_id", "sample_id"]) or first_record_value(records, ["eval_run_id", "run_id", "sample_id"]) or "rag_eval_001"
    candidate = candidate_id or first_clean(manifest, ["candidate_rag_id", "candidate_id", "system_id"]) or "candidate_rag"
    baseline = baseline_candidate_id or first_clean(manifest, ["baseline_rag_id", "baseline_candidate_id", "baseline_id"]) or "baseline_rag"
    src = eval_source_file(source_file, inputs)
    at = measured_at or first_clean(manifest, ["measured_at", "evaluated_at", "timestamp"])
    operator = operator_or_agent or first_clean(manifest, ["operator_or_agent", "evaluator", "operator", "agent"]) or "falsiflow_rag_eval_import"
    instrument = instrument_id or first_clean(manifest, ["instrument_id", "harness_id", "judge_version", "evaluator_version"]) or "rag_eval_harness"
    base_notes = notes or ADAPTER_PROFILES[profile]["description"]
    metrics = collect_eval_metrics(records, manifest, candidate, baseline)

    rows = [
        evidence_row("evaluation_provenance", candidate, run_id, "eval_set_version_recorded", truth_recorded(manifest, ["eval_set_version", "dataset_version", "eval_set_id", "dataset_hash"]), src, at, operator, instrument, "RAG eval set version from manifest."),
        evidence_row("evaluation_provenance", candidate, run_id, "query_set_hash_recorded", truth_recorded(manifest, ["query_set_hash", "prompt_set_hash", "query_hash"]), src, at, operator, instrument, "RAG query set hash from manifest."),
        evidence_row("evaluation_provenance", candidate, run_id, "candidate_rag_version_recorded", truth_recorded(manifest, ["candidate_rag_version", "candidate_rag_revision", "candidate_rag_id", "retriever_version"]), src, at, operator, instrument, "Candidate RAG pipeline version from manifest."),
        evidence_row("evaluation_provenance", candidate, run_id, "baseline_rag_version_recorded", truth_recorded(manifest, ["baseline_rag_version", "baseline_rag_revision", "baseline_rag_id", "baseline_retriever_version"]), src, at, operator, instrument, "Baseline RAG pipeline version from manifest."),
        evidence_row("evaluation_provenance", candidate, run_id, "judge_version_recorded", truth_recorded(manifest, ["judge_version", "evaluator_version", "eval_harness_version"]), src, at, operator, instrument, "Judge or evaluator version from manifest."),
    ]
    for actor in [candidate, baseline]:
        for field in ["recall_at_5", "mrr_at_10", "retrieval_coverage_rate"]:
            value = metrics.get(actor, {}).get(field, "")
            if value:
                rows.append(evidence_row("retrieval_quality", actor, run_id, field, value, src, at, operator, instrument, f"{field} imported from RAG eval artifact."))
    for field in ["faithfulness_rate", "unsupported_answer_rate", "answer_correctness_rate", "judged_item_count"]:
        value = metrics.get(candidate, {}).get(field, "")
        if value:
            rows.append(evidence_row("answer_faithfulness", candidate, run_id, field, value, src, at, operator, instrument, f"{field} imported from RAG eval artifact."))
    for field in ["citation_precision", "source_coverage_rate", "missing_source_rate"]:
        value = metrics.get(candidate, {}).get(field, "")
        if value:
            rows.append(evidence_row("source_coverage", candidate, run_id, field, value, src, at, operator, instrument, f"{field} imported from RAG eval artifact."))
    rows.extend([
        evidence_row("reproducibility_package", candidate, run_id, "retrieval_run_archived", truth_recorded(manifest, ["retrieval_run_uri", "retrieval_run_path", "retrieval_run_sha256"]), src, at, operator, instrument, "Retrieval run artifact from manifest."),
        evidence_row("reproducibility_package", candidate, run_id, "raw_answers_archived", truth_recorded(manifest, ["raw_answers_uri", "raw_outputs_uri", "raw_answers_sha256"]), src, at, operator, instrument, "Raw answer artifact from manifest."),
        evidence_row("reproducibility_package", candidate, run_id, "eval_script_hash_recorded", truth_recorded(manifest, ["eval_script_hash", "eval_script_sha256", "harness_commit"]), src, at, operator, instrument, "Evaluation script or harness hash from manifest."),
        evidence_row("reproducibility_package", candidate, run_id, "regression_ci_run_recorded", truth_recorded(manifest, ["regression_ci_run", "ci_run_url", "ci_run_id"]), src, at, operator, instrument, "Regression CI run from manifest."),
    ])
    return rows, {
        "sample_id": run_id,
        "candidate_id": candidate,
        "baseline_candidate_id": baseline,
        "metric_candidates": sorted(metrics),
        "notes": str(base_notes),
    }


def write_eval_artifact_import(
    inputs: list[Path],
    manifest: Path | None,
    evidence_out: Path,
    summary_out: Path | None,
    profile: str,
    source_file: str,
    measured_at: str,
    operator_or_agent: str,
    instrument_id: str,
    notes: str,
    sample_id: str,
    candidate_id: str,
    baseline_candidate_id: str,
) -> dict[str, Any]:
    if profile not in EVAL_IMPORT_PROFILE_NAMES:
        raise ValueError(f"`{profile}` is not an eval artifact profile.")
    records, input_summaries = load_eval_records(inputs)
    manifest_data = load_json_object(manifest) if manifest is not None else {}
    if profile == "rag-eval":
        evidence_rows, profile_summary = rag_eval_rows(
            records,
            manifest_data,
            profile,
            inputs,
            source_file,
            measured_at,
            operator_or_agent,
            instrument_id,
            notes,
            sample_id,
            candidate_id,
            baseline_candidate_id,
        )
    else:
        evidence_rows, profile_summary = ai_eval_rows(
            records,
            manifest_data,
            profile,
            inputs,
            source_file,
            measured_at,
            operator_or_agent,
            instrument_id,
            notes,
            sample_id,
            candidate_id,
            baseline_candidate_id,
        )
    write_csv(evidence_out, evidence_rows, EVIDENCE_FIELDS)
    summary: dict[str, Any] = {
        "status": "converted",
        "adapter_profile": profile,
        "adapter_profile_description": str(ADAPTER_PROFILES[profile].get("description", "")),
        "adapter_kind": "eval-artifact",
        "inputs": input_summaries,
        "manifest": str(manifest) if manifest is not None else "",
        "evidence_out": str(evidence_out),
        "evidence_rows": len(evidence_rows),
        "skipped_rows": 0,
        "skipped_values": 0,
        "gates": sorted({row["gate_id"] for row in evidence_rows}),
        "profile_summary": profile_summary,
    }
    if summary_out is not None:
        summary_out.parent.mkdir(parents=True, exist_ok=True)
        summary_out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def build_project_from_evidence(
    evidence_rows: list[dict[str, str]],
    project_id: str,
    claim_id: str,
    claim_statement: str,
    source_file_base_dir: str,
    allowed_source_roots: list[str],
) -> dict[str, Any]:
    fields_by_gate: dict[str, set[str]] = defaultdict(set)
    samples_by_gate: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in evidence_rows:
        gate_id = row["gate_id"]
        fields_by_gate[gate_id].add(row["field"])
        samples_by_gate[gate_id].add((row["candidate_id"], row["sample_id"]))

    gate_order = [gate for gate in PHASE_TO_GATE.values() if gate in fields_by_gate]
    gate_order.extend(sorted(set(fields_by_gate) - set(gate_order)))
    gates = []
    for gate_id in gate_order:
        gates.append({
            "id": gate_id,
            "title": GATE_TITLES.get(gate_id, gate_id.replace("_", " ").title()),
            "samples": [
                {"candidate_id": candidate_id, "sample_id": sample_id}
                for candidate_id, sample_id in sorted(samples_by_gate[gate_id])
            ],
            "required_fields": sorted(fields_by_gate[gate_id]),
            "acceptance_rules": [],
        })
        apply_limina_scientific_overlay(gates[-1], fields_by_gate[gate_id])

    return {
        "project": {
            "id": project_id,
            "name": project_id.replace("_", " ").title(),
            "domain": "limina-neural-materials",
            "version": "0.1.0",
        },
        "claim": {
            "id": claim_id,
            "statement": claim_statement,
            "requires_gates": gate_order,
        },
        "evidence_policy": {
            "source_file_base_dir": source_file_base_dir,
            "require_source_files": True,
            "reject_placeholder_values": True,
            "allowed_source_roots": allowed_source_roots,
            "required_metadata_fields": [
                "source_file",
                "measured_at",
                "operator_or_agent",
            ],
            "placeholder_markers": DEFAULT_PLACEHOLDERS,
        },
        "gates": gates,
    }


def write_limina_conversion(
    inputs: list[Path],
    evidence_out: Path,
    summary_out: Path | None,
    project_out: Path | None,
    default_candidate: str,
    default_gate: str,
    project_id: str,
    claim_id: str,
    claim_statement: str,
    source_file_base_dir: str,
    allowed_source_roots: list[str],
) -> dict[str, Any]:
    evidence_rows, summary = convert_limina_source_values(inputs, default_candidate, default_gate)
    write_csv(evidence_out, evidence_rows, EVIDENCE_FIELDS)
    summary["evidence_out"] = str(evidence_out)

    if project_out is not None:
        project = build_project_from_evidence(
            evidence_rows,
            project_id=project_id,
            claim_id=claim_id,
            claim_statement=claim_statement,
            source_file_base_dir=source_file_base_dir,
            allowed_source_roots=allowed_source_roots,
        )
        project_out.parent.mkdir(parents=True, exist_ok=True)
        project_out.write_text(json.dumps(project, indent=2, sort_keys=True), encoding="utf-8")
        summary["project_out"] = str(project_out)
        summary["project_gate_count"] = len(project["gates"])
    if summary_out is not None:
        summary_out.parent.mkdir(parents=True, exist_ok=True)
        summary_out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary
