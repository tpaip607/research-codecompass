You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Add a simple in-memory cache (a dict) to CommentsRepository in app/db/repositories/comments.py to cache author profile lookups. When fetching a comment's author, check the cache before calling ProfilesRepository. This avoids redundant profile queries when listing many comments.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT: Before editing any file, run this command to discover structural dependencies:

    codecompass neighbors <file_path>

This shows all files that import or instantiate the target file.
Read every file returned by this command before making edits.

The most commonly missed files are dependency injection factories.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

