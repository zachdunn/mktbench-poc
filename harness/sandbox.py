"""Per-run agent sandbox: the universe minus answer_key/ and gen/, with logged reads.

Hard requirement from the handoff: `answer_key/` and `gen/` must be unreachable from the
agent's sandbox. We enforce this three ways: (1) blocked dirs are never copied into the
run dir, (2) path resolution rejects any escape from the run dir, (3) blocked names are
rejected by name even if a path were to slip through.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

BLOCKED_DIRS = {"answer_key", "gen"}


class SandboxAccessError(PermissionError):
    pass


class Sandbox:
    def __init__(self, universe_root: Path, run_dir: Path):
        self.universe_root = Path(universe_root)
        self.root = Path(run_dir) / "sandbox"
        self.access_log: list[dict] = []
        self._build()

    def _build(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for src in sorted(self.universe_root.rglob("*")):
            rel = src.relative_to(self.universe_root)
            if any(part in BLOCKED_DIRS for part in rel.parts):
                continue
            dst = self.root / rel
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    def list_files(self) -> list[str]:
        return sorted(
            str(p.relative_to(self.root))
            for p in self.root.rglob("*") if p.is_file()
        )

    def _resolve(self, rel_path: str) -> Path:
        if any(part in BLOCKED_DIRS for part in Path(rel_path).parts):
            raise SandboxAccessError(f"access to {rel_path!r} is blocked")
        candidate = (self.root / rel_path).resolve()
        root = self.root.resolve()
        if root not in candidate.parents and candidate != root:
            raise SandboxAccessError(f"path {rel_path!r} escapes the sandbox")
        return candidate

    def read_file(self, rel_path: str) -> str:
        """Read a sandboxed file as text (binary files return a placeholder note)."""
        path = self._resolve(rel_path)
        if not path.exists() or not path.is_file():
            self._log(rel_path, ok=False)
            raise FileNotFoundError(f"no such file in sandbox: {rel_path}")
        self._log(rel_path, ok=True)
        try:
            return path.read_text()
        except UnicodeDecodeError:
            return f"[binary file: {rel_path}, {path.stat().st_size} bytes — content not text-readable]"

    def _log(self, rel_path: str, ok: bool) -> None:
        self.access_log.append({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "path": rel_path,
            "ok": ok,
        })
