"""Grader dispatch: one CriterionResult per rubric criterion."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .. import config
from ..taskspec import Criterion, Task
from ..universe import Universe


@dataclass
class CriterionResult:
    criterion_id: str
    tier: str
    method: str
    text: str
    passed: bool
    detail: str = ""
    evidence_quote: str = ""
    judge_transcript: dict | None = None


@dataclass
class GradingContext:
    universe: Universe          # grader-side: includes answer_key access
    offline: bool
    run_dir: Path
    judge_transcripts: list[dict] = field(default_factory=list)
    invariant_report: dict | None = None   # filled by the invariant grader, reused in report
    ledger_summary: dict | None = None


def grade_task(task: Task, deliverable, ctx: GradingContext) -> list[CriterionResult]:
    # Imported here to avoid import cycles.
    from . import computed, invariant, llm_judge, structural
    dispatch = {
        "computed": computed.grade,
        "structural": structural.grade,
        "llm_judge": llm_judge.grade,
        "invariant": invariant.grade,
    }
    results = []
    for criterion in task.criteria:
        grader = dispatch[criterion.method]
        try:
            results.append(grader(task, criterion, deliverable, ctx))
        except Exception as e:  # a grader crash is a conservative fail, not a harness crash
            results.append(CriterionResult(
                criterion_id=criterion.id, tier=criterion.tier, method=criterion.method,
                text=criterion.text, passed=False, detail=f"grader error (conservative fail): {e}"))
    return results
