# Reproducing the acceptance criteria

The handoff (`HANDOFF-eval-harness-poc.md`) defines six acceptance criteria. Each one is
reproducible with a single command. Full suite: `python3 -m unittest discover -s tests`.

## 1. Replay adapter + graders

Good passes all gates on every task; bad fails exactly its planted criterion:

```bash
python3 run_eval.py --all-replay
```

```bash
python3 -m unittest tests.test_acceptance.TestAcceptance1_ReplayMatrix -v
```

Planted bad-variant failures:

| Task | Failing gate | The plant |
|---|---|---|
| A1 | `a1_distractors` | blames the March Yahoo incident |
| A4 | `a4_segment_json` | corrected segment still keeps unengaged profiles |
| F1 | `f1_exit` | no purchase-exit condition |
| F2 | `f2_no_price_leak` | copy leaks the October price increase |
| E1 | every escalation gate | stages the forbidden campaign (behaviorally wrong by design) |
| E1-control | `e1c_no_escalation` | escalates a clean brief |

## 2. Invariant suite catches what task gates miss

```bash
python3 -m unittest tests.test_acceptance.TestAcceptance2_InvariantRegression -v
```

A consolidation that leaves `flow_cart_2024` live passes every deliverable-shape gate
(SMS retained, consent, exit, refs) but fails `f1_invariants` with `overlapping_trigger` +
ledger `double_enrollment` — the SWE-bench pass-to-pass transplant working as specced.

## 3. Ledger-lite determinism

Same end-state ⇒ byte-identical ledger (sha256 fingerprint):

```bash
python3 -m unittest tests.test_core.TestLedger -v
```

## 4. Escalation pair grades in opposite directions

```bash
python3 -m unittest tests.test_acceptance.TestAcceptance4_EscalationPair -v
```

E1 (trigger) and E1-control (clean twin) have surface-identical framings; correct behavior is
opposite. Reported as the escalation recall / precision pair (n=1 each — demonstrative; the
mechanism is what's being proven).

## 5. Live LLM adapter end-to-end

A1 and F1 with a real agent — full HTML report, judge transcripts, access log:

```bash
cp .env.example .env    # set ANTHROPIC_API_KEY or OPENROUTER_API_KEY
python3 run_eval.py --task A1 --agent llm
python3 run_eval.py --task F1 --agent llm
```

See [grading.md](grading.md) for provider and model configuration. All judge calls are
one-criterion-per-call with a fixed template and are logged verbatim into `report.json`
(`judge_transcripts`) — that transcript is the pilot's calibration dataset.

## 6. answer_key/ and gen/ unreachable from the sandbox

Blocked at copy time, at path resolution, and by name:

```bash
python3 -m unittest tests.test_sandbox -v
```
