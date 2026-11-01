"""No paid network calls: contract, teaching-state and failure behavior tests."""
import base64
import io
import wave

import pytest
from fastapi.testclient import TestClient
from backend import main


@pytest.fixture(autouse=True)
def clean_state(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("SARVAM_API_KEY", "")
    monkeypatch.setattr(main, "STORAGE", tmp_path)
    for store in [main.sources, main.lessons, main.speech_cache, main.audio_files, main.followups]:
        store.clear()


@pytest.fixture
def client():
    return TestClient(main.app)


def demo(client):
    response = client.post("/api/lesson", json={"mode": "demo", "language": "en-IN"})
    assert response.status_code == 200
    return response.json()


def test_material_preserves_source_and_live_needs_gemini(client):
    response = client.post("/api/material", data={"text": "A fraction describes equal parts of a whole. Four equal pieces make four quarters.", "title": "Fractions"})
    assert response.status_code == 200
    source = response.json()
    assert source["pages"][0]["page"] == 1
    result = client.post("/api/lesson", json={"sourceId": source["sourceId"], "mode": "live"})
    assert result.status_code == 503
    assert "GEMINI_API_KEY" in result.json()["detail"]


def test_demo_is_explicit_and_does_not_claim_source_pages(client):
    lesson = demo(client)
    assert lesson["provider"] == "demo"
    assert lesson["sourceId"] is None
    assert all(not step["sourcePages"] for step in lesson["steps"])
    assert client.post("/api/lesson", json={"mode": "demo", "language": "kn-IN"}).status_code == 422


def test_misconception_repairs_then_grades_transfer_question(client):
    lesson = demo(client)
    payload = {"lessonId": lesson["id"], "stepId": "compare-parts", "mode": "demo", "answer": "1/4 because four is bigger"}
    repair = client.post("/api/answer", json=payload).json()
    assert repair["status"] == "needs_work"
    assert "1/2" in repair["followUpQuestion"]
    payload["answer"] = "1/3 because there are fewer equal parts"
    assert client.post("/api/answer", json=payload).json()["status"] != "correct"
    payload["answer"] = "1/2 because the same whole is split into fewer equal parts"
    assert client.post("/api/answer", json=payload).json()["status"] == "correct"


def test_correct_guess_without_reason_is_not_mastery(client):
    lesson = demo(client)
    result = client.post("/api/answer", json={"lessonId": lesson["id"], "stepId": "compare-parts", "answer": "1/3"}).json()
    assert result["status"] == "unclear"


def test_request_cannot_switch_live_lesson_to_demo_grading(client):
    lesson = demo(client)
    main.lessons[lesson["id"]]["provider"] = "gemini"
    result = client.post("/api/answer", json={"lessonId": lesson["id"], "stepId": "compare-parts", "mode": "demo", "answer": "1/3 because fewer equal parts"})
    assert result.status_code == 503


def test_invalid_material_and_custom_voice_clear_errors(client):
    assert client.post("/api/material", data={"text": "tiny"}).status_code == 422
    assert client.post("/api/material", files={"file": ("wrong.exe", b"not a document")}).status_code == 422
    response = client.post("/api/speech", json={"sessionId": "test", "lessonStepId": "step", "responseVersion": 0, "text": "Hello", "voice": {"kind": "custom", "profileId": "test"}})
    assert response.status_code == 501


def test_speech_cache_reuses_audio_but_preserves_response_version(client, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-only-not-real")
    monkeypatch.setenv("SARVAM_TTS_MODEL", "bulbul:v3")
    calls = []

    class Response:
        status_code = 200
        def json(self):
            return {"audios": [base64.b64encode(b"RIFFtest audio").decode()]}

    class FakeClient:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            calls.append((url, kwargs["json"]))
            return Response()

    monkeypatch.setattr(main.httpx, "AsyncClient", FakeClient)
    payload = {"sessionId": "test", "lessonStepId": "step", "responseVersion": 1, "text": "One equal piece.", "voice": {"kind": "preset"}}
    first = client.post("/api/speech", json=payload)
    assert first.status_code == 200
    payload["responseVersion"] = 2
    second = client.post("/api/speech", json=payload).json()
    assert len(calls) == 1
    assert second["responseVersion"] == 2
    assert second["audioUrl"] == first.json()["audioUrl"]
    assert client.get(second["audioUrl"]).status_code == 200
    assert calls[0][1]["target_language_code"] == "en-IN"


def test_long_wav_rejected_before_provider_call(client, monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-only-not-real")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 16000 * 31)
    response = client.post("/api/transcribe", files={"file": ("answer.wav", buffer.getvalue(), "audio/wav")})
    assert response.status_code == 422
