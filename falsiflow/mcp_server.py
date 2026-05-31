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


def decode_text_payload(result: dict[str, object]) -> dict[str, object]:
    content = result.get("content")
    if not isinstance(content, list) or not content:
        raise ValueError("MCP tool result did not include text content.")
    first = content[0]
    if not isinstance(first, dict):
        raise ValueError("MCP tool result content item is not an object.")
    text = first.get("text")
    if not isinstance(text, str):
        raise ValueError("MCP tool result content item did not include text.")
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("MCP tool result text did not decode to a JSON object.")
    return loaded


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


def run_selftest() -> dict[str, object]:
    """Exercise the local MCP protocol surface without opening a network port."""
    checks: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    request_id = 0

    def add(check: str, ok: bool, message: str, details: dict[str, object] | None = None) -> None:
        item: dict[str, object] = {
            "check": check,
            "status": "passed" if ok else "failed",
            "message": message,
        }
        if details:
            item["details"] = details
        checks.append(item)
        if not ok:
            failures.append(item)

    def request(method: str, params: dict[str, object] | None = None) -> dict[str, object]:
        nonlocal request_id
        request_id += 1
        response = handle_request({
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        })
        if response is None:
            raise ValueError(f"MCP method {method} did not return a response.")
        if "error" in response:
            error = response.get("error", {})
            if isinstance(error, dict):
                raise ValueError(str(error.get("message", error)))
            raise ValueError(str(error))
        result = response.get("result")
        if not isinstance(result, dict):
            raise ValueError(f"MCP method {method} returned a non-object result.")
        return result

    template_root = Path(__file__).resolve().parent / "templates"
    ai_template = template_root / "ai_claim_evaluation"
    rag_template = template_root / "rag_quality_gate"

    tool_names: set[str] = set()
    resource_uris: set[str] = set()
    claim_payload: dict[str, object] = {}
    bundle_payload: dict[str, object] = {}
    todo_payload: dict[str, object] = {}
    blocker_payload: dict[str, object] = {}

    try:
        initialized = request("initialize")
        server_info = initialized.get("serverInfo", {})
        ok = isinstance(server_info, dict) and server_info.get("name") == "falsiflow"
        add("initialize", ok, "MCP initialize returns the Falsiflow server identity.", {"server_info": server_info} if isinstance(server_info, dict) else None)
        if not ok:
            raise ValueError("initialize did not return the Falsiflow server identity.")

        tools = request("tools/list")
        tool_items = tools.get("tools", [])
        if isinstance(tool_items, list):
            tool_names = {str(tool.get("name", "")) for tool in tool_items if isinstance(tool, dict)}
        expected_tools = {"falsiflow.validate_claims", "falsiflow.check_bundle", "falsiflow.explain_blockers", "falsiflow.create_evidence_todo"}
        missing_tools = sorted(expected_tools - tool_names)
        add("tools_list", not missing_tools, "MCP tools/list exposes the local claim, bundle, blocker, and todo tools.", {"missing_tools": missing_tools})

        resources = request("resources/list")
        resource_items = resources.get("resources", [])
        if isinstance(resource_items, list):
            resource_uris = {str(resource.get("uri", "")) for resource in resource_items if isinstance(resource, dict)}
        expected_resources = {"falsiflow://schemas/evidence-row", "falsiflow://templates/local-llm-eval", "falsiflow://examples/blocked-pr"}
        missing_resources = sorted(expected_resources - resource_uris)
        add("resources_list", not missing_resources, "MCP resources/list exposes schemas, local LLM guidance, and blocked PR context.", {"missing_resources": missing_resources})

        local_llm = request("resources/read", {"uri": "falsiflow://templates/local-llm-eval"})
        contents = local_llm.get("contents", [])
        local_llm_text = ""
        if isinstance(contents, list) and contents and isinstance(contents[0], dict):
            local_llm_text = str(contents[0].get("text", ""))
        add("resource_read", "Local LLM Eval Evidence Contract" in local_llm_text, "MCP resources/read returns the local LLM evidence contract.")

        todo_result = request("tools/call", {
            "name": "falsiflow.create_evidence_todo",
            "arguments": {"config": str(rag_template / "project.json")},
        })
        todo_payload = decode_text_payload(todo_result)
        add("create_evidence_todo", todo_payload.get("status") == "evidence_todo_ready", "MCP create_evidence_todo returns a missing-evidence checklist.", {"status": str(todo_payload.get("status", ""))})

        with tempfile.TemporaryDirectory(prefix="falsiflow_mcp_selftest_") as tmp:
            claim_dir = Path(tmp) / "claim_check"
            claim_result = request("tools/call", {
                "name": "falsiflow.validate_claims",
                "arguments": {
                    "config": str(ai_template / "project.json"),
                    "evidence": str(ai_template / "evidence_pass_demo.csv"),
                    "out_dir": str(claim_dir),
                    "force": True,
                },
            })
            claim_payload = decode_text_payload(claim_result)
            add("validate_claims", claim_payload.get("status") == "claim_check_ready", "MCP validate_claims runs claim-check on a bundled source-backed fixture.", {"status": str(claim_payload.get("status", ""))})

            outputs = claim_payload.get("outputs", {})
            if not isinstance(outputs, dict):
                raise ValueError("validate_claims did not return an outputs object.")
            bundle_zip = str(outputs.get("bundle_zip", ""))
            claim_check_json = str(outputs.get("claim_check", ""))

            bundle_result = request("tools/call", {
                "name": "falsiflow.check_bundle",
                "arguments": {"zip_path": bundle_zip},
            })
            bundle_payload = decode_text_payload(bundle_result)
            add("check_bundle", bundle_payload.get("status") == "bundle_verified", "MCP check_bundle verifies the bundle produced by validate_claims.", {"status": str(bundle_payload.get("status", ""))})

            blocker_result = request("tools/call", {
                "name": "falsiflow.explain_blockers",
                "arguments": {"claim_check_json": claim_check_json},
            })
            blocker_payload = decode_text_payload(blocker_result)
            add("explain_blockers", blocker_payload.get("status") == "claim_check_ready", "MCP explain_blockers reads claim_check.json and returns reviewer context.", {"status": str(blocker_payload.get("status", ""))})
    except Exception as exc:
        add("selftest_exception", False, str(exc))

    status = "mcp_selftest_ready" if not failures else "mcp_selftest_blocked"
    return {
        "status": status,
        "server": SERVER_INFO,
        "tool_count": len(tool_names),
        "resource_count": len(resource_uris),
        "checked_tool_statuses": {
            "falsiflow.validate_claims": str(claim_payload.get("status", "")),
            "falsiflow.check_bundle": str(bundle_payload.get("status", "")),
            "falsiflow.explain_blockers": str(blocker_payload.get("status", "")),
            "falsiflow.create_evidence_todo": str(todo_payload.get("status", "")),
        },
        "checks": checks,
        "failure_count": len(failures),
        "failures": failures,
    }


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
