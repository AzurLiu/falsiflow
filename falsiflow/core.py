"""Core Falsiflow evidence-gate logic.

The engine is intentionally small and dependency-free. A project config defines
claims, gates, required evidence fields, source-file policy, and acceptance
rules. Evidence CSV rows then either support or block a claim.
"""

from __future__ import annotations

import csv
import json
import operator
from html import escape
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

NUMERIC_DERIVED_OPERATIONS = {
    "abs_delta",
    "abs_pct_change",
    "delta",
    "difference",
    "gain_pct",
    "pct_change",
    "ratio",
    "reduction_pct",
    "subtract",
}

DERIVED_OPERATIONS = NUMERIC_DERIVED_OPERATIONS | {"all_false", "any_true", "copy"}


def add_issue(issues: list[dict[str, Any]], level: str, path: str, message: str) -> None:
    issues.append({"level": level, "path": path, "message": message})


def string_array_schema() -> dict[str, Any]:
    return {"type": "array", "items": {"type": "string"}}


def field_ref_schema() -> dict[str, Any]:
    return {
        "oneOf": [
            {"type": "string"},
            {
                "type": "object",
                "required": ["field"],
                "properties": {
                    "field": {"type": "string"},
                    "candidate_id": {"type": "string"},
                    "candidate_ids": string_array_schema(),
                    "candidate_id_contains": {"oneOf": [{"type": "string"}, string_array_schema()]},
                    "sample_id": {"type": "string"},
                    "sample_ids": string_array_schema(),
                    "sample_id_contains": {"oneOf": [{"type": "string"}, string_array_schema()]},
                },
                "additionalProperties": True,
            },
        ]
    }


def project_json_schema() -> dict[str, Any]:
    field_ref = field_ref_schema()
    rule_filter_properties = {
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
                        "candidate_ids": string_array_schema(),
                        "sample_ids": string_array_schema(),
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
                                    **rule_filter_properties,
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


def evidence_record_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/evidence-record.schema.json",
        "title": "Falsiflow discovery evidence record",
        "type": "object",
        "required": ["id", "claim", "material", "assay", "readout", "outcome", "caveat", "source_url"],
        "properties": {
            "id": {"type": "string"},
            "claim": {"type": "string"},
            "material": {"type": "string"},
            "mechanism": {"type": "string"},
            "assay": {"type": "string"},
            "readout": {"type": "string"},
            "outcome": {"type": "string"},
            "caveat": {"type": "string"},
            "source_url": {"type": "string"},
        },
        "additionalProperties": True,
    }


def candidate_recipe_json_schema() -> dict[str, Any]:
    gate_schema = {
        "type": "object",
        "required": ["id", "purpose", "required_evidence"],
        "properties": {
            "id": {"type": "string"},
            "purpose": {"type": "string"},
            "required_evidence": string_array_schema(),
            "acceptance_hint": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/candidate-recipe.schema.json",
        "title": "Falsiflow discovery candidate recipe",
        "type": "object",
        "required": ["id", "name", "material_stack", "expected_mechanism", "near_term_test", "kill_criteria", "recommended_gates"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "domain": {"type": "string"},
            "material_stack": {"type": "array", "items": {"type": "object"}},
            "expected_mechanism": {"type": "string"},
            "known_risks": string_array_schema(),
            "near_term_test": {"type": "string"},
            "kill_criteria": string_array_schema(),
            "recommended_gates": {"type": "array", "items": gate_schema},
            "evidence_refs": string_array_schema(),
        },
        "additionalProperties": True,
    }


def discovery_summary_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/discovery-summary.schema.json",
        "title": "Falsiflow discovery summary",
        "type": "object",
        "required": ["status", "goal", "ai_used", "claim_ready", "top_candidate", "outputs"],
        "properties": {
            "status": {"type": "string"},
            "goal": {"type": "string"},
            "ai_used": {"type": "boolean"},
            "claim_ready": {"type": "boolean"},
            "top_candidate": {"type": "string"},
            "candidate_count": {"type": "integer"},
            "evidence_record_count": {"type": "integer"},
            "outputs": {"type": "object"},
        },
        "additionalProperties": True,
    }


def claim_summary_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/claim-summary.schema.json",
        "title": "Falsiflow claim summary",
        "type": "object",
        "required": ["project_id", "claim_id", "status", "claim_ready", "gate_count", "blocker_count"],
        "properties": {
            "project_id": {"type": "string"},
            "claim_id": {"type": "string"},
            "status": {"type": "string", "enum": ["claim_ready", "claim_blocked"]},
            "claim_ready": {"type": "boolean"},
            "gate_count": {"type": "integer"},
            "status_counts": {"type": "object"},
            "valid_required_evidence_rows": {"type": "integer"},
            "required_evidence_rows": {"type": "integer"},
            "completion_pct": {"type": "number"},
            "derived_field_count": {"type": "integer"},
            "blocker_count": {"type": "integer"},
            "project_config_valid": {"type": "boolean"},
            "project_validation_error_count": {"type": "integer"},
            "project_validation_warning_count": {"type": "integer"},
            "evidence_issue_count": {"type": "integer"},
            "evidence_error_count": {"type": "integer"},
            "evidence_warning_count": {"type": "integer"},
            "next_action_count": {"type": "integer"},
            "gates": {"type": "array", "items": {"type": "object"}},
        },
        "additionalProperties": True,
    }


def audit_review_json_schema() -> dict[str, Any]:
    check_schema = {
        "type": "object",
        "required": ["check", "status", "message"],
        "properties": {
            "check": {"type": "string"},
            "status": {"type": "string", "enum": ["passed", "blocked", "review"]},
            "message": {"type": "string"},
        },
        "additionalProperties": True,
    }
    blocker_schema = {
        "type": "object",
        "required": ["gate_id", "sample_id", "field", "reasons"],
        "properties": {
            "gate_id": {"type": "string"},
            "candidate_id": {"type": "string"},
            "sample_id": {"type": "string"},
            "field": {"type": "string"},
            "reasons": string_array_schema(),
            "actual": {},
            "operator": {"type": "string"},
            "expected": {},
        },
        "additionalProperties": True,
    }
    gate_schema = {
        "type": "object",
        "required": ["gate_id", "status", "completion_pct", "blocker_count"],
        "properties": {
            "gate_id": {"type": "string"},
            "title": {"type": "string"},
            "status": {"type": "string"},
            "completion_pct": {"type": "number"},
            "valid_required_evidence_rows": {"type": "integer"},
            "required_evidence_rows": {"type": "integer"},
            "derived_field_count": {"type": "integer"},
            "blocker_count": {"type": "integer"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/audit-review.schema.json",
        "title": "Falsiflow audit review",
        "type": "object",
        "required": [
            "status",
            "decision",
            "project_id",
            "claim_id",
            "claim_ready",
            "blocking_stage",
            "completion_pct",
            "check_count",
            "checks",
            "gate_count",
            "blocker_count",
            "top_blockers",
            "next_actions",
            "human_review_checklist",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["review_ready", "review_blocked"]},
            "decision": {"type": "string"},
            "project_id": {"type": "string"},
            "claim_id": {"type": "string"},
            "claim_statement": {"type": "string"},
            "claim_ready": {"type": "boolean"},
            "blocking_stage": {"type": "string"},
            "completion_pct": {"type": "number"},
            "check_count": {"type": "integer"},
            "checks": {"type": "array", "items": check_schema},
            "gate_count": {"type": "integer"},
            "passed_gate_count": {"type": "integer"},
            "blocked_gate_count": {"type": "integer"},
            "failed_gate_count": {"type": "integer"},
            "valid_required_evidence_rows": {"type": "integer"},
            "required_evidence_rows": {"type": "integer"},
            "derived_field_count": {"type": "integer"},
            "blocker_count": {"type": "integer"},
            "project_validation_error_count": {"type": "integer"},
            "project_validation_warning_count": {"type": "integer"},
            "evidence_error_count": {"type": "integer"},
            "evidence_warning_count": {"type": "integer"},
            "top_blockers": {"type": "array", "items": blocker_schema},
            "next_actions": {"type": "array", "items": {"type": "object"}},
            "human_review_checklist": string_array_schema(),
            "gates": {"type": "array", "items": gate_schema},
        },
        "additionalProperties": True,
    }


def portfolio_summary_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/portfolio-summary.schema.json",
        "title": "Falsiflow portfolio summary",
        "type": "object",
        "required": ["status", "claim_count", "ready_count", "blocked_count", "claims"],
        "properties": {
            "status": {"type": "string", "enum": ["portfolio_ready", "portfolio_blocked"]},
            "claim_count": {"type": "integer"},
            "ready_count": {"type": "integer"},
            "blocked_count": {"type": "integer"},
            "status_counts": {"type": "object"},
            "completion_pct_avg": {"type": "number"},
            "blocker_count": {"type": "integer"},
            "project_validation_error_count": {"type": "integer"},
            "project_validation_warning_count": {"type": "integer"},
            "evidence_error_count": {"type": "integer"},
            "evidence_warning_count": {"type": "integer"},
            "claims": {"type": "array", "items": {"type": "object"}},
        },
        "additionalProperties": True,
    }


def import_coverage_json_schema() -> dict[str, Any]:
    evidence_key_schema = {
        "type": "object",
        "required": ["gate_id", "candidate_id", "sample_id", "field"],
        "properties": {
            "gate_id": {"type": "string"},
            "candidate_id": {"type": "string"},
            "sample_id": {"type": "string"},
            "field": {"type": "string"},
        },
        "additionalProperties": True,
    }
    gate_coverage_schema = {
        "type": "object",
        "required": [
            "gate_id",
            "required_evidence_rows",
            "matched_evidence_rows",
            "missing_evidence_rows",
            "completion_pct",
        ],
        "properties": {
            "gate_id": {"type": "string"},
            "required_evidence_rows": {"type": "integer"},
            "matched_evidence_rows": {"type": "integer"},
            "missing_evidence_rows": {"type": "integer"},
            "completion_pct": {"type": "number"},
            "missing_keys": {"type": "array", "items": evidence_key_schema},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/import-coverage.schema.json",
        "title": "Falsiflow import coverage",
        "type": "object",
        "required": [
            "status",
            "project_id",
            "claim_id",
            "required_evidence_rows",
            "matched_evidence_rows",
            "missing_evidence_rows",
            "completion_pct",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["coverage_ready", "coverage_blocked"]},
            "project_id": {"type": "string"},
            "claim_id": {"type": "string"},
            "required_evidence_rows": {"type": "integer"},
            "matched_evidence_rows": {"type": "integer"},
            "missing_evidence_rows": {"type": "integer"},
            "extra_evidence_rows": {"type": "integer"},
            "duplicate_configured_keys": {"type": "integer"},
            "duplicate_extra_keys": {"type": "integer"},
            "completion_pct": {"type": "number"},
            "evidence_file_issue_count": {"type": "integer"},
            "evidence_file_error_count": {"type": "integer"},
            "evidence_file_warning_count": {"type": "integer"},
            "gates": {"type": "array", "items": gate_coverage_schema},
            "missing_keys": {"type": "array", "items": evidence_key_schema},
            "extra_keys": {"type": "array", "items": evidence_key_schema},
            "duplicate_configured": {"type": "array", "items": evidence_key_schema},
            "duplicate_extra": {"type": "array", "items": evidence_key_schema},
        },
        "additionalProperties": True,
    }


