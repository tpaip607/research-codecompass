You are working on the FastAPI RealWorld example app at /Users/tarak/engineer/repos/fastapi-realworld-example-app.

Task: In app/db/repositories/articles.py, extract the article data enrichment logic from _get_article_from_db_record into a separate private method _build_enrichment_pipeline(). The _get_article_from_db_record method should call this new method. Ensure the existing behavior is preserved.
