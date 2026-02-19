#!/usr/bin/env python3
"""run_all_sdk.py — Orchestrator for all 270 CodeCompass trials.

Iterates 30 tasks × 3 conditions × 3 runs. Skips completed trials,
retries on transient failures, and shows a live Rich display.

Usage:
    python3 harness/sdk/run_all_sdk.py [options]

Options:
    --tasks 01,02,23      Only run these task IDs (zero-padded)
    --condition A         Only run this condition (A, B, C; or comma-separated)
    --runs 1,2            Only run these run numbers
    --dry-run             Print pending trials without executing
    --no-display          Disable Rich live display
    --max-retries N       Max retry attempts per trial (default 3)
    --pause N             Seconds to wait between trials (default 3)

Examples:
    # Single trial
    python3 harness/sdk/run_all_sdk.py --tasks 23 --condition C --runs 1

    # All remaining Condition C trials
    python3 harness/sdk/run_all_sdk.py --condition C

    # Full experiment
    python3 harness/sdk/run_all_sdk.py
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Make sure the repo root is on the path so `harness.sdk.*` imports resolve
_REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / ".env")

import anthropic

from harness.sdk.display import ExperimentDisplay
from harness.sdk.notify import notify
from harness.sdk.run_trial_sdk import REPO_ROOT, run_trial

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALL_TASKS = [f"{i:02d}" for i in range(1, 31)]
ALL_CONDITIONS = ["A", "B", "C"]
ALL_RUNS = [1, 2, 3]

DEFAULT_MAX_RETRIES = 3
DEFAULT_PAUSE = 3  # seconds between trials


# ---------------------------------------------------------------------------
# Langfuse (optional dependency)
# ---------------------------------------------------------------------------


def _init_langfuse() -> Optional[object]:
    try:
        from langfuse import Langfuse  # type: ignore
    except ImportError:
        print("langfuse not installed — tracing disabled (pip install langfuse)")
        return None

    pk = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    sk = os.getenv("LANGFUSE_SECRET_KEY", "")
    if not pk or not sk:
        print("LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY not set — tracing disabled")
        return None

    host = (
        os.getenv("LANGFUSE_BASE_URL")
        or os.getenv("LANGFUSE_HOST")
        or "https://cloud.langfuse.com"
    )
    return Langfuse(public_key=pk, secret_key=sk, host=host)


# ---------------------------------------------------------------------------
# Trial bookkeeping
# ---------------------------------------------------------------------------


def _result_glob(task_id: str, condition: str, run_num: int) -> list[Path]:
    return list(
        (REPO_ROOT / "results").glob(f"task_{task_id}_{condition}_run{run_num}_*")
    )


def trial_is_complete(task_id: str, condition: str, run_num: int) -> bool:
    """Return True if a metrics.json exists for this trial."""
    for d in _result_glob(task_id, condition, run_num):
        if d.is_dir() and (d / "metrics.json").exists():
            return True
    return False


def _failed_marker(task_id: str, condition: str, run_num: int) -> Path:
    return REPO_ROOT / "results" / f"task_{task_id}_{condition}_run{run_num}_FAILED"


def write_failed_marker(task_id: str, condition: str, run_num: int, error: str) -> None:
    marker = _failed_marker(task_id, condition, run_num)
    marker.mkdir(exist_ok=True)
    (marker / "failed.txt").write_text(error[:2000])


def clear_failed_marker(task_id: str, condition: str, run_num: int) -> None:
    marker = _failed_marker(task_id, condition, run_num)
    if marker.exists():
        shutil.rmtree(marker, ignore_errors=True)


# ---------------------------------------------------------------------------
# Trial list construction
# ---------------------------------------------------------------------------


def _task_group(task_id: str) -> str:
    tid = int(task_id)
    if tid <= 10:
        return "g1"
    if tid <= 20:
        return "g2"
    return "g3"


def build_trial_list(
    tasks: list[str],
    conditions: list[str],
    runs: list[int],
) -> list[tuple[str, str, int]]:
    """Return pending (task_id, condition, run_num) tuples, skipping completed trials."""
    pending = []
    for condition in conditions:
        for task_id in tasks:
            for run_num in runs:
                if not trial_is_complete(task_id, condition, run_num):
                    pending.append((task_id, condition, run_num))
    return pending


def count_completed(
    tasks: list[str], conditions: list[str], runs: list[int]
) -> tuple[int, dict[str, int]]:
    """Count completed trials overall and per condition."""
    total = 0
    per_cond: dict[str, int] = {c: 0 for c in conditions}
    for condition in conditions:
        for task_id in tasks:
            for run_num in runs:
                if trial_is_complete(task_id, condition, run_num):
                    total += 1
                    per_cond[condition] += 1
    return total, per_cond


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_all(args: argparse.Namespace) -> None:
    # Parse filter arguments
    tasks = sorted(set(args.tasks.split(","))) if args.tasks else ALL_TASKS
    conditions = args.condition.upper().split(",") if args.condition else ALL_CONDITIONS
    runs = [int(r) for r in args.runs.split(",")] if args.runs else ALL_RUNS
    max_retries: int = args.max_retries
    pause: int = args.pause

    total_possible = len(tasks) * len(conditions) * len(runs)
    completed_initial, _ = count_completed(tasks, conditions, runs)
    trials = build_trial_list(tasks, conditions, runs)

    print(f"CodeCompass SDK Runner")
    print(f"  Tasks: {len(tasks)}  Conditions: {conditions}  Runs: {runs}")
    print(f"  Total possible: {total_possible}")
    print(f"  Already done:   {completed_initial}")
    print(f"  To run:         {len(trials)}")
    print()

    if args.dry_run:
        for task_id, condition, run_num in trials:
            print(f"  WOULD RUN: task_{task_id}_{condition}_run{run_num}")
        return

    if not trials:
        print("All selected trials are already complete.")
        return

    # Init external services
    langfuse = _init_langfuse()

    # Init display
    display = ExperimentDisplay(
        total_trials=total_possible,
        completed_initial=completed_initial,
        use_live=not args.no_display,
    )

    completed_count = completed_initial
    failed_trials: list[tuple[str, str, int, str]] = []

    with display:
        for task_id, condition, run_num in trials:
            group = _task_group(task_id)
            display.set_current_trial(task_id, condition, run_num, group)
            display.set_status("RUNNING")

            last_error: Optional[str] = None

            for attempt in range(1, max_retries + 1):
                clear_failed_marker(task_id, condition, run_num)
                try:
                    metrics = run_trial(
                        task_id=task_id,
                        condition=condition,
                        run_num=run_num,
                        tool_callback=display.on_tool_call,
                        langfuse=langfuse,
                    )

                    # Success
                    completed_count += 1
                    display.update_overall(completed_count, condition, group, metrics["acs"])
                    display.set_status("DONE")
                    trace_id = metrics.get("langfuse_trace_id")
                    if trace_id:
                        lf_host = (
                            os.getenv("LANGFUSE_BASE_URL")
                            or os.getenv("LANGFUSE_HOST")
                            or "https://cloud.langfuse.com"
                        )
                        display.set_langfuse_url(f"{lf_host}/traces/{trace_id}")
                    last_error = None
                    break

                except anthropic.RateLimitError:
                    wait = 60 * attempt  # 60s, 120s, 180s
                    msg = f"Rate limit hit — waiting {wait}s (attempt {attempt}/{max_retries})"
                    display.set_status(f"RATE LIMIT ({wait}s)")
                    notify("CodeCompass — Rate Limit", msg)
                    time.sleep(wait)

                except anthropic.AuthenticationError as e:
                    notify("CodeCompass — Auth Error", str(e), urgent=True)
                    raise  # don't retry auth failures

                except Exception as e:
                    last_error = f"{type(e).__name__}: {e}"
                    display.set_status(f"ERROR (attempt {attempt}/{max_retries})")
                    notify(
                        "CodeCompass — Trial Failed",
                        f"task_{task_id}_{condition}_run{run_num}: {last_error}",
                    )
                    if attempt < max_retries:
                        time.sleep(10)

            if last_error is not None:
                # All retries exhausted
                write_failed_marker(task_id, condition, run_num, last_error)
                failed_trials.append((task_id, condition, run_num, last_error))
                display.set_status("FAILED")

            time.sleep(pause)

    # Flush Langfuse
    if langfuse is not None:
        try:
            langfuse.flush()
        except Exception:
            pass

    # Summary
    newly_done = completed_count - completed_initial
    print(f"\n{'=' * 60}")
    print(f"Experiment run complete.")
    print(f"  Newly completed: {newly_done}")
    print(f"  Failed:          {len(failed_trials)}")
    if failed_trials:
        print("\nFailed trials (re-run to retry):")
        for t, c, r, err in failed_trials:
            print(f"  task_{t}_{c}_run{r}  —  {err}")

    # Auto-aggregate
    aggregate_script = REPO_ROOT / "harness" / "aggregate_results.py"
    if aggregate_script.exists():
        print("\nAggregating results...")
        try:
            subprocess.run(
                [sys.executable, str(aggregate_script)],
                cwd=REPO_ROOT,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"  aggregate_results.py exited with {e.returncode}")

    notify("CodeCompass — Run Complete", f"Done. {newly_done} trials completed.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run CodeCompass benchmark trials via the Anthropic SDK.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--tasks",
        metavar="ID[,ID...]",
        help="Comma-separated task IDs to run (zero-padded), e.g. '01,23'",
    )
    parser.add_argument(
        "--condition",
        metavar="C[,C...]",
        help="Condition(s) to run: A, B, C (comma-separated)",
    )
    parser.add_argument(
        "--runs",
        metavar="N[,N...]",
        help="Run numbers to execute, e.g. '1,2'",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print pending trials without executing them",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Disable the Rich live display",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        metavar="N",
        help=f"Max retry attempts per trial (default {DEFAULT_MAX_RETRIES})",
    )
    parser.add_argument(
        "--pause",
        type=int,
        default=DEFAULT_PAUSE,
        metavar="SECS",
        help=f"Seconds to wait between trials (default {DEFAULT_PAUSE})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    run_all(_parse_args())