def source_manifest_json_schema() -> dict[str, Any]:
    source_reference_schema = {
        "type": "object",
        "required": ["row_number", "gate_id", "candidate_id", "sample_id", "field"],
        "properties": {
            "row_number": {"type": "integer"},
            "gate_id": {"type": "string"},
            "candidate_id": {"type": "string"},
            "sample_id": {"type": "string"},
            "field": {"type": "string"},
        },
        "additionalProperties": True,
    }
    source_file_schema = {
        "type": "object",
        "required": ["source_file", "status", "reference_count", "resolved_path", "exists", "within_allowed_roots"],
        "properties": {
            "source_file": {"type": "string"},
            "status": {"type": "string", "enum": ["present", "missing", "outside_allowed_roots"]},
            "reference_count": {"type": "integer"},
            "resolved_path": {"type": "string"},
            "exists": {"type": "boolean"},
            "within_allowed_roots": {"type": "boolean"},
            "issue": {"type": "string"},
            "references": {"type": "array", "items": source_reference_schema},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/source-manifest.schema.json",
        "title": "Falsiflow source manifest",
        "type": "object",
        "required": [
            "status",
            "project_id",
            "claim_id",
            "source_policy_required",
            "evidence_row_count",
            "referenced_source_file_count",
            "present_source_file_count",
            "missing_source_file_count",
            "outside_allowed_roots_count",
            "blank_source_row_count",
            "blocker_count",
            "source_files",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["sources_ready", "sources_blocked"]},
            "project_id": {"type": "string"},
            "claim_id": {"type": "string"},
            "source_policy_required": {"type": "boolean"},
            "source_file_base_dir": {"type": "string"},
            "allowed_source_roots": string_array_schema(),
            "evidence_row_count": {"type": "integer"},
            "referenced_source_file_count": {"type": "integer"},
            "present_source_file_count": {"type": "integer"},
            "missing_source_file_count": {"type": "integer"},
            "outside_allowed_roots_count": {"type": "integer"},
            "blank_source_row_count": {"type": "integer"},
            "source_blocker_count": {"type": "integer"},
            "evidence_file_issue_count": {"type": "integer"},
            "evidence_file_error_count": {"type": "integer"},
            "evidence_file_warning_count": {"type": "integer"},
            "blocker_count": {"type": "integer"},
            "blank_source_rows": {"type": "array", "items": source_reference_schema},
            "source_files": {"type": "array", "items": source_file_schema},
        },
        "additionalProperties": True,
    }


def bundle_manifest_json_schema() -> dict[str, Any]:
    artifact_schema = {
        "type": "object",
        "required": ["role", "path", "bytes", "sha256"],
        "properties": {
            "role": {"type": "string"},
            "path": {"type": "string"},
            "bytes": {"type": "integer"},
            "sha256": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/bundle-manifest.schema.json",
        "title": "Falsiflow bundle manifest",
        "type": "object",
        "required": [
            "status",
            "project_id",
            "claim_id",
            "audit_status",
            "claim_ready",
            "source_status",
            "artifact_count",
            "source_file_count",
            "artifacts",
            "copied_source_files",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["bundle_ready", "bundle_blocked"]},
            "project_id": {"type": "string"},
            "claim_id": {"type": "string"},
            "audit_status": {"type": "string"},
            "claim_ready": {"type": "boolean"},
            "source_status": {"type": "string", "enum": ["sources_ready", "sources_blocked"]},
            "artifact_count": {"type": "integer"},
            "source_file_count": {"type": "integer"},
            "artifacts": {"type": "array", "items": artifact_schema},
            "copied_source_files": {"type": "array", "items": artifact_schema},
            "zip_path": {"type": "string"},
            "zip_bytes": {"type": "integer"},
            "zip_sha256": {"type": "string"},
        },
        "additionalProperties": True,
    }


def bundle_verification_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "expected": {},
            "actual": {},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/bundle-verification.schema.json",
        "title": "Falsiflow bundle verification",
        "type": "object",
        "required": [
            "status",
            "integrity_status",
            "bundle_status",
            "input_format",
            "input_path",
            "bundle_dir",
            "manifest_path",
            "artifact_count",
            "checked_artifact_count",
            "missing_artifact_count",
            "bytes_mismatch_count",
            "hash_mismatch_count",
            "unsafe_path_count",
            "duplicate_path_count",
            "unmanifested_file_count",
            "zip_issue_count",
            "issue_count",
            "error_count",
            "warning_count",
            "issues",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["bundle_verified", "bundle_blocked", "bundle_failed"]},
            "integrity_status": {"type": "string", "enum": ["integrity_verified", "integrity_failed"]},
            "bundle_status": {"type": "string"},
            "input_format": {"type": "string", "enum": ["directory", "zip"]},
            "input_path": {"type": "string"},
            "bundle_dir": {"type": "string"},
            "manifest_path": {"type": "string"},
            "artifact_count": {"type": "integer"},
            "checked_artifact_count": {"type": "integer"},
            "missing_artifact_count": {"type": "integer"},
            "bytes_mismatch_count": {"type": "integer"},
            "hash_mismatch_count": {"type": "integer"},
            "unsafe_path_count": {"type": "integer"},
            "duplicate_path_count": {"type": "integer"},
            "unmanifested_file_count": {"type": "integer"},
            "issue_count": {"type": "integer"},
            "error_count": {"type": "integer"},
            "warning_count": {"type": "integer"},
            "zip_path": {"type": "string"},
            "zip_member_count": {"type": "integer"},
            "zip_extracted_file_count": {"type": "integer"},
            "zip_issue_count": {"type": "integer"},
            "zip_bundle_root": {"type": "string"},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }


def claim_check_json_schema() -> dict[str, Any]:
    failure_schema = {
        "type": "object",
        "required": ["stage", "id", "message"],
        "properties": {
            "stage": {"type": "string"},
            "id": {"type": "string"},
            "message": {"type": "string"},
        },
        "additionalProperties": True,
    }
    action_schema = {
        "type": "object",
        "required": ["action_id", "why"],
        "properties": {
            "action_id": {"type": "string"},
            "rank": {"type": "integer"},
            "why": {"type": "string"},
            "gate_id": {"type": "string"},
            "sample_id": {"type": "string"},
            "field": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/claim-check.schema.json",
        "title": "Falsiflow claim check",
        "type": "object",
        "required": [
            "status",
            "project_id",
            "claim_id",
            "claim_check_ready",
            "claim_ready",
            "audit_status",
            "audit_review_status",
            "source_status",
            "bundle_status",
            "verification_status",
            "blocking_stage",
            "gate_count",
            "completion_pct",
            "blocker_count",
            "issue_count",
            "failure_count",
            "failures",
            "outputs",
            "next_actions",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["claim_check_ready", "claim_check_blocked"]},
            "project_id": {"type": "string"},
            "claim_id": {"type": "string"},
            "config_path": {"type": "string"},
            "evidence_path": {"type": "string"},
            "out_dir": {"type": "string"},
            "claim_check_ready": {"type": "boolean"},
            "claim_ready": {"type": "boolean"},
            "audit_status": {"type": "string"},
            "audit_review_status": {"type": "string"},
            "source_status": {"type": "string"},
            "bundle_status": {"type": "string"},
            "verification_status": {"type": "string"},
            "blocking_stage": {"type": "string"},
            "gate_count": {"type": "integer"},
            "completion_pct": {"type": "number"},
            "blocker_count": {"type": "integer"},
            "artifact_count": {"type": "integer"},
            "source_file_count": {"type": "integer"},
            "checked_artifact_count": {"type": "integer"},
            "issue_count": {"type": "integer"},
            "failure_count": {"type": "integer"},
            "failures": {"type": "array", "items": failure_schema},
            "outputs": {"type": "object"},
            "next_actions": {"type": "array", "items": action_schema},
        },
        "additionalProperties": True,
    }


def quickstart_summary_json_schema() -> dict[str, Any]:
    failure_schema = {
        "type": "object",
        "required": ["stage", "id", "message"],
        "properties": {
            "stage": {"type": "string"},
            "id": {"type": "string"},
            "message": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/quickstart-summary.schema.json",
        "title": "Falsiflow quickstart summary",
        "type": "object",
        "required": [
            "status",
            "template",
            "project_dir",
            "claim_check_status",
            "verification_status",
            "failure_count",
            "failures",
            "outputs",
            "next_commands",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["quickstart_ready", "quickstart_blocked"]},
            "template": {"type": "string"},
            "project_dir": {"type": "string"},
            "config_path": {"type": "string"},
            "evidence_path": {"type": "string"},
            "claim_check_status": {"type": "string"},
            "claim_ready": {"type": "boolean"},
            "audit_review_status": {"type": "string"},
            "source_status": {"type": "string"},
            "bundle_status": {"type": "string"},
            "verification_status": {"type": "string"},
            "failure_count": {"type": "integer"},
            "failures": {"type": "array", "items": failure_schema},
            "outputs": {"type": "object"},
            "next_commands": {"type": "array", "items": {"type": "string"}},
            "claim_check_summary": {"type": "object"},
        },
        "additionalProperties": True,
    }


def doctor_summary_json_schema() -> dict[str, Any]:
    failure_schema = {
        "type": "object",
        "required": ["stage", "id", "message"],
        "properties": {
            "stage": {"type": "string"},
            "id": {"type": "string"},
            "message": {"type": "string"},
        },
        "additionalProperties": True,
    }
    check_schema = {
        "type": "object",
        "required": ["check", "status", "message"],
        "properties": {
            "check": {"type": "string"},
            "status": {"type": "string", "enum": ["passed", "failed"]},
            "message": {"type": "string"},
            "path": {"type": "string"},
        },
        "additionalProperties": True,
    }
    action_schema = {
        "type": "object",
        "required": ["action_id", "why"],
        "properties": {
            "rank": {"type": "integer"},
            "action_id": {"type": "string"},
            "why": {"type": "string"},
        },
        "additionalProperties": True,
    }
    repair_schema = {
        "type": "object",
        "required": ["rank", "action_id", "why", "command", "expected_artifact"],
        "properties": {
            "rank": {"type": "integer"},
            "action_id": {"type": "string"},
            "why": {"type": "string"},
            "command": {"type": "string"},
            "expected_artifact": {"type": "string"},
            "success_signal": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/doctor-summary.schema.json",
        "title": "Falsiflow doctor summary",
        "type": "object",
        "required": [
            "status",
            "mode",
            "project_dir",
            "config_path",
            "evidence_path",
            "out_dir",
            "project_status",
            "evidence_status",
            "claim_check_status",
            "audit_review_status",
            "source_status",
            "bundle_status",
            "verification_status",
            "check_count",
            "failure_count",
            "checks",
            "failures",
            "outputs",
            "next_actions",
            "repair_checklist",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["doctor_ready", "doctor_blocked"]},
            "mode": {"type": "string", "enum": ["project"]},
            "project_dir": {"type": "string"},
            "config_path": {"type": "string"},
            "evidence_path": {"type": "string"},
            "out_dir": {"type": "string"},
            "project_status": {"type": "string"},
            "project_error_count": {"type": "integer"},
            "project_warning_count": {"type": "integer"},
            "evidence_status": {"type": "string"},
            "evidence_error_count": {"type": "integer"},
            "evidence_warning_count": {"type": "integer"},
            "claim_check_status": {"type": "string"},
            "claim_ready": {"type": "boolean"},
            "audit_review_status": {"type": "string"},
            "source_status": {"type": "string"},
            "bundle_status": {"type": "string"},
            "verification_status": {"type": "string"},
            "blocking_stage": {"type": "string"},
            "check_count": {"type": "integer"},
            "failure_count": {"type": "integer"},
            "checks": {"type": "array", "items": check_schema},
            "failures": {"type": "array", "items": failure_schema},
            "outputs": {"type": "object"},
            "next_actions": {"type": "array", "items": action_schema},
            "repair_checklist": {"type": "array", "items": repair_schema},
            "claim_check_summary": {"type": "object"},
        },
        "additionalProperties": True,
    }


def demo_summary_json_schema() -> dict[str, Any]:
    step_schema = {
        "type": "object",
        "required": ["step", "status"],
        "properties": {
            "step": {"type": "string"},
            "status": {"type": "string"},
            "path": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/demo-summary.schema.json",
        "title": "Falsiflow demo summary",
        "type": "object",
        "required": [
            "status",
            "template",
            "artifact_root",
            "project_dir",
            "validation_status",
            "audit_status",
            "claim_ready",
            "source_status",
            "bundle_status",
            "verification_status",
            "issue_count",
            "steps",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["demo_ready", "demo_blocked"]},
            "template": {"type": "string"},
            "artifact_root": {"type": "string"},
            "project_dir": {"type": "string"},
            "validation_status": {"type": "string"},
            "audit_status": {"type": "string"},
            "claim_ready": {"type": "boolean"},
            "source_status": {"type": "string"},
            "bundle_status": {"type": "string"},
            "verification_status": {"type": "string"},
            "issue_count": {"type": "integer"},
            "steps": {"type": "array", "items": step_schema},
        },
        "additionalProperties": True,
    }


