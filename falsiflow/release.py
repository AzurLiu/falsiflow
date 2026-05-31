"""Release and distribution checks for Falsiflow."""

from __future__ import annotations

from importlib import metadata as importlib_metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import venv
from collections.abc import Callable
from typing import Any

from .bundle import markdown_cell

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback.
    tomllib = None


EXPECTED_REQUIRES_PYTHON = ">=3.10"
EXPECTED_PYPROJECT_KEYWORDS = {
    "audit",
    "claim-checking",
    "evidence",
    "provenance",
    "quality-gates",
    "rd",
    "research",
    "templates",
    "workflow",
}
EXPECTED_PYPROJECT_CLASSIFIERS = {
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering",
    "Topic :: Software Development :: Quality Assurance",
    "Topic :: Utilities",
}
EXPECTED_PROJECT_URLS = {
    "Homepage": "https://github.com/AzurLiu/falsiflow",
    "Documentation": "https://github.com/AzurLiu/falsiflow#readme",
    "Architecture": "https://github.com/AzurLiu/falsiflow/blob/main/docs/falsiflow_architecture.md",
    "DataContract": "https://github.com/AzurLiu/falsiflow/blob/main/docs/falsiflow_data_contract.md",
    "AdapterProfiles": "https://github.com/AzurLiu/falsiflow/blob/main/docs/falsiflow_adapter_profiles.md",
    "CasebookCheck": "https://github.com/AzurLiu/falsiflow/blob/main/docs/falsiflow_casebook_check.md",
    "TemplateAuthoring": "https://github.com/AzurLiu/falsiflow/blob/main/docs/falsiflow_template_authoring.md",
    "Troubleshooting": "https://github.com/AzurLiu/falsiflow/blob/main/docs/falsiflow_troubleshooting.md",
    "Source": "https://github.com/AzurLiu/falsiflow",
    "Issues": "https://github.com/AzurLiu/falsiflow/issues",
    "Changelog": "https://github.com/AzurLiu/falsiflow/blob/main/CHANGELOG.md",
    "Demo": "https://azurliu.github.io/falsiflow/",
    "LivePRStory": "https://github.com/AzurLiu/falsiflow/pull/17",
    "BlockedRun": "https://github.com/AzurLiu/falsiflow/actions/runs/26708459093",
    "ReadyRun": "https://github.com/AzurLiu/falsiflow/actions/runs/26708472653",
    "LaunchArticle": "https://github.com/AzurLiu/falsiflow/blob/main/docs/launch_articles/stop_shipping_unverifiable_ai_eval_claims.md",
    "DownstreamDemo": "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo",
    "DownstreamPR": "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1",
    "DownstreamBlockedRun": "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990",
    "DownstreamReadyRun": "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112",
    "Citation": "https://github.com/AzurLiu/falsiflow/blob/main/CITATION.cff",
    "Governance": "https://github.com/AzurLiu/falsiflow/blob/main/GOVERNANCE.md",
}


def failure_record(stage: str, identifier: str, message: str) -> dict[str, str]:
    return {"stage": stage, "id": identifier, "message": message}


def release_check_item(check_id: str, ok: bool, message: str, path: Path | str = "") -> dict[str, str]:
    return {
        "check": check_id,
        "status": "passed" if ok else "failed",
        "message": message,
        "path": str(path),
    }


def release_review_artifact_index(summary: dict[str, object]) -> list[dict[str, object]]:
    artifact_root = Path(str(summary.get("artifact_root", ""))) if summary.get("artifact_root") else Path()
    claim_summary = summary.get("claim_check_summary", {})
    claim_outputs = claim_summary.get("outputs", {}) if isinstance(claim_summary, dict) and isinstance(claim_summary.get("outputs"), dict) else {}
    template_release_verification = summary.get("template_release_verification_summary", {})
    release_artifacts = template_release_verification if isinstance(template_release_verification, dict) else {}
    launch_kit_summary = summary.get("launch_kit_summary", {})
    launch_outputs = launch_kit_summary.get("outputs", {}) if isinstance(launch_kit_summary, dict) and isinstance(launch_kit_summary.get("outputs"), dict) else {}
    demo_package_summary = summary.get("demo_package_summary", {})
    demo_outputs = demo_package_summary.get("outputs", {}) if isinstance(demo_package_summary, dict) and isinstance(demo_package_summary.get("outputs"), dict) else {}
    publish_kit_summary = summary.get("publish_kit_summary", {})
    publish_outputs = publish_kit_summary.get("outputs", {}) if isinstance(publish_kit_summary, dict) and isinstance(publish_kit_summary.get("outputs"), dict) else {}
    external_summary = summary.get("external_check_summary", {})
    external_outputs = external_summary.get("outputs", {}) if isinstance(external_summary, dict) and isinstance(external_summary.get("outputs"), dict) else {}

    def output_path(key: str, fallback: Path) -> str:
        value = str(claim_outputs.get(key, "") or "").strip()
        return value or str(fallback)

    rows = [
        {
            "artifact": "Claim-check report",
            "status": str(summary.get("claim_check_status", "")),
            "path": output_path("claim_check_report", artifact_root / "claim_check" / "claim_check.md"),
            "purpose": "Top-level claim ready/blocked decision used by release-check.",
        },
        {
            "artifact": "Source manifest",
            "status": str(claim_summary.get("source_status", "") if isinstance(claim_summary, dict) else ""),
            "path": output_path("source_manifest_report", artifact_root / "claim_check" / "evidence_bundle" / "source_manifest.md"),
            "purpose": "Release evidence for raw source-file provenance.",
        },
        {
            "artifact": "Bundle verification",
            "status": str(claim_summary.get("verification_status", "") if isinstance(claim_summary, dict) else ""),
            "path": output_path("bundle_verification_report", artifact_root / "claim_check" / "evidence_bundle_verify.md"),
            "purpose": "Release evidence that the claim-check bundle verifies from zip.",
        },
        {
            "artifact": "Evidence bundle",
            "status": str(claim_summary.get("bundle_status", "") if isinstance(claim_summary, dict) else ""),
            "path": output_path("bundle_zip", artifact_root / "claim_check" / "evidence_bundle.zip"),
            "purpose": "Portable claim-review package produced during release-check.",
        },
        {
            "artifact": "Template release zip",
            "status": str(summary.get("template_release_status", "")),
            "path": str(release_artifacts.get("release_zip_path", "") or artifact_root / "template_release.zip"),
            "purpose": "Template release package checked before install handoff.",
        },
        {
            "artifact": "Template release verification",
            "status": str(summary.get("template_release_verification_status", "")),
            "path": str(artifact_root / "template_release_verification.md"),
            "purpose": "Human-readable integrity report for template pack, registry, lock, attestation, and policy artifacts.",
        },
        {
            "artifact": "Public demo package",
            "status": str(summary.get("demo_package_status", "")),
            "path": str(demo_outputs.get("summary", "") or artifact_root / "public_demo" / "demo_package_summary.json"),
            "purpose": "Hostable static demo package used for zero-install public review.",
        },
        {
            "artifact": "Launch proof card",
            "status": str(summary.get("launch_kit_status", "")),
            "path": str(launch_outputs.get("proof_card_report", "") or artifact_root / "launch_kit" / "proof_card.md"),
            "purpose": "Concise public proof points, try commands, verification commands, and responsible-use boundary.",
        },
        {
            "artifact": "Launch metrics tracker",
            "status": str(launch_kit_summary.get("launch_metrics_status", "") if isinstance(launch_kit_summary, dict) else ""),
            "path": str(launch_outputs.get("launch_metrics_report", "") or artifact_root / "launch_kit" / "launch_metrics.md"),
            "purpose": "1k-star launch tracking for traffic, referrers, stars, demo visits, install signals, questions, and follow-up fixes.",
        },
        {
            "artifact": "Launch posts",
            "status": str(summary.get("launch_kit_status", "")),
            "path": str(launch_outputs.get("launch_posts", "") or artifact_root / "launch_kit" / "launch_posts.md"),
            "purpose": "Draft public launch copy for review before account-bound publishing.",
        },
        {
            "artifact": "External readiness report",
            "status": str(summary.get("external_check_status", "")),
            "path": str(external_outputs.get("report", "") or artifact_root / "external_readiness" / "external_readiness.md"),
            "purpose": "Public repository, hosted demo, PyPI package, pipx, Windows, and workflow evidence gate.",
        },
        {
            "artifact": "Public release evidence ledger",
            "status": str(publish_kit_summary.get("public_release_evidence_status", "") if isinstance(publish_kit_summary, dict) else ""),
            "path": str(publish_outputs.get("public_release_evidence_report", "") or artifact_root / "publish_kit" / "public_release_evidence.md"),
            "purpose": "One-page final release evidence ledger linking local gates, public URLs, smoke artifacts, Scorecard, and external readiness.",
        },
        {
            "artifact": "Public release rehearsal",
            "status": str(publish_kit_summary.get("release_rehearsal_status", "") if isinstance(publish_kit_summary, dict) else ""),
            "path": str(publish_outputs.get("release_rehearsal_report", "") or artifact_root / "publish_kit" / "release_rehearsal.md"),
            "purpose": "Step-by-step public release rehearsal with commands, expected artifacts, success signals, and strict external stop conditions.",
        },
    ]
    return [row for row in rows if str(row.get("path", "")).strip()]


def schema_filename(kind: str) -> str:
    return f"{kind.replace('-', '_')}.schema.json"


def render_release_check_report(summary: dict[str, object]) -> str:
    adoption_summary = summary.get("adoption_check_summary", {})
    ready_priority_count = 0
    priority_count = 0
    if isinstance(adoption_summary, dict):
        ready_priority_count = int(adoption_summary.get("ready_priority_count", 0) or 0)
        priority_count = int(adoption_summary.get("priority_count", 0) or 0)
    lines = [
        "# Falsiflow Release Check",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Package: `{summary.get('package_status', '')}`",
        f"- Distribution: `{summary.get('dist_status', '')}`",
        f"- Release validation: `{summary.get('release_validation_status', '')}`",
        f"- Release validation note: {markdown_cell(summary.get('release_validation_message', ''))}",
        f"- Schemas: {summary.get('schema_count', 0)}",
        f"- Templates: {summary.get('template_count', 0)}",
        f"- Template gallery: `{summary.get('template_gallery_status', '')}`",
        f"- Casebook check: `{summary.get('casebook_check_status', '')}`",
        f"- Template checks: {summary.get('template_check_ready_count', 0)}/{summary.get('template_check_count', 0)}",
        f"- Template pack: `{summary.get('template_pack_status', '')}` verification=`{summary.get('template_pack_verification_status', '')}`",
        f"- Template registry: `{summary.get('template_registry_status', '')}`",
        f"- Template lock: `{summary.get('template_lock_status', '')}`",
        f"- Template attestation: `{summary.get('template_attestation_status', '')}` verification=`{summary.get('template_attestation_verification_status', '')}`",
        f"- Template policy: `{summary.get('template_policy_status', '')}` verification=`{summary.get('template_policy_verification_status', '')}`",
        f"- Template release: `{summary.get('template_release_status', '')}` verification=`{summary.get('template_release_verification_status', '')}`",
        f"- Template install: `{summary.get('template_install_status', '')}`",
        f"- Quickstart: `{summary.get('quickstart_status', '')}`",
        f"- Doctor: `{summary.get('doctor_status', '')}`",
        f"- Claim check: `{summary.get('claim_check_status', '')}`",
        f"- Adoption check: `{summary.get('adoption_check_status', '')}` priorities={ready_priority_count}/{priority_count}",
        f"- Adoption release validation: `{adoption_summary.get('release_validation_status', '') if isinstance(adoption_summary, dict) else ''}`",
        f"- Ready audits: {summary.get('audit_ready_count', 0)}",
        f"- Ready sources: {summary.get('source_ready_count', 0)}",
        f"- Ready bundles: {summary.get('bundle_ready_count', 0)}",
        f"- Verified bundles: {summary.get('bundle_verified_count', 0)}",
        f"- Demo package: `{summary.get('demo_package_status', '')}`",
        f"- Publish kit: `{summary.get('publish_kit_status', '')}`",
        f"- Launch kit: `{summary.get('launch_kit_status', '')}`",
        f"- External readiness: `{summary.get('external_check_status', '')}`",
        f"- Failures: {summary.get('failure_count', 0)}",
        "",
        "## Release Review Artifact Index",
        "",
        "| Artifact | Status | Path | Purpose |",
        "| --- | --- | --- | --- |",
    ]
    for artifact in release_review_artifact_index(summary):
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(artifact.get("artifact", "")),
                f"`{markdown_cell(artifact.get('status', ''))}`",
                f"`{markdown_cell(artifact.get('path', ''))}`",
                markdown_cell(artifact.get("purpose", "")),
            ])
            + " |"
        )
    lines.extend([
        "",
        "## Adoption Priorities",
        "",
    ])
    adoption_priorities = adoption_summary.get("priorities", []) if isinstance(adoption_summary, dict) else []
    if not adoption_priorities:
        lines.append("No adoption priorities were evaluated.")
    else:
        lines.extend(["| Priority | Status | Checks |", "| --- | --- | ---: |"])
        for priority in adoption_priorities:
            if not isinstance(priority, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(priority.get("title", "")),
                    markdown_cell(priority.get("status", "")),
                    f"{priority.get('passed_check_count', 0)}/{priority.get('check_count', 0)}",
                ])
                + " |"
            )
        lines.extend(["", "## Adoption Priority Evidence", ""])
        for priority in adoption_priorities:
            if not isinstance(priority, dict):
                continue
            lines.extend(["", f"### {priority.get('title', '')}", ""])
            checks = priority.get("checks", [])
            if not isinstance(checks, list) or not checks:
                lines.append("No checks recorded.")
                continue
            lines.extend(["| Check | Status | Path | Message |", "| --- | --- | --- | --- |"])
            for check in checks:
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
    adoption_repair_checklist = adoption_summary.get("repair_checklist", []) if isinstance(adoption_summary, dict) else []
    lines.extend(["", "## Adoption Repair Checklist", ""])
    if not adoption_repair_checklist:
        lines.append("No adoption repair or recheck items were recorded.")
    else:
        lines.extend(["| Rank | Priority | Action | Command | Expected Artifact | Success Signal |", "| ---: | --- | --- | --- | --- | --- |"])
        for item in adoption_repair_checklist:
            if not isinstance(item, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(item.get("rank", "")),
                    f"`{markdown_cell(item.get('priority_id', ''))}`",
                    f"`{markdown_cell(item.get('action_id', ''))}`",
                    f"`{markdown_cell(item.get('command', ''))}`",
                    f"`{markdown_cell(item.get('expected_artifact', ''))}`",
                    markdown_cell(item.get("success_signal", "")),
                ])
                + " |"
            )
    lines.extend([
        "",
        "## Templates",
        "",
        "| Template | Audit | Sources | Bundle | Verification |",
        "| --- | --- | --- | --- | --- |",
    ])
    for template in summary.get("templates", []):
        if not isinstance(template, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(template.get("template", "")),
                markdown_cell(template.get("audit_status", "")),
                markdown_cell(template.get("source_status", "")),
                markdown_cell(template.get("bundle_status", "")),
                markdown_cell(template.get("verification_status", "")),
            ])
                + " |"
        )

    package_checks = summary.get("package_checks", [])
    lines.extend(["", "## Package Checks", ""])
    if not package_checks:
        lines.append("No package checks were run.")
    else:
        lines.extend(["| Check | Status | Path | Message |", "| --- | --- | --- | --- |"])
        for check in package_checks:
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

    dist_checks = summary.get("dist_checks", [])
    lines.extend(["", "## Distribution Checks", ""])
    if not dist_checks:
        lines.append("No distribution checks were run.")
    else:
        lines.extend(["| Check | Status | Path | Message |", "| --- | --- | --- | --- |"])
        for check in dist_checks:
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

    failures = summary.get("failures", [])
    lines.extend(["", "## Failures", ""])
    if not failures:
        lines.append("No failures found.")
    else:
        lines.extend(["| Stage | ID | Message |", "| --- | --- | --- |"])
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


def remove_generated_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def command_excerpt(completed: subprocess.CompletedProcess[str]) -> str:
    output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)
    return output[-1000:] if output else f"exit code {completed.returncode}"


def pyproject_build_requires(pyproject_path: Path) -> list[str]:
    if tomllib is None:
        return ["setuptools>=77"]
    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return ["setuptools>=77"]
    raw_requires = data.get("build-system", {}).get("requires", [])
    requires = [str(item) for item in raw_requires if isinstance(item, str)]
    return requires or ["setuptools>=77"]


