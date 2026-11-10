"""Offline tests for the Streamlit UI (app.py).

A fake provider replaces the real model, so these tests use no API key and no
network. They check that the UI drives the same tool loop as chat.py, shows the
tool calls, handles clarify/provider errors, and writes a transcript.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

import providers
from providers.base import ModelResponse, ToolCall

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class ScriptedProvider:
    """Returns one scripted ModelResponse per complete() call and records the messages."""

    default_model = "fake-model"

    def __init__(self, responses: list[ModelResponse | Exception]) -> None:
        self.responses = list(responses)
        self.calls: list[list[dict[str, str]]] = []

    def complete(self, messages, tools=None, **kwargs: Any) -> ModelResponse:
        self.calls.append(list(messages))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def ui(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("AGENT_TRANSCRIPTS_DIR", str(tmp_path))

    def _start(responses: list[ModelResponse | Exception]) -> tuple[AppTest, ScriptedProvider]:
        fake = ScriptedProvider(responses)
        monkeypatch.setattr(providers, "make_provider", lambda name: fake)
        app = AppTest.from_file(APP, default_timeout=30).run()
        assert not app.exception, app.exception
        return app, fake

    return _start


def transcript(tmp_path: Path) -> dict[str, Any]:
    files = list(tmp_path.glob("*.transcript.json"))
    assert len(files) == 1
    return json.loads(files[0].read_text(encoding="utf-8"))


def all_text(app: AppTest) -> str:
    return "\n".join(m.value for m in app.markdown) + "\n".join(c.value for c in app.code)


def test_first_screen_shows_sample_questions_and_no_transcript_yet(ui, tmp_path: Path) -> None:
    app, fake = ui([])
    labels = [b.label for b in app.button]
    assert "Tin tức AI hôm nay có gì nổi bật?" in labels
    assert fake.calls == []
    assert list(tmp_path.glob("*.json")) == []


def test_tool_call_is_executed_shown_and_logged(ui, tmp_path: Path) -> None:
    items = [{"title": "Tin A", "url": "https://example.com/a", "source": "example.com"}]
    app, fake = ui([
        ModelResponse(tool_calls=[ToolCall("format", {"items": items, "template": "bullets"})]),
        ModelResponse(text="Đây là bản tin."),
    ])

    app.chat_input[0].set_value("Làm bản tin giúp mình").run()

    assert not app.exception
    text = all_text(app)
    assert "`format`" in text                     # tool call rendered
    assert "[example.com](https://example.com/a)" in text  # tool result rendered
    assert "Đây là bản tin." in text              # final answer rendered
    assert len(fake.calls) == 2                   # model saw the tool result in round 2
    assert "TOOL_RESULTS_JSON" in fake.calls[1][-1]["content"]

    log = transcript(tmp_path)
    assert log["interface"] == "streamlit"
    turn = log["turns"][0]
    assert turn["status"] == "answered"
    assert turn["rounds"][0]["tool_calls"][0]["name"] == "format"
    assert turn["tool_events"][0]["result"]["item_count"] == 1


def test_clarify_pauses_and_choice_button_sends_answer(ui, tmp_path: Path) -> None:
    app, fake = ui([
        ModelResponse(tool_calls=[ToolCall("clarify", {
            "question": "Bạn muốn xem tweet của ai?", "response_type": "choice", "options": ["sama", "OpenAI"],
        })]),
        ModelResponse(text="OK, xem tweet của sama."),
    ])

    app.chat_input[0].set_value("Xem tweet mới nhất").run()
    assert "Bạn muốn xem tweet của ai?" in all_text(app)
    assert len(fake.calls) == 1                   # loop stopped, waiting for user

    next(b for b in app.button if b.label == "sama").click().run()

    assert not app.exception
    second_turn_messages = fake.calls[1]
    assert second_turn_messages[-1] == {"role": "user", "content": "sama"}
    assert any("Bạn muốn xem tweet của ai?" in m["content"] for m in second_turn_messages)  # history kept
    statuses = [t["status"] for t in transcript(tmp_path)["turns"]]
    assert statuses == ["waiting_for_user", "answered"]


def test_tool_call_works_on_cp1252_console(ui, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: on a Windows cp1252 console the emoji log line printed by
    chat.run_model_tool_loop raised UnicodeEncodeError and the turn failed."""
    import io
    import sys

    console = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", console)
    items = [{"title": "Tin A", "url": "https://example.com/a", "source": "example.com"}]
    app, _ = ui([
        ModelResponse(tool_calls=[ToolCall("format", {"items": items, "template": "bullets"})]),
        ModelResponse(text="Xong."),
    ])
    app.chat_input[0].set_value("Tin AI hôm nay?").run()

    assert not app.exception
    assert not app.error, [e.value for e in app.error]
    assert transcript(tmp_path)["turns"][0]["status"] == "answered"


def test_provider_error_is_shown_not_raised(ui, tmp_path: Path) -> None:
    app, _ = ui([RuntimeError("Missing API key env var: OPENROUTER_API_KEY")])

    app.chat_input[0].set_value("Tin AI hôm nay?").run()

    assert not app.exception
    assert any("Missing API key" in e.value for e in app.error)
    assert transcript(tmp_path)["turns"][0]["status"] == "provider_error"
