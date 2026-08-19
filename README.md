# MarketingBench — eval-harness proof of concept

A runnable pipeline that sandboxes an agent against the `alma-botanica` universe, grades its
deliverable through four grader types (`computed`, `structural`, `llm_judge`, `invariant`), and
emits `report.json` + a marketer-legible `report.html`. Built per `HANDOFF-eval-harness-poc.md`;
rubrics authored from `phase1-task-spec.md` §4/§4a/§8/§9; scoring per
`marketing-benchmark-framework.md` §2 (two-tier: gates → shippable, quality conditional on
shippable). Layout mirrors [Harvey LAB](https://github.com/harveyai/harvey-labs)
(`tasks/` + `harness/` + sandbox + all-pass rubric with per-criterion LLM-judge calls).

**PoC scope:** 6 tasks (A1, A4, F1, F2, E1, E1-control), 1 universe, stdlib-only Python 3.11+.

## Quick start

```bash
python3 run_eval.py --task A1 --agent replay:good     # one task, canned deliverable
python3 run_eval.py --all-replay                      # full replay matrix, offline
python3 run_eval.py --task A1 --agent llm             # live agent (needs ANTHROPIC_API_KEY)
```

Each run writes `runs/<run-id>/report.json`, `report.html`, and (for `llm`) `agent_transcript.json`.

## Reproducing the acceptance criteria

**1. Replay adapter + graders** — good passes all gates on every task; bad fails exactly its
planted criterion:

```bash
python3 run_eval.py --all-replay
```

```bash
python3 -m unittest tests.test_acceptance.TestAcceptance1_ReplayMatrix -v
```

Planted bad-variant failures: A1 → `a1_distractors` (blames the Yahoo incident), A4 →
`a4_segment_json` (corrected segment still keeps unengaged profiles), F1 → `f1_exit` (no
purchase exit), F2 → `f2_no_price_leak` (copy leaks the October price increase). The escalation
pair's bad variants are *behaviorally* wrong (staging the forbidden campaign / escalating a clean
brief), so E1-bad fails every escalation gate by design and E1-control-bad fails exactly
`e1c_no_escalation`.

**2. Invariant suite catches a regression F1's own gates miss:**

```bash
python3 -m unittest tests.test_acceptance.TestAcceptance2_InvariantRegression -v
```

A consolidation that leaves `flow_cart_2024` live passes every deliverable-shape gate
(SMS retained, consent, exit, refs) but fails `f1_invariants` with `overlapping_trigger` +
ledger `double_enrollment` — the SWE-bench pass-to-pass transplant working as specced.

**3. Ledger-lite determinism** — same end-state ⇒ byte-identical ledger (sha256 fingerprint):

```bash
python3 -m unittest tests.test_core.TestLedger -v
```

**4. E1 / E1-control grade in opposite directions on surface-identical framings:**

```bash
python3 -m unittest tests.test_acceptance.TestAcceptance4_EscalationPair -v
```

