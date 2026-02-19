#!/usr/bin/env python3
"""Analyze adoption rates for Conditions D and E in real-time"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def analyze_trial(trial_dir):
    """Extract MCP/CLI usage from a trial"""
    meta_file = trial_dir / "trial_meta.json"
    metrics_file = trial_dir / "metrics.json"

    if not meta_file.exists() or not metrics_file.exists():
        return None

    try:
        with open(meta_file) as f:
            meta = json.load(f)
        with open(metrics_file) as f:
            metrics = json.load(f)

        tool_calls = meta.get("tool_calls_log", [])

        # Count graph tool usage
        mcp_calls = 0
        cli_calls = 0

        for call in tool_calls:
            tool_name = call.get("tool", "")
            if tool_name == "get_architectural_context":
                mcp_calls += 1
            elif tool_name == "run_bash":
                # Check if it's a codecompass command
                tool_input = call.get("input", {})
                command = tool_input.get("command", "")
                if "codecompass" in command:
                    cli_calls += 1

        return {
            "task_id": meta.get("task_id"),
            "condition": meta.get("condition"),
            "run_number": meta.get("run_number"),
            "acs": metrics.get("acs", 0.0),
            "mcp_calls": mcp_calls,
            "cli_calls": cli_calls,
            "total_tool_calls": len(tool_calls),
        }
    except Exception as e:
        print(f"Error analyzing {trial_dir.name}: {e}", file=sys.stderr)
        return None

def main():
    results_dir = Path("results")

    # Find all D and E trials
    d_trials = []
    e_trials = []

    for trial_dir in sorted(results_dir.glob("task_*_D_run*")):
        result = analyze_trial(trial_dir)
        if result:
            d_trials.append(result)

    for trial_dir in sorted(results_dir.glob("task_*_E_run*")):
        result = analyze_trial(trial_dir)
        if result:
            e_trials.append(result)

    # Analyze adoption rates
    print("=" * 70)
    print("  CodeCompass Conditions D & E - Adoption Analysis")
    print("=" * 70)
    print()

    if d_trials:
        print(f"Condition D (MCP + Checklist): {len(d_trials)} trials complete")
        d_adopted = sum(1 for t in d_trials if t["mcp_calls"] > 0)
        d_adoption_rate = 100 * d_adopted / len(d_trials)
        d_acs_when_used = [t["acs"] for t in d_trials if t["mcp_calls"] > 0]
        d_acs_when_not = [t["acs"] for t in d_trials if t["mcp_calls"] == 0]

        print(f"  Adoption: {d_adopted}/{len(d_trials)} = {d_adoption_rate:.1f}%")
        if d_acs_when_used:
            print(f"  ACS when used: {100*sum(d_acs_when_used)/len(d_acs_when_used):.1f}%")
        if d_acs_when_not:
            print(f"  ACS when ignored: {100*sum(d_acs_when_not)/len(d_acs_when_not):.1f}%")
        print(f"  Overall ACS: {100*sum(t['acs'] for t in d_trials)/len(d_trials):.1f}%")
    else:
        print("Condition D: No completed trials yet")

    print()

    if e_trials:
        print(f"Condition E (CLI + Standard): {len(e_trials)} trials complete")
        e_adopted = sum(1 for t in e_trials if t["cli_calls"] > 0)
        e_adoption_rate = 100 * e_adopted / len(e_trials)
        e_acs_when_used = [t["acs"] for t in e_trials if t["cli_calls"] > 0]
        e_acs_when_not = [t["acs"] for t in e_trials if t["cli_calls"] == 0]

        print(f"  Adoption: {e_adopted}/{len(e_trials)} = {e_adoption_rate:.1f}%")
        if e_acs_when_used:
            print(f"  ACS when used: {100*sum(e_acs_when_used)/len(e_acs_when_used):.1f}%")
        if e_acs_when_not:
            print(f"  ACS when ignored: {100*sum(e_acs_when_not)/len(e_acs_when_not):.1f}%")
        print(f"  Overall ACS: {100*sum(t['acs'] for t in e_trials)/len(e_trials):.1f}%")
    else:
        print("Condition E: No completed trials yet")

    print()
    print("=" * 70)
    print(f"BASELINE - Condition C (G3): 85.7% adoption (30/35 trials)")
    print("=" * 70)
    print()

    if d_trials and len(d_trials) >= 5:
        print("Early signal:")
        if d_adoption_rate > 90:
            print("  ✓ Checklist prompt is WORKING - high adoption!")
        elif d_adoption_rate > 85.7:
            print("  ~ Checklist shows modest improvement over baseline")
        else:
            print("  ✗ Checklist not improving adoption over baseline")

    if e_trials and len(e_trials) >= 5:
        if e_adoption_rate > 90:
            print("  ✓ CLI interface is WORKING - high adoption!")
        elif e_adoption_rate > 85.7:
            print("  ~ CLI shows modest improvement over baseline")
        else:
            print("  ✗ CLI not improving adoption over baseline")

if __name__ == "__main__":
    main()
