"""Agent adapter interface: run(sandbox, task) -> Deliverable."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..sandbox import Sandbox
from ..taskspec import Task


@dataclass
class Deliverable:
    """Named parts, e.g. {"memo": "...", "flow.json": "...", "email_copy": "..."}."""
    parts: dict[str, str] = field(default_factory=dict)
    meta: dict = field(default_factory=dict)


class AgentAdapter(Protocol):
    name: str

    def run(self, sandbox: Sandbox, task: Task) -> Deliverable: ...
