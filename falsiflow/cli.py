"""Command-line interface for Falsiflow."""

from __future__ import annotations

import argparse
import base64
import contextlib
import csv
from datetime import datetime, timezone
import functools
import hashlib
import hmac
from html import escape
import http.server
import io
from importlib import metadata as importlib_metadata
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import urllib.parse
import urllib.request
import webbrowser
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback.
    tomllib = None

from .adapters import write_limina_conversion, write_wide_lab_conversion
from .core import (
    EVIDENCE_COLUMNS,
    OPERATORS,
    allowed_roots,
    configured_evidence_keys,
    discover_claim_summary_paths,
    evidence_rows_by_key,
    falsiflow_schema,
    load_project,
    read_csv_rows_with_diagnostics,
    resolve_source_file,
    rule_applies_to_sample,
    source_file_base_dir,
    validate_project_config,
    write_portfolio_artifacts,
    write_render_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates"
REPO_TEMPLATE_ROOT = ROOT / "examples" / "falsiflow"
TEMPLATE_ROOTS = [PACKAGE_TEMPLATE_ROOT, REPO_TEMPLATE_ROOT]
SCHEMA_KINDS = [
    "project",
    "evidence-row",
    "evidence-record",
    "candidate-recipe",
    "discovery-summary",
    "claim-summary",
    "audit-review",
    "portfolio-summary",
    "import-coverage",
    "source-manifest",
    "bundle-manifest",
    "bundle-verification",
    "claim-check",
    "quickstart-summary",
    "doctor-summary",
    "demo-summary",
    "template-check",
    "template-pack-manifest",
    "template-pack-verification",
    "template-install",
    "template-registry",
    "template-lock",
    "template-attestation",
    "template-attestation-verification",
    "template-policy",
    "template-policy-verification",
    "template-release",
    "template-release-verification",
    "template-gallery",
    "adoption-check",
    "release-check",
    "all",
]


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


def safe_template_identifier(identifier: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", identifier)) and identifier not in {".", ".."}


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


def cmd_init(args: argparse.Namespace) -> int:
    source = template_path(args.template, args.template_root)
    if source is None:
        raise SystemExit(f"Unknown template `{args.template}`. Run `falsiflow templates` to list available templates.")
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty directory: {args.out}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, args.out, dirs_exist_ok=True)
    print(f"Initialized Falsiflow project from `{args.template}` at {args.out}")
    return 0


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


def remove_generated_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def title_from_id(identifier: str) -> str:
    return " ".join(part for part in identifier.replace("-", "_").split("_") if part).title()


def parse_scaffold_gate(raw: str) -> dict[str, object]:
    if ":" not in raw:
        raise SystemExit("Invalid --gate value. Use `gate_id:field_a,field_b`.")
    gate_id, fields_raw = raw.split(":", 1)
    gate_id = gate_id.strip()
    fields = [field.strip() for field in fields_raw.split(",") if field.strip()]
    if not gate_id or not fields:
        raise SystemExit("Invalid --gate value. Use `gate_id:field_a,field_b` with at least one field.")
    return {"id": gate_id, "required_fields": fields}


def parse_scaffold_gate_titles(raw_titles: list[str], gate_ids: set[str]) -> dict[str, str]:
    titles: dict[str, str] = {}
    for raw in raw_titles:
        if "=" not in raw:
            raise SystemExit("Invalid --gate-title value. Use `gate_id=Human title`.")
        gate_id, title = raw.split("=", 1)
        gate_id = gate_id.strip()
        title = title.strip()
        if not gate_id or not title:
            raise SystemExit("Invalid --gate-title value. Use `gate_id=Human title`.")
        if gate_id not in gate_ids:
            raise SystemExit(f"--gate-title references unknown gate `{gate_id}`.")
        titles[gate_id] = title
    return titles


def parse_rule_value(raw: str) -> object:
    normalized = raw.strip()
    lowered = normalized.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if any(marker in normalized for marker in [".", "e", "E"]):
            return float(normalized)
        return int(normalized)
    except ValueError:
        return normalized


def parse_scaffold_rules(raw_rules: list[str], gate_fields: dict[str, set[str]]) -> dict[str, list[dict[str, object]]]:
    rules: dict[str, list[dict[str, object]]] = {}
    for raw in raw_rules:
        parts = [part.strip() for part in raw.split(":", 4)]
        if len(parts) < 4 or not all(parts[:4]):
            raise SystemExit("Invalid --rule value. Use `gate_id:field:operator:value[:reason]`.")
        gate_id, field, operator_text, value_text = parts[:4]
        reason = parts[4] if len(parts) == 5 else ""
        if gate_id not in gate_fields:
            raise SystemExit(f"--rule references unknown gate `{gate_id}`.")
        if field not in gate_fields[gate_id]:
            raise SystemExit(f"--rule references field `{field}` that is not required by gate `{gate_id}`.")
        if operator_text not in OPERATORS:
            raise SystemExit(f"--rule uses unknown operator `{operator_text}`.")
        rule: dict[str, object] = {
            "field": field,
            "operator": operator_text,
            "value": parse_rule_value(value_text),
        }
        if reason:
            rule["reason"] = reason
        rules.setdefault(gate_id, []).append(rule)
    return rules


def parse_scaffold_samples(
    raw_samples: list[str],
    gate_ids: set[str],
    default_candidate_id: str,
    default_sample_id: str,
) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]]]:
    global_samples: list[dict[str, str]] = []
    gate_samples: dict[str, list[dict[str, str]]] = {}
    for raw in raw_samples:
        parts = [part.strip() for part in raw.split(":")]
        if len(parts) == 2 and all(parts):
            global_samples.append({"candidate_id": parts[0], "sample_id": parts[1]})
            continue
        if len(parts) == 3 and all(parts):
            gate_id, candidate_id, sample_id = parts
            if gate_id not in gate_ids:
                raise SystemExit(f"--sample references unknown gate `{gate_id}`.")
            gate_samples.setdefault(gate_id, []).append({"candidate_id": candidate_id, "sample_id": sample_id})
            continue
        raise SystemExit("Invalid --sample value. Use `candidate_id:sample_id` or `gate_id:candidate_id:sample_id`.")

    if not global_samples:
        global_samples = [{"candidate_id": default_candidate_id, "sample_id": default_sample_id}]
    return global_samples, gate_samples


def dedupe_samples(samples: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for sample in samples:
        key = (sample["candidate_id"], sample["sample_id"])
        if key not in seen:
            seen.add(key)
            deduped.append(sample)
    return deduped


def scaffold_evidence_rows(project: dict[str, object]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for gate in project.get("gates", []):
        if not isinstance(gate, dict):
            continue
        for sample in gate.get("samples", []):
            if not isinstance(sample, dict):
                continue
            for field in gate.get("required_fields", []):
                row = {column: "" for column in EVIDENCE_COLUMNS}
                row.update({
                    "gate_id": str(gate.get("id", "")),
                    "candidate_id": str(sample.get("candidate_id", "")),
                    "sample_id": str(sample.get("sample_id", "")),
                    "field": str(field),
                    "value": "record_actual",
                    "notes": "Replace this placeholder with measured evidence before audit.",
                })
                rows.append(row)
    return rows


def rule_candidate_values(rule: dict[str, object]) -> list[object]:
    expected = rule.get("value", "")
    operator_text = str(rule.get("operator", ""))
    if isinstance(expected, bool):
        if operator_text == "==":
            return [expected]
        if operator_text == "!=":
            return [not expected]
        return [expected, not expected]
    if isinstance(expected, int | float):
        value = float(expected)
        if operator_text == ">":
            return [value + 1, value + 0.1]
        if operator_text == ">=":
            return [value, value + 1]
        if operator_text == "<":
            return [value - 1, value - 0.1]
        if operator_text == "<=":
            return [value, value - 1]
        if operator_text == "==":
            return [expected]
        if operator_text == "!=":
            return [value + 1, value - 1]
    text = str(expected)
    if operator_text == "==":
        return [text]
    if operator_text == "!=":
        return [f"{text}_pass", "pass_value"]
    return [text, f"{text}z", "pass_value", "1"]


def candidate_passes_rules(value: object, rules: list[dict[str, object]]) -> bool:
    actual = parse_rule_value(str(value))
    for rule in rules:
        operator_text = str(rule.get("operator", ""))
        op = OPERATORS.get(operator_text)
        if op is None:
            return False
        expected = rule.get("value")
        try:
            passed = op(actual, expected)
        except TypeError:
            passed = op(str(actual), str(expected))
        if not passed:
            return False
    return True


def serialize_demo_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def passing_demo_value(rules: list[dict[str, object]]) -> str:
    candidates: list[object] = []
    for rule in rules:
        candidates.extend(rule_candidate_values(rule))
    candidates.extend([1, 10, 100, 0, -1, True, False, "pass_value"])
    seen: set[str] = set()
    for candidate in candidates:
        key = repr(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate_passes_rules(candidate, rules):
            return serialize_demo_value(candidate)
    return "pass_value"


def scaffold_passing_evidence_rows(project: dict[str, object], source_file: str = "source_files/demo_raw_export.csv") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for gate in project.get("gates", []):
        if not isinstance(gate, dict):
            continue
        gate_id = str(gate.get("id", ""))
        rules = [rule for rule in gate.get("acceptance_rules", []) if isinstance(rule, dict)]
        for sample in gate.get("samples", []):
            if not isinstance(sample, dict):
                continue
            sample_key = (str(sample.get("candidate_id", "")), str(sample.get("sample_id", "")))
            for field in gate.get("required_fields", []):
                field_rules = [
                    rule
                    for rule in rules
                    if str(rule.get("field", "")) == str(field) and rule_applies_to_sample(rule, sample_key)
                ]
                row = {column: "" for column in EVIDENCE_COLUMNS}
                row.update({
                    "gate_id": gate_id,
                    "candidate_id": sample_key[0],
                    "sample_id": sample_key[1],
                    "field": str(field),
                    "value": passing_demo_value(field_rules),
                    "source_file": source_file,
                    "measured_at": "2026-05-25T09:00:00Z",
                    "operator_or_agent": "falsiflow_template_scaffold",
                    "instrument_id": "demo_instrument",
                    "notes": "Synthetic demo evidence for validating template mechanics; replace before real use.",
                })
                rows.append(row)
    return rows


def write_evidence_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVIDENCE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def scaffold_project_readme(project: dict[str, object]) -> str:
    project_id = str(project.get("project", {}).get("id", "project"))
    project_name = str(project.get("project", {}).get("name", project_id))
    return f"""# {project_name}

Generated by `falsiflow scaffold`.

## Workflow

```bash
falsiflow validate --config project.json --strict
falsiflow render --config project.json --out-dir blank_audit
falsiflow audit --config project.json --evidence evidence_template.csv --out-dir audit --strict
```

Fill `evidence_template.csv` with measured values, source files under
`source_files/`, timestamps, operators, and instruments before using audit
results as a readiness claim.

Project id: `{project_id}`
"""


def scaffold_source_readme() -> str:
    return """# Source Files

Put raw exports, instrument files, vendor records, or lab notebooks here.
Evidence rows should reference these files through the `source_file` column.
Falsiflow treats missing source files as blockers when source-file policy is
enabled.
"""


def build_scaffold_project(args: argparse.Namespace) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, str]]]:
    gate_specs = [parse_scaffold_gate(raw) for raw in args.gate]
    gate_ids = [str(gate["id"]) for gate in gate_specs]
    duplicate_gate_ids = sorted({gate_id for gate_id in gate_ids if gate_ids.count(gate_id) > 1})
    if duplicate_gate_ids:
        raise SystemExit(f"Duplicate scaffold gate id(s): {', '.join(duplicate_gate_ids)}")

    gate_id_set = set(gate_ids)
    gate_fields = {str(gate["id"]): set(str(field) for field in gate["required_fields"]) for gate in gate_specs}
    gate_titles = parse_scaffold_gate_titles(args.gate_title, gate_id_set)
    rules_by_gate = parse_scaffold_rules(args.rule, gate_fields)
    global_samples, gate_specific_samples = parse_scaffold_samples(
        args.sample,
        gate_id_set,
        args.candidate_id,
        args.sample_id,
    )

    gates: list[dict[str, object]] = []
    for gate in gate_specs:
        gate_id = str(gate["id"])
        samples = dedupe_samples(global_samples + gate_specific_samples.get(gate_id, []))
        gates.append({
            "id": gate_id,
            "title": gate_titles.get(gate_id, title_from_id(gate_id)),
            "samples": samples,
            "required_fields": gate["required_fields"],
            "acceptance_rules": rules_by_gate.get(gate_id, []),
        })

    project = {
        "project": {
            "id": args.project_id,
            "name": args.project_name or title_from_id(args.project_id),
            "domain": args.domain,
            "version": "0.1.0",
        },
        "claim": {
            "id": args.claim_id,
            "statement": args.claim_statement,
            "requires_gates": gate_ids,
        },
        "evidence_policy": {
            "source_file_base_dir": ".",
            "require_source_files": True,
            "reject_placeholder_values": True,
            "allowed_source_roots": ["source_files"],
            "required_metadata_fields": ["source_file", "measured_at", "operator_or_agent"],
            "placeholder_markers": ["record_actual", "raw_file_needed", "not_measured"],
        },
        "gates": gates,
    }
    return project, gates, scaffold_evidence_rows(project)


def cmd_scaffold(args: argparse.Namespace) -> int:
    if args.out.exists():
        if not args.out.is_dir():
            raise SystemExit(f"Refusing to write scaffold over non-directory path: {args.out}")
        if any(args.out.iterdir()):
            raise SystemExit(f"Refusing to overwrite non-empty directory: {args.out}")

    project, gates, evidence_rows = build_scaffold_project(args)
    validation = validate_project_config(project)
    if not validation["valid"]:
        messages = "; ".join(issue["message"] for issue in validation.get("issues", []) if issue["level"] == "error")
        raise SystemExit(f"Generated scaffold project was invalid: {messages}")

    args.out.mkdir(parents=True, exist_ok=True)
    source_dir = args.out / "source_files"
    source_dir.mkdir(parents=True, exist_ok=True)
    project_path = args.out / "project.json"
    evidence_path = args.out / "evidence_template.csv"
    readme_path = args.out / "README.md"
    source_readme_path = source_dir / "README.md"

    project_path.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_evidence_csv(evidence_path, evidence_rows)
    readme_path.write_text(scaffold_project_readme(project), encoding="utf-8")
    source_readme_path.write_text(scaffold_source_readme(), encoding="utf-8")

    summary = {
        "status": "scaffolded",
        "project_id": args.project_id,
        "claim_id": args.claim_id,
        "gate_count": len(gates),
        "sample_count": sum(len(gate["samples"]) for gate in gates),
        "required_evidence_rows": len(evidence_rows),
        "project_path": str(project_path),
        "evidence_template_path": str(evidence_path),
        "source_files_dir": str(source_dir),
        "readme_path": str(readme_path),
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("Falsiflow scaffold: scaffolded")
        print(f"Gates: {summary['gate_count']}")
        print(f"Required evidence rows: {summary['required_evidence_rows']}")
        print(f"Wrote {project_path}")
        print(f"Wrote {evidence_path}")
        print(f"Wrote {source_dir}")
        print(f"Wrote {readme_path}")
    return 0


def template_scaffold_readme(template_id: str, project: dict[str, object]) -> str:
    claim = project.get("claim", {})
    claim_statement = str(claim.get("statement", "")) if isinstance(claim, dict) else ""
    return f"""# {title_from_id(template_id)}

Generated by `falsiflow template-scaffold`.

## Template Check

```bash
falsiflow template-check --template-dir . --out-dir /tmp/{template_id}_template_check --force
```

The positive demo evidence should reach `claim_ready`. The placeholder demo
evidence must stay blocked. Replace the synthetic demo evidence before using
this template to support a real research claim.

Claim: {claim_statement}
"""


def write_template_demo_source(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["row_id", "gate_id", "candidate_id", "sample_id", "field", "value"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            writer.writerow({
                "row_id": f"demo_{index:03d}",
                "gate_id": row.get("gate_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "sample_id": row.get("sample_id", ""),
                "field": row.get("field", ""),
                "value": row.get("value", ""),
            })


def cmd_template_scaffold(args: argparse.Namespace) -> int:
    if args.out.exists():
        if not args.out.is_dir():
            raise SystemExit(f"Refusing to write template over non-directory path: {args.out}")
        if any(args.out.iterdir()):
            if not args.force:
                raise SystemExit(f"Refusing to overwrite non-empty template directory without --force: {args.out}")
            shutil.rmtree(args.out)

    args.project_id = args.project_id or f"{args.template_id}_project"
    args.project_name = args.project_name or title_from_id(args.project_id)
    args.claim_id = args.claim_id or f"{args.template_id}_claim"
    args.template_name = args.template_name or title_from_id(args.template_id)
    args.template_description = args.template_description or f"Evidence-gated starter template for: {args.claim_statement}"

    project, gates, placeholder_rows = build_scaffold_project(args)
    validation = validate_project_config(project)
    if not validation["valid"]:
        messages = "; ".join(issue["message"] for issue in validation.get("issues", []) if issue["level"] == "error")
        raise SystemExit(f"Generated template project was invalid: {messages}")

    pass_rows = scaffold_passing_evidence_rows(project)
    args.out.mkdir(parents=True, exist_ok=True)
    source_path = args.out / "source_files" / "demo_raw_export.csv"
    project_path = args.out / "project.json"
    pass_evidence_path = args.out / "evidence_pass_demo.csv"
    placeholder_evidence_path = args.out / "evidence_placeholder_demo.csv"
    template_path_out = args.out / "template.json"
    readme_path = args.out / "README.md"

    template_manifest = {
        "id": args.template_id,
        "name": args.template_name,
        "domain": args.domain,
        "description": args.template_description,
        "project_config": "project.json",
        "demo_evidence": "evidence_pass_demo.csv",
        "placeholder_evidence": "evidence_placeholder_demo.csv",
    }

    project_path.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    template_path_out.write_text(json.dumps(template_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_evidence_csv(pass_evidence_path, pass_rows)
    write_evidence_csv(placeholder_evidence_path, placeholder_rows)
    write_template_demo_source(source_path, pass_rows)
    readme_path.write_text(template_scaffold_readme(args.template_id, project), encoding="utf-8")

    if args.check_out_dir is not None:
        check_summary = run_template_check(args.out, args.check_out_dir, force=args.force)
    else:
        with tempfile.TemporaryDirectory(prefix="falsiflow_template_scaffold_check_") as tmp:
            check_summary = run_template_check(args.out, Path(tmp), force=True)

    summary = {
        "status": "template_scaffolded" if check_summary.get("status") == "template_ready" else "template_scaffold_blocked",
        "template_id": args.template_id,
        "template_name": args.template_name,
        "domain": args.domain,
        "gate_count": len(gates),
        "sample_count": sum(len(gate["samples"]) for gate in gates),
        "required_evidence_rows": len(placeholder_rows),
        "template_check_status": check_summary.get("status", ""),
        "template_check_failure_count": check_summary.get("failure_count", 0),
        "template_dir": str(args.out),
        "template_manifest_path": str(template_path_out),
        "project_path": str(project_path),
        "pass_evidence_path": str(pass_evidence_path),
        "placeholder_evidence_path": str(placeholder_evidence_path),
        "source_file_path": str(source_path),
        "readme_path": str(readme_path),
    }
    if args.check_out_dir is not None:
        summary["template_check_path"] = str(args.check_out_dir / "template_check.json")

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-scaffold: {summary['status']}")
        print(f"Template: {summary['template_id']}")
        print(f"Gates: {summary['gate_count']}")
        print(f"Required evidence rows: {summary['required_evidence_rows']}")
        print(f"Template check: {summary['template_check_status']}")
        print(f"Wrote {template_path_out}")
        print(f"Wrote {project_path}")
        print(f"Wrote {pass_evidence_path}")
        print(f"Wrote {placeholder_evidence_path}")
        print(f"Wrote {source_path}")
    return 0 if summary["status"] == "template_scaffolded" else 2


def cmd_render(args: argparse.Namespace) -> int:
    project = load_project(args.config)
    if args.evidence is not None and not args.evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {args.evidence}")
    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(args.evidence)
    rendered = write_render_artifacts(project, evidence_rows, args.out_dir, evidence_file_issues=evidence_issues)
    audit = rendered["audit"]
    print(f"Falsiflow render: {audit['status']}")
    print(f"Claim ready: {str(bool(audit['claim_ready'])).lower()}")
    print(f"Wrote {args.out_dir / 'measurement_template.csv'}")
    print(f"Wrote {args.out_dir / 'claim_audit.json'}")
    print(f"Wrote {args.out_dir / 'claim_audit.md'}")
    print(f"Wrote {args.out_dir / 'audit_review.json'}")
    print(f"Wrote {args.out_dir / 'audit_review.md'}")
    print(f"Wrote {args.out_dir / 'claim_summary.json'}")
    print(f"Wrote {args.out_dir / 'next_actions.json'}")
    print(f"Wrote {args.out_dir / 'dashboard.html'}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    project = load_project(args.config)
    if not args.evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {args.evidence}")
    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(args.evidence)
    rendered = write_render_artifacts(project, evidence_rows, args.out_dir, evidence_file_issues=evidence_issues)
    audit = rendered["audit"]
    print(f"Falsiflow audit: {audit['status']}")
    print(f"Claim ready: {str(bool(audit['claim_ready'])).lower()}")
    print(f"Wrote {args.out_dir / 'claim_audit.json'}")
    print(f"Wrote {args.out_dir / 'claim_audit.md'}")
    print(f"Wrote {args.out_dir / 'audit_review.json'}")
    print(f"Wrote {args.out_dir / 'audit_review.md'}")
    print(f"Wrote {args.out_dir / 'claim_summary.json'}")
    print(f"Wrote {args.out_dir / 'next_actions.json'}")
    print(f"Wrote {args.out_dir / 'dashboard.html'}")
    return 0 if audit["claim_ready"] or not args.strict else 2


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact_record(root: Path, path: Path, role: str) -> dict[str, object]:
    return {
        "role": role,
        "path": str(path.relative_to(root)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def safe_source_relative_path(source_file: str) -> Path:
    path = Path(source_file)
    parts = [part for part in path.parts if part not in {"", ".", "..", path.anchor}]
    if path.is_absolute():
        parts = ["absolute", *parts]
    if not parts:
        parts = ["source_file"]
    return Path(*parts)


def write_bundle_manifest(
    out_dir: Path,
    project: dict[str, object],
    audit: dict[str, object],
    manifest: dict[str, object],
    zip_path: Path | None,
) -> dict[str, object]:
    artifacts: list[dict[str, object]] = []
    for path, role in [
        (out_dir / "inputs" / "project.json", "project_config"),
        (out_dir / "inputs" / "evidence.csv", "evidence_csv"),
        (out_dir / "audit" / "measurement_template.csv", "measurement_template"),
        (out_dir / "audit" / "claim_audit.json", "claim_audit"),
        (out_dir / "audit" / "claim_audit.md", "claim_audit_report"),
        (out_dir / "audit" / "audit_review.json", "audit_review"),
        (out_dir / "audit" / "audit_review.md", "audit_review_report"),
        (out_dir / "audit" / "claim_summary.json", "claim_summary"),
        (out_dir / "audit" / "next_actions.json", "next_actions"),
        (out_dir / "audit" / "dashboard.html", "dashboard"),
        (out_dir / "source_manifest.json", "source_manifest"),
        (out_dir / "source_manifest.md", "source_manifest_report"),
    ]:
        if path.exists():
            artifacts.append(artifact_record(out_dir, path, role))

    copied_sources = []
    for path in sorted((out_dir / "sources").rglob("*")) if (out_dir / "sources").exists() else []:
        if path.is_file():
            record = artifact_record(out_dir, path, "source_file")
            copied_sources.append(record)
            artifacts.append(record)

    bundle_ready = bool(audit.get("claim_ready")) and manifest.get("status") == "sources_ready"
    bundle = {
        "status": "bundle_ready" if bundle_ready else "bundle_blocked",
        "project_id": str(project.get("project", {}).get("id", "")),
        "claim_id": str(project.get("claim", {}).get("id", "")),
        "audit_status": audit.get("status", ""),
        "claim_ready": bool(audit.get("claim_ready")),
        "source_status": manifest.get("status", ""),
        "artifact_count": len(artifacts),
        "source_file_count": len(copied_sources),
        "artifacts": artifacts,
        "copied_source_files": copied_sources,
        "zip_path": str(zip_path) if zip_path else "",
    }
    (out_dir / "bundle_manifest.json").write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    return bundle


def zip_bundle(out_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(out_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(out_dir))


def verification_issue(
    severity: str,
    code: str,
    message: str,
    path: str = "",
    expected: object | None = None,
    actual: object | None = None,
) -> dict[str, object]:
    issue: dict[str, object] = {
        "severity": severity,
        "code": code,
        "message": message,
        "path": path,
    }
    if expected is not None:
        issue["expected"] = expected
    if actual is not None:
        issue["actual"] = actual
    return issue


def verification_failure_report(
    input_path: Path,
    input_format: str,
    issues: list[dict[str, object]],
    manifest_path: Path | None = None,
) -> dict[str, object]:
    return {
        "status": "bundle_failed",
        "integrity_status": "integrity_failed",
        "bundle_status": "",
        "input_format": input_format,
        "input_path": str(input_path),
        "bundle_dir": str(input_path),
        "manifest_path": str(manifest_path or (input_path / "bundle_manifest.json")),
        "artifact_count": 0,
        "checked_artifact_count": 0,
        "missing_artifact_count": 0,
        "bytes_mismatch_count": 0,
        "hash_mismatch_count": 0,
        "unsafe_path_count": sum(1 for issue in issues if issue["code"] in {"unsafe_artifact_path", "unsafe_zip_member"}),
        "duplicate_path_count": sum(1 for issue in issues if issue["code"] in {"duplicate_artifact_path", "duplicate_zip_member"}),
        "unmanifested_file_count": 0,
        "zip_member_count": 0,
        "zip_extracted_file_count": 0,
        "zip_issue_count": sum(1 for issue in issues if str(issue["code"]).startswith("zip_") or issue["code"] in {"unsafe_zip_member", "duplicate_zip_member"}),
        "issue_count": len(issues),
        "error_count": sum(1 for issue in issues if issue.get("severity") == "error"),
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }


def relative_artifact_path(bundle_dir: Path, raw_path: object, issues: list[dict[str, object]]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        issues.append(verification_issue("error", "invalid_artifact_path", "Artifact path must be a non-empty string."))
        return None
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts:
        issues.append(verification_issue("error", "unsafe_artifact_path", "Artifact path must stay inside the bundle.", raw_path))
        return None
    resolved_bundle = bundle_dir.resolve()
    resolved_path = (bundle_dir / path).resolve()
    try:
        resolved_path.relative_to(resolved_bundle)
    except ValueError:
        issues.append(verification_issue("error", "unsafe_artifact_path", "Artifact path resolves outside the bundle.", raw_path))
        return None
    return resolved_path


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdefABCDEF" for char in value)


def verify_bundle(bundle_dir: Path, input_path: Path | None = None, input_format: str = "directory") -> dict[str, object]:
    input_path = input_path or bundle_dir
    issues: list[dict[str, object]] = []
    manifest_path = bundle_dir / "bundle_manifest.json"
    if not bundle_dir.exists():
        issues.append(verification_issue("error", "bundle_dir_missing", "Bundle directory does not exist.", str(bundle_dir)))
    if not bundle_dir.is_dir():
        issues.append(verification_issue("error", "bundle_dir_not_directory", "Bundle path is not a directory.", str(bundle_dir)))
    if issues:
        return verification_failure_report(input_path, input_format, issues, manifest_path)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        manifest = {}
        issues.append(verification_issue("error", "manifest_missing", "bundle_manifest.json is missing.", "bundle_manifest.json"))
    except json.JSONDecodeError as exc:
        manifest = {}
        issues.append(verification_issue("error", "manifest_invalid_json", f"bundle_manifest.json is not valid JSON: {exc}", "bundle_manifest.json"))

    if not isinstance(manifest, dict):
        issues.append(verification_issue("error", "manifest_not_object", "bundle_manifest.json must contain a JSON object.", "bundle_manifest.json"))
        manifest = {}

    required_fields = [
        "status",
        "project_id",
        "claim_id",
        "audit_status",
        "claim_ready",
        "source_status",
        "artifact_count",
        "source_file_count",
        "artifacts",
        "copied_source_files",
    ]
    for field in required_fields:
        if field not in manifest:
            issues.append(verification_issue("error", "manifest_field_missing", f"Manifest is missing `{field}`.", "bundle_manifest.json"))

    artifacts_raw = manifest.get("artifacts", [])
    if not isinstance(artifacts_raw, list):
        issues.append(verification_issue("error", "manifest_artifacts_invalid", "Manifest `artifacts` must be an array.", "bundle_manifest.json"))
        artifacts: list[object] = []
    else:
        artifacts = artifacts_raw

    copied_sources_raw = manifest.get("copied_source_files", [])
    if not isinstance(copied_sources_raw, list):
        issues.append(verification_issue("error", "manifest_sources_invalid", "Manifest `copied_source_files` must be an array.", "bundle_manifest.json"))
        copied_sources: list[object] = []
    else:
        copied_sources = copied_sources_raw

    if manifest.get("artifact_count") != len(artifacts):
        issues.append(verification_issue("error", "artifact_count_mismatch", "Manifest artifact_count does not match artifacts length.", "bundle_manifest.json", len(artifacts), manifest.get("artifact_count")))
    if manifest.get("source_file_count") != len(copied_sources):
        issues.append(verification_issue("error", "source_file_count_mismatch", "Manifest source_file_count does not match copied_source_files length.", "bundle_manifest.json", len(copied_sources), manifest.get("source_file_count")))

    required_roles = {
        "project_config",
        "evidence_csv",
        "measurement_template",
        "claim_audit",
        "claim_audit_report",
        "audit_review",
        "audit_review_report",
        "claim_summary",
        "next_actions",
        "dashboard",
        "source_manifest",
        "source_manifest_report",
    }
    artifact_roles: set[str] = set()
    artifact_by_path: dict[str, dict[str, object]] = {}
    source_artifact_paths: set[str] = set()
    checked_artifact_count = 0
    missing_artifact_count = 0
    bytes_mismatch_count = 0
    hash_mismatch_count = 0
    duplicate_path_count = 0

    for index, artifact in enumerate(artifacts):
        artifact_path = f"artifacts[{index}]"
        if not isinstance(artifact, dict):
            issues.append(verification_issue("error", "artifact_invalid", "Artifact entry must be an object.", artifact_path))
            continue
        role = artifact.get("role")
        raw_path = artifact.get("path")
        expected_bytes = artifact.get("bytes")
        expected_sha256 = artifact.get("sha256")
        if not isinstance(role, str) or not role:
            issues.append(verification_issue("error", "artifact_role_invalid", "Artifact role must be a non-empty string.", artifact_path))
        else:
            artifact_roles.add(role)
        if not isinstance(expected_bytes, int) or expected_bytes < 0:
            issues.append(verification_issue("error", "artifact_bytes_invalid", "Artifact bytes must be a non-negative integer.", artifact_path))
        if not is_sha256(expected_sha256):
            issues.append(verification_issue("error", "artifact_sha256_invalid", "Artifact sha256 must be a 64-character hex digest.", artifact_path))

        resolved = relative_artifact_path(bundle_dir, raw_path, issues)
        normalized_path = Path(raw_path).as_posix() if isinstance(raw_path, str) else artifact_path
        if isinstance(raw_path, str):
            if normalized_path in artifact_by_path:
                duplicate_path_count += 1
                issues.append(verification_issue("error", "duplicate_artifact_path", "Artifact path appears more than once.", normalized_path))
            artifact_by_path[normalized_path] = artifact
        if role == "source_file":
            source_artifact_paths.add(normalized_path)
        if resolved is None:
            continue
        if not resolved.exists():
            missing_artifact_count += 1
            issues.append(verification_issue("error", "artifact_missing", "Artifact file is missing.", normalized_path))
            continue
        if not resolved.is_file():
            issues.append(verification_issue("error", "artifact_not_file", "Artifact path is not a file.", normalized_path))
            continue
        checked_artifact_count += 1
        actual_bytes = resolved.stat().st_size
        if isinstance(expected_bytes, int) and actual_bytes != expected_bytes:
            bytes_mismatch_count += 1
            issues.append(verification_issue("error", "artifact_bytes_mismatch", "Artifact byte size does not match manifest.", normalized_path, expected_bytes, actual_bytes))
        if is_sha256(expected_sha256):
            actual_sha256 = sha256_file(resolved)
            if str(expected_sha256).lower() != actual_sha256.lower():
                hash_mismatch_count += 1
                issues.append(verification_issue("error", "artifact_hash_mismatch", "Artifact SHA-256 does not match manifest.", normalized_path, expected_sha256, actual_sha256))

    for role in sorted(required_roles - artifact_roles):
        issues.append(verification_issue("error", "required_role_missing", f"Required artifact role `{role}` is missing.", "bundle_manifest.json"))

    for index, source in enumerate(copied_sources):
        source_path = f"copied_source_files[{index}]"
        if not isinstance(source, dict):
            issues.append(verification_issue("error", "copied_source_invalid", "Copied source entry must be an object.", source_path))
            continue
        raw_path = source.get("path")
        normalized_path = Path(raw_path).as_posix() if isinstance(raw_path, str) else source_path
        artifact = artifact_by_path.get(normalized_path)
        if artifact is None:
            issues.append(verification_issue("error", "copied_source_not_artifact", "Copied source is not listed in artifacts.", normalized_path))
            continue
        if artifact.get("role") != "source_file":
            issues.append(verification_issue("error", "copied_source_role_mismatch", "Copied source artifact must use role `source_file`.", normalized_path))
        for field in ["bytes", "sha256"]:
            if source.get(field) != artifact.get(field):
                issues.append(verification_issue("error", "copied_source_record_mismatch", f"Copied source `{field}` does not match artifact record.", normalized_path, artifact.get(field), source.get(field)))

    if isinstance(manifest.get("source_file_count"), int) and manifest.get("source_file_count") != len(source_artifact_paths):
        issues.append(verification_issue("error", "source_artifact_count_mismatch", "source_file_count does not match artifacts with role `source_file`.", "bundle_manifest.json", len(source_artifact_paths), manifest.get("source_file_count")))

    manifested_paths = set(artifact_by_path)
    unmanifested_files = [
        path.relative_to(bundle_dir).as_posix()
        for path in sorted(bundle_dir.rglob("*"))
        if path.is_file() and path.relative_to(bundle_dir).as_posix() not in manifested_paths and path.name != "bundle_manifest.json"
    ]
    for path in unmanifested_files:
        issues.append(verification_issue("error", "unmanifested_file", "Bundle contains a file not listed in bundle_manifest.json.", path))

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    integrity_status = "integrity_failed" if error_count else "integrity_verified"
    bundle_status = str(manifest.get("status", ""))
    if error_count:
        status = "bundle_failed"
    elif bundle_status == "bundle_ready":
        status = "bundle_verified"
    else:
        status = "bundle_blocked"

    return {
        "status": status,
        "integrity_status": integrity_status,
        "bundle_status": bundle_status,
        "input_format": input_format,
        "input_path": str(input_path),
        "bundle_dir": str(bundle_dir),
        "manifest_path": str(manifest_path),
        "artifact_count": len(artifacts),
        "checked_artifact_count": checked_artifact_count,
        "missing_artifact_count": missing_artifact_count,
        "bytes_mismatch_count": bytes_mismatch_count,
        "hash_mismatch_count": hash_mismatch_count,
        "unsafe_path_count": sum(1 for issue in issues if issue["code"] == "unsafe_artifact_path"),
        "duplicate_path_count": duplicate_path_count,
        "unmanifested_file_count": len(unmanifested_files),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues,
    }


def safe_zip_member_relative_path(member_name: str) -> Path | None:
    normalized = member_name.replace("\\", "/").strip("/")
    if not normalized:
        return None
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        return None
    if member_name.startswith(("/", "\\")):
        return None
    return Path(*parts)


def extracted_bundle_root(extract_root: Path, issues: list[dict[str, object]]) -> Path:
    if (extract_root / "bundle_manifest.json").exists():
        return extract_root
    manifests = sorted(extract_root.rglob("bundle_manifest.json"))
    if len(manifests) == 1:
        bundle_root = manifests[0].parent
        outside_files = [
            path.relative_to(extract_root).as_posix()
            for path in sorted(extract_root.rglob("*"))
            if path.is_file() and not path.resolve().is_relative_to(bundle_root.resolve())
        ]
        for path in outside_files:
            issues.append(verification_issue("error", "zip_file_outside_bundle_root", "Zip contains a file outside the detected bundle root.", path))
        return bundle_root
    if len(manifests) > 1:
        for manifest in manifests:
            issues.append(verification_issue("error", "multiple_bundle_manifests", "Zip contains multiple bundle_manifest.json files.", manifest.relative_to(extract_root).as_posix()))
    return extract_root


def merge_verification_issues(report: dict[str, object], extra_issues: list[dict[str, object]]) -> dict[str, object]:
    issues = [*extra_issues, *list(report.get("issues", []))]
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    report["issues"] = issues
    report["issue_count"] = len(issues)
    report["error_count"] = error_count
    report["warning_count"] = warning_count
    report["unsafe_path_count"] = sum(1 for issue in issues if issue["code"] in {"unsafe_artifact_path", "unsafe_zip_member"})
    report["duplicate_path_count"] = sum(1 for issue in issues if issue["code"] in {"duplicate_artifact_path", "duplicate_zip_member"})
    report["zip_issue_count"] = sum(1 for issue in extra_issues if issue.get("severity") == "error")
    if error_count:
        report["status"] = "bundle_failed"
        report["integrity_status"] = "integrity_failed"
    return report


def verify_bundle_zip(zip_path: Path) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    if not zip_path.exists():
        issues.append(verification_issue("error", "zip_missing", "Bundle zip does not exist.", str(zip_path)))
    if not zip_path.is_file():
        issues.append(verification_issue("error", "zip_not_file", "Bundle zip path is not a file.", str(zip_path)))
    if issues:
        return verification_failure_report(zip_path, "zip", issues, zip_path)

    try:
        archive = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        issues.append(verification_issue("error", "zip_invalid", f"Bundle zip is not a valid zip archive: {exc}", str(zip_path)))
        return verification_failure_report(zip_path, "zip", issues, zip_path)

    with archive:
        infos = archive.infolist()
        with tempfile.TemporaryDirectory(prefix="falsiflow_bundle_zip_") as tmp:
            extract_root = Path(tmp) / "bundle"
            extract_root.mkdir(parents=True, exist_ok=True)
            seen_files: set[str] = set()
            extracted_file_count = 0
            for info in infos:
                relative_path = safe_zip_member_relative_path(info.filename)
                if relative_path is None:
                    issues.append(verification_issue("error", "unsafe_zip_member", "Zip member path is empty, absolute, or escapes the archive root.", info.filename))
                    continue
                normalized = relative_path.as_posix()
                if info.is_dir():
                    (extract_root / relative_path).mkdir(parents=True, exist_ok=True)
                    continue
                if normalized in seen_files:
                    issues.append(verification_issue("error", "duplicate_zip_member", "Zip member path appears more than once.", normalized))
                    continue
                seen_files.add(normalized)
                destination = (extract_root / relative_path).resolve()
                try:
                    destination.relative_to(extract_root.resolve())
                except ValueError:
                    issues.append(verification_issue("error", "unsafe_zip_member", "Zip member resolves outside the extraction root.", info.filename))
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with archive.open(info, "r") as source, destination.open("wb") as target:
                        shutil.copyfileobj(source, target)
                    extracted_file_count += 1
                except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                    issues.append(verification_issue("error", "zip_member_read_failed", f"Could not extract zip member: {exc}", normalized))

            bundle_root = extracted_bundle_root(extract_root, issues)
            report = verify_bundle(bundle_root, input_path=zip_path, input_format="zip")
            report["bundle_dir"] = str(zip_path)
            report["zip_path"] = str(zip_path)
            report["zip_member_count"] = len(infos)
            report["zip_extracted_file_count"] = extracted_file_count
            report["zip_bundle_root"] = bundle_root.relative_to(extract_root).as_posix() if bundle_root != extract_root else "."
            report["manifest_path"] = f"{zip_path}:{Path(report['manifest_path']).relative_to(bundle_root).as_posix()}" if (bundle_root / "bundle_manifest.json").exists() else f"{zip_path}:bundle_manifest.json"
            return merge_verification_issues(report, issues)


def render_bundle_verification_report(report: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Bundle Verification",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Integrity: `{report.get('integrity_status', '')}`",
        f"- Bundle status: `{report.get('bundle_status', '')}`",
        f"- Input: `{report.get('input_format', '')}` `{report.get('input_path', '')}`",
        f"- Artifacts checked: {report.get('checked_artifact_count', 0)}/{report.get('artifact_count', 0)}",
        f"- Issues: {report.get('issue_count', 0)} errors={report.get('error_count', 0)} warnings={report.get('warning_count', 0)}",
        "",
        "## Counters",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in [
        "missing_artifact_count",
        "bytes_mismatch_count",
        "hash_mismatch_count",
        "unsafe_path_count",
        "duplicate_path_count",
        "unmanifested_file_count",
        "zip_member_count",
        "zip_extracted_file_count",
        "zip_issue_count",
    ]:
        if key in report:
            lines.append(f"| `{key}` | {report.get(key, 0)} |")
    issues = report.get("issues", [])
    lines.extend(["", "## Issues", ""])
    if not issues:
        lines.append("No issues found.")
    else:
        lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(issue.get("severity", "")),
                    f"`{markdown_cell(issue.get('code', ''))}`",
                    markdown_cell(issue.get("path", "")),
                    markdown_cell(issue.get("message", "")),
                ])
                + " |"
            )
    return "\n".join(lines) + "\n"


def build_bundle(config: Path, evidence: Path, out_dir: Path, zip_out: Path | None = None, force: bool = False) -> dict[str, object]:
    project = load_project(config)
    if not evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {evidence}")
    if out_dir.exists() and any(out_dir.iterdir()) and not force:
        raise SystemExit(f"Refusing to overwrite non-empty directory without --force: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (out_dir / "sources").mkdir(parents=True, exist_ok=True)

    shutil.copy2(config, out_dir / "inputs" / "project.json")
    shutil.copy2(evidence, out_dir / "inputs" / "evidence.csv")

    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(evidence)
    rendered = write_render_artifacts(project, evidence_rows, out_dir / "audit", evidence_file_issues=evidence_issues)
    audit = rendered["audit"]
    manifest = source_manifest(project, evidence_rows, evidence_issues)
    (out_dir / "source_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "source_manifest.md").write_text(render_source_manifest_report(manifest), encoding="utf-8")

    for record in manifest.get("source_files", []):
        if not isinstance(record, dict) or record.get("status") != "present":
            continue
        source_file = str(record.get("source_file", ""))
        source_path = Path(str(record.get("resolved_path", "")))
        destination = out_dir / "sources" / safe_source_relative_path(source_file)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)

    bundle = write_bundle_manifest(out_dir, project, audit, manifest, zip_out)
    if zip_out is not None:
        zip_bundle(out_dir, zip_out)
    return bundle


def cmd_bundle(args: argparse.Namespace) -> int:
    bundle = build_bundle(args.config, args.evidence, args.out_dir, args.zip_out, force=args.force)

    print(f"Falsiflow bundle: {bundle['status']}")
    print(f"Claim ready: {str(bool(bundle['claim_ready'])).lower()}")
    print(f"Source status: {bundle['source_status']}")
    print(f"Artifacts: {bundle['artifact_count']}")
    print(f"Copied source files: {bundle['source_file_count']}")
    print(f"Wrote {args.out_dir / 'bundle_manifest.json'}")
    if args.zip_out is not None:
        print(f"Wrote {args.zip_out}")
    return 0 if bundle["status"] == "bundle_ready" or not args.strict else 2


def cmd_verify_bundle(args: argparse.Namespace) -> int:
    report = verify_bundle_zip(args.zip_path) if args.zip_path is not None else verify_bundle(args.bundle_dir)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(render_bundle_verification_report(report), encoding="utf-8")
    print(f"Falsiflow verify-bundle: {report['status']}")
    print(f"Integrity: {report['integrity_status']}")
    print(f"Bundle status: {report['bundle_status']}")
    print(f"Artifacts checked: {report['checked_artifact_count']}/{report['artifact_count']}")
    print(f"Issues: {report['issue_count']}")
    if args.out:
        print(f"Wrote {args.out}")
    if args.report_out:
        print(f"Wrote {args.report_out}")
    if report["status"] == "bundle_failed":
        return 2
    if args.strict and report["status"] != "bundle_verified":
        return 2
    return 0


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
    claim_check_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    claim_check_report.write_text(render_claim_check_report(summary), encoding="utf-8")
    return summary


def resolve_claim_check_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    project_dir = args.project_dir.expanduser() if getattr(args, "project_dir", None) is not None else None
    config = args.config.expanduser() if args.config is not None else None
    evidence = args.evidence.expanduser() if args.evidence is not None else None
    out_dir = args.out_dir.expanduser() if args.out_dir is not None else None

    if project_dir is not None:
        config = config or project_dir / "project.json"
        evidence = evidence or project_dir / "evidence_pass_demo.csv"
        out_dir = out_dir or project_dir / "claim_check"

    missing = []
    if config is None:
        missing.append("--config or --project-dir")
    if evidence is None:
        missing.append("--evidence or --project-dir")
    if out_dir is None:
        missing.append("--out-dir or --project-dir")
    if missing:
        raise SystemExit("Missing required claim-check path(s): " + ", ".join(missing))
    if not config.exists():
        raise SystemExit(f"Project config does not exist: {config}")
    if not evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {evidence}")
    return config, evidence, out_dir


def cmd_claim_check(args: argparse.Namespace) -> int:
    config, evidence, out_dir = resolve_claim_check_paths(args)
    summary = run_claim_check(config, evidence, out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow claim-check: {summary['status']}")
        print(f"Config: {config}")
        print(f"Evidence: {evidence}")
        print(f"Claim ready: {str(bool(summary['claim_ready'])).lower()}")
        print(f"Audit review: {summary['audit_review_status']}")
        print(f"Sources: {summary['source_status']}")
        print(f"Bundle: {summary['bundle_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Failures: {summary['failure_count']}")
        print(f"Wrote {out_dir / 'claim_check.json'}")
        print(f"Wrote {out_dir / 'claim_check.md'}")
        print(f"Wrote {out_dir / 'evidence_bundle.zip'}")
        print(f"Wrote {out_dir / 'evidence_bundle_verify.json'}")
        print(f"Wrote {out_dir / 'evidence_bundle_verify.md'}")
    return 0 if summary["status"] == "claim_check_ready" or not args.strict else 2


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


def run_quickstart(template: str, out_dir: Path, template_roots: list[Path] | None = None, force: bool = False, include_env: bool = True) -> dict[str, object]:
    source = template_path(template, template_roots, include_env=include_env)
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


def cmd_quickstart(args: argparse.Namespace) -> int:
    summary = run_quickstart(args.template, args.out, args.template_root, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow quickstart: {summary['status']}")
        print(f"Template: {summary['template']}")
        print(f"Project: {summary['project_dir']}")
        print(f"Claim check: {summary['claim_check_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Failures: {summary['failure_count']}")
        outputs = summary.get("outputs", {})
        if isinstance(outputs, dict):
            print(f"Wrote {outputs.get('quickstart_summary', '')}")
            print(f"Wrote {outputs.get('quickstart_report', '')}")
            print(f"Wrote {outputs.get('claim_check', '')}")
            print(f"Wrote {outputs.get('evidence_bundle_zip', '')}")
        next_commands = summary.get("next_commands", [])
        if isinstance(next_commands, list) and next_commands:
            print(f"Next: {next_commands[0]}")
    return 0 if summary["status"] == "quickstart_ready" or not args.strict else 2


def file_href(report_dir: Path, path_text: object) -> str:
    raw = str(path_text or "").strip()
    if not raw:
        return "#"
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (report_dir / path).resolve()
    else:
        path = path.resolve()
    try:
        rel = os.path.relpath(path, report_dir.resolve())
        if rel != os.pardir and not rel.startswith(os.pardir + os.sep):
            return urllib.parse.quote(rel.replace(os.sep, "/"), safe="/#?=&%:;,+")
        return path.as_uri()
    except ValueError:
        return path.as_uri()


def html_file_link(report_dir: Path, label: str, path_text: object) -> str:
    text = str(path_text or "").strip()
    if not text:
        return ""
    return f'<a href="{escape(file_href(report_dir, text), quote=True)}">{escape(label)}</a>'


def render_workbench_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Falsiflow Workbench</title>
  <style>
    :root {
      --ink: #1f2933;
      --muted: #607080;
      --line: #d9e1ea;
      --bg: #f7f9fb;
      --panel: #ffffff;
      --ready: #177245;
      --blocked: #b42318;
      --accent: #276a7b;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }
    main { width: min(1120px, calc(100% - 32px)); margin: 24px auto 48px; }
    header { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 14px; }
    h1 { margin: 0 0 8px; font-size: 32px; letter-spacing: 0; }
    h2 { margin: 0 0 10px; font-size: 17px; letter-spacing: 0; }
    p { margin: 0; color: var(--muted); line-height: 1.5; }
    a { color: var(--accent); font-weight: 700; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, 0.8fr); gap: 12px; }
    section, .status { background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 16px; }
    label { display: block; font-size: 13px; font-weight: 700; margin: 14px 0 6px; }
    select, input[type="file"] { width: 100%; border: 1px solid var(--line); border-radius: 5px; background: white; padding: 9px; color: var(--ink); }
    button { border: 0; border-radius: 5px; background: var(--accent); color: #fff; font-weight: 700; padding: 10px 14px; cursor: pointer; margin-top: 14px; }
    button[disabled] { opacity: 0.55; cursor: progress; }
    .hint { margin-top: 6px; font-size: 13px; color: var(--muted); }
    .status strong { font-size: 22px; color: var(--blocked); }
    .status.ready strong { color: var(--ready); }
    .metrics { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }
    .metric { border: 1px solid var(--line); border-radius: 5px; padding: 10px; min-height: 70px; }
    .metric span { display: block; color: var(--muted); font-size: 12px; margin-bottom: 4px; }
    .metric b { overflow-wrap: anywhere; }
    ul { margin: 10px 0 0; padding-left: 20px; }
    li { margin: 8px 0; }
    pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #eef3f7; border: 1px solid var(--line); border-radius: 5px; padding: 12px; max-height: 260px; overflow: auto; }
    .hidden { display: none; }
    @media (max-width: 860px) { header, .grid { display: block; } section, .status { margin-top: 12px; } }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Falsiflow Workbench</h1>
        <p>Run a local evidence check from the browser. Files stay on this machine and are processed by the localhost Falsiflow server.</p>
      </div>
      <p><a href="index.html">Launchpad</a> · <a href="try_report.html">Example report</a> · <a href="falsiflow_wizard.html">Wizard</a></p>
    </header>
    <div class="grid">
      <section>
        <h2>Project And Evidence</h2>
        <p>Select a template, then optionally replace the project config and evidence with your own files.</p>
        <label for="template">Template</label>
        <select id="template"></select>
        <label for="project">Project JSON</label>
        <input id="project" type="file" accept=".json,application/json">
        <div class="hint">Optional. If empty, the selected template project is used.</div>
        <label for="evidence">Evidence CSV</label>
        <input id="evidence" type="file" accept=".csv,text/csv">
        <div class="hint">Optional. If empty, the selected template passing demo evidence is used.</div>
        <label for="sources">Raw Source Files</label>
        <input id="sources" type="file" multiple>
        <div class="hint">Optional. Files are copied into <code>source_files/</code> by filename.</div>
        <button id="run">Run Evidence Check</button>
      </section>
      <section>
        <h2>Result</h2>
        <div id="status" class="status">
          <span>Status</span>
          <strong>not_run</strong>
          <p class="hint">Run a check to see claim readiness, blockers, and review links.</p>
        </div>
        <div class="metrics">
          <div class="metric"><span>Claim</span><b id="claim">-</b></div>
          <div class="metric"><span>Sources</span><b id="sourcesStatus">-</b></div>
          <div class="metric"><span>Bundle</span><b id="bundle">-</b></div>
          <div class="metric"><span>Failures</span><b id="failures">-</b></div>
        </div>
        <ul id="links"></ul>
        <pre id="details" class="hidden"></pre>
      </section>
    </div>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    async function loadTemplates() {
      const response = await fetch("/api/templates");
      const payload = await response.json();
      $("template").innerHTML = payload.templates.map((item) => `<option value="${item.template}">${item.template} - ${item.name}</option>`).join("");
    }
    function readText(file) {
      if (!file) return Promise.resolve("");
      return file.text();
    }
    function readSource(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = () => reject(reader.error);
        reader.onload = () => {
          const value = String(reader.result || "");
          resolve({ name: file.name, content_b64: value.split(",").pop() || "" });
        };
        reader.readAsDataURL(file);
      });
    }
    function setResult(payload) {
      const status = $("status");
      status.className = payload.status === "workbench_ready" ? "status ready" : "status";
      status.querySelector("strong").textContent = payload.status || "unknown";
      $("claim").textContent = payload.claim_check_status || "-";
      $("sourcesStatus").textContent = payload.source_status || "-";
      $("bundle").textContent = payload.bundle_status || "-";
      $("failures").textContent = String(payload.failure_count ?? "-");
      const links = payload.links || {};
      $("links").innerHTML = Object.entries(links).filter(([, href]) => href).map(([label, href]) => `<li><a href="${href}">${label.replaceAll("_", " ")}</a></li>`).join("");
      $("details").classList.remove("hidden");
      $("details").textContent = JSON.stringify(payload.next_actions || payload.failures || [], null, 2);
    }
    async function runCheck() {
      $("run").disabled = true;
      try {
        const sourceFiles = await Promise.all(Array.from($("sources").files || []).map(readSource));
        const payload = {
          template: $("template").value,
          project_json: await readText($("project").files[0]),
          evidence_csv: await readText($("evidence").files[0]),
          source_files: sourceFiles
        };
        const response = await fetch("/api/workbench/check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const result = await response.json();
        setResult(result);
      } catch (error) {
        setResult({ status: "workbench_blocked", failure_count: 1, failures: [{ message: String(error) }] });
      } finally {
        $("run").disabled = false;
      }
    }
    $("run").addEventListener("click", runCheck);
    loadTemplates().catch((error) => setResult({ status: "workbench_blocked", failure_count: 1, failures: [{ message: String(error) }] }));
  </script>
</body>
</html>
"""


def render_try_report_html(summary: dict[str, object]) -> str:
    report_dir = Path(str(summary.get("out_dir", ".")))
    outputs = summary.get("outputs", {}) if isinstance(summary.get("outputs"), dict) else {}
    next_commands = summary.get("next_commands", []) if isinstance(summary.get("next_commands"), list) else []
    status = str(summary.get("status", ""))
    ready = status == "try_ready"
    status_class = "ready" if ready else "blocked"
    conclusion = (
        "The starter claim is ready: gates passed, source provenance is present, and the evidence bundle verified."
        if ready
        else "The starter claim is blocked; inspect the first action and generated reports."
    )
    link_items = [
        ("Launchpad", outputs.get("launchpad", report_dir / "index.html")),
        ("Claim dashboard", outputs.get("dashboard", "")),
        ("Quickstart report", outputs.get("quickstart_report", "")),
        ("Claim-check report", outputs.get("claim_check_report", "")),
        ("Evidence bundle", outputs.get("evidence_bundle_zip", "")),
        ("Bundle verification", outputs.get("bundle_verification_report", "")),
        ("Start your own project", outputs.get("wizard", "")),
    ]
    links = "\n".join(
        f"<li>{html_file_link(report_dir, label, path)}</li>"
        for label, path in link_items
        if str(path or "").strip()
    )
    command_rows = "\n".join(f"<li><code>{escape(str(command))}</code></li>" for command in next_commands)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Falsiflow Try</title>
  <style>
    :root {{
      --ink: #1f2933;
      --muted: #5f6f80;
      --line: #d9e1ea;
      --bg: #f7f9fb;
      --panel: #ffffff;
      --ready: #177245;
      --blocked: #b42318;
      --accent: #276a7b;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }}
    main {{ width: min(1060px, calc(100% - 32px)); margin: 24px auto 48px; }}
    header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.5; }}
    .status {{ min-width: 180px; border: 1px solid var(--line); border-radius: 6px; background: var(--panel); padding: 12px 14px; text-align: right; }}
    .status span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 4px; }}
    .status strong {{ color: var(--blocked); font-size: 20px; }}
    .status.ready strong {{ color: var(--ready); }}
    .summary {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 16px 0; }}
    .metric, section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 6px; }}
    .metric {{ padding: 14px; min-height: 78px; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 6px; }}
    .metric strong {{ font-size: 19px; overflow-wrap: anywhere; }}
    section {{ padding: 16px; margin-top: 12px; }}
    h2 {{ font-size: 16px; margin: 0 0 10px; letter-spacing: 0; }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin: 8px 0; }}
    a {{ color: var(--accent); font-weight: 600; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    code {{ background: #eef3f7; border: 1px solid var(--line); border-radius: 4px; padding: 2px 5px; overflow-wrap: anywhere; }}
    .callout {{ border-left: 4px solid var(--accent); padding-left: 12px; }}
    @media (max-width: 760px) {{
      header {{ display: block; }}
      .status {{ text-align: left; margin-top: 12px; }}
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Falsiflow Try</h1>
        <p>{escape(conclusion)}</p>
      </div>
      <div class="status {status_class}">
        <span>Status</span>
        <strong>{escape(status)}</strong>
      </div>
    </header>
    <div class="summary">
      <div class="metric"><span>Template</span><strong>{escape(str(summary.get("template", "")))}</strong></div>
      <div class="metric"><span>Claim check</span><strong>{escape(str(summary.get("claim_check_status", "")))}</strong></div>
      <div class="metric"><span>Sources</span><strong>{escape(str(summary.get("source_status", "")))}</strong></div>
      <div class="metric"><span>Verification</span><strong>{escape(str(summary.get("verification_status", "")))}</strong></div>
    </div>
    <section class="callout">
      <h2>Open</h2>
      <ul>
        {links}
      </ul>
    </section>
    <section>
      <h2>Start Your Own Project</h2>
      <p>Use the browser wizard to draft a claim, gate, threshold, starter project JSON, evidence CSV, and scaffold command without writing the schema by hand.</p>
    </section>
    <section>
      <h2>Next Commands</h2>
      <ul>
        {command_rows or "<li>No next commands recorded.</li>"}
      </ul>
    </section>
  </main>
</body>
</html>
"""


def render_try_launchpad_html(summary: dict[str, object]) -> str:
    report_dir = Path(str(summary.get("out_dir", ".")))
    outputs = summary.get("outputs", {}) if isinstance(summary.get("outputs"), dict) else {}
    next_commands = summary.get("next_commands", []) if isinstance(summary.get("next_commands"), list) else []
    status = str(summary.get("status", ""))
    ready = status == "try_ready"
    status_class = "ready" if ready else "blocked"
    headline = "A local app for checking whether a project decision has enough evidence"
    summary_text = (
        "No account or upload is needed. Start with the example result, then use the wizard to make your own evidence checklist."
        if ready
        else "The local demo needs attention before it can be used as a clean starter."
    )
    first_command = str(next_commands[0]) if next_commands else "falsiflow doctor --project-dir falsiflow_try/project --strict"
    cards = [
        (
            "1. Run your own check",
            "Open workbench",
            outputs.get("workbench", report_dir / "workbench.html"),
            "Upload project, evidence, and source files, then run the local evidence gate from this browser.",
        ),
        (
            "2. See the example result",
            "Open report",
            outputs.get("try_report", report_dir / "try_report.html"),
            "A readable pass/fail report that shows the decision, the evidence, and what to check next.",
        ),
        (
            "3. Make your own checklist",
            "Open wizard",
            outputs.get("wizard", report_dir / "falsiflow_wizard.html"),
            "Answer a few form fields and download starter files without writing JSON by hand.",
        ),
        (
            "4. Inspect the evidence",
            "Open dashboard",
            outputs.get("dashboard", ""),
            "See which measured values and source files support the example decision.",
        ),
    ]
    card_html = "\n".join(
        f"""      <article>
        <span>{escape(kicker)}</span>
        <h2>{escape(title)}</h2>
        <p>{escape(body)}</p>
        {html_file_link(report_dir, title, href)}
      </article>"""
        for kicker, title, href, body in cards
        if str(href or "").strip()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Falsiflow Launchpad</title>
  <style>
    :root {{
      --ink: #1f2933;
      --muted: #5f6f80;
      --line: #d9e1ea;
      --bg: #f7f9fb;
      --panel: #ffffff;
      --ready: #177245;
      --blocked: #b42318;
      --accent: #276a7b;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }}
    main {{ width: min(1080px, calc(100% - 32px)); margin: 24px auto 48px; }}
    header {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 18px; align-items: start; margin-bottom: 16px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.5; }}
    .status {{ min-width: 184px; border: 1px solid var(--line); border-radius: 6px; background: var(--panel); padding: 12px 14px; text-align: right; }}
    .status span, article span, .metric span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 5px; }}
    .status strong {{ color: var(--blocked); font-size: 20px; }}
    .status.ready strong {{ color: var(--ready); }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 12px; }}
    .metric, article, section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 6px; }}
    .metric {{ padding: 14px; min-height: 76px; }}
    .metric strong {{ font-size: 18px; overflow-wrap: anywhere; }}
    .cards {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 12px 0; }}
    article {{ padding: 16px; min-height: 188px; display: flex; flex-direction: column; gap: 10px; }}
    article h2 {{ font-size: 17px; margin: 0; letter-spacing: 0; }}
    article p {{ flex: 1; }}
    a {{ color: var(--accent); font-weight: 700; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    section {{ padding: 16px; margin-top: 12px; }}
    section h2 {{ font-size: 16px; margin: 0 0 10px; letter-spacing: 0; }}
    code {{ display: block; background: #eef3f7; border: 1px solid var(--line); border-radius: 5px; padding: 10px; overflow-wrap: anywhere; }}
    @media (max-width: 900px) {{
      header {{ grid-template-columns: 1fr; }}
      .status {{ text-align: left; }}
      .metrics, .cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 620px) {{
      .metrics, .cards {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Falsiflow Launchpad</h1>
        <p>{escape(headline)}. {escape(summary_text)}</p>
      </div>
      <div class="status {status_class}">
        <span>Status</span>
        <strong>{escape(status)}</strong>
      </div>
    </header>
    <div class="metrics">
      <div class="metric"><span>Example</span><strong>{escape(str(summary.get("template", "")))}</strong></div>
      <div class="metric"><span>Decision check</span><strong>{escape(str(summary.get("claim_check_status", "")))}</strong></div>
      <div class="metric"><span>Source files</span><strong>{escape(str(summary.get("source_status", "")))}</strong></div>
      <div class="metric"><span>Review package</span><strong>{escape(str(summary.get("verification_status", "")))}</strong></div>
    </div>
    <div class="cards">
{card_html}
    </div>
    <section>
      <h2>Advanced CLI Handoff</h2>
      <p>Use this only when you are ready to inspect or rerun the generated project from the terminal.</p>
      <code>{escape(first_command)}</code>
    </section>
  </main>
</body>
</html>
"""


def refresh_try_browser_assets(out_dir: Path, summary: dict[str, object]) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = summary.get("outputs")
    if not isinstance(outputs, dict):
        outputs = {}
        summary["outputs"] = outputs
    outputs.setdefault("try_summary", str(out_dir / "try_summary.json"))
    outputs.setdefault("launchpad", str(out_dir / "index.html"))
    outputs.setdefault("try_report", str(out_dir / "try_report.html"))
    outputs.setdefault("workbench", str(out_dir / "workbench.html"))
    outputs.setdefault("wizard", str(out_dir / "falsiflow_wizard.html"))
    summary.setdefault("out_dir", str(out_dir))
    wizard_path = Path(str(outputs["wizard"]))
    if not wizard_path.exists():
        wizard_path.parent.mkdir(parents=True, exist_ok=True)
        wizard_path.write_text(render_browser_wizard_html(), encoding="utf-8")
    launchpad_path = Path(str(outputs["launchpad"]))
    launchpad_path.parent.mkdir(parents=True, exist_ok=True)
    launchpad_path.write_text(render_try_launchpad_html(summary), encoding="utf-8")
    workbench_path = Path(str(outputs["workbench"]))
    workbench_path.parent.mkdir(parents=True, exist_ok=True)
    workbench_path.write_text(render_workbench_html(), encoding="utf-8")
    try_summary_path = Path(str(outputs["try_summary"]))
    try_summary_path.parent.mkdir(parents=True, exist_ok=True)
    try_summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def run_try(template: str, out_dir: Path, template_roots: list[Path] | None = None, force: bool = False, include_env: bool = True) -> dict[str, object]:
    prepare_output_directory(out_dir, "try output directory", force=force)
    out_dir.mkdir(parents=True, exist_ok=True)
    project_dir = out_dir / "project"
    quickstart = run_quickstart(template, project_dir, template_roots=template_roots, force=True, include_env=include_env)
    quickstart_outputs = quickstart.get("outputs", {}) if isinstance(quickstart.get("outputs"), dict) else {}
    try_json = out_dir / "try_summary.json"
    launchpad = out_dir / "index.html"
    try_report = out_dir / "try_report.html"
    workbench_path = out_dir / "workbench.html"
    wizard_path = out_dir / "falsiflow_wizard.html"
    wizard_path.write_text(render_browser_wizard_html(), encoding="utf-8")
    next_commands = list(quickstart.get("next_commands", [])) if isinstance(quickstart.get("next_commands"), list) else []
    next_commands.append(f"open {launchpad}")
    next_commands.append(f"open {wizard_path}")
    status = "try_ready" if quickstart.get("status") == "quickstart_ready" else "try_blocked"
    outputs = {
        "try_summary": str(try_json),
        "launchpad": str(launchpad),
        "try_report": str(try_report),
        "workbench": str(workbench_path),
        "project_dir": str(project_dir),
        "quickstart_summary": str(quickstart_outputs.get("quickstart_summary", project_dir / "quickstart_summary.json")),
        "quickstart_report": str(quickstart_outputs.get("quickstart_report", project_dir / "quickstart_summary.md")),
        "claim_check": str(quickstart_outputs.get("claim_check", project_dir / "claim_check" / "claim_check.json")),
        "claim_check_report": str(quickstart_outputs.get("claim_check_report", project_dir / "claim_check" / "claim_check.md")),
        "dashboard": str(quickstart_outputs.get("dashboard", project_dir / "claim_check" / "evidence_bundle" / "audit" / "dashboard.html")),
        "wizard": str(wizard_path),
        "evidence_bundle_zip": str(quickstart_outputs.get("evidence_bundle_zip", project_dir / "claim_check" / "evidence_bundle.zip")),
        "bundle_verification_report": str(quickstart_outputs.get("bundle_verification_report", project_dir / "claim_check" / "evidence_bundle_verify.md")),
    }
    summary: dict[str, object] = {
        "status": status,
        "template": template,
        "out_dir": str(out_dir),
        "project_dir": str(project_dir),
        "claim_ready": bool(quickstart.get("claim_ready")),
        "quickstart_status": str(quickstart.get("status", "")),
        "claim_check_status": str(quickstart.get("claim_check_status", "")),
        "audit_review_status": str(quickstart.get("audit_review_status", "")),
        "source_status": str(quickstart.get("source_status", "")),
        "bundle_status": str(quickstart.get("bundle_status", "")),
        "verification_status": str(quickstart.get("verification_status", "")),
        "failure_count": int(quickstart.get("failure_count", 0) or 0),
        "failures": quickstart.get("failures", []),
        "outputs": outputs,
        "next_commands": next_commands,
        "quickstart_summary": quickstart,
    }
    try_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    launchpad.write_text(render_try_launchpad_html(summary), encoding="utf-8")
    workbench_path.write_text(render_workbench_html(), encoding="utf-8")
    try_report.write_text(render_try_report_html(summary), encoding="utf-8")
    return summary


def cmd_try(args: argparse.Namespace) -> int:
    summary = run_try(args.template, args.out_dir, args.template_root, force=args.force)
    outputs = summary.get("outputs", {}) if isinstance(summary.get("outputs"), dict) else {}
    launchpad_path = Path(str(outputs.get("launchpad", ""))) if outputs.get("launchpad") else None
    if args.open and launchpad_path is not None:
        webbrowser.open(launchpad_path.resolve().as_uri())
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow try: {summary['status']}")
        print(f"Template: {summary['template']}")
        print(f"Project: {summary['project_dir']}")
        print(f"Claim check: {summary['claim_check_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Open: {outputs.get('launchpad', outputs.get('try_report', ''))}")
        print(f"Report: {outputs.get('try_report', '')}")
        print(f"Workbench: {outputs.get('workbench', '')}")
        print(f"Dashboard: {outputs.get('dashboard', '')}")
        print(f"Wizard: {outputs.get('wizard', '')}")
        next_commands = summary.get("next_commands", [])
        if isinstance(next_commands, list) and next_commands:
            print(f"Next: {next_commands[0]}")
    return 0 if summary["status"] == "try_ready" or not args.strict else 2


def render_browser_wizard_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Falsiflow Browser Wizard</title>
  <style>
    :root {
      --ink: #1f2933;
      --muted: #5f6f80;
      --line: #d9e1ea;
      --bg: #f7f9fb;
      --panel: #ffffff;
      --accent: #276a7b;
      --focus: #c5dce5;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }
    main { width: min(1120px, calc(100% - 32px)); margin: 24px auto 48px; }
    h1 { margin: 0 0 6px; font-size: 30px; letter-spacing: 0; }
    p { margin: 0; color: var(--muted); line-height: 1.5; }
    .grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(360px, 0.9fr); gap: 14px; margin-top: 18px; align-items: start; }
    form, section { background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 16px; }
    fieldset { border: 0; padding: 0; margin: 0 0 18px; }
    legend, h2 { font-size: 16px; font-weight: 700; margin: 0 0 12px; letter-spacing: 0; }
    label { display: block; color: var(--muted); font-size: 12px; margin: 0 0 6px; }
    input, textarea, select { width: 100%; border: 1px solid var(--line); border-radius: 6px; padding: 10px 11px; font: inherit; color: var(--ink); background: #fff; }
    textarea { min-height: 84px; resize: vertical; }
    input:focus, textarea:focus, select:focus { outline: 3px solid var(--focus); border-color: var(--accent); }
    .row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-bottom: 10px; }
    .row.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    pre { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; background: #eef3f7; border: 1px solid var(--line); border-radius: 6px; padding: 12px; min-height: 112px; }
    button, a.download { display: inline-flex; align-items: center; justify-content: center; min-height: 38px; border-radius: 6px; border: 1px solid var(--accent); background: var(--accent); color: #fff; padding: 8px 12px; font: inherit; font-weight: 700; text-decoration: none; cursor: pointer; }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    .ghost { background: #fff; color: var(--accent); }
    .hint { color: var(--muted); font-size: 12px; margin-top: 8px; }
    @media (max-width: 860px) {
      .grid { grid-template-columns: 1fr; }
      .row, .row.three { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <h1>Falsiflow Browser Wizard</h1>
    <p>Start from a plain-language checklist, then export the command and starter files.</p>
    <div class="grid">
      <form id="wizard">
        <fieldset>
          <legend>Choose a starter</legend>
          <label for="preset">Plain-language use case</label>
          <select id="preset">
            <option value="biointerface">Material or coating screen</option>
            <option value="vendor">Vendor evidence review</option>
            <option value="custom">Custom R&D decision</option>
          </select>
          <p class="hint">Pick the closest use case first. You can still edit every field below.</p>
        </fieldset>
        <fieldset>
          <legend>Decision</legend>
          <div class="row">
            <div>
              <label for="projectId">Project ID</label>
              <input id="projectId" value="my_rd_screen">
            </div>
            <div>
              <label for="claimId">Claim ID</label>
              <input id="claimId" value="candidate_claim">
            </div>
          </div>
          <label for="claimStatement">Decision to check</label>
          <textarea id="claimStatement">Candidate has enough source-backed screening evidence to proceed.</textarea>
        </fieldset>
        <fieldset>
          <legend>Evidence checklist</legend>
          <div class="row">
            <div>
              <label for="gateId">Checklist ID</label>
              <input id="gateId" value="screening_gate">
            </div>
            <div>
              <label for="fields">Values you need</label>
              <input id="fields" value="viability_pct,response_score">
            </div>
          </div>
          <div class="row">
            <div>
              <label for="candidateId">Option being checked</label>
              <input id="candidateId" value="candidate_a">
            </div>
            <div>
              <label for="sampleId">Sample or record ID</label>
              <input id="sampleId" value="sample_001">
            </div>
          </div>
        </fieldset>
        <fieldset>
          <legend>Pass rule</legend>
          <div class="row three">
            <div>
              <label for="ruleField">Value to compare</label>
              <input id="ruleField" value="viability_pct">
            </div>
            <div>
              <label for="operator">Operator</label>
              <select id="operator">
                <option>&gt;=</option>
                <option>&gt;</option>
                <option>&lt;=</option>
                <option>&lt;</option>
                <option>==</option>
                <option>!=</option>
              </select>
            </div>
            <div>
              <label for="ruleValue">Value</label>
              <input id="ruleValue" value="80">
            </div>
          </div>
        </fieldset>
      </form>
      <section>
        <h2>Command</h2>
        <pre id="command"></pre>
        <div class="actions">
          <button id="copyCommand" type="button">Copy Command</button>
          <a id="downloadProject" class="download ghost" download="project.json" href="#">Download project.json</a>
          <a id="downloadEvidence" class="download ghost" download="evidence_template.csv" href="#">Download evidence_template.csv</a>
        </div>
        <p class="hint">Run the command, fill measured values and source files, then run <code>falsiflow doctor --project-dir my_falsiflow_project --strict</code>.</p>
      </section>
    </div>
  </main>
  <script>
    const ids = ["projectId", "claimId", "claimStatement", "gateId", "fields", "candidateId", "sampleId", "ruleField", "operator", "ruleValue"];
    const $ = (id) => document.getElementById(id);
    const presets = {
      biointerface: {
        projectId: "material_screen",
        claimId: "ready_for_cell_contact_screen",
        claimStatement: "Candidate material has enough source-backed screening evidence to proceed to cell-contact testing.",
        gateId: "screening_gate",
        fields: "viability_pct,response_score",
        candidateId: "candidate_material_a",
        sampleId: "sample_001",
        ruleField: "viability_pct",
        operator: ">=",
        ruleValue: "80"
      },
      vendor: {
        projectId: "vendor_evidence_review",
        claimId: "supplier_ready_for_shortlist",
        claimStatement: "Supplier has enough documented evidence to stay on the shortlist.",
        gateId: "vendor_evidence_gate",
        fields: "certificate_present,response_time_days,quoted_price_usd",
        candidateId: "supplier_a",
        sampleId: "quote_001",
        ruleField: "response_time_days",
        operator: "<=",
        ruleValue: "7"
      },
      custom: {
        projectId: "my_rd_screen",
        claimId: "candidate_claim",
        claimStatement: "Candidate has enough source-backed screening evidence to proceed.",
        gateId: "screening_gate",
        fields: "value,response_score",
        candidateId: "candidate_a",
        sampleId: "sample_001",
        ruleField: "value",
        operator: ">=",
        ruleValue: "1"
      }
    };
    function cleanId(value, fallback) {
      const cleaned = String(value || "").trim().replace(/[^A-Za-z0-9_.-]+/g, "_").replace(/^_+|_+$/g, "");
      return cleaned || fallback;
    }
    function fieldList() {
      return $("fields").value.split(",").map((item) => cleanId(item, "")).filter(Boolean);
    }
    function shellQuote(value) {
      return "'" + String(value).replace(/'/g, "'\\\"'\\\"'") + "'";
    }
    function projectJson() {
      const gateId = cleanId($("gateId").value, "screening_gate");
      const fields = fieldList();
      const ruleField = cleanId($("ruleField").value, fields[0] || "value");
      const rule = {
        field: ruleField,
        operator: $("operator").value,
        value: Number.isNaN(Number($("ruleValue").value)) ? $("ruleValue").value : Number($("ruleValue").value),
        reason: "Wizard threshold."
      };
      return {
        project: {
          id: cleanId($("projectId").value, "my_rd_screen"),
          name: cleanId($("projectId").value, "my_rd_screen").replaceAll("_", " "),
          domain: "custom-rd",
          version: "0.1.0"
        },
        claim: {
          id: cleanId($("claimId").value, "candidate_claim"),
          statement: $("claimStatement").value.trim() || "Candidate has enough source-backed evidence to proceed.",
          requires_gates: [gateId]
        },
        evidence_policy: {
          source_file_base_dir: ".",
          require_source_files: true,
          reject_placeholder_values: true,
          allowed_source_roots: ["source_files"],
          required_metadata_fields: ["source_file", "measured_at", "operator_or_agent"],
          placeholder_markers: ["record_actual", "raw_file_needed", "not_measured"]
        },
        gates: [{
          id: gateId,
          title: gateId.replaceAll("_", " "),
          samples: [{ candidate_id: cleanId($("candidateId").value, "candidate_a"), sample_id: cleanId($("sampleId").value, "sample_001") }],
          required_fields: fields.length ? fields : ["value"],
          acceptance_rules: [rule]
        }]
      };
    }
    function evidenceCsv() {
      const gateId = cleanId($("gateId").value, "screening_gate");
      const candidateId = cleanId($("candidateId").value, "candidate_a");
      const sampleId = cleanId($("sampleId").value, "sample_001");
      const header = "gate_id,candidate_id,sample_id,field,value,source_file,measured_at,operator_or_agent,instrument_id,notes";
      const rows = fieldList().map((field) => [gateId, candidateId, sampleId, field, "record_actual", "source_files/raw_export.csv", "record_actual", "record_actual", "", ""].join(","));
      return [header, ...rows].join("\\n") + "\\n";
    }
    function setDownload(link, text, type) {
      const blob = new Blob([text], { type });
      const old = link.dataset.url;
      if (old) URL.revokeObjectURL(old);
      const url = URL.createObjectURL(blob);
      link.href = url;
      link.dataset.url = url;
    }
    function update() {
      const project = projectJson();
      const gateId = project.gates[0].id;
      const fields = project.gates[0].required_fields.join(",");
      const rule = project.gates[0].acceptance_rules[0];
      const command = [
        "falsiflow scaffold",
        "--out my_falsiflow_project",
        "--project-id " + shellQuote(project.project.id),
        "--claim-id " + shellQuote(project.claim.id),
        "--claim-statement " + shellQuote(project.claim.statement),
        "--gate " + shellQuote(gateId + ":" + fields),
        "--sample " + shellQuote(project.gates[0].samples[0].candidate_id + ":" + project.gates[0].samples[0].sample_id),
        "--rule " + shellQuote(gateId + ":" + rule.field + ":" + rule.operator + ":" + rule.value + ":" + rule.reason)
      ].join(" \\\\\\n  ");
      $("command").textContent = command;
      setDownload($("downloadProject"), JSON.stringify(project, null, 2) + "\\n", "application/json");
      setDownload($("downloadEvidence"), evidenceCsv(), "text/csv");
    }
    function applyPreset() {
      const preset = presets[$("preset").value] || presets.biointerface;
      Object.entries(preset).forEach(([id, value]) => {
        if ($(id)) $(id).value = value;
      });
      update();
    }
    ids.forEach((id) => $(id).addEventListener("input", update));
    $("operator").addEventListener("change", update);
    $("preset").addEventListener("change", applyPreset);
    $("copyCommand").addEventListener("click", async () => {
      await navigator.clipboard.writeText($("command").textContent);
    });
    applyPreset();
  </script>
</body>
</html>
"""


def run_wizard(out: Path, force: bool = False) -> dict[str, object]:
    if out.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing wizard file without --force: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_browser_wizard_html(), encoding="utf-8")
    return {
        "status": "wizard_ready",
        "wizard_path": str(out),
        "mode": "static_browser_wizard",
        "next_commands": [
            f"open {out}",
            "Use the generated scaffold command, then run falsiflow doctor --project-dir my_falsiflow_project --strict.",
        ],
    }


def cmd_wizard(args: argparse.Namespace) -> int:
    summary = run_wizard(args.out, force=args.force)
    if args.open:
        webbrowser.open(args.out.resolve().as_uri())
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow wizard: {summary['status']}")
        print(f"Open: {summary['wizard_path']}")
        print(f"Next: {summary['next_commands'][1]}")
    return 0


def safe_uploaded_source_name(name: object) -> str:
    filename = Path(str(name or "").replace("\\", "/")).name
    if not filename or filename in {".", ".."}:
        raise SystemExit("Uploaded source file is missing a safe filename.")
    return filename


def workbench_link(out_dir: Path, path_text: object) -> str:
    text = str(path_text or "").strip()
    if not text:
        return ""
    try:
        relative = Path(text).resolve().relative_to(out_dir.resolve())
    except ValueError:
        return ""
    return urllib.parse.quote(str(relative), safe="/")


def write_workbench_uploads(out_dir: Path, payload: dict[str, object]) -> tuple[str, Path, Path, Path]:
    template = str(payload.get("template") or "biointerface_coatings")
    workbench_dir = out_dir / "workbench_project"
    if workbench_dir.exists():
        shutil.rmtree(workbench_dir)
    project_json = str(payload.get("project_json") or "").strip()
    evidence_csv = str(payload.get("evidence_csv") or "").strip()

    if project_json:
        workbench_dir.mkdir(parents=True, exist_ok=True)
        (workbench_dir / "source_files").mkdir(parents=True, exist_ok=True)
        (workbench_dir / "project.json").write_text(project_json + "\n", encoding="utf-8")
    else:
        source_template = template_path(template)
        if source_template is None:
            raise SystemExit(f"Unknown template `{template}`.")
        shutil.copytree(source_template, workbench_dir)

    if evidence_csv:
        evidence_path = workbench_dir / "evidence.csv"
        evidence_path.write_text(evidence_csv if evidence_csv.endswith("\n") else evidence_csv + "\n", encoding="utf-8")
    else:
        evidence_path = default_project_evidence_path(workbench_dir)

    source_dir = workbench_dir / "source_files"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_files = payload.get("source_files", [])
    if isinstance(source_files, list):
        for source in source_files:
            if not isinstance(source, dict):
                continue
            filename = safe_uploaded_source_name(source.get("name", ""))
            encoded = str(source.get("content_b64") or "")
            try:
                data = base64.b64decode(encoded.encode("ascii"), validate=True)
            except Exception as exc:
                raise SystemExit(f"Could not decode uploaded source file `{filename}`: {exc}") from exc
            (source_dir / filename).write_bytes(data)

    return template, workbench_dir, workbench_dir / "project.json", evidence_path


def run_workbench_check(out_dir: Path, payload: dict[str, object]) -> dict[str, object]:
    template, project_dir, config, evidence = write_workbench_uploads(out_dir, payload)
    doctor_dir = project_dir / "doctor"
    doctor = run_doctor(project_dir, config, evidence, doctor_dir, force=True)
    claim_check = doctor.get("claim_check_summary", {}) if isinstance(doctor.get("claim_check_summary"), dict) else {}
    claim_outputs = claim_check.get("outputs", {}) if isinstance(claim_check.get("outputs"), dict) else {}
    doctor_outputs = doctor.get("outputs", {}) if isinstance(doctor.get("outputs"), dict) else {}
    ready = doctor.get("status") == "doctor_ready"
    summary: dict[str, object] = {
        "status": "workbench_ready" if ready else "workbench_blocked",
        "template": template,
        "project_dir": str(project_dir),
        "config_path": str(config),
        "evidence_path": str(evidence),
        "doctor_status": str(doctor.get("status", "")),
        "claim_check_status": str(doctor.get("claim_check_status", "")),
        "claim_ready": bool(doctor.get("claim_ready")),
        "source_status": str(doctor.get("source_status", "")),
        "bundle_status": str(doctor.get("bundle_status", "")),
        "verification_status": str(doctor.get("verification_status", "")),
        "blocking_stage": str(doctor.get("blocking_stage", "")),
        "failure_count": int(doctor.get("failure_count", 0) or 0),
        "failures": doctor.get("failures", []),
        "next_actions": doctor.get("next_actions", []),
        "links": {
            "doctor_report": workbench_link(out_dir, doctor_outputs.get("doctor_report", "")),
            "claim_check_report": workbench_link(out_dir, claim_outputs.get("claim_check_report", "")),
            "dashboard": workbench_link(out_dir, claim_outputs.get("dashboard", "")),
            "evidence_bundle": workbench_link(out_dir, claim_outputs.get("bundle_zip", "")),
            "bundle_verification": workbench_link(out_dir, claim_outputs.get("bundle_verification_report", "")),
        },
        "doctor_summary": doctor,
    }
    summary_path = out_dir / "workbench_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def discovery_slug(text: str, fallback: str = "candidate") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or fallback


def load_discovery_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def builtin_discovery_candidates() -> list[dict[str, object]]:
    return [
        {
            "id": "falsiflow_neural_interface_conductive_hydrogel",
            "name": "Neural-interface conductive hydrogel baseline",
            "lane": "neural-interface-material",
            "status": "seed_candidate",
            "why_it_matters": "A hydrated soft interface can be useful only if medium stability, electrical benefit, and cell/network response are all checked separately.",
            "near_term_test": "Run H-A acellular stability before any H-B electrical or H-C cell/network expansion.",
            "known_risks": ["extractables", "swelling", "delamination", "network response worse than control"],
            "evidence_refs": ["seed_neural_interface_review"],
            "scores": {"evidence_fit": 4, "measurement_accessibility": 4, "risk_control": 3},
        }
    ]


def builtin_evidence_lookup() -> dict[str, dict[str, object]]:
    return {
        "seed_neural_interface_review": {
            "id": "seed_neural_interface_review",
            "source_url": "manual-seed",
        }
    }


def discovery_candidate_score(record: dict[str, object]) -> float:
    scores = record.get("scores", {})
    if not isinstance(scores, dict) or not scores:
        return 3.0
    values = []
    for value in scores.values():
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            pass
    return round(sum(values) / len(values), 3) if values else 3.0


def discovery_matches_goal(record: dict[str, object], goal: str) -> bool:
    goal_tokens = {token for token in re.split(r"[^a-z0-9]+", goal.lower()) if len(token) > 2}
    if not goal_tokens:
        return True
    haystack = " ".join(str(record.get(key, "")) for key in ["id", "name", "lane", "why_it_matters", "near_term_test"]).lower()
    return any(token in haystack for token in goal_tokens)


def recommended_gates_for_candidate(record: dict[str, object], goal: str) -> list[dict[str, object]]:
    text = f"{goal} {record.get('lane', '')} {record.get('name', '')}".lower()
    if any(token in text for token in ["neural", "mea", "wetware", "hydrogel", "pedot", "cell"]):
        return [
            {
                "id": "h_a_medium_stability",
                "purpose": "Rule out medium chemistry and physical instability before live-cell claims.",
                "required_evidence": ["ph_initial", "ph_final", "osmolality_initial_mosm", "osmolality_final_mosm", "visible_debris_present"],
                "acceptance_hint": "pH/osmolality drift and visible debris stay inside the configured stability window.",
            },
            {
                "id": "h_b_electrical_interface",
                "purpose": "Check whether the material improves an inspectable electrical interface readout.",
                "required_evidence": ["impedance_1khz_control_ohm", "impedance_1khz_candidate_ohm", "charge_storage_control_mC_cm2", "charge_storage_candidate_mC_cm2"],
                "acceptance_hint": "Candidate improves impedance and charge-storage proxies without adding blocking noise or delamination.",
            },
            {
                "id": "h_c_network_response",
                "purpose": "Only after H-A/H-B, check cell health and network response against a matched control.",
                "required_evidence": ["viability_pct", "burst_rate_hz", "inflammation_marker"],
                "acceptance_hint": "Viability remains acceptable and network/inflammation readouts are not materially worse than control.",
            },
        ]
    return [
        {
            "id": "source_backed_claim",
            "purpose": "Require source-backed evidence before promoting the research claim.",
            "required_evidence": ["measured_value", "source_file_present", "operator_or_agent"],
            "acceptance_hint": "All required rows have non-placeholder values and raw source files.",
        },
        {
            "id": "near_term_validation",
            "purpose": "Convert the candidate into a small, falsifiable near-term test.",
            "required_evidence": ["primary_readout", "control_readout", "failure_mode"],
            "acceptance_hint": "Primary readout beats the control without an unresolved failure mode.",
        },
    ]


def candidate_recipe(record: dict[str, object], goal: str) -> dict[str, object]:
    name = str(record.get("name") or record.get("id") or "Discovery candidate")
    risks = record.get("known_risks", [])
    if not isinstance(risks, list):
        risks = [str(risks)]
    return {
        "id": str(record.get("id") or discovery_slug(name)),
        "name": name,
        "domain": str(record.get("lane") or "custom-rd"),
        "status": str(record.get("status") or "candidate_proposed"),
        "material_stack": record.get("material_stack") if isinstance(record.get("material_stack"), list) else [
            {"layer": "candidate", "material": name, "function": "Research target to be falsified by source-backed gates."}
        ],
        "expected_mechanism": str(record.get("why_it_matters") or "Mechanism requires evidence extraction before any claim can be promoted."),
        "known_risks": [str(risk) for risk in risks],
        "near_term_test": str(record.get("near_term_test") or "Define the smallest source-backed experiment that can falsify the candidate."),
        "kill_criteria": [f"Kill or hold if unresolved risk remains: {risk}" for risk in risks] or ["Kill or hold if required source-backed evidence is missing."],
        "recommended_gates": recommended_gates_for_candidate(record, goal),
        "evidence_refs": [str(ref) for ref in record.get("evidence_refs", [])] if isinstance(record.get("evidence_refs", []), list) else [],
        "score": discovery_candidate_score(record),
    }


def discovery_evidence_records(candidates: list[dict[str, object]], goal: str) -> list[dict[str, object]]:
    seed = load_discovery_json(ROOT / "data" / "evidence_records_seed.json", [])
    known = builtin_evidence_lookup()
    if isinstance(seed, list):
        for item in seed:
            if isinstance(item, dict) and item.get("id"):
                known[str(item["id"])] = item
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for candidate in candidates:
        refs = candidate.get("evidence_refs", [])
        if not isinstance(refs, list):
            continue
        for ref in refs:
            ref_id = str(ref)
            if ref_id in seen:
                continue
            seen.add(ref_id)
            source = known.get(ref_id, {"id": ref_id, "source_url": ""})
            records.append({
                "id": ref_id,
                "claim": f"Evidence signal relevant to: {goal}",
                "material": str(candidate.get("name", "")),
                "mechanism": str(candidate.get("why_it_matters", "")),
                "assay": "literature_or_manual_seed",
                "readout": "candidate_rationale",
                "outcome": str(candidate.get("near_term_test", "")),
                "caveat": "Discovery evidence proposes candidates only; it cannot make a Falsiflow claim ready.",
                "source_url": str(source.get("source_url", "")),
            })
    return records


def discovery_project_draft(recipe: dict[str, object]) -> dict[str, object]:
    candidate_id = discovery_slug(str(recipe.get("id") or recipe.get("name", "candidate")))
    gates = []
    for gate in recipe.get("recommended_gates", []):
        if not isinstance(gate, dict):
            continue
        fields = [str(field) for field in gate.get("required_evidence", [])] if isinstance(gate.get("required_evidence", []), list) else ["measured_value"]
        gates.append({
            "id": str(gate.get("id", "discovery_gate")),
            "title": str(gate.get("purpose", "Discovery gate")),
            "samples": [{"candidate_id": candidate_id, "sample_id": "sample_001"}],
            "required_fields": fields,
            "acceptance_rules": [
                {
                    "field": fields[0],
                    "operator": "!=",
                    "value": "record_actual",
                    "reason": str(gate.get("acceptance_hint", "Replace placeholder evidence before claiming readiness.")),
                }
            ],
        })
    return {
        "project": {
            "id": f"{candidate_id}_discovery_project",
            "name": f"{recipe.get('name', 'Candidate')} discovery draft",
            "domain": str(recipe.get("domain", "custom-rd")),
            "version": "0.1.0",
        },
        "claim": {
            "id": f"{candidate_id}_claim",
            "statement": f"{recipe.get('name', 'Candidate')} has enough source-backed evidence to advance.",
            "requires_gates": [str(gate.get("id")) for gate in gates],
        },
        "evidence_policy": {
            "require_source_files": True,
            "reject_placeholder_values": True,
            "allowed_source_roots": ["source_files"],
            "required_metadata_fields": ["source_file", "measured_at", "operator_or_agent"],
            "placeholder_markers": ["record_actual", "raw_file_needed", "not_measured"],
        },
        "gates": gates,
    }


def discovery_evidence_template(project: dict[str, object]) -> str:
    rows = [",".join(EVIDENCE_COLUMNS)]
    for gate in project.get("gates", []):
        if not isinstance(gate, dict):
            continue
        samples = gate.get("samples", [])
        sample = samples[0] if isinstance(samples, list) and samples and isinstance(samples[0], dict) else {"candidate_id": "candidate", "sample_id": "sample_001"}
        fields = gate.get("required_fields", [])
        if not isinstance(fields, list):
            continue
        for field in fields:
            rows.append(",".join([
                str(gate.get("id", "")),
                str(sample.get("candidate_id", "")),
                str(sample.get("sample_id", "")),
                str(field),
                "record_actual",
                "source_files/raw_export.csv",
                "record_actual",
                "record_actual",
                "",
                "Discovery placeholder; replace with measured source-backed evidence.",
            ]))
    return "\n".join(rows) + "\n"


def render_discovery_ranking(summary: dict[str, object], candidates: list[dict[str, object]]) -> str:
    lines = [
        "# Falsiflow Discovery Ranking",
        "",
        f"- Goal: {summary.get('goal', '')}",
        f"- AI used: `{str(bool(summary.get('ai_used'))).lower()}`",
        f"- Claim ready: `{str(bool(summary.get('claim_ready'))).lower()}`",
        "",
        "This is a candidate-generation artifact. It does not create material suitability evidence or make any claim ready.",
        "",
        "| Rank | Score | Candidate | Status | Near-term test |",
        "| ---: | ---: | --- | --- | --- |",
    ]
    for index, item in enumerate(candidates, start=1):
        lines.append(
            "| "
            + " | ".join([
                str(index),
                f"{float(item.get('score', 0.0)):.3f}",
                f"`{markdown_cell(item.get('id', ''))}`",
                markdown_cell(item.get("status", "")),
                markdown_cell(item.get("near_term_test", "")),
            ])
            + " |"
        )
    return "\n".join(lines) + "\n"


def render_discovery_assay_plan(recipe: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Discovery Assay Plan",
        "",
        f"- Candidate: `{recipe.get('id', '')}`",
        f"- Name: {recipe.get('name', '')}",
        f"- Boundary: candidate proposal only; run Falsiflow evidence gates before any claim is ready.",
        "",
        "## Recommended Gates",
        "",
    ]
    for gate in recipe.get("recommended_gates", []):
        if not isinstance(gate, dict):
            continue
        fields = ", ".join(str(field) for field in gate.get("required_evidence", [])) if isinstance(gate.get("required_evidence", []), list) else ""
        lines.extend([
            f"### {gate.get('id', '')}",
            "",
            f"- Purpose: {gate.get('purpose', '')}",
            f"- Required evidence: {fields}",
            f"- Acceptance hint: {gate.get('acceptance_hint', '')}",
            "",
        ])
    lines.extend(["## Kill Criteria", ""])
    lines.extend(f"- {item}" for item in recipe.get("kill_criteria", []))
    return "\n".join(lines) + "\n"


def run_discover(goal: str, out_dir: Path, force: bool = False) -> dict[str, object]:
    prepare_output_directory(out_dir, "discovery output directory", force=force)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = load_discovery_json(ROOT / "data" / "limina_discovery_candidates.json", builtin_discovery_candidates())
    records = raw if isinstance(raw, list) else builtin_discovery_candidates()
    matching = [record for record in records if isinstance(record, dict) and discovery_matches_goal(record, goal)]
    if not matching:
        matching = [record for record in records if isinstance(record, dict)]
    recipes = sorted((candidate_recipe(record, goal) for record in matching), key=lambda item: float(item.get("score", 0)), reverse=True)
    top = recipes[0] if recipes else candidate_recipe(builtin_discovery_candidates()[0], goal)
    evidence_records = discovery_evidence_records(recipes, goal)
    project = discovery_project_draft(top)
    outputs = {
        "summary": str(out_dir / "discover_summary.json"),
        "evidence_records": str(out_dir / "evidence_records.json"),
        "candidate_queue": str(out_dir / "candidate_queue.json"),
        "ranking": str(out_dir / "ranking.md"),
        "assay_plan": str(out_dir / "assay_plan.md"),
        "rfq_package": str(out_dir / "rfq_package.md"),
        "project_draft": str(out_dir / "project_draft" / "project.json"),
        "evidence_template": str(out_dir / "project_draft" / "evidence_template.csv"),
    }
    summary: dict[str, object] = {
        "status": "discovery_ready",
        "goal": goal,
        "ai_used": False,
        "claim_ready": False,
        "boundary": "Discovery proposes candidates and gates only; Falsiflow Core must still audit source-backed evidence.",
        "top_candidate": str(top.get("id", "")),
        "candidate_count": len(recipes),
        "evidence_record_count": len(evidence_records),
        "outputs": outputs,
        "next_commands": [
            f"falsiflow doctor --config {out_dir / 'project_draft' / 'project.json'} --evidence {out_dir / 'project_draft' / 'evidence_template.csv'} --out-dir {out_dir / 'project_draft' / 'doctor'} --strict",
            f"falsiflow claim-check --config {out_dir / 'project_draft' / 'project.json'} --evidence {out_dir / 'project_draft' / 'evidence_template.csv'} --out-dir {out_dir / 'project_draft' / 'claim_check'} --strict",
        ],
    }
    (out_dir / "evidence_records.json").write_text(json.dumps(evidence_records, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "candidate_queue.json").write_text(json.dumps(recipes, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "ranking.md").write_text(render_discovery_ranking(summary, recipes), encoding="utf-8")
    (out_dir / "assay_plan.md").write_text(render_discovery_assay_plan(top), encoding="utf-8")
    (out_dir / "rfq_package.md").write_text(render_discovery_assay_plan(top).replace("Assay Plan", "RFQ Package"), encoding="utf-8")
    draft_dir = out_dir / "project_draft"
    (draft_dir / "source_files").mkdir(parents=True, exist_ok=True)
    (draft_dir / "project.json").write_text(json.dumps(project, indent=2, sort_keys=True), encoding="utf-8")
    (draft_dir / "evidence_template.csv").write_text(discovery_evidence_template(project), encoding="utf-8")
    (out_dir / "discover_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def cmd_discover(args: argparse.Namespace) -> int:
    summary = run_discover(args.goal, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow discover: {summary['status']}")
        print(f"Goal: {summary['goal']}")
        print(f"Top candidate: {summary['top_candidate']}")
        print(f"AI used: {str(bool(summary['ai_used'])).lower()}")
        print(f"Claim ready: {str(bool(summary['claim_ready'])).lower()}")
        print(f"Wrote {summary['outputs']['summary']}")
        print(f"Wrote {summary['outputs']['candidate_queue']}")
        print(f"Wrote {summary['outputs']['project_draft']}")
    return 0


def cmd_agent_discover(args: argparse.Namespace) -> int:
    summary = run_discover(args.goal, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow agent discover: {summary['status']}")
        print("Agent boundary: structured candidate proposal only; Core still decides claim readiness.")
        print(f"Goal: {summary['goal']}")
        print(f"Top candidate: {summary['top_candidate']}")
        print(f"AI used: {str(bool(summary['ai_used'])).lower()}")
        print(f"Claim ready: {str(bool(summary['claim_ready'])).lower()}")
        print(f"Wrote {summary['outputs']['summary']}")
        print(f"Wrote {summary['outputs']['candidate_queue']}")
        print(f"Wrote {summary['outputs']['project_draft']}")
    return 0


def cmd_candidate_rank(args: argparse.Namespace) -> int:
    summary = run_discover(args.goal, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow candidate rank: {summary['status']}")
        print(f"Goal: {summary['goal']}")
        print(f"Top candidate: {summary['top_candidate']}")
        print(f"Candidate count: {summary['candidate_count']}")
        print(f"Claim ready: {str(bool(summary['claim_ready'])).lower()}")
        print(f"Wrote {summary['outputs']['candidate_queue']}")
        print(f"Wrote {summary['outputs']['ranking']}")
    return 0


def cmd_assay_plan(args: argparse.Namespace) -> int:
    summary = run_discover(args.goal, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow assay-plan: {summary['status']}")
        print(f"Goal: {summary['goal']}")
        print(f"Top candidate: {summary['top_candidate']}")
        print("Boundary: assay/RFQ drafts still require measured source-backed evidence.")
        print(f"Wrote {summary['outputs']['assay_plan']}")
        print(f"Wrote {summary['outputs']['rfq_package']}")
        print(f"Wrote {summary['outputs']['project_draft']}")
    return 0


class FalsiflowHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def falsiflow_out_dir(self) -> Path:
        return Path(str(getattr(self.server, "falsiflow_out_dir", ".")))

    def send_json(self, payload: dict[str, object], status: int = 200) -> None:
        data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json_payload(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > 20_000_000:
            raise SystemExit("Workbench upload is too large for the local API limit.")
        raw = self.rfile.read(length)
        loaded = json.loads(raw.decode("utf-8"))
        if not isinstance(loaded, dict):
            raise SystemExit("Workbench payload must be a JSON object.")
        return loaded

    def do_GET(self) -> None:
        request_path = urllib.parse.urlparse(self.path).path
        if request_path == "/api/templates":
            self.send_json({"status": "templates_ready", "templates": template_records(include_env=False)})
            return
        if request_path == "/api/workbench/state":
            summary_path = self.falsiflow_out_dir() / "workbench_summary.json"
            if summary_path.exists():
                self.send_json(read_json_object(summary_path, "workbench summary"))
            else:
                self.send_json({"status": "workbench_not_run", "links": {}})
            return
        return super().do_GET()

    def do_POST(self) -> None:
        request_path = urllib.parse.urlparse(self.path).path
        if request_path != "/api/workbench/check":
            self.send_json({"status": "not_found", "message": "Unknown local API endpoint."}, status=404)
            return
        try:
            summary = run_workbench_check(self.falsiflow_out_dir(), self.read_json_payload())
            self.send_json(summary)
        except SystemExit as exc:
            self.send_json({"status": "workbench_blocked", "message": str(exc), "failure_count": 1, "failures": [{"stage": "workbench", "id": "request_failed", "message": str(exc)}]}, status=400)
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary.
            self.send_json({"status": "workbench_blocked", "message": str(exc), "failure_count": 1, "failures": [{"stage": "workbench", "id": "unexpected_error", "message": str(exc)}]}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        return


def ensure_try_output(template: str, out_dir: Path, template_roots: list[Path] | None, force: bool, include_env: bool = True) -> dict[str, object]:
    launchpad = out_dir / "index.html"
    try_report = out_dir / "try_report.html"
    try_summary_path = out_dir / "try_summary.json"
    if force or not try_report.exists():
        if out_dir.exists() and any(out_dir.iterdir()) and not force:
            raise SystemExit(f"Refusing to replace non-empty serve output directory without --force: {out_dir}")
        return run_try(template, out_dir, template_roots=template_roots, force=force, include_env=include_env)
    if try_summary_path.exists():
        try:
            summary = read_json_object(try_summary_path, "try summary")
            if isinstance(summary, dict):
                return refresh_try_browser_assets(out_dir, summary)
        except SystemExit:
            pass
    summary = {
        "status": "try_ready",
        "template": template,
        "out_dir": str(out_dir),
        "outputs": {
            "try_summary": str(try_summary_path),
            "launchpad": str(launchpad),
            "try_report": str(try_report),
            "wizard": str(out_dir / "falsiflow_wizard.html"),
        },
    }
    return refresh_try_browser_assets(out_dir, summary)


def local_url(host: str, port: int, path: str) -> str:
    display_host = "127.0.0.1" if host in {"", "0.0.0.0", "::"} else host
    quoted_path = urllib.parse.quote(path.lstrip("/"), safe="/#?=&%:;,+")
    return f"http://{display_host}:{port}/{quoted_path}"


def serve_summary(out_dir: Path, try_summary: dict[str, object], host: str, port: int, check_status: str = "not_run", status_code: int = 0, entry_command: str = "serve") -> dict[str, object]:
    outputs = try_summary.get("outputs", {}) if isinstance(try_summary.get("outputs"), dict) else {}
    url = local_url(host, port, "index.html")
    reopen_command = f"falsiflow start --out-dir {out_dir}" if entry_command == "start" else f"falsiflow try --out-dir {out_dir} --force --open"
    summary: dict[str, object] = {
        "status": "serve_ready" if check_status != "http_blocked" else "serve_blocked",
        "entry_command": entry_command,
        "url": url,
        "launchpad_url": url,
        "workbench_url": local_url(host, port, "workbench.html"),
        "try_report_url": local_url(host, port, "try_report.html"),
        "wizard_url": local_url(host, port, "falsiflow_wizard.html"),
        "host": host,
        "port": port,
        "out_dir": str(out_dir),
        "try_status": str(try_summary.get("status", "")),
        "launchpad": str(outputs.get("launchpad", out_dir / "index.html")),
        "workbench": str(outputs.get("workbench", out_dir / "workbench.html")),
        "try_report": str(outputs.get("try_report", out_dir / "try_report.html")),
        "wizard": str(outputs.get("wizard", out_dir / "falsiflow_wizard.html")),
        "dashboard": str(outputs.get("dashboard", "")),
        "check_status": check_status,
        "status_code": status_code,
        "next_commands": [
            f"open {url}",
            reopen_command,
            f"open {local_url(host, port, 'workbench.html')}",
            f"falsiflow wizard --out {out_dir / 'falsiflow_wizard.html'} --open",
        ],
    }
    (out_dir / "serve_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def make_httpd(out_dir: Path, host: str, port: int) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(FalsiflowHTTPRequestHandler, directory=str(out_dir.resolve()))
    httpd = http.server.ThreadingHTTPServer((host, port), handler)
    httpd.falsiflow_out_dir = out_dir
    return httpd


def cmd_serve(args: argparse.Namespace) -> int:
    entry_command = str(getattr(args, "entry_command", "serve"))
    try_summary = ensure_try_output(args.template, args.out_dir, args.template_root, force=args.force)
    httpd = make_httpd(args.out_dir, args.host, args.port)
    actual_port = int(httpd.server_address[1])
    summary = serve_summary(args.out_dir, try_summary, args.host, actual_port, entry_command=entry_command)
    url = str(summary["url"])

    if args.check:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        status_code = 0
        check_status = "http_blocked"
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                status_code = int(getattr(response, "status", 0) or response.getcode())
                body = response.read(4096).decode("utf-8", errors="replace")
            check_status = "http_ready" if status_code == 200 and "Falsiflow Launchpad" in body else "http_blocked"
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)
        summary = serve_summary(args.out_dir, try_summary, args.host, actual_port, check_status=check_status, status_code=status_code, entry_command=entry_command)
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(f"Falsiflow {entry_command}: {summary['status']}")
            print(f"URL: {summary['url']}")
            print(f"HTTP check: {summary['check_status']} {summary['status_code']}")
            print(f"Wrote {args.out_dir / 'serve_summary.json'}")
        return 0 if summary["status"] == "serve_ready" else 2

    if args.open:
        webbrowser.open(url)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    else:
        print(f"Falsiflow {entry_command}: serving")
        print(f"URL: {url}")
        print(f"Directory: {args.out_dir}")
        print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    args.entry_command = "start"
    args.force = bool(args.reset)
    args.open = not bool(args.no_open)
    return cmd_serve(args)


def onboard_summary(out_dir: Path, start_summary: dict[str, object]) -> dict[str, object]:
    return {
        "status": "onboard_ready" if start_summary.get("status") == "serve_ready" else "onboard_blocked",
        "out_dir": str(out_dir),
        "start_status": str(start_summary.get("status", "")),
        "launchpad_url": str(start_summary.get("launchpad_url", start_summary.get("url", ""))),
        "try_report_url": str(start_summary.get("try_report_url", "")),
        "wizard_url": str(start_summary.get("wizard_url", "")),
        "local_only": True,
        "steps": [
            {
                "step": 1,
                "title": "Open the local app",
                "action": str(start_summary.get("url", "")),
            },
            {
                "step": 2,
                "title": "Review the example decision",
                "action": "Open report from the launchpad.",
            },
            {
                "step": 3,
                "title": "Create your own evidence checklist",
                "action": "Open wizard and choose a plain-language preset.",
            },
            {
                "step": 4,
                "title": "Bring real evidence",
                "action": "Fill the downloaded evidence CSV and keep source files beside it.",
            },
        ],
        "next_commands": [
            f"falsiflow start --out-dir {out_dir}",
            f"falsiflow wizard --out {out_dir / 'falsiflow_wizard.html'} --open",
            f"falsiflow doctor --project-dir {out_dir / 'project'} --strict",
        ],
        "start_summary": start_summary,
    }


def cmd_onboard(args: argparse.Namespace) -> int:
    try_summary = ensure_try_output(args.template, args.out_dir, args.template_root, force=bool(args.reset))
    httpd = make_httpd(args.out_dir, args.host, args.port)
    actual_port = int(httpd.server_address[1])
    start_summary = serve_summary(args.out_dir, try_summary, args.host, actual_port, entry_command="start")
    summary = onboard_summary(args.out_dir, start_summary)
    summary_path = args.out_dir / "onboard_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    if args.check:
        url = str(start_summary["url"])
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        status_code = 0
        check_status = "http_blocked"
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                status_code = int(getattr(response, "status", 0) or response.getcode())
                body = response.read(4096).decode("utf-8", errors="replace")
            check_status = "http_ready" if status_code == 200 and "Falsiflow Launchpad" in body else "http_blocked"
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)
        start_summary = serve_summary(
            args.out_dir,
            try_summary,
            args.host,
            actual_port,
            check_status=check_status,
            status_code=status_code,
            entry_command="start",
        )
        summary = onboard_summary(args.out_dir, start_summary)
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(f"Falsiflow onboard: {summary['status']}")
            print(f"Local app: {summary['launchpad_url']}")
            print(f"HTTP check: {start_summary['check_status']} {start_summary['status_code']}")
            print(f"Wrote {summary_path}")
        return 0 if summary["status"] == "onboard_ready" else 2

    if not args.no_open:
        webbrowser.open(str(summary["launchpad_url"]))
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    else:
        print("Falsiflow onboard: serving")
        print(f"Local app: {summary['launchpad_url']}")
        print(f"Report: {summary['try_report_url']}")
        print(f"Wizard: {summary['wizard_url']}")
        print(f"Wrote {summary_path}")
        print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


def cmd_static_demo(args: argparse.Namespace) -> int:
    summary = run_try(args.template, args.out_dir, args.template_root, force=args.force)
    outputs = summary.get("outputs", {}) if isinstance(summary.get("outputs"), dict) else {}
    ready = summary.get("status") == "try_ready"
    static_summary = {
        "status": "static_demo_ready" if ready else "static_demo_blocked",
        "site_dir": str(args.out_dir),
        "index": str(outputs.get("launchpad", args.out_dir / "index.html")),
        "try_report": str(outputs.get("try_report", args.out_dir / "try_report.html")),
        "wizard": str(outputs.get("wizard", args.out_dir / "falsiflow_wizard.html")),
        "dashboard": str(outputs.get("dashboard", "")),
        "publishable": ready,
        "publish_note": "Host this directory with GitHub Pages, Netlify, or any static file server.",
        "try_summary": summary,
    }
    (args.out_dir / "static_demo_summary.json").write_text(json.dumps(static_summary, indent=2, sort_keys=True), encoding="utf-8")
    if args.open:
        webbrowser.open(Path(str(static_summary["index"])).resolve().as_uri())
    if args.json:
        print(json.dumps(static_summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow static-demo: {static_summary['status']}")
        print(f"Site: {static_summary['site_dir']}")
        print(f"Open: {static_summary['index']}")
        print("Host the directory with GitHub Pages, Netlify, or any static file server.")
    return 0 if static_summary["status"] == "static_demo_ready" else 2


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


def run_demo_package(template: str, out_dir: Path, template_roots: list[Path], force: bool = False) -> dict[str, object]:
    try_summary = run_try(template, out_dir, template_roots, force=force)
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


def cmd_demo_package(args: argparse.Namespace) -> int:
    summary = run_demo_package(args.template, args.out_dir, args.template_root, force=args.force)
    if args.open:
        webbrowser.open(Path(str(summary["local_preview"])).resolve().as_uri())
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow demo-package: {summary['status']}")
        print(f"Site: {summary['site_dir']}")
        print(f"Open: {summary['local_preview']}")
        print(f"Wrote {summary['outputs']['summary']}")
        print(f"Wrote {summary['outputs']['publish_checklist']}")
    return 0 if summary["status"] == "demo_package_ready" else 2


def render_publish_env_example(repo_url: str, public_demo_url: str) -> str:
    return "\n".join([
        "# Falsiflow public release readiness inputs.",
        "# Fill these with real hosted values after creating the repository and demo site.",
        f"FALSIFLOW_REPO_URL={repo_url}",
        f"FALSIFLOW_PUBLIC_DEMO_URL={public_demo_url}",
        "# Set to 1 only after the pipx smoke workflow or local pipx smoke passes.",
        "FALSIFLOW_PIPX_VALIDATED=0",
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
        "",
        f"FALSIFLOW_REPO_URL={repo_url} \\",
        f"FALSIFLOW_PUBLIC_DEMO_URL={public_demo_url or 'https://OWNER.github.io/falsiflow/'} \\",
        "FALSIFLOW_PIPX_VALIDATED=1 \\",
        "FALSIFLOW_WINDOWS_VALIDATED=1 \\",
        "falsiflow external-check --out-dir falsiflow_external_check --force --strict",
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
    for key in ["demo_package", "external_readiness", "env_example", "github_commands"]:
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
        "6. Publish a GitHub release only after `release-check` and `external-check --strict` pass.",
        "",
    ])
    if isinstance(blockers, list) and blockers:
        lines.extend(["## Current External Blockers", ""])
        for blocker in blockers:
            if isinstance(blocker, dict):
                lines.append(f"- `{blocker.get('check', '')}`: {blocker.get('message', '')}")
        lines.append("")
    return "\n".join(lines)


def run_publish_kit(out_dir: Path, template: str, template_roots: list[Path], repo_slug: str = "", public_demo_url: str = "", tag: str = "v0.1.0", force: bool = False) -> dict[str, object]:
    prepare_output_directory(out_dir, "publish-kit output directory", force=force)
    out_dir.mkdir(parents=True, exist_ok=True)
    repo_slug_value = repo_slug.strip()
    repo_url = f"https://github.com/{repo_slug_value}" if repo_slug_value else "https://github.com/OWNER/falsiflow"
    demo_url = public_demo_url.strip() or ("https://OWNER.github.io/falsiflow/" if not repo_slug_value else f"https://{repo_slug_value.split('/', 1)[0]}.github.io/{repo_slug_value.split('/', 1)[-1]}/")
    demo_package = run_demo_package(template, out_dir / "public_demo", template_roots, force=True)
    external = run_external_check(out_dir / "external_readiness", force=True)
    outputs = {
        "summary": str(out_dir / "publish_handoff.json"),
        "report": str(out_dir / "publish_handoff.md"),
        "demo_package": str(out_dir / "public_demo" / "demo_package_summary.json"),
        "external_readiness": str(out_dir / "external_readiness" / "external_readiness.json"),
        "env_example": str(out_dir / "publish.env.example"),
        "github_commands": str(out_dir / "github_publish_commands.sh"),
    }
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
        "boundary": "This kit prepares all local release handoff artifacts; GitHub authentication, repository creation, Pages deployment, workflow results, and PyPI publishing remain external account actions.",
        "outputs": outputs,
        "next_commands": [
            f"bash {out_dir / 'github_publish_commands.sh'}",
            f"FALSIFLOW_REPO_URL={repo_url} FALSIFLOW_PUBLIC_DEMO_URL={demo_url} FALSIFLOW_PIPX_VALIDATED=1 FALSIFLOW_WINDOWS_VALIDATED=1 falsiflow external-check --out-dir {out_dir / 'external_readiness_final'} --force --strict",
        ],
    }
    (out_dir / "publish.env.example").write_text(render_publish_env_example(repo_url, demo_url), encoding="utf-8")
    commands_path = out_dir / "github_publish_commands.sh"
    commands_path.write_text(render_github_publish_commands(repo_slug_value or "OWNER/falsiflow", tag, demo_url), encoding="utf-8")
    try:
        commands_path.chmod(0o755)
    except OSError:
        pass
    (out_dir / "publish_handoff.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "publish_handoff.md").write_text(render_publish_handoff(summary), encoding="utf-8")
    return summary


def cmd_publish_kit(args: argparse.Namespace) -> int:
    summary = run_publish_kit(
        args.out_dir,
        args.template,
        args.template_root,
        repo_slug=args.repo_slug,
        public_demo_url=args.public_demo_url,
        tag=args.tag,
        force=args.force,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow publish-kit: {summary['status']}")
        print(f"External readiness: {summary['external_status']}")
        print(f"Repository URL: {summary['repo_url']}")
        print(f"Public demo URL: {summary['public_demo_url']}")
        print(f"Wrote {summary['outputs']['summary']}")
        print(f"Wrote {summary['outputs']['report']}")
        print(f"Wrote {summary['outputs']['github_commands']}")
    return 0 if summary["status"] == "publish_kit_ready" else 2


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
        "| Check | Status | Message |",
        "| --- | --- | --- |",
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


def run_external_check(out_dir: Path, force: bool = False) -> dict[str, object]:
    prepare_output_directory(out_dir, "external-check output directory", force=force)
    out_dir.mkdir(parents=True, exist_ok=True)
    repo_url = os.environ.get("FALSIFLOW_REPO_URL", "").strip() or git_remote_url(ROOT)
    public_demo_url = os.environ.get("FALSIFLOW_PUBLIC_DEMO_URL", "").strip()
    pipx_path = shutil.which("pipx") or ""
    pipx_validated = bool(pipx_path) or truthy_env("FALSIFLOW_PIPX_VALIDATED")
    powershell_path = shutil.which("pwsh") or shutil.which("powershell") or ""
    windows_validated = sys.platform.startswith("win") or truthy_env("FALSIFLOW_WINDOWS_VALIDATED")
    pages_workflow = ROOT / ".github" / "workflows" / "falsiflow-pages.yml"
    cross_platform_workflow = ROOT / ".github" / "workflows" / "falsiflow-cross-platform.yml"
    publish_workflow = ROOT / ".github" / "workflows" / "falsiflow-publish.yml"
    checks = [
        external_check_item("git_available", shutil.which("git") is not None, "git is available for repository URL and release workflows.", shutil.which("git") or ""),
        external_check_item("public_repo_url", public_https_url(repo_url), "FALSIFLOW_REPO_URL or git remote is a public HTTPS repository URL.", repo_url),
        external_check_item("public_demo_url", public_https_url(public_demo_url), "FALSIFLOW_PUBLIC_DEMO_URL points to a hosted public static demo.", public_demo_url),
        external_check_item("pipx_available", pipx_validated, "pipx is available or FALSIFLOW_PIPX_VALIDATED records a passing pipx smoke test.", pipx_path or os.environ.get("FALSIFLOW_PIPX_VALIDATED", "")),
        external_check_item("powershell_available", bool(powershell_path) or windows_validated, "PowerShell is available here or Windows validation has been explicitly recorded.", powershell_path or os.environ.get("FALSIFLOW_WINDOWS_VALIDATED", "")),
        external_check_item("python_available", bool(sys.executable), "Python executable is available for local install and release checks.", sys.executable),
        external_check_item("demo_package_command", True, "`falsiflow demo-package` can prepare hostable static demo artifacts.", "falsiflow demo-package"),
        external_check_item("github_pages_workflow", workflow_contains(pages_workflow, ["demo-package", "upload-pages-artifact", "deploy-pages", "pages: write"]), "GitHub Pages workflow can build and deploy the static demo package.", str(pages_workflow)),
        external_check_item("cross_platform_workflow", workflow_contains(cross_platform_workflow, ["ubuntu-latest", "macos-latest", "windows-latest", "pipx", "install_local.ps1"]), "Cross-platform workflow covers Linux, macOS, Windows, pipx, and installers.", str(cross_platform_workflow)),
        external_check_item("pypi_publish_workflow", workflow_contains(publish_workflow, ["pypa/gh-action-pypi-publish", "twine check", "dist/*", "id-token: write"]), "PyPI publish workflow builds, checks, and can publish distributions with trusted publishing.", str(publish_workflow)),
    ]
    blockers = [check for check in checks if check.get("status") != "passed"]
    summary: dict[str, object] = {
        "status": "external_ready" if not blockers else "external_blocked",
        "check_count": len(checks),
        "ready_check_count": len(checks) - len(blockers),
        "blocker_count": len(blockers),
        "checks": checks,
        "blockers": blockers,
        "outputs": {
            "summary": str(out_dir / "external_readiness.json"),
            "report": str(out_dir / "external_readiness.md"),
        },
        "next_commands": [
            "falsiflow demo-package --out-dir falsiflow_public_demo --force",
            "FALSIFLOW_REPO_URL=https://github.com/<owner>/<repo> FALSIFLOW_PUBLIC_DEMO_URL=https://<host>/<demo> falsiflow external-check --out-dir falsiflow_external_check --force --strict",
        ],
    }
    (out_dir / "external_readiness.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "external_readiness.md").write_text(render_external_check_report(summary), encoding="utf-8")
    return summary


def cmd_external_check(args: argparse.Namespace) -> int:
    summary = run_external_check(args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow external-check: {summary['status']}")
        print(f"Checks: {summary['ready_check_count']}/{summary['check_count']}")
        print(f"Blockers: {summary['blocker_count']}")
        print(f"Wrote {summary['outputs']['summary']}")
        print(f"Wrote {summary['outputs']['report']}")
        for blocker in summary.get("blockers", []):
            if isinstance(blocker, dict):
                print(f"blocked: {blocker.get('check', '')}: {blocker.get('message', '')}")
    return 0 if summary["status"] == "external_ready" or not args.strict else 2


def default_project_evidence_path(project_dir: Path) -> Path:
    for name in ["evidence_pass_demo.csv", "evidence.csv", "evidence_template.csv"]:
        candidate = project_dir / name
        if candidate.exists():
            return candidate
    return project_dir / "evidence_pass_demo.csv"


def resolve_doctor_paths(args: argparse.Namespace) -> tuple[Path | None, Path, Path, Path]:
    project_dir = args.project_dir.expanduser() if getattr(args, "project_dir", None) is not None else None
    config = args.config.expanduser() if args.config is not None else None
    evidence = args.evidence.expanduser() if args.evidence is not None else None
    out_dir = args.out_dir.expanduser() if args.out_dir is not None else None

    if project_dir is not None:
        config = config or project_dir / "project.json"
        evidence = evidence or default_project_evidence_path(project_dir)
        out_dir = out_dir or project_dir / "doctor"

    missing = []
    if config is None:
        missing.append("--config or --project-dir")
    if evidence is None:
        missing.append("--evidence or --project-dir")
    if out_dir is None:
        missing.append("--out-dir or --project-dir")
    if missing:
        raise SystemExit("Missing required doctor path(s): " + ", ".join(missing))
    return project_dir, config, evidence, out_dir


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


def cmd_doctor(args: argparse.Namespace) -> int:
    project_dir, config, evidence, out_dir = resolve_doctor_paths(args)
    summary = run_doctor(project_dir, config, evidence, out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow doctor: {summary['status']}")
        print(f"Project: {summary['project_dir']}")
        print(f"Project config: {summary['project_status']}")
        print(f"Evidence: {summary['evidence_status']}")
        print(f"Claim check: {summary['claim_check_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Failures: {summary['failure_count']}")
        repair_checklist = summary.get("repair_checklist", [])
        if isinstance(repair_checklist, list) and repair_checklist:
            first_repair = repair_checklist[0]
            if isinstance(first_repair, dict):
                label = "Next review" if summary["status"] == "doctor_ready" else "First repair"
                print(f"{label}: {first_repair.get('action_id', '')}")
                print(f"Run: {first_repair.get('command', '')}")
        outputs = summary.get("outputs", {})
        if isinstance(outputs, dict):
            print(f"Wrote {outputs.get('doctor_summary', '')}")
            print(f"Wrote {outputs.get('doctor_report', '')}")
            print(f"Wrote {outputs.get('claim_check', '')}")
    return 0 if summary["status"] == "doctor_ready" or not args.strict else 2


def run_demo(template: str, out_dir: Path, force: bool = False) -> dict[str, object]:
    source = template_path(template)
    if source is None:
        raise SystemExit(f"Unknown template `{template}`. Run `falsiflow templates` to list available templates.")
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"Refusing to overwrite non-empty demo directory without --force: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    project_dir = out_dir / template
    shutil.copytree(source, project_dir)
    config_path = project_dir / "project.json"
    evidence_path = project_dir / "evidence_pass_demo.csv"
    validation_path = out_dir / "project_validation.json"
    audit_dir = out_dir / "audit"
    source_manifest_path = out_dir / "source_manifest.json"
    source_report_path = out_dir / "source_manifest.md"
    bundle_dir = out_dir / "evidence_bundle"
    bundle_zip = out_dir / "evidence_bundle.zip"
    verification_json = out_dir / "evidence_bundle_verify.json"
    verification_report = out_dir / "evidence_bundle_verify.md"

    steps: list[dict[str, object]] = []
    project = load_project(config_path)
    validation = validate_project_config(project)
    validation_path.write_text(json.dumps(validation, indent=2, sort_keys=True), encoding="utf-8")
    steps.append({"step": "validate", "status": validation.get("status", ""), "path": str(validation_path)})

    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(evidence_path)
    rendered = write_render_artifacts(project, evidence_rows, audit_dir, evidence_file_issues=evidence_issues)
    audit = rendered["audit"]
    steps.append({"step": "audit", "status": audit.get("status", ""), "path": str(audit_dir / "claim_audit.json")})

    manifest = source_manifest(project, evidence_rows, evidence_issues)
    source_manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    source_report_path.write_text(render_source_manifest_report(manifest), encoding="utf-8")
    steps.append({"step": "sources", "status": manifest.get("status", ""), "path": str(source_manifest_path)})

    bundle = build_bundle(config_path, evidence_path, bundle_dir, bundle_zip, force=True)
    steps.append({"step": "bundle", "status": bundle.get("status", ""), "path": str(bundle_dir / "bundle_manifest.json")})

    verification = verify_bundle_zip(bundle_zip)
    verification_json.write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")
    verification_report.write_text(render_bundle_verification_report(verification), encoding="utf-8")
    steps.append({"step": "verify-bundle", "status": verification.get("status", ""), "path": str(verification_json)})

    demo_ready = (
        validation.get("valid") is True
        and audit.get("claim_ready") is True
        and manifest.get("status") == "sources_ready"
        and bundle.get("status") == "bundle_ready"
        and verification.get("status") == "bundle_verified"
    )
    summary: dict[str, object] = {
        "status": "demo_ready" if demo_ready else "demo_blocked",
        "template": template,
        "artifact_root": str(out_dir),
        "project_dir": str(project_dir),
        "validation_status": validation.get("status", ""),
        "audit_status": audit.get("status", ""),
        "claim_ready": bool(audit.get("claim_ready")),
        "source_status": manifest.get("status", ""),
        "bundle_status": bundle.get("status", ""),
        "verification_status": verification.get("status", ""),
        "issue_count": int(validation.get("error_count", 0))
        + int(audit.get("evidence_error_count", 0))
        + int(manifest.get("blocker_count", 0))
        + int(verification.get("issue_count", 0)),
        "steps": steps,
        "project_validation": str(validation_path),
        "claim_audit": str(audit_dir / "claim_audit.json"),
        "source_manifest": str(source_manifest_path),
        "bundle_manifest": str(bundle_dir / "bundle_manifest.json"),
        "bundle_zip": str(bundle_zip),
        "bundle_verification": str(verification_json),
        "bundle_verification_report": str(verification_report),
    }
    (out_dir / "demo_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def cmd_demo(args: argparse.Namespace) -> int:
    summary = run_demo(args.template, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow demo: {summary['status']}")
        print(f"Template: {summary['template']}")
        print(f"Claim ready: {str(bool(summary['claim_ready'])).lower()}")
        print(f"Sources: {summary['source_status']}")
        print(f"Bundle: {summary['bundle_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Wrote {args.out_dir / 'demo_summary.json'}")
        print(f"Wrote {summary['bundle_zip']}")
        print(f"Wrote {summary['bundle_verification_report']}")
    return 0 if summary["status"] == "demo_ready" else 2


def cmd_next(args: argparse.Namespace) -> int:
    project = load_project(args.config)
    if args.evidence is not None and not args.evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {args.evidence}")
    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(args.evidence)
    rendered = write_render_artifacts(project, evidence_rows, args.out_dir, evidence_file_issues=evidence_issues)
    for action in rendered["audit"].get("next_actions", []):
        print(f"{action['rank']}. {action['action_id']}: {action['why']}")
    print(f"Wrote {args.out_dir / 'claim_audit.md'}")
    print(f"Wrote {args.out_dir / 'audit_review.md'}")
    print(f"Wrote {args.out_dir / 'claim_summary.json'}")
    print(f"Wrote {args.out_dir / 'next_actions.json'}")
    print(f"Wrote {args.out_dir / 'dashboard.html'}")
    return 0


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def source_manifest(project: dict[str, object], evidence_rows: list[dict[str, str]], evidence_issues: list[dict[str, object]]) -> dict[str, object]:
    policy = project.get("evidence_policy", {})
    policy = policy if isinstance(policy, dict) else {}
    require_sources = bool(policy.get("require_source_files", True))
    roots = allowed_roots(project)
    base_dir = source_file_base_dir(project)
    source_records: dict[str, dict[str, object]] = {}
    blank_source_rows: list[dict[str, object]] = []

    for row_number, row in enumerate(evidence_rows, start=2):
        source_file = str(row.get("source_file", "") or "").strip()
        reference = {
            "row_number": row_number,
            "gate_id": str(row.get("gate_id", "")),
            "candidate_id": str(row.get("candidate_id", "")),
            "sample_id": str(row.get("sample_id", "")),
            "field": str(row.get("field", "")),
        }
        if not source_file:
            blank_source_rows.append(reference)
            continue
        record = source_records.setdefault(source_file, {
            "source_file": source_file,
            "reference_count": 0,
            "references": [],
        })
        record["reference_count"] = int(record["reference_count"]) + 1
        references = record["references"]
        if isinstance(references, list) and len(references) < 50:
            references.append(reference)

    source_files = []
    missing_count = 0
    outside_allowed_roots_count = 0
    present_count = 0
    for source_file, record in sorted(source_records.items()):
        resolved = resolve_source_file(project, source_file)
        exists = resolved.exists()
        within_allowed_roots = not roots or any(resolved == root or root in resolved.parents for root in roots)
        status = "present"
        issue = ""
        if not exists:
            status = "missing"
            issue = "source_file does not exist"
            missing_count += 1
        elif not within_allowed_roots:
            status = "outside_allowed_roots"
            issue = "source_file outside allowed roots"
            outside_allowed_roots_count += 1
        else:
            present_count += 1
        source_files.append({
            **record,
            "status": status,
            "exists": exists,
            "within_allowed_roots": within_allowed_roots,
            "resolved_path": str(resolved),
            "issue": issue,
        })

    evidence_file_error_count = sum(1 for issue in evidence_issues if issue.get("level") == "error")
    evidence_file_warning_count = sum(1 for issue in evidence_issues if issue.get("level") == "warning")
    source_blocker_count = (
        len(blank_source_rows) + missing_count + outside_allowed_roots_count
        if require_sources
        else 0
    )
    blocker_count = evidence_file_error_count + source_blocker_count

    return {
        "status": "sources_ready" if blocker_count == 0 else "sources_blocked",
        "project_id": str(project.get("project", {}).get("id", "")),
        "claim_id": str(project.get("claim", {}).get("id", "")),
        "source_policy_required": require_sources,
        "source_file_base_dir": str(base_dir),
        "allowed_source_roots": [str(root) for root in roots],
        "evidence_row_count": len(evidence_rows),
        "referenced_source_file_count": len(source_files),
        "present_source_file_count": present_count,
        "missing_source_file_count": missing_count,
        "outside_allowed_roots_count": outside_allowed_roots_count,
        "blank_source_row_count": len(blank_source_rows),
        "source_blocker_count": source_blocker_count,
        "evidence_file_issue_count": len(evidence_issues),
        "evidence_file_error_count": evidence_file_error_count,
        "evidence_file_warning_count": evidence_file_warning_count,
        "blocker_count": blocker_count,
        "blank_source_rows": blank_source_rows[:200],
        "source_files": source_files,
    }


def render_source_manifest_report(manifest: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Source Manifest",
        "",
        f"**Status:** `{manifest.get('status')}`",
        f"**Project:** `{manifest.get('project_id')}`",
        f"**Claim:** `{manifest.get('claim_id')}`",
        f"**Source policy required:** `{str(bool(manifest.get('source_policy_required'))).lower()}`",
        f"**Evidence rows:** {manifest.get('evidence_row_count', 0)}",
        f"**Referenced source files:** {manifest.get('referenced_source_file_count', 0)}",
        f"**Present:** {manifest.get('present_source_file_count', 0)}",
        f"**Missing:** {manifest.get('missing_source_file_count', 0)}",
        f"**Outside allowed roots:** {manifest.get('outside_allowed_roots_count', 0)}",
        f"**Blank source rows:** {manifest.get('blank_source_row_count', 0)}",
        f"**Evidence file errors / warnings:** {manifest.get('evidence_file_error_count', 0)} / {manifest.get('evidence_file_warning_count', 0)}",
        "",
        "## Source Files",
        "",
        "| Source file | Status | References | Resolved path | Issue |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for record in manifest.get("source_files", []):
        if not isinstance(record, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(record.get("source_file", "")),
                markdown_cell(record.get("status", "")),
                markdown_cell(record.get("reference_count", 0)),
                markdown_cell(record.get("resolved_path", "")),
                markdown_cell(record.get("issue", "")),
            ])
            + " |"
        )
    if manifest.get("blank_source_rows"):
        lines.extend([
            "",
            "## Blank Source Rows",
            "",
            "| Row | Gate | Candidate | Sample | Field |",
            "| ---: | --- | --- | --- | --- |",
        ])
        for row in manifest.get("blank_source_rows", []):
            if not isinstance(row, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(row.get("row_number", "")),
                    markdown_cell(row.get("gate_id", "")),
                    markdown_cell(row.get("candidate_id", "")),
                    markdown_cell(row.get("sample_id", "")),
                    markdown_cell(row.get("field", "")),
                ])
                + " |"
            )
    lines.append("")
    return "\n".join(lines)


def cmd_sources(args: argparse.Namespace) -> int:
    project = load_project(args.config)
    if not args.evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {args.evidence}")
    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(args.evidence)
    manifest = source_manifest(project, evidence_rows, evidence_issues)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if args.report_out is not None:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(render_source_manifest_report(manifest), encoding="utf-8")
    print(f"Falsiflow sources: {manifest['status']}")
    print(f"Referenced source files: {manifest['referenced_source_file_count']}")
    print(f"Present: {manifest['present_source_file_count']}")
    print(f"Missing: {manifest['missing_source_file_count']}")
    print(f"Outside allowed roots: {manifest['outside_allowed_roots_count']}")
    print(f"Blank source rows: {manifest['blank_source_row_count']}")
    print(f"Wrote {args.out}")
    if args.report_out is not None:
        print(f"Wrote {args.report_out}")
    return 0 if manifest["status"] == "sources_ready" or not args.strict else 2


def cmd_ingest_limina_source_values(args: argparse.Namespace) -> int:
    summary = write_limina_conversion(
        inputs=args.input,
        evidence_out=args.out,
        summary_out=args.summary_out,
        project_out=args.project_out,
        default_candidate=args.default_candidate,
        default_gate=args.default_gate,
        project_id=args.project_id,
        claim_id=args.claim_id,
        claim_statement=args.claim_statement,
        source_file_base_dir=args.source_file_base_dir,
        allowed_source_roots=args.allowed_source_root,
    )
    print(f"Falsiflow LIMINA ingest: {summary['status']}")
    print(f"Evidence rows: {summary['evidence_rows']}")
    print(f"Gates: {', '.join(summary['gates'])}")
    print(f"Wrote {args.out}")
    if args.project_out:
        print(f"Wrote {args.project_out}")
    if args.summary_out:
        print(f"Wrote {args.summary_out}")
    return 0


def key_record(key: tuple[str, str, str, str]) -> dict[str, str]:
    gate_id, candidate_id, sample_id, field = key
    return {
        "gate_id": gate_id,
        "candidate_id": candidate_id,
        "sample_id": sample_id,
        "field": field,
    }


def evidence_coverage_report(project: dict[str, object], evidence_rows: list[dict[str, str]]) -> dict[str, object]:
    required_keys = configured_evidence_keys(project)
    rows_by_key = evidence_rows_by_key(evidence_rows)
    imported_keys = set(rows_by_key)
    matched_keys = required_keys & imported_keys
    missing_keys = sorted(required_keys - imported_keys)
    extra_keys = sorted(imported_keys - required_keys)
    duplicate_configured_keys = sorted(key for key, rows in rows_by_key.items() if key in required_keys and len(rows) > 1)
    duplicate_extra_keys = sorted(key for key, rows in rows_by_key.items() if key not in required_keys and len(rows) > 1)

    gate_rows = []
    gate_ids = [str(gate.get("id", "")).strip() for gate in project.get("gates", []) if isinstance(gate, dict)]
    for gate_id in gate_ids:
        gate_required = {key for key in required_keys if key[0] == gate_id}
        gate_matched = gate_required & matched_keys
        gate_missing = sorted(gate_required - matched_keys)
        gate_rows.append({
            "gate_id": gate_id,
            "required_evidence_rows": len(gate_required),
            "matched_evidence_rows": len(gate_matched),
            "missing_evidence_rows": len(gate_missing),
            "completion_pct": round((len(gate_matched) / len(gate_required) * 100), 2) if gate_required else 0.0,
            "missing_keys": [key_record(key) for key in gate_missing[:50]],
        })

    blocked = bool(missing_keys or duplicate_configured_keys)
    return {
        "status": "coverage_blocked" if blocked else "coverage_ready",
        "project_id": str(project.get("project", {}).get("id", "")),
        "claim_id": str(project.get("claim", {}).get("id", "")),
        "required_evidence_rows": len(required_keys),
        "matched_evidence_rows": len(matched_keys),
        "missing_evidence_rows": len(missing_keys),
        "extra_evidence_rows": len(extra_keys),
        "duplicate_configured_keys": len(duplicate_configured_keys),
        "duplicate_extra_keys": len(duplicate_extra_keys),
        "completion_pct": round((len(matched_keys) / len(required_keys) * 100), 2) if required_keys else 0.0,
        "gates": gate_rows,
        "missing_keys": [key_record(key) for key in missing_keys[:200]],
        "extra_keys": [key_record(key) for key in extra_keys[:200]],
        "duplicate_configured": [key_record(key) for key in duplicate_configured_keys[:200]],
        "duplicate_extra": [key_record(key) for key in duplicate_extra_keys[:200]],
    }


def cmd_ingest_wide_csv(args: argparse.Namespace) -> int:
    summary = write_wide_lab_conversion(
        inputs=args.input,
        evidence_out=args.out,
        summary_out=args.summary_out,
        gate_id=args.gate_id,
        candidate_id=args.candidate_id,
        sample_id_column=args.sample_id_column,
        field_columns=args.field,
        exclude_columns=args.exclude_column,
        gate_id_column=args.gate_id_column,
        candidate_id_column=args.candidate_id_column,
        source_file=args.source_file,
        source_file_column=args.source_file_column,
        measured_at=args.measured_at,
        measured_at_column=args.measured_at_column,
        operator_or_agent=args.operator_or_agent,
        operator_or_agent_column=args.operator_or_agent_column,
        instrument_id=args.instrument_id,
        instrument_id_column=args.instrument_id_column,
        notes=args.notes,
        notes_column=args.notes_column,
    )
    if args.config is not None:
        project = load_project(args.config)
        evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(args.out)
        coverage = evidence_coverage_report(project, evidence_rows)
        coverage["evidence_file_issue_count"] = len(evidence_issues)
        coverage["evidence_file_error_count"] = sum(1 for issue in evidence_issues if issue.get("level") == "error")
        coverage["evidence_file_warning_count"] = sum(1 for issue in evidence_issues if issue.get("level") == "warning")
        summary["coverage"] = coverage
        if args.coverage_out is not None:
            args.coverage_out.parent.mkdir(parents=True, exist_ok=True)
            args.coverage_out.write_text(json.dumps(coverage, indent=2, sort_keys=True), encoding="utf-8")
        if args.summary_out is not None:
            args.summary_out.parent.mkdir(parents=True, exist_ok=True)
            args.summary_out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Falsiflow wide CSV ingest: {summary['status']}")
    print(f"Evidence rows: {summary['evidence_rows']}")
    print(f"Skipped rows: {summary['skipped_rows']}")
    print(f"Skipped blank values: {summary['skipped_values']}")
    print(f"Gates: {', '.join(summary['gates'])}")
    if "coverage" in summary:
        coverage = summary["coverage"]
        print(f"Coverage: {coverage['status']}")
        print(f"Matched: {coverage['matched_evidence_rows']} / {coverage['required_evidence_rows']}")
        print(f"Missing: {coverage['missing_evidence_rows']}")
        print(f"Extra: {coverage['extra_evidence_rows']}")
    print(f"Wrote {args.out}")
    if args.coverage_out:
        print(f"Wrote {args.coverage_out}")
    if args.summary_out:
        print(f"Wrote {args.summary_out}")
    if args.strict and summary.get("coverage", {}).get("status") == "coverage_blocked":
        return 2
    return 0


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


def cmd_templates(args: argparse.Namespace) -> int:
    records = template_records(args.template_root)
    if args.json:
        print(json.dumps(records, indent=2, sort_keys=True))
    else:
        for record in records:
            print(f"{record['template']}\t{record['status']}\t{record['domain']}\t{record['project_id']}")
    return 0


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


def template_gallery_summary(extra_roots: list[Path] | None = None, include_env: bool = True) -> dict[str, object]:
    records = template_records(extra_roots, include_env=include_env)
    issues: list[dict[str, str]] = []
    templates: list[dict[str, object]] = []
    roots = [str(root) for root in all_template_roots(extra_roots, include_env=include_env)]

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
) -> dict[str, object]:
    summary = template_gallery_summary(extra_roots, include_env=include_env)
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


def cmd_template_gallery(args: argparse.Namespace) -> int:
    summary = run_template_gallery(args.template_root, out=args.out, json_out=args.json_out)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-gallery: {summary['status']}")
        print(f"Templates: {summary['valid_template_count']}/{summary['template_count']}")
        print(f"Domains: {summary['domain_count']}")
        print(f"Non-neural templates: {summary['non_neural_template_count']}")
        print(f"Issues: {summary['issue_count']}")
        if args.out:
            print(f"Wrote {args.out}")
        if args.json_out:
            print(f"Wrote {args.json_out}")
    return 0 if summary["status"] == "template_gallery_ready" else 2


def cmd_schema(args: argparse.Namespace) -> int:
    schema = falsiflow_schema(args.kind)
    payload = json.dumps(schema, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(f"{payload}\n", encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(payload)
    return 0


def failure_record(stage: str, identifier: str, message: str) -> dict[str, str]:
    return {"stage": stage, "id": identifier, "message": message}


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
        f"- External readiness: `{summary.get('external_check_status', '')}`",
        f"- Failures: {summary.get('failure_count', 0)}",
        "",
        "## Adoption Priorities",
        "",
    ]
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


def release_check_item(check_id: str, ok: bool, message: str, path: Path | str = "") -> dict[str, str]:
    return {
        "check": check_id,
        "status": "passed" if ok else "failed",
        "message": message,
        "path": str(path),
    }


def adoption_priority(
    priority_id: str,
    title: str,
    checks: list[dict[str, str]],
    next_actions: list[str],
) -> dict[str, object]:
    passed = sum(1 for check in checks if check.get("status") == "passed")
    failed_checks = [str(check.get("check", "")) for check in checks if check.get("status") != "passed"]
    return {
        "priority_id": priority_id,
        "title": title,
        "status": "priority_ready" if passed == len(checks) else "priority_blocked",
        "check_count": len(checks),
        "passed_check_count": passed,
        "checks": checks,
        "next_actions": next_actions if failed_checks else [],
        "failed_checks": failed_checks,
    }


def package_check_lookup(package: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(check.get("check", "")): check
        for check in package.get("checks", [])
        if isinstance(check, dict) and check.get("check")
    }


def package_check_item(
    package_checks: dict[str, dict[str, object]],
    check_id: str,
    *,
    installed_mode: bool,
    installed_ok: bool = False,
) -> dict[str, str]:
    check = package_checks.get(check_id)
    if check is not None:
        return release_check_item(
            check_id,
            check.get("status") == "passed",
            str(check.get("message", "")),
            str(check.get("path", "")),
        )
    if installed_mode and installed_ok:
        return release_check_item(
            check_id,
            True,
            "Source documentation gate is covered by source release-check; installed package mode verifies runtime metadata and bundled templates.",
            ROOT,
        )
    return release_check_item(check_id, False, f"Package check `{check_id}` was not run.", ROOT)


def package_check_any_item(
    package_checks: dict[str, dict[str, object]],
    check_id: str,
    aliases: list[str],
    *,
    installed_mode: bool,
    installed_ok: bool = False,
) -> dict[str, str]:
    for alias in aliases:
        check = package_checks.get(alias)
        if check is not None:
            return release_check_item(
                check_id,
                check.get("status") == "passed",
                str(check.get("message", "")),
                str(check.get("path", "")),
            )
    if installed_mode and installed_ok:
        return release_check_item(
            check_id,
            True,
            "Source-tree package gate is covered before packaging; installed package mode verifies the nearest runtime equivalent.",
            ROOT,
        )
    return release_check_item(check_id, False, f"None of `{', '.join(aliases)}` ran.", ROOT)


def dist_check_item(
    dist_checks: dict[str, dict[str, object]],
    check_id: str,
    *,
    dist_status: str,
    dist_root: Path,
    skipped_ok: bool = False,
) -> dict[str, str]:
    check = dist_checks.get(check_id)
    if check is not None:
        return release_check_item(
            check_id,
            check.get("status") == "passed",
            str(check.get("message", "")),
            str(check.get("path", "")),
        )
    if skipped_ok and dist_status == "dist_skipped":
        return release_check_item(
            check_id,
            True,
            "Distribution hygiene is verified by full release-check; this fast or installed-package run skipped distribution checks.",
            dist_root,
        )
    return release_check_item(check_id, False, f"Distribution check `{check_id}` was not run.", dist_root)


def command_list_contains(commands: object, token: str) -> bool:
    return isinstance(commands, list) and any(token in str(command) for command in commands)


def release_validation_status_for_dist(dist_status: str) -> tuple[str, str]:
    if dist_status == "dist_ready":
        return "release_validation_ready", "Wheel, sdist, isolated install, and installed-package release checks completed."
    if dist_status == "dist_skipped":
        return "release_validation_skipped", "Distribution validation was skipped; run adoption-check or release-check without --skip-dist before treating the tree as publish-ready."
    return "release_validation_blocked", f"Distribution validation ended as {dist_status or 'unknown'}."


def adoption_release_validation_status(dist_status: str) -> tuple[str, str]:
    return release_validation_status_for_dist(dist_status)


def adoption_repair_checklist(
    priorities: list[dict[str, object]],
    artifact_root: Path,
    dist_status: str,
    adoption_rerun_root: Path | None = None,
) -> list[dict[str, object]]:
    blocked = [priority for priority in priorities if priority.get("status") != "priority_ready"]
    skip_dist_flag = " --skip-dist" if dist_status == "dist_skipped" else ""
    rerun_root = adoption_rerun_root or artifact_root

    def checklist_item(
        rank: int,
        priority: dict[str, object],
        action_id: str,
        why: str,
        command: str,
        expected_artifact: Path,
        success_signal: str,
    ) -> dict[str, object]:
        failed_checks = priority.get("failed_checks", [])
        return {
            "rank": rank,
            "priority_id": str(priority.get("priority_id", "")),
            "action_id": action_id,
            "failed_checks": [str(check) for check in failed_checks] if isinstance(failed_checks, list) else [],
            "why": why,
            "command": command,
            "expected_artifact": str(expected_artifact),
            "success_signal": success_signal,
        }

    if not blocked:
        return [{
            "rank": 1,
            "priority_id": "all_priorities",
            "action_id": "verify_adoption_ready",
            "failed_checks": [],
            "why": "All adoption priorities are ready; rerun this gate before release or after changing docs, templates, packaging, quickstart, doctor, or claim-check behavior.",
            "command": f"falsiflow adoption-check --out-dir {rerun_root}{skip_dist_flag} --force",
            "expected_artifact": str(rerun_root / "adoption_check.json"),
            "success_signal": "adoption_check.json reports adoption_ready with ready_priority_count equal to priority_count.",
        }]

    checklist: list[dict[str, object]] = []
    for index, priority in enumerate(blocked, start=1):
        priority_id = str(priority.get("priority_id", ""))
        if priority_id == "open_source_entry_point":
            checklist.append(checklist_item(
                index,
                priority,
                "repair_open_source_entry_point",
                "Repair README, examples, quickstart, or handoff checks until first-run users can start from one clear path.",
                f"falsiflow quickstart --template biointerface_coatings --out {artifact_root / 'quickstart_project'} --strict --force",
                artifact_root / "quickstart_project" / "quickstart_summary.json",
                "Quickstart reports quickstart_ready and next_commands starts with falsiflow doctor --project-dir.",
            ))
        elif priority_id == "trusted_audit_experience":
            checklist.append(checklist_item(
                index,
                priority,
                "repair_trusted_audit_experience",
                "Repair claim-check, doctor, audit-review, source, bundle, or verification blockers before treating claims as reviewable.",
                f"falsiflow doctor --project-dir {artifact_root / 'quickstart_project'} --out-dir {artifact_root / 'doctor'} --strict --force",
                artifact_root / "doctor" / "doctor_summary.json",
                "Doctor reports doctor_ready and its repair_checklist points to a claim-check artifact.",
            ))
        elif priority_id == "generality_proof":
            checklist.append(checklist_item(
                index,
                priority,
                "repair_generality_proof",
                "Repair starter templates or template-gallery coverage until Falsiflow visibly spans non-neural workflows.",
                f"falsiflow template-gallery --out {artifact_root / 'template_gallery.md'} --json-out {artifact_root / 'template_gallery.json'}",
                artifact_root / "template_gallery.json",
                "Template gallery reports template_gallery_ready with at least three non-neural templates and doctor handoffs.",
            ))
        elif priority_id == "release_and_distribution":
            checklist.append(checklist_item(
                index,
                priority,
                "repair_release_and_distribution",
                "Repair package metadata, distribution artifacts, or release docs before publishing.",
                f"falsiflow release-check --out-dir {artifact_root / 'release_check'} --force",
                artifact_root / "release_check" / "release_check.json",
                "Release check reports release_ready, package_ready, dist_ready, and adoption_check_status adoption_ready.",
            ))
        else:
            checklist.append(checklist_item(
                index,
                priority,
                "repair_user_experience_convergence",
                "Repair priority docs, adoption-check docs, quickstart handoff, doctor checklist, or claim-check next actions.",
                f"falsiflow adoption-check --out-dir {rerun_root}{skip_dist_flag} --force",
                rerun_root / "adoption_check.md",
                "Adoption report includes Falsiflow Adoption Check, Repair Checklist, and adoption_ready.",
            ))
    return checklist


def render_adoption_check_report(summary: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Adoption Check",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Priorities: {summary.get('ready_priority_count', 0)}/{summary.get('priority_count', 0)}",
        f"- Readiness: {summary.get('readiness_pct', 0)}%",
        f"- Release validation: `{summary.get('release_validation_status', '')}`",
        f"- Release validation note: {markdown_cell(summary.get('release_validation_message', ''))}",
        f"- Failures: {summary.get('failure_count', 0)}",
        "",
        "## Priorities",
        "",
        "| Priority | Status | Checks |",
        "| --- | --- | ---: |",
    ]
    for priority in summary.get("priorities", []):
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

    for priority in summary.get("priorities", []):
        if not isinstance(priority, dict):
            continue
        lines.extend(["", f"## {priority.get('title', '')}", ""])
        checks = priority.get("checks", [])
        if not checks:
            lines.append("No checks recorded.")
        else:
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
        next_actions = priority.get("next_actions", [])
        if isinstance(next_actions, list) and next_actions:
            lines.extend(["", "Next actions:"])
            for action in next_actions:
                lines.append(f"- {markdown_cell(action)}")

    repair_checklist = summary.get("repair_checklist", [])
    lines.extend(["", "## Repair Checklist", ""])
    if not repair_checklist:
        lines.append("No repair checklist items recorded.")
    else:
        lines.extend(["| Rank | Priority | Action | Command | Expected Artifact | Success Signal |", "| ---: | --- | --- | --- | --- | --- |"])
        for item in repair_checklist:
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

    outputs = summary.get("outputs", {})
    lines.extend(["", "## Outputs", ""])
    if not isinstance(outputs, dict) or not outputs:
        lines.append("No outputs recorded.")
    else:
        lines.extend(["| Artifact | Path |", "| --- | --- |"])
        for key, value in outputs.items():
            lines.append(f"| `{markdown_cell(key)}` | `{markdown_cell(value)}` |")

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


def cmd_template_check(args: argparse.Namespace) -> int:
    summary = run_template_check(args.template_dir, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-check: {summary['status']}")
        print(f"Template: {summary['template_id']}")
        print(f"Pass audit: {summary['pass_audit_status']}")
        print(f"Placeholder claim ready: {str(bool(summary['placeholder_claim_ready'])).lower()}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Failures: {summary['failure_count']}")
        print(f"Wrote {args.out_dir / 'template_check.json'}")
        print(f"Wrote {args.out_dir / 'template_check.md'}")
    return 0 if summary["status"] == "template_ready" else 2


def template_pack_artifact_role(relative_path: Path) -> str:
    path = relative_path.as_posix()
    if path == "template/template.json":
        return "template_manifest"
    if path == "template/project.json":
        return "project_config"
    if path == "template/evidence_pass_demo.csv":
        return "pass_demo_evidence"
    if path == "template/evidence_placeholder_demo.csv":
        return "placeholder_demo_evidence"
    if path == "template/README.md":
        return "template_readme"
    if path.startswith("template/source_files/"):
        return "template_source_file"
    if path == "checks/template_check.json":
        return "template_check_summary"
    if path == "checks/template_check.md":
        return "template_check_report"
    if path == "checks/bundle_verification.json":
        return "template_bundle_verification"
    if path == "checks/bundle_verification.md":
        return "template_bundle_verification_report"
    if path.startswith("checks/"):
        return "template_check_artifact"
    return "template_file"


def write_template_pack_manifest(
    out_dir: Path,
    template_manifest: dict[str, object],
    template_check: dict[str, object],
    zip_path: Path | None,
) -> dict[str, object]:
    artifacts = [
        artifact_record(out_dir, path, template_pack_artifact_role(path.relative_to(out_dir)))
        for path in sorted(out_dir.rglob("*"))
        if path.is_file() and path.name != "template_pack_manifest.json"
    ]
    template_ready = template_check.get("status") == "template_ready"
    manifest: dict[str, object] = {
        "status": "template_pack_ready" if template_ready else "template_pack_blocked",
        "template_id": str(template_manifest.get("id") or ""),
        "template_name": str(template_manifest.get("name") or ""),
        "template_domain": str(template_manifest.get("domain") or ""),
        "template_check_status": str(template_check.get("status", "")),
        "template_check_failure_count": int(template_check.get("failure_count", 0) or 0),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "zip_path": str(zip_path) if zip_path else "",
    }
    (out_dir / "template_pack_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def template_pack_failure_report(
    input_path: Path,
    input_format: str,
    issues: list[dict[str, object]],
    manifest_path: Path | None = None,
) -> dict[str, object]:
    return {
        "status": "template_pack_failed",
        "integrity_status": "integrity_failed",
        "template_pack_status": "",
        "input_format": input_format,
        "input_path": str(input_path),
        "pack_dir": str(input_path),
        "manifest_path": str(manifest_path or (input_path / "template_pack_manifest.json")),
        "template_id": "",
        "artifact_count": 0,
        "checked_artifact_count": 0,
        "missing_artifact_count": 0,
        "bytes_mismatch_count": 0,
        "hash_mismatch_count": 0,
        "unsafe_path_count": sum(1 for issue in issues if issue["code"] in {"unsafe_artifact_path", "unsafe_zip_member"}),
        "duplicate_path_count": sum(1 for issue in issues if issue["code"] in {"duplicate_artifact_path", "duplicate_zip_member"}),
        "unmanifested_file_count": 0,
        "zip_member_count": 0,
        "zip_extracted_file_count": 0,
        "zip_issue_count": sum(1 for issue in issues if str(issue["code"]).startswith("zip_") or issue["code"] in {"unsafe_zip_member", "duplicate_zip_member"}),
        "issue_count": len(issues),
        "error_count": sum(1 for issue in issues if issue.get("severity") == "error"),
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }


def verify_template_pack(pack_dir: Path, input_path: Path | None = None, input_format: str = "directory") -> dict[str, object]:
    input_path = input_path or pack_dir
    issues: list[dict[str, object]] = []
    manifest_path = pack_dir / "template_pack_manifest.json"
    if not pack_dir.exists():
        issues.append(verification_issue("error", "pack_dir_missing", "Template pack directory does not exist.", str(pack_dir)))
    if not pack_dir.is_dir():
        issues.append(verification_issue("error", "pack_dir_not_directory", "Template pack path is not a directory.", str(pack_dir)))
    if issues:
        return template_pack_failure_report(input_path, input_format, issues, manifest_path)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        manifest = {}
        issues.append(verification_issue("error", "manifest_missing", "template_pack_manifest.json is missing.", "template_pack_manifest.json"))
    except json.JSONDecodeError as exc:
        manifest = {}
        issues.append(verification_issue("error", "manifest_invalid_json", f"template_pack_manifest.json is not valid JSON: {exc}", "template_pack_manifest.json"))

    if not isinstance(manifest, dict):
        issues.append(verification_issue("error", "manifest_not_object", "template_pack_manifest.json must contain a JSON object.", "template_pack_manifest.json"))
        manifest = {}

    required_fields = ["status", "template_id", "template_check_status", "artifact_count", "artifacts"]
    for field in required_fields:
        if field not in manifest:
            issues.append(verification_issue("error", "manifest_field_missing", f"Manifest is missing `{field}`.", "template_pack_manifest.json"))
    if manifest.get("status") == "template_pack_ready" and manifest.get("template_check_status") != "template_ready":
        issues.append(verification_issue("error", "template_check_status_mismatch", "Ready template packs must come from a ready template-check.", "template_pack_manifest.json", "template_ready", manifest.get("template_check_status")))

    artifacts_raw = manifest.get("artifacts", [])
    if not isinstance(artifacts_raw, list):
        issues.append(verification_issue("error", "manifest_artifacts_invalid", "Manifest `artifacts` must be an array.", "template_pack_manifest.json"))
        artifacts: list[object] = []
    else:
        artifacts = artifacts_raw
    if manifest.get("artifact_count") != len(artifacts):
        issues.append(verification_issue("error", "artifact_count_mismatch", "Manifest artifact_count does not match artifacts length.", "template_pack_manifest.json", len(artifacts), manifest.get("artifact_count")))

    required_roles = {
        "template_manifest",
        "project_config",
        "pass_demo_evidence",
        "placeholder_demo_evidence",
        "template_source_file",
        "template_check_summary",
        "template_check_report",
        "template_bundle_verification",
        "template_bundle_verification_report",
    }
    artifact_roles: set[str] = set()
    artifact_by_path: dict[str, dict[str, object]] = {}
    checked_artifact_count = 0
    missing_artifact_count = 0
    bytes_mismatch_count = 0
    hash_mismatch_count = 0
    duplicate_path_count = 0

    for index, artifact in enumerate(artifacts):
        artifact_path = f"artifacts[{index}]"
        if not isinstance(artifact, dict):
            issues.append(verification_issue("error", "artifact_invalid", "Artifact entry must be an object.", artifact_path))
            continue
        role = artifact.get("role")
        raw_path = artifact.get("path")
        expected_bytes = artifact.get("bytes")
        expected_sha256 = artifact.get("sha256")
        if not isinstance(role, str) or not role:
            issues.append(verification_issue("error", "artifact_role_invalid", "Artifact role must be a non-empty string.", artifact_path))
        else:
            artifact_roles.add(role)
        if not isinstance(expected_bytes, int) or expected_bytes < 0:
            issues.append(verification_issue("error", "artifact_bytes_invalid", "Artifact bytes must be a non-negative integer.", artifact_path))
        if not is_sha256(expected_sha256):
            issues.append(verification_issue("error", "artifact_sha256_invalid", "Artifact sha256 must be a 64-character hex digest.", artifact_path))

        resolved = relative_artifact_path(pack_dir, raw_path, issues)
        normalized_path = Path(raw_path).as_posix() if isinstance(raw_path, str) else artifact_path
        if isinstance(raw_path, str):
            if normalized_path in artifact_by_path:
                duplicate_path_count += 1
                issues.append(verification_issue("error", "duplicate_artifact_path", "Artifact path appears more than once.", normalized_path))
            artifact_by_path[normalized_path] = artifact
        if resolved is None:
            continue
        if not resolved.exists():
            missing_artifact_count += 1
            issues.append(verification_issue("error", "artifact_missing", "Artifact file is missing.", normalized_path))
            continue
        if not resolved.is_file():
            issues.append(verification_issue("error", "artifact_not_file", "Artifact path is not a file.", normalized_path))
            continue
        checked_artifact_count += 1
        actual_bytes = resolved.stat().st_size
        if isinstance(expected_bytes, int) and actual_bytes != expected_bytes:
            bytes_mismatch_count += 1
            issues.append(verification_issue("error", "artifact_bytes_mismatch", "Artifact byte size does not match manifest.", normalized_path, expected_bytes, actual_bytes))
        if is_sha256(expected_sha256):
            actual_sha256 = sha256_file(resolved)
            if str(expected_sha256).lower() != actual_sha256.lower():
                hash_mismatch_count += 1
                issues.append(verification_issue("error", "artifact_hash_mismatch", "Artifact SHA-256 does not match manifest.", normalized_path, expected_sha256, actual_sha256))

    for role in sorted(required_roles - artifact_roles):
        issues.append(verification_issue("error", "required_role_missing", f"Required artifact role `{role}` is missing.", "template_pack_manifest.json"))

    manifested_paths = set(artifact_by_path)
    unmanifested_files = [
        path.relative_to(pack_dir).as_posix()
        for path in sorted(pack_dir.rglob("*"))
        if path.is_file()
        and path.relative_to(pack_dir).as_posix() not in manifested_paths
        and path.name != "template_pack_manifest.json"
    ]
    for path in unmanifested_files:
        issues.append(verification_issue("error", "unmanifested_file", "Template pack contains a file not listed in template_pack_manifest.json.", path))

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    integrity_status = "integrity_failed" if error_count else "integrity_verified"
    template_pack_status = str(manifest.get("status", ""))
    if error_count:
        status = "template_pack_failed"
    elif template_pack_status == "template_pack_ready":
        status = "template_pack_verified"
    else:
        status = "template_pack_blocked"

    return {
        "status": status,
        "integrity_status": integrity_status,
        "template_pack_status": template_pack_status,
        "input_format": input_format,
        "input_path": str(input_path),
        "pack_dir": str(pack_dir),
        "manifest_path": str(manifest_path),
        "template_id": str(manifest.get("template_id", "")),
        "artifact_count": len(artifacts),
        "checked_artifact_count": checked_artifact_count,
        "missing_artifact_count": missing_artifact_count,
        "bytes_mismatch_count": bytes_mismatch_count,
        "hash_mismatch_count": hash_mismatch_count,
        "unsafe_path_count": sum(1 for issue in issues if issue["code"] == "unsafe_artifact_path"),
        "duplicate_path_count": duplicate_path_count,
        "unmanifested_file_count": len(unmanifested_files),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues,
    }


def extracted_template_pack_root(extract_root: Path, issues: list[dict[str, object]]) -> Path:
    if (extract_root / "template_pack_manifest.json").exists():
        return extract_root
    manifests = sorted(extract_root.rglob("template_pack_manifest.json"))
    if len(manifests) == 1:
        pack_root = manifests[0].parent
        outside_files = [
            path.relative_to(extract_root).as_posix()
            for path in sorted(extract_root.rglob("*"))
            if path.is_file() and not path.resolve().is_relative_to(pack_root.resolve())
        ]
        for path in outside_files:
            issues.append(verification_issue("error", "zip_file_outside_pack_root", "Zip contains a file outside the detected template pack root.", path))
        return pack_root
    if len(manifests) > 1:
        for manifest in manifests:
            issues.append(verification_issue("error", "multiple_template_pack_manifests", "Zip contains multiple template_pack_manifest.json files.", manifest.relative_to(extract_root).as_posix()))
    return extract_root


def merge_template_pack_verification_issues(report: dict[str, object], extra_issues: list[dict[str, object]]) -> dict[str, object]:
    issues = [*extra_issues, *list(report.get("issues", []))]
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    report["issues"] = issues
    report["issue_count"] = len(issues)
    report["error_count"] = error_count
    report["warning_count"] = warning_count
    report["unsafe_path_count"] = sum(1 for issue in issues if issue["code"] in {"unsafe_artifact_path", "unsafe_zip_member"})
    report["duplicate_path_count"] = sum(1 for issue in issues if issue["code"] in {"duplicate_artifact_path", "duplicate_zip_member"})
    report["zip_issue_count"] = sum(1 for issue in extra_issues if issue.get("severity") == "error")
    if error_count:
        report["status"] = "template_pack_failed"
        report["integrity_status"] = "integrity_failed"
    return report


def extract_template_pack_zip(zip_path: Path, extract_root: Path) -> tuple[Path | None, list[dict[str, object]], int, int]:
    issues: list[dict[str, object]] = []
    if not zip_path.exists():
        issues.append(verification_issue("error", "zip_missing", "Template pack zip does not exist.", str(zip_path)))
    if not zip_path.is_file():
        issues.append(verification_issue("error", "zip_not_file", "Template pack zip path is not a file.", str(zip_path)))
    if issues:
        return None, issues, 0, 0

    try:
        archive = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        issues.append(verification_issue("error", "zip_invalid", f"Template pack zip is not a valid zip archive: {exc}", str(zip_path)))
        return None, issues, 0, 0

    with archive:
        infos = archive.infolist()
        extract_root.mkdir(parents=True, exist_ok=True)
        seen_files: set[str] = set()
        extracted_file_count = 0
        for info in infos:
            relative_path = safe_zip_member_relative_path(info.filename)
            if relative_path is None:
                issues.append(verification_issue("error", "unsafe_zip_member", "Zip member path is empty, absolute, or escapes the archive root.", info.filename))
                continue
            normalized = relative_path.as_posix()
            if info.is_dir():
                (extract_root / relative_path).mkdir(parents=True, exist_ok=True)
                continue
            if normalized in seen_files:
                issues.append(verification_issue("error", "duplicate_zip_member", "Zip member path appears more than once.", normalized))
                continue
            seen_files.add(normalized)
            destination = (extract_root / relative_path).resolve()
            try:
                destination.relative_to(extract_root.resolve())
            except ValueError:
                issues.append(verification_issue("error", "unsafe_zip_member", "Zip member resolves outside the extraction root.", info.filename))
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                with archive.open(info, "r") as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target)
                extracted_file_count += 1
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                issues.append(verification_issue("error", "zip_member_read_failed", f"Could not extract zip member: {exc}", normalized))

    pack_root = extracted_template_pack_root(extract_root, issues)
    return pack_root, issues, len(infos), extracted_file_count


def verify_template_pack_zip(zip_path: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="falsiflow_template_pack_zip_") as tmp:
        extract_root = Path(tmp) / "template_pack"
        pack_root, issues, member_count, extracted_file_count = extract_template_pack_zip(zip_path, extract_root)
        if pack_root is None:
            return template_pack_failure_report(zip_path, "zip", issues, zip_path)
        report = verify_template_pack(pack_root, input_path=zip_path, input_format="zip")
        report["pack_dir"] = str(zip_path)
        report["zip_path"] = str(zip_path)
        report["zip_member_count"] = member_count
        report["zip_extracted_file_count"] = extracted_file_count
        report["zip_pack_root"] = pack_root.relative_to(extract_root).as_posix() if pack_root != extract_root else "."
        report["manifest_path"] = f"{zip_path}:{Path(report['manifest_path']).relative_to(pack_root).as_posix()}" if (pack_root / "template_pack_manifest.json").exists() else f"{zip_path}:template_pack_manifest.json"
        return merge_template_pack_verification_issues(report, issues)


def render_template_pack_verification_report(report: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Template Pack Verification",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Integrity: `{report.get('integrity_status', '')}`",
        f"- Template pack status: `{report.get('template_pack_status', '')}`",
        f"- Template: `{report.get('template_id', '')}`",
        f"- Input: `{report.get('input_format', '')}` `{report.get('input_path', '')}`",
        f"- Artifacts checked: {report.get('checked_artifact_count', 0)}/{report.get('artifact_count', 0)}",
        f"- Issues: {report.get('issue_count', 0)} errors={report.get('error_count', 0)} warnings={report.get('warning_count', 0)}",
        "",
        "## Counters",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in [
        "missing_artifact_count",
        "bytes_mismatch_count",
        "hash_mismatch_count",
        "unsafe_path_count",
        "duplicate_path_count",
        "unmanifested_file_count",
        "zip_member_count",
        "zip_extracted_file_count",
        "zip_issue_count",
    ]:
        if key in report:
            lines.append(f"| `{key}` | {report.get(key, 0)} |")
    issues = report.get("issues", [])
    lines.extend(["", "## Issues", ""])
    if not issues:
        lines.append("No issues found.")
    else:
        lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(issue.get("severity", "")),
                    f"`{markdown_cell(issue.get('code', ''))}`",
                    markdown_cell(issue.get("path", "")),
                    markdown_cell(issue.get("message", "")),
                ])
                + " |"
            )
    return "\n".join(lines) + "\n"


def run_template_pack(
    template_dir: Path,
    out_dir: Path,
    zip_out: Path,
    verification_out: Path | None = None,
    report_out: Path | None = None,
    force: bool = False,
) -> dict[str, object]:
    template_dir = template_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"Refusing to write template pack into non-empty directory without --force: {out_dir}")
        shutil.rmtree(out_dir)
    resolved_out = out_dir.resolve()
    resolved_template = template_dir.resolve()
    resolved_zip = zip_out.resolve()
    if resolved_out == resolved_template or resolved_template in resolved_out.parents:
        raise SystemExit("Refusing to write a template pack inside the source template directory.")
    if resolved_zip == resolved_out or resolved_out in resolved_zip.parents:
        raise SystemExit("Refusing to write template pack zip inside the pack directory.")
    for output_path in [verification_out, report_out]:
        if output_path is not None:
            resolved_output = output_path.resolve()
            if resolved_output == resolved_out or resolved_out in resolved_output.parents:
                raise SystemExit("Refusing to write template pack verification outputs inside the pack directory.")
    out_dir.mkdir(parents=True, exist_ok=True)

    packaged_template_dir = out_dir / "template"
    shutil.copytree(template_dir, packaged_template_dir)
    template_check = run_template_check(packaged_template_dir, out_dir / "checks", force=True)
    manifest_path = packaged_template_dir / "template.json"
    template_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    pack_manifest = write_template_pack_manifest(out_dir, template_manifest, template_check, zip_out)
    zip_bundle(out_dir, zip_out)

    verification = verify_template_pack_zip(zip_out)
    if verification_out is not None:
        verification_out.parent.mkdir(parents=True, exist_ok=True)
        verification_out.write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")
    if report_out is not None:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(render_template_pack_verification_report(verification), encoding="utf-8")

    ready = pack_manifest.get("status") == "template_pack_ready" and verification.get("status") == "template_pack_verified"
    return {
        "status": "template_pack_ready" if ready else "template_pack_blocked",
        "template_id": pack_manifest.get("template_id", ""),
        "template_check_status": template_check.get("status", ""),
        "template_check_failure_count": template_check.get("failure_count", 0),
        "template_pack_status": pack_manifest.get("status", ""),
        "verification_status": verification.get("status", ""),
        "artifact_count": pack_manifest.get("artifact_count", 0),
        "pack_dir": str(out_dir),
        "zip_path": str(zip_out),
        "manifest_path": str(out_dir / "template_pack_manifest.json"),
        "verification_path": str(verification_out or ""),
        "verification_report_path": str(report_out or ""),
    }


def cmd_template_pack(args: argparse.Namespace) -> int:
    zip_out = args.zip_out or args.out_dir.with_suffix(".zip")
    verification_out = args.verify_out or zip_out.with_suffix(".verification.json")
    report_out = args.report_out or zip_out.with_suffix(".verification.md")
    summary = run_template_pack(
        args.template_dir,
        args.out_dir,
        zip_out,
        verification_out=verification_out,
        report_out=report_out,
        force=args.force,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-pack: {summary['status']}")
        print(f"Template: {summary['template_id']}")
        print(f"Template check: {summary['template_check_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Artifacts: {summary['artifact_count']}")
        print(f"Wrote {summary['manifest_path']}")
        print(f"Wrote {summary['zip_path']}")
        print(f"Wrote {summary['verification_report_path']}")
    return 0 if summary["status"] == "template_pack_ready" else 2


def cmd_verify_template_pack(args: argparse.Namespace) -> int:
    report = verify_template_pack_zip(args.zip_path) if args.zip_path is not None else verify_template_pack(args.pack_dir)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(render_template_pack_verification_report(report), encoding="utf-8")
    print(f"Falsiflow verify-template-pack: {report['status']}")
    print(f"Integrity: {report['integrity_status']}")
    print(f"Template pack status: {report['template_pack_status']}")
    print(f"Artifacts checked: {report['checked_artifact_count']}/{report['artifact_count']}")
    print(f"Issues: {report['issue_count']}")
    if args.out:
        print(f"Wrote {args.out}")
    if args.report_out:
        print(f"Wrote {args.report_out}")
    if report["status"] == "template_pack_failed":
        return 2
    if args.strict and report["status"] != "template_pack_verified":
        return 2
    return 0


def read_json_object(path: Path, label: str) -> dict[str, object]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"{label} does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} is not valid JSON: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise SystemExit(f"{label} must contain a JSON object: {path}")
    return loaded


def template_source_url(base_url: str, zip_path: Path) -> str:
    normalized = base_url.strip()
    if not normalized:
        return ""
    if not normalized.endswith("/"):
        normalized += "/"
    return urllib.parse.urljoin(normalized, urllib.parse.quote(zip_path.name))


def template_registry_entry(zip_path: Path, source_url: str = "") -> dict[str, object]:
    zip_path = zip_path.expanduser().resolve()
    source_bytes = zip_path.stat().st_size if zip_path.exists() and zip_path.is_file() else 0
    source_sha256 = sha256_file(zip_path) if zip_path.exists() and zip_path.is_file() else ""
    with tempfile.TemporaryDirectory(prefix="falsiflow_template_registry_") as tmp:
        extract_root = Path(tmp) / "template_pack"
        pack_root, extraction_issues, member_count, extracted_file_count = extract_template_pack_zip(zip_path, extract_root)
        if pack_root is None:
            verification = template_pack_failure_report(zip_path, "zip", extraction_issues, zip_path)
            manifest: dict[str, object] = {}
            project: dict[str, object] = {}
        else:
            verification = verify_template_pack(pack_root, input_path=zip_path, input_format="zip")
            verification["zip_path"] = str(zip_path)
            verification["zip_member_count"] = member_count
            verification["zip_extracted_file_count"] = extracted_file_count
            verification = merge_template_pack_verification_issues(verification, extraction_issues)
            try:
                manifest = read_json_object(pack_root / "template_pack_manifest.json", "template pack manifest") if (pack_root / "template_pack_manifest.json").exists() else {}
            except SystemExit:
                manifest = {}
            try:
                project = read_json_object(pack_root / "template" / "project.json", "template project")
            except SystemExit:
                project = {}

    project_meta = project.get("project", {}) if isinstance(project.get("project"), dict) else {}
    template_id = str(manifest.get("template_id") or verification.get("template_id", ""))
    template_version = str(project_meta.get("version", ""))
    return {
        "status": "template_available" if verification.get("status") == "template_pack_verified" else "template_blocked",
        "template_id": template_id,
        "template_name": str(manifest.get("template_name", "")),
        "template_domain": str(manifest.get("template_domain", "")),
        "template_version": template_version,
        "template_project_id": str(project_meta.get("id", "")),
        "template_project_version": template_version,
        "source_type": "url" if source_url else "file",
        "source_url": source_url,
        "source_path": str(zip_path),
        "source_bytes": source_bytes,
        "source_sha256": source_sha256,
        "verification_status": str(verification.get("status", "")),
        "integrity_status": str(verification.get("integrity_status", "")),
        "template_pack_status": str(verification.get("template_pack_status", "")),
        "artifact_count": int(verification.get("artifact_count", 0) or 0),
        "zip_member_count": int(verification.get("zip_member_count", 0) or 0),
        "zip_extracted_file_count": int(verification.get("zip_extracted_file_count", 0) or 0),
        "issue_count": int(verification.get("issue_count", 0) or 0),
        "error_count": int(verification.get("error_count", 0) or 0),
        "warning_count": int(verification.get("warning_count", 0) or 0),
        "issues": list(verification.get("issues", [])),
    }


def render_template_registry_report(registry: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Template Registry",
        "",
        f"- Status: `{registry.get('status', '')}`",
        f"- Templates: {registry.get('verified_template_count', 0)}/{registry.get('template_count', 0)}",
        f"- Duplicates: {registry.get('duplicate_template_count', 0)}",
        f"- Issues: {registry.get('issue_count', 0)}",
        "",
        "## Entries",
        "",
        "| Template | Status | Version | Source SHA-256 | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in registry.get("templates", []):
        if not isinstance(entry, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(entry.get("template_id", "")),
                markdown_cell(entry.get("status", "")),
                markdown_cell(entry.get("template_version", entry.get("template_project_version", ""))),
                markdown_cell(entry.get("source_sha256", "")),
                markdown_cell(entry.get("source_url") or entry.get("source_path", "")),
            ])
            + " |"
        )
    issues = registry.get("issues", [])
    lines.extend(["", "## Issues", ""])
    if not issues:
        lines.append("No issues found.")
    else:
        lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(issue.get("severity", "")),
                    f"`{markdown_cell(issue.get('code', ''))}`",
                    markdown_cell(issue.get("path", "")),
                    markdown_cell(issue.get("message", "")),
                ])
                + " |"
            )
    return "\n".join(lines) + "\n"


def run_template_registry(pack_zips: list[Path], out: Path | None = None, report_out: Path | None = None, base_url: str = "") -> dict[str, object]:
    entries = [
        template_registry_entry(zip_path, source_url=template_source_url(base_url, zip_path) if base_url else "")
        for zip_path in pack_zips
    ]
    issues: list[dict[str, object]] = []
    seen: dict[tuple[str, str], int] = {}
    duplicate_template_count = 0
    for entry in entries:
        template_id = str(entry.get("template_id", ""))
        template_version = str(entry.get("template_version") or entry.get("template_project_version", ""))
        if not safe_template_identifier(template_id):
            issues.append(verification_issue("error", "unsafe_template_id", "Registry entry template_id is missing or unsafe.", str(entry.get("source_path", ""))))
        if template_id:
            key = (template_id, template_version)
            seen[key] = seen.get(key, 0) + 1
    for (template_id, template_version), count in sorted(seen.items()):
        if count > 1:
            duplicate_template_count += 1
            issues.append(verification_issue("error", "duplicate_template_version", "Registry contains duplicate template id/version entries.", f"{template_id}@{template_version}"))
    for entry in entries:
        if entry.get("status") != "template_available":
            issues.append(verification_issue("error", "template_pack_not_available", "Template pack is not verified and available.", str(entry.get("source_path", "")), "template_available", entry.get("status")))
        for issue in entry.get("issues", []):
            if isinstance(issue, dict) and issue.get("severity") == "error":
                issues.append(issue)

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    registry = {
        "status": "template_registry_ready" if not error_count else "template_registry_blocked",
        "template_count": len(entries),
        "verified_template_count": sum(1 for entry in entries if entry.get("status") == "template_available"),
        "duplicate_template_count": duplicate_template_count,
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "templates": entries,
        "issues": issues,
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report_out is not None:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(render_template_registry_report(registry), encoding="utf-8")
    return registry


def cmd_template_registry(args: argparse.Namespace) -> int:
    registry = run_template_registry(args.pack_zip, out=args.out, report_out=args.report_out, base_url=args.base_url)
    if args.json:
        print(json.dumps(registry, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-registry: {registry['status']}")
        print(f"Templates: {registry['verified_template_count']}/{registry['template_count']}")
        print(f"Issues: {registry['issue_count']}")
        if args.out:
            print(f"Wrote {args.out}")
        if args.report_out:
            print(f"Wrote {args.report_out}")
    return 0 if registry["status"] == "template_registry_ready" else 2


def safe_cache_segment(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return cleaned or fallback


def template_source_cache_path(cache_dir: Path, template_id: str, template_version: str, source_sha256: str) -> Path:
    template_part = safe_cache_segment(template_id, "template")
    version_part = safe_cache_segment(template_version, "unversioned")
    sha_part = source_sha256[:16] if is_sha256(source_sha256) else "unverified"
    return cache_dir / f"{template_part}-{version_part}-{sha_part}.zip"


def download_template_source(source_url: str, cache_dir: Path, template_id: str, template_version: str, expected_bytes: int, expected_sha256: str) -> Path:
    parsed = urllib.parse.urlparse(source_url)
    if parsed.scheme not in {"http", "https", "file"}:
        raise SystemExit(f"Unsupported template source URL scheme: {source_url}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = template_source_cache_path(cache_dir, template_id, template_version, expected_sha256)
    if cached.exists() and cached.is_file():
        if cached.stat().st_size == expected_bytes and sha256_file(cached) == expected_sha256:
            return cached
        cached.unlink()
    tmp_path = cached.with_suffix(cached.suffix + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()
    try:
        with urllib.request.urlopen(source_url, timeout=30) as response, tmp_path.open("wb") as target:
            shutil.copyfileobj(response, target)
    except Exception as exc:  # pragma: no cover - defensive network/file URL boundary.
        if tmp_path.exists():
            tmp_path.unlink()
        raise SystemExit(f"Could not fetch template source URL `{source_url}`: {exc}") from exc
    actual_bytes = tmp_path.stat().st_size
    if actual_bytes != expected_bytes:
        tmp_path.unlink()
        raise SystemExit(f"Downloaded template source byte size mismatch: expected {expected_bytes}, got {actual_bytes}")
    actual_sha256 = sha256_file(tmp_path)
    if actual_sha256 != expected_sha256:
        tmp_path.unlink()
        raise SystemExit(f"Downloaded template source SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}")
    tmp_path.replace(cached)
    return cached


def run_template_lock(registry_path: Path, template_id: str, version: str = "", out: Path | None = None, cache_dir: Path | None = None) -> dict[str, object]:
    registry_path = registry_path.expanduser().resolve()
    registry = read_json_object(registry_path, "template registry")
    issues: list[dict[str, object]] = []
    if registry.get("status") != "template_registry_ready":
        issues.append(verification_issue("error", "registry_not_ready", "Template registry is not ready.", str(registry_path), "template_registry_ready", registry.get("status")))
    entries = [
        entry
        for entry in registry.get("templates", [])
        if isinstance(entry, dict)
        and entry.get("template_id") == template_id
        and (not version or str(entry.get("template_version") or entry.get("template_project_version", "")) == version)
    ]
    if not entries:
        issues.append(verification_issue("error", "template_not_found", "Template id/version was not found in the registry.", f"{template_id}@{version}" if version else template_id))
        entry: dict[str, object] = {}
    elif len(entries) > 1:
        issues.append(verification_issue("error", "ambiguous_template_version", "Template id appears more than once in the registry; pass --version.", template_id))
        entry = entries[0]
    else:
        entry = entries[0]
    if entry and entry.get("status") != "template_available":
        issues.append(verification_issue("error", "template_not_available", "Template registry entry is not available.", template_id, "template_available", entry.get("status")))

    template_version = str(entry.get("template_version") or entry.get("template_project_version", "")) if entry else version
    source_url = str(entry.get("source_url", "")) if entry else ""
    source_path = Path(str(entry.get("source_path", ""))).expanduser() if entry else Path()
    if source_path and not source_path.is_absolute():
        source_path = (registry_path.parent / source_path).resolve()
    source_bytes = int(entry.get("source_bytes", 0) or 0) if entry else 0
    source_sha256 = str(entry.get("source_sha256", "")) if entry else ""
    cached_source_path = ""
    if entry:
        if source_url:
            try:
                resolved_cache_dir = cache_dir or (registry_path.parent / ".falsiflow_template_cache")
                cached_source_path = str(download_template_source(source_url, resolved_cache_dir, template_id, template_version, source_bytes, source_sha256))
            except SystemExit as exc:
                issues.append(verification_issue("error", "source_url_fetch_failed", str(exc), source_url))
        elif not source_path.exists() or not source_path.is_file():
            issues.append(verification_issue("error", "source_missing", "Template pack source zip is missing.", str(source_path)))
        else:
            actual_bytes = source_path.stat().st_size
            if actual_bytes != source_bytes:
                issues.append(verification_issue("error", "source_bytes_mismatch", "Template pack source bytes do not match registry.", str(source_path), source_bytes, actual_bytes))
            actual_sha256 = sha256_file(source_path)
            if actual_sha256 != source_sha256:
                issues.append(verification_issue("error", "source_sha256_mismatch", "Template pack source SHA-256 does not match registry.", str(source_path), source_sha256, actual_sha256))

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    lock = {
        "status": "template_locked" if not error_count else "template_lock_blocked",
        "template_id": template_id,
        "template_name": str(entry.get("template_name", "")) if entry else "",
        "template_domain": str(entry.get("template_domain", "")) if entry else "",
        "template_version": template_version,
        "template_project_version": str(entry.get("template_project_version", "")) if entry else "",
        "registry_path": str(registry_path),
        "registry_sha256": sha256_file(registry_path) if registry_path.exists() else "",
        "source_type": str(entry.get("source_type", "")) if entry else "",
        "source_url": source_url,
        "source_path": str(source_path) if entry else "",
        "cached_source_path": cached_source_path,
        "source_bytes": source_bytes,
        "source_sha256": source_sha256,
        "pack_verification_status": str(entry.get("verification_status", "")) if entry else "",
        "artifact_count": int(entry.get("artifact_count", 0) or 0) if entry else 0,
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lock


def cmd_template_lock(args: argparse.Namespace) -> int:
    lock = run_template_lock(args.registry, args.template, version=args.version, out=args.out, cache_dir=args.cache_dir)
    if args.json:
        print(json.dumps(lock, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-lock: {lock['status']}")
        print(f"Template: {lock['template_id']}")
        print(f"Source SHA-256: {lock['source_sha256']}")
        print(f"Issues: {lock['issue_count']}")
        print(f"Wrote {args.out}")
    return 0 if lock["status"] == "template_locked" else 2


def infer_template_subject_type(subject: dict[str, object], subject_path: Path, requested: str = "") -> str:
    if requested:
        return requested
    status = str(subject.get("status", ""))
    if status in {"template_locked", "template_lock_blocked"} or "registry_sha256" in subject:
        return "template-lock"
    if status in {"template_registry_ready", "template_registry_blocked"} or isinstance(subject.get("templates"), list):
        return "template-registry"
    name = subject_path.name.lower()
    if "lock" in name:
        return "template-lock"
    if "registry" in name:
        return "template-registry"
    raise SystemExit("Could not infer template attestation subject type; pass --subject-type.")


def template_subject_payload(subject_path: Path, subject_type: str = "", builder: str = "") -> tuple[dict[str, object], list[dict[str, object]]]:
    subject_path = subject_path.expanduser().resolve()
    subject = read_json_object(subject_path, "template attestation subject")
    resolved_type = infer_template_subject_type(subject, subject_path, subject_type)
    issues: list[dict[str, object]] = []
    payload: dict[str, object] = {
        "subject_type": resolved_type,
        "subject_path": str(subject_path),
        "subject_bytes": subject_path.stat().st_size if subject_path.exists() and subject_path.is_file() else 0,
        "subject_sha256": sha256_file(subject_path) if subject_path.exists() and subject_path.is_file() else "",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "builder": builder,
        "generator": "falsiflow template-attest",
    }
    if resolved_type == "template-lock":
        if subject.get("status") != "template_locked":
            issues.append(verification_issue("error", "subject_not_ready", "Template lock subject is not ready.", str(subject_path), "template_locked", subject.get("status")))
        payload.update({
            "template_id": str(subject.get("template_id", "")),
            "template_version": str(subject.get("template_version") or subject.get("template_project_version", "")),
            "registry_sha256": str(subject.get("registry_sha256", "")),
            "source_type": str(subject.get("source_type", "")),
            "source_url": str(subject.get("source_url", "")),
            "source_bytes": int(subject.get("source_bytes", 0) or 0),
            "source_sha256": str(subject.get("source_sha256", "")),
            "pack_verification_status": str(subject.get("pack_verification_status", "")),
        })
    elif resolved_type == "template-registry":
        if subject.get("status") != "template_registry_ready":
            issues.append(verification_issue("error", "subject_not_ready", "Template registry subject is not ready.", str(subject_path), "template_registry_ready", subject.get("status")))
        templates = [
            {
                "template_id": str(entry.get("template_id", "")),
                "template_version": str(entry.get("template_version") or entry.get("template_project_version", "")),
                "source_type": str(entry.get("source_type", "")),
                "source_url": str(entry.get("source_url", "")),
                "source_bytes": int(entry.get("source_bytes", 0) or 0),
                "source_sha256": str(entry.get("source_sha256", "")),
            }
            for entry in subject.get("templates", [])
            if isinstance(entry, dict)
        ]
        payload.update({
            "template_count": int(subject.get("template_count", 0) or 0),
            "verified_template_count": int(subject.get("verified_template_count", 0) or 0),
            "templates": templates,
        })
    else:
        issues.append(verification_issue("error", "unsupported_subject_type", "Unsupported template attestation subject type.", resolved_type))
    return payload, issues


def resolve_attestation_key(signing_key: str = "") -> str:
    return signing_key or os.environ.get("FALSIFLOW_TEMPLATE_ATTESTATION_KEY", "")


def sign_attestation_payload(payload: dict[str, object], signing_key: str) -> str:
    return hmac.new(signing_key.encode("utf-8"), canonical_json_bytes(payload), hashlib.sha256).hexdigest()


def run_template_attestation(
    subject_path: Path,
    subject_type: str = "",
    out: Path | None = None,
    signing_key: str = "",
    key_id: str = "",
    builder: str = "",
) -> dict[str, object]:
    payload, issues = template_subject_payload(subject_path, subject_type=subject_type, builder=builder)
    resolved_key = resolve_attestation_key(signing_key)
    payload_sha256 = sha256_bytes(canonical_json_bytes(payload))
    signature_type = "hmac-sha256" if resolved_key else "unsigned"
    signature = sign_attestation_payload(payload, resolved_key) if resolved_key else ""
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    attestation = {
        "status": "template_attested" if not error_count else "template_attestation_blocked",
        "subject_type": str(payload.get("subject_type", "")),
        "subject_path": str(payload.get("subject_path", "")),
        "subject_bytes": int(payload.get("subject_bytes", 0) or 0),
        "subject_sha256": str(payload.get("subject_sha256", "")),
        "payload_sha256": payload_sha256,
        "created_at": str(payload.get("created_at", "")),
        "builder": builder,
        "generator": "falsiflow template-attest",
        "signature_type": signature_type,
        "signature": signature,
        "key_id": key_id,
        "payload": payload,
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(attestation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return attestation


def cmd_template_attest(args: argparse.Namespace) -> int:
    attestation = run_template_attestation(
        args.subject,
        subject_type=args.subject_type,
        out=args.out,
        signing_key=args.signing_key,
        key_id=args.key_id,
        builder=args.builder,
    )
    if args.json:
        print(json.dumps(attestation, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-attest: {attestation['status']}")
        print(f"Subject: {attestation['subject_type']}")
        print(f"Subject SHA-256: {attestation['subject_sha256']}")
        print(f"Signature: {attestation['signature_type']}")
        print(f"Issues: {attestation['issue_count']}")
        print(f"Wrote {args.out}")
    return 0 if attestation["status"] == "template_attested" else 2


def attestation_subject_path(attestation: dict[str, object], attestation_path: Path, override: Path | None = None) -> Path:
    if override is not None:
        return override.expanduser().resolve()
    payload = attestation.get("payload", {})
    raw_path = str(payload.get("subject_path", "") if isinstance(payload, dict) else "").strip()
    if not raw_path:
        raw_path = str(attestation.get("subject_path", "")).strip()
    if not raw_path:
        raise SystemExit("Template attestation does not declare a subject path; pass --subject.")
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (attestation_path.parent / path).resolve()
    return path


def run_verify_template_attestation(
    attestation_path: Path,
    subject_path: Path | None = None,
    signing_key: str = "",
) -> dict[str, object]:
    attestation_path = attestation_path.expanduser().resolve()
    attestation = read_json_object(attestation_path, "template attestation")
    issues: list[dict[str, object]] = []
    payload = attestation.get("payload")
    if not isinstance(payload, dict):
        payload = {}
        issues.append(verification_issue("error", "payload_missing", "Template attestation payload is missing or invalid.", str(attestation_path)))
    expected_payload_sha256 = str(attestation.get("payload_sha256", ""))
    actual_payload_sha256 = sha256_bytes(canonical_json_bytes(payload))
    if expected_payload_sha256 != actual_payload_sha256:
        issues.append(verification_issue("error", "payload_sha256_mismatch", "Template attestation payload hash does not match.", str(attestation_path), expected_payload_sha256, actual_payload_sha256))

    subject = attestation_subject_path(attestation, attestation_path, override=subject_path)
    if not subject.exists() or not subject.is_file():
        issues.append(verification_issue("error", "subject_missing", "Template attestation subject file does not exist.", str(subject)))
        actual_subject_bytes = 0
        actual_subject_sha256 = ""
    else:
        actual_subject_bytes = subject.stat().st_size
        actual_subject_sha256 = sha256_file(subject)
    expected_subject_bytes = int(payload.get("subject_bytes", attestation.get("subject_bytes", 0)) or 0)
    expected_subject_sha256 = str(payload.get("subject_sha256", attestation.get("subject_sha256", "")))
    if actual_subject_bytes != expected_subject_bytes:
        issues.append(verification_issue("error", "subject_bytes_mismatch", "Template attestation subject byte size does not match.", str(subject), expected_subject_bytes, actual_subject_bytes))
    if actual_subject_sha256 != expected_subject_sha256:
        issues.append(verification_issue("error", "subject_sha256_mismatch", "Template attestation subject SHA-256 does not match.", str(subject), expected_subject_sha256, actual_subject_sha256))

    signature_type = str(attestation.get("signature_type", "unsigned") or "unsigned")
    signature_verified = False
    if signature_type == "hmac-sha256":
        resolved_key = resolve_attestation_key(signing_key)
        if not resolved_key:
            issues.append(verification_issue("warning", "signing_key_missing", "Template attestation has an HMAC signature, but no signing key was provided.", str(attestation_path)))
        else:
            expected_signature = str(attestation.get("signature", ""))
            actual_signature = sign_attestation_payload(payload, resolved_key)
            if hmac.compare_digest(expected_signature, actual_signature):
                signature_verified = True
            else:
                issues.append(verification_issue("error", "signature_mismatch", "Template attestation HMAC signature does not match.", str(attestation_path)))
    elif signature_type == "unsigned":
        issues.append(verification_issue("warning", "attestation_unsigned", "Template attestation is unsigned; provenance is not trusted.", str(attestation_path)))
    else:
        issues.append(verification_issue("error", "unsupported_signature_type", "Template attestation signature type is not supported.", str(attestation_path), "hmac-sha256 or unsigned", signature_type))

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    if error_count:
        status = "template_attestation_failed"
    elif signature_verified:
        status = "template_attestation_verified"
    else:
        status = "template_attestation_untrusted"
    return {
        "status": status,
        "attestation_path": str(attestation_path),
        "subject_type": str(payload.get("subject_type", attestation.get("subject_type", ""))),
        "subject_path": str(subject),
        "subject_bytes": actual_subject_bytes,
        "subject_sha256": actual_subject_sha256,
        "payload_sha256": actual_payload_sha256,
        "signature_type": signature_type,
        "signature_verified": signature_verified,
        "key_id": str(attestation.get("key_id", "")),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }


def cmd_verify_template_attestation(args: argparse.Namespace) -> int:
    verification = run_verify_template_attestation(args.attestation, subject_path=args.subject, signing_key=args.signing_key)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(verification, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow verify-template-attestation: {verification['status']}")
        print(f"Subject: {verification['subject_type']}")
        print(f"Subject SHA-256: {verification['subject_sha256']}")
        print(f"Signature verified: {str(bool(verification['signature_verified'])).lower()}")
        print(f"Issues: {verification['issue_count']}")
        if args.out:
            print(f"Wrote {args.out}")
    if verification["status"] == "template_attestation_failed":
        return 2
    if args.strict and verification["status"] != "template_attestation_verified":
        return 2
    return 0


def template_policy_expected(lock: dict[str, object], lock_path: Path, attestation_verification: dict[str, object]) -> dict[str, object]:
    return {
        "template_id": str(lock.get("template_id", "")),
        "template_version": str(lock.get("template_version") or lock.get("template_project_version", "")),
        "source_type": str(lock.get("source_type", "")),
        "source_url": str(lock.get("source_url", "")),
        "source_bytes": int(lock.get("source_bytes", 0) or 0),
        "source_sha256": str(lock.get("source_sha256", "")),
        "registry_sha256": str(lock.get("registry_sha256", "")),
        "lock_sha256": sha256_file(lock_path) if lock_path.exists() and lock_path.is_file() else "",
        "attestation_subject_sha256": str(attestation_verification.get("subject_sha256", "")),
        "attestation_payload_sha256": str(attestation_verification.get("payload_sha256", "")),
        "attestation_signature_type": str(attestation_verification.get("signature_type", "")),
        "attestation_key_id": str(attestation_verification.get("key_id", "")),
    }


def run_template_policy(
    lock_path: Path,
    attestation_path: Path,
    out: Path | None = None,
    signing_key: str = "",
    policy_id: str = "",
    owner: str = "",
) -> dict[str, object]:
    lock_path = lock_path.expanduser().resolve()
    attestation_path = attestation_path.expanduser().resolve()
    lock = read_json_object(lock_path, "template lock")
    attestation_verification = run_verify_template_attestation(attestation_path, subject_path=lock_path, signing_key=signing_key)
    issues = [issue for issue in attestation_verification.get("issues", []) if isinstance(issue, dict)]
    if lock.get("status") != "template_locked":
        issues.append(verification_issue("error", "lock_not_ready", "Template policy requires a locked template.", str(lock_path), "template_locked", lock.get("status")))
    if attestation_verification.get("status") != "template_attestation_verified":
        issues.append(verification_issue("error", "attestation_not_verified", "Template policy requires a verified template-lock attestation.", str(attestation_path), "template_attestation_verified", attestation_verification.get("status")))
    expected = template_policy_expected(lock, lock_path, attestation_verification)
    if not expected["attestation_key_id"]:
        issues.append(verification_issue("error", "attestation_key_id_missing", "Template policy requires an attestation key_id.", str(attestation_path)))
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    policy = {
        "status": "template_policy_ready" if not error_count else "template_policy_blocked",
        "policy_id": policy_id or f"{expected['template_id']}@{expected['template_version']}",
        "policy_version": "1",
        "owner": owner,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generator": "falsiflow template-policy",
        "lock_path": str(lock_path),
        "attestation_path": str(attestation_path),
        "template_id": expected["template_id"],
        "template_version": expected["template_version"],
        "require_attestation": True,
        "trusted_key_id": expected["attestation_key_id"],
        "expected": expected,
        "attestation_status": str(attestation_verification.get("status", "")),
        "attestation_signature_verified": bool(attestation_verification.get("signature_verified")),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return policy


def cmd_template_policy(args: argparse.Namespace) -> int:
    policy = run_template_policy(
        args.lock,
        args.attestation,
        out=args.out,
        signing_key=args.signing_key,
        policy_id=args.policy_id,
        owner=args.owner,
    )
    if args.json:
        print(json.dumps(policy, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-policy: {policy['status']}")
        print(f"Policy: {policy['policy_id']}")
        print(f"Template: {policy['template_id']}@{policy['template_version']}")
        print(f"Trusted key: {policy['trusted_key_id']}")
        print(f"Issues: {policy['issue_count']}")
        print(f"Wrote {args.out}")
    return 0 if policy["status"] == "template_policy_ready" else 2


def run_verify_template_policy(
    policy_path: Path,
    lock_path: Path,
    attestation_path: Path,
    signing_key: str = "",
) -> dict[str, object]:
    policy_path = policy_path.expanduser().resolve()
    lock_path = lock_path.expanduser().resolve()
    attestation_path = attestation_path.expanduser().resolve()
    policy = read_json_object(policy_path, "template policy")
    lock = read_json_object(lock_path, "template lock")
    attestation_verification = run_verify_template_attestation(attestation_path, subject_path=lock_path, signing_key=signing_key)
    issues = [issue for issue in attestation_verification.get("issues", []) if isinstance(issue, dict)]
    if policy.get("status") != "template_policy_ready":
        issues.append(verification_issue("error", "policy_not_ready", "Template policy is not ready.", str(policy_path), "template_policy_ready", policy.get("status")))
    if lock.get("status") != "template_locked":
        issues.append(verification_issue("error", "lock_not_ready", "Template policy verification requires a locked template.", str(lock_path), "template_locked", lock.get("status")))
    if attestation_verification.get("status") != "template_attestation_verified":
        issues.append(verification_issue("error", "attestation_not_verified", "Template policy verification requires template_attestation_verified.", str(attestation_path), "template_attestation_verified", attestation_verification.get("status")))

    expected = policy.get("expected", {}) if isinstance(policy.get("expected"), dict) else {}
    actual = template_policy_expected(lock, lock_path, attestation_verification)
    for key, actual_value in actual.items():
        if expected.get(key) != actual_value:
            issues.append(verification_issue("error", f"policy_{key}_mismatch", f"Template policy expected `{key}` does not match.", str(policy_path), expected.get(key), actual_value))
    trusted_key_id = str(policy.get("trusted_key_id", ""))
    if trusted_key_id and trusted_key_id != str(actual.get("attestation_key_id", "")):
        issues.append(verification_issue("error", "policy_trusted_key_id_mismatch", "Template policy trusted_key_id does not match the attestation key_id.", str(policy_path), trusted_key_id, actual.get("attestation_key_id", "")))
    if bool(policy.get("require_attestation", True)) and attestation_verification.get("status") != "template_attestation_verified":
        issues.append(verification_issue("error", "policy_attestation_required", "Template policy requires a verified attestation.", str(policy_path)))

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    return {
        "status": "template_policy_verified" if not error_count else "template_policy_failed",
        "policy_path": str(policy_path),
        "policy_id": str(policy.get("policy_id", "")),
        "lock_path": str(lock_path),
        "attestation_path": str(attestation_path),
        "template_id": str(actual.get("template_id", "")),
        "template_version": str(actual.get("template_version", "")),
        "trusted_key_id": trusted_key_id,
        "attestation_status": str(attestation_verification.get("status", "")),
        "attestation_signature_verified": bool(attestation_verification.get("signature_verified")),
        "expected": expected,
        "actual": actual,
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }


def cmd_verify_template_policy(args: argparse.Namespace) -> int:
    verification = run_verify_template_policy(args.policy, args.lock, args.attestation, signing_key=args.signing_key)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(verification, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow verify-template-policy: {verification['status']}")
        print(f"Policy: {verification['policy_id']}")
        print(f"Template: {verification['template_id']}@{verification['template_version']}")
        print(f"Attestation: {verification['attestation_status']}")
        print(f"Issues: {verification['issue_count']}")
        if args.out:
            print(f"Wrote {args.out}")
    if verification["status"] == "template_policy_failed":
        return 2
    if args.strict and verification["status"] != "template_policy_verified":
        return 2
    return 0


def copy_template_release_artifact(release_root: Path, source: Path, name: str, role: str) -> dict[str, object]:
    target = release_root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return artifact_record(release_root, target, role)


def template_release_manifest(
    release_root: Path,
    artifacts: list[dict[str, object]],
    lock: dict[str, object],
    policy: dict[str, object],
    pack_verification: dict[str, object],
    attestation_verification: dict[str, object],
    policy_verification: dict[str, object],
    issues: list[dict[str, object]],
) -> dict[str, object]:
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    return {
        "status": "template_release_ready" if not error_count else "template_release_blocked",
        "template_id": str(lock.get("template_id", "")),
        "template_version": str(lock.get("template_version") or lock.get("template_project_version", "")),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generator": "falsiflow template-release",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "pack_verification_status": str(pack_verification.get("status", "")),
        "attestation_verification_status": str(attestation_verification.get("status", "")),
        "policy_verification_status": str(policy_verification.get("status", "")),
        "trusted_key_id": str(policy.get("trusted_key_id", "")),
        "source_sha256": str(lock.get("source_sha256", "")),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }


def run_template_release(
    pack_zip: Path,
    registry_path: Path,
    lock_path: Path,
    attestation_path: Path,
    policy_path: Path,
    out: Path,
    signing_key: str = "",
) -> dict[str, object]:
    pack_zip = pack_zip.expanduser().resolve()
    registry_path = registry_path.expanduser().resolve()
    lock_path = lock_path.expanduser().resolve()
    attestation_path = attestation_path.expanduser().resolve()
    policy_path = policy_path.expanduser().resolve()
    out = out.expanduser().resolve()
    issues: list[dict[str, object]] = []
    missing_input = False
    for label, path in [
        ("template_pack", pack_zip),
        ("template_registry", registry_path),
        ("template_lock", lock_path),
        ("template_attestation", attestation_path),
        ("template_policy", policy_path),
    ]:
        if not path.exists() or not path.is_file():
            missing_input = True
            issues.append(verification_issue("error", f"{label}_missing", "Template release input file is missing.", str(path)))
    lock = read_json_object(lock_path, "template lock") if lock_path.exists() and lock_path.is_file() else {}
    policy = read_json_object(policy_path, "template policy") if policy_path.exists() and policy_path.is_file() else {}
    pack_verification = verify_template_pack_zip(pack_zip) if pack_zip.exists() and pack_zip.is_file() else {"status": "template_pack_failed", "issues": []}
    attestation_verification = run_verify_template_attestation(attestation_path, subject_path=lock_path, signing_key=signing_key) if attestation_path.exists() and attestation_path.is_file() and lock_path.exists() and lock_path.is_file() else {"status": "template_attestation_failed", "issues": []}
    policy_verification = run_verify_template_policy(policy_path, lock_path, attestation_path, signing_key=signing_key) if policy_path.exists() and policy_path.is_file() and lock_path.exists() and lock_path.is_file() and attestation_path.exists() and attestation_path.is_file() else {"status": "template_policy_failed", "issues": []}
    issues.extend(issue for issue in pack_verification.get("issues", []) if isinstance(issue, dict) and issue.get("severity") == "error")
    issues.extend(issue for issue in attestation_verification.get("issues", []) if isinstance(issue, dict) and issue.get("severity") == "error")
    issues.extend(issue for issue in policy_verification.get("issues", []) if isinstance(issue, dict) and issue.get("severity") == "error")
    if pack_verification.get("status") != "template_pack_verified":
        issues.append(verification_issue("error", "template_pack_not_verified", "Template release requires a verified template pack.", str(pack_zip), "template_pack_verified", pack_verification.get("status")))
    if attestation_verification.get("status") != "template_attestation_verified":
        issues.append(verification_issue("error", "attestation_not_verified", "Template release requires a verified attestation.", str(attestation_path), "template_attestation_verified", attestation_verification.get("status")))
    if policy_verification.get("status") != "template_policy_verified":
        issues.append(verification_issue("error", "policy_not_verified", "Template release requires a verified policy.", str(policy_path), "template_policy_verified", policy_verification.get("status")))
    if lock.get("source_sha256") and pack_zip.exists() and pack_zip.is_file() and sha256_file(pack_zip) != str(lock.get("source_sha256", "")):
        issues.append(verification_issue("error", "pack_source_sha256_mismatch", "Template pack zip does not match the lockfile source SHA-256.", str(pack_zip), lock.get("source_sha256"), sha256_file(pack_zip)))
    if lock.get("registry_sha256") and registry_path.exists() and registry_path.is_file() and sha256_file(registry_path) != str(lock.get("registry_sha256", "")):
        issues.append(verification_issue("error", "registry_sha256_mismatch", "Template registry does not match the lockfile registry SHA-256.", str(registry_path), lock.get("registry_sha256"), sha256_file(registry_path)))

    if missing_input:
        manifest = template_release_manifest(Path(), [], lock, policy, pack_verification, attestation_verification, policy_verification, issues)
        return {
            **manifest,
            "release_zip_path": str(out),
            "release_zip_bytes": 0,
            "release_zip_sha256": "",
        }

    with tempfile.TemporaryDirectory(prefix="falsiflow_template_release_") as tmp:
        release_root = Path(tmp) / "release"
        release_root.mkdir(parents=True, exist_ok=True)
        artifacts = [
            copy_template_release_artifact(release_root, pack_zip, "template_pack.zip", "template_pack"),
            copy_template_release_artifact(release_root, registry_path, "template_registry.json", "template_registry"),
            copy_template_release_artifact(release_root, lock_path, "falsiflow_template_lock.json", "template_lock"),
            copy_template_release_artifact(release_root, attestation_path, "falsiflow_template_lock.attestation.json", "template_attestation"),
            copy_template_release_artifact(release_root, policy_path, "falsiflow_template_policy.json", "template_policy"),
        ]
        manifest = template_release_manifest(release_root, artifacts, lock, policy, pack_verification, attestation_verification, policy_verification, issues)
        (release_root / "template_release_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        zip_bundle(release_root, out)

    summary = {
        **manifest,
        "release_zip_path": str(out),
        "release_zip_bytes": out.stat().st_size if out.exists() else 0,
        "release_zip_sha256": sha256_file(out) if out.exists() else "",
    }
    return summary


def cmd_template_release(args: argparse.Namespace) -> int:
    summary = run_template_release(
        args.pack_zip,
        args.registry,
        args.lock,
        args.attestation,
        args.policy,
        args.out,
        signing_key=args.signing_key,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-release: {summary['status']}")
        print(f"Template: {summary['template_id']}@{summary['template_version']}")
        print(f"Policy: {summary['policy_verification_status']}")
        print(f"Issues: {summary['issue_count']}")
        print(f"Wrote {summary['release_zip_path']}")
    return 0 if summary["status"] == "template_release_ready" else 2


def relative_release_artifact_path(release_root: Path, raw_path: object, issues: list[dict[str, object]]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        issues.append(verification_issue("error", "invalid_artifact_path", "Template release artifact path must be a non-empty string."))
        return None
    relative_path = safe_zip_member_relative_path(raw_path)
    if relative_path is None:
        issues.append(verification_issue("error", "unsafe_artifact_path", "Template release artifact path must stay inside the release.", raw_path))
        return None
    resolved_root = release_root.resolve()
    resolved_path = (release_root / relative_path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        issues.append(verification_issue("error", "unsafe_artifact_path", "Template release artifact path resolves outside the release.", raw_path))
        return None
    return resolved_path


def extract_template_release_zip(zip_path: Path, extract_root: Path) -> tuple[Path | None, list[dict[str, object]], int, int]:
    issues: list[dict[str, object]] = []
    if not zip_path.exists() or not zip_path.is_file():
        return None, [verification_issue("error", "zip_missing", "Template release zip does not exist.", str(zip_path))], 0, 0
    release_root = extract_root / "release"
    member_count = 0
    extracted_file_count = 0
    seen: set[str] = set()
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                member_count += 1
                relative_path = safe_zip_member_relative_path(info.filename)
                if relative_path is None:
                    issues.append(verification_issue("error", "unsafe_zip_member", "Zip member path is empty, absolute, or escapes the archive root.", info.filename))
                    continue
                relative_name = relative_path.as_posix()
                if relative_name in seen:
                    issues.append(verification_issue("error", "duplicate_zip_member", "Zip member appears more than once.", relative_name))
                    continue
                seen.add(relative_name)
                target = (release_root / relative_path).resolve()
                resolved_release_root = release_root.resolve()
                try:
                    target.relative_to(resolved_release_root)
                except ValueError:
                    issues.append(verification_issue("error", "unsafe_zip_member", "Zip member resolves outside the extraction root.", info.filename))
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as dest:
                    shutil.copyfileobj(source, dest)
                extracted_file_count += 1
    except zipfile.BadZipFile as exc:
        issues.append(verification_issue("error", "zip_invalid", f"Template release zip is not readable: {exc}", str(zip_path)))
    return release_root if release_root.exists() else None, issues, member_count, extracted_file_count


def run_verify_template_release(
    release_zip: Path,
    signing_key: str = "",
    extract_dir: Path | None = None,
) -> dict[str, object]:
    release_zip = release_zip.expanduser().resolve()
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if extract_dir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="falsiflow_template_release_verify_")
        extract_root = Path(temp_dir.name)
    else:
        extract_root = extract_dir.expanduser().resolve()
        if extract_root.exists():
            shutil.rmtree(extract_root)
        extract_root.mkdir(parents=True, exist_ok=True)
    try:
        release_root, extraction_issues, member_count, extracted_file_count = extract_template_release_zip(release_zip, extract_root)
        issues = list(extraction_issues)
        manifest: dict[str, object] = {}
        artifact_paths: dict[str, Path] = {}
        artifact_entries: list[dict[str, object]] = []
        manifested_paths: set[str] = {"template_release_manifest.json"}
        missing_artifact_count = 0
        bytes_mismatch_count = 0
        hash_mismatch_count = 0
        duplicate_path_count = 0
        if release_root is None:
            manifest_path = extract_root / "release" / "template_release_manifest.json"
        else:
            manifest_path = release_root / "template_release_manifest.json"
            try:
                manifest = read_json_object(manifest_path, "template release manifest")
            except SystemExit as exc:
                issues.append(verification_issue("error", "manifest_invalid", str(exc), str(manifest_path)))
            if manifest:
                if manifest.get("status") != "template_release_ready":
                    issues.append(verification_issue("error", "manifest_not_ready", "Template release manifest is not ready.", str(manifest_path), "template_release_ready", manifest.get("status")))
                raw_artifacts = manifest.get("artifacts", [])
                if not isinstance(raw_artifacts, list):
                    issues.append(verification_issue("error", "artifacts_invalid", "Template release manifest artifacts must be a list.", str(manifest_path)))
                    raw_artifacts = []
                artifact_entries = [artifact for artifact in raw_artifacts if isinstance(artifact, dict)]
                if len(artifact_entries) != len(raw_artifacts):
                    issues.append(verification_issue("error", "artifact_entry_invalid", "Template release manifest contains a non-object artifact entry.", str(manifest_path)))
                expected_artifact_count = int(manifest.get("artifact_count", 0) or 0)
                if expected_artifact_count != len(artifact_entries):
                    issues.append(verification_issue("error", "artifact_count_mismatch", "Template release manifest artifact_count does not match the artifact list.", str(manifest_path), expected_artifact_count, len(artifact_entries)))
            seen_roles: set[str] = set()
            seen_paths: set[str] = set()
            for artifact in artifact_entries:
                role = str(artifact.get("role", ""))
                if not role:
                    issues.append(verification_issue("error", "artifact_role_missing", "Template release artifact role is missing.", str(manifest_path)))
                elif role in seen_roles:
                    issues.append(verification_issue("error", "duplicate_artifact_role", "Template release artifact role appears more than once.", role))
                else:
                    seen_roles.add(role)
                path = relative_release_artifact_path(release_root, artifact.get("path", ""), issues)
                if path is None:
                    continue
                relative_name = path.relative_to(release_root.resolve()).as_posix()
                if relative_name in seen_paths:
                    duplicate_path_count += 1
                    issues.append(verification_issue("error", "duplicate_artifact_path", "Template release artifact path appears more than once.", relative_name))
                    continue
                seen_paths.add(relative_name)
                manifested_paths.add(relative_name)
                if role and role not in artifact_paths:
                    artifact_paths[role] = path
                if not isinstance(artifact, dict):
                    continue
                if not path.exists() or not path.is_file():
                    missing_artifact_count += 1
                    issues.append(verification_issue("error", "artifact_missing", "Template release artifact is missing.", str(path)))
                    continue
                expected_bytes = int(artifact.get("bytes", 0) or 0)
                expected_sha256 = str(artifact.get("sha256", ""))
                if path.stat().st_size != expected_bytes:
                    bytes_mismatch_count += 1
                    issues.append(verification_issue("error", "artifact_bytes_mismatch", "Template release artifact byte count does not match.", str(path), expected_bytes, path.stat().st_size))
                actual_sha256 = sha256_file(path)
                if actual_sha256 != expected_sha256:
                    hash_mismatch_count += 1
                    issues.append(verification_issue("error", "artifact_sha256_mismatch", "Template release artifact SHA-256 does not match.", str(path), expected_sha256, actual_sha256))
            unmanifested_files = [
                path.resolve().relative_to(release_root.resolve()).as_posix()
                for path in sorted(release_root.rglob("*"))
                if path.is_file() and path.resolve().relative_to(release_root.resolve()).as_posix() not in manifested_paths
            ]
            for path in unmanifested_files:
                issues.append(verification_issue("error", "unmanifested_file", "Template release contains a file not listed in template_release_manifest.json.", path))
        if release_root is None:
            unmanifested_files = []

        pack_zip = artifact_paths.get("template_pack", Path())
        registry_path = artifact_paths.get("template_registry", Path())
        lock_path = artifact_paths.get("template_lock", Path())
        attestation_path = artifact_paths.get("template_attestation", Path())
        policy_path = artifact_paths.get("template_policy", Path())
        required_roles = {
            "template_pack": pack_zip,
            "template_registry": registry_path,
            "template_lock": lock_path,
            "template_attestation": attestation_path,
            "template_policy": policy_path,
        }
        for role, path in required_roles.items():
            if not path or not path.exists() or not path.is_file():
                issues.append(verification_issue("error", f"{role}_missing", "Template release is missing a required artifact role.", role))

        lock = read_json_object(lock_path, "template lock") if lock_path.exists() and lock_path.is_file() else {}
        pack_verification = verify_template_pack_zip(pack_zip) if pack_zip.exists() and pack_zip.is_file() else {"status": "template_pack_failed", "issues": []}
        attestation_verification = run_verify_template_attestation(attestation_path, subject_path=lock_path, signing_key=signing_key) if attestation_path.exists() and attestation_path.is_file() and lock_path.exists() and lock_path.is_file() else {"status": "template_attestation_failed", "issues": []}
        policy_verification = run_verify_template_policy(policy_path, lock_path, attestation_path, signing_key=signing_key) if policy_path.exists() and policy_path.is_file() and lock_path.exists() and lock_path.is_file() and attestation_path.exists() and attestation_path.is_file() else {"status": "template_policy_failed", "issues": []}
        if pack_verification.get("status") != "template_pack_verified":
            issues.append(verification_issue("error", "template_pack_not_verified", "Template release pack is not verified.", str(pack_zip), "template_pack_verified", pack_verification.get("status")))
        if attestation_verification.get("status") != "template_attestation_verified":
            issues.append(verification_issue("error", "attestation_not_verified", "Template release attestation is not verified.", str(attestation_path), "template_attestation_verified", attestation_verification.get("status")))
        if policy_verification.get("status") != "template_policy_verified":
            issues.append(verification_issue("error", "policy_not_verified", "Template release policy is not verified.", str(policy_path), "template_policy_verified", policy_verification.get("status")))
        if lock.get("source_sha256") and pack_zip.exists() and pack_zip.is_file() and sha256_file(pack_zip) != str(lock.get("source_sha256", "")):
            issues.append(verification_issue("error", "pack_source_sha256_mismatch", "Template release pack does not match the lockfile source SHA-256.", str(pack_zip), lock.get("source_sha256"), sha256_file(pack_zip)))
        if lock.get("registry_sha256") and registry_path.exists() and registry_path.is_file() and sha256_file(registry_path) != str(lock.get("registry_sha256", "")):
            issues.append(verification_issue("error", "registry_sha256_mismatch", "Template release registry does not match the lockfile registry SHA-256.", str(registry_path), lock.get("registry_sha256"), sha256_file(registry_path)))
        if manifest.get("template_id") and lock.get("template_id") and str(manifest.get("template_id")) != str(lock.get("template_id")):
            issues.append(verification_issue("error", "manifest_template_id_mismatch", "Template release manifest template_id does not match the lockfile.", str(manifest_path), manifest.get("template_id"), lock.get("template_id")))
        lock_version = str(lock.get("template_version") or lock.get("template_project_version", ""))
        if manifest.get("template_version") and lock_version and str(manifest.get("template_version")) != lock_version:
            issues.append(verification_issue("error", "manifest_template_version_mismatch", "Template release manifest template_version does not match the lockfile.", str(manifest_path), manifest.get("template_version"), lock_version))
        if manifest.get("source_sha256") and lock.get("source_sha256") and str(manifest.get("source_sha256")) != str(lock.get("source_sha256")):
            issues.append(verification_issue("error", "manifest_source_sha256_mismatch", "Template release manifest source_sha256 does not match the lockfile.", str(manifest_path), manifest.get("source_sha256"), lock.get("source_sha256")))
        for manifest_key, actual_value in [
            ("pack_verification_status", pack_verification.get("status", "")),
            ("attestation_verification_status", attestation_verification.get("status", "")),
            ("policy_verification_status", policy_verification.get("status", "")),
        ]:
            if manifest.get(manifest_key) and str(manifest.get(manifest_key)) != str(actual_value):
                issues.append(verification_issue("error", f"manifest_{manifest_key}_mismatch", f"Template release manifest `{manifest_key}` does not match re-verification.", str(manifest_path), manifest.get(manifest_key), actual_value))

        error_count = sum(1 for issue in issues if issue.get("severity") == "error")
        return {
            "status": "template_release_verified" if not error_count else "template_release_failed",
            "release_zip_path": str(release_zip),
            "release_zip_bytes": release_zip.stat().st_size if release_zip.exists() else 0,
            "release_zip_sha256": sha256_file(release_zip) if release_zip.exists() else "",
            "release_dir": str(release_root or ""),
            "manifest_path": str(manifest_path),
            "template_id": str(lock.get("template_id", manifest.get("template_id", ""))),
            "template_version": str(lock.get("template_version") or lock.get("template_project_version", manifest.get("template_version", ""))),
            "zip_member_count": member_count,
            "zip_extracted_file_count": extracted_file_count,
            "artifact_count": int(manifest.get("artifact_count", 0) or 0),
            "artifact_paths": {role: str(path) for role, path in required_roles.items()},
            "missing_artifact_count": missing_artifact_count,
            "bytes_mismatch_count": bytes_mismatch_count,
            "hash_mismatch_count": hash_mismatch_count,
            "unsafe_path_count": sum(1 for issue in issues if issue.get("code") in {"unsafe_artifact_path", "unsafe_zip_member"}),
            "duplicate_path_count": duplicate_path_count + sum(1 for issue in issues if issue.get("code") == "duplicate_zip_member"),
            "unmanifested_file_count": len(unmanifested_files),
            "zip_issue_count": sum(1 for issue in extraction_issues if issue.get("severity") == "error"),
            "pack_verification_status": str(pack_verification.get("status", "")),
            "attestation_verification_status": str(attestation_verification.get("status", "")),
            "policy_verification_status": str(policy_verification.get("status", "")),
            "attestation_verification_summary": attestation_verification,
            "policy_verification_summary": policy_verification,
            "issue_count": len(issues),
            "error_count": error_count,
            "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
            "issues": issues,
        }
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def render_template_release_verification_report(report: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Template Release Verification",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Template: `{report.get('template_id', '')}@{report.get('template_version', '')}`",
        f"- Release zip SHA-256: `{report.get('release_zip_sha256', '')}`",
        f"- Pack verification: `{report.get('pack_verification_status', '')}`",
        f"- Attestation verification: `{report.get('attestation_verification_status', '')}`",
        f"- Policy verification: `{report.get('policy_verification_status', '')}`",
        f"- Issues: {report.get('issue_count', 0)} errors={report.get('error_count', 0)} warnings={report.get('warning_count', 0)}",
        "",
        "## Integrity Counters",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in [
        "artifact_count",
        "missing_artifact_count",
        "bytes_mismatch_count",
        "hash_mismatch_count",
        "unsafe_path_count",
        "duplicate_path_count",
        "unmanifested_file_count",
        "zip_member_count",
        "zip_extracted_file_count",
        "zip_issue_count",
    ]:
        if key in report:
            lines.append(f"| `{key}` | {report.get(key, 0)} |")
    artifact_paths = report.get("artifact_paths", {})
    lines.extend(["", "## Artifacts", ""])
    if isinstance(artifact_paths, dict) and artifact_paths:
        lines.extend(["| Role | Path |", "| --- | --- |"])
        for role, path in sorted(artifact_paths.items()):
            lines.append(f"| `{markdown_cell(role)}` | {markdown_cell(path)} |")
    else:
        lines.append("No artifact paths found.")
    issues = report.get("issues", [])
    lines.extend(["", "## Issues", ""])
    if not issues:
        lines.append("No issues found.")
    else:
        lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(issue.get("severity", "")),
                    f"`{markdown_cell(issue.get('code', ''))}`",
                    markdown_cell(issue.get("path", "")),
                    markdown_cell(issue.get("message", "")),
                ])
                + " |"
            )
    return "\n".join(lines) + "\n"


def cmd_verify_template_release(args: argparse.Namespace) -> int:
    verification = run_verify_template_release(args.release, signing_key=args.signing_key)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(render_template_release_verification_report(verification), encoding="utf-8")
    if args.json:
        print(json.dumps(verification, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow verify-template-release: {verification['status']}")
        print(f"Template: {verification['template_id']}@{verification['template_version']}")
        print(f"Policy: {verification['policy_verification_status']}")
        print(f"Issues: {verification['issue_count']}")
        if args.out:
            print(f"Wrote {args.out}")
        if args.report_out:
            print(f"Wrote {args.report_out}")
    if verification["status"] == "template_release_failed":
        return 2
    if args.strict and verification["status"] != "template_release_verified":
        return 2
    return 0


def locked_template_zip(lock_path: Path, cache_dir: Path | None = None) -> tuple[Path, dict[str, object]]:
    lock_path = lock_path.expanduser().resolve()
    lock = read_json_object(lock_path, "template lock")
    if lock.get("status") != "template_locked":
        raise SystemExit(f"Template lock is not ready: {lock_path}")
    expected_bytes = int(lock.get("source_bytes", 0) or 0)
    expected_sha256 = str(lock.get("source_sha256", ""))
    template_id = str(lock.get("template_id", ""))
    template_version = str(lock.get("template_version") or lock.get("template_project_version", ""))
    source_url = str(lock.get("source_url", ""))
    if source_url:
        return download_template_source(
            source_url,
            cache_dir or (lock_path.parent / ".falsiflow_template_cache"),
            template_id,
            template_version,
            expected_bytes,
            expected_sha256,
        ), lock
    raw_cached_source = str(lock.get("cached_source_path", ""))
    cached_source_path = Path(raw_cached_source).expanduser()
    if raw_cached_source and not cached_source_path.is_absolute():
        cached_source_path = (lock_path.parent / cached_source_path).resolve()
    if raw_cached_source and cached_source_path.exists() and cached_source_path.is_file():
        source_path = cached_source_path
    else:
        source_path = Path(str(lock.get("source_path", ""))).expanduser()
    if not source_path.is_absolute():
        source_path = (lock_path.parent / source_path).resolve()
    if not source_path.exists() or not source_path.is_file():
        raise SystemExit(f"Locked template pack source does not exist: {source_path}")
    actual_bytes = source_path.stat().st_size
    if actual_bytes != expected_bytes:
        raise SystemExit(f"Locked template pack byte size mismatch: expected {expected_bytes}, got {actual_bytes}")
    actual_sha256 = sha256_file(source_path)
    if actual_sha256 != expected_sha256:
        raise SystemExit(f"Locked template pack SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}")
    return source_path, lock


def count_files(path: Path) -> int:
    return sum(1 for item in path.rglob("*") if item.is_file()) if path.exists() else 0


def template_install_index_path(templates_dir: Path) -> Path:
    return templates_dir / "falsiflow_template_index.json"


def write_template_install_index(templates_dir: Path, record: dict[str, object]) -> dict[str, object]:
    index_path = template_install_index_path(templates_dir)
    existing_templates: list[dict[str, object]] = []
    if index_path.exists():
        try:
            loaded = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("templates"), list):
                existing_templates = [item for item in loaded["templates"] if isinstance(item, dict)]
        except json.JSONDecodeError:
            existing_templates = []
    template_id = str(record.get("template_id", ""))
    templates = [item for item in existing_templates if str(item.get("template_id", "")) != template_id]
    templates.append(record)
    templates = sorted(templates, key=lambda item: str(item.get("template_id", "")))
    index = {
        "status": "template_index_ready",
        "template_count": len(templates),
        "templates": templates,
    }
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def template_install_blocked_summary(
    zip_path: Path,
    templates_dir: Path,
    install_dir: Path | None,
    verification: dict[str, object],
    issues: list[dict[str, object]],
    template_id: str = "",
    attestation_verification: dict[str, object] | None = None,
    attestation_required: bool = False,
    policy_verification: dict[str, object] | None = None,
) -> dict[str, object]:
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    attestation_fields = template_install_attestation_fields(attestation_verification, attestation_required)
    policy_fields = template_install_policy_fields(policy_verification)
    return {
        "status": "template_install_blocked",
        "template_id": template_id or str(verification.get("template_id", "")),
        "input_path": str(zip_path),
        "templates_dir": str(templates_dir),
        "install_dir": str(install_dir or ""),
        "registry_path": str(template_install_index_path(templates_dir)),
        "verification_status": str(verification.get("status", "")),
        "integrity_status": str(verification.get("integrity_status", "")),
        "template_check_status": "",
        "template_check_failure_count": 0,
        "artifact_count": int(verification.get("artifact_count", 0) or 0),
        "installed_file_count": 0,
        "registry_template_count": 0,
        **attestation_fields,
        **policy_fields,
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }


def template_install_attestation_fields(attestation_verification: dict[str, object] | None, attestation_required: bool) -> dict[str, object]:
    if not attestation_verification:
        return {
            "attestation_required": attestation_required,
            "attestation_path": "",
            "attestation_status": "not_checked",
            "attestation_subject_type": "",
            "attestation_subject_sha256": "",
            "attestation_signature_verified": False,
            "attestation_key_id": "",
            "attestation_issue_count": 0,
        }
    return {
        "attestation_required": attestation_required,
        "attestation_path": str(attestation_verification.get("attestation_path", "")),
        "attestation_status": str(attestation_verification.get("status", "")),
        "attestation_subject_type": str(attestation_verification.get("subject_type", "")),
        "attestation_subject_sha256": str(attestation_verification.get("subject_sha256", "")),
        "attestation_signature_verified": bool(attestation_verification.get("signature_verified")),
        "attestation_key_id": str(attestation_verification.get("key_id", "")),
        "attestation_issue_count": int(attestation_verification.get("issue_count", 0) or 0),
    }


def template_install_policy_fields(policy_verification: dict[str, object] | None) -> dict[str, object]:
    if not policy_verification:
        return {
            "policy_path": "",
            "policy_status": "not_checked",
            "policy_id": "",
            "policy_trusted_key_id": "",
            "policy_issue_count": 0,
        }
    return {
        "policy_path": str(policy_verification.get("policy_path", "")),
        "policy_status": str(policy_verification.get("status", "")),
        "policy_id": str(policy_verification.get("policy_id", "")),
        "policy_trusted_key_id": str(policy_verification.get("trusted_key_id", "")),
        "policy_issue_count": int(policy_verification.get("issue_count", 0) or 0),
    }


def template_install_attestation_issues(attestation_verification: dict[str, object] | None, attestation_required: bool) -> list[dict[str, object]]:
    if attestation_verification is None:
        if not attestation_required:
            return []
        return [verification_issue("error", "attestation_required_missing", "Template install requires a verified template-lock attestation.", "template-install")]
    issues = [issue for issue in attestation_verification.get("issues", []) if isinstance(issue, dict)]
    status = str(attestation_verification.get("status", ""))
    subject_type = str(attestation_verification.get("subject_type", ""))
    if subject_type and subject_type != "template-lock":
        issues.append(verification_issue("error", "attestation_subject_type_mismatch", "Template install attestations must verify a template-lock subject.", str(attestation_verification.get("attestation_path", "")), "template-lock", subject_type))
    if status == "template_attestation_failed" and not any(issue.get("severity") == "error" for issue in issues):
        issues.append(verification_issue("error", "attestation_verification_failed", "Template attestation verification failed.", str(attestation_verification.get("attestation_path", ""))))
    if status not in {"template_attestation_verified", "template_attestation_untrusted", "template_attestation_failed"}:
        issues.append(verification_issue("error", "attestation_status_unknown", "Template attestation verification status is not recognized.", str(attestation_verification.get("attestation_path", "")), "template_attestation_verified", status))
    if attestation_required and status != "template_attestation_verified":
        issues.append(verification_issue("error", "attestation_not_verified", "Template install requires template_attestation_verified.", str(attestation_verification.get("attestation_path", "")), "template_attestation_verified", status))
    return issues


def template_install_policy_issues(policy_verification: dict[str, object] | None) -> list[dict[str, object]]:
    if policy_verification is None:
        return []
    issues = [issue for issue in policy_verification.get("issues", []) if isinstance(issue, dict)]
    if policy_verification.get("status") != "template_policy_verified":
        issues.append(verification_issue("error", "policy_not_verified", "Template install requires template_policy_verified.", str(policy_verification.get("policy_path", "")), "template_policy_verified", policy_verification.get("status")))
    return issues


def template_install_preflight_blocked_summary(
    input_path: Path,
    templates_dir: Path,
    issues: list[dict[str, object]],
    template_id: str = "",
    attestation_verification: dict[str, object] | None = None,
    attestation_required: bool = False,
    policy_verification: dict[str, object] | None = None,
) -> dict[str, object]:
    verification = {
        "status": "",
        "integrity_status": "",
        "artifact_count": 0,
        "issues": [],
    }
    return template_install_blocked_summary(
        input_path,
        templates_dir.expanduser().resolve(),
        None,
        verification,
        issues,
        template_id=template_id,
        attestation_verification=attestation_verification,
        attestation_required=attestation_required,
        policy_verification=policy_verification,
    )


def run_template_install(
    zip_path: Path,
    templates_dir: Path,
    check_out_dir: Path | None = None,
    force: bool = False,
    attestation_verification: dict[str, object] | None = None,
    attestation_required: bool = False,
    policy_verification: dict[str, object] | None = None,
) -> dict[str, object]:
    templates_dir = templates_dir.expanduser().resolve()
    zip_path = zip_path.expanduser().resolve()
    attestation_issues = template_install_attestation_issues(attestation_verification, attestation_required)
    policy_issues = template_install_policy_issues(policy_verification)
    preflight_issues = [*attestation_issues, *policy_issues]
    if any(issue.get("severity") == "error" for issue in preflight_issues):
        return template_install_blocked_summary(
            zip_path,
            templates_dir,
            None,
            {"status": "", "integrity_status": "", "artifact_count": 0, "issues": []},
            preflight_issues,
            attestation_verification=attestation_verification,
            attestation_required=attestation_required,
            policy_verification=policy_verification,
        )
    with tempfile.TemporaryDirectory(prefix="falsiflow_template_install_") as tmp:
        extract_root = Path(tmp) / "template_pack"
        pack_root, extraction_issues, member_count, extracted_file_count = extract_template_pack_zip(zip_path, extract_root)
        if pack_root is None:
            verification = template_pack_failure_report(zip_path, "zip", extraction_issues, zip_path)
            return template_install_blocked_summary(zip_path, templates_dir, None, verification, extraction_issues, attestation_verification=attestation_verification, attestation_required=attestation_required, policy_verification=policy_verification)

        verification = verify_template_pack(pack_root, input_path=zip_path, input_format="zip")
        verification["pack_dir"] = str(zip_path)
        verification["zip_path"] = str(zip_path)
        verification["zip_member_count"] = member_count
        verification["zip_extracted_file_count"] = extracted_file_count
        verification["zip_pack_root"] = pack_root.relative_to(extract_root).as_posix() if pack_root != extract_root else "."
        verification["manifest_path"] = f"{zip_path}:{Path(verification['manifest_path']).relative_to(pack_root).as_posix()}" if (pack_root / "template_pack_manifest.json").exists() else f"{zip_path}:template_pack_manifest.json"
        verification = merge_template_pack_verification_issues(verification, extraction_issues)
        if verification.get("status") != "template_pack_verified":
            return template_install_blocked_summary(zip_path, templates_dir, None, verification, list(verification.get("issues", [])), attestation_verification=attestation_verification, attestation_required=attestation_required, policy_verification=policy_verification)

        source_template_dir = pack_root / "template"
        local_issues: list[dict[str, object]] = []
        if not source_template_dir.exists() or not source_template_dir.is_dir():
            local_issues.append(verification_issue("error", "template_dir_missing", "Verified template pack does not contain template/.", "template"))

        template_id = str(verification.get("template_id", "")).strip()
        if not safe_template_identifier(template_id):
            local_issues.append(verification_issue("error", "unsafe_template_id", "Template id must be a safe path segment.", "template_pack_manifest.json", "safe template id", template_id))
        install_dir = templates_dir / template_id if template_id else None
        if install_dir is not None:
            resolved_install = install_dir.resolve()
            try:
                resolved_install.relative_to(templates_dir)
            except ValueError:
                local_issues.append(verification_issue("error", "install_dir_escape", "Resolved install directory escapes templates_dir.", str(install_dir)))
        if local_issues:
            return template_install_blocked_summary(zip_path, templates_dir, install_dir, verification, [*list(verification.get("issues", [])), *local_issues, *attestation_issues, *policy_issues], template_id, attestation_verification=attestation_verification, attestation_required=attestation_required, policy_verification=policy_verification)

        assert install_dir is not None
        if templates_dir.exists() and not templates_dir.is_dir():
            raise SystemExit(f"Refusing to install templates into non-directory path: {templates_dir}")
        if install_dir.exists() and not install_dir.is_dir():
            raise SystemExit(f"Refusing to overwrite non-directory installed template path: {install_dir}")
        if install_dir.exists() and any(install_dir.iterdir()) and not force:
            raise SystemExit(f"Refusing to overwrite installed template without --force: {install_dir}")

        templates_dir.mkdir(parents=True, exist_ok=True)
        staging_dir = templates_dir / f".{template_id}.installing"
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        shutil.copytree(source_template_dir, staging_dir)
        if install_dir.exists():
            shutil.rmtree(install_dir)
        shutil.move(str(staging_dir), str(install_dir))

        check_dir = check_out_dir or (templates_dir / ".falsiflow_template_checks" / template_id)
        template_check = run_template_check(install_dir, check_dir, force=True)
        if template_check.get("status") != "template_ready":
            shutil.rmtree(install_dir)
            install_issue = verification_issue("error", "installed_template_check_blocked", "Installed template did not pass template-check.", str(check_dir), "template_ready", template_check.get("status"))
            return template_install_blocked_summary(zip_path, templates_dir, install_dir, verification, [*list(verification.get("issues", [])), install_issue, *attestation_issues, *policy_issues], template_id, attestation_verification=attestation_verification, attestation_required=attestation_required, policy_verification=policy_verification)

        template_manifest_path = install_dir / "template.json"
        template_manifest = json.loads(template_manifest_path.read_text(encoding="utf-8")) if template_manifest_path.exists() else {}
        attestation_fields = template_install_attestation_fields(attestation_verification, attestation_required)
        policy_fields = template_install_policy_fields(policy_verification)
        summary_issues = [*list(verification.get("issues", [])), *attestation_issues, *policy_issues]
        record = {
            "template_id": template_id,
            "template_name": str(template_manifest.get("name", "")) if isinstance(template_manifest, dict) else "",
            "template_domain": str(template_manifest.get("domain", "")) if isinstance(template_manifest, dict) else "",
            "template_dir": str(install_dir),
            "source_zip": str(zip_path),
            "source_sha256": sha256_file(zip_path),
            "pack_verification_status": str(verification.get("status", "")),
            "template_check_status": str(template_check.get("status", "")),
            **attestation_fields,
            **policy_fields,
            "artifact_count": int(verification.get("artifact_count", 0) or 0),
            "installed_file_count": count_files(install_dir),
        }
        index = write_template_install_index(templates_dir, record)
        return {
            "status": "template_installed",
            "template_id": template_id,
            "template_name": record["template_name"],
            "template_domain": record["template_domain"],
            "input_path": str(zip_path),
            "templates_dir": str(templates_dir),
            "install_dir": str(install_dir),
            "registry_path": str(template_install_index_path(templates_dir)),
            "verification_status": str(verification.get("status", "")),
            "integrity_status": str(verification.get("integrity_status", "")),
            "template_check_status": str(template_check.get("status", "")),
            "template_check_failure_count": int(template_check.get("failure_count", 0) or 0),
            "artifact_count": int(verification.get("artifact_count", 0) or 0),
            "installed_file_count": count_files(install_dir),
            "registry_template_count": int(index.get("template_count", 0) or 0),
            **attestation_fields,
            **policy_fields,
            "issue_count": len(summary_issues),
            "error_count": sum(1 for issue in summary_issues if issue.get("severity") == "error"),
            "warning_count": sum(1 for issue in summary_issues if issue.get("severity") == "warning"),
            "issues": summary_issues,
        }


def cmd_template_install(args: argparse.Namespace) -> int:
    lock: dict[str, object] | None = None
    lock_path: Path | None = args.lock_path
    zip_path = args.zip_path
    attestation_verification: dict[str, object] | None = None
    policy_verification: dict[str, object] | None = None
    release_verification: dict[str, object] | None = None
    if args.release_path is not None:
        if args.attestation_path is not None or args.policy_path is not None:
            raise SystemExit("--release includes its own attestation and policy; do not pass --attestation or --policy.")
        with tempfile.TemporaryDirectory(prefix="falsiflow_template_release_install_") as tmp:
            release_verification = run_verify_template_release(
                args.release_path,
                signing_key=args.signing_key,
                extract_dir=Path(tmp) / "release_extract",
            )
            release_issues = [issue for issue in release_verification.get("issues", []) if isinstance(issue, dict)]
            artifact_paths = release_verification.get("artifact_paths", {}) if isinstance(release_verification.get("artifact_paths"), dict) else {}
            lock_path = Path(str(artifact_paths.get("template_lock", "")))
            zip_path = Path(str(artifact_paths.get("template_pack", "")))
            lock_preview = read_json_object(lock_path, "template lock") if lock_path.exists() else {}
            attestation_verification = release_verification.get("attestation_verification_summary") if isinstance(release_verification.get("attestation_verification_summary"), dict) else None
            policy_verification = release_verification.get("policy_verification_summary") if isinstance(release_verification.get("policy_verification_summary"), dict) else None
            if release_verification.get("status") != "template_release_verified":
                summary = template_install_preflight_blocked_summary(
                    args.release_path,
                    args.templates_dir,
                    release_issues,
                    template_id=str(release_verification.get("template_id", "")),
                    attestation_verification=attestation_verification,
                    attestation_required=True,
                    policy_verification=policy_verification,
                )
                summary["release_path"] = str(args.release_path)
                summary["release_status"] = str(release_verification.get("status", ""))
                summary["release_sha256"] = str(release_verification.get("release_zip_sha256", ""))
                summary["lock_path"] = str(lock_path)
                summary["lock_status"] = str(lock_preview.get("status", ""))
                summary["lock_source_sha256"] = str(lock_preview.get("source_sha256", ""))
                if args.json:
                    print(json.dumps(summary, indent=2, sort_keys=True))
                else:
                    print(f"Falsiflow template-install: {summary['status']}")
                    print(f"Release: {summary.get('release_status', '')}")
                    print(f"Attestation: {summary.get('attestation_status', '')}")
                    print(f"Policy: {summary.get('policy_status', '')}")
                    print(f"Issues: {summary['issue_count']}")
                return 2
            lock = lock_preview
            summary = run_template_install(
                zip_path,
                args.templates_dir,
                check_out_dir=args.check_out_dir,
                force=args.force,
                attestation_verification=attestation_verification,
                attestation_required=True,
                policy_verification=policy_verification,
            )
            summary["release_path"] = str(args.release_path)
            summary["release_status"] = str(release_verification.get("status", ""))
            summary["release_sha256"] = str(release_verification.get("release_zip_sha256", ""))
            summary["lock_path"] = str(lock_path)
            summary["lock_status"] = str(lock.get("status", "")) if lock else ""
            summary["lock_source_sha256"] = str(lock.get("source_sha256", "")) if lock else ""
            if args.json:
                print(json.dumps(summary, indent=2, sort_keys=True))
            else:
                print(f"Falsiflow template-install: {summary['status']}")
                print(f"Template: {summary['template_id']}")
                print(f"Release: {summary.get('release_status', '')}")
                print(f"Attestation: {summary.get('attestation_status', '')}")
                print(f"Policy: {summary.get('policy_status', '')}")
                print(f"Installed files: {summary['installed_file_count']}")
                print(f"Wrote {summary['install_dir']}")
                print(f"Wrote {summary['registry_path']}")
            return 0 if summary["status"] == "template_installed" else 2
    if args.attestation_path is not None and lock_path is None:
        raise SystemExit("--attestation can only be used with --lock.")
    if args.require_attestation and lock_path is None:
        raise SystemExit("--require-attestation requires --lock.")
    if args.policy_path is not None and lock_path is None:
        raise SystemExit("--policy requires --lock.")
    if args.policy_path is not None and args.attestation_path is None:
        raise SystemExit("--policy requires --attestation.")
    effective_attestation_required = bool(args.require_attestation or args.policy_path is not None)
    if lock_path is not None:
        lock_preview = read_json_object(lock_path.expanduser().resolve(), "template lock")
        if args.attestation_path is not None:
            attestation_verification = run_verify_template_attestation(
                args.attestation_path,
                subject_path=lock_path,
                signing_key=args.signing_key,
            )
        if args.policy_path is not None:
            policy_verification = run_verify_template_policy(
                args.policy_path,
                lock_path,
                args.attestation_path,
                signing_key=args.signing_key,
            )
        attestation_issues = template_install_attestation_issues(attestation_verification, effective_attestation_required)
        policy_issues = template_install_policy_issues(policy_verification)
        preflight_issues = [*attestation_issues, *policy_issues]
        if any(issue.get("severity") == "error" for issue in preflight_issues):
            summary = template_install_preflight_blocked_summary(
                lock_path,
                args.templates_dir,
                preflight_issues,
                template_id=str(lock_preview.get("template_id", "")),
                attestation_verification=attestation_verification,
                attestation_required=effective_attestation_required,
                policy_verification=policy_verification,
            )
            summary["lock_path"] = str(lock_path)
            summary["lock_status"] = str(lock_preview.get("status", ""))
            summary["lock_source_sha256"] = str(lock_preview.get("source_sha256", ""))
            if args.json:
                print(json.dumps(summary, indent=2, sort_keys=True))
            else:
                print(f"Falsiflow template-install: {summary['status']}")
                print(f"Template: {summary['template_id']}")
                print(f"Lock: {summary.get('lock_status', '')}")
                print(f"Attestation: {summary.get('attestation_status', '')}")
                print(f"Policy: {summary.get('policy_status', '')}")
                print(f"Issues: {summary['issue_count']}")
            return 2
        zip_path, lock = locked_template_zip(lock_path, cache_dir=args.cache_dir)
    summary = run_template_install(
        zip_path,
        args.templates_dir,
        check_out_dir=args.check_out_dir,
        force=args.force,
        attestation_verification=attestation_verification,
        attestation_required=effective_attestation_required,
        policy_verification=policy_verification,
    )
    if lock_path is not None:
        summary["lock_path"] = str(lock_path)
        summary["lock_status"] = str(lock.get("status", "")) if lock else ""
        summary["lock_source_sha256"] = str(lock.get("source_sha256", "")) if lock else ""
        if lock and summary.get("template_id") != lock.get("template_id"):
            summary["status"] = "template_install_blocked"
            summary["issues"] = [
                *list(summary.get("issues", [])),
                verification_issue("error", "lock_template_mismatch", "Installed template id does not match the lockfile.", str(lock_path), lock.get("template_id"), summary.get("template_id")),
            ]
            summary["issue_count"] = len(summary["issues"])
            summary["error_count"] = int(summary.get("error_count", 0) or 0) + 1
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-install: {summary['status']}")
        print(f"Template: {summary['template_id']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Template check: {summary['template_check_status']}")
        if lock_path is not None:
            print(f"Lock: {summary.get('lock_status', '')}")
        if args.attestation_path is not None or effective_attestation_required:
            print(f"Attestation: {summary.get('attestation_status', '')}")
        if args.policy_path is not None:
            print(f"Policy: {summary.get('policy_status', '')}")
        print(f"Installed files: {summary['installed_file_count']}")
        print(f"Wrote {summary['install_dir']}")
        print(f"Wrote {summary['registry_path']}")
    return 0 if summary["status"] == "template_installed" else 2


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


def package_init_version(path: Path) -> str:
    if not path.exists():
        return ""
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    return match.group(1) if match else ""


def package_release_checks(root: Path) -> dict[str, object]:
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
    release_path = root / "RELEASE.md"
    security_path = root / "SECURITY.md"
    responsible_use_path = root / "RESPONSIBLE_USE.md"
    adoption_priorities_path = root / "docs" / "falsiflow_adoption_priorities.md"
    walkthrough_path = root / "examples" / "README.md"
    manifest_path = root / "MANIFEST.in"
    makefile_path = root / "Makefile"
    install_script_path = root / "scripts" / "install_local.sh"
    powershell_install_path = root / "scripts" / "install_local.ps1"
    github_ci_path = root / ".github" / "workflows" / "falsiflow.yml"
    github_pages_path = root / ".github" / "workflows" / "falsiflow-pages.yml"
    github_cross_platform_path = root / ".github" / "workflows" / "falsiflow-cross-platform.yml"
    github_publish_path = root / ".github" / "workflows" / "falsiflow-publish.yml"
    gitignore_path = root / ".gitignore"
    init_path = root / "falsiflow" / "__init__.py"
    templates_path = root / "falsiflow" / "templates"
    init_version = package_init_version(init_path)

    add("package_init_exists", init_path.exists(), "falsiflow/__init__.py exists.", init_path)

    if pyproject_path.exists():
        add("pyproject_exists", True, "pyproject.toml exists.", pyproject_path)
        add("readme_exists", readme_path.exists() and readme_path.stat().st_size > 0, "README.md exists and is non-empty.", readme_path)
        add("license_exists", license_path.exists() and license_path.stat().st_size > 0, "LICENSE exists and is non-empty.", license_path)
        add("changelog_exists", changelog_path.exists() and changelog_path.stat().st_size > 0, "CHANGELOG.md exists and is non-empty.", changelog_path)
        add("contributing_exists", contributing_path.exists() and contributing_path.stat().st_size > 0, "CONTRIBUTING.md exists and is non-empty.", contributing_path)
        add("release_guide_exists", release_path.exists() and release_path.stat().st_size > 0, "RELEASE.md exists and is non-empty.", release_path)
        add("security_policy_exists", security_path.exists() and security_path.stat().st_size > 0, "SECURITY.md exists and is non-empty.", security_path)
        add("responsible_use_exists", responsible_use_path.exists() and responsible_use_path.stat().st_size > 0, "RESPONSIBLE_USE.md exists and is non-empty.", responsible_use_path)
        add("adoption_priorities_exists", adoption_priorities_path.exists() and adoption_priorities_path.stat().st_size > 0, "Adoption priorities doc exists and is non-empty.", adoption_priorities_path)
        add("walkthrough_exists", walkthrough_path.exists() and walkthrough_path.stat().st_size > 0, "examples/README.md exists and is non-empty.", walkthrough_path)
        add("manifest_exists", manifest_path.exists() and manifest_path.stat().st_size > 0, "MANIFEST.in exists and is non-empty.", manifest_path)

        pyproject_text = pyproject_path.read_text(encoding="utf-8")
        readme_text = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
        license_text = license_path.read_text(encoding="utf-8") if license_path.exists() else ""
        changelog_text = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
        contributing_text = contributing_path.read_text(encoding="utf-8") if contributing_path.exists() else ""
        release_text = release_path.read_text(encoding="utf-8") if release_path.exists() else ""
        security_text = security_path.read_text(encoding="utf-8") if security_path.exists() else ""
        responsible_use_text = responsible_use_path.read_text(encoding="utf-8") if responsible_use_path.exists() else ""
        adoption_priorities_text = adoption_priorities_path.read_text(encoding="utf-8") if adoption_priorities_path.exists() else ""
        walkthrough_text = walkthrough_path.read_text(encoding="utf-8") if walkthrough_path.exists() else ""
        manifest_text = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else ""
        makefile_text = makefile_path.read_text(encoding="utf-8") if makefile_path.exists() else ""
        install_script_text = install_script_path.read_text(encoding="utf-8") if install_script_path.exists() else ""
        powershell_install_text = powershell_install_path.read_text(encoding="utf-8") if powershell_install_path.exists() else ""
        github_ci_text = github_ci_path.read_text(encoding="utf-8") if github_ci_path.exists() else ""
        github_pages_text = github_pages_path.read_text(encoding="utf-8") if github_pages_path.exists() else ""
        github_cross_platform_text = github_cross_platform_path.read_text(encoding="utf-8") if github_cross_platform_path.exists() else ""
        github_publish_text = github_publish_path.read_text(encoding="utf-8") if github_publish_path.exists() else ""
        gitignore_text = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
        gitignore_patterns = {line.strip() for line in gitignore_text.splitlines() if line.strip() and not line.lstrip().startswith("#")}

        data = pyproject_data(pyproject_path)
        project_name = get_nested(data, "project", "name") if data else None
        project_version = get_nested(data, "project", "version") if data else None
        readme_value = get_nested(data, "project", "readme") if data else None
        license_value = get_nested(data, "project", "license") if data else None
        scripts = get_nested(data, "project", "scripts") if data else None
        packages = get_nested(data, "tool", "setuptools", "packages") if data else None
        package_data = get_nested(data, "tool", "setuptools", "package-data", "falsiflow") if data else None

        add("pyproject_name", project_name == "falsiflow" if data else 'name = "falsiflow"' in pyproject_text, "Project name is falsiflow.", pyproject_path)
        add("pyproject_version", bool(project_version) if data else bool(re.search(r'^version\s*=\s*"[^"]+"', pyproject_text, flags=re.MULTILINE)), "Project version is declared.", pyproject_path)
        if data:
            add("version_matches_init", bool(project_version) and project_version == init_version, "pyproject version matches falsiflow.__version__.", init_path)
        else:
            add("version_matches_init", init_version in pyproject_text and bool(init_version), "pyproject version matches falsiflow.__version__.", init_path)
        add("readme_declared", readme_value == "README.md" if data else 'readme = "README.md"' in pyproject_text, "pyproject readme points to README.md.", pyproject_path)
        add("license_declared", isinstance(license_value, dict) and license_value.get("file") == "LICENSE" if data else 'file = "LICENSE"' in pyproject_text, "pyproject license points to LICENSE.", pyproject_path)
        add("console_script", isinstance(scripts, dict) and scripts.get("falsiflow") == "falsiflow.cli:main" if data else 'falsiflow = "falsiflow.cli:main"' in pyproject_text, "Console script points to falsiflow.cli:main.", pyproject_path)
        add("setuptools_package", isinstance(packages, list) and "falsiflow" in packages if data else 'packages = ["falsiflow"]' in pyproject_text, "setuptools includes the falsiflow package.", pyproject_path)
        expected_data_patterns = {"templates/*/*.json", "templates/*/*.csv", "templates/*/source_files/*.csv"}
        if data:
            package_data_set = set(package_data) if isinstance(package_data, list) else set()
            package_data_ready = expected_data_patterns <= package_data_set
        else:
            package_data_ready = all(pattern in pyproject_text for pattern in expected_data_patterns)
        add("template_package_data", package_data_ready, "Package data includes template JSON, CSV, and source CSV files.", pyproject_path)
        add("readme_release_commands", all(token in readme_text for token in ["release-check", "verify-bundle", "falsiflow selftest"]), "README documents release, verification, and selftest commands.", readme_path)
        add("readme_adoption_entry", all(token in readme_text for token in ["Project Priorities", "Five-Minute Quickstart", "quickstart", "doctor", "Adoption Path", "falsiflow_adoption_priorities.md"]), "README documents adoption priorities and first-run path.", readme_path)
        add("start_docs", all(token in readme_text for token in ["falsiflow start", "free localhost port", "falsiflow start --check --json", "beginner entry point"]), "README documents the beginner local app command.", readme_path)
        add("install_docs", all(token in readme_text for token in ["scripts/install_local.sh", "make install-local", "make start", "FALSIFLOW_REPO_URL", "virtual environment"]), "README documents one-command local installation.", readme_path)
        add("install_script", all(token in install_script_text for token in ["FALSIFLOW_REPO_URL", "python3 -m venv", "pip install -e", "falsiflow\" start", "--from-local"]), "scripts/install_local.sh installs into a virtual environment and starts the local app.", install_script_path)
        add("powershell_install_script", all(token in powershell_install_text for token in ["FALSIFLOW_REPO_URL", "python -m venv", "pip install -e", "falsiflow.exe", "FromLocal"]), "scripts/install_local.ps1 installs into a virtual environment and starts the local app.", powershell_install_path)
        add("pipx_docs", all(token in readme_text + makefile_text for token in ["make pipx-install", "make pipx-start", "pipx install --force ."]), "README and Makefile document pipx installation.", readme_path)
        add("onboard_docs", all(token in readme_text for token in ["falsiflow onboard --check --json", "onboard_summary.json", "beginner-friendly next-step checklist"]), "README documents beginner onboarding.", readme_path)
        add("static_demo_docs", all(token in readme_text for token in ["falsiflow static-demo", "static_demo_summary.json", "GitHub Pages", "Netlify"]), "README documents static zero-install demo export.", readme_path)
        add("demo_package_docs", all(token in readme_text for token in ["falsiflow demo-package", "demo_package_summary.json", "external_url_required", "FALSIFLOW_PUBLIC_DEMO_URL"]), "README documents public demo packaging and hosted URL handoff.", readme_path)
        add("publish_kit_docs", all(token in readme_text for token in ["falsiflow publish-kit", "publish_handoff.json", "github_publish_commands.sh", "account_action_required"]), "README documents the public release handoff kit for account-bound steps.", readme_path)
        add("external_check_docs", all(token in readme_text for token in ["falsiflow external-check", "external_readiness.json", "external_ready", "external_blocked"]), "README documents external publication readiness checks.", readme_path)
        add("workbench_docs", all(token in readme_text for token in ["workbench.html", "upload `project.json`", "raw source files", "ready/blocked status"]), "README documents the browser workbench closed loop.", readme_path)
        add("discover_docs", all(token in readme_text for token in ["falsiflow discover", "evidence_records.json", "candidate_queue.json", "ai_used=false", "claim_ready=false"]), "README documents structured discovery outputs and the non-claim boundary.", readme_path)
        add("public_interface_docs", all(token in readme_text for token in ["falsiflow agent discover", "falsiflow candidate rank", "falsiflow assay-plan", "falsiflow evidence import"]), "README documents the structured discovery and evidence public interfaces.", readme_path)
        add("makefile_entrypoints", all(token in makefile_text for token in ["install-local:", "pipx-install:", "start:", "start-check:", "onboard-check:", "static-demo:", "demo-package:", "publish-kit:", "external-check:", "release-check:"]), "Makefile exposes install, pipx, start, onboarding, static-demo, demo-package, publish-kit, external-check, and release-check shortcuts.", makefile_path)
        add("github_ci_workflow", all(token in github_ci_text for token in ["regress_falsiflow_core.py", "release-check", "template-pack", "template-release", "demo-package", "agent discover", "evidence import", "evidence-record"]), "GitHub Actions CI workflow covers regression, release-check, public interfaces, and template supply-chain gates.", github_ci_path)
        add("github_pages_workflow", all(token in github_pages_text for token in ["demo-package", "upload-pages-artifact", "deploy-pages", "pages: write"]), "GitHub Pages workflow builds and deploys the static demo package.", github_pages_path)
        add("github_cross_platform_workflow", all(token in github_cross_platform_text for token in ["ubuntu-latest", "macos-latest", "windows-latest", "pipx", "install_local.ps1", "external-check"]), "GitHub Actions cross-platform workflow covers Linux, macOS, Windows, pipx, installers, and external-check smoke.", github_cross_platform_path)
        add("github_pypi_publish_workflow", all(token in github_publish_text for token in ["python -m build", "python -m twine check dist/*", "pypa/gh-action-pypi-publish", "id-token: write"]), "GitHub Actions publish workflow builds, checks, stores, and can publish PyPI distributions.", github_publish_path)
        add("try_docs", all(token in readme_text for token in ["falsiflow try", "try_report.html", "Falsiflow Try", "dashboard.html"]), "README documents the low-friction local browser demo.", readme_path)
        add("launchpad_docs", all(token in readme_text for token in ["index.html", "Falsiflow Launchpad", "try_report_url", "wizard_url"]), "README documents the first-run local browser launchpad.", readme_path)
        add("wizard_docs", all(token in readme_text for token in ["falsiflow wizard", "falsiflow_wizard.html", "Falsiflow Browser Wizard", "plain-language presets", "falsiflow scaffold"]), "README documents the browser wizard for drafting claim gates.", readme_path)
        add("serve_docs", all(token in readme_text for token in ["falsiflow serve", "localhost", "serve_summary.json", "try_report.html"]), "README documents the localhost browser demo.", readme_path)
        add("quickstart_docs", all(token in readme_text for token in ["quickstart", "quickstart_summary.json", "next_commands", "Falsiflow Quickstart", "quickstart_ready", "quickstart_blocked"]), "README documents the one-command first-run quickstart.", readme_path)
        add("doctor_docs", all(token in readme_text for token in ["doctor", "doctor_summary.json", "repair_checklist", "Falsiflow Doctor", "doctor_ready", "doctor_blocked"]), "README documents the one-command project health diagnosis.", readme_path)
        add("claim_check_docs", all(token in readme_text for token in ["claim-check", "--project-dir", "claim_check.json", "Falsiflow Claim Check", "claim_check_ready", "claim_check_blocked"]), "README documents the one-command claim gate.", readme_path)
        add("adoption_check_docs", all(token in readme_text for token in ["adoption-check", "adoption_check.json", "Falsiflow Adoption Check", "adoption_ready", "adoption_blocked", "repair_checklist", "adoption_recheck", "release_validation_status"]), "README documents the priority-readiness adoption gate.", readme_path)
        add("audit_review_docs", all(token in readme_text for token in ["audit_review.json", "audit_review.md", "Falsiflow Audit Review", "review_ready", "review_blocked"]), "README documents trusted audit review decision cards.", readme_path)
        add("template_check_docs", all(token in readme_text for token in ["template-check", "placeholder_evidence", "template_ready"]), "README documents external template authoring checks.", readme_path)
        add("template_scaffold_docs", all(token in readme_text for token in ["template-scaffold", "evidence_pass_demo.csv", "template_scaffolded"]), "README documents starter template generation.", readme_path)
        add("template_pack_docs", all(token in readme_text for token in ["template-pack", "verify-template-pack", "template_pack_verified"]), "README documents starter template packaging and verification.", readme_path)
        add("template_install_docs", all(token in readme_text for token in ["template-install", "falsiflow_template_index.json", "template_installed", "--require-attestation"]), "README documents verified starter template installation.", readme_path)
        add("template_registry_docs", all(token in readme_text for token in ["template-registry", "template-lock", "falsiflow_template_lock.json", "source_url", "--version"]), "README documents template registry and lockfile workflows.", readme_path)
        add("template_attestation_docs", all(token in readme_text for token in ["template-attest", "verify-template-attestation", "template_attestation_verified"]), "README documents template lock attestations and verification.", readme_path)
        add("template_policy_docs", all(token in readme_text for token in ["template-policy", "verify-template-policy", "template_policy_verified", "--policy"]), "README documents template adoption policies.", readme_path)
        add("template_release_docs", all(token in readme_text for token in ["template-release", "verify-template-release", "template_release_verified", "template_release_verification.md", "--release"]), "README documents template release bundles.", readme_path)
        add("template_gallery_docs", all(token in readme_text for token in ["template-gallery", "Falsiflow Template Gallery", "rfq_vendor_evidence", "biointerface_coatings", "wetware_support_hardware"]), "README documents the template gallery and cross-domain starter breadth.", readme_path)
        add("license_mit", "MIT License" in license_text, "LICENSE declares MIT License.", license_path)
        current_version = str(project_version or init_version)
        add("changelog_current_version", bool(current_version) and current_version in changelog_text, "CHANGELOG includes the current version.", changelog_path)
        add("contributing_gates", all(token in contributing_text for token in ["release-check", "claim_ready", "CHANGELOG.md"]), "CONTRIBUTING.md documents gates, tests, and changelog expectations.", contributing_path)
        add("release_checklist", all(token in release_text for token in ["release_ready", "package_ready", "dist_ready", "release_validation_ready", "demo_package_ready", "publish_kit_ready", "external_check_status", "release-check"]), "RELEASE.md documents required release gates.", release_path)
        add("security_policy", all(token in security_text for token in ["vulnerability", "verify-bundle", "SHA-256"]), "SECURITY.md documents vulnerability reporting and bundle integrity risks.", security_path)
        add("responsible_use_policy", all(token in responsible_use_text for token in ["not proof", "regulatory compliance", "independent"]), "RESPONSIBLE_USE.md documents evidence limitations and independent validation boundaries.", responsible_use_path)
        add("adoption_priorities", all(token in adoption_priorities_text for token in ["Open-source entry point", "Trusted audit experience", "Generality proof", "Release and distribution", "User experience convergence"]), "Adoption priorities record the current optimization order.", adoption_priorities_path)
        add("walkthrough_commands", all(token in walkthrough_text for token in ["init", "claim-check", "claim_check_ready", "audit", "sources", "bundle", "verify-bundle", "release-check", "bundle_verified"]), "examples/README.md documents the end-to-end verified-bundle walkthrough.", walkthrough_path)
        add("manifest_release_docs", all(token in manifest_text for token in ["CHANGELOG.md", "CONTRIBUTING.md", "RELEASE.md", "SECURITY.md", "RESPONSIBLE_USE.md", "examples/README.md", "docs/falsiflow_adoption_priorities.md", "scripts/install_local.sh", "scripts/install_local.ps1", "Makefile", ".github/workflows"]), "MANIFEST.in includes release, security, responsible-use, walkthrough, installers, Makefile, workflows, and adoption docs in source distributions.", manifest_path)
        add("gitignore_build_artifacts", {"build/", "dist/", "*.egg-info/"} <= gitignore_patterns, ".gitignore excludes local build caches and package metadata artifacts.", gitignore_path)
    else:
        add("installed_metadata_mode", True, "Source metadata files are absent; checking installed package metadata.", root)
        try:
            distribution = importlib_metadata.distribution("falsiflow")
            metadata = distribution.metadata
            entry_points = list(distribution.entry_points)
            installed_version = distribution.version
            add("installed_name", metadata.get("Name", "").lower() == "falsiflow", "Installed package metadata name is falsiflow.", root)
            add("installed_version", bool(installed_version), "Installed package version is declared.", root)
            add("installed_version_matches_init", bool(init_version) and installed_version == init_version, "Installed version matches falsiflow.__version__.", init_path)
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


def command_excerpt(completed: subprocess.CompletedProcess[str]) -> str:
    output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)
    return output[-1000:] if output else f"exit code {completed.returncode}"


def dist_release_checks(root: Path, artifact_root: Path, run_dist: bool) -> dict[str, object]:
    checks: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    def add(check_id: str, ok: bool, message: str, path: Path | str = "") -> None:
        checks.append(release_check_item(check_id, ok, message, path))
        if not ok:
            failures.append(failure_record("dist", check_id, message))

    dist_root = artifact_root / "dist"
    wheel_dir = dist_root / "wheel"
    sdist_dir = dist_root / "sdist"
    install_dir = dist_root / "installed"
    installed_check_dir = dist_root / "installed_release_check"
    pyproject_path = root / "pyproject.toml"
    build_dir = root / "build"
    egg_info = root / "falsiflow.egg-info"
    build_dir_existed = build_dir.exists()
    egg_info_existed = egg_info.exists()
    if not run_dist:
        add("dist_skipped", True, "Distribution build check was skipped by request.", dist_root)
        return {"status": "dist_skipped", "check_count": len(checks), "failure_count": 0, "checks": checks, "failures": failures}
    if not pyproject_path.exists():
        add("dist_skipped_no_pyproject", True, "Distribution build check skipped outside a source tree.", root)
        return {"status": "dist_skipped", "check_count": len(checks), "failure_count": 0, "checks": checks, "failures": failures}

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
        import setuptools.build_meta as build_meta

        build_stdout = io.StringIO()
        build_stderr = io.StringIO()
        with contextlib.redirect_stdout(build_stdout), contextlib.redirect_stderr(build_stderr):
            sdist_name = build_meta.build_sdist(str(sdist_dir))
        add("sdist_build", bool(sdist_name), "Source distribution builds with setuptools.build_meta.", sdist_dir / sdist_name if sdist_name else sdist_dir)
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
                f"{base}/RELEASE.md",
                f"{base}/SECURITY.md",
                f"{base}/RESPONSIBLE_USE.md",
                f"{base}/MANIFEST.in",
                f"{base}/.github/workflows/falsiflow.yml",
                f"{base}/.github/workflows/falsiflow-pages.yml",
                f"{base}/.github/workflows/falsiflow-cross-platform.yml",
                f"{base}/.github/workflows/falsiflow-publish.yml",
                f"{base}/docs/falsiflow_adoption_priorities.md",
                f"{base}/examples/README.md",
                f"{base}/falsiflow/cli.py",
                f"{base}/falsiflow/core.py",
                f"{base}/falsiflow/templates/neural_materials/project.json",
                f"{base}/falsiflow/templates/neural_materials/source_files/demo_raw_export.csv",
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
                    add("installed_templates", installed_summary.get("template_count") == 4 and installed_summary.get("bundle_verified_count") == 4, "Installed wheel exposes all starter templates and verifies their bundles.", installed_check_dir / "release_check.json")
                except json.JSONDecodeError as exc:
                    add("installed_templates", False, f"Installed release-check did not return JSON: {exc}", installed_check_dir)

    cleanup_errors: list[str] = []
    for generated_path, existed_before in [(egg_info, egg_info_existed), (build_dir, build_dir_existed)]:
        if not existed_before and (generated_path.exists() or generated_path.is_symlink()):
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
        and (egg_info_existed or not (egg_info.exists() or egg_info.is_symlink()))
        and (build_dir_existed or not (build_dir.exists() or build_dir.is_symlink())),
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


def build_adoption_check_summary(
    package: dict[str, object],
    dist: dict[str, object],
    quickstart_summary: dict[str, object],
    doctor_summary: dict[str, object],
    claim_check_summary: dict[str, object],
    template_gallery: dict[str, object],
    artifact_root: Path,
    adoption_rerun_root: Path | None = None,
) -> dict[str, object]:
    package_checks = package_check_lookup(package)
    dist_checks = package_check_lookup(dist)
    installed_mode = "installed_metadata_mode" in package_checks
    quickstart_outputs = quickstart_summary.get("outputs", {}) if isinstance(quickstart_summary.get("outputs", {}), dict) else {}
    doctor_outputs = doctor_summary.get("outputs", {}) if isinstance(doctor_summary.get("outputs", {}), dict) else {}
    claim_outputs = claim_check_summary.get("outputs", {}) if isinstance(claim_check_summary.get("outputs", {}), dict) else {}
    gallery_templates = [
        template
        for template in template_gallery.get("templates", [])
        if isinstance(template, dict)
    ]

    open_source_checks = [
        package_check_item(package_checks, "readme_adoption_entry", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "quickstart_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "walkthrough_commands", installed_mode=installed_mode, installed_ok=True),
        release_check_item(
            "quickstart_ready",
            quickstart_summary.get("status") == "quickstart_ready",
            f"Quickstart ended as {quickstart_summary.get('status', '')}.",
            str(quickstart_outputs.get("quickstart_summary", "")),
        ),
        release_check_item(
            "quickstart_doctor_handoff",
            command_list_contains(quickstart_summary.get("next_commands", []), "doctor --project-dir"),
            "Quickstart tells the user to run doctor next.",
            str(quickstart_outputs.get("quickstart_report", "")),
        ),
    ]

    trusted_audit_checks = [
        package_check_item(package_checks, "audit_review_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "claim_check_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "doctor_docs", installed_mode=installed_mode, installed_ok=True),
        release_check_item(
            "claim_check_ready",
            claim_check_summary.get("status") == "claim_check_ready",
            f"Claim check ended as {claim_check_summary.get('status', '')}.",
            str(claim_outputs.get("claim_check", "")),
        ),
        release_check_item(
            "doctor_ready",
            doctor_summary.get("status") == "doctor_ready",
            f"Doctor ended as {doctor_summary.get('status', '')}.",
            str(doctor_outputs.get("doctor_summary", "")),
        ),
        release_check_item(
            "doctor_repair_checklist",
            isinstance(doctor_summary.get("repair_checklist", []), list) and bool(doctor_summary.get("repair_checklist", [])),
            "Doctor emits a repair checklist with commands, expected artifacts, and success signals.",
            str(doctor_outputs.get("doctor_report", "")),
        ),
    ]

    generality_checks = [
        package_check_item(package_checks, "template_gallery_docs", installed_mode=installed_mode, installed_ok=True),
        release_check_item(
            "template_gallery_ready",
            template_gallery.get("status") == "template_gallery_ready",
            f"Template gallery ended as {template_gallery.get('status', '')}.",
            str(template_gallery.get("json_path", "")),
        ),
        release_check_item(
            "template_gallery_breadth",
            int(template_gallery.get("template_count", 0) or 0) >= 4,
            "Template gallery covers at least four starter workflows.",
            str(template_gallery.get("json_path", "")),
        ),
        release_check_item(
            "non_neural_template_breadth",
            int(template_gallery.get("non_neural_template_count", 0) or 0) >= 3,
            "Template gallery includes at least three non-neural starter workflows.",
            str(template_gallery.get("json_path", "")),
        ),
        release_check_item(
            "template_doctor_handoffs",
            bool(gallery_templates) and all(command_list_contains(template.get("first_commands", []), "doctor --project-dir") for template in gallery_templates),
            "Every starter template exposes a doctor handoff in first_commands.",
            str(template_gallery.get("json_path", "")),
        ),
    ]

    release_distribution_checks = [
        release_check_item(
            "package_ready",
            package.get("status") == "package_ready",
            f"Package checks ended as {package.get('status', '')}.",
            ROOT,
        ),
        release_check_item(
            "dist_ready_or_skipped",
            dist.get("status") in {"dist_ready", "dist_skipped"},
            f"Distribution checks ended as {dist.get('status', '')}.",
            artifact_root / "dist",
        ),
        package_check_any_item(package_checks, "console_script", ["console_script", "installed_console_script"], installed_mode=installed_mode),
        package_check_any_item(package_checks, "template_package_data", ["template_package_data", "template_package_root"], installed_mode=installed_mode),
        package_check_item(package_checks, "gitignore_build_artifacts", installed_mode=installed_mode, installed_ok=True),
        dist_check_item(
            dist_checks,
            "source_build_cache_cleanup",
            dist_status=str(dist.get("status", "")),
            dist_root=artifact_root / "dist",
            skipped_ok=True,
        ),
        package_check_item(package_checks, "manifest_release_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "release_checklist", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "template_release_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "template_install_docs", installed_mode=installed_mode, installed_ok=True),
    ]

    user_experience_checks = [
        package_check_item(package_checks, "adoption_priorities", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "adoption_check_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "doctor_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "quickstart_docs", installed_mode=installed_mode, installed_ok=True),
        release_check_item(
            "quickstart_doctor_handoff",
            command_list_contains(quickstart_summary.get("next_commands", []), "doctor --project-dir"),
            "Quickstart gives a concrete next command for project diagnosis.",
            str(quickstart_outputs.get("quickstart_report", "")),
        ),
        release_check_item(
            "doctor_repair_checklist",
            isinstance(doctor_summary.get("repair_checklist", []), list) and bool(doctor_summary.get("repair_checklist", [])),
            "Doctor gives repair commands and expected artifacts.",
            str(doctor_outputs.get("doctor_report", "")),
        ),
        release_check_item(
            "claim_check_next_actions",
            isinstance(claim_check_summary.get("next_actions", []), list) and bool(claim_check_summary.get("next_actions", [])),
            "Claim check provides next actions for human review or repair.",
            str(claim_outputs.get("claim_check_report", "")),
        ),
    ]

    priorities = [
        adoption_priority(
            "open_source_entry_point",
            "Open-source entry point",
            open_source_checks,
            [
                "Keep README adoption path, quickstart docs, and examples walkthrough in sync with the CLI.",
                "Run `falsiflow quickstart --template biointerface_coatings --out /tmp/falsiflow_quickstart --strict --json`.",
            ],
        ),
        adoption_priority(
            "trusted_audit_experience",
            "Trusted audit experience",
            trusted_audit_checks,
            [
                "Run `falsiflow doctor --project-dir <project> --strict` and inspect doctor_summary.json.",
                "Repair claim-check, audit-review, source, bundle, or verification blockers before sharing a claim.",
            ],
        ),
        adoption_priority(
            "generality_proof",
            "Generality proof",
            generality_checks,
            [
                "Run `falsiflow template-gallery --json` and keep non-neural templates passing.",
                "Add or repair starter templates until cross-domain coverage is visible from first_commands.",
            ],
        ),
        adoption_priority(
            "release_and_distribution",
            "Release and distribution",
            release_distribution_checks,
            [
                "Run `falsiflow release-check --out-dir <dir> --json --force` before tagging a release.",
                "Run adoption-check without `--skip-dist` when validating a distributable source tree.",
            ],
        ),
        adoption_priority(
            "user_experience_convergence",
            "User experience convergence",
            user_experience_checks,
            [
                "Keep the priority order, adoption-check docs, quickstart handoff, and doctor repair checklist aligned.",
                "Use adoption_check.json as the single status artifact when answering priority-completion questions.",
            ],
        ),
    ]

    failures: list[dict[str, str]] = []
    for priority in priorities:
        for check in priority.get("checks", []):
            if isinstance(check, dict) and check.get("status") != "passed":
                failures.append(failure_record(str(priority.get("priority_id", "")), str(check.get("check", "")), str(check.get("message", ""))))

    release_validation_status, release_validation_message = adoption_release_validation_status(str(dist.get("status", "")))
    ready_priority_count = sum(1 for priority in priorities if priority.get("status") == "priority_ready")
    priority_count = len(priorities)
    outputs = {
        "adoption_check": str(artifact_root / "adoption_check.json"),
        "adoption_report": str(artifact_root / "adoption_check.md"),
        "template_gallery": str(template_gallery.get("json_path", artifact_root / "template_gallery.json")),
        "quickstart_summary": str(quickstart_outputs.get("quickstart_summary", "")),
        "doctor_summary": str(doctor_outputs.get("doctor_summary", "")),
        "claim_check": str(claim_outputs.get("claim_check", "")),
    }
    return {
        "status": "adoption_ready" if ready_priority_count == priority_count else "adoption_blocked",
        "artifact_root": str(artifact_root),
        "package_status": str(package.get("status", "")),
        "dist_status": str(dist.get("status", "")),
        "release_validation_status": release_validation_status,
        "release_validation_message": release_validation_message,
        "quickstart_status": str(quickstart_summary.get("status", "")),
        "doctor_status": str(doctor_summary.get("status", "")),
        "claim_check_status": str(claim_check_summary.get("status", "")),
        "template_gallery_status": str(template_gallery.get("status", "")),
        "priority_count": priority_count,
        "ready_priority_count": ready_priority_count,
        "readiness_pct": round((ready_priority_count / priority_count) * 100, 1) if priority_count else 0.0,
        "failure_count": len(failures),
        "priorities": priorities,
        "failures": failures,
        "outputs": outputs,
        "repair_checklist": adoption_repair_checklist(
            priorities,
            artifact_root,
            str(dist.get("status", "")),
            adoption_rerun_root=adoption_rerun_root,
        ),
    }


def write_adoption_check_artifacts(summary: dict[str, object], artifact_root: Path) -> None:
    (artifact_root / "adoption_check.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (artifact_root / "adoption_check.md").write_text(render_adoption_check_report(summary), encoding="utf-8")


def run_adoption_check(artifact_root: Path, run_dist: bool = False) -> dict[str, object]:
    artifact_root.mkdir(parents=True, exist_ok=True)
    package = package_release_checks(ROOT)
    dist = dist_release_checks(ROOT, artifact_root, run_dist)

    try:
        template_gallery = run_template_gallery(
            include_env=False,
            out=artifact_root / "template_gallery.md",
            json_out=artifact_root / "template_gallery.json",
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        template_gallery = {
            "status": "template_gallery_blocked",
            "template_count": 0,
            "non_neural_template_count": 0,
            "templates": [],
            "message": str(exc),
        }

    try:
        quickstart_summary = run_quickstart(
            "biointerface_coatings",
            artifact_root / "quickstart_project",
            force=True,
            include_env=False,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        quickstart_summary = {
            "status": "quickstart_blocked",
            "template": "biointerface_coatings",
            "project_dir": str(artifact_root / "quickstart_project"),
            "next_commands": [],
            "outputs": {},
            "message": str(exc),
        }

    try:
        quickstart_project_dir = artifact_root / "quickstart_project"
        doctor_summary = run_doctor(
            quickstart_project_dir,
            quickstart_project_dir / "project.json",
            default_project_evidence_path(quickstart_project_dir),
            artifact_root / "doctor",
            force=True,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        doctor_summary = {
            "status": "doctor_blocked",
            "project_dir": str(artifact_root / "quickstart_project"),
            "repair_checklist": [],
            "outputs": {},
            "message": str(exc),
        }

    try:
        claim_template_dir = template_path("neural_materials", include_env=False)
        if claim_template_dir is None:
            claim_check_summary = {
                "status": "claim_check_blocked",
                "next_actions": [],
                "outputs": {},
                "message": "neural_materials template was not found.",
            }
        else:
            claim_check_summary = run_claim_check(
                claim_template_dir / "project.json",
                claim_template_dir / "evidence_pass_demo.csv",
                artifact_root / "claim_check",
                force=True,
            )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        claim_check_summary = {
            "status": "claim_check_blocked",
            "next_actions": [],
            "outputs": {},
            "message": str(exc),
        }

    summary = build_adoption_check_summary(
        package,
        dist,
        quickstart_summary,
        doctor_summary,
        claim_check_summary,
        template_gallery,
        artifact_root,
    )
    write_adoption_check_artifacts(summary, artifact_root)
    return summary


def cmd_adoption_check(args: argparse.Namespace) -> int:
    prepare_output_directory(args.out_dir, "adoption-check output directory", force=args.force)
    summary = run_adoption_check(args.out_dir, run_dist=not args.skip_dist)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow adoption-check: {summary['status']}")
        print(f"Priorities: {summary['ready_priority_count']}/{summary['priority_count']}")
        print(f"Readiness: {summary['readiness_pct']}%")
        print(f"Release validation: {summary['release_validation_status']}")
        print(f"Package: {summary['package_status']}")
        print(f"Distribution: {summary['dist_status']}")
        print(f"Quickstart: {summary['quickstart_status']}")
        print(f"Doctor: {summary['doctor_status']}")
        print(f"Claim check: {summary['claim_check_status']}")
        print(f"Template gallery: {summary['template_gallery_status']}")
        print(f"Failures: {summary['failure_count']}")
        repair_checklist = summary.get("repair_checklist", [])
        if isinstance(repair_checklist, list) and repair_checklist:
            first_repair = repair_checklist[0]
            if isinstance(first_repair, dict):
                label = "Next check" if summary["status"] == "adoption_ready" else "First repair"
                print(f"{label}: {first_repair.get('action_id', '')}")
                print(f"Run: {first_repair.get('command', '')}")
        print(f"Wrote {args.out_dir / 'adoption_check.json'}")
        print(f"Wrote {args.out_dir / 'adoption_check.md'}")
        for failure in summary["failures"]:
            print(f"failure: {failure['stage']}:{failure['id']}: {failure['message']}")
    return 0 if summary["status"] == "adoption_ready" else 2


def run_release_check(artifact_root: Path, run_dist: bool = True) -> dict[str, object]:
    artifact_root.mkdir(parents=True, exist_ok=True)
    failures: list[dict[str, str]] = []

    package = package_release_checks(ROOT)
    failures.extend(package["failures"])
    dist = dist_release_checks(ROOT, artifact_root, run_dist)
    failures.extend(dist["failures"])
    demo_summary: dict[str, object]
    try:
        demo_summary = run_demo("neural_materials", artifact_root / "demo", force=True)
        if demo_summary.get("status") != "demo_ready":
            failures.append(failure_record("demo", "neural_materials", f"Demo ended as {demo_summary.get('status', '')}."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        demo_summary = {"status": "demo_failed", "template": "neural_materials", "message": str(exc)}
        failures.append(failure_record("demo", "neural_materials", str(exc)))

    try:
        demo_package_summary = run_demo_package("biointerface_coatings", artifact_root / "public_demo", [], force=True)
        if demo_package_summary.get("status") != "demo_package_ready":
            failures.append(failure_record("demo_package", "public_demo", f"Demo package ended as {demo_package_summary.get('status', '')}."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        demo_package_summary = {"status": "demo_package_failed", "template": "biointerface_coatings", "message": str(exc)}
        failures.append(failure_record("demo_package", "public_demo", str(exc)))

    try:
        external_check_summary = run_external_check(artifact_root / "external_readiness", force=True)
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
        publish_kit_summary = run_publish_kit(artifact_root / "publish_kit", "biointerface_coatings", [], force=True)
        if publish_kit_summary.get("status") != "publish_kit_ready":
            failures.append(failure_record("publish_kit", "handoff", f"Publish kit ended as {publish_kit_summary.get('status', '')}."))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        publish_kit_summary = {"status": "publish_kit_failed", "message": str(exc)}
        failures.append(failure_record("publish_kit", "handoff", str(exc)))

    quickstart_summary: dict[str, object]
    try:
        quickstart_summary = run_quickstart(
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
        doctor_summary = run_doctor(
            quickstart_project_dir,
            quickstart_project_dir / "project.json",
            default_project_evidence_path(quickstart_project_dir),
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
        claim_template_dir = template_path("neural_materials", include_env=False)
        if claim_template_dir is None:
            claim_check_summary = {"status": "claim_check_blocked", "message": "neural_materials template was not found."}
            failures.append(failure_record("claim_check", "neural_materials", "neural_materials template was not found."))
        else:
            claim_check_summary = run_claim_check(
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
    for kind in SCHEMA_KINDS:
        try:
            schema = falsiflow_schema(kind)
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
        records = template_records(include_env=False)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        records = []
        failures.append(failure_record("template_discovery", "templates", str(exc)))
    if not records:
        failures.append(failure_record("template_discovery", "templates", "No starter templates found."))

    try:
        template_gallery = run_template_gallery(
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

    template_check_results: list[dict[str, object]] = []
    for record in records:
        template_id = record["template"]
        try:
            template_check = run_template_check(Path(record["path"]), artifact_root / "template_checks" / template_id, force=True)
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
            template_pack_summary = run_template_pack(
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
            template_registry_summary = run_template_registry(
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
            template_lock_summary = run_template_lock(
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
                template_attestation_summary = run_template_attestation(
                    lock_path,
                    subject_type="template-lock",
                    out=template_attestation_path,
                    signing_key=release_attestation_key,
                    key_id="release-check",
                    builder="release-check",
                )
                if template_attestation_summary.get("status") != "template_attested":
                    failures.append(failure_record("template_attestation", str(template_pack_summary.get("template_id", "")), f"Template attestation ended as {template_attestation_summary.get('status', '')}."))
                template_attestation_verification_summary = run_verify_template_attestation(
                    template_attestation_path,
                    subject_path=lock_path,
                    signing_key=release_attestation_key,
                )
                if template_attestation_verification_summary.get("status") != "template_attestation_verified":
                    failures.append(failure_record("template_attestation_verify", str(template_pack_summary.get("template_id", "")), f"Template attestation verification ended as {template_attestation_verification_summary.get('status', '')}."))
                template_policy_summary = run_template_policy(
                    lock_path,
                    template_attestation_path,
                    out=template_policy_path,
                    signing_key=release_attestation_key,
                    policy_id="release-check:neural_materials",
                    owner="release-check",
                )
                if template_policy_summary.get("status") != "template_policy_ready":
                    failures.append(failure_record("template_policy", str(template_pack_summary.get("template_id", "")), f"Template policy ended as {template_policy_summary.get('status', '')}."))
                template_policy_verification_summary = run_verify_template_policy(
                    template_policy_path,
                    lock_path,
                    template_attestation_path,
                    signing_key=release_attestation_key,
                )
                if template_policy_verification_summary.get("status") != "template_policy_verified":
                    failures.append(failure_record("template_policy_verify", str(template_pack_summary.get("template_id", "")), f"Template policy verification ended as {template_policy_verification_summary.get('status', '')}."))
                template_release_path = artifact_root / "template_release.zip"
                template_release_summary = run_template_release(
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
                template_release_verification_summary = run_verify_template_release(
                    template_release_path,
                    signing_key=release_attestation_key,
                    extract_dir=artifact_root / "template_release_extract",
                )
                (artifact_root / "template_release_verification.json").write_text(
                    json.dumps(template_release_verification_summary, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                (artifact_root / "template_release_verification.md").write_text(
                    render_template_release_verification_report(template_release_verification_summary),
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
                    lock = read_json_object(release_lock_path, "template lock")
                    template_install_summary = run_template_install(
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
            bundle = build_bundle(config_path, evidence_path, bundle_dir, bundle_zip, force=True)
            verification = verify_bundle_zip(bundle_zip)
            verification_json.write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")
            verification_report.write_text(render_bundle_verification_report(verification), encoding="utf-8")
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
            portfolio = write_portfolio_artifacts(claim_summary_paths, artifact_root / "portfolio")
            if portfolio["blocked_count"] != 0:
                failures.append(failure_record("portfolio", "release_templates", f"Portfolio has {portfolio['blocked_count']} blocked claim(s)."))
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            failures.append(failure_record("portfolio", "release_templates", str(exc)))
    else:
        failures.append(failure_record("portfolio", "release_templates", "No ready bundle claim summaries were produced."))

    adoption_check_summary = build_adoption_check_summary(
        package,
        dist,
        quickstart_summary,
        doctor_summary,
        claim_check_summary,
        template_gallery,
        artifact_root,
        adoption_rerun_root=artifact_root / "adoption_recheck",
    )
    write_adoption_check_artifacts(adoption_check_summary, artifact_root)
    if adoption_check_summary.get("status") != "adoption_ready":
        for failure in adoption_check_summary.get("failures", []):
            if isinstance(failure, dict):
                failures.append(failure_record("adoption_check", str(failure.get("id", "")), str(failure.get("message", ""))))

    release_validation_status, release_validation_message = release_validation_status_for_dist(str(dist.get("status", "")))
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
    return summary


def cmd_release_check(args: argparse.Namespace) -> int:
    prepare_output_directory(args.out_dir, "release-check output directory", force=args.force)
    summary = run_release_check(args.out_dir, run_dist=not args.skip_dist)
    (args.out_dir / "release_check.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (args.out_dir / "release_check.md").write_text(render_release_check_report(summary), encoding="utf-8")
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow release-check: {summary['status']}")
        print(f"Package: {summary['package_status']}")
        print(f"Distribution: {summary['dist_status']}")
        print(f"Release validation: {summary['release_validation_status']}")
        print(f"Demo: {summary['demo_status']}")
        print(f"Demo package: {summary['demo_package_status']}")
        print(f"Publish kit: {summary['publish_kit_status']}")
        print(f"External readiness: {summary['external_check_status']}")
        print(f"Schemas: {summary['schema_count']}")
        print(f"Template gallery: {summary['template_gallery_status']}")
        print(f"Template checks: {summary['template_check_ready_count']}/{summary['template_check_count']}")
        print(f"Template pack: {summary['template_pack_status']} / {summary['template_pack_verification_status']}")
        print(f"Template registry: {summary['template_registry_status']}")
        print(f"Template lock: {summary['template_lock_status']}")
        print(f"Template attestation: {summary['template_attestation_status']} / {summary['template_attestation_verification_status']}")
        print(f"Template policy: {summary['template_policy_status']} / {summary['template_policy_verification_status']}")
        print(f"Template release: {summary['template_release_status']} / {summary['template_release_verification_status']}")
        print(f"Template install: {summary['template_install_status']}")
        print(f"Quickstart: {summary['quickstart_status']}")
        print(f"Doctor: {summary['doctor_status']}")
        print(f"Claim check: {summary['claim_check_status']}")
        adoption_summary = summary.get("adoption_check_summary", {})
        if isinstance(adoption_summary, dict):
            print(f"Adoption check: {summary['adoption_check_status']} ({adoption_summary.get('ready_priority_count', 0)}/{adoption_summary.get('priority_count', 0)} priorities)")
            print(f"Adoption release validation: {adoption_summary.get('release_validation_status', '')}")
            repair_checklist = adoption_summary.get("repair_checklist", [])
            if isinstance(repair_checklist, list) and repair_checklist:
                first_repair = repair_checklist[0]
                if isinstance(first_repair, dict):
                    label = "Next adoption check" if summary["adoption_check_status"] == "adoption_ready" else "First adoption repair"
                    print(f"{label}: {first_repair.get('action_id', '')}")
                    print(f"Run: {first_repair.get('command', '')}")
        else:
            print(f"Adoption check: {summary['adoption_check_status']}")
        print(f"Templates: {summary['template_count']}")
        print(f"Ready audits: {summary['audit_ready_count']}")
        print(f"Verified bundles: {summary['bundle_verified_count']}")
        print(f"Failures: {summary['failure_count']}")
        print(f"Wrote {args.out_dir / 'release_check.json'}")
        print(f"Wrote {args.out_dir / 'release_check.md'}")
        print(f"Wrote {args.out_dir / 'adoption_check.json'}")
        print(f"Wrote {args.out_dir / 'adoption_check.md'}")
        for failure in summary["failures"]:
            print(f"failure: {failure['stage']}:{failure['id']}: {failure['message']}")
    return 0 if summary["status"] == "release_ready" else 2


def run_selftest(artifact_root: Path, keep_artifacts: bool) -> dict[str, object]:
    failures: list[dict[str, str]] = []
    schemas: list[dict[str, object]] = []
    for kind in SCHEMA_KINDS:
        try:
            schema = falsiflow_schema(kind)
            ok = isinstance(schema, dict) and bool(schema)
            schemas.append({"kind": kind, "status": "passed" if ok else "failed"})
            if not ok:
                failures.append({"stage": "schema", "id": kind, "message": "Schema payload was empty."})
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            schemas.append({"kind": kind, "status": "failed"})
            failures.append({"stage": "schema", "id": kind, "message": str(exc)})

    try:
        records = template_records(include_env=False)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        records = []
        failures.append({"stage": "template_discovery", "id": "templates", "message": str(exc)})
    if not records:
        failures.append({"stage": "template_discovery", "id": "templates", "message": "No starter templates found."})

    templates: list[dict[str, object]] = []
    claim_summary_paths: list[Path] = []
    for record in records:
        template_id = record["template"]
        template_dir = Path(record["path"])
        config_path = Path(record["project_config"])
        evidence_path = template_dir / "evidence_pass_demo.csv"
        audit_dir = artifact_root / template_id
        template_result: dict[str, object] = {
            "template": template_id,
            "validation_status": record["status"],
            "project_id": record["project_id"],
            "audit_status": "not_run",
            "claim_ready": False,
            "audit_dir": str(audit_dir) if keep_artifacts else "",
        }

        if record["status"] != "valid":
            failures.append({
                "stage": "template_validation",
                "id": template_id,
                "message": f"Template config is {record['status']}.",
            })
            templates.append(template_result)
            continue
        if not evidence_path.exists():
            failures.append({
                "stage": "template_audit",
                "id": template_id,
                "message": "Missing evidence_pass_demo.csv.",
            })
            templates.append(template_result)
            continue

        try:
            project = load_project(config_path)
            rows, evidence_issues = read_csv_rows_with_diagnostics(evidence_path)
            rendered = write_render_artifacts(project, rows, audit_dir, evidence_file_issues=evidence_issues)
            audit = rendered["audit"]
            template_result["audit_status"] = audit["status"]
            template_result["claim_ready"] = bool(audit["claim_ready"])
            template_result["evidence_error_count"] = audit["evidence_error_count"]
            template_result["evidence_warning_count"] = audit["evidence_warning_count"]
            if audit["claim_ready"]:
                claim_summary_paths.append(audit_dir / "claim_summary.json")
            else:
                failures.append({
                    "stage": "template_audit",
                    "id": template_id,
                    "message": f"Demo audit ended as {audit['status']}.",
                })
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            template_result["audit_status"] = "failed"
            failures.append({"stage": "template_audit", "id": template_id, "message": str(exc)})
        templates.append(template_result)

    portfolio: dict[str, object] | None = None
    if claim_summary_paths:
        try:
            portfolio_dir = artifact_root / "portfolio"
            portfolio = write_portfolio_artifacts(claim_summary_paths, portfolio_dir)
            if portfolio["blocked_count"] != 0:
                failures.append({
                    "stage": "portfolio",
                    "id": "starter_templates",
                    "message": f"Portfolio has {portfolio['blocked_count']} blocked claim(s).",
                })
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            failures.append({"stage": "portfolio", "id": "starter_templates", "message": str(exc)})
    else:
        failures.append({
            "stage": "portfolio",
            "id": "starter_templates",
            "message": "No ready template audit summaries were produced.",
        })

    audit_ready_count = sum(1 for template in templates if template.get("claim_ready") is True)
    summary: dict[str, object] = {
        "status": "passed" if not failures else "failed",
        "schema_count": len(schemas),
        "schemas": schemas,
        "template_count": len(templates),
        "audit_ready_count": audit_ready_count,
        "failure_count": len(failures),
        "failures": failures,
        "templates": templates,
        "portfolio_status": portfolio["status"] if portfolio else "not_run",
        "portfolio_claim_count": portfolio["claim_count"] if portfolio else 0,
        "artifact_root": str(artifact_root) if keep_artifacts else "",
    }
    return summary


def cmd_selftest(args: argparse.Namespace) -> int:
    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        summary = run_selftest(args.out_dir, keep_artifacts=True)
    else:
        with tempfile.TemporaryDirectory(prefix="falsiflow_selftest_") as tmp:
            summary = run_selftest(Path(tmp), keep_artifacts=False)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow selftest: {summary['status']}")
        print(f"Schemas: {summary['schema_count']}")
        print(f"Templates: {summary['template_count']}")
        print(f"Ready demo audits: {summary['audit_ready_count']}")
        print(f"Portfolio: {summary['portfolio_status']}")
        if summary["artifact_root"]:
            print(f"Wrote {summary['artifact_root']}")
        for failure in summary["failures"]:
            print(f"failure: {failure['stage']}:{failure['id']}: {failure['message']}")
    return 0 if summary["status"] == "passed" else 2


def cmd_validate(args: argparse.Namespace) -> int:
    project = load_project(args.config)
    validation = validate_project_config(project)
    print(f"Falsiflow validate: {validation['status']}")
    print(f"Errors: {validation['error_count']}")
    print(f"Warnings: {validation['warning_count']}")
    for issue in validation.get("issues", []):
        print(f"{issue['level']}: {issue['path']}: {issue['message']}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(validation, indent=2, sort_keys=True), encoding="utf-8")
        print(f"Wrote {args.out}")
    return 0 if validation["valid"] or not args.strict else 2


def cmd_portfolio(args: argparse.Namespace) -> int:
    inputs = args.input or [Path.cwd() / "data" / "falsiflow"]
    summary_paths = discover_claim_summary_paths(inputs)
    if not summary_paths:
        raise SystemExit("No claim_summary.json files found.")
    portfolio = write_portfolio_artifacts(summary_paths, args.out_dir)
    print(f"Falsiflow portfolio: {portfolio['status']}")
    print(f"Claims: {portfolio['claim_count']}")
    print(f"Ready: {portfolio['ready_count']}")
    print(f"Blocked: {portfolio['blocked_count']}")
    print(f"Wrote {args.out_dir / 'portfolio_summary.json'}")
    print(f"Wrote {args.out_dir / 'portfolio_summary.md'}")
    print(f"Wrote {args.out_dir / 'portfolio_dashboard.html'}")
    return 0 if portfolio["blocked_count"] == 0 or not args.strict else 2


def add_discovery_arguments(target: argparse.ArgumentParser, default_out_dir: Path = Path("falsiflow_discovery")) -> None:
    target.add_argument("--goal", required=True, help="Research goal to turn into evidence records, candidates, gates, and an assay plan.")
    target.add_argument("--out-dir", type=Path, default=default_out_dir, help="Directory for discovery artifacts.")
    target.add_argument("--force", action="store_true", help="Allow replacing an existing discovery directory.")
    target.add_argument("--json", action="store_true", help="Print machine-readable discovery summary.")


def add_wide_csv_arguments(target: argparse.ArgumentParser) -> None:
    target.add_argument("--input", type=Path, action="append", required=True, help="Wide lab CSV. Repeatable.")
    target.add_argument("--out", type=Path, required=True, help="Falsiflow evidence CSV to write.")
    target.add_argument("--summary-out", type=Path, help="Optional conversion summary JSON.")
    target.add_argument("--config", type=Path, help="Optional project config for import coverage precheck.")
    target.add_argument("--coverage-out", type=Path, help="Optional coverage precheck JSON output path.")
    target.add_argument("--strict", action="store_true", help="Exit non-zero when project coverage is blocked.")
    target.add_argument("--gate-id", required=True)
    target.add_argument("--candidate-id", required=True)
    target.add_argument("--sample-id-column", default="sample_id")
    target.add_argument("--field", action="append", default=[], help="Value column to import. Repeatable. Defaults to all non-metadata columns.")
    target.add_argument("--exclude-column", action="append", default=[], help="Column to ignore when auto-selecting value columns.")
    target.add_argument("--gate-id-column", default="")
    target.add_argument("--candidate-id-column", default="")
    target.add_argument("--source-file", default="")
    target.add_argument("--source-file-column", default="")
    target.add_argument("--measured-at", default="")
    target.add_argument("--measured-at-column", default="")
    target.add_argument("--operator-or-agent", default="")
    target.add_argument("--operator-or-agent-column", default="")
    target.add_argument("--instrument-id", default="")
    target.add_argument("--instrument-id-column", default="")
    target.add_argument("--notes", default="")
    target.add_argument("--notes-column", default="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="falsiflow", description="Evidence-gated R&D workflow engine.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Copy a starter Falsiflow template.")
    init.add_argument("--template", default="neural_materials")
    init.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    init.add_argument("--out", type=Path, required=True)
    init.set_defaults(func=cmd_init)

    start = sub.add_parser("start", help="Open the beginner-friendly local Falsiflow app.")
    start.add_argument("--template", default="biointerface_coatings", help="Starter example to show. Defaults to biointerface_coatings.")
    start.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    start.add_argument("--out-dir", type=Path, default=Path("falsiflow_start"), help="Directory for the local app files.")
    start.add_argument("--host", default="127.0.0.1", help="Host interface for the local server.")
    start.add_argument("--port", type=int, default=0, help="Port for the local app. Defaults to a free port.")
    start.add_argument("--reset", action="store_true", help="Regenerate the local app output directory before opening it.")
    start.add_argument("--no-open", action="store_true", help="Do not open the browser automatically.")
    start.add_argument("--check", action="store_true", help="Start the server, fetch index.html once, write serve_summary.json, and exit.")
    start.add_argument("--json", action="store_true", help="Print machine-readable local app summary.")
    start.set_defaults(func=cmd_start)

    onboard = sub.add_parser("onboard", help="Run the beginner onboarding check and write next-step guidance.")
    onboard.add_argument("--template", default="biointerface_coatings", help="Starter example to show. Defaults to biointerface_coatings.")
    onboard.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    onboard.add_argument("--out-dir", type=Path, default=Path("falsiflow_onboard"), help="Directory for onboarding files.")
    onboard.add_argument("--host", default="127.0.0.1", help="Host interface for the local check server.")
    onboard.add_argument("--port", type=int, default=0, help="Port for the local check server. Defaults to a free port.")
    onboard.add_argument("--reset", action="store_true", help="Regenerate the onboarding output directory before checking it.")
    onboard.add_argument("--no-open", action="store_true", help="Do not open the browser after onboarding.")
    onboard.add_argument("--check", action="store_true", help="Run the onboarding HTTP check and exit.")
    onboard.add_argument("--json", action="store_true", help="Print machine-readable onboarding summary.")
    onboard.set_defaults(func=cmd_onboard)

    static_demo = sub.add_parser("static-demo", help="Export a hostable static demo site for zero-install visitors.")
    static_demo.add_argument("--template", default="biointerface_coatings", help="Starter template to export. Defaults to biointerface_coatings.")
    static_demo.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    static_demo.add_argument("--out-dir", type=Path, default=Path("falsiflow_static_demo"), help="Directory for static demo files.")
    static_demo.add_argument("--force", action="store_true", help="Allow replacing an existing static demo directory.")
    static_demo.add_argument("--open", action="store_true", help="Open the exported index.html in the default browser.")
    static_demo.add_argument("--json", action="store_true", help="Print machine-readable static demo summary.")
    static_demo.set_defaults(func=cmd_static_demo)

    demo_package = sub.add_parser("demo-package", help="Prepare a GitHub Pages/Netlify-ready static demo package.")
    demo_package.add_argument("--template", default="biointerface_coatings", help="Starter template to export. Defaults to biointerface_coatings.")
    demo_package.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    demo_package.add_argument("--out-dir", type=Path, default=Path("falsiflow_public_demo"), help="Directory for publishable demo files.")
    demo_package.add_argument("--force", action="store_true", help="Allow replacing an existing demo package directory.")
    demo_package.add_argument("--open", action="store_true", help="Open the exported index.html in the default browser.")
    demo_package.add_argument("--json", action="store_true", help="Print machine-readable demo package summary.")
    demo_package.set_defaults(func=cmd_demo_package)

    publish_kit = sub.add_parser("publish-kit", help="Generate a local handoff kit for GitHub Pages, external readiness, and PyPI release steps.")
    publish_kit.add_argument("--template", default="biointerface_coatings", help="Starter template to export in the public demo package.")
    publish_kit.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    publish_kit.add_argument("--out-dir", type=Path, default=Path("falsiflow_publish_kit"), help="Directory for publish handoff artifacts.")
    publish_kit.add_argument("--repo-slug", default="", help="Optional GitHub repo slug such as OWNER/falsiflow.")
    publish_kit.add_argument("--public-demo-url", default="", help="Optional hosted public demo URL.")
    publish_kit.add_argument("--tag", default="v0.1.0", help="Release tag to include in generated GitHub commands.")
    publish_kit.add_argument("--force", action="store_true", help="Allow replacing an existing publish-kit directory.")
    publish_kit.add_argument("--json", action="store_true", help="Print machine-readable publish handoff summary.")
    publish_kit.set_defaults(func=cmd_publish_kit)

    external_check = sub.add_parser("external-check", help="Check public release dependencies such as hosted demo URL, repo URL, pipx, and Windows validation.")
    external_check.add_argument("--out-dir", type=Path, default=Path("falsiflow_external_check"), help="Directory for external readiness artifacts.")
    external_check.add_argument("--force", action="store_true", help="Allow replacing an existing external-check directory.")
    external_check.add_argument("--strict", action="store_true", help="Exit non-zero unless every external readiness check passes.")
    external_check.add_argument("--json", action="store_true", help="Print machine-readable external readiness summary.")
    external_check.set_defaults(func=cmd_external_check)

    discover = sub.add_parser("discover", help="Generate a structured, non-AI discovery candidate queue and project draft.")
    add_discovery_arguments(discover)
    discover.set_defaults(func=cmd_discover)

    agent = sub.add_parser("agent", help="Optional agent interfaces that still emit auditable Falsiflow artifacts.")
    agent_sub = agent.add_subparsers(dest="agent_command", required=True)
    agent_discover = agent_sub.add_parser("discover", help="Generate a structured discovery package through the agent-facing interface.")
    add_discovery_arguments(agent_discover)
    agent_discover.set_defaults(func=cmd_agent_discover)

    candidate = sub.add_parser("candidate", help="Candidate queue utilities.")
    candidate_sub = candidate.add_subparsers(dest="candidate_command", required=True)
    candidate_rank = candidate_sub.add_parser("rank", help="Rank candidate recipes for a research goal and write ranking artifacts.")
    add_discovery_arguments(candidate_rank, default_out_dir=Path("falsiflow_candidate_rank"))
    candidate_rank.set_defaults(func=cmd_candidate_rank)

    assay_plan = sub.add_parser("assay-plan", help="Draft assay and RFQ packages for the top candidate from a research goal.")
    add_discovery_arguments(assay_plan, default_out_dir=Path("falsiflow_assay_plan"))
    assay_plan.set_defaults(func=cmd_assay_plan)

    evidence = sub.add_parser("evidence", help="Evidence import utilities.")
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_import = evidence_sub.add_parser("import", help="Convert a wide lab CSV into Falsiflow evidence rows.")
    add_wide_csv_arguments(evidence_import)
    evidence_import.set_defaults(func=cmd_ingest_wide_csv)

    try_cmd = sub.add_parser("try", help="Run a 30-second starter demo and write a local browser launchpad.")
    try_cmd.add_argument("--template", default="biointerface_coatings", help="Starter template to run. Defaults to biointerface_coatings.")
    try_cmd.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    try_cmd.add_argument("--out-dir", type=Path, default=Path("falsiflow_try"), help="Directory for the demo project, JSON, launchpad, and HTML report.")
    try_cmd.add_argument("--force", action="store_true", help="Allow replacing an existing try output directory.")
    try_cmd.add_argument("--open", action="store_true", help="Open the local launchpad in the default browser after writing it.")
    try_cmd.add_argument("--strict", action="store_true", help="Exit non-zero unless the starter claim is ready.")
    try_cmd.add_argument("--json", action="store_true", help="Print machine-readable try summary.")
    try_cmd.set_defaults(func=cmd_try)

    wizard = sub.add_parser("wizard", help="Write a static browser wizard for drafting a claim gate.")
    wizard.add_argument("--out", type=Path, default=Path("falsiflow_wizard.html"), help="HTML wizard file to write.")
    wizard.add_argument("--force", action="store_true", help="Allow replacing an existing wizard HTML file.")
    wizard.add_argument("--open", action="store_true", help="Open the wizard in the default browser after writing it.")
    wizard.add_argument("--json", action="store_true", help="Print machine-readable wizard summary.")
    wizard.set_defaults(func=cmd_wizard)

    serve = sub.add_parser("serve", help="Generate and serve the local Falsiflow browser demo on localhost.")
    serve.add_argument("--template", default="biointerface_coatings", help="Starter template to run when generating the demo.")
    serve.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    serve.add_argument("--out-dir", type=Path, default=Path("falsiflow_try"), help="Directory containing or receiving index.html and try_report.html.")
    serve.add_argument("--host", default="127.0.0.1", help="Host interface for the local server.")
    serve.add_argument("--port", type=int, default=8765, help="Port for the local server. Use 0 to choose a free port.")
    serve.add_argument("--force", action="store_true", help="Regenerate the try output directory before serving.")
    serve.add_argument("--open", action="store_true", help="Open the local demo URL in the default browser.")
    serve.add_argument("--check", action="store_true", help="Start the server, fetch index.html once, write serve_summary.json, and exit.")
    serve.add_argument("--json", action="store_true", help="Print machine-readable serve summary.")
    serve.set_defaults(func=cmd_serve)

    quickstart = sub.add_parser("quickstart", help="Create a starter project and immediately run the one-command claim gate.")
    quickstart.add_argument("--template", default="neural_materials")
    quickstart.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    quickstart.add_argument("--out", type=Path, required=True, help="Project directory to create.")
    quickstart.add_argument("--force", action="store_true", help="Allow replacing an existing quickstart project directory.")
    quickstart.add_argument("--strict", action="store_true", help="Exit non-zero unless the quickstart claim check is ready.")
    quickstart.add_argument("--json", action="store_true", help="Print machine-readable quickstart summary.")
    quickstart.set_defaults(func=cmd_quickstart)

    doctor = sub.add_parser("doctor", help="Diagnose a project directory and run the complete claim gate with actionable next steps.")
    doctor.add_argument("--project-dir", type=Path, help="Project directory containing project.json and an evidence CSV; defaults --out-dir to PROJECT_DIR/doctor.")
    doctor.add_argument("--config", type=Path, help="Project config JSON path. Defaults to PROJECT_DIR/project.json when --project-dir is used.")
    doctor.add_argument("--evidence", type=Path, help="Evidence CSV path. Defaults to PROJECT_DIR/evidence_pass_demo.csv, evidence.csv, or evidence_template.csv when --project-dir is used.")
    doctor.add_argument("--out-dir", type=Path, help="Output directory. Defaults to PROJECT_DIR/doctor when --project-dir is used.")
    doctor.add_argument("--force", action="store_true", help="Allow writing into a non-empty doctor output directory.")
    doctor.add_argument("--strict", action="store_true", help="Exit non-zero unless the doctor summary is ready.")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable doctor summary.")
    doctor.set_defaults(func=cmd_doctor)

    scaffold = sub.add_parser("scaffold", help="Create a custom Falsiflow project from gates and fields.")
    scaffold.add_argument("--out", type=Path, required=True, help="Directory to create.")
    scaffold.add_argument("--project-id", required=True)
    scaffold.add_argument("--project-name", default="")
    scaffold.add_argument("--domain", default="custom-rd")
    scaffold.add_argument("--claim-id", required=True)
    scaffold.add_argument("--claim-statement", required=True)
    scaffold.add_argument(
        "--gate",
        action="append",
        required=True,
        help="Gate definition as `gate_id:field_a,field_b`. Repeatable.",
    )
    scaffold.add_argument("--gate-title", action="append", default=[], help="Optional title as `gate_id=Human title`. Repeatable.")
    scaffold.add_argument(
        "--sample",
        action="append",
        default=[],
        help="Sample as `candidate_id:sample_id` for all gates, or `gate_id:candidate_id:sample_id`. Repeatable.",
    )
    scaffold.add_argument(
        "--rule",
        action="append",
        default=[],
        help="Acceptance rule as `gate_id:field:operator:value[:reason]`. Repeatable.",
    )
    scaffold.add_argument("--candidate-id", default="candidate_a", help="Default candidate_id when --sample is omitted.")
    scaffold.add_argument("--sample-id", default="sample_001", help="Default sample_id when --sample is omitted.")
    scaffold.add_argument("--json", action="store_true", help="Print machine-readable scaffold summary.")
    scaffold.set_defaults(func=cmd_scaffold)

    template_scaffold = sub.add_parser("template-scaffold", help="Create a reusable starter template with pass and placeholder demos.")
    template_scaffold.add_argument("--out", type=Path, required=True, help="Template directory to create.")
    template_scaffold.add_argument("--template-id", required=True)
    template_scaffold.add_argument("--template-name", default="")
    template_scaffold.add_argument("--template-description", default="")
    template_scaffold.add_argument("--project-id", default="")
    template_scaffold.add_argument("--project-name", default="")
    template_scaffold.add_argument("--domain", default="custom-rd")
    template_scaffold.add_argument("--claim-id", default="")
    template_scaffold.add_argument("--claim-statement", required=True)
    template_scaffold.add_argument(
        "--gate",
        action="append",
        required=True,
        help="Gate definition as `gate_id:field_a,field_b`. Repeatable.",
    )
    template_scaffold.add_argument("--gate-title", action="append", default=[], help="Optional title as `gate_id=Human title`. Repeatable.")
    template_scaffold.add_argument(
        "--sample",
        action="append",
        default=[],
        help="Sample as `candidate_id:sample_id` for all gates, or `gate_id:candidate_id:sample_id`. Repeatable.",
    )
    template_scaffold.add_argument(
        "--rule",
        action="append",
        default=[],
        help="Acceptance rule as `gate_id:field:operator:value[:reason]`. Repeatable.",
    )
    template_scaffold.add_argument("--candidate-id", default="candidate_a", help="Default candidate_id when --sample is omitted.")
    template_scaffold.add_argument("--sample-id", default="sample_001", help="Default sample_id when --sample is omitted.")
    template_scaffold.add_argument("--check-out-dir", type=Path, help="Optional directory for template-check artifacts.")
    template_scaffold.add_argument("--force", action="store_true", help="Allow replacing a non-empty template or check output directory.")
    template_scaffold.add_argument("--json", action="store_true", help="Print machine-readable template-scaffold summary.")
    template_scaffold.set_defaults(func=cmd_template_scaffold)

    templates = sub.add_parser("templates", help="List available starter templates.")
    templates.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to list before bundled templates. Repeatable.")
    templates.add_argument("--json", action="store_true", help="Print machine-readable template metadata.")
    templates.set_defaults(func=cmd_templates)

    template_gallery = sub.add_parser("template-gallery", help="Write a Markdown and JSON gallery of starter template use cases.")
    template_gallery.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to include before bundled templates. Repeatable.")
    template_gallery.add_argument("--out", type=Path, help="Optional Markdown gallery output path.")
    template_gallery.add_argument("--json-out", type=Path, help="Optional JSON gallery output path.")
    template_gallery.add_argument("--json", action="store_true", help="Print machine-readable template-gallery summary.")
    template_gallery.set_defaults(func=cmd_template_gallery)

    schema = sub.add_parser("schema", help="Print machine-readable Falsiflow JSON Schemas.")
    schema.add_argument("--kind", choices=SCHEMA_KINDS, default="project")
    schema.add_argument("--out", type=Path, help="Optional JSON output path.")
    schema.set_defaults(func=cmd_schema)

    selftest = sub.add_parser("selftest", help="Verify packaged schemas, templates, demo audits, and portfolio output.")
    selftest.add_argument("--out-dir", type=Path, help="Optional directory for selftest artifacts.")
    selftest.add_argument("--json", action="store_true", help="Print machine-readable selftest results.")
    selftest.set_defaults(func=cmd_selftest)

    demo = sub.add_parser("demo", help="Run the end-to-end starter walkthrough and produce a verified bundle.")
    demo.add_argument("--out-dir", type=Path, required=True, help="Directory for demo project and artifacts.")
    demo.add_argument("--template", default="neural_materials", help="Starter template to run. Defaults to neural_materials.")
    demo.add_argument("--json", action="store_true", help="Print machine-readable demo summary.")
    demo.add_argument("--force", action="store_true", help="Allow replacing a non-empty demo output directory.")
    demo.set_defaults(func=cmd_demo)

    template_check = sub.add_parser("template-check", help="Validate an external or bundled starter template end to end.")
    template_check.add_argument("--template-dir", type=Path, required=True, help="Directory containing template.json, project.json, evidence demos, and source_files/.")
    template_check.add_argument("--out-dir", type=Path, required=True, help="Directory for template-check artifacts and reports.")
    template_check.add_argument("--json", action="store_true", help="Print machine-readable template-check summary.")
    template_check.add_argument("--force", action="store_true", help="Allow writing into a non-empty template-check directory.")
    template_check.set_defaults(func=cmd_template_check)

    template_pack = sub.add_parser("template-pack", help="Package a checked starter template into a verifiable zip artifact.")
    template_pack.add_argument("--template-dir", type=Path, required=True, help="Template directory to package.")
    template_pack.add_argument("--out-dir", type=Path, required=True, help="Directory for the unpacked template pack.")
    template_pack.add_argument("--zip-out", type=Path, help="Zip archive path. Defaults to OUT_DIR with .zip suffix.")
    template_pack.add_argument("--verify-out", type=Path, help="Optional JSON verification output path. Defaults next to the zip.")
    template_pack.add_argument("--report-out", type=Path, help="Optional Markdown verification report output path. Defaults next to the zip.")
    template_pack.add_argument("--force", action="store_true", help="Allow replacing a non-empty template pack directory.")
    template_pack.add_argument("--json", action="store_true", help="Print machine-readable template-pack summary.")
    template_pack.set_defaults(func=cmd_template_pack)

    verify_template_pack_cmd = sub.add_parser("verify-template-pack", help="Verify a template pack directory or zip archive against its manifest and hashes.")
    verify_template_target = verify_template_pack_cmd.add_mutually_exclusive_group(required=True)
    verify_template_target.add_argument("--pack-dir", type=Path, help="Template pack directory containing template_pack_manifest.json.")
    verify_template_target.add_argument("--zip", dest="zip_path", type=Path, help="Template pack zip archive to verify without manual extraction.")
    verify_template_pack_cmd.add_argument("--out", type=Path, help="Optional JSON verification report output path.")
    verify_template_pack_cmd.add_argument("--report-out", type=Path, help="Optional Markdown verification report output path.")
    verify_template_pack_cmd.add_argument("--strict", action="store_true", help="Exit non-zero unless the template pack is verified and ready.")
    verify_template_pack_cmd.set_defaults(func=cmd_verify_template_pack)

    template_registry = sub.add_parser("template-registry", help="Build a verified local registry from one or more template-pack zip archives.")
    template_registry.add_argument("--pack-zip", type=Path, action="append", required=True, help="Template pack zip archive to index. Repeatable.")
    template_registry.add_argument("--out", type=Path, required=True, help="JSON registry output path.")
    template_registry.add_argument("--report-out", type=Path, help="Optional Markdown registry report output path.")
    template_registry.add_argument("--base-url", default="", help="Optional public base URL for registry source_url entries.")
    template_registry.add_argument("--json", action="store_true", help="Print machine-readable template-registry summary.")
    template_registry.set_defaults(func=cmd_template_registry)

    template_lock = sub.add_parser("template-lock", help="Lock a template registry entry to an exact source zip hash.")
    template_lock.add_argument("--registry", type=Path, required=True, help="Template registry JSON path.")
    template_lock.add_argument("--template", required=True, help="Template id to lock.")
    template_lock.add_argument("--version", default="", help="Optional exact template version to lock when a registry has multiple versions.")
    template_lock.add_argument("--out", type=Path, required=True, help="Template lock JSON output path.")
    template_lock.add_argument("--cache-dir", type=Path, help="Optional cache directory for verifying source_url entries.")
    template_lock.add_argument("--json", action="store_true", help="Print machine-readable template-lock summary.")
    template_lock.set_defaults(func=cmd_template_lock)

    template_attest = sub.add_parser("template-attest", help="Create a provenance attestation for a template registry or lockfile.")
    template_attest.add_argument("--subject", type=Path, required=True, help="Template registry or lock JSON file to attest.")
    template_attest.add_argument("--subject-type", choices=["template-registry", "template-lock"], default="", help="Optional subject type. Inferred from the subject when omitted.")
    template_attest.add_argument("--out", type=Path, required=True, help="Template attestation JSON output path.")
    template_attest.add_argument("--builder", default="", help="Builder or CI identity to record in the attestation payload.")
    template_attest.add_argument("--key-id", default="", help="Optional identifier for the signing key.")
    template_attest.add_argument("--signing-key", default="", help="Optional HMAC signing key. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY.")
    template_attest.add_argument("--json", action="store_true", help="Print machine-readable template-attestation summary.")
    template_attest.set_defaults(func=cmd_template_attest)

    verify_template_attestation = sub.add_parser("verify-template-attestation", help="Verify a template provenance attestation against its subject and optional HMAC key.")
    verify_template_attestation.add_argument("--attestation", type=Path, required=True, help="Template attestation JSON path.")
    verify_template_attestation.add_argument("--subject", type=Path, help="Optional subject path override.")
    verify_template_attestation.add_argument("--signing-key", default="", help="Optional HMAC signing key. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY.")
    verify_template_attestation.add_argument("--out", type=Path, help="Optional JSON verification report output path.")
    verify_template_attestation.add_argument("--strict", action="store_true", help="Exit non-zero unless the attestation signature is verified.")
    verify_template_attestation.add_argument("--json", action="store_true", help="Print machine-readable template-attestation verification.")
    verify_template_attestation.set_defaults(func=cmd_verify_template_attestation)

    template_policy = sub.add_parser("template-policy", help="Create a reusable trust policy from a verified template lock attestation.")
    template_policy.add_argument("--lock", type=Path, required=True, help="Template lock JSON path.")
    template_policy.add_argument("--attestation", type=Path, required=True, help="Template-lock attestation JSON path.")
    template_policy.add_argument("--out", type=Path, required=True, help="Template policy JSON output path.")
    template_policy.add_argument("--policy-id", default="", help="Optional stable policy id. Defaults to template_id@version.")
    template_policy.add_argument("--owner", default="", help="Optional owner or team name recorded in the policy.")
    template_policy.add_argument("--signing-key", default="", help="HMAC signing key for verifying the attestation. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY.")
    template_policy.add_argument("--json", action="store_true", help="Print machine-readable template-policy summary.")
    template_policy.set_defaults(func=cmd_template_policy)

    verify_template_policy = sub.add_parser("verify-template-policy", help="Verify a template trust policy against a lock and attestation.")
    verify_template_policy.add_argument("--policy", type=Path, required=True, help="Template policy JSON path.")
    verify_template_policy.add_argument("--lock", type=Path, required=True, help="Template lock JSON path.")
    verify_template_policy.add_argument("--attestation", type=Path, required=True, help="Template-lock attestation JSON path.")
    verify_template_policy.add_argument("--signing-key", default="", help="HMAC signing key for verifying the attestation. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY.")
    verify_template_policy.add_argument("--out", type=Path, help="Optional JSON policy verification report output path.")
    verify_template_policy.add_argument("--strict", action="store_true", help="Exit non-zero unless the template policy is verified.")
    verify_template_policy.add_argument("--json", action="store_true", help="Print machine-readable template-policy verification.")
    verify_template_policy.set_defaults(func=cmd_verify_template_policy)

    template_release = sub.add_parser("template-release", help="Package a verified template pack, lock, attestation, and policy into one release zip.")
    template_release.add_argument("--pack-zip", type=Path, required=True, help="Verified template-pack zip archive.")
    template_release.add_argument("--registry", type=Path, required=True, help="Template registry JSON path.")
    template_release.add_argument("--lock", type=Path, required=True, help="Template lock JSON path.")
    template_release.add_argument("--attestation", type=Path, required=True, help="Template-lock attestation JSON path.")
    template_release.add_argument("--policy", type=Path, required=True, help="Template adoption policy JSON path.")
    template_release.add_argument("--out", type=Path, required=True, help="Template release zip output path.")
    template_release.add_argument("--signing-key", default="", help="HMAC signing key for verifying the attestation and policy before packaging.")
    template_release.add_argument("--json", action="store_true", help="Print machine-readable template-release summary.")
    template_release.set_defaults(func=cmd_template_release)

    verify_template_release = sub.add_parser("verify-template-release", help="Verify a template release zip before installation.")
    verify_template_release.add_argument("--release", type=Path, required=True, help="Template release zip path.")
    verify_template_release.add_argument("--signing-key", default="", help="HMAC signing key for verifying the release attestation and policy.")
    verify_template_release.add_argument("--out", type=Path, help="Optional JSON release verification report output path.")
    verify_template_release.add_argument("--report-out", type=Path, help="Optional Markdown release verification report output path.")
    verify_template_release.add_argument("--strict", action="store_true", help="Exit non-zero unless the template release is verified.")
    verify_template_release.add_argument("--json", action="store_true", help="Print machine-readable template-release verification.")
    verify_template_release.set_defaults(func=cmd_verify_template_release)

    template_install = sub.add_parser("template-install", help="Verify and install a template-pack zip into a reusable template root.")
    template_install_source = template_install.add_mutually_exclusive_group(required=True)
    template_install_source.add_argument("--zip", dest="zip_path", type=Path, help="Template pack zip archive to verify and install.")
    template_install_source.add_argument("--lock", dest="lock_path", type=Path, help="Template lock JSON file to verify before installing.")
    template_install_source.add_argument("--release", dest="release_path", type=Path, help="Template release zip to verify and install.")
    template_install.add_argument("--templates-dir", type=Path, required=True, help="Template root where the verified template directory will be installed.")
    template_install.add_argument("--check-out-dir", type=Path, help="Optional directory for installed-template check artifacts.")
    template_install.add_argument("--cache-dir", type=Path, help="Optional cache directory for lockfile source_url downloads.")
    template_install.add_argument("--attestation", dest="attestation_path", type=Path, help="Optional template-lock attestation to verify before installing from --lock.")
    template_install.add_argument("--signing-key", default="", help="Optional HMAC signing key for --attestation. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY.")
    template_install.add_argument("--policy", dest="policy_path", type=Path, help="Optional template policy to verify before installing from --lock.")
    template_install.add_argument("--require-attestation", action="store_true", help="Block installation unless --attestation verifies with a trusted signature.")
    template_install.add_argument("--force", action="store_true", help="Allow replacing an installed template with the same id.")
    template_install.add_argument("--json", action="store_true", help="Print machine-readable template-install summary.")
    template_install.set_defaults(func=cmd_template_install)

    adoption_check = sub.add_parser("adoption-check", help="Audit the five adoption priorities as a machine-readable readiness gate.")
    adoption_check.add_argument("--out-dir", type=Path, required=True, help="Directory for adoption-check artifacts and reports.")
    adoption_check.add_argument("--json", action="store_true", help="Print machine-readable adoption-check results.")
    adoption_check.add_argument("--force", action="store_true", help="Allow writing into a non-empty adoption-check directory.")
    adoption_check.add_argument("--skip-dist", action="store_true", help="Skip wheel/sdist build and isolated wheel install checks.")
    adoption_check.set_defaults(func=cmd_adoption_check)

    release_check = sub.add_parser("release-check", help="Run the full pre-release gate: schemas, templates, bundles, zip verification, and portfolio.")
    release_check.add_argument("--out-dir", type=Path, required=True, help="Directory for release-check artifacts and reports.")
    release_check.add_argument("--json", action="store_true", help="Print machine-readable release-check results.")
    release_check.add_argument("--force", action="store_true", help="Allow replacing a non-empty release-check directory.")
    release_check.add_argument("--skip-dist", action="store_true", help="Skip wheel/sdist build and isolated wheel install checks.")
    release_check.set_defaults(func=cmd_release_check)

    validate = sub.add_parser("validate", help="Validate a Falsiflow project config.")
    validate.add_argument("--config", type=Path, required=True)
    validate.add_argument("--out", type=Path, help="Optional validation JSON output path.")
    validate.add_argument("--strict", action="store_true", help="Exit non-zero when validation has errors.")
    validate.set_defaults(func=cmd_validate)

    portfolio = sub.add_parser("portfolio", help="Aggregate claim_summary.json files into a portfolio dashboard.")
    portfolio.add_argument("--input", type=Path, action="append", help="Audit directory, claim_summary.json, or root to scan. Repeatable.")
    portfolio.add_argument("--out-dir", type=Path, required=True)
    portfolio.add_argument("--strict", action="store_true", help="Exit non-zero when any claim is blocked.")
    portfolio.set_defaults(func=cmd_portfolio)

    render = sub.add_parser("render", help="Render measurement templates and an audit report.")
    render.add_argument("--config", type=Path, required=True)
    render.add_argument("--evidence", type=Path)
    render.add_argument("--out-dir", type=Path, required=True)
    render.set_defaults(func=cmd_render)

    audit = sub.add_parser("audit", help="Audit evidence against configured gates.")
    audit.add_argument("--config", type=Path, required=True)
    audit.add_argument("--evidence", type=Path, required=True)
    audit.add_argument("--out-dir", type=Path, required=True)
    audit.add_argument("--strict", action="store_true", help="Exit non-zero when claim_ready is false.")
    audit.set_defaults(func=cmd_audit)

    claim_check = sub.add_parser("claim-check", help="Run audit, source provenance, evidence bundle, and zip verification in one command.")
    claim_check.add_argument("--project-dir", type=Path, help="Project directory containing project.json and evidence_pass_demo.csv; defaults --out-dir to PROJECT_DIR/claim_check.")
    claim_check.add_argument("--config", type=Path, help="Project config JSON path. Defaults to PROJECT_DIR/project.json when --project-dir is used.")
    claim_check.add_argument("--evidence", type=Path, help="Evidence CSV path. Defaults to PROJECT_DIR/evidence_pass_demo.csv when --project-dir is used.")
    claim_check.add_argument("--out-dir", type=Path, help="Output directory. Defaults to PROJECT_DIR/claim_check when --project-dir is used.")
    claim_check.add_argument("--strict", action="store_true", help="Exit non-zero unless the complete claim check is ready.")
    claim_check.add_argument("--force", action="store_true", help="Allow writing into a non-empty claim-check directory.")
    claim_check.add_argument("--json", action="store_true", help="Print machine-readable claim-check summary.")
    claim_check.set_defaults(func=cmd_claim_check)

    bundle = sub.add_parser("bundle", help="Build a portable evidence bundle with audit artifacts, sources, and hashes.")
    bundle.add_argument("--config", type=Path, required=True)
    bundle.add_argument("--evidence", type=Path, required=True)
    bundle.add_argument("--out-dir", type=Path, required=True)
    bundle.add_argument("--zip-out", type=Path, help="Optional zip archive path for the bundle directory.")
    bundle.add_argument("--strict", action="store_true", help="Exit non-zero when audit or source provenance is blocked.")
    bundle.add_argument("--force", action="store_true", help="Allow writing into a non-empty bundle directory.")
    bundle.set_defaults(func=cmd_bundle)

    verify_bundle_cmd = sub.add_parser("verify-bundle", help="Verify a bundle directory or zip archive against its manifest and hashes.")
    verify_target = verify_bundle_cmd.add_mutually_exclusive_group(required=True)
    verify_target.add_argument("--bundle-dir", type=Path, help="Bundle directory containing bundle_manifest.json.")
    verify_target.add_argument("--zip", dest="zip_path", type=Path, help="Bundle zip archive to verify without manual extraction.")
    verify_bundle_cmd.add_argument("--out", type=Path, help="Optional JSON verification report output path.")
    verify_bundle_cmd.add_argument("--report-out", type=Path, help="Optional Markdown verification report output path.")
    verify_bundle_cmd.add_argument("--strict", action="store_true", help="Exit non-zero unless the bundle is verified and bundle_ready.")
    verify_bundle_cmd.set_defaults(func=cmd_verify_bundle)

    next_cmd = sub.add_parser("next", help="Print the next evidence-filling actions.")
    next_cmd.add_argument("--config", type=Path, required=True)
    next_cmd.add_argument("--evidence", type=Path)
    next_cmd.add_argument("--out-dir", type=Path, required=True)
    next_cmd.set_defaults(func=cmd_next)

    sources = sub.add_parser("sources", help="Write a source-file provenance manifest for evidence rows.")
    sources.add_argument("--config", type=Path, required=True)
    sources.add_argument("--evidence", type=Path, required=True)
    sources.add_argument("--out", type=Path, required=True, help="Source manifest JSON output path.")
    sources.add_argument("--report-out", type=Path, help="Optional Markdown report output path.")
    sources.add_argument("--strict", action="store_true", help="Exit non-zero when required source provenance is incomplete.")
    sources.set_defaults(func=cmd_sources)

    ingest = sub.add_parser("ingest-limina-source-values", help="Convert LIMINA source-value sheets into Falsiflow evidence.")
    ingest.add_argument("--input", type=Path, action="append", required=True, help="LIMINA source-value CSV. Repeatable.")
    ingest.add_argument("--out", type=Path, required=True, help="Falsiflow evidence CSV to write.")
    ingest.add_argument("--summary-out", type=Path, help="Optional conversion summary JSON.")
    ingest.add_argument("--project-out", type=Path, help="Optional generated Falsiflow project JSON.")
    ingest.add_argument("--default-candidate", required=True)
    ingest.add_argument("--default-gate", default="h_a_medium_stability")
    ingest.add_argument("--project-id", default="limina_nhi_pedot_habc_falsiflow")
    ingest.add_argument("--claim-id", default="limina_nhi_pedot_habc_evidence_completeness")
    ingest.add_argument(
        "--claim-statement",
        default=(
            "LIMINA NHI-PEDOT H-A/H-B/H-C evidence pack is complete enough for "
            "Falsiflow provenance audit. This is not a material suitability claim."
        ),
    )
    ingest.add_argument("--source-file-base-dir", default=".")
    ingest.add_argument("--allowed-source-root", action="append", default=["data/source_files"])
    ingest.set_defaults(func=cmd_ingest_limina_source_values)

    wide = sub.add_parser("ingest-wide-csv", help="Convert a wide lab CSV into Falsiflow evidence rows.")
    add_wide_csv_arguments(wide)
    wide.set_defaults(func=cmd_ingest_wide_csv)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
