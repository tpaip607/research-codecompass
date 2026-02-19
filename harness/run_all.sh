#!/bin/bash
# run_all.sh — Run the full CodeCompass experiment (270 trials)
#
# 30 tasks x 3 conditions (A, B, C) x 3 runs = 270 trials
#
# Usage:
#   ./harness/run_all.sh                    # Run everything
#   ./harness/run_all.sh --condition A      # Run only Condition A
#   ./harness/run_all.sh --tasks 01,02,03   # Run specific tasks only
#   ./harness/run_all.sh --dry-run          # Print what would run, don't execute

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults
CONDITIONS=("A" "B" "C")
RUNS=(1 2 3)
DRY_RUN=false
SPECIFIC_TASKS=""
SPECIFIC_CONDITION=""

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --condition)   SPECIFIC_CONDITION="$2"; shift 2 ;;
        --tasks)       SPECIFIC_TASKS="$2";     shift 2 ;;
        --dry-run)     DRY_RUN=true;            shift ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

if [ -n "$SPECIFIC_CONDITION" ]; then
    CONDITIONS=("$SPECIFIC_CONDITION")
fi

# Build task list
if [ -n "$SPECIFIC_TASKS" ]; then
    IFS=',' read -ra TASK_LIST <<< "$SPECIFIC_TASKS"
else
    TASK_LIST=()
    for i in $(seq -w 1 30); do
        TASK_LIST+=("$i")
    done
fi

TOTAL=$(( ${#TASK_LIST[@]} * ${#CONDITIONS[@]} * ${#RUNS[@]} ))
COMPLETED=0
FAILED=0

echo "============================================"
echo " CodeCompass Full Experiment"
echo " Tasks:      ${#TASK_LIST[@]}"
echo " Conditions: ${CONDITIONS[*]}"
echo " Runs each:  ${#RUNS[@]}"
echo " Total:      $TOTAL trials"
echo " Dry run:    $DRY_RUN"
echo "============================================"

LOG_FILE="$REPO_ROOT/results/run_all_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$REPO_ROOT/results"

for CONDITION in "${CONDITIONS[@]}"; do
    for TASK_ID in "${TASK_LIST[@]}"; do
        for RUN in "${RUNS[@]}"; do
            TRIAL_LABEL="task_${TASK_ID}_${CONDITION}_run${RUN}"

            if $DRY_RUN; then
                echo "  [DRY RUN] Would run: $TRIAL_LABEL"
                continue
            fi

            echo ""
            echo "--- $TRIAL_LABEL ($((COMPLETED + FAILED + 1))/$TOTAL) ---"

            # Skip if a successful result already exists for this trial
            EXISTING=$(find "$REPO_ROOT/results" -type f \
                -path "*/task_${TASK_ID}_${CONDITION}_run${RUN}_*/metrics.json" 2>/dev/null | head -1)
            if [ -n "$EXISTING" ] && [ -s "$EXISTING" ]; then
                echo "  [SKIP] $TRIAL_LABEL — result exists at $EXISTING"
                COMPLETED=$((COMPLETED + 1))
                continue
            fi

            if bash "$SCRIPT_DIR/run_trial.sh" "$TASK_ID" "$CONDITION" "$RUN" 2>&1 | tee -a "$LOG_FILE"; then
                COMPLETED=$((COMPLETED + 1))
                echo "  [OK] $TRIAL_LABEL"
            else
                FAILED=$((FAILED + 1))
                echo "  [FAILED] $TRIAL_LABEL" | tee -a "$LOG_FILE"
            fi

            # Brief pause between trials to avoid rate limits
            sleep 5
        done
    done
done

echo ""
echo "============================================"
echo " Experiment complete"
echo " Completed: $COMPLETED"
echo " Failed:    $FAILED"
echo " Log:       $LOG_FILE"
echo "============================================"

if [ "$COMPLETED" -gt 0 ]; then
    echo ""
    echo "Running aggregation..."
    python3 "$SCRIPT_DIR/aggregate_results.py" --results "$REPO_ROOT/results"
fi
