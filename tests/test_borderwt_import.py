import xml.etree.ElementTree as ET
from datetime import datetime

from app.core.database import BorderPort, BorderTimeImport, WaitTime
from app.services.borderwt import import_border_wait_times


def make_port(port_number, date="07/10/2026", **fields):
    port = ET.Element("port")
    ET.SubElement(port, "port_number").text = port_number
    ET.SubElement(port, "date").text = date
    for tag, value in {
        "border": "Mexico",
        "port_name": "Tecate",
        "hours": "24 hours",
        "port_status": "Open",
        **fields,
    }.items():
        ET.SubElement(port, tag).text = value
    return port


def add_lane(
    port, primary, secondary, operational_status, update_time, delay_minutes, lanes_open
):
    primary_el = port.find(primary)
    if primary_el is None:
        primary_el = ET.SubElement(port, primary)
    secondary_el = ET.SubElement(primary_el, secondary)
    ET.SubElement(secondary_el, "operational_status").text = operational_status
    ET.SubElement(secondary_el, "update_time").text = update_time
    ET.SubElement(secondary_el, "delay_minutes").text = str(delay_minutes)
    ET.SubElement(secondary_el, "lanes_open").text = str(lanes_open)
    return secondary_el


def make_root(*ports):
    root = ET.Element("border_wait_time")
    for port in ports:
        root.append(port)
    return root


def run_import(monkeypatch, session_factory, root):
    monkeypatch.setattr("app.services.borderwt.SessionLocal", session_factory)
    monkeypatch.setattr(
        "app.services.borderwt.fetch_border_wait_times_xml", lambda: root
    )
    return import_border_wait_times.run()


def test_import_creates_new_port_and_wait_time(monkeypatch, session_factory):
    port = make_port("111111")
    add_lane(
        port,
        "passenger_vehicle_lanes",
        "standard_lanes",
        "no delay",
        "at 8:00 am PDT",
        5,
        3,
    )
    result = run_import(monkeypatch, session_factory, make_root(port))

    assert result["created_ports"] == ["111111"]
    assert result["created_wait_times"] == [
        {
            "port_number": "111111",
            "primary_lane_type": "passenger_vehicle_lanes",
            "secondary_lane_type": "standard_lanes",
            "action": "created",
        }
    ]

    with session_factory() as session:
        border_port = session.query(BorderPort).filter_by(port_number="111111").one()
        wait_time = (
            session.query(WaitTime).filter_by(border_port_id=border_port.id).one()
        )
        assert wait_time.delay_minutes == 5
        assert wait_time.lanes_open == 3
        assert wait_time.operational_status == "no delay"

        import_log = session.query(BorderTimeImport).one()
        assert import_log.borderport_total == 1
        assert import_log.waittime_total == 1


def test_import_skips_invalid_operational_status(monkeypatch, session_factory):
    port = make_port("222222")
    add_lane(
        port,
        "commercial_vehicle_lanes",
        "ready_lanes",
        "N/A",
        "at 8:00 am PDT",
        0,
        0,
    )
    result = run_import(monkeypatch, session_factory, make_root(port))

    assert result["created_wait_times"] == []

    with session_factory() as session:
        assert session.query(WaitTime).count() == 0


def test_import_skips_duplicate_within_one_hour(monkeypatch, session_factory):
    with session_factory() as session:
        border_port = BorderPort(port_number="333333", border="Mexico")
        session.add(border_port)
        session.flush()
        session.add(
            WaitTime(
                border_port_id=border_port.id,
                operational_status="no delay",
                update_time=datetime(2026, 7, 10, 8, 0),
                delay_minutes=5,
                lanes_open=2,
                primary_lane_type="passenger_vehicle_lanes",
                secondary_lane_type="standard_lanes",
            )
        )
        session.commit()

    port = make_port("333333")
    add_lane(
        port,
        "passenger_vehicle_lanes",
        "standard_lanes",
        "no delay",
        "8:30 am",
        6,
        2,
    )
    result = run_import(monkeypatch, session_factory, make_root(port))

    assert result["created_wait_times"][0]["action"] == "skipped"
    with session_factory() as session:
        assert session.query(WaitTime).count() == 1


def test_import_creates_new_row_when_outside_one_hour_window(
    monkeypatch, session_factory
):
    with session_factory() as session:
        border_port = BorderPort(port_number="444444", border="Mexico")
        session.add(border_port)
        session.flush()
        session.add(
            WaitTime(
                border_port_id=border_port.id,
                operational_status="no delay",
                update_time=datetime(2026, 7, 10, 6, 0),
                delay_minutes=5,
                lanes_open=2,
                primary_lane_type="passenger_vehicle_lanes",
                secondary_lane_type="standard_lanes",
            )
        )
        session.commit()

    port = make_port("444444")
    add_lane(
        port,
        "passenger_vehicle_lanes",
        "standard_lanes",
        "no delay",
        "9:00 am",
        8,
        2,
    )
    result = run_import(monkeypatch, session_factory, make_root(port))

    assert result["created_wait_times"][0]["action"] == "created"
    with session_factory() as session:
        assert session.query(WaitTime).count() == 2
