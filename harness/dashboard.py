#!/usr/bin/env python3
"""
dashboard.py — Live experiment dashboard for CodeCompass trials.

Polls the results/ directory and renders a real-time terminal display
showing ACS, MCP calls, missed files, and per-condition progress.

Usage:
    python3 harness/dashboard.py
    python3 harness/dashboard.py --results /path/to/results --interval 10
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path


# ── ANSI helpers ────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RED    = "\033[31m"
WHITE  = "\033[37m"
BG_BAR = "\033[48;5;236m"


def clr(text, *codes):
    return "".join(codes) + str(text) + RESET


def bar(fraction, width=20):
    filled = int(fraction * width)
    empty  = width - filled
    return clr("█" * filled, GREEN) + clr("░" * empty, DIM)


def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


# ── Data loading ─────────────────────────────────────────────────────────────

def load_metrics(results_dir: Path) -> list[dict]:
    """Read all metrics.json files from the results directory."""
    records = []
    for metrics_file in sorted(results_dir.glob("*/metrics.json")):
        try:
            folder = metrics_file.parent.name  # e.g. task_23_C_run2_20260215_211740
            parts = folder.split("_")
            # Parse: task_<id>_<cond>_run<n>_<timestamp>
            # parts: ['task', id, cond, 'run<n>', ts]
            if len(parts) < 4:
                continue
            task_id  = parts[1].zfill(2)
            cond     = parts[2]
            run_num  = parts[3].replace("run", "")

            data = json.loads(metrics_file.read_text())
            data["_task_id"]  = task_id
            data["_cond"]     = cond
            data["_run"]      = run_num
            data["_folder"]   = folder
            records.append(data)
        except Exception:
            continue
    return records


# ── Aggregation ──────────────────────────────────────────────────────────────

def aggregate(records: list[dict]) -> dict:
    """
    Returns:
      by_cond[cond] = {acs: [floats], mcp: [ints], missed_files: Counter}
      by_task_cond[(task, cond)] = {acs: [floats], runs: int}
      total_trials, completed_by_cond
    """
    by_cond   = defaultdict(lambda: {"acs": [], "mcp": [], "missed": defaultdict(int)})
    by_task   = defaultdict(lambda: defaultdict(list))  # [task][cond] -> list of acs

    for r in records:
        c = r.get("_cond", "?")
        t = r.get("_task_id", "?")
        acs = r.get("acs", 0.0)
        mcp = r.get("mcp_calls", 0)
        missed = r.get("required_files_missed", [])

        by_cond[c]["acs"].append(acs)
        by_cond[c]["mcp"].append(mcp)
        for f in missed:
            by_cond[c]["missed"][f] += 1

        by_task[t][c].append(acs)

    return {"by_cond": dict(by_cond), "by_task": dict(by_task), "total": len(records)}


# ── Rendering ────────────────────────────────────────────────────────────────

def mean(lst):
    return sum(lst) / len(lst) if lst else 0.0


def render(records: list[dict], results_dir: Path):
    agg = aggregate(records)
    by_cond  = agg["by_cond"]
    by_task  = agg["by_task"]
    total    = agg["total"]

    lines = []
    w = 72

    def sep(char="─"):
        lines.append(clr(char * w, DIM))

    def hdr(text):
        lines.append(clr(f" {text}", BOLD + CYAN))

    lines.append("")
    lines.append(clr("  CodeCompass — Live Experiment Dashboard".center(w), BOLD + WHITE))
    lines.append(clr(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}  │  {total} trials completed".center(w), DIM))
    sep("═")

    # ── Per-condition summary ────────────────────────────────────────────────
    hdr("ACS by Condition  (mean ± N trials)")
    sep()
    for cond, label in [("A", "Vanilla Claude"), ("B", "BM25 Augmented"), ("C", "Graph MCP    ")]:
        d = by_cond.get(cond, {})
        acs_list = d.get("acs", [])
        mcp_list = d.get("mcp", [])
        n        = len(acs_list)
        avg_acs  = mean(acs_list)
        avg_mcp  = mean(mcp_list)
        b        = bar(avg_acs)
        pct      = f"{avg_acs:.1%}"

        cond_clr = {"A": YELLOW, "B": CYAN, "C": GREEN}.get(cond, WHITE)
        lines.append(
            f"  {clr(cond, cond_clr + BOLD)} {label}  {b} {clr(pct, BOLD)}  "
            f"n={clr(n, DIM)}  mcp_calls={clr(f'{avg_mcp:.1f}', CYAN)}"
        )

    sep()

    # ── Task × Condition grid ────────────────────────────────────────────────
    hdr("Per-task ACS  (A / B / C)  — mean across runs")
    sep()

    # Header row
    group_ranges = [("G1 Semantic", range(1, 11)),
                    ("G2 Structural", range(11, 21)),
                    ("G3 Hidden", range(21, 31))]

    for group_name, task_range in group_ranges:
        lines.append(f"  {clr(group_name, BOLD + YELLOW)}")
        for t in task_range:
            tid = str(t).zfill(2)
            row_parts = [f"  task_{tid}  "]
            task_data = by_task.get(tid, {})
            for cond in ("A", "B", "C"):
                acs_vals = task_data.get(cond, [])
                if not acs_vals:
                    cell = clr("  ·  ", DIM)
                else:
                    avg = mean(acs_vals)
                    color = GREEN if avg >= 1.0 else (YELLOW if avg >= 0.6 else RED)
                    cell = clr(f"{avg:5.1%}", color)
                row_parts.append(cell + "  ")
            lines.append("".join(row_parts))
        lines.append("")

    sep()

    # ── Most-missed files (Condition A+B vs C) ───────────────────────────────
    hdr("Most-missed required files")
    sep()
    for cond, label in [("A", "Vanilla"), ("B", "BM25"), ("C", "Graph ")]:
        d       = by_cond.get(cond, {})
        missed  = d.get("missed", {})
        top5    = sorted(missed.items(), key=lambda x: -x[1])[:3]
        cond_clr = {"A": YELLOW, "B": CYAN, "C": GREEN}.get(cond, WHITE)
        if top5:
            files_str = "  │  ".join(f"{f.split('/')[-1]}×{n}" for f, n in top5)
        else:
            files_str = clr("none yet", DIM)
        lines.append(f"  {clr(cond, cond_clr + BOLD)} {label}:  {files_str}")

    sep("═")
    lines.append(f"  {clr('Watching', DIM)} {clr(str(results_dir), DIM)}  "
                 f"{clr('— refreshes every 15s  (Ctrl-C to quit)', DIM)}")
    lines.append("")

    clear_screen()
    print("\n".join(lines))


# ── Main loop ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results",  default="results", help="Path to results directory")
    parser.add_argument("--interval", type=int, default=15, help="Refresh interval in seconds")
    args = parser.parse_args()

    results_dir = Path(args.results)
    if not results_dir.is_absolute():
        results_dir = Path(__file__).parent.parent / results_dir

    print(f"Starting dashboard — watching {results_dir}")

    while True:
        records = load_metrics(results_dir)
        render(records, results_dir)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
