"""Candidate discovery and evidence-gate drafting workflows for Falsiflow."""

from __future__ import annotations

import json
from pathlib import Path
import re

from .bundle import markdown_cell
from .core import EVIDENCE_COLUMNS
from .quickstart import prepare_output_directory

ROOT = Path(__file__).resolve().parents[1]


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
