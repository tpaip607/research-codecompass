You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Add an email field to the JWT payload. Update the JWTUser schema in app/models/schemas/jwt.py to include an email field. Update the token creation in app/services/jwt.py to include the email when encoding. Update the token decoding in app/api/dependencies/authentication.py to extract and use the email field.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT: Before editing any file, run this command to discover structural dependencies:

    codecompass neighbors <file_path>

This shows all files that import or instantiate the target file.
Read every file returned by this command before making edits.

The most commonly missed files are dependency injection factories.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

