#!/bin/bash
# Monitor Condition D and E experiments

while true; do
    clear
    echo "════════════════════════════════════════════════════"
    echo "  CodeCompass Experiments D & E Monitor"
    echo "  $(date)"
    echo "════════════════════════════════════════════════════"
    echo

    # Count trials
    d_count=$(find results -name "task_*_D_run*" -type d | wc -l | tr -d ' ')
    e_count=$(find results -name "task_*_E_run*" -type d | wc -l | tr -d ' ')

    echo "Condition D (MCP + Checklist):  $d_count/30 trials"
    echo "Condition E (CLI + Standard):   $e_count/30 trials"
    echo
    echo "Total: $((d_count + e_count))/60 trials"
    echo

    # Latest trials
    echo "Latest D trials:"
    ls -t results/ | grep "_D_run" | head -3
    echo
    echo "Latest E trials:"
    ls -t results/ | grep "_E_run" | head -3
    echo

    # Check for completion
    if [ "$d_count" -ge 30 ] && [ "$e_count" -ge 30 ]; then
        echo "✓ BOTH EXPERIMENTS COMPLETE!"
        break
    fi

    sleep 15
done
