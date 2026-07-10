def create_port(client, port_number="111111"):
    response = client.post(
        "/border-ports",
        json={"port_number": port_number, "border": "Mexico", "port_name": "Tecate"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def create_wait_time(client, border_port_id, **overrides):
    payload = {
        "border_port_id": border_port_id,
        "primary_lane_type": "passenger_vehicle_lanes",
        "secondary_lane_type": "standard_lanes",
        "operational_status": "no delay",
        "delay_minutes": 5,
        "lanes_open": 2,
    }
    payload.update(overrides)
    response = client.post("/wait-times", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_and_list_wait_times(client):
    border_port_id = create_port(client)
    created = create_wait_time(client, border_port_id)
    assert created["delay_minutes"] == 5
    assert created["primary_lane_type"] == "passenger_vehicle_lanes"

    response = client.get("/wait-times")
    assert response.status_code == 200
    assert any(w["id"] == created["id"] for w in response.json())


def test_wait_times_pagination(client):
    border_port_id = create_port(client)
    for minutes in (1, 2, 3):
        create_wait_time(client, border_port_id, delay_minutes=minutes)

    page = client.get("/wait-times", params={"limit": 2, "offset": 1})
    assert response_delays(page) == [2, 3]


def response_delays(response):
    return [w["delay_minutes"] for w in response.json()]


def test_list_primary_and_secondary_lane_types(client):
    border_port_id = create_port(client)
    create_wait_time(
        client,
        border_port_id,
        primary_lane_type="passenger_vehicle_lanes",
        secondary_lane_type="standard_lanes",
    )
    create_wait_time(
        client,
        border_port_id,
        primary_lane_type="passenger_vehicle_lanes",
        secondary_lane_type="ready_lanes",
    )

    primary_response = client.get(f"/border-ports/{border_port_id}/primary-lane-types")
    assert primary_response.status_code == 200
    assert [entry["primary_lane_type"] for entry in primary_response.json()] == [
        "passenger_vehicle_lanes"
    ]

    secondary_response = client.get(
        f"/border-ports/{border_port_id}/primary-lane-types/"
        "passenger_vehicle_lanes/secondary-lane-types"
    )
    assert secondary_response.status_code == 200
    secondary_types = sorted(
        entry["secondary_lane_type"] for entry in secondary_response.json()
    )
    assert secondary_types == ["ready_lanes", "standard_lanes"]


def test_wait_time_history_reports_newest_first(client):
    border_port_id = create_port(client)
    create_wait_time(
        client,
        border_port_id,
        operational_status="no delay",
        delay_minutes=5,
        update_time="2026-07-10T08:00:00Z",
    )
    create_wait_time(
        client,
        border_port_id,
        operational_status="delay",
        delay_minutes=30,
        update_time="2026-07-10T09:00:00Z",
    )

    response = client.get(
        f"/border-ports/{border_port_id}/primary-lane-types/"
        "passenger_vehicle_lanes/secondary-lane-types/standard_lanes/wait-times"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["current_wait"] == 30
    assert body["operational_status"] == "delay"
    assert len(body["wait_times"]) == 2
    assert body["wait_times"][0]["delay_minutes"] == 30
    assert body["wait_times"][1]["delay_minutes"] == 5


def test_wait_time_history_empty_when_no_data(client):
    border_port_id = create_port(client)

    response = client.get(
        f"/border-ports/{border_port_id}/primary-lane-types/"
        "passenger_vehicle_lanes/secondary-lane-types/standard_lanes/wait-times"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["current_wait"] is None
    assert body["operational_status"] is None
    assert body["wait_times"] == []
