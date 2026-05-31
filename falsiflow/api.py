"""Small local API surface for embedding Falsiflow in tools and agents."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from .bundle import verify_bundle, verify_bundle_zip
from .claim_check import claim_check_evidence_todo, run_claim_check
from .core import audit_project, audit_review, load_project, read_csv_rows_with_diagnostics


def check_claim(config: Path, evidence: Path, out_dir: Path | None = None, force: bool = True) -> dict[str, object]:
    """Run the full claim-check workflow and return its machine-readable summary."""
    target_dir = out_dir or Path(tempfile.mkdtemp(prefix="falsiflow_claim_check_"))
    return run_claim_check(config, evidence, target_dir, force=force)


def check_project_dir(project_dir: Path, out_dir: Path | None = None, evidence_name: str = "evidence_pass_demo.csv", force: bool = True) -> dict[str, object]:
    """Run claim-check against a Falsiflow project directory."""
    return check_claim(project_dir / "project.json", project_dir / evidence_name, out_dir=out_dir, force=force)


def validate_bundle(bundle_dir: Path | None = None, zip_path: Path | None = None) -> dict[str, object]:
    """Verify an evidence bundle directory or zip archive."""
    if zip_path is not None:
        return verify_bundle_zip(zip_path)
    if bundle_dir is None:
        raise ValueError("validate_bundle requires bundle_dir or zip_path.")
    return verify_bundle(bundle_dir)


def explain_blockers(claim_check_json: Path) -> dict[str, object]:
    """Extract blocker-oriented repair context from a claim-check JSON artifact."""
    summary = json.loads(claim_check_json.read_text(encoding="utf-8"))
    if not isinstance(summary, dict):
        raise ValueError(f"Expected JSON object in {claim_check_json}.")
    return {
        "status": summary.get("status", ""),
        "claim_id": summary.get("claim_id", ""),
        "blocking_stage": summary.get("blocking_stage", ""),
        "top_blockers": summary.get("top_blockers", []),
        "evidence_todo": summary.get("evidence_todo", []),
        "next_actions": summary.get("next_actions", []),
        "outputs": summary.get("outputs", {}),
    }


def create_evidence_todo(config: Path, evidence: Path | None = None) -> dict[str, Any]:
    """Build an evidence repair todo list from a project config and optional evidence CSV."""
    project = load_project(config)
    if evidence is None:
        rows: list[dict[str, str]] = []
        issues: list[dict[str, Any]] = []
    else:
        rows, issues = read_csv_rows_with_diagnostics(evidence)
    audit = audit_project(project, rows, evidence_file_issues=issues)
    review = audit_review(audit)
    return {
        "status": "evidence_todo_ready",
        "claim_id": str(project.get("claim", {}).get("id", "")),
        "claim_ready": bool(audit.get("claim_ready")),
        "blocking_stage": review.get("blocking_stage", ""),
        "evidence_todo": claim_check_evidence_todo(review),
        "next_actions": audit.get("next_actions", []),
        "top_blockers": review.get("top_blockers", []),
    }
