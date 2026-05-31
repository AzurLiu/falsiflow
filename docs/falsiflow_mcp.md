# Falsiflow MCP Server

`falsiflow mcp` runs an experimental local stdio MCP server for AI coding
agents. It is intentionally local-first: no network listener, no hosted API, no
database, and no model execution.

## Boundary

Falsiflow MCP lets an agent inspect claims before or during a PR:

- validate a local claim gate
- verify an evidence bundle
- explain blockers from `claim_check.json`
- create an evidence todo list from `project.json` and optional evidence CSV

It does not run models, run RAG pipelines, judge answers, store experiments, or
upload private eval artifacts.

## Start

```bash
pipx install falsiflow
falsiflow mcp
```

For local development:

```bash
python3 -m pip install -e .
python3 scripts/falsiflow.py mcp
```

## Tools

- `falsiflow.validate_claims`
- `falsiflow.check_bundle`
- `falsiflow.explain_blockers`
- `falsiflow.create_evidence_todo`

## Resources

- `falsiflow://schemas/evidence-row`
- `falsiflow://schemas/claim-check`
- `falsiflow://templates/rag-eval`
- `falsiflow://templates/local-llm-eval`
- `falsiflow://examples/blocked-pr`

## Agent Story

The intended use is simple: an AI coding agent can draft a README, eval report,
or PR claim, then ask Falsiflow which evidence rows are missing before CI
blocks the change. CI remains the final gate through `falsiflow claim-check` or
the GitHub Action.
