You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Add an optional cache=False parameter to the get_repository() function in app/api/dependencies/database.py. When cache=True, the repository instance should be cached per-request using a dict stored on the request state. Update the function signature and all call sites that use get_repository() to pass the parameter explicitly.
