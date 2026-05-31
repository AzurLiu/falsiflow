"""Browser demo, wizard, and workbench workflows for Falsiflow."""

from __future__ import annotations

import base64
from importlib import resources
import json
import os
from html import escape
from pathlib import Path
import shutil
from typing import Protocol
import urllib.parse

from .doctor import default_project_evidence_path, run_doctor
from .quickstart import prepare_output_directory


LIVE_PR_STORY_REEL = "falsiflow_live_pr_story_reel.svg"
LIVE_PR_STORY_REEL_RELATIVE = f"assets/{LIVE_PR_STORY_REEL}"
DOWNSTREAM_PR_PROOF_STRIP = "falsiflow_downstream_pr_proof_strip.svg"
DOWNSTREAM_PR_PROOF_STRIP_RELATIVE = f"assets/{DOWNSTREAM_PR_PROOF_STRIP}"


class QuickstartRunner(Protocol):
    def __call__(
        self,
        template: str,
        out_dir: Path,
        template_roots: list[Path] | None = None,
        force: bool = False,
        include_env: bool = True,
    ) -> dict[str, object]: ...


class TemplateResolver(Protocol):
    def __call__(
        self,
        template: str,
        extra_roots: list[Path] | None = None,
        include_env: bool = True,
    ) -> Path | None: ...


def file_href(report_dir: Path, path_text: object) -> str:
    raw = str(path_text or "").strip()
    if not raw:
        return "#"
    path = Path(raw).expanduser()
    if not path.is_absolute():
        report_parts = report_dir.parts
        if report_parts and path.parts[: len(report_parts)] == report_parts:
            path = path.resolve()
        else:
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


def copy_packaged_demo_asset(out_dir: Path, asset_name: str, relative_path: str) -> Path:
    target = out_dir / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        asset_text = resources.files("falsiflow").joinpath("assets", asset_name).read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, OSError):
        asset_text = (Path(__file__).resolve().parents[1] / "docs" / "assets" / asset_name).read_text(encoding="utf-8")
    target.write_text(asset_text, encoding="utf-8")
    return target


def copy_live_pr_story_reel(out_dir: Path) -> Path:
    return copy_packaged_demo_asset(out_dir, LIVE_PR_STORY_REEL, LIVE_PR_STORY_REEL_RELATIVE)


