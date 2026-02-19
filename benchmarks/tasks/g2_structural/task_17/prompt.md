You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Refactor the database connection lifecycle in app/db/events.py to use an async context manager class DatabaseLifecycle instead of separate connect_to_db() and close_db_connection() functions. Update app/core/events.py to use the new class.
