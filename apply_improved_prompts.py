#!/usr/bin/env python3
"""Apply improved prompt format (checklist at END) to all G3 tasks."""

from pathlib import Path
import re

TEMPLATE = """You are working on the FastAPI RealWorld example app at `/Users/tarak/engineer/repos/fastapi-realworld-example-app`.

## Task

{task_description}

---

## ⚠️ MANDATORY PRE-FLIGHT CHECKLIST

**Complete ALL steps in order BEFORE making any edits:**

- [ ] **Step 1:** Call `get_architectural_context("{primary_file}")`
- [ ] **Step 2:** Read EVERY file returned by the tool (all structural neighbors)
- [ ] **Step 3:** Verify you've covered ALL files that import or depend on the target
- [ ] **Step 4:** Identify which files need editing vs. which are read-only dependencies
- [ ] **Step 5:** Implement changes across all required files

### Why This Matters

- Files that **depend on** or **instantiate** the target file MUST be checked
- These files may have **zero keyword overlap** with the task description
- Only the **structural graph** can surface them
- **Skipping Step 1 will cause you to miss required files**

### Important Notes

- Do NOT use the Task tool
- Your **first action** must be Step 1 above
- Read all neighbors before deciding what to edit

---
"""

def extract_task_info(prompt_path: Path) -> tuple[str, str]:
    """Extract task description and primary file from existing prompt."""
    content = prompt_path.read_text()

    # Extract task description (usually after "Task:" line)
    lines = content.split('\n')
    task_desc_lines = []
    in_task = False

    for line in lines:
        if 'Task:' in line or '## Task' in line:
            in_task = True
            continue
        if in_task:
            if line.strip().startswith('---') or line.strip().startswith('##') or 'Do NOT use' in line:
                break
            if line.strip():
                task_desc_lines.append(line.strip())

    task_description = ' '.join(task_desc_lines)

    # Try to find primary file from prompt
    # Look for patterns like: app/db/repositories/base.py, app/api/routes/users.py, etc.
    file_pattern = r'app/[\w/]+\.py'
    matches = re.findall(file_pattern, content)
    primary_file = matches[0] if matches else "app/UNKNOWN.py"

    return task_description, primary_file

def main():
    base_dir = Path("benchmarks/tasks/g3_hidden")

    for task_dir in sorted(base_dir.glob("task_*")):
        task_id = task_dir.name

        # Check for existing prompt
        prompt_c = task_dir / "prompt_c.md"
        prompt_base = task_dir / "prompt.md"

        source = prompt_c if prompt_c.exists() else prompt_base
        if not source.exists():
            print(f"⚠️  {task_id}: No prompt found")
            continue

        # Extract info
        try:
            task_desc, primary_file = extract_task_info(source)

            # Backup original
            if prompt_c.exists():
                backup = task_dir / "prompt_c_original.md"
                if not backup.exists():
                    prompt_c.rename(backup)
                    source = backup

            # Generate improved prompt
            improved = TEMPLATE.format(
                task_description=task_desc,
                primary_file=primary_file
            )

            # Write new prompt_c.md
            (task_dir / "prompt_c.md").write_text(improved)
            print(f"✓ {task_id}: Updated (file: {primary_file})")

        except Exception as e:
            print(f"✗ {task_id}: Error - {e}")

if __name__ == "__main__":
    main()