def template_check_json_schema() -> dict[str, Any]:
    check_schema = {
        "type": "object",
        "required": ["check", "status", "message"],
        "properties": {
            "check": {"type": "string"},
            "status": {"type": "string", "enum": ["passed", "failed"]},
            "message": {"type": "string"},
            "path": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-check.schema.json",
        "title": "Falsiflow template check",
        "type": "object",
        "required": [
            "status",
            "template_id",
            "template_dir",
            "artifact_root",
            "manifest_status",
            "validation_status",
            "pass_audit_status",
            "pass_claim_ready",
            "placeholder_audit_status",
            "placeholder_claim_ready",
            "source_status",
            "bundle_status",
            "verification_status",
            "check_count",
            "failure_count",
            "checks",
            "failures",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_ready", "template_blocked"]},
            "template_id": {"type": "string"},
            "template_dir": {"type": "string"},
            "artifact_root": {"type": "string"},
            "manifest_status": {"type": "string", "enum": ["present", "missing", "invalid_json", "invalid_object"]},
            "manifest_path": {"type": "string"},
            "project_config_path": {"type": "string"},
            "pass_evidence_path": {"type": "string"},
            "placeholder_evidence_path": {"type": "string"},
            "validation_status": {"type": "string"},
            "pass_audit_status": {"type": "string"},
            "pass_claim_ready": {"type": "boolean"},
            "placeholder_audit_status": {"type": "string"},
            "placeholder_claim_ready": {"type": "boolean"},
            "source_status": {"type": "string"},
            "bundle_status": {"type": "string"},
            "verification_status": {"type": "string"},
            "check_count": {"type": "integer"},
            "failure_count": {"type": "integer"},
            "checks": {"type": "array", "items": check_schema},
            "failures": {"type": "array", "items": check_schema},
        },
        "additionalProperties": True,
    }


def template_pack_manifest_json_schema() -> dict[str, Any]:
    artifact_schema = {
        "type": "object",
        "required": ["role", "path", "bytes", "sha256"],
        "properties": {
            "role": {"type": "string"},
            "path": {"type": "string"},
            "bytes": {"type": "integer"},
            "sha256": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-pack-manifest.schema.json",
        "title": "Falsiflow template pack manifest",
        "type": "object",
        "required": [
            "status",
            "template_id",
            "template_check_status",
            "artifact_count",
            "artifacts",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_pack_ready", "template_pack_blocked"]},
            "template_id": {"type": "string"},
            "template_name": {"type": "string"},
            "template_domain": {"type": "string"},
            "template_check_status": {"type": "string"},
            "template_check_failure_count": {"type": "integer"},
            "artifact_count": {"type": "integer"},
            "artifacts": {"type": "array", "items": artifact_schema},
            "zip_path": {"type": "string"},
        },
        "additionalProperties": True,
    }


def template_pack_verification_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "expected": {},
            "actual": {},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-pack-verification.schema.json",
        "title": "Falsiflow template pack verification",
        "type": "object",
        "required": [
            "status",
            "integrity_status",
            "template_pack_status",
            "input_format",
            "input_path",
            "pack_dir",
            "manifest_path",
            "artifact_count",
            "checked_artifact_count",
            "missing_artifact_count",
            "bytes_mismatch_count",
            "hash_mismatch_count",
            "unsafe_path_count",
            "duplicate_path_count",
            "unmanifested_file_count",
            "issue_count",
            "error_count",
            "warning_count",
            "issues",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_pack_verified", "template_pack_blocked", "template_pack_failed"]},
            "integrity_status": {"type": "string", "enum": ["integrity_verified", "integrity_failed"]},
            "template_pack_status": {"type": "string"},
            "input_format": {"type": "string", "enum": ["directory", "zip"]},
            "input_path": {"type": "string"},
            "pack_dir": {"type": "string"},
            "manifest_path": {"type": "string"},
            "template_id": {"type": "string"},
            "artifact_count": {"type": "integer"},
            "checked_artifact_count": {"type": "integer"},
            "missing_artifact_count": {"type": "integer"},
            "bytes_mismatch_count": {"type": "integer"},
            "hash_mismatch_count": {"type": "integer"},
            "unsafe_path_count": {"type": "integer"},
            "duplicate_path_count": {"type": "integer"},
            "unmanifested_file_count": {"type": "integer"},
            "issue_count": {"type": "integer"},
            "error_count": {"type": "integer"},
            "warning_count": {"type": "integer"},
            "zip_path": {"type": "string"},
            "zip_member_count": {"type": "integer"},
            "zip_extracted_file_count": {"type": "integer"},
            "zip_issue_count": {"type": "integer"},
            "zip_pack_root": {"type": "string"},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }


def template_install_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "expected": {},
            "actual": {},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-install.schema.json",
        "title": "Falsiflow template install",
        "type": "object",
        "required": [
            "status",
            "template_id",
            "input_path",
            "templates_dir",
            "install_dir",
            "registry_path",
            "verification_status",
            "integrity_status",
            "template_check_status",
            "artifact_count",
            "installed_file_count",
            "registry_template_count",
            "attestation_required",
            "attestation_path",
            "attestation_status",
            "attestation_signature_verified",
            "policy_path",
            "policy_status",
            "issue_count",
            "error_count",
            "warning_count",
            "issues",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_installed", "template_install_blocked", "template_install_failed"]},
            "template_id": {"type": "string"},
            "template_name": {"type": "string"},
            "template_domain": {"type": "string"},
            "input_path": {"type": "string"},
            "templates_dir": {"type": "string"},
            "install_dir": {"type": "string"},
            "registry_path": {"type": "string"},
            "verification_status": {"type": "string"},
            "integrity_status": {"type": "string"},
            "template_check_status": {"type": "string"},
            "template_check_failure_count": {"type": "integer"},
            "artifact_count": {"type": "integer"},
            "installed_file_count": {"type": "integer"},
            "registry_template_count": {"type": "integer"},
            "attestation_required": {"type": "boolean"},
            "attestation_path": {"type": "string"},
            "attestation_status": {"type": "string"},
            "attestation_subject_type": {"type": "string"},
            "attestation_subject_sha256": {"type": "string"},
            "attestation_signature_verified": {"type": "boolean"},
            "attestation_key_id": {"type": "string"},
            "attestation_issue_count": {"type": "integer"},
            "policy_path": {"type": "string"},
            "policy_status": {"type": "string"},
            "policy_id": {"type": "string"},
            "policy_trusted_key_id": {"type": "string"},
            "policy_issue_count": {"type": "integer"},
            "release_path": {"type": "string"},
            "release_status": {"type": "string"},
            "release_sha256": {"type": "string"},
            "issue_count": {"type": "integer"},
            "error_count": {"type": "integer"},
            "warning_count": {"type": "integer"},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }


def template_registry_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "expected": {},
            "actual": {},
        },
        "additionalProperties": True,
    }
    entry_schema = {
        "type": "object",
        "required": [
            "status",
            "template_id",
            "source_type",
            "source_path",
            "source_bytes",
            "source_sha256",
            "verification_status",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_available", "template_blocked"]},
            "template_id": {"type": "string"},
            "template_name": {"type": "string"},
            "template_domain": {"type": "string"},
            "template_version": {"type": "string"},
            "template_project_id": {"type": "string"},
            "template_project_version": {"type": "string"},
            "source_type": {"type": "string", "enum": ["file", "url"]},
            "source_url": {"type": "string"},
            "source_path": {"type": "string"},
            "source_bytes": {"type": "integer"},
            "source_sha256": {"type": "string"},
            "verification_status": {"type": "string"},
            "integrity_status": {"type": "string"},
            "template_pack_status": {"type": "string"},
            "artifact_count": {"type": "integer"},
            "issue_count": {"type": "integer"},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-registry.schema.json",
        "title": "Falsiflow template registry",
        "type": "object",
        "required": [
            "status",
            "template_count",
            "verified_template_count",
            "duplicate_template_count",
            "issue_count",
            "error_count",
            "warning_count",
            "templates",
            "issues",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_registry_ready", "template_registry_blocked"]},
            "template_count": {"type": "integer"},
            "verified_template_count": {"type": "integer"},
            "duplicate_template_count": {"type": "integer"},
            "issue_count": {"type": "integer"},
            "error_count": {"type": "integer"},
            "warning_count": {"type": "integer"},
            "templates": {"type": "array", "items": entry_schema},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }


def template_lock_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "expected": {},
            "actual": {},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-lock.schema.json",
        "title": "Falsiflow template lock",
        "type": "object",
        "required": [
            "status",
            "template_id",
            "registry_path",
            "registry_sha256",
            "source_type",
            "source_path",
            "source_bytes",
            "source_sha256",
            "pack_verification_status",
            "artifact_count",
            "issue_count",
            "error_count",
            "warning_count",
            "issues",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_locked", "template_lock_blocked"]},
            "template_id": {"type": "string"},
            "template_name": {"type": "string"},
            "template_domain": {"type": "string"},
            "template_version": {"type": "string"},
            "template_project_version": {"type": "string"},
            "registry_path": {"type": "string"},
            "registry_sha256": {"type": "string"},
            "source_type": {"type": "string", "enum": ["file", "url", ""]},
            "source_url": {"type": "string"},
            "source_path": {"type": "string"},
            "cached_source_path": {"type": "string"},
            "source_bytes": {"type": "integer"},
            "source_sha256": {"type": "string"},
            "pack_verification_status": {"type": "string"},
            "artifact_count": {"type": "integer"},
            "issue_count": {"type": "integer"},
            "error_count": {"type": "integer"},
            "warning_count": {"type": "integer"},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }


def template_attestation_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "expected": {},
            "actual": {},
        },
        "additionalProperties": True,
    }
    payload_schema = {
        "type": "object",
        "required": ["subject_type", "subject_path", "subject_bytes", "subject_sha256", "created_at", "generator"],
        "properties": {
            "subject_type": {"type": "string", "enum": ["template-registry", "template-lock"]},
            "subject_path": {"type": "string"},
            "subject_bytes": {"type": "integer"},
            "subject_sha256": {"type": "string"},
            "created_at": {"type": "string"},
            "builder": {"type": "string"},
            "generator": {"type": "string"},
            "template_id": {"type": "string"},
            "template_version": {"type": "string"},
            "registry_sha256": {"type": "string"},
            "source_type": {"type": "string"},
            "source_url": {"type": "string"},
            "source_bytes": {"type": "integer"},
            "source_sha256": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-attestation.schema.json",
        "title": "Falsiflow template attestation",
        "type": "object",
        "required": [
            "status",
            "subject_type",
            "subject_path",
            "subject_bytes",
            "subject_sha256",
            "payload_sha256",
            "created_at",
            "signature_type",
            "signature",
            "key_id",
            "payload",
            "issue_count",
            "error_count",
            "warning_count",
            "issues",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_attested", "template_attestation_blocked"]},
            "subject_type": {"type": "string", "enum": ["template-registry", "template-lock"]},
            "subject_path": {"type": "string"},
            "subject_bytes": {"type": "integer"},
            "subject_sha256": {"type": "string"},
            "payload_sha256": {"type": "string"},
            "created_at": {"type": "string"},
            "builder": {"type": "string"},
            "generator": {"type": "string"},
            "signature_type": {"type": "string", "enum": ["hmac-sha256", "unsigned"]},
            "signature": {"type": "string"},
            "key_id": {"type": "string"},
            "payload": payload_schema,
            "issue_count": {"type": "integer"},
            "error_count": {"type": "integer"},
            "warning_count": {"type": "integer"},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }


def template_attestation_verification_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "expected": {},
            "actual": {},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-attestation-verification.schema.json",
        "title": "Falsiflow template attestation verification",
        "type": "object",
        "required": [
            "status",
            "attestation_path",
            "subject_type",
            "subject_path",
            "subject_bytes",
            "subject_sha256",
            "payload_sha256",
            "signature_type",
            "signature_verified",
            "issue_count",
            "error_count",
            "warning_count",
            "issues",
        ],
        "properties": {
            "status": {
                "type": "string",
                "enum": [
                    "template_attestation_verified",
                    "template_attestation_untrusted",
                    "template_attestation_failed",
                ],
            },
            "attestation_path": {"type": "string"},
            "subject_type": {"type": "string", "enum": ["template-registry", "template-lock", ""]},
            "subject_path": {"type": "string"},
            "subject_bytes": {"type": "integer"},
            "subject_sha256": {"type": "string"},
            "payload_sha256": {"type": "string"},
            "signature_type": {"type": "string"},
            "signature_verified": {"type": "boolean"},
            "key_id": {"type": "string"},
            "issue_count": {"type": "integer"},
            "error_count": {"type": "integer"},
            "warning_count": {"type": "integer"},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }


def template_policy_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "expected": {},
            "actual": {},
        },
        "additionalProperties": True,
    }
    expected_schema = {
        "type": "object",
        "required": ["template_id", "template_version", "source_sha256", "lock_sha256", "attestation_payload_sha256", "attestation_key_id"],
        "properties": {
            "template_id": {"type": "string"},
            "template_version": {"type": "string"},
            "source_type": {"type": "string"},
            "source_url": {"type": "string"},
            "source_bytes": {"type": "integer"},
            "source_sha256": {"type": "string"},
            "registry_sha256": {"type": "string"},
            "lock_sha256": {"type": "string"},
            "attestation_subject_sha256": {"type": "string"},
            "attestation_payload_sha256": {"type": "string"},
            "attestation_signature_type": {"type": "string"},
            "attestation_key_id": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-policy.schema.json",
        "title": "Falsiflow template policy",
        "type": "object",
        "required": [
            "status",
            "policy_id",
            "policy_version",
            "lock_path",
            "attestation_path",
            "template_id",
            "template_version",
            "require_attestation",
            "trusted_key_id",
            "expected",
            "attestation_status",
            "attestation_signature_verified",
            "issue_count",
            "error_count",
            "warning_count",
            "issues",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_policy_ready", "template_policy_blocked"]},
            "policy_id": {"type": "string"},
            "policy_version": {"type": "string"},
            "owner": {"type": "string"},
            "created_at": {"type": "string"},
            "generator": {"type": "string"},
            "lock_path": {"type": "string"},
            "attestation_path": {"type": "string"},
            "template_id": {"type": "string"},
            "template_version": {"type": "string"},
            "require_attestation": {"type": "boolean"},
            "trusted_key_id": {"type": "string"},
            "expected": expected_schema,
            "attestation_status": {"type": "string"},
            "attestation_signature_verified": {"type": "boolean"},
            "issue_count": {"type": "integer"},
            "error_count": {"type": "integer"},
            "warning_count": {"type": "integer"},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }


def template_policy_verification_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "expected": {},
            "actual": {},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-policy-verification.schema.json",
        "title": "Falsiflow template policy verification",
        "type": "object",
        "required": [
            "status",
            "policy_path",
            "policy_id",
            "lock_path",
            "attestation_path",
            "template_id",
            "template_version",
            "trusted_key_id",
            "attestation_status",
            "attestation_signature_verified",
            "expected",
            "actual",
            "issue_count",
            "error_count",
            "warning_count",
            "issues",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_policy_verified", "template_policy_failed"]},
            "policy_path": {"type": "string"},
            "policy_id": {"type": "string"},
            "lock_path": {"type": "string"},
            "attestation_path": {"type": "string"},
            "template_id": {"type": "string"},
            "template_version": {"type": "string"},
            "trusted_key_id": {"type": "string"},
            "attestation_status": {"type": "string"},
            "attestation_signature_verified": {"type": "boolean"},
            "expected": {"type": "object"},
            "actual": {"type": "object"},
            "issue_count": {"type": "integer"},
            "error_count": {"type": "integer"},
            "warning_count": {"type": "integer"},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }


def template_release_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "expected": {},
            "actual": {},
        },
        "additionalProperties": True,
    }
    artifact_schema = {
        "type": "object",
        "required": ["role", "path", "bytes", "sha256"],
        "properties": {
            "role": {"type": "string"},
            "path": {"type": "string"},
            "bytes": {"type": "integer"},
            "sha256": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-release.schema.json",
        "title": "Falsiflow template release",
        "type": "object",
        "required": [
            "status",
            "template_id",
            "template_version",
            "artifact_count",
            "artifacts",
            "pack_verification_status",
            "attestation_verification_status",
            "policy_verification_status",
            "source_sha256",
            "issue_count",
            "error_count",
            "warning_count",
            "issues",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_release_ready", "template_release_blocked"]},
            "template_id": {"type": "string"},
            "template_version": {"type": "string"},
            "created_at": {"type": "string"},
            "generator": {"type": "string"},
            "artifact_count": {"type": "integer"},
            "artifacts": {"type": "array", "items": artifact_schema},
            "pack_verification_status": {"type": "string"},
            "attestation_verification_status": {"type": "string"},
            "policy_verification_status": {"type": "string"},
            "trusted_key_id": {"type": "string"},
            "source_sha256": {"type": "string"},
            "release_zip_path": {"type": "string"},
            "release_zip_bytes": {"type": "integer"},
            "release_zip_sha256": {"type": "string"},
            "issue_count": {"type": "integer"},
            "error_count": {"type": "integer"},
            "warning_count": {"type": "integer"},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }


def template_release_verification_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "expected": {},
            "actual": {},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-release-verification.schema.json",
        "title": "Falsiflow template release verification",
        "type": "object",
        "required": [
            "status",
            "release_zip_path",
            "release_zip_sha256",
            "manifest_path",
            "template_id",
            "template_version",
            "pack_verification_status",
            "attestation_verification_status",
            "policy_verification_status",
            "missing_artifact_count",
            "bytes_mismatch_count",
            "hash_mismatch_count",
            "unsafe_path_count",
            "duplicate_path_count",
            "unmanifested_file_count",
            "issue_count",
            "error_count",
            "warning_count",
            "issues",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_release_verified", "template_release_failed"]},
            "release_zip_path": {"type": "string"},
            "release_zip_bytes": {"type": "integer"},
            "release_zip_sha256": {"type": "string"},
            "release_dir": {"type": "string"},
            "manifest_path": {"type": "string"},
            "template_id": {"type": "string"},
            "template_version": {"type": "string"},
            "zip_member_count": {"type": "integer"},
            "zip_extracted_file_count": {"type": "integer"},
            "artifact_count": {"type": "integer"},
            "artifact_paths": {"type": "object"},
            "missing_artifact_count": {"type": "integer"},
            "bytes_mismatch_count": {"type": "integer"},
            "hash_mismatch_count": {"type": "integer"},
            "unsafe_path_count": {"type": "integer"},
            "duplicate_path_count": {"type": "integer"},
            "unmanifested_file_count": {"type": "integer"},
            "zip_issue_count": {"type": "integer"},
            "pack_verification_status": {"type": "string"},
            "attestation_verification_status": {"type": "string"},
            "policy_verification_status": {"type": "string"},
            "attestation_verification_summary": {"type": "object"},
            "policy_verification_summary": {"type": "object"},
            "issue_count": {"type": "integer"},
            "error_count": {"type": "integer"},
            "warning_count": {"type": "integer"},
            "issues": {"type": "array", "items": issue_schema},
        },
        "additionalProperties": True,
    }


def template_gallery_json_schema() -> dict[str, Any]:
    issue_schema = {
        "type": "object",
        "required": ["severity", "code", "message", "path"],
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "path": {"type": "string"},
            "template": {"type": "string"},
        },
        "additionalProperties": True,
    }
    gate_schema = {
        "type": "object",
        "required": ["id", "title", "required_field_count", "sample_count", "acceptance_rule_count"],
        "properties": {
            "id": {"type": "string"},
            "title": {"type": "string"},
            "required_fields": string_array_schema(),
            "required_field_count": {"type": "integer"},
            "sample_count": {"type": "integer"},
            "derived_field_count": {"type": "integer"},
            "acceptance_rule_count": {"type": "integer"},
        },
        "additionalProperties": True,
    }
    template_schema = {
        "type": "object",
        "required": [
            "template",
            "name",
            "domain",
            "status",
            "path",
            "project_config",
            "claim_id",
            "claim_statement",
            "gate_count",
            "gates",
            "demo_evidence",
            "placeholder_evidence",
            "source_file_count",
            "first_commands",
        ],
        "properties": {
            "template": {"type": "string"},
            "name": {"type": "string"},
            "domain": {"type": "string"},
            "description": {"type": "string"},
            "status": {"type": "string"},
            "path": {"type": "string"},
            "root": {"type": "string"},
            "manifest": {"type": "string"},
            "project_config": {"type": "string"},
            "project_id": {"type": "string"},
            "claim_id": {"type": "string"},
            "claim_statement": {"type": "string"},
            "gate_count": {"type": "integer"},
            "required_evidence_row_count": {"type": "integer"},
            "gates": {"type": "array", "items": gate_schema},
            "demo_evidence": {"type": "string"},
            "placeholder_evidence": {"type": "string"},
            "demo_evidence_exists": {"type": "boolean"},
            "placeholder_evidence_exists": {"type": "boolean"},
            "source_file_count": {"type": "integer"},
            "source_files": string_array_schema(),
            "first_commands": string_array_schema(),
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/template-gallery.schema.json",
        "title": "Falsiflow template gallery",
        "type": "object",
        "required": [
            "status",
            "template_count",
            "valid_template_count",
            "domain_count",
            "non_neural_template_count",
            "template_roots",
            "templates",
            "issue_count",
            "issues",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["template_gallery_ready", "template_gallery_blocked"]},
            "template_count": {"type": "integer"},
            "valid_template_count": {"type": "integer"},
            "domain_count": {"type": "integer"},
            "non_neural_template_count": {"type": "integer"},
            "template_roots": string_array_schema(),
            "templates": {"type": "array", "items": template_schema},
            "issue_count": {"type": "integer"},
            "issues": {"type": "array", "items": issue_schema},
            "markdown_path": {"type": "string"},
            "json_path": {"type": "string"},
        },
        "additionalProperties": True,
    }