def copy_downstream_pr_proof_strip(out_dir: Path) -> Path:
    return copy_packaged_demo_asset(out_dir, DOWNSTREAM_PR_PROOF_STRIP, DOWNSTREAM_PR_PROOF_STRIP_RELATIVE)


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
    main { width: min(1180px, calc(100% - 32px)); margin: 24px auto 48px; }
    header { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 14px; }
    h1 { margin: 0 0 8px; font-size: 32px; letter-spacing: 0; }
    h2 { margin: 0 0 10px; font-size: 17px; letter-spacing: 0; }
    p { margin: 0; color: var(--muted); line-height: 1.5; }
    a { color: var(--accent); font-weight: 700; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, 0.8fr); gap: 12px; }
    .review-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(360px, 0.9fr); gap: 12px; margin-top: 12px; }
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
    .flow { display: grid; gap: 8px; }
    .stage, .artifact, .checklist-item, .source-row { border: 1px solid var(--line); border-radius: 5px; padding: 10px; background: #fbfdff; }
    .stage { display: grid; grid-template-columns: minmax(130px, 0.9fr) minmax(0, 1fr) auto; gap: 8px; align-items: center; }
    .artifact { display: grid; grid-template-columns: minmax(120px, 0.55fr) minmax(0, 1fr) auto; gap: 8px; align-items: start; }
    .lineage { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
    .lineage .metric { min-height: 62px; }
    .pill { display: inline-flex; align-items: center; justify-content: center; min-height: 26px; border-radius: 999px; padding: 3px 9px; font-size: 12px; font-weight: 700; color: #fff; background: var(--blocked); }
    .pill.ready { background: var(--ready); }
    .pill.neutral { background: #4f5f6f; }
    .path { font-size: 12px; color: var(--muted); overflow-wrap: anywhere; }
    .checklist, .artifact-list, .source-list { display: grid; gap: 8px; margin-top: 10px; }
    .checklist-item code { display: block; margin-top: 6px; white-space: pre-wrap; overflow-wrap: anywhere; }
    .source-row { display: grid; grid-template-columns: minmax(0, 1fr) 110px 78px; gap: 8px; align-items: center; }
    .empty { color: var(--muted); font-size: 13px; margin-top: 8px; }
    ul { margin: 10px 0 0; padding-left: 20px; }
    li { margin: 8px 0; }
    pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #eef3f7; border: 1px solid var(--line); border-radius: 5px; padding: 12px; max-height: 260px; overflow: auto; }
    .hidden { display: none; }
    @media (max-width: 960px) { header, .grid, .review-grid { display: block; } section, .status { margin-top: 12px; } }
    @media (max-width: 640px) { .stage, .artifact, .source-row { grid-template-columns: 1fr; } .lineage { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
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
    <div class="review-grid">
      <section>
        <h2>Review Flow</h2>
        <div id="reviewFlow" class="flow"><p class="empty">No run yet.</p></div>
      </section>
      <section>
        <h2>Evidence Lineage</h2>
        <div id="lineage" class="lineage"></div>
        <div id="sourceList" class="source-list"></div>
      </section>
      <section>
        <h2>Review Artifacts</h2>
        <div id="artifacts" class="artifact-list"><p class="empty">No artifacts yet.</p></div>
      </section>
      <section>
        <h2>Repair Checklist</h2>
        <div id="repair" class="checklist"><p class="empty">No run yet.</p></div>
      </section>
    </div>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[char]));
    }
    function pill(status, ready) {
      const text = escapeHtml(status || "not_run");
      const tone = ready === true ? "ready" : ready === false ? "" : "neutral";
      return `<span class="pill ${tone}">${text}</span>`;
    }
    function linkedText(text, href) {
      const safeText = escapeHtml(text || "-");
      return href ? `<a href="${escapeHtml(href)}">${safeText}</a>` : safeText;
    }
    async function loadTemplates() {
      const response = await fetch("/api/templates");
      const payload = await response.json();
      $("template").innerHTML = payload.templates.map((item) => `<option value="${escapeHtml(item.template)}">${escapeHtml(item.template)} - ${escapeHtml(item.name)}</option>`).join("");
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
      status.querySelector(".hint").textContent = payload.blocking_stage ? `Blocking stage: ${payload.blocking_stage}` : "Run a check to see claim readiness, blockers, and review links.";
      $("claim").textContent = payload.claim_check_status || "-";
      $("sourcesStatus").textContent = payload.source_status || "-";
      $("bundle").textContent = payload.bundle_status || "-";
      $("failures").textContent = String(payload.failure_count ?? "-");
      const links = payload.links || {};
      $("links").innerHTML = Object.entries(links)
        .filter(([, href]) => href)
        .map(([label, href]) => `<li><a href="${escapeHtml(href)}">${escapeHtml(label.replaceAll("_", " "))}</a></li>`)
        .join("");
      $("details").classList.remove("hidden");
      $("details").textContent = JSON.stringify(payload.next_actions || payload.failures || [], null, 2);
      renderReviewFlow(payload.review_flow || []);
      renderLineage(payload.evidence_lineage || {});
      renderArtifacts(payload.review_artifacts || []);
      renderRepair(payload.repair_checklist || []);
    }
    function renderReviewFlow(flow) {
      if (!flow.length) {
        $("reviewFlow").innerHTML = '<p class="empty">No run yet.</p>';
        return;
      }
      $("reviewFlow").innerHTML = flow.map((stage) => `
        <div class="stage">
          <b>${linkedText(stage.stage, stage.href)}</b>
          <span class="path">${escapeHtml(stage.href || "")}</span>
          ${pill(stage.status, stage.ready)}
        </div>
      `).join("");
    }
    function renderLineage(lineage) {
      const metrics = [
        ["Project", lineage.project_id || "-"],
        ["Claim", lineage.claim_id || "-"],
        ["Evidence rows", lineage.evidence_row_count ?? "-"],
        ["Sources present", `${lineage.present_source_file_count ?? "-"} / ${lineage.referenced_source_file_count ?? "-"}`],
        ["Missing sources", lineage.missing_source_file_count ?? "-"],
        ["Blank source rows", lineage.blank_source_row_count ?? "-"],
        ["Bundle artifacts", lineage.artifact_count ?? "-"],
        ["Verified artifacts", lineage.checked_artifact_count ?? "-"],
        ["Verification issues", lineage.verification_issue_count ?? "-"]
      ];
      $("lineage").innerHTML = metrics.map(([label, value]) => `<div class="metric"><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b></div>`).join("");
      const files = Array.isArray(lineage.source_files) ? lineage.source_files : [];
      $("sourceList").innerHTML = files.length ? files.slice(0, 8).map((file) => `
        <div class="source-row">
          <b>${escapeHtml(file.source_file || "")}</b>
          ${pill(file.status || "", file.status === "present")}
          <span class="path">${escapeHtml(file.reference_count ?? 0)} refs</span>
        </div>
      `).join("") : '<p class="empty">No source files recorded yet.</p>';
    }
    function renderArtifacts(artifacts) {
      if (!artifacts.length) {
        $("artifacts").innerHTML = '<p class="empty">No artifacts yet.</p>';
        return;
      }
      $("artifacts").innerHTML = artifacts.map((artifact) => `
        <div class="artifact">
          <b>${linkedText(artifact.label, artifact.href)}</b>
          <span>${escapeHtml(artifact.purpose || "")}</span>
          ${pill(artifact.status || "", artifact.status && !String(artifact.status).includes("blocked") && !String(artifact.status).includes("failed"))}
        </div>
      `).join("");
    }
    function renderRepair(items) {
      if (!items.length) {
        $("repair").innerHTML = '<p class="empty">No repair checklist items recorded.</p>';
        return;
      }
      $("repair").innerHTML = items.map((item) => `
        <div class="checklist-item">
          <b>${escapeHtml(item.rank || "")}. ${escapeHtml(item.action_id || "")}</b>
          <p>${escapeHtml(item.why || "")}</p>
          <code>${escapeHtml(item.command || "")}</code>
          <p class="path">${escapeHtml(item.success_signal || "")}</p>
        </div>
      `).join("");
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
    async function loadPreviousState() {
      const response = await fetch("/api/workbench/state");
      if (response.ok) {
        const payload = await response.json();
        if (payload.status && payload.status !== "workbench_not_run") setResult(payload);
      }
    }
    loadTemplates()
      .then(loadPreviousState)
      .catch((error) => setResult({ status: "workbench_blocked", failure_count: 1, failures: [{ message: String(error) }] }));
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
    headline = "CI gates for claims before they ship"
    summary_text = (
        "Real AI, RAG, and product-metric PRs fail on placeholder evidence, then pass after the evidence is source-backed."
        if ready
        else "The local demo needs attention before it can be used as a clean starter."
    )
    first_command = str(next_commands[0]) if next_commands else "falsiflow doctor --project-dir falsiflow_try/project --strict"
    proof_rows = [
        (
            "Blocked placeholder",
            "claim_check_blocked",
            "Missing source files, placeholder values, or unpinned benchmark metadata stop the claim before it reaches release notes.",
        ),
        (
            "Source-backed pass",
            str(summary.get("claim_check_status", "")),
            "Measured rows, required metadata, source manifests, audit reports, and bundle verification agree.",
        ),
    ]
    proof_html = "\n".join(
        f"""        <article class="proof {escape('ready' if 'ready' in status else 'blocked')}">
          <span>{escape(kicker)}</span>
          <strong>{escape(status)}</strong>
          <p>{escape(body)}</p>
        </article>"""
        for kicker, status, body in proof_rows
    )
    use_cases = [
        (
            "AI eval claim",
            "Model beats baseline",
            "Blocks public comparison until dataset, model, raw-output, and reproducibility evidence are pinned.",
        ),
        (
            "RAG eval claim",
            "Grounded answers improved",
            "Blocks release notes until retrieval, faithfulness, citation, raw export, and reproducibility evidence are source-backed.",
        ),
        (
            "Product metric",
            "Activation improved",
            "Blocks launch until metric definition, exposure, guardrails, rollback owner, and dashboard evidence are present.",
        ),
        (
            "R&D result",
            "Experiment is ready",
            "Blocks advancement until measured evidence, raw source files, thresholds, and review artifacts line up.",
        ),
        (
            "Vendor handoff",
            "Supplier can run it",
            "Keeps contact claims, scope confirmation, and measured-data return requirements separate.",
        ),
    ]
    use_case_html = "\n".join(
        f"""        <article class="case">
          <span>{escape(label)}</span>
          <h2>{escape(claim)}</h2>
          <p>{escape(body)}</p>
        </article>"""
        for label, claim, body in use_cases
    )
    pr_story = [
        (
            "1. AI eval PR",
            "AI eval improved",
            "A separate repo tries to ship an eval claim before the dataset, raw outputs, baseline, and metadata are reviewable.",
            "Open AI PR #1",
            "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1",
            "neutral",
        ),
        (
            "2. AI CI blocks it",
            "claim_check_blocked",
            "Strict CI refuses placeholder evidence and keeps the claim out of release notes.",
            "AI blocked run",
            "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711652990",
            "blocked",
        ),
        (
            "3. AI evidence passes",
            "claim_check_ready",
            "The same PR passes after source-backed eval rows, pinned versions, raw artifacts, and a review bundle are added.",
            "AI ready run",
            "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/actions/runs/26711669112",
            "ready",
        ),
        (
            "4. RAG eval PR",
            "RAG quality improved",
            "A RAG repo tries to ship a grounded-answer claim before retrieval, faithfulness, citation, and reproducibility evidence are complete.",
            "Open RAG PR #1",
            "https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/pull/1",
            "neutral",
        ),
        (
            "5. RAG CI blocks it",
            "claim_check_blocked",
            "Strict CI rejects the placeholder eval-set row and missing raw RAG export.",
            "RAG blocked run",
            "https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721829145",
            "blocked",
        ),
        (
            "6. RAG evidence passes",
            "claim_check_ready",
            "The same PR passes after source-backed retrieval, faithfulness, citation, reproducibility rows, and the raw export are added.",
            "RAG ready run",
            "https://github.com/AzurLiu/falsiflow-downstream-rag-eval-demo/actions/runs/26721856616",
            "ready",
        ),
        (
            "7. Product metric PR",
            "Activation lifted",
            "A product repo tries to ship a launch metric before metric provenance, lift, guardrails, and rollback readiness are reviewable.",
            "Open product PR #1",
            "https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/pull/1",
            "neutral",
        ),
        (
            "8. Product CI blocks it",
            "claim_check_blocked",
            "Strict CI rejects placeholder analytics evidence before the launch claim can pass.",
            "Product blocked run",
            "https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726360229",
            "blocked",
        ),
        (
            "9. Product evidence passes",
            "claim_check_ready",
            "The same PR passes after source-backed metric provenance, lift, guardrail, and rollback-readiness rows are added.",
            "Product ready run",
            "https://github.com/AzurLiu/falsiflow-downstream-product-metric-demo/actions/runs/26726392921",
            "ready",
        ),
    ]
    pr_story_html = "\n".join(
        f"""        <article class="story-card {escape(kind)}">
          <span>{escape(kicker)}</span>
          <h2>{escape(title)}</h2>
          <p>{escape(body)}</p>
          <a href="{escape(href)}">{escape(link_label)}</a>
        </article>"""
        for kicker, title, body, link_label, href, kind in pr_story
    )
    downstream_proof_strip_src = file_href(report_dir, outputs.get("downstream_proof_strip", report_dir / DOWNSTREAM_PR_PROOF_STRIP_RELATIVE))
    story_reel_src = file_href(report_dir, outputs.get("story_reel", report_dir / LIVE_PR_STORY_REEL_RELATIVE))
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
  <meta name="description" content="Live downstream PR stories: Falsiflow blocks unverifiable AI, RAG, and product-metric evidence in CI, then passes the same claims after source-backed evidence is added.">
  <meta property="og:title" content="Falsiflow: unverifiable AI, RAG, and product claims should fail CI">
  <meta property="og:description" content="See downstream AI, RAG, and product-metric PRs move from claim_check_blocked to claim_check_ready after source-backed evidence is added.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://azurliu.github.io/falsiflow/">
  <meta property="og:image" content="https://raw.githubusercontent.com/AzurLiu/falsiflow/main/docs/assets/falsiflow_downstream_pr_proof_strip.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Falsiflow: unverifiable AI, RAG, and product claims should fail CI">
  <meta name="twitter:description" content="Real PR stories: placeholder AI, RAG, and product evidence is blocked, then source-backed evidence passes.">
  <meta name="twitter:image" content="https://raw.githubusercontent.com/AzurLiu/falsiflow/main/docs/assets/falsiflow_downstream_pr_proof_strip.png">
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
    .story-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
    .story-card {{ min-height: 202px; }}
    .story-card h2 {{ font-size: 20px; }}
    .story-card.blocked h2 {{ color: var(--blocked); }}
    .story-card.ready h2 {{ color: var(--ready); }}
    .story-reel {{ margin-top: 14px; border: 1px solid var(--line); border-radius: 6px; overflow: hidden; background: #f8fafc; }}
    .story-reel img {{ display: block; width: 100%; height: auto; }}
    .replay-links {{ margin-top: 12px; }}
    .proof-grid, .case-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .case-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .proof {{ min-height: 128px; }}
    .proof strong {{ display: block; font-size: 22px; margin-bottom: 8px; color: var(--blocked); overflow-wrap: anywhere; }}
    .proof.ready strong {{ color: var(--ready); }}
    .case {{ min-height: 168px; }}
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
      .metrics, .cards, .case-grid, .story-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 620px) {{
      .metrics, .cards, .proof-grid, .case-grid, .story-grid {{ grid-template-columns: 1fr; }}
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
    <section>
      <h2>Live Downstream PR Story</h2>
      <div class="story-grid">
{pr_story_html}
      </div>
      <div class="story-reel">
        <img src="{escape(downstream_proof_strip_src, quote=True)}" alt="Falsiflow downstream PR proof strip">
      </div>
      <div class="story-reel">
        <img src="{escape(story_reel_src, quote=True)}" alt="Falsiflow in-repo PR replay reel">
      </div>
      <p class="replay-links">In-repo replay:
        <a href="https://github.com/AzurLiu/falsiflow/pull/17">PR #17</a>,
        <a href="https://github.com/AzurLiu/falsiflow/actions/runs/26708459093">blocked run 26708459093</a>,
        <a href="https://github.com/AzurLiu/falsiflow/actions/runs/26708472653">ready run 26708472653</a>.
      </p>
    </section>
    <div class="metrics">
      <div class="metric"><span>Example</span><strong>{escape(str(summary.get("template", "")))}</strong></div>
      <div class="metric"><span>Decision check</span><strong>{escape(str(summary.get("claim_check_status", "")))}</strong></div>
      <div class="metric"><span>Source files</span><strong>{escape(str(summary.get("source_status", "")))}</strong></div>
      <div class="metric"><span>Review package</span><strong>{escape(str(summary.get("verification_status", "")))}</strong></div>
    </div>
    <section>
      <h2>Ready Or Blocked</h2>
      <div class="proof-grid">
{proof_html}
      </div>
    </section>
    <section>
      <h2>Claims This Demo Targets</h2>
      <div class="case-grid">
{use_case_html}
      </div>
    </section>
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
    outputs.setdefault("story_reel", str(out_dir / LIVE_PR_STORY_REEL_RELATIVE))
    outputs.setdefault("downstream_proof_strip", str(out_dir / DOWNSTREAM_PR_PROOF_STRIP_RELATIVE))
    summary.setdefault("out_dir", str(out_dir))
    copy_live_pr_story_reel(out_dir)
    copy_downstream_pr_proof_strip(out_dir)
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

def run_try(
    template: str,
    out_dir: Path,
    template_roots: list[Path] | None = None,
    force: bool = False,
    include_env: bool = True,
    *,
    quickstart_runner: QuickstartRunner,
) -> dict[str, object]:
    prepare_output_directory(out_dir, "try output directory", force=force)
    out_dir.mkdir(parents=True, exist_ok=True)
    project_dir = out_dir / "project"
    quickstart = quickstart_runner(template, project_dir, template_roots=template_roots, force=True, include_env=include_env)
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
    outputs["story_reel"] = str(copy_live_pr_story_reel(out_dir))
    outputs["downstream_proof_strip"] = str(copy_downstream_pr_proof_strip(out_dir))
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

def read_optional_json_object(path_text: object) -> dict[str, object]:
    text = str(path_text or "").strip()
    if not text:
        return {}
    try:
        value = json.loads(Path(text).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}

def workbench_stage(stage: str, status: object, ready: bool, href: str = "") -> dict[str, object]:
    return {
        "stage": stage,
        "status": str(status or ""),
        "ready": ready,
        "href": href,
    }

def workbench_artifact(label: str, status: object, href: str, purpose: str) -> dict[str, object]:
    return {
        "label": label,
        "status": str(status or ""),
        "href": href,
        "purpose": purpose,
    }

def write_workbench_uploads(
    out_dir: Path,
    payload: dict[str, object],
    *,
    template_resolver: TemplateResolver,
) -> tuple[str, Path, Path, Path]:
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
        source_template = template_resolver(template)
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

def run_workbench_check(
    out_dir: Path,
    payload: dict[str, object],
    *,
    template_resolver: TemplateResolver,
) -> dict[str, object]:
    template, project_dir, config, evidence = write_workbench_uploads(out_dir, payload, template_resolver=template_resolver)
    doctor_dir = project_dir / "doctor"
    doctor = run_doctor(project_dir, config, evidence, doctor_dir, force=True)
    claim_check = doctor.get("claim_check_summary", {}) if isinstance(doctor.get("claim_check_summary"), dict) else {}
    claim_outputs = claim_check.get("outputs", {}) if isinstance(claim_check.get("outputs"), dict) else {}
    doctor_outputs = doctor.get("outputs", {}) if isinstance(doctor.get("outputs"), dict) else {}
    source_summary = read_optional_json_object(claim_outputs.get("source_manifest", ""))
    ready = doctor.get("status") == "doctor_ready"
    links = {
        "project_config": workbench_link(out_dir, config),
        "evidence_csv": workbench_link(out_dir, evidence),
        "doctor_summary": workbench_link(out_dir, doctor_outputs.get("doctor_summary", "")),
        "doctor_report": workbench_link(out_dir, doctor_outputs.get("doctor_report", "")),
        "claim_check_json": workbench_link(out_dir, claim_outputs.get("claim_check", "")),
        "claim_check_report": workbench_link(out_dir, claim_outputs.get("claim_check_report", "")),
        "claim_audit_report": workbench_link(out_dir, claim_outputs.get("claim_audit_report", "")),
        "audit_review_report": workbench_link(out_dir, claim_outputs.get("audit_review_report", "")),
        "source_manifest": workbench_link(out_dir, claim_outputs.get("source_manifest", "")),
        "source_manifest_report": workbench_link(out_dir, claim_outputs.get("source_manifest_report", "")),
        "dashboard": workbench_link(out_dir, claim_outputs.get("dashboard", "")),
        "bundle_manifest": workbench_link(out_dir, claim_outputs.get("bundle_manifest", "")),
        "evidence_bundle": workbench_link(out_dir, claim_outputs.get("bundle_zip", "")),
        "bundle_verification": workbench_link(out_dir, claim_outputs.get("bundle_verification", "")),
        "bundle_verification_report": workbench_link(out_dir, claim_outputs.get("bundle_verification_report", "")),
    }
    review_flow = [
        workbench_stage("Project config", doctor.get("project_status", ""), doctor.get("project_status") == "valid", links["project_config"]),
        workbench_stage("Evidence CSV", doctor.get("evidence_status", ""), doctor.get("evidence_status") == "evidence_ready", links["evidence_csv"]),
        workbench_stage("Claim gate", doctor.get("claim_check_status", ""), doctor.get("claim_check_status") == "claim_check_ready", links["claim_check_report"]),
        workbench_stage("Audit review", doctor.get("audit_review_status", ""), doctor.get("audit_review_status") == "review_ready", links["audit_review_report"]),
        workbench_stage("Source provenance", doctor.get("source_status", ""), doctor.get("source_status") == "sources_ready", links["source_manifest_report"]),
        workbench_stage("Bundle", doctor.get("bundle_status", ""), doctor.get("bundle_status") == "bundle_ready", links["bundle_manifest"]),
        workbench_stage("Verification", doctor.get("verification_status", ""), doctor.get("verification_status") == "bundle_verified", links["bundle_verification_report"]),
        workbench_stage("Human handoff", "ready_for_review" if ready else "blocked", ready, links["doctor_report"]),
    ]
    review_artifacts = [
        workbench_artifact("Doctor report", doctor.get("status", ""), links["doctor_report"], "Overall readiness, checks, and repair checklist."),
        workbench_artifact("Claim-check report", doctor.get("claim_check_status", ""), links["claim_check_report"], "Gate result, blockers, outputs, and next actions."),
        workbench_artifact("Audit review", doctor.get("audit_review_status", ""), links["audit_review_report"], "Reviewer decision card for the generated audit."),
        workbench_artifact("Source manifest", doctor.get("source_status", ""), links["source_manifest_report"], "Raw file provenance, missing sources, and allowed-root checks."),
        workbench_artifact("Dashboard", doctor.get("claim_check_status", ""), links["dashboard"], "Browser view of measured values and claim evidence."),
        workbench_artifact("Bundle verification", doctor.get("verification_status", ""), links["bundle_verification_report"], "Zip integrity and manifest verification."),
        workbench_artifact("Evidence bundle", doctor.get("bundle_status", ""), links["evidence_bundle"], "Shareable local review package."),
    ]
    evidence_lineage = {
        "project_id": str(claim_check.get("project_id", "")),
        "claim_id": str(claim_check.get("claim_id", "")),
        "config_path": str(config),
        "evidence_path": str(evidence),
        "evidence_row_count": int(source_summary.get("evidence_row_count", 0) or 0),
        "referenced_source_file_count": int(source_summary.get("referenced_source_file_count", 0) or 0),
        "present_source_file_count": int(source_summary.get("present_source_file_count", 0) or 0),
        "missing_source_file_count": int(source_summary.get("missing_source_file_count", 0) or 0),
        "outside_allowed_roots_count": int(source_summary.get("outside_allowed_roots_count", 0) or 0),
        "blank_source_row_count": int(source_summary.get("blank_source_row_count", 0) or 0),
        "source_policy_required": bool(source_summary.get("source_policy_required", True)),
        "artifact_count": int(claim_check.get("artifact_count", 0) or 0),
        "checked_artifact_count": int(claim_check.get("checked_artifact_count", 0) or 0),
        "verification_issue_count": int(claim_check.get("verification_issue_count", 0) or 0),
        "source_files": source_summary.get("source_files", [])[:20] if isinstance(source_summary.get("source_files"), list) else [],
    }
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
        "repair_checklist": doctor.get("repair_checklist", []),
        "review_flow": review_flow,
        "review_artifacts": [artifact for artifact in review_artifacts if artifact["href"]],
        "evidence_lineage": evidence_lineage,
        "links": links,
        "doctor_summary": doctor,
    }
    summary_path = out_dir / "workbench_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary
