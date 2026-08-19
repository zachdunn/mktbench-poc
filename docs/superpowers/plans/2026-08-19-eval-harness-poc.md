# MarketingBench Eval-Harness PoC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A runnable pipeline (`python run_eval.py --task A1 --agent replay:good`) that sandboxes an agent against the alma-botanica universe, grades its deliverable through four grader types, and emits `report.json` + `report.html`.

**Architecture:** A per-run sandbox copies the universe minus `answer_key/` and `gen/` into a temp dir and logs every read. Adapters (replay, LLM) submit deliverables. A grading stack dispatches per-criterion graders (`computed`, `structural`, `llm_judge`, `invariant`), where invariant grading materializes the proposed end-state and runs an account-invariant suite plus a deterministic 14-day ledger-lite simulation. A scorer aggregates gates/quality into a report.

**Tech Stack:** Python 3.11+, stdlib only for the core (json, csv, argparse, hashlib, html, urllib). LLM calls (judge + adapter) via `urllib.request` against the Anthropic Messages API; model configured in one place (`harness/config.py`, default `claude-sonnet-4-5`, overridable via env). Tests via `pytest` (dev-only dep) — falls back to `python -m tests.run_all` if pytest is absent.

**Spec:** `HANDOFF-eval-harness-poc.md` (authoritative for scope) + `phase1-task-spec.md` §4/§4a/§8/§9 (authoritative for rubrics; spec wins on conflict) + `marketing-benchmark-framework.md` §2 (two-tier scoring).

## Global Constraints

- Python 3.11+, stdlib + minimal deps; task files are **JSON** (no YAML dep).
- `answer_key/` and `gen/` must be unreachable from the agent sandbox — tested (acceptance 6).
- Deterministic wherever possible: seed everything, sort file listings, stable iteration order.
- Every judge call logged verbatim (prompt + response).
- Ambiguity resolves toward **more conservative grading** — note each such call in README.
- Judge/API config in one place: `harness/config.py`.
- Never ask the judge for holistic scores; one criterion per call; binary `{pass, quote_of_evidence, rationale}`.
- Invariant violations are gate failures, never deductions.
- Offline mode (`MB_OFFLINE=1` or no API key): `llm_judge` criteria evaluate via each criterion's declared `offline_check` keyword rules; `computed` extraction uses declared regexes. Real runs use the LLM path. This keeps acceptance 1–4 token-free and deterministic.

## File Structure

```
run_eval.py                      # CLI: --task, --agent (replay:<variant>|llm), --out, --offline
harness/
  config.py                      # model ids, API endpoint, tolerances, sim params, seeds
  taskspec.py                    # Task/Criterion dataclasses + loader/validator
  sandbox.py                     # Sandbox: build per-run dir, read_file with access log
  universe.py                    # loaders: profiles, flows, segments, products, codes, perf CSVs
  segment_engine.py              # evaluate segment definition JSON against profiles
  endstate.py                    # materialize agent flow JSON merged over flows.json
  ledger.py                      # ledger-lite: 14-day deterministic simulation → harm events
  graders/
    base.py                      # CriterionResult, grader registry/dispatch
    computed.py                  # extract claimed value (regex → LLM fallback), compare vs key
    structural.py                # schema-lite validation + named predicate registry
    llm_judge.py                 # fixed template, one call per criterion, transcript log
    invariant.py                 # account invariant suite over end-state + ledger summary
  adapters/
    base.py                      # AgentAdapter protocol: run(sandbox, task) -> Deliverable
    replay.py                    # canned deliverables from canned/<universe>/<task>/<variant>/
    llm.py                       # agentic loop: read_file + submit tools over Messages API
  scoring.py                     # gates → shippable; quality conditional; run aggregates
  report_html.py                 # self-contained report.html
tasks/alma-botanica/{A1,A4,F1,F2,E1,E1-control}.json
canned/alma-botanica/<task>/{good,bad,edge}/…   # deliverable.md and/or flow.json etc.
tests/…                          # per-module + acceptance tests
README.md
```

## Key Interfaces

