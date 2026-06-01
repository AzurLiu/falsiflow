"""Regression checks for the Falsiflow evidence-gate MVP."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from falsiflow import __version__ as FALSIFLOW_VERSION  # noqa: E402
from falsiflow.adapters import build_project_from_evidence, limina_source_value_to_evidence  # noqa: E402
from falsiflow.cli import (  # noqa: E402
    adoption_release_validation_status,
    adoption_repair_checklist,
    run_discover,
    run_workbench_check,
    release_validation_status_for_dist,
)
from falsiflow.core import (  # noqa: E402
    audit_project,
    falsiflow_schema,
    load_project,
    read_csv_rows,
    read_csv_rows_with_diagnostics,
    validate_project_config,
)


PROJECT_PATH = ROOT / "examples" / "falsiflow" / "neural_materials" / "project.json"
PASS_EVIDENCE = ROOT / "examples" / "falsiflow" / "neural_materials" / "evidence_pass_demo.csv"
PLACEHOLDER_EVIDENCE = ROOT / "examples" / "falsiflow" / "neural_materials" / "evidence_placeholder_demo.csv"
CLI = ROOT / "scripts" / "falsiflow.py"
EXAMPLE_TEMPLATE_ROOT = ROOT / "examples" / "falsiflow"
PACKAGE_TEMPLATE_ROOT = ROOT / "falsiflow" / "templates"
EXPECTED_TEMPLATE_IDS = {
    "neural_materials",
    "rfq_vendor_evidence",
    "biointerface_coatings",
    "wetware_support_hardware",
    "ai_claim_evaluation",
    "rag_quality_gate",
    "product_metric_launch",
}
EXPECTED_TEMPLATE_COUNT = len(EXPECTED_TEMPLATE_IDS)
EXPECTED_NON_NEURAL_TEMPLATE_COUNT = EXPECTED_TEMPLATE_COUNT - 1


def relative_files(root: Path) -> list[Path]:
    return sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())


def write_tampered_zip(source_zip: Path, target_zip: Path, transform) -> None:
    with zipfile.ZipFile(source_zip) as archive:
        entries = {
            info.filename: archive.read(info)
            for info in archive.infolist()
            if not info.is_dir()
        }
    entries = transform(entries)
    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            archive.writestr(name, data)


def sha256_data(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fill_ready_evidence_template(path: Path, source_file: str = "source_files/raw_export.csv", value: str | None = None) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    for index, row in enumerate(rows, start=1):
        row["value"] = value if value is not None else str(index)
        row["source_file"] = source_file
        row["measured_at"] = "2026-05-25T09:00:00Z"
        row["operator_or_agent"] = "falsiflow_regression"
        row["instrument_id"] = "instrument_regression"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def assert_blocked_blank(project: dict) -> None:
    audit = audit_project(project, [])
    assert audit["claim_ready"] is False
    assert audit["status"] == "claim_blocked"
    assert all(gate["status"] == "blocked_missing_evidence" for gate in audit["gates"])
    assert audit["next_actions"], "blocked audit should provide next actions"


def assert_blocked_placeholder(project: dict) -> None:
    audit = audit_project(project, read_csv_rows(PLACEHOLDER_EVIDENCE))
    assert audit["claim_ready"] is False
    reasons = [
        reason
        for gate in audit["gates"]
        for blocker in gate["blockers"]
        for reason in blocker["reasons"]
    ]
    assert "value is blank or placeholder" in reasons
    assert "missing evidence row" in reasons


def assert_passes(project: dict) -> None:
    audit = audit_project(project, read_csv_rows(PASS_EVIDENCE))
    assert audit["claim_ready"] is True
    assert audit["status"] == "claim_ready"
    assert audit["evidence_error_count"] == 0
    assert audit["evidence_warning_count"] == 0
    assert all(gate["status"] == "passed" for gate in audit["gates"])
    derived = {
        (item["gate_id"], item["sample_id"], item["field"]): item["value"]
        for gate in audit["gates"]
        for item in gate["derived_fields"]
    }
    assert round(float(derived[("h_a_medium_stability", "ha_demo_001", "ph_drift_24h_abs")]), 3) == 0.08
    assert round(float(derived[("h_b_electrical_interface", "hb_demo_001", "impedance_reduction_1khz_pct")]), 1) == 31.0
    assert round(float(derived[("h_c_network_response", "hc_demo_candidate", "burst_rate_ratio_vs_control")]), 2) == 0.96
    assert round(float(derived[("h_c_network_response", "hc_demo_control", "burst_rate_ratio_vs_control")]), 2) == 1.00


def assert_derived_rule_failure(project: dict) -> None:
    rows = read_csv_rows(PASS_EVIDENCE)
    for row in rows:
        if row["gate_id"] == "h_a_medium_stability" and row["field"] == "ph_final":
            row["value"] = "7.50"
    audit = audit_project(project, rows)
    assert audit["claim_ready"] is False
    h_a = next(gate for gate in audit["gates"] if gate["gate_id"] == "h_a_medium_stability")
    assert h_a["status"] == "failed_acceptance_rules"
    blockers = [reason for blocker in h_a["blockers"] for reason in blocker["reasons"]]
    assert "pH drift must stay inside the H-A stability window." in blockers


def assert_evidence_diagnostics_contract(project: dict) -> None:
    rows = read_csv_rows(PASS_EVIDENCE)

    duplicated = [dict(row) for row in rows]
    duplicate_row = dict(duplicated[0])
    duplicate_row["value"] = "999"
    duplicated.append(duplicate_row)
    audit = audit_project(project, duplicated)
    assert audit["claim_ready"] is False
    assert audit["evidence_error_count"] == 1
    assert any(issue["kind"] == "duplicate_evidence_key" for issue in audit["evidence_issues"])
    duplicate_reasons = [
        reason
        for gate in audit["gates"]
        for blocker in gate["blockers"]
        for reason in blocker["reasons"]
    ]
    assert "duplicate evidence rows for key (2 rows)" in duplicate_reasons

    extra = [dict(row) for row in rows]
    extra.append({
        "gate_id": "unused_gate",
        "candidate_id": "unused_candidate",
        "sample_id": "unused_sample",
        "field": "unused_field",
        "value": "123",
        "source_file": "",
        "measured_at": "",
        "operator_or_agent": "",
        "instrument_id": "",
        "notes": "",
    })
    audit = audit_project(project, extra)
    assert audit["claim_ready"] is True
    assert audit["evidence_error_count"] == 0
    assert audit["evidence_warning_count"] == 1
    assert audit["evidence_issues"][0]["kind"] == "unconfigured_evidence_key"


def assert_evidence_csv_format_contract(project: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        header_error_project = {
            "project": {"id": "header_error_contract"},
            "claim": {"id": "claim", "requires_gates": ["gate_a"]},
            "evidence_policy": {
                "require_source_files": False,
                "required_metadata_fields": [],
            },
            "gates": [
                {
                    "id": "gate_a",
                    "samples": [{"candidate_id": "candidate", "sample_id": "sample_001"}],
                    "required_fields": ["score"],
                    "acceptance_rules": [{"field": "score", "operator": ">=", "value": 10}],
                }
            ],
        }

        missing_field_column = tmp_dir / "missing_field_column.csv"
        missing_field_column.write_text(
            "\n".join([
                "gate_id,candidate_id,sample_id,value,source_file,measured_at,operator_or_agent",
                "h_a_medium_stability,alg_lam_pedot_lowdose,ha_demo_001,7.20,source_files/demo_raw_export.csv,2026-05-25T09:00:00Z,demo_operator",
            ]),
            encoding="utf-8",
        )
        rows, issues = read_csv_rows_with_diagnostics(missing_field_column)
        assert len(rows) == 1
        assert any(issue["kind"] == "missing_required_evidence_column" and issue["field"] == "field" for issue in issues)
        audit = audit_project(project, rows, evidence_file_issues=issues)
        assert audit["claim_ready"] is False
        assert audit["evidence_error_count"] >= 1

        duplicate_column = tmp_dir / "duplicate_column.csv"
        duplicate_column.write_text(
            "\n".join([
                "gate_id,candidate_id,sample_id,field,value,value",
                "gate_a,candidate,sample_001,score,11,11",
            ]),
            encoding="utf-8",
        )
        rows, issues = read_csv_rows_with_diagnostics(duplicate_column)
        assert any(issue["kind"] == "duplicate_evidence_column" and issue["field"] == "value" for issue in issues)
        audit = audit_project(header_error_project, rows, evidence_file_issues=issues)
        assert audit["status"] == "claim_blocked"
        assert audit["claim_ready"] is False
        assert audit["evidence_error_count"] == 1
        assert all(gate["status"] == "passed" for gate in audit["gates"])
        assert audit["next_actions"][0]["action_id"] == "fix_evidence_file_diagnostics"

        blank_key = tmp_dir / "blank_key.csv"
        blank_key.write_text(
            "\n".join([
                "gate_id,candidate_id,sample_id,field,value,source_file,measured_at,operator_or_agent",
                "h_a_medium_stability,,ha_demo_001,ph_initial,7.20,source_files/demo_raw_export.csv,2026-05-25T09:00:00Z,demo_operator",
            ]),
            encoding="utf-8",
        )
        _rows, issues = read_csv_rows_with_diagnostics(blank_key)
        assert any(issue["kind"] == "blank_evidence_key_component" and issue["field"] == "candidate_id" for issue in issues)


def assert_config_validation_contract() -> None:
    invalid_project = {
        "project": {"id": "invalid_contract"},
        "claim": {"id": "claim", "requires_gates": ["gate_a"]},
        "gates": [
            {
                "id": "gate_a",
                "samples": [
                    {"candidate_id": "candidate", "sample_id": "sample_001"},
                    {"candidate_id": "candidate", "sample_id": "sample_001"},
                ],
                "required_fields": ["score", "score"],
                "derived_fields": [
                    {"field": "score", "operation": "copy", "source": "raw_score"},
                    {"field": "ratio_to_control", "operation": "ratio", "numerator": "score", "denominator": {
                        "candidate_id": "missing_control",
                        "sample_id": "control_001",
                        "field": "score",
                    }},
                ],
                "acceptance_rules": [
                    {"field": "typo_score", "operator": ">=", "value": 1},
                    {"field": "score", "operator": "approximately", "value": 1},
                ],
            }
        ],
    }
    validation = validate_project_config(invalid_project)
    assert validation["valid"] is False
    messages = [issue["message"] for issue in validation["issues"]]
    assert any("Duplicate sample" in message for message in messages)
    assert any("Duplicate required field `score`" in message for message in messages)
    assert any("would overwrite a required evidence field" in message for message in messages)
    assert any("Referenced field `raw_score`" in message for message in messages)
    assert any("matches no configured sample" in message for message in messages)
    assert any("Acceptance rule field `typo_score`" in message for message in messages)
    assert any("Unknown acceptance operator" in message for message in messages)


def assert_schema_contract() -> None:
    project_schema = falsiflow_schema("project")
    assert project_schema["title"] == "Falsiflow project config"
    operations = project_schema["properties"]["gates"]["items"]["properties"]["derived_fields"]["items"]["properties"]["operation"]["enum"]
    assert "ratio" in operations
    operators = project_schema["properties"]["gates"]["items"]["properties"]["acceptance_rules"]["items"]["properties"]["operator"]["enum"]
    assert ">=" in operators

    evidence_schema = falsiflow_schema("evidence-row")
    assert evidence_schema["required"] == ["gate_id", "candidate_id", "sample_id", "field", "value"]
    assert "source_file" in evidence_schema["properties"]

    all_schemas = falsiflow_schema("all")
    assert {"project", "evidence-row", "evidence-record", "candidate-recipe", "discovery-summary", "claim-summary", "audit-review", "portfolio-summary", "import-coverage", "source-manifest", "bundle-manifest", "bundle-verification", "claim-check", "quickstart-summary", "doctor-summary", "demo-summary", "template-check", "template-pack-manifest", "template-pack-verification", "template-install", "template-registry", "template-lock", "template-attestation", "template-attestation-verification", "template-policy", "template-policy-verification", "template-release", "template-release-verification", "template-gallery", "casebook-check", "external-evidence", "external-readiness", "adoption-check", "release-check"} <= set(all_schemas)
    evidence_record_schema = falsiflow_schema("evidence-record")
    assert evidence_record_schema["title"] == "Falsiflow discovery evidence record"
    assert "source_url" in evidence_record_schema["required"]
    candidate_recipe_schema = falsiflow_schema("candidate-recipe")
    assert candidate_recipe_schema["title"] == "Falsiflow discovery candidate recipe"
    assert "recommended_gates" in candidate_recipe_schema["required"]
    discovery_summary_schema = falsiflow_schema("discovery-summary")
    assert discovery_summary_schema["title"] == "Falsiflow discovery summary"
    assert "ai_used" in discovery_summary_schema["required"]
    assert "claim_ready" in discovery_summary_schema["required"]
    coverage_schema = falsiflow_schema("import-coverage")
    assert coverage_schema["title"] == "Falsiflow import coverage"
    assert "coverage_ready" in coverage_schema["properties"]["status"]["enum"]
    source_schema = falsiflow_schema("source-manifest")
    assert source_schema["title"] == "Falsiflow source manifest"
    assert "sources_ready" in source_schema["properties"]["status"]["enum"]
    bundle_schema = falsiflow_schema("bundle-manifest")
    assert bundle_schema["title"] == "Falsiflow bundle manifest"
    assert "bundle_ready" in bundle_schema["properties"]["status"]["enum"]
    verification_schema = falsiflow_schema("bundle-verification")
    assert verification_schema["title"] == "Falsiflow bundle verification"
    assert "bundle_verified" in verification_schema["properties"]["status"]["enum"]
    claim_check_schema = falsiflow_schema("claim-check")
    assert claim_check_schema["title"] == "Falsiflow claim check"
    assert "claim_check_ready" in claim_check_schema["properties"]["status"]["enum"]
    assert "claim_check_blocked" in claim_check_schema["properties"]["status"]["enum"]
    quickstart_schema = falsiflow_schema("quickstart-summary")
    assert quickstart_schema["title"] == "Falsiflow quickstart summary"
    assert "quickstart_ready" in quickstart_schema["properties"]["status"]["enum"]
    assert "next_commands" in quickstart_schema["required"]
    doctor_schema = falsiflow_schema("doctor-summary")
    assert doctor_schema["title"] == "Falsiflow doctor summary"
    assert "doctor_ready" in doctor_schema["properties"]["status"]["enum"]
    assert "repair_checklist" in doctor_schema["required"]
    demo_schema = falsiflow_schema("demo-summary")
    assert demo_schema["title"] == "Falsiflow demo summary"
    assert "demo_ready" in demo_schema["properties"]["status"]["enum"]
    template_check_schema = falsiflow_schema("template-check")
    assert template_check_schema["title"] == "Falsiflow template check"
    assert "template_ready" in template_check_schema["properties"]["status"]["enum"]
    template_pack_schema = falsiflow_schema("template-pack-manifest")
    assert template_pack_schema["title"] == "Falsiflow template pack manifest"
    assert "template_pack_ready" in template_pack_schema["properties"]["status"]["enum"]
    template_pack_verification_schema = falsiflow_schema("template-pack-verification")
    assert template_pack_verification_schema["title"] == "Falsiflow template pack verification"
    assert "template_pack_verified" in template_pack_verification_schema["properties"]["status"]["enum"]
    template_install_schema = falsiflow_schema("template-install")
    assert template_install_schema["title"] == "Falsiflow template install"
    assert "template_installed" in template_install_schema["properties"]["status"]["enum"]
    assert "attestation_status" in template_install_schema["properties"]
    assert "attestation_signature_verified" in template_install_schema["required"]
    assert "policy_status" in template_install_schema["properties"]
    template_registry_schema = falsiflow_schema("template-registry")
    assert template_registry_schema["title"] == "Falsiflow template registry"
    assert "template_registry_ready" in template_registry_schema["properties"]["status"]["enum"]
    registry_entry_props = template_registry_schema["properties"]["templates"]["items"]["properties"]
    assert "source_url" in registry_entry_props
    assert "template_version" in registry_entry_props
    template_lock_schema = falsiflow_schema("template-lock")
    assert template_lock_schema["title"] == "Falsiflow template lock"
    assert "template_locked" in template_lock_schema["properties"]["status"]["enum"]
    assert "source_url" in template_lock_schema["properties"]
    assert "template_version" in template_lock_schema["properties"]
    template_attestation_schema = falsiflow_schema("template-attestation")
    assert template_attestation_schema["title"] == "Falsiflow template attestation"
    assert "template_attested" in template_attestation_schema["properties"]["status"]["enum"]
    assert "hmac-sha256" in template_attestation_schema["properties"]["signature_type"]["enum"]
    template_attestation_verification_schema = falsiflow_schema("template-attestation-verification")
    assert template_attestation_verification_schema["title"] == "Falsiflow template attestation verification"
    assert "template_attestation_verified" in template_attestation_verification_schema["properties"]["status"]["enum"]
    template_policy_schema = falsiflow_schema("template-policy")
    assert template_policy_schema["title"] == "Falsiflow template policy"
    assert "template_policy_ready" in template_policy_schema["properties"]["status"]["enum"]
    template_policy_verification_schema = falsiflow_schema("template-policy-verification")
    assert template_policy_verification_schema["title"] == "Falsiflow template policy verification"
    assert "template_policy_verified" in template_policy_verification_schema["properties"]["status"]["enum"]
    template_release_schema = falsiflow_schema("template-release")
    assert template_release_schema["title"] == "Falsiflow template release"
    assert "template_release_ready" in template_release_schema["properties"]["status"]["enum"]
    template_release_verification_schema = falsiflow_schema("template-release-verification")
    assert template_release_verification_schema["title"] == "Falsiflow template release verification"
    assert "template_release_verified" in template_release_verification_schema["properties"]["status"]["enum"]
    assert "unsafe_path_count" in template_release_verification_schema["properties"]
    assert "unmanifested_file_count" in template_release_verification_schema["required"]
    audit_review_schema = falsiflow_schema("audit-review")
    assert audit_review_schema["title"] == "Falsiflow audit review"
    assert "review_ready" in audit_review_schema["properties"]["status"]["enum"]
    assert "human_review_checklist" in audit_review_schema["required"]
    template_gallery_schema = falsiflow_schema("template-gallery")
    assert template_gallery_schema["title"] == "Falsiflow template gallery"
    assert "template_gallery_ready" in template_gallery_schema["properties"]["status"]["enum"]
    assert "non_neural_template_count" in template_gallery_schema["required"]
    casebook_check_schema = falsiflow_schema("casebook-check")
    assert casebook_check_schema["title"] == "Falsiflow casebook check"
    assert "casebook_check_ready" in casebook_check_schema["properties"]["status"]["enum"]
    assert "blocked_path_count" in casebook_check_schema["required"]
    external_evidence_schema = falsiflow_schema("external-evidence")
    assert external_evidence_schema["title"] == "Falsiflow external evidence"
    assert "public_demo_url" in external_evidence_schema["properties"]["checks"]["required"]
    assert "pypi_package_url" in external_evidence_schema["properties"]["checks"]["required"]
    assert "pipx_smoke" in external_evidence_schema["properties"]["checks"]["required"]
    assert "pipx_public_package" in external_evidence_schema["properties"]["checks"]["required"]
    assert "public_package_first_run" in external_evidence_schema["properties"]["checks"]["required"]
    assert "public_package_claim_check" in external_evidence_schema["properties"]["checks"]["required"]
    assert "mcp_public_package_selftest" in external_evidence_schema["properties"]["checks"]["required"]
    pypi_evidence_properties = external_evidence_schema["properties"]["checks"]["properties"]["pypi_package_url"]["properties"]
    assert "expected_version" in pypi_evidence_properties
    assert "published_version" in pypi_evidence_properties
    external_readiness_schema = falsiflow_schema("external-readiness")
    assert external_readiness_schema["title"] == "Falsiflow external readiness"
    assert "external_ready" in external_readiness_schema["properties"]["status"]["enum"]
    assert "external_evidence_status" in external_readiness_schema["required"]
    adoption_schema = falsiflow_schema("adoption-check")
    assert adoption_schema["title"] == "Falsiflow adoption check"
    assert "adoption_ready" in adoption_schema["properties"]["status"]["enum"]
    assert "adoption_blocked" in adoption_schema["properties"]["status"]["enum"]
    assert "ready_priority_count" in adoption_schema["required"]
    assert "release_validation_status" in adoption_schema["required"]
    assert "release_validation_ready" in adoption_schema["properties"]["release_validation_status"]["enum"]
    assert "release_validation_skipped" in adoption_schema["properties"]["release_validation_status"]["enum"]
    assert "casebook_check_status" in adoption_schema["required"]
    assert "repair_checklist" in adoption_schema["required"]
    release_schema = falsiflow_schema("release-check")
    assert release_schema["title"] == "Falsiflow release check"
    assert "release_ready" in release_schema["properties"]["status"]["enum"]
    assert "package_status" in release_schema["required"]
    assert "dist_status" in release_schema["required"]
    assert "release_validation_status" in release_schema["required"]
    assert "release_validation_ready" in release_schema["properties"]["release_validation_status"]["enum"]
    assert "release_validation_skipped" in release_schema["properties"]["release_validation_status"]["enum"]
    assert "demo_package_status" in release_schema["required"]
    assert "external_check_status" in release_schema["required"]
    assert "publish_kit_status" in release_schema["required"]
    assert "launch_kit_status" in release_schema["required"]
    assert "template_check_ready_count" in release_schema["required"]
    assert "template_pack_verification_status" in release_schema["required"]
    assert "template_install_status" in release_schema["required"]
    assert "template_registry_status" in release_schema["required"]
    assert "template_lock_status" in release_schema["required"]
    assert "template_attestation_status" in release_schema["required"]
    assert "template_attestation_verification_status" in release_schema["required"]
    assert "quickstart_status" in release_schema["required"]
    assert "doctor_status" in release_schema["required"]
    assert "claim_check_status" in release_schema["required"]
    assert "template_policy_status" in release_schema["required"]
    assert "template_policy_verification_status" in release_schema["required"]
    assert "template_release_status" in release_schema["required"]
    assert "template_release_verification_status" in release_schema["required"]
    assert "template_gallery_status" in release_schema["required"]
    assert "casebook_check_status" in release_schema["required"]
    assert "adoption_check_status" in release_schema["required"]


def assert_adoption_repair_checklist_contract() -> None:
    assert release_validation_status_for_dist("dist_ready")[0] == "release_validation_ready"
    assert release_validation_status_for_dist("dist_skipped")[0] == "release_validation_skipped"
    assert release_validation_status_for_dist("dist_blocked")[0] == "release_validation_blocked"
    assert adoption_release_validation_status("dist_ready")[0] == "release_validation_ready"
    assert adoption_release_validation_status("dist_skipped")[0] == "release_validation_skipped"
    assert adoption_release_validation_status("dist_blocked")[0] == "release_validation_blocked"

    artifact_root = Path("/tmp/falsiflow_adoption_blocked_contract")
    blocked_priorities = [
        {"priority_id": "open_source_entry_point", "status": "priority_blocked", "failed_checks": ["quickstart_ready"]},
        {"priority_id": "trusted_audit_experience", "status": "priority_blocked", "failed_checks": ["doctor_ready"]},
        {"priority_id": "generality_proof", "status": "priority_blocked", "failed_checks": ["template_gallery_ready"]},
        {"priority_id": "release_and_distribution", "status": "priority_blocked", "failed_checks": ["dist_ready_or_skipped"]},
        {"priority_id": "user_experience_convergence", "status": "priority_blocked", "failed_checks": ["adoption_check_docs"]},
    ]

    checklist = adoption_repair_checklist(blocked_priorities, artifact_root, "dist_skipped")
    assert [item["action_id"] for item in checklist] == [
        "repair_open_source_entry_point",
        "repair_trusted_audit_experience",
        "repair_generality_proof",
        "repair_release_and_distribution",
        "repair_user_experience_convergence",
    ]
    assert checklist[0]["command"].startswith("falsiflow quickstart")
    assert checklist[0]["expected_artifact"].endswith("quickstart_project/quickstart_summary.json")
    assert checklist[1]["command"].startswith("falsiflow doctor")
    assert checklist[1]["expected_artifact"].endswith("doctor/doctor_summary.json")
    assert checklist[2]["command"].startswith("falsiflow template-gallery")
    assert checklist[2]["expected_artifact"].endswith("template_gallery.json")
    assert checklist[3]["command"].startswith("falsiflow release-check")
    assert checklist[3]["expected_artifact"].endswith("release_check/release_check.json")
    assert checklist[4]["command"].startswith("falsiflow adoption-check")
    assert "--skip-dist" in checklist[4]["command"]
    assert checklist[4]["expected_artifact"].endswith("adoption_check.md")
    assert all(item["failed_checks"] for item in checklist)
    assert all(item["success_signal"] for item in checklist)

    ready_checklist = adoption_repair_checklist([], artifact_root, "dist_skipped")
    assert ready_checklist[0]["action_id"] == "verify_adoption_ready"
    assert "--skip-dist" in ready_checklist[0]["command"]
    assert ready_checklist[0]["expected_artifact"].endswith("adoption_check.json")

    release_ready_checklist = adoption_repair_checklist([], artifact_root, "dist_ready")
    assert release_ready_checklist[0]["action_id"] == "verify_adoption_ready"
    assert "--skip-dist" not in release_ready_checklist[0]["command"]
    safe_release_ready_checklist = adoption_repair_checklist(
        [],
        artifact_root,
        "dist_ready",
        adoption_rerun_root=artifact_root / "adoption_recheck",
    )
    assert "adoption_recheck" in safe_release_ready_checklist[0]["command"]
    assert safe_release_ready_checklist[0]["expected_artifact"].endswith("adoption_recheck/adoption_check.json")


def assert_project_validation_blocks_claim() -> None:
    invalid_but_measured_project = {
        "project": {"id": "invalid_but_measured"},
        "claim": {"id": "claim", "requires_gates": ["gate_a"]},
        "evidence_policy": {
            "require_source_files": False,
            "required_metadata_fields": [],
        },
        "gates": [
            {
                "id": "gate_a",
                "samples": [
                    {"candidate_id": "candidate", "sample_id": "sample_001"},
                    {"candidate_id": "candidate", "sample_id": "sample_001"},
                ],
                "required_fields": ["score"],
                "acceptance_rules": [{"field": "score", "operator": ">=", "value": 10}],
            }
        ],
    }
    evidence = [
        {
            "gate_id": "gate_a",
            "candidate_id": "candidate",
            "sample_id": "sample_001",
            "field": "score",
            "value": "11",
        }
    ]
    audit = audit_project(invalid_but_measured_project, evidence)
    assert audit["project_config_valid"] is False
    assert audit["project_validation_error_count"] == 1
    assert audit["claim_ready"] is False
    assert audit["status"] == "claim_blocked"
    assert all(gate["status"] == "passed" for gate in audit["gates"])
    assert audit["next_actions"][0]["action_id"] == "fix_project_config_diagnostics"


def assert_cli_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "pass"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "audit",
                "--config",
                str(PROJECT_PATH),
                "--evidence",
                str(PASS_EVIDENCE),
                "--out-dir",
                str(out_dir),
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        audit = json.loads((out_dir / "claim_audit.json").read_text(encoding="utf-8"))
        assert audit["claim_ready"] is True
        assert (out_dir / "claim_audit.md").exists()
        assert (out_dir / "audit_review.json").exists()
        assert (out_dir / "audit_review.md").exists()
        assert (out_dir / "claim_summary.json").exists()
        assert (out_dir / "next_actions.json").exists()
        assert (out_dir / "dashboard.html").exists()
        review = json.loads((out_dir / "audit_review.json").read_text(encoding="utf-8"))
        assert review["status"] == "review_ready"
        assert review["decision"] == "ready_for_human_release_review"
        assert review["blocking_stage"] == "ready_for_human_review"
        assert "Falsiflow Audit Review" in (out_dir / "audit_review.md").read_text(encoding="utf-8")
        summary = json.loads((out_dir / "claim_summary.json").read_text(encoding="utf-8"))
        assert summary["claim_ready"] is True
        assert summary["completion_pct"] == 100.0
        assert summary["evidence_error_count"] == 0
        assert summary["evidence_warning_count"] == 0
        assert "Falsiflow Claim Dashboard" in (out_dir / "dashboard.html").read_text(encoding="utf-8")

        blocked_dir = Path(tmp) / "blocked"
        blocked = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "audit",
                "--config",
                str(PROJECT_PATH),
                "--evidence",
                str(PLACEHOLDER_EVIDENCE),
                "--out-dir",
                str(blocked_dir),
                "--strict",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert blocked.returncode == 2
        blocked_audit = json.loads((blocked_dir / "claim_audit.json").read_text(encoding="utf-8"))
        assert blocked_audit["claim_ready"] is False
        blocked_review = json.loads((blocked_dir / "audit_review.json").read_text(encoding="utf-8"))
        assert blocked_review["status"] == "review_blocked"
        assert blocked_review["decision"] == "blocked_before_release"
        assert blocked_review["blocking_stage"] == "gate_evidence"
        assert blocked_review["top_blockers"]

        missing_evidence = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "audit",
                "--config",
                str(PROJECT_PATH),
                "--evidence",
                str(Path(tmp) / "does_not_exist.csv"),
                "--out-dir",
                str(Path(tmp) / "missing"),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert missing_evidence.returncode != 0
        assert "Evidence file does not exist" in missing_evidence.stderr

        header_error_project = {
            "project": {"id": "header_error_cli"},
            "claim": {"id": "claim", "requires_gates": ["gate_a"]},
            "evidence_policy": {
                "require_source_files": False,
                "required_metadata_fields": [],
            },
            "gates": [
                {
                    "id": "gate_a",
                    "samples": [{"candidate_id": "candidate", "sample_id": "sample_001"}],
                    "required_fields": ["score"],
                    "acceptance_rules": [{"field": "score", "operator": ">=", "value": 10}],
                }
            ],
        }
        header_error_config = Path(tmp) / "header_error_project.json"
        header_error_config.write_text(json.dumps(header_error_project), encoding="utf-8")
        header_error_evidence = Path(tmp) / "header_error_evidence.csv"
        header_error_evidence.write_text(
            "\n".join([
                "gate_id,candidate_id,sample_id,field,value,value",
                "gate_a,candidate,sample_001,score,11,11",
            ]),
            encoding="utf-8",
        )
        header_error_dir = Path(tmp) / "header_error"
        header_error = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "audit",
                "--config",
                str(header_error_config),
                "--evidence",
                str(header_error_evidence),
                "--out-dir",
                str(header_error_dir),
                "--strict",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert header_error.returncode == 2
        header_error_summary = json.loads((header_error_dir / "claim_summary.json").read_text(encoding="utf-8"))
        assert header_error_summary["claim_ready"] is False
        assert header_error_summary["evidence_error_count"] == 1

        invalid_config_project = {
            "project": {"id": "invalid_config_cli"},
            "claim": {"id": "claim", "requires_gates": ["gate_a"]},
            "evidence_policy": {
                "require_source_files": False,
                "required_metadata_fields": [],
            },
            "gates": [
                {
                    "id": "gate_a",
                    "samples": [
                        {"candidate_id": "candidate", "sample_id": "sample_001"},
                        {"candidate_id": "candidate", "sample_id": "sample_001"},
                    ],
                    "required_fields": ["score"],
                    "acceptance_rules": [{"field": "score", "operator": ">=", "value": 10}],
                }
            ],
        }
        invalid_config_path = Path(tmp) / "invalid_config_project.json"
        invalid_config_path.write_text(json.dumps(invalid_config_project), encoding="utf-8")
        invalid_config_evidence = Path(tmp) / "invalid_config_evidence.csv"
        invalid_config_evidence.write_text(
            "\n".join([
                "gate_id,candidate_id,sample_id,field,value,source_file,measured_at,operator_or_agent,instrument_id,notes",
                "gate_a,candidate,sample_001,score,11,,,,,",
            ]),
            encoding="utf-8",
        )
        invalid_config_dir = Path(tmp) / "invalid_config"
        invalid_config = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "audit",
                "--config",
                str(invalid_config_path),
                "--evidence",
                str(invalid_config_evidence),
                "--out-dir",
                str(invalid_config_dir),
                "--strict",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert invalid_config.returncode == 2
        invalid_config_summary = json.loads((invalid_config_dir / "claim_summary.json").read_text(encoding="utf-8"))
        assert invalid_config_summary["claim_ready"] is False
        assert invalid_config_summary["project_validation_error_count"] == 1

        portfolio_dir = Path(tmp) / "portfolio"
        portfolio = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "portfolio",
                "--input",
                str(out_dir),
                "--input",
                str(blocked_dir),
                "--out-dir",
                str(portfolio_dir),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "Falsiflow portfolio: portfolio_blocked" in portfolio.stdout
        portfolio_summary = json.loads((portfolio_dir / "portfolio_summary.json").read_text(encoding="utf-8"))
        assert portfolio_summary["claim_count"] == 2
        assert portfolio_summary["ready_count"] == 1
        assert portfolio_summary["blocked_count"] == 1
        assert portfolio_summary["project_validation_error_count"] == 0
        assert portfolio_summary["project_validation_warning_count"] == 0
        assert portfolio_summary["evidence_error_count"] == 0
        assert portfolio_summary["evidence_warning_count"] == 0
        assert (portfolio_dir / "portfolio_dashboard.html").exists()

        validation_out = Path(tmp) / "validation.json"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "validate",
                "--config",
                str(PROJECT_PATH),
                "--out",
                str(validation_out),
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        validation = json.loads(validation_out.read_text(encoding="utf-8"))
        assert validation["valid"] is True

        templates = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "templates",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        records = json.loads(templates.stdout)
        template_ids = {record["template"] for record in records}
        assert EXPECTED_TEMPLATE_IDS <= template_ids
        assert all(record["status"] == "valid" for record in records)

        template_gallery_out = Path(tmp) / "template_gallery.md"
        template_gallery_json = Path(tmp) / "template_gallery.json"
        template_gallery = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-gallery",
                "--out",
                str(template_gallery_out),
                "--json-out",
                str(template_gallery_json),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_gallery_summary = json.loads(template_gallery.stdout)
        assert template_gallery_summary["status"] == "template_gallery_ready"
        assert template_gallery_summary["template_count"] == EXPECTED_TEMPLATE_COUNT
        assert template_gallery_summary["valid_template_count"] == EXPECTED_TEMPLATE_COUNT
        assert template_gallery_summary["non_neural_template_count"] == EXPECTED_NON_NEURAL_TEMPLATE_COUNT
        gallery_ids = {template["template"] for template in template_gallery_summary["templates"]}
        assert EXPECTED_TEMPLATE_IDS <= gallery_ids
        assert all(any("doctor --project-dir" in command for command in template["first_commands"]) for template in template_gallery_summary["templates"])
        assert template_gallery_json.exists()
        assert "Falsiflow Template Gallery" in template_gallery_out.read_text(encoding="utf-8")

        casebook_dir = Path(tmp) / "casebook_check"
        casebook_check = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "casebook-check",
                "--out-dir",
                str(casebook_dir),
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        casebook_summary = json.loads(casebook_check.stdout)
        assert casebook_summary["status"] == "casebook_check_ready"
        assert casebook_summary["template_count"] == EXPECTED_TEMPLATE_COUNT
        assert casebook_summary["positive_demo_ready_count"] == EXPECTED_TEMPLATE_COUNT
        assert casebook_summary["blocked_path_count"] == EXPECTED_TEMPLATE_COUNT
        assert casebook_summary["bundle_verified_count"] == EXPECTED_TEMPLATE_COUNT
        assert len(casebook_summary["reviewer_replay"]) == EXPECTED_TEMPLATE_COUNT
        assert any(entry["template"] == "biointerface_coatings" for entry in casebook_summary["reviewer_replay"])
        assert any(entry["template"] == "ai_claim_evaluation" for entry in casebook_summary["reviewer_replay"])
        assert all(entry["expected_placeholder_status"] == "claim_check_blocked" for entry in casebook_summary["reviewer_replay"])
        assert all(template["placeholder_blocks_claim"] is True for template in casebook_summary["templates"])
        assert (casebook_dir / "casebook_check.json").exists()
        assert (casebook_dir / "casebook_reviewer_replay.md").exists()
        assert (casebook_dir / "casebook_reviewer_replay.sh").exists()
        assert (casebook_dir / "casebook_reviewer_replay.ps1").exists()
        assert os.access(casebook_dir / "casebook_reviewer_replay.sh", os.X_OK)
        casebook_report = (casebook_dir / "casebook_check.md").read_text(encoding="utf-8")
        assert "Falsiflow Casebook Check" in casebook_report
        assert "Reviewer Replay" in casebook_report
        replay_markdown = (casebook_dir / "casebook_reviewer_replay.md").read_text(encoding="utf-8")
        replay_shell = (casebook_dir / "casebook_reviewer_replay.sh").read_text(encoding="utf-8")
        replay_powershell = (casebook_dir / "casebook_reviewer_replay.ps1").read_text(encoding="utf-8")
        assert "Falsiflow Casebook Reviewer Replay" in replay_markdown
        assert "positive demos finish as `claim_check_ready`" in replay_markdown
        assert "claim_check_blocked" in replay_markdown
        assert "evidence_placeholder_demo.csv" in replay_shell
        assert "assert_status" in replay_shell
        assert "casebook-check" in replay_shell
        assert "evidence_placeholder_demo.csv" in replay_powershell
        assert "Assert-Status" in replay_powershell

        for record in records:
            template_dir = Path(record["path"])
            demo_evidence = template_dir / "evidence_pass_demo.csv"
            if not demo_evidence.exists():
                continue
            demo_dir = Path(tmp) / f"template_{record['template']}"
            subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "audit",
                    "--config",
                    record["project_config"],
                    "--evidence",
                    str(demo_evidence),
                    "--out-dir",
                    str(demo_dir),
                    "--strict",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            demo_audit = json.loads((demo_dir / "claim_audit.json").read_text(encoding="utf-8"))
            assert demo_audit["claim_ready"] is True

        schema = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "schema",
                "--kind",
                "evidence-row",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        evidence_schema = json.loads(schema.stdout)
        assert evidence_schema["title"] == "Falsiflow evidence row"

        schema_out = Path(tmp) / "schemas.json"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "schema",
                "--kind",
                "all",
                "--out",
                str(schema_out),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        schemas = json.loads(schema_out.read_text(encoding="utf-8"))
        assert "audit-review" in schemas
        assert "portfolio-summary" in schemas
        assert "import-coverage" in schemas
        assert "source-manifest" in schemas
        assert "bundle-manifest" in schemas
        assert "bundle-verification" in schemas
        assert "claim-check" in schemas
        assert "quickstart-summary" in schemas
        assert "doctor-summary" in schemas
        assert "demo-summary" in schemas
        assert "template-check" in schemas
        assert "template-pack-manifest" in schemas
        assert "template-pack-verification" in schemas
        assert "template-install" in schemas
        assert "template-registry" in schemas
        assert "template-lock" in schemas
        assert "template-attestation" in schemas
        assert "template-attestation-verification" in schemas
        assert "template-policy" in schemas
        assert "template-policy-verification" in schemas
        assert "template-release" in schemas
        assert "template-release-verification" in schemas
        assert "template-gallery" in schemas
        assert "adoption-check" in schemas
        assert "release-check" in schemas

        source_manifest_out = Path(tmp) / "source_manifest.json"
        source_report_out = Path(tmp) / "source_manifest.md"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "sources",
                "--config",
                str(PROJECT_PATH),
                "--evidence",
                str(PASS_EVIDENCE),
                "--out",
                str(source_manifest_out),
                "--report-out",
                str(source_report_out),
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        source_manifest = json.loads(source_manifest_out.read_text(encoding="utf-8"))
        assert source_manifest["status"] == "sources_ready"
        assert source_manifest["referenced_source_file_count"] == 1
        assert source_manifest["present_source_file_count"] == 1
        assert source_manifest["blocker_count"] == 0
        assert "Falsiflow Source Manifest" in source_report_out.read_text(encoding="utf-8")

        missing_source_evidence = Path(tmp) / "missing_source.csv"
        missing_source_evidence.write_text(
            PASS_EVIDENCE.read_text(encoding="utf-8").replace(
                "source_files/demo_raw_export.csv",
                "source_files/missing_raw_export.csv",
            ),
            encoding="utf-8",
        )
        missing_source_out = Path(tmp) / "missing_source_manifest.json"
        missing_source = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "sources",
                "--config",
                str(PROJECT_PATH),
                "--evidence",
                str(missing_source_evidence),
                "--out",
                str(missing_source_out),
                "--strict",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert missing_source.returncode == 2
        missing_source_manifest = json.loads(missing_source_out.read_text(encoding="utf-8"))
        assert missing_source_manifest["status"] == "sources_blocked"
        assert missing_source_manifest["missing_source_file_count"] == 1

        bundle_dir = Path(tmp) / "bundle"
        bundle_zip = Path(tmp) / "bundle.zip"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "bundle",
                "--config",
                str(PROJECT_PATH),
                "--evidence",
                str(PASS_EVIDENCE),
                "--out-dir",
                str(bundle_dir),
                "--zip-out",
                str(bundle_zip),
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        bundle_manifest = json.loads((bundle_dir / "bundle_manifest.json").read_text(encoding="utf-8"))
        assert bundle_manifest["status"] == "bundle_ready"
        assert bundle_manifest["claim_ready"] is True
        assert bundle_manifest["source_status"] == "sources_ready"
        assert bundle_manifest["source_file_count"] == 1
        artifact_roles = {artifact["role"] for artifact in bundle_manifest["artifacts"]}
        assert {"project_config", "evidence_csv", "claim_audit", "audit_review", "audit_review_report", "source_manifest", "source_file"} <= artifact_roles
        assert (bundle_dir / "sources" / "source_files" / "demo_raw_export.csv").exists()
        assert bundle_zip.exists()

        bundle_verify_out = Path(tmp) / "bundle_verify.json"
        bundle_verify_report = Path(tmp) / "bundle_verify.md"
        bundle_verify = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify-bundle",
                "--bundle-dir",
                str(bundle_dir),
                "--out",
                str(bundle_verify_out),
                "--report-out",
                str(bundle_verify_report),
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "Falsiflow verify-bundle: bundle_verified" in bundle_verify.stdout
        bundle_verification = json.loads(bundle_verify_out.read_text(encoding="utf-8"))
        assert bundle_verification["status"] == "bundle_verified"
        assert bundle_verification["integrity_status"] == "integrity_verified"
        assert bundle_verification["input_format"] == "directory"
        assert bundle_verification["hash_mismatch_count"] == 0
        assert "No issues found." in bundle_verify_report.read_text(encoding="utf-8")

        zip_bundle_verify_out = Path(tmp) / "zip_bundle_verify.json"
        zip_bundle_verify_report = Path(tmp) / "zip_bundle_verify.md"
        zip_bundle_verify = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify-bundle",
                "--zip",
                str(bundle_zip),
                "--out",
                str(zip_bundle_verify_out),
                "--report-out",
                str(zip_bundle_verify_report),
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "Falsiflow verify-bundle: bundle_verified" in zip_bundle_verify.stdout
        zip_bundle_verification = json.loads(zip_bundle_verify_out.read_text(encoding="utf-8"))
        assert zip_bundle_verification["status"] == "bundle_verified"
        assert zip_bundle_verification["input_format"] == "zip"
        assert zip_bundle_verification["zip_member_count"] >= bundle_manifest["artifact_count"]
        assert "Falsiflow Bundle Verification" in zip_bundle_verify_report.read_text(encoding="utf-8")

        claim_check_dir = Path(tmp) / "claim_check"
        claim_check = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "claim-check",
                "--config",
                str(PROJECT_PATH),
                "--evidence",
                str(PASS_EVIDENCE),
                "--out-dir",
                str(claim_check_dir),
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        claim_check_summary = json.loads(claim_check.stdout)
        assert claim_check_summary["status"] == "claim_check_ready"
        assert claim_check_summary["claim_check_ready"] is True
        assert claim_check_summary["audit_review_status"] == "review_ready"
        assert claim_check_summary["source_status"] == "sources_ready"
        assert claim_check_summary["bundle_status"] == "bundle_ready"
        assert claim_check_summary["verification_status"] == "bundle_verified"
        assert any(artifact["artifact"] == "Source manifest" for artifact in claim_check_summary["review_artifact_index"])
        assert any(artifact["artifact"] == "Bundle verification" for artifact in claim_check_summary["review_artifact_index"])
        assert (claim_check_dir / "claim_check.json").exists()
        assert (claim_check_dir / "claim_check.md").exists()
        assert (claim_check_dir / "evidence_bundle.zip").exists()
        claim_check_report = (claim_check_dir / "claim_check.md").read_text(encoding="utf-8")
        assert "Falsiflow Claim Check" in claim_check_report
        assert "Review Artifact Index" in claim_check_report
        assert "evidence_bundle/source_manifest.md" in claim_check_report
        assert "evidence_bundle_verify.md" in claim_check_report
        bundle_verification_report = (claim_check_dir / "evidence_bundle_verify.md").read_text(encoding="utf-8")
        assert "Review Artifact Index" in bundle_verification_report
        assert "source_manifest.md" in bundle_verification_report

        blocked_claim_check_dir = Path(tmp) / "blocked_claim_check"
        blocked_claim_check = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "claim-check",
                "--config",
                str(PROJECT_PATH),
                "--evidence",
                str(PLACEHOLDER_EVIDENCE),
                "--out-dir",
                str(blocked_claim_check_dir),
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert blocked_claim_check.returncode == 2
        blocked_claim_check_summary = json.loads(blocked_claim_check.stdout)
        assert blocked_claim_check_summary["status"] == "claim_check_blocked"
        assert blocked_claim_check_summary["audit_review_status"] == "review_blocked"
        assert blocked_claim_check_summary["blocking_stage"] == "gate_evidence"

        shortcut_project_dir = Path(tmp) / "shortcut_project"
        shutil.copytree(EXAMPLE_TEMPLATE_ROOT / "biointerface_coatings", shortcut_project_dir)
        shortcut_claim_check = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "claim-check",
                "--project-dir",
                str(shortcut_project_dir),
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        shortcut_claim_check_summary = json.loads(shortcut_claim_check.stdout)
        assert shortcut_claim_check_summary["status"] == "claim_check_ready"
        assert shortcut_claim_check_summary["verification_status"] == "bundle_verified"
        assert (shortcut_project_dir / "claim_check" / "claim_check.json").exists()
        assert (shortcut_project_dir / "claim_check" / "evidence_bundle.zip").exists()

        quickstart_project_dir = Path(tmp) / "quickstart_project"
        quickstart = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "quickstart",
                "--template",
                "biointerface_coatings",
                "--out",
                str(quickstart_project_dir),
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        quickstart_summary = json.loads(quickstart.stdout)
        assert quickstart_summary["status"] == "quickstart_ready"
        assert quickstart_summary["claim_check_status"] == "claim_check_ready"
        assert quickstart_summary["verification_status"] == "bundle_verified"
        assert quickstart_summary["next_commands"][0].startswith("falsiflow doctor --project-dir")
        assert (quickstart_project_dir / "project.json").exists()
        assert (quickstart_project_dir / "quickstart_summary.json").exists()
        quickstart_report = (quickstart_project_dir / "quickstart_summary.md").read_text(encoding="utf-8")
        assert "Falsiflow Quickstart" in quickstart_report
        assert "Next Commands" in quickstart_report

        try_dir = Path(tmp) / "try_demo"
        try_demo = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "try",
                "--template",
                "biointerface_coatings",
                "--out-dir",
                str(try_dir),
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        try_summary = json.loads(try_demo.stdout)
        assert try_summary["status"] == "try_ready"
        assert try_summary["quickstart_status"] == "quickstart_ready"
        assert try_summary["claim_check_status"] == "claim_check_ready"
        assert try_summary["verification_status"] == "bundle_verified"
        assert try_summary["outputs"]["launchpad"].endswith("index.html")
        assert try_summary["outputs"]["try_report"].endswith("try_report.html")
        assert try_summary["outputs"]["dashboard"].endswith("dashboard.html")
        assert try_summary["outputs"]["wizard"].endswith("falsiflow_wizard.html")
        assert try_summary["next_commands"][-1].startswith("open ")
        assert (try_dir / "try_summary.json").exists()
        assert (try_dir / "index.html").exists()
        assert (try_dir / "try_report.html").exists()
        assert (try_dir / "falsiflow_wizard.html").exists()
        assert (try_dir / "project" / "claim_check" / "claim_check.json").exists()
        launchpad = (try_dir / "index.html").read_text(encoding="utf-8")
        assert "Falsiflow Launchpad" in launchpad
        assert "CI gates for claims before they ship" in launchpad
        assert "Live Downstream PR Story" in launchpad
        assert 'property="og:title"' in launchpad
        assert 'name="twitter:card"' in launchpad
        assert "falsiflow_downstream_pr_proof_strip.svg" in launchpad
        assert "falsiflow_live_pr_story_reel.svg" in launchpad
        assert "Falsiflow: unverifiable AI, RAG, and product claims should fail CI" in launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1" in launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990" in launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112" in launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1" in launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721829145" in launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721856616" in launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1" in launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726360229" in launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726392921" in launchpad
        assert "https://github.com/AzurLiu/falsiflow/pull/17" in launchpad
        assert "https://github.com/AzurLiu/falsiflow/actions/runs/26708459093" in launchpad
        assert "https://github.com/AzurLiu/falsiflow/actions/runs/26708472653" in launchpad
        assert "Ready Or Blocked" in launchpad
        assert "claim_check_blocked" in launchpad
        assert "Claims This Demo Targets" in launchpad
        assert "See the example result" in launchpad
        assert "Make your own checklist" in launchpad
        assert "Advanced CLI Handoff" in launchpad
        assert 'href="workbench.html"' in launchpad
        assert "Open report" in launchpad
        assert "Open wizard" in launchpad
        try_report = (try_dir / "try_report.html").read_text(encoding="utf-8")
        assert "Falsiflow Try" in try_report
        assert "Launchpad" in try_report
        assert "Claim dashboard" in try_report
        assert "Start your own project" in try_report
        assert "bundle_verified" in try_report

        serve = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "serve",
                "--out-dir",
                str(try_dir),
                "--port",
                "0",
                "--check",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        serve_summary = json.loads(serve.stdout)
        assert serve_summary["status"] == "serve_ready"
        assert serve_summary["check_status"] == "http_ready"
        assert serve_summary["status_code"] == 200
        assert serve_summary["url"].startswith("http://127.0.0.1:")
        assert serve_summary["url"].endswith("/index.html")
        assert serve_summary["try_report_url"].endswith("/try_report.html")
        assert serve_summary["wizard_url"].endswith("/falsiflow_wizard.html")
        assert serve_summary["launchpad"].endswith("index.html")
        assert serve_summary["try_report"].endswith("try_report.html")
        assert (try_dir / "serve_summary.json").exists()

        start_dir = Path(tmp) / "start_app"
        start = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "start",
                "--out-dir",
                str(start_dir),
                "--check",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        start_summary = json.loads(start.stdout)
        assert start_summary["status"] == "serve_ready"
        assert start_summary["entry_command"] == "start"
        assert start_summary["check_status"] == "http_ready"
        assert start_summary["status_code"] == 200
        assert start_summary["url"].startswith("http://127.0.0.1:")
        assert start_summary["url"].endswith("/index.html")
        assert start_summary["workbench_url"].endswith("/workbench.html")
        assert start_summary["next_commands"][1].startswith("falsiflow start")
        assert (start_dir / "index.html").exists()
        assert (start_dir / "workbench.html").exists()
        assert (start_dir / "serve_summary.json").exists()
        workbench_html = (start_dir / "workbench.html").read_text(encoding="utf-8")
        assert "Review Flow" in workbench_html
        assert "Evidence Lineage" in workbench_html
        assert "Repair Checklist" in workbench_html
        assert "/api/workbench/state" in workbench_html
        workbench_summary = run_workbench_check(start_dir, {"template": "biointerface_coatings", "project_json": "", "evidence_csv": "", "source_files": []})
        assert workbench_summary["status"] == "workbench_ready"
        assert workbench_summary["claim_check_status"] == "claim_check_ready"
        assert workbench_summary["source_status"] == "sources_ready"
        assert workbench_summary["claim_ready"] is True
        assert workbench_summary["links"]["dashboard"].endswith("dashboard.html")
        assert workbench_summary["links"]["source_manifest_report"].endswith("source_manifest.md")
        assert workbench_summary["links"]["bundle_verification_report"].endswith("evidence_bundle_verify.md")
        assert len(workbench_summary["review_flow"]) >= 7
        assert workbench_summary["review_flow"][-1]["stage"] == "Human handoff"
        assert workbench_summary["evidence_lineage"]["present_source_file_count"] >= 1
        assert workbench_summary["evidence_lineage"]["checked_artifact_count"] >= 1
        assert any(artifact["label"] == "Source manifest" for artifact in workbench_summary["review_artifacts"])
        assert workbench_summary["repair_checklist"][0]["command"].startswith("falsiflow claim-check")
        assert (start_dir / "workbench_summary.json").exists()

        install_dir = Path(tmp) / "installer_home"
        installer = subprocess.run(
            [
                str(ROOT / "scripts" / "install_local.sh"),
                "--from-local",
                str(ROOT),
                "--prefix",
                str(install_dir),
                "--check",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        installer_json_start = installer.stdout.find("{")
        assert installer_json_start >= 0
        installer_summary = json.loads(installer.stdout[installer_json_start:])
        assert installer_summary["status"] == "serve_ready"
        assert installer_summary["entry_command"] == "start"
        assert installer_summary["check_status"] == "http_ready"
        assert (install_dir / "venv" / "bin" / "falsiflow").exists()
        assert (install_dir / "source" / "pyproject.toml").exists()
        assert (install_dir / "app" / "index.html").exists()
        powershell_installer = (ROOT / "scripts" / "install_local.ps1").read_text(encoding="utf-8")
        assert "FALSIFLOW_REPO_URL" in powershell_installer
        assert "python -m venv" in powershell_installer
        assert "falsiflow.exe" in powershell_installer

        onboard_dir = Path(tmp) / "onboard_app"
        onboard = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "onboard",
                "--out-dir",
                str(onboard_dir),
                "--check",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        onboard_summary = json.loads(onboard.stdout)
        assert onboard_summary["status"] == "onboard_ready"
        assert onboard_summary["start_status"] == "serve_ready"
        assert onboard_summary["local_only"] is True
        assert onboard_summary["steps"][0]["title"] == "Open the local app"
        assert onboard_summary["next_commands"][0].startswith("falsiflow start")
        assert (onboard_dir / "onboard_summary.json").exists()

        static_demo_dir = Path(tmp) / "static_demo"
        static_demo = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "static-demo",
                "--out-dir",
                str(static_demo_dir),
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        static_demo_summary = json.loads(static_demo.stdout)
        assert static_demo_summary["status"] == "static_demo_ready"
        assert static_demo_summary["publishable"] is True
        assert static_demo_summary["index"].endswith("index.html")
        assert (static_demo_dir / "index.html").exists()
        assert (static_demo_dir / "try_report.html").exists()
        assert (static_demo_dir / "falsiflow_wizard.html").exists()
        assert (static_demo_dir / "static_demo_summary.json").exists()

        demo_package_dir = Path(tmp) / "public_demo"
        demo_package = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "demo-package",
                "--out-dir",
                str(demo_package_dir),
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        demo_package_summary = json.loads(demo_package.stdout)
        assert demo_package_summary["status"] == "demo_package_ready"
        assert demo_package_summary["publishable"] is True
        assert demo_package_summary["external_url_required"] is True
        assert (demo_package_dir / "demo_package_summary.json").exists()
        assert (demo_package_dir / "static_demo_summary.json").exists()
        assert (demo_package_dir / ".nojekyll").exists()
        assert (demo_package_dir / "netlify.toml").exists()
        assert (demo_package_dir / "publish_checklist.md").exists()
        demo_package_readme = (demo_package_dir / "README.md").read_text(encoding="utf-8")
        assert "live downstream PR story" in demo_package_readme
        assert "PR #1 in the downstream AI eval demo" in demo_package_readme

        publish_kit_dir = Path(tmp) / "publish_kit"
        publish_kit = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "publish-kit",
                "--out-dir",
                str(publish_kit_dir),
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        publish_kit_summary = json.loads(publish_kit.stdout)
        assert publish_kit_summary["status"] == "publish_kit_ready"
        assert publish_kit_summary["account_action_required"] is True
        assert publish_kit_summary["public_release_evidence_status"] == "public_release_evidence_ready"
        assert publish_kit_summary["release_rehearsal_status"] == "release_rehearsal_ready"
        assert (publish_kit_dir / "publish_handoff.json").exists()
        assert (publish_kit_dir / "publish_handoff.md").exists()
        assert (publish_kit_dir / "publish.env.example").exists()
        assert (publish_kit_dir / "github_publish_commands.sh").exists()
        publish_commands = (publish_kit_dir / "github_publish_commands.sh").read_text(encoding="utf-8")
        assert "Falsiflow External Evidence" in publish_commands
        assert "FALSIFLOW_EXPECTED_VERSION" in publish_commands
        assert "gh run watch" in publish_commands
        assert publish_commands.index("gh release create") < publish_commands.index("Falsiflow External Evidence")
        assert (publish_kit_dir / "external_evidence_template.json").exists()
        assert (publish_kit_dir / "public_release_evidence.json").exists()
        assert (publish_kit_dir / "public_release_evidence.md").exists()
        release_evidence = json.loads((publish_kit_dir / "public_release_evidence.json").read_text(encoding="utf-8"))
        assert release_evidence["status"] == "public_release_evidence_ready"
        assert {"public_package_pipx_smoke", "scorecard_workflow", "launch_metrics"} <= {item["id"] for item in release_evidence["evidence"]}
        release_evidence_report = (publish_kit_dir / "public_release_evidence.md").read_text(encoding="utf-8")
        assert "Falsiflow Public Release Evidence Ledger" in release_evidence_report
        assert "external-check --strict" in release_evidence_report
        assert (publish_kit_dir / "release_rehearsal.json").exists()
        assert (publish_kit_dir / "release_rehearsal.md").exists()
        release_rehearsal = json.loads((publish_kit_dir / "release_rehearsal.json").read_text(encoding="utf-8"))
        assert release_rehearsal["status"] == "release_rehearsal_ready"
        rehearsal_step_ids = [step["id"] for step in release_rehearsal["steps"]]
        assert {"github_release", "pypi_publish", "external_workflow", "external_check_strict", "public_announcement"} <= set(rehearsal_step_ids)
        assert rehearsal_step_ids.index("github_release") < rehearsal_step_ids.index("pypi_publish") < rehearsal_step_ids.index("external_workflow") < rehearsal_step_ids.index("external_check_strict")
        release_rehearsal_report = (publish_kit_dir / "release_rehearsal.md").read_text(encoding="utf-8")
        assert "Falsiflow Public Release Rehearsal" in release_rehearsal_report
        assert "external-check --strict" in release_rehearsal_report
        assert "public_release_evidence.md" in release_rehearsal_report
        assert (publish_kit_dir / "public_demo" / "demo_package_summary.json").exists()

        launch_kit_dir = Path(tmp) / "launch_kit"
        launch_kit = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "launch-kit",
                "--out-dir",
                str(launch_kit_dir),
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        launch_kit_summary = json.loads(launch_kit.stdout)
        assert launch_kit_summary["status"] == "launch_kit_ready"
        assert launch_kit_summary["account_action_required"] is True
        assert launch_kit_summary["launch_metrics_status"] == "launch_metrics_ready"
        assert launch_kit_summary["release_rehearsal_status"] == "release_rehearsal_ready"
        assert (launch_kit_dir / "launch_summary.json").exists()
        assert (launch_kit_dir / "proof_card.md").exists()
        assert (launch_kit_dir / "announcement.md").exists()
        announcement = (launch_kit_dir / "announcement.md").read_text(encoding="utf-8")
        assert "Falsiflow is a CI gate for claims" in announcement
        assert "falsiflow_demo_pr_playbook.md" in announcement
        assert "claim_check_blocked" in announcement
        assert "claim_check_ready" in announcement
        assert announcement.count("```") % 2 == 0
        assert (launch_kit_dir / "demo_script.md").exists()
        demo_script = (launch_kit_dir / "demo_script.md").read_text(encoding="utf-8")
        assert "## 2:15 Demo PR" in demo_script
        assert "evidence_placeholder_demo.csv" in demo_script
        assert "evidence_pass_demo.csv" in demo_script
        assert demo_script.count("```") % 2 == 0
        assert (launch_kit_dir / "readme_proof_strip.svg").exists()
        assert "claim_ready after proof" in (launch_kit_dir / "readme_proof_strip.svg").read_text(encoding="utf-8")
        assert (launch_kit_dir / "social_preview.svg").exists()
        assert "Falsiflow GitHub social preview" in (launch_kit_dir / "social_preview.svg").read_text(encoding="utf-8")
        social_preview_png = launch_kit_dir / "social_preview.png"
        assert social_preview_png.exists()
        assert social_preview_png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert social_preview_png.stat().st_size > 1000
        assert (launch_kit_dir / "github_repo_profile.md").exists()
        github_repo_profile = (launch_kit_dir / "github_repo_profile.md").read_text(encoding="utf-8")
        assert "## Topics" in github_repo_profile
        assert "Demo PR playbook" in github_repo_profile
        assert "Upload `social_preview.png`" in github_repo_profile
        assert "Live AI eval downstream PR proof" in github_repo_profile
        assert "Live RAG eval downstream PR proof" in github_repo_profile
        assert "Live product metric downstream PR proof" in github_repo_profile
        assert "falsiflow-downstream-rag-eval-demo" in github_repo_profile
        assert "26721829145" in github_repo_profile
        assert "26721856616" in github_repo_profile
        assert "falsiflow-downstream-product-metric-demo" in github_repo_profile
        assert "26726360229" in github_repo_profile
        assert "26726392921" in github_repo_profile
        assert (launch_kit_dir / "launch_posts.md").exists()
        launch_posts = (launch_kit_dir / "launch_posts.md").read_text(encoding="utf-8")
        assert "Show HN" in launch_posts
        assert "unverifiable AI eval claims" in launch_posts
        assert "falsiflow-downstream-ai-eval-demo" in launch_posts
        assert "26711652990" in launch_posts
        assert "26711669112" in launch_posts
        assert "falsiflow-downstream-rag-eval-demo" in launch_posts
        assert "26721829145" in launch_posts
        assert "26721856616" in launch_posts
        assert "falsiflow-downstream-product-metric-demo" in launch_posts
        assert "26726360229" in launch_posts
        assert "26726392921" in launch_posts
        assert "AI eval downstream PR" in launch_posts
        assert "RAG eval downstream PR" in launch_posts
        assert "Product metric downstream PR" in launch_posts
        assert "Demo PR playbook" in launch_posts
        assert "Reply Bank" in launch_posts
        assert "Great Expectations" in launch_posts
        assert "GITHUB_ACTION_PATH" in launch_posts
        assert launch_posts.count("```") % 2 == 0
        assert (launch_kit_dir / "launch_metrics.json").exists()
        assert (launch_kit_dir / "launch_metrics.md").exists()
        launch_metrics = json.loads((launch_kit_dir / "launch_metrics.json").read_text(encoding="utf-8"))
        assert launch_metrics["status"] == "launch_metrics_ready"
        assert any(row["stage"] == "verification" for row in launch_metrics["funnel"])
        assert "demo PR replay" in json.dumps(launch_metrics)
        launch_metrics_report = (launch_kit_dir / "launch_metrics.md").read_text(encoding="utf-8")
        assert "Falsiflow 1k-Star Launch Tracker" in launch_metrics_report
        assert "GitHub traffic" in launch_metrics_report
        assert "day-14" in launch_metrics_report
        assert "quality-gates" in launch_kit_summary["github_topics"]
        assert (launch_kit_dir / "maintainer_checklist.md").exists()
        maintainer_checklist = (launch_kit_dir / "maintainer_checklist.md").read_text(encoding="utf-8")
        assert "Launch Metrics" in maintainer_checklist
        assert "falsiflow_demo_pr_playbook.md" in maintainer_checklist
        assert (launch_kit_dir / "publish_kit" / "publish_handoff.json").exists()
        assert (launch_kit_dir / "publish_kit" / "public_release_evidence.md").exists()
        assert (launch_kit_dir / "publish_kit" / "release_rehearsal.md").exists()

        external_check_dir = Path(tmp) / "external_check"
        external_check = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "external-check",
                "--out-dir",
                str(external_check_dir),
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        external_check_summary = json.loads(external_check.stdout)
        assert external_check_summary["status"] in {"external_ready", "external_blocked"}
        assert external_check_summary["check_count"] >= 8
        external_check_ids = {check["check"] for check in external_check_summary["checks"]}
        assert {"pypi_package_url", "pipx_public_package", "public_package_first_run", "public_package_claim_check", "mcp_public_package_selftest"} <= external_check_ids
        assert (external_check_dir / "external_readiness.json").exists()
        assert (external_check_dir / "external_readiness.md").exists()

        external_evidence_path = Path(tmp) / "external_evidence.json"
        external_evidence = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "external-evidence",
                "--out",
                str(external_evidence_path),
                "--repo-url",
                "https://github.com/AzurLiu/falsiflow",
                "--public-demo-url",
                "https://falsiflow-demo.netlify.app",
                "--pypi-package-url",
                "https://pypi.org/project/falsiflow/",
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        external_evidence_summary = json.loads(external_evidence.stdout)
        assert external_evidence_summary["status"] == "external_evidence_template_ready"
        evidence_doc = json.loads(external_evidence_path.read_text(encoding="utf-8"))
        assert "pypi_package_url" in evidence_doc["checks"]
        assert "pipx_public_package" in evidence_doc["checks"]
        assert "public_package_first_run" in evidence_doc["checks"]
        assert "public_package_claim_check" in evidence_doc["checks"]
        assert "mcp_public_package_selftest" in evidence_doc["checks"]
        assert evidence_doc["checks"]["pypi_package_url"]["verification_url"] == "https://pypi.org/pypi/falsiflow/json"
        assert evidence_doc["checks"]["pypi_package_url"]["artifact"] == "falsiflow_pypi_project.json"
        assert evidence_doc["checks"]["pypi_package_url"]["expected_version"] == FALSIFLOW_VERSION
        assert evidence_doc["checks"]["pypi_package_url"]["published_version"] == ""
        evidence_doc["checks"]["public_repo_url"]["status"] = "passed"
        evidence_doc["checks"]["public_repo_url"]["evidence_url"] = "https://github.com/AzurLiu/falsiflow"
        evidence_doc["checks"]["public_demo_url"]["status"] = "passed"
        evidence_doc["checks"]["public_demo_url"]["evidence_url"] = "https://falsiflow-demo.netlify.app"
        evidence_doc["checks"]["pypi_package_url"]["status"] = "passed"
        evidence_doc["checks"]["pypi_package_url"]["evidence_url"] = "https://pypi.org/project/falsiflow/"
        evidence_doc["checks"]["pypi_package_url"]["published_version"] = evidence_doc["checks"]["pypi_package_url"]["expected_version"]
        evidence_doc["checks"]["pipx_smoke"]["status"] = "passed"
        evidence_doc["checks"]["pipx_smoke"]["workflow_url"] = "https://github.com/AzurLiu/falsiflow/actions/runs/1"
        evidence_doc["checks"]["pipx_public_package"]["status"] = "passed"
        evidence_doc["checks"]["pipx_public_package"]["workflow_url"] = "https://github.com/AzurLiu/falsiflow/actions/runs/3"
        evidence_doc["checks"]["public_package_first_run"]["status"] = "passed"
        evidence_doc["checks"]["public_package_first_run"]["workflow_url"] = "https://github.com/AzurLiu/falsiflow/actions/runs/5"
        evidence_doc["checks"]["public_package_claim_check"]["status"] = "passed"
        evidence_doc["checks"]["public_package_claim_check"]["workflow_url"] = "https://github.com/AzurLiu/falsiflow/actions/runs/6"
        evidence_doc["checks"]["public_package_claim_check"]["claim_check_status"] = "claim_check_ready"
        evidence_doc["checks"]["public_package_claim_check"]["bundle_verification_status"] = "bundle_verified"
        evidence_doc["checks"]["mcp_public_package_selftest"]["status"] = "passed"
        evidence_doc["checks"]["mcp_public_package_selftest"]["workflow_url"] = "https://github.com/AzurLiu/falsiflow/actions/runs/4"
        evidence_doc["checks"]["windows_powershell"]["status"] = "passed"
        evidence_doc["checks"]["windows_powershell"]["workflow_url"] = "https://github.com/AzurLiu/falsiflow/actions/runs/2"
        external_evidence_path.write_text(json.dumps(evidence_doc, indent=2, sort_keys=True), encoding="utf-8")
        external_ready_dir = Path(tmp) / "external_ready"
        external_ready = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "external-check",
                "--out-dir",
                str(external_ready_dir),
                "--evidence",
                str(external_evidence_path),
                "--force",
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            env={**os.environ, "FALSIFLOW_REPO_URL": "https://github.com/AzurLiu/falsiflow", "FALSIFLOW_PYPI_PACKAGE_URL": "https://pypi.org/project/falsiflow/"},
            check=True,
            capture_output=True,
            text=True,
        )
        external_ready_summary = json.loads(external_ready.stdout)
        assert external_ready_summary["status"] == "external_ready"
        assert external_ready_summary["external_evidence_status"] == "loaded"
        ready_checks = {check["check"]: check for check in external_ready_summary["checks"]}
        assert ready_checks["pypi_package_url"]["status"] == "passed"
        assert ready_checks["pypi_version_match"]["status"] == "passed"
        assert ready_checks["pipx_public_package"]["status"] == "passed"
        assert ready_checks["public_package_first_run"]["status"] == "passed"
        assert ready_checks["public_package_claim_check"]["status"] == "passed"
        assert ready_checks["mcp_public_package_selftest"]["status"] == "passed"

        release_proof_path = Path(tmp) / "release_proof.md"
        release_proof = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "release-proof",
                "--evidence",
                str(external_evidence_path),
                "--readiness",
                str(external_ready_dir / "external_readiness.json"),
                "--out",
                str(release_proof_path),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        release_proof_summary = json.loads(release_proof.stdout)
        assert release_proof_summary["status"] == "external_proof_ready"
        assert release_proof_summary["external_evidence_run_url"] == "https://github.com/AzurLiu/falsiflow/actions/runs/6"
        release_proof_text = release_proof_path.read_text(encoding="utf-8")
        assert "External Evidence run" in release_proof_text
        assert "pypi_version_match=passed" in release_proof_text
        assert "public_package_claim_check=passed" in release_proof_text
        assert "claim_check_ready" in release_proof_text
        assert "bundle_verified" in release_proof_text
        assert "external_ready" in release_proof_text

        cli_reference_md = Path(tmp) / "cli_reference.md"
        cli_reference_json = Path(tmp) / "cli_reference.json"
        cli_reference = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "cli-reference",
                "--out",
                str(cli_reference_md),
                "--json-out",
                str(cli_reference_json),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        cli_reference_summary = json.loads(cli_reference.stdout)
        assert cli_reference_summary["status"] == "cli_reference_ready"
        commands = {record["command"] for record in cli_reference_summary["commands"]}
        assert {"start", "cli-reference", "release-check", "release-proof", "external-evidence", "casebook-check", "evidence import", "template-release"} <= commands
        assert cli_reference_summary["command_count"] >= 50
        assert cli_reference_md.exists()
        assert cli_reference_json.exists()
        cli_reference_text = cli_reference_md.read_text(encoding="utf-8")
        assert "Falsiflow CLI Reference" in cli_reference_text
        assert "falsiflow casebook-check" in cli_reference_text
        assert "--profile" in cli_reference_text
        assert "falsiflow evidence import" in cli_reference_text

        discovery_dir = Path(tmp) / "discovery"
        discovery_summary = run_discover("MEA neural interface material", discovery_dir, force=True)
        assert discovery_summary["status"] == "discovery_ready"
        assert discovery_summary["ai_used"] is False
        assert discovery_summary["claim_ready"] is False
        assert discovery_summary["top_candidate"]
        assert (discovery_dir / "evidence_records.json").exists()
        assert (discovery_dir / "candidate_queue.json").exists()
        assert (discovery_dir / "ranking.md").exists()
        assert (discovery_dir / "assay_plan.md").exists()
        assert (discovery_dir / "rfq_package.md").exists()
        assert (discovery_dir / "project_draft" / "project.json").exists()
        assert (discovery_dir / "project_draft" / "evidence_template.csv").exists()
        discovery_doctor = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "doctor",
                "--config",
                str(discovery_dir / "project_draft" / "project.json"),
                "--evidence",
                str(discovery_dir / "project_draft" / "evidence_template.csv"),
                "--out-dir",
                str(discovery_dir / "project_draft" / "doctor"),
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert discovery_doctor.returncode == 2
        discovery_doctor_summary = json.loads(discovery_doctor.stdout)
        assert discovery_doctor_summary["claim_ready"] is False

        agent_discovery_dir = Path(tmp) / "agent_discovery"
        agent_discovery = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "agent",
                "discover",
                "--goal",
                "MEA neural interface material",
                "--out-dir",
                str(agent_discovery_dir),
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        agent_discovery_summary = json.loads(agent_discovery.stdout)
        assert agent_discovery_summary["status"] == "discovery_ready"
        assert agent_discovery_summary["claim_ready"] is False
        assert (agent_discovery_dir / "candidate_queue.json").exists()

        candidate_rank_dir = Path(tmp) / "candidate_rank"
        candidate_rank = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "candidate",
                "rank",
                "--goal",
                "MEA neural interface material",
                "--out-dir",
                str(candidate_rank_dir),
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        candidate_rank_summary = json.loads(candidate_rank.stdout)
        assert candidate_rank_summary["status"] == "discovery_ready"
        assert (candidate_rank_dir / "ranking.md").exists()

        assay_plan_dir = Path(tmp) / "assay_plan"
        assay_plan = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "assay-plan",
                "--goal",
                "MEA neural interface material",
                "--out-dir",
                str(assay_plan_dir),
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assay_plan_summary = json.loads(assay_plan.stdout)
        assert assay_plan_summary["status"] == "discovery_ready"
        assert (assay_plan_dir / "assay_plan.md").exists()
        assert (assay_plan_dir / "rfq_package.md").exists()

        wizard_out = Path(tmp) / "falsiflow_wizard.html"
        wizard = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "wizard",
                "--out",
                str(wizard_out),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        wizard_summary = json.loads(wizard.stdout)
        assert wizard_summary["status"] == "wizard_ready"
        assert wizard_summary["wizard_path"].endswith("falsiflow_wizard.html")
        wizard_html = wizard_out.read_text(encoding="utf-8")
        assert "Falsiflow Browser Wizard" in wizard_html
        assert "Plain-language use case" in wizard_html
        assert "Material or coating screen" in wizard_html
        assert "Vendor evidence review" in wizard_html
        assert "Custom R&D decision" in wizard_html
        assert "falsiflow scaffold" in wizard_html
        assert "Download project.json" in wizard_html

        doctor = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "doctor",
                "--project-dir",
                str(quickstart_project_dir),
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        doctor_summary = json.loads(doctor.stdout)
        assert doctor_summary["status"] == "doctor_ready"
        assert doctor_summary["claim_check_status"] == "claim_check_ready"
        assert doctor_summary["verification_status"] == "bundle_verified"
        assert doctor_summary["repair_checklist"][0]["command"].startswith("falsiflow claim-check")
        assert (quickstart_project_dir / "doctor" / "doctor_summary.json").exists()
        doctor_report = (quickstart_project_dir / "doctor" / "doctor_summary.md").read_text(encoding="utf-8")
        assert "Falsiflow Doctor" in doctor_report
        assert "Repair Checklist" in doctor_report
        doctor_human_dir = Path(tmp) / "doctor_human_ready"
        doctor_human = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "doctor",
                "--project-dir",
                str(quickstart_project_dir),
                "--out-dir",
                str(doctor_human_dir),
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "Next review:" in doctor_human.stdout
        assert "First repair:" not in doctor_human.stdout

        blocked_doctor_dir = Path(tmp) / "blocked_doctor"
        blocked_doctor = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "doctor",
                "--project-dir",
                str(quickstart_project_dir),
                "--evidence",
                str(quickstart_project_dir / "evidence_placeholder_demo.csv"),
                "--out-dir",
                str(blocked_doctor_dir),
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert blocked_doctor.returncode == 2
        blocked_doctor_summary = json.loads(blocked_doctor.stdout)
        assert blocked_doctor_summary["status"] == "doctor_blocked"
        assert blocked_doctor_summary["repair_checklist"]
        assert "command" in blocked_doctor_summary["repair_checklist"][0]
        assert "Repair Checklist" in (blocked_doctor_dir / "doctor_summary.md").read_text(encoding="utf-8")

        adoption_check_dir = Path(tmp) / "adoption_check"
        adoption_check = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "adoption-check",
                "--out-dir",
                str(adoption_check_dir),
                "--skip-dist",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        adoption_summary = json.loads(adoption_check.stdout)
        assert adoption_summary["status"] == "adoption_ready"
        assert adoption_summary["release_validation_status"] == "release_validation_skipped"
        assert "Distribution validation was skipped" in adoption_summary["release_validation_message"]
        assert adoption_summary["casebook_check_status"] == "casebook_check_ready"
        assert adoption_summary["ready_priority_count"] == 5
        assert adoption_summary["priority_count"] == 5
        assert adoption_summary["repair_checklist"][0]["command"].startswith("falsiflow adoption-check")
        assert adoption_summary["repair_checklist"][0]["expected_artifact"].endswith("adoption_check.json")
        assert "success_signal" in adoption_summary["repair_checklist"][0]
        adoption_release_priority = next(priority for priority in adoption_summary["priorities"] if priority["priority_id"] == "release_and_distribution")
        adoption_release_checks = {check["check"]: check for check in adoption_release_priority["checks"]}
        assert {"gitignore_build_artifacts", "source_build_cache_cleanup"} <= set(adoption_release_checks)
        assert adoption_release_checks["gitignore_build_artifacts"]["status"] == "passed"
        assert adoption_release_checks["source_build_cache_cleanup"]["status"] == "passed"
        assert "skipped" in adoption_release_checks["source_build_cache_cleanup"]["message"]
        assert (adoption_check_dir / "adoption_check.json").exists()
        assert (adoption_check_dir / "casebook_check" / "casebook_check.json").exists()
        adoption_report = (adoption_check_dir / "adoption_check.md").read_text(encoding="utf-8")
        assert "Falsiflow Adoption Check" in adoption_report
        assert "casebook_check_ready" in adoption_report
        assert "release_validation_skipped" in adoption_report
        assert "Repair Checklist" in adoption_report
        adoption_human_dir = Path(tmp) / "adoption_check_human"
        adoption_human = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "adoption-check",
                "--out-dir",
                str(adoption_human_dir),
                "--skip-dist",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "Next check: verify_adoption_ready" in adoption_human.stdout
        assert "Release validation: release_validation_skipped" in adoption_human.stdout
        assert "First repair:" not in adoption_human.stdout

        (bundle_dir / "sources" / "source_files" / "demo_raw_export.csv").write_text("tampered\n", encoding="utf-8")
        tampered_verify_out = Path(tmp) / "tampered_bundle_verify.json"
        tampered_verify = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify-bundle",
                "--bundle-dir",
                str(bundle_dir),
                "--out",
                str(tampered_verify_out),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert tampered_verify.returncode == 2
        tampered_verification = json.loads(tampered_verify_out.read_text(encoding="utf-8"))
        assert tampered_verification["status"] == "bundle_failed"
        assert tampered_verification["hash_mismatch_count"] == 1

        blocked_bundle_dir = Path(tmp) / "blocked_bundle"
        blocked_bundle = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "bundle",
                "--config",
                str(PROJECT_PATH),
                "--evidence",
                str(missing_source_evidence),
                "--out-dir",
                str(blocked_bundle_dir),
                "--strict",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert blocked_bundle.returncode == 2
        blocked_bundle_manifest = json.loads((blocked_bundle_dir / "bundle_manifest.json").read_text(encoding="utf-8"))
        assert blocked_bundle_manifest["status"] == "bundle_blocked"
        assert blocked_bundle_manifest["source_status"] == "sources_blocked"

        selftest = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "selftest",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "Falsiflow selftest: passed" in selftest.stdout

        selftest_out = Path(tmp) / "selftest"
        selftest_json = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "selftest",
                "--json",
                "--out-dir",
                str(selftest_out),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        selftest_summary = json.loads(selftest_json.stdout)
        assert selftest_summary["status"] == "passed"
        assert selftest_summary["template_count"] == EXPECTED_TEMPLATE_COUNT
        assert selftest_summary["audit_ready_count"] == EXPECTED_TEMPLATE_COUNT
        assert selftest_summary["failure_count"] == 0
        schema_kinds = {schema["kind"] for schema in selftest_summary["schemas"]}
        assert {"project", "evidence-row", "claim-summary", "audit-review", "portfolio-summary", "import-coverage", "source-manifest", "bundle-manifest", "bundle-verification", "claim-check", "quickstart-summary", "doctor-summary", "demo-summary", "template-check", "template-pack-manifest", "template-pack-verification", "template-install", "template-registry", "template-lock", "template-attestation", "template-attestation-verification", "template-policy", "template-policy-verification", "template-release", "template-release-verification", "template-gallery", "casebook-check", "external-evidence", "external-readiness", "adoption-check", "release-check", "all"} <= schema_kinds
        assert (selftest_out / "portfolio" / "portfolio_summary.json").exists()

        demo_out = Path(tmp) / "demo"
        demo = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "demo",
                "--out-dir",
                str(demo_out),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        demo_summary = json.loads(demo.stdout)
        assert demo_summary["status"] == "demo_ready"
        assert demo_summary["verification_status"] == "bundle_verified"
        assert (demo_out / "demo_summary.json").exists()
        assert (demo_out / "evidence_bundle_verify.md").exists()

        template_check_out = Path(tmp) / "template_check"
        template_check = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-check",
                "--template-dir",
                str(EXAMPLE_TEMPLATE_ROOT / "neural_materials"),
                "--out-dir",
                str(template_check_out),
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_check_summary = json.loads(template_check.stdout)
        assert template_check_summary["status"] == "template_ready"
        assert template_check_summary["pass_claim_ready"] is True
        assert template_check_summary["placeholder_claim_ready"] is False
        assert template_check_summary["verification_status"] == "bundle_verified"
        assert template_check_summary["failure_count"] == 0
        assert (template_check_out / "template_check.md").exists()

        unsafe_template = Path(tmp) / "unsafe_template"
        shutil.copytree(EXAMPLE_TEMPLATE_ROOT / "neural_materials", unsafe_template)
        (unsafe_template / "evidence_placeholder_demo.csv").write_text(
            (unsafe_template / "evidence_pass_demo.csv").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        unsafe_template_check_out = Path(tmp) / "unsafe_template_check"
        unsafe_template_check = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-check",
                "--template-dir",
                str(unsafe_template),
                "--out-dir",
                str(unsafe_template_check_out),
                "--json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert unsafe_template_check.returncode == 2
        unsafe_template_check_summary = json.loads(unsafe_template_check.stdout)
        assert unsafe_template_check_summary["status"] == "template_blocked"
        assert unsafe_template_check_summary["placeholder_claim_ready"] is True
        assert any(check["check"] == "placeholder_demo_blocks_claim" for check in unsafe_template_check_summary["failures"])

        template_scaffold_dir = Path(tmp) / "template_scaffold"
        template_scaffold_check_dir = Path(tmp) / "template_scaffold_check"
        template_scaffold = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-scaffold",
                "--out",
                str(template_scaffold_dir),
                "--template-id",
                "custom_screen_template",
                "--template-name",
                "Custom Screen Template",
                "--domain",
                "custom-biointerface",
                "--claim-statement",
                "Candidate clears a source-backed custom screen.",
                "--gate",
                "stability:ph_final,osmolality_final",
                "--gate",
                "response:viability_pct",
                "--rule",
                "stability:ph_final:<=:8",
                "--rule",
                "response:viability_pct:>=:80",
                "--sample",
                "candidate_a:sample_001",
                "--check-out-dir",
                str(template_scaffold_check_dir),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_scaffold_summary = json.loads(template_scaffold.stdout)
        assert template_scaffold_summary["status"] == "template_scaffolded"
        assert template_scaffold_summary["template_check_status"] == "template_ready"
        assert (template_scaffold_dir / "template.json").exists()
        assert (template_scaffold_dir / "evidence_pass_demo.csv").exists()
        assert (template_scaffold_dir / "evidence_placeholder_demo.csv").exists()
        assert (template_scaffold_dir / "source_files" / "demo_raw_export.csv").exists()
        generated_template_check = json.loads((template_scaffold_check_dir / "template_check.json").read_text(encoding="utf-8"))
        assert generated_template_check["status"] == "template_ready"
        assert generated_template_check["pass_claim_ready"] is True
        assert generated_template_check["placeholder_claim_ready"] is False

        template_pack_dir = Path(tmp) / "template_pack"
        template_pack_zip = Path(tmp) / "template_pack.zip"
        template_pack_verify_out = Path(tmp) / "template_pack_verify.json"
        template_pack_verify_report = Path(tmp) / "template_pack_verify.md"
        template_pack = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-pack",
                "--template-dir",
                str(template_scaffold_dir),
                "--out-dir",
                str(template_pack_dir),
                "--zip-out",
                str(template_pack_zip),
                "--verify-out",
                str(template_pack_verify_out),
                "--report-out",
                str(template_pack_verify_report),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_pack_summary = json.loads(template_pack.stdout)
        assert template_pack_summary["status"] == "template_pack_ready"
        assert template_pack_summary["verification_status"] == "template_pack_verified"
        assert (template_pack_dir / "template_pack_manifest.json").exists()
        assert template_pack_zip.exists()
        pack_verification = json.loads(template_pack_verify_out.read_text(encoding="utf-8"))
        assert pack_verification["status"] == "template_pack_verified"
        assert pack_verification["integrity_status"] == "integrity_verified"
        assert "Falsiflow Template Pack Verification" in template_pack_verify_report.read_text(encoding="utf-8")

        verify_template_pack_out = Path(tmp) / "verify_template_pack.json"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify-template-pack",
                "--zip",
                str(template_pack_zip),
                "--out",
                str(verify_template_pack_out),
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        verify_template_pack = json.loads(verify_template_pack_out.read_text(encoding="utf-8"))
        assert verify_template_pack["status"] == "template_pack_verified"

        installed_templates_dir = Path(tmp) / "installed_templates"
        install_check_dir = Path(tmp) / "installed_template_check"
        template_install = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-install",
                "--zip",
                str(template_pack_zip),
                "--templates-dir",
                str(installed_templates_dir),
                "--check-out-dir",
                str(install_check_dir),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_install_summary = json.loads(template_install.stdout)
        assert template_install_summary["status"] == "template_installed"
        assert template_install_summary["verification_status"] == "template_pack_verified"
        assert template_install_summary["template_check_status"] == "template_ready"
        assert template_install_summary["template_id"] == "custom_screen_template"
        assert (installed_templates_dir / "custom_screen_template" / "template.json").exists()
        assert (installed_templates_dir / "falsiflow_template_index.json").exists()
        installed_index = json.loads((installed_templates_dir / "falsiflow_template_index.json").read_text(encoding="utf-8"))
        assert installed_index["template_count"] == 1

        installed_templates = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "templates",
                "--template-root",
                str(installed_templates_dir),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        installed_template_records = json.loads(installed_templates.stdout)
        assert installed_template_records[0]["template"] == "custom_screen_template"
        installed_project_dir = Path(tmp) / "installed_project"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "init",
                "--template",
                "custom_screen_template",
                "--template-root",
                str(installed_templates_dir),
                "--out",
                str(installed_project_dir),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert (installed_project_dir / "project.json").exists()

        template_registry_out = Path(tmp) / "template_registry.json"
        template_registry_report = Path(tmp) / "template_registry.md"
        template_registry = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-registry",
                "--pack-zip",
                str(template_pack_zip),
                "--base-url",
                Path(tmp).as_uri(),
                "--out",
                str(template_registry_out),
                "--report-out",
                str(template_registry_report),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_registry_summary = json.loads(template_registry.stdout)
        assert template_registry_summary["status"] == "template_registry_ready"
        assert template_registry_summary["verified_template_count"] == 1
        assert template_registry_summary["templates"][0]["template_id"] == "custom_screen_template"
        assert template_registry_summary["templates"][0]["template_version"] == "0.1.0"
        assert template_registry_summary["templates"][0]["source_type"] == "url"
        assert template_registry_summary["templates"][0]["source_url"].startswith("file:")
        assert len(template_registry_summary["templates"][0]["source_sha256"]) == 64
        assert "Falsiflow Template Registry" in template_registry_report.read_text(encoding="utf-8")

        template_lock_out = Path(tmp) / "falsiflow_template_lock.json"
        template_lock = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-lock",
                "--registry",
                str(template_registry_out),
                "--template",
                "custom_screen_template",
                "--version",
                "0.1.0",
                "--out",
                str(template_lock_out),
                "--cache-dir",
                str(Path(tmp) / "template_source_cache"),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_lock_summary = json.loads(template_lock.stdout)
        assert template_lock_summary["status"] == "template_locked"
        assert template_lock_summary["template_id"] == "custom_screen_template"
        assert template_lock_summary["template_version"] == "0.1.0"
        assert template_lock_summary["source_type"] == "url"
        assert template_lock_summary["source_url"].startswith("file:")
        assert template_lock_summary["source_sha256"] == template_registry_summary["templates"][0]["source_sha256"]

        template_attestation_out = Path(tmp) / "falsiflow_template_lock.attestation.json"
        template_attestation = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-attest",
                "--subject",
                str(template_lock_out),
                "--subject-type",
                "template-lock",
                "--out",
                str(template_attestation_out),
                "--builder",
                "regression",
                "--key-id",
                "regression-key",
                "--signing-key",
                "regression-secret",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_attestation_summary = json.loads(template_attestation.stdout)
        assert template_attestation_summary["status"] == "template_attested"
        assert template_attestation_summary["subject_type"] == "template-lock"
        assert template_attestation_summary["signature_type"] == "hmac-sha256"
        assert template_attestation_summary["payload"]["template_id"] == "custom_screen_template"
        assert template_attestation_summary["payload"]["source_sha256"] == template_lock_summary["source_sha256"]

        template_attestation_verification = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify-template-attestation",
                "--attestation",
                str(template_attestation_out),
                "--subject",
                str(template_lock_out),
                "--signing-key",
                "regression-secret",
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_attestation_verification_summary = json.loads(template_attestation_verification.stdout)
        assert template_attestation_verification_summary["status"] == "template_attestation_verified"
        assert template_attestation_verification_summary["signature_verified"] is True

        template_policy_out = Path(tmp) / "falsiflow_template_policy.json"
        template_policy = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-policy",
                "--lock",
                str(template_lock_out),
                "--attestation",
                str(template_attestation_out),
                "--out",
                str(template_policy_out),
                "--policy-id",
                "regression-custom-screen",
                "--owner",
                "regression",
                "--signing-key",
                "regression-secret",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_policy_summary = json.loads(template_policy.stdout)
        assert template_policy_summary["status"] == "template_policy_ready"
        assert template_policy_summary["trusted_key_id"] == "regression-key"
        assert template_policy_summary["expected"]["source_sha256"] == template_lock_summary["source_sha256"]

        template_policy_verification = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify-template-policy",
                "--policy",
                str(template_policy_out),
                "--lock",
                str(template_lock_out),
                "--attestation",
                str(template_attestation_out),
                "--signing-key",
                "regression-secret",
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_policy_verification_summary = json.loads(template_policy_verification.stdout)
        assert template_policy_verification_summary["status"] == "template_policy_verified"
        assert template_policy_verification_summary["attestation_status"] == "template_attestation_verified"

        template_release_out = Path(tmp) / "falsiflow_template_release.zip"
        template_release = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-release",
                "--pack-zip",
                str(template_pack_zip),
                "--registry",
                str(template_registry_out),
                "--lock",
                str(template_lock_out),
                "--attestation",
                str(template_attestation_out),
                "--policy",
                str(template_policy_out),
                "--out",
                str(template_release_out),
                "--signing-key",
                "regression-secret",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_release_summary = json.loads(template_release.stdout)
        assert template_release_summary["status"] == "template_release_ready"
        assert template_release_summary["policy_verification_status"] == "template_policy_verified"

        template_release_verify_out = Path(tmp) / "falsiflow_template_release_verification.json"
        template_release_verify_report = Path(tmp) / "falsiflow_template_release_verification.md"
        template_release_verification = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify-template-release",
                "--release",
                str(template_release_out),
                "--signing-key",
                "regression-secret",
                "--out",
                str(template_release_verify_out),
                "--report-out",
                str(template_release_verify_report),
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        template_release_verification_summary = json.loads(template_release_verification.stdout)
        assert template_release_verification_summary["status"] == "template_release_verified"
        assert template_release_verification_summary["policy_verification_status"] == "template_policy_verified"
        assert template_release_verification_summary["unsafe_path_count"] == 0
        assert template_release_verification_summary["unmanifested_file_count"] == 0
        assert template_release_verification_summary["artifact_members"]["template_pack"] == "template_pack.zip"
        assert json.loads(template_release_verify_out.read_text(encoding="utf-8"))["status"] == "template_release_verified"
        template_release_report = template_release_verify_report.read_text(encoding="utf-8")
        assert "Falsiflow Template Release Verification" in template_release_report
        assert "Review Artifact Index" in template_release_report
        assert "template_release_manifest.json" in template_release_report
        assert "template_pack.zip" in template_release_report
        assert "No issues found." in template_release_report

        unsafe_release_out = Path(tmp) / "unsafe_template_release.zip"

        def make_unsafe_release(entries: dict[str, bytes]) -> dict[str, bytes]:
            manifest = json.loads(entries["template_release_manifest.json"])
            manifest["artifacts"][0]["path"] = "../template_pack.zip"
            entries["template_release_manifest.json"] = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
            return entries

        write_tampered_zip(template_release_out, unsafe_release_out, make_unsafe_release)
        unsafe_release_verification = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify-template-release",
                "--release",
                str(unsafe_release_out),
                "--signing-key",
                "regression-secret",
                "--report-out",
                str(Path(tmp) / "unsafe_template_release_verification.md"),
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert unsafe_release_verification.returncode == 2
        unsafe_release_summary = json.loads(unsafe_release_verification.stdout)
        assert unsafe_release_summary["status"] == "template_release_failed"
        assert unsafe_release_summary["unsafe_path_count"] >= 1
        assert any(issue["code"] == "unsafe_artifact_path" for issue in unsafe_release_summary["issues"])
        assert "unsafe_artifact_path" in (Path(tmp) / "unsafe_template_release_verification.md").read_text(encoding="utf-8")

        extra_file_release_out = Path(tmp) / "extra_file_template_release.zip"

        def add_unmanifested_file(entries: dict[str, bytes]) -> dict[str, bytes]:
            entries["unexpected.txt"] = b"not listed in the release manifest\n"
            return entries

        write_tampered_zip(template_release_out, extra_file_release_out, add_unmanifested_file)
        extra_file_release_verification = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify-template-release",
                "--release",
                str(extra_file_release_out),
                "--signing-key",
                "regression-secret",
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert extra_file_release_verification.returncode == 2
        extra_file_release_summary = json.loads(extra_file_release_verification.stdout)
        assert extra_file_release_summary["status"] == "template_release_failed"
        assert extra_file_release_summary["unmanifested_file_count"] == 1
        assert any(issue["code"] == "unmanifested_file" for issue in extra_file_release_summary["issues"])

        registry_mismatch_release_out = Path(tmp) / "registry_mismatch_template_release.zip"

        def tamper_registry_with_matching_artifact_hash(entries: dict[str, bytes]) -> dict[str, bytes]:
            registry = json.loads(entries["template_registry.json"])
            registry["tampered_for_regression"] = True
            registry_bytes = json.dumps(registry, indent=2, sort_keys=True).encode("utf-8") + b"\n"
            entries["template_registry.json"] = registry_bytes
            manifest = json.loads(entries["template_release_manifest.json"])
            for artifact in manifest["artifacts"]:
                if artifact["role"] == "template_registry":
                    artifact["bytes"] = len(registry_bytes)
                    artifact["sha256"] = sha256_data(registry_bytes)
            entries["template_release_manifest.json"] = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
            return entries

        write_tampered_zip(template_release_out, registry_mismatch_release_out, tamper_registry_with_matching_artifact_hash)
        registry_mismatch_verification = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify-template-release",
                "--release",
                str(registry_mismatch_release_out),
                "--signing-key",
                "regression-secret",
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert registry_mismatch_verification.returncode == 2
        registry_mismatch_summary = json.loads(registry_mismatch_verification.stdout)
        assert registry_mismatch_summary["status"] == "template_release_failed"
        assert any(issue["code"] == "registry_sha256_mismatch" for issue in registry_mismatch_summary["issues"])

        locked_templates_dir = Path(tmp) / "locked_templates"
        locked_install = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-install",
                "--lock",
                str(template_lock_out),
                "--attestation",
                str(template_attestation_out),
                "--signing-key",
                "regression-secret",
                "--require-attestation",
                "--policy",
                str(template_policy_out),
                "--templates-dir",
                str(locked_templates_dir),
                "--cache-dir",
                str(Path(tmp) / "template_install_cache"),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        locked_install_summary = json.loads(locked_install.stdout)
        assert locked_install_summary["status"] == "template_installed"
        assert locked_install_summary["lock_status"] == "template_locked"
        assert locked_install_summary["attestation_required"] is True
        assert locked_install_summary["attestation_status"] == "template_attestation_verified"
        assert locked_install_summary["attestation_signature_verified"] is True
        assert locked_install_summary["policy_status"] == "template_policy_verified"
        assert (locked_templates_dir / "custom_screen_template" / "project.json").exists()
        locked_install_index = json.loads((locked_templates_dir / "falsiflow_template_index.json").read_text(encoding="utf-8"))
        assert locked_install_index["templates"][0]["attestation_status"] == "template_attestation_verified"
        assert locked_install_index["templates"][0]["policy_status"] == "template_policy_verified"

        release_templates_dir = Path(tmp) / "release_templates"
        release_install = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-install",
                "--release",
                str(template_release_out),
                "--signing-key",
                "regression-secret",
                "--templates-dir",
                str(release_templates_dir),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        release_install_summary = json.loads(release_install.stdout)
        assert release_install_summary["status"] == "template_installed"
        assert release_install_summary["release_status"] == "template_release_verified"
        assert release_install_summary["policy_status"] == "template_policy_verified"
        assert (release_templates_dir / "custom_screen_template" / "project.json").exists()

        rejected_templates_dir = Path(tmp) / "rejected_templates"
        rejected_install = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "template-install",
                "--lock",
                str(template_lock_out),
                "--attestation",
                str(template_attestation_out),
                "--signing-key",
                "wrong-secret",
                "--require-attestation",
                "--policy",
                str(template_policy_out),
                "--templates-dir",
                str(rejected_templates_dir),
                "--cache-dir",
                str(Path(tmp) / "template_install_cache_rejected"),
                "--json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert rejected_install.returncode == 2
        rejected_install_summary = json.loads(rejected_install.stdout)
        assert rejected_install_summary["status"] == "template_install_blocked"
        assert rejected_install_summary["attestation_status"] == "template_attestation_failed"
        assert rejected_install_summary["policy_status"] == "template_policy_failed"
        assert rejected_install_summary["installed_file_count"] == 0

        (template_pack_dir / "template" / "project.json").write_text("tampered\n", encoding="utf-8")
        tampered_template_pack_out = Path(tmp) / "tampered_template_pack.json"
        tampered_template_pack = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify-template-pack",
                "--pack-dir",
                str(template_pack_dir),
                "--out",
                str(tampered_template_pack_out),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert tampered_template_pack.returncode == 2
        tampered_template_pack_summary = json.loads(tampered_template_pack_out.read_text(encoding="utf-8"))
        assert tampered_template_pack_summary["status"] == "template_pack_failed"
        assert tampered_template_pack_summary["hash_mismatch_count"] == 1

        release_check_out = Path(tmp) / "release_check"
        release_check = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "release-check",
                "--out-dir",
                str(release_check_out),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        release_summary = json.loads(release_check.stdout)
        assert release_summary["status"] == "release_ready"
        assert release_summary["package_status"] == "package_ready"
        assert release_summary["package_failure_count"] == 0
        assert release_summary["dist_status"] == "dist_ready"
        assert release_summary["release_validation_status"] == "release_validation_ready"
        assert "Wheel, sdist" in release_summary["release_validation_message"]
        assert release_summary["dist_failure_count"] == 0
        assert release_summary["demo_status"] == "demo_ready"
        assert release_summary["demo_summary"]["verification_status"] == "bundle_verified"
        assert release_summary["demo_package_status"] == "demo_package_ready"
        assert release_summary["demo_package_summary"]["publishable"] is True
        assert release_summary["publish_kit_status"] == "publish_kit_ready"
        assert release_summary["publish_kit_summary"]["account_action_required"] is True
        assert release_summary["external_check_status"] in {"external_ready", "external_blocked"}
        assert release_summary["external_check_summary"]["check_count"] >= 8
        assert any(check["check"] == "pipx_public_package" for check in release_summary["external_check_summary"]["checks"])
        assert any(check["check"] == "public_package_first_run" for check in release_summary["external_check_summary"]["checks"])
        assert any(check["check"] == "public_package_claim_check" for check in release_summary["external_check_summary"]["checks"])
        assert any(check["check"] == "mcp_public_package_selftest" for check in release_summary["external_check_summary"]["checks"])
        assert release_summary["quickstart_status"] == "quickstart_ready"
        assert release_summary["quickstart_summary"]["claim_check_status"] == "claim_check_ready"
        assert release_summary["quickstart_summary"]["verification_status"] == "bundle_verified"
        assert release_summary["quickstart_summary"]["next_commands"][0].startswith("falsiflow doctor --project-dir")
        assert release_summary["doctor_status"] == "doctor_ready"
        assert release_summary["doctor_summary"]["claim_check_status"] == "claim_check_ready"
        assert release_summary["doctor_summary"]["verification_status"] == "bundle_verified"
        assert release_summary["doctor_summary"]["repair_checklist"][0]["expected_artifact"].endswith("claim_check.md")
        assert release_summary["claim_check_status"] == "claim_check_ready"
        assert release_summary["claim_check_summary"]["verification_status"] == "bundle_verified"
        assert release_summary["downstream_smoke_replay_status"] == "downstream_smoke_replay_ready"
        downstream_smoke = release_summary["downstream_smoke_replay_summary"]
        assert downstream_smoke["fixture_count"] == 3
        downstream_replay_checks = {check["check"]: check for check in downstream_smoke["checks"]}
        assert {
            "downstream_ai_eval_smoke_blocked_replay",
            "downstream_ai_eval_smoke_ready_replay",
            "downstream_product_metric_smoke_blocked_replay",
            "downstream_product_metric_smoke_ready_replay",
            "downstream_rag_eval_smoke_blocked_replay",
            "downstream_rag_eval_smoke_ready_replay",
        } <= set(downstream_replay_checks)
        assert all(check["status"] == "passed" for check in downstream_replay_checks.values())
        assert all(fixture["blocked_status"] == "claim_check_blocked" for fixture in downstream_smoke["fixtures"])
        assert all(fixture["ready_status"] == "claim_check_ready" for fixture in downstream_smoke["fixtures"])
        assert all(fixture["ready_verification_status"] == "bundle_verified" for fixture in downstream_smoke["fixtures"])
        assert release_summary["adoption_check_status"] == "adoption_ready"
        assert release_summary["adoption_check_summary"]["release_validation_status"] == "release_validation_ready"
        assert release_summary["adoption_check_summary"]["ready_priority_count"] == 5
        assert release_summary["adoption_check_summary"]["priority_count"] == 5
        assert release_summary["adoption_check_summary"]["repair_checklist"][0]["command"].startswith("falsiflow adoption-check")
        assert "adoption_recheck" in release_summary["adoption_check_summary"]["repair_checklist"][0]["command"]
        assert release_summary["adoption_check_summary"]["repair_checklist"][0]["expected_artifact"].endswith("adoption_recheck/adoption_check.json")
        release_adoption_priority = next(priority for priority in release_summary["adoption_check_summary"]["priorities"] if priority["priority_id"] == "release_and_distribution")
        release_adoption_checks = {check["check"]: check for check in release_adoption_priority["checks"]}
        assert release_adoption_checks["gitignore_build_artifacts"]["status"] == "passed"
        assert release_adoption_checks["source_build_cache_cleanup"]["status"] == "passed"
        assert release_summary["template_gallery_status"] == "template_gallery_ready"
        assert release_summary["template_gallery_summary"]["template_count"] == EXPECTED_TEMPLATE_COUNT
        assert release_summary["template_gallery_summary"]["non_neural_template_count"] == EXPECTED_NON_NEURAL_TEMPLATE_COUNT
        assert release_summary["casebook_check_status"] == "casebook_check_ready"
        assert release_summary["casebook_check_summary"]["positive_demo_ready_count"] == EXPECTED_TEMPLATE_COUNT
        assert release_summary["casebook_check_summary"]["blocked_path_count"] == EXPECTED_TEMPLATE_COUNT
        assert release_summary["casebook_check_summary"]["bundle_verified_count"] == EXPECTED_TEMPLATE_COUNT
        assert release_summary["template_check_count"] == EXPECTED_TEMPLATE_COUNT
        assert release_summary["template_check_ready_count"] == EXPECTED_TEMPLATE_COUNT
        assert all(item["status"] == "template_ready" for item in release_summary["template_checks"])
        assert release_summary["template_pack_status"] == "template_pack_ready"
        assert release_summary["template_pack_verification_status"] == "template_pack_verified"
        assert release_summary["template_pack_summary"]["template_id"] == "neural_materials"
        assert release_summary["template_registry_status"] == "template_registry_ready"
        assert release_summary["template_registry_summary"]["verified_template_count"] == 1
        assert release_summary["template_registry_summary"]["templates"][0]["source_type"] == "url"
        assert release_summary["template_lock_status"] == "template_locked"
        assert release_summary["template_lock_summary"]["template_id"] == "neural_materials"
        assert release_summary["template_lock_summary"]["source_type"] == "url"
        assert release_summary["template_attestation_status"] == "template_attested"
        assert release_summary["template_attestation_summary"]["subject_type"] == "template-lock"
        assert release_summary["template_attestation_summary"]["signature_type"] == "hmac-sha256"
        assert release_summary["template_attestation_verification_status"] == "template_attestation_verified"
        assert release_summary["template_attestation_verification_summary"]["signature_verified"] is True
        assert release_summary["template_policy_status"] == "template_policy_ready"
        assert release_summary["template_policy_verification_status"] == "template_policy_verified"
        assert release_summary["template_policy_summary"]["trusted_key_id"] == "release-check"
        assert release_summary["template_release_status"] == "template_release_ready"
        assert release_summary["template_release_verification_status"] == "template_release_verified"
        assert release_summary["template_install_status"] == "template_installed"
        assert release_summary["template_install_summary"]["template_id"] == "neural_materials"
        assert release_summary["template_install_summary"]["template_check_status"] == "template_ready"
        assert release_summary["template_install_summary"]["attestation_required"] is True
        assert release_summary["template_install_summary"]["attestation_status"] == "template_attestation_verified"
        assert release_summary["template_install_summary"]["attestation_signature_verified"] is True
        assert release_summary["template_install_summary"]["policy_status"] == "template_policy_verified"
        assert release_summary["template_install_summary"]["release_status"] == "template_release_verified"
        package_checks = {check["check"] for check in release_summary["package_checks"]}
        assert {
            "changelog_current_version",
            "console_script",
            "pyproject_requires_python",
            "pyproject_keywords",
            "pyproject_classifiers",
            "pyproject_project_urls",
            "pyproject_project_url_labels_pypi_safe",
            "manifest_release_docs",
            "readme_adoption_entry",
            "readme_community_health_entry",
            "readme_citation_governance_entry",
            "readme_architecture_entry",
            "readme_data_contract_entry",
            "readme_adapter_profiles_entry",
            "readme_mcp_entry",
            "readme_template_authoring_entry",
            "readme_troubleshooting_entry",
            "readme_security_posture_entry",
            "readme_cli_reference_entry",
            "readme_positioning_entry",
            "readme_public_casebook_entry",
            "readme_rag_quality_gate_proposal_entry",
            "readme_casebook_check_entry",
            "package_downstream_pr_proof_strip_exists",
            "downstream_pr_proof_strip_exists",
            "downstream_pr_proof_strip_png_exists",
            "readme_downstream_pr_proof_strip_asset",
            "readme_benchmark_proof_links",
            "readme_local_llm_proof_links",
            "package_downstream_pr_proof_strip_matches_docs",
            "readme_proof_strip_exists",
            "readme_visual_asset",
            "readme_pypi_renderable_image_urls",
            "readme_first_screen_story",
            "start_docs",
            "install_docs",
            "install_script",
            "powershell_install_script",
            "pipx_docs",
            "onboard_docs",
            "static_demo_docs",
            "demo_package_docs",
            "publish_kit_docs",
            "launch_kit_docs",
            "launch_metrics_docs",
            "launch_execution_exists",
            "launch_execution_docs",
            "launch_article_exists",
            "launch_article_visual_docs",
            "product_metric_article_exists",
            "product_metric_article_live_proof_docs",
            "benchmark_article_exists",
            "benchmark_article_live_proof_docs",
            "external_check_docs",
            "readme_github_action_docs",
            "github_action_examples_rag_eval_snippet",
            "downstream_ai_eval_smoke_fixture_exists",
            "downstream_ai_eval_smoke_fixture",
            "downstream_product_metric_smoke_fixture_exists",
            "downstream_product_metric_smoke_fixture",
            "downstream_rag_eval_smoke_fixture_exists",
            "downstream_rag_eval_smoke_fixture",
            "downstream_ai_eval_live_proof_links",
            "workbench_docs",
            "discover_docs",
            "public_interface_docs",
            "makefile_entrypoints",
            "github_ci_workflow",
            "github_action_exists",
            "github_action_entrypoint",
            "github_action_yaml_safe",
            "github_pages_workflow",
            "github_cross_platform_workflow",
            "github_external_evidence_workflow",
            "github_scorecard_workflow",
            "github_pypi_publish_workflow",
            "github_dependabot_config",
            "try_docs",
            "launchpad_docs",
            "wizard_docs",
            "serve_docs",
            "quickstart_docs",
            "doctor_docs",
            "adoption_check_docs",
            "adoption_priorities",
            "architecture_exists",
            "architecture_docs",
            "data_contract_exists",
            "data_contract_docs",
            "adapter_profiles_exists",
            "adapter_profiles_docs",
            "local_llm_eval_quickstart_exists",
            "local_llm_eval_quickstart_docs",
            "local_llm_eval_fixture_proof_snippet_docs",
            "mcp_docs_exists",
            "mcp_docs",
            "casebook_check_exists",
            "casebook_check_docs",
            "template_authoring_exists",
            "template_authoring_docs",
            "troubleshooting_exists",
            "troubleshooting_docs",
            "cli_reference_docs",
            "positioning_casebook",
            "public_casebook",
            "rag_quality_gate_proposal_exists",
            "rag_quality_gate_proposal_docs",
            "pypi_trusted_publishing_exists",
            "pypi_trusted_publishing_docs",
            "security_posture_exists",
            "security_posture_docs",
            "audit_review_docs",
            "gitignore_build_artifacts",
            "contributing_gates",
            "release_checklist",
            "citation_metadata",
            "security_policy",
            "code_of_conduct_policy",
            "governance_policy",
            "support_policy",
            "responsible_use_policy",
            "roadmap_policy",
            "claim_check_docs",
            "walkthrough_commands",
            "template_package_data",
            "template_check_docs",
            "template_scaffold_docs",
            "template_pack_docs",
            "template_install_docs",
            "template_registry_docs",
            "template_attestation_docs",
            "template_policy_docs",
            "template_release_docs",
            "template_gallery_docs",
            "local_llm_eval_import_fixture",
            "github_action_evidence_import_mode",
        } <= package_checks
        dist_checks = {check["check"]: check for check in release_summary["dist_checks"]}
        assert {"wheel_build", "sdist_build", "wheel_install", "installed_release_check", "installed_templates", "source_build_cache_cleanup"} <= set(dist_checks)
        assert "isolated PEP 517" in dist_checks["sdist_build"]["message"]
        package_check_map = {check["check"]: check for check in release_summary["package_checks"]}
        assert package_check_map["release_checklist"]["status"] == "passed"
        assert package_check_map["github_action_entrypoint"]["status"] == "passed"
        assert package_check_map["github_action_yaml_safe"]["status"] == "passed"
        assert package_check_map["github_external_evidence_workflow"]["status"] == "passed"
        assert package_check_map["pypi_trusted_publishing_docs"]["status"] == "passed"
        assert package_check_map["readme_github_action_docs"]["status"] == "passed"
        assert package_check_map["package_downstream_pr_proof_strip_matches_docs"]["status"] == "passed"
        assert package_check_map["readme_downstream_pr_proof_strip_asset"]["status"] == "passed"
        assert package_check_map["readme_pypi_renderable_image_urls"]["status"] == "passed"
        assert package_check_map["launch_execution_docs"]["status"] == "passed"
        assert package_check_map["mcp_docs"]["status"] == "passed"
        assert package_check_map["github_action_examples_rag_eval_snippet"]["status"] == "passed"
        assert package_check_map["downstream_ai_eval_smoke_fixture"]["status"] == "passed"
        assert package_check_map["downstream_product_metric_smoke_fixture"]["status"] == "passed"
        assert package_check_map["downstream_rag_eval_smoke_fixture"]["status"] == "passed"
        assert package_check_map["local_llm_eval_import_fixture"]["status"] == "passed"
        assert package_check_map["github_action_evidence_import_mode"]["status"] == "passed"
        assert package_check_map["downstream_ai_eval_live_proof_links"]["status"] == "passed"
        action_text = (ROOT / "action.yml").read_text(encoding="utf-8")
        assert "using: composite" in action_text
        assert "actions/setup-python@v6" in action_text
        assert "GITHUB_ACTION_PATH" in action_text
        assert 'description: "Gate to run:' in action_text
        assert 'description: "Evidence CSV path for claim-check mode, or output evidence CSV path for evidence-import mode."' in action_text
        assert "evidence-import)" in action_text
        assert 'cmd+=(evidence import --profile "$FALSIFLOW_PROFILE"' in action_text
        assert 'cmd+=(--project-dir "$FALSIFLOW_PROJECT_DIR")' in action_text
        assert 'if [ -n "$FALSIFLOW_EVIDENCE" ]; then\n                cmd+=(--evidence "$FALSIFLOW_EVIDENCE")' in action_text
        assert {"claim-check", "evidence-import", "template-check", "casebook-check", "release-check", "adoption-check", "quickstart", "external-check"} <= set(action_text.replace(",", " ").split())
        readme_first_screen = (ROOT / "README.md").read_text(encoding="utf-8")[:2400]
        assert "AI eval" in readme_first_screen
        assert "falsiflow quickstart --template ai_claim_evaluation" in readme_first_screen
        assert "claim_check_blocked" in readme_first_screen
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
        assert re.search(r"!\[[^\]]*\]\(docs/assets/", readme_text) is None
        assert "release_validation_ready" in (ROOT / "RELEASE.md").read_text(encoding="utf-8")
        assert release_summary["template_count"] == EXPECTED_TEMPLATE_COUNT
        assert release_summary["bundle_verified_count"] == EXPECTED_TEMPLATE_COUNT
        assert release_summary["failure_count"] == 0
        assert any(artifact["artifact"] == "Launch metrics tracker" for artifact in release_summary["release_review_artifact_index"])
        assert any(artifact["artifact"] == "Public release evidence ledger" for artifact in release_summary["release_review_artifact_index"])
        assert any(artifact["artifact"] == "Public release rehearsal" for artifact in release_summary["release_review_artifact_index"])
        assert (release_check_out / "release_check.json").exists()
        assert (release_check_out / "release_check.md").exists()
        assert (release_check_out / "adoption_check.json").exists()
        assert (release_check_out / "adoption_check.md").exists()
        assert (release_check_out / "quickstart_project" / "quickstart_summary.json").exists()
        assert (release_check_out / "quickstart_project" / "claim_check" / "claim_check.json").exists()
        assert (release_check_out / "doctor" / "doctor_summary.json").exists()
        assert (release_check_out / "doctor" / "doctor_summary.md").exists()
        assert (release_check_out / "template_gallery.json").exists()
        assert (release_check_out / "template_gallery.md").exists()
        assert (release_check_out / "casebook_check" / "casebook_check.json").exists()
        assert (release_check_out / "casebook_check" / "casebook_check.md").exists()
        assert (release_check_out / "casebook_check" / "casebook_reviewer_replay.md").exists()
        assert (release_check_out / "casebook_check" / "casebook_reviewer_replay.sh").exists()
        assert (release_check_out / "casebook_check" / "casebook_reviewer_replay.ps1").exists()
        assert (release_check_out / "claim_check" / "claim_check.json").exists()
        assert (release_check_out / "claim_check" / "claim_check.md").exists()
        assert (release_check_out / "launch_kit" / "launch_summary.json").exists()
        assert (release_check_out / "launch_kit" / "launch_metrics.json").exists()
        assert (release_check_out / "launch_kit" / "launch_metrics.md").exists()
        assert (release_check_out / "publish_kit" / "public_release_evidence.json").exists()
        assert (release_check_out / "publish_kit" / "public_release_evidence.md").exists()
        assert (release_check_out / "publish_kit" / "release_rehearsal.json").exists()
        assert (release_check_out / "publish_kit" / "release_rehearsal.md").exists()
        release_report = (release_check_out / "release_check.md").read_text(encoding="utf-8")
        assert "Adoption Repair Checklist" in release_report
        assert "Release Review Artifact Index" in release_report
        assert "Template release verification" in release_report
        assert "Launch metrics tracker" in release_report
        assert "Public release evidence ledger" in release_report
        assert "Public release rehearsal" in release_report
        assert "Downstream Smoke Replay" in release_report
        assert "Downstream AI Eval Smoke" in release_report
        assert "Downstream Product Metric Smoke" in release_report
        assert "Downstream RAG Eval Smoke" in release_report
        assert (release_check_out / "downstream_smoke_replay" / "downstream_ai_eval_smoke" / "blocked" / "claim_check.json").exists()
        assert (release_check_out / "downstream_smoke_replay" / "downstream_ai_eval_smoke" / "ready" / "claim_check.json").exists()
        assert (release_check_out / "downstream_smoke_replay" / "downstream_product_metric_smoke" / "blocked" / "claim_check.json").exists()
        assert (release_check_out / "downstream_smoke_replay" / "downstream_product_metric_smoke" / "ready" / "claim_check.json").exists()
        assert (release_check_out / "downstream_smoke_replay" / "downstream_rag_eval_smoke" / "blocked" / "claim_check.json").exists()
        assert (release_check_out / "downstream_smoke_replay" / "downstream_rag_eval_smoke" / "ready" / "claim_check.json").exists()
        assert "claim_check/claim_check.md" in release_report
        assert "launch_kit/launch_metrics.md" in release_report
        assert "publish_kit/public_release_evidence.md" in release_report
        assert "publish_kit/release_rehearsal.md" in release_report
        assert "Release validation: `release_validation_ready`" in release_report
        assert "Adoption release validation: `release_validation_ready`" in release_report
        assert "Adoption Priority Evidence" in release_report
        assert "gitignore_build_artifacts" in release_report
        assert "source_build_cache_cleanup" in release_report
        assert "Distribution check removes transient build/" in release_report
        assert "adoption_recheck" in release_report
        release_human_out = Path(tmp) / "release_check_human"
        release_human = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "release-check",
                "--out-dir",
                str(release_human_out),
                "--skip-dist",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "Next adoption check: verify_adoption_ready" in release_human.stdout
        assert "Release validation: release_validation_skipped" in release_human.stdout
        assert "Adoption release validation: release_validation_skipped" in release_human.stdout
        assert "adoption_recheck" in release_human.stdout
        assert "First adoption repair:" not in release_human.stdout
        stale_release_out = Path(tmp) / "release_check_stale"
        stale_release_out.mkdir()
        stale_release_file = stale_release_out / "stale.txt"
        stale_release_file.write_text("stale release artifact\n", encoding="utf-8")
        stale_release_refused = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "release-check",
                "--out-dir",
                str(stale_release_out),
                "--skip-dist",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert stale_release_refused.returncode != 0
        assert "without --force" in stale_release_refused.stderr + stale_release_refused.stdout
        assert stale_release_file.exists()
        stale_release_forced = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "release-check",
                "--out-dir",
                str(stale_release_out),
                "--skip-dist",
                "--force",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        stale_release_summary = json.loads(stale_release_forced.stdout)
        assert stale_release_summary["status"] == "release_ready"
        assert stale_release_summary["failure_count"] == 0
        assert not stale_release_file.exists()
        assert (stale_release_out / "release_check.json").exists()
        assert "Falsiflow Adoption Check" in (release_check_out / "adoption_check.md").read_text(encoding="utf-8")
        assert "Falsiflow Template Gallery" in (release_check_out / "template_gallery.md").read_text(encoding="utf-8")
        assert "Falsiflow Casebook Check" in (release_check_out / "casebook_check" / "casebook_check.md").read_text(encoding="utf-8")
        assert (release_check_out / "template_release_verification.json").exists()
        assert (release_check_out / "template_release_verification.md").exists()
        release_template_report = (release_check_out / "template_release_verification.md").read_text(encoding="utf-8")
        assert "Falsiflow Template Release Verification" in release_template_report
        assert "Review Artifact Index" in release_template_report
        assert (release_check_out / "templates" / "neural_materials" / "bundle_verification.md").exists()


def assert_scaffold_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        scaffold_dir = tmp_dir / "custom_project"
        scaffold = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "scaffold",
                "--out",
                str(scaffold_dir),
                "--project-id",
                "custom_electrode_screen",
                "--project-name",
                "Custom Electrode Screen",
                "--domain",
                "biointerface",
                "--claim-id",
                "custom_claim",
                "--claim-statement",
                "Custom electrode candidate has source-backed screening evidence.",
                "--gate",
                "stability:ph_initial,ph_final",
                "--gate",
                "response:viability_pct,burst_rate_hz",
                "--gate-title",
                "response=Matched response",
                "--sample",
                "candidate_a:sample_001",
                "--sample",
                "response:control:control_001",
                "--rule",
                "stability:ph_final:<=:200:pH must stay bounded.",
                "--rule",
                "response:viability_pct:>=:80:Viability threshold.",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        scaffold_summary = json.loads(scaffold.stdout)
        assert scaffold_summary["status"] == "scaffolded"
        assert scaffold_summary["gate_count"] == 2
        assert scaffold_summary["sample_count"] == 3
        assert scaffold_summary["required_evidence_rows"] == 6

        project_path = scaffold_dir / "project.json"
        evidence_path = scaffold_dir / "evidence_template.csv"
        source_file = scaffold_dir / "source_files" / "raw_export.csv"
        project = load_project(project_path)
        validation = validate_project_config(project)
        assert validation["valid"] is True
        assert project["claim"]["requires_gates"] == ["stability", "response"]
        assert project["gates"][1]["title"] == "Matched response"
        assert project["gates"][0]["acceptance_rules"][0]["value"] == 200
        assert project["gates"][1]["acceptance_rules"][0]["operator"] == ">="
        assert (scaffold_dir / "README.md").exists()
        assert (scaffold_dir / "source_files" / "README.md").exists()

        blocked_dir = tmp_dir / "scaffold_blocked"
        blocked = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "audit",
                "--config",
                str(project_path),
                "--evidence",
                str(evidence_path),
                "--out-dir",
                str(blocked_dir),
                "--strict",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert blocked.returncode == 2
        blocked_summary = json.loads((blocked_dir / "claim_summary.json").read_text(encoding="utf-8"))
        assert blocked_summary["claim_ready"] is False

        source_file.write_text("row_id,value\nsource,regression\n", encoding="utf-8")
        fill_ready_evidence_template(evidence_path, value="100")
        ready_dir = tmp_dir / "scaffold_ready"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "audit",
                "--config",
                str(project_path),
                "--evidence",
                str(evidence_path),
                "--out-dir",
                str(ready_dir),
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        ready_summary = json.loads((ready_dir / "claim_summary.json").read_text(encoding="utf-8"))
        assert ready_summary["claim_ready"] is True
        assert ready_summary["required_evidence_rows"] == 6


def assert_limina_adapter_contract() -> None:
    row = {
        "run_id": "NHIPEDOT-H-B-lead_nhi_pedot_low_loading-R1-pre_soak",
        "phase": "H-B",
        "article_id": "lead_nhi_pedot_low_loading",
        "target_field": "eis_1khz_final_ohm",
        "value": "7200",
        "source_file": "data/source_files/full/nhi_pedot_forward/demo.csv",
        "measured_at": "2026-05-25T10:00:00Z",
        "operator_or_agent": "demo_operator",
        "instrument_id": "potentiostat_001",
    }
    evidence = limina_source_value_to_evidence(
        row,
        default_candidate="limina_alg_lam_pedot_lowdose_v0_2",
        default_gate="h_a_medium_stability",
    )
    assert evidence is not None
    assert evidence["gate_id"] == "h_b_electrical_interface"
    assert evidence["candidate_id"] == "lead_nhi_pedot_low_loading"
    assert evidence["field"] == "eis_1khz_final_ohm"

    h_a_row = {
        "run_id": "NHIPEDOT-H-A-lead_nhi_pedot_low_loading-R1-24h",
        "sample_event": "final",
        "target_field": "pH",
    }
    h_a_evidence = limina_source_value_to_evidence(
        h_a_row,
        default_candidate="limina_alg_lam_pedot_lowdose_v0_2",
        default_gate="h_a_medium_stability",
    )
    assert h_a_evidence is not None
    assert h_a_evidence["gate_id"] == "h_a_medium_stability"
    assert h_a_evidence["candidate_id"] == "lead_nhi_pedot_low_loading"
    assert h_a_evidence["field"] == "final.pH"

    project = build_project_from_evidence(
        [evidence, h_a_evidence],
        project_id="adapter_contract",
        claim_id="adapter_claim",
        claim_statement="Adapter contract test.",
        source_file_base_dir=".",
        allowed_source_roots=["data/source_files"],
    )
    assert project["claim"]["requires_gates"] == ["h_a_medium_stability", "h_b_electrical_interface"]
    assert len(project["gates"]) == 2


def assert_rule_filter_contract() -> None:
    project = {
        "project": {"id": "rule_filter_contract"},
        "claim": {"id": "claim", "requires_gates": ["filtered_gate"]},
        "evidence_policy": {
            "require_source_files": False,
            "required_metadata_fields": [],
        },
        "gates": [
            {
                "id": "filtered_gate",
                "samples": [
                    {"candidate_id": "control_article", "sample_id": "control_001"},
                    {"candidate_id": "lead_article", "sample_id": "lead_001"},
                ],
                "required_fields": ["score"],
                "acceptance_rules": [
                    {
                        "field": "score",
                        "operator": ">=",
                        "value": 10,
                        "candidate_id_contains": "lead",
                        "reason": "Only the lead article is subject to this rule.",
                    }
                ],
            }
        ],
    }
    evidence = [
        {"gate_id": "filtered_gate", "candidate_id": "control_article", "sample_id": "control_001", "field": "score", "value": "0"},
        {"gate_id": "filtered_gate", "candidate_id": "lead_article", "sample_id": "lead_001", "field": "score", "value": "11"},
    ]
    audit = audit_project(project, evidence)
    assert audit["claim_ready"] is True

    evidence[1]["value"] = "9"
    audit = audit_project(project, evidence)
    assert audit["claim_ready"] is False
    assert audit["gates"][0]["status"] == "failed_acceptance_rules"


def assert_wide_ingest_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        wide_csv = tmp_dir / "lab_export.csv"
        wide_csv.write_text(
            "\n".join([
                "sample_id,measured_at,operator,ph_initial,ph_final,blank_value",
                "sample_a,2026-05-25T09:00:00Z,lab_agent,7.20,7.28,",
                "sample_b,2026-05-25T09:10:00Z,lab_agent,7.18,7.24,",
            ]),
            encoding="utf-8",
        )
        out = tmp_dir / "evidence.csv"
        summary_out = tmp_dir / "summary.json"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "ingest-wide-csv",
                "--input",
                str(wide_csv),
                "--out",
                str(out),
                "--summary-out",
                str(summary_out),
                "--gate-id",
                "h_a_medium_stability",
                "--candidate-id",
                "candidate_a",
                "--sample-id-column",
                "sample_id",
                "--measured-at-column",
                "measured_at",
                "--operator-or-agent-column",
                "operator",
                "--source-file",
                str(wide_csv),
                "--field",
                "ph_initial",
                "--field",
                "ph_final",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        summary = json.loads(summary_out.read_text(encoding="utf-8"))
        assert summary["evidence_rows"] == 4
        assert summary["skipped_rows"] == 0
        evidence = out.read_text(encoding="utf-8")
        assert "h_a_medium_stability,candidate_a,sample_a,ph_initial,7.20" in evidence
        assert "h_a_medium_stability,candidate_a,sample_b,ph_final,7.24" in evidence

        evidence_import_out = tmp_dir / "evidence_import.csv"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "evidence",
                "import",
                "--input",
                str(wide_csv),
                "--out",
                str(evidence_import_out),
                "--gate-id",
                "h_a_medium_stability",
                "--candidate-id",
                "candidate_a",
                "--sample-id-column",
                "sample_id",
                "--measured-at-column",
                "measured_at",
                "--operator-or-agent-column",
                "operator",
                "--field",
                "ph_initial",
                "--field",
                "ph_final",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        evidence_import = evidence_import_out.read_text(encoding="utf-8")
        assert "h_a_medium_stability,candidate_a,sample_a,ph_initial,7.20" in evidence_import
        assert "h_a_medium_stability,candidate_a,sample_b,ph_final,7.24" in evidence_import

        vendor_csv = tmp_dir / "vendor_return.csv"
        vendor_csv.write_text(
            "\n".join([
                "sample,article,measured_at,vendor_contact,instrument_id,source_file,notes,vendor,adhesion_mpa,cytotoxicity_fraction",
                "coupon_001,coating_a,2026-05-25T11:00:00Z,vendor_lab,utm_01,vendor_raw.csv,first return,Example Labs,2.4,0.02",
            ]),
            encoding="utf-8",
        )
        profile_out = tmp_dir / "profile_evidence.csv"
        profile_summary = tmp_dir / "profile_summary.json"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "evidence",
                "import",
                "--profile",
                "vendor-measurement",
                "--input",
                str(vendor_csv),
                "--out",
                str(profile_out),
                "--summary-out",
                str(profile_summary),
                "--gate-id",
                "vendor_return_gate",
                "--candidate-id",
                "fallback_candidate",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        profile_summary_json = json.loads(profile_summary.read_text(encoding="utf-8"))
        assert profile_summary_json["adapter_profile"] == "vendor-measurement"
        assert profile_summary_json["adapter_settings"]["sample_id_column"] == "sample"
        assert profile_summary_json["adapter_settings"]["candidate_id_column"] == "article"
        assert profile_summary_json["evidence_rows"] == 2
        profile_evidence = profile_out.read_text(encoding="utf-8")
        assert "vendor_return_gate,coating_a,coupon_001,adhesion_mpa,2.4,vendor_raw.csv" in profile_evidence
        assert "vendor_return_gate,coating_a,coupon_001,cytotoxicity_fraction,0.02,vendor_raw.csv" in profile_evidence

        project_dir = tmp_dir / "wide_project"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "scaffold",
                "--out",
                str(project_dir),
                "--project-id",
                "wide_ingest_coverage",
                "--claim-id",
                "wide_ingest_coverage_claim",
                "--claim-statement",
                "Wide ingest coverage contract.",
                "--gate",
                "h_a_medium_stability:ph_initial,ph_final",
                "--sample",
                "candidate_a:sample_a",
                "--sample",
                "candidate_a:sample_b",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        coverage_out = tmp_dir / "coverage.json"
        covered_summary_out = tmp_dir / "covered_summary.json"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "ingest-wide-csv",
                "--input",
                str(wide_csv),
                "--out",
                str(tmp_dir / "covered_evidence.csv"),
                "--summary-out",
                str(covered_summary_out),
                "--coverage-out",
                str(coverage_out),
                "--config",
                str(project_dir / "project.json"),
                "--gate-id",
                "h_a_medium_stability",
                "--candidate-id",
                "candidate_a",
                "--sample-id-column",
                "sample_id",
                "--measured-at-column",
                "measured_at",
                "--operator-or-agent-column",
                "operator",
                "--field",
                "ph_initial",
                "--field",
                "ph_final",
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        coverage = json.loads(coverage_out.read_text(encoding="utf-8"))
        assert coverage["status"] == "coverage_ready"
        assert coverage["matched_evidence_rows"] == 4
        assert coverage["required_evidence_rows"] == 4
        assert coverage["missing_evidence_rows"] == 0
        covered_summary = json.loads(covered_summary_out.read_text(encoding="utf-8"))
        assert covered_summary["coverage"]["status"] == "coverage_ready"

        missing_coverage = tmp_dir / "missing_coverage.json"
        blocked = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "ingest-wide-csv",
                "--input",
                str(wide_csv),
                "--out",
                str(tmp_dir / "missing_evidence.csv"),
                "--coverage-out",
                str(missing_coverage),
                "--config",
                str(project_dir / "project.json"),
                "--gate-id",
                "h_a_medium_stability",
                "--candidate-id",
                "candidate_a",
                "--sample-id-column",
                "sample_id",
                "--measured-at-column",
                "measured_at",
                "--operator-or-agent-column",
                "operator",
                "--field",
                "ph_initial",
                "--strict",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert blocked.returncode == 2
        missing = json.loads(missing_coverage.read_text(encoding="utf-8"))
        assert missing["status"] == "coverage_blocked"
        assert missing["matched_evidence_rows"] == 2
        assert missing["missing_evidence_rows"] == 2
        assert {item["field"] for item in missing["missing_keys"]} == {"ph_final"}


def assert_eval_artifact_import_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        local_manifest = tmp_dir / "local_model_manifest.json"
        local_manifest.write_text(
            json.dumps({
                "eval_run_id": "eval_run_001",
                "candidate_model_id": "candidate_model",
                "baseline_model_id": "baseline_model",
                "dataset_version": "claims_eval_v2026_05_26",
                "prompt_set_hash": "promptset_sha256_demo",
                "model_file_hash": "gguf_sha256_demo",
                "baseline_model_version": "baseline_llm_2026_05_01",
                "evaluator_version": "eval_harness_0.4.0",
                "eval_script_hash": "eval_script_sha256_demo",
                "random_seed": 7,
                "raw_outputs_uri": "artifacts/candidate_raw_outputs.jsonl",
                "human_spotcheck_passed": True,
                "ci_run_url": "https://github.example/actions/runs/1",
                "runtime": "llama.cpp",
                "quantization": "Q4_K_M",
                "measured_at": "2026-05-26T12:00:00Z",
            }),
            encoding="utf-8",
        )
        local_results = tmp_dir / "local_eval_results.jsonl"
        local_results.write_text(
            "\n".join([
                json.dumps({"model_id": "candidate_model", "metric": "exact_match_rate", "value": 0.86}),
                json.dumps({"model_id": "candidate_model", "metric": "hallucination_rate", "value": 0.035}),
                json.dumps({"model_id": "candidate_model", "metric": "safety_policy_failure_rate", "value": 0.012}),
                json.dumps({"model_id": "candidate_model", "metric": "evaluated_item_count", "value": 640}),
                json.dumps({"model_id": "baseline_model", "metric": "exact_match_rate", "value": 0.78}),
                json.dumps({"model_id": "baseline_model", "metric": "hallucination_rate", "value": 0.07}),
                json.dumps({"model_id": "baseline_model", "metric": "safety_policy_failure_rate", "value": 0.025}),
                json.dumps({"model_id": "baseline_model", "metric": "evaluated_item_count", "value": 640}),
            ]),
            encoding="utf-8",
        )
        local_out = tmp_dir / "local_llm_evidence.csv"
        local_summary = tmp_dir / "local_llm_summary.json"
        local_coverage = tmp_dir / "local_llm_coverage.json"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "evidence",
                "import",
                "--profile",
                "local-llm-eval",
                "--input",
                str(local_results),
                "--manifest",
                str(local_manifest),
                "--out",
                str(local_out),
                "--summary-out",
                str(local_summary),
                "--config",
                str(ROOT / "examples" / "falsiflow" / "ai_claim_evaluation" / "project.json"),
                "--coverage-out",
                str(local_coverage),
                "--source-file",
                "source_files/ai_eval_raw_export.csv",
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        local_summary_json = json.loads(local_summary.read_text(encoding="utf-8"))
        assert local_summary_json["adapter_profile"] == "local-llm-eval"
        assert local_summary_json["adapter_kind"] == "eval-artifact"
        assert local_summary_json["profile_summary"]["local_model_metadata"]["runtime"] == "llama.cpp"
        assert json.loads(local_coverage.read_text(encoding="utf-8"))["status"] == "coverage_ready"
        assert "benchmark_quality,candidate_model,eval_run_001,exact_match_rate,0.86" in local_out.read_text(encoding="utf-8")

        fixture_dir = tmp_dir / "local_llm_eval_import"
        shutil.copytree(ROOT / "examples" / "local_llm_eval_import", fixture_dir)
        fixture_project = fixture_dir / "falsiflow_local_llm_eval"
        fixture_blocked = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "claim-check",
                "--project-dir",
                str(fixture_project),
                "--evidence",
                str(fixture_project / "evidence.csv"),
                "--out-dir",
                str(tmp_dir / "local_llm_fixture_blocked"),
                "--strict",
                "--force",
                "--json",
            ],
            cwd=fixture_dir,
            check=False,
            capture_output=True,
            text=True,
        )
        assert fixture_blocked.returncode == 2
        assert json.loads(fixture_blocked.stdout)["status"] == "claim_check_blocked"
        fixture_import = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "evidence",
                "import",
                "--profile",
                "local-llm-eval",
                "--input",
                str(fixture_project / "source_files" / "local_eval_results.jsonl"),
                "--manifest",
                str(fixture_project / "local_model_manifest.json"),
                "--out",
                str(fixture_project / "evidence.csv"),
                "--summary-out",
                str(tmp_dir / "local_llm_fixture_import_summary.json"),
                "--config",
                str(fixture_project / "project.json"),
                "--coverage-out",
                str(tmp_dir / "local_llm_fixture_import_coverage.json"),
                "--source-file",
                "source_files/local_eval_results.jsonl",
                "--strict",
                "--json",
            ],
            cwd=fixture_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        fixture_import_json = json.loads(fixture_import.stdout)
        assert fixture_import_json["adapter_profile"] == "local-llm-eval"
        assert fixture_import_json["coverage"]["status"] == "coverage_ready"
        assert fixture_import_json["profile_summary"]["local_model_metadata"]["runtime"] == "llama.cpp"
        assert (fixture_project / "evidence.csv").read_text(encoding="utf-8") == (fixture_project / "evidence_imported_demo.csv").read_text(encoding="utf-8")
        fixture_ready = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "claim-check",
                "--project-dir",
                str(fixture_project),
                "--evidence",
                str(fixture_project / "evidence.csv"),
                "--out-dir",
                str(tmp_dir / "local_llm_fixture_ready"),
                "--strict",
                "--force",
                "--json",
            ],
            cwd=fixture_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(fixture_ready.stdout)["status"] == "claim_check_ready"

        rag_manifest = tmp_dir / "rag_manifest.json"
        rag_manifest.write_text(
            json.dumps({
                "rag_eval_run_id": "rag_eval_001",
                "candidate_rag_id": "candidate_rag",
                "baseline_rag_id": "baseline_rag",
                "eval_set_version": "rag_eval_v2026_05_26",
                "query_set_hash": "queryset_sha256_demo",
                "candidate_rag_version": "candidate_rag@abc123",
                "baseline_rag_version": "baseline_rag@def456",
                "judge_version": "rag_judge_0.3.0",
                "retrieval_run_sha256": "retrieval_sha256_demo",
                "raw_answers_sha256": "answers_sha256_demo",
                "eval_script_hash": "rag_eval_script_sha256_demo",
                "ci_run_url": "https://github.example/actions/runs/2",
                "measured_at": "2026-05-26T12:30:00Z",
            }),
            encoding="utf-8",
        )
        rag_results = tmp_dir / "rag_results.json"
        rag_results.write_text(
            json.dumps({
                "candidate_metrics": {
                    "recall_at_5": 0.86,
                    "mrr_at_10": 0.74,
                    "retrieval_coverage_rate": 0.98,
                    "faithfulness_rate": 0.94,
                    "unsupported_answer_rate": 0.025,
                    "answer_correctness_rate": 0.87,
                    "judged_item_count": 420,
                    "citation_precision": 0.93,
                    "source_coverage_rate": 0.97,
                    "missing_source_rate": 0.01,
                },
                "baseline_metrics": {
                    "recall_at_5": 0.80,
                    "mrr_at_10": 0.68,
                    "retrieval_coverage_rate": 0.95,
                },
            }),
            encoding="utf-8",
        )
        rag_out = tmp_dir / "rag_evidence.csv"
        rag_coverage = tmp_dir / "rag_coverage.json"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "evidence",
                "import",
                "--profile",
                "rag-eval",
                "--input",
                str(rag_results),
                "--manifest",
                str(rag_manifest),
                "--out",
                str(rag_out),
                "--config",
                str(ROOT / "examples" / "falsiflow" / "rag_quality_gate" / "project.json"),
                "--coverage-out",
                str(rag_coverage),
                "--source-file",
                "source_files/rag_eval_raw_export.csv",
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(rag_coverage.read_text(encoding="utf-8"))["status"] == "coverage_ready"
        rag_evidence = rag_out.read_text(encoding="utf-8")
        assert "retrieval_quality,candidate_rag,rag_eval_001,recall_at_5,0.86" in rag_evidence
        assert "source_coverage,candidate_rag,rag_eval_001,citation_precision,0.93" in rag_evidence

        raw_rag_out = tmp_dir / "raw_rag_evidence.csv"
        raw_rag_coverage = tmp_dir / "raw_rag_coverage.json"
        subprocess.run(
            [
                sys.executable,
                str(CLI),
                "evidence",
                "import",
                "--profile",
                "rag-eval",
                "--input",
                str(ROOT / "examples" / "falsiflow" / "rag_quality_gate" / "source_files" / "rag_eval_raw_export.csv"),
                "--out",
                str(raw_rag_out),
                "--config",
                str(ROOT / "examples" / "falsiflow" / "rag_quality_gate" / "project.json"),
                "--coverage-out",
                str(raw_rag_coverage),
                "--source-file",
                "source_files/rag_eval_raw_export.csv",
                "--strict",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(raw_rag_coverage.read_text(encoding="utf-8"))["status"] == "coverage_ready"
        raw_rag_evidence = raw_rag_out.read_text(encoding="utf-8")
        assert "evaluation_provenance,candidate_rag,rag_eval_001,candidate_rag_version_recorded,true" in raw_rag_evidence
        assert "reproducibility_package,candidate_rag,rag_eval_001,retrieval_run_archived,true" in raw_rag_evidence
        raw_claim_check = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "claim-check",
                "--config",
                str(ROOT / "examples" / "falsiflow" / "rag_quality_gate" / "project.json"),
                "--evidence",
                str(raw_rag_out),
                "--out-dir",
                str(tmp_dir / "raw_rag_claim_check"),
                "--strict",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(raw_claim_check.stdout)["status"] == "claim_check_ready"


def assert_mcp_server_contract() -> None:
    selftest = subprocess.run(
        [sys.executable, str(CLI), "mcp", "--selftest", "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    selftest_summary = json.loads(selftest.stdout)
    assert selftest_summary["status"] == "mcp_selftest_ready"
    assert selftest_summary["tool_count"] >= 4
    assert selftest_summary["resource_count"] >= 5
    assert selftest_summary["checked_tool_statuses"]["falsiflow.validate_claims"] == "claim_check_ready"
    assert selftest_summary["checked_tool_statuses"]["falsiflow.check_bundle"] == "bundle_verified"
    assert selftest_summary["checked_tool_statuses"]["falsiflow.create_evidence_todo"] == "evidence_todo_ready"

    proc = subprocess.Popen(
        [sys.executable, str(CLI), "mcp"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    def request(payload: dict[str, object]) -> dict[str, object]:
        assert proc.stdin is not None
        assert proc.stdout is not None
        proc.stdin.write(json.dumps(payload) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        assert line, "MCP server did not respond"
        return json.loads(line)

    try:
        initialized = request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert initialized["result"]["serverInfo"]["name"] == "falsiflow"
        tools = request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tool_names = {tool["name"] for tool in tools["result"]["tools"]}
        assert {"falsiflow.validate_claims", "falsiflow.check_bundle", "falsiflow.explain_blockers", "falsiflow.create_evidence_todo"} <= tool_names
        todo = request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "falsiflow.create_evidence_todo",
                "arguments": {"config": str(ROOT / "examples" / "falsiflow" / "rag_quality_gate" / "project.json")},
            },
        })
        todo_text = todo["result"]["content"][0]["text"]
        assert "evidence_todo_ready" in todo_text
        resources = request({"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}})
        resource_uris = {resource["uri"] for resource in resources["result"]["resources"]}
        assert "falsiflow://templates/local-llm-eval" in resource_uris
    finally:
        if proc.stdin is not None:
            proc.stdin.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def assert_packaged_template_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        install_dir = tmp_dir / "installed"
        work_dir = tmp_dir / "work"
        work_dir.mkdir()
        root_build_dir = ROOT / "build"
        root_egg_info = ROOT / "falsiflow.egg-info"
        root_build_dir_existed = root_build_dir.exists()
        root_egg_info_existed = root_egg_info.exists()

        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    str(ROOT),
                    "--target",
                    str(install_dir),
                    "--no-deps",
                    "--quiet",
                ],
                cwd=work_dir,
                check=True,
                capture_output=True,
                text=True,
            )
        finally:
            if not root_build_dir_existed and root_build_dir.exists():
                shutil.rmtree(root_build_dir)
            if not root_egg_info_existed and root_egg_info.exists():
                shutil.rmtree(root_egg_info)
        assert root_build_dir_existed or not root_build_dir.exists()
        assert root_egg_info_existed or not root_egg_info.exists()

        env = os.environ.copy()
        env["PYTHONPATH"] = str(install_dir)

        templates = subprocess.run(
            [sys.executable, "-m", "falsiflow.cli", "templates", "--json"],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        records = json.loads(templates.stdout)
        template_ids = {record["template"] for record in records}
        assert EXPECTED_TEMPLATE_IDS <= template_ids
        assert all("/falsiflow/templates/" in record["path"] for record in records)

        template_gallery = subprocess.run(
            [sys.executable, "-m", "falsiflow.cli", "template-gallery", "--json"],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        template_gallery_summary = json.loads(template_gallery.stdout)
        assert template_gallery_summary["status"] == "template_gallery_ready"
        assert template_gallery_summary["template_count"] == EXPECTED_TEMPLATE_COUNT
        assert template_gallery_summary["non_neural_template_count"] == EXPECTED_NON_NEURAL_TEMPLATE_COUNT

        schema = subprocess.run(
            [sys.executable, "-m", "falsiflow.cli", "schema", "--kind", "claim-summary"],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_schema = json.loads(schema.stdout)
        assert packaged_schema["title"] == "Falsiflow claim summary"

        project_dir = work_dir / "starter"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "init",
                "--template",
                "biointerface_coatings",
                "--out",
                str(project_dir),
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        assert (project_dir / "project.json").exists()
        assert (project_dir / "source_files" / "coating_raw_export.csv").exists()

        audit_dir = work_dir / "data" / "falsiflow" / "wetware_audit"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "audit",
                "--config",
                str(project_dir / "project.json"),
                "--evidence",
                str(project_dir / "evidence_pass_demo.csv"),
                "--out-dir",
                str(audit_dir),
                "--strict",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        summary = json.loads((audit_dir / "claim_summary.json").read_text(encoding="utf-8"))
        assert summary["claim_ready"] is True

        source_manifest_dir = work_dir / "source_manifest"
        source_manifest_dir.mkdir()
        subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "sources",
                "--config",
                str(project_dir / "project.json"),
                "--evidence",
                str(project_dir / "evidence_pass_demo.csv"),
                "--out",
                str(source_manifest_dir / "source_manifest.json"),
                "--report-out",
                str(source_manifest_dir / "source_manifest.md"),
                "--strict",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_source_manifest = json.loads((source_manifest_dir / "source_manifest.json").read_text(encoding="utf-8"))
        assert packaged_source_manifest["status"] == "sources_ready"

        bundle_dir = work_dir / "bundle"
        bundle_zip = work_dir / "bundle.zip"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "bundle",
                "--config",
                str(project_dir / "project.json"),
                "--evidence",
                str(project_dir / "evidence_pass_demo.csv"),
                "--out-dir",
                str(bundle_dir),
                "--zip-out",
                str(bundle_zip),
                "--strict",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_bundle = json.loads((bundle_dir / "bundle_manifest.json").read_text(encoding="utf-8"))
        assert packaged_bundle["status"] == "bundle_ready"
        assert packaged_bundle["source_file_count"] == 1
        assert bundle_zip.exists()

        packaged_bundle_verify_out = work_dir / "bundle_verify.json"
        packaged_bundle_verify_report = work_dir / "bundle_verify.md"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "verify-bundle",
                "--zip",
                str(bundle_zip),
                "--out",
                str(packaged_bundle_verify_out),
                "--report-out",
                str(packaged_bundle_verify_report),
                "--strict",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_bundle_verification = json.loads(packaged_bundle_verify_out.read_text(encoding="utf-8"))
        assert packaged_bundle_verification["status"] == "bundle_verified"
        assert packaged_bundle_verification["input_format"] == "zip"
        assert "No issues found." in packaged_bundle_verify_report.read_text(encoding="utf-8")

        packaged_claim_check_dir = project_dir / "claim_check"
        packaged_claim_check = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "claim-check",
                "--project-dir",
                str(project_dir),
                "--strict",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_claim_check_summary = json.loads(packaged_claim_check.stdout)
        assert packaged_claim_check_summary["status"] == "claim_check_ready"
        assert packaged_claim_check_summary["verification_status"] == "bundle_verified"
        packaged_claim_check_report = (packaged_claim_check_dir / "claim_check.md").read_text(encoding="utf-8")
        assert "Falsiflow Claim Check" in packaged_claim_check_report
        assert "Review Artifact Index" in packaged_claim_check_report

        packaged_quickstart_dir = work_dir / "quickstart_project"
        packaged_quickstart = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "quickstart",
                "--template",
                "wetware_support_hardware",
                "--out",
                str(packaged_quickstart_dir),
                "--strict",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_quickstart_summary = json.loads(packaged_quickstart.stdout)
        assert packaged_quickstart_summary["status"] == "quickstart_ready"
        assert packaged_quickstart_summary["claim_check_status"] == "claim_check_ready"
        assert packaged_quickstart_summary["next_commands"][0].startswith("falsiflow doctor --project-dir")
        assert "Falsiflow Quickstart" in (packaged_quickstart_dir / "quickstart_summary.md").read_text(encoding="utf-8")

        packaged_try_dir = work_dir / "try_demo"
        packaged_try = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "try",
                "--template",
                "wetware_support_hardware",
                "--out-dir",
                str(packaged_try_dir),
                "--force",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_try_summary = json.loads(packaged_try.stdout)
        assert packaged_try_summary["status"] == "try_ready"
        assert packaged_try_summary["outputs"]["launchpad"].endswith("index.html")
        assert packaged_try_summary["outputs"]["try_report"].endswith("try_report.html")
        assert packaged_try_summary["outputs"]["wizard"].endswith("falsiflow_wizard.html")
        packaged_launchpad = (packaged_try_dir / "index.html").read_text(encoding="utf-8")
        assert "Falsiflow Launchpad" in packaged_launchpad
        assert "Live Downstream PR Story" in packaged_launchpad
        assert 'property="og:title"' in packaged_launchpad
        assert 'name="twitter:card"' in packaged_launchpad
        assert "falsiflow_downstream_pr_proof_strip.svg" in packaged_launchpad
        assert "falsiflow_live_pr_story_reel.svg" in packaged_launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1" in packaged_launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990" in packaged_launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112" in packaged_launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1" in packaged_launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726360229" in packaged_launchpad
        assert "https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726392921" in packaged_launchpad
        assert "https://github.com/AzurLiu/falsiflow/pull/17" in packaged_launchpad
        assert "Falsiflow Try" in (packaged_try_dir / "try_report.html").read_text(encoding="utf-8")
        assert "Falsiflow Browser Wizard" in (packaged_try_dir / "falsiflow_wizard.html").read_text(encoding="utf-8")
        packaged_serve = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "serve",
                "--out-dir",
                str(packaged_try_dir),
                "--port",
                "0",
                "--check",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_serve_summary = json.loads(packaged_serve.stdout)
        assert packaged_serve_summary["status"] == "serve_ready"
        assert packaged_serve_summary["check_status"] == "http_ready"
        assert packaged_serve_summary["status_code"] == 200
        assert packaged_serve_summary["url"].endswith("/index.html")
        assert packaged_serve_summary["try_report_url"].endswith("/try_report.html")
        assert packaged_serve_summary["wizard_url"].endswith("/falsiflow_wizard.html")
        assert (packaged_try_dir / "serve_summary.json").exists()
        packaged_start_dir = work_dir / "start_app"
        packaged_start = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "start",
                "--out-dir",
                str(packaged_start_dir),
                "--check",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_start_summary = json.loads(packaged_start.stdout)
        assert packaged_start_summary["status"] == "serve_ready"
        assert packaged_start_summary["entry_command"] == "start"
        assert packaged_start_summary["check_status"] == "http_ready"
        assert packaged_start_summary["url"].endswith("/index.html")
        assert "Falsiflow Launchpad" in (packaged_start_dir / "index.html").read_text(encoding="utf-8")
        packaged_onboard_dir = work_dir / "onboard_app"
        packaged_onboard = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "onboard",
                "--out-dir",
                str(packaged_onboard_dir),
                "--check",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_onboard_summary = json.loads(packaged_onboard.stdout)
        assert packaged_onboard_summary["status"] == "onboard_ready"
        assert packaged_onboard_summary["start_status"] == "serve_ready"
        assert (packaged_onboard_dir / "onboard_summary.json").exists()
        packaged_static_demo_dir = work_dir / "static_demo"
        packaged_static_demo = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "static-demo",
                "--out-dir",
                str(packaged_static_demo_dir),
                "--force",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_static_demo_summary = json.loads(packaged_static_demo.stdout)
        assert packaged_static_demo_summary["status"] == "static_demo_ready"
        assert (packaged_static_demo_dir / "static_demo_summary.json").exists()
        packaged_demo_package_dir = work_dir / "public_demo"
        packaged_demo_package = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "demo-package",
                "--out-dir",
                str(packaged_demo_package_dir),
                "--force",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_demo_package_summary = json.loads(packaged_demo_package.stdout)
        assert packaged_demo_package_summary["status"] == "demo_package_ready"
        assert (packaged_demo_package_dir / "demo_package_summary.json").exists()
        assert (packaged_demo_package_dir / ".nojekyll").exists()
        packaged_demo_package_readme = (packaged_demo_package_dir / "README.md").read_text(encoding="utf-8")
        assert "live downstream PR story" in packaged_demo_package_readme
        assert "PR #1 in the downstream AI eval demo" in packaged_demo_package_readme
        packaged_publish_kit_dir = work_dir / "publish_kit"
        packaged_publish_kit = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "publish-kit",
                "--out-dir",
                str(packaged_publish_kit_dir),
                "--force",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_publish_kit_summary = json.loads(packaged_publish_kit.stdout)
        assert packaged_publish_kit_summary["status"] == "publish_kit_ready"
        assert (packaged_publish_kit_dir / "publish_handoff.json").exists()
        assert (packaged_publish_kit_dir / "external_evidence_template.json").exists()
        assert (packaged_publish_kit_dir / "public_release_evidence.json").exists()
        assert (packaged_publish_kit_dir / "public_release_evidence.md").exists()
        assert (packaged_publish_kit_dir / "release_rehearsal.json").exists()
        assert (packaged_publish_kit_dir / "release_rehearsal.md").exists()
        packaged_launch_kit_dir = work_dir / "launch_kit"
        packaged_launch_kit = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "launch-kit",
                "--out-dir",
                str(packaged_launch_kit_dir),
                "--force",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_launch_kit_summary = json.loads(packaged_launch_kit.stdout)
        assert packaged_launch_kit_summary["status"] == "launch_kit_ready"
        assert (packaged_launch_kit_dir / "launch_summary.json").exists()
        assert (packaged_launch_kit_dir / "proof_card.md").exists()
        assert (packaged_launch_kit_dir / "readme_proof_strip.svg").exists()
        assert (packaged_launch_kit_dir / "social_preview.svg").exists()
        assert (packaged_launch_kit_dir / "social_preview.png").exists()
        assert (packaged_launch_kit_dir / "github_repo_profile.md").exists()
        assert (packaged_launch_kit_dir / "launch_posts.md").exists()
        assert (packaged_launch_kit_dir / "launch_metrics.json").exists()
        assert (packaged_launch_kit_dir / "launch_metrics.md").exists()
        assert (packaged_launch_kit_dir / "publish_kit" / "public_release_evidence.md").exists()
        assert (packaged_launch_kit_dir / "publish_kit" / "release_rehearsal.md").exists()
        packaged_external_evidence_path = work_dir / "external_evidence.json"
        packaged_external_evidence = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "external-evidence",
                "--out",
                str(packaged_external_evidence_path),
                "--force",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_external_evidence_summary = json.loads(packaged_external_evidence.stdout)
        assert packaged_external_evidence_summary["status"] == "external_evidence_template_ready"
        assert packaged_external_evidence_path.exists()
        packaged_cli_reference_md = work_dir / "cli_reference.md"
        packaged_cli_reference = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "cli-reference",
                "--out",
                str(packaged_cli_reference_md),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_cli_reference_summary = json.loads(packaged_cli_reference.stdout)
        assert packaged_cli_reference_summary["status"] == "cli_reference_ready"
        packaged_commands = {record["command"] for record in packaged_cli_reference_summary["commands"]}
        assert "casebook-check" in packaged_commands
        assert "release-proof" in packaged_commands
        assert packaged_cli_reference_md.exists()
        packaged_external_check_dir = work_dir / "external_check"
        packaged_external_check = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "external-check",
                "--out-dir",
                str(packaged_external_check_dir),
                "--force",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_external_check_summary = json.loads(packaged_external_check.stdout)
        assert packaged_external_check_summary["status"] in {"external_ready", "external_blocked"}
        assert (packaged_external_check_dir / "external_readiness.json").exists()
        packaged_wizard_out = work_dir / "falsiflow_wizard.html"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "wizard",
                "--out",
                str(packaged_wizard_out),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_wizard_html = packaged_wizard_out.read_text(encoding="utf-8")
        assert "Falsiflow Browser Wizard" in packaged_wizard_html
        assert "Plain-language use case" in packaged_wizard_html

        packaged_doctor = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "doctor",
                "--project-dir",
                str(packaged_quickstart_dir),
                "--strict",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_doctor_summary = json.loads(packaged_doctor.stdout)
        assert packaged_doctor_summary["status"] == "doctor_ready"
        assert packaged_doctor_summary["claim_check_status"] == "claim_check_ready"
        assert packaged_doctor_summary["repair_checklist"][0]["command"].startswith("falsiflow claim-check")
        assert "Falsiflow Doctor" in (packaged_quickstart_dir / "doctor" / "doctor_summary.md").read_text(encoding="utf-8")

        packaged_adoption_check_dir = work_dir / "adoption_check"
        packaged_adoption_check = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "adoption-check",
                "--out-dir",
                str(packaged_adoption_check_dir),
                "--skip-dist",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_adoption_summary = json.loads(packaged_adoption_check.stdout)
        assert packaged_adoption_summary["status"] == "adoption_ready"
        assert packaged_adoption_summary["release_validation_status"] == "release_validation_skipped"
        assert packaged_adoption_summary["casebook_check_status"] == "casebook_check_ready"
        assert packaged_adoption_summary["ready_priority_count"] == 5
        assert packaged_adoption_summary["repair_checklist"][0]["command"].startswith("falsiflow adoption-check")
        packaged_adoption_report = (packaged_adoption_check_dir / "adoption_check.md").read_text(encoding="utf-8")
        assert "Falsiflow Adoption Check" in packaged_adoption_report
        assert "Repair Checklist" in packaged_adoption_report

        portfolio_dir = work_dir / "portfolio_default"
        subprocess.run(
            [sys.executable, "-m", "falsiflow.cli", "portfolio", "--out-dir", str(portfolio_dir), "--strict"],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        portfolio = json.loads((portfolio_dir / "portfolio_summary.json").read_text(encoding="utf-8"))
        assert portfolio["claim_count"] == 1
        assert portfolio["ready_count"] == 1
        assert portfolio["project_validation_error_count"] == 0
        assert portfolio["project_validation_warning_count"] == 0
        assert portfolio["evidence_error_count"] == 0
        assert portfolio["evidence_warning_count"] == 0

        selftest_dir = work_dir / "selftest"
        selftest = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "selftest",
                "--json",
                "--out-dir",
                str(selftest_dir),
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        selftest_summary = json.loads(selftest.stdout)
        assert selftest_summary["status"] == "passed"
        assert selftest_summary["template_count"] == EXPECTED_TEMPLATE_COUNT
        assert selftest_summary["audit_ready_count"] == EXPECTED_TEMPLATE_COUNT
        assert selftest_summary["failure_count"] == 0
        assert (selftest_dir / "portfolio" / "portfolio_summary.json").exists()

        demo_dir = work_dir / "demo"
        demo = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "demo",
                "--out-dir",
                str(demo_dir),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        demo_summary = json.loads(demo.stdout)
        assert demo_summary["status"] == "demo_ready"
        assert demo_summary["verification_status"] == "bundle_verified"
        assert (demo_dir / "demo_summary.json").exists()

        template_check_dir = work_dir / "template_check"
        template_check = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "template-check",
                "--template-dir",
                str(project_dir),
                "--out-dir",
                str(template_check_dir),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        template_check_summary = json.loads(template_check.stdout)
        assert template_check_summary["status"] == "template_ready"
        assert template_check_summary["pass_claim_ready"] is True
        assert template_check_summary["placeholder_claim_ready"] is False
        assert template_check_summary["verification_status"] == "bundle_verified"
        assert (template_check_dir / "template_check.json").exists()

        generated_template_dir = work_dir / "generated_template"
        generated_template_check_dir = work_dir / "generated_template_check"
        generated_template = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "template-scaffold",
                "--out",
                str(generated_template_dir),
                "--template-id",
                "packaged_generated_template",
                "--claim-statement",
                "Packaged generated template claim.",
                "--gate",
                "gate_a:score,replicate_score",
                "--rule",
                "gate_a:score:>=:1:Score threshold.",
                "--check-out-dir",
                str(generated_template_check_dir),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        generated_template_summary = json.loads(generated_template.stdout)
        assert generated_template_summary["status"] == "template_scaffolded"
        assert generated_template_summary["template_check_status"] == "template_ready"
        assert (generated_template_dir / "template.json").exists()
        assert (generated_template_check_dir / "template_check.json").exists()

        packaged_template_pack_dir = work_dir / "template_pack"
        packaged_template_pack_zip = work_dir / "template_pack.zip"
        packaged_template_pack_verify = work_dir / "template_pack_verify.json"
        packaged_template_pack_report = work_dir / "template_pack_verify.md"
        packaged_template_pack = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "template-pack",
                "--template-dir",
                str(generated_template_dir),
                "--out-dir",
                str(packaged_template_pack_dir),
                "--zip-out",
                str(packaged_template_pack_zip),
                "--verify-out",
                str(packaged_template_pack_verify),
                "--report-out",
                str(packaged_template_pack_report),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_template_pack_summary = json.loads(packaged_template_pack.stdout)
        assert packaged_template_pack_summary["status"] == "template_pack_ready"
        assert packaged_template_pack_summary["verification_status"] == "template_pack_verified"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "verify-template-pack",
                "--zip",
                str(packaged_template_pack_zip),
                "--strict",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

        packaged_installed_templates = work_dir / "installed_templates"
        packaged_install_check = work_dir / "installed_template_check"
        packaged_template_install = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "template-install",
                "--zip",
                str(packaged_template_pack_zip),
                "--templates-dir",
                str(packaged_installed_templates),
                "--check-out-dir",
                str(packaged_install_check),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_template_install_summary = json.loads(packaged_template_install.stdout)
        assert packaged_template_install_summary["status"] == "template_installed"
        assert packaged_template_install_summary["template_id"] == "packaged_generated_template"
        packaged_registry = work_dir / "template_registry.json"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "template-registry",
                "--pack-zip",
                str(packaged_template_pack_zip),
                "--base-url",
                work_dir.as_uri(),
                "--out",
                str(packaged_registry),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_lock = work_dir / "falsiflow_template_lock.json"
        packaged_template_lock = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "template-lock",
                "--registry",
                str(packaged_registry),
                "--template",
                "packaged_generated_template",
                "--version",
                "0.1.0",
                "--out",
                str(packaged_lock),
                "--cache-dir",
                str(work_dir / "template_source_cache"),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_template_lock_summary = json.loads(packaged_template_lock.stdout)
        assert packaged_template_lock_summary["status"] == "template_locked"
        assert packaged_template_lock_summary["source_type"] == "url"
        assert packaged_template_lock_summary["source_url"].startswith("file:")
        packaged_attestation = work_dir / "falsiflow_template_lock.attestation.json"
        packaged_template_attestation = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "template-attest",
                "--subject",
                str(packaged_lock),
                "--subject-type",
                "template-lock",
                "--out",
                str(packaged_attestation),
                "--builder",
                "packaged-regression",
                "--key-id",
                "packaged-regression-key",
                "--signing-key",
                "packaged-regression-secret",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_template_attestation_summary = json.loads(packaged_template_attestation.stdout)
        assert packaged_template_attestation_summary["status"] == "template_attested"
        assert packaged_template_attestation_summary["signature_type"] == "hmac-sha256"
        packaged_template_attestation_verification = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "verify-template-attestation",
                "--attestation",
                str(packaged_attestation),
                "--subject",
                str(packaged_lock),
                "--signing-key",
                "packaged-regression-secret",
                "--strict",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_template_attestation_verification_summary = json.loads(packaged_template_attestation_verification.stdout)
        assert packaged_template_attestation_verification_summary["status"] == "template_attestation_verified"
        packaged_policy = work_dir / "falsiflow_template_policy.json"
        packaged_template_policy = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "template-policy",
                "--lock",
                str(packaged_lock),
                "--attestation",
                str(packaged_attestation),
                "--out",
                str(packaged_policy),
                "--policy-id",
                "packaged-regression-policy",
                "--owner",
                "packaged-regression",
                "--signing-key",
                "packaged-regression-secret",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_template_policy_summary = json.loads(packaged_template_policy.stdout)
        assert packaged_template_policy_summary["status"] == "template_policy_ready"
        packaged_template_policy_verification = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "verify-template-policy",
                "--policy",
                str(packaged_policy),
                "--lock",
                str(packaged_lock),
                "--attestation",
                str(packaged_attestation),
                "--signing-key",
                "packaged-regression-secret",
                "--strict",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_template_policy_verification_summary = json.loads(packaged_template_policy_verification.stdout)
        assert packaged_template_policy_verification_summary["status"] == "template_policy_verified"
        packaged_release = work_dir / "falsiflow_template_release.zip"
        packaged_template_release = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "template-release",
                "--pack-zip",
                str(packaged_template_pack_zip),
                "--registry",
                str(packaged_registry),
                "--lock",
                str(packaged_lock),
                "--attestation",
                str(packaged_attestation),
                "--policy",
                str(packaged_policy),
                "--out",
                str(packaged_release),
                "--signing-key",
                "packaged-regression-secret",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_template_release_summary = json.loads(packaged_template_release.stdout)
        assert packaged_template_release_summary["status"] == "template_release_ready"
        packaged_release_verification_report = work_dir / "falsiflow_template_release_verification.md"
        packaged_template_release_verification = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "verify-template-release",
                "--release",
                str(packaged_release),
                "--signing-key",
                "packaged-regression-secret",
                "--report-out",
                str(packaged_release_verification_report),
                "--strict",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_template_release_verification_summary = json.loads(packaged_template_release_verification.stdout)
        assert packaged_template_release_verification_summary["status"] == "template_release_verified"
        assert "Falsiflow Template Release Verification" in packaged_release_verification_report.read_text(encoding="utf-8")
        packaged_locked_templates = work_dir / "locked_templates"
        packaged_locked_install = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "template-install",
                "--lock",
                str(packaged_lock),
                "--attestation",
                str(packaged_attestation),
                "--signing-key",
                "packaged-regression-secret",
                "--require-attestation",
                "--policy",
                str(packaged_policy),
                "--templates-dir",
                str(packaged_locked_templates),
                "--cache-dir",
                str(work_dir / "template_install_cache"),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_locked_install_summary = json.loads(packaged_locked_install.stdout)
        assert packaged_locked_install_summary["status"] == "template_installed"
        assert packaged_locked_install_summary["lock_status"] == "template_locked"
        assert packaged_locked_install_summary["attestation_status"] == "template_attestation_verified"
        assert packaged_locked_install_summary["attestation_signature_verified"] is True
        assert packaged_locked_install_summary["policy_status"] == "template_policy_verified"
        packaged_release_templates = work_dir / "release_templates"
        packaged_release_install = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "template-install",
                "--release",
                str(packaged_release),
                "--signing-key",
                "packaged-regression-secret",
                "--templates-dir",
                str(packaged_release_templates),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_release_install_summary = json.loads(packaged_release_install.stdout)
        assert packaged_release_install_summary["status"] == "template_installed"
        assert packaged_release_install_summary["release_status"] == "template_release_verified"
        packaged_templates = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "templates",
                "--template-root",
                str(packaged_installed_templates),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        packaged_template_records = json.loads(packaged_templates.stdout)
        assert packaged_template_records[0]["template"] == "packaged_generated_template"
        packaged_installed_project = work_dir / "installed_project"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "init",
                "--template",
                "packaged_generated_template",
                "--template-root",
                str(packaged_installed_templates),
                "--out",
                str(packaged_installed_project),
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        assert (packaged_installed_project / "project.json").exists()

        release_check_dir = work_dir / "release_check"
        release_check = subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "release-check",
                "--out-dir",
                str(release_check_dir),
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        release_check_summary = json.loads(release_check.stdout)
        assert release_check_summary["status"] == "release_ready"
        assert release_check_summary["package_status"] == "package_ready"
        assert release_check_summary["package_failure_count"] == 0
        assert release_check_summary["dist_status"] == "dist_skipped"
        assert release_check_summary["release_validation_status"] == "release_validation_skipped"
        assert "Distribution validation was skipped" in release_check_summary["release_validation_message"]
        assert release_check_summary["demo_status"] == "demo_ready"
        assert release_check_summary["quickstart_status"] == "quickstart_ready"
        assert release_check_summary["quickstart_summary"]["claim_check_status"] == "claim_check_ready"
        assert release_check_summary["quickstart_summary"]["next_commands"][0].startswith("falsiflow doctor --project-dir")
        assert release_check_summary["doctor_status"] == "doctor_ready"
        assert release_check_summary["doctor_summary"]["verification_status"] == "bundle_verified"
        assert release_check_summary["doctor_summary"]["repair_checklist"][0]["command"].startswith("falsiflow claim-check")
        assert release_check_summary["claim_check_status"] == "claim_check_ready"
        assert release_check_summary["claim_check_summary"]["verification_status"] == "bundle_verified"
        assert release_check_summary["downstream_smoke_replay_status"] == "downstream_smoke_replay_skipped"
        assert release_check_summary["downstream_smoke_replay_summary"]["checks"][0]["check"] == "downstream_smoke_replay_skipped"
        assert release_check_summary["adoption_check_status"] == "adoption_ready"
        assert release_check_summary["adoption_check_summary"]["release_validation_status"] == "release_validation_skipped"
        assert release_check_summary["adoption_check_summary"]["ready_priority_count"] == 5
        assert "adoption_recheck" in release_check_summary["adoption_check_summary"]["repair_checklist"][0]["command"]
        assert release_check_summary["adoption_check_summary"]["repair_checklist"][0]["expected_artifact"].endswith("adoption_check.json")
        packaged_release_priority = next(priority for priority in release_check_summary["adoption_check_summary"]["priorities"] if priority["priority_id"] == "release_and_distribution")
        packaged_release_checks = {check["check"]: check for check in packaged_release_priority["checks"]}
        assert packaged_release_checks["gitignore_build_artifacts"]["status"] == "passed"
        assert packaged_release_checks["source_build_cache_cleanup"]["status"] == "passed"
        assert release_check_summary["template_gallery_status"] == "template_gallery_ready"
        assert release_check_summary["template_gallery_summary"]["template_count"] == EXPECTED_TEMPLATE_COUNT
        assert release_check_summary["casebook_check_status"] == "casebook_check_ready"
        assert release_check_summary["casebook_check_summary"]["blocked_path_count"] == EXPECTED_TEMPLATE_COUNT
        assert release_check_summary["template_check_ready_count"] == EXPECTED_TEMPLATE_COUNT
        assert release_check_summary["template_pack_status"] == "template_pack_ready"
        assert release_check_summary["template_pack_verification_status"] == "template_pack_verified"
        assert release_check_summary["template_registry_status"] == "template_registry_ready"
        assert release_check_summary["template_lock_status"] == "template_locked"
        assert release_check_summary["template_lock_summary"]["source_type"] == "url"
        assert release_check_summary["template_attestation_status"] == "template_attested"
        assert release_check_summary["template_attestation_verification_status"] == "template_attestation_verified"
        assert release_check_summary["template_policy_status"] == "template_policy_ready"
        assert release_check_summary["template_policy_verification_status"] == "template_policy_verified"
        assert release_check_summary["template_release_status"] == "template_release_ready"
        assert release_check_summary["template_release_verification_status"] == "template_release_verified"
        assert release_check_summary["template_install_status"] == "template_installed"
        assert release_check_summary["template_install_summary"]["attestation_status"] == "template_attestation_verified"
        assert release_check_summary["template_install_summary"]["policy_status"] == "template_policy_verified"
        assert release_check_summary["template_install_summary"]["release_status"] == "template_release_verified"
        assert release_check_summary["bundle_verified_count"] == EXPECTED_TEMPLATE_COUNT
        assert (release_check_dir / "release_check.json").exists()
        assert (release_check_dir / "adoption_check.json").exists()
        assert (release_check_dir / "adoption_check.md").exists()
        assert (release_check_dir / "quickstart_project" / "quickstart_summary.json").exists()
        assert (release_check_dir / "doctor" / "doctor_summary.json").exists()
        assert (release_check_dir / "claim_check" / "claim_check.json").exists()
        assert (release_check_dir / "template_gallery.md").exists()
        assert (release_check_dir / "casebook_check" / "casebook_check.md").exists()
        installed_release_report = (release_check_dir / "release_check.md").read_text(encoding="utf-8")
        assert "Adoption Repair Checklist" in installed_release_report
        assert "Release validation: `release_validation_skipped`" in installed_release_report
        assert "Adoption release validation: `release_validation_skipped`" in installed_release_report
        assert "Adoption Priority Evidence" in installed_release_report
        assert "source_build_cache_cleanup" in installed_release_report
        assert "Distribution hygiene is verified by full release-check" in installed_release_report
        assert "adoption_recheck" in installed_release_report

        scaffold_dir = work_dir / "custom_scaffold"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "scaffold",
                "--out",
                str(scaffold_dir),
                "--project-id",
                "packaged_custom_project",
                "--claim-id",
                "packaged_custom_claim",
                "--claim-statement",
                "Packaged scaffold contract claim.",
                "--gate",
                "gate_a:score,replicate_score",
                "--rule",
                "gate_a:score:>=:1:Score threshold.",
                "--json",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        (scaffold_dir / "source_files" / "raw_export.csv").write_text("row_id,value\nsource,packaged\n", encoding="utf-8")
        fill_ready_evidence_template(scaffold_dir / "evidence_template.csv")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "falsiflow.cli",
                "audit",
                "--config",
                str(scaffold_dir / "project.json"),
                "--evidence",
                str(scaffold_dir / "evidence_template.csv"),
                "--out-dir",
                str(work_dir / "custom_scaffold_audit"),
                "--strict",
            ],
            cwd=work_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )


def assert_template_mirror_contract() -> None:
    example_files = relative_files(EXAMPLE_TEMPLATE_ROOT)
    package_files = relative_files(PACKAGE_TEMPLATE_ROOT)
    assert example_files == package_files
    for relative_path in example_files:
        example_bytes = (EXAMPLE_TEMPLATE_ROOT / relative_path).read_bytes()
        package_bytes = (PACKAGE_TEMPLATE_ROOT / relative_path).read_bytes()
        assert example_bytes == package_bytes, f"template mirror drifted: {relative_path}"


def main() -> int:
    project = load_project(PROJECT_PATH)
    assert_template_mirror_contract()
    assert_blocked_blank(project)
    assert_blocked_placeholder(project)
    assert_passes(project)
    assert_derived_rule_failure(project)
    assert_evidence_diagnostics_contract(project)
    assert_evidence_csv_format_contract(project)
    assert_config_validation_contract()
    assert_schema_contract()
    assert_adoption_repair_checklist_contract()
    assert_project_validation_blocks_claim()
    assert_cli_contract()
    assert_scaffold_contract()
    assert_limina_adapter_contract()
    assert_rule_filter_contract()
    assert_wide_ingest_contract()
    assert_eval_artifact_import_contract()
    assert_mcp_server_contract()
    assert_packaged_template_contract()
    print("Falsiflow regression passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
