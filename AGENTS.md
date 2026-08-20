# AGENTS.md — operating guide for coding agents

MarketingBench is a benchmark harness for evaluating AI agents on lifecycle-marketing work.
Two halves: a **task dataset** (`tasks/`, `canned/`, `universes/`) and an **execution harness**
(`harness/`, `run_eval.py`). Python 3.11+, stdlib only — no pip installs, no new dependencies.

## Commands

```bash
python3 run_eval.py --dry-run                          # every task loads, rubrics resolve, canned parts parse
python3 run_eval.py --all-replay                       # replay matrix: good passes gates, bad fails its plant
python3 -m unittest discover -s tests                  # offline unit tests
python3 run_eval.py --task <ID> --agent replay:good    # grade one canned variant (also replay:bad, replay:edge)
python3 run_eval.py --universe meridian-travel-goods --dry-run   # non-default universe (flag applies to any mode)
python3 run_eval.py --universe all --dry-run           # sweep every universe (--dry-run / --all-replay only)
```

All three validation commands must be green before any work is considered done. Everything is
offline and token-free by design — never add a step that needs an API key to validate.

## Layout

```
tasks/<universe>/<category>/<ID>-<slug>.json   task specs (categories: account-audit · flow-design · escalation)
canned/<universe>/<ID>/{good,bad,edge}/        replay deliverables — every file becomes a deliverable part
universes/<universe>/                          closed brand environment (+ grader-only answer_key/)
universes/gen/                                 deterministic generators — regenerate, never hand-edit output
harness/graders/                               computed.py · structural.py · llm_judge.py · invariant.py
harness/prompts/                               versioned judge-prompt templates
docs/phase1-task-spec.md                       worked task archetypes and rubric intent — the source of truth for task design
```

The harness resolves tasks by the `id` field inside the JSON, not the filename; folders and
slugs are for humans. Universes: `alma-botanica` (default), `meridian-travel-goods`.

## Task JSON anatomy

Copy `tasks/alma-botanica/flow-design/F1-cart-flow-consolidation.json` as the starting shape.

- Top level: `id`, `universe`, `title`, `instructions` (verbatim, realistically underspecified),
  `files_in_scope` (universe-relative paths), `deliverable` (`kind` + `parts` keyed by filename),
  `criteria`, and `invariant_scope` (flow IDs in the task's remit — required if flows change).
- Each criterion: `id` (prefix with the lowercase task id, e.g. `a2_root_cause`), `tier`
  (`gate` = binary, all-pass ⇒ shippable; `quality` = scored only on shippable work), `method`,
  `text`, `evidence_files`, `params`.
- Methods, in order of preference:
  - `computed` — extract a number from the deliverable via `params.extract.regexes`, compare to
    an answer-key value: `params.key` (must exist in `universes/<u>/answer_key/computed_values.json`)
    with `params.tolerance_pct`.
  - `structural` — `params.predicate` naming a function registered in
    `harness/graders/structural.py` `PREDICATES`. Add new predicates there; reuse existing ones
    where they fit.
  - `llm_judge` — genuinely textual judgments only; never holistic scores. **Every `llm_judge`
    criterion requires `params.offline_check`** (`must_mention` / `must_not_mention` keyword
    groups) so replay stays deterministic and token-free.
  - `invariant` — one per flow-touching task; empty `params`, graded against account invariants
    and the simulated-send ledger.

## Rubric rules

- One testable assertion per criterion — split compound requirements.
- Grade failure modes, not ideal answers: name what FAILS, don't describe the ideal.
- `evidence_files` must list the universe files that decide the criterion — never `answer_key/`
  or `gen/` paths (dry-run rejects them).
- No weights; tiers are the only stratification. When in doubt, grade conservatively.
- Distractor-rejection gates (must NOT blame X) are as valuable as detection gates.

## Canned deliverables

`good/` passes every gate. `bad/` fails **exactly one** planted gate — a bad variant failing
three gates at once proves less than one clean miss. `edge/` exercises a boundary case
(near-tolerance number, partial escalation, etc.). Write them as a competent (or specifically
flawed) marketer would — realistic memos and flow JSON, not test stubs.

## Ground rules

- **Synthetic everything.** Never real people, brands, or data.
- **Ground truth comes from the generator.** Plant issues by editing `universes/gen/` and
  regenerating — never hand-edit universe data or `answer_key/`.
- **Don't leak the key.** Tasks, instructions, and canned deliverables must never quote
  `answer_key/` contents beyond what a criterion's tolerance implies.
- Deterministic everywhere: seed everything, sort listings.
- Match existing code style; comment density in `harness/` is low — keep it that way.

More detail: [CONTRIBUTING.md](CONTRIBUTING.md), [docs/architecture.md](docs/architecture.md),
[docs/grading.md](docs/grading.md).
