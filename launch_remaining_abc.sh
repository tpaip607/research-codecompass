#!/bin/bash
# Launch remaining A, B, C trials in parallel

cd /Users/tarak/engineer/repos/research-codecompass

# Load environment variables
set -a
source .env
set +a

# Launch A (2 trials: task_30 runs 2,3)
echo "Launching remaining A trials..."
nohup .venv/bin/python harness/sdk/run_all_sdk.py \
  --tasks 30 --condition A --runs 2,3 \
  > /tmp/finish_a.log 2>&1 &
A_PID=$!
echo "A: PID $A_PID"

# Launch B (13 trials: various tasks)
echo "Launching remaining B trials..."
nohup .venv/bin/python harness/sdk/run_all_sdk.py \
  --tasks 05,06,08,20,29,30 --condition B --runs 1,2,3 \
  > /tmp/finish_b.log 2>&1 &
B_PID=$!
echo "B: PID $B_PID"

# Launch C (3 trials: tasks 03,04,05)
echo "Launching remaining C trials..."
nohup .venv/bin/python harness/sdk/run_all_sdk.py \
  --tasks 03,04,05 --condition C --runs 1,2,3 \
  > /tmp/finish_c.log 2>&1 &
C_PID=$!
echo "C: PID $C_PID"

echo ""
echo "All 3 conditions running in parallel!"
echo "A: 2 trials, B: 13 trials, C: 3 trials (total: 18)"
echo ""
echo "Monitor with:"
echo "  python3.11 analyze_abc_progress.py"
