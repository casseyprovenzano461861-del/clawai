# -*- coding: utf-8 -*-
"""
Unit tests for EventBus from src/shared/backend/events.py
"""

import os
import sys
import pytest
from datetime import datetime

os.environ["ENVIRONMENT"] = "testing"

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.shared.backend.events import EventBus, Event, EventType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_event_bus():
    """Reset the singleton before and after every test so tests stay isolated."""
    EventBus.reset()
    yield
    EventBus.reset()


@pytest.fixture
def bus():
    """Return a fresh EventBus instance (not the singleton)."""
    return EventBus()


# ---------------------------------------------------------------------------
# Singleton pattern
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEventBusSingleton:
    def test_get_returns_same_instance(self):
        a = EventBus.get()
        b = EventBus.get()
        assert a is b

    def test_reset_creates_new_instance(self):
        a = EventBus.get()
        EventBus.reset()
        b = EventBus.get()
        assert a is not b

    def test_reset_sets_instance_to_none(self):
        EventBus.get()
        EventBus.reset()
        assert EventBus._instance is None


# ---------------------------------------------------------------------------
# Subscribe / Unsubscribe
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEventBusSubscribeUnsubscribe:
    def test_subscribe_adds_handler(self, bus):
        handler = lambda e: None
        bus.subscribe(EventType.MESSAGE, handler)
        assert handler in bus._handlers.get(EventType.MESSAGE, [])

    def test_subscribe_prevents_duplicate(self, bus):
        handler = lambda e: None
        bus.subscribe(EventType.MESSAGE, handler)
        bus.subscribe(EventType.MESSAGE, handler)
        assert bus._handlers[EventType.MESSAGE].count(handler) == 1

    def test_unsubscribe_removes_handler(self, bus):
        handler = lambda e: None
        bus.subscribe(EventType.MESSAGE, handler)
        bus.unsubscribe(EventType.MESSAGE, handler)
        assert handler not in bus._handlers.get(EventType.MESSAGE, [])

    def test_unsubscribe_nonexistent_handler_no_error(self, bus):
        handler = lambda e: None
        bus.unsubscribe(EventType.MESSAGE, handler)  # should not raise

    def test_unsubscribe_nonexistent_event_type_no_error(self, bus):
        handler = lambda e: None
        bus.unsubscribe(EventType.USER_COMMAND, handler)  # no handlers registered


# ---------------------------------------------------------------------------
# Emit and handler invocation
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEventBusEmit:
    def test_emit_calls_subscribed_handler(self, bus):
        received = []
        bus.subscribe(EventType.MESSAGE, lambda e: received.append(e))
        event = Event(EventType.MESSAGE, {"text": "hello"})
        bus.emit(event)
        assert len(received) == 1
        assert received[0].data["text"] == "hello"

    def test_emit_calls_multiple_handlers(self, bus):
        results_a, results_b = [], []
        bus.subscribe(EventType.MESSAGE, lambda e: results_a.append(1))
        bus.subscribe(EventType.MESSAGE, lambda e: results_b.append(2))
        bus.emit(Event(EventType.MESSAGE, {}))
        assert results_a == [1]
        assert results_b == [2]

    def test_emit_does_not_call_handlers_for_other_types(self, bus):
        received = []
        bus.subscribe(EventType.STATE_CHANGED, lambda e: received.append(e))
        bus.emit(Event(EventType.MESSAGE, {}))
        assert received == []

    def test_emit_with_no_subscribers_no_error(self, bus):
        bus.emit(Event(EventType.MESSAGE, {}))  # should not raise

    def test_event_timestamp_is_set(self):
        before = datetime.now()
        event = Event(EventType.MESSAGE, {})
        after = datetime.now()
        assert before <= event.timestamp <= after


# ---------------------------------------------------------------------------
# Exception isolation
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEventBusExceptionIsolation:
    def test_one_failing_handler_does_not_affect_others(self, bus):
        good_results = []

        def bad_handler(e):
            raise RuntimeError("boom")

        def good_handler(e):
            good_results.append(e)

        bus.subscribe(EventType.MESSAGE, bad_handler)
        bus.subscribe(EventType.MESSAGE, good_handler)
        bus.emit(Event(EventType.MESSAGE, {"text": "test"}))
        assert len(good_results) == 1

    def test_multiple_failing_handlers_isolated(self, bus):
        results = []

        def fail1(e):
            raise ValueError("fail1")

        def fail2(e):
            raise TypeError("fail2")

        def ok(e):
            results.append("ok")

        bus.subscribe(EventType.MESSAGE, fail1)
        bus.subscribe(EventType.MESSAGE, ok)
        bus.subscribe(EventType.MESSAGE, fail2)
        bus.emit(Event(EventType.MESSAGE, {}))
        assert results == ["ok"]


