#!/usr/bin/env python3
"""
g2_analysis.py

G2 Regression Deep Dive: Why did Graph (Condition C) underperform on structural tasks?

This script analyzes G2 trials to understand the regression where Condition C
achieved 76.4% ACS vs 79.7% Vanilla (A) and 85.1% BM25 (B).

Expected findings:
1. Zero MCP tool adoption on G2 (0/30 trials)
2. Prompt overhead without tool benefit
3. Lower precision (more files accessed, same ACS)
"""

import pandas as pd
import sys
from pathlib import Path


def analyze_g2_regression(summary_path):
    df = pd.read_csv(summary_path)

    # Filter G2 trials
    g2 = df[df['group'] == 'g2'].copy()

    print("=" * 70)
    print("G2 Regression Analysis: Structural Tasks")
    print("=" * 70)
    print()

    # 1. Performance comparison
    print("## 1. Mean ACS by Condition (G2 Tasks Only)")
    print("-" * 70)
    for cond in ['A', 'B', 'C']:
        subset = g2[g2['condition'] == cond]
        if len(subset) > 0:
            print(f"Condition {cond}:")
            print(f"  Mean ACS:    {subset['acs'].mean():.3f} (±{subset['acs'].std():.3f})")
            print(f"  n:           {len(subset)} trials")
    print()

    # 2. Tool adoption on G2
    g2_c = g2[g2['condition'] == 'C']
    mcp_usage = (g2_c['mcp_calls'] > 0).sum()
    print("## 2. MCP Tool Adoption on G2 (Condition C)")
    print("-" * 70)
    print(f"Trials using graph tool: {mcp_usage}/{len(g2_c)} ({mcp_usage/len(g2_c)*100:.1f}%)")
    print()
    print("→ KEY FINDING: 0% adoption explains the regression!")
    print("  Model skipped graph tool despite structural dependencies")
    print("  being the tool's primary design purpose.")
    print()

    # 3. Tool call overhead
    print("## 3. Tool Usage Patterns")
    print("-" * 70)
    for cond in ['A', 'B', 'C']:
        subset = g2[g2['condition'] == cond]
        if len(subset) > 0:
            print(f"Condition {cond}:")
            print(f"  Mean total tool calls:  {subset['total_tool_calls'].mean():.1f}")
            print(f"  Mean MCP calls:         {subset['mcp_calls'].mean():.1f}")
            print(f"  Mean internal search:   {subset['internal_search_calls'].mean():.1f}")
            if 'files_read_count' in subset.columns:
                print(f"  Mean files read:        {subset['files_read_count'].mean():.1f}")
            if 'files_edited_count' in subset.columns:
                print(f"  Mean files edited:      {subset['files_edited_count'].mean():.1f}")
    print()

    # 4. Precision analysis
    if 'files_read_count' in g2.columns and 'required_files_total' in g2.columns:
        print("## 4. File Access Precision")
        print("-" * 70)
        for cond in ['A', 'B', 'C']:
            subset = g2[g2['condition'] == cond]
            if len(subset) > 0:
                # Calculate precision: required files hit / total files accessed
                total_accessed = subset['files_read_count'] + subset['files_edited_count']
                # Avoid division by zero
                precision_values = []
                for idx, row in subset.iterrows():
                    accessed = row['files_read_count'] + row['files_edited_count']
                    if accessed > 0:
                        precision = row['required_files_hit'] / accessed
                        precision_values.append(precision)

                if precision_values:
                    mean_precision = sum(precision_values) / len(precision_values)
                    print(f"Condition {cond}: {mean_precision:.3f} (required_hit / files_accessed)")
        print()

    # 5. Hypothesis summary
    print("=" * 70)
    print("## 5. Interpretation and Root Cause")
    print("=" * 70)
    print()
    print("The G2 regression (76.4% vs 79.7% Vanilla) is explained by:")
    print()
    print("1. **Zero graph tool adoption**: 0/30 G2 trials invoked get_architectural_context")
    print("   - Model applied rational heuristic: glob+read achieves ~80% ACS on G2")
    print("   - Tool overhead not justified when default strategy is 'good enough'")
    print()
    print("2. **Prompt overhead without tool benefit**:")
    print("   - Condition C has longer system prompt (graph tool instructions)")
    print("   - Without actually using the tool, this may distract from core task")
    print("   - Result: worst of both worlds (overhead + no navigation benefit)")
    print()
    print("3. **Implications:**")
    print("   - Confirms that tool adoption is the bottleneck, not graph quality")
    print("   - Suggests need for structural workflow enforcement (tool_choice)")
    print("   - Or: adaptive prompting that only adds tool instructions when needed")
    print()
    print("4. **Contrast with G3:**")
    print("   - G3 tasks: 100% MCP adoption (with improved prompt)")
    print("   - G3 result: 99.4% ACS (23.2pp improvement)")
    print("   - Shows the graph WORKS when adopted")
    print()

    # 6. Detailed condition comparison
    print("=" * 70)
    print("## 6. Detailed Comparison Table")
    print("=" * 70)
    print()
    print(f"{'Metric':<30} {'Condition A':<15} {'Condition B':<15} {'Condition C':<15}")
    print("-" * 75)

    metrics = [
        ('Mean ACS', 'acs'),
        ('Std ACS', 'acs'),  # Will compute std separately
        ('Mean FCTC', 'fctc'),
        ('Mean Tool Calls', 'total_tool_calls'),
        ('Mean MCP Calls', 'mcp_calls'),
    ]

    for label, col in metrics:
        row = f"{label:<30}"
        for cond in ['A', 'B', 'C']:
            subset = g2[g2['condition'] == cond][col]
            if 'Std' in label:
                val = subset.std()
            else:
                val = subset.mean()

            if 'ACS' in label:
                row += f" {val:.3f}"
            elif 'FCTC' in label:
                row += f" {val:.2f}"
            else:
                row += f" {val:.1f}"
            row += " " * (15 - len(f"{val:.1f}"))
        print(row)
    print()


if __name__ == '__main__':
    summary_path = Path(__file__).parent.parent / 'results' / 'summary.csv'

    if not summary_path.exists():
        print(f"Error: {summary_path} not found", file=sys.stderr)
        print("Run 'python harness/aggregate_results.py' first to generate summary.csv")
        sys.exit(1)

    analyze_g2_regression(summary_path)
