#!/usr/bin/env python3
"""MarketingBench PoC eval runner.

Examples:
  python run_eval.py --task A1 --agent replay:good
  python run_eval.py --task F1 --agent replay:bad
  python run_eval.py --all-replay            # full replay matrix (acceptance 1)
  python run_eval.py --task A1 --agent llm   # live agent (needs ANTHROPIC_API_KEY)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from harness import config, scoring
from harness.runner import run_task

ALL_TASKS = ["A1", "A4", "F1", "F2", "E1", "E1-control"]
VARIANTS = ["good", "bad", "edge"]


def main() -> int:
    ap = argparse.ArgumentParser(description="MarketingBench PoC eval harness")
    ap.add_argument("--task", help="task id, e.g. A1")
    ap.add_argument("--agent", default="replay:good", help="replay:<good|bad|edge> or llm")
    ap.add_argument("--universe", default="alma-botanica")
    ap.add_argument("--out", help="output directory (default runs/<run-id>)")
    ap.add_argument("--offline", action="store_true", help="force offline grading (no LLM calls)")
    ap.add_argument("--all-replay", action="store_true",
                    help="run the whole replay matrix (all tasks × good/bad/edge), offline")
    args = ap.parse_args()

    if args.all_replay:
        scores = []
        print(f"{'task':<12} {'variant':<7} {'shippable':<10} failed gates")
        for task_id in ALL_TASKS:
            for variant in VARIANTS:
                r = run_task(task_id, f"replay:{variant}", args.universe, offline=True)
                s = r["score"]
                if variant == "good":
                    scores.append(s)
                print(f"{task_id:<12} {variant:<7} {str(s['shippable']):<10} {', '.join(s['failed_gates']) or '—'}")
        summary = scoring.run_summary(scores)
        print("\nrun summary over `good` submissions:", summary)
        return 0

    if not args.task:
        ap.error("--task is required unless --all-replay")
    report = run_task(args.task, args.agent, args.universe,
                      out_dir=Path(args.out) if args.out else None,
                      offline=True if args.offline else None)
    s = report["score"]
    print(f"task {args.task} · agent {report['agent']} · shippable={s['shippable']} "
          f"({s['gates_passed']}/{s['gates_total']} gates)")
    if s["failed_gates"]:
        print("failed gates:", ", ".join(s["failed_gates"]))
    if s["quality_score"] is not None:
        print(f"quality score: {s['quality_score']}")
    print("report:", report["run_dir"] + "/report.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
