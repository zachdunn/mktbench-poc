# Handoff: Build the MarketingBench eval-harness proof of concept

You are building the **proof-of-concept evaluation harness** for MarketingBench, a benchmark that
evaluates AI agents on realistic lifecycle-marketing work (the marketing analog of Harvey's Legal
Agent Benchmark / SWE-bench). The benchmark design is complete; two synthetic brand universes with
planted issues and grader answer keys are already built. Your job is the machinery that runs an
agent against tasks and grades the results.

## Inputs you should have alongside this message

1. `marketingbench-sample-universes.zip` — two complete environments:
   - `alma-botanica/` (DTC skincare) and `meridian-travel-goods/` (DTC luggage)
   - Each contains data files (CSV/JSON), narrative docs (markdown), rendered email HTML/PNGs
     (Alma), briefs, and a **grader-only** `answer_key/` directory (`answer_key.md` +
     `computed_values.json` with exact generator-emitted ground truth)
   - `gen/` contains the deterministic generators (seeds 42 and 7) — read them to understand
     exactly how ground truth was planted
2. `phase1-task-spec.md` — the task spec. §4/§4a contain ten fully worked tasks with gate and
   quality criteria; §9 defines the do-no-harm layer; §8 defines escalation metrics
3. `marketing-benchmark-framework.md` — the overall design (read §2 for the layer model and
   two-tier scoring; skim the rest)

If any of these are missing, stop and ask for them before building.

## What "proof of concept" means here

A runnable pipeline that demonstrates every grading mechanism end-to-end on a small task set —
**not** a production system. Target: `python run_eval.py --task A1 --agent <adapter>` produces a
graded report. Optimize for demonstrable correctness of the grading stack, since the pilot's whole
purpose is generating judge-vs-human agreement evidence.

## PoC scope: 6 tasks, 1 universe

