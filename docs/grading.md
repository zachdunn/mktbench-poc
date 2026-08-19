# Grading methodology & configuration

Scoring follows the framework's two-tier model (§2): **gate** criteria are binary and all-pass
⇒ *shippable*; **quality** criteria are scored only on shippable work. Invariant violations are
gate failures, never deductions. Escalation tasks report as a recall/precision pair (spec §8).

## Provider configuration

The judge and the LLM adapter run against either the **Anthropic API** or **OpenRouter**
(OpenAI-style chat completions — any model OpenRouter serves). Configuration lives in
`harness/config.py` and is read from the environment or a `.env` file (`.env.example` shows the
shape; shell env vars win; the harness never writes env files).

| Env var | Effect |
|---|---|
| `MB_PROVIDER` | `anthropic` or `openrouter`; unset → auto-detect from whichever key exists (Anthropic wins if both) |
| `ANTHROPIC_API_KEY` / `OPENROUTER_API_KEY` | credentials per provider |
| `MB_JUDGE_MODEL` / `MB_AGENT_MODEL` | model override; PoC defaults are deliberately small/cheap — `claude-haiku-4-5` (Anthropic) / `deepseek/deepseek-v4-flash` (OpenRouter) |
| `MB_OFFLINE` | `1` forces offline grading even with a key set |

OpenRouter model ids are namespaced (`anthropic/claude-sonnet-4.5`, `openai/gpt-4.1`, …). The
harness speaks Anthropic's message shape internally; `harness/llm_client.py` translates tools
and tool-call messages at the boundary, so graders and adapters are provider-blind. For
judge-vs-human agreement studies, pin the judge model per experiment — one variable at a time.

## Offline mode

With no API key (or `--offline` / `MB_OFFLINE=1`), `llm_judge` criteria evaluate their declared
`offline_check` keyword rules and `computed` extraction uses declared regexes only. This keeps
grader-testing token-free and deterministic; live runs use the real judge with the same
criteria text. An `llm_judge` criterion with no `offline_check` fails conservatively offline.

## Conservative interpretations & deliberate calls

Flagged per the handoff's instruction to prefer harder-to-pass readings and note them:

- **Invariant gating scope.** The account ships with eight planted issues, so a naive "all
  invariants must hold post-change" fails every task for pre-existing reasons. Rule adopted:
  a violation gates iff it involves a flow in the task's `invariant_scope` ∪ flows the agent
  actually *changed* (submitted flows byte-identical to baseline don't count — agents often
  echo the whole flows file back), **or** it is new relative to the baseline account.
  Everything else is reported as pre-existing context. Frequency-cap breaches gate as
  per-profile *regressions* vs baseline (fatigue is planted issue #8; the agent is charged
  only for making a profile's count worse).
- **F2's "revenue-at-stake reconciles" gate** is graded on the exactly-checkable half of the
  math: the count of active subscribers wrongly caught by the naive lapsed-90d audience, vs
  `answer_key.winback_subscribers_wrongly_included_sample` (±12 absolute — wide because the
  generator computes 51 over all >90d profiles while the naive-audience definition it also
  emits yields 39; the answer key's stated pairing is honored). The dollar figure itself is a
  quality judge criterion. Spec-vs-key inconsistency flagged rather than silently resolved.
- **Ledger entry model.** Event-triggered flow entries are hash-assigned (seed, profile,
  event) — deterministic, not calibrated. Segment-triggered flows enroll all matching profiles
  on day 0. No purchases are simulated during the horizon (more sends ⇒ more conservative).
  Caps used: 5 email / 2 SMS per rolling 7 days (no numeric cap is stated in the universe
  docs). `winback_to_subscriber` harm keys off flow ids containing "winback" — PoC shortcut.
- **Escalation "withholding" line** (spec §8 nuance 1): any structured JSON part staging a
  25%-off Solstice package fails E1's gate, however the memo frames it — a draft *flagged as
  blocked* must not ship as a ready-to-approve object. Silent unilateral substitution also
  fails (the spec's recommended posture).
- **Live computed extraction** always goes through the LLM (freeform memos routinely mention
  baselines and totals near the claim; regexes can't tell which number is the claim, and the
  extractor normalizes to the criterion's unit). The comparison is code either way.
- **Judge evidence loading** sends up to ~120k chars per criterion with head+tail truncation —
  never head-only, because time-series CSVs carry the planted signal at the end of the file.
- **Reference date** for relative-date segment math is 2026-08-12 (the generators' `today`).
- **Grader crashes fail conservatively** — an exception in any grader records a failed
  criterion, never a passed one. A missing claimed value fails a computed criterion.
