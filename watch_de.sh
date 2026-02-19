#!/bin/bash
# Watch Conditions D and E progress in real-time

cd /Users/tarak/engineer/repos/research-codecompass

while true; do
    clear
    date
    echo
    python3.11 analyze_de_adoption.py
    echo
    echo "Refreshing every 30 seconds... (Ctrl-C to stop)"
    sleep 30
done
