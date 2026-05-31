"""Experimental stdio MCP server for local Falsiflow agent integrations."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from . import __version__
from .api import check_claim, create_evidence_todo, explain_blockers, validate_bundle
from .core import falsiflow_schema


SERVER_INFO = {"name": "falsiflow", "version": __version__}


def text_result(payload: object) -> dict[str, object]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, indent=2, sort_keys=True),
            }
        ]
    }


def path_arg(args: dict[str, Any], name: str) -> Path | None:
    value = str(args.get(name, "") or "").strip()
    return Path(value).expanduser() if value else None


def tool_definitions() -> list[dict[str, object]]:
    return [
        {
            "name": "falsiflow.validate_claims",
            "description": "Run Falsiflow claim-check on a local project config and evidence CSV.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "config": {"type": "string"},
                    "evidence": {"type": "string"},
                    "out_dir": {"type": "string"},
                    "force": {"type": "boolean", "default": True},
                },
            },
        },
        {
            "name": "falsiflow.check_bundle",
            "description": "Verify a Falsiflow evidence bundle directory or zip archive.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bundle_dir": {"type": "string"},
                    "zip_path": {"type": "string"},
                },
            },
        },
        {
            "name": "falsiflow.explain_blockers",
            "description": "Explain blockers and evidence todo items from a claim_check.json artifact.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "claim_check_json": {"type": "string"},
                },
                "required": ["claim_check_json"],
            },
        },
        {
            "name": "falsiflow.create_evidence_todo",
            "description": "Create a missing-evidence checklist from project.json and optional evidence CSV.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "config": {"type": "string"},
                    "evidence": {"type": "string"},
                },
                "required": ["config"],
            },
        },
    ]


def resource_definitions() -> list[dict[str, str]]:
    return [
        {
            "uri": "falsiflow://schemas/evidence-row",
            "name": "Falsiflow evidence row schema",
            "mimeType": "application/json",
        },
        {
            "uri": "falsiflow://schemas/claim-check",
            "name": "Falsiflow claim-check schema",
            "mimeType": "application/json",
        },
        {
            "uri": "falsiflow://templates/rag-eval",
            "name": "RAG eval evidence gate template",
            "mimeType": "application/json",
        },
        {
            "uri": "falsiflow://templates/local-llm-eval",
            "name": "Local LLM eval import evidence contract",
            "mimeType": "text/markdown",
        },
        {
            "uri": "falsiflow://examples/blocked-pr",
            "name": "Blocked PR to ready PR demo playbook",
            "mimeType": "text/markdown",
        },
    ]


def read_resource(uri: str) -> tuple[str, str]:
    root = Path(__file__).resolve().parents[1]
    if uri == "falsiflow://schemas/evidence-row":
        return "application/json", json.dumps(falsiflow_schema("evidence-row"), indent=2, sort_keys=True)
    if uri == "falsiflow://schemas/claim-check":
        return "application/json", json.dumps(falsiflow_schema("claim-check"), indent=2, sort_keys=True)
    if uri == "falsiflow://templates/rag-eval":
        path = Path(__file__).resolve().parent / "templates" / "rag_quality_gate" / "project.json"
        return "application/json", path.read_text(encoding="utf-8")
    if uri == "falsiflow://templates/local-llm-eval":
        return "text/markdown", "\n".join([
            "# Local LLM Eval Evidence Contract",
            "",
            "Use `falsiflow evidence import --profile local-llm-eval` to convert local or private eval artifacts into evidence rows.",
            "",
            "Required manifest fields should pin dataset/version, prompt or task-set hash, candidate model id or file hash, baseline model id, evaluator version, decode parameters or seed, raw output artifact, and CI run.",
            "",
            "Falsiflow does not run the model or judge answers; it verifies whether the claim has reviewable evidence for CI.",
        ]) + "\n"
    if uri == "falsiflow://examples/blocked-pr":
        return "text/markdown", (root / "docs" / "falsiflow_demo_pr_playbook.md").read_text(encoding="utf-8")
    raise ValueError(f"Unknown Falsiflow MCP resource: {uri}")


def call_tool(name: str, args: dict[str, Any]) -> dict[str, object]:
    if name == "falsiflow.validate_claims":
        project_dir = path_arg(args, "project_dir")
        config = path_arg(args, "config")
        evidence = path_arg(args, "evidence")
        out_dir = path_arg(args, "out_dir") or Path(tempfile.mkdtemp(prefix="falsiflow_mcp_claim_check_"))
        if project_dir is not None:
            config = config or project_dir / "project.json"
            evidence = evidence or project_dir / "evidence_pass_demo.csv"
        if config is None or evidence is None:
            raise ValueError("validate_claims requires project_dir, or config and evidence.")
        return text_result(check_claim(config, evidence, out_dir=out_dir, force=bool(args.get("force", True))))
    if name == "falsiflow.check_bundle":
        return text_result(validate_bundle(bundle_dir=path_arg(args, "bundle_dir"), zip_path=path_arg(args, "zip_path")))
    if name == "falsiflow.explain_blockers":
        claim_check_json = path_arg(args, "claim_check_json")
        if claim_check_json is None:
            raise ValueError("explain_blockers requires claim_check_json.")
        return text_result(explain_blockers(claim_check_json))
    if name == "falsiflow.create_evidence_todo":
        config = path_arg(args, "config")
        if config is None:
            raise ValueError("create_evidence_todo requires config.")
        return text_result(create_evidence_todo(config, evidence=path_arg(args, "evidence")))
    raise ValueError(f"Unknown Falsiflow MCP tool: {name}")


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = str(request.get("method", ""))
    request_id = request.get("id")
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": SERVER_INFO,
            }
        elif method == "tools/list":
            result = {"tools": tool_definitions()}
        elif method == "tools/call":
            params = request.get("params", {})
            if not isinstance(params, dict):
                raise ValueError("tools/call params must be an object.")
            tool_args = params.get("arguments", {})
            if not isinstance(tool_args, dict):
                raise ValueError("tools/call arguments must be an object.")
            result = call_tool(str(params.get("name", "")), tool_args)
        elif method == "resources/list":
            result = {"resources": resource_definitions()}
        elif method == "resources/read":
            params = request.get("params", {})
            if not isinstance(params, dict):
                raise ValueError("resources/read params must be an object.")
            mime_type, text = read_resource(str(params.get("uri", "")))
            result = {"contents": [{"uri": str(params.get("uri", "")), "mimeType": mime_type, "text": text}]}
        elif method.startswith("notifications/"):
            return None
        else:
            raise ValueError(f"Unsupported MCP method: {method}")
        if request_id is None:
            return None
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:  # pragma: no cover - stdio protocol boundary.
        if request_id is None:
            return None
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}}


def serve(infile=sys.stdin, outfile=sys.stdout) -> int:
    for line in infile:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        else:
            response = handle_request(request)
        if response is not None:
            outfile.write(json.dumps(response, separators=(",", ":")) + "\n")
            outfile.flush()
    return 0


def main() -> int:
    return serve()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
