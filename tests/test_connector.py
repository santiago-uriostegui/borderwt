import time
from contextlib import contextmanager
from urllib.error import URLError

import pytest

from app.services.connector import (
    BorderWaitTimeFetchError,
    fetch_border_wait_times_xml,
)

VALID_XML = (
    b"<border_wait_time><port><port_number>111111</port_number>"
    b"</port></border_wait_time>"
)


@contextmanager
def fake_response(body: bytes):
    class Response:
        def read(self):
            return body

    yield Response()


def test_fetch_parses_valid_xml(monkeypatch):
    monkeypatch.setattr(
        "app.services.connector.urlopen", lambda *a, **kw: fake_response(VALID_XML)
    )
    root = fetch_border_wait_times_xml()
    assert root.find("port").findtext("port_number") == "111111"


def test_fetch_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda seconds: None)
    calls = {"count": 0}

    def flaky_urlopen(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 2:
            raise URLError("temporary failure")
        return fake_response(VALID_XML)

    monkeypatch.setattr("app.services.connector.urlopen", flaky_urlopen)
    root = fetch_border_wait_times_xml()
    assert root.find("port").findtext("port_number") == "111111"
    assert calls["count"] == 2


def test_fetch_raises_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    def always_fails(*args, **kwargs):
        raise URLError("down")

    monkeypatch.setattr("app.services.connector.urlopen", always_fails)
    with pytest.raises(URLError):
        fetch_border_wait_times_xml()


def test_fetch_wraps_unexpected_errors(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    def boom(*args, **kwargs):
        raise ValueError("unexpected")

    monkeypatch.setattr("app.services.connector.urlopen", boom)
    with pytest.raises(BorderWaitTimeFetchError):
        fetch_border_wait_times_xml()
