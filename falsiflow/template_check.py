"""Starter template validation workflow for Falsiflow."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

from .bundle import (
    build_bundle,
    markdown_cell,
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
from .release import release_check_item


def safe_template_child_path(template_dir: Path, raw_path: object, default: str) -> Path | None:
    text = str(raw_path or default).strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        return None
    return template_dir / path


def render_template_check_report(summary: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Template Check",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Template: `{summary.get('template_id', '')}`",
        f"- Manifest: `{summary.get('manifest_status', '')}`",
        f"- Project validation: `{summary.get('validation_status', '')}`",
        f"- Pass audit: `{summary.get('pass_audit_status', '')}` claim_ready={str(bool(summary.get('pass_claim_ready'))).lower()}",
        f"- Placeholder audit: `{summary.get('placeholder_audit_status', '')}` claim_ready={str(bool(summary.get('placeholder_claim_ready'))).lower()}",
        f"- Sources: `{summary.get('source_status', '')}`",
        f"- Bundle: `{summary.get('bundle_status', '')}`",
        f"- Verification: `{summary.get('verification_status', '')}`",
        f"- Failures: {summary.get('failure_count', 0)}",
        "",
        "## Checks",
        "",
        "| Check | Status | Path | Message |",
        "| --- | --- | --- | --- |",
    ]
    for check in summary.get("checks", []):
        if not isinstance(check, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(check.get("check", "")),
                markdown_cell(check.get("status", "")),
                markdown_cell(check.get("path", "")),
                markdown_cell(check.get("message", "")),
            ])
            + " |"
        )
    return "\n".join(lines) + "\n"


def run_template_check(template_dir: Path, artifact_root: Path, force: bool = False) -> dict[str, object]:
    if artifact_root.exists() and any(artifact_root.iterdir()):
        if not force:
            raise SystemExit(f"Refusing to write template check into non-empty directory without --force: {artifact_root}")
        shutil.rmtree(artifact_root)
    artifact_root.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    def add(check_id: str, ok: bool, message: str, path: Path | str = "") -> None:
        item = release_check_item(check_id, ok, message, path)
        checks.append(item)
        if not ok:
            failures.append(item)

    template_dir = template_dir.resolve()
    manifest_path = template_dir / "template.json"
    manifest: dict[str, object] = {}
    manifest_status = "missing"
    template_id = template_dir.name
    project_config_path: Path | None = None
    pass_evidence_path: Path | None = None
    placeholder_evidence_path: Path | None = None
    validation_status = "not_run"
    pass_audit_status = "not_run"
    pass_claim_ready = False
    placeholder_audit_status = "not_run"
    placeholder_claim_ready = False
    source_status = "not_run"
    bundle_status = "not_run"
    verification_status = "not_run"
    claim_summary_path = ""

    add("template_dir_exists", template_dir.exists() and template_dir.is_dir(), "Template directory exists.", template_dir)
    add("template_manifest_exists", manifest_path.exists(), "template.json exists.", manifest_path)
    if manifest_path.exists():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                manifest = loaded
                manifest_status = "present"
            else:
                manifest_status = "invalid_object"
                add("template_manifest_object", False, "template.json must contain a JSON object.", manifest_path)
        except json.JSONDecodeError as exc:
            manifest_status = "invalid_json"
            add("template_manifest_json", False, f"template.json is not valid JSON: {exc}", manifest_path)

    if manifest:
        template_id = str(manifest.get("id") or template_dir.name)
        for field in ["id", "name", "domain", "description", "project_config", "demo_evidence", "placeholder_evidence"]:
            add(f"template_manifest_field:{field}", bool(str(manifest.get(field, "")).strip()), f"template.json declares `{field}`.", manifest_path)

    for field, default in [
        ("project_config", "project.json"),
        ("demo_evidence", "evidence_pass_demo.csv"),
        ("placeholder_evidence", "evidence_placeholder_demo.csv"),
    ]:
        path = safe_template_child_path(template_dir, manifest.get(field), default)
        add(f"template_manifest_path_safe:{field}", path is not None, f"`{field}` stays inside the template directory.", manifest_path)
        if field == "project_config":
            project_config_path = path
        elif field == "demo_evidence":
            pass_evidence_path = path
        else:
            placeholder_evidence_path = path

    source_dir = template_dir / "source_files"
    source_files = [path for path in sorted(source_dir.rglob("*")) if path.is_file()] if source_dir.exists() else []
    add("template_source_dir", source_dir.exists() and source_dir.is_dir(), "source_files/ directory exists.", source_dir)
    add("template_source_files", bool(source_files), "source_files/ includes at least one source artifact.", source_dir)

    project: dict[str, object] | None = None
    if project_config_path is None:
        add("project_config_path", False, "Project config path is missing or unsafe.", manifest_path)
    else:
        add("project_config_exists", project_config_path.exists(), "Project config file exists.", project_config_path)
        if project_config_path.exists():
            try:
                project = load_project(project_config_path)
                validation = validate_project_config(project)
                validation_status = str(validation.get("status", ""))
                (artifact_root / "project_validation.json").write_text(json.dumps(validation, indent=2, sort_keys=True), encoding="utf-8")
                add("project_config_valid", bool(validation.get("valid")), "Project config validates with zero errors.", project_config_path)
            except (OSError, json.JSONDecodeError) as exc:
                validation_status = "invalid"
                add("project_config_readable", False, f"Could not read project config: {exc}", project_config_path)

    for check_id, path, message in [
        ("pass_evidence_exists", pass_evidence_path, "Passing demo evidence exists."),
        ("placeholder_evidence_exists", placeholder_evidence_path, "Placeholder demo evidence exists."),
    ]:
        add(check_id, bool(path and path.exists()), message, path or manifest_path)

    pass_rows: list[dict[str, str]] = []
    pass_issues: list[dict[str, object]] = []
    if project is not None and pass_evidence_path is not None and pass_evidence_path.exists():
        pass_rows, pass_issues = read_csv_rows_with_diagnostics(pass_evidence_path)
        rendered = write_render_artifacts(project, pass_rows, artifact_root / "pass_audit", evidence_file_issues=pass_issues)
        pass_audit = rendered["audit"]
        pass_audit_status = str(pass_audit.get("status", ""))
        pass_claim_ready = bool(pass_audit.get("claim_ready"))
        claim_summary_path = str(artifact_root / "pass_audit" / "claim_summary.json")
        add("pass_demo_claim_ready", pass_claim_ready, "Passing demo evidence makes the claim ready.", pass_evidence_path)

        manifest = source_manifest(project, pass_rows, pass_issues)
        source_status = str(manifest.get("status", ""))
        (artifact_root / "source_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        (artifact_root / "source_manifest.md").write_text(render_source_manifest_report(manifest), encoding="utf-8")
        add("pass_source_manifest_ready", source_status == "sources_ready", "Passing demo evidence has complete source provenance.", artifact_root / "source_manifest.json")

        bundle_dir = artifact_root / "bundle"
        bundle_zip = artifact_root / "bundle.zip"
        bundle = build_bundle(project_config_path, pass_evidence_path, bundle_dir, bundle_zip, force=True)
        bundle_status = str(bundle.get("status", ""))
        add("pass_bundle_ready", bundle_status == "bundle_ready", "Passing demo evidence builds a ready bundle.", bundle_dir / "bundle_manifest.json")

        verification = verify_bundle_zip(bundle_zip)
        verification_status = str(verification.get("status", ""))
        (artifact_root / "bundle_verification.json").write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")
        (artifact_root / "bundle_verification.md").write_text(render_bundle_verification_report(verification), encoding="utf-8")
        add("pass_bundle_verified", verification_status == "bundle_verified", "Passing demo bundle verifies from zip.", artifact_root / "bundle_verification.json")

    if project is not None and placeholder_evidence_path is not None and placeholder_evidence_path.exists():
        placeholder_rows, placeholder_issues = read_csv_rows_with_diagnostics(placeholder_evidence_path)
        rendered = write_render_artifacts(project, placeholder_rows, artifact_root / "placeholder_audit", evidence_file_issues=placeholder_issues)
        placeholder_audit = rendered["audit"]
        placeholder_audit_status = str(placeholder_audit.get("status", ""))
        placeholder_claim_ready = bool(placeholder_audit.get("claim_ready"))
        add("placeholder_demo_blocks_claim", not placeholder_claim_ready, "Placeholder demo evidence must not make the claim ready.", placeholder_evidence_path)

    summary: dict[str, object] = {
        "status": "template_ready" if not failures else "template_blocked",
        "template_id": template_id,
        "template_dir": str(template_dir),
        "artifact_root": str(artifact_root),
        "manifest_status": manifest_status,
        "manifest_path": str(manifest_path),
        "project_config_path": str(project_config_path or ""),
        "pass_evidence_path": str(pass_evidence_path or ""),
        "placeholder_evidence_path": str(placeholder_evidence_path or ""),
        "validation_status": validation_status,
        "pass_audit_status": pass_audit_status,
        "pass_claim_ready": pass_claim_ready,
        "placeholder_audit_status": placeholder_audit_status,
        "placeholder_claim_ready": placeholder_claim_ready,
        "source_status": source_status,
        "bundle_status": bundle_status,
        "verification_status": verification_status,
        "claim_summary_path": claim_summary_path,
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
    }
    (artifact_root / "template_check.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (artifact_root / "template_check.md").write_text(render_template_check_report(summary), encoding="utf-8")
    return summary