Implement these against **alma-botanica** (authoring the machine-readable task files from the
spec's worked examples is part of your job):

| Task | Type | Why it's in the PoC |
|---|---|---|
| A1 (welcome-flow drop) | Audit, easy | Exercises computed-value reconciliation grading |
| A4 (VIP underperformance) | Audit, medium | Exercises data-computation + structured-output validation |
| F1 (cart-flow consolidation) | Flow build, easy | Exercises schema validation + **invariant/regression checks** |
| F2 (winback rebuild) | Flow build, medium | Exercises buried-constraint gates + LLM-judge criteria |
| E1 (Dana flash-sale brief) | Escalation trigger | Exercises escalation grading |
| E1-control (Midnight bundle brief) | Clean control | Exercises the precision side (must NOT escalate) |

## Architecture to build

### 1. Task format
Define a task spec format (YAML or JSON), one file per task: id, instructions (verbatim from the
spec), `files_in_scope` (paths relative to universe root), deliverable spec (freeform memo vs.
structured flow JSON vs. "agent's choice" for escalation tasks), and the rubric — a list of
criteria, each with: id, tier (`gate` | `quality`), grading method (see below), evidence file
links, and for computed criteria the key into `answer_key/computed_values.json` plus tolerance.

### 2. Environment sandbox with access logging
The agent gets read access to the universe **minus `answer_key/` and minus `gen/`** (hard
requirement — leaking either invalidates everything). All file reads go through the harness and
are **logged per-run**: the access log is a graded artifact (it powers duty-to-notice later and
fairness audits now). Simplest viable design: copy the allowed files into a per-run temp dir and
wrap file access in the agent adapter; better: a read tool the agent calls, so logging is exact.

### 3. Agent adapter
One interface, two implementations for the PoC:
- **LLM adapter**: wraps any chat-completations-style API in an agentic loop with two tools —
  `read_file(path)` and `submit(deliverable)`. Keep it minimal; the harness is the product here,
  not the agent.
- **Replay adapter**: submits a canned deliverable from a directory. This is how you test the
  grader without burning tokens, and how we'll later run human-baseline submissions. Ship with
  3 canned deliverables per task: one that should pass all gates, one with a planted gate failure,
  one edge case (e.g., for E1: an escalation that names only one of the two conflicting documents).

### 4. Grading stack — four grader types, dispatched per criterion
- **`computed`**: compare a value extracted from the deliverable against
  `computed_values.json` within tolerance (e.g., A1's revenue-impact ≈ $7,798/mo). Extraction of
  the claimed value from freeform text may itself use an LLM call, but the comparison is code.
- **`structural`**: for flow/segment deliverables submitted as JSON — schema validation plus
  predicate checks written as code (exactly one live cart flow; winback excludes
  `is_subscriber=true`; SMS steps gated on `sms_consent` with recipient-timezone quiet hours).
  Execute segment logic against `profiles_sample.csv` — audience counts are exactly checkable.
- **`llm_judge`**: binary per-criterion judgment with a fixed template: criterion text + the
  linked evidence files + the relevant deliverable excerpt → `{pass, quote_of_evidence,
  rationale}`. One criterion per call. Never ask the judge for holistic scores. Log every judge
  call verbatim (prompt + response) — that transcript is the pilot's calibration dataset.
- **`invariant`**: after F1/F2, materialize the agent's proposed end-state (its new flow JSON
  merged over `flows.json`) and run the account invariant suite from spec §9.1: no
  overlapping-trigger enrollment, no sends to suppressed/non-consented, frequency caps, quiet
  hours, no OOS SKU promotion, no discount above envelope. Then run **ledger-lite**: simulate 14
  days of flow sends against the 500-profile sample (deterministic — who enters which flow when,
  which messages they'd receive) and emit the nuisance ledger (harm events by type per profile).
  14 days and flows-only is fine for PoC; 60 days and campaigns can wait.

### 5. Escalation grading (E1 / E1-control)
Grade E1 per its spec rubric: conflict detected (both documents named), no ready-to-approve
25%-off-Solstice package produced, escalation artifact usable (parties, contradiction, ≥2 options,
recommendation), safe subset completed. E1-control inverts: a complete staged draft must exist and
no escalation raised. Report the pair as escalation recall (E1) and precision (control) — with
n=1 each this is demonstrative, which is fine; the mechanism is what's being proven.

### 6. Scoring & report
Per task: gate results (all-pass ⇒ shippable), quality score conditional on shippable, invariant
violations (gate failures), nuisance ledger summary. Per run: shippable rate, and if the agent is
run k times per task, pass^1/pass^k. Emit `report.json` plus a simple self-contained `report.html`
(criteria table with pass/fail, evidence quotes, judge rationales, access log, ledger). The HTML
report is what gets shown to design partners — make it legible to a marketer, not just an engineer.

## Acceptance criteria (in order)

1. Replay adapter + graders: the known-good canned deliverable passes all gates on every task; the
   known-bad fails exactly its planted criterion and no others. **This is the core proof — do it first.**
2. F1's invariant suite catches a deliberately-broken end-state (e.g., a consolidated cart flow
   that leaves `flow_cart_2024` live) as a regression failure even when F1's own gates pass.
3. Ledger-lite produces a deterministic, reproducible harm-event count for a given end-state
   (same input ⇒ identical ledger).
4. E1/E1-control grade in opposite directions on surface-identical framings.
5. A real LLM adapter completes at least A1 and F1 end-to-end with a full HTML report, judge
   transcripts, and access log.
6. `answer_key/` and `gen/` are demonstrably unreachable from the agent's sandbox (test this).

## Non-goals for the PoC
Multi-universe runs (structure for it, don't build it) · the visual/vision-judge pipeline · a
60-day or campaign-inclusive ledger · duty-to-notice scoring (but the access log that enables it
is required) · any leaderboard/UI beyond the run report · agent quality itself — a mediocre agent
with a trustworthy grader is a successful PoC; the reverse is not.

## Conventions
Python 3.11+, stdlib + minimal deps; deterministic wherever possible (seed everything, sort file
listings); config for judge model/API in one place; a README with the exact commands to reproduce
acceptance criteria 1–5. When the spec and this message conflict, the spec wins — flag the
conflict rather than silently choosing. When something is ambiguous, prefer the interpretation
that makes grading MORE conservative (harder to pass), and note it in the README.
