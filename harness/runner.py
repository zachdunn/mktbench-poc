"""Run one task end-to-end: sandbox → adapter → graders → score → report files."""
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
from .taskspec import Task, load_task_by_id
from .universe import Universe


def make_adapter(spec: str):
    if spec.startswith("replay:"):
        return ReplayAdapter(spec.split(":", 1)[1])
    if spec == "llm":
        return LLMAdapter()
    raise ValueError(f"unknown agent spec {spec!r} (use replay:<variant> or llm)")


def run_task(task_id: str, agent_spec: str, universe_name: str = "alma-botanica",
             out_dir: Path | None = None, offline: bool | None = None) -> dict:
    task = load_task_by_id(task_id, universe_name)
    offline = config.offline_default() if offline is None else offline
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{task_id}-{agent_spec.replace(':', '_')}"
    run_dir = Path(out_dir) if out_dir else config.RUNS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    universe_root = config.UNIVERSES_ROOT / universe_name
    sandbox = Sandbox(universe_root, run_dir)
    adapter = make_adapter(agent_spec)
    deliverable: Deliverable = adapter.run(sandbox, task)

    ctx = GradingContext(universe=Universe(universe_root), offline=offline, run_dir=run_dir)
    results = grade_task(task, deliverable, ctx)
    score = scoring.score_task(task, results)

    report = {
        "run_id": run_id,
        "agent": adapter.name,
        "offline": offline,
        "task": {"id": task.id, "title": task.title, "universe": task.universe,
                 "escalation_role": task.escalation_role},
        "score": score,
        "criteria": [dataclasses.asdict(r) for r in results],
        "invariants": ctx.invariant_report,
        "ledger": ctx.ledger_summary,
        "judge_transcripts": ctx.judge_transcripts,
        "access_log": sandbox.access_log,
        "deliverable": {"parts": deliverable.parts, "meta": {k: v for k, v in deliverable.meta.items()
                                                             if k != "transcript"}},
    }
    (run_dir / "report.json").write_text(json.dumps(report, indent=1, default=str))
    (run_dir / "report.html").write_text(report_html.render(report))
    if deliverable.meta.get("transcript"):
        (run_dir / "agent_transcript.json").write_text(
            json.dumps(deliverable.meta["transcript"], indent=1, default=str))
    report["run_dir"] = str(run_dir)
    return report
