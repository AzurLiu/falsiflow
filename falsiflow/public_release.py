"""Public demo and release handoff workflows for Falsiflow."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Protocol

from . import __version__ as FALSIFLOW_VERSION
from .bundle import markdown_cell
from .quickstart import prepare_output_directory

ROOT = Path(__file__).resolve().parents[1]
DOWNSTREAM_DEMO_URL = "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo"
DOWNSTREAM_PR_URL = f"{DOWNSTREAM_DEMO_URL}/pull/1"
DOWNSTREAM_BLOCKED_RUN_URL = f"{DOWNSTREAM_DEMO_URL}/actions/runs/26711652990"
DOWNSTREAM_READY_RUN_URL = f"{DOWNSTREAM_DEMO_URL}/actions/runs/26711669112"
DOWNSTREAM_RAG_DEMO_URL = "https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo"
DOWNSTREAM_RAG_PR_URL = f"{DOWNSTREAM_RAG_DEMO_URL}/pull/1"
DOWNSTREAM_RAG_BLOCKED_RUN_URL = f"{DOWNSTREAM_RAG_DEMO_URL}/actions/runs/26721829145"
DOWNSTREAM_RAG_READY_RUN_URL = f"{DOWNSTREAM_RAG_DEMO_URL}/actions/runs/26721856616"


class TryRunner(Protocol):
    def __call__(
        self,
        template: str,
        out_dir: Path,
        template_roots: list[Path] | None = None,
        force: bool = False,
        include_env: bool = True,
    ) -> dict[str, object]: ...


def run_static_demo(
    template: str,
    out_dir: Path,
    template_roots: list[Path] | None = None,
    force: bool = False,
    *,
    try_runner: TryRunner,
) -> dict[str, object]:
    try_summary = try_runner(template, out_dir, template_roots, force=force)
    outputs = try_summary.get("outputs", {}) if isinstance(try_summary.get("outputs"), dict) else {}
    ready = try_summary.get("status") == "try_ready"
    static_summary = {
        "status": "static_demo_ready" if ready else "static_demo_blocked",
        "site_dir": str(out_dir),
        "index": str(outputs.get("launchpad", out_dir / "index.html")),
        "try_report": str(outputs.get("try_report", out_dir / "try_report.html")),
        "wizard": str(outputs.get("wizard", out_dir / "falsiflow_wizard.html")),
        "dashboard": str(outputs.get("dashboard", "")),
        "publishable": ready,
        "publish_note": "Host this directory with GitHub Pages, Netlify, or any static file server.",
        "try_summary": try_summary,
    }
    (out_dir / "static_demo_summary.json").write_text(json.dumps(static_summary, indent=2, sort_keys=True), encoding="utf-8")
    return static_summary


def render_demo_package_readme(summary: dict[str, object]) -> str:
    outputs = summary.get("outputs", {}) if isinstance(summary.get("outputs"), dict) else {}
    return "\n".join([
        "# Falsiflow Public Demo Package",
        "",
        "This directory is a static, zero-install Falsiflow demo package.",
        "",
        "## Preview",
        "",
        "- Open `index.html` locally, or publish this directory with GitHub Pages, Netlify, or any static file server.",
        "- The launchpad starts with the live downstream PR story: PR #1 in the downstream AI eval demo blocks placeholder evidence in CI, then passes after source-backed evidence is added.",
        f"- Workbench shell: `{outputs.get('workbench', 'workbench.html')}`",
        f"- Try report: `{outputs.get('try_report', 'try_report.html')}`",
        f"- Wizard: `{outputs.get('wizard', 'falsiflow_wizard.html')}`",
        "",
        "## Publish Checklist",
        "",
        "- Keep `.nojekyll` so GitHub Pages serves files exactly as written.",
        "- Netlify can deploy the directory directly; `netlify.toml` sets the publish root to this folder.",
        "- Set `FALSIFLOW_REPO_URL` and `FALSIFLOW_PUBLIC_DEMO_URL`, then run `falsiflow external-check --out-dir falsiflow_external_check --force --strict` before calling a release externally ready.",
        "",
        "## Boundary",
        "",
        "The demo shows evidence gates and audit outputs. It does not upload data, run cloud AI, or make unverified research claims ready.",
        "",
    ])

def render_demo_package_checklist(summary: dict[str, object]) -> str:
    return "\n".join([
        "# Falsiflow Demo Publish Checklist",
        "",
        f"- Package status: `{summary.get('status', '')}`",
        f"- Publishable static files: `{str(bool(summary.get('publishable'))).lower()}`",
        f"- External URL required: `{str(bool(summary.get('external_url_required'))).lower()}`",
        "",
        "## Before Sharing Publicly",
        "",
        "- Publish the directory with GitHub Pages, Netlify, or another static host.",
        "- Record the repository URL in `FALSIFLOW_REPO_URL`.",
        "- Record the hosted demo URL in `FALSIFLOW_PUBLIC_DEMO_URL`.",
        "- Re-run `falsiflow external-check --out-dir falsiflow_external_check --force --strict`.",
        "",
    ])

def run_demo_package(
    template: str,
    out_dir: Path,
    template_roots: list[Path] | None = None,
    force: bool = False,
    *,
    try_runner: TryRunner,
) -> dict[str, object]:
    try_summary = try_runner(template, out_dir, template_roots, force=force)
    outputs = try_summary.get("outputs", {}) if isinstance(try_summary.get("outputs"), dict) else {}
    ready = try_summary.get("status") == "try_ready"
    package_outputs = {
        "summary": str(out_dir / "demo_package_summary.json"),
        "static_demo_summary": str(out_dir / "static_demo_summary.json"),
        "index": str(outputs.get("launchpad", out_dir / "index.html")),
        "workbench": str(outputs.get("workbench", out_dir / "workbench.html")),
        "try_report": str(outputs.get("try_report", out_dir / "try_report.html")),
        "wizard": str(outputs.get("wizard", out_dir / "falsiflow_wizard.html")),
        "readme": str(out_dir / "README.md"),
        "publish_checklist": str(out_dir / "publish_checklist.md"),
        "netlify_config": str(out_dir / "netlify.toml"),
        "github_pages_marker": str(out_dir / ".nojekyll"),
    }
    summary: dict[str, object] = {
        "status": "demo_package_ready" if ready else "demo_package_blocked",
        "site_dir": str(out_dir),
        "template": template,
        "publishable": ready,
        "external_url_required": True,
        "public_hosting_required": True,
        "github_pages_ready": ready,
        "netlify_ready": ready,
        "local_preview": str(outputs.get("launchpad", out_dir / "index.html")),
        "required_external_values": ["FALSIFLOW_REPO_URL", "FALSIFLOW_PUBLIC_DEMO_URL"],
        "boundary": "Static demo package only; public hosting and repository URLs must be verified separately.",
        "outputs": package_outputs,
        "try_summary": try_summary,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    (out_dir / "netlify.toml").write_text("[build]\n  publish = \".\"\n", encoding="utf-8")
    (out_dir / "README.md").write_text(render_demo_package_readme(summary), encoding="utf-8")
    (out_dir / "publish_checklist.md").write_text(render_demo_package_checklist(summary), encoding="utf-8")
    (out_dir / "demo_package_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    static_summary = {
        "status": "static_demo_ready" if ready else "static_demo_blocked",
        "site_dir": str(out_dir),
        "index": package_outputs["index"],
        "try_report": package_outputs["try_report"],
        "wizard": package_outputs["wizard"],
        "workbench": package_outputs["workbench"],
        "publishable": ready,
        "publish_note": "Host this directory with GitHub Pages, Netlify, or any static file server.",
        "try_summary": try_summary,
    }
    (out_dir / "static_demo_summary.json").write_text(json.dumps(static_summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary

def default_pypi_package_url() -> str:
    return "https://pypi.org/project/falsiflow/"


def default_expected_version() -> str:
    return FALSIFLOW_VERSION


def external_evidence_template(repo_url: str = "", public_demo_url: str = "", pypi_package_url: str = "") -> dict[str, object]:
    return {
        "status": "external_evidence_draft",
        "version": 1,
        "instructions": "Set each required check to passed only after the linked public URL, CI run, or artifact proves the public release smoke test passed.",
        "checks": {
            "public_repo_url": {
                "status": "pending",
                "url": repo_url or "https://<owner>/<repo>",
                "evidence_url": "",
                "notes": "Public GitHub repository URL.",
            },
            "public_demo_url": {
                "status": "pending",
                "url": public_demo_url or "https://<host>/<demo>",
                "evidence_url": "",
                "notes": "Hosted static demo URL after GitHub Pages, Netlify, Cloudflare Pages, Vercel, or another static host is live.",
            },
            "pypi_package_url": {
                "status": "pending",
                "url": pypi_package_url or default_pypi_package_url(),
                "evidence_url": "",
                "verification_url": "https://pypi.org/pypi/falsiflow/json",
                "artifact": "falsiflow_pypi_project.json",
                "expected_version": default_expected_version(),
                "published_version": "",
                "notes": "Public PyPI package page plus PyPI JSON API evidence whose published version matches the expected release after trusted publishing succeeds.",
            },
            "pipx_smoke": {
                "status": "pending",
                "command": "pipx install --force . && falsiflow start --check --json",
                "workflow_url": "",
                "artifact_url": "",
                "notes": "Record a public CI run or artifact proving pipx install from the public repository checkout and smoke start passed.",
            },
            "pipx_public_package": {
                "status": "pending",
                "command": "pipx run --spec falsiflow falsiflow start --check --json",
                "workflow_url": "",
                "artifact_url": "",
                "notes": "Record a public CI run or artifact proving a clean pipx run from the published package passed.",
            },
            "public_package_first_run": {
                "status": "pending",
                "command": "pipx run --spec falsiflow falsiflow quickstart --template ai_claim_evaluation --strict --json && pipx run --spec falsiflow falsiflow doctor --strict --json",
                "workflow_url": "",
                "artifact_url": "",
                "notes": "Record a public CI run or artifact proving the published package README first-run quickstart and doctor path passed.",
            },
            "public_package_claim_check": {
                "status": "pending",
                "command": "pipx run --spec falsiflow falsiflow claim-check --project-dir <quickstart-project> --strict --force --json",
                "workflow_url": "",
                "artifact_url": "",
                "claim_check_status": "",
                "bundle_verification_status": "",
                "notes": "Record a public CI run or artifact proving the published package AI eval starter claim-check path reaches claim_check_ready and bundle_verified.",
            },
            "mcp_public_package_selftest": {
                "status": "pending",
                "command": "pipx run --spec falsiflow falsiflow mcp --selftest --json",
                "workflow_url": "",
                "artifact_url": "",
                "notes": "Record a public CI run or artifact proving the published package MCP selftest passed without opening a network listener.",
            },
            "windows_powershell": {
                "status": "pending",
                "command": ".\\scripts\\install_local.ps1 -FromLocal . -Check",
                "workflow_url": "",
                "artifact_url": "",
                "notes": "Record a public Windows workflow run or artifact proving the PowerShell installer path passed.",
            },
        },
    }

def render_external_evidence_report(summary: dict[str, object]) -> str:
    outputs = summary.get("outputs", {}) if isinstance(summary.get("outputs"), dict) else {}
    lines = [
        "# Falsiflow External Evidence Template",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Evidence file: `{outputs.get('evidence', '')}`",
        "",
        "## Required Checks",
        "",
        "| Check | What To Record |",
        "| --- | --- |",
        "| `public_repo_url` | Public HTTPS GitHub repository URL. |",
        "| `public_demo_url` | Hosted HTTPS static demo URL. |",
        "| `pypi_package_url` | Public PyPI project URL plus `https://pypi.org/pypi/falsiflow/json` evidence whose `published_version` matches `expected_version` after trusted publishing succeeds. |",
        "| `pipx_smoke` | Public CI run or artifact proving checkout-based pipx install and `falsiflow start --check --json` passed. |",
        "| `pipx_public_package` | Public CI run or artifact proving `pipx run --spec falsiflow falsiflow start --check --json` passed from the published package. |",
        "| `public_package_first_run` | Public CI run or artifact proving `pipx run --spec falsiflow falsiflow quickstart --template ai_claim_evaluation --strict --json` and `doctor --strict --json` passed from the published package. |",
        "| `public_package_claim_check` | Public CI run or artifact proving `pipx run --spec falsiflow falsiflow claim-check --project-dir <quickstart-project> --strict --force --json` reaches `claim_check_ready` and `bundle_verified` from the published package. |",
        "| `mcp_public_package_selftest` | Public CI run or artifact proving `pipx run --spec falsiflow falsiflow mcp --selftest --json` passed from the published package. |",
        "| `windows_powershell` | Public Windows workflow run or artifact proving `install_local.ps1 -Check` passed. |",
        "",
        "After filling the JSON evidence file, run:",
        "",
        "```bash",
        f"falsiflow external-check --out-dir falsiflow_external_check --evidence {outputs.get('evidence', 'falsiflow_external_evidence.json')} --force --strict",
        "```",
        "",
    ]
    return "\n".join(lines)

def run_external_evidence_template(
    out: Path,
    repo_url: str = "",
    public_demo_url: str = "",
    pypi_package_url: str = "",
    force: bool = False,
) -> dict[str, object]:
    if out.exists() and not force:
        raise SystemExit(f"External evidence file already exists: {out}. Use --force to replace it.")
    out.parent.mkdir(parents=True, exist_ok=True)
    evidence = external_evidence_template(repo_url=repo_url, public_demo_url=public_demo_url, pypi_package_url=pypi_package_url)
    report = out.with_suffix(".md")
    summary: dict[str, object] = {
        "status": "external_evidence_template_ready",
        "evidence_status": evidence["status"],
        "outputs": {
            "evidence": str(out),
            "report": str(report),
        },
        "next_commands": [
            f"falsiflow external-check --out-dir falsiflow_external_check --evidence {out} --force --strict",
        ],
        "evidence": evidence,
    }
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    report.write_text(render_external_evidence_report(summary), encoding="utf-8")
    return summary

def render_publish_env_example(repo_url: str, public_demo_url: str) -> str:
    return "\n".join([
        "# Falsiflow public release readiness inputs.",
        "# Fill these with real hosted values after creating the repository and demo site.",
        f"FALSIFLOW_REPO_URL={repo_url}",
        f"FALSIFLOW_PUBLIC_DEMO_URL={public_demo_url}",
        "# Set this to the real PyPI project URL after trusted publishing succeeds.",
        f"FALSIFLOW_PYPI_PACKAGE_URL={default_pypi_package_url()}",
        "# Expected PyPI JSON version for the external-evidence workflow.",
        f"FALSIFLOW_EXPECTED_VERSION={default_expected_version()}",
        "# Optional structured evidence file consumed by `falsiflow external-check --evidence`.",
        "FALSIFLOW_EXTERNAL_EVIDENCE=falsiflow_external_evidence.json",
        "# Set to 1 only after the pipx smoke workflow or local pipx smoke passes.",
        "FALSIFLOW_PIPX_VALIDATED=0",
        "# Set to 1 only after a clean pipx run from the published package passes.",
        "FALSIFLOW_PIPX_PUBLIC_VALIDATED=0",
        "# Set to 1 only after the published package first-run quickstart and doctor path passes.",
        "FALSIFLOW_PUBLIC_PACKAGE_FIRST_RUN_VALIDATED=0",
        "# Set to 1 only after the published package AI eval starter claim-check path reaches claim_check_ready.",
        "FALSIFLOW_PUBLIC_PACKAGE_CLAIM_CHECK_VALIDATED=0",
        "# Set to 1 only after a clean published-package MCP selftest passes.",
        "FALSIFLOW_MCP_PUBLIC_SELFTEST_VALIDATED=0",
        "# Set to 1 only after the Windows PowerShell workflow passes.",
        "FALSIFLOW_WINDOWS_VALIDATED=0",
        "",
    ])

def render_github_publish_commands(repo_slug: str, tag: str, public_demo_url: str) -> str:
    repo_arg = repo_slug or "OWNER/falsiflow"
    repo_url = f"https://github.com/{repo_arg}"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# Run these commands from the Falsiflow repository root after reviewing the generated publish kit.",
        "gh auth status || gh auth login",
        "git status --short",
        f"gh repo create {repo_arg} --public --source=. --remote=origin --push",
        "gh workflow run \"Falsiflow Cross Platform\"",
        "gh workflow run \"Falsiflow Pages Demo\"",
        f"gh release create {tag} --generate-notes --title \"Falsiflow {tag}\"",
        "sleep 10",
        "publish_run_id=\"$(gh run list --workflow falsiflow-publish.yml --event release --limit 1 --json databaseId --jq '.[0].databaseId')\"",
        "test -n \"$publish_run_id\"",
        "gh run watch \"$publish_run_id\" --exit-status",
        f"gh workflow run \"Falsiflow External Evidence\" --field public_demo_url=\"${{FALSIFLOW_PUBLIC_DEMO_URL:-https://OWNER.github.io/falsiflow/}}\" --field pypi_package_url=\"${{FALSIFLOW_PYPI_PACKAGE_URL:-https://pypi.org/project/falsiflow/}}\" --field expected_version=\"${{FALSIFLOW_EXPECTED_VERSION:-{default_expected_version()}}}\"",
        "",
        f"FALSIFLOW_REPO_URL={repo_url} \\",
        f"FALSIFLOW_PUBLIC_DEMO_URL={public_demo_url or 'https://OWNER.github.io/falsiflow/'} \\",
        f"FALSIFLOW_PYPI_PACKAGE_URL={default_pypi_package_url()} \\",
        f"FALSIFLOW_EXPECTED_VERSION={default_expected_version()} \\",
        "FALSIFLOW_EXTERNAL_EVIDENCE=falsiflow_external_evidence.json \\",
        "FALSIFLOW_PIPX_VALIDATED=1 \\",
        "FALSIFLOW_PIPX_PUBLIC_VALIDATED=1 \\",
        "FALSIFLOW_WINDOWS_VALIDATED=1 \\",
        "falsiflow external-check --out-dir falsiflow_external_check --evidence falsiflow_external_evidence.json --force --strict",
        "",
    ]
    return "\n".join(lines)

def render_publish_handoff(summary: dict[str, object]) -> str:
    outputs = summary.get("outputs", {}) if isinstance(summary.get("outputs"), dict) else {}
    blockers = summary.get("external_blockers", [])
    lines = [
        "# Falsiflow Publish Handoff",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Account action required: `{str(bool(summary.get('account_action_required'))).lower()}`",
        f"- External readiness: `{summary.get('external_status', '')}`",
        f"- Repository URL: `{summary.get('repo_url', '')}`",
        f"- Public demo URL: `{summary.get('public_demo_url', '')}`",
        "",
        "## Generated Artifacts",
        "",
    ]
    for key in ["demo_package", "external_readiness", "external_evidence_template", "env_example", "github_commands"]:
        if key in outputs:
            lines.append(f"- `{key}`: `{outputs[key]}`")
    for key in ["public_release_evidence_report", "public_release_evidence"]:
        if key in outputs:
            lines.append(f"- `{key}`: `{outputs[key]}`")
    for key in ["release_rehearsal_report", "release_rehearsal"]:
        if key in outputs:
            lines.append(f"- `{key}`: `{outputs[key]}`")
    lines.extend([
        "",
        "## Account Steps",
        "",
        "1. Log in with `gh auth login`.",
        "2. Create or choose the public GitHub repository.",
        "3. Push this source tree to the repository.",
        "4. Enable GitHub Pages for the Pages workflow, or deploy the generated `public_demo/` directory to another static host.",
        "5. Let the cross-platform workflow pass on Linux, macOS, and Windows.",
        "6. Publish the package through trusted publishing and confirm the public PyPI project URL.",
        "7. Publish the GitHub release only after trusted publishing is configured, then wait for the `Falsiflow Publish` `publish-pypi` job to pass.",
        "8. Run the `Falsiflow External Evidence` workflow with the hosted demo URL, PyPI package URL, and expected package version, then download its evidence artifact.",
        "9. Announce only after `release-check` and `external-check --strict` pass.",
        "",
    ])
    if isinstance(blockers, list) and blockers:
        lines.extend(["## Current External Blockers", ""])
        for blocker in blockers:
            if isinstance(blocker, dict):
                lines.append(f"- `{blocker.get('check', '')}`: {blocker.get('message', '')}")
        lines.append("")
    return "\n".join(lines)


def public_release_rehearsal(summary: dict[str, object]) -> dict[str, object]:
    repo_url = str(summary.get("repo_url", ""))
    public_demo_url = str(summary.get("public_demo_url", ""))
    external_status = str(summary.get("external_status", ""))
    tag = str(summary.get("tag", "v0.1.1"))
    outputs = summary.get("outputs", {}) if isinstance(summary.get("outputs"), dict) else {}
    return {
        "status": "release_rehearsal_ready",
        "external_status": external_status,
        "account_action_required": True,
        "repo_url": repo_url,
        "public_demo_url": public_demo_url,
        "pypi_package_url": default_pypi_package_url(),
        "expected_version": default_expected_version(),
        "decision_boundary": "This is a public-release rehearsal plan. It proves the local sequence is documented and reviewable, not that GitHub, hosting, PyPI, pipx, Windows, or Scorecard evidence has passed.",
        "success_condition": "Publish externally only after release-check is release_ready and external-check --strict is external_ready with real public evidence.",
        "steps": [
            {
                "id": "local_regression",
                "phase": "local-preflight",
                "owner": "Maintainer",
                "command": "make test",
                "expected_artifact": "terminal output",
                "success_signal": "Regression suite exits 0.",
                "status": "manual_rehearsal",
            },
            {
                "id": "release_check",
                "phase": "local-preflight",
                "owner": "Maintainer",
                "command": "falsiflow release-check --out-dir data/falsiflow/release_check --force",
                "expected_artifact": "data/falsiflow/release_check/release_check.md",
                "success_signal": "release_check.json reports release_ready and release_validation_ready.",
                "status": "manual_rehearsal",
            },
            {
                "id": "casebook_replay",
                "phase": "local-preflight",
                "owner": "Maintainer",
                "command": "falsiflow casebook-check --out-dir data/falsiflow/casebook_check --force",
                "expected_artifact": "data/falsiflow/casebook_check/casebook_reviewer_replay.md",
                "success_signal": "casebook_check_ready with Bash and PowerShell replay scripts.",
                "status": "manual_rehearsal",
            },
            {
                "id": "launch_kit",
                "phase": "launch-review",
                "owner": "Maintainer",
                "command": "falsiflow launch-kit --out-dir falsiflow_launch_kit --force",
                "expected_artifact": "falsiflow_launch_kit/launch_metrics.md",
                "success_signal": "launch_kit_ready with launch posts, proof card, maintainer checklist, and launch metrics.",
                "status": "manual_rehearsal",
            },
            {
                "id": "evidence_ledger_review",
                "phase": "launch-review",
                "owner": "Maintainer",
                "command": f"Review {outputs.get('public_release_evidence_report', 'public_release_evidence.md')} before continuing.",
                "expected_artifact": str(outputs.get("public_release_evidence_report", "public_release_evidence.md")),
                "success_signal": "public_release_evidence.md names every local-ready and pending-external proof.",
                "status": "manual_rehearsal",
            },
            {
                "id": "external_evidence_template",
                "phase": "external-evidence",
                "owner": "Maintainer",
                "command": "falsiflow external-evidence --out falsiflow_external_evidence.json --force",
                "expected_artifact": "falsiflow_external_evidence.json",
                "success_signal": "Template contains public repo, hosted demo, expected PyPI version, PyPI JSON, checkout-pipx, public-package-pipx, and Windows checks.",
                "status": "manual_rehearsal",
            },
            {
                "id": "github_release",
                "phase": "publish",
                "owner": "Maintainer",
                "command": f"gh release create {tag} --generate-notes --title \"Falsiflow {tag}\"",
                "expected_artifact": "Public GitHub release page and release-triggered Falsiflow Publish workflow run",
                "success_signal": "Release is public and the publish workflow started from the release event.",
                "status": "pending_external",
            },
            {
                "id": "pypi_publish",
                "phase": "publish",
                "owner": "GitHub Actions",
                "command": "gh run watch <Falsiflow Publish release run id> --exit-status",
                "expected_artifact": "Successful Falsiflow Publish workflow with publish-pypi job",
                "success_signal": "publish-pypi succeeds and the PyPI JSON API serves the expected version.",
                "status": "pending_external",
            },
            {
                "id": "external_workflow",
                "phase": "external-evidence",
                "owner": "GitHub Actions",
                "command": "gh workflow run \"Falsiflow External Evidence\" --field public_demo_url=\"$FALSIFLOW_PUBLIC_DEMO_URL\" --field pypi_package_url=\"$FALSIFLOW_PYPI_PACKAGE_URL\" --field expected_version=\"$FALSIFLOW_EXPECTED_VERSION\"",
                "expected_artifact": "falsiflow_external_evidence.json and falsiflow_pypi_project.json workflow artifacts",
                "success_signal": "Hosted demo fetch, PyPI JSON fetch with expected-version match, checkout pipx, public-package pipx, public-package first-run quickstart/doctor, public-package claim-check, public-package MCP selftest, and Windows smoke jobs pass.",
                "status": "pending_external",
            },
            {
                "id": "external_check_strict",
                "phase": "external-evidence",
                "owner": "Maintainer",
                "command": "falsiflow external-check --out-dir falsiflow_external_check --evidence falsiflow_external_evidence.json --force --strict",
                "expected_artifact": "falsiflow_external_check/external_readiness.md",
                "success_signal": "external_readiness.json reports external_ready.",
                "status": "pending_external",
            },
            {
                "id": "public_announcement",
                "phase": "publish",
                "owner": "Maintainer",
                "command": "Publish reviewed launch posts only after external_ready is recorded.",
                "expected_artifact": "Launch post URLs copied into launch_metrics.md",
                "success_signal": "Launch metrics tracker records post URLs, referrers, stars, forks, demo visits, installs, questions, and fixes.",
                "status": "pending_external",
            },
        ],
        "stop_conditions": [
            "Do not publish launch posts if release-check is not release_ready.",
            "Do not claim external readiness if external-check --strict is external_blocked.",
            "Do not claim PyPI or pipx availability until the public-package pipx smoke has passed.",
            "Do not claim Windows support until the public Windows workflow or PowerShell smoke has passed.",
        ],
        "required_artifacts": [
            "release_check.md",
            "casebook_reviewer_replay.md",
            "launch_metrics.md",
            "public_release_evidence.md",
            "falsiflow_external_evidence.json",
            "external_readiness.md",
        ],
    }


def render_public_release_rehearsal(summary: dict[str, object]) -> str:
    rehearsal = summary.get("release_rehearsal", {})
    if not isinstance(rehearsal, dict):
        rehearsal = public_release_rehearsal(summary)
    lines = [
        "# Falsiflow Public Release Rehearsal",
        "",
        f"- Status: `{rehearsal.get('status', '')}`",
        f"- External readiness: `{rehearsal.get('external_status', '')}`",
        f"- Account action required: `{str(bool(rehearsal.get('account_action_required'))).lower()}`",
        f"- Repository URL: `{rehearsal.get('repo_url', '')}`",
        f"- Public demo URL: `{rehearsal.get('public_demo_url', '')}`",
        f"- PyPI package URL: `{rehearsal.get('pypi_package_url', '')}`",
        "",
        "## Decision Boundary",
        "",
        str(rehearsal.get("decision_boundary", "")),
        "",
        "## Success Condition",
        "",
        str(rehearsal.get("success_condition", "")),
        "",
        "## Rehearsal Steps",
        "",
        "| ID | Phase | Owner | Command | Expected Artifact | Success Signal | Status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for step in rehearsal.get("steps", []):
        if not isinstance(step, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                f"`{markdown_cell(step.get('id', ''))}`",
                markdown_cell(step.get("phase", "")),
                markdown_cell(step.get("owner", "")),
                f"`{markdown_cell(step.get('command', ''))}`",
                f"`{markdown_cell(step.get('expected_artifact', ''))}`",
                markdown_cell(step.get("success_signal", "")),
                f"`{markdown_cell(step.get('status', ''))}`",
            ])
            + " |"
        )
    lines.extend(["", "## Stop Conditions", ""])
    for condition in rehearsal.get("stop_conditions", []):
        lines.append(f"- {condition}")
    lines.extend(["", "## Required Artifacts", ""])
    for artifact in rehearsal.get("required_artifacts", []):
        lines.append(f"- `{artifact}`")
    lines.append("")
    return "\n".join(lines)


def public_release_evidence_ledger(summary: dict[str, object]) -> dict[str, object]:
    repo_url = str(summary.get("repo_url", ""))
    public_demo_url = str(summary.get("public_demo_url", ""))
    pypi_url = default_pypi_package_url()
    external_status = str(summary.get("external_status", ""))
    return {
        "status": "public_release_evidence_ready",
        "external_status": external_status,
        "account_action_required": True,
        "repo_url": repo_url,
        "public_demo_url": public_demo_url,
        "pypi_package_url": pypi_url,
        "expected_version": default_expected_version(),
        "decision_boundary": "This ledger is a release-review checklist. It does not mark the public release externally ready until external-check --strict passes with real public evidence.",
        "evidence": [
            {
                "id": "public_repo_url",
                "status": "pending_external",
                "owner": "GitHub",
                "proof": "Public repository URL and workflow run URL.",
                "command": "falsiflow external-evidence --out falsiflow_external_evidence.json --force",
                "artifact": "falsiflow_external_evidence.json",
            },
            {
                "id": "hosted_demo_url",
                "status": "pending_external",
                "owner": "Static hosting",
                "proof": "HTTPS demo URL fetched by the Falsiflow External Evidence workflow.",
                "command": "gh workflow run \"Falsiflow External Evidence\" --field public_demo_url=\"$FALSIFLOW_PUBLIC_DEMO_URL\" --field pypi_package_url=\"$FALSIFLOW_PYPI_PACKAGE_URL\" --field expected_version=\"$FALSIFLOW_EXPECTED_VERSION\"",
                "artifact": "falsiflow_public_demo_index.html",
            },
            {
                "id": "pypi_package_url",
                "status": "pending_external",
                "owner": "PyPI trusted publishing",
                "proof": "Public PyPI project page plus PyPI JSON API response whose published version matches the expected release.",
                "command": "gh workflow run \"Falsiflow Publish\"",
                "artifact": "falsiflow_pypi_project.json",
            },
            {
                "id": "checkout_pipx_smoke",
                "status": "pending_external",
                "owner": "GitHub Actions",
                "proof": "pipx install from the public checkout and start smoke artifact.",
                "command": "python -m pipx run --spec . falsiflow start --check --json",
                "artifact": "falsiflow_pipx_start.json",
            },
            {
                "id": "public_package_pipx_smoke",
                "status": "pending_external",
                "owner": "GitHub Actions",
                "proof": "pipx run from the published package and start smoke artifact.",
                "command": "python -m pipx run --spec falsiflow falsiflow start --check --json",
                "artifact": "falsiflow_public_package_start.json",
            },
            {
                "id": "public_package_mcp_selftest",
                "status": "pending_external",
                "owner": "GitHub Actions",
                "proof": "pipx run from the published package and MCP selftest artifact.",
                "command": "python -m pipx run --spec falsiflow falsiflow mcp --selftest --json",
                "artifact": "falsiflow_public_package_mcp_selftest.json",
            },
            {
                "id": "public_package_first_run",
                "status": "pending_external",
                "owner": "GitHub Actions",
                "proof": "pipx run from the published package and README first-run quickstart/doctor artifacts.",
                "command": "python -m pipx run --spec falsiflow falsiflow quickstart --template ai_claim_evaluation --strict --json && python -m pipx run --spec falsiflow falsiflow doctor --strict --json",
                "artifact": "falsiflow_public_package_first_run_quickstart.json and falsiflow_public_package_first_run_doctor.json",
            },
            {
                "id": "public_package_claim_check",
                "status": "pending_external",
                "owner": "GitHub Actions",
                "proof": "pipx run from the published package and AI eval starter claim-check artifact.",
                "command": "python -m pipx run --spec falsiflow falsiflow claim-check --project-dir <quickstart-project> --strict --force --json",
                "artifact": "falsiflow_public_package_claim_check.json",
            },
            {
                "id": "windows_powershell_smoke",
                "status": "pending_external",
                "owner": "GitHub Actions Windows",
                "proof": "PowerShell installer smoke workflow run.",
                "command": ".\\scripts\\install_local.ps1 -FromLocal . -Check",
                "artifact": "Falsiflow External Evidence workflow run",
            },
            {
                "id": "release_check",
                "status": "local_ready",
                "owner": "Maintainer",
                "proof": "Full local release gate including package, dist, templates, adoption, and artifact indexes.",
                "command": "falsiflow release-check --out-dir data/falsiflow/release_check --force",
                "artifact": "data/falsiflow/release_check/release_check.md",
            },
            {
                "id": "casebook_replay",
                "status": "local_ready",
                "owner": "Maintainer",
                "proof": "Positive demos and placeholder blocked paths replayable by reviewers.",
                "command": "falsiflow casebook-check --out-dir data/falsiflow/casebook_check --force",
                "artifact": "data/falsiflow/casebook_check/casebook_reviewer_replay.md",
            },
            {
                "id": "launch_metrics",
                "status": "local_ready",
                "owner": "Maintainer",
                "proof": "Post-launch tracking windows for traffic, referrers, stars, demos, installs, questions, and fixes.",
                "command": "falsiflow launch-kit --out-dir falsiflow_launch_kit --force",
                "artifact": "falsiflow_launch_kit/launch_metrics.md",
            },
            {
                "id": "scorecard_workflow",
                "status": "pending_external",
                "owner": "GitHub Actions",
                "proof": "OpenSSF Scorecard workflow run and SARIF upload after the public repository is live.",
                "command": "gh workflow run \"Falsiflow Scorecard\"",
                "artifact": "scorecard-results.sarif",
            },
        ],
        "final_commands": [
            "falsiflow release-check --out-dir data/falsiflow/release_check --force",
            "falsiflow external-check --out-dir falsiflow_external_check --evidence falsiflow_external_evidence.json --force --strict",
        ],
    }


def render_public_release_evidence_ledger(summary: dict[str, object]) -> str:
    ledger = summary.get("public_release_evidence", {})
    if not isinstance(ledger, dict):
        ledger = public_release_evidence_ledger(summary)
    lines = [
        "# Falsiflow Public Release Evidence Ledger",
        "",
        f"- Status: `{ledger.get('status', '')}`",
        f"- External readiness: `{ledger.get('external_status', '')}`",
        f"- Account action required: `{str(bool(ledger.get('account_action_required'))).lower()}`",
        f"- Repository URL: `{ledger.get('repo_url', '')}`",
        f"- Public demo URL: `{ledger.get('public_demo_url', '')}`",
        f"- PyPI package URL: `{ledger.get('pypi_package_url', '')}`",
        "",
        "## Decision Boundary",
        "",
        str(ledger.get("decision_boundary", "")),
        "",
        "## Evidence",
        "",
        "| ID | Status | Owner | Proof | Command | Artifact |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in ledger.get("evidence", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                f"`{markdown_cell(row.get('id', ''))}`",
                f"`{markdown_cell(row.get('status', ''))}`",
                markdown_cell(row.get("owner", "")),
                markdown_cell(row.get("proof", "")),
                f"`{markdown_cell(row.get('command', ''))}`",
                f"`{markdown_cell(row.get('artifact', ''))}`",
            ])
            + " |"
        )
    lines.extend(["", "## Final Commands", ""])
    for command in ledger.get("final_commands", []):
        lines.append(f"- `{command}`")
    lines.append("")
    return "\n".join(lines)


def run_publish_kit(
    out_dir: Path,
    template: str,
    template_roots: list[Path] | None = None,
    repo_slug: str = "",
    public_demo_url: str = "",
    tag: str = "v0.1.1",
    force: bool = False,
    *,
    try_runner: TryRunner,
) -> dict[str, object]:
    prepare_output_directory(out_dir, "publish-kit output directory", force=force)
    out_dir.mkdir(parents=True, exist_ok=True)
    repo_slug_value = repo_slug.strip()
    repo_url = f"https://github.com/{repo_slug_value}" if repo_slug_value else "https://github.com/OWNER/falsiflow"
    demo_url = public_demo_url.strip() or ("https://OWNER.github.io/falsiflow/" if not repo_slug_value else f"https://{repo_slug_value.split('/', 1)[0]}.github.io/{repo_slug_value.split('/', 1)[-1]}/")
    demo_package = run_demo_package(template, out_dir / "public_demo", template_roots, force=True, try_runner=try_runner)
    external = run_external_check(out_dir / "external_readiness", force=True)
    outputs = {
        "summary": str(out_dir / "publish_handoff.json"),
        "report": str(out_dir / "publish_handoff.md"),
        "demo_package": str(out_dir / "public_demo" / "demo_package_summary.json"),
        "external_readiness": str(out_dir / "external_readiness" / "external_readiness.json"),
        "external_evidence_template": str(out_dir / "external_evidence_template.json"),
        "env_example": str(out_dir / "publish.env.example"),
        "github_commands": str(out_dir / "github_publish_commands.sh"),
        "public_release_evidence": str(out_dir / "public_release_evidence.json"),
        "public_release_evidence_report": str(out_dir / "public_release_evidence.md"),
        "release_rehearsal": str(out_dir / "release_rehearsal.json"),
        "release_rehearsal_report": str(out_dir / "release_rehearsal.md"),
    }
    ledger_seed = {
        "repo_url": repo_url,
        "public_demo_url": demo_url,
        "external_status": external.get("status", ""),
        "tag": tag,
        "outputs": outputs,
    }
    release_evidence = public_release_evidence_ledger(ledger_seed)
    release_rehearsal = public_release_rehearsal(ledger_seed)
    summary: dict[str, object] = {
        "status": "publish_kit_ready" if demo_package.get("status") == "demo_package_ready" else "publish_kit_blocked",
        "account_action_required": True,
        "repo_slug": repo_slug_value or "OWNER/falsiflow",
        "repo_url": repo_url,
        "public_demo_url": demo_url,
        "tag": tag,
        "external_status": external.get("status", ""),
        "external_blockers": external.get("blockers", []),
        "demo_package_status": demo_package.get("status", ""),
        "public_release_evidence_status": release_evidence["status"],
        "public_release_evidence": release_evidence,
        "release_rehearsal_status": release_rehearsal["status"],
        "release_rehearsal": release_rehearsal,
        "boundary": "This kit prepares all local release handoff artifacts; GitHub authentication, repository creation, Pages deployment, workflow results, and PyPI publishing remain external account actions.",
        "outputs": outputs,
        "next_commands": [
            f"bash {out_dir / 'github_publish_commands.sh'}",
            f"FALSIFLOW_REPO_URL={repo_url} FALSIFLOW_PUBLIC_DEMO_URL={demo_url} FALSIFLOW_PYPI_PACKAGE_URL={default_pypi_package_url()} FALSIFLOW_EXPECTED_VERSION={default_expected_version()} FALSIFLOW_EXTERNAL_EVIDENCE={out_dir / 'external_evidence_template.json'} FALSIFLOW_PIPX_VALIDATED=1 FALSIFLOW_PIPX_PUBLIC_VALIDATED=1 FALSIFLOW_WINDOWS_VALIDATED=1 falsiflow external-check --out-dir {out_dir / 'external_readiness_final'} --evidence {out_dir / 'external_evidence_template.json'} --force --strict",
        ],
    }
    (out_dir / "external_evidence_template.json").write_text(
        json.dumps(external_evidence_template(repo_url=repo_url, public_demo_url=demo_url, pypi_package_url=default_pypi_package_url()), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_dir / "publish.env.example").write_text(render_publish_env_example(repo_url, demo_url), encoding="utf-8")
    commands_path = out_dir / "github_publish_commands.sh"
    commands_path.write_text(render_github_publish_commands(repo_slug_value or "OWNER/falsiflow", tag, demo_url), encoding="utf-8")
    try:
        commands_path.chmod(0o755)
    except OSError:
        pass
    (out_dir / "public_release_evidence.json").write_text(json.dumps(release_evidence, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "public_release_evidence.md").write_text(render_public_release_evidence_ledger(summary), encoding="utf-8")
    (out_dir / "release_rehearsal.json").write_text(json.dumps(release_rehearsal, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "release_rehearsal.md").write_text(render_public_release_rehearsal(summary), encoding="utf-8")
    (out_dir / "publish_handoff.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "publish_handoff.md").write_text(render_publish_handoff(summary), encoding="utf-8")
    return summary

def render_readme_proof_strip_svg(summary: dict[str, object]) -> str:
    status = str(summary.get("status", "launch_kit_ready"))
    external_status = str(summary.get("external_status", "external_blocked"))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="420" viewBox="0 0 1200 420" role="img" aria-labelledby="title desc">
  <title id="title">Falsiflow evidence-gated claim workflow</title>
  <desc id="desc">A visual proof strip showing a claim moving through evidence gates, source provenance, audit bundles, and ready or blocked release decisions.</desc>
  <rect width="1200" height="420" rx="18" fill="#f8fbff"/>
  <rect x="24" y="24" width="1152" height="372" rx="16" fill="#ffffff" stroke="#d8e2ef"/>

  <text x="58" y="72" fill="#122033" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="32" font-weight="700">Falsiflow turns risky claims into auditable gates</text>
  <text x="58" y="108" fill="#52677f" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="18">Launch kit: {status}; external readiness: {external_status}</text>

  <g font-family="Inter, Segoe UI, Arial, sans-serif">
    <g transform="translate(58 156)">
      <rect width="190" height="126" rx="12" fill="#fff7ed" stroke="#f2c99a"/>
      <text x="18" y="34" fill="#8a4b10" font-size="15" font-weight="700">1. Claim</text>
      <text x="18" y="65" fill="#2f3b4a" font-size="18" font-weight="700">High-risk decision</text>
      <text x="18" y="94" fill="#6a7889" font-size="14">thresholds must be explicit</text>
    </g>
    <path d="M268 219h48" stroke="#90a4bc" stroke-width="3" stroke-linecap="round"/>
    <path d="M308 210l12 9-12 9" fill="none" stroke="#90a4bc" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    <g transform="translate(336 156)">
      <rect width="190" height="126" rx="12" fill="#eef8f2" stroke="#a8d8b4"/>
      <text x="18" y="34" fill="#24643a" font-size="15" font-weight="700">2. Evidence gates</text>
      <text x="18" y="65" fill="#2f3b4a" font-size="18" font-weight="700">CSV + rules</text>
      <text x="18" y="94" fill="#6a7889" font-size="14">missing rows stay blocked</text>
    </g>
    <path d="M546 219h48" stroke="#90a4bc" stroke-width="3" stroke-linecap="round"/>
    <path d="M586 210l12 9-12 9" fill="none" stroke="#90a4bc" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    <g transform="translate(614 156)">
      <rect width="190" height="126" rx="12" fill="#eef6ff" stroke="#a7cdf7"/>
      <text x="18" y="34" fill="#1d5a9e" font-size="15" font-weight="700">3. Provenance</text>
      <text x="18" y="65" fill="#2f3b4a" font-size="18" font-weight="700">Source files</text>
      <text x="18" y="94" fill="#6a7889" font-size="14">hashes and manifests travel</text>
    </g>
    <path d="M824 219h48" stroke="#90a4bc" stroke-width="3" stroke-linecap="round"/>
    <path d="M864 210l12 9-12 9" fill="none" stroke="#90a4bc" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    <g transform="translate(892 156)">
      <rect width="250" height="126" rx="12" fill="#f4f1ff" stroke="#c6b8f4"/>
      <text x="18" y="34" fill="#5639a6" font-size="15" font-weight="700">4. Audit bundle</text>
      <text x="18" y="65" fill="#2f3b4a" font-size="18" font-weight="700">Review + release checks</text>
      <text x="18" y="94" fill="#6a7889" font-size="14">ready only when all gates pass</text>
    </g>
  </g>
  <g font-family="Inter, Segoe UI, Arial, sans-serif" transform="translate(58 320)">
    <rect width="226" height="46" rx="23" fill="#eaf8ef" stroke="#9fd4ae"/>
    <circle cx="26" cy="23" r="10" fill="#2e9d52"/>
    <path d="M21 23l4 4 8-9" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    <text x="48" y="29" fill="#205e35" font-size="16" font-weight="700">claim_ready after proof</text>
    <rect x="250" width="250" height="46" rx="23" fill="#fff1f0" stroke="#f0b2ab"/>
    <circle cx="278" cy="23" r="10" fill="#d84b3f"/>
    <path d="M274 19l8 8m0-8l-8 8" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
    <text x="300" y="29" fill="#9b2d24" font-size="16" font-weight="700">claim_blocked on gaps</text>
    <rect x="524" width="296" height="46" rx="23" fill="#eef6ff" stroke="#b6d4f3"/>
    <text x="548" y="29" fill="#2c5b88" font-size="16" font-weight="700">JSON + Markdown + zip bundle</text>
    <rect x="844" width="238" height="46" rx="23" fill="#f8fafc" stroke="#d0d9e4"/>
    <text x="868" y="29" fill="#475569" font-size="16" font-weight="700">local-first, no cloud upload</text>
  </g>
</svg>
"""

