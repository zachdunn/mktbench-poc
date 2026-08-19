# MarketingBench

A proof-of-concept benchmark harness for evaluating AI agents on realistic lifecycle-marketing
work — the marketing analog of [Harvey LAB](https://github.com/harveyai/harvey-labs) / SWE-bench.

Two components: a **task set** (instructions, in-scope files, and per-criterion rubrics over a
closed synthetic brand universe with planted issues and exact answer keys) and an **execution
harness** that sandboxes an agent, grades its deliverable through four grader types, and emits
`report.json` plus a marketer-legible `report.html`.

**PoC scope:** 6 tasks (audits, flow builds, and an escalation trigger/control pair) against one
universe (`alma-botanica`). Python 3.11+, stdlib only.

## Quick start

```bash
python3 run_eval.py --task A1 --agent replay:good   # one task, canned deliverable
python3 run_eval.py --all-replay                    # full replay matrix, offline, token-free
```

Live agent runs (grading a real model end-to-end):

```bash
cp .env.example .env                                # set an Anthropic or OpenRouter key
python3 run_eval.py --task A1 --agent llm
```

Each run writes `runs/<run-id>/report.html` — open it in a browser, or see committed samples in
[`examples/`](examples/). Tests: `python3 -m unittest discover -s tests`.

## Documentation

| Doc | What's in it |
|---|---|
| [docs/acceptance.md](docs/acceptance.md) | Reproducing the six acceptance criteria, one command each |
| [docs/architecture.md](docs/architecture.md) | Module map, the four grader types, how to add a task |
| [docs/grading.md](docs/grading.md) | Scoring model, provider/model config, offline mode, conservative-grading decisions |
| [docs/marketing-benchmark-framework.md](docs/marketing-benchmark-framework.md) | Overall benchmark design and layer model |
