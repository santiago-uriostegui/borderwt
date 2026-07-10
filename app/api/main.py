from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import Pagination, pagination_params
from app.core.config import get_settings
from app.core.database import (
    BorderPort,
    BorderTimeImport,
    PrimaryLaneType,
    SecondaryLaneType,
    SessionLocal,
    WaitTime,
)
from app.core.logging import get_logger
from app.repositories import border_ports, border_time_imports, wait_times
from app.schemas.schemas import (
    BorderPortCreate,
    BorderPortNameRead,
    BorderPortPrimaryLaneTypeRead,
    BorderPortRead,
    BorderPortSecondaryLaneTypeRead,
    BorderTimeImportCreate,
    BorderTimeImportRead,
    WaitTimeCreate,
    WaitTimeHistoryEntry,
    WaitTimeHistoryRead,
    WaitTimeRead,
)
from app.services.celery_app import import_border_wait_times

logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(title="BorderWT API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to BorderWT API"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check database probe failed")
        return {"status": "error", "database": "unreachable"}
    return {"status": "ok", "database": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> JSONResponse:
    return JSONResponse(status_code=204, content=None)


@app.post("/tasks/import-border-wait-times")
def trigger_import_task() -> dict[str, str]:
    task = import_border_wait_times.delay()
    return {"task_id": task.id, "status": "queued"}


@app.post("/border-ports", response_model=BorderPortRead)
def create_border_port(
    payload: BorderPortCreate, db: Session = Depends(get_db)
) -> BorderPort:
    return border_ports.create(db, payload)


@app.get("/border-ports", response_model=list[BorderPortRead])
def list_border_ports(
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(pagination_params),
) -> list[BorderPort]:
    return border_ports.list_all(db, limit=pagination.limit, offset=pagination.offset)


@app.get("/border-ports/borders", response_model=list[str])
def list_unique_borders(db: Session = Depends(get_db)) -> list[str]:
    return border_ports.list_unique_borders(db)


@app.get(
    "/border-ports/{border}/port-names",
    response_model=list[BorderPortNameRead],
)
def list_port_names_by_border(
    border: str, db: Session = Depends(get_db)
) -> list[BorderPort]:
    return border_ports.list_port_names_by_border(db, border)


@app.get(
    "/border-ports/{border_port_id}/primary-lane-types",
    response_model=list[BorderPortPrimaryLaneTypeRead],
)
def list_primary_lane_types_by_border_port(
    border_port_id: int, db: Session = Depends(get_db)
) -> list[BorderPortPrimaryLaneTypeRead]:
    return wait_times.list_primary_lane_types(db, border_port_id)


@app.get(
    "/border-ports/{border_port_id}/primary-lane-types/{primary_lane_type}"
    "/secondary-lane-types",
    response_model=list[BorderPortSecondaryLaneTypeRead],
)
def list_secondary_lane_types_by_border_port_and_primary_lane_type(
    border_port_id: int,
    primary_lane_type: PrimaryLaneType,
    db: Session = Depends(get_db),
) -> list[BorderPortSecondaryLaneTypeRead]:
    return wait_times.list_secondary_lane_types(db, border_port_id, primary_lane_type)


@app.get(
    "/border-ports/{border_port_id}/primary-lane-types/{primary_lane_type}"
    "/secondary-lane-types/{secondary_lane_type}/wait-times",
    response_model=WaitTimeHistoryRead,
)
def list_wait_times_by_border_port_and_lane_types(
    border_port_id: int,
    primary_lane_type: PrimaryLaneType,
    secondary_lane_type: SecondaryLaneType,
    db: Session = Depends(get_db),
) -> WaitTimeHistoryRead:
    history = wait_times.list_history(
        db, border_port_id, primary_lane_type, secondary_lane_type
    )
    newest = history[0] if history else None
    return WaitTimeHistoryRead(
        operational_status=newest.operational_status if newest else None,
        current_wait=newest.delay_minutes if newest else None,
        lanes_open=newest.lanes_open if newest else None,
        primary_lane_type=primary_lane_type,
        secondary_lane_type=secondary_lane_type,
        wait_times=[WaitTimeHistoryEntry.model_validate(entry) for entry in history],
    )


@app.post("/wait-times", response_model=WaitTimeRead)
def create_wait_time(
    payload: WaitTimeCreate, db: Session = Depends(get_db)
) -> WaitTime:
    return wait_times.create(db, payload)


@app.get("/wait-times", response_model=list[WaitTimeRead])
def list_wait_times(
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(pagination_params),
) -> list[WaitTime]:
    return wait_times.list_all(db, limit=pagination.limit, offset=pagination.offset)


@app.post("/border-time-imports", response_model=BorderTimeImportRead)
def create_border_time_import(
    payload: BorderTimeImportCreate, db: Session = Depends(get_db)
) -> BorderTimeImport:
    return border_time_imports.create(db, payload)


@app.get("/border-time-imports", response_model=list[BorderTimeImportRead])
def list_border_time_imports(
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(pagination_params),
) -> list[BorderTimeImport]:
    return border_time_imports.list_all(
        db, limit=pagination.limit, offset=pagination.offset
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
