#!/bin/bash
# Properly launch D and E experiments with environment variables

cd /Users/tarak/engineer/repos/research-codecompass

# Load environment variables
set -a
source .env
set +a

# Launch Condition D
echo "Launching Condition D..."
nohup .venv/bin/python harness/sdk/run_all_sdk.py \
  --tasks 21,22,23,24,25,26,27,28,29,30 \
  --condition D \
  --runs 1,2,3 \
  > /tmp/condition_d.log 2>&1 &

D_PID=$!
echo "D: PID $D_PID"

# Launch Condition E
echo "Launching Condition E..."
nohup .venv/bin/python harness/sdk/run_all_sdk.py \
  --tasks 21,22,23,24,25,26,27,28,29,30 \
  --condition E \
  --runs 1,2,3 \
  > /tmp/condition_e.log 2>&1 &

E_PID=$!
echo "E: PID $E_PID"

echo
echo "Both experiments launched!"
echo "Monitor with: python3.11 analyze_de_adoption.py"