def isolated_python_path(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def build_sdist_in_isolated_env(root: Path, sdist_dir: Path, build_env_dir: Path, pyproject_path: Path) -> tuple[str, str]:
    if build_env_dir.exists():
        shutil.rmtree(build_env_dir)
    venv.EnvBuilder(with_pip=True, clear=True).create(build_env_dir)
    build_python = isolated_python_path(build_env_dir)
    requirements = pyproject_build_requires(pyproject_path)
    install = subprocess.run(
        [str(build_python), "-m", "pip", "install", "--quiet", *requirements],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if install.returncode != 0:
        raise RuntimeError("Could not install sdist build requirements: " + command_excerpt(install))

    result_path = sdist_dir / "sdist_build_result.json"
    script = """
import contextlib
import io
import json
import os
from pathlib import Path
import sys

os.chdir(sys.argv[1])
sdist_dir = Path(sys.argv[2])
result_path = Path(sys.argv[3])
import setuptools.build_meta as build_meta

stdout = io.StringIO()
stderr = io.StringIO()
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    sdist_name = build_meta.build_sdist(str(sdist_dir))
result_path.write_text(json.dumps({
    "sdist_name": sdist_name,
    "stdout": stdout.getvalue(),
    "stderr": stderr.getvalue(),
}), encoding="utf-8")
"""
    build = subprocess.run(
        [str(build_python), "-c", script, str(root), str(sdist_dir), str(result_path)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if build.returncode != 0:
        raise RuntimeError("Source distribution build failed: " + command_excerpt(build))
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Source distribution build did not write a valid result: {exc}") from exc
    return str(result.get("sdist_name", "")), "; ".join(part for part in [str(result.get("stdout", "")).strip(), str(result.get("stderr", "")).strip()] if part)


def pyproject_data(path: Path) -> dict[str, object]:
    if tomllib is None:
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def get_nested(data: dict[str, object], *keys: str) -> object:
    current: object = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def string_values(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value if isinstance(item, str)}


def keyword_values(value: object) -> set[str]:
    return {item.strip().lower() for item in string_values(value) if item.strip()}


def metadata_keywords(metadata: Any) -> set[str]:
    raw = str(metadata.get("Keywords", "") or "")
    return {part.strip().lower() for part in re.split(r"[,\s]+", raw) if part.strip()}


def metadata_project_urls(metadata: Any) -> dict[str, str]:
    urls: dict[str, str] = {}
    for entry in metadata.get_all("Project-URL") or []:
        name, separator, url = str(entry).partition(",")
        if separator:
            urls[name.strip()] = url.strip()
    return urls


def package_init_version(path: Path) -> str:
    if not path.exists():
        return ""
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    return match.group(1) if match else ""


def package_release_checks(root: Path) -> dict[str, object]:
    root = root.resolve()
    checks: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    def add(check_id: str, ok: bool, message: str, path: Path | str = "") -> None:
        checks.append(release_check_item(check_id, ok, message, path))
        if not ok:
            failures.append(failure_record("package", check_id, message))

    pyproject_path = root / "pyproject.toml"
    readme_path = root / "README.md"
    license_path = root / "LICENSE"
    changelog_path = root / "CHANGELOG.md"
    contributing_path = root / "CONTRIBUTING.md"
    citation_path = root / "CITATION.cff"
    code_of_conduct_path = root / "CODE_OF_CONDUCT.md"
    governance_path = root / "GOVERNANCE.md"
    release_path = root / "RELEASE.md"
    security_path = root / "SECURITY.md"
    support_path = root / "SUPPORT.md"
    responsible_use_path = root / "RESPONSIBLE_USE.md"
    roadmap_path = root / "ROADMAP.md"
    adoption_priorities_path = root / "docs" / "falsiflow_adoption_priorities.md"
    launch_plan_path = root / "docs" / "falsiflow_1k_launch_plan.md"
    launch_execution_path = root / "docs" / "falsiflow_launch_execution.md"
    architecture_path = root / "docs" / "falsiflow_architecture.md"
    cli_reference_path = root / "docs" / "falsiflow_cli_reference.md"
    data_contract_path = root / "docs" / "falsiflow_data_contract.md"
    adapter_profiles_path = root / "docs" / "falsiflow_adapter_profiles.md"
    local_llm_eval_path = root / "docs" / "falsiflow_local_llm_eval.md"
    mcp_path = root / "docs" / "falsiflow_mcp.md"
    casebook_check_path = root / "docs" / "falsiflow_casebook_check.md"
    demo_pr_playbook_path = root / "docs" / "falsiflow_demo_pr_playbook.md"
    github_action_examples_path = root / "docs" / "falsiflow_github_action_examples.md"
    positioning_path = root / "docs" / "falsiflow_positioning.md"
    public_casebook_path = root / "docs" / "falsiflow_public_casebook.md"
    rag_quality_gate_proposal_path = root / "docs" / "falsiflow_rag_quality_gate_proposal.md"
    pypi_trusted_publishing_path = root / "docs" / "falsiflow_pypi_trusted_publishing.md"
    security_posture_path = root / "docs" / "falsiflow_security_posture.md"
    template_authoring_path = root / "docs" / "falsiflow_template_authoring.md"
    troubleshooting_path = root / "docs" / "falsiflow_troubleshooting.md"
    downstream_pr_proof_strip_path = root / "docs" / "assets" / "falsiflow_downstream_pr_proof_strip.svg"
    downstream_pr_proof_strip_png_path = root / "docs" / "assets" / "falsiflow_downstream_pr_proof_strip.png"
    readme_pr_story_reel_path = root / "docs" / "assets" / "falsiflow_live_pr_story_reel.svg"
    readme_proof_strip_path = root / "docs" / "assets" / "falsiflow_proof_strip.svg"
    readme_demo_strip_path = root / "docs" / "assets" / "falsiflow_30_second_demo.svg"
    walkthrough_path = root / "examples" / "README.md"
    downstream_smoke_path = root / "examples" / "downstream_ai_eval_smoke"
    downstream_smoke_readme_path = downstream_smoke_path / "README.md"
    downstream_smoke_workflow_path = downstream_smoke_path / ".github" / "workflows" / "falsiflow-ai-eval.yml"
    downstream_smoke_project_path = downstream_smoke_path / "falsiflow_ai_eval" / "project.json"
    downstream_smoke_evidence_path = downstream_smoke_path / "falsiflow_ai_eval" / "evidence.csv"
    downstream_smoke_placeholder_path = downstream_smoke_path / "falsiflow_ai_eval" / "evidence_placeholder_demo.csv"
    downstream_smoke_pass_path = downstream_smoke_path / "falsiflow_ai_eval" / "evidence_pass_demo.csv"
    downstream_smoke_source_path = downstream_smoke_path / "falsiflow_ai_eval" / "source_files" / "ai_eval_raw_export.csv"
    downstream_product_smoke_path = root / "examples" / "downstream_product_metric_smoke"
    downstream_product_smoke_readme_path = downstream_product_smoke_path / "README.md"
    downstream_product_smoke_workflow_path = downstream_product_smoke_path / ".github" / "workflows" / "falsiflow-product-metric.yml"
    downstream_product_smoke_project_path = downstream_product_smoke_path / "falsiflow_product_metric" / "project.json"
    downstream_product_smoke_evidence_path = downstream_product_smoke_path / "falsiflow_product_metric" / "evidence.csv"
    downstream_product_smoke_placeholder_path = downstream_product_smoke_path / "falsiflow_product_metric" / "evidence_placeholder_demo.csv"
    downstream_product_smoke_pass_path = downstream_product_smoke_path / "falsiflow_product_metric" / "evidence_pass_demo.csv"
    downstream_product_smoke_source_path = downstream_product_smoke_path / "falsiflow_product_metric" / "source_files" / "product_metric_raw_export.csv"
    manifest_path = root / "MANIFEST.in"
    action_path = root / "action.yml"
    makefile_path = root / "Makefile"
    install_script_path = root / "scripts" / "install_local.sh"
    powershell_install_path = root / "scripts" / "install_local.ps1"
    github_ci_path = root / ".github" / "workflows" / "falsiflow.yml"
    github_pages_path = root / ".github" / "workflows" / "falsiflow-pages.yml"
    github_cross_platform_path = root / ".github" / "workflows" / "falsiflow-cross-platform.yml"
    github_external_evidence_path = root / ".github" / "workflows" / "falsiflow-external-evidence.yml"
    github_scorecard_path = root / ".github" / "workflows" / "falsiflow-scorecard.yml"
    github_publish_path = root / ".github" / "workflows" / "falsiflow-publish.yml"
    github_dependabot_path = root / ".github" / "dependabot.yml"
    github_issue_config_path = root / ".github" / "ISSUE_TEMPLATE" / "config.yml"
    github_bug_template_path = root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml"
    github_feature_template_path = root / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml"
    github_claim_gate_template_path = root / ".github" / "ISSUE_TEMPLATE" / "claim_gate_request.yml"
    github_launch_feedback_template_path = root / ".github" / "ISSUE_TEMPLATE" / "launch_feedback.yml"
    github_pr_template_path = root / ".github" / "PULL_REQUEST_TEMPLATE.md"
    gitignore_path = root / ".gitignore"
    init_path = root / "falsiflow" / "__init__.py"
    templates_path = root / "falsiflow" / "templates"
    package_downstream_pr_proof_strip_path = root / "falsiflow" / "assets" / "falsiflow_downstream_pr_proof_strip.svg"
    package_pr_story_reel_path = root / "falsiflow" / "assets" / "falsiflow_live_pr_story_reel.svg"
    init_version = package_init_version(init_path)

    add("package_init_exists", init_path.exists(), "falsiflow/__init__.py exists.", init_path)
    add("package_downstream_pr_proof_strip_exists", package_downstream_pr_proof_strip_path.exists() and package_downstream_pr_proof_strip_path.stat().st_size > 0, "Packaged downstream PR proof-strip asset exists and is non-empty.", package_downstream_pr_proof_strip_path)
    add("package_pr_story_reel_exists", package_pr_story_reel_path.exists() and package_pr_story_reel_path.stat().st_size > 0, "Packaged live PR story reel asset exists and is non-empty.", package_pr_story_reel_path)

    if pyproject_path.exists():
        add("pyproject_exists", True, "pyproject.toml exists.", pyproject_path)
        add("readme_exists", readme_path.exists() and readme_path.stat().st_size > 0, "README.md exists and is non-empty.", readme_path)
        add("license_exists", license_path.exists() and license_path.stat().st_size > 0, "LICENSE exists and is non-empty.", license_path)
        add("changelog_exists", changelog_path.exists() and changelog_path.stat().st_size > 0, "CHANGELOG.md exists and is non-empty.", changelog_path)
        add("contributing_exists", contributing_path.exists() and contributing_path.stat().st_size > 0, "CONTRIBUTING.md exists and is non-empty.", contributing_path)
        add("citation_exists", citation_path.exists() and citation_path.stat().st_size > 0, "CITATION.cff exists and is non-empty.", citation_path)
        add("code_of_conduct_exists", code_of_conduct_path.exists() and code_of_conduct_path.stat().st_size > 0, "CODE_OF_CONDUCT.md exists and is non-empty.", code_of_conduct_path)
        add("governance_exists", governance_path.exists() and governance_path.stat().st_size > 0, "GOVERNANCE.md exists and is non-empty.", governance_path)
        add("release_guide_exists", release_path.exists() and release_path.stat().st_size > 0, "RELEASE.md exists and is non-empty.", release_path)
        add("security_policy_exists", security_path.exists() and security_path.stat().st_size > 0, "SECURITY.md exists and is non-empty.", security_path)
        add("support_policy_exists", support_path.exists() and support_path.stat().st_size > 0, "SUPPORT.md exists and is non-empty.", support_path)
        add("responsible_use_exists", responsible_use_path.exists() and responsible_use_path.stat().st_size > 0, "RESPONSIBLE_USE.md exists and is non-empty.", responsible_use_path)
        add("roadmap_exists", roadmap_path.exists() and roadmap_path.stat().st_size > 0, "ROADMAP.md exists and is non-empty.", roadmap_path)
        add("adoption_priorities_exists", adoption_priorities_path.exists() and adoption_priorities_path.stat().st_size > 0, "Adoption priorities doc exists and is non-empty.", adoption_priorities_path)
        add("launch_execution_exists", launch_execution_path.exists() and launch_execution_path.stat().st_size > 0, "Launch execution doc exists and is non-empty.", launch_execution_path)
        add("architecture_exists", architecture_path.exists() and architecture_path.stat().st_size > 0, "Architecture doc exists and is non-empty.", architecture_path)
        add("cli_reference_exists", cli_reference_path.exists() and cli_reference_path.stat().st_size > 0, "Generated CLI reference exists and is non-empty.", cli_reference_path)
        add("data_contract_exists", data_contract_path.exists() and data_contract_path.stat().st_size > 0, "Data contract doc exists and is non-empty.", data_contract_path)
        add("adapter_profiles_exists", adapter_profiles_path.exists() and adapter_profiles_path.stat().st_size > 0, "Adapter profiles doc exists and is non-empty.", adapter_profiles_path)
        add("local_llm_eval_quickstart_exists", local_llm_eval_path.exists() and local_llm_eval_path.stat().st_size > 0, "Local LLM eval quickstart doc exists and is non-empty.", local_llm_eval_path)
        add("mcp_docs_exists", mcp_path.exists() and mcp_path.stat().st_size > 0, "MCP server doc exists and is non-empty.", mcp_path)
        add("casebook_check_exists", casebook_check_path.exists() and casebook_check_path.stat().st_size > 0, "Casebook check doc exists and is non-empty.", casebook_check_path)
        add("demo_pr_playbook_exists", demo_pr_playbook_path.exists() and demo_pr_playbook_path.stat().st_size > 0, "Demo PR playbook doc exists and is non-empty.", demo_pr_playbook_path)
        add("github_action_examples_exists", github_action_examples_path.exists() and github_action_examples_path.stat().st_size > 0, "GitHub Action examples doc exists and is non-empty.", github_action_examples_path)
        add("positioning_exists", positioning_path.exists() and positioning_path.stat().st_size > 0, "Positioning and casebook doc exists and is non-empty.", positioning_path)
        add("public_casebook_exists", public_casebook_path.exists() and public_casebook_path.stat().st_size > 0, "Public casebook doc exists and is non-empty.", public_casebook_path)
        add("rag_quality_gate_proposal_exists", rag_quality_gate_proposal_path.exists() and rag_quality_gate_proposal_path.stat().st_size > 0, "RAG quality gate proposal doc exists and is non-empty.", rag_quality_gate_proposal_path)
        add("pypi_trusted_publishing_exists", pypi_trusted_publishing_path.exists() and pypi_trusted_publishing_path.stat().st_size > 0, "PyPI trusted publishing runbook exists and is non-empty.", pypi_trusted_publishing_path)
        add("security_posture_exists", security_posture_path.exists() and security_posture_path.stat().st_size > 0, "Security posture doc exists and is non-empty.", security_posture_path)
        add("template_authoring_exists", template_authoring_path.exists() and template_authoring_path.stat().st_size > 0, "Template authoring doc exists and is non-empty.", template_authoring_path)
        add("troubleshooting_exists", troubleshooting_path.exists() and troubleshooting_path.stat().st_size > 0, "Troubleshooting doc exists and is non-empty.", troubleshooting_path)
        add("downstream_pr_proof_strip_exists", downstream_pr_proof_strip_path.exists() and downstream_pr_proof_strip_path.stat().st_size > 0, "Downstream PR proof-strip SVG exists and is non-empty.", downstream_pr_proof_strip_path)
        add("downstream_pr_proof_strip_png_exists", downstream_pr_proof_strip_png_path.exists() and downstream_pr_proof_strip_png_path.stat().st_size > 0, "Downstream PR proof-strip PNG exists and is non-empty for social previews.", downstream_pr_proof_strip_png_path)
        add("readme_pr_story_reel_exists", readme_pr_story_reel_path.exists() and readme_pr_story_reel_path.stat().st_size > 0, "README live PR story reel SVG exists and is non-empty.", readme_pr_story_reel_path)
        add("readme_proof_strip_exists", readme_proof_strip_path.exists() and readme_proof_strip_path.stat().st_size > 0, "README proof-strip SVG exists and is non-empty.", readme_proof_strip_path)
        add("readme_demo_strip_exists", readme_demo_strip_path.exists() and readme_demo_strip_path.stat().st_size > 0, "README 30-second demo SVG exists and is non-empty.", readme_demo_strip_path)
        add("walkthrough_exists", walkthrough_path.exists() and walkthrough_path.stat().st_size > 0, "examples/README.md exists and is non-empty.", walkthrough_path)
        downstream_smoke_files = [
            downstream_smoke_readme_path,
            downstream_smoke_workflow_path,
            downstream_smoke_project_path,
            downstream_smoke_evidence_path,
            downstream_smoke_placeholder_path,
            downstream_smoke_pass_path,
            downstream_smoke_source_path,
        ]
        add("downstream_ai_eval_smoke_fixture_exists", all(path.exists() and path.stat().st_size > 0 for path in downstream_smoke_files), "Downstream AI eval smoke fixture includes README, workflow, project, placeholder, pass, evidence, and source files.", downstream_smoke_path)
        downstream_product_smoke_files = [
            downstream_product_smoke_readme_path,
            downstream_product_smoke_workflow_path,
            downstream_product_smoke_project_path,
            downstream_product_smoke_evidence_path,
            downstream_product_smoke_placeholder_path,
            downstream_product_smoke_pass_path,
            downstream_product_smoke_source_path,
        ]
        add("downstream_product_metric_smoke_fixture_exists", all(path.exists() and path.stat().st_size > 0 for path in downstream_product_smoke_files), "Downstream product metric smoke fixture includes README, workflow, project, placeholder, pass, evidence, and source files.", downstream_product_smoke_path)
        add("manifest_exists", manifest_path.exists() and manifest_path.stat().st_size > 0, "MANIFEST.in exists and is non-empty.", manifest_path)
        add("github_action_exists", action_path.exists() and action_path.stat().st_size > 0, "Reusable GitHub Action exists and is non-empty.", action_path)

        pyproject_text = pyproject_path.read_text(encoding="utf-8")
        readme_text = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
        license_text = license_path.read_text(encoding="utf-8") if license_path.exists() else ""
        changelog_text = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
        contributing_text = contributing_path.read_text(encoding="utf-8") if contributing_path.exists() else ""
        citation_text = citation_path.read_text(encoding="utf-8") if citation_path.exists() else ""
        code_of_conduct_text = code_of_conduct_path.read_text(encoding="utf-8") if code_of_conduct_path.exists() else ""
        governance_text = governance_path.read_text(encoding="utf-8") if governance_path.exists() else ""
        release_text = release_path.read_text(encoding="utf-8") if release_path.exists() else ""
        security_text = security_path.read_text(encoding="utf-8") if security_path.exists() else ""
        support_text = support_path.read_text(encoding="utf-8") if support_path.exists() else ""
        responsible_use_text = responsible_use_path.read_text(encoding="utf-8") if responsible_use_path.exists() else ""
        roadmap_text = roadmap_path.read_text(encoding="utf-8") if roadmap_path.exists() else ""
        adoption_priorities_text = adoption_priorities_path.read_text(encoding="utf-8") if adoption_priorities_path.exists() else ""
        launch_plan_text = launch_plan_path.read_text(encoding="utf-8") if launch_plan_path.exists() else ""
        launch_execution_text = launch_execution_path.read_text(encoding="utf-8") if launch_execution_path.exists() else ""
        architecture_text = architecture_path.read_text(encoding="utf-8") if architecture_path.exists() else ""
        cli_reference_text = cli_reference_path.read_text(encoding="utf-8") if cli_reference_path.exists() else ""
        data_contract_text = data_contract_path.read_text(encoding="utf-8") if data_contract_path.exists() else ""
        adapter_profiles_text = adapter_profiles_path.read_text(encoding="utf-8") if adapter_profiles_path.exists() else ""
        local_llm_eval_text = local_llm_eval_path.read_text(encoding="utf-8") if local_llm_eval_path.exists() else ""
        mcp_text = mcp_path.read_text(encoding="utf-8") if mcp_path.exists() else ""
        casebook_check_text = casebook_check_path.read_text(encoding="utf-8") if casebook_check_path.exists() else ""
        demo_pr_playbook_text = demo_pr_playbook_path.read_text(encoding="utf-8") if demo_pr_playbook_path.exists() else ""
        github_action_examples_text = github_action_examples_path.read_text(encoding="utf-8") if github_action_examples_path.exists() else ""
        positioning_text = positioning_path.read_text(encoding="utf-8") if positioning_path.exists() else ""
        public_casebook_text = public_casebook_path.read_text(encoding="utf-8") if public_casebook_path.exists() else ""
        rag_quality_gate_proposal_text = rag_quality_gate_proposal_path.read_text(encoding="utf-8") if rag_quality_gate_proposal_path.exists() else ""
        pypi_trusted_publishing_text = pypi_trusted_publishing_path.read_text(encoding="utf-8") if pypi_trusted_publishing_path.exists() else ""
        security_posture_text = security_posture_path.read_text(encoding="utf-8") if security_posture_path.exists() else ""
        template_authoring_text = template_authoring_path.read_text(encoding="utf-8") if template_authoring_path.exists() else ""
        troubleshooting_text = troubleshooting_path.read_text(encoding="utf-8") if troubleshooting_path.exists() else ""
        downstream_pr_proof_strip_text = downstream_pr_proof_strip_path.read_text(encoding="utf-8") if downstream_pr_proof_strip_path.exists() else ""
        readme_pr_story_reel_text = readme_pr_story_reel_path.read_text(encoding="utf-8") if readme_pr_story_reel_path.exists() else ""
        readme_proof_strip_text = readme_proof_strip_path.read_text(encoding="utf-8") if readme_proof_strip_path.exists() else ""
        readme_demo_strip_text = readme_demo_strip_path.read_text(encoding="utf-8") if readme_demo_strip_path.exists() else ""
        walkthrough_text = walkthrough_path.read_text(encoding="utf-8") if walkthrough_path.exists() else ""
        downstream_smoke_readme_text = downstream_smoke_readme_path.read_text(encoding="utf-8") if downstream_smoke_readme_path.exists() else ""
        downstream_smoke_workflow_text = downstream_smoke_workflow_path.read_text(encoding="utf-8") if downstream_smoke_workflow_path.exists() else ""
        downstream_smoke_evidence_text = downstream_smoke_evidence_path.read_text(encoding="utf-8") if downstream_smoke_evidence_path.exists() else ""
        downstream_smoke_placeholder_text = downstream_smoke_placeholder_path.read_text(encoding="utf-8") if downstream_smoke_placeholder_path.exists() else ""
        downstream_smoke_pass_text = downstream_smoke_pass_path.read_text(encoding="utf-8") if downstream_smoke_pass_path.exists() else ""
        downstream_product_smoke_readme_text = downstream_product_smoke_readme_path.read_text(encoding="utf-8") if downstream_product_smoke_readme_path.exists() else ""
        downstream_product_smoke_workflow_text = downstream_product_smoke_workflow_path.read_text(encoding="utf-8") if downstream_product_smoke_workflow_path.exists() else ""
        downstream_product_smoke_evidence_text = downstream_product_smoke_evidence_path.read_text(encoding="utf-8") if downstream_product_smoke_evidence_path.exists() else ""
        downstream_product_smoke_placeholder_text = downstream_product_smoke_placeholder_path.read_text(encoding="utf-8") if downstream_product_smoke_placeholder_path.exists() else ""
        downstream_product_smoke_pass_text = downstream_product_smoke_pass_path.read_text(encoding="utf-8") if downstream_product_smoke_pass_path.exists() else ""
        manifest_text = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else ""
        action_text = action_path.read_text(encoding="utf-8") if action_path.exists() else ""
        makefile_text = makefile_path.read_text(encoding="utf-8") if makefile_path.exists() else ""
        install_script_text = install_script_path.read_text(encoding="utf-8") if install_script_path.exists() else ""
        powershell_install_text = powershell_install_path.read_text(encoding="utf-8") if powershell_install_path.exists() else ""
        github_ci_text = github_ci_path.read_text(encoding="utf-8") if github_ci_path.exists() else ""
        github_pages_text = github_pages_path.read_text(encoding="utf-8") if github_pages_path.exists() else ""
        github_cross_platform_text = github_cross_platform_path.read_text(encoding="utf-8") if github_cross_platform_path.exists() else ""
        github_external_evidence_text = github_external_evidence_path.read_text(encoding="utf-8") if github_external_evidence_path.exists() else ""
        github_scorecard_text = github_scorecard_path.read_text(encoding="utf-8") if github_scorecard_path.exists() else ""
        github_publish_text = github_publish_path.read_text(encoding="utf-8") if github_publish_path.exists() else ""
        github_dependabot_text = github_dependabot_path.read_text(encoding="utf-8") if github_dependabot_path.exists() else ""
        github_issue_config_text = github_issue_config_path.read_text(encoding="utf-8") if github_issue_config_path.exists() else ""
        github_bug_template_text = github_bug_template_path.read_text(encoding="utf-8") if github_bug_template_path.exists() else ""
        github_feature_template_text = github_feature_template_path.read_text(encoding="utf-8") if github_feature_template_path.exists() else ""
        github_claim_gate_template_text = github_claim_gate_template_path.read_text(encoding="utf-8") if github_claim_gate_template_path.exists() else ""
        github_launch_feedback_template_text = github_launch_feedback_template_path.read_text(encoding="utf-8") if github_launch_feedback_template_path.exists() else ""
        github_pr_template_text = github_pr_template_path.read_text(encoding="utf-8") if github_pr_template_path.exists() else ""
        gitignore_text = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
        gitignore_patterns = {line.strip() for line in gitignore_text.splitlines() if line.strip() and not line.lstrip().startswith("#")}
        action_description_colon_conflicts = [
            line.strip()
            for line in action_text.splitlines()
            if re.match(r"\s*description:\s+[^\"'].*:\s", line)
        ]

        data = pyproject_data(pyproject_path)
        project_name = get_nested(data, "project", "name") if data else None
        project_version = get_nested(data, "project", "version") if data else None
        requires_python = get_nested(data, "project", "requires-python") if data else None
        readme_value = get_nested(data, "project", "readme") if data else None
        license_value = get_nested(data, "project", "license") if data else None
        keywords = get_nested(data, "project", "keywords") if data else None
        classifiers = get_nested(data, "project", "classifiers") if data else None
        project_urls = get_nested(data, "project", "urls") if data else None
        scripts = get_nested(data, "project", "scripts") if data else None
        packages = get_nested(data, "tool", "setuptools", "packages") if data else None
        package_data = get_nested(data, "tool", "setuptools", "package-data", "falsiflow") if data else None
        current_version = str(project_version or init_version)
        readme_first_screen = readme_text[:2400]
        readme_image_targets = re.findall(r"!\[[^\]]*\]\(([^)\s]+)", readme_text)
        relative_readme_asset_images = [
            target for target in readme_image_targets if target.startswith("docs/assets/")
        ]

        add("pyproject_name", project_name == "falsiflow" if data else 'name = "falsiflow"' in pyproject_text, "Project name is falsiflow.", pyproject_path)
        add("pyproject_version", bool(project_version) if data else bool(re.search(r'^version\s*=\s*"[^"]+"', pyproject_text, flags=re.MULTILINE)), "Project version is declared.", pyproject_path)
        add(
            "pyproject_requires_python",
            requires_python == EXPECTED_REQUIRES_PYTHON if data else f'requires-python = "{EXPECTED_REQUIRES_PYTHON}"' in pyproject_text,
            f"Project declares supported Python range {EXPECTED_REQUIRES_PYTHON}.",
            pyproject_path,
        )
        if data:
            add("version_matches_init", bool(project_version) and project_version == init_version, "pyproject version matches falsiflow.__version__.", init_path)
        else:
            add("version_matches_init", init_version in pyproject_text and bool(init_version), "pyproject version matches falsiflow.__version__.", init_path)
        project_url_values = {str(key): str(value) for key, value in project_urls.items()} if isinstance(project_urls, dict) else {}
        add(
            "pyproject_keywords",
            EXPECTED_PYPROJECT_KEYWORDS <= keyword_values(keywords) if data else all(f'"{keyword}"' in pyproject_text for keyword in EXPECTED_PYPROJECT_KEYWORDS),
            "Project metadata includes discovery keywords for evidence, provenance, templates, R&D, and quality gates.",
            pyproject_path,
        )
        add(
            "pyproject_classifiers",
            EXPECTED_PYPROJECT_CLASSIFIERS <= string_values(classifiers) if data else all(f'"{classifier}"' in pyproject_text for classifier in EXPECTED_PYPROJECT_CLASSIFIERS),
            "Project metadata includes audience, status, Python-version, OS, and topic classifiers.",
            pyproject_path,
        )
        add(
            "pyproject_project_urls",
            EXPECTED_PROJECT_URLS.items() <= project_url_values.items() if data else all(name in pyproject_text and url in pyproject_text for name, url in EXPECTED_PROJECT_URLS.items()),
            "Project metadata links homepage, docs, architecture, data contract, adapter profiles, casebook check, template authoring, troubleshooting, source, issues, changelog, demo, live PR proof links, downstream proof links, launch article, citation, and governance URLs.",
            pyproject_path,
        )
        add("readme_declared", readme_value == "README.md" if data else 'readme = "README.md"' in pyproject_text, "pyproject readme points to README.md.", pyproject_path)
        license_files = get_nested(data, "project", "license-files") if data else []
        add("license_declared", license_value == "MIT" and "LICENSE" in (license_files if isinstance(license_files, list) else []) if data else 'license = "MIT"' in pyproject_text and 'license-files = ["LICENSE"]' in pyproject_text, "pyproject declares the MIT SPDX license and includes the LICENSE file.", pyproject_path)
        add("console_script", isinstance(scripts, dict) and scripts.get("falsiflow") == "falsiflow.cli:main" if data else 'falsiflow = "falsiflow.cli:main"' in pyproject_text, "Console script points to falsiflow.cli:main.", pyproject_path)
        add("setuptools_package", isinstance(packages, list) and "falsiflow" in packages if data else 'packages = ["falsiflow"]' in pyproject_text, "setuptools includes the falsiflow package.", pyproject_path)
        expected_data_patterns = {"assets/*.svg", "templates/*/*.json", "templates/*/*.csv", "templates/*/source_files/*.csv"}
        if data:
            package_data_set = set(package_data) if isinstance(package_data, list) else set()
            package_data_ready = expected_data_patterns <= package_data_set
        else:
            package_data_ready = all(pattern in pyproject_text for pattern in expected_data_patterns)
        add("template_package_data", package_data_ready, "Package data includes template JSON, CSV, and source CSV files.", pyproject_path)
        add("readme_release_commands", all(token in readme_text for token in ["release-check", "verify-bundle", "falsiflow selftest"]), "README documents release, verification, and selftest commands.", readme_path)
        add("readme_community_health_entry", all(token in readme_text for token in ["CODE_OF_CONDUCT.md", "SUPPORT.md", "ROADMAP.md", "Community Entry Points"]), "README links code of conduct, support, and roadmap from community entry points.", readme_path)
        add("readme_citation_governance_entry", all(token in readme_text for token in ["CITATION.cff", "GOVERNANCE.md", "Citation and governance"]), "README links citation and governance entry points.", readme_path)
        add("readme_architecture_entry", all(token in readme_text for token in ["falsiflow_architecture.md", "module map", "extension-point"]), "README links the architecture and extension-point notes.", readme_path)
        add("readme_data_contract_entry", all(token in readme_text for token in ["falsiflow_data_contract.md", "evidence CSV", "JSON status", "CI/ELN/LIMS"]), "README links the data contract for evidence CSV, JSON status, and integration boundaries.", readme_path)
        add("readme_adapter_profiles_entry", all(token in readme_text for token in ["falsiflow_adapter_profiles.md", "vendor-measurement", "instrument-export", "plate-reader", "falsiflow_local_llm_eval.md", "Ollama", "LM Studio", "llama.cpp"]), "README links adapter profile guidance for vendor, instrument, plate-reader, and local LLM eval imports.", readme_path)
        add("readme_mcp_entry", all(token in readme_text for token in ["falsiflow_mcp.md", "falsiflow mcp --selftest --json", "mcp_selftest_ready", "falsiflow mcp", "no network listener", "does not run models"]), "README documents the local stdio MCP server, one-command selftest, and no-network/no-model boundary for agent integrations.", readme_path)
        add("readme_template_authoring_entry", all(token in readme_text for token in ["falsiflow_template_authoring.md", "template authoring", "placeholder demo"]), "README links template authoring guidance for placeholder demos and release flow.", readme_path)
        add("readme_troubleshooting_entry", all(token in readme_text for token in ["falsiflow_troubleshooting.md", "claim_check_blocked", "external_blocked"]), "README links troubleshooting for blocked commands and external readiness.", readme_path)
        add("readme_security_posture_entry", all(token in readme_text for token in ["falsiflow_security_posture.md", "Dependabot", "OpenSSF Scorecard", "supply-chain release gates"]), "README links the security posture, dependency automation, Scorecard, and supply-chain gates.", readme_path)
        add("readme_adoption_entry", all(token in readme_text for token in ["Project Priorities", "Five-Minute Quickstart", "quickstart", "doctor", "Adoption Path", "falsiflow_adoption_priorities.md"]), "README documents adoption priorities and first-run path.", readme_path)
        add("readme_cli_reference_entry", all(token in readme_text for token in ["falsiflow_cli_reference.md", "falsiflow cli-reference"]), "README links the generated CLI reference.", readme_path)
        add("readme_positioning_entry", all(token in readme_text for token in ["falsiflow_positioning.md", "spreadsheets", "ELN/LIMS", "workflow orchestrators", "Great Expectations", "Evidently", "Deepchecks", "MLflow"]), "README links the positioning, comparison casebook, and named neighboring-tool boundaries.", readme_path)
        add("readme_public_casebook_entry", all(token in readme_text for token in ["falsiflow_public_casebook.md", "Biointerface", "AI claim", "product metric", "vendor", "wetware"]), "README links the public casebook and names its starter-template coverage.", readme_path)
        add("readme_rag_quality_gate_proposal_entry", all(token in readme_text for token in ["falsiflow_rag_quality_gate_proposal.md", "RAG quality gate", "evaluation-set", "provenance", "retrieval quality", "answer faithfulness", "placeholder-blocked evidence rows"]), "README links the proposed RAG quality gate starter template and names its evidence dimensions.", readme_path)
        add("readme_casebook_check_entry", all(token in readme_text for token in ["falsiflow_casebook_check.md", "casebook-check", "positive demos", "placeholder blockers"]), "README links the casebook check and documents machine-verifiable public proof paths.", readme_path)
        add("readme_demo_pr_entry", all(token in readme_text for token in ["falsiflow_demo_pr_playbook.md", "public demo PR", "placeholder evidence", "source-backed evidence"]), "README links the public demo PR playbook for blocked and ready claim-gate demonstrations.", readme_path)
        add("readme_downstream_pr_proof_strip_asset", all(token in readme_text + demo_pr_playbook_text + launch_plan_text for token in ["docs/assets/falsiflow_downstream_pr_proof_strip.svg", "falsiflow-downstream-ai-eval-demo", "26711652990", "26711669112"]) and all(token in downstream_pr_proof_strip_text for token in ["Downstream PR #1", "claim_check_blocked", "claim_check_ready", "26711652990", "26711669112", "does not prove the model is good, safe, or shippable"]), "README and launch docs embed or link the shareable downstream PR proof strip with blocked and ready CI proof links.", downstream_pr_proof_strip_path)
        add("package_downstream_pr_proof_strip_matches_docs", package_downstream_pr_proof_strip_path.read_text(encoding="utf-8") == downstream_pr_proof_strip_text if package_downstream_pr_proof_strip_path.exists() and downstream_pr_proof_strip_text else False, "Packaged downstream PR proof strip matches the README/docs asset.", package_downstream_pr_proof_strip_path)
        add("readme_live_pr_story_reel_asset", "docs/assets/falsiflow_live_pr_story_reel.svg" in readme_text and all(token in readme_pr_story_reel_text for token in ["Live PR Story", "PR #17", "claim_check_blocked", "claim_check_ready", "26708459093", "26708472653"]), "README documents the packaged live PR story reel with blocked and ready CI proof links.", readme_pr_story_reel_path)
        add("package_pr_story_reel_matches_docs", package_pr_story_reel_path.read_text(encoding="utf-8") == readme_pr_story_reel_text if package_pr_story_reel_path.exists() and readme_pr_story_reel_text else False, "Packaged live PR story reel matches the README/docs asset.", package_pr_story_reel_path)
        add("readme_visual_asset", all(token in readme_text for token in ["docs/assets/falsiflow_proof_strip.svg", "Falsiflow evidence-gated claim workflow"]) and all(token in readme_proof_strip_text for token in ["claim_ready after proof", "claim_blocked on gaps", "Source files", "Review + release checks"]), "README embeds a first-screen proof-strip visual that explains the evidence gate flow.", readme_proof_strip_path)
        add("readme_30_second_demo_asset", all(token in readme_text for token in ["docs/assets/falsiflow_30_second_demo.svg", "Falsiflow 30-second ready vs blocked demo", "30-second demo"]) and all(token in readme_demo_strip_text for token in ["30-second AI claim demo", "quickstart_ready", "claim_check_ready", "claim_check_blocked", "evidence_placeholder_demo.csv", "next actions"]), "README embeds a 30-second demo visual showing ready and blocked AI-claim paths.", readme_demo_strip_path)
        add("readme_pypi_renderable_image_urls", bool(readme_image_targets) and not relative_readme_asset_images and all(target.startswith("https://") for target in readme_image_targets), "README embeds images with absolute HTTPS URLs so PyPI long descriptions can render proof assets instead of keeping repository-relative paths.", readme_path)
        add("readme_first_screen_story", all(token in readme_first_screen for token in ["AI eval", "product metric", "R&D", "falsiflow quickstart --template ai_claim_evaluation", "quickstart_ready", "claim_check_ready", "claim_check_blocked", "GitHub Action", "Public demo", "PyPI trusted publishing"]), "README first screen names broad use cases, public demo, AI-claim quickstart, blocked placeholder behavior, GitHub Action adoption, and current PyPI trusted-publishing status.", readme_path)
        add("start_docs", all(token in readme_text for token in ["falsiflow start", "free localhost port", "falsiflow start --check --json", "beginner entry point"]), "README documents the beginner local app command.", readme_path)
        add("install_docs", all(token in readme_text for token in ["scripts/install_local.sh", "make install-local", "make start", "FALSIFLOW_REPO_URL", "virtual environment"]), "README documents one-command local installation.", readme_path)
        add("install_script", all(token in install_script_text for token in ["FALSIFLOW_REPO_URL", "python3 -m venv", "pip install -e", "falsiflow\" start", "--from-local"]), "scripts/install_local.sh installs into a virtual environment and starts the local app.", install_script_path)
        add("powershell_install_script", all(token in powershell_install_text for token in ["FALSIFLOW_REPO_URL", "python -m venv", "pip install -e", "falsiflow.exe", "FromLocal"]), "scripts/install_local.ps1 installs into a virtual environment and starts the local app.", powershell_install_path)
        add("pipx_docs", all(token in readme_text + makefile_text for token in ["make pipx-install", "make pipx-start", "pipx install --force ."]), "README and Makefile document pipx installation.", readme_path)
        add("onboard_docs", all(token in readme_text for token in ["falsiflow onboard --check --json", "onboard_summary.json", "beginner-friendly next-step checklist"]), "README documents beginner onboarding.", readme_path)
        add("static_demo_docs", all(token in readme_text for token in ["falsiflow static-demo", "static_demo_summary.json", "GitHub Pages", "Netlify"]), "README documents static zero-install demo export.", readme_path)
        add("demo_package_docs", all(token in readme_text for token in ["falsiflow demo-package", "demo_package_summary.json", "external_url_required", "FALSIFLOW_PUBLIC_DEMO_URL"]), "README documents public demo packaging and hosted URL handoff.", readme_path)
        add("publish_kit_docs", all(token in readme_text for token in ["falsiflow publish-kit", "publish_handoff.json", "github_publish_commands.sh", "account_action_required", "external_evidence_template.json", "public_release_evidence.json", "public_release_evidence.md", "release_rehearsal.json", "release_rehearsal.md", "public release rehearsal", "Scorecard", "casebook-replay"]), "README documents the public release handoff kit, evidence ledger, and release rehearsal for account-bound steps.", readme_path)
        add("launch_kit_docs", all(token in readme_text for token in ["falsiflow launch-kit", "launch_summary.json", "proof_card.md", "announcement.md", "demo_script.md", "readme_proof_strip.svg", "social_preview.svg", "github_repo_profile.md", "launch_posts.md", "Channel Checklist", "Hacker News", "Reddit", "LinkedIn", "awesome lists", "launch_metrics.json", "launch_metrics.md", "public_release_evidence.md", "release_rehearsal.md", "maintainer_checklist.md"]), "README documents public launch materials, proof-card generation, social preview, repo profile, channel-aware launch posts, launch metrics, publish evidence ledger, release rehearsal, and README proof-strip asset.", readme_path)
        add("launch_metrics_docs", all(token in readme_text + adoption_priorities_text + roadmap_text for token in ["launch metrics tracker", "GitHub traffic", "referrers", "stars", "forks", "clones", "demo visits", "install/download signals", "Post-Launch Metrics Review", "launch_metrics.json", "launch_metrics.md", "weekly maintainer review", "traction signals", "local/private validation", "concrete follow-up issues", "verification command"]), "README, adoption priorities, and roadmap document post-launch metrics tracking, weekly review, validation boundaries, and concrete follow-up issues for the 1k-star path.", readme_path)
        add("launch_execution_docs", all(token in launch_execution_text for token in ["Falsiflow Launch Execution", "Pre-public-post baseline", "0 stars", "2 forks", "open issue #22 only", "open PR #17 only", "falsiflow-external-evidence.yml", "pre-launch seed queue is complete", "24-hour post-public-post metrics review", "claim_check_blocked", "claim_check_ready"]), "Launch execution doc records the current pre-public-post baseline, completed seed queue, external evidence workflow, and blocked-to-ready launch copy.", launch_execution_path)
        add("external_check_docs", all(token in readme_text for token in ["falsiflow external-evidence", "falsiflow external-check", "external_readiness.json", "external_ready", "external_blocked", "--evidence", "FALSIFLOW_EXTERNAL_EVIDENCE", "FALSIFLOW_PYPI_PACKAGE_URL", "https://pypi.org/pypi/falsiflow/json", "expected_version", "published_version", "FALSIFLOW_PIPX_PUBLIC_VALIDATED", "public-package pipx", "Falsiflow External Evidence", "falsiflow_external_evidence.json"]), "README documents structured external evidence, public package evidence, PyPI JSON expected-version verification, CI evidence capture, and publication readiness checks.", readme_path)
        action_ref_ready = f"uses: AzurLiu/falsiflow@v{current_version}" in readme_text
        add("readme_github_action_docs", action_ref_ready and all(token in readme_text for token in ["action.yml", "mode: claim-check", "install-command", "GITHUB_ACTION_PATH", "falsiflow_github_action_examples.md", "examples/downstream_ai_eval_smoke", "examples/downstream_product_metric_smoke", "falsiflow-downstream-ai-eval-demo", "template-check", "external-check"]), "README documents downstream reusable GitHub Action adoption, versioned action pinning, default action-checkout installation, install override, live downstream proof, and copy-paste examples.", readme_path)
        versioned_action_ref = f"AzurLiu/falsiflow@v{current_version}"
        add("github_action_examples_docs", all(token in github_action_examples_text for token in ["Clean Downstream Smoke Repo", "examples/downstream_ai_eval_smoke", "examples/downstream_product_metric_smoke", "falsiflow-downstream-ai-eval-demo", "26711652990", "26711669112", "falsiflow_ai_eval/project.json", "falsiflow_ai_eval/evidence.csv", "falsiflow_product_metric/project.json", "falsiflow_product_metric/evidence.csv", "evidence_placeholder_demo.csv", "evidence_pass_demo.csv", "Product Metric Downstream Smoke", "product_metric_blocked", "product_metric_ready", "Local reproduction before pushing", "python3 -m venv .venv", "downstream_blocked", "downstream_ready", "AI Eval Claim Gate", "actions/checkout@v6", versioned_action_ref, "actions/upload-artifact@v7", "summary-json", "summary-md", "GITHUB_ACTION_PATH", "install-command", "claim_check_ready", "claim_check_blocked", "falsiflow_demo_pr_playbook.md"]), "GitHub Action examples document maintained AI eval and product metric downstream smoke fixtures, live downstream proof repo, exact local venv reproduction, claim gates, artifact uploads, default action checkout installs, install overrides, ready/blocked statuses, and the public demo PR playbook.", github_action_examples_path)
        add(
            "github_action_examples_rag_eval_snippet",
            all(
                token in github_action_examples_text
                for token in [
                    "RAG Eval Downstream Claim Gate",
                    "rag_quality_gate",
                    "falsiflow_rag_quality_gate_proposal.md",
                    "falsiflow_rag_eval/project.json",
                    "falsiflow_rag_eval/evidence.csv",
                    "uses: AzurLiu/falsiflow@v",
                    versioned_action_ref,
                    "mode: claim-check",
                    "project-dir: falsiflow_rag_eval",
                    "evidence: falsiflow_rag_eval/evidence.csv",
                    "rag_eval_blocked",
                    "rag_eval_ready",
                    "claim_check_blocked",
                    "claim_check_ready",
                    "artifact-first",
                    "does not call a hosted model, open an API",
                ]
            ),
            "GitHub Action examples include a compact downstream RAG eval claim-gate snippet with artifact-first boundaries, blocked and ready statuses, and links to the bundled RAG quality gate.",
            github_action_examples_path,
        )
        add(
            "downstream_ai_eval_live_proof_links",
            all(token in readme_text + github_action_examples_text + launch_plan_text for token in ["falsiflow-downstream-ai-eval-demo", "26711652990", "26711669112", "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1"]),
            "README, GitHub Action examples, and launch plan link the live downstream blocked-to-ready AI eval PR proof.",
            github_action_examples_path,
        )
        add(
            "downstream_ai_eval_smoke_fixture",
            all(token in downstream_smoke_workflow_text for token in ["Falsiflow Downstream AI Eval Smoke", "actions/checkout@v6", versioned_action_ref, "mode: claim-check", "project-dir: falsiflow_ai_eval", "evidence: falsiflow_ai_eval/evidence.csv", "actions/upload-artifact@v7"])
            and all(token in downstream_smoke_readme_text for token in ["copy-paste downstream repository fixture", "claim_check_blocked", "claim_check_ready", "evidence_pass_demo.csv", "evidence_placeholder_demo.csv"])
            and "dataset_pending" in downstream_smoke_evidence_text
            and downstream_smoke_evidence_text == downstream_smoke_placeholder_text
            and "exact_match_rate,0.86" in downstream_smoke_pass_text,
            "Downstream AI eval smoke fixture is a copy-paste repo skeleton whose default evidence is blocked and whose pass evidence is source-backed.",
            downstream_smoke_path,
        )
        add(
            "downstream_product_metric_smoke_fixture",
            all(token in downstream_product_smoke_workflow_text for token in ["Falsiflow Downstream Product Metric Smoke", "actions/checkout@v6", versioned_action_ref, "mode: claim-check", "project-dir: falsiflow_product_metric", "evidence: falsiflow_product_metric/evidence.csv", "actions/upload-artifact@v7"])
            and all(token in downstream_product_smoke_readme_text for token in ["copy-paste downstream repository fixture", "product metric claim", "activation lift", "claim_check_blocked", "claim_check_ready", "evidence_pass_demo.csv", "evidence_placeholder_demo.csv"])
            and "analysis_pending" in downstream_product_smoke_evidence_text
            and downstream_product_smoke_evidence_text == downstream_product_smoke_placeholder_text
            and "activation_rate,0.128" in downstream_product_smoke_pass_text,
            "Downstream product metric smoke fixture is a copy-paste repo skeleton whose default evidence is blocked and whose pass evidence is source-backed.",
            downstream_product_smoke_path,
        )
        add("workbench_docs", all(token in readme_text for token in ["workbench.html", "upload `project.json`", "raw source files", "ready/blocked status", "review flow", "evidence lineage", "repair checklist", "source manifest", "bundle verification"]), "README documents the browser workbench closed loop.", readme_path)
        add("discover_docs", all(token in readme_text for token in ["falsiflow discover", "evidence_records.json", "candidate_queue.json", "ai_used=false", "claim_ready=false"]), "README documents structured discovery outputs and the non-claim boundary.", readme_path)
        add("public_interface_docs", all(token in readme_text for token in ["falsiflow agent discover", "falsiflow candidate rank", "falsiflow assay-plan", "falsiflow evidence import"]), "README documents the structured discovery and evidence public interfaces.", readme_path)
        add("makefile_entrypoints", all(token in makefile_text for token in ["install-local:", "pipx-install:", "start:", "start-check:", "onboard-check:", "static-demo:", "demo-package:", "publish-kit:", "launch-kit:", "external-evidence:", "external-check:", "cli-reference:", "casebook-check:", "release-check:"]), "Makefile exposes install, pipx, start, onboarding, static-demo, demo-package, publish-kit, launch-kit, external-evidence, external-check, cli-reference, casebook-check, and release-check shortcuts.", makefile_path)
        add("github_ci_workflow", all(token in github_ci_text for token in ["regress_falsiflow_core.py", "release-check", "template-pack", "template-release", "demo-package", "agent discover", "evidence import", "evidence-record", "Reusable action smoke", "uses: ./", "ai_claim_evaluation"]), "GitHub Actions CI workflow covers regression, release-check, public interfaces, template supply-chain gates, and reusable-action smoke.", github_ci_path)
        add("github_action_entrypoint", all(token in action_text for token in ["using: composite", "actions/setup-python@v6", "install-command", "GITHUB_ACTION_PATH", "mode", "claim-check", "template-check", "casebook-check", "release-check", "adoption-check", "quickstart", "external-check", "summary-json", "GITHUB_OUTPUT"]), "Reusable GitHub Action exposes supported Falsiflow gates, current Python setup action, default action-checkout install, install override, and output metadata.", action_path)
        add("github_action_yaml_safe", not action_description_colon_conflicts and 'description: "Gate to run:' in action_text, "Reusable GitHub Action metadata quotes colon-bearing descriptions for YAML safety.", action_path)
        add("github_pages_workflow", all(token in github_pages_text for token in ["workflow_dispatch", "push:", "branches: [main]", "docs/public_demo/**", "demo-package", "upload-pages-artifact", "deploy-pages", "pages: write", "actions/configure-pages@v6", "enablement: true"]), "GitHub Pages workflow can enable Pages, build, auto-refresh, and deploy the static demo package.", github_pages_path)
        add("github_cross_platform_workflow", all(token in github_cross_platform_text for token in ["ubuntu-latest", "macos-latest", "windows-latest", "pipx", "install_local.ps1", "external-check"]), "GitHub Actions cross-platform workflow covers Linux, macOS, Windows, pipx, installers, and external-check smoke.", github_cross_platform_path)
        add("github_external_evidence_workflow", all(token in github_external_evidence_text for token in ["Falsiflow External Evidence", "public_demo_url", "pypi_package_url", "expected_version", "Expected PyPI package version", "Verify PyPI project URL", "https://pypi.org/pypi/falsiflow/json", "falsiflow_pypi_project.json", "falsiflow_expected_version.txt", "falsiflow_pypi_version.txt", "published_version", "tomllib", "pipx-smoke", "pipx-public-package", "windows-powershell", "pypi_package_url", "pipx_public_package", "falsiflow_external_evidence.json", "external-check", "upload-artifact"]), "GitHub Actions external-evidence workflow captures hosted demo, PyPI JSON expected-version package proof, checkout pipx, public-package pipx, Windows, and external-check artifacts for public readiness proof.", github_external_evidence_path)
        add("github_scorecard_workflow", all(token in github_scorecard_text for token in ["Falsiflow Scorecard", "ossf/scorecard-action@v2.4.3", "results_format: sarif", "publish_results: false", "scorecard-results.sarif", "github/codeql-action/upload-sarif@v4", "security-events: write", "id-token: write"]), "GitHub Actions Scorecard workflow records OpenSSF Scorecard SARIF security signals with the current CodeQL SARIF uploader and without publishing to the Scorecard webapp under SARIF upload permissions.", github_scorecard_path)
        add("github_pypi_publish_workflow", all(token in github_publish_text for token in ["python -m build", "python -m twine check dist/*", "pypa/gh-action-pypi-publish", "id-token: write"]), "GitHub Actions publish workflow builds, checks, stores, and can publish PyPI distributions.", github_publish_path)
        add("github_dependabot_config", all(token in github_dependabot_text for token in ["version: 2", 'package-ecosystem: "github-actions"', 'package-ecosystem: "pip"', "schedule:", 'interval: "weekly"']), "Dependabot is configured for weekly GitHub Actions and Python packaging updates.", github_dependabot_path)
        add("github_issue_templates", all([
            "blank_issues_enabled: false" in github_issue_config_text,
            "Bug report" in github_bug_template_text,
            "Command or workflow" in github_bug_template_text,
            "Feature request" in github_feature_template_text,
            "Success criteria" in github_feature_template_text,
            "Claim gate or template request" in github_claim_gate_template_text,
            "Responsible-use boundary" in github_claim_gate_template_text,
            "Launch feedback" in github_launch_feedback_template_text,
            "Entry point" in github_launch_feedback_template_text,
            "claim_ready" in github_launch_feedback_template_text,
        ]), "GitHub issue templates route bugs, feature requests, claim-gate/template requests, and public launch feedback.", github_issue_config_path)
        add("github_pr_template", all(token in github_pr_template_text for token in ["Verification", "claim_ready", "template-check", "Responsible use", "release-check"]), "GitHub pull request template asks for verification commands, evidence boundaries, and release impact.", github_pr_template_path)
        add("try_docs", all(token in readme_text for token in ["falsiflow try", "try_report.html", "Falsiflow Try", "dashboard.html"]), "README documents the low-friction local browser demo.", readme_path)
        add("launchpad_docs", all(token in readme_text for token in ["index.html", "Falsiflow Launchpad", "try_report_url", "wizard_url"]), "README documents the first-run local browser launchpad.", readme_path)
        add("wizard_docs", all(token in readme_text for token in ["falsiflow wizard", "falsiflow_wizard.html", "Falsiflow Browser Wizard", "plain-language presets", "falsiflow scaffold"]), "README documents the browser wizard for drafting claim gates.", readme_path)
        add("serve_docs", all(token in readme_text for token in ["falsiflow serve", "localhost", "serve_summary.json", "try_report.html"]), "README documents the localhost browser demo.", readme_path)
        add("quickstart_docs", all(token in readme_text for token in ["quickstart", "quickstart_summary.json", "next_commands", "Falsiflow Quickstart", "quickstart_ready", "quickstart_blocked"]), "README documents the one-command first-run quickstart.", readme_path)
        add("doctor_docs", all(token in readme_text for token in ["doctor", "doctor_summary.json", "repair_checklist", "Falsiflow Doctor", "doctor_ready", "doctor_blocked"]), "README documents the one-command project health diagnosis.", readme_path)
        add("claim_check_docs", all(token in readme_text for token in ["claim-check", "--project-dir", "claim_check.json", "Falsiflow Claim Check", "claim_check_ready", "claim_check_blocked", "Review Artifact Index", "source manifest", "bundle verification"]), "README documents the one-command claim gate and review artifact index.", readme_path)
        add("adoption_check_docs", all(token in readme_text for token in ["adoption-check", "adoption_check.json", "Falsiflow Adoption Check", "adoption_ready", "adoption_blocked", "repair_checklist", "adoption_recheck", "release_validation_status"]), "README documents the priority-readiness adoption gate.", readme_path)
        add("audit_review_docs", all(token in readme_text for token in ["audit_review.json", "audit_review.md", "Falsiflow Audit Review", "review_ready", "review_blocked"]), "README documents trusted audit review decision cards.", readme_path)
        add("template_check_docs", all(token in readme_text for token in ["template-check", "placeholder_evidence", "template_ready"]), "README documents external template authoring checks.", readme_path)
        add("template_scaffold_docs", all(token in readme_text for token in ["template-scaffold", "evidence_pass_demo.csv", "template_scaffolded"]), "README documents starter template generation.", readme_path)
        add("template_pack_docs", all(token in readme_text for token in ["template-pack", "verify-template-pack", "template_pack_verified"]), "README documents starter template packaging and verification.", readme_path)
        add("template_install_docs", all(token in readme_text for token in ["template-install", "falsiflow_template_index.json", "template_installed", "--require-attestation"]), "README documents verified starter template installation.", readme_path)
        add("template_registry_docs", all(token in readme_text for token in ["template-registry", "template-lock", "falsiflow_template_lock.json", "source_url", "--version"]), "README documents template registry and lockfile workflows.", readme_path)
        add("template_attestation_docs", all(token in readme_text for token in ["template-attest", "verify-template-attestation", "template_attestation_verified"]), "README documents template lock attestations and verification.", readme_path)
        add("template_policy_docs", all(token in readme_text for token in ["template-policy", "verify-template-policy", "template_policy_verified", "--policy"]), "README documents template adoption policies.", readme_path)
        add("template_release_docs", all(token in readme_text for token in ["template-release", "verify-template-release", "template_release_verified", "template_release_verification.md", "--release", "Review Artifact Index", "release manifest"]), "README documents template release bundles and release artifact indexes.", readme_path)
        add("template_gallery_docs", all(token in readme_text for token in ["template-gallery", "Falsiflow Template Gallery", "rfq_vendor_evidence", "biointerface_coatings", "wetware_support_hardware", "ai_claim_evaluation", "product_metric_launch"]), "README documents the template gallery and cross-domain starter breadth.", readme_path)
        add("license_mit", "MIT License" in license_text, "LICENSE declares MIT License.", license_path)
        add("changelog_current_version", bool(current_version) and current_version in changelog_text, "CHANGELOG includes the current version.", changelog_path)
        add("contributing_gates", all(token in contributing_text for token in ["release-check", "casebook-check", "claim_ready", "CHANGELOG.md", "CODE_OF_CONDUCT.md", "SUPPORT.md", "GOVERNANCE.md", "CITATION.cff", "ROADMAP.md", "falsiflow_architecture.md", "falsiflow_data_contract.md", "falsiflow_adapter_profiles.md", "falsiflow_casebook_check.md", "falsiflow_template_authoring.md", "falsiflow_troubleshooting.md"]), "CONTRIBUTING.md documents gates, tests, changelog, and community, citation, governance, architecture, data-contract, adapter-profile, casebook-check, template authoring, and troubleshooting expectations.", contributing_path)
        add("release_checklist", all(token in release_text for token in ["release_ready", "package_ready", "dist_ready", "release_validation_ready", "demo_package_ready", "publish_kit_ready", "launch_kit_ready", "launch_metrics.json", "launch_metrics.md", "public_release_evidence.json", "public_release_evidence.md", "release_rehearsal.json", "release_rehearsal.md", "public release rehearsal", "casebook_check_ready", "mcp --selftest --json", "mcp_selftest_ready", "external-evidence", "external_check_status", "public PyPI package URL", "PyPI JSON API", "expected_version", "published_version", "falsiflow_pypi_project.json", "falsiflow_expected_version.txt", "falsiflow_pypi_version.txt", "invalid-publisher", "falsiflow-publish.yml", "public-package pipx", "Falsiflow External Evidence", "falsiflow_external_evidence.json", "release-check", "casebook-check", "Release Review Artifact Index", "Review Artifact Index", "PyPI package metadata", "requires-python", "classifiers", "project URLs", "action.yml", "GitHub Action", "reusable-action quickstart smoke", "CODE_OF_CONDUCT.md", "SUPPORT.md", "ROADMAP.md", "CITATION.cff", "GOVERNANCE.md", "falsiflow_architecture.md", "falsiflow_data_contract.md", "falsiflow_adapter_profiles.md", "falsiflow_mcp.md", "falsiflow_casebook_check.md", "falsiflow_security_posture.md", "falsiflow_template_authoring.md", "falsiflow_troubleshooting.md", "falsiflow_1k_launch_plan.md", "Dependabot", "Falsiflow Scorecard"]), "RELEASE.md documents required release gates, MCP selftest, review artifact indexes, launch metrics, 1k launch plan, public release evidence ledger, release rehearsal, reusable GitHub Action, public package and PyPI JSON expected-version evidence, PyPI trusted-publisher recovery, casebook proof artifacts, external evidence workflow artifacts, package metadata checks, community trust files, citation/governance files, architecture docs, data-contract docs, adapter-profile docs, MCP docs, template authoring docs, troubleshooting docs, and security automation.", release_path)
        add("architecture_docs", all(token in architecture_text for token in ["Core Data Model", "Command Flow", "Module Map", "Release Invariants", "Extension Points", "falsiflow_data_contract.md", "claim_ready", "release-check"]), "Architecture doc explains data model, command flow, module map, release invariants, extension points, data contract, and release-check coverage.", architecture_path)
        add("data_contract_docs", all(token in data_contract_text for token in ["Stable Inputs", "Evidence CSV", "JSON Status Contract", "Report Artifacts", "Source Provenance", "JSON Schemas", "Integration Guidance", "claim_check_ready", "external_ready", "source_file"]), "Data contract doc explains stable inputs, evidence CSV fields, JSON status, report artifacts, source provenance, schemas, integration guidance, and ready statuses.", data_contract_path)
        add("adapter_profiles_docs", all(token in adapter_profiles_text for token in ["Falsiflow Adapter Profiles", "generic-wide", "vendor-measurement", "instrument-export", "plate-reader", "local-llm-eval", "falsiflow_local_llm_eval.md", "adapter_profile", "adapter_settings"]), "Adapter profile doc explains built-in CSV import profiles, local LLM eval handoff, summary fields, overrides, and coverage checks.", adapter_profiles_path)
        add("local_llm_eval_quickstart_docs", all(token in local_llm_eval_text for token in ["Falsiflow Local LLM Eval Quickstart", "Falsiflow does not need to run your local model, expose an API port", "Ollama", "LM Studio", "llama.cpp", "falsiflow quickstart --template ai_claim_evaluation", "source_files/local_eval_results.jsonl", "local_model_manifest.json", "--profile local-llm-eval", "falsiflow doctor --project-dir . --strict", "claim_check_ready", "bundle_verified"]), "Local LLM eval quickstart documents artifact-first runner handoff, required manifest fields, import command, doctor/claim-check path, and no-server boundary.", local_llm_eval_path)
        add("mcp_docs", all(token in mcp_text for token in ["Falsiflow MCP Server", "falsiflow mcp --selftest --json", "mcp_selftest_ready", "falsiflow mcp", "\"command\": \"falsiflow\"", "\"args\": [\"mcp\"]", "falsiflow.validate_claims", "falsiflow.check_bundle", "falsiflow.explain_blockers", "falsiflow.create_evidence_todo", "no network listener", "does not run models", "Why Stdio, Not An API Port?"]), "MCP docs explain the local stdio boundary, one-command selftest, generic client command shape, tools, resources, and no-network/no-model API boundary.", mcp_path)
        add("casebook_check_docs", all(token in casebook_check_text for token in ["Falsiflow Casebook Check", "casebook_check_ready", "Positive Demo Proof", "Blocked-path Proof", "Reviewer Replay Scripts", "casebook_reviewer_replay.sh", "casebook_reviewer_replay.ps1", "casebook_check.json", "template_check.json", "positive demos", "placeholder blockers"]), "Casebook check doc explains machine-verifiable casebook proofs, positive demos, placeholder blockers, reviewer replay scripts, and review artifacts.", casebook_check_path)
        add("demo_pr_playbook_docs", all(token in demo_pr_playbook_text for token in ["Falsiflow Demo PR Playbook", "Tiny LLM Eval Fixture", "dataset_pending", "exact_match_rate", "does not prove", "Blocked PR", "Ready PR", "evidence_placeholder_demo.csv", "evidence_pass_demo.csv", "claim_check_blocked", "claim_check_ready", versioned_action_ref, "actions/upload-artifact@v7", "GITHUB_ACTION_PATH", "30-second Recording Script"]), "Demo PR playbook documents a public blocked-to-ready AI eval claim gate demonstration, tiny LLM eval fixture, reusable action setup, recording guidance, and responsible-use boundary.", demo_pr_playbook_path)
        add("template_authoring_docs", all(token in template_authoring_text for token in ["Template Layout", "Evidence Contract", "Positive And Placeholder Demos", "Authoring Flow", "Admission Checklist", "template-check", "template-pack", "template-release", "source_files", "claim_ready"]), "Template authoring doc explains layout, evidence contract, placeholder demos, authoring flow, admission checklist, and verified template release commands.", template_authoring_path)
        add("troubleshooting_docs", all(token in troubleshooting_text for token in ["Fast Triage", "Install Or Start Fails", "claim_check_blocked", "doctor_blocked", "template_blocked", "release_blocked", "external_blocked", "public-package pipx", "public_release_evidence.md", "repair_checklist", "SUPPORT.md"]), "Troubleshooting doc explains fast triage, install/start, claim, doctor, template, release, external readiness, public package evidence, and support recovery paths.", troubleshooting_path)
        add("citation_metadata", all(token in citation_text for token in ["cff-version: 1.2.0", 'title: "Falsiflow"', "type: software", f'version: "{current_version}"', "repository-code", "Evidence-gated"]), "CITATION.cff records software citation metadata for public research reuse.", citation_path)
        add("security_policy", all(token in security_text for token in ["vulnerability", "verify-bundle", "SHA-256"]), "SECURITY.md documents vulnerability reporting and bundle integrity risks.", security_path)
        add("security_posture_docs", all(token in security_posture_text for token in ["local-first", "arbitrary code", "path traversal", "SHA-256", "Dependabot", "OpenSSF Scorecard", "public PyPI package URL", "public-package pipx", "release-check", "external-check --strict"]), "Security posture doc explains local runtime boundaries, bundle verification, dependency automation, Scorecard, public package evidence, and release gates.", security_posture_path)
        add("code_of_conduct_policy", all(token in code_of_conduct_text for token in ["Expected Behavior", "Unacceptable Behavior", "Reporting", "Enforcement", "claim_ready"]), "CODE_OF_CONDUCT.md documents behavior expectations, reporting, enforcement, and evidence-boundary conduct.", code_of_conduct_path)
        add("governance_policy", all(token in governance_text for token in ["Maintainer Responsibilities", "Decision Process", "Template Admission", "Release Ownership", "Security And Conduct", "claim_ready", "falsiflow_template_authoring.md"]), "GOVERNANCE.md documents maintainer responsibilities, decision process, template admission, release ownership, template authoring, and security/conduct routing.", governance_path)
        add("support_policy", all(token in support_text for token in ["Good Support Requests", "Where To Ask", "What Maintainers Can Help With", "What Maintainers Cannot Provide", "SECURITY.md", "CODE_OF_CONDUCT.md", "falsiflow_troubleshooting.md", "repair_checklist"]), "SUPPORT.md documents troubleshooting, support routes, useful report contents, and support boundaries.", support_path)
        add("responsible_use_policy", all(token in responsible_use_text for token in ["not proof", "regulatory compliance", "independent"]), "RESPONSIBLE_USE.md documents evidence limitations and independent validation boundaries.", responsible_use_path)
        add("roadmap_policy", all(token in roadmap_text for token in ["Now", "Next", "Later", "Not Planned", "Falsiflow External Evidence", "public release evidence ledger", "public release rehearsal", "claim_ready"]), "ROADMAP.md documents near-term direction, public release evidence, release rehearsal, later opportunities, and non-goals.", roadmap_path)
        add("adoption_priorities", all(token in adoption_priorities_text for token in ["Open-source entry point", "Trusted audit experience", "Generality proof", "Release and distribution", "User experience convergence"]), "Adoption priorities record the current optimization order.", adoption_priorities_path)
        add("cli_reference_docs", all(token in cli_reference_text for token in ["Falsiflow CLI Reference", "falsiflow start", "falsiflow cli-reference", "falsiflow mcp", "--selftest", "mcp_selftest_ready", "falsiflow release-check", "falsiflow external-evidence", "falsiflow evidence import", "falsiflow template-release"]), "Generated CLI reference documents first-run, MCP selftest, release, external evidence, import, and template commands.", cli_reference_path)
        add("positioning_casebook", all(token in positioning_text for token in ["Comparison Map", "Named Tool Boundaries", "Plain GitHub Actions Boundary", "Casebook", "Spreadsheet checklist", "CI test suite", "ELN or LIMS", "ML eval harness", "Materials database", "Workflow orchestrator", "Great Expectations", "Evidently", "Deepchecks", "MLflow", "Plain GitHub Actions", "evidence CSV", "source-file inventory", "repair checklist", "Decision Rubric"]), "Positioning doc explains when Falsiflow fits and how it differs from adjacent tool categories, named neighboring tools, and plain GitHub Actions.", positioning_path)
        add("public_casebook", all(token in public_casebook_text for token in ["Falsiflow Public Casebook", "Biointerface Coating Screen", "Neural Materials Interface", "AI Claim Evaluation", "Product Metric Launch", "Vendor Or External-Lab Handoff", "Wetware Support Hardware", "ai_claim_evaluation", "product_metric_launch", "Blocked-path proof", "Reviewer Rubric", "casebook_reviewer_replay.sh", "casebook_reviewer_replay.ps1", "falsiflow claim-check"]), "Public casebook documents concrete starter-template stories, blocked-path proofs, reviewer replay artifacts, and demo commands.", public_casebook_path)
        add("rag_quality_gate_proposal_docs", all(token in rag_quality_gate_proposal_text for token in ["Falsiflow RAG Quality Gate Proposal", "rag_quality_gate", "evaluation-set provenance", "retrieval quality", "answer faithfulness", "source coverage", "eval_set_pending", "recall_at_5", "claim_check_blocked", "claim_check_ready", "template-check", "--strict"]), "RAG quality gate proposal defines the future starter template, evidence fields, source files, blocked placeholder row, positive evidence row, and strict verification target.", rag_quality_gate_proposal_path)
        add("pypi_trusted_publishing_docs", all(token in pypi_trusted_publishing_text + readme_text + troubleshooting_text for token in ["Falsiflow PyPI Trusted Publishing", "invalid-publisher", "repo:AzurLiu/falsiflow:environment:pypi", "pending publisher", "existing-project trusted publisher", "project name: `falsiflow`", "falsiflow-publish.yml", "environment `pypi`", "workflow_dispatch rehearsal is not enough", "https://pypi.org/pypi/falsiflow/json", "0.1.2", "expected_version", "Falsiflow External Evidence", "falsiflow_expected_version.txt", "falsiflow_pypi_version.txt", "v0.1.16 README Rendering Check", "repository-relative Markdown image targets", "falsiflow_downstream_pr_proof_strip.png", "https://raw.githubusercontent.com/AzurLiu/falsiflow/main/docs/assets/falsiflow_downstream_pr_proof_strip.png", "pypi_description_rendering_inputs_ready"]), "PyPI trusted publishing runbook documents the current account-bound publisher claim, pending publisher and existing-project setup paths, required PyPI settings, release-triggered publish verification, expected-version verification, PyPI README rendering checks, and external evidence path.", pypi_trusted_publishing_path)
        add("walkthrough_commands", all(token in walkthrough_text for token in ["init", "claim-check", "claim_check_ready", "Downstream AI Eval Smoke", "Downstream Product Metric Smoke", "claim_check_blocked", "audit", "sources", "bundle", "verify-bundle", "release-check", "bundle_verified"]), "examples/README.md documents the end-to-end verified-bundle walkthrough plus downstream AI eval and product metric smoke fixtures.", walkthrough_path)
        add("manifest_release_docs", all(token in manifest_text for token in ["CHANGELOG.md", "CONTRIBUTING.md", "CITATION.cff", "CODE_OF_CONDUCT.md", "GOVERNANCE.md", "RELEASE.md", "SECURITY.md", "SUPPORT.md", "RESPONSIBLE_USE.md", "ROADMAP.md", "examples/README.md", "examples/downstream_ai_eval_smoke", "examples/downstream_product_metric_smoke", "docs/falsiflow_adoption_priorities.md", "docs/falsiflow_1k_launch_plan.md", "docs/falsiflow_launch_execution.md", "docs/falsiflow_architecture.md", "docs/falsiflow_cli_reference.md", "docs/falsiflow_data_contract.md", "docs/falsiflow_adapter_profiles.md", "docs/falsiflow_local_llm_eval.md", "docs/falsiflow_mcp.md", "docs/falsiflow_casebook_check.md", "docs/falsiflow_demo_pr_playbook.md", "docs/falsiflow_github_action_examples.md", "docs/falsiflow_public_issue_queue.md", "docs/falsiflow_positioning.md", "docs/falsiflow_public_casebook.md", "docs/falsiflow_rag_quality_gate_proposal.md", "docs/falsiflow_pypi_trusted_publishing.md", "docs/falsiflow_security_posture.md", "docs/falsiflow_template_authoring.md", "docs/falsiflow_troubleshooting.md", "docs/launch_articles", "docs/assets", "falsiflow/assets", "falsiflow_downstream_pr_proof_strip.svg", "falsiflow_30_second_demo.svg", "falsiflow_live_pr_story_reel.svg", "scripts/install_local.sh", "scripts/install_local.ps1", "Makefile", "action.yml", ".github/workflows", ".github/ISSUE_TEMPLATE", "launch_feedback.yml", ".github/PULL_REQUEST_TEMPLATE.md", ".github/dependabot.yml"]), "MANIFEST.in includes release, security, support, conduct, roadmap, responsible-use, citation, governance, launch plan, launch execution, launch articles, walkthrough, downstream smoke fixtures, architecture, CLI reference, data contract, adapter profiles, local LLM eval quickstart, MCP docs, casebook check, demo PR playbook, GitHub Action examples, public issue queue, positioning, public casebook, RAG quality gate proposal, PyPI trusted publishing, security posture, template authoring, troubleshooting, README visual assets, downstream PR proof strip, the 30-second demo visual, the live PR story reel, packaged static assets, installers, Makefile, reusable GitHub Action, workflows, community templates, launch feedback template, dependency automation, and adoption docs in source distributions.", manifest_path)
        add("gitignore_build_artifacts", {"build/", "dist/", "*.egg-info/"} <= gitignore_patterns, ".gitignore excludes local build caches and package metadata artifacts.", gitignore_path)
    else:
        add("installed_metadata_mode", True, "Source metadata files are absent; checking installed package metadata.", root)
        try:
            distribution = importlib_metadata.distribution("falsiflow")
            metadata = distribution.metadata
            entry_points = list(distribution.entry_points)
            installed_version = distribution.version
            installed_project_urls = metadata_project_urls(metadata)
            add("installed_name", metadata.get("Name", "").lower() == "falsiflow", "Installed package metadata name is falsiflow.", root)
            add("installed_version", bool(installed_version), "Installed package version is declared.", root)
            add("installed_version_matches_init", bool(init_version) and installed_version == init_version, "Installed version matches falsiflow.__version__.", init_path)
            add(
                "installed_requires_python",
                metadata.get("Requires-Python") == EXPECTED_REQUIRES_PYTHON,
                f"Installed metadata declares supported Python range {EXPECTED_REQUIRES_PYTHON}.",
                root,
            )
            add(
                "installed_keywords",
                EXPECTED_PYPROJECT_KEYWORDS <= metadata_keywords(metadata),
                "Installed metadata includes discovery keywords for evidence, provenance, templates, R&D, and quality gates.",
                root,
            )
            add(
                "installed_classifiers",
                EXPECTED_PYPROJECT_CLASSIFIERS <= set(metadata.get_all("Classifier") or []),
                "Installed metadata includes audience, status, Python-version, license, OS, and topic classifiers.",
                root,
            )
            add(
                "installed_project_urls",
                EXPECTED_PROJECT_URLS.items() <= installed_project_urls.items(),
                "Installed metadata links homepage, docs, architecture, data contract, adapter profiles, casebook check, template authoring, troubleshooting, source, issues, changelog, demo, live PR proof links, downstream proof links, launch article, citation, and governance URLs.",
                root,
            )
            add(
                "installed_console_script",
                any(entry.name == "falsiflow" and entry.value == "falsiflow.cli:main" for entry in entry_points),
                "Installed console script points to falsiflow.cli:main.",
                root,
            )
        except importlib_metadata.PackageNotFoundError:
            add("installed_metadata", False, "Installed falsiflow package metadata was not found.", root)

    template_dirs = [path for path in sorted(templates_path.iterdir()) if path.is_dir()] if templates_path.exists() else []
    add("template_package_root", bool(template_dirs), "Packaged starter template directories exist.", templates_path)
    for template_dir in template_dirs:
        required_paths = [
            template_dir / "template.json",
            template_dir / "project.json",
            template_dir / "evidence_pass_demo.csv",
            template_dir / "evidence_placeholder_demo.csv",
        ]
        add(f"template_files:{template_dir.name}", all(path.exists() for path in required_paths), f"Template `{template_dir.name}` has required packaged files.", template_dir)
        source_files = list((template_dir / "source_files").glob("*.csv")) if (template_dir / "source_files").exists() else []
        add(f"template_sources:{template_dir.name}", bool(source_files), f"Template `{template_dir.name}` includes at least one source CSV.", template_dir / "source_files")

    return {
        "status": "package_ready" if not failures else "package_blocked",
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
    }


def dist_release_checks(root: Path, artifact_root: Path, run_dist: bool) -> dict[str, object]:
    root = root.resolve()
    artifact_root = artifact_root.resolve()
    checks: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    def add(check_id: str, ok: bool, message: str, path: Path | str = "") -> None:
        checks.append(release_check_item(check_id, ok, message, path))
        if not ok:
            failures.append(failure_record("dist", check_id, message))

    dist_root = artifact_root / "dist"
    wheel_dir = dist_root / "wheel"
    sdist_dir = dist_root / "sdist"
    build_env_dir = dist_root / "sdist_build_env"
    install_dir = dist_root / "installed"
    installed_check_dir = dist_root / "installed_release_check"
    pyproject_path = root / "pyproject.toml"
    package_template_root = root / "falsiflow" / "templates"
    expected_template_count = len([path for path in package_template_root.iterdir() if path.is_dir()]) if package_template_root.exists() else 0
    build_dir = root / "build"
    egg_info = root / "falsiflow.egg-info"
    if not run_dist:
        add("dist_skipped", True, "Distribution build check was skipped by request.", dist_root)
        return {"status": "dist_skipped", "check_count": len(checks), "failure_count": 0, "checks": checks, "failures": failures}
    if not pyproject_path.exists():
        add("dist_skipped_no_pyproject", True, "Distribution build check skipped outside a source tree.", root)
        return {"status": "dist_skipped", "check_count": len(checks), "failure_count": 0, "checks": checks, "failures": failures}

    prebuild_cleanup_errors: list[str] = []
    for generated_path in [egg_info, build_dir]:
        if generated_path.exists() or generated_path.is_symlink():
            try:
                remove_generated_path(generated_path)
            except OSError as exc:  # pragma: no cover - defensive filesystem boundary.
                prebuild_cleanup_errors.append(f"{generated_path}: {exc}")
    add(
        "source_build_cache_preclean",
        not prebuild_cleanup_errors,
        "Distribution check removes stale build/ and falsiflow.egg-info artifacts before building.",
        root if prebuild_cleanup_errors else dist_root,
    )

    wheel_dir.mkdir(parents=True, exist_ok=True)
    sdist_dir.mkdir(parents=True, exist_ok=True)
    pip_wheel = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", str(root), "--no-deps", "--wheel-dir", str(wheel_dir)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    add("wheel_build", pip_wheel.returncode == 0, "Wheel builds with pip wheel.", wheel_dir if pip_wheel.returncode == 0 else command_excerpt(pip_wheel))
    wheels = sorted(wheel_dir.glob("falsiflow-*.whl"))
    add("wheel_artifact", len(wheels) == 1, "Exactly one falsiflow wheel artifact was produced.", wheels[0] if wheels else wheel_dir)

    sdist_name = ""
    try:
        sdist_name, _sdist_output = build_sdist_in_isolated_env(root, sdist_dir, build_env_dir, pyproject_path)
        add("sdist_build", bool(sdist_name), "Source distribution builds in an isolated PEP 517 environment.", sdist_dir / sdist_name if sdist_name else sdist_dir)
    except Exception as exc:  # pragma: no cover - defensive build boundary.
        add("sdist_build", False, f"Source distribution build failed: {exc}", sdist_dir)

    sdist_path = sdist_dir / sdist_name if sdist_name else None
    add("sdist_artifact", bool(sdist_path and sdist_path.exists()), "Source distribution artifact exists.", sdist_path or sdist_dir)
    if sdist_path and sdist_path.exists():
        try:
            with tarfile.open(sdist_path, "r:gz") as archive:
                names = set(archive.getnames())
            base = next(iter(name.split("/", 1)[0] for name in names if "/" in name), "")
            required = {
                f"{base}/pyproject.toml",
                f"{base}/README.md",
                f"{base}/LICENSE",
                f"{base}/CHANGELOG.md",
                f"{base}/CONTRIBUTING.md",
                f"{base}/CITATION.cff",
                f"{base}/CODE_OF_CONDUCT.md",
                f"{base}/GOVERNANCE.md",
                f"{base}/RELEASE.md",
                f"{base}/SECURITY.md",
                f"{base}/SUPPORT.md",
                f"{base}/RESPONSIBLE_USE.md",
                f"{base}/ROADMAP.md",
                f"{base}/MANIFEST.in",
                f"{base}/.github/workflows/falsiflow.yml",
                f"{base}/.github/workflows/falsiflow-pages.yml",
                f"{base}/.github/workflows/falsiflow-cross-platform.yml",
                f"{base}/.github/workflows/falsiflow-external-evidence.yml",
                f"{base}/.github/workflows/falsiflow-scorecard.yml",
                f"{base}/.github/workflows/falsiflow-publish.yml",
                f"{base}/.github/ISSUE_TEMPLATE/config.yml",
                f"{base}/.github/ISSUE_TEMPLATE/bug_report.yml",
                f"{base}/.github/ISSUE_TEMPLATE/feature_request.yml",
                f"{base}/.github/ISSUE_TEMPLATE/claim_gate_request.yml",
                f"{base}/.github/ISSUE_TEMPLATE/launch_feedback.yml",
                f"{base}/.github/PULL_REQUEST_TEMPLATE.md",
                f"{base}/.github/dependabot.yml",
                f"{base}/docs/falsiflow_adoption_priorities.md",
                f"{base}/docs/falsiflow_architecture.md",
                f"{base}/docs/falsiflow_cli_reference.md",
                f"{base}/docs/falsiflow_data_contract.md",
                f"{base}/docs/falsiflow_adapter_profiles.md",
                f"{base}/docs/falsiflow_local_llm_eval.md",
                f"{base}/docs/falsiflow_mcp.md",
                f"{base}/docs/falsiflow_casebook_check.md",
                f"{base}/docs/falsiflow_demo_pr_playbook.md",
                f"{base}/docs/falsiflow_github_action_examples.md",
                f"{base}/docs/falsiflow_public_issue_queue.md",
                f"{base}/docs/falsiflow_positioning.md",
                f"{base}/docs/falsiflow_public_casebook.md",
                f"{base}/docs/falsiflow_rag_quality_gate_proposal.md",
                f"{base}/docs/falsiflow_pypi_trusted_publishing.md",
                f"{base}/docs/falsiflow_security_posture.md",
                f"{base}/docs/falsiflow_template_authoring.md",
                f"{base}/docs/falsiflow_troubleshooting.md",
                f"{base}/docs/assets/falsiflow_downstream_pr_proof_strip.svg",
                f"{base}/docs/assets/falsiflow_downstream_pr_proof_strip.png",
                f"{base}/docs/assets/falsiflow_live_pr_story_reel.svg",
                f"{base}/docs/assets/falsiflow_proof_strip.svg",
                f"{base}/docs/assets/falsiflow_30_second_demo.svg",
                f"{base}/examples/README.md",
                f"{base}/examples/downstream_product_metric_smoke/README.md",
                f"{base}/examples/downstream_product_metric_smoke/.github/workflows/falsiflow-product-metric.yml",
                f"{base}/examples/downstream_product_metric_smoke/falsiflow_product_metric/project.json",
                f"{base}/examples/downstream_product_metric_smoke/falsiflow_product_metric/evidence.csv",
                f"{base}/examples/downstream_product_metric_smoke/falsiflow_product_metric/evidence_pass_demo.csv",
                f"{base}/examples/downstream_product_metric_smoke/falsiflow_product_metric/evidence_placeholder_demo.csv",
                f"{base}/examples/downstream_product_metric_smoke/falsiflow_product_metric/source_files/product_metric_raw_export.csv",
                f"{base}/falsiflow/adapters.py",
                f"{base}/falsiflow/adoption.py",
                f"{base}/falsiflow/casebook_check.py",
                f"{base}/falsiflow/bundle.py",
                f"{base}/falsiflow/browser_demo.py",
                f"{base}/falsiflow/claim_check.py",
                f"{base}/falsiflow/cli.py",
                f"{base}/falsiflow/core.py",
                f"{base}/falsiflow/assets/falsiflow_downstream_pr_proof_strip.svg",
                f"{base}/falsiflow/assets/falsiflow_live_pr_story_reel.svg",
                f"{base}/falsiflow/demo.py",
                f"{base}/falsiflow/discovery.py",
                f"{base}/falsiflow/doctor.py",
                f"{base}/falsiflow/local_server.py",
                f"{base}/falsiflow/public_release.py",
                f"{base}/falsiflow/quickstart.py",
                f"{base}/falsiflow/release.py",
                f"{base}/falsiflow/scaffold.py",
                f"{base}/falsiflow/template_discovery.py",
                f"{base}/falsiflow/template_gallery.py",
                f"{base}/falsiflow/template_check.py",
                f"{base}/falsiflow/template_pack.py",
                f"{base}/falsiflow/template_registry.py",
                f"{base}/falsiflow/template_provenance.py",
                f"{base}/falsiflow/template_release.py",
                f"{base}/falsiflow/template_install.py",
                f"{base}/falsiflow/templates/neural_materials/project.json",
                f"{base}/falsiflow/templates/neural_materials/source_files/demo_raw_export.csv",
                f"{base}/falsiflow/templates/product_metric_launch/project.json",
                f"{base}/falsiflow/templates/product_metric_launch/source_files/product_metric_raw_export.csv",
            }
            add("sdist_required_files", required <= names, "Source distribution includes release docs, package modules, and template data.", sdist_path)
        except (OSError, tarfile.TarError) as exc:
            add("sdist_required_files", False, f"Could not inspect source distribution: {exc}", sdist_path)

    if wheels:
        install = subprocess.run(
            [sys.executable, "-m", "pip", "install", str(wheels[0]), "--target", str(install_dir), "--no-deps", "--quiet"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        add("wheel_install", install.returncode == 0, "Wheel installs into an isolated target directory.", install_dir if install.returncode == 0 else command_excerpt(install))
        if install.returncode == 0:
            env = dict(os.environ, PYTHONPATH=str(install_dir))
            installed_check = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "falsiflow.cli",
                    "release-check",
                    "--out-dir",
                    str(installed_check_dir),
                    "--json",
                ],
                cwd=dist_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            add("installed_release_check", installed_check.returncode == 0, "Installed wheel passes release-check.", installed_check_dir if installed_check.returncode == 0 else command_excerpt(installed_check))
            if installed_check.returncode == 0:
                try:
                    installed_summary = json.loads(installed_check.stdout)
                    add("installed_templates", installed_summary.get("template_count") == expected_template_count and installed_summary.get("bundle_verified_count") == expected_template_count, "Installed wheel exposes all starter templates and verifies their bundles.", installed_check_dir / "release_check.json")
                except json.JSONDecodeError as exc:
                    add("installed_templates", False, f"Installed release-check did not return JSON: {exc}", installed_check_dir)

    cleanup_errors: list[str] = []
    for generated_path in [egg_info, build_dir]:
        if generated_path.exists() or generated_path.is_symlink():
            try:
                remove_generated_path(generated_path)
            except OSError as exc:  # pragma: no cover - defensive filesystem boundary.
                cleanup_errors.append(f"{generated_path}: {exc}")
    cleanup_message = (
        "Distribution check removes transient build/ and falsiflow.egg-info artifacts from the source root."
        if not cleanup_errors
        else "Could not clean transient source build artifacts: " + "; ".join(cleanup_errors)
    )
    add(
        "source_build_cache_cleanup",
        not cleanup_errors
        and not (egg_info.exists() or egg_info.is_symlink())
        and not (build_dir.exists() or build_dir.is_symlink()),
        cleanup_message,
        root if cleanup_errors else dist_root,
    )

    return {
        "status": "dist_ready" if not failures else "dist_blocked",
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
    }


def run_release_check(
    artifact_root: Path,
    run_dist: bool = True,
    *,
    source_root: Path,
    schema_kinds: list[str],
    schema_provider: Callable[..., Any],
    template_records_provider: Callable[..., Any],
    template_resolver: Callable[..., Any],
    demo_runner: Callable[..., Any],
    demo_package_runner: Callable[..., Any],
    external_check_runner: Callable[..., Any],
    publish_kit_runner: Callable[..., Any],
    launch_kit_runner: Callable[..., Any],
    quickstart_runner: Callable[..., Any],
    doctor_runner: Callable[..., Any],
    default_evidence_path: Callable[..., Any],
    claim_check_runner: Callable[..., Any],
    template_gallery_runner: Callable[..., Any],
    casebook_check_runner: Callable[..., Any],
    template_check_runner: Callable[..., Any],
    template_pack_runner: Callable[..., Any],
    template_registry_runner: Callable[..., Any],
    template_lock_runner: Callable[..., Any],
    template_attestation_runner: Callable[..., Any],
    verify_template_attestation_runner: Callable[..., Any],
    template_policy_runner: Callable[..., Any],
    verify_template_policy_runner: Callable[..., Any],
    template_release_runner: Callable[..., Any],
    verify_template_release_runner: Callable[..., Any],
    template_install_runner: Callable[..., Any],
    read_json_object_runner: Callable[..., Any],
    bundle_builder: Callable[..., Any],
    bundle_zip_verifier: Callable[..., Any],
    bundle_verification_report_renderer: Callable[..., Any],
    template_release_verification_report_renderer: Callable[..., Any],
    portfolio_writer: Callable[..., Any],
    adoption_summary_builder: Callable[..., Any],
    adoption_artifact_writer: Callable[..., Any],
    release_validation_status_for_dist_runner: Callable[..., Any],
) -> dict[str, object]:
    source_root = source_root.resolve()
    artifact_root = artifact_root.resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)
    failures: list[dict[str, str]] = []

    package = package_release_checks(source_root)
    failures.extend(package["failures"])
    dist = dist_release_checks(source_root, artifact_root, run_dist)
    failures.extend(dist["failures"])
    demo_summary: dict[str, object]
    try:
        demo_summary = demo_runner("neural_materials", artifact_root / "demo", force=True)
        if demo_summary.get("status") != "demo_ready":
            failures.append(failure_record("demo", "neural_materials", f"Demo ended as {demo_summary.get('status', '')}."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        demo_summary = {"status": "demo_failed", "template": "neural_materials", "message": str(exc)}
        failures.append(failure_record("demo", "neural_materials", str(exc)))

    try:
        demo_package_summary = demo_package_runner("biointerface_coatings", artifact_root / "public_demo", [], force=True)
        if demo_package_summary.get("status") != "demo_package_ready":
            failures.append(failure_record("demo_package", "public_demo", f"Demo package ended as {demo_package_summary.get('status', '')}."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        demo_package_summary = {"status": "demo_package_failed", "template": "biointerface_coatings", "message": str(exc)}
        failures.append(failure_record("demo_package", "public_demo", str(exc)))

    try:
        external_check_summary = external_check_runner(artifact_root / "external_readiness", force=True)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        external_check_summary = {
            "status": "external_check_failed",
            "check_count": 0,
            "ready_check_count": 0,
            "blocker_count": 1,
            "checks": [],
            "blockers": [{"check": "external_check", "status": "blocked", "message": str(exc)}],
            "message": str(exc),
        }

    try:
        publish_kit_summary = publish_kit_runner(artifact_root / "publish_kit", "biointerface_coatings", [], force=True)
        if publish_kit_summary.get("status") != "publish_kit_ready":
            failures.append(failure_record("publish_kit", "handoff", f"Publish kit ended as {publish_kit_summary.get('status', '')}."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        publish_kit_summary = {"status": "publish_kit_failed", "message": str(exc)}
        failures.append(failure_record("publish_kit", "handoff", str(exc)))

    try:
        launch_kit_summary = launch_kit_runner(artifact_root / "launch_kit", "biointerface_coatings", [], force=True)
        if launch_kit_summary.get("status") != "launch_kit_ready":
            failures.append(failure_record("launch_kit", "handoff", f"Launch kit ended as {launch_kit_summary.get('status', '')}."))
        else:
            launch_kit_dir = artifact_root / "launch_kit"
            launch_content_checks = {
                "launch_posts": (
                    launch_kit_dir / "launch_posts.md",
                    ["Channel Checklist", "Hacker News / Show HN", "Reddit / community threads", "LinkedIn", "Awesome lists / ecosystem repos", "responsible-use boundary", "launch_metrics.md", "Show HN", "unverifiable AI eval claims", "falsiflow-downstream-ai-eval-demo", "26711652990", "26711669112", "Live downstream PR", "Demo PR playbook", "Reply Bank", "Great Expectations", "GITHUB_ACTION_PATH", "claim_check_blocked", "claim_check_ready"],
                ),
                "launch_announcement": (
                    launch_kit_dir / "announcement.md",
                    ["Falsiflow is a CI gate for claims", "falsiflow_demo_pr_playbook.md", "claim_check_blocked", "claim_check_ready", "Public Release Boundary"],
                ),
                "launch_demo_script": (
                    launch_kit_dir / "demo_script.md",
                    ["## 2:15 Demo PR", "evidence_placeholder_demo.csv", "evidence_pass_demo.csv", "claim_check_blocked", "claim_check_ready"],
                ),
                "launch_maintainer_checklist": (
                    launch_kit_dir / "maintainer_checklist.md",
                    ["falsiflow_demo_pr_playbook.md", "claim_check_blocked", "claim_check_ready", "Launch Metrics"],
                ),
                "launch_metrics": (
                    launch_kit_dir / "launch_metrics.md",
                    ["demo PR playbook", "demo PR replay", "day-14", "Falsiflow 1k-Star Launch Tracker"],
                ),
            }
            for check_id, (path, tokens) in launch_content_checks.items():
                text = path.read_text(encoding="utf-8") if path.exists() else ""
                missing_tokens = [token for token in tokens if token not in text]
                if missing_tokens:
                    failures.append(failure_record("launch_kit_content", check_id, f"Missing launch-kit content tokens: {', '.join(missing_tokens)}"))
                if check_id in {"launch_announcement", "launch_demo_script", "launch_posts"} and text.count("```") % 2:
                    failures.append(failure_record("launch_kit_content", check_id, "Markdown code fences are not balanced."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        launch_kit_summary = {"status": "launch_kit_failed", "message": str(exc)}
        failures.append(failure_record("launch_kit", "handoff", str(exc)))

    quickstart_summary: dict[str, object]
    try:
        quickstart_summary = quickstart_runner(
            "biointerface_coatings",
            artifact_root / "quickstart_project",
            force=True,
            include_env=False,
        )
        if quickstart_summary.get("status") != "quickstart_ready":
            failures.append(failure_record("quickstart", "biointerface_coatings", f"Quickstart ended as {quickstart_summary.get('status', '')}."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        quickstart_summary = {"status": "quickstart_blocked", "template": "biointerface_coatings", "message": str(exc)}
        failures.append(failure_record("quickstart", "biointerface_coatings", str(exc)))

    doctor_summary: dict[str, object]
    try:
        quickstart_project_dir = artifact_root / "quickstart_project"
        doctor_summary = doctor_runner(
            quickstart_project_dir,
            quickstart_project_dir / "project.json",
            default_evidence_path(quickstart_project_dir),
            artifact_root / "doctor",
            force=True,
        )
        if doctor_summary.get("status") != "doctor_ready":
            failures.append(failure_record("doctor", "quickstart_project", f"Doctor ended as {doctor_summary.get('status', '')}."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        doctor_summary = {"status": "doctor_blocked", "project_dir": str(artifact_root / "quickstart_project"), "message": str(exc)}
        failures.append(failure_record("doctor", "quickstart_project", str(exc)))

    claim_check_summary: dict[str, object]
    try:
        claim_template_dir = template_resolver("neural_materials", include_env=False)
        if claim_template_dir is None:
            claim_check_summary = {"status": "claim_check_blocked", "message": "neural_materials template was not found."}
            failures.append(failure_record("claim_check", "neural_materials", "neural_materials template was not found."))
        else:
            claim_check_summary = claim_check_runner(
                claim_template_dir / "project.json",
                claim_template_dir / "evidence_pass_demo.csv",
                artifact_root / "claim_check",
                force=True,
            )
            if claim_check_summary.get("status") != "claim_check_ready":
                failures.append(failure_record("claim_check", "neural_materials", f"Claim check ended as {claim_check_summary.get('status', '')}."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        claim_check_summary = {"status": "claim_check_blocked", "template": "neural_materials", "message": str(exc)}
        failures.append(failure_record("claim_check", "neural_materials", str(exc)))

    schema_dir = artifact_root / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    schemas: list[dict[str, object]] = []
    for kind in schema_kinds:
        try:
            schema = schema_provider(kind)
            ok = isinstance(schema, dict) and bool(schema)
            schemas.append({"kind": kind, "status": "passed" if ok else "failed", "path": str(schema_dir / schema_filename(kind))})
            if ok:
                (schema_dir / schema_filename(kind)).write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")
            else:
                failures.append(failure_record("schema", kind, "Schema payload was empty."))
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            schemas.append({"kind": kind, "status": "failed", "path": str(schema_dir / schema_filename(kind))})
            failures.append(failure_record("schema", kind, str(exc)))

    try:
        records = template_records_provider(include_env=False)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        records = []
        failures.append(failure_record("template_discovery", "templates", str(exc)))
    if not records:
        failures.append(failure_record("template_discovery", "templates", "No starter templates found."))

    try:
        template_gallery = template_gallery_runner(
            include_env=False,
            out=artifact_root / "template_gallery.md",
            json_out=artifact_root / "template_gallery.json",
        )
        if template_gallery.get("status") != "template_gallery_ready":
            failures.append(failure_record("template_gallery", "templates", f"Template gallery ended as {template_gallery.get('status', '')}."))
        if template_gallery.get("template_count") != len(records):
            failures.append(failure_record("template_gallery", "templates", "Template gallery did not cover every discovered starter template."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        template_gallery = {"status": "template_gallery_blocked", "message": str(exc), "template_count": 0}
        failures.append(failure_record("template_gallery", "templates", str(exc)))

    try:
        casebook_check_summary = casebook_check_runner(
            artifact_root / "casebook_check",
            [],
            force=True,
            include_env=False,
        )
        if casebook_check_summary.get("status") != "casebook_check_ready":
            failures.append(failure_record("casebook_check", "templates", f"Casebook check ended as {casebook_check_summary.get('status', '')}."))
        if int(casebook_check_summary.get("template_count", 0) or 0) != len(records):
            failures.append(failure_record("casebook_check", "templates", "Casebook check did not cover every discovered starter template."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        casebook_check_summary = {"status": "casebook_check_blocked", "message": str(exc), "template_count": 0}
        failures.append(failure_record("casebook_check", "templates", str(exc)))

    template_check_results: list[dict[str, object]] = []
    for record in records:
        template_id = record["template"]
        try:
            template_check = template_check_runner(Path(record["path"]), artifact_root / "template_checks" / template_id, force=True)
            template_check_results.append(template_check)
            for failed in template_check.get("failures", []):
                if isinstance(failed, dict):
                    failures.append(failure_record("template_check", f"{template_id}:{failed.get('check', '')}", str(failed.get("message", ""))))
            if template_check.get("status") != "template_ready" and not template_check.get("failures"):
                failures.append(failure_record("template_check", template_id, f"Template check ended as {template_check.get('status', '')}."))
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            template_check_results.append({
                "status": "template_blocked",
                "template_id": template_id,
                "template_dir": record.get("path", ""),
                "artifact_root": str(artifact_root / "template_checks" / template_id),
                "failure_count": 1,
                "failures": [{"check": "template_check_exception", "status": "failed", "message": str(exc), "path": record.get("path", "")}],
            })
            failures.append(failure_record("template_check", template_id, str(exc)))

    template_pack_summary: dict[str, object]
    try:
        pack_record = next((record for record in records if record.get("template") == "neural_materials"), records[0] if records else None)
        if pack_record is None:
            template_pack_summary = {"status": "template_pack_skipped", "verification_status": "", "message": "No templates available."}
            failures.append(failure_record("template_pack", "templates", "No templates available to package."))
        else:
            template_pack_summary = template_pack_runner(
                Path(pack_record["path"]),
                artifact_root / "template_pack",
                artifact_root / "template_pack.zip",
                verification_out=artifact_root / "template_pack_verification.json",
                report_out=artifact_root / "template_pack_verification.md",
                force=True,
            )
            if template_pack_summary.get("status") != "template_pack_ready":
                failures.append(failure_record("template_pack", str(pack_record.get("template", "")), f"Template pack ended as {template_pack_summary.get('status', '')}."))
            if template_pack_summary.get("verification_status") != "template_pack_verified":
                failures.append(failure_record("template_pack_verify", str(pack_record.get("template", "")), f"Template pack verification ended as {template_pack_summary.get('verification_status', '')}."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        template_pack_summary = {"status": "template_pack_failed", "verification_status": "", "message": str(exc)}
        failures.append(failure_record("template_pack", "templates", str(exc)))

    template_registry_summary: dict[str, object]
    template_lock_summary: dict[str, object]
    template_attestation_summary: dict[str, object]
    template_attestation_verification_summary: dict[str, object]
    template_policy_summary: dict[str, object]
    template_policy_verification_summary: dict[str, object]
    template_release_summary: dict[str, object]
    template_release_verification_summary: dict[str, object]
    template_install_summary: dict[str, object]
    try:
        zip_path = Path(str(template_pack_summary.get("zip_path", artifact_root / "template_pack.zip")))
        if template_pack_summary.get("verification_status") != "template_pack_verified":
            template_registry_summary = {
                "status": "template_registry_blocked",
                "template_count": 0,
                "message": "Template pack was not verified.",
            }
            template_lock_summary = {
                "status": "template_lock_blocked",
                "template_id": str(template_pack_summary.get("template_id", "")),
                "message": "Template registry was not ready.",
            }
            template_install_summary = {
                "status": "template_install_blocked",
                "template_id": str(template_pack_summary.get("template_id", "")),
                "verification_status": str(template_pack_summary.get("verification_status", "")),
                "message": "Template pack was not verified.",
            }
            template_attestation_summary = {
                "status": "template_attestation_blocked",
                "subject_type": "template-lock",
                "message": "Template lock was not ready.",
            }
            template_attestation_verification_summary = {
                "status": "template_attestation_failed",
                "subject_type": "template-lock",
                "message": "Template attestation was not created.",
            }
            template_policy_summary = {
                "status": "template_policy_blocked",
                "message": "Template lock attestation was not ready.",
            }
            template_policy_verification_summary = {
                "status": "template_policy_failed",
                "message": "Template policy was not created.",
            }
            template_release_summary = {
                "status": "template_release_blocked",
                "message": "Template policy was not ready.",
            }
            template_release_verification_summary = {
                "status": "template_release_failed",
                "message": "Template release was not created.",
            }
            failures.append(failure_record("template_registry", "template_pack", "Template pack was not verified for registry indexing."))
        else:
            registry_path = artifact_root / "template_registry.json"
            template_registry_summary = template_registry_runner(
                [zip_path],
                out=registry_path,
                report_out=artifact_root / "template_registry.md",
                base_url=artifact_root.resolve().as_uri(),
            )
            if template_registry_summary.get("status") != "template_registry_ready":
                failures.append(failure_record("template_registry", str(template_pack_summary.get("template_id", "")), f"Template registry ended as {template_registry_summary.get('status', '')}."))
            lock_path = artifact_root / "falsiflow_template_lock.json"
            registry_entries = [entry for entry in template_registry_summary.get("templates", []) if isinstance(entry, dict)]
            registry_version = str(registry_entries[0].get("template_version", "")) if registry_entries else ""
            template_lock_summary = template_lock_runner(
                registry_path,
                str(template_pack_summary.get("template_id", "")),
                version=registry_version,
                out=lock_path,
                cache_dir=artifact_root / "template_source_cache",
            )
            if template_lock_summary.get("status") != "template_locked":
                failures.append(failure_record("template_lock", str(template_pack_summary.get("template_id", "")), f"Template lock ended as {template_lock_summary.get('status', '')}."))
                template_install_summary = {
                    "status": "template_install_blocked",
                    "template_id": str(template_pack_summary.get("template_id", "")),
                    "message": "Template lock was not ready.",
                }
                template_attestation_summary = {
                    "status": "template_attestation_blocked",
                    "subject_type": "template-lock",
                    "subject_path": str(lock_path),
                    "message": "Template lock was not ready.",
                }
                template_attestation_verification_summary = {
                    "status": "template_attestation_failed",
                    "subject_type": "template-lock",
                    "subject_path": str(lock_path),
                    "message": "Template attestation was not created.",
                }
                template_policy_summary = {
                    "status": "template_policy_blocked",
                    "template_id": str(template_pack_summary.get("template_id", "")),
                    "message": "Template lock attestation was not ready.",
                }
                template_policy_verification_summary = {
                    "status": "template_policy_failed",
                    "template_id": str(template_pack_summary.get("template_id", "")),
                    "message": "Template policy was not created.",
                }
                template_release_summary = {
                    "status": "template_release_blocked",
                    "template_id": str(template_pack_summary.get("template_id", "")),
                    "message": "Template policy was not ready.",
                }
                template_release_verification_summary = {
                    "status": "template_release_failed",
                    "template_id": str(template_pack_summary.get("template_id", "")),
                    "message": "Template release was not created.",
                }
            else:
                release_attestation_key = "falsiflow-release-check-template-attestation"
                template_attestation_path = artifact_root / "falsiflow_template_lock.attestation.json"
                template_policy_path = artifact_root / "falsiflow_template_policy.json"
                template_attestation_summary = template_attestation_runner(
                    lock_path,
                    subject_type="template-lock",
                    out=template_attestation_path,
                    signing_key=release_attestation_key,
                    key_id="release-check",
                    builder="release-check",
                )
                if template_attestation_summary.get("status") != "template_attested":
                    failures.append(failure_record("template_attestation", str(template_pack_summary.get("template_id", "")), f"Template attestation ended as {template_attestation_summary.get('status', '')}."))
                template_attestation_verification_summary = verify_template_attestation_runner(
                    template_attestation_path,
                    subject_path=lock_path,
                    signing_key=release_attestation_key,
                )
                if template_attestation_verification_summary.get("status") != "template_attestation_verified":
                    failures.append(failure_record("template_attestation_verify", str(template_pack_summary.get("template_id", "")), f"Template attestation verification ended as {template_attestation_verification_summary.get('status', '')}."))
                template_policy_summary = template_policy_runner(
                    lock_path,
                    template_attestation_path,
                    out=template_policy_path,
                    signing_key=release_attestation_key,
                    policy_id="release-check:neural_materials",
                    owner="release-check",
                )
                if template_policy_summary.get("status") != "template_policy_ready":
                    failures.append(failure_record("template_policy", str(template_pack_summary.get("template_id", "")), f"Template policy ended as {template_policy_summary.get('status', '')}."))
                template_policy_verification_summary = verify_template_policy_runner(
                    template_policy_path,
                    lock_path,
                    template_attestation_path,
                    signing_key=release_attestation_key,
                )
                if template_policy_verification_summary.get("status") != "template_policy_verified":
                    failures.append(failure_record("template_policy_verify", str(template_pack_summary.get("template_id", "")), f"Template policy verification ended as {template_policy_verification_summary.get('status', '')}."))
                template_release_path = artifact_root / "template_release.zip"
                template_release_summary = template_release_runner(
                    zip_path,
                    registry_path,
                    lock_path,
                    template_attestation_path,
                    template_policy_path,
                    template_release_path,
                    signing_key=release_attestation_key,
                )
                if template_release_summary.get("status") != "template_release_ready":
                    failures.append(failure_record("template_release", str(template_pack_summary.get("template_id", "")), f"Template release ended as {template_release_summary.get('status', '')}."))
                template_release_verification_summary = verify_template_release_runner(
                    template_release_path,
                    signing_key=release_attestation_key,
                    extract_dir=artifact_root / "template_release_extract",
                )
                (artifact_root / "template_release_verification.json").write_text(
                    json.dumps(template_release_verification_summary, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                (artifact_root / "template_release_verification.md").write_text(
                    template_release_verification_report_renderer(template_release_verification_summary),
                    encoding="utf-8",
                )
                if template_release_verification_summary.get("status") != "template_release_verified":
                    failures.append(failure_record("template_release_verify", str(template_pack_summary.get("template_id", "")), f"Template release verification ended as {template_release_verification_summary.get('status', '')}."))
                    template_install_summary = {
                        "status": "template_install_blocked",
                        "template_id": str(template_pack_summary.get("template_id", "")),
                        "message": "Template release was not verified.",
                    }
                    lock = template_lock_summary
                else:
                    release_artifacts = template_release_verification_summary.get("artifact_paths", {}) if isinstance(template_release_verification_summary.get("artifact_paths"), dict) else {}
                    release_pack_zip = Path(str(release_artifacts.get("template_pack", "")))
                    release_lock_path = Path(str(release_artifacts.get("template_lock", "")))
                    lock = read_json_object_runner(release_lock_path, "template lock")
                    template_install_summary = template_install_runner(
                        release_pack_zip,
                        artifact_root / "template_install_templates",
                        check_out_dir=artifact_root / "template_install_check",
                        force=True,
                        attestation_verification=template_release_verification_summary.get("attestation_verification_summary") if isinstance(template_release_verification_summary.get("attestation_verification_summary"), dict) else template_attestation_verification_summary,
                        attestation_required=True,
                        policy_verification=template_release_verification_summary.get("policy_verification_summary") if isinstance(template_release_verification_summary.get("policy_verification_summary"), dict) else template_policy_verification_summary,
                    )
                    template_install_summary["release_path"] = str(template_release_path)
                    template_install_summary["release_status"] = str(template_release_verification_summary.get("status", ""))
                    template_install_summary["release_sha256"] = str(template_release_verification_summary.get("release_zip_sha256", ""))
                template_install_summary["lock_path"] = str(lock_path)
                template_install_summary["lock_status"] = str(lock.get("status", ""))
                template_install_summary["lock_source_sha256"] = str(lock.get("source_sha256", ""))
                if template_install_summary.get("status") != "template_installed":
                    failures.append(failure_record("template_install", str(template_install_summary.get("template_id", "")), f"Template install ended as {template_install_summary.get('status', '')}."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        template_registry_summary = {"status": "template_registry_failed", "message": str(exc)}
        template_lock_summary = {"status": "template_lock_failed", "message": str(exc)}
        template_attestation_summary = {"status": "template_attestation_failed", "message": str(exc)}
        template_attestation_verification_summary = {"status": "template_attestation_failed", "message": str(exc)}
        template_policy_summary = {"status": "template_policy_failed", "message": str(exc)}
        template_policy_verification_summary = {"status": "template_policy_failed", "message": str(exc)}
        template_release_summary = {"status": "template_release_failed", "message": str(exc)}
        template_release_verification_summary = {"status": "template_release_failed", "message": str(exc)}
        template_install_summary = {"status": "template_install_failed", "message": str(exc)}
        failures.append(failure_record("template_registry", "template_pack", str(exc)))

    templates: list[dict[str, object]] = []
    claim_summary_paths: list[Path] = []
    template_root = artifact_root / "templates"
    for record in records:
        template_id = record["template"]
        template_dir = Path(record["path"])
        config_path = Path(record["project_config"])
        evidence_path = template_dir / "evidence_pass_demo.csv"
        template_artifact_dir = template_root / template_id
        bundle_dir = template_artifact_dir / "bundle"
        bundle_zip = template_artifact_dir / "bundle.zip"
        verification_json = template_artifact_dir / "bundle_verification.json"
        verification_report = template_artifact_dir / "bundle_verification.md"
        template_result: dict[str, object] = {
            "template": template_id,
            "project_id": record["project_id"],
            "validation_status": record["status"],
            "audit_status": "not_run",
            "claim_ready": False,
            "source_status": "not_run",
            "bundle_status": "not_run",
            "verification_status": "not_run",
            "artifact_dir": str(template_artifact_dir),
        }

        if record["status"] != "valid":
            failures.append(failure_record("template_validation", template_id, f"Template config is {record['status']}."))
            templates.append(template_result)
            continue
        if not evidence_path.exists():
            failures.append(failure_record("template_bundle", template_id, "Missing evidence_pass_demo.csv."))
            templates.append(template_result)
            continue

        try:
            template_artifact_dir.mkdir(parents=True, exist_ok=True)
            bundle = bundle_builder(config_path, evidence_path, bundle_dir, bundle_zip, force=True)
            verification = bundle_zip_verifier(bundle_zip)
            verification_json.write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")
            verification_report.write_text(bundle_verification_report_renderer(verification), encoding="utf-8")
            template_result["audit_status"] = bundle.get("audit_status", "")
            template_result["claim_ready"] = bool(bundle.get("claim_ready"))
            template_result["source_status"] = bundle.get("source_status", "")
            template_result["bundle_status"] = bundle.get("status", "")
            template_result["verification_status"] = verification.get("status", "")
            template_result["verification_issue_count"] = verification.get("issue_count", 0)
            if bundle.get("claim_ready") and bundle.get("status") == "bundle_ready":
                claim_summary_paths.append(bundle_dir / "audit" / "claim_summary.json")
            if bundle.get("status") != "bundle_ready":
                failures.append(failure_record("template_bundle", template_id, f"Bundle ended as {bundle.get('status', '')}."))
            if verification.get("status") != "bundle_verified":
                failures.append(failure_record("template_verify", template_id, f"Bundle verification ended as {verification.get('status', '')}."))
        except SystemExit as exc:
            template_result["bundle_status"] = "failed"
            failures.append(failure_record("template_bundle", template_id, str(exc)))
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            template_result["bundle_status"] = "failed"
            failures.append(failure_record("template_bundle", template_id, str(exc)))
        templates.append(template_result)

    portfolio: dict[str, object] | None = None
    if claim_summary_paths:
        try:
            portfolio = portfolio_writer(claim_summary_paths, artifact_root / "portfolio")
            if portfolio["blocked_count"] != 0:
                failures.append(failure_record("portfolio", "release_templates", f"Portfolio has {portfolio['blocked_count']} blocked claim(s)."))
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            failures.append(failure_record("portfolio", "release_templates", str(exc)))
    else:
        failures.append(failure_record("portfolio", "release_templates", "No ready bundle claim summaries were produced."))

    adoption_check_summary = adoption_summary_builder(
        package,
        dist,
        quickstart_summary,
        doctor_summary,
        claim_check_summary,
        template_gallery,
        casebook_check_summary,
        artifact_root,
        adoption_rerun_root=artifact_root / "adoption_recheck",
    )
    adoption_artifact_writer(adoption_check_summary, artifact_root)
    if adoption_check_summary.get("status") != "adoption_ready":
        for failure in adoption_check_summary.get("failures", []):
            if isinstance(failure, dict):
                failures.append(failure_record("adoption_check", str(failure.get("id", "")), str(failure.get("message", ""))))

    release_validation_status, release_validation_message = release_validation_status_for_dist_runner(str(dist.get("status", "")))
    summary: dict[str, object] = {
        "status": "release_ready" if not failures else "release_blocked",
        "artifact_root": str(artifact_root),
        "package_status": package["status"],
        "package_check_count": package["check_count"],
        "package_failure_count": package["failure_count"],
        "package_checks": package["checks"],
        "dist_status": dist["status"],
        "release_validation_status": release_validation_status,
        "release_validation_message": release_validation_message,
        "dist_check_count": dist["check_count"],
        "dist_failure_count": dist["failure_count"],
        "dist_checks": dist["checks"],
        "demo_status": demo_summary.get("status", ""),
        "demo_summary": demo_summary,
        "demo_package_status": demo_package_summary.get("status", ""),
        "demo_package_summary": demo_package_summary,
        "external_check_status": external_check_summary.get("status", ""),
        "external_check_summary": external_check_summary,
        "publish_kit_status": publish_kit_summary.get("status", ""),
        "publish_kit_summary": publish_kit_summary,
        "launch_kit_status": launch_kit_summary.get("status", ""),
        "launch_kit_summary": launch_kit_summary,
        "quickstart_status": quickstart_summary.get("status", ""),
        "quickstart_summary": quickstart_summary,
        "doctor_status": doctor_summary.get("status", ""),
        "doctor_summary": doctor_summary,
        "claim_check_status": claim_check_summary.get("status", ""),
        "claim_check_summary": claim_check_summary,
        "schema_count": len(schemas),
        "schemas": schemas,
        "template_gallery_status": template_gallery.get("status", ""),
        "template_gallery_summary": template_gallery,
        "casebook_check_status": casebook_check_summary.get("status", ""),
        "casebook_check_summary": casebook_check_summary,
        "template_check_count": len(template_check_results),
        "template_check_ready_count": sum(1 for item in template_check_results if item.get("status") == "template_ready"),
        "template_checks": template_check_results,
        "template_pack_status": template_pack_summary.get("status", ""),
        "template_pack_verification_status": template_pack_summary.get("verification_status", ""),
        "template_pack_summary": template_pack_summary,
        "template_registry_status": template_registry_summary.get("status", ""),
        "template_registry_summary": template_registry_summary,
        "template_lock_status": template_lock_summary.get("status", ""),
        "template_lock_summary": template_lock_summary,
        "template_attestation_status": template_attestation_summary.get("status", ""),
        "template_attestation_summary": template_attestation_summary,
        "template_attestation_verification_status": template_attestation_verification_summary.get("status", ""),
        "template_attestation_verification_summary": template_attestation_verification_summary,
        "template_policy_status": template_policy_summary.get("status", ""),
        "template_policy_summary": template_policy_summary,
        "template_policy_verification_status": template_policy_verification_summary.get("status", ""),
        "template_policy_verification_summary": template_policy_verification_summary,
        "template_release_status": template_release_summary.get("status", ""),
        "template_release_summary": template_release_summary,
        "template_release_verification_status": template_release_verification_summary.get("status", ""),
        "template_release_verification_summary": template_release_verification_summary,
        "template_install_status": template_install_summary.get("status", ""),
        "template_install_summary": template_install_summary,
        "adoption_check_status": adoption_check_summary.get("status", ""),
        "adoption_check_summary": adoption_check_summary,
        "template_count": len(templates),
        "audit_ready_count": sum(1 for template in templates if template.get("claim_ready") is True),
        "source_ready_count": sum(1 for template in templates if template.get("source_status") == "sources_ready"),
        "bundle_ready_count": sum(1 for template in templates if template.get("bundle_status") == "bundle_ready"),
        "bundle_verified_count": sum(1 for template in templates if template.get("verification_status") == "bundle_verified"),
        "failure_count": len(failures),
        "failures": failures,
        "templates": templates,
        "portfolio_status": portfolio["status"] if portfolio else "not_run",
        "portfolio_claim_count": portfolio["claim_count"] if portfolio else 0,
    }
    summary["release_review_artifact_index"] = release_review_artifact_index(summary)
    return summary
