# BorderWT

A FastAPI + Celery service that ingests U.S. CBP border wait time data (from
`https://bwt.cbp.gov/xml/bwt.xml`) into PostgreSQL and exposes it via a REST API.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start Redis (if not already running):
   ```bash
   redis-server
   ```
4. Start PostgreSQL and run migrations (see [PostgreSQL](#postgresql) below).
5. Start the FastAPI server:
   ```bash
   uvicorn app.api.main:app --reload
   ```
6. Start a Celery worker in a second terminal:
   ```bash
   celery -A app.services.celery_app worker --loglevel=info
   ```
7. Start Celery beat in a third terminal, so the import task runs automatically
   (every 5 minutes, see `beat_schedule` in `app/services/celery_app.py`):
   ```bash
   celery -A app.services.celery_app beat --loglevel=info
   ```

## PostgreSQL

This project uses PostgreSQL via SQLAlchemy. By default it expects a local database
named `borderwt` with user `devs` and no password.

If you do not already have PostgreSQL running locally, start it with PostgreSQL.app
or Homebrew, then create the database:

```bash
createdb -U devs borderwt
```

You can override the connection string with:

```bash
export DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/dbname"
```

### Migrations

Schema is managed entirely through Alembic — the app does not auto-create tables.
After creating the database, bring it up to date with:

```bash
alembic upgrade head
```

Run this again any time you pull changes that include a new migration under
`alembic/versions/`.

### Example requests

Request/response bodies are validated with Pydantic models (see `app/schemas/schemas.py`).
Create endpoints take a JSON body rather than query params.

Create a border port:
```bash
curl -X POST "http://127.0.0.1:8000/border-ports" \
  -H "Content-Type: application/json" \
  -d '{"port_number": "250501", "border": "Mexico", "port_name": "Tecate"}'
```

List border ports:
```bash
curl http://127.0.0.1:8000/border-ports
```

Create a wait time (`primary_lane_type` / `secondary_lane_type` must match the
`PrimaryLaneType` / `SecondaryLaneType` enum values in `app/core/database.py`):
```bash
curl -X POST "http://127.0.0.1:8000/wait-times" \
  -H "Content-Type: application/json" \
  -d '{"border_port_id": 1, "primary_lane_type": "commercial_vehicle_lanes", "secondary_lane_type": "standard_lanes", "operational_status": "no delay", "delay_minutes": 5, "lanes_open": 2}'
```

List wait times:
```bash
curl http://127.0.0.1:8000/wait-times
```

Create a border time import log entry (`import_time` defaults to now if omitted):
```bash
curl -X POST "http://127.0.0.1:8000/border-time-imports" \
  -H "Content-Type: application/json" \
  -d '{"borderport_total": 83, "waittime_total": 178}'
```

List border time import log entries:
```bash
curl http://127.0.0.1:8000/border-time-imports
```

### Trigger the border wait time import task

The task fetches the CBP XML feed, upserts `border_ports`, and records one
`wait_times` row per port/lane combination. If an existing row's `update_time`
is less than an hour older than the incoming value, it's skipped instead of
duplicated. Each run also logs a summary row to `border_time_imports`.

- Via API:
  ```bash
  curl -X POST "http://127.0.0.1:8000/tasks/import-border-wait-times"
  ```

- Via Python:
  ```bash
  python -c "from app.services.celery_app import import_border_wait_times; print(import_border_wait_times.delay().id)"
  ```

Open http://127.0.0.1:8000/docs for the interactive API docs.
