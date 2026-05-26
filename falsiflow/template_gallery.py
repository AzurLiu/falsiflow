"""Template gallery summaries and reports for Falsiflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .bundle import markdown_cell
from .core import configured_evidence_keys, load_project
from .template_check import safe_template_child_path


class TemplateRecordsProvider(Protocol):
    def __call__(self, extra_roots: list[Path] | None = None, include_env: bool = True) -> list[dict[str, str]]: ...


class TemplateRootsProvider(Protocol):
    def __call__(self, extra_roots: list[Path] | None = None, include_env: bool = True) -> list[Path]: ...


def template_gallery_issue(severity: str, code: str, message: str, path: Path | str = "", template: str = "") -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "path": str(path),
        "template": template,
    }

def first_template_commands(template_id: str) -> list[str]:
    project_dir = f"{template_id}_project"
    return [
        f"falsiflow quickstart --template {template_id} --out {project_dir} --strict",
        f"falsiflow doctor --project-dir {project_dir} --strict",
        f"falsiflow init --template {template_id} --out {project_dir}",
        f"falsiflow claim-check --project-dir {project_dir} --strict",
    ]

def template_gallery_summary(
    extra_roots: list[Path] | None = None,
    include_env: bool = True,
    *,
    template_records_provider: TemplateRecordsProvider,
    template_roots_provider: TemplateRootsProvider,
) -> dict[str, object]:
    records = template_records_provider(extra_roots, include_env=include_env)
    issues: list[dict[str, str]] = []
    templates: list[dict[str, object]] = []
    roots = [str(root) for root in template_roots_provider(extra_roots, include_env=include_env)]

    if not records:
        issues.append(template_gallery_issue("error", "no_templates", "No starter templates were found."))

    for record in records:
        template_id = record["template"]
        template_dir = Path(record["path"])
        manifest_path = template_dir / "template.json"
        manifest: dict[str, object] = {}
        project: dict[str, object] = {}
        if manifest_path.exists():
            try:
                loaded_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if isinstance(loaded_manifest, dict):
                    manifest = loaded_manifest
                else:
                    issues.append(template_gallery_issue("error", "manifest_not_object", "Template manifest is not a JSON object.", manifest_path, template_id))
            except json.JSONDecodeError as exc:
                issues.append(template_gallery_issue("error", "manifest_invalid_json", f"Template manifest is invalid JSON: {exc}", manifest_path, template_id))
        else:
            issues.append(template_gallery_issue("error", "manifest_missing", "Template manifest is missing.", manifest_path, template_id))

        config_path = Path(record["project_config"])
        if config_path.exists():
            try:
                project = load_project(config_path)
            except Exception as exc:  # pragma: no cover - defensive gallery boundary.
                issues.append(template_gallery_issue("error", "project_load_failed", f"Project config could not be loaded: {exc}", config_path, template_id))
        else:
            issues.append(template_gallery_issue("error", "project_missing", "Project config is missing.", config_path, template_id))

        if record["status"] != "valid":
            issues.append(template_gallery_issue("error", "project_not_valid", f"Template project validation ended as {record['status']}.", config_path, template_id))

        demo_path = safe_template_child_path(template_dir, manifest.get("demo_evidence"), "evidence_pass_demo.csv")
        placeholder_path = safe_template_child_path(template_dir, manifest.get("placeholder_evidence"), "evidence_placeholder_demo.csv")
        if demo_path is None or not demo_path.exists():
            issues.append(template_gallery_issue("error", "demo_evidence_missing", "Positive demo evidence is missing or unsafe.", demo_path or "", template_id))
        if placeholder_path is None or not placeholder_path.exists():
            issues.append(template_gallery_issue("error", "placeholder_evidence_missing", "Placeholder demo evidence is missing or unsafe.", placeholder_path or "", template_id))

        source_dir = template_dir / "source_files"
        source_files = sorted(path.relative_to(template_dir).as_posix() for path in source_dir.rglob("*") if path.is_file()) if source_dir.exists() else []
        if not source_files:
            issues.append(template_gallery_issue("error", "source_files_missing", "Template has no source_files artifacts.", source_dir, template_id))

        claim = project.get("claim", {}) if isinstance(project, dict) else {}
        claim = claim if isinstance(claim, dict) else {}
        gates: list[dict[str, object]] = []
        project_gates = project.get("gates", []) if isinstance(project, dict) else []
        for gate in project_gates:
            if not isinstance(gate, dict):
                continue
            samples = gate.get("samples", [])
            if isinstance(samples, list) and samples:
                sample_count = len([sample for sample in samples if isinstance(sample, dict)])
            else:
                candidate_ids = gate.get("candidate_ids", [])
                sample_ids = gate.get("sample_ids", [])
                sample_count = len(candidate_ids if isinstance(candidate_ids, list) else []) * len(sample_ids if isinstance(sample_ids, list) else [])
            required_fields = [str(field) for field in gate.get("required_fields", []) if str(field)]
            derived_fields = [field for field in gate.get("derived_fields", []) if isinstance(field, dict)]
            acceptance_rules = [rule for rule in gate.get("acceptance_rules", []) if isinstance(rule, dict)]
            gates.append({
                "id": str(gate.get("id", "")),
                "title": str(gate.get("title", "")),
                "required_fields": required_fields,
                "required_field_count": len(required_fields),
                "sample_count": sample_count,
                "derived_field_count": len(derived_fields),
                "acceptance_rule_count": len(acceptance_rules),
            })

        templates.append({
            "template": template_id,
            "name": record["name"],
            "domain": record["domain"],
            "description": record["description"],
            "status": record["status"],
            "path": record["path"],
            "root": record["root"],
            "manifest": str(manifest_path) if manifest_path.exists() else "",
            "project_config": str(config_path),
            "project_id": record["project_id"],
            "claim_id": str(claim.get("id", "")),
            "claim_statement": str(claim.get("statement", "")),
            "gate_count": len(gates),
            "required_evidence_row_count": len(configured_evidence_keys(project)) if project else 0,
            "gates": gates,
            "demo_evidence": str(demo_path) if demo_path is not None else "",
            "placeholder_evidence": str(placeholder_path) if placeholder_path is not None else "",
            "demo_evidence_exists": bool(demo_path and demo_path.exists()),
            "placeholder_evidence_exists": bool(placeholder_path and placeholder_path.exists()),
            "source_file_count": len(source_files),
            "source_files": source_files,
            "first_commands": first_template_commands(template_id),
        })

    error_count = sum(1 for issue in issues if issue["severity"] == "error")
    domains = {str(template.get("domain", "")) for template in templates if str(template.get("domain", ""))}
    valid_template_count = sum(1 for template in templates if template.get("status") == "valid")
    return {
        "status": "template_gallery_ready" if error_count == 0 else "template_gallery_blocked",
        "template_count": len(templates),
        "valid_template_count": valid_template_count,
        "domain_count": len(domains),
        "non_neural_template_count": sum(1 for template in templates if template.get("template") != "neural_materials"),
        "template_roots": roots,
        "templates": templates,
        "issue_count": len(issues),
        "issues": issues,
    }

def render_template_gallery_report(summary: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Template Gallery",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Templates: {summary.get('valid_template_count', 0)}/{summary.get('template_count', 0)} valid",
        f"- Domains: {summary.get('domain_count', 0)}",
        f"- Non-neural templates: {summary.get('non_neural_template_count', 0)}",
        "",
        "## Templates",
        "",
        "| Template | Domain | Gates | Required rows | Claim | First command |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for template in summary.get("templates", []):
        if not isinstance(template, dict):
            continue
        first_commands = template.get("first_commands", [])
        first_command = first_commands[0] if isinstance(first_commands, list) and first_commands else ""
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(template.get("template", "")),
                markdown_cell(template.get("domain", "")),
                markdown_cell(template.get("gate_count", "")),
                markdown_cell(template.get("required_evidence_row_count", "")),
                markdown_cell(template.get("claim_statement", "")),
                markdown_cell(first_command),
            ])
            + " |"
        )

    for template in summary.get("templates", []):
        if not isinstance(template, dict):
            continue
        lines.extend([
            "",
            f"## {template.get('template', '')}",
            "",
            f"- Name: {template.get('name', '')}",
            f"- Domain: `{template.get('domain', '')}`",
            f"- Status: `{template.get('status', '')}`",
            f"- Description: {template.get('description', '')}",
            f"- Project config: `{template.get('project_config', '')}`",
            f"- Positive demo evidence: `{template.get('demo_evidence', '')}`",
            f"- Placeholder demo evidence: `{template.get('placeholder_evidence', '')}`",
            f"- Source files: {template.get('source_file_count', 0)}",
            "",
            "### First Commands",
            "",
            "```bash",
        ])
        for command in template.get("first_commands", []):
            lines.append(str(command))
        lines.extend([
            "```",
            "",
            "### Gates",
            "",
            "| Gate | Title | Fields | Samples | Derived | Rules |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ])
        for gate in template.get("gates", []):
            if not isinstance(gate, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(gate.get("id", "")),
                    markdown_cell(gate.get("title", "")),
                    markdown_cell(gate.get("required_field_count", "")),
                    markdown_cell(gate.get("sample_count", "")),
                    markdown_cell(gate.get("derived_field_count", "")),
                    markdown_cell(gate.get("acceptance_rule_count", "")),
                ])
                + " |"
            )

    issues = summary.get("issues", [])
    lines.extend(["", "## Issues", ""])
    if not issues:
        lines.append("No gallery issues found.")
    else:
        lines.extend(["| Severity | Code | Template | Path | Message |", "| --- | --- | --- | --- | --- |"])
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(issue.get("severity", "")),
                    markdown_cell(issue.get("code", "")),
                    markdown_cell(issue.get("template", "")),
                    markdown_cell(issue.get("path", "")),
                    markdown_cell(issue.get("message", "")),
                ])
                + " |"
            )
    return "\n".join(lines) + "\n"

def run_template_gallery(
    extra_roots: list[Path] | None = None,
    include_env: bool = True,
    out: Path | None = None,
    json_out: Path | None = None,
    *,
    template_records_provider: TemplateRecordsProvider,
    template_roots_provider: TemplateRootsProvider,
) -> dict[str, object]:
    summary = template_gallery_summary(
        extra_roots,
        include_env=include_env,
        template_records_provider=template_records_provider,
        template_roots_provider=template_roots_provider,
    )
    if out is not None:
        summary["markdown_path"] = str(out)
    if json_out is not None:
        summary["json_path"] = str(json_out)
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_template_gallery_report(summary), encoding="utf-8")
    if json_out is not None:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary
