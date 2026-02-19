You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Change the API response envelope format from using the resource name as the key (e.g., {"user": {...}}) to always using "data" as the key (e.g., {"data": {...}}). Update all response schema classes, all route handlers that return these schemas, and all tests that assert on the response structure.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT: Before editing any file, run this command to discover structural dependencies:

    codecompass neighbors <file_path>

This shows all files that import or instantiate the target file.
Read every file returned by this command before making edits.

The most commonly missed files are dependency injection factories.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

