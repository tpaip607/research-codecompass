#!/bin/bash
# run_trial.sh — Run a single CodeCompass experiment trial
#
# Usage: ./harness/run_trial.sh <task_id> <condition> <run_number>
#
#   task_id:    Two-digit task number, e.g. 01, 15, 30
#   condition:  A (vanilla) | B (bm25) | C (graph)
#   run_number: Integer, e.g. 1, 2, 3
#
# Example:
#   ./harness/run_trial.sh 01 A 1    # Vanilla Claude, task 1, first run
#   ./harness/run_trial.sh 21 C 2    # Graph MCP, task 21, second run

set -e

TASK_ID="${1}"
CONDITION="${2}"
RUN_NUM="${3}"

if [ -z "$TASK_ID" ] || [ -z "$CONDITION" ] || [ -z "$RUN_NUM" ]; then
    echo "Usage: $0 <task_id> <condition: A|B|C> <run_number>"
    exit 1
fi

if [[ ! "$CONDITION" =~ ^[ABC]$ ]]; then
    echo "Error: condition must be A, B, or C"
    exit 1
fi

# --- Paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BENCHMARK_REPO="/Users/tarak/engineer/repos/fastapi-realworld-example-app"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RESULT_DIR="$REPO_ROOT/results/task_${TASK_ID}_${CONDITION}_run${RUN_NUM}_${TIMESTAMP}"

# Find task directory
TASK_DIR="$(find "$REPO_ROOT/benchmarks/tasks" -type d -name "task_${TASK_ID}" 2>/dev/null | head -1)"
if [ -z "$TASK_DIR" ]; then
    echo "Error: task directory not found for task_id=${TASK_ID}"
    exit 1
fi

# Condition C uses prompt_c.md (includes graph navigation instruction) if it exists
if [ "$CONDITION" = "C" ] && [ -f "$TASK_DIR/prompt_c.md" ]; then
    PROMPT_FILE="$TASK_DIR/prompt_c.md"
else
    PROMPT_FILE="$TASK_DIR/prompt.md"
fi
GOLD_FILE="$TASK_DIR/gold_standard.json"

if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: prompt file not found at $PROMPT_FILE"
    exit 1
fi

echo "============================================"
echo " CodeCompass Trial"
echo " Task:      ${TASK_ID}"
echo " Condition: ${CONDITION}"
echo " Run:       ${RUN_NUM}"
echo " Output:    ${RESULT_DIR}"
echo "============================================"

# --- Step 1: Reset benchmark repo to clean state ---
echo "[1/4] Resetting benchmark repo..."
cd "$BENCHMARK_REPO"
git stash --quiet 2>/dev/null || true
git stash drop --quiet 2>/dev/null || true
git checkout -- . 2>/dev/null || true
echo "      Repo reset to clean state"

# --- Step 2: Build prompt (Condition B prepends BM25 rankings) ---
mkdir -p "$RESULT_DIR"

if [ "$CONDITION" = "B" ]; then
    echo "[2/4] Building BM25-augmented prompt..."
    TASK_DESC="$(python3 -c "import json; d=json.load(open('$GOLD_FILE')); print(d['description'])")"
    BM25_RESULTS="$(python3 "$REPO_ROOT/data_processing/build_bm25_index.py" \
        --repo "$BENCHMARK_REPO" \
        --output /tmp/bm25_trial.pkl \
        --query "$TASK_DESC" 2>/dev/null | grep -A 20 'Top results')"

    # Prepend BM25 ranked files to the original prompt
    {
        echo "The following files are likely relevant to this task (ranked by keyword similarity):"
        echo "$BM25_RESULTS"
        echo ""
        echo "---"
        echo ""
        cat "$PROMPT_FILE"
    } > "$RESULT_DIR/prompt_used.md"
else
    echo "[2/4] Using original prompt (Condition ${CONDITION})..."
    cp "$PROMPT_FILE" "$RESULT_DIR/prompt_used.md"
fi

# --- Step 3: Run Claude Code in print mode ---
echo "[3/4] Running claude -p (Condition ${CONDITION})..."
cd "$BENCHMARK_REPO"

# Note: For Condition C, ensure MCP is registered:
#   claude mcp add codecompass --command "python" --args "<path>/mcp_server/server.py"
# For Condition A, MCP should be absent from claude mcp list.

CLAUDECODE="" claude -p "$(cat "$RESULT_DIR/prompt_used.md")" \
    --dangerously-skip-permissions \
    > "$RESULT_DIR/output.txt" 2>&1
EXIT_CODE=$?
echo "      claude exit code: $EXIT_CODE"

# --- Step 4: Capture transcript and calculate ACS ---
echo "[4/4] Capturing transcript and calculating ACS..."

# Find the latest transcript for the benchmark repo
PROJ_HASH="$(ls -t ~/.claude/projects/ | grep -- "-fastapi-" | head -1)"
if [ -n "$PROJ_HASH" ]; then
    LATEST_JSONL="$(ls -t ~/.claude/projects/$PROJ_HASH/*.jsonl 2>/dev/null | head -1)"
    if [ -n "$LATEST_JSONL" ]; then
        cp "$LATEST_JSONL" "$RESULT_DIR/transcript.jsonl"
        echo "      Transcript saved"
    else
        echo "      Warning: no JSONL transcript found"
    fi
else
    echo "      Warning: no Claude project directory found for fastapi repo"
fi

# Write trial metadata
python3 -c "
import json, datetime
meta = {
    'task_id': '${TASK_ID}',
    'condition': '${CONDITION}',
    'run_number': ${RUN_NUM},
    'timestamp': '${TIMESTAMP}',
    'claude_exit_code': ${EXIT_CODE},
    'benchmark_repo': '${BENCHMARK_REPO}',
}
print(json.dumps(meta, indent=2))
" > "$RESULT_DIR/trial_meta.json"

# Calculate ACS
python3 "$REPO_ROOT/harness/calculate_acs.py" \
    --transcript "$RESULT_DIR/transcript.jsonl" \
    --gold "$GOLD_FILE" \
    --output "$RESULT_DIR/metrics.json"

echo ""
echo "Trial complete: $RESULT_DIR"
