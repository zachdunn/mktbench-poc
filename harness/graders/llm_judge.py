"""LLM-judge grader: binary per-criterion judgment with a fixed template.

One criterion per call; never holistic. Every call is logged verbatim (prompt + response)
— the transcript is the pilot's calibration dataset. Offline mode evaluates the
criterion's declared `offline_check` keyword rules instead (deterministic; used by the
replay acceptance tests so grading the graders burns no tokens).

offline_check params:
  must_mention:      [[synonym, synonym], ...]  — every group must match somewhere
  must_not_mention:  [term, ...]                — fails if a term appears in a sentence
                                                  without a negation cue
  part:              restrict scan to one deliverable part
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .. import config, llm_client
from ..taskspec import Criterion, Task
from .base import CriterionResult, GradingContext

# The judge prompt lives in a template file so it can be versioned and diffed independently
# of grader code (harvey-labs' evaluation/prompts/ convention). Placeholders: {criterion},
# {evidence}, {deliverable}.
_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "prompts" / "rubric_criterion.txt"
JUDGE_TEMPLATE = _TEMPLATE_PATH.read_text()

_NEGATION = re.compile(
    r"\b(not|n't|no|never|neither|without|rather than|instead of|rule[sd]? out|"
    r"unrelated|irrelevant|isn't|wasn't|doesn't|didn't|dismiss\w*|reject\w*|exonerat\w*)\b",
    re.IGNORECASE)


def _deliverable_text(deliverable, part: str | None = None) -> str:
    if part:
        return deliverable.parts.get(part, "")
    return "\n\n".join(f"--- {n} ---\n{c}" for n, c in sorted(deliverable.parts.items()))


# A lone newline mid-paragraph is a soft wrap, not a sentence boundary — a negation cue
# must still count when the wrapped line carries the flagged term.
_SOFT_WRAP = re.compile(r"(?<![.!?:\n])\n(?![\n\-*#\d])")


def _sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?:])\s+|\n+", _SOFT_WRAP.sub(" ", text))


def offline_evaluate(check: dict, text: str) -> tuple[bool, str]:
    low = text.lower()
    for group in check.get("must_mention", []):
        if not any(term.lower() in low for term in group):
            return False, f"none of {group} mentioned"
    for term in check.get("must_not_mention", []):
        for sent in _sentences(text):
            if term.lower() in sent.lower() and not _NEGATION.search(sent):
                return False, f"mentions {term!r} without negation: {sent.strip()[:120]!r}"
    for a, b in check.get("forbid_together", []):
        for sent in _sentences(text):
            s = sent.lower()
            if a.lower() in s and b.lower() in s and not _NEGATION.search(sent):
                return False, f"{a!r} and {b!r} appear together: {sent.strip()[:120]!r}"
    return True, "offline keyword rules satisfied"


def _load_evidence(ctx: GradingContext, files: list[str], budget_chars: int = 120000) -> str:
    chunks = []
    per_file = max(budget_chars // max(len(files), 1), 4000)
    for rel in files:
        path = ctx.universe.root / rel
        try:
            content = path.read_text()
        except Exception as e:
            content = f"[unreadable: {e}]"
        if len(content) > per_file:
            # Head+tail, never head-only: time-series CSVs carry the planted signal at the
            # END of the file, and a head-only excerpt misleads the judge about what exists.
            half = per_file // 2
            content = (content[:half]
                       + f"\n… [{len(content) - per_file} chars elided — file continues] …\n"
                       + content[-half:])
        chunks.append(f"=== {rel} ===\n{content}")
    return "\n\n".join(chunks) if chunks else "(no evidence files linked)"


def grade(task: Task, criterion: Criterion, deliverable, ctx: GradingContext) -> CriterionResult:
    part = criterion.params.get("part")
    text = _deliverable_text(deliverable, part)
    if not text.strip():
        return CriterionResult(criterion.id, criterion.tier, "llm_judge", criterion.text,
                               passed=False, detail="deliverable part empty; conservative fail")
    if ctx.offline:
        check = criterion.params.get("offline_check")
        if not check:
            return CriterionResult(criterion.id, criterion.tier, "llm_judge", criterion.text,
                                   passed=False, detail="offline mode and no offline_check declared; conservative fail")
        passed, detail = offline_evaluate(check, text)
        return CriterionResult(criterion.id, criterion.tier, "llm_judge", criterion.text,
                               passed=passed, detail=f"[offline] {detail}")

    prompt = JUDGE_TEMPLATE.format(
        criterion=criterion.text,
        evidence=_load_evidence(ctx, criterion.evidence_files),
        deliverable=text[:40000],
    )
    resp = llm_client.messages(config.judge_model(), config.JUDGE_MAX_TOKENS, None,
                               [{"role": "user", "content": prompt}])
    out = llm_client.text_of(resp)
    transcript = {"kind": "judge", "criterion_id": criterion.id, "model": config.judge_model(),
                  "prompt": prompt, "response": out}
    ctx.judge_transcripts.append(transcript)
    m = re.search(r"\{.*\}", out, re.DOTALL)
    if not m:
        return CriterionResult(criterion.id, criterion.tier, "llm_judge", criterion.text,
                               passed=False, detail="judge returned no JSON; conservative fail",
                               judge_transcript=transcript)
    try:
        verdict = json.loads(m.group(0))
    except json.JSONDecodeError:
        return CriterionResult(criterion.id, criterion.tier, "llm_judge", criterion.text,
                               passed=False, detail="judge JSON unparsable; conservative fail",
                               judge_transcript=transcript)
    return CriterionResult(
        criterion.id, criterion.tier, "llm_judge", criterion.text,
        passed=bool(verdict.get("pass") is True),
        detail=str(verdict.get("rationale", ""))[:500],
        evidence_quote=str(verdict.get("quote_of_evidence", ""))[:300],
        judge_transcript=transcript)
