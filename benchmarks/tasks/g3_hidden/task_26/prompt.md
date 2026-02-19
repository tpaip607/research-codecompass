You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Replace the @lru_cache decorator on get_app_settings() in app/core/config.py with a manual singleton pattern using a module-level variable. The function should still return the same settings instance on repeated calls. Ensure the test configuration in tests/conftest.py still works correctly after this change.
