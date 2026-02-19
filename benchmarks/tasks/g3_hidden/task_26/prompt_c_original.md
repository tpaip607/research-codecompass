You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Replace the @lru_cache decorator on get_app_settings() in app/core/config.py with a manual singleton pattern using a module-level variable. The function should still return the same settings instance on repeated calls. Ensure the test configuration in tests/conftest.py still works correctly after this change.

Do NOT use the Task tool. Your very first tool call must be get_architectural_context(file_path="app/core/config.py"). After receiving the results, you MUST read every file listed in the output before making any edits — even files that may not need modification. Only after reading all neighbors should you decide which files to edit.
