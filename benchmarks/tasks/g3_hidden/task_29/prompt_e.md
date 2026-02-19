You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Change get_user_by_username() and get_user_by_email() in app/db/repositories/users.py to return Optional[UserInDB] instead of raising EntityDoesNotExist. Update all call sites that currently catch EntityDoesNotExist from these methods to handle the None return value instead.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT: Before editing any file, run this command to discover structural dependencies:

    codecompass neighbors <file_path>

This shows all files that import or instantiate the target file.
Read every file returned by this command before making edits.

The most commonly missed files are dependency injection factories.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