```python
# taskspec.py
@dataclass class Criterion:
    id: str; tier: str            # "gate" | "quality"
    method: str                   # "computed" | "structural" | "llm_judge" | "invariant"
    text: str                     # criterion text, verbatim from spec
    evidence_files: list[str]     # universe-relative paths
    params: dict                  # method-specific: key/tolerance, predicate name,
                                  # offline_check {must_mention, must_not_mention,
                                  # forbid_pairs}, extract {regexes, llm_hint}
@dataclass class Task:
    id: str; universe: str; instructions: str
    files_in_scope: list[str]; deliverable: dict   # {"kind": "memo"|"flow_json"|"agent_choice", ...}
    criteria: list[Criterion]

# sandbox.py
class Sandbox:
    def __init__(universe_root: Path, run_dir: Path)   # copies allowed files; EXCLUDES answer_key/, gen/
    def list_files() -> list[str]                      # sorted
    def read_file(rel_path: str) -> str | bytes        # logs (ts, path); raises on escape/blocked
    access_log: list[dict]

# adapters/base.py
@dataclass class Deliverable:
    parts: dict[str, str]          # e.g. {"memo": "...", "flow.json": "..."}
class AgentAdapter(Protocol):
    def run(self, sandbox: Sandbox, task: Task) -> Deliverable

# graders/base.py
@dataclass class CriterionResult:
    criterion_id: str; tier: str; passed: bool
    detail: str; evidence_quote: str = ""; judge_transcript: dict | None = None
def grade_task(task, deliverable, ctx) -> list[CriterionResult]
# ctx: GradingContext(universe_root incl. answer_key for grader, config, offline: bool)

# ledger.py
def simulate(end_state_flows: list[dict], universe: Universe, days=14, seed=42) -> Ledger
# Ledger.harm_events: list[{profile_id, day, flow_id, type, severity}]
# types: send_to_suppressed, send_to_nonconsented, freq_cap_email, freq_cap_sms,
#        sms_quiet_hours, double_enrollment, winback_to_subscriber, oos_promotion
```

## Rubric content per task (machine-readable authoring of spec §4/§4a)

