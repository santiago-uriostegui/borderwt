import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import pytest

from app.services.parser import (
    find_stripped_text,
    parse_optional_int,
    parse_update_time,
)


def make_element(tag_text: Optional[str]) -> ET.Element:
    root = ET.Element("root")
    if tag_text is not None:
        ET.SubElement(root, "value").text = tag_text
    return root


@pytest.mark.parametrize(
    "text, expected",
    [
        ("  hello  ", "hello"),
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_find_stripped_text(text, expected):
    element = make_element(text)
    assert find_stripped_text(element, "value") == expected


def test_find_stripped_text_missing_tag():
    root = ET.Element("root")
    assert find_stripped_text(root, "missing") is None


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("N/A", None),
        (" 5 ", 5),
        ("0", 0),
        ("not-a-number", None),
    ],
)
def test_parse_optional_int(value, expected):
    assert parse_optional_int(value) == expected


@pytest.mark.parametrize("value, port_date", [(None, "07/10/2026"), ("8:00 am", None)])
def test_parse_update_time_missing_inputs(value, port_date):
    assert parse_update_time(value, port_date) is None


def test_parse_update_time_not_available():
    assert parse_update_time("N/A", "07/10/2026") is None


def test_parse_update_time_with_known_timezone():
    result = parse_update_time("at 8:00 am PDT", "07/10/2026")
    assert result == datetime(2026, 7, 10, 8, 0, tzinfo=ZoneInfo("America/Los_Angeles"))


def test_parse_update_time_without_at_prefix():
    result = parse_update_time("8:00 am PDT", "07/10/2026")
    assert result == datetime(2026, 7, 10, 8, 0, tzinfo=ZoneInfo("America/Los_Angeles"))


def test_parse_update_time_with_unknown_timezone_abbreviation_is_naive():
    result = parse_update_time("8:00 am XYZ", "07/10/2026")
    assert result == datetime(2026, 7, 10, 8, 0)
    assert result.tzinfo is None


def test_parse_update_time_without_timezone_is_naive():
    result = parse_update_time("8:00 am", "07/10/2026")
    assert result == datetime(2026, 7, 10, 8, 0)
    assert result.tzinfo is None


def test_parse_update_time_malformed_time_returns_none():
    assert parse_update_time("garbage", "07/10/2026") is None


def test_parse_update_time_invalid_port_date_returns_none():
    assert parse_update_time("8:00 am PDT", "not-a-date") is None
