import pytest

from app.crew.gitlab_notes import post_progress_note


def test_post_progress_note_accepts_existing_id(monkeypatch):
    calls = []

    def fake_update(**kwargs):
        calls.append(kwargs)
        return {"status": "ok", "note": {"id": 123}}

    monkeypatch.setattr("app.crew.gitlab_notes.update_merge_request_comment", fake_update)
    resp = post_progress_note(project_id=1, mr_iid=2, note_id=123)
    assert resp["note"]["id"] == 123
    assert calls[0]["note_id"] == 123
