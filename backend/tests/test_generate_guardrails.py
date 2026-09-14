"""
Integration tests for the generation request flow and the session-limit
guardrail (api/generate.py + tasks that mutate generations_used).

All Supabase calls are monkeypatched — the real deployed value of
GENERATION_LIMIT is 0 (try-on generation currently disabled, see main.py /
CLAUDE.md), so most of these tests raise it via monkeypatch to exercise the
queueing/validation logic that's dormant in production right now.

Ground-rule under test (CLAUDE.md "Rules for Code" #5): failed generations
must NOT count against the limit — increment only happens on success.
"""
import uuid

import pytest

import api.generate as generate_module
from db import client as db


@pytest.fixture(autouse=True)
def _patch_touch_session(monkeypatch):
    # require_session() touches last_active_at on every authenticated request.
    monkeypatch.setattr(db, "touch_session", lambda token: None)

SESSION_TOKEN = "test-session-token"
JOB_ID = str(uuid.uuid4())
FRAME_ID = str(uuid.uuid4())
TASK_ID = str(uuid.uuid4())


def _fake_session(used=0):
    return {"token": SESSION_TOKEN, "generations_used": used}


def _fake_job(owner=SESSION_TOKEN):
    return {"job_id": JOB_ID, "session_token": owner, "status": "complete"}


def _fake_frame():
    return {
        "frame_id": FRAME_ID,
        "product_image_url": "https://example.com/frame.webp",
        "style": "rectangular",
        "colour": "black",
    }


async def _noop_bg(*args, **kwargs) -> None:
    return None


def _get_client():
    # Imported lazily so conftest's dummy env vars are set before main.py loads.
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)


# ── POST /generate — limit guardrail ────────────────────────────────────────────

