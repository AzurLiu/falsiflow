"""Core Falsiflow evidence-gate logic.

Falsiflow v0.2 keeps the engine small: a project config plus an evidence CSV
either makes a numeric claim ready for review or blocks it with concrete
repair reasons.
"""

from __future__ import annotations

import csv
import json
import operator
from pathlib import Path
from typing import Any, Callable


DEFAULT_PLACEHOLDERS = {
    "",
    "-",
    "fixture",
    "not_evidence",
    "pending",
    "record_actual",
    "record_lot",
    "synthetic",
    "tbd",
    "unknown",
}

DEFAULT_METADATA_FIELDS = ["source_file", "measured_at", "operator_or_agent"]
EVIDENCE_COLUMNS = [
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
EVIDENCE_REQUIRED_COLUMNS = ["gate_id", "candidate_id", "sample_id", "field", "value"]
EVIDENCE_KEY_COLUMNS = ["gate_id", "candidate_id", "sample_id", "field"]

OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}

DERIVED_OPERATIONS = {
    "abs_delta",
    "abs_pct_change",
    "all_false",
    "any_true",
    "copy",
    "delta",
    "difference",
    "gain_pct",
    "pct_change",
    "ratio",
    "reduction_pct",
    "subtract",
}


def add_issue(issues: list[dict[str, Any]], level: str, path: str, message: str) -> None:
    issues.append({"level": level, "path": path, "message": message})


def string_array_schema() -> dict[str, Any]:
    return {"type": "array", "items": {"type": "string"}}


def field_ref_schema() -> dict[str, Any]:
    selector_properties = {
        "field": {"type": "string"},
        "candidate_id": {"type": "string"},
        "candidate_ids": string_array_schema(),
        "candidate_id_contains": {"oneOf": [{"type": "string"}, string_array_schema()]},
        "sample_id": {"type": "string"},
        "sample_ids": string_array_schema(),
        "sample_id_contains": {"oneOf": [{"type": "string"}, string_array_schema()]},
    }
    return {
        "oneOf": [
            {"type": "string"},
            {
                "type": "object",
                "required": ["field"],
                "properties": selector_properties,
                "additionalProperties": True,
            },
        ]
    }


def project_json_schema() -> dict[str, Any]:
    field_ref = field_ref_schema()
    selector_properties = {
        "candidate_id": {"type": "string"},
        "candidate_ids": string_array_schema(),
        "candidate_id_contains": {"oneOf": [{"type": "string"}, string_array_schema()]},
        "sample_id": {"type": "string"},
        "sample_ids": string_array_schema(),
        "sample_id_contains": {"oneOf": [{"type": "string"}, string_array_schema()]},
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/project.schema.json",
        "title": "Falsiflow project config",
        "type": "object",
        "required": ["project", "claim", "gates"],
        "properties": {
            "project": {
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "domain": {"type": "string"},
                    "version": {"type": "string"},
                },
                "additionalProperties": True,
            },
            "claim": {
                "type": "object",
                "required": ["id", "requires_gates"],
                "properties": {
                    "id": {"type": "string"},
                    "statement": {"type": "string"},
                    "requires_gates": string_array_schema(),
                },
                "additionalProperties": True,
            },
            "evidence_policy": {
                "type": "object",
                "properties": {
                    "source_file_base_dir": {"type": "string"},
                    "require_source_files": {"type": "boolean"},
                    "reject_placeholder_values": {"type": "boolean"},
                    "allowed_source_roots": string_array_schema(),
                    "required_metadata_fields": string_array_schema(),
                    "placeholder_markers": string_array_schema(),
                },
                "additionalProperties": True,
            },
            "gates": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["id", "required_fields"],
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "samples": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["candidate_id", "sample_id"],
                                "properties": {
                                    "candidate_id": {"type": "string"},
                                    "sample_id": {"type": "string"},
                                },
                                "additionalProperties": True,
                            },
                        },
                        "candidate_ids": string_array_schema(),
                        "sample_ids": string_array_schema(),
                        "required_fields": string_array_schema(),
                        "derived_fields": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["operation"],
                                "properties": {
                                    "field": {"type": "string"},
                                    "id": {"type": "string"},
                                    "operation": {"type": "string", "enum": sorted(DERIVED_OPERATIONS)},
                                    "inputs": string_array_schema(),
                                    "fields": string_array_schema(),
                                    "left": field_ref,
                                    "right": field_ref,
                                    "before": field_ref,
                                    "after": field_ref,
                                    "numerator": field_ref,
                                    "denominator": field_ref,
                                    "source": field_ref,
                                },
                                "additionalProperties": True,
                            },
                        },
                        "acceptance_rules": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["field", "operator", "value"],
                                "properties": {
                                    "field": {"type": "string"},
                                    "operator": {"type": "string", "enum": sorted(OPERATORS)},
                                    "value": {},
                                    "reason": {"type": "string"},
                                    **selector_properties,
                                },
                                "additionalProperties": True,
                            },
                        },
                    },
                    "additionalProperties": True,
                },
            },
        },
        "additionalProperties": True,
    }


def evidence_row_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/evidence-row.schema.json",
        "title": "Falsiflow evidence row",
        "type": "object",
        "required": EVIDENCE_REQUIRED_COLUMNS,
        "properties": {column: {"type": "string"} for column in EVIDENCE_COLUMNS},
        "additionalProperties": True,
    }


def falsiflow_schema(kind: str) -> dict[str, Any]:
    schemas = {
        "project": project_json_schema,
        "evidence-row": evidence_row_json_schema,
    }
    if kind == "all":
        return {schema_kind: factory() for schema_kind, factory in schemas.items()}
    if kind not in schemas:
        raise ValueError(f"unknown schema kind: {kind}")
    return schemas[kind]()