def casebook_check_json_schema() -> dict[str, Any]:
    failure_schema = {
        "type": "object",
        "required": ["stage", "id", "message"],
        "properties": {
            "stage": {"type": "string"},
            "id": {"type": "string"},
            "message": {"type": "string"},
        },
        "additionalProperties": True,
    }
    template_schema = {
        "type": "object",
        "required": [
            "template",
            "domain",
            "status",
            "claim_ready",
            "placeholder_blocks_claim",
            "source_status",
            "bundle_status",
            "verification_status",
            "artifact_dir",
        ],
        "properties": {
            "template": {"type": "string"},
            "domain": {"type": "string"},
            "project_id": {"type": "string"},
            "status": {"type": "string", "enum": ["case_ready", "case_blocked"]},
            "claim_ready": {"type": "boolean"},
            "pass_audit_status": {"type": "string"},
            "placeholder_blocks_claim": {"type": "boolean"},
            "placeholder_audit_status": {"type": "string"},
            "source_status": {"type": "string"},
            "bundle_status": {"type": "string"},
            "verification_status": {"type": "string"},
            "artifact_dir": {"type": "string"},
            "template_check": {"type": "string"},
            "claim_summary": {"type": "string"},
            "failure_count": {"type": "integer"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/casebook-check.schema.json",
        "title": "Falsiflow casebook check",
        "type": "object",
        "required": [
            "status",
            "artifact_root",
            "template_count",
            "ready_template_count",
            "domain_count",
            "non_neural_template_count",
            "positive_demo_ready_count",
            "blocked_path_count",
            "source_ready_count",
            "bundle_verified_count",
            "templates",
            "failure_count",
            "failures",
            "outputs",
            "reviewer_commands",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["casebook_check_ready", "casebook_check_blocked"]},
            "artifact_root": {"type": "string"},
            "template_count": {"type": "integer"},
            "ready_template_count": {"type": "integer"},
            "domain_count": {"type": "integer"},
            "non_neural_template_count": {"type": "integer"},
            "positive_demo_ready_count": {"type": "integer"},
            "blocked_path_count": {"type": "integer"},
            "source_ready_count": {"type": "integer"},
            "bundle_verified_count": {"type": "integer"},
            "templates": {"type": "array", "items": template_schema},
            "failure_count": {"type": "integer"},
            "failures": {"type": "array", "items": failure_schema},
            "outputs": {"type": "object"},
            "reviewer_commands": string_array_schema(),
        },
        "additionalProperties": True,
    }


def adoption_check_json_schema() -> dict[str, Any]:
    check_schema = {
        "type": "object",
        "required": ["check", "status", "message"],
        "properties": {
            "check": {"type": "string"},
            "status": {"type": "string", "enum": ["passed", "failed"]},
            "message": {"type": "string"},
            "path": {"type": "string"},
        },
        "additionalProperties": True,
    }
    priority_schema = {
        "type": "object",
        "required": ["priority_id", "title", "status", "check_count", "passed_check_count", "checks"],
        "properties": {
            "priority_id": {"type": "string"},
            "title": {"type": "string"},
            "status": {"type": "string", "enum": ["priority_ready", "priority_blocked"]},
            "check_count": {"type": "integer"},
            "passed_check_count": {"type": "integer"},
            "checks": {"type": "array", "items": check_schema},
            "next_actions": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    }
    failure_schema = {
        "type": "object",
        "required": ["stage", "id", "message"],
        "properties": {
            "stage": {"type": "string"},
            "id": {"type": "string"},
            "message": {"type": "string"},
        },
        "additionalProperties": True,
    }
    repair_schema = {
        "type": "object",
        "required": ["rank", "action_id", "why", "command", "expected_artifact", "success_signal"],
        "properties": {
            "rank": {"type": "integer"},
            "action_id": {"type": "string"},
            "priority_id": {"type": "string"},
            "failed_checks": {"type": "array", "items": {"type": "string"}},
            "why": {"type": "string"},
            "command": {"type": "string"},
            "expected_artifact": {"type": "string"},
            "success_signal": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/adoption-check.schema.json",
        "title": "Falsiflow adoption check",
        "type": "object",
        "required": [
            "status",
            "priority_count",
            "ready_priority_count",
            "readiness_pct",
            "release_validation_status",
            "release_validation_message",
            "casebook_check_status",
            "failure_count",
            "priorities",
            "failures",
            "outputs",
            "repair_checklist",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["adoption_ready", "adoption_blocked"]},
            "priority_count": {"type": "integer"},
            "ready_priority_count": {"type": "integer"},
            "readiness_pct": {"type": "number"},
            "release_validation_status": {"type": "string", "enum": ["release_validation_ready", "release_validation_skipped", "release_validation_blocked"]},
            "release_validation_message": {"type": "string"},
            "casebook_check_status": {"type": "string"},
            "failure_count": {"type": "integer"},
            "priorities": {"type": "array", "items": priority_schema},
            "failures": {"type": "array", "items": failure_schema},
            "outputs": {"type": "object"},
            "repair_checklist": {"type": "array", "items": repair_schema},
        },
        "additionalProperties": True,
    }


def release_check_json_schema() -> dict[str, Any]:
    failure_schema = {
        "type": "object",
        "required": ["stage", "id", "message"],
        "properties": {
            "stage": {"type": "string"},
            "id": {"type": "string"},
            "message": {"type": "string"},
        },
        "additionalProperties": True,
    }
    template_schema = {
        "type": "object",
        "required": [
            "template",
            "validation_status",
            "audit_status",
            "source_status",
            "bundle_status",
            "verification_status",
        ],
        "properties": {
            "template": {"type": "string"},
            "project_id": {"type": "string"},
            "validation_status": {"type": "string"},
            "audit_status": {"type": "string"},
            "claim_ready": {"type": "boolean"},
            "source_status": {"type": "string"},
            "bundle_status": {"type": "string"},
            "verification_status": {"type": "string"},
            "artifact_dir": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/release-check.schema.json",
        "title": "Falsiflow release check",
        "type": "object",
        "required": [
            "status",
            "artifact_root",
            "package_status",
            "package_check_count",
            "package_failure_count",
            "package_checks",
            "dist_status",
            "release_validation_status",
            "release_validation_message",
            "dist_check_count",
            "dist_failure_count",
            "dist_checks",
            "demo_status",
            "demo_summary",
            "demo_package_status",
            "demo_package_summary",
            "external_check_status",
            "external_check_summary",
            "publish_kit_status",
            "publish_kit_summary",
            "launch_kit_status",
            "launch_kit_summary",
            "quickstart_status",
            "quickstart_summary",
            "doctor_status",
            "doctor_summary",
            "claim_check_status",
            "claim_check_summary",
            "schema_count",
            "template_check_count",
            "template_check_ready_count",
            "template_checks",
            "template_pack_status",
            "template_pack_verification_status",
            "template_pack_summary",
            "template_install_status",
            "template_install_summary",
            "template_registry_status",
            "template_registry_summary",
            "template_lock_status",
            "template_lock_summary",
            "template_attestation_status",
            "template_attestation_summary",
            "template_attestation_verification_status",
            "template_attestation_verification_summary",
            "template_policy_status",
            "template_policy_summary",
            "template_policy_verification_status",
            "template_policy_verification_summary",
            "template_release_status",
            "template_release_summary",
            "template_release_verification_status",
            "template_release_verification_summary",
            "template_gallery_status",
            "template_gallery_summary",
            "casebook_check_status",
            "casebook_check_summary",
            "adoption_check_status",
            "adoption_check_summary",
            "template_count",
            "audit_ready_count",
            "source_ready_count",
            "bundle_ready_count",
            "bundle_verified_count",
            "failure_count",
            "failures",
            "schemas",
            "templates",
            "portfolio_status",
            "portfolio_claim_count",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["release_ready", "release_blocked"]},
            "artifact_root": {"type": "string"},
            "package_status": {"type": "string", "enum": ["package_ready", "package_blocked"]},
            "package_check_count": {"type": "integer"},
            "package_failure_count": {"type": "integer"},
            "package_checks": {"type": "array"},
            "dist_status": {"type": "string", "enum": ["dist_ready", "dist_blocked", "dist_skipped"]},
            "release_validation_status": {"type": "string", "enum": ["release_validation_ready", "release_validation_skipped", "release_validation_blocked"]},
            "release_validation_message": {"type": "string"},
            "dist_check_count": {"type": "integer"},
            "dist_failure_count": {"type": "integer"},
            "dist_checks": {"type": "array"},
            "demo_status": {"type": "string"},
            "demo_summary": {"type": "object"},
            "demo_package_status": {"type": "string"},
            "demo_package_summary": {"type": "object"},
            "external_check_status": {"type": "string"},
            "external_check_summary": {"type": "object"},
            "publish_kit_status": {"type": "string"},
            "publish_kit_summary": {"type": "object"},
            "launch_kit_status": {"type": "string"},
            "launch_kit_summary": {"type": "object"},
            "quickstart_status": {"type": "string"},
            "quickstart_summary": {"type": "object"},
            "doctor_status": {"type": "string"},
            "doctor_summary": {"type": "object"},
            "claim_check_status": {"type": "string"},
            "claim_check_summary": {"type": "object"},
            "schema_count": {"type": "integer"},
            "template_check_count": {"type": "integer"},
            "template_check_ready_count": {"type": "integer"},
            "template_checks": {"type": "array"},
            "template_pack_status": {"type": "string"},
            "template_pack_verification_status": {"type": "string"},
            "template_pack_summary": {"type": "object"},
            "template_install_status": {"type": "string"},
            "template_install_summary": {"type": "object"},
            "template_registry_status": {"type": "string"},
            "template_registry_summary": {"type": "object"},
            "template_lock_status": {"type": "string"},
            "template_lock_summary": {"type": "object"},
            "template_attestation_status": {"type": "string"},
            "template_attestation_summary": {"type": "object"},
            "template_attestation_verification_status": {"type": "string"},
            "template_attestation_verification_summary": {"type": "object"},
            "template_policy_status": {"type": "string"},
            "template_policy_summary": {"type": "object"},
            "template_policy_verification_status": {"type": "string"},
            "template_policy_verification_summary": {"type": "object"},
            "template_release_status": {"type": "string"},
            "template_release_summary": {"type": "object"},
            "template_release_verification_status": {"type": "string"},
            "template_release_verification_summary": {"type": "object"},
            "template_gallery_status": {"type": "string"},
            "template_gallery_summary": {"type": "object"},
            "casebook_check_status": {"type": "string"},
            "casebook_check_summary": {"type": "object"},
            "adoption_check_status": {"type": "string"},
            "adoption_check_summary": {"type": "object"},
            "template_count": {"type": "integer"},
            "audit_ready_count": {"type": "integer"},
            "source_ready_count": {"type": "integer"},
            "bundle_ready_count": {"type": "integer"},
            "bundle_verified_count": {"type": "integer"},
            "failure_count": {"type": "integer"},
            "failures": {"type": "array", "items": failure_schema},
            "schemas": {"type": "array"},
            "templates": {"type": "array", "items": template_schema},
            "portfolio_status": {"type": "string"},
            "portfolio_claim_count": {"type": "integer"},
        },
        "additionalProperties": True,
    }


def external_evidence_json_schema() -> dict[str, Any]:
    evidence_record = {
        "type": "object",
        "required": ["status"],
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "passed", "ready", "validated", "blocked", "failed"],
            },
            "url": {"type": "string"},
            "evidence_url": {"type": "string"},
            "workflow_url": {"type": "string"},
            "artifact_url": {"type": "string"},
            "report_url": {"type": "string"},
            "ci_url": {"type": "string"},
            "artifact": {"type": "string"},
            "artifact_sha256": {"type": "string"},
            "command": {"type": "string"},
            "expected_version": {"type": "string"},
            "published_version": {"type": "string"},
            "notes": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/external-evidence.schema.json",
        "title": "Falsiflow external evidence",
        "type": "object",
        "required": ["status", "version", "checks"],
        "properties": {
            "status": {
                "type": "string",
                "enum": ["external_evidence_draft", "external_evidence_ready", "external_evidence_blocked"],
            },
            "version": {"type": "integer"},
            "instructions": {"type": "string"},
            "checks": {
                "type": "object",
                "required": ["public_repo_url", "public_demo_url", "pypi_package_url", "pipx_smoke", "pipx_public_package", "mcp_public_package_selftest", "windows_powershell"],
                "properties": {
                    "public_repo_url": evidence_record,
                    "public_demo_url": evidence_record,
                    "pypi_package_url": evidence_record,
                    "pipx_smoke": evidence_record,
                    "pipx_public_package": evidence_record,
                    "mcp_public_package_selftest": evidence_record,
                    "windows_powershell": evidence_record,
                },
                "additionalProperties": True,
            },
        },
        "additionalProperties": True,
    }


