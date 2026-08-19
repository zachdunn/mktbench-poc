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
    path = config.TASKS_ROOT / universe / f"{task_id}.json"
    if not path.exists():
        raise TaskSpecError(f"no task file at {path}")
    return load_task(path)
