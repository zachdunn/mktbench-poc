"""Task spec format: one JSON file per task, loaded into dataclasses and validated."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import config

VALID_TIERS = {"gate", "quality"}
VALID_METHODS = {"computed", "structural", "llm_judge", "invariant"}
VALID_DELIVERABLE_KINDS = {"memo", "flow_json", "agent_choice"}


@dataclass
class Criterion:
    id: str
    tier: str
    method: str
    text: str
    evidence_files: list[str] = field(default_factory=list)
    params: dict = field(default_factory=dict)


@dataclass
class Task:
    id: str
    universe: str
    title: str
    instructions: str
    files_in_scope: list[str]
    deliverable: dict
    criteria: list[Criterion]
    # Flow ids inside the task's remit for invariant gating (see README: pre-existing
    # account violations outside this scope are reported, not gated).
    invariant_scope: list[str] = field(default_factory=list)
    escalation_role: str | None = None  # "trigger" | "control" | None

    def gate_criteria(self) -> list[Criterion]:
        return [c for c in self.criteria if c.tier == "gate"]

    def quality_criteria(self) -> list[Criterion]:
        return [c for c in self.criteria if c.tier == "quality"]


class TaskSpecError(ValueError):
    pass


def load_task(path: Path) -> Task:
    raw = json.loads(path.read_text())
    criteria = []
    seen_ids: set[str] = set()
    for c in raw.get("criteria", []):
        if c.get("tier") not in VALID_TIERS:
            raise TaskSpecError(f"{path.name}: criterion {c.get('id')} has invalid tier {c.get('tier')!r}")
        if c.get("method") not in VALID_METHODS:
            raise TaskSpecError(f"{path.name}: criterion {c.get('id')} has invalid method {c.get('method')!r}")
        if not c.get("id") or c["id"] in seen_ids:
            raise TaskSpecError(f"{path.name}: missing or duplicate criterion id {c.get('id')!r}")
        seen_ids.add(c["id"])
        if c["method"] == "computed":
            p = c.get("params", {})
            if "key" not in p or not ("tolerance_pct" in p or "tolerance_abs" in p):
                raise TaskSpecError(f"{path.name}: computed criterion {c['id']} needs params.key and a tolerance")
        if c["method"] == "structural" and "predicate" not in c.get("params", {}):
            raise TaskSpecError(f"{path.name}: structural criterion {c['id']} needs params.predicate")
        criteria.append(Criterion(
            id=c["id"], tier=c["tier"], method=c["method"], text=c.get("text", ""),
            evidence_files=c.get("evidence_files", []), params=c.get("params", {}),
        ))
    if raw.get("deliverable", {}).get("kind") not in VALID_DELIVERABLE_KINDS:
        raise TaskSpecError(f"{path.name}: invalid deliverable.kind")
    return Task(
        id=raw["id"], universe=raw["universe"], title=raw.get("title", raw["id"]),
        instructions=raw["instructions"], files_in_scope=raw.get("files_in_scope", []),
        deliverable=raw["deliverable"], criteria=criteria,
        invariant_scope=raw.get("invariant_scope", []),
        escalation_role=raw.get("escalation_role"),
    )


def load_task_by_id(task_id: str, universe: str = "alma-botanica") -> Task:
    """Find a task by its `id` field anywhere under tasks/<universe>/ — task files live in
    category folders with descriptive slugs (e.g. flow-design/F1-cart-flow-consolidation.json),
    so resolution goes by content, not filename."""
    root = config.TASKS_ROOT / universe
    for path in sorted(root.rglob("*.json")):
        try:
            if json.loads(path.read_text()).get("id") == task_id:
                return load_task(path)
        except json.JSONDecodeError as e:
            raise TaskSpecError(f"unparsable task file {path}: {e}") from e
    raise TaskSpecError(f"no task with id {task_id!r} under {root}")


def list_task_ids(universe: str = "alma-botanica") -> list[str]:
    root = config.TASKS_ROOT / universe
    return sorted(json.loads(p.read_text()).get("id", "?") for p in root.rglob("*.json"))


def list_tasks(universe: str = "alma-botanica") -> list[tuple[str, str, Path]]:
    """(category, task_id, path) for every task file, sorted by path. Category is the
    folder under tasks/<universe>/ (account-audit, flow-design, escalation, …)."""
    root = config.TASKS_ROOT / universe
    out = []
    for path in sorted(root.rglob("*.json")):
        category = path.parent.name if path.parent != root else ""
        out.append((category, json.loads(path.read_text()).get("id", "?"), path))
    return out


def resolve_task_selector(selector: str, universe: str = "alma-botanica") -> list[str]:
    """Resolve a --task argument to task ids: an exact id, a category folder name, or 'all'."""
    tasks = list_tasks(universe)
    if selector == "all":
        return [tid for _, tid, _ in tasks]
    by_category = [tid for cat, tid, _ in tasks if cat == selector]
    if by_category:
        return by_category
    if any(tid == selector for _, tid, _ in tasks):
        return [selector]
    known = sorted({cat for cat, _, _ in tasks if cat})
    raise TaskSpecError(f"no task id or category {selector!r}; categories: {', '.join(known)}")
