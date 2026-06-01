"""Regression checks for the Falsiflow core reset."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts" / "falsiflow.py"
EXAMPLE = ROOT / "examples" / "minimal_numeric_claim"
CONFIG = EXAMPLE / "project.json"
PLACEHOLDER = EXAMPLE / "evidence_placeholder.csv"
BLOCKED = EXAMPLE / "evidence_blocked.csv"
READY = EXAMPLE / "evidence_ready.csv"


def run_cli(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def assert_core_claim_gate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        placeholder = run_cli([
            "check",
            "--config",
            str(CONFIG),
            "--evidence",
            str(PLACEHOLDER),
            "--out-dir",
            str(tmp_path / "placeholder"),
            "--strict",
            "--force",
        ])
        assert placeholder.returncode == 2
        assert placeholder.stdout.splitlines()[0] == "claim_blocked"
        assert "value is blank or placeholder" in placeholder.stdout

        weak_lift = run_cli([
            "check",
            "--config",
            str(CONFIG),
            "--evidence",
            str(BLOCKED),
            "--out-dir",
            str(tmp_path / "blocked"),
            "--strict",
            "--force",
        ])
        assert weak_lift.returncode == 2
        assert weak_lift.stdout.splitlines()[0] == "claim_blocked"
        assert "Variant must beat baseline by at least 5%" in weak_lift.stdout

        ready_out = tmp_path / "ready"
        ready = run_cli([
            "check",
            "--config",
            str(CONFIG),
            "--evidence",
            str(READY),
            "--out-dir",
            str(ready_out),
            "--strict",
            "--force",
        ], check=True)
        assert ready.stdout.splitlines()[0] == "claim_ready"
        assert (ready_out / "claim_check.json").exists()
        assert (ready_out / "claim_check.md").exists()
        assert (ready_out / "evidence_bundle.zip").exists()

        json_out = tmp_path / "json"
        json_run = run_cli([
            "check",
            "--config",
            str(CONFIG),
            "--evidence",
            str(BLOCKED),
            "--out-dir",
            str(json_out),
            "--force",
            "--json",
        ], check=True)
        payload = json.loads(json_run.stdout)
        assert payload["status"] == "claim_blocked"
        assert payload["blocking_stage"] == "acceptance_rules"
        assert payload["evidence_todo"]
        assert payload["report"].endswith("claim_check.md")
        assert payload["bundle"].endswith("evidence_bundle.zip")

        legacy = run_cli([
            "claim-check",
            "--config",
            str(CONFIG),
            "--evidence",
            str(READY),
            "--out-dir",
            str(tmp_path / "legacy"),
            "--strict",
            "--force",
        ], check=True)
        assert legacy.stdout.splitlines()[0] == "claim_ready"


def assert_public_surface() -> None:
    help_run = run_cli(["--help"], check=True)
    help_text = help_run.stdout
    assert "check" in help_text
    assert "schema" in help_text
    for hidden in [
        "quickstart",
        "doctor",
        "release-check",
        "adoption-check",
        "demo",
        "discover",
        "mcp",
        "template",
        "launch-kit",
    ]:
        assert hidden not in help_text

    project_schema = run_cli(["schema", "--kind", "project"], check=True)
    assert json.loads(project_schema.stdout)["title"] == "Falsiflow project config"
    evidence_schema = run_cli(["schema", "--kind", "evidence-row"], check=True)
    assert json.loads(evidence_schema.stdout)["title"] == "Falsiflow evidence row"


def main() -> int:
    assert_core_claim_gate()
    assert_public_surface()
    print("Falsiflow core reset regression passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
