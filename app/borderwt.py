from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from app.celery_app import celery_app
from app.connector import fetch_border_wait_times_xml
from app.parser import find_stripped_text, parse_optional_int, parse_update_time
from app.database import (
    BorderPort,
    BorderTimeImport,
    PrimaryLaneType,
    SecondaryLaneType,
    SessionLocal,
    WaitTime,
)

INVALID_OPERATIONAL_STATUSES = {"N/A", "Lanes Closed", "Update Pending"}


@celery_app.task(name="app.celery_app.import_border_wait_times")
def import_border_wait_times(name: str) -> dict:
    root = fetch_border_wait_times_xml()
    created_ports = []
    created_wait_times = []

    def is_within_one_hour(a: Optional[datetime], b: Optional[datetime]) -> bool:
        if a is None or b is None:
            return False

        utc = ZoneInfo("UTC")
        a_utc = a.replace(tzinfo=utc) if a.tzinfo is None else a.astimezone(utc)
        b_utc = b.replace(tzinfo=utc) if b.tzinfo is None else b.astimezone(utc)
        return abs(a_utc - b_utc) < timedelta(hours=1)

    with SessionLocal() as session:
        existing_ports = {port.port_number: port for port in session.query(BorderPort).all()}

        for port_element in root.findall("port"):
            port_number = find_stripped_text(port_element, "port_number")
            if not port_number:
                continue

            port_date = find_stripped_text(port_element, "date")

            border_port = existing_ports.get(port_number)
            if border_port is None:
                border_port = BorderPort(
                    port_number=port_number,
                    border=find_stripped_text(port_element, "border"),
                    port_name=find_stripped_text(port_element, "port_name"),
                    hours=find_stripped_text(port_element, "hours"),
                    port_status=find_stripped_text(port_element, "port_status"),
                )
                session.add(border_port)
                session.flush()
                existing_ports[port_number] = border_port
                created_ports.append(port_number)

            for primary_lane_type in PrimaryLaneType:
                primary_container = port_element.find(primary_lane_type.value)
                if primary_container is None:
                    continue

                for secondary_lane_type in SecondaryLaneType:
                    secondary_container = primary_container.find(secondary_lane_type.value)
                    if secondary_container is None:
                        continue

                    operational_status = find_stripped_text(secondary_container, "operational_status")
                    if operational_status in INVALID_OPERATIONAL_STATUSES:
                        continue

                    existing_wait_time = (
                        session.query(WaitTime)
                        .filter(
                            WaitTime.border_port_id == border_port.id,
                            WaitTime.primary_lane_type == primary_lane_type,
                            WaitTime.secondary_lane_type == secondary_lane_type,
                            WaitTime.update_time.isnot(None),
                        )
                        .order_by(WaitTime.update_time.desc())
                        .first()
                    )

                    incoming_update_time = parse_update_time(
                        secondary_container.findtext("update_time"),
                        port_date,
                    )

                    if existing_wait_time is not None and is_within_one_hour(
                        incoming_update_time, existing_wait_time.update_time
                    ):
                        action = "skipped"
                    else:
                        wait_time = WaitTime(
                            border_port_id=border_port.id,
                            operational_status=operational_status,
                            update_time=incoming_update_time,
                            delay_minutes=parse_optional_int(secondary_container.findtext("delay_minutes")),
                            lanes_open=parse_optional_int(secondary_container.findtext("lanes_open")),
                            primary_lane_type=primary_lane_type,
                            secondary_lane_type=secondary_lane_type,
                        )
                        session.add(wait_time)
                        action = "created"

                    created_wait_times.append(
                        {
                            "port_number": port_number,
                            "primary_lane_type": primary_lane_type.value,
                            "secondary_lane_type": secondary_lane_type.value,
                            "action": action,
                        }
                    )

        session.add(
            BorderTimeImport(
                import_time=datetime.now(timezone.utc),
                borderport_total=len(root.findall("port")),
                waittime_total=len(created_wait_times),
            )
        )

        session.commit()

    return {
        "name": name,
        "ports_found": len(root.findall("port")),
        "created_ports": created_ports,
        "created_wait_times": created_wait_times,
    }
