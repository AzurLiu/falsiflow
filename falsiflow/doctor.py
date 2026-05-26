"""Project diagnosis workflow for Falsiflow."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil

from .bundle import markdown_cell
from .claim_check import run_claim_check
from .core import load_project, read_csv_rows_with_diagnostics, validate_project_config
from .release import failure_record, release_check_item


def prepare_output_directory(path: Path, label: str, force: bool = False) -> None:
    if path.exists() and any(path.iterdir()):
        if not force:
            raise SystemExit(f"Refusing to overwrite non-empty {label} without --force: {path}")
        resolved = path.resolve()
        protected = {Path.cwd().resolve(), Path.home().resolve(), Path("/").resolve()}
        if resolved in protected:
            raise SystemExit(f"Refusing to remove protected {label}: {path}")
        shutil.rmtree(path)
    path.parent.mkdir(parents=True, exist_ok=True)


def default_project_evidence_path(project_dir: Path) -> Path:
    for name in ["evidence_pass_demo.csv", "evidence.csv", "evidence_template.csv"]:
        candidate = project_dir / name
        if candidate.exists():
            return candidate
    return project_dir / "evidence_pass_demo.csv"


def doctor_next_actions(
    project_exists: bool,
    evidence_exists: bool,
    project_status: str,
    evidence_error_count: int,
    claim_check: dict[str, object],
) -> list[dict[str, object]]:
    raw_actions = claim_check.get("next_actions", [])
    if isinstance(raw_actions, list) and raw_actions:
        actions: list[dict[str, object]] = []
        for raw_action in raw_actions[:5]:
            if not isinstance(raw_action, dict):
                continue
            action = dict(raw_action)
            action.setdefault("rank", len(actions) + 1)
            action.setdefault("action_id", f"claim_action_{len(actions) + 1}")
            action.setdefault("why", "Claim check reported this as the next repair.")
            actions.append(action)
        if actions:
            return actions

    action_id = "human_release_review"
    why = "Review doctor_summary, claim_check, audit_review, source_manifest, and bundle verification before relying on the claim."
    if not project_exists:
        action_id = "add_project_config"
        why = "Create or point --config at a Falsiflow project.json file."
    elif not evidence_exists:
        action_id = "add_evidence_file"
        why = "Create or point --evidence at the evidence CSV for this project."
    elif project_status != "valid":
        action_id = "fix_project_config_diagnostics"
        why = "Open project_validation.json and fix project config errors before rerunning doctor."
    elif evidence_error_count:
        action_id = "fix_evidence_file_diagnostics"
        why = "Open evidence_diagnostics.json and fix evidence CSV errors before rerunning doctor."
    return [{"rank": 1, "action_id": action_id, "why": why}]


def doctor_repair_checklist(
    next_actions: list[dict[str, object]],
    config: Path,
    evidence: Path,
    out_dir: Path,
) -> list[dict[str, object]]:
    checklist: list[dict[str, object]] = []

    def command_for(action_id: str) -> tuple[str, str, str]:
        if action_id == "add_project_config":
            return (
                f"falsiflow init --template neural_materials --out {config.parent}",
                str(config),
                "Project config exists, then doctor can validate it.",
            )
        if action_id == "add_evidence_file":
            return (
                f"falsiflow render --config {config} --out-dir {out_dir / 'blank_audit'}",
                str(evidence),
                "Evidence CSV exists, then doctor can parse and gate it.",
            )
        if action_id == "fix_project_config_diagnostics":
            return (
                f"falsiflow validate --config {config} --strict",
                str(out_dir / "project_validation.json"),
                "Validation reruns with zero project config errors.",
            )
        if action_id == "fix_evidence_file_diagnostics":
            return (
                f"falsiflow doctor --config {config} --evidence {evidence} --out-dir {out_dir} --strict --force",
                str(out_dir / "evidence_diagnostics.json"),
                "Doctor reruns with evidence_error_count=0.",
            )
        if action_id == "repair_source_provenance":
            return (
                f"falsiflow sources --config {config} --evidence {evidence} --out {out_dir / 'source_manifest.json'} --report-out {out_dir / 'source_manifest.md'} --strict",
                str(out_dir / "source_manifest.json"),
                "Source manifest reports sources_ready.",
            )
        if action_id.startswith("fill_"):
            return (
                f"falsiflow next --config {config} --evidence {evidence} --out-dir {out_dir / 'next'}",
                str(out_dir / "next" / "next_actions.json"),
                "Fill the listed evidence rows, then rerun doctor until claim_check_ready.",
            )
        if action_id in {"resolve_bundle_blockers", "repair_bundle_verification"}:
            return (
                f"falsiflow claim-check --config {config} --evidence {evidence} --out-dir {out_dir / 'claim_check'} --strict --force",
                str(out_dir / "claim_check" / "claim_check.json"),
                "Claim check reports claim_check_ready and bundle_verified.",
            )
        return (
            f"falsiflow claim-check --config {config} --evidence {evidence} --out-dir {out_dir / 'claim_check'} --strict --force",
            str(out_dir / "claim_check" / "claim_check.md"),
            "Human review confirms claim wording, source files, and bundle verification.",
        )

    for index, action in enumerate(next_actions, start=1):
        action_id = str(action.get("action_id", f"doctor_action_{index}"))
        command, expected_artifact, success_signal = command_for(action_id)
        checklist.append({
            "rank": int(action.get("rank", index) or index),
            "action_id": action_id,
            "why": str(action.get("why", "")),
            "command": command,
            "expected_artifact": expected_artifact,
            "success_signal": success_signal,
        })
    return checklist


def render_doctor_report(summary: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Doctor",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Project: `{summary.get('project_dir', '')}`",
        f"- Config: `{summary.get('config_path', '')}`",
        f"- Evidence: `{summary.get('evidence_path', '')}`",
        f"- Project config: `{summary.get('project_status', '')}`",
        f"- Evidence file: `{summary.get('evidence_status', '')}`",
        f"- Claim check: `{summary.get('claim_check_status', '')}`",
        f"- Claim ready: `{str(bool(summary.get('claim_ready'))).lower()}`",
        f"- Audit review: `{summary.get('audit_review_status', '')}`",
        f"- Sources: `{summary.get('source_status', '')}`",
        f"- Bundle: `{summary.get('bundle_status', '')}`",
        f"- Verification: `{summary.get('verification_status', '')}`",
        f"- Blocking stage: `{summary.get('blocking_stage', '')}`",
        f"- Failures: {summary.get('failure_count', 0)}",
        "",
        "## Checks",
        "",
        "| Check | Status | Message | Path |",
        "| --- | --- | --- | --- |",
    ]
    for check in summary.get("checks", []):
        if not isinstance(check, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                f"`{markdown_cell(check.get('check', ''))}`",
                f"`{markdown_cell(check.get('status', ''))}`",
                markdown_cell(check.get("message", "")),
                f"`{markdown_cell(check.get('path', ''))}`",
            ])
            + " |"
        )

    lines.extend(["", "## Next Actions", ""])
    next_actions = summary.get("next_actions", [])
    if not next_actions:
        lines.append("No next actions recorded.")
    else:
        lines.extend(["| Rank | Action | Why |", "| ---: | --- | --- |"])
        for action in next_actions:
            if not isinstance(action, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(action.get("rank", "")),
                    f"`{markdown_cell(action.get('action_id', ''))}`",
                    markdown_cell(action.get("why", "")),
                ])
                + " |"
            )

    lines.extend(["", "## Repair Checklist", ""])
    repair_checklist = summary.get("repair_checklist", [])
    if not repair_checklist:
        lines.append("No repair checklist items recorded.")
    else:
        lines.extend(["| Rank | Action | Command | Expected Artifact | Success Signal |", "| ---: | --- | --- | --- | --- |"])
        for item in repair_checklist:
            if not isinstance(item, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(item.get("rank", "")),
                    f"`{markdown_cell(item.get('action_id', ''))}`",
                    f"`{markdown_cell(item.get('command', ''))}`",
                    f"`{markdown_cell(item.get('expected_artifact', ''))}`",
                    markdown_cell(item.get("success_signal", "")),
                ])
                + " |"
            )

    lines.extend(["", "## Outputs", "", "| Artifact | Path |", "| --- | --- |"])
    outputs = summary.get("outputs", {})
    if isinstance(outputs, dict):
        for key, value in outputs.items():
            lines.append(f"| `{markdown_cell(key)}` | `{markdown_cell(value)}` |")

    lines.extend(["", "## Failures", ""])
    failures = summary.get("failures", [])
    if not failures:
        lines.append("No failures found.")
    else:
        lines.extend(["| Stage | Id | Message |", "| --- | --- | --- |"])
        for failure in failures:
            if not isinstance(failure, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(failure.get("stage", "")),
                    markdown_cell(failure.get("id", "")),
                    markdown_cell(failure.get("message", "")),
                ])
                + " |"
            )
    return "\n".join(lines) + "\n"


def run_doctor(project_dir: Path | None, config: Path, evidence: Path, out_dir: Path, force: bool = False) -> dict[str, object]:
    prepare_output_directory(out_dir, "doctor output directory", force=force)
    out_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    def add(check_id: str, ok: bool, message: str, path: Path | str = "") -> None:
        item = release_check_item(check_id, ok, message, path)
        checks.append(item)
        if not ok:
            failures.append(failure_record("doctor", check_id, message))

    project_exists = config.exists()
    evidence_exists = evidence.exists()
    project_status = "missing"
    project_error_count = 0
    project_warning_count = 0
    evidence_status = "missing"
    evidence_error_count = 0
    evidence_warning_count = 0
    claim_check: dict[str, object] = {
        "status": "claim_check_blocked",
        "claim_ready": False,
        "audit_review_status": "not_run",
        "source_status": "not_run",
        "bundle_status": "not_run",
        "verification_status": "not_run",
        "blocking_stage": "project_or_evidence",
    }

    add("project_config_exists", project_exists, "Project config file exists.", config)
    if project_exists:
        try:
            project = load_project(config)
            validation = validate_project_config(project)
            project_status = str(validation.get("status", ""))
            project_error_count = int(validation.get("error_count", 0) or 0)
            project_warning_count = int(validation.get("warning_count", 0) or 0)
            (out_dir / "project_validation.json").write_text(json.dumps(validation, indent=2, sort_keys=True), encoding="utf-8")
            add("project_config_valid", bool(validation.get("valid")), "Project config validates with zero errors.", config)
        except (OSError, json.JSONDecodeError) as exc:
            project_status = "invalid"
            project_error_count = 1
            add("project_config_readable", False, f"Could not read project config: {exc}", config)

    add("evidence_exists", evidence_exists, "Evidence CSV file exists.", evidence)
    if evidence_exists:
        try:
            _, evidence_issues = read_csv_rows_with_diagnostics(evidence)
            evidence_error_count = sum(1 for issue in evidence_issues if issue.get("level") == "error")
            evidence_warning_count = sum(1 for issue in evidence_issues if issue.get("level") == "warning")
            evidence_status = "evidence_ready" if evidence_error_count == 0 else "evidence_blocked"
            (out_dir / "evidence_diagnostics.json").write_text(json.dumps({
                "status": evidence_status,
                "error_count": evidence_error_count,
                "warning_count": evidence_warning_count,
                "issues": evidence_issues,
            }, indent=2, sort_keys=True), encoding="utf-8")
            add("evidence_file_readable", True, "Evidence CSV can be read.", evidence)
            add("evidence_file_no_errors", evidence_error_count == 0, "Evidence CSV has zero parser/structure errors.", evidence)
        except (OSError, csv.Error) as exc:
            evidence_status = "evidence_blocked"
            evidence_error_count = 1
            add("evidence_file_readable", False, f"Could not read evidence CSV: {exc}", evidence)

    if project_exists and evidence_exists:
        try:
            claim_check = run_claim_check(config, evidence, out_dir / "claim_check", force=True)
        except SystemExit as exc:
            claim_check = {
                "status": "claim_check_blocked",
                "claim_ready": False,
                "audit_review_status": "not_run",
                "source_status": "not_run",
                "bundle_status": "not_run",
                "verification_status": "not_run",
                "blocking_stage": "claim_check_exception",
                "message": str(exc),
            }
            add("claim_check_runs", False, f"Claim check could not run: {exc}", out_dir / "claim_check")
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            claim_check = {
                "status": "claim_check_blocked",
                "claim_ready": False,
                "audit_review_status": "not_run",
                "source_status": "not_run",
                "bundle_status": "not_run",
                "verification_status": "not_run",
                "blocking_stage": "claim_check_exception",
                "message": str(exc),
            }
            add("claim_check_runs", False, f"Claim check could not run: {exc}", out_dir / "claim_check")
        else:
            add("claim_check_ready", claim_check.get("status") == "claim_check_ready", "Complete claim check is ready.", out_dir / "claim_check" / "claim_check.json")
            add("audit_review_ready", claim_check.get("audit_review_status") == "review_ready", "Audit review decision card is ready.", out_dir / "claim_check" / "evidence_bundle" / "audit" / "audit_review.json")
            add("source_provenance_ready", claim_check.get("source_status") == "sources_ready", "Source provenance is complete.", out_dir / "claim_check" / "evidence_bundle" / "source_manifest.json")
            add("bundle_ready", claim_check.get("bundle_status") == "bundle_ready", "Evidence bundle is ready.", out_dir / "claim_check" / "evidence_bundle" / "bundle_manifest.json")
            add("bundle_verified", claim_check.get("verification_status") == "bundle_verified", "Evidence bundle zip verifies.", out_dir / "claim_check" / "evidence_bundle_verify.json")

    outputs = {
        "doctor_summary": str(out_dir / "doctor_summary.json"),
        "doctor_report": str(out_dir / "doctor_summary.md"),
        "project_validation": str(out_dir / "project_validation.json"),
        "evidence_diagnostics": str(out_dir / "evidence_diagnostics.json"),
        "claim_check": str(out_dir / "claim_check" / "claim_check.json"),
        "claim_check_report": str(out_dir / "claim_check" / "claim_check.md"),
        "evidence_bundle_zip": str(out_dir / "claim_check" / "evidence_bundle.zip"),
        "bundle_verification": str(out_dir / "claim_check" / "evidence_bundle_verify.json"),
    }
    next_actions = doctor_next_actions(project_exists, evidence_exists, project_status, evidence_error_count, claim_check)
    summary: dict[str, object] = {
        "status": "doctor_ready" if not failures else "doctor_blocked",
        "mode": "project",
        "project_dir": str(project_dir or config.parent),
        "config_path": str(config),
        "evidence_path": str(evidence),
        "out_dir": str(out_dir),
        "project_status": project_status,
        "project_error_count": project_error_count,
        "project_warning_count": project_warning_count,
        "evidence_status": evidence_status,
        "evidence_error_count": evidence_error_count,
        "evidence_warning_count": evidence_warning_count,
        "claim_check_status": str(claim_check.get("status", "")),
        "claim_ready": bool(claim_check.get("claim_ready")),
        "audit_review_status": str(claim_check.get("audit_review_status", "")),
        "source_status": str(claim_check.get("source_status", "")),
        "bundle_status": str(claim_check.get("bundle_status", "")),
        "verification_status": str(claim_check.get("verification_status", "")),
        "blocking_stage": str(claim_check.get("blocking_stage", "")),
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
        "outputs": outputs,
        "next_actions": next_actions,
        "repair_checklist": doctor_repair_checklist(next_actions, config, evidence, out_dir),
        "claim_check_summary": claim_check,
    }
    (out_dir / "doctor_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "doctor_summary.md").write_text(render_doctor_report(summary), encoding="utf-8")
    return summary