def external_readiness_json_schema() -> dict[str, Any]:
    check_schema = {
        "type": "object",
        "required": ["check", "status", "message", "value", "evidence"],
        "properties": {
            "check": {"type": "string"},
            "status": {"type": "string", "enum": ["passed", "blocked"]},
            "message": {"type": "string"},
            "value": {"type": "string"},
            "evidence": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://falsiflow.dev/schemas/external-readiness.schema.json",
        "title": "Falsiflow external readiness",
        "type": "object",
        "required": [
            "status",
            "check_count",
            "ready_check_count",
            "blocker_count",
            "checks",
            "blockers",
            "external_evidence_status",
            "outputs",
            "next_commands",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["external_ready", "external_blocked"]},
            "check_count": {"type": "integer"},
            "ready_check_count": {"type": "integer"},
            "blocker_count": {"type": "integer"},
            "checks": {"type": "array", "items": check_schema},
            "blockers": {"type": "array", "items": check_schema},
            "external_evidence_status": {"type": "string", "enum": ["loaded", "error", "not_provided"]},
            "external_evidence_path": {"type": "string"},
            "external_evidence_error": {"type": "string"},
            "outputs": {"type": "object"},
            "next_commands": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    }


def falsiflow_schema(kind: str) -> dict[str, Any]:
    schemas = {
        "project": project_json_schema,
        "evidence-row": evidence_row_json_schema,
        "evidence-record": evidence_record_json_schema,
        "candidate-recipe": candidate_recipe_json_schema,
        "discovery-summary": discovery_summary_json_schema,
        "claim-summary": claim_summary_json_schema,
        "audit-review": audit_review_json_schema,
        "portfolio-summary": portfolio_summary_json_schema,
        "import-coverage": import_coverage_json_schema,
        "source-manifest": source_manifest_json_schema,
        "bundle-manifest": bundle_manifest_json_schema,
        "bundle-verification": bundle_verification_json_schema,
        "claim-check": claim_check_json_schema,
        "quickstart-summary": quickstart_summary_json_schema,
        "doctor-summary": doctor_summary_json_schema,
        "demo-summary": demo_summary_json_schema,
        "template-check": template_check_json_schema,
        "template-pack-manifest": template_pack_manifest_json_schema,
        "template-pack-verification": template_pack_verification_json_schema,
        "template-install": template_install_json_schema,
        "template-registry": template_registry_json_schema,
        "template-lock": template_lock_json_schema,
        "template-attestation": template_attestation_json_schema,
        "template-attestation-verification": template_attestation_verification_json_schema,
        "template-policy": template_policy_json_schema,
        "template-policy-verification": template_policy_verification_json_schema,
        "template-release": template_release_json_schema,
        "template-release-verification": template_release_verification_json_schema,
        "template-gallery": template_gallery_json_schema,
        "casebook-check": casebook_check_json_schema,
        "external-evidence": external_evidence_json_schema,
        "external-readiness": external_readiness_json_schema,
        "adoption-check": adoption_check_json_schema,
        "release-check": release_check_json_schema,
    }
    if kind == "all":
        return {schema_kind: factory() for schema_kind, factory in schemas.items()}
    if kind not in schemas:
        raise ValueError(f"unknown schema kind: {kind}")
    return schemas[kind]()


def load_project(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        project = json.load(handle)
    project.setdefault("_config_dir", str(path.resolve().parent))
    return project


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
            derived_path = f"{path}.derived_fields[{derived_index}]"
            operation = str(derived.get("operation", "")).strip()
            field = derived_field_id(derived)
            if not field:
                add_issue(issues, "error", derived_path, "Derived field must define `field` or `id`.")
            elif field in required_field_set:
                add_issue(
                    issues,
                    "error",
                    f"{derived_path}.field",
                    f"Derived field `{field}` would overwrite a required evidence field.",
                )
            elif field in derived_field_set:
                add_issue(issues, "error", f"{derived_path}.field", f"Duplicate derived field `{field}`.")
            if operation not in DERIVED_OPERATIONS:
                add_issue(issues, "error", f"{derived_path}.operation", f"Unknown derived operation `{operation}`.")
            else:
                for ref_path, ref in derived_input_refs(derived):
                    validate_field_ref(
                        issues=issues,
                        path=f"{derived_path}.{ref_path}",
                        ref=ref,
                        known_fields=known_fields,
                        sample_keys=sample_keys,
                    )
            if field:
                derived_field_set.add(field)
                known_fields.add(field)

        for rule_index, rule in enumerate(gate.get("acceptance_rules", [])):
            rule_path = f"{path}.acceptance_rules[{rule_index}]"
            field = str(rule.get("field", "")).strip()
            if not field:
                add_issue(issues, "error", f"{rule_path}.field", "Acceptance rule field is required.")
            elif field not in known_fields:
                add_issue(
                    issues,
                    "error",
                    f"{rule_path}.field",
                    f"Acceptance rule field `{field}` is not a required or derived field.",
                )
            operator_text = str(rule.get("operator", "")).strip()
            if operator_text not in OPERATORS:
                add_issue(issues, "error", f"{rule_path}.operator", f"Unknown acceptance operator `{operator_text}`.")

    required_gates = project.get("claim", {}).get("requires_gates", [])
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


def read_csv_rows_with_diagnostics(path: Path | None) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    if path is None or not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        stripped_fieldnames = [str(field or "").strip() for field in fieldnames]
        issues: list[dict[str, Any]] = evidence_header_diagnostics(stripped_fieldnames)
        rows: list[dict[str, str]] = []
        for row_number, raw_row in enumerate(reader, start=2):
            if None in raw_row:
                issues.append({
                    "level": "warning",
                    "kind": "evidence_row_extra_columns",
                    "row_number": row_number,
                    "message": "Evidence row has more values than header columns; extra values are ignored.",
                })
            row = {str(key or "").strip(): value for key, value in raw_row.items() if key is not None}
            rows.append(row)
            for column in EVIDENCE_KEY_COLUMNS:
                if column in stripped_fieldnames and not str(row.get(column, "") or "").strip():
                    issues.append({
                        "level": "warning",
                        "kind": "blank_evidence_key_component",
                        "row_number": row_number,
                        "field": column,
                        "message": f"Evidence row has a blank `{column}` key component and cannot match configured evidence.",
                    })
        return rows, issues


def read_csv_rows(path: Path | None) -> list[dict[str, str]]:
    rows, _issues = read_csv_rows_with_diagnostics(path)
    return rows


def evidence_header_diagnostics(fieldnames: list[str]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not fieldnames:
        issues.append({
            "level": "error",
            "kind": "missing_evidence_header",
            "message": "Evidence CSV has no header row.",
        })
        return issues

    seen: set[str] = set()
    duplicate_fields: set[str] = set()
    for field in fieldnames:
        if not field:
            issues.append({
                "level": "warning",
                "kind": "blank_evidence_column",
                "field": field,
                "message": "Evidence CSV has a blank column name.",
            })
            continue
        if field in seen:
            duplicate_fields.add(field)
        seen.add(field)
    for field in sorted(duplicate_fields):
        issues.append({
            "level": "error",
            "kind": "duplicate_evidence_column",
            "field": field,
            "message": f"Evidence CSV has duplicate column `{field}`.",
        })
    for field in EVIDENCE_REQUIRED_COLUMNS:
        if field not in seen:
            issues.append({
                "level": "error",
                "kind": "missing_required_evidence_column",
                "field": field,
                "message": f"Evidence CSV is missing required column `{field}`.",
            })
    for field in EVIDENCE_COLUMNS:
        if field not in seen and field not in EVIDENCE_REQUIRED_COLUMNS:
            issues.append({
                "level": "warning",
                "kind": "missing_standard_evidence_column",
                "field": field,
                "message": f"Evidence CSV is missing standard column `{field}`.",
            })
    return issues


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def placeholder_set(project: dict[str, Any]) -> set[str]:
    configured = project.get("evidence_policy", {}).get("placeholder_markers", [])
    return {str(item).strip().lower() for item in [*DEFAULT_PLACEHOLDERS, *configured]}


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


def field_ref(derived: dict[str, Any], key: str, inputs: list[str], index: int) -> Any:
    raw = derived.get(key)
    if raw is None and len(inputs) > index:
        raw = inputs[index]
    if isinstance(raw, dict):
        return raw
    return str(raw if raw is not None else "").strip()


def ref_label(ref: Any) -> str:
    if isinstance(ref, dict):
        field = str(ref.get("field", "")).strip()
        candidate = str(ref.get("candidate_id", "")).strip()
        sample = str(ref.get("sample_id", "")).strip()
        if candidate or sample:
            return f"{candidate or '*'}:{sample or '*'}:{field}"
        return field
    return str(ref).strip()


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


def resolve_ref_value(
    ref: Any,
    values: dict[str, Any],
    all_values: dict[tuple[str, str], dict[str, Any]],
    sample_key: tuple[str, str],
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
        target_key = matches[0]
        target_values = all_values[target_key]
        if field not in target_values:
            raise ValueError(f"required input field is missing: {ref_label(ref)}")
        return target_values[field]

    field = str(ref).strip()
    if field not in values:
        raise ValueError(f"required input field is missing: {field}")
    return values[field]


def numeric_field(
    values: dict[str, Any],
    ref: Any,
    all_values: dict[tuple[str, str], dict[str, Any]],
    sample_key: tuple[str, str],
) -> float:
    return number_value(resolve_ref_value(ref, values, all_values, sample_key), ref_label(ref))


def nonzero_denominator(value: float, label: str) -> float:
    if value == 0:
        raise ValueError(f"{label} is zero")
    return value


def bool_field(
    values: dict[str, Any],
    ref: Any,
    all_values: dict[tuple[str, str], dict[str, Any]],
    sample_key: tuple[str, str],
) -> bool:
    value = parse_scalar(resolve_ref_value(ref, values, all_values, sample_key))
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"true", "yes", "1"}:
        return True
    if lowered in {"false", "no", "0"}:
        return False
    raise ValueError(f"{ref_label(ref)} is not boolean")


def evaluate_derived_field(
    derived: dict[str, Any],
    values: dict[str, Any],
    all_values: dict[tuple[str, str], dict[str, Any]],
    sample_key: tuple[str, str],
) -> Any:
    operation = str(derived.get("operation", "")).strip()
    inputs = [str(item).strip() for item in derived.get("inputs", [])]
    if operation in {"delta", "difference", "subtract", "abs_delta"}:
        left_ref = field_ref(derived, "left", inputs, 0)
        right_ref = field_ref(derived, "right", inputs, 1)
        delta = numeric_field(values, left_ref, all_values, sample_key) - numeric_field(
            values,
            right_ref,
            all_values,
            sample_key,
        )
        return abs(delta) if operation == "abs_delta" else delta
    if operation in {"pct_change", "abs_pct_change", "gain_pct", "reduction_pct"}:
        before_ref = field_ref(derived, "before", inputs, 0)
        after_ref = field_ref(derived, "after", inputs, 1)
        before = nonzero_denominator(
            numeric_field(values, before_ref, all_values, sample_key),
            ref_label(before_ref),
        )
        after = numeric_field(values, after_ref, all_values, sample_key)
        if operation == "reduction_pct":
            return ((before - after) / before) * 100
        change = ((after - before) / before) * 100
        return abs(change) if operation == "abs_pct_change" else change
    if operation == "ratio":
        numerator_ref = field_ref(derived, "numerator", inputs, 0)
        denominator_ref = field_ref(derived, "denominator", inputs, 1)
        denominator = nonzero_denominator(
            numeric_field(values, denominator_ref, all_values, sample_key),
            ref_label(denominator_ref),
        )
        return numeric_field(values, numerator_ref, all_values, sample_key) / denominator
    if operation == "any_true":
        fields = inputs or [str(item).strip() for item in derived.get("fields", [])]
        if not fields:
            raise ValueError("any_true has no input fields")
        return any(bool_field(values, field, all_values, sample_key) for field in fields)
    if operation == "all_false":
        fields = inputs or [str(item).strip() for item in derived.get("fields", [])]
        if not fields:
            raise ValueError("all_false has no input fields")
        return all(not bool_field(values, field, all_values, sample_key) for field in fields)
    if operation == "copy":
        source_ref = field_ref(derived, "source", inputs, 0)
        return resolve_ref_value(source_ref, values, all_values, sample_key)
    raise ValueError(f"unknown derived operation: {operation}")


def derived_field_id(derived: dict[str, Any]) -> str:
    return str(derived.get("field") or derived.get("id") or "").strip()


def compute_derived_fields(
    gate: dict[str, Any],
    value_by_sample: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    derived_results: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for derived in gate.get("derived_fields", []):
        field = derived_field_id(derived)
        if not field:
            blockers.append({
                "gate_id": gate.get("id"),
                "field": "",
                "reasons": ["derived field is missing an id or field name"],
            })
            continue
        for sample_key, values in value_by_sample.items():
            try:
                value = evaluate_derived_field(derived, values, value_by_sample, sample_key)
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


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def text_contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


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
    raw = project.get("evidence_policy", {}).get("source_file_base_dir", "")
    if not raw:
        return config_dir(project)
    path = Path(str(raw))
    if not path.is_absolute():
        path = config_dir(project) / path
    return path.resolve()


def allowed_roots(project: dict[str, Any]) -> list[Path]:
    roots = project.get("evidence_policy", {}).get("allowed_source_roots", [])
    base = source_file_base_dir(project)
    resolved = []
    for root in roots:
        path = Path(str(root))
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


def gate_samples(gate: dict[str, Any]) -> list[dict[str, Any]]:
    samples = gate.get("samples", [])
    if samples:
        return samples
    return [{"candidate_id": candidate, "sample_id": sample} for candidate in gate.get("candidate_ids", []) for sample in gate.get("sample_ids", [])]


def measurement_template_rows(project: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for gate in project.get("gates", []):
        fields = gate.get("required_fields", [])
        for sample in gate_samples(gate):
            for field in fields:
                rows.append({
                    "gate_id": gate.get("id", ""),
                    "gate_title": gate.get("title", ""),
                    "candidate_id": sample.get("candidate_id", ""),
                    "sample_id": sample.get("sample_id", ""),
                    "field": field,
                    "value": "",
                    "source_file": "",
                    "measured_at": "",
                    "operator_or_agent": "",
                    "instrument_id": "",
                    "notes": "",
                })
    return rows


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
                "message": (
                    "Duplicate evidence rows for a configured key; use distinct sample_id values for replicates."
                    if configured
                    else "Duplicate evidence rows for an unconfigured key."
                ),
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
    require_sources = bool(project.get("evidence_policy", {}).get("require_source_files", True))
    reject_placeholders = bool(project.get("evidence_policy", {}).get("reject_placeholder_values", True))
    metadata_fields = project.get("evidence_policy", {}).get("required_metadata_fields", DEFAULT_METADATA_FIELDS)
    gate_results = []

    for gate in project.get("gates", []):
        blockers: list[dict[str, Any]] = []
        valid_required_rows = 0
        value_by_sample: dict[tuple[str, str], dict[str, Any]] = {}

        for sample in gate_samples(gate):
            candidate_id = str(sample.get("candidate_id", "")).strip()
            sample_id = str(sample.get("sample_id", "")).strip()
            sample_key = (candidate_id, sample_id)
            value_by_sample.setdefault(sample_key, {})
            for field in gate.get("required_fields", []):
                key = (str(gate.get("id", "")).strip(), candidate_id, sample_id, str(field).strip())
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
                        value_by_sample[sample_key][str(field)] = parse_scalar(raw_value)

                if row_blockers:
                    blockers.append({
                        "gate_id": gate.get("id"),
                        "candidate_id": candidate_id,
                        "sample_id": sample_id,
                        "field": field,
                        "reasons": row_blockers,
                    })

        derived_results, derived_blockers = compute_derived_fields(gate, value_by_sample)
        blockers.extend(derived_blockers)

        for rule in gate.get("acceptance_rules", []):
            field = str(rule.get("field", ""))
            op_text = str(rule.get("operator", ""))
            expected = rule.get("value")
            op = OPERATORS.get(op_text)
            if not op:
                blockers.append({
                    "gate_id": gate.get("id"),
                    "field": field,
                    "reasons": [f"unknown acceptance operator: {op_text}"],
                })
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
                        "reasons": [rule.get("reason", "acceptance rule failed")],
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

    required_gate_ids = set(project.get("claim", {}).get("requires_gates", []))
    gate_status = {gate["gate_id"]: gate["status"] for gate in gate_results}
    missing_gates = sorted(gate_id for gate_id in required_gate_ids if gate_id not in gate_status)
    gates_ready = not missing_gates and all(gate_status.get(gate_id) == "passed" for gate_id in required_gate_ids)
    claim_ready = project_error_count == 0 and evidence_error_count == 0 and gates_ready
    result = {
        "status": "claim_ready" if claim_ready else "claim_blocked",
        "claim_ready": claim_ready,
        "project": project.get("project", {}),
        "claim": project.get("claim", {}),
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
            "success_criterion": "Human review confirms raw sources and claim wording before release.",
        }]
    actions = []
    if int(audit.get("project_validation_error_count", 0) or 0) > 0:
        actions.append({
            "rank": 1,
            "action_id": "fix_project_config_diagnostics",
            "why": f"Project validation includes {audit.get('project_validation_error_count')} error(s).",
            "success_criterion": "Project validation is valid with zero errors before claim release.",
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
            "action_id": f"fill_{gate.get('gate_id')}_evidence",
            "why": f"Gate `{gate.get('gate_id')}` is `{gate.get('status')}` with {gate.get('blocker_count')} blocker(s).",
            "success_criterion": "All required rows have non-placeholder values, required metadata, and allowed source files; acceptance rules pass.",
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
    issues = validation.get("issues", [])
    if issues:
        for issue in issues[:40]:
            lines.append(f"- `{issue.get('level', '')}` `{issue.get('path', '')}`: {issue.get('message', '')}")
    else:
        lines.append("- none")

    lines.extend(["", "## Evidence Diagnostics", ""])
    issues = audit.get("evidence_issues", [])
    if issues:
        for issue in issues[:40]:
            lines.append(
                f"- `{issue.get('level', '')}` `{issue.get('kind', '')}` "
                f"`{issue.get('gate_id', '')}` `{issue.get('sample_id', '')}` "
                f"`{issue.get('field', '')}`: {issue.get('message', '')}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Blockers", ""])
    blocker_seen = False
    for gate in audit.get("gates", []):
        for blocker in gate.get("blockers", [])[:40]:
            blocker_seen = True
            reasons = "; ".join(blocker.get("reasons", []))
            lines.append(
                f"- `{gate['gate_id']}` `{blocker.get('sample_id', '-')}` `{blocker.get('field', '-')}`: {reasons}"
            )
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
    checks = [
        {
            "check": "project_config_errors",
            "status": "passed" if project_errors == 0 else "blocked",
            "message": f"Project validation errors: {project_errors}.",
        },
        {
            "check": "evidence_file_errors",
            "status": "passed" if evidence_errors == 0 else "blocked",
            "message": f"Evidence diagnostics errors: {evidence_errors}.",
        },
        {
            "check": "required_gate_evidence",
            "status": "passed" if completion_pct_value == 100.0 else "blocked",
            "message": f"Required evidence completion: {completion_pct_value}%.",
        },
        {
            "check": "gate_blockers",
            "status": "passed" if blocker_count == 0 else "blocked",
            "message": f"Gate blockers: {blocker_count}.",
        },
        {
            "check": "warnings_review",
            "status": "passed" if warnings == 0 else "review",
            "message": f"Warnings requiring reviewer attention: {warnings}.",
        },
        {
            "check": "human_release_review",
            "status": "review",
            "message": "A ready audit still needs human review of raw sources, claim wording, and downstream-use boundaries.",
        },
    ]
    return checks


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
    gate_status_counts = summary.get("status_counts", {}) if isinstance(summary.get("status_counts", {}), dict) else {}
    claim = audit.get("claim", {}) if isinstance(audit.get("claim", {}), dict) else {}
    review = {
        "status": "review_ready" if audit.get("claim_ready") else "review_blocked",
        "decision": "ready_for_human_release_review" if audit.get("claim_ready") else "blocked_before_release",
        "project_id": str(summary.get("project_id", "")),
        "claim_id": str(summary.get("claim_id", "")),
        "claim_statement": str(claim.get("statement", "")),
        "claim_ready": bool(summary.get("claim_ready")),
        "blocking_stage": audit_blocking_stage(audit, summary),
        "completion_pct": float(summary.get("completion_pct", 0) or 0),
        "gate_count": int(summary.get("gate_count", 0) or 0),
        "passed_gate_count": int(gate_status_counts.get("passed", 0) or 0),
        "blocked_gate_count": int(gate_status_counts.get("blocked_missing_evidence", 0) or 0),
        "failed_gate_count": int(gate_status_counts.get("failed_acceptance_rules", 0) or 0),
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
            "Confirm warnings are intentionally accepted or repaired before release.",
            "Confirm the audit is not treated as biological safety, clinical efficacy, regulatory compliance, or commercial readiness proof.",
        ],
        "gates": summary.get("gates", []),
    }
    checks = audit_review_checks(audit, summary)
    review["checks"] = checks
    review["check_count"] = len(checks)
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
        if not isinstance(check, dict):
            continue
        lines.append(f"| `{check.get('check', '')}` | `{check.get('status', '')}` | {check.get('message', '')} |")

    lines.extend(["", "## Top Blockers", ""])
    blockers = review.get("top_blockers", [])
    if blockers:
        lines.extend(["| Gate | Sample | Field | Reasons |", "| --- | --- | --- | --- |"])
        for blocker in blockers:
            if not isinstance(blocker, dict):
                continue
            reasons = "; ".join(str(reason) for reason in blocker.get("reasons", []))
            lines.append(
                f"| `{blocker.get('gate_id', '')}` | `{blocker.get('sample_id', '')}` | "
                f"`{blocker.get('field', '')}` | {reasons} |"
            )
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


def render_dashboard(audit: dict[str, Any]) -> str:
    summary = claim_summary(audit)
    status_class = "ready" if summary["claim_ready"] else "blocked"
    gates_html = []
    for gate in summary["gates"]:
        pct = gate["completion_pct"]
        gates_html.append(
            f"""
            <section class="gate">
              <div class="gate-head">
                <div>
                  <h2>{escape(str(gate['gate_id']))}</h2>
                  <p>{escape(str(gate['title']))}</p>
                </div>
                <span class="pill {escape(gate['status'])}">{escape(gate['status'])}</span>
              </div>
              <div class="bar"><span style="width: {pct}%"></span></div>
              <dl>
                <div><dt>Valid rows</dt><dd>{gate['valid_required_evidence_rows']} / {gate['required_evidence_rows']}</dd></div>
                <div><dt>Derived</dt><dd>{gate['derived_field_count']}</dd></div>
                <div><dt>Blockers</dt><dd>{gate['blocker_count']}</dd></div>
              </dl>
            </section>
            """
        )

    blocker_items = []
    for gate in audit.get("gates", []):
        for blocker in gate.get("blockers", [])[:20]:
            reasons = "; ".join(blocker.get("reasons", []))
            blocker_items.append(
                "<li>"
                f"<strong>{escape(str(gate.get('gate_id', '')))}</strong> "
                f"{escape(str(blocker.get('sample_id', '-')))} "
                f"<code>{escape(str(blocker.get('field', '-')))}</code>"
                f"<span>{escape(reasons)}</span>"
                "</li>"
            )
    if not blocker_items:
        blocker_items.append("<li>No blockers.</li>")

    actions_html = []
    for action in audit.get("next_actions", []):
        actions_html.append(
            "<li>"
            f"<strong>{action.get('rank', '')}. {escape(str(action.get('action_id', '')))}</strong>"
            f"<span>{escape(str(action.get('why', '')))}</span>"
            "</li>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Falsiflow Dashboard - {escape(str(summary['claim_id']))}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1f2933;
      --muted: #617080;
      --line: #d7dee7;
      --bg: #f7f9fb;
      --panel: #ffffff;
      --ready: #177245;
      --blocked: #b42318;
      --warn: #975a16;
      --accent: #246b8f;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }}
    main {{ width: min(1180px, calc(100% - 32px)); margin: 24px auto 48px; }}
    header {{ display: flex; justify-content: space-between; gap: 24px; align-items: flex-start; margin-bottom: 20px; }}
    h1 {{ font-size: 28px; line-height: 1.15; margin: 0 0 8px; letter-spacing: 0; }}
    h2 {{ font-size: 16px; margin: 0; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); }}
    code {{ background: #eef3f7; border: 1px solid var(--line); border-radius: 4px; padding: 1px 5px; }}
    .status {{ border: 1px solid var(--line); border-radius: 6px; background: var(--panel); padding: 10px 14px; min-width: 170px; text-align: right; }}
    .status strong {{ display: block; font-size: 20px; color: var(--blocked); }}
    .status.ready strong {{ color: var(--ready); }}
    .metrics {{ display: grid; grid-template-columns: repeat(9, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }}
    .metric, .gate, .list-panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 14px; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 6px; }}
    .metric strong {{ font-size: 22px; }}
    .gates {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin: 16px 0; }}
    .gate-head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }}
    .pill {{ white-space: nowrap; border-radius: 999px; padding: 4px 8px; font-size: 12px; border: 1px solid var(--line); color: var(--muted); }}
    .pill.passed {{ color: var(--ready); border-color: #a8d5bd; background: #eef8f2; }}
    .pill.blocked_missing_evidence {{ color: var(--blocked); border-color: #efb4ad; background: #fff1ef; }}
    .pill.failed_acceptance_rules {{ color: var(--warn); border-color: #f2d19b; background: #fff7e8; }}
    .bar {{ height: 8px; background: #e8edf2; border-radius: 999px; overflow: hidden; margin: 14px 0 12px; }}
    .bar span {{ display: block; height: 100%; background: var(--accent); }}
    dl {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 0; }}
    dt {{ color: var(--muted); font-size: 12px; }}
    dd {{ margin: 2px 0 0; font-weight: 600; }}
    .lists {{ display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(260px, .7fr); gap: 12px; }}
    ul {{ margin: 10px 0 0; padding-left: 18px; }}
    li {{ margin: 0 0 10px; }}
    li span {{ display: block; color: var(--muted); margin-top: 3px; }}
    @media (max-width: 820px) {{
      header, .lists {{ display: block; }}
      .status {{ text-align: left; margin-top: 12px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .list-panel {{ margin-bottom: 12px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Falsiflow Claim Dashboard</h1>
        <p>Project <code>{escape(str(summary['project_id']))}</code> / Claim <code>{escape(str(summary['claim_id']))}</code></p>
      </div>
      <div class="status {status_class}">
        <span>Status</span>
        <strong>{escape(str(summary['status']))}</strong>
      </div>
    </header>
    <section class="metrics">
      <div class="metric"><span>Claim ready</span><strong>{str(summary['claim_ready']).lower()}</strong></div>
      <div class="metric"><span>Completion</span><strong>{summary['completion_pct']}%</strong></div>
      <div class="metric"><span>Valid rows</span><strong>{summary['valid_required_evidence_rows']} / {summary['required_evidence_rows']}</strong></div>
      <div class="metric"><span>Derived values</span><strong>{summary['derived_field_count']}</strong></div>
      <div class="metric"><span>Blockers</span><strong>{summary['blocker_count']}</strong></div>
      <div class="metric"><span>Project errors</span><strong>{summary['project_validation_error_count']}</strong></div>
      <div class="metric"><span>Project warnings</span><strong>{summary['project_validation_warning_count']}</strong></div>
      <div class="metric"><span>Evidence errors</span><strong>{summary['evidence_error_count']}</strong></div>
      <div class="metric"><span>Evidence warnings</span><strong>{summary['evidence_warning_count']}</strong></div>
    </section>
    <section class="gates">
      {''.join(gates_html)}
    </section>
    <section class="lists">
      <div class="list-panel">
        <h2>Top Blockers</h2>
        <ul>{''.join(blocker_items)}</ul>
      </div>
      <div class="list-panel">
        <h2>Next Actions</h2>
        <ul>{''.join(actions_html)}</ul>
      </div>
    </section>
  </main>
</body>
</html>
"""


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def discover_claim_summary_paths(inputs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for raw in inputs:
        path = raw.expanduser()
        if path.is_file():
            if path.name == "claim_summary.json":
                paths.append(path)
            continue
        if path.is_dir():
            paths.extend(sorted(path.rglob("claim_summary.json")))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def first_action_for_summary(path: Path) -> dict[str, Any]:
    action_path = path.parent / "next_actions.json"
    if not action_path.exists():
        return {}
    actions = read_json(action_path)
    if isinstance(actions, list) and actions:
        return actions[0] if isinstance(actions[0], dict) else {}
    return {}


def portfolio_summary(summary_paths: list[Path]) -> dict[str, Any]:
    claims = []
    status_counts: dict[str, int] = {}
    ready_count = 0
    blocker_total = 0
    project_error_total = 0
    project_warning_total = 0
    evidence_error_total = 0
    evidence_warning_total = 0
    completion_total = 0.0

    for path in summary_paths:
        summary = read_json(path)
        if not isinstance(summary, dict):
            continue
        status = str(summary.get("status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
        claim_ready = bool(summary.get("claim_ready"))
        ready_count += 1 if claim_ready else 0
        blockers = int(summary.get("blocker_count", 0) or 0)
        project_errors = int(summary.get("project_validation_error_count", 0) or 0)
        project_warnings = int(summary.get("project_validation_warning_count", 0) or 0)
        evidence_errors = int(summary.get("evidence_error_count", 0) or 0)
        evidence_warnings = int(summary.get("evidence_warning_count", 0) or 0)
        blocker_total += blockers
        project_error_total += project_errors
        project_warning_total += project_warnings
        evidence_error_total += evidence_errors
        evidence_warning_total += evidence_warnings
        completion = float(summary.get("completion_pct", 0) or 0)
        completion_total += completion
        first_action = first_action_for_summary(path)
        claims.append({
            "source_path": str(path),
            "audit_dir": str(path.parent),
            "project_id": summary.get("project_id", ""),
            "claim_id": summary.get("claim_id", ""),
            "status": status,
            "claim_ready": claim_ready,
            "completion_pct": completion,
            "gate_count": int(summary.get("gate_count", 0) or 0),
            "blocker_count": blockers,
            "project_validation_error_count": project_errors,
            "project_validation_warning_count": project_warnings,
            "evidence_error_count": evidence_errors,
            "evidence_warning_count": evidence_warnings,
            "next_action_count": int(summary.get("next_action_count", 0) or 0),
            "first_action_id": first_action.get("action_id", ""),
            "first_action_why": first_action.get("why", ""),
        })

    claims.sort(key=lambda item: (item["claim_ready"], -item["blocker_count"], item["project_id"], item["claim_id"]))
    claim_count = len(claims)
    blocked_count = claim_count - ready_count
    return {
        "status": "portfolio_ready" if claim_count and blocked_count == 0 else "portfolio_blocked",
        "claim_count": claim_count,
        "ready_count": ready_count,
        "blocked_count": blocked_count,
        "status_counts": status_counts,
        "completion_pct_avg": round(completion_total / claim_count, 1) if claim_count else 0.0,
        "blocker_count": blocker_total,
        "project_validation_error_count": project_error_total,
        "project_validation_warning_count": project_warning_total,
        "evidence_error_count": evidence_error_total,
        "evidence_warning_count": evidence_warning_total,
        "claims": claims,
    }


def render_portfolio_report(portfolio: dict[str, Any]) -> str:
    lines = [
        "# Falsiflow Portfolio Summary",
        "",
        f"**Status:** `{portfolio.get('status')}`",
        f"**Claims:** {portfolio.get('claim_count', 0)}",
        f"**Ready:** {portfolio.get('ready_count', 0)}",
        f"**Blocked:** {portfolio.get('blocked_count', 0)}",
        f"**Average completion:** {portfolio.get('completion_pct_avg', 0)}%",
        f"**Blockers:** {portfolio.get('blocker_count', 0)}",
        f"**Project validation errors:** {portfolio.get('project_validation_error_count', 0)}",
        f"**Project validation warnings:** {portfolio.get('project_validation_warning_count', 0)}",
        f"**Evidence errors:** {portfolio.get('evidence_error_count', 0)}",
        f"**Evidence warnings:** {portfolio.get('evidence_warning_count', 0)}",
        "",
        "| Project | Claim | Status | Ready | Completion | Blockers | Project issues | Evidence issues | First action |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for claim in portfolio.get("claims", []):
        lines.append(
            f"| `{claim.get('project_id', '')}` | `{claim.get('claim_id', '')}` | "
            f"`{claim.get('status', '')}` | `{str(bool(claim.get('claim_ready'))).lower()}` | "
            f"{claim.get('completion_pct', 0)} | {claim.get('blocker_count', 0)} | "
            f"{claim.get('project_validation_error_count', 0)} / {claim.get('project_validation_warning_count', 0)} | "
            f"{claim.get('evidence_error_count', 0)} / {claim.get('evidence_warning_count', 0)} | "
            f"`{claim.get('first_action_id', '') or '-'}` |"
        )
    lines.append("")
    return "\n".join(lines)


def render_portfolio_dashboard(portfolio: dict[str, Any]) -> str:
    status_class = "ready" if portfolio.get("status") == "portfolio_ready" else "blocked"
    rows = []
    for claim in portfolio.get("claims", []):
        pct = float(claim.get("completion_pct", 0) or 0)
        rows.append(
            f"""
            <tr>
              <td><code>{escape(str(claim.get('project_id', '')))}</code></td>
              <td><code>{escape(str(claim.get('claim_id', '')))}</code></td>
              <td><span class="pill {escape(str(claim.get('status', '')))}">{escape(str(claim.get('status', '')))}</span></td>
              <td>{str(bool(claim.get('claim_ready'))).lower()}</td>
              <td>
                <div class="bar"><span style="width: {pct}%"></span></div>
                <span class="pct">{pct}%</span>
              </td>
              <td>{claim.get('blocker_count', 0)}</td>
              <td>{claim.get('project_validation_error_count', 0)} / {claim.get('project_validation_warning_count', 0)}</td>
              <td>{claim.get('evidence_error_count', 0)} / {claim.get('evidence_warning_count', 0)}</td>
              <td><code>{escape(str(claim.get('first_action_id', '') or '-'))}</code><small>{escape(str(claim.get('first_action_why', '')))}</small></td>
            </tr>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Falsiflow Portfolio Dashboard</title>
  <style>
    :root {{
      --ink: #1f2933;
      --muted: #617080;
      --line: #d7dee7;
      --bg: #f7f9fb;
      --panel: #ffffff;
      --ready: #177245;
      --blocked: #b42318;
      --accent: #246b8f;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }}
    main {{ width: min(1220px, calc(100% - 32px)); margin: 24px auto 48px; }}
    header {{ display: flex; justify-content: space-between; gap: 20px; align-items: flex-start; margin-bottom: 16px; }}
    h1 {{ font-size: 28px; margin: 0 0 8px; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); }}
    .status {{ border: 1px solid var(--line); border-radius: 6px; background: var(--panel); padding: 10px 14px; min-width: 170px; text-align: right; }}
    .status strong {{ display: block; font-size: 20px; color: var(--blocked); }}
    .status.ready strong {{ color: var(--ready); }}
    .metrics {{ display: grid; grid-template-columns: repeat(9, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }}
    .metric {{ background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 14px; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 6px; }}
    .metric strong {{ font-size: 22px; }}
    .table-wrap {{ overflow-x: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 6px; }}
    table {{ border-collapse: collapse; width: 100%; min-width: 900px; }}
    th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ color: var(--muted); font-size: 12px; font-weight: 600; }}
    code {{ background: #eef3f7; border: 1px solid var(--line); border-radius: 4px; padding: 1px 5px; }}
    small {{ display: block; color: var(--muted); margin-top: 4px; max-width: 360px; }}
    .pill {{ white-space: nowrap; border-radius: 999px; padding: 4px 8px; font-size: 12px; border: 1px solid var(--line); color: var(--muted); }}
    .pill.claim_ready {{ color: var(--ready); border-color: #a8d5bd; background: #eef8f2; }}
    .pill.claim_blocked {{ color: var(--blocked); border-color: #efb4ad; background: #fff1ef; }}
    .bar {{ height: 8px; min-width: 130px; background: #e8edf2; border-radius: 999px; overflow: hidden; margin-bottom: 4px; }}
    .bar span {{ display: block; height: 100%; background: var(--accent); }}
    .pct {{ color: var(--muted); font-size: 12px; }}
    @media (max-width: 820px) {{
      header {{ display: block; }}
      .status {{ text-align: left; margin-top: 12px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Falsiflow Portfolio Dashboard</h1>
        <p>Aggregated claim readiness across Falsiflow audit outputs.</p>
      </div>
      <div class="status {status_class}">
        <span>Status</span>
        <strong>{escape(str(portfolio.get('status', '')))}</strong>
      </div>
    </header>
    <section class="metrics">
      <div class="metric"><span>Claims</span><strong>{portfolio.get('claim_count', 0)}</strong></div>
      <div class="metric"><span>Ready</span><strong>{portfolio.get('ready_count', 0)}</strong></div>
      <div class="metric"><span>Blocked</span><strong>{portfolio.get('blocked_count', 0)}</strong></div>
      <div class="metric"><span>Avg completion</span><strong>{portfolio.get('completion_pct_avg', 0)}%</strong></div>
      <div class="metric"><span>Blockers</span><strong>{portfolio.get('blocker_count', 0)}</strong></div>
      <div class="metric"><span>Project errors</span><strong>{portfolio.get('project_validation_error_count', 0)}</strong></div>
      <div class="metric"><span>Project warnings</span><strong>{portfolio.get('project_validation_warning_count', 0)}</strong></div>
      <div class="metric"><span>Evidence errors</span><strong>{portfolio.get('evidence_error_count', 0)}</strong></div>
      <div class="metric"><span>Evidence warnings</span><strong>{portfolio.get('evidence_warning_count', 0)}</strong></div>
    </section>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Project</th>
            <th>Claim</th>
            <th>Status</th>
            <th>Ready</th>
            <th>Completion</th>
            <th>Blockers</th>
            <th>Project errors / warnings</th>
            <th>Evidence errors / warnings</th>
            <th>First Action</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </main>
</body>
</html>
"""


def write_portfolio_artifacts(summary_paths: list[Path], out_dir: Path) -> dict[str, Any]:
    portfolio = portfolio_summary(summary_paths)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "portfolio_summary.json").write_text(
        json.dumps(portfolio, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_dir / "portfolio_summary.md").write_text(render_portfolio_report(portfolio), encoding="utf-8")
    (out_dir / "portfolio_dashboard.html").write_text(render_portfolio_dashboard(portfolio), encoding="utf-8")
    return portfolio


def render_project(
    project: dict[str, Any],
    evidence_rows: list[dict[str, str]],
    evidence_file_issues: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "measurement_template_rows": measurement_template_rows(project),
        "audit": audit_project(project, evidence_rows, evidence_file_issues=evidence_file_issues),
    }


def write_audit_artifacts(audit: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    review = audit_review(audit)
    (out_dir / "claim_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "claim_audit.md").write_text(render_audit_report(audit), encoding="utf-8")
    (out_dir / "audit_review.json").write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "audit_review.md").write_text(render_audit_review_report(review), encoding="utf-8")
    (out_dir / "claim_summary.json").write_text(
        json.dumps(claim_summary(audit), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_dir / "next_actions.json").write_text(
        json.dumps(audit.get("next_actions", []), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_dir / "dashboard.html").write_text(render_dashboard(audit), encoding="utf-8")


def write_render_artifacts(
    project: dict[str, Any],
    evidence_rows: list[dict[str, str]],
    out_dir: Path,
    evidence_file_issues: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rendered = render_project(project, evidence_rows, evidence_file_issues=evidence_file_issues)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        out_dir / "measurement_template.csv",
        rendered["measurement_template_rows"],
        [
            "gate_id",
            "gate_title",
            "candidate_id",
            "sample_id",
            "field",
            "value",
            "source_file",
            "measured_at",
            "operator_or_agent",
            "instrument_id",
            "notes",
        ],
    )
    write_audit_artifacts(rendered["audit"], out_dir)
    return rendered
