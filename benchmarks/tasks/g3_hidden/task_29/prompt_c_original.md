You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Change get_user_by_username() and get_user_by_email() in app/db/repositories/users.py to return Optional[UserInDB] instead of raising EntityDoesNotExist. Update all call sites that currently catch EntityDoesNotExist from these methods to handle the None return value instead.

Do NOT use the Task tool. Your very first tool call must be get_architectural_context(file_path="app/db/repositories/users.py"). After receiving the results, you MUST read every file listed in the output before making any edits — even files that may not need modification. Only after reading all neighbors should you decide which files to edit.
