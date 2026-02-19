You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: Extract the article creation logic from the route handler into the existing ArticlesService (app/services/articles.py). Create a new method ArticlesService.create_article() that accepts the article data and the current user. Update the route in articles_resource.py to call this service method instead of calling the repository directly.
