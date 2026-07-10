from app.api.main import app, get_db


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to BorderWT API"}


def test_favicon(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 204


def test_health_check_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_check_reports_database_error(client):
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise RuntimeError("connection refused")

    def override_get_db():
        yield BrokenSession()

    previous_override = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides[get_db] = previous_override

    assert response.status_code == 200
    assert response.json() == {"status": "error", "database": "unreachable"}


def test_trigger_import_task(client, monkeypatch):
    class FakeTask:
        id = "fake-task-id"

    monkeypatch.setattr(
        "app.api.main.import_border_wait_times.delay", lambda: FakeTask()
    )
    response = client.post("/tasks/import-border-wait-times")
    assert response.status_code == 200
    assert response.json() == {"task_id": "fake-task-id", "status": "queued"}
