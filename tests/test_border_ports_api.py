def create_port(client, port_number, border="Mexico", port_name="Test Port"):
    response = client.post(
        "/border-ports",
        json={"port_number": port_number, "border": border, "port_name": port_name},
    )
    assert response.status_code == 200
    return response.json()


def test_create_and_get_border_port(client):
    created = create_port(client, "111111", border="Mexico", port_name="Tecate")
    assert created["port_number"] == "111111"
    assert created["border"] == "Mexico"
    assert created["port_name"] == "Tecate"
    assert created["id"] is not None

    response = client.get("/border-ports")
    assert response.status_code == 200
    port_numbers = [port["port_number"] for port in response.json()]
    assert "111111" in port_numbers


def test_list_border_ports_pagination(client):
    for number in ("100000", "200000", "300000"):
        create_port(client, number)

    first_page = client.get("/border-ports", params={"limit": 2, "offset": 0})
    second_page = client.get("/border-ports", params={"limit": 2, "offset": 2})

    assert [p["port_number"] for p in first_page.json()] == ["100000", "200000"]
    assert [p["port_number"] for p in second_page.json()] == ["300000"]


def test_list_border_ports_pagination_rejects_out_of_range_params(client):
    assert client.get("/border-ports", params={"limit": 0}).status_code == 422
    assert client.get("/border-ports", params={"limit": 500}).status_code == 422
    assert client.get("/border-ports", params={"offset": -1}).status_code == 422


def test_list_unique_borders(client):
    create_port(client, "100000", border="Mexico")
    create_port(client, "200000", border="Canada")
    create_port(client, "300000", border="Mexico")

    response = client.get("/border-ports/borders")
    assert response.status_code == 200
    assert response.json() == ["Canada", "Mexico"]


def test_list_port_names_by_border(client):
    create_port(client, "100000", border="Mexico", port_name="Zapata")
    create_port(client, "200000", border="Mexico", port_name="Andrade")
    create_port(client, "300000", border="Canada", port_name="Blaine")

    response = client.get("/border-ports/Mexico/port-names")
    assert response.status_code == 200
    names = [entry["port_name"] for entry in response.json()]
    assert names == ["Andrade", "Zapata"]
