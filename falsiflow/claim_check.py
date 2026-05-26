"""Claim-check workflow for Falsiflow."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil

from .bundle import (
    build_bundle,
    markdown_cell,
    render_bundle_verification_report,
    verify_bundle_zip,
)
from .release import failure_record
from .template_registry import read_json_object


CLAIM_REVIEW_ARTIFACTS = [
    ("claim_check_report", "Claim-check report", "status", "Top-level ready/blocked decision, blocking stage, failures, and next actions."),
    ("claim_check", "Claim-check JSON", "status", "Machine-readable status for CI, release-check, and browser handoffs."),
    ("audit_review_report", "Audit review", "audit_review_status", "Human review card for gate results, blockers, and decision boundaries."),
    ("claim_audit_report", "Claim audit", "audit_status", "Detailed measured evidence evaluation for the claim gates."),
    ("source_manifest_report", "Source manifest", "source_status", "Raw source-file provenance, missing files, allowed roots, and blank source rows."),
    ("bundle_manifest", "Bundle manifest", "bundle_status", "Declared bundle contents with byte counts and SHA-256 hashes."),
    ("bundle_verification_report", "Bundle verification", "verification_status", "Independent zip integrity check for the review bundle."),
    ("dashboard", "Claim dashboard", "status", "Browser-readable evidence dashboard for non-CLI reviewers."),
    ("bundle_zip", "Evidence bundle", "bundle_status", "Portable review package containing inputs, audit outputs, source manifest, and copied sources."),
    ("template_release_verification_report", "Template release verification", "template_release_verification_status", "Template-release integrity report when this claim-check is embedded in a release workflow."),
]


def markdown_path_link(label: str, path_text: object, base_dir: Path | None = None) -> str:
    text = str(path_text or "").strip()
    if not text:
        return ""
    target = text
    if base_dir is not None:
        try:
            path = Path(text).expanduser()
            candidate = path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()
            try:
                rel = os.path.relpath(candidate, base_dir.resolve())
                if rel != os.pardir and not rel.startswith(os.pardir + os.sep):
                    target = rel
            except ValueError:
                target = text
        except (OSError, ValueError):
            target = text
    target = target.replace("\\", "/")
    return f"[{markdown_cell(label)}](<{markdown_cell(target)}>)"


def claim_check_review_artifact_index(summary: dict[str, object]) -> list[dict[str, object]]:
    outputs = summary.get("outputs", {})
    if not isinstance(outputs, dict):
        return []
    rows: list[dict[str, object]] = []
    for key, label, status_key, purpose in CLAIM_REVIEW_ARTIFACTS:
        path = str(outputs.get(key, "") or "").strip()
        if not path:
            continue
        rows.append({
            "artifact": label,
            "key": key,
            "status": str(summary.get(status_key, summary.get("status", "")) or ""),
            "path": path,
            "purpose": purpose,
        })
    return rows


def cleanup_claim_check_outputs(out_dir: Path) -> None:
    for path in [
        out_dir / "evidence_bundle",
        out_dir / "evidence_bundle.zip",
        out_dir / "evidence_bundle_verify.json",
        out_dir / "evidence_bundle_verify.md",
        out_dir / "claim_check.json",
        out_dir / "claim_check.md",
    ]:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def claim_check_blocking_stage(
    audit_review: dict[str, object],
    source_manifest_summary: dict[str, object],
    bundle: dict[str, object],
    verification: dict[str, object],
) -> str:
    review_stage = str(audit_review.get("blocking_stage", ""))
    if review_stage and review_stage != "ready_for_human_review":
        return review_stage
    if source_manifest_summary.get("status") != "sources_ready":
        return "source_provenance"
    if bundle.get("status") != "bundle_ready":
        return "evidence_bundle"
    if verification.get("status") != "bundle_verified":
        return "bundle_verification"
    return "ready_for_human_review"


def claim_check_next_actions(
    audit_review: dict[str, object],
    source_manifest_summary: dict[str, object],
    bundle: dict[str, object],
    verification: dict[str, object],
) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    seen: set[str] = set()

    def add(action_id: str, why: str, **extra: object) -> None:
        if action_id in seen:
            return
        seen.add(action_id)
        action = {"rank": len(actions) + 1, "action_id": action_id, "why": why}
        action.update({key: value for key, value in extra.items() if value not in {"", None}})
        actions.append(action)

    for raw_action in audit_review.get("next_actions", []):
        if not isinstance(raw_action, dict):
            continue
        action_id = str(raw_action.get("action_id", "") or f"audit_action_{len(actions) + 1}")
        if action_id in seen:
            continue
        normalized = dict(raw_action)
        normalized["action_id"] = action_id
        normalized["rank"] = len(actions) + 1
        actions.append(normalized)
        seen.add(action_id)
        if len(actions) >= 5:
            break

    if source_manifest_summary.get("status") != "sources_ready":
        missing = int(source_manifest_summary.get("missing_source_file_count", 0) or 0)
        outside = int(source_manifest_summary.get("outside_allowed_roots_count", 0) or 0)
        blank = int(source_manifest_summary.get("blank_source_row_count", 0) or 0)
        add(
            "repair_source_provenance",
            f"Resolve source-file provenance blockers: missing={missing}, outside_allowed_roots={outside}, blank_rows={blank}.",
        )
    if bundle.get("status") != "bundle_ready":
        add(
            "resolve_bundle_blockers",
            f"Make audit and source provenance ready before treating the bundle as shareable; bundle_status={bundle.get('status', '')}.",
        )
    if verification.get("status") == "bundle_failed" or verification.get("integrity_status") == "integrity_failed":
        add(
            "repair_bundle_verification",
            f"Rebuild or repair the evidence bundle until zip verification returns bundle_verified; current={verification.get('status', '')}.",
        )
    if not actions:
        add(
            "human_release_review",
            "Review claim_audit, audit_review, source_manifest, and the verified bundle before relying on or sharing the claim.",
        )
    return actions


def render_claim_check_report(summary: dict[str, object]) -> str:
    out_dir = Path(str(summary.get("out_dir", ".")))
    lines = [
        "# Falsiflow Claim Check",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Claim ready: `{str(bool(summary.get('claim_ready'))).lower()}`",
        f"- Audit: `{summary.get('audit_status', '')}`",
        f"- Audit review: `{summary.get('audit_review_status', '')}`",
        f"- Sources: `{summary.get('source_status', '')}`",
        f"- Bundle: `{summary.get('bundle_status', '')}`",
        f"- Verification: `{summary.get('verification_status', '')}`",
        f"- Config: `{summary.get('config_path', '')}`",
        f"- Evidence: `{summary.get('evidence_path', '')}`",
        f"- Blocking stage: `{summary.get('blocking_stage', '')}`",
        f"- Completion: {summary.get('completion_pct', 0)}%",
        f"- Blockers: {summary.get('blocker_count', 0)}",
        f"- Failures: {summary.get('failure_count', 0)}",
        "",
        "## Outputs",
        "",
        "| Artifact | Path |",
        "| --- | --- |",
    ]
    outputs = summary.get("outputs", {})
    if isinstance(outputs, dict):
        for key, value in outputs.items():
            lines.append(f"| `{markdown_cell(key)}` | `{markdown_cell(value)}` |")

    artifact_index = summary.get("review_artifact_index", [])
    if not isinstance(artifact_index, list) or not artifact_index:
        artifact_index = claim_check_review_artifact_index(summary)
    lines.extend([
        "",
        "## Review Artifact Index",
        "",
        "| Artifact | Status | Link | Purpose |",
        "| --- | --- | --- | --- |",
    ])
    for artifact in artifact_index:
        if not isinstance(artifact, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(artifact.get("artifact", "")),
                f"`{markdown_cell(artifact.get('status', ''))}`",
                markdown_path_link(str(artifact.get("artifact", "artifact")), artifact.get("path", ""), out_dir),
                markdown_cell(artifact.get("purpose", "")),
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


def run_claim_check(config: Path, evidence: Path, out_dir: Path, force: bool = False) -> dict[str, object]:
    if out_dir.exists() and any(out_dir.iterdir()) and not force:
        raise SystemExit(f"Refusing to write claim check into non-empty directory without --force: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    if force:
        cleanup_claim_check_outputs(out_dir)

    bundle_dir = out_dir / "evidence_bundle"
    bundle_zip = out_dir / "evidence_bundle.zip"
    verification_json = out_dir / "evidence_bundle_verify.json"
    verification_report = out_dir / "evidence_bundle_verify.md"
    claim_check_json = out_dir / "claim_check.json"
    claim_check_report = out_dir / "claim_check.md"

    bundle = build_bundle(config, evidence, bundle_dir, bundle_zip, force=True)
    verification = verify_bundle_zip(bundle_zip)
    verification_json.write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")
    verification_report.write_text(render_bundle_verification_report(verification), encoding="utf-8")

    claim_summary = read_json_object(bundle_dir / "audit" / "claim_summary.json", "claim summary")
    audit_review = read_json_object(bundle_dir / "audit" / "audit_review.json", "audit review")
    source_summary = read_json_object(bundle_dir / "source_manifest.json", "source manifest")

    failures: list[dict[str, str]] = []
    if not bool(bundle.get("claim_ready")):
        failures.append(failure_record("audit", str(bundle.get("claim_id", "")), f"Audit ended as {bundle.get('audit_status', '')}."))
    if audit_review.get("status") != "review_ready":
        failures.append(failure_record("audit_review", str(bundle.get("claim_id", "")), f"Audit review ended as {audit_review.get('status', '')}."))
    if source_summary.get("status") != "sources_ready":
        failures.append(failure_record("sources", str(bundle.get("claim_id", "")), f"Source provenance ended as {source_summary.get('status', '')}."))
    if bundle.get("status") != "bundle_ready":
        failures.append(failure_record("bundle", str(bundle.get("claim_id", "")), f"Bundle ended as {bundle.get('status', '')}."))
    if verification.get("status") != "bundle_verified":
        failures.append(failure_record("verify_bundle", str(bundle.get("claim_id", "")), f"Bundle verification ended as {verification.get('status', '')}."))

    claim_check_ready = not failures
    outputs = {
        "claim_check": str(claim_check_json),
        "claim_check_report": str(claim_check_report),
        "claim_audit": str(bundle_dir / "audit" / "claim_audit.json"),
        "claim_audit_report": str(bundle_dir / "audit" / "claim_audit.md"),
        "audit_review": str(bundle_dir / "audit" / "audit_review.json"),
        "audit_review_report": str(bundle_dir / "audit" / "audit_review.md"),
        "claim_summary": str(bundle_dir / "audit" / "claim_summary.json"),
        "next_actions": str(bundle_dir / "audit" / "next_actions.json"),
        "dashboard": str(bundle_dir / "audit" / "dashboard.html"),
        "source_manifest": str(bundle_dir / "source_manifest.json"),
        "source_manifest_report": str(bundle_dir / "source_manifest.md"),
        "bundle_manifest": str(bundle_dir / "bundle_manifest.json"),
        "bundle_zip": str(bundle_zip),
        "bundle_verification": str(verification_json),
        "bundle_verification_report": str(verification_report),
    }
    summary: dict[str, object] = {
        "status": "claim_check_ready" if claim_check_ready else "claim_check_blocked",
        "project_id": str(bundle.get("project_id", "")),
        "claim_id": str(bundle.get("claim_id", "")),
        "config_path": str(config),
        "evidence_path": str(evidence),
        "out_dir": str(out_dir),
        "claim_check_ready": claim_check_ready,
        "claim_ready": bool(bundle.get("claim_ready")),
        "audit_status": str(bundle.get("audit_status", "")),
        "audit_review_status": str(audit_review.get("status", "")),
        "source_status": str(source_summary.get("status", "")),
        "bundle_status": str(bundle.get("status", "")),
        "verification_status": str(verification.get("status", "")),
        "blocking_stage": claim_check_blocking_stage(audit_review, source_summary, bundle, verification),
        "gate_count": int(claim_summary.get("gate_count", 0) or 0),
        "completion_pct": float(claim_summary.get("completion_pct", 0) or 0),
        "blocker_count": int(claim_summary.get("blocker_count", 0) or 0),
        "source_blocker_count": int(source_summary.get("blocker_count", 0) or 0),
        "artifact_count": int(bundle.get("artifact_count", 0) or 0),
        "source_file_count": int(bundle.get("source_file_count", 0) or 0),
        "checked_artifact_count": int(verification.get("checked_artifact_count", 0) or 0),
        "verification_issue_count": int(verification.get("issue_count", 0) or 0),
        "issue_count": int(verification.get("issue_count", 0) or 0),
        "failure_count": len(failures),
        "failures": failures,
        "outputs": outputs,
        "next_actions": claim_check_next_actions(audit_review, source_summary, bundle, verification),
        "bundle_summary": bundle,
        "bundle_verification_summary": verification,
    }
    summary["review_artifact_index"] = claim_check_review_artifact_index(summary)
    claim_check_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    claim_check_report.write_text(render_claim_check_report(summary), encoding="utf-8")
    return summary
