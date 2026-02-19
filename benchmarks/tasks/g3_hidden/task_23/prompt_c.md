You are working on the FastAPI RealWorld example app at `/Users/tarak/engineer/repos/fastapi-realworld-example-app`.

## Task

Add a `logger` parameter to the `BaseRepository.__init__` method in `app/db/repositories/base.py`. The logger should default to `None`. Update all repository classes that inherit from BaseRepository to pass a logger when they internally instantiate other repository classes.

---

## ⚠️ MANDATORY PRE-FLIGHT CHECKLIST

**Complete ALL steps in order BEFORE making any edits:**

- [ ] **Step 1:** Call `get_architectural_context("app/db/repositories/base.py")`
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
