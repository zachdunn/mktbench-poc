"""Replay adapter: submits a canned deliverable from canned/<universe>/<task>/<variant>/.

Every file in the variant directory becomes a deliverable part named by its filename.
This is how the graders get tested without burning tokens, and how human-baseline
submissions will run later.
"""
from __future__ import annotations

from pathlib import Path

from .. import config
from ..sandbox import Sandbox
from ..taskspec import Task
from .base import Deliverable


class ReplayAdapter:
    def __init__(self, variant: str, canned_root: Path | None = None):
        self.variant = variant
        self.canned_root = canned_root or config.CANNED_ROOT
        self.name = f"replay:{variant}"

    def run(self, sandbox: Sandbox, task: Task) -> Deliverable:
        d = self.canned_root / task.universe / task.id / self.variant
        if not d.is_dir():
            raise FileNotFoundError(f"no canned deliverable at {d}")
        parts = {}
        for f in sorted(d.iterdir()):
            if f.is_file():
                parts[f.name] = f.read_text()
        # A replay agent "reads" its in-scope files so the access log is populated.
        for rel in task.files_in_scope:
            try:
                sandbox.read_file(rel)
            except (FileNotFoundError, PermissionError):
                pass
        return Deliverable(parts=parts, meta={"adapter": self.name})
