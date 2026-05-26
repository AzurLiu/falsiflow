"""First-run project bootstrap workflow for Falsiflow."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import shutil

from .bundle import markdown_cell
from .claim_check import run_claim_check
from .release import failure_record

TemplateResolver = Callable[[str, list[Path] | None, bool], Path | None]


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


def render_quickstart_report(summary: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Quickstart",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Template: `{summary.get('template', '')}`",
        f"- Project: `{summary.get('project_dir', '')}`",
        f"- Claim check: `{summary.get('claim_check_status', '')}`",
        f"- Claim ready: `{str(bool(summary.get('claim_ready'))).lower()}`",
        f"- Audit review: `{summary.get('audit_review_status', '')}`",
        f"- Sources: `{summary.get('source_status', '')}`",
        f"- Bundle: `{summary.get('bundle_status', '')}`",
        f"- Verification: `{summary.get('verification_status', '')}`",
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

    lines.extend(["", "## Next Commands", ""])
    next_commands = summary.get("next_commands", [])
    if not next_commands:
        lines.append("No next commands recorded.")
    else:
        for command in next_commands:
            lines.append(f"- `{markdown_cell(command)}`")

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


def run_quickstart(
    template: str,
    out_dir: Path,
    template_roots: list[Path] | None = None,
    force: bool = False,
    include_env: bool = True,
    *,
    template_resolver: TemplateResolver,
) -> dict[str, object]:
    source = template_resolver(template, template_roots, include_env)
    if source is None:
        raise SystemExit(f"Unknown template `{template}`. Run `falsiflow templates` to list available templates.")
    prepare_output_directory(out_dir, "quickstart project directory", force=force)
    shutil.copytree(source, out_dir, dirs_exist_ok=True)

    config_path = out_dir / "project.json"
    evidence_path = out_dir / "evidence_pass_demo.csv"
    claim_check_dir = out_dir / "claim_check"
    quickstart_json = out_dir / "quickstart_summary.json"
    quickstart_report = out_dir / "quickstart_summary.md"

    claim_check = run_claim_check(config_path, evidence_path, claim_check_dir, force=True)
    failures: list[dict[str, str]] = []
    if claim_check.get("status") != "claim_check_ready":
        failures.append(failure_record("claim_check", str(claim_check.get("claim_id", "")), f"Claim check ended as {claim_check.get('status', '')}."))
    quickstart_ready = not failures
    claim_check_outputs = claim_check.get("outputs", {}) if isinstance(claim_check.get("outputs"), dict) else {}
    outputs = {
        "project_dir": str(out_dir),
        "project_config": str(config_path),
        "evidence": str(evidence_path),
        "quickstart_summary": str(quickstart_json),
        "quickstart_report": str(quickstart_report),
        "claim_check": str(claim_check_dir / "claim_check.json"),
        "claim_check_report": str(claim_check_dir / "claim_check.md"),
        "dashboard": str(claim_check_outputs.get("dashboard", claim_check_dir / "evidence_bundle" / "audit" / "dashboard.html")),
        "evidence_bundle_zip": str(claim_check_dir / "evidence_bundle.zip"),
        "bundle_verification": str(claim_check_dir / "evidence_bundle_verify.json"),
        "bundle_verification_report": str(claim_check_dir / "evidence_bundle_verify.md"),
    }
    next_commands = [
        f"falsiflow doctor --project-dir {out_dir} --strict",
        f"falsiflow claim-check --project-dir {out_dir} --strict --force",
    ]
    summary: dict[str, object] = {
        "status": "quickstart_ready" if quickstart_ready else "quickstart_blocked",
        "template": template,
        "project_dir": str(out_dir),
        "config_path": str(config_path),
        "evidence_path": str(evidence_path),
        "claim_check_status": str(claim_check.get("status", "")),
        "claim_ready": bool(claim_check.get("claim_ready")),
        "audit_review_status": str(claim_check.get("audit_review_status", "")),
        "source_status": str(claim_check.get("source_status", "")),
        "bundle_status": str(claim_check.get("bundle_status", "")),
        "verification_status": str(claim_check.get("verification_status", "")),
        "failure_count": len(failures),
        "failures": failures,
        "outputs": outputs,
        "next_commands": next_commands,
        "claim_check_summary": claim_check,
    }
    quickstart_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    quickstart_report.write_text(render_quickstart_report(summary), encoding="utf-8")
    return summary
