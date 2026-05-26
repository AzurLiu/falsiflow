"""Starter template discovery and path resolution helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .core import load_project, validate_project_config
from .template_registry import safe_template_identifier


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates"
REPO_TEMPLATE_ROOT = ROOT / "examples" / "falsiflow"
TEMPLATE_ROOTS = [PACKAGE_TEMPLATE_ROOT, REPO_TEMPLATE_ROOT]


def env_template_roots() -> list[Path]:
    raw = os.environ.get("FALSIFLOW_TEMPLATE_ROOTS", "")
    return [Path(part).expanduser() for part in raw.split(os.pathsep) if part.strip()]


def all_template_roots(extra_roots: list[Path] | None = None, include_env: bool = True) -> list[Path]:
    candidates = [*(extra_roots or [])]
    if include_env:
        candidates.extend(env_template_roots())
    candidates.extend(TEMPLATE_ROOTS)
    roots: list[Path] = []
    seen: set[Path] = set()
    for root in candidates:
        resolved = root.expanduser().resolve()
        if resolved not in seen:
            roots.append(root.expanduser())
            seen.add(resolved)
    return roots


def template_root(extra_roots: list[Path] | None = None, include_env: bool = True) -> Path:
    for root in all_template_roots(extra_roots, include_env=include_env):
        if root.exists():
            return root
    return PACKAGE_TEMPLATE_ROOT


def template_path(template: str, extra_roots: list[Path] | None = None, include_env: bool = True) -> Path | None:
    if not safe_template_identifier(template):
        return None
    for root in all_template_roots(extra_roots, include_env=include_env):
        path = root / template
        if path.exists():
            return path
    return None


def template_records(extra_roots: list[Path] | None = None, include_env: bool = True) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    seen_templates: set[str] = set()
    for root in all_template_roots(extra_roots, include_env=include_env):
        if not root.exists():
            continue
        for path in sorted(item for item in root.iterdir() if item.is_dir() and not item.name.startswith(".")):
            manifest_path = path / "template.json"
            manifest: dict[str, str] = {}
            manifest_status = "missing"
            if manifest_path.exists():
                try:
                    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        manifest = loaded
                        manifest_status = "present"
                    else:
                        manifest_status = "invalid_object"
                except json.JSONDecodeError:
                    manifest_status = "invalid_json"
            template_id = str(manifest.get("id") or path.name)
            if template_id in seen_templates:
                continue
            seen_templates.add(template_id)
            config = path / manifest.get("project_config", "project.json")
            status = "missing_project_json"
            project_id = ""
            if manifest_status != "present":
                status = f"template_manifest_{manifest_status}"
            elif config.exists():
                project = load_project(config)
                validation = validate_project_config(project)
                status = validation["status"]
                project_id = str(project.get("project", {}).get("id", ""))
            records.append({
                "template": template_id,
                "name": str(manifest.get("name") or path.name),
                "domain": str(manifest.get("domain") or ""),
                "description": str(manifest.get("description") or ""),
                "path": str(path),
                "root": str(root),
                "manifest": str(manifest_path) if manifest_path.exists() else "",
                "project_config": str(config),
                "project_id": project_id,
                "status": status,
            })
    return records
