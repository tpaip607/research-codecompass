#!/usr/bin/env python3
"""
fill_results.py

Polls results/ until all 270 trials are complete, then:
  1. Computes full ACS statistics by group × condition
  2. Writes results/final_results.json
  3. Prints the filled results table for copy-paste into the paper
"""

import json
import time
import statistics
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path(__file__).parent.parent / "results"
TOTAL_TRIALS = 270

def load_all():
    by_group_cond = defaultdict(lambda: defaultdict(list))
    by_task_cond  = defaultdict(lambda: defaultdict(list))
    mcp_calls     = defaultdict(list)

    for m in RESULTS_DIR.glob("*/metrics.json"):
        parts = m.parent.name.split("_")
        if len(parts) < 4 or parts[2] not in ("A","B","C"):
            continue
        tid  = int(parts[1])
        cond = parts[2]
        try:
            d   = json.loads(m.read_text())
            acs = d.get("acs", 0.0)
            g   = "G1" if tid <= 10 else "G2" if tid <= 20 else "G3"
            by_group_cond[g][cond].append(acs)
            by_task_cond[tid][cond].append(acs)
            mcp_calls[cond].append(d.get("mcp_calls", 0))
        except:
            pass
    return by_group_cond, by_task_cond, mcp_calls

def count_complete():
    n = 0
    for m in RESULTS_DIR.glob("*/metrics.json"):
        parts = m.parent.name.split("_")
        if len(parts) >= 4 and parts[2] in ("A","B","C"):
            n += 1
    return n

def mean(lst): return sum(lst)/len(lst) if lst else 0.0
def stdev(lst): return statistics.stdev(lst) if len(lst) > 1 else 0.0

def print_results(by_group_cond, by_task_cond, mcp_calls):
    print("\n" + "="*70)
    print("  CODECOMPASS FINAL RESULTS")
    print("="*70)

    # Overall summary table
    print("\nTable 1: Mean ACS by Condition × Group\n")
    print(f"{'Group':<12} {'Condition A':>14} {'Condition B':>14} {'Condition C':>14}")
    print("-"*56)
    for g in ["G1","G2","G3"]:
        row = f"{g:<12}"
        for c in ["A","B","C"]:
            vals = by_group_cond[g][c]
            if vals:
                row += f"  {mean(vals):6.1%} ±{stdev(vals):4.1%}"
            else:
                row += f"  {'--':>12}"
        print(row)
    print()

    # Overall per-condition
    print("Overall ACS:")
    for c in ["A","B","C"]:
        all_vals = []
        for g in ["G1","G2","G3"]:
            all_vals += by_group_cond[g][c]
        if all_vals:
            avg_mcp = mean(mcp_calls[c])
            print(f"  Condition {c}: {mean(all_vals):.1%} ±{stdev(all_vals):.1%}  "
                  f"(n={len(all_vals)})  mcp_calls={avg_mcp:.1f}")
    print()

    # Per-task breakdown
    print("Table 2: Per-task ACS (mean across 3 runs)\n")
    print(f"{'Task':<10} {'Group':<5} {'A':>8} {'B':>8} {'C':>8}")
    print("-"*42)
    for tid in range(1, 31):
        g = "G1" if tid <= 10 else "G2" if tid <= 20 else "G3"
        row = f"task_{tid:02d}   {g:<5}"
        for c in ["A","B","C"]:
            vals = by_task_cond[tid][c]
            row += f"  {mean(vals):5.1%}" if vals else f"  {'--':>5}"
        print(row)
    print()

    # Key findings
    print("Key Findings:")
    for g in ["G1","G2","G3"]:
        a = mean(by_group_cond[g]["A"])
        b = mean(by_group_cond[g]["B"])
        c = mean(by_group_cond[g]["C"])
        best = max([("A",a),("B",b),("C",c)], key=lambda x: x[1])
        print(f"  {g}: A={a:.1%}  B={b:.1%}  C={c:.1%}  → best={best[0]} (+{best[1]-min(a,b,c):.1%} vs worst)")

def save_json(by_group_cond, by_task_cond, mcp_calls):
    out = {
        "by_group_condition": {
            g: {c: {
                "mean": mean(by_group_cond[g][c]),
                "stdev": stdev(by_group_cond[g][c]),
                "n": len(by_group_cond[g][c]),
                "values": by_group_cond[g][c]
            } for c in ["A","B","C"] if by_group_cond[g][c]}
            for g in ["G1","G2","G3"]
        },
        "by_task": {
            str(tid): {c: mean(by_task_cond[tid][c])
                       for c in ["A","B","C"] if by_task_cond[tid][c]}
            for tid in range(1, 31)
        },
        "mcp_calls_mean": {c: mean(mcp_calls[c]) for c in ["A","B","C"] if mcp_calls[c]}
    }
    out_path = RESULTS_DIR / "final_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nSaved to {out_path}")

if __name__ == "__main__":
    print("Watching for experiment completion...")
    while True:
        n = count_complete()
        print(f"  {n}/270 complete", end="\r", flush=True)
        if n >= TOTAL_TRIALS:
            break
        time.sleep(30)

    print(f"\n\n✓ All {TOTAL_TRIALS} trials complete!")
    by_group_cond, by_task_cond, mcp_calls = load_all()
    print_results(by_group_cond, by_task_cond, mcp_calls)
    save_json(by_group_cond, by_task_cond, mcp_calls)
