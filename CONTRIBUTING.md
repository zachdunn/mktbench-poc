# Contributing

MarketingBench has two halves: the **task dataset** (`tasks/`, `canned/`, `universes/`) and the
**execution harness** (`harness/`, `run_eval.py`). Most contributions are new tasks or rubric
improvements; this guide covers both. Module-level detail lives in
[docs/architecture.md](docs/architecture.md); grading policy in [docs/grading.md](docs/grading.md).

## Repo layout

```
tasks/<universe>/<category>/<ID>-<slug>.json   task specs (account-audit · flow-design · escalation)
canned/<universe>/<ID>/{good,bad,edge}/        replay deliverables for grading the graders
universes/<universe>/                          the closed brand environment (+ grader-only answer_key/)
universes/gen/                                 deterministic generators — regenerate, don't hand-edit
harness/                                       sandbox, adapters, graders, scoring, reports
harness/prompts/                               versioned judge-prompt templates
tests/                                         offline, token-free (stdlib unittest)
```

## Add a task

1. Create `tasks/<universe>/<category>/<ID>-<slug>.json`. Copy
   `tasks/alma-botanica/flow-design/F1-cart-flow-consolidation.json` as a starting shape. The
   harness resolves tasks by the `id` field, not the filename — folder and slug are for humans.
2. Add three canned deliverables under `canned/<universe>/<ID>/`: `good/` passes every gate,
   `bad/` fails exactly one planted gate, `edge/` exercises a boundary case. Every file in a
   variant directory becomes a deliverable part named by its filename.
3. If the task grades flow changes, list the flows in its remit in `invariant_scope`.
4. New structural checks are named predicates registered in `harness/graders/structural.py`.

## Write good rubrics

- **One testable assertion per criterion.** Split compound requirements. Prefer
  *"PASS if the memo identifies the expired SOLSTICE10 code as the root cause; FAIL if the drop
  is attributed to seasonality, deliverability, or the Yahoo incident"* phrasing — name the
  failure modes, don't just describe the ideal.
- **Grade failure modes, not ideal answers.** "Excludes purchasers from the last 30 days" is
  binary; "is this the best winback strategy" is not a criterion.
- **Prefer executable methods.** Use `computed` (answer-key value + tolerance) or `structural`
  (a predicate run against real data) wherever possible; reserve `llm_judge` for genuinely
  textual judgments. Never ask a judge for a holistic score.
- **Link evidence.** Every criterion lists the `evidence_files` that decide it (never
  `answer_key/` or `gen/` — those are grader-only and the dry-run rejects them).
- **Every `llm_judge` criterion needs an `offline_check`** (keyword rules) so the replay matrix
  stays deterministic and token-free.
- **No weights.** Tiers are the only stratification: `gate` (binary, all-pass ⇒ shippable) or
  `quality` (scored only on shippable work). When in doubt, grade conservatively — harder to
  pass — and note the call in [docs/grading.md](docs/grading.md).

## Validate

```bash
python3 run_eval.py --universe all --dry-run       # every task loads, rubric params resolve, canned parts parse
python3 run_eval.py --universe all --all-replay    # good passes, bad fails its planted gate
python3 -m unittest discover -s tests
```

All three must be green before a PR. Tests are offline by design — no API key needed.

## Ground rules

- **Synthetic everything.** People, brands, addresses, and metrics are generator-produced.
  Never add real customer data, real company names, or real personal information.
- **Ground truth comes from the generator.** Plant issues by editing `universes/gen/` and
  regenerating so the answer key stays exact — never hand-edit universe data or
  `answer_key/` directly.
- **Don't leak the key.** Task files, instructions, and canned deliverables must never quote
  `answer_key/` contents beyond what a criterion's tolerance implies.
- **Keep the replay matrix meaningful.** A bad variant that fails three gates at once proves
  less than one that fails exactly its plant.
- Small, focused PRs; deterministic everywhere (seed everything, sort listings).
