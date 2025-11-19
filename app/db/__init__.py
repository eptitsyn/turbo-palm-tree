# app/db/__init__.py
"""
Database package.

Note:
We intentionally do NOT import engine/SessionLocal/get_db here
to avoid side effects (e.g., creating a Postgres engine) when
`app.db` is imported during tests.

Import from `app.db.session` explicitly where needed in the app.
"""