def render_social_preview_svg(summary: dict[str, object]) -> str:
    external_status = str(summary.get("external_status", "external_blocked"))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640" role="img" aria-labelledby="title desc">
  <title id="title">Falsiflow GitHub social preview</title>
  <desc id="desc">Social preview for Falsiflow, an evidence-gated R&amp;D workflow engine for high-risk technical claims.</desc>
  <rect width="1280" height="640" fill="#f8fbff"/>
  <rect x="64" y="64" width="1152" height="512" rx="28" fill="#ffffff" stroke="#d7e3ef" stroke-width="2"/>
  <text x="112" y="154" fill="#122033" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="72" font-weight="800">Falsiflow</text>
  <text x="116" y="210" fill="#52677f" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="28" font-weight="600">Evidence-gated R&amp;D workflow engine</text>
  <text x="116" y="268" fill="#253449" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="34" font-weight="700">Block risky claims until evidence, provenance,</text>
  <text x="116" y="310" fill="#253449" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="34" font-weight="700">bundles, and release gates agree.</text>

  <g font-family="Inter, Segoe UI, Arial, sans-serif" font-size="22" font-weight="700">
    <rect x="116" y="382" width="202" height="56" rx="28" fill="#eaf8ef" stroke="#9fd4ae"/>
    <text x="148" y="418" fill="#205e35">claim_ready</text>
    <rect x="342" y="382" width="216" height="56" rx="28" fill="#fff1f0" stroke="#f0b2ab"/>
    <text x="374" y="418" fill="#9b2d24">claim_blocked</text>
    <rect x="582" y="382" width="274" height="56" rx="28" fill="#eef6ff" stroke="#b6d4f3"/>
    <text x="614" y="418" fill="#2c5b88">portable audit bundle</text>
  </g>

  <g transform="translate(914 148)" font-family="Inter, Segoe UI, Arial, sans-serif">
    <rect width="226" height="278" rx="20" fill="#f8fafc" stroke="#d0d9e4"/>
    <text x="28" y="54" fill="#475569" font-size="18" font-weight="700">Launch proof</text>
    <text x="28" y="98" fill="#122033" font-size="34" font-weight="800">6 templates</text>
    <text x="28" y="134" fill="#52677f" font-size="18">cross-domain starters</text>
    <text x="28" y="184" fill="#122033" font-size="34" font-weight="800">release_ready</text>
    <text x="28" y="220" fill="#52677f" font-size="18">local gates pass</text>
    <text x="28" y="252" fill="#52677f" font-size="16">external: {external_status}</text>
  </g>
