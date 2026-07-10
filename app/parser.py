import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo


def find_stripped_text(element: ET.Element, tag: str) -> Optional[str]:
    return (element.findtext(tag) or "").strip() or None


def parse_optional_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    text = value.strip()
    if not text or text == "N/A":
        return None
    try:
        return int(text)
    except ValueError:
        return None


def parse_update_time(
    value: Optional[str], port_date: Optional[str]
) -> Optional[datetime]:
    if not value or not port_date:
        return None

    text = value.strip()
    if not text or text == "N/A":
        return None

    if text.lower().startswith("at "):
        text = text[3:].strip()

    match = re.match(
        r"(?P<time>\d{1,2}:\d{2})\s*(?P<ampm>am|pm)\s*(?P<tz>[A-Za-z]{3})?",
        text,
    )
    if not match:
        return None

    try:
        parsed_date = datetime.strptime(port_date.strip(), "%m/%d/%Y")
    except ValueError:
        return None

    time_value = match.group("time")
    ampm = match.group("ampm")
    tz_name = (match.group("tz") or "").upper()

    try:
        parsed_time = datetime.strptime(f"{time_value} {ampm}", "%I:%M %p")
    except ValueError:
        return None

    timezone_name = {
        "EDT": "America/New_York",
        "EST": "America/New_York",
        "CDT": "America/Chicago",
        "CST": "America/Chicago",
        "MDT": "America/Denver",
        "MST": "America/Denver",
        "PDT": "America/Los_Angeles",
        "PST": "America/Los_Angeles",
    }.get(tz_name)

    if timezone_name is None:
        return parsed_date.replace(
            hour=parsed_time.hour,
            minute=parsed_time.minute,
            second=0,
            microsecond=0,
        )

    return parsed_date.replace(
        hour=parsed_time.hour,
        minute=parsed_time.minute,
        second=0,
        microsecond=0,
        tzinfo=ZoneInfo(timezone_name),
    )