class TestGenerationLimitGuardrail:
    def test_no_session_returns_401(self, monkeypatch):
        client = _get_client()
        resp = client.post("/generate", json={"job_id": JOB_ID, "frame_id": FRAME_ID})
        assert resp.status_code == 401

    def test_deployed_limit_zero_rejects_immediately(self, monkeypatch):
        """The real, currently-deployed guardrail: GENERATION_LIMIT = 0."""
        monkeypatch.setattr(db, "get_session", lambda token: _fake_session(used=0))
        client = _get_client()
        resp = client.post(
            "/generate",
            json={"job_id": JOB_ID, "frame_id": FRAME_ID},
            headers={"X-Session-Token": SESSION_TOKEN},
        )
        assert resp.status_code == 403
        body = resp.json()["detail"]
        assert body["error"] == "generation_limit_reached"
        assert body["generations_remaining"] == 0

    def test_used_at_limit_rejects(self, monkeypatch):
        monkeypatch.setattr(generate_module, "GENERATION_LIMIT", 3)
        monkeypatch.setattr(db, "get_session", lambda token: _fake_session(used=3))
        client = _get_client()
        resp = client.post(
            "/generate",
            json={"job_id": JOB_ID, "frame_id": FRAME_ID},
            headers={"X-Session-Token": SESSION_TOKEN},
        )
        assert resp.status_code == 403

    def test_under_limit_queues_successfully(self, monkeypatch):
        monkeypatch.setattr(generate_module, "GENERATION_LIMIT", 3)
        monkeypatch.setattr(generate_module, "_run_generation_bg", _noop_bg)
        monkeypatch.setattr(db, "get_session", lambda token: _fake_session(used=1))
        monkeypatch.setattr(db, "get_job", lambda job_id: _fake_job())
        monkeypatch.setattr(db, "get_frame", lambda frame_id: _fake_frame())
        monkeypatch.setattr(db, "create_generation_task", lambda *a, **kw: TASK_ID)

        client = _get_client()
        resp = client.post(
            "/generate",
            json={"job_id": JOB_ID, "frame_id": FRAME_ID},
            headers={"X-Session-Token": SESSION_TOKEN},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "queued"
        assert body["generations_remaining"] == 1  # limit(3) - used(1) - 1


# ── POST /generate — job/frame ownership validation ─────────────────────────────

class TestJobAndFrameValidation:
    def test_job_owned_by_other_session_rejected(self, monkeypatch):
        monkeypatch.setattr(generate_module, "GENERATION_LIMIT", 3)
        monkeypatch.setattr(db, "get_session", lambda token: _fake_session(used=0))
        monkeypatch.setattr(db, "get_job", lambda job_id: _fake_job(owner="someone-else"))
        client = _get_client()
        resp = client.post(
            "/generate",
            json={"job_id": JOB_ID, "frame_id": FRAME_ID},
            headers={"X-Session-Token": SESSION_TOKEN},
        )
        assert resp.status_code == 403

    def test_missing_job_rejected(self, monkeypatch):
        monkeypatch.setattr(generate_module, "GENERATION_LIMIT", 3)
        monkeypatch.setattr(db, "get_session", lambda token: _fake_session(used=0))
        monkeypatch.setattr(db, "get_job", lambda job_id: None)
        client = _get_client()
        resp = client.post(
            "/generate",
            json={"job_id": JOB_ID, "frame_id": FRAME_ID},
            headers={"X-Session-Token": SESSION_TOKEN},
        )
        assert resp.status_code == 403

    def test_missing_frame_returns_404(self, monkeypatch):
        monkeypatch.setattr(generate_module, "GENERATION_LIMIT", 3)
        monkeypatch.setattr(db, "get_session", lambda token: _fake_session(used=0))
        monkeypatch.setattr(db, "get_job", lambda job_id: _fake_job())
        monkeypatch.setattr(db, "get_frame", lambda frame_id: None)
        client = _get_client()
        resp = client.post(
            "/generate",
            json={"job_id": JOB_ID, "frame_id": FRAME_ID},
            headers={"X-Session-Token": SESSION_TOKEN},
        )
        assert resp.status_code == 404


# ── GET /generate/{task_id} ──────────────────────────────────────────────────────

class TestGenerationStatus:
    def test_task_not_owned_by_session_returns_404(self, monkeypatch):
        monkeypatch.setattr(db, "get_session", lambda token: _fake_session(used=0))
        monkeypatch.setattr(db, "get_generation_task", lambda task_id: {"session_token": "someone-else"})
        client = _get_client()
        resp = client.get(f"/generate/{TASK_ID}", headers={"X-Session-Token": SESSION_TOKEN})
        assert resp.status_code == 404

    def test_failed_task_reports_not_counted_message(self, monkeypatch):
        monkeypatch.setattr(db, "get_session", lambda token: _fake_session(used=0))
        monkeypatch.setattr(
            db, "get_generation_task",
            lambda task_id: {"session_token": SESSION_TOKEN, "status": "failed"},
        )
        client = _get_client()
        resp = client.get(f"/generate/{TASK_ID}", headers={"X-Session-Token": SESSION_TOKEN})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "failed"
        assert "not been counted" in body["message"]


# ── Increment-only-on-success contract (CLAUDE.md rule #5) ──────────────────────

class TestIncrementOnlyOnSuccess:
    async def test_successful_generation_increments_counter(self, monkeypatch):
        increments = []
        monkeypatch.setattr(db, "get_frame", lambda frame_id: _fake_frame())
        monkeypatch.setattr(db, "update_generation_task", lambda *a, **kw: None)
        monkeypatch.setattr(db, "increment_generations", lambda token: increments.append(token))

        async def fake_generate_try_on(job_id, frame, task_id, distinct_id="unknown"):
            return "generated/fake-key.webp"

        monkeypatch.setattr(generate_module.gen_svc, "generate_try_on", fake_generate_try_on)

        await generate_module._run_generation_bg(TASK_ID, JOB_ID, FRAME_ID, SESSION_TOKEN)
        assert increments == [SESSION_TOKEN]

    async def test_failed_generation_does_not_increment_counter(self, monkeypatch):
        increments = []
        monkeypatch.setattr(db, "get_frame", lambda frame_id: _fake_frame())
        monkeypatch.setattr(db, "update_generation_task", lambda *a, **kw: None)
        monkeypatch.setattr(db, "increment_generations", lambda token: increments.append(token))

        async def fake_generate_try_on(job_id, frame, task_id, distinct_id="unknown"):
            raise RuntimeError("segmind unavailable")

        monkeypatch.setattr(generate_module.gen_svc, "generate_try_on", fake_generate_try_on)

        await generate_module._run_generation_bg(TASK_ID, JOB_ID, FRAME_ID, SESSION_TOKEN)
        assert increments == []

    async def test_missing_frame_does_not_increment_counter(self, monkeypatch):
        increments = []
        monkeypatch.setattr(db, "get_frame", lambda frame_id: None)
        monkeypatch.setattr(db, "update_generation_task", lambda *a, **kw: None)
        monkeypatch.setattr(db, "increment_generations", lambda token: increments.append(token))

        await generate_module._run_generation_bg(TASK_ID, JOB_ID, FRAME_ID, SESSION_TOKEN)
        assert increments == []
