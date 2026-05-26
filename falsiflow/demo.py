"""Local verified demo workflow for bundled starter templates."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

from .bundle import (
    build_bundle,
    render_bundle_verification_report,
    render_source_manifest_report,
    source_manifest,
    verify_bundle_zip,
)
from .core import (
    load_project,
    read_csv_rows_with_diagnostics,
    validate_project_config,
    write_render_artifacts,
)
from .template_discovery import template_path


def run_demo(template: str, out_dir: Path, force: bool = False) -> dict[str, object]:
    source = template_path(template)
    if source is None:
        raise SystemExit(f"Unknown template `{template}`. Run `falsiflow templates` to list available templates.")
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"Refusing to overwrite non-empty demo directory without --force: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    project_dir = out_dir / template
    shutil.copytree(source, project_dir)
    config_path = project_dir / "project.json"
    evidence_path = project_dir / "evidence_pass_demo.csv"
    validation_path = out_dir / "project_validation.json"
    audit_dir = out_dir / "audit"
    source_manifest_path = out_dir / "source_manifest.json"
    source_report_path = out_dir / "source_manifest.md"
    bundle_dir = out_dir / "evidence_bundle"
    bundle_zip = out_dir / "evidence_bundle.zip"
    verification_json = out_dir / "evidence_bundle_verify.json"
    verification_report = out_dir / "evidence_bundle_verify.md"

    steps: list[dict[str, object]] = []
    project = load_project(config_path)
    validation = validate_project_config(project)
    validation_path.write_text(json.dumps(validation, indent=2, sort_keys=True), encoding="utf-8")
    steps.append({"step": "validate", "status": validation.get("status", ""), "path": str(validation_path)})

    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(evidence_path)
    rendered = write_render_artifacts(project, evidence_rows, audit_dir, evidence_file_issues=evidence_issues)
    audit = rendered["audit"]
    steps.append({"step": "audit", "status": audit.get("status", ""), "path": str(audit_dir / "claim_audit.json")})

    manifest = source_manifest(project, evidence_rows, evidence_issues)
    source_manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    source_report_path.write_text(render_source_manifest_report(manifest), encoding="utf-8")
    steps.append({"step": "sources", "status": manifest.get("status", ""), "path": str(source_manifest_path)})

    bundle = build_bundle(config_path, evidence_path, bundle_dir, bundle_zip, force=True)
    steps.append({"step": "bundle", "status": bundle.get("status", ""), "path": str(bundle_dir / "bundle_manifest.json")})

    verification = verify_bundle_zip(bundle_zip)
    verification_json.write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")
    verification_report.write_text(render_bundle_verification_report(verification), encoding="utf-8")
    steps.append({"step": "verify-bundle", "status": verification.get("status", ""), "path": str(verification_json)})

    demo_ready = (
        validation.get("valid") is True
        and audit.get("claim_ready") is True
        and manifest.get("status") == "sources_ready"
        and bundle.get("status") == "bundle_ready"
        and verification.get("status") == "bundle_verified"
    )
    summary: dict[str, object] = {
        "status": "demo_ready" if demo_ready else "demo_blocked",
        "template": template,
        "artifact_root": str(out_dir),
        "project_dir": str(project_dir),
        "validation_status": validation.get("status", ""),
        "audit_status": audit.get("status", ""),
        "claim_ready": bool(audit.get("claim_ready")),
        "source_status": manifest.get("status", ""),
        "bundle_status": bundle.get("status", ""),
        "verification_status": verification.get("status", ""),
        "issue_count": int(validation.get("error_count", 0))
        + int(audit.get("evidence_error_count", 0))
        + int(manifest.get("blocker_count", 0))
        + int(verification.get("issue_count", 0)),
        "steps": steps,
        "project_validation": str(validation_path),
        "claim_audit": str(audit_dir / "claim_audit.json"),
        "source_manifest": str(source_manifest_path),
        "bundle_manifest": str(bundle_dir / "bundle_manifest.json"),
        "bundle_zip": str(bundle_zip),
        "bundle_verification": str(verification_json),
        "bundle_verification_report": str(verification_report),
    }
    (out_dir / "demo_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary
