#!/usr/bin/env python3
"""Regression-test that portfolio selection never substitutes for the claim audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = ROOT / "data" / "limina_portfolio_claim_boundary_regression.json"
REPORT_OUT = ROOT / "reports" / "limina_portfolio_claim_boundary_regression.md"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def branch_by_id(portfolio: dict[str, Any], technology_id: str) -> dict[str, Any]:
    for item in portfolio.get("branches", []):
        if item.get("technology_id") == technology_id:
            return item
    return {}


def assert_condition(assertions: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    assertions.append({"name": name, "passed": passed, "detail": detail})


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIMINA Portfolio Claim-Boundary Regression",
        "",
        "This regression proves that the portfolio selector cannot declare material suitability before the final claim audit.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Portfolio status:** `{result.get('portfolio_status', '-')}`",
        f"**Primary next branch:** `{result.get('primary_next_branch', '-')}`",
        "",
        "## Assertions",
        "",
        "| Assertion | Result | Detail |",
        "| --- | --- | --- |",
    ]
    for item in result["assertions"]:
        status = "pass" if item["passed"] else "fail"
        detail = str(item["detail"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{item['name']}` | `{status}` | {detail} |")
    lines.extend([
        "",
        "## Boundary",
        "",
        "Passing-looking portfolio inputs should only produce a claim-audit-required workflow state. The suitability claim remains gated by `audit_limina_suitability_claim.py`.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    tmp_root = Path(tempfile.mkdtemp(prefix="limina_portfolio_claim_boundary_"))
    technologies = tmp_root / "technologies.json"
    readiness = tmp_root / "zrc_readiness.json"
    sentinel = tmp_root / "zrc_sentinel.json"
    ranking = tmp_root / "ranking.json"
    h_a = tmp_root / "h_a.json"
    h_a_service = tmp_root / "h_a_service.json"
    nhi_results = tmp_root / "nhi_results.json"
    nhi_long_results = tmp_root / "nhi_long_results.json"
    portfolio_json = tmp_root / "portfolio.json"
    portfolio_report = tmp_root / "portfolio.md"

    write_json(technologies, [
        {
            "id": "limina_zrc_nd_v0_1",
            "name": "ZRC-ND",
            "priority_lane": "LIMINA-External-1",
            "status": "nominated",
            "score": {"weighted_internal_score": 4.02},
        },
        {
            "id": "limina_nhi_pedot_laminin_v0_1",
            "name": "NHI-PEDOT",
            "priority_lane": "LIMINA-Cell-1",
            "status": "nominated",
            "score": {"weighted_internal_score": 4.08},
        },
    ])
    write_json(readiness, {"readiness": "suitable", "suitable": True})
    write_json(sentinel, {"status": "sentinel_passes_continue"})
    write_json(ranking, {
        "items": [
            {
                "id": "limina_alg_lam_pedot_lowdose_v0_2",
                "priority": "promote_now",
            }
        ]
    })
    write_json(h_a, {"status": "h_a_lead_passes_continue_h_b"})
    write_json(h_a_service, {"status": "ready_to_request_real_measurements"})
    write_json(nhi_results, {"summary": {"status": "nhi_pedot_passes_gates"}})
    write_json(nhi_long_results, {"summary": {"status": "nhi_pedot_long_passes_gates"}})

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/select_limina_next_technology.py",
            "--technologies",
            str(technologies),
            "--readiness",
            str(readiness),
            "--sentinel",
            str(sentinel),
            "--discovery-ranking",
            str(ranking),
            "--nhi-h-a",
            str(h_a),
            "--nhi-h-a-service",
            str(h_a_service),
            "--nhi-results",
            str(nhi_results),
            "--nhi-long-results",
            str(nhi_long_results),
            "--json-out",
            str(portfolio_json),
            "--report",
            str(portfolio_report),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    portfolio = read_json(portfolio_json)
    zrc = branch_by_id(portfolio, "limina_zrc_nd_v0_1")
    nhi = branch_by_id(portfolio, "limina_nhi_pedot_laminin_v0_1")

    assertions: list[dict[str, Any]] = []
    assert_condition(
        assertions,
        "selector_command_succeeded",
        completed.returncode == 0,
        f"returncode={completed.returncode}; stderr={completed.stderr.strip()}",
    )
    assert_condition(
        assertions,
        "portfolio_does_not_claim_suitable_material_present",
        portfolio.get("status") != "suitable_material_present",
        f"portfolio status={portfolio.get('status')}",
    )
    assert_condition(
        assertions,
        "portfolio_requires_claim_audit",
        portfolio.get("status") == "claim_audit_required",
        f"portfolio status={portfolio.get('status')}",
    )
    assert_condition(
        assertions,
        "zrc_suitable_readiness_still_requires_claim_audit",
        zrc.get("portfolio_status") == "readiness_gates_passed_claim_audit_required",
        f"zrc status={zrc.get('portfolio_status')}",
    )
    assert_condition(
        assertions,
        "nhi_long_pass_still_requires_claim_audit",
        nhi.get("portfolio_status") == "long_gates_passed_claim_audit_required",
        f"nhi status={nhi.get('portfolio_status')}",
    )

    status = "pass" if assertions and all(item["passed"] for item in assertions) else "fail"
    result = {
        "status": status,
        "tmp_dir": str(tmp_root),
        "portfolio_status": portfolio.get("status"),
        "primary_next_branch": portfolio.get("primary_next_branch"),
        "portfolio": portfolio,
        "command": {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        },
        "assertions": assertions,
    }
    write_json(DATA_OUT, result)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(render_report(result), encoding="utf-8")

    print(f"LIMINA portfolio claim-boundary regression: {status}")
    print(f"Wrote {DATA_OUT}")
    print(f"Wrote {REPORT_OUT}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