# ---------------------------------------------------------------------------
# Convenience methods
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEventBusConvenienceMethods:
    def test_emit_state(self, bus):
        received = []
        bus.subscribe(EventType.STATE_CHANGED, lambda e: received.append(e))
        bus.emit_state("running", details="scanning", target="10.0.0.1", task="nmap")
        assert len(received) == 1
        data = received[0].data
        assert data["state"] == "running"
        assert data["details"] == "scanning"
        assert data["target"] == "10.0.0.1"
        assert data["task"] == "nmap"

    def test_emit_state_omits_optional_fields(self, bus):
        received = []
        bus.subscribe(EventType.STATE_CHANGED, lambda e: received.append(e))
        bus.emit_state("idle")
        data = received[0].data
        assert data["state"] == "idle"
        assert "target" not in data
        assert "task" not in data

    def test_emit_message(self, bus):
        received = []
        bus.subscribe(EventType.MESSAGE, lambda e: received.append(e))
        bus.emit_message("hello", msg_type="success")
        data = received[0].data
        assert data["text"] == "hello"
        assert data["type"] == "success"

    def test_emit_message_default_type(self, bus):
        received = []
        bus.subscribe(EventType.MESSAGE, lambda e: received.append(e))
        bus.emit_message("info msg")
        assert received[0].data["type"] == "info"

    def test_emit_tool(self, bus):
        received = []
        bus.subscribe(EventType.TOOL, lambda e: received.append(e))
        bus.emit_tool("complete", "nmap", args={"target": "10.0.0.1"}, result="open ports: 80")
        data = received[0].data
        assert data["status"] == "complete"
        assert data["name"] == "nmap"
        assert data["args"] == {"target": "10.0.0.1"}
        assert data["result"] == "open ports: 80"

    def test_emit_tool_default_args(self, bus):
        received = []
        bus.subscribe(EventType.TOOL, lambda e: received.append(e))
        bus.emit_tool("start", "sqlmap")
        data = received[0].data
        assert data["args"] == {}
        assert data["result"] is None

    def test_emit_finding(self, bus):
        received = []
        bus.subscribe(EventType.FINDING, lambda e: received.append(e))
        bus.emit_finding("SQL Injection", severity="high", detail="UNION based")
        data = received[0].data
        assert data["title"] == "SQL Injection"
        assert data["severity"] == "high"
        assert data["detail"] == "UNION based"

    def test_emit_finding_defaults(self, bus):
        received = []
        bus.subscribe(EventType.FINDING, lambda e: received.append(e))
        bus.emit_finding("Info finding")
        data = received[0].data
        assert data["severity"] == "info"
        assert data["detail"] == ""

    def test_emit_progress(self, bus):
        received = []
        bus.subscribe(EventType.PROGRESS, lambda e: received.append(e))
        bus.emit_progress(0.5, "halfway")
        data = received[0].data
        assert data["percent"] == 0.5
        assert data["description"] == "halfway"

    def test_emit_command(self, bus):
        received = []
        bus.subscribe(EventType.USER_COMMAND, lambda e: received.append(e))
        bus.emit_command("pause")
        assert received[0].data["command"] == "pause"

    def test_emit_input(self, bus):
        received = []
        bus.subscribe(EventType.USER_INPUT, lambda e: received.append(e))
        bus.emit_input("scan the target")
        assert received[0].data["text"] == "scan the target"


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEventBusReset:
    def test_reset_clears_singleton(self):
        inst = EventBus.get()
        EventBus.reset()
        assert EventBus._instance is None
        new_inst = EventBus.get()
        assert new_inst is not inst

    def test_reset_clears_handlers_on_new_instance(self):
        bus = EventBus.get()
        bus.subscribe(EventType.MESSAGE, lambda e: None)
        EventBus.reset()
        new_bus = EventBus.get()
        assert new_bus._handlers == {}
