"""Computed grader: extract the claimed value from the deliverable, compare against
answer_key/computed_values.json within tolerance. Extraction may use an LLM in live
mode, but the comparison is always code.
"""
from __future__ import annotations

import json
import re

from .. import config, llm_client
from ..taskspec import Criterion, Task
from .base import CriterionResult, GradingContext


def _deliverable_text(deliverable) -> str:
    return "\n\n".join(f"--- {name} ---\n{content}" for name, content in sorted(deliverable.parts.items()))


def extract_value(text: str, extract: dict, ctx: GradingContext, criterion_text: str) -> tuple[float | None, str]:
    # Live mode uses the LLM to extract the claimed value (freeform memos routinely mention
    # several numbers — baselines, deltas — and a regex can't tell which one is the claim).
    # Offline mode falls back to the criterion's declared regexes, which the canned
    # deliverables are written against. The comparison below is code either way.
    if ctx.offline:
        for pattern in extract.get("regexes", []):
            m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if m:
                raw = m.group(1).replace(",", "").replace("$", "").strip()
                try:
                    return float(raw), f"regex {pattern!r} → {m.group(0)!r}"
                except ValueError:
                    continue
    if not ctx.offline:
        prompt = (
            "Extract the numeric value the deliverable below claims for this criterion. "
            f"Criterion: {criterion_text}\nHint: {extract.get('hint', '')}\n"
            "Reply with ONLY a JSON object: {\"value\": <number>} or {\"value\": null} if no value is claimed.\n\n"
            f"DELIVERABLE:\n{text[:20000]}"
        )
        resp = llm_client.messages(config.judge_model(), 256, None, [{"role": "user", "content": prompt}])
        out = llm_client.text_of(resp)
        ctx.judge_transcripts.append({"kind": "extraction", "criterion": criterion_text,
                                     "prompt": prompt, "response": out})
        m = re.search(r'"value"\s*:\s*(-?[\d.]+)', out)
        if m:
            return float(m.group(1)), "llm extraction"
        return None, "llm extraction found no value"
    return None, "no regex matched (offline mode)"


def grade(task: Task, criterion: Criterion, deliverable, ctx: GradingContext) -> CriterionResult:
    p = criterion.params
    expected = ctx.universe.answer_key()[p["key"]]
    text = _deliverable_text(deliverable)
    value, how = extract_value(text, p.get("extract", {}), ctx, criterion.text)
    if value is None:
        return CriterionResult(criterion.id, criterion.tier, "computed", criterion.text,
                               passed=False, detail=f"no claimed value found ({how}); conservative fail")
    if "tolerance_pct" in p:
        tol = abs(expected) * p["tolerance_pct"] / 100.0
    else:
        tol = p["tolerance_abs"]
    passed = abs(value - expected) <= tol
    return CriterionResult(
        criterion.id, criterion.tier, "computed", criterion.text, passed=passed,
        detail=f"claimed {value} vs expected {expected} (tolerance ±{round(tol, 3)}; via {how})",
        evidence_quote=f"answer_key[{p['key']}] = {expected}")
