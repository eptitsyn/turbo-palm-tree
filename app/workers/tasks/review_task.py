# app/workers/tasks/review_tasks.py
from app.crew.crew_factory import run_file_diff_review
from app.workers.celery_app import celery_app


@celery_app.task(name="review_merge_request")
def review_merge_request(project_id: int, mr_iid: int, last_commit_sha: str | None):
    """
    MVP version:
    - In future: fetch MR diff from GitLab, split per file and call crewAI.
    - Now: just log and run crew on a fake diff to prove everything is wired.
    """
    # TODO: replace with real GitLab integration
    dummy_diff_context = {
        "file_path": "src/example.py",
        "language": "python",
        "diff": """@@ -1,3 +1,5 @@
- print("Hello")
+ def hello():
+     print("Hello, world!")
""",
        "old_code": 'print("Hello")\n',
        "new_code": 'def hello():\n    print("Hello, world!")\n',
    }

    findings = run_file_diff_review(dummy_diff_context)

    # In real code: persist findings to DB, post comments to GitLab, etc.
    # For now, just return them in task result:
    return {
        "project_id": project_id,
        "mr_iid": mr_iid,
        "last_commit_sha": last_commit_sha,
        "findings": findings,
    }
