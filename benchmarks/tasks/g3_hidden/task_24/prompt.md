You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Move the password hashing logic out of app/services/security.py into a new module app/db/hash_service.py. Update all files that currently import from app/services/security.py to import from the new location. The UserInDB model and the users repository both depend on this.