</svg>
"""

def launch_topics() -> list[str]:
    return [
        "evidence",
        "provenance",
        "research",
        "workflow",
        "quality-gates",
        "audit",
        "templates",
        "r-and-d",
        "cli",
        "open-science",
        "ai-evaluation",
    ]

def render_github_repo_profile(summary: dict[str, object]) -> str:
    proof_card = summary.get("proof_card", {}) if isinstance(summary.get("proof_card"), dict) else {}
    topics = launch_topics()
    repo_url = str(summary.get("repo_url", ""))
    public_demo_url = str(summary.get("public_demo_url", ""))
    demo_pr_playbook_url = f"{repo_url.rstrip('/')}/blob/main/docs/falsiflow_demo_pr_playbook.md" if repo_url else "docs/falsiflow_demo_pr_playbook.md"
    return "\n".join([
        "# Falsiflow GitHub Repository Profile",
        "",
        "Use this when configuring the public GitHub repository About box, topics, links, and social preview.",
        "",
        "## About Description",
        "",
        "Evidence-gated R&D workflow engine for high-risk technical claims.",
        "",
        "## Website",
        "",
        public_demo_url,
        "",
        "## Topics",
        "",
        " ".join(f"`{topic}`" for topic in topics),
        "",
        "## Social Preview",
        "",
        "Upload `social_preview.svg` in GitHub repository settings after reviewing the generated image.",
        "",
        "## Pinned Links",
        "",
        f"- Repository: {repo_url}",
        f"- Public demo: {public_demo_url}",
        f"- Live AI eval downstream PR proof: {DOWNSTREAM_PR_URL}",
        f"- AI eval blocked CI run: {DOWNSTREAM_BLOCKED_RUN_URL}",
        f"- AI eval ready CI run: {DOWNSTREAM_READY_RUN_URL}",
        f"- Live RAG eval downstream PR proof: {DOWNSTREAM_RAG_PR_URL}",
        f"- RAG eval blocked CI run: {DOWNSTREAM_RAG_BLOCKED_RUN_URL}",
        f"- RAG eval ready CI run: {DOWNSTREAM_RAG_READY_RUN_URL}",
        f"- Demo PR playbook: {demo_pr_playbook_url}",
        "- README proof strip: `docs/assets/falsiflow_proof_strip.svg`",
        "- 30-second README demo: `docs/assets/falsiflow_30_second_demo.svg`",
        "- CLI reference: `docs/falsiflow_cli_reference.md`",
        "- Positioning and casebook: `docs/falsiflow_positioning.md`",
        "- Release checklist: `RELEASE.md`",
        "- Launch tracker: `launch_metrics.md`",
        "",
        "## Launch Proof",
        "",
        str(proof_card.get("one_liner", "")),
        "",
        "## Boundary",
        "",
        "Do not describe `claim_ready` as scientific proof. It means supplied evidence passed configured gates and provenance checks.",
        "",
    ])

def render_launch_posts(summary: dict[str, object]) -> str:
    repo_url = str(summary.get("repo_url", ""))
    public_demo_url = str(summary.get("public_demo_url", ""))
    external_status = str(summary.get("external_status", ""))
    demo_pr_playbook_url = f"{repo_url.rstrip('/')}/blob/main/docs/falsiflow_demo_pr_playbook.md" if repo_url else "docs/falsiflow_demo_pr_playbook.md"
    return "\n".join([
        "# Falsiflow Launch Posts",
        "",
        "Use these as drafts after the final public repository, hosted demo, live downstream AI/RAG PRs, and release evidence are green.",
        "",
        "## Channel Checklist",
        "",
        "Post only after `external_ready` is recorded or the remaining blocker is named in the first paragraph.",
        "",
        "| Channel | Best fit | Before posting | Follow-up |",
        "| --- | --- | --- | --- |",
        "| Hacker News / Show HN | Concise technical launch with a working demo. | Confirm PyPI status, demo URL, live downstream AI/RAG PRs, release evidence, and responsible-use boundary. | Watch the first 60 minutes for install failures and unclear positioning questions. |",
        "| Reddit / community threads | Feedback from people running AI eval, RAG eval, product analytics, R&D review, or CI gates. | Choose one relevant community at a time and include the downstream PR proofs plus demo PR playbook. | Turn repeated questions into docs or labeled GitHub issues within 24 hours. |",
        "| LinkedIn | Product and research leadership audience. | Lead with the risk of unsupported claims, not implementation internals. | Collect use-case requests and decide whether they belong in starter templates. |",
        "| X / short thread | Fast visual summary and demo link. | Put `claim_check_blocked` and `claim_check_ready` in the first two posts. | Link the README proof strip, demo PR playbook, and release evidence in replies. |",
        "| Awesome lists / ecosystem repos | Longer-lived discovery after launch traffic fades. | Submit only after PyPI, public demo, and README first-run path are stable. | Track accepted listings, declined submissions, and requested docs fixes in `launch_metrics.md`. |",
        "",
        "Open a follow-up issue for every repeated question, broken install path, confusing README section, demo screenshot gap, or template request that appears in launch replies.",
        "",
        "## Hacker News",
        "",
        "Title: Show HN: Falsiflow - stop unverifiable AI eval claims from passing CI",
        "",
        "I built Falsiflow, a local-first CLI and reusable GitHub Action for the moment a team says \"the model improved,\" \"the launch metric passed,\" or \"this experiment is ready.\" It turns that sentence into explicit evidence rows, required source files, derived metrics, review artifacts, and a CI status. Placeholder evidence stays `claim_check_blocked`; source-backed evidence can become `claim_check_ready`.",
        "",
        f"Repo: {repo_url}",
        f"Demo: {public_demo_url}",
        f"AI eval downstream PR: {DOWNSTREAM_PR_URL}",
        f"AI eval blocked run: {DOWNSTREAM_BLOCKED_RUN_URL}",
        f"AI eval ready run: {DOWNSTREAM_READY_RUN_URL}",
        f"RAG eval downstream PR: {DOWNSTREAM_RAG_PR_URL}",
        f"RAG eval blocked run: {DOWNSTREAM_RAG_BLOCKED_RUN_URL}",
        f"RAG eval ready run: {DOWNSTREAM_RAG_READY_RUN_URL}",
        f"Demo PR playbook: {demo_pr_playbook_url}",
        "",
        "The fastest demo is a pair of real downstream PRs: one AI-eval claim and one RAG-eval claim first fail because placeholder provenance backs the claim, then turn green after source-backed rows and raw export evidence are added. It is not an ELN/LIMS, not a regulatory system, and not scientific proof. It is a reproducible audit layer for deciding whether supplied evidence is complete enough to move forward.",
        "",
        "## Reddit / Community Post",
        "",
        "I am open-sourcing Falsiflow, a small evidence-gated workflow engine for AI eval, product metric, and R&D claims. It packages claim checks, source-file provenance, audit reports, template release bundles, reusable GitHub Actions, and local browser demos into one repeatable gate. I would love feedback from people who have watched spreadsheet-based evidence review or model-eval launch claims drift over time.",
        "",
        f"- Repo: {repo_url}",
        f"- Demo: {public_demo_url}",
        f"- AI eval downstream PR: {DOWNSTREAM_PR_URL}",
        f"- AI eval blocked run: {DOWNSTREAM_BLOCKED_RUN_URL}",
        f"- AI eval ready run: {DOWNSTREAM_READY_RUN_URL}",
        f"- RAG eval downstream PR: {DOWNSTREAM_RAG_PR_URL}",
        f"- RAG eval blocked run: {DOWNSTREAM_RAG_BLOCKED_RUN_URL}",
        f"- RAG eval ready run: {DOWNSTREAM_RAG_READY_RUN_URL}",
        f"- Demo PR playbook: {demo_pr_playbook_url}",
        "- Try locally: `make install-local && make start`",
        f"- CI gate: `uses: AzurLiu/falsiflow@v{FALSIFLOW_VERSION}` with `mode: claim-check`",
        "- Verify: `falsiflow release-check --out-dir data/falsiflow/release_check --force`",
        "",
        "## LinkedIn",
        "",
        "Falsiflow is ready for public review: CI gates for claims that should not ship on vibes. It targets AI eval claims, product-metric launches, and R&D decisions where the sentence sounds simple but the evidence package matters.",
        "",
        "The clean downstream PRs show the core behavior for both AI eval and RAG eval: placeholder evidence produces `claim_check_blocked`; source-backed evidence produces `claim_check_ready`; reviewers get JSON, Markdown, source manifests, dashboards, and a bundle verification report.",
        "",
        f"AI eval downstream PR: {DOWNSTREAM_PR_URL}",
        f"AI eval blocked run: {DOWNSTREAM_BLOCKED_RUN_URL}",
        f"AI eval ready run: {DOWNSTREAM_READY_RUN_URL}",
        f"RAG eval downstream PR: {DOWNSTREAM_RAG_PR_URL}",
        f"RAG eval blocked run: {DOWNSTREAM_RAG_BLOCKED_RUN_URL}",
        f"RAG eval ready run: {DOWNSTREAM_RAG_READY_RUN_URL}",
        f"Demo PR playbook: {demo_pr_playbook_url}",
        "",
        "The goal is not to replace lab systems, eval harnesses, or product analytics. It is to make the handoff between claim, evidence, source files, and release checks explicit enough that reviewers can trust what moved forward and why.",
        "",
        f"External readiness at launch-kit time: `{external_status}`.",
        "",
        "## X / Short Thread",
        "",
        "1/ I built Falsiflow: CI gates for claims like \"the model improved\" or \"the launch metric passed.\" Claims stay blocked until evidence rows, source files, thresholds, and bundles agree.",
        "",
        "2/ The quickest demo is two downstream PRs: placeholder AI/RAG eval evidence fails as `claim_check_blocked`; source-backed evidence passes as `claim_check_ready`.",
        "",
        f"3/ AI PR: {DOWNSTREAM_PR_URL} Blocked: {DOWNSTREAM_BLOCKED_RUN_URL} Ready: {DOWNSTREAM_READY_RUN_URL}",
        "",
        f"4/ RAG PR: {DOWNSTREAM_RAG_PR_URL} Blocked: {DOWNSTREAM_RAG_BLOCKED_RUN_URL} Ready: {DOWNSTREAM_RAG_READY_RUN_URL}",
        "",
        f"5/ Demo: {public_demo_url} Repo: {repo_url} Playbook: {demo_pr_playbook_url}",
        "",
        "## Reply Bank",
        "",
        "**How is this different from Great Expectations, Evidently, Deepchecks, or MLflow?**",
        "",
        "Those tools can generate or validate important evidence. Falsiflow sits at the claim-promotion boundary: it asks whether the full evidence package is complete enough for a claim to move forward in CI.",
        "",
        "**Can I use it before PyPI is published?**",
        "",
        "Yes. The reusable GitHub Action installs from `GITHUB_ACTION_PATH` by default, so `uses: AzurLiu/falsiflow@main` works without depending on PyPI.",
        "",
        "**Does `claim_ready` mean the claim is true?**",
        "",
        "No. It means the supplied evidence passed the repository's configured gates and provenance checks. It is not proof of safety, efficacy, regulatory compliance, or experimental truth.",
        "",
        "**Why include both AI eval and RAG eval demos?**",
        "",
        "They fail for different evidence gaps. The AI eval story is about pinned benchmark provenance, raw outputs, baselines, thresholds, and evaluator metadata. The RAG story adds retrieval, faithfulness, citation coverage, reproducibility rows, and the raw RAG export.",
        "",
        "## Short Post",
        "",
        f"Falsiflow turns AI eval, RAG eval, product metric, and R&D claims into auditable CI gates: claim -> evidence rows -> source provenance -> review bundle -> ready/blocked. AI PR: {DOWNSTREAM_PR_URL} RAG PR: {DOWNSTREAM_RAG_PR_URL} Demo: {public_demo_url} Repo: {repo_url}",
        "",
    ])

def render_launch_readme(summary: dict[str, object]) -> str:
    outputs = summary.get("outputs", {}) if isinstance(summary.get("outputs"), dict) else {}
    return "\n".join([
        "# Falsiflow Launch Kit",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- External readiness: `{summary.get('external_status', '')}`",
        f"- Account action required: `{str(bool(summary.get('account_action_required'))).lower()}`",
        f"- Repository URL: `{summary.get('repo_url', '')}`",
        f"- Public demo URL: `{summary.get('public_demo_url', '')}`",
        "",
        "## Use This Kit For",
        "",
        "- Reviewing the public launch story before repository or hosting account work.",
        "- Running a short demo that starts from the browser launchpad and ends at evidence provenance.",
        "- Sharing concise proof that Falsiflow has install, demo, audit, and release gates.",
        "",
        "## Files",
        "",
        f"- Proof card JSON: `{outputs.get('proof_card', '')}`",
        f"- Proof card Markdown: `{outputs.get('proof_card_report', '')}`",
        f"- Announcement draft: `{outputs.get('announcement', '')}`",
        f"- Demo script: `{outputs.get('demo_script', '')}`",
        f"- README proof strip: `{outputs.get('readme_proof_strip', '')}`",
        f"- Social preview: `{outputs.get('social_preview', '')}`",
        f"- GitHub repo profile: `{outputs.get('github_repo_profile', '')}`",
        f"- Launch posts: `{outputs.get('launch_posts', '')}`",
        f"- Launch metrics JSON: `{outputs.get('launch_metrics', '')}`",
        f"- Launch metrics Markdown: `{outputs.get('launch_metrics_report', '')}`",
        f"- Maintainer checklist: `{outputs.get('maintainer_checklist', '')}`",
        f"- Publish handoff: `{outputs.get('publish_kit', '')}`",
        f"- Public release evidence ledger: `{outputs.get('public_release_evidence', '')}`",
        f"- Public release rehearsal: `{outputs.get('release_rehearsal', '')}`",
        "",
        "## Boundary",
        "",
        "This kit prepares local launch materials. It does not prove external hosting, GitHub workflow results, pipx availability, Windows validation, PyPI publishing, safety, efficacy, regulatory compliance, or experimental truth.",
        "",
    ])

def render_launch_announcement(summary: dict[str, object]) -> str:
    repo_url = str(summary.get("repo_url", ""))
    demo_pr_playbook_url = f"{repo_url.rstrip('/')}/blob/main/docs/falsiflow_demo_pr_playbook.md" if repo_url else "docs/falsiflow_demo_pr_playbook.md"
    return "\n".join([
        "# Falsiflow Launch Announcement Draft",
        "",
        "Falsiflow is a CI gate for claims that should not ship on unsupported evidence.",
        "",
        "It turns AI eval, product metric, and R&D claims into explicit gates, required evidence rows, source-file policy, derived metrics, and acceptance rules. A claim only becomes ready when configuration, evidence, provenance, bundles, and verification artifacts agree.",
        "",
        "## Try It",
        "",
        "```bash",
        "make install-local",
        "make start",
        "```",
        "",
        "CLI-first path:",
        "",
        "```bash",
        "python3 -m pip install -e .",
        "falsiflow quickstart --template biointerface_coatings --out my_falsiflow_project --strict",
        "falsiflow doctor --project-dir my_falsiflow_project --strict",
        "```",
        "",
        "## What To Inspect",
        "",
        f"- Demo PR playbook: {demo_pr_playbook_url}",
        "- The blocked-to-ready demo: `evidence_placeholder_demo.csv` produces `claim_check_blocked`; `evidence_pass_demo.csv` produces `claim_check_ready`.",
        "- `claim_check.json` and `claim_check.md` for the ready/blocked decision.",
        "- `audit_review.md` for the human review card.",
        "- `evidence_bundle.zip` and `evidence_bundle_verify.md` for portable provenance.",
        "- `falsiflow template-gallery` for cross-domain starter templates.",
        "- `falsiflow release-check` for package, distribution, demo, template, and adoption gates.",
        "",
        "## Public Release Boundary",
        "",
        f"- External readiness currently reports `{summary.get('external_status', '')}`.",
        "- `claim_ready` means supplied evidence passed configured gates. It is not proof of safety, efficacy, regulatory compliance, or experimental truth.",
        "",
    ])

def render_launch_demo_script(summary: dict[str, object]) -> str:
    repo_url = str(summary.get("repo_url", ""))
    demo_pr_playbook_url = f"{repo_url.rstrip('/')}/blob/main/docs/falsiflow_demo_pr_playbook.md" if repo_url else "docs/falsiflow_demo_pr_playbook.md"
    return "\n".join([
        "# Falsiflow Three-Minute Demo Script",
        "",
        "## 0:00 Problem",
        "",
        "AI eval, product metric, and R&D claims often advance with missing provenance, placeholder evidence, or ambiguous thresholds. Falsiflow blocks that drift.",
        "",
        "## 0:30 Local Browser",
        "",
        "```bash",
        "make install-local",
        "make start",
        "```",
        "",
        "Open the launchpad, then the proof report, dashboard, workbench, and wizard.",
        "",
        "## 1:15 Evidence Gate",
        "",
        "```bash",
        "falsiflow quickstart --template biointerface_coatings --out my_falsiflow_project --strict",
        "falsiflow doctor --project-dir my_falsiflow_project --strict",
        "```",
        "",
        "Show `claim_check.md`, `audit_review.md`, `dashboard.html`, and `evidence_bundle_verify.md`.",
        "",
        "## 2:15 Demo PR",
        "",
        f"Open the demo PR playbook: {demo_pr_playbook_url}",
        "",
        "Show the same AI-eval claim moving from `claim_check_blocked` with `evidence_placeholder_demo.csv` to `claim_check_ready` with `evidence_pass_demo.csv`.",
        "",
        "## 2:35 Generality",
        "",
        "```bash",
        "falsiflow template-gallery --out data/falsiflow/template_gallery.md --json-out data/falsiflow/template_gallery.json",
        "```",
        "",
        "Show that the same contract covers neural materials, biointerface coatings, wetware support hardware, vendor RFQ evidence, AI claim evaluation, and product metric launch claims.",
        "",
        "## 2:50 Release Proof",
        "",
        "```bash",
        "falsiflow adoption-check --out-dir data/falsiflow/adoption_check --force",
        "falsiflow release-check --out-dir data/falsiflow/release_check --force",
        "```",
        "",
        f"End by noting that external readiness is `{summary.get('external_status', '')}` until public hosting, PyPI, pipx, and Windows validation evidence are recorded.",
        "",
    ])

def launch_metrics_plan(summary: dict[str, object]) -> dict[str, object]:
    repo_url = str(summary.get("repo_url", ""))
    public_demo_url = str(summary.get("public_demo_url", ""))
    return {
        "status": "launch_metrics_ready",
        "goal": "Reach 1,000 GitHub stars with evidence-first adoption rather than vanity clicks.",
        "repo_url": repo_url,
        "public_demo_url": public_demo_url,
        "artifacts": [
            {
                "path": "launch_metrics.json",
                "use": "Structured launch-review source for scripts, issue comments, or spreadsheets.",
            },
            {
                "path": "launch_metrics.md",
                "use": "Weekly maintainer review checklist for traction, validation boundaries, and follow-up issues.",
            },
        ],
        "funnel": [
            {
                "stage": "impression",
                "signal": "README/social preview viewed",
                "target": "Visitors understand the blocked-claim promise in under one minute.",
                "source": "GitHub traffic, launch post analytics, referrers",
                "action": "Tighten headline, proof strip, and first command if visitors bounce before trying the demo.",
            },
            {
                "stage": "trial",
                "signal": "Hosted demo or local start path opened",
                "target": "Visitors can inspect ready and blocked examples without account setup.",
                "source": "Demo host analytics, GitHub Pages/Netlify logs, README clicks",
                "action": "Promote `make install-local && make start` and the public demo above deeper docs.",
            },
            {
                "stage": "verification",
                "signal": "demo PR replay, release-check, casebook replay, or pipx smoke run",
                "target": "Reviewers can reproduce the proof before starring or sharing.",
                "source": "CI artifacts, issue comments, community replies, pipx/PyPI download signals",
                "action": "Link directly to the demo PR playbook, casebook replay, and release-check evidence from launch replies.",
            },
            {
                "stage": "conversion",
                "signal": "star, fork, issue, template request, or citation",
                "target": "Stars come with enough intent to produce issues, forks, templates, or feedback.",
                "source": "GitHub stars/forks/issues, issue templates, discussion links",
                "action": "Turn repeated questions into docs, examples, and starter templates within 24 hours.",
            },
        ],
        "weekly_maintainer_review": [
            {
                "step": "Collect traction signals",
                "checks": [
                    "Record GitHub traffic, top referrers, stars, forks, and clones.",
                    "Record demo visits and install/download signals from public channels only.",
                    "Record repeated questions from issues, launch replies, and community threads.",
                ],
            },
            {
                "step": "Separate validation from traction",
                "checks": [
                    "Keep release-check, adoption-check, casebook-check, and private smoke runs under validation evidence.",
                    "Do not count local/private validation, placeholder evidence, or maintainer-only test traffic as public traction.",
                    "Promote traction claims only when public referrers, demo visits, installs, stars, forks, clones, issues, or template requests support them.",
                ],
            },
            {
                "step": "Open concrete follow-up issues",
                "checks": [
                    "Open one issue per repeated question, broken install path, confusing doc section, demo fix, or template request.",
                    "Include the source signal, affected artifact, owner, label, and verification command in each issue.",
                    "Close the weekly review only after at least one docs/demo fix or a documented no-change decision exists.",
                ],
            },
        ],
        "review_windows": [
            {
                "window": "pre-launch",
                "checks": [
                    "release-check and adoption-check pass locally",
                    "external-check is either strict-ready or blockers are named honestly",
                    "README first screen shows proof strip, demo URL, and five-minute path",
                    "demo PR playbook has a blocked-to-ready recording path",
                    "launch posts include the responsible-use boundary and PyPI status",
                ],
            },
            {
                "window": "day-0",
                "checks": [
                    "record launch post URLs and first referrers",
                    "verify public demo HTTPS URL after posting",
                    "watch for install errors, Windows reports, and unclear README questions",
                    "reply with the demo PR playbook when people ask whether blockers are real",
                    "reply with casebook replay commands when people ask whether blockers are real",
                ],
            },
            {
                "window": "day-1",
                "checks": [
                    "compare GitHub views, unique visitors, clones, stars, and forks",
                    "identify top referrers and pages from GitHub traffic",
                    "patch README if the most common question is already answerable",
                    "ship one small doc or demo fix while traffic is warm",
                ],
            },
            {
                "window": "day-3",
                "checks": [
                    "summarize conversion from demo visitors to stars/issues",
                    "turn repeated use-case requests into issue labels or starter-template candidates",
                    "re-run release-check after any public-launch fix",
                    "post a short follow-up with concrete blocker examples",
                ],
            },
            {
                "window": "day-7",
                "checks": [
                    "review whether stars are accompanied by forks, issues, or template requests",
                    "publish one deeper casebook or architecture write-up if traffic is qualified",
                    "refresh public demo and external evidence after fixes",
                    "decide whether another community launch is justified",
                ],
            },
            {
                "window": "day-14",
                "checks": [
                    "compare star growth against the 1k target and referral mix",
                    "prune weak launch channels and double down on qualified referrers",
                    "promote install path only after pipx/PyPI evidence is public",
                    "move repeated feature asks into ROADMAP only when they preserve scope",
                ],
            },
        ],
        "follow_up_issue_fields": [
            "source_signal",
            "affected_artifact",
            "proposed_fix",
            "owner",
            "label",
            "verification_command",
            "launch_window",
        ],
        "daily_fields": [
            "date",
            "stars",
            "forks",
            "watchers",
            "unique_visitors",
            "views",
            "clones",
            "top_referrers",
            "demo_visits",
            "pipx_or_pypi_signal",
            "issues_opened",
            "docs_or_demo_fix_shipped",
        ],
        "commands": [
            "falsiflow launch-kit --out-dir falsiflow_launch_kit --force",
            "falsiflow release-check --out-dir data/falsiflow/release_check --force",
            "falsiflow casebook-check --out-dir data/falsiflow/casebook_check --force",
            "falsiflow claim-check --project-dir falsiflow_ai_eval --evidence falsiflow_ai_eval/evidence.csv --out-dir data/falsiflow/demo_pr_ready --strict --force",
        ],
        "boundary": "Do not treat local/private validation, private traffic, or placeholder external evidence as public traction.",
    }

def render_launch_metrics(summary: dict[str, object]) -> str:
    metrics = summary.get("launch_metrics", {}) if isinstance(summary.get("launch_metrics"), dict) else launch_metrics_plan(summary)
    lines = [
        "# Falsiflow 1k-Star Launch Tracker",
        "",
        f"- Status: `{metrics.get('status', '')}`",
        f"- Goal: {metrics.get('goal', '')}",
        f"- Repository URL: `{metrics.get('repo_url', '')}`",
        f"- Public demo URL: `{metrics.get('public_demo_url', '')}`",
        "",
        "## Generated Artifacts",
        "",
        "| Artifact | Use |",
        "| --- | --- |",
    ]
    for artifact in metrics.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(artifact.get("path", "")),
                markdown_cell(artifact.get("use", "")),
            ])
            + " |"
        )
    lines.extend([
        "",
        "## Funnel",
        "",
        "| Stage | Signal | Target | Source | Action |",
        "| --- | --- | --- | --- | --- |",
    ])
    for row in metrics.get("funnel", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(row.get("stage", "")),
                markdown_cell(row.get("signal", "")),
                markdown_cell(row.get("target", "")),
                markdown_cell(row.get("source", "")),
                markdown_cell(row.get("action", "")),
            ])
            + " |"
        )
    lines.extend(["", "## Weekly Maintainer Review", ""])
    for item in metrics.get("weekly_maintainer_review", []):
        if not isinstance(item, dict):
            continue
        lines.extend([f"### {item.get('step', '')}", ""])
        for check in item.get("checks", []):
            lines.append(f"- [ ] {check}")
        lines.append("")
    lines.extend(["", "## Review Windows", ""])
    for window in metrics.get("review_windows", []):
        if not isinstance(window, dict):
            continue
        lines.extend([f"### {window.get('window', '')}", ""])
        for check in window.get("checks", []):
            lines.append(f"- [ ] {check}")
        lines.append("")
    lines.extend([
        "## Daily Fields",
        "",
        "Record these fields in a launch note, spreadsheet, or issue comment:",
        "",
    ])
    for field in metrics.get("daily_fields", []):
        lines.append(f"- `{field}`")
    lines.extend([
        "",
        "## Follow-Up Issue Fields",
        "",
        "Every repeated question, install failure, docs gap, demo fix, or template request should become a concrete follow-up issue with:",
        "",
    ])
    for field in metrics.get("follow_up_issue_fields", []):
        lines.append(f"- `{field}`")
    lines.extend(["", "## Recheck Commands", ""])
    for command in metrics.get("commands", []):
        lines.append(f"- `{command}`")
    lines.extend(["", "## Boundary", "", str(metrics.get("boundary", "")), ""])
    return "\n".join(lines)

def render_launch_maintainer_checklist(summary: dict[str, object]) -> str:
    blockers = summary.get("external_blockers", [])
    lines = [
        "# Falsiflow Public Launch Maintainer Checklist",
        "",
        "## Local Gates",
        "",
        "- [ ] `make test` passes.",
        "- [ ] `falsiflow adoption-check --out-dir data/falsiflow/adoption_check --force` reports `adoption_ready`.",
        "- [ ] `falsiflow release-check --out-dir data/falsiflow/release_check --force` reports `release_ready`.",
        "- [ ] `falsiflow launch-kit --out-dir falsiflow_launch_kit --force` reports `launch_kit_ready`.",
        "- [ ] `release_rehearsal.md` has been reviewed for step order, expected artifacts, success signals, and stop conditions.",
        "- [ ] `docs/falsiflow_demo_pr_playbook.md` has been rehearsed with `claim_check_blocked` followed by `claim_check_ready`.",
        "",
        "## External Gates",
        "",
        "- [ ] Public GitHub repository URL is set in `FALSIFLOW_REPO_URL`.",
        "- [ ] Hosted static demo URL is set in `FALSIFLOW_PUBLIC_DEMO_URL`.",
        "- [ ] pipx smoke evidence is recorded with `FALSIFLOW_PIPX_VALIDATED=1` or a successful workflow.",
        "- [ ] Windows PowerShell evidence is recorded with `FALSIFLOW_WINDOWS_VALIDATED=1` or a successful workflow.",
        "- [ ] `falsiflow external-check --out-dir falsiflow_external_check --force --strict` reports `external_ready`.",
        "",
        "## Launch Metrics",
        "",
        "- [ ] `launch_metrics.json` and `launch_metrics.md` are attached to the launch review issue.",
        "- [ ] `launch_metrics.md` has the launch post URLs, GitHub traffic fields, demo traffic, weekly maintainer review notes, and day-0/day-1/day-3/day-7/day-14 review notes.",
        "- [ ] Launch replies link the demo PR playbook when users ask for proof that placeholder evidence fails.",
        "- [ ] Top referrers, popular GitHub content, stars, forks, clones, demo visits, and install/download signals are reviewed after launch.",
        "- [ ] Local/private validation is kept separate from public traction signals.",
        "- [ ] Repeated install, docs, or blocked-claim questions are converted into concrete follow-up issues before the next launch channel.",
        "",
        "## Current External Blockers",
        "",
    ]
    if isinstance(blockers, list) and blockers:
        for blocker in blockers:
            if isinstance(blocker, dict):
                lines.append(f"- `{blocker.get('check', '')}`: {blocker.get('message', '')}")
    else:
        lines.append("No external blockers were recorded.")
    lines.extend(["", "## Responsible-Use Review", "", "- [ ] Launch copy does not imply `claim_ready` is scientific proof.", "- [ ] Examples use non-sensitive fixtures or sanitized evidence.", ""])
    return "\n".join(lines)

def render_launch_proof_card(summary: dict[str, object]) -> str:
    proof_card = summary.get("proof_card", {}) if isinstance(summary.get("proof_card"), dict) else {}
    lines = [
        "# Falsiflow Launch Proof Card",
        "",
        f"- Project: `{proof_card.get('project', 'Falsiflow')}`",
        f"- Status: `{summary.get('status', '')}`",
        f"- External readiness: `{summary.get('external_status', '')}`",
        f"- Public demo URL: `{summary.get('public_demo_url', '')}`",
        "",
        "## Why It Matters",
        "",
        str(proof_card.get("one_liner", "")),
        "",
        "## Try Commands",
        "",
    ]
    for command in proof_card.get("try_commands", []):
        lines.append(f"- `{command}`")
    lines.extend(["", "## Verification Commands", ""])
    for command in proof_card.get("verification_commands", []):
        lines.append(f"- `{command}`")
    lines.extend(["", "## Boundary", "", str(proof_card.get("responsible_use", "")), ""])
    return "\n".join(lines)

def run_launch_kit(
    out_dir: Path,
    template: str,
    template_roots: list[Path] | None = None,
    repo_slug: str = "",
    public_demo_url: str = "",
    tag: str = "v0.1.1",
    force: bool = False,
    *,
    try_runner: TryRunner,
) -> dict[str, object]:
    prepare_output_directory(out_dir, "launch-kit output directory", force=force)
    out_dir.mkdir(parents=True, exist_ok=True)
    publish_kit = run_publish_kit(
        out_dir / "publish_kit",
        template,
        template_roots,
        repo_slug=repo_slug,
        public_demo_url=public_demo_url,
        tag=tag,
        force=True,
        try_runner=try_runner,
    )
    repo_url = str(publish_kit.get("repo_url", ""))
    demo_url = str(publish_kit.get("public_demo_url", ""))
    external_status = str(publish_kit.get("external_status", ""))
    external_blockers = publish_kit.get("external_blockers", [])
    outputs = {
        "summary": str(out_dir / "launch_summary.json"),
        "report": str(out_dir / "README.md"),
        "announcement": str(out_dir / "announcement.md"),
        "demo_script": str(out_dir / "demo_script.md"),
        "readme_proof_strip": str(out_dir / "readme_proof_strip.svg"),
        "social_preview": str(out_dir / "social_preview.svg"),
        "github_repo_profile": str(out_dir / "github_repo_profile.md"),
        "launch_posts": str(out_dir / "launch_posts.md"),
        "launch_metrics": str(out_dir / "launch_metrics.json"),
        "launch_metrics_report": str(out_dir / "launch_metrics.md"),
        "maintainer_checklist": str(out_dir / "maintainer_checklist.md"),
        "proof_card": str(out_dir / "proof_card.json"),
        "proof_card_report": str(out_dir / "proof_card.md"),
        "publish_kit": str(out_dir / "publish_kit" / "publish_handoff.json"),
        "public_release_evidence": str(out_dir / "publish_kit" / "public_release_evidence.md"),
        "release_rehearsal": str(out_dir / "publish_kit" / "release_rehearsal.md"),
    }
    proof_card = {
        "project": "Falsiflow",
        "tag": tag,
        "repo_url": repo_url,
        "public_demo_url": demo_url,
        "one_liner": "Evidence-gated R&D workflow engine that blocks high-risk claims until configuration, evidence, source provenance, bundles, and verification artifacts agree.",
        "try_commands": [
            "make install-local",
            "make start",
            "falsiflow quickstart --template biointerface_coatings --out my_falsiflow_project --strict",
            "falsiflow doctor --project-dir my_falsiflow_project --strict",
        ],
        "verification_commands": [
            "make test",
            "falsiflow adoption-check --out-dir data/falsiflow/adoption_check --force",
            "falsiflow release-check --out-dir data/falsiflow/release_check --force",
            "falsiflow external-check --out-dir falsiflow_external_check --force --strict",
        ],
        "external_status": external_status,
        "external_blockers": external_blockers,
        "responsible_use": "Falsiflow readiness is an audit of supplied evidence against configured gates, not proof of safety, efficacy, regulatory compliance, commercial readiness, or experimental truth.",
    }
    launch_metrics = launch_metrics_plan({
        "repo_url": repo_url,
        "public_demo_url": demo_url,
    })
    summary: dict[str, object] = {
        "status": "launch_kit_ready" if publish_kit.get("status") == "publish_kit_ready" else "launch_kit_blocked",
        "template": template,
        "tag": tag,
        "repo_url": repo_url,
        "public_demo_url": demo_url,
        "account_action_required": True,
        "external_status": external_status,
        "external_blockers": external_blockers,
        "publish_kit_status": publish_kit.get("status", ""),
        "demo_package_status": publish_kit.get("demo_package_status", ""),
        "proof_card": proof_card,
        "launch_metrics_status": launch_metrics["status"],
        "launch_metrics": launch_metrics,
        "release_rehearsal_status": publish_kit.get("release_rehearsal_status", ""),
        "github_topics": launch_topics(),
        "outputs": outputs,
        "next_commands": [
            f"falsiflow launch-kit --out-dir {out_dir} --force",
            f"FALSIFLOW_REPO_URL={repo_url} FALSIFLOW_PUBLIC_DEMO_URL={demo_url} FALSIFLOW_PYPI_PACKAGE_URL={default_pypi_package_url()} FALSIFLOW_EXPECTED_VERSION={default_expected_version()} FALSIFLOW_PIPX_VALIDATED=1 FALSIFLOW_PIPX_PUBLIC_VALIDATED=1 FALSIFLOW_WINDOWS_VALIDATED=1 falsiflow external-check --out-dir {out_dir / 'external_readiness_final'} --force --strict",
        ],
        "boundary": "Local launch materials are ready; external hosting, GitHub workflows, pipx, Windows, and PyPI evidence remain account-bound until external-check passes strictly.",
    }
    (out_dir / "proof_card.json").write_text(json.dumps(proof_card, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "proof_card.md").write_text(render_launch_proof_card(summary), encoding="utf-8")
    (out_dir / "announcement.md").write_text(render_launch_announcement(summary), encoding="utf-8")
    (out_dir / "demo_script.md").write_text(render_launch_demo_script(summary), encoding="utf-8")
    (out_dir / "readme_proof_strip.svg").write_text(render_readme_proof_strip_svg(summary), encoding="utf-8")
    (out_dir / "social_preview.svg").write_text(render_social_preview_svg(summary), encoding="utf-8")
    (out_dir / "github_repo_profile.md").write_text(render_github_repo_profile(summary), encoding="utf-8")
    (out_dir / "launch_posts.md").write_text(render_launch_posts(summary), encoding="utf-8")
    (out_dir / "launch_metrics.json").write_text(json.dumps(launch_metrics, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "launch_metrics.md").write_text(render_launch_metrics(summary), encoding="utf-8")
    (out_dir / "maintainer_checklist.md").write_text(render_launch_maintainer_checklist(summary), encoding="utf-8")
    (out_dir / "README.md").write_text(render_launch_readme(summary), encoding="utf-8")
    (out_dir / "launch_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary

def public_https_url(value: str) -> bool:
    stripped = value.strip()
    if not stripped.startswith("https://"):
        return False
    lowered = stripped.lower()
    return not any(token in lowered for token in ["example.com", "localhost", "127.0.0.1", "placeholder", "<", ">"])

def git_remote_url(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()

def truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip() in {"1", "true", "TRUE", "yes", "YES"}

def ready_external_status(value: object) -> bool:
    return str(value).strip().lower() in {"passed", "ready", "validated", "external_ready"}

def load_external_evidence(path: Path | None) -> tuple[dict[str, object], str]:
    if path is None:
        env_path = os.environ.get("FALSIFLOW_EXTERNAL_EVIDENCE", "").strip()
        path = Path(env_path) if env_path else None
    if path is None:
        return {}, ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"{path}: {exc}"
    if not isinstance(data, dict):
        return {}, f"{path}: evidence file must contain a JSON object"
    data["_evidence_path"] = str(path)
    return data, ""

def external_evidence_record(evidence: dict[str, object], check_id: str) -> dict[str, object]:
    checks = evidence.get("checks", {})
    if isinstance(checks, dict):
        record = checks.get(check_id)
        if isinstance(record, dict):
            return record
    record = evidence.get(check_id)
    return record if isinstance(record, dict) else {}

def first_public_evidence_url(record: dict[str, object]) -> str:
    for key in ["evidence_url", "workflow_url", "artifact_url", "report_url", "ci_url", "url"]:
        value = str(record.get(key, "")).strip()
        if public_https_url(value):
            return value
    return ""

def external_evidence_ready(evidence: dict[str, object], check_id: str, *, require_url: bool = True) -> tuple[bool, str]:
    record = external_evidence_record(evidence, check_id)
    if not record or not ready_external_status(record.get("status", "")):
        return False, ""
    value = first_public_evidence_url(record)
    if value:
        return True, value
    artifact_sha256 = str(record.get("artifact_sha256", "")).strip()
    artifact = str(record.get("artifact", "")).strip()
    if not require_url and artifact and artifact_sha256:
        return True, artifact
    return False, ""

def workflow_contains(path: Path, tokens: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return all(token in text for token in tokens)

def external_check_item(check_id: str, ok: bool, message: str, value: str = "", evidence: str = "") -> dict[str, object]:
    return {
        "check": check_id,
        "status": "passed" if ok else "blocked",
        "message": message,
        "value": value,
        "evidence": evidence,
    }

def render_external_check_report(summary: dict[str, object]) -> str:
    lines = [
        "# Falsiflow External Readiness",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Checks: {summary.get('ready_check_count', 0)}/{summary.get('check_count', 0)}",
        f"- Blockers: {summary.get('blocker_count', 0)}",
        "",
        "| Check | Status | Message | Evidence |",
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
                markdown_cell(check.get("evidence", "")),
            ])
            + " |"
        )
    blockers = summary.get("blockers", [])
    if isinstance(blockers, list) and blockers:
        lines.extend(["", "## Next Actions", ""])
        for blocker in blockers:
            if isinstance(blocker, dict):
                lines.append(f"- `{blocker.get('check', '')}`: {blocker.get('message', '')}")
    lines.append("")
    return "\n".join(lines)

def load_json_artifact(path: Path, label: str) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read {label} JSON from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{label} JSON must contain an object: {path}")
    return data

def external_readiness_check_record(readiness: dict[str, object], check_id: str) -> dict[str, object]:
    checks = readiness.get("checks", [])
    if not isinstance(checks, list):
        return {}
    for check in checks:
        if isinstance(check, dict) and check.get("check") == check_id:
            return check
    return {}

def external_evidence_run_url(evidence: dict[str, object]) -> str:
    checks = evidence.get("checks", {})
    if not isinstance(checks, dict):
        return ""
    for check_id in [
        "pypi_package_url",
        "public_package_claim_check",
        "mcp_public_package_selftest",
        "public_package_first_run",
        "pipx_public_package",
        "public_demo_url",
        "public_repo_url",
    ]:
        record = checks.get(check_id)
        if not isinstance(record, dict):
            continue
        for key in ["workflow_url", "evidence_url", "artifact_url", "report_url", "ci_url"]:
            value = str(record.get(key, "")).strip()
            if public_https_url(value) and "/actions/runs/" in value:
                return value
    for record in checks.values():
        if not isinstance(record, dict):
            continue
        value = first_public_evidence_url(record)
        if value:
            return value
    return ""

def render_release_proof_snippet(summary: dict[str, object]) -> str:
    return "\n".join([
        "## Falsiflow Public Release Proof",
        "",
        f"- External Evidence run: {summary.get('external_evidence_run_url', '')}",
        f"- PyPI version match: `pypi_version_match={summary.get('pypi_version_match_status', '')}` (`expected_version={summary.get('expected_version', '')}`, `published_version={summary.get('published_version', '')}`)",
        f"- Published-package claim gate: `public_package_claim_check={summary.get('public_package_claim_check_status', '')}`, `{summary.get('claim_check_status', '')}`, `{summary.get('bundle_verification_status', '')}`",
        f"- External readiness: `{summary.get('external_readiness_status', '')}`",
        "",
    ])

def run_release_proof(
    evidence_path: Path,
    readiness_path: Path,
    out: Path | None = None,
) -> dict[str, object]:
    evidence = load_json_artifact(evidence_path, "External Evidence")
    readiness = load_json_artifact(readiness_path, "external readiness")
    pypi_record = external_evidence_record(evidence, "pypi_package_url")
    claim_record = external_evidence_record(evidence, "public_package_claim_check")
    pypi_match_record = external_readiness_check_record(readiness, "pypi_version_match")
    expected_version = str(pypi_record.get("expected_version", "")).strip()
    published_version = str(pypi_record.get("published_version", "") or pypi_record.get("pypi_version", "")).strip()
    pypi_version_match_status = str(pypi_match_record.get("status", "")).strip()
    if not pypi_version_match_status and expected_version and published_version == expected_version and ready_external_status(pypi_record.get("status", "")):
        pypi_version_match_status = "passed"
    public_package_claim_check_status = str(claim_record.get("status", "")).strip()
    claim_check_status = str(claim_record.get("claim_check_status", "") or claim_record.get("claim_status", "")).strip()
    if not claim_check_status and ready_external_status(public_package_claim_check_status):
        claim_check_status = "claim_check_ready"
    bundle_verification_status = str(claim_record.get("bundle_verification_status", "") or claim_record.get("verification_status", "")).strip()
    if not bundle_verification_status and claim_check_status == "claim_check_ready":
        bundle_verification_status = "bundle_verified"
    summary: dict[str, object] = {
        "status": "external_proof_blocked",
        "external_evidence": str(evidence_path),
        "external_readiness": str(readiness_path),
        "external_evidence_run_url": external_evidence_run_url(evidence),
        "expected_version": expected_version,
        "published_version": published_version,
        "pypi_version_match_status": pypi_version_match_status,
        "public_package_claim_check_status": public_package_claim_check_status,
        "claim_check_status": claim_check_status,
        "bundle_verification_status": bundle_verification_status,
        "external_readiness_status": str(readiness.get("status", "")).strip(),
        "checks": [],
        "outputs": {},
    }
    checks = [
        external_check_item("external_evidence_run_url", bool(summary["external_evidence_run_url"]), "External Evidence run URL is present.", str(summary["external_evidence_run_url"])),
        external_check_item("pypi_version_match", summary["pypi_version_match_status"] == "passed", "PyPI expected_version matches published_version.", str(summary["published_version"]), f"expected={summary['expected_version']}"),
        external_check_item("public_package_claim_check", summary["public_package_claim_check_status"] == "passed", "Published-package claim-check evidence passed.", str(summary["public_package_claim_check_status"])),
        external_check_item("claim_check_ready", summary["claim_check_status"] == "claim_check_ready", "Published-package claim-check reached claim_check_ready.", str(summary["claim_check_status"])),
        external_check_item("bundle_verified", summary["bundle_verification_status"] == "bundle_verified", "Published-package claim-check bundle verification is recorded or implied by the passing strict claim-check artifact.", str(summary["bundle_verification_status"])),
        external_check_item("external_ready", summary["external_readiness_status"] == "external_ready", "external-check strict readiness passed.", str(summary["external_readiness_status"])),
    ]
    summary["checks"] = checks
    blockers = [check for check in checks if check.get("status") != "passed"]
    summary["blocker_count"] = len(blockers)
    summary["blockers"] = blockers
    if not blockers:
        summary["status"] = "external_proof_ready"
    snippet = render_release_proof_snippet(summary)
    summary["snippet"] = snippet
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(snippet, encoding="utf-8")
        summary["outputs"] = {"snippet": str(out)}
    return summary

def run_external_check(
    out_dir: Path,
    force: bool = False,
    root: Path | None = None,
    evidence_path: Path | None = None,
) -> dict[str, object]:
    prepare_output_directory(out_dir, "external-check output directory", force=force)
    out_dir.mkdir(parents=True, exist_ok=True)
    repo_root = root or ROOT
    external_evidence, evidence_error = load_external_evidence(evidence_path)
    evidence_loaded = bool(external_evidence)
    evidence_file = str(external_evidence.get("_evidence_path", ""))
    repo_record = external_evidence_record(external_evidence, "public_repo_url")
    demo_record = external_evidence_record(external_evidence, "public_demo_url")
    pypi_record = external_evidence_record(external_evidence, "pypi_package_url")
    repo_url = os.environ.get("FALSIFLOW_REPO_URL", "").strip() or str(repo_record.get("url", "")).strip() or git_remote_url(repo_root)
    public_demo_url = os.environ.get("FALSIFLOW_PUBLIC_DEMO_URL", "").strip() or str(demo_record.get("url", "")).strip()
    pypi_package_url = os.environ.get("FALSIFLOW_PYPI_PACKAGE_URL", "").strip() or str(pypi_record.get("url", "")).strip()
    pipx_path = shutil.which("pipx") or ""
    pipx_evidence_ready, pipx_evidence_value = external_evidence_ready(external_evidence, "pipx_smoke")
    pipx_validated = bool(pipx_path) or truthy_env("FALSIFLOW_PIPX_VALIDATED") or pipx_evidence_ready
    pipx_public_evidence_ready, pipx_public_evidence_value = external_evidence_ready(external_evidence, "pipx_public_package")
    pipx_public_validated = truthy_env("FALSIFLOW_PIPX_PUBLIC_VALIDATED") or pipx_public_evidence_ready
    first_run_evidence_ready, first_run_evidence_value = external_evidence_ready(external_evidence, "public_package_first_run")
    first_run_validated = truthy_env("FALSIFLOW_PUBLIC_PACKAGE_FIRST_RUN_VALIDATED") or first_run_evidence_ready
    claim_check_evidence_ready, claim_check_evidence_value = external_evidence_ready(external_evidence, "public_package_claim_check")
    claim_check_validated = truthy_env("FALSIFLOW_PUBLIC_PACKAGE_CLAIM_CHECK_VALIDATED") or claim_check_evidence_ready
    mcp_public_evidence_ready, mcp_public_evidence_value = external_evidence_ready(external_evidence, "mcp_public_package_selftest")
    mcp_public_validated = truthy_env("FALSIFLOW_MCP_PUBLIC_SELFTEST_VALIDATED") or mcp_public_evidence_ready
    powershell_path = shutil.which("pwsh") or shutil.which("powershell") or ""
    windows_evidence_ready, windows_evidence_value = external_evidence_ready(external_evidence, "windows_powershell")
    windows_validated = sys.platform.startswith("win") or truthy_env("FALSIFLOW_WINDOWS_VALIDATED") or windows_evidence_ready
    demo_evidence_ready, demo_evidence_value = external_evidence_ready(external_evidence, "public_demo_url")
    public_demo_ready = public_https_url(public_demo_url) and (not evidence_loaded or demo_evidence_ready or bool(os.environ.get("FALSIFLOW_PUBLIC_DEMO_URL", "").strip()))
    pypi_evidence_ready, pypi_evidence_value = external_evidence_ready(external_evidence, "pypi_package_url")
    pypi_package_ready = public_https_url(pypi_package_url) and (not evidence_loaded or pypi_evidence_ready or bool(os.environ.get("FALSIFLOW_PYPI_PACKAGE_URL", "").strip()))
    pypi_expected_version = str(pypi_record.get("expected_version", "")).strip() or os.environ.get("FALSIFLOW_EXPECTED_VERSION", "").strip()
    pypi_published_version = str(pypi_record.get("published_version", "") or pypi_record.get("pypi_version", "")).strip()
    pypi_version_matches = pypi_evidence_ready and bool(pypi_expected_version) and pypi_published_version == pypi_expected_version
    pages_workflow = repo_root / ".github" / "workflows" / "falsiflow-pages.yml"
    cross_platform_workflow = repo_root / ".github" / "workflows" / "falsiflow-cross-platform.yml"
    publish_workflow = repo_root / ".github" / "workflows" / "falsiflow-publish.yml"
    checks = []
    if evidence_path is not None or os.environ.get("FALSIFLOW_EXTERNAL_EVIDENCE", "").strip():
        checks.append(external_check_item("external_evidence_file", evidence_loaded and not evidence_error, "Structured external evidence JSON is readable.", evidence_file, evidence_file if evidence_loaded else evidence_error))
    checks.extend([
        external_check_item("git_available", shutil.which("git") is not None, "git is available for repository URL and release workflows.", shutil.which("git") or ""),
        external_check_item("public_repo_url", public_https_url(repo_url), "FALSIFLOW_REPO_URL or git remote is a public HTTPS repository URL.", repo_url),
        external_check_item("public_demo_url", public_demo_ready, "FALSIFLOW_PUBLIC_DEMO_URL or external evidence points to a hosted public static demo.", public_demo_url, demo_evidence_value),
        external_check_item("pypi_package_url", pypi_package_ready, "FALSIFLOW_PYPI_PACKAGE_URL or external evidence points to a public PyPI package page.", pypi_package_url, pypi_evidence_value),
    ])
    if evidence_loaded:
        checks.append(
            external_check_item(
                "pypi_version_match",
                pypi_version_matches,
                "Structured PyPI evidence records expected_version matching published_version from the PyPI JSON API.",
                pypi_published_version,
                f"expected={pypi_expected_version}",
            )
        )
    checks.extend([
        external_check_item("pipx_available", pipx_validated, "pipx is available, FALSIFLOW_PIPX_VALIDATED is set, or external evidence records a passing checkout-based pipx smoke test.", pipx_path or os.environ.get("FALSIFLOW_PIPX_VALIDATED", "") or pipx_evidence_value, pipx_evidence_value),
        external_check_item("pipx_public_package", pipx_public_validated, "FALSIFLOW_PIPX_PUBLIC_VALIDATED is set, or external evidence records a passing pipx smoke test from the published package.", os.environ.get("FALSIFLOW_PIPX_PUBLIC_VALIDATED", "") or pipx_public_evidence_value, pipx_public_evidence_value),
        external_check_item("public_package_first_run", first_run_validated, "FALSIFLOW_PUBLIC_PACKAGE_FIRST_RUN_VALIDATED is set, or external evidence records a passing published-package quickstart and doctor first-run path.", os.environ.get("FALSIFLOW_PUBLIC_PACKAGE_FIRST_RUN_VALIDATED", "") or first_run_evidence_value, first_run_evidence_value),
        external_check_item("public_package_claim_check", claim_check_validated, "FALSIFLOW_PUBLIC_PACKAGE_CLAIM_CHECK_VALIDATED is set, or external evidence records a passing published-package AI eval starter claim-check path.", os.environ.get("FALSIFLOW_PUBLIC_PACKAGE_CLAIM_CHECK_VALIDATED", "") or claim_check_evidence_value, claim_check_evidence_value),
        external_check_item("mcp_public_package_selftest", mcp_public_validated, "FALSIFLOW_MCP_PUBLIC_SELFTEST_VALIDATED is set, or external evidence records a passing published-package MCP selftest.", os.environ.get("FALSIFLOW_MCP_PUBLIC_SELFTEST_VALIDATED", "") or mcp_public_evidence_value, mcp_public_evidence_value),
        external_check_item("powershell_available", bool(powershell_path) or windows_validated, "PowerShell is available here, FALSIFLOW_WINDOWS_VALIDATED is set, or external evidence records a passing Windows smoke test.", powershell_path or os.environ.get("FALSIFLOW_WINDOWS_VALIDATED", "") or windows_evidence_value, windows_evidence_value),
        external_check_item("python_available", bool(sys.executable), "Python executable is available for local install and release checks.", sys.executable),
        external_check_item("demo_package_command", True, "`falsiflow demo-package` can prepare hostable static demo artifacts.", "falsiflow demo-package"),
        external_check_item("github_pages_workflow", workflow_contains(pages_workflow, ["workflow_dispatch", "push:", "branches: [main]", "docs/public_demo/**", "demo-package", "upload-pages-artifact", "deploy-pages", "pages: write", "enablement: true"]), "GitHub Pages workflow can enable Pages, auto-refresh, build, and deploy the static demo package.", str(pages_workflow)),
        external_check_item("cross_platform_workflow", workflow_contains(cross_platform_workflow, ["ubuntu-latest", "macos-latest", "windows-latest", "pipx", "install_local.ps1"]), "Cross-platform workflow covers Linux, macOS, Windows, pipx, and installers.", str(cross_platform_workflow)),
        external_check_item("pypi_publish_workflow", workflow_contains(publish_workflow, ["pypa/gh-action-pypi-publish", "twine check", "dist/*", "id-token: write"]), "PyPI publish workflow builds, checks, and can publish distributions with trusted publishing.", str(publish_workflow)),
    ])
    blockers = [check for check in checks if check.get("status") != "passed"]
    summary: dict[str, object] = {
        "status": "external_ready" if not blockers else "external_blocked",
        "check_count": len(checks),
        "ready_check_count": len(checks) - len(blockers),
        "blocker_count": len(blockers),
        "checks": checks,
        "blockers": blockers,
        "external_evidence_status": "loaded" if evidence_loaded else ("error" if evidence_error else "not_provided"),
        "external_evidence_path": evidence_file,
        "external_evidence_error": evidence_error,
        "outputs": {
            "summary": str(out_dir / "external_readiness.json"),
            "report": str(out_dir / "external_readiness.md"),
        },
        "next_commands": [
            "falsiflow external-evidence --out falsiflow_external_evidence.json --force",
            "falsiflow demo-package --out-dir falsiflow_public_demo --force",
            f"FALSIFLOW_REPO_URL=https://github.com/<owner>/<repo> FALSIFLOW_PUBLIC_DEMO_URL=https://<host>/<demo> FALSIFLOW_PYPI_PACKAGE_URL=https://pypi.org/project/falsiflow/ FALSIFLOW_EXPECTED_VERSION={default_expected_version()} falsiflow external-check --out-dir falsiflow_external_check --evidence falsiflow_external_evidence.json --force --strict",
        ],
    }
    (out_dir / "external_readiness.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "external_readiness.md").write_text(render_external_check_report(summary), encoding="utf-8")
    return summary
