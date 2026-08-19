#!/usr/bin/env python3
"""MarketingBench PoC eval runner.

Examples:
  python run_eval.py --task A1 --agent replay:good
  python run_eval.py --task flow-design --agent replay:good   # every task in a category
  python run_eval.py --task all --agent llm                   # every task
  python run_eval.py --all-replay                             # full replay matrix (acceptance 1)
  python run_eval.py --dry-run                                # validate tasks/rubrics/canned, no tokens
  python run_eval.py --regrade runs/<run-id> [...]            # re-grade saved runs, zero agent tokens
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from harness import config, scoring
from harness.runner import grade_run, run_task
from harness.taskspec import TaskSpecError, list_tasks, load_task, resolve_task_selector

VARIANTS = ["good", "bad", "edge"]


def dry_run(universe: str) -> int:
    """Preflight: every task loads, rubric params resolve, canned deliverables parse.
    No tokens spent. Non-zero exit on any error."""
    from harness.graders.structural import PREDICATES
    from harness.universe import Universe
    u = Universe(config.UNIVERSES_ROOT / universe)
    answer_key = u.answer_key()
    errors, warnings = [], []
    tasks = list_tasks(universe)
    for category, tid, path in tasks:
        try:
            task = load_task(path)
        except TaskSpecError as e:
            errors.append(f"{tid}: {e}")
            continue
        for rel in task.files_in_scope:
            if not (u.root / rel).exists():
                errors.append(f"{tid}: files_in_scope missing {rel}")
        for c in task.criteria:
            for rel in c.evidence_files:
                if rel.startswith(("answer_key", "gen")):
                    errors.append(f"{tid}/{c.id}: evidence file {rel} is grader-only")
                elif not (u.root / rel).exists():
                    errors.append(f"{tid}/{c.id}: evidence file missing {rel}")
            if c.method == "computed" and c.params.get("key") not in answer_key:
                errors.append(f"{tid}/{c.id}: computed key {c.params.get('key')!r} not in answer_key")
            if c.method == "structural" and c.params.get("predicate") not in PREDICATES:
                errors.append(f"{tid}/{c.id}: unknown predicate {c.params.get('predicate')!r}")
            if c.method == "llm_judge" and "offline_check" not in c.params:
                warnings.append(f"{tid}/{c.id}: llm_judge criterion has no offline_check "
                                "(fails conservatively in offline/replay runs)")
        for variant in VARIANTS:
            vdir = config.CANNED_ROOT / universe / tid / variant
            if not vdir.is_dir():
                warnings.append(f"{tid}: no canned {variant}/ deliverable")
                continue
            for f in sorted(vdir.iterdir()):
                if f.suffix == ".json":
                    try:
                        json.loads(f.read_text())
                    except json.JSONDecodeError as e:
                        errors.append(f"{tid}: canned {variant}/{f.name} unparsable: {e}")
        n_gates = len(task.gate_criteria())
        print(f"  {category + '/' if category else '':<15}{tid:<12} {n_gates} gates, "
              f"{len(task.criteria) - n_gates} quality")
    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}")
    print(f"\n{len(tasks)} tasks · {len(warnings)} warnings · {len(errors)} errors")
    return 1 if errors else 0


def run_matrix(universe: str) -> int:
    scores = []
    print(f"{'task':<12} {'variant':<7} {'shippable':<10} failed gates")
    for _, tid, _ in list_tasks(universe):
        for variant in VARIANTS:
            r = run_task(tid, f"replay:{variant}", universe, offline=True)
            s = r["score"]
            if variant == "good":
                scores.append(s)
            print(f"{tid:<12} {variant:<7} {str(s['shippable']):<10} {', '.join(s['failed_gates']) or '—'}")
    print("\nrun summary over `good` submissions:", scoring.run_summary(scores))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="MarketingBench PoC eval harness")
    ap.add_argument("--task", help="task id (A1), category (flow-design), or 'all'")
    ap.add_argument("--agent", default="replay:good", help="replay:<good|bad|edge> or llm")
    ap.add_argument("--universe", default="alma-botanica")
    ap.add_argument("--out", help="output directory (default runs/<run-id>; single-task runs only)")
    ap.add_argument("--offline", action="store_true", help="force offline grading (no LLM calls)")
    ap.add_argument("--all-replay", action="store_true",
                    help="run the whole replay matrix (all tasks × good/bad/edge), offline")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate every task, rubric, and canned deliverable without running anything")
    ap.add_argument("--regrade", nargs="+", metavar="RUN_DIR",
                    help="re-grade saved run directories (no agent execution; honors --offline "
                         "and current judge config)")
    args = ap.parse_args()

    if args.dry_run:
        return dry_run(args.universe)
    if args.all_replay:
        return run_matrix(args.universe)
    if args.regrade:
        for run_dir in args.regrade:
            report = grade_run(Path(run_dir), offline=True if args.offline else None)
            s = report["score"]
            print(f"regraded {run_dir} · task {report['task']['id']} · shippable={s['shippable']} "
                  f"({s['gates_passed']}/{s['gates_total']} gates)"
                  + (f" · judge {report['judge_model']}" if report.get("judge_model") else " · offline"))
            if s["failed_gates"]:
                print("  failed gates:", ", ".join(s["failed_gates"]))
        return 0
    if not args.task:
        ap.error("--task is required unless --all-replay, --dry-run, or --regrade")

    task_ids = resolve_task_selector(args.task, args.universe)
    if len(task_ids) > 1 and args.out:
        ap.error("--out only applies to single-task runs")

    scores = []
    for tid in task_ids:
        report = run_task(tid, args.agent, args.universe,
                          out_dir=Path(args.out) if args.out else None,
                          offline=True if args.offline else None)
        s = report["score"]
        scores.append(s)
        print(f"task {tid} · agent {report['agent']} · shippable={s['shippable']} "
              f"({s['gates_passed']}/{s['gates_total']} gates, "
              f"{s['criteria_passed']}/{s['criteria_total']} criteria)")
        if s["failed_gates"]:
            print("  failed gates:", ", ".join(s["failed_gates"]))
        if s["quality_score"] is not None:
            print(f"  quality score: {s['quality_score']}")
        print("  report:", report["run_dir"] + "/report.html")
    if len(scores) > 1:
        print("\nrun summary:", scoring.run_summary(scores))
    return 0


if __name__ == "__main__":
    sys.exit(main())
