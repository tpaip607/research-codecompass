You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Add a simple in-memory cache (a dict) to CommentsRepository in app/db/repositories/comments.py to cache author profile lookups. When fetching a comment's author, check the cache before calling ProfilesRepository. This avoids redundant profile queries when listing many comments.
