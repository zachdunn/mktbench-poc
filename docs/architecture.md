# Architecture

One run = sandbox → adapter → graders → score → report.

```
run_eval.py               CLI
harness/
  config.py               provider/model/API config, sim params, seeds — one place
  taskspec.py             task JSON loader (id, instructions, files_in_scope, rubric)
  sandbox.py              per-run copy of the universe minus answer_key/ + gen/; logged reads
  universe.py             grader-side loaders (graders may read answer_key; agents may not)
  segment_engine.py       executes segment-definition JSON against profiles_sample.csv
  endstate.py             merges submitted flow JSON over flows.json
  ledger.py               deterministic 14-day flows-only send simulation → harm events
  llm_client.py           Anthropic / OpenRouter backends behind one call shape
  graders/                computed · structural (predicate registry) · llm_judge · invariant
  adapters/               replay (canned deliverables) · llm (read_file/submit tool loop)
  scoring.py              gates → shippable; quality conditional; escalation pair metrics
  report_html.py          self-contained report
tasks/<universe>/<category>/  task files by taxonomy: account-audit · flow-design · escalation
canned/alma-botanica/     3 canned deliverables per task (good / bad / edge)
universes/                the closed brand environments + their generators and answer keys
tests/                    acceptance + unit tests (stdlib unittest, no deps)
```

Run and grade are separable phases: `execute_task` persists `deliverable.json` +
`access_log.json` (+ `agent_transcript.json` for the LLM adapter), and `grade_run` grades a
saved run dir into `report.json`/`report.html`. `python3 run_eval.py --regrade runs/<run-id>`
re-grades without re-running the agent — the seam for judge-prompt iteration and future
dual-judge passes. Note: regrading overwrites the run's reports in place.

## The four grader types

- **computed** — extract the claimed value from the deliverable (LLM extraction live, declared
  regexes offline), compare against `answer_key/computed_values.json` in code, within tolerance.
- **structural** — schema-lite validation plus named predicates executed as code; segment logic
  runs against the 500-profile sample, so audience properties are checked, not eyeballed.
- **llm_judge** — binary per-criterion judgment with a fixed template (criterion + linked
  evidence files + deliverable) → `{pass, quote_of_evidence, rationale}`. Never holistic.
- **invariant** — materialize the agent's proposed end-state, run the account invariant suite
  (spec §9.1) and ledger-lite (§9.2), gate on violations attributable to the agent's work.

## Adding a task

1. Drop `tasks/<universe>/<category>/<ID>-<slug>.json` — see
   `tasks/alma-botanica/flow-design/F1-cart-flow-consolidation.json` for the shape. Categories
   mirror the spec's taxonomy (`account-audit`, `flow-design`, `escalation`); the harness
   resolves tasks by their `id` field, so folder and slug are for humans.
2. Add canned deliverables under `canned/<universe>/<ID>/{good,bad,edge}/` (every file in the
   variant directory becomes a deliverable part named by its filename).
3. If the task grades flow changes, list the flows in its remit in `invariant_scope`.
4. New structural checks are named predicates registered in `harness/graders/structural.py`.
5. Give every `llm_judge` criterion an `offline_check` so the replay matrix stays token-free.

Multi-universe structure exists (`tasks/<universe>/`, `--universe`) but only alma-botanica is
populated — per the handoff's non-goals.