Reported as the escalation recall / precision pair (n=1 each — demonstrative; the mechanism is
what's being proven).

**5. Live LLM adapter end-to-end** (A1 and F1, full HTML report + judge transcripts + access log):

```bash
cp .env.example .env                   # then set ANTHROPIC_API_KEY or OPENROUTER_API_KEY
python3 run_eval.py --task A1 --agent llm
python3 run_eval.py --task F1 --agent llm
```
All judge calls are one-criterion-per-call with a fixed template and are logged verbatim into
`report.json` (`judge_transcripts`) — that transcript is the pilot's calibration dataset.
*Not run in this workspace: no API key was available at build time.*

### Provider configuration

The judge and the LLM adapter run against either the **Anthropic API** or **OpenRouter**
(OpenAI-style chat completions — any model OpenRouter serves). Selection lives in
`harness/config.py`:

| Env var | Effect |
|---|---|
| `MB_PROVIDER` | `anthropic` or `openrouter`; unset → auto-detect from whichever key exists (Anthropic wins if both) |
| `ANTHROPIC_API_KEY` / `OPENROUTER_API_KEY` | credentials per provider |
| `MB_JUDGE_MODEL` / `MB_AGENT_MODEL` | model override; PoC defaults are deliberately small/cheap — `claude-haiku-4-5` (Anthropic) / `deepseek/deepseek-v4-flash` (OpenRouter) |

OpenRouter model ids are namespaced (`anthropic/claude-sonnet-4.5`, `openai/gpt-4.1`, …). The
harness speaks Anthropic's message shape internally; `harness/llm_client.py` translates tools and
tool-call messages at the boundary, so graders and adapters are provider-blind. For
judge-vs-human agreement studies, pin the judge model per experiment — one variable at a time.

**6. answer_key/ and gen/ unreachable from the sandbox** (blocked at copy, at path resolution,
and by name):

```bash
python3 -m unittest tests.test_sandbox -v
```

Full suite: `python3 -m unittest discover -s tests`.

## Architecture

```
run_eval.py               CLI
harness/
  config.py               judge/agent model + API config, sim params, seeds — one place
  taskspec.py             task JSON loader (id, instructions, files_in_scope, rubric)
  sandbox.py              per-run copy of the universe minus answer_key/ + gen/; logged reads
  universe.py             grader-side loaders (graders may read answer_key; agents may not)
  segment_engine.py       executes segment-definition JSON against profiles_sample.csv
  endstate.py             merges submitted flow JSON over flows.json
  ledger.py               deterministic 14-day flows-only send simulation → harm events
  graders/                computed · structural (predicate registry) · llm_judge · invariant
  adapters/               replay (canned deliverables) · llm (read_file/submit tool loop)
  scoring.py              gates → shippable; quality conditional; escalation pair metrics
  report_html.py          self-contained report
tasks/alma-botanica/      6 machine-readable task files authored from the spec's worked examples
canned/alma-botanica/     3 canned deliverables per task (good / bad / edge)
```

Multi-universe structure exists (`tasks/<universe>/`, `--universe`) but only alma-botanica is
populated — per the handoff's non-goals.

## Offline mode

With no `ANTHROPIC_API_KEY` (or with `MB_OFFLINE=1` / `--offline`), `llm_judge` criteria evaluate
their declared `offline_check` keyword rules and `computed` extraction uses declared regexes only.
This keeps grader-testing token-free and deterministic; live runs use the real judge with the same
criteria text. An `llm_judge` criterion with no `offline_check` fails conservatively offline.

## Conservative interpretations & deliberate calls (flagged per the handoff)

- **Invariant gating scope.** The account ships with eight planted issues, so a naive "all
  invariants must hold post-change" fails every task for pre-existing reasons. Rule adopted:
  a violation gates iff it involves a flow in the task's `invariant_scope` ∪ flows the agent
  submitted, **or** it is new relative to the baseline account. Everything else is reported as
  pre-existing context. Frequency-cap breaches gate as per-profile *regressions* vs baseline
  (fatigue is planted issue #8; the agent is charged only for making a profile's count worse).
- **F2's "revenue-at-stake reconciles" gate** is graded on the exactly-checkable half of the math:
  the count of active subscribers wrongly caught by the naive lapsed-90d audience, vs
  `answer_key.winback_subscribers_wrongly_included_sample` (±12 absolute — wide because the
  generator computes 51 over all >90d profiles while the naive-audience definition it also emits
  yields 39; the answer key's stated pairing is honored). The dollar figure itself is a quality
  judge criterion. Spec-vs-key inconsistency flagged rather than silently resolved.
- **Ledger entry model.** Event-triggered flow entries are hash-assigned (seed, profile, event) —
  deterministic, not calibrated. Segment-triggered flows enroll all matching profiles on day 0.
  No purchases are simulated during the horizon (more sends ⇒ more conservative). Caps used:
  5 email / 2 SMS per rolling 7 days (no numeric cap is stated in the universe docs).
  `winback_to_subscriber` harm keys off flow ids containing "winback" — PoC shortcut.
- **Escalation "withholding" line** (spec §8 nuance 1): any structured JSON part staging a 25%-off
  Solstice package fails E1's gate, however the memo frames it — a draft *flagged as blocked* must
  not ship as a ready-to-approve object. Silent unilateral substitution also fails (spec's
  recommended posture).
- **Reference date** for relative-date segment math is 2026-08-12 (the generators' `today`).
- **Grader crashes fail conservatively** — an exception in any grader records a failed criterion,
  never a passed one.
- **A missing claimed value fails a computed criterion** (no benefit of the doubt for memos that
  state no number).

## Adding a task

Drop `tasks/<universe>/<ID>.json` (see `tasks/alma-botanica/F1.json` for the shape), add canned
deliverables under `canned/<universe>/<ID>/{good,bad,edge}/`, and — if it grades flow changes —
list the flows in the task's remit in `invariant_scope`. Structural checks are named predicates in
`harness/graders/structural.py`'s registry.
