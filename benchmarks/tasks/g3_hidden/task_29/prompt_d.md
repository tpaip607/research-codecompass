You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Change get_user_by_username() and get_user_by_email() in app/db/repositories/users.py to return Optional[UserInDB] instead of raising EntityDoesNotExist. Update all call sites that currently catch EntityDoesNotExist from these methods to handle the None return value instead.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY PRE-FLIGHT CHECKLIST — Complete BEFORE making any edits
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You MUST complete this checklist in order. Do not skip any step.

[ ] Step 1: IDENTIFY the target file mentioned in the task
           Write it here: _______________________

[ ] Step 2: DISCOVER structural dependencies
           Run this command: get_architectural_context(<target_file>)
           List files returned: _______________________

[ ] Step 3: READ every file returned in Step 2
           Use read_file() for each one
           Mark when complete: [ ] Done

[ ] Step 4: VERIFY architectural coverage
           Question: Have you read every file that imports or instantiates the target?
           Answer: YES / NO
           If NO, go back to Step 2

[ ] Step 5: PROCEED to editing
           Only proceed after Steps 1-4 are complete

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  WARNING: Skipping this checklist will result in incomplete edits.
⚠️  CRITICAL: Dependency injection factories are the most commonly missed files.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Now begin with Step 1.

