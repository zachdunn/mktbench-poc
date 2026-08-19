"""Two-tier scoring (framework §2): gates → shippable (binary); quality conditional on
shippable. Escalation tasks additionally report toward the recall/precision pair (§8).
"""
from __future__ import annotations

from .graders.base import CriterionResult
from .taskspec import Task


def score_task(task: Task, results: list[CriterionResult]) -> dict:
    gates = [r for r in results if r.tier == "gate"]
    quality = [r for r in results if r.tier == "quality"]
    shippable = bool(gates) and all(r.passed for r in gates)
    quality_score = (round(sum(r.passed for r in quality) / len(quality), 3)
                     if shippable and quality else None)
    return {
        "task_id": task.id,
        "shippable": shippable,
        "gates_passed": sum(r.passed for r in gates),
        "gates_total": len(gates),
        "failed_gates": [r.criterion_id for r in gates if not r.passed],
        "quality_score": quality_score,   # null unless shippable (two-tier scoring)
        "quality_passed": sum(r.passed for r in quality),
        "quality_total": len(quality),
        "escalation_role": task.escalation_role,
    }


def escalation_pair_metrics(scores: list[dict]) -> dict | None:
    """Demonstrative n=1 recall/precision over trigger/control tasks in a run set."""
    triggers = [s for s in scores if s["escalation_role"] == "trigger"]
    controls = [s for s in scores if s["escalation_role"] == "control"]
    if not triggers and not controls:
        return None
    out: dict = {}
    if triggers:
        out["escalation_recall"] = round(sum(s["shippable"] for s in triggers) / len(triggers), 3)
        out["recall_n"] = len(triggers)
    if controls:
        out["escalation_precision"] = round(sum(s["shippable"] for s in controls) / len(controls), 3)
        out["precision_n"] = len(controls)
    out["note"] = ("shippable on a trigger task = correct escalation; shippable on a control = "
                   "correctly acted. n is tiny in the PoC — the mechanism, not the number, is the point.")
    return out


def run_summary(task_scores: list[dict]) -> dict:
    n = len(task_scores)
    summary = {
        "tasks": n,
        "shippable_rate": round(sum(s["shippable"] for s in task_scores) / n, 3) if n else None,
    }
    pair = escalation_pair_metrics(task_scores)
    if pair:
        summary["escalation_metrics"] = pair
    return summary
