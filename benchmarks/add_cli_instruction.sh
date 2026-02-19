#!/bin/bash
# Create Condition E prompts with CLI instructions

CLI_INSTRUCTION='

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT: Before editing any file, run this command to discover structural dependencies:

    codecompass neighbors <file_path>

This shows all files that import or instantiate the target file.
Read every file returned by this command before making edits.

The most commonly missed files are dependency injection factories.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
'

for task_dir in tasks/g3_hidden/task_*; do
    cp "$task_dir/prompt.md" "$task_dir/prompt_e.md"
    echo "$CLI_INSTRUCTION" >> "$task_dir/prompt_e.md"
    echo "Created $task_dir/prompt_e.md with CLI instruction"
done
