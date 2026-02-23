"""
aggregate_results.py

Reads all results/*/metrics.json files and produces:
  - results/summary.csv    : one row per trial
  - results/analysis.json  : mean ACS, std dev, FCTC per condition per group

Usage:
    python harness/aggregate_results.py --results results/
"""

import json
import csv
import argparse
import statistics
from pathlib import Path
from collections import defaultdict


GROUP_MAP = {
    "g1": "semantic",
    "g2": "structural",
    "g3": "hidden",
}


def get_group(task_id: str) -> str:
    """Infer group from task_id (e.g. 'g1_task_01' or '01')."""
    if task_id.startswith("g1"):
        return "g1"
    if task_id.startswith("g2"):
        return "g2"
    if task_id.startswith("g3"):
        return "g3"
    # Infer from numeric ID
    try:
        n = int(task_id.replace("task_", "").replace("g1_", "").replace("g2_", "").replace("g3_", ""))
        if n <= 10:
            return "g1"
        if n <= 20:
            return "g2"
        return "g3"
    except ValueError:
        return "unknown"


def get_condition_from_dir(dir_name: str) -> str:
    """Extract condition (A/B/C) from result directory name."""
    parts = dir_name.split("_")
    for part in parts:
        if part in ("A", "B", "C"):
            return part
    return "unknown"


def load_all_metrics(results_dir: Path) -> list[dict]:
    rows = []
    for metrics_file in sorted(results_dir.rglob("metrics.json")):
        try:
            data = json.loads(metrics_file.read_text())
        except Exception:
            continue

        # Infer condition from parent directory name
        dir_name = metrics_file.parent.name
        condition = get_condition_from_dir(dir_name)
        group = get_group(data.get("task_id", ""))

        # Load trial metadata if available
        meta_file = metrics_file.parent / "trial_meta.json"
        run_number = 0
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
                run_number = meta.get("run_number", 0)
                condition = meta.get("condition", condition)
            except Exception:
                pass

        rows.append({
            "result_dir": dir_name,
            "task_id": data.get("task_id", ""),
            "condition": condition,
            "group": group,
            "run_number": run_number,
            "acs": data.get("acs", 0.0),
            "ecr": data.get("ecr", 0.0),  # NEW
            "rer": data.get("rer", -1),  # NEW
            "fctc": data.get("fctc", -1),
            "total_tool_calls": data.get("total_tool_calls", 0),
            "mcp_calls": data.get("mcp_calls", 0),
            "internal_search_calls": data.get("internal_search_calls", 0),
            "required_files_total": data.get("required_files_total", 0),
            "required_files_hit": len(data.get("required_files_hit", [])),
            "required_files_edited": len(data.get("required_files_edited", [])),  # NEW
            "files_read_count": len(data.get("files_read", [])),  # NEW
            "files_edited_count": len(data.get("files_edited", [])),  # NEW
        })

    return rows


def write_csv(rows: list[dict], output_path: Path):
    if not rows:
        print("No results to write")
        return

    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {output_path}")


def compute_analysis(rows: list[dict]) -> dict:
    """Compute mean/std ACS and FCTC per condition per group."""
    # Bucket: condition -> group -> [acs values]
    acs_buckets = defaultdict(lambda: defaultdict(list))
    fctc_buckets = defaultdict(lambda: defaultdict(list))

    for row in rows:
        c = row["condition"]
        g = row["group"]
        acs_buckets[c][g].append(row["acs"])
        if row["fctc"] >= 0:  # -1 means never touched a required file
            fctc_buckets[c][g].append(row["fctc"])

    analysis = {"by_condition_group": {}}

    for condition in sorted(acs_buckets.keys()):
        analysis["by_condition_group"][condition] = {}
        for group in sorted(acs_buckets[condition].keys()):
            acs_vals = acs_buckets[condition][group]
            fctc_vals = fctc_buckets[condition][group]

            analysis["by_condition_group"][condition][group] = {
                "n": len(acs_vals),
                "acs_mean": round(statistics.mean(acs_vals), 4) if acs_vals else None,
                "acs_std": round(statistics.stdev(acs_vals), 4) if len(acs_vals) > 1 else None,
                "acs_min": round(min(acs_vals), 4) if acs_vals else None,
                "acs_max": round(max(acs_vals), 4) if acs_vals else None,
                "fctc_mean": round(statistics.mean(fctc_vals), 2) if fctc_vals else None,
                "fctc_std": round(statistics.stdev(fctc_vals), 2) if len(fctc_vals) > 1 else None,
            }

    # Overall per condition
    analysis["by_condition"] = {}
    for condition in sorted(acs_buckets.keys()):
        all_acs = [v for group_vals in acs_buckets[condition].values() for v in group_vals]
        all_fctc = [v for group_vals in fctc_buckets[condition].values() for v in group_vals]
        analysis["by_condition"][condition] = {
            "n": len(all_acs),
            "acs_mean": round(statistics.mean(all_acs), 4) if all_acs else None,
            "acs_std": round(statistics.stdev(all_acs), 4) if len(all_acs) > 1 else None,
            "fctc_mean": round(statistics.mean(all_fctc), 2) if all_fctc else None,
        }

    return analysis


def print_summary_table(analysis: dict):
    print("\n=== ACS Summary (mean ± std) ===")
    print(f"{'Condition':<12} {'G1 Semantic':<18} {'G2 Structural':<18} {'G3 Hidden':<18} {'Overall':<18}")
    print("-" * 76)

    for condition in ["A", "B", "C"]:
        cond_data = analysis["by_condition_group"].get(condition, {})
        overall = analysis["by_condition"].get(condition, {})
        row = f"{condition:<12}"
        for group in ["g1", "g2", "g3"]:
            gd = cond_data.get(group, {})
            if gd.get("acs_mean") is not None:
                cell = f"{gd['acs_mean']:.2%} ± {gd['acs_std'] or 0:.2%}"
            else:
                cell = "N/A"
            row += f" {cell:<17}"
        if overall.get("acs_mean") is not None:
            row += f" {overall['acs_mean']:.2%}"
        print(row)


def main():
    parser = argparse.ArgumentParser(description="Aggregate CodeCompass experiment results")
    parser.add_argument("--results", default="results", help="Path to results directory")
    args = parser.parse_args()

    results_dir = Path(args.results)
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return

    rows = load_all_metrics(results_dir)
    if not rows:
        print("No metrics.json files found in results directory")
        return

    print(f"Loaded {len(rows)} trial results")

    # Write CSV
    write_csv(rows, results_dir / "summary.csv")

    # Write analysis JSON
    analysis = compute_analysis(rows)
    analysis_path = results_dir / "analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2))
    print(f"Saved analysis to {analysis_path}")

    # Print table
    print_summary_table(analysis)


if __name__ == "__main__":
    main()
