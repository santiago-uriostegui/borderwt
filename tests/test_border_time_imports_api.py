def test_create_border_time_import_defaults_import_time(client):
    response = client.post(
        "/border-time-imports",
        json={"borderport_total": 10, "waittime_total": 20},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["borderport_total"] == 10
    assert body["waittime_total"] == 20
    assert body["import_time"] is not None


def test_create_border_time_import_preserves_explicit_import_time(client):
    response = client.post(
        "/border-time-imports",
        json={
            "borderport_total": 1,
            "waittime_total": 2,
            "import_time": "2026-07-10T12:00:00Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["import_time"].startswith("2026-07-10T12:00:00")


def test_list_border_time_imports_pagination(client):
    for total in (1, 2, 3):
        client.post(
            "/border-time-imports",
            json={"borderport_total": total, "waittime_total": total},
        )

    response = client.get("/border-time-imports", params={"limit": 2, "offset": 1})
    assert response.status_code == 200
    assert [entry["borderport_total"] for entry in response.json()] == [2, 3]
