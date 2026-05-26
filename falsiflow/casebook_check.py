"""Public casebook proof checks for Falsiflow starter templates."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import shlex
from typing import Protocol

from .bundle import markdown_cell


class TemplateRecordsProvider(Protocol):
    def __call__(self, extra_roots: list[Path] | None = None, include_env: bool = True) -> list[dict[str, str]]: ...


class TemplateCheckRunner(Protocol):
    def __call__(self, template_dir: Path, artifact_root: Path, force: bool = False) -> dict[str, object]: ...


def casebook_failure(stage: str, identifier: str, message: str) -> dict[str, str]:
    return {"stage": stage, "id": identifier, "message": message}


def casebook_template_record(template_check: dict[str, object], record: dict[str, str]) -> dict[str, object]:
    placeholder_claim_ready = bool(template_check.get("placeholder_claim_ready"))
    pass_ready = bool(template_check.get("pass_claim_ready"))
    source_ready = template_check.get("source_status") == "sources_ready"
    bundle_verified = template_check.get("verification_status") == "bundle_verified"
    return {
        "template": str(template_check.get("template_id") or record.get("template", "")),
        "domain": record.get("domain", ""),
        "project_id": record.get("project_id", ""),
        "template_dir": record.get("path", ""),
        "project_config": str(template_check.get("project_config_path") or record.get("project_config", "")),
        "demo_evidence": str(template_check.get("pass_evidence_path") or record.get("demo_evidence", "")),
        "placeholder_evidence": str(template_check.get("placeholder_evidence_path") or record.get("placeholder_evidence", "")),
        "claim_ready": pass_ready,
        "pass_audit_status": str(template_check.get("pass_audit_status", "")),
        "placeholder_blocks_claim": not placeholder_claim_ready,
        "placeholder_audit_status": str(template_check.get("placeholder_audit_status", "")),
        "source_status": str(template_check.get("source_status", "")),
        "bundle_status": str(template_check.get("bundle_status", "")),
        "verification_status": str(template_check.get("verification_status", "")),
        "artifact_dir": str(template_check.get("artifact_root", "")),
        "template_check": str(Path(str(template_check.get("artifact_root", ""))) / "template_check.json") if template_check.get("artifact_root") else "",
        "claim_summary": str(template_check.get("claim_summary_path", "")),
        "failure_count": int(template_check.get("failure_count", 0) or 0),
        "status": "case_ready" if pass_ready and not placeholder_claim_ready and source_ready and bundle_verified and int(template_check.get("failure_count", 0) or 0) == 0 else "case_blocked",
    }


def shell_quote(value: object) -> str:
    return shlex.quote(str(value))


def powershell_quote(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def casebook_replay_entries(templates: list[dict[str, object]]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for template in templates:
        template_id = str(template.get("template", "")).strip()
        if not template_id:
            continue
        template_dir = str(template.get("template_dir", "")).strip()
        project_config = str(template.get("project_config", "")).strip()
        demo_evidence = str(template.get("demo_evidence", "")).strip()
        placeholder_evidence = str(template.get("placeholder_evidence", "")).strip()
        entries.append({
            "template": template_id,
            "domain": str(template.get("domain", "")),
            "expected_positive_status": "claim_check_ready",
            "expected_placeholder_status": "claim_check_blocked",
            "template_check_command": " ".join([
                "falsiflow",
                "template-check",
                shell_quote(template_dir),
                "--out-dir",
                f'"$OUT_DIR/templates/{template_id}"',
                "--force",
            ]),
            "positive_claim_command": " ".join([
                "falsiflow",
                "claim-check",
                "--config",
                shell_quote(project_config),
                "--evidence",
                shell_quote(demo_evidence),
                "--out-dir",
                f'"$OUT_DIR/claims/{template_id}/positive"',
                "--strict",
                "--force",
            ]),
            "placeholder_claim_command": " ".join([
                "falsiflow",
                "claim-check",
                "--config",
                shell_quote(project_config),
                "--evidence",
                shell_quote(placeholder_evidence),
                "--out-dir",
                f'"$OUT_DIR/claims/{template_id}/placeholder"',
                "--force",
            ]),
            "inspect_artifacts": [
                f"$OUT_DIR/templates/{template_id}/template_check.md",
                f"$OUT_DIR/claims/{template_id}/positive/claim_check.md",
                f"$OUT_DIR/claims/{template_id}/placeholder/claim_check.md",
            ],
        })
    return entries


def render_casebook_reviewer_replay_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Casebook Reviewer Replay",
        "",
        "Run these scripts to reproduce the public casebook positive and blocked-path checks from a local checkout or installed package.",
        "The scripts assert that positive demos finish as `claim_check_ready` and placeholder demos finish as `claim_check_blocked`.",
        "",
        "```bash",
        f"bash {summary.get('outputs', {}).get('reviewer_replay_shell', 'casebook_reviewer_replay.sh')}",
        "```",
        "",
        "```powershell",
        f"pwsh -File {summary.get('outputs', {}).get('reviewer_replay_powershell', 'casebook_reviewer_replay.ps1')}",
        "```",
        "",
        "## Replay Matrix",
        "",
        "| Template | Positive expectation | Placeholder expectation | Inspect |",
        "| --- | --- | --- | --- |",
    ]
    for entry in summary.get("reviewer_replay", []):
        if not isinstance(entry, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(entry.get("template", "")),
                f"`{markdown_cell(entry.get('expected_positive_status', ''))}`",
                f"`{markdown_cell(entry.get('expected_placeholder_status', ''))}`",
                "<br>".join(f"`{markdown_cell(path)}`" for path in entry.get("inspect_artifacts", []) if isinstance(path, str)),
            ])
            + " |"
        )
    lines.extend(["", "## Commands", ""])
    for entry in summary.get("reviewer_replay", []):
        if not isinstance(entry, dict):
            continue
        lines.extend([
            f"### {entry.get('template', '')}",
            "",
            "```bash",
            str(entry.get("template_check_command", "")),
            str(entry.get("positive_claim_command", "")),
            str(entry.get("placeholder_claim_command", "")),
            "```",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def render_casebook_reviewer_replay_shell(summary: dict[str, object]) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        'OUT_DIR="${1:-data/falsiflow/casebook_replay}"',
        'mkdir -p "$OUT_DIR"',
        "assert_status() {",
        '  python3 - "$1" "$2" <<\'PY\'',
        "import json",
        "import sys",
        "path, expected = sys.argv[1:3]",
        "actual = json.load(open(path, encoding='utf-8')).get('status')",
        "if actual != expected:",
        "    raise SystemExit(f'{path}: expected {expected}, got {actual}')",
        "PY",
        "}",
        'echo "Writing casebook replay artifacts to $OUT_DIR"',
        'falsiflow template-gallery --out "$OUT_DIR/template_gallery.md" --json-out "$OUT_DIR/template_gallery.json"',
        'falsiflow casebook-check --out-dir "$OUT_DIR/casebook_check" --force',
    ]
    for entry in summary.get("reviewer_replay", []):
        if not isinstance(entry, dict):
            continue
        lines.extend([
            "",
            f"echo \"Replaying {entry.get('template', '')}\"",
            str(entry.get("template_check_command", "")),
            str(entry.get("positive_claim_command", "")),
            f'assert_status "$OUT_DIR/claims/{entry.get("template", "")}/positive/claim_check.json" claim_check_ready',
            "# Placeholder claim-check intentionally runs without --strict so the replay can assert the blocked status.",
            str(entry.get("placeholder_claim_command", "")),
            f'assert_status "$OUT_DIR/claims/{entry.get("template", "")}/placeholder/claim_check.json" claim_check_blocked',
        ])
    lines.append('echo "Casebook replay complete."')
    return "\n".join(lines) + "\n"


def render_casebook_reviewer_replay_powershell(summary: dict[str, object]) -> str:
    lines = [
        "$ErrorActionPreference = 'Stop'",
        "$OutDir = if ($args.Count -gt 0) { $args[0] } else { 'data/falsiflow/casebook_replay' }",
        "New-Item -ItemType Directory -Force -Path $OutDir | Out-Null",
        "function Assert-Status {",
        "  param([string]$Path, [string]$Expected)",
        "  $Actual = (Get-Content -Raw -Path $Path | ConvertFrom-Json).status",
        "  if ($Actual -ne $Expected) { throw \"$Path expected $Expected, got $Actual\" }",
        "}",
        "Write-Host \"Writing casebook replay artifacts to $OutDir\"",
        "falsiflow template-gallery --out (Join-Path $OutDir 'template_gallery.md') --json-out (Join-Path $OutDir 'template_gallery.json')",
        "falsiflow casebook-check --out-dir (Join-Path $OutDir 'casebook_check') --force",
    ]
    for entry in summary.get("reviewer_replay", []):
        if not isinstance(entry, dict):
            continue
        template_id = str(entry.get("template", ""))
        template_dir = next((str(template.get("template_dir", "")) for template in summary.get("templates", []) if isinstance(template, dict) and template.get("template") == template_id), "")
        project_config = next((str(template.get("project_config", "")) for template in summary.get("templates", []) if isinstance(template, dict) and template.get("template") == template_id), "")
        demo_evidence = next((str(template.get("demo_evidence", "")) for template in summary.get("templates", []) if isinstance(template, dict) and template.get("template") == template_id), "")
        placeholder_evidence = next((str(template.get("placeholder_evidence", "")) for template in summary.get("templates", []) if isinstance(template, dict) and template.get("template") == template_id), "")
        lines.extend([
            "",
            f"Write-Host {powershell_quote('Replaying ' + template_id)}",
            f"falsiflow template-check {powershell_quote(template_dir)} --out-dir (Join-Path $OutDir {powershell_quote('templates/' + template_id)}) --force",
            f"falsiflow claim-check --config {powershell_quote(project_config)} --evidence {powershell_quote(demo_evidence)} --out-dir (Join-Path $OutDir {powershell_quote('claims/' + template_id + '/positive')}) --strict --force",
            f"Assert-Status (Join-Path $OutDir {powershell_quote('claims/' + template_id + '/positive/claim_check.json')}) 'claim_check_ready'",
            "# Placeholder claim-check intentionally runs without --strict so the replay can assert the blocked status.",
            f"falsiflow claim-check --config {powershell_quote(project_config)} --evidence {powershell_quote(placeholder_evidence)} --out-dir (Join-Path $OutDir {powershell_quote('claims/' + template_id + '/placeholder')}) --force",
            f"Assert-Status (Join-Path $OutDir {powershell_quote('claims/' + template_id + '/placeholder/claim_check.json')}) 'claim_check_blocked'",
        ])
    lines.append("Write-Host 'Casebook replay complete.'")
    return "\n".join(lines) + "\n"


def render_casebook_check_report(summary: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Casebook Check",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Templates: {summary.get('ready_template_count', 0)}/{summary.get('template_count', 0)} ready",
        f"- Domains: {summary.get('domain_count', 0)}",
        f"- Positive demo proofs: {summary.get('positive_demo_ready_count', 0)}",
        f"- Blocked-path proofs: {summary.get('blocked_path_count', 0)}",
        f"- Source-ready proofs: {summary.get('source_ready_count', 0)}",
        f"- Bundle-verified proofs: {summary.get('bundle_verified_count', 0)}",
        f"- Failures: {summary.get('failure_count', 0)}",
        "",
        "## Positive Demo Proof",
        "",
        "| Template | Domain | Claim Ready | Sources | Bundle | Verification |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for template in summary.get("templates", []):
        if not isinstance(template, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(template.get("template", "")),
                markdown_cell(template.get("domain", "")),
                markdown_cell(str(bool(template.get("claim_ready"))).lower()),
                markdown_cell(template.get("source_status", "")),
                markdown_cell(template.get("bundle_status", "")),
                markdown_cell(template.get("verification_status", "")),
            ])
            + " |"
        )

    lines.extend([
        "",
        "## Blocked-path Proof",
        "",
        "| Template | Placeholder Blocks Claim | Placeholder Audit | Template Check |",
        "| --- | --- | --- | --- |",
    ])
    for template in summary.get("templates", []):
        if not isinstance(template, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(template.get("template", "")),
                markdown_cell(str(bool(template.get("placeholder_blocks_claim"))).lower()),
                markdown_cell(template.get("placeholder_audit_status", "")),
                markdown_cell(template.get("template_check", "")),
            ])
            + " |"
        )

    lines.extend(["", "## Reviewer Commands", "", "```bash"])
    for command in summary.get("reviewer_commands", []):
        lines.append(str(command))
    lines.extend(["```", "", "## Reviewer Replay", ""])
    outputs = summary.get("outputs", {}) if isinstance(summary.get("outputs"), dict) else {}
    lines.extend([
        "| Artifact | Path |",
        "| --- | --- |",
        f"| Markdown guide | `{markdown_cell(outputs.get('reviewer_replay_markdown', ''))}` |",
        f"| Bash script | `{markdown_cell(outputs.get('reviewer_replay_shell', ''))}` |",
        f"| PowerShell script | `{markdown_cell(outputs.get('reviewer_replay_powershell', ''))}` |",
        "",
        "## Failures",
        "",
    ])
    failures = summary.get("failures", [])
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


def run_casebook_check(
    artifact_root: Path,
    extra_roots: list[Path] | None = None,
    force: bool = False,
    include_env: bool = True,
    *,
    template_records_provider: TemplateRecordsProvider,
    template_check_runner: TemplateCheckRunner,
) -> dict[str, object]:
    if artifact_root.exists() and any(artifact_root.iterdir()):
        if not force:
            raise SystemExit(f"Refusing to write casebook check into non-empty directory without --force: {artifact_root}")
        shutil.rmtree(artifact_root)
    artifact_root.mkdir(parents=True, exist_ok=True)

    failures: list[dict[str, str]] = []
    try:
        records = template_records_provider(extra_roots, include_env=include_env)
    except Exception as exc:  # pragma: no cover - defensive public-check boundary.
        records = []
        failures.append(casebook_failure("template_discovery", "templates", str(exc)))

    templates: list[dict[str, object]] = []
    for record in records:
        template_id = record.get("template", "")
        template_dir = Path(record.get("path", ""))
        try:
            template_check = template_check_runner(template_dir, artifact_root / "templates" / template_id, force=True)
            case = casebook_template_record(template_check, record)
            templates.append(case)
            if case["status"] != "case_ready":
                failures.append(casebook_failure("casebook", template_id, "Positive demo, blocked-path, source, bundle, or verification proof is not ready."))
            for failed in template_check.get("failures", []):
                if isinstance(failed, dict):
                    failures.append(casebook_failure("template_check", f"{template_id}:{failed.get('check', '')}", str(failed.get("message", ""))))
        except Exception as exc:  # pragma: no cover - defensive public-check boundary.
            templates.append({
                "template": template_id,
                "domain": record.get("domain", ""),
                "project_id": record.get("project_id", ""),
                "status": "case_blocked",
                "claim_ready": False,
                "placeholder_blocks_claim": False,
                "source_status": "not_run",
                "bundle_status": "not_run",
                "verification_status": "not_run",
                "artifact_dir": str(artifact_root / "templates" / template_id),
                "failure_count": 1,
            })
            failures.append(casebook_failure("casebook", template_id, str(exc)))

    domains = {str(template.get("domain", "")) for template in templates if str(template.get("domain", ""))}
    ready_template_count = sum(1 for template in templates if template.get("status") == "case_ready")
    positive_demo_ready_count = sum(1 for template in templates if template.get("claim_ready") is True)
    blocked_path_count = sum(1 for template in templates if template.get("placeholder_blocks_claim") is True)
    source_ready_count = sum(1 for template in templates if template.get("source_status") == "sources_ready")
    bundle_verified_count = sum(1 for template in templates if template.get("verification_status") == "bundle_verified")
    if not templates:
        failures.append(casebook_failure("casebook", "templates", "No starter templates were checked."))

    summary: dict[str, object] = {
        "status": "casebook_check_ready" if templates and not failures else "casebook_check_blocked",
        "artifact_root": str(artifact_root),
        "template_count": len(templates),
        "ready_template_count": ready_template_count,
        "domain_count": len(domains),
        "non_neural_template_count": sum(1 for template in templates if template.get("template") != "neural_materials"),
        "positive_demo_ready_count": positive_demo_ready_count,
        "blocked_path_count": blocked_path_count,
        "source_ready_count": source_ready_count,
        "bundle_verified_count": bundle_verified_count,
        "templates": templates,
        "failure_count": len(failures),
        "failures": failures,
        "outputs": {
            "summary": str(artifact_root / "casebook_check.json"),
            "report": str(artifact_root / "casebook_check.md"),
            "reviewer_replay_markdown": str(artifact_root / "casebook_reviewer_replay.md"),
            "reviewer_replay_shell": str(artifact_root / "casebook_reviewer_replay.sh"),
            "reviewer_replay_powershell": str(artifact_root / "casebook_reviewer_replay.ps1"),
        },
        "reviewer_commands": [
            f"falsiflow casebook-check --out-dir {artifact_root} --force",
            "falsiflow template-gallery --out data/falsiflow/template_gallery.md --json-out data/falsiflow/template_gallery.json",
            f"bash {artifact_root / 'casebook_reviewer_replay.sh'}",
            f"pwsh -File {artifact_root / 'casebook_reviewer_replay.ps1'}",
        ],
    }
    summary["reviewer_replay"] = casebook_replay_entries(templates)
    (artifact_root / "casebook_check.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    replay_shell = artifact_root / "casebook_reviewer_replay.sh"
    replay_shell.write_text(render_casebook_reviewer_replay_shell(summary), encoding="utf-8")
    replay_shell.chmod(0o755)
    (artifact_root / "casebook_reviewer_replay.ps1").write_text(render_casebook_reviewer_replay_powershell(summary), encoding="utf-8")
    (artifact_root / "casebook_reviewer_replay.md").write_text(render_casebook_reviewer_replay_markdown(summary), encoding="utf-8")
    (artifact_root / "casebook_check.md").write_text(render_casebook_check_report(summary), encoding="utf-8")
    return summary
