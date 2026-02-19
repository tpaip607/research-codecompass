You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Change the API response envelope format from using the resource name as the key (e.g., {"user": {...}}) to always using "data" as the key (e.g., {"data": {...}}). Update all response schema classes, all route handlers that return these schemas, and all tests that assert on the response structure.

Do NOT use the Task tool. Your very first tool call must be get_architectural_context(file_path="app/models/schemas/users.py"). After receiving the results, you MUST read every file listed in the output before making any edits — even files that may not need modification. Only after reading all neighbors should you decide which files to edit.