def load_project(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        project = json.load(handle)
    if not isinstance(project, dict):
        raise SystemExit(f"Project config must be a JSON object: {path}")
    project.setdefault("_config_dir", str(path.resolve().parent))
    return project


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def text_contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def gate_samples(gate: dict[str, Any]) -> list[dict[str, Any]]:
    samples = gate.get("samples", [])
    if isinstance(samples, list) and samples:
        return [sample for sample in samples if isinstance(sample, dict)]
    return [
        {"candidate_id": candidate, "sample_id": sample}
        for candidate in as_list(gate.get("candidate_ids"))
        for sample in as_list(gate.get("sample_ids"))
    ]


def derived_field_id(derived: dict[str, Any]) -> str:
    return str(derived.get("field") or derived.get("id") or "").strip()


def field_ref(derived: dict[str, Any], key: str, inputs: list[str], index: int) -> Any:
    raw = derived.get(key)
    if raw is None and len(inputs) > index:
        raw = inputs[index]
    if isinstance(raw, dict):
        return raw
    return str(raw if raw is not None else "").strip()


def derived_input_refs(derived: dict[str, Any]) -> list[tuple[str, Any]]:
    operation = str(derived.get("operation", "")).strip()
    inputs = [str(item).strip() for item in derived.get("inputs", [])]
    if operation in {"delta", "difference", "subtract", "abs_delta"}:
        return [
            ("left", field_ref(derived, "left", inputs, 0)),
            ("right", field_ref(derived, "right", inputs, 1)),
        ]
    if operation in {"pct_change", "abs_pct_change", "gain_pct", "reduction_pct"}:
        return [
            ("before", field_ref(derived, "before", inputs, 0)),
            ("after", field_ref(derived, "after", inputs, 1)),
        ]
    if operation == "ratio":
        return [
            ("numerator", field_ref(derived, "numerator", inputs, 0)),
            ("denominator", field_ref(derived, "denominator", inputs, 1)),
        ]
    if operation == "copy":
        return [("source", field_ref(derived, "source", inputs, 0))]
    if operation in {"any_true", "all_false"}:
        fields = inputs or [str(item).strip() for item in derived.get("fields", [])]
        return [(f"inputs[{index}]", field) for index, field in enumerate(fields)] or [("inputs", "")]
    return []


def sample_matches_ref(ref: dict[str, Any], sample_key: tuple[str, str]) -> bool:
    candidate_id, sample_id = sample_key
    candidate_ids = as_list(ref.get("candidate_ids")) or as_list(ref.get("candidate_id"))
    if candidate_ids and candidate_id not in candidate_ids:
        return False
    sample_ids = as_list(ref.get("sample_ids")) or as_list(ref.get("sample_id"))
    if sample_ids and sample_id not in sample_ids:
        return False
    candidate_contains = as_list(ref.get("candidate_id_contains"))
    if candidate_contains and not text_contains_any(candidate_id, candidate_contains):
        return False
    sample_contains = as_list(ref.get("sample_id_contains"))
    if sample_contains and not text_contains_any(sample_id, sample_contains):
        return False
    return True


def ref_label(ref: Any) -> str:
    if isinstance(ref, dict):
        field = str(ref.get("field", "")).strip()
        candidate = str(ref.get("candidate_id", "")).strip()
        sample = str(ref.get("sample_id", "")).strip()
        if candidate or sample:
            return f"{candidate or '*'}:{sample or '*'}:{field}"
        return field
    return str(ref).strip()


def validate_field_ref(
    issues: list[dict[str, Any]],
    path: str,
    ref: Any,
    known_fields: set[str],
    sample_keys: list[tuple[str, str]],
) -> None:
    if isinstance(ref, dict):
        field = str(ref.get("field", "")).strip()
        if not field:
            add_issue(issues, "error", path, "Cross-sample field reference is missing `field`.")
            return
        if field not in known_fields:
            add_issue(issues, "error", path, f"Referenced field `{field}` is not available before this derived field.")
        matches = [sample_key for sample_key in sample_keys if sample_matches_ref(ref, sample_key)]
        if not matches:
            add_issue(issues, "error", path, f"Cross-sample reference `{ref_label(ref)}` matches no configured sample.")
        elif len(matches) > 1:
            add_issue(issues, "error", path, f"Cross-sample reference `{ref_label(ref)}` is ambiguous.")
        return

    field = str(ref).strip()
    if not field:
        add_issue(issues, "error", path, "Derived field input reference is required.")
    elif field not in known_fields:
        add_issue(issues, "error", path, f"Referenced field `{field}` is not available before this derived field.")


def validate_project_config(project: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    gate_ids: set[str] = set()

    if not isinstance(project.get("project"), dict):
        add_issue(issues, "error", "project", "`project` object is required.")
    if not isinstance(project.get("claim"), dict):
        add_issue(issues, "error", "claim", "`claim` object is required.")

    gates = project.get("gates", [])
    if not isinstance(gates, list) or not gates:
        add_issue(issues, "error", "gates", "`gates` must be a non-empty list.")
        gates = []

    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            add_issue(issues, "error", f"gates[{index}]", "Gate must be an object.")
            continue
        path = f"gates[{index}]"
        gate_id = str(gate.get("id", "")).strip()
        if not gate_id:
            add_issue(issues, "error", f"{path}.id", "Gate id is required.")
        elif gate_id in gate_ids:
            add_issue(issues, "error", f"{path}.id", f"Duplicate gate id `{gate_id}`.")
        else:
            gate_ids.add(gate_id)

        samples = gate_samples(gate)
        sample_keys: list[tuple[str, str]] = []
        seen_samples: set[tuple[str, str]] = set()
        if not samples:
            add_issue(issues, "error", f"{path}.samples", "At least one sample is required.")
        for sample_index, sample in enumerate(samples):
            candidate_id = str(sample.get("candidate_id", "")).strip()
            sample_id = str(sample.get("sample_id", "")).strip()
            sample_path = f"{path}.samples[{sample_index}]"
            if not candidate_id:
                add_issue(issues, "error", f"{sample_path}.candidate_id", "Sample candidate_id is required.")
            if not sample_id:
                add_issue(issues, "error", f"{sample_path}.sample_id", "Sample sample_id is required.")
            sample_key = (candidate_id, sample_id)
            sample_keys.append(sample_key)
            if sample_key in seen_samples:
                add_issue(issues, "error", sample_path, f"Duplicate sample `{candidate_id}/{sample_id}`.")
            seen_samples.add(sample_key)

        required_fields = [str(field).strip() for field in gate.get("required_fields", [])]
        required_field_set: set[str] = set()
        if not required_fields:
            add_issue(issues, "warning", f"{path}.required_fields", "Gate has no required fields.")
        for field_index, field in enumerate(required_fields):
            field_path = f"{path}.required_fields[{field_index}]"
            if not field:
                add_issue(issues, "error", field_path, "Required field cannot be blank.")
                continue
            if field in required_field_set:
                add_issue(issues, "error", field_path, f"Duplicate required field `{field}`.")
            required_field_set.add(field)

        known_fields = set(required_field_set)
        derived_field_set: set[str] = set()
        for derived_index, derived in enumerate(gate.get("derived_fields", [])):
            if not isinstance(derived, dict):
                add_issue(issues, "error", f"{path}.derived_fields[{derived_index}]", "Derived field must be an object.")
                continue
            derived_path = f"{path}.derived_fields[{derived_index}]"
            operation = str(derived.get("operation", "")).strip()
            field = derived_field_id(derived)
            if not field:
                add_issue(issues, "error", derived_path, "Derived field must define `field` or `id`.")
            elif field in required_field_set:
                add_issue(issues, "error", f"{derived_path}.field", f"Derived field `{field}` would overwrite a required evidence field.")
            elif field in derived_field_set:
                add_issue(issues, "error", f"{derived_path}.field", f"Duplicate derived field `{field}`.")
            if operation not in DERIVED_OPERATIONS:
                add_issue(issues, "error", f"{derived_path}.operation", f"Unknown derived operation `{operation}`.")
            else:
                for ref_path, ref in derived_input_refs(derived):
                    validate_field_ref(issues, f"{derived_path}.{ref_path}", ref, known_fields, sample_keys)
            if field:
                derived_field_set.add(field)
                known_fields.add(field)

        for rule_index, rule in enumerate(gate.get("acceptance_rules", [])):
            if not isinstance(rule, dict):
                add_issue(issues, "error", f"{path}.acceptance_rules[{rule_index}]", "Acceptance rule must be an object.")
                continue
            rule_path = f"{path}.acceptance_rules[{rule_index}]"
            field = str(rule.get("field", "")).strip()
            if not field:
                add_issue(issues, "error", f"{rule_path}.field", "Acceptance rule field is required.")
            elif field not in known_fields:
                add_issue(issues, "error", f"{rule_path}.field", f"Acceptance rule field `{field}` is not a required or derived field.")
            operator_text = str(rule.get("operator", "")).strip()
            if operator_text not in OPERATORS:
                add_issue(issues, "error", f"{rule_path}.operator", f"Unknown acceptance operator `{operator_text}`.")

    claim = project.get("claim", {}) if isinstance(project.get("claim"), dict) else {}
    required_gates = claim.get("requires_gates", [])
    if not isinstance(required_gates, list) or not required_gates:
        add_issue(issues, "error", "claim.requires_gates", "Claim must require at least one gate.")
        required_gates = []
    for gate_id in required_gates:
        if gate_id not in gate_ids:
            add_issue(issues, "error", "claim.requires_gates", f"Required gate `{gate_id}` is not defined.")

    error_count = sum(1 for issue in issues if issue["level"] == "error")
    warning_count = sum(1 for issue in issues if issue["level"] == "warning")
    return {
        "status": "valid" if error_count == 0 else "invalid",
        "valid": error_count == 0,
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues,
    }


def evidence_header_diagnostics(fieldnames: list[str]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not fieldnames:
        issues.append({"level": "error", "kind": "missing_evidence_header", "message": "Evidence CSV has no header row."})
        return issues

    seen: set[str] = set()
    duplicate_fields: set[str] = set()
    for field in fieldnames:
        if not field:
            issues.append({"level": "warning", "kind": "blank_evidence_column", "field": field, "message": "Evidence CSV has a blank column name."})
            continue
        if field in seen:
            duplicate_fields.add(field)
        seen.add(field)

    for field in sorted(duplicate_fields):
        issues.append({"level": "error", "kind": "duplicate_evidence_column", "field": field, "message": f"Evidence CSV has duplicate column `{field}`."})
    for field in EVIDENCE_REQUIRED_COLUMNS:
        if field not in seen:
            issues.append({"level": "error", "kind": "missing_required_evidence_column", "field": field, "message": f"Evidence CSV is missing required column `{field}`."})
    for field in EVIDENCE_COLUMNS:
        if field not in seen and field not in EVIDENCE_REQUIRED_COLUMNS:
            issues.append({"level": "warning", "kind": "missing_standard_evidence_column", "field": field, "message": f"Evidence CSV is missing standard column `{field}`."})
    return issues


def read_csv_rows_with_diagnostics(path: Path | None) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    if path is None or not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = [str(field or "").strip() for field in (reader.fieldnames or [])]
        issues = evidence_header_diagnostics(fieldnames)
        rows: list[dict[str, str]] = []
        for row_number, raw_row in enumerate(reader, start=2):
            if None in raw_row:
                issues.append({
                    "level": "warning",
                    "kind": "evidence_row_extra_columns",
                    "row_number": row_number,
                    "message": "Evidence row has more values than header columns; extra values are ignored.",
                })
            row = {str(key or "").strip(): str(value if value is not None else "") for key, value in raw_row.items() if key is not None}
            rows.append(row)
            for column in EVIDENCE_KEY_COLUMNS:
                if column in fieldnames and not str(row.get(column, "")).strip():
                    issues.append({
                        "level": "warning",
                        "kind": "blank_evidence_key_component",
                        "row_number": row_number,
                        "field": column,
                        "message": f"Evidence row has a blank `{column}` key component and cannot match configured evidence.",
                    })
        return rows, issues


def placeholder_set(project: dict[str, Any]) -> set[str]:
    policy = project.get("evidence_policy", {})
    configured = policy.get("placeholder_markers", []) if isinstance(policy, dict) else []
    return {str(item).strip().lower() for item in [*DEFAULT_PLACEHOLDERS, *as_list(configured)]}


def is_placeholder(value: Any, placeholders: set[str]) -> bool:
    return str(value if value is not None else "").strip().lower() in placeholders


def parse_scalar(value: Any) -> Any:
    text = str(value).strip()
    lowered = text.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    try:
        if "." in text or "e" in lowered:
            return float(text)
        return int(text)
    except ValueError:
        return text


def number_value(value: Any, label: str) -> float:
    parsed = parse_scalar(value)
    if isinstance(parsed, bool):
        raise ValueError(f"{label} is boolean, not numeric")
    if isinstance(parsed, int | float):
        return float(parsed)
    raise ValueError(f"{label} is not numeric")


def resolve_ref_value(
    ref: Any,
    values: dict[str, Any],
    all_values: dict[tuple[str, str], dict[str, Any]],
) -> Any:
    if isinstance(ref, dict):
        field = str(ref.get("field", "")).strip()
        if not field:
            raise ValueError("field reference is missing `field`")
        matches = [key for key in all_values if sample_matches_ref(ref, key)]
        if not matches:
            raise ValueError(f"cross-sample reference has no match: {ref_label(ref)}")
        if len(matches) > 1:
            raise ValueError(f"cross-sample reference is ambiguous: {ref_label(ref)}")
        target_values = all_values[matches[0]]
        if field not in target_values:
            raise ValueError(f"required input field is missing: {ref_label(ref)}")
        return target_values[field]

    field = str(ref).strip()
    if field not in values:
        raise ValueError(f"required input field is missing: {field}")
    return values[field]


def numeric_field(ref: Any, values: dict[str, Any], all_values: dict[tuple[str, str], dict[str, Any]]) -> float:
    return number_value(resolve_ref_value(ref, values, all_values), ref_label(ref))


def nonzero_denominator(value: float, label: str) -> float:
    if value == 0:
        raise ValueError(f"{label} is zero")
    return value


def bool_field(ref: Any, values: dict[str, Any], all_values: dict[tuple[str, str], dict[str, Any]]) -> bool:
    value = parse_scalar(resolve_ref_value(ref, values, all_values))
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"true", "yes", "1"}:
        return True
    if lowered in {"false", "no", "0"}:
        return False
    raise ValueError(f"{ref_label(ref)} is not boolean")


def pct_change(before: float, after: float) -> float:
    denominator = nonzero_denominator(abs(before), "before")
    return ((after - before) / denominator) * 100.0


def evaluate_derived_field(
    derived: dict[str, Any],
    values: dict[str, Any],
    all_values: dict[tuple[str, str], dict[str, Any]],
) -> Any:
    operation = str(derived.get("operation", "")).strip()
    inputs = [str(item).strip() for item in derived.get("inputs", [])]
    if operation in {"delta", "difference", "subtract", "abs_delta"}:
        left_ref = field_ref(derived, "left", inputs, 0)
        right_ref = field_ref(derived, "right", inputs, 1)
        delta = numeric_field(left_ref, values, all_values) - numeric_field(right_ref, values, all_values)
        return abs(delta) if operation == "abs_delta" else delta
    if operation in {"pct_change", "abs_pct_change", "gain_pct", "reduction_pct"}:
        before_ref = field_ref(derived, "before", inputs, 0)
        after_ref = field_ref(derived, "after", inputs, 1)
        before = numeric_field(before_ref, values, all_values)
        after = numeric_field(after_ref, values, all_values)
        value = pct_change(before, after)
        if operation == "reduction_pct":
            value = pct_change(after, before)
        if operation == "abs_pct_change":
            value = abs(value)
        return value
    if operation == "ratio":
        numerator_ref = field_ref(derived, "numerator", inputs, 0)
        denominator_ref = field_ref(derived, "denominator", inputs, 1)
        denominator = nonzero_denominator(numeric_field(denominator_ref, values, all_values), ref_label(denominator_ref))
        return numeric_field(numerator_ref, values, all_values) / denominator
    if operation == "any_true":
        fields = inputs or [str(item).strip() for item in derived.get("fields", [])]
        if not fields:
            raise ValueError("any_true has no input fields")
        return any(bool_field(field, values, all_values) for field in fields)
    if operation == "all_false":
        fields = inputs or [str(item).strip() for item in derived.get("fields", [])]
        if not fields:
            raise ValueError("all_false has no input fields")
        return all(not bool_field(field, values, all_values) for field in fields)
    if operation == "copy":
        source_ref = field_ref(derived, "source", inputs, 0)
        return resolve_ref_value(source_ref, values, all_values)
    raise ValueError(f"unknown derived operation: {operation}")


def compute_derived_fields(
    gate: dict[str, Any],
    value_by_sample: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    derived_results: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for derived in gate.get("derived_fields", []):
        if not isinstance(derived, dict):
            continue
        field = derived_field_id(derived)
        if not field:
            blockers.append({"gate_id": gate.get("id"), "field": "", "reasons": ["derived field is missing an id or field name"]})
            continue
        for sample_key, values in value_by_sample.items():
            try:
                value = evaluate_derived_field(derived, values, value_by_sample)
            except ValueError as exc:
                blockers.append({
                    "gate_id": gate.get("id"),
                    "candidate_id": sample_key[0],
                    "sample_id": sample_key[1],
                    "field": field,
                    "reasons": [f"derived field failed: {exc}"],
                })
                continue
            values[field] = value
            derived_results.append({
                "gate_id": gate.get("id"),
                "candidate_id": sample_key[0],
                "sample_id": sample_key[1],
                "field": field,
                "operation": derived.get("operation", ""),
                "value": value,
            })
    return derived_results, blockers


def rule_applies_to_sample(rule: dict[str, Any], sample_key: tuple[str, str]) -> bool:
    candidate_id, sample_id = sample_key
    candidate_ids = as_list(rule.get("candidate_ids")) or as_list(rule.get("candidate_id"))
    if candidate_ids and candidate_id not in candidate_ids:
        return False
    sample_ids = as_list(rule.get("sample_ids")) or as_list(rule.get("sample_id"))
    if sample_ids and sample_id not in sample_ids:
        return False
    candidate_contains = as_list(rule.get("candidate_id_contains"))
    if candidate_contains and not text_contains_any(candidate_id, candidate_contains):
        return False
    sample_contains = as_list(rule.get("sample_id_contains"))
    if sample_contains and not text_contains_any(sample_id, sample_contains):
        return False
    return True


def config_dir(project: dict[str, Any]) -> Path:
    return Path(str(project.get("_config_dir", "."))).resolve()


def source_file_base_dir(project: dict[str, Any]) -> Path:
    policy = project.get("evidence_policy", {})
    raw = policy.get("source_file_base_dir", "") if isinstance(policy, dict) else ""
    if not raw:
        return config_dir(project)
    path = Path(str(raw))
    if not path.is_absolute():
        path = config_dir(project) / path
    return path.resolve()


def allowed_roots(project: dict[str, Any]) -> list[Path]:
    policy = project.get("evidence_policy", {})
    roots = policy.get("allowed_source_roots", []) if isinstance(policy, dict) else []
    base = source_file_base_dir(project)
    resolved = []
    for root in as_list(roots):
        path = Path(root)
        if not path.is_absolute():
            path = base / path
        resolved.append(path.resolve())
    return resolved


def resolve_source_file(project: dict[str, Any], source_file: str) -> Path:
    path = Path(source_file)
    if path.is_absolute():
        return path.resolve()
    return (source_file_base_dir(project) / path).resolve()


def source_file_issue(project: dict[str, Any], source_file: str) -> str | None:
    if not source_file:
        return "source_file is blank"
    path = resolve_source_file(project, source_file)
    if not path.exists():
        return f"source_file does not exist: {source_file}"
    roots = allowed_roots(project)
    if roots and not any(path == root or root in path.parents for root in roots):
        return f"source_file outside allowed roots: {source_file}"
    return None


def evidence_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        str(row.get("gate_id", "")).strip(),
        str(row.get("candidate_id", "")).strip(),
        str(row.get("sample_id", "")).strip(),
        str(row.get("field", "")).strip(),
    )


def evidence_index(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, str]]:
    indexed: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in rows:
        indexed.setdefault(evidence_key(row), row)
    return indexed


def evidence_rows_by_key(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(evidence_key(row), []).append(row)
    return grouped


def configured_evidence_keys(project: dict[str, Any]) -> set[tuple[str, str, str, str]]:
    keys: set[tuple[str, str, str, str]] = set()
    for gate in project.get("gates", []):
        if not isinstance(gate, dict):
            continue
        gate_id = str(gate.get("id", "")).strip()
        for sample in gate_samples(gate):
            candidate_id = str(sample.get("candidate_id", "")).strip()
            sample_id = str(sample.get("sample_id", "")).strip()
            for field in gate.get("required_fields", []):
                keys.add((gate_id, candidate_id, sample_id, str(field).strip()))
    return keys


def evidence_diagnostics(
    rows_by_key: dict[tuple[str, str, str, str], list[dict[str, str]]],
    configured_keys: set[tuple[str, str, str, str]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for key, rows in sorted(rows_by_key.items()):
        gate_id, candidate_id, sample_id, field = key
        configured = key in configured_keys
        if len(rows) > 1:
            issues.append({
                "level": "error" if configured else "warning",
                "kind": "duplicate_evidence_key",
                "gate_id": gate_id,
                "candidate_id": candidate_id,
                "sample_id": sample_id,
                "field": field,
                "row_count": len(rows),
                "message": "Duplicate evidence rows for a configured key; use distinct sample_id values for replicates." if configured else "Duplicate evidence rows for an unconfigured key.",
            })
        if not configured:
            issues.append({
                "level": "warning",
                "kind": "unconfigured_evidence_key",
                "gate_id": gate_id,
                "candidate_id": candidate_id,
                "sample_id": sample_id,
                "field": field,
                "row_count": len(rows),
                "message": "Evidence row does not match any configured required gate/sample/field and is ignored.",
            })
    return issues


def audit_project(
    project: dict[str, Any],
    evidence_rows: list[dict[str, str]],
    evidence_file_issues: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    project_validation = validate_project_config(project)
    project_error_count = int(project_validation.get("error_count", 0) or 0)
    project_warning_count = int(project_validation.get("warning_count", 0) or 0)
    placeholders = placeholder_set(project)
    indexed = evidence_index(evidence_rows)
    grouped_rows = evidence_rows_by_key(evidence_rows)
    configured_keys = configured_evidence_keys(project)
    duplicate_counts = {key: len(rows) for key, rows in grouped_rows.items() if len(rows) > 1}
    evidence_issues = [*(evidence_file_issues or []), *evidence_diagnostics(grouped_rows, configured_keys)]
    evidence_error_count = sum(1 for issue in evidence_issues if issue.get("level") == "error")
    evidence_warning_count = sum(1 for issue in evidence_issues if issue.get("level") == "warning")
    policy = project.get("evidence_policy", {}) if isinstance(project.get("evidence_policy"), dict) else {}
    require_sources = bool(policy.get("require_source_files", True))
    reject_placeholders = bool(policy.get("reject_placeholder_values", True))
    metadata_fields = as_list(policy.get("required_metadata_fields")) or DEFAULT_METADATA_FIELDS
    gate_results = []

    for gate in project.get("gates", []):
        if not isinstance(gate, dict):
            continue
        blockers: list[dict[str, Any]] = []
        valid_required_rows = 0
        value_by_sample: dict[tuple[str, str], dict[str, Any]] = {}

        for sample in gate_samples(gate):
            candidate_id = str(sample.get("candidate_id", "")).strip()
            sample_id = str(sample.get("sample_id", "")).strip()
            sample_key = (candidate_id, sample_id)
            value_by_sample.setdefault(sample_key, {})
            for field in gate.get("required_fields", []):
                field_name = str(field).strip()
                key = (str(gate.get("id", "")).strip(), candidate_id, sample_id, field_name)
                row = indexed.get(key)
                row_blockers: list[str] = []
                if not row:
                    row_blockers.append("missing evidence row")
                else:
                    duplicate_count = duplicate_counts.get(key, 0)
                    if duplicate_count:
                        row_blockers.append(f"duplicate evidence rows for key ({duplicate_count} rows)")
                    raw_value = row.get("value", "")
                    if reject_placeholders and is_placeholder(raw_value, placeholders):
                        row_blockers.append("value is blank or placeholder")
                    for metadata_field in metadata_fields:
                        if is_placeholder(row.get(metadata_field, ""), placeholders):
                            row_blockers.append(f"{metadata_field} is blank or placeholder")
                    if require_sources:
                        issue = source_file_issue(project, row.get("source_file", ""))
                        if issue:
                            row_blockers.append(issue)
                    if not row_blockers:
                        valid_required_rows += 1
                        value_by_sample[sample_key][field_name] = parse_scalar(raw_value)

                if row_blockers:
                    blockers.append({
                        "gate_id": gate.get("id"),
                        "candidate_id": candidate_id,
                        "sample_id": sample_id,
                        "field": field_name,
                        "reasons": row_blockers,
                    })

        derived_results, derived_blockers = compute_derived_fields(gate, value_by_sample)
        blockers.extend(derived_blockers)

        for rule in gate.get("acceptance_rules", []):
            if not isinstance(rule, dict):
                continue
            field = str(rule.get("field", "")).strip()
            op_text = str(rule.get("operator", "")).strip()
            expected = rule.get("value")
            op = OPERATORS.get(op_text)
            if not op:
                blockers.append({"gate_id": gate.get("id"), "field": field, "reasons": [f"unknown acceptance operator: {op_text}"]})
                continue
            for sample_key, values in value_by_sample.items():
                if not rule_applies_to_sample(rule, sample_key):
                    continue
                if field not in values:
                    blockers.append({
                        "gate_id": gate.get("id"),
                        "candidate_id": sample_key[0],
                        "sample_id": sample_key[1],
                        "field": field,
                        "reasons": ["acceptance field is missing or not derived"],
                    })
                    continue
                actual = values[field]
                expected_value = parse_scalar(expected)
                try:
                    passed = op(actual, expected_value)
                except TypeError:
                    passed = op(str(actual), str(expected_value))
                if not passed:
                    blockers.append({
                        "gate_id": gate.get("id"),
                        "candidate_id": sample_key[0],
                        "sample_id": sample_key[1],
                        "field": field,
                        "actual": actual,
                        "operator": op_text,
                        "expected": expected_value,
                        "reasons": [str(rule.get("reason") or "acceptance rule failed")],
                    })

        required_rows = len(gate_samples(gate)) * len(gate.get("required_fields", []))
        if blockers:
            status = "blocked_missing_evidence" if valid_required_rows < required_rows else "failed_acceptance_rules"
        else:
            status = "passed"
        gate_results.append({
            "gate_id": gate.get("id"),
            "title": gate.get("title", ""),
            "status": status,
            "required_evidence_rows": required_rows,
            "valid_required_evidence_rows": valid_required_rows,
            "derived_field_count": len(derived_results),
            "derived_fields": derived_results[:200],
            "blocker_count": len(blockers),
            "blockers": blockers,
        })

    claim = project.get("claim", {}) if isinstance(project.get("claim"), dict) else {}
    required_gate_ids = set(as_list(claim.get("requires_gates")))
    gate_status = {str(gate["gate_id"]): str(gate["status"]) for gate in gate_results}
    missing_gates = sorted(gate_id for gate_id in required_gate_ids if gate_id not in gate_status)
    gates_ready = not missing_gates and all(gate_status.get(gate_id) == "passed" for gate_id in required_gate_ids)
    claim_ready = project_error_count == 0 and evidence_error_count == 0 and gates_ready
    result = {
        "status": "claim_ready" if claim_ready else "claim_blocked",
        "claim_ready": claim_ready,
        "project": project.get("project", {}),
        "claim": claim,
        "project_validation": project_validation,
        "project_config_valid": bool(project_validation.get("valid")),
        "project_validation_error_count": project_error_count,
        "project_validation_warning_count": project_warning_count,
        "missing_required_gates": missing_gates,
        "evidence_issue_count": len(evidence_issues),
        "evidence_error_count": evidence_error_count,
        "evidence_warning_count": evidence_warning_count,
        "evidence_issues": evidence_issues[:500],
        "gates": gate_results,
    }
    result["next_actions"] = next_actions(result)
    return result


def next_actions(audit: dict[str, Any]) -> list[dict[str, Any]]:
    if audit.get("claim_ready"):
        return [{
            "rank": 1,
            "action_id": "review_claim_for_release",
            "why": "All required gates passed with source-backed evidence.",
            "success_criterion": "Human review confirms raw sources and claim wording before relying on the claim.",
        }]
    actions = []
    if int(audit.get("project_validation_error_count", 0) or 0) > 0:
        actions.append({
            "rank": len(actions) + 1,
            "action_id": "fix_project_config_diagnostics",
            "why": f"Project validation includes {audit.get('project_validation_error_count')} error(s).",
            "success_criterion": "Project validation is valid with zero errors.",
        })
    if int(audit.get("evidence_error_count", 0) or 0) > 0:
        actions.append({
            "rank": len(actions) + 1,
            "action_id": "fix_evidence_file_diagnostics",
            "why": f"Evidence diagnostics include {audit.get('evidence_error_count')} error(s).",
            "success_criterion": "Evidence diagnostics have zero errors; warnings are reviewed or intentionally accepted.",
        })
    for gate in audit.get("gates", []):
        if gate.get("status") == "passed":
            continue
        actions.append({
            "rank": len(actions) + 1,
            "action_id": f"repair_{gate.get('gate_id')}_evidence",
            "why": f"Gate `{gate.get('gate_id')}` is `{gate.get('status')}` with {gate.get('blocker_count')} blocker(s).",
            "success_criterion": "All required rows have non-placeholder values, required metadata, allowed source files, and passing acceptance rules.",
        })
    return actions


def render_audit_report(audit: dict[str, Any]) -> str:
    lines = [
        "# Falsiflow Claim Audit",
        "",
        f"**Project:** `{audit.get('project', {}).get('id', '-')}`",
        f"**Claim:** `{audit.get('claim', {}).get('id', '-')}`",
        f"**Status:** `{audit.get('status')}`",
        f"**Claim ready:** `{str(bool(audit.get('claim_ready'))).lower()}`",
        "",
        "## Gates",
        "",
        "| Gate | Status | Valid rows | Required rows | Derived | Blockers |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for gate in audit.get("gates", []):
        lines.append(
            f"| `{gate['gate_id']}` | `{gate['status']}` | {gate['valid_required_evidence_rows']} | "
            f"{gate['required_evidence_rows']} | {gate.get('derived_field_count', 0)} | {gate['blocker_count']} |"
        )

    lines.extend(["", "## Project Validation", ""])
    validation = audit.get("project_validation", {})
    lines.append(f"- status: `{validation.get('status', 'unknown')}`")
    for issue in validation.get("issues", [])[:40]:
        lines.append(f"- `{issue.get('level', '')}` `{issue.get('path', '')}`: {issue.get('message', '')}")
    if not validation.get("issues"):
        lines.append("- none")

    lines.extend(["", "## Evidence Diagnostics", ""])
    for issue in audit.get("evidence_issues", [])[:40]:
        lines.append(
            f"- `{issue.get('level', '')}` `{issue.get('kind', '')}` "
            f"`{issue.get('gate_id', '')}` `{issue.get('sample_id', '')}` "
            f"`{issue.get('field', '')}`: {issue.get('message', '')}"
        )
    if not audit.get("evidence_issues"):
        lines.append("- none")

    lines.extend(["", "## Blockers", ""])
    blocker_seen = False
    for gate in audit.get("gates", []):
        for blocker in gate.get("blockers", [])[:40]:
            blocker_seen = True
            reasons = "; ".join(str(reason) for reason in blocker.get("reasons", []))
            lines.append(f"- `{gate['gate_id']}` `{blocker.get('sample_id', '-')}` `{blocker.get('field', '-')}`: {reasons}")
    if not blocker_seen:
        lines.append("- none")

    lines.extend(["", "## Next Actions", ""])
    for action in audit.get("next_actions", []):
        lines.append(f"- {action['rank']}. `{action['action_id']}` - {action['why']}")
    lines.append("")
    return "\n".join(lines)


def completion_pct(gate: dict[str, Any]) -> float:
    required = int(gate.get("required_evidence_rows", 0) or 0)
    if required <= 0:
        return 100.0
    valid = int(gate.get("valid_required_evidence_rows", 0) or 0)
    return round((valid / required) * 100, 1)


def claim_summary(audit: dict[str, Any]) -> dict[str, Any]:
    gates = []
    blocker_total = 0
    valid_total = 0
    required_total = 0
    status_counts: dict[str, int] = {}
    for gate in audit.get("gates", []):
        status = str(gate.get("status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
        blockers = int(gate.get("blocker_count", 0) or 0)
        valid_rows = int(gate.get("valid_required_evidence_rows", 0) or 0)
        required_rows = int(gate.get("required_evidence_rows", 0) or 0)
        blocker_total += blockers
        valid_total += valid_rows
        required_total += required_rows
        gates.append({
            "gate_id": gate.get("gate_id", ""),
            "title": gate.get("title", ""),
            "status": status,
            "completion_pct": completion_pct(gate),
            "valid_required_evidence_rows": valid_rows,
            "required_evidence_rows": required_rows,
            "derived_field_count": int(gate.get("derived_field_count", 0) or 0),
            "blocker_count": blockers,
        })
    return {
        "project_id": audit.get("project", {}).get("id", ""),
        "claim_id": audit.get("claim", {}).get("id", ""),
        "status": audit.get("status", ""),
        "claim_ready": bool(audit.get("claim_ready")),
        "gate_count": len(gates),
        "status_counts": status_counts,
        "valid_required_evidence_rows": valid_total,
        "required_evidence_rows": required_total,
        "completion_pct": round((valid_total / required_total) * 100, 1) if required_total else 100.0,
        "derived_field_count": sum(gate["derived_field_count"] for gate in gates),
        "blocker_count": blocker_total,
        "project_config_valid": bool(audit.get("project_config_valid", False)),
        "project_validation_error_count": int(audit.get("project_validation_error_count", 0) or 0),
        "project_validation_warning_count": int(audit.get("project_validation_warning_count", 0) or 0),
        "evidence_issue_count": int(audit.get("evidence_issue_count", 0) or 0),
        "evidence_error_count": int(audit.get("evidence_error_count", 0) or 0),
        "evidence_warning_count": int(audit.get("evidence_warning_count", 0) or 0),
        "next_action_count": len(audit.get("next_actions", [])),
        "gates": gates,
    }


def audit_blocking_stage(audit: dict[str, Any], summary: dict[str, Any]) -> str:
    if audit.get("claim_ready"):
        return "ready_for_human_review"
    if int(audit.get("project_validation_error_count", 0) or 0) > 0:
        return "project_config"
    if int(audit.get("evidence_error_count", 0) or 0) > 0:
        return "evidence_file"
    if any(gate.get("status") == "blocked_missing_evidence" for gate in audit.get("gates", [])):
        return "gate_evidence"
    if any(gate.get("status") == "failed_acceptance_rules" for gate in audit.get("gates", [])):
        return "acceptance_rules"
    if audit.get("missing_required_gates"):
        return "required_gates"
    if int(summary.get("blocker_count", 0) or 0) > 0:
        return "claim_blockers"
    return "unknown"


def audit_review_checks(audit: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, str]]:
    project_errors = int(audit.get("project_validation_error_count", 0) or 0)
    evidence_errors = int(audit.get("evidence_error_count", 0) or 0)
    blocker_count = int(summary.get("blocker_count", 0) or 0)
    completion_pct_value = float(summary.get("completion_pct", 0) or 0)
    warnings = int(audit.get("project_validation_warning_count", 0) or 0) + int(audit.get("evidence_warning_count", 0) or 0)
    return [
        {"check": "project_config_errors", "status": "passed" if project_errors == 0 else "blocked", "message": f"Project validation errors: {project_errors}."},
        {"check": "evidence_file_errors", "status": "passed" if evidence_errors == 0 else "blocked", "message": f"Evidence diagnostics errors: {evidence_errors}."},
        {"check": "required_gate_evidence", "status": "passed" if completion_pct_value == 100.0 else "blocked", "message": f"Required evidence completion: {completion_pct_value}%."},
        {"check": "gate_blockers", "status": "passed" if blocker_count == 0 else "blocked", "message": f"Gate blockers: {blocker_count}."},
        {"check": "warnings_review", "status": "passed" if warnings == 0 else "review", "message": f"Warnings requiring reviewer attention: {warnings}."},
        {"check": "human_review", "status": "review", "message": "A ready audit still needs human review of raw sources, claim wording, and downstream-use boundaries."},
    ]


def top_audit_blockers(audit: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for gate in audit.get("gates", []):
        for blocker in gate.get("blockers", []):
            item = {
                "gate_id": str(gate.get("gate_id", "")),
                "candidate_id": str(blocker.get("candidate_id", "")),
                "sample_id": str(blocker.get("sample_id", "")),
                "field": str(blocker.get("field", "")),
                "reasons": [str(reason) for reason in blocker.get("reasons", [])],
            }
            for key in ["actual", "operator", "expected"]:
                if key in blocker:
                    item[key] = blocker[key]
            blockers.append(item)
            if len(blockers) >= limit:
                return blockers
    return blockers


def audit_review(audit: dict[str, Any]) -> dict[str, Any]:
    summary = claim_summary(audit)
    status_counts = summary.get("status_counts", {}) if isinstance(summary.get("status_counts"), dict) else {}
    claim = audit.get("claim", {}) if isinstance(audit.get("claim"), dict) else {}
    review = {
        "status": "review_ready" if audit.get("claim_ready") else "review_blocked",
        "decision": "ready_for_human_review" if audit.get("claim_ready") else "blocked_before_review",
        "project_id": str(summary.get("project_id", "")),
        "claim_id": str(summary.get("claim_id", "")),
        "claim_statement": str(claim.get("statement", "")),
        "claim_ready": bool(summary.get("claim_ready")),
        "blocking_stage": audit_blocking_stage(audit, summary),
        "completion_pct": float(summary.get("completion_pct", 0) or 0),
        "gate_count": int(summary.get("gate_count", 0) or 0),
        "passed_gate_count": int(status_counts.get("passed", 0) or 0),
        "blocked_gate_count": int(status_counts.get("blocked_missing_evidence", 0) or 0),
        "failed_gate_count": int(status_counts.get("failed_acceptance_rules", 0) or 0),
        "valid_required_evidence_rows": int(summary.get("valid_required_evidence_rows", 0) or 0),
        "required_evidence_rows": int(summary.get("required_evidence_rows", 0) or 0),
        "derived_field_count": int(summary.get("derived_field_count", 0) or 0),
        "blocker_count": int(summary.get("blocker_count", 0) or 0),
        "project_validation_error_count": int(summary.get("project_validation_error_count", 0) or 0),
        "project_validation_warning_count": int(summary.get("project_validation_warning_count", 0) or 0),
        "evidence_error_count": int(summary.get("evidence_error_count", 0) or 0),
        "evidence_warning_count": int(summary.get("evidence_warning_count", 0) or 0),
        "top_blockers": top_audit_blockers(audit),
        "next_actions": audit.get("next_actions", [])[:10],
        "human_review_checklist": [
            "Confirm raw source files match the evidence rows and sample ids.",
            "Confirm claim wording is no broader than the configured gates and measured evidence.",
            "Confirm warnings are intentionally accepted or repaired before relying on the claim.",
            "Confirm the audit is not treated as model-quality, scientific-truth, safety, regulatory, or impact proof.",
        ],
        "gates": summary.get("gates", []),
    }
    review["checks"] = audit_review_checks(audit, summary)
    review["check_count"] = len(review["checks"])
    return review


def render_audit_review_report(review: dict[str, Any]) -> str:
    lines = [
        "# Falsiflow Audit Review",
        "",
        f"- Decision: `{review.get('decision', '')}`",
        f"- Status: `{review.get('status', '')}`",
        f"- Claim ready: `{str(bool(review.get('claim_ready'))).lower()}`",
        f"- Blocking stage: `{review.get('blocking_stage', '')}`",
        f"- Completion: {review.get('completion_pct', 0)}%",
        f"- Blockers: {review.get('blocker_count', 0)}",
        f"- Project errors: {review.get('project_validation_error_count', 0)}",
        f"- Evidence errors: {review.get('evidence_error_count', 0)}",
        "",
        "## Gate Snapshot",
        "",
        "| Gate | Status | Completion | Valid rows | Required rows | Blockers |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for gate in review.get("gates", []):
        if not isinstance(gate, dict):
            continue
        lines.append(
            f"| `{gate.get('gate_id', '')}` | `{gate.get('status', '')}` | {gate.get('completion_pct', 0)}% | "
            f"{gate.get('valid_required_evidence_rows', 0)} | {gate.get('required_evidence_rows', 0)} | {gate.get('blocker_count', 0)} |"
        )

    lines.extend(["", "## Checks", "", "| Check | Status | Message |", "| --- | --- | --- |"])
    for check in review.get("checks", []):
        if isinstance(check, dict):
            lines.append(f"| `{check.get('check', '')}` | `{check.get('status', '')}` | {check.get('message', '')} |")

    lines.extend(["", "## Top Blockers", ""])
    blockers = review.get("top_blockers", [])
    if blockers:
        lines.extend(["| Gate | Sample | Field | Reasons |", "| --- | --- | --- | --- |"])
        for blocker in blockers:
            if not isinstance(blocker, dict):
                continue
            reasons = "; ".join(str(reason) for reason in blocker.get("reasons", []))
            lines.append(f"| `{blocker.get('gate_id', '')}` | `{blocker.get('sample_id', '')}` | `{blocker.get('field', '')}` | {reasons} |")
    else:
        lines.append("No blockers found.")

    lines.extend(["", "## Next Actions", ""])
    for action in review.get("next_actions", []):
        if isinstance(action, dict):
            lines.append(f"- {action.get('rank', '')}. `{action.get('action_id', '')}` - {action.get('why', '')}")
    if not review.get("next_actions"):
        lines.append("- none")

    lines.extend(["", "## Human Review Checklist", ""])
    for item in review.get("human_review_checklist", []):
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def render_project(
    project: dict[str, Any],
    evidence_rows: list[dict[str, str]],
    evidence_file_issues: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {"audit": audit_project(project, evidence_rows, evidence_file_issues=evidence_file_issues)}


def write_audit_artifacts(audit: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    review = audit_review(audit)
    (out_dir / "claim_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "claim_audit.md").write_text(render_audit_report(audit), encoding="utf-8")
    (out_dir / "audit_review.json").write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "audit_review.md").write_text(render_audit_review_report(review), encoding="utf-8")
    (out_dir / "claim_summary.json").write_text(json.dumps(claim_summary(audit), indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "next_actions.json").write_text(json.dumps(audit.get("next_actions", []), indent=2, sort_keys=True), encoding="utf-8")


def write_render_artifacts(
    project: dict[str, Any],
    evidence_rows: list[dict[str, str]],
    out_dir: Path,
    evidence_file_issues: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rendered = render_project(project, evidence_rows, evidence_file_issues=evidence_file_issues)
    write_audit_artifacts(rendered["audit"], out_dir)
    return rendered
