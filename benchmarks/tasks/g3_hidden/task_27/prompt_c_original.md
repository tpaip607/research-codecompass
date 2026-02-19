You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Add a simple in-memory cache (a dict) to CommentsRepository in app/db/repositories/comments.py to cache author profile lookups. When fetching a comment's author, check the cache before calling ProfilesRepository. This avoids redundant profile queries when listing many comments.

Do NOT use the Task tool. Your very first tool call must be get_architectural_context(file_path="app/db/repositories/comments.py"). After receiving the results, you MUST read every file listed in the output before making any edits — even files that may not need modification. Only after reading all neighbors should you decide which files to edit.
