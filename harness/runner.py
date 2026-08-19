"""Run and grade phases for one task.

The two phases are separable (harvey-labs convention): `execute_task` runs the agent and
persists everything grading needs (`deliverable.json`, `access_log.json`, agent transcript);
`grade_run` grades a saved run directory and writes `report.json`/`report.html`. Re-grading a
saved run — after a judge-prompt change, with a different judge model, or offline vs live —
costs zero agent tokens. `run_task` chains the two for the common case.
"""
from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone
from pathlib import Path

from . import config, report_html, scoring
from .adapters.base import Deliverable
from .adapters.llm import LLMAdapter
from .adapters.replay import ReplayAdapter
from .graders.base import GradingContext, grade_task
from .sandbox import Sandbox
from .taskspec import load_task_by_id
from .universe import Universe


def make_adapter(spec: str):
    if spec.startswith("replay:"):
        return ReplayAdapter(spec.split(":", 1)[1])
    if spec == "llm":
        return LLMAdapter()
    raise ValueError(f"unknown agent spec {spec!r} (use replay:<variant> or llm)")


def execute_task(task_id: str, agent_spec: str, universe_name: str = "alma-botanica",
                 out_dir: Path | None = None) -> Path:
    """Run phase: sandbox the universe, run the agent, persist the run. Returns the run dir."""
    task = load_task_by_id(task_id, universe_name)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{task_id}-{agent_spec.replace(':', '_')}"
    run_dir = Path(out_dir) if out_dir else config.RUNS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    sandbox = Sandbox(config.UNIVERSES_ROOT / universe_name, run_dir)
    adapter = make_adapter(agent_spec)
    deliverable: Deliverable = adapter.run(sandbox, task)

    meta = {k: v for k, v in deliverable.meta.items() if k != "transcript"}
    (run_dir / "deliverable.json").write_text(json.dumps({
        "run_id": run_id,
        "task_id": task.id,
        "universe": universe_name,
        "agent": adapter.name,
        "agent_model": config.agent_model() if agent_spec == "llm" else None,
        "executed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "parts": deliverable.parts,
        "meta": meta,
    }, indent=1, default=str))
    (run_dir / "access_log.json").write_text(json.dumps(sandbox.access_log, indent=1))
    if deliverable.meta.get("transcript"):
        (run_dir / "agent_transcript.json").write_text(
            json.dumps(deliverable.meta["transcript"], indent=1, default=str))
    return run_dir


def _load_saved_run(run_dir: Path) -> dict:
    """Read a saved run's grading inputs. Prefers deliverable.json; falls back to report.json
    (pre-phase-split runs and the committed examples/ snapshots carry the deliverable there)."""
    d = run_dir / "deliverable.json"
    if d.exists():
        saved = json.loads(d.read_text())
        log_path = run_dir / "access_log.json"
        saved["access_log"] = json.loads(log_path.read_text()) if log_path.exists() else []
        return saved
    r = run_dir / "report.json"
    if r.exists():
        old = json.loads(r.read_text())
        return {
            "run_id": old.get("run_id", run_dir.name),
            "task_id": old["task"]["id"],
            "universe": old["task"]["universe"],
            "agent": old.get("agent", "?"),
            "agent_model": None,
            "executed_at": None,
            "parts": old["deliverable"]["parts"],
            "meta": old["deliverable"].get("meta", {}),
            "access_log": old.get("access_log", []),
        }
    raise FileNotFoundError(f"{run_dir} has neither deliverable.json nor report.json")


def grade_run(run_dir: Path, offline: bool | None = None) -> dict:
    """Grade phase: grade a saved run directory and (re)write report.json / report.html."""
    run_dir = Path(run_dir)
    saved = _load_saved_run(run_dir)
    task = load_task_by_id(saved["task_id"], saved["universe"])
    offline = config.offline_default() if offline is None else offline

    deliverable = Deliverable(parts=saved["parts"], meta=saved.get("meta", {}))
    ctx = GradingContext(universe=Universe(config.UNIVERSES_ROOT / saved["universe"]),
                         offline=offline, run_dir=run_dir)
    results = grade_task(task, deliverable, ctx)
    score = scoring.score_task(task, results)

    report = {
        "run_id": saved["run_id"],
        "agent": saved["agent"],
        "agent_model": saved.get("agent_model"),
        "offline": offline,
        "judge_model": None if offline else config.judge_model(),
        "executed_at": saved.get("executed_at"),
        "graded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "task": {"id": task.id, "title": task.title, "universe": task.universe,
                 "escalation_role": task.escalation_role},
        "score": score,
        "criteria": [dataclasses.asdict(r) for r in results],
        "invariants": ctx.invariant_report,
        "ledger": ctx.ledger_summary,
        "judge_transcripts": ctx.judge_transcripts,
        "access_log": saved["access_log"],
        "deliverable": {"parts": deliverable.parts, "meta": deliverable.meta},
    }
    (run_dir / "report.json").write_text(json.dumps(report, indent=1, default=str))
    (run_dir / "report.html").write_text(report_html.render(report))
    report["run_dir"] = str(run_dir)
    return report


def run_task(task_id: str, agent_spec: str, universe_name: str = "alma-botanica",
             out_dir: Path | None = None, offline: bool | None = None) -> dict:
    """Run + grade in one shot (the common case)."""
    run_dir = execute_task(task_id, agent_spec, universe_name, out_dir)
    return grade_run(run_dir, offline)
