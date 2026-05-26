"""Project and starter-template scaffolding helpers."""

from __future__ import annotations

from collections.abc import Callable
import csv
import json
from pathlib import Path
import shutil
import tempfile

from .core import (
    EVIDENCE_COLUMNS,
    OPERATORS,
    rule_applies_to_sample,
    validate_project_config,
)
from .template_check import run_template_check


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


def build_scaffold_project(
    *,
    gate: list[str],
    gate_title: list[str],
    rule: list[str],
    sample: list[str],
    candidate_id: str,
    sample_id: str,
    project_id: str,
    project_name: str,
    domain: str,
    claim_id: str,
    claim_statement: str,
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, str]]]:
    gate_specs = [parse_scaffold_gate(raw) for raw in gate]
    gate_ids = [str(gate["id"]) for gate in gate_specs]
    duplicate_gate_ids = sorted({gate_id for gate_id in gate_ids if gate_ids.count(gate_id) > 1})
    if duplicate_gate_ids:
        raise SystemExit(f"Duplicate scaffold gate id(s): {', '.join(duplicate_gate_ids)}")

    gate_id_set = set(gate_ids)
    gate_fields = {str(gate["id"]): set(str(field) for field in gate["required_fields"]) for gate in gate_specs}
    gate_titles = parse_scaffold_gate_titles(gate_title, gate_id_set)
    rules_by_gate = parse_scaffold_rules(rule, gate_fields)
    global_samples, gate_specific_samples = parse_scaffold_samples(
        sample,
        gate_id_set,
        candidate_id,
        sample_id,
    )

    gates: list[dict[str, object]] = []
    for gate_spec in gate_specs:
        gate_id = str(gate_spec["id"])
        samples = dedupe_samples(global_samples + gate_specific_samples.get(gate_id, []))
        gates.append({
            "id": gate_id,
            "title": gate_titles.get(gate_id, title_from_id(gate_id)),
            "samples": samples,
            "required_fields": gate_spec["required_fields"],
            "acceptance_rules": rules_by_gate.get(gate_id, []),
        })

    project = {
        "project": {
            "id": project_id,
            "name": project_name or title_from_id(project_id),
            "domain": domain,
            "version": "0.1.0",
        },
        "claim": {
            "id": claim_id,
            "statement": claim_statement,
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


def run_scaffold(
    out: Path,
    *,
    project_id: str,
    project_name: str,
    domain: str,
    claim_id: str,
    claim_statement: str,
    gate: list[str],
    gate_title: list[str],
    rule: list[str],
    sample: list[str],
    candidate_id: str,
    sample_id: str,
) -> dict[str, object]:
    if out.exists():
        if not out.is_dir():
            raise SystemExit(f"Refusing to write scaffold over non-directory path: {out}")
        if any(out.iterdir()):
            raise SystemExit(f"Refusing to overwrite non-empty directory: {out}")

    project, gates, evidence_rows = build_scaffold_project(
        gate=gate,
        gate_title=gate_title,
        rule=rule,
        sample=sample,
        candidate_id=candidate_id,
        sample_id=sample_id,
        project_id=project_id,
        project_name=project_name,
        domain=domain,
        claim_id=claim_id,
        claim_statement=claim_statement,
    )
    validation = validate_project_config(project)
    if not validation["valid"]:
        messages = "; ".join(issue["message"] for issue in validation.get("issues", []) if issue["level"] == "error")
        raise SystemExit(f"Generated scaffold project was invalid: {messages}")

    out.mkdir(parents=True, exist_ok=True)
    source_dir = out / "source_files"
    source_dir.mkdir(parents=True, exist_ok=True)
    project_path = out / "project.json"
    evidence_path = out / "evidence_template.csv"
    readme_path = out / "README.md"
    source_readme_path = source_dir / "README.md"

    project_path.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_evidence_csv(evidence_path, evidence_rows)
    readme_path.write_text(scaffold_project_readme(project), encoding="utf-8")
    source_readme_path.write_text(scaffold_source_readme(), encoding="utf-8")

    return {
        "status": "scaffolded",
        "project_id": project_id,
        "claim_id": claim_id,
        "gate_count": len(gates),
        "sample_count": sum(len(gate_item["samples"]) for gate_item in gates),
        "required_evidence_rows": len(evidence_rows),
        "project_path": str(project_path),
        "evidence_template_path": str(evidence_path),
        "source_files_dir": str(source_dir),
        "readme_path": str(readme_path),
    }


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


def run_template_scaffold(
    out: Path,
    *,
    template_id: str,
    template_name: str = "",
    template_description: str = "",
    project_id: str = "",
    project_name: str = "",
    domain: str = "custom-rd",
    claim_id: str = "",
    claim_statement: str,
    gate: list[str],
    gate_title: list[str],
    rule: list[str],
    sample: list[str],
    candidate_id: str,
    sample_id: str,
    check_out_dir: Path | None = None,
    force: bool = False,
    template_check_runner: Callable[..., dict[str, object]] = run_template_check,
) -> dict[str, object]:
    if out.exists():
        if not out.is_dir():
            raise SystemExit(f"Refusing to write template over non-directory path: {out}")
        if any(out.iterdir()):
            if not force:
                raise SystemExit(f"Refusing to overwrite non-empty template directory without --force: {out}")
            shutil.rmtree(out)

    project_id = project_id or f"{template_id}_project"
    project_name = project_name or title_from_id(project_id)
    claim_id = claim_id or f"{template_id}_claim"
    template_name = template_name or title_from_id(template_id)
    template_description = template_description or f"Evidence-gated starter template for: {claim_statement}"

    project, gates, placeholder_rows = build_scaffold_project(
        gate=gate,
        gate_title=gate_title,
        rule=rule,
        sample=sample,
        candidate_id=candidate_id,
        sample_id=sample_id,
        project_id=project_id,
        project_name=project_name,
        domain=domain,
        claim_id=claim_id,
        claim_statement=claim_statement,
    )
    validation = validate_project_config(project)
    if not validation["valid"]:
        messages = "; ".join(issue["message"] for issue in validation.get("issues", []) if issue["level"] == "error")
        raise SystemExit(f"Generated template project was invalid: {messages}")

    pass_rows = scaffold_passing_evidence_rows(project)
    out.mkdir(parents=True, exist_ok=True)
    source_path = out / "source_files" / "demo_raw_export.csv"
    project_path = out / "project.json"
    pass_evidence_path = out / "evidence_pass_demo.csv"
    placeholder_evidence_path = out / "evidence_placeholder_demo.csv"
    template_path_out = out / "template.json"
    readme_path = out / "README.md"

    template_manifest = {
        "id": template_id,
        "name": template_name,
        "domain": domain,
        "description": template_description,
        "project_config": "project.json",
        "demo_evidence": "evidence_pass_demo.csv",
        "placeholder_evidence": "evidence_placeholder_demo.csv",
    }

    project_path.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    template_path_out.write_text(json.dumps(template_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_evidence_csv(pass_evidence_path, pass_rows)
    write_evidence_csv(placeholder_evidence_path, placeholder_rows)
    write_template_demo_source(source_path, pass_rows)
    readme_path.write_text(template_scaffold_readme(template_id, project), encoding="utf-8")

    if check_out_dir is not None:
        check_summary = template_check_runner(out, check_out_dir, force=force)
    else:
        with tempfile.TemporaryDirectory(prefix="falsiflow_template_scaffold_check_") as tmp:
            check_summary = template_check_runner(out, Path(tmp), force=True)

    summary = {
        "status": "template_scaffolded" if check_summary.get("status") == "template_ready" else "template_scaffold_blocked",
        "template_id": template_id,
        "template_name": template_name,
        "domain": domain,
        "gate_count": len(gates),
        "sample_count": sum(len(gate_item["samples"]) for gate_item in gates),
        "required_evidence_rows": len(placeholder_rows),
        "template_check_status": check_summary.get("status", ""),
        "template_check_failure_count": check_summary.get("failure_count", 0),
        "template_dir": str(out),
        "template_manifest_path": str(template_path_out),
        "project_path": str(project_path),
        "pass_evidence_path": str(pass_evidence_path),
        "placeholder_evidence_path": str(placeholder_evidence_path),
        "source_file_path": str(source_path),
        "readme_path": str(readme_path),
    }
    if check_out_dir is not None:
        summary["template_check_path"] = str(check_out_dir / "template_check.json")
    return summary