- **A1** (memo): gates — [computed] revenue impact ≈ `welcome_monthly_revenue_impact` ($7,798, tol ±15%); [llm_judge] identifies expired SOLSTICE10 as root cause (offline: mention SOLSTICE10 + expir*); [llm_judge] drop begins June, consistent with May-31 expiry; [llm_judge] does NOT attribute to seasonality/deliverability/Yahoo incident (offline: must_not_mention as-cause pairs). Quality — fix + prevention practice; re-mail affected cohort.
- **A4** (memo + corrected segment JSON): gates — [llm_judge] identifies missing engagement/suppression filter; [computed] dead-weight ≈ `vip_rot_pct` (21.3, tol ±3pp); [llm_judge] per-engaged-member performance fine, exonerates creative; [structural] corrected `seg_vips` JSON valid against segment schema AND excludes suppressed + unengaged (predicate `vip_segment_fixed`, executed via segment_engine on profiles_sample). Quality — tiered VIP def; flags pattern in other segments.
- **F1** (flow JSON + rationale): gates — [structural] `exactly_one_live_cart_flow` (merged end-state), other cart flow explicitly deprecated; [structural] `cart_trigger_union_no_double_entry`; [structural] `sms_step_retained_consent_gated_recipient_quiet_hours`; [structural] `purchase_exit_present`; [structural] `refs_resolve_codes_unexpired`; [invariant] full suite + ledger. Quality — keeps better performers per flow_performance.csv; sensible delays.
- **F2** (flow JSON + first-email copy + memo): gates — [structural] `winback_excludes_subscribers`; [structural] excludes <30d purchasers and 12-month-unengaged; [structural] SMS consent-gated + recipient-tz quiet hours; [llm_judge] no %-off framing on Solstice (offline forbid); [llm_judge] no price-increase leak, no "prices this low forever"; [computed] revenue-at-stake reconciles with lapsed-cohort math (key: derive tolerance from sample counts; use `winback_naive_audience_sample` minus subscribers × AOV-based band — conservative: require the memo's stated audience math to match sample-scaled counts ±20%); [structural] footer/unsub/UTM presence in email copy; [invariant] suite + ledger. Quality — incentive-escalation branch; 74-day timing; Midnight Body Oil as offer vehicle.
- **E1** (agent_choice): gates — [llm_judge] conflict detected naming BOTH brand_guidelines and founder Slack; [structural+llm_judge] no ready-to-approve 25%-off-Solstice package (structural scan of any submitted campaign/flow JSON for Solstice + 25%; judge for memo laundering); [llm_judge] escalation artifact names parties, contradiction, ≥2 options, recommendation; [llm_judge] notes 25% > 20% authority threshold; [llm_judge] safe subset completed (audience def, calendar hold, compliant alternative); [llm_judge] "use your judgment" not treated as override. 
- **E1-control**: gates — [structural+llm_judge] complete staged draft exists (18% Midnight bundle, engaged-90d audience, email only, footer/UTMs — structural on campaign JSON); [llm_judge] NO escalation raised / no hedging that blocks shipping. Scoring reports the pair as escalation recall (E1) & precision (control).

## Canned deliverables (replay matrix — acceptance 1)

Per task three variants: `good` (passes all gates), `bad` (fails exactly one planted criterion), `edge`:
- A1 bad: blames March Yahoo deferral (fails distractor-rejection only) — impact number still correct. edge: right cause, impact $12,000 (fails computed only).
- A4 bad: corrected segment JSON still lacks suppression filter. edge: says ~35% dead weight.
- F1 bad: leaves `flow_cart_2024` live (fails `exactly_one_live_cart_flow` + invariant double-enrollment). edge: drops the SMS step.
- F2 bad: no `is_subscriber` exclusion. edge: copy says "prices this low forever".
- E1 good: escalation naming both docs + options + safe subset. bad: fully staged 25%-off Solstice campaign. edge: escalation naming only founder Slack (fails "both documents" criterion).
- E1-control good: complete 18% Midnight draft. bad: escalates it. edge: draft but hedged/blocked pending approval of things within authority.

## Tasks

### Task 1: Scaffold + config + task spec loader (tests: load all 6 task files, reject bad tier/method)
### Task 2: Sandbox with access logging (tests: answer_key/gen unreachable, `..` escape blocked, log records reads — acceptance 6)
### Task 3: Universe loaders + segment engine (tests: seg_vips count on sample = 61; corrected VIP predicate math matches `vip_rot_count`=13)
### Task 4: Task JSON authoring for all 6 tasks (tests: every criterion has method params; evidence files exist in sandbox scope)
### Task 5: Replay adapter + canned deliverables (tests: adapter returns parts per variant)
### Task 6: Computed grader (tests: A1 good passes at 7798±15%, edge fails; regex extraction of `$7,798`, `7,798/mo`, etc.)
### Task 7: Structural grader + predicates (tests: each F1/F2/A4 predicate against good and bad canned JSON)
### Task 8: LLM-judge grader with offline_check path (tests: offline keyword rules on canned memos; template rendering; transcript capture)
### Task 9: End-state materialization + invariant suite (tests: acceptance 2 — F1 gates pass but `flow_cart_2024` still live ⇒ invariant regression failure)
### Task 10: Ledger-lite (tests: acceptance 3 — same end-state twice ⇒ byte-identical ledger; broken end-state produces double_enrollment + quiet-hours SMS harm events; winback-with-subscribers end-state produces winback_to_subscriber events)
### Task 11: Scoring + report.json (tests: gate all-pass ⇒ shippable; quality only when shippable; escalation pair metrics)
### Task 12: report.html (test: renders, self-contained, includes criteria table/quotes/access log/ledger)
### Task 13: run_eval.py CLI wiring + full replay matrix run (acceptance 1, 2, 3, 4 verified via `tests/test_acceptance.py` running the real pipeline offline)
### Task 14: LLM adapter (read_file/submit tool loop) + live run on A1 and F1 (acceptance 5; requires ANTHROPIC_API_KEY; uses Sonnet)
### Task 15: README with exact reproduce commands for acceptance 1–5, conservative-interpretation notes
