You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Change the article slug generation in app/services/articles.py to add a "conduit-" prefix to every generated slug. Update all places in the codebase that create, store, or query articles by slug to account for this change. Ensure existing tests are updated to use the new slug format.

Do NOT use the Task tool. Your very first tool call must be get_architectural_context(file_path="app/services/articles.py"). After receiving the results, you MUST read every file listed in the output before making any edits — even files that may not need modification. Only after reading all neighbors should you decide which files to edit.
