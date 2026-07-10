from datetime import datetime, timezone
from typing import List

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.celery_app import import_border_wait_times
from app.database import (
    BorderPort,
    BorderTimeImport,
    PrimaryLaneType,
    SecondaryLaneType,
    SessionLocal,
    WaitTime,
)
from app.schemas import (
    BorderPortCreate,
    BorderPortNameRead,
    BorderPortPrimaryLaneTypeRead,
    BorderPortRead,
    BorderPortSecondaryLaneTypeRead,
    BorderTimeImportCreate,
    BorderTimeImportRead,
    WaitTimeCreate,
    WaitTimeHistoryRead,
    WaitTimeRead,
)

app = FastAPI(title="BorderWT API", version="0.1.0")


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
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> JSONResponse:
    return JSONResponse(status_code=204, content=None)


@app.post("/tasks/sample")
def trigger_sample_task(name: str = "world") -> dict[str, str]:
    task = import_border_wait_times.delay(name)
    return {"task_id": task.id, "status": "queued"}


@app.post("/border-ports", response_model=BorderPortRead)
def create_border_port(
    payload: BorderPortCreate, db: Session = Depends(get_db)
) -> BorderPort:
    port = BorderPort(**payload.model_dump())
    db.add(port)
    db.commit()
    db.refresh(port)
    return port


@app.get("/border-ports", response_model=List[BorderPortRead])
def list_border_ports(db: Session = Depends(get_db)) -> List[BorderPort]:
    return db.query(BorderPort).all()


@app.get("/border-ports/borders", response_model=List[str])
def list_unique_borders(db: Session = Depends(get_db)) -> List[str]:
    borders = (
        db.query(BorderPort.border)
        .filter(BorderPort.border.isnot(None))
        .distinct()
        .all()
    )
    return sorted(border for (border,) in borders)


@app.get(
    "/border-ports/{border}/port-names",
    response_model=List[BorderPortNameRead],
)
def list_port_names_by_border(
    border: str, db: Session = Depends(get_db)
) -> List[BorderPort]:
    return (
        db.query(BorderPort)
        .filter(
            BorderPort.border == border, BorderPort.port_name.isnot(None)
        )
        .order_by(BorderPort.port_name)
        .all()
    )


@app.get(
    "/border-ports/{border_port_id}/primary-lane-types",
    response_model=List[BorderPortPrimaryLaneTypeRead],
)
def list_primary_lane_types_by_border_port(
    border_port_id: int, db: Session = Depends(get_db)
) -> List[BorderPortPrimaryLaneTypeRead]:
    lane_types = (
        db.query(WaitTime.primary_lane_type)
        .filter(
            WaitTime.border_port_id == border_port_id,
            WaitTime.primary_lane_type.isnot(None),
        )
        .distinct()
        .all()
    )
    return sorted(
        (
            BorderPortPrimaryLaneTypeRead(
                border_port_id=border_port_id, primary_lane_type=lane_type
            )
            for (lane_type,) in lane_types
        ),
        key=lambda item: item.primary_lane_type.value,
    )


@app.get(
    "/border-ports/{border_port_id}/primary-lane-types/{primary_lane_type}"
    "/secondary-lane-types",
    response_model=List[BorderPortSecondaryLaneTypeRead],
)
def list_secondary_lane_types_by_border_port_and_primary_lane_type(
    border_port_id: int,
    primary_lane_type: PrimaryLaneType,
    db: Session = Depends(get_db),
) -> List[BorderPortSecondaryLaneTypeRead]:
    secondary_lane_types = (
        db.query(WaitTime.secondary_lane_type)
        .filter(
            WaitTime.border_port_id == border_port_id,
            WaitTime.primary_lane_type == primary_lane_type,
            WaitTime.secondary_lane_type.isnot(None),
        )
        .distinct()
        .all()
    )
    return sorted(
        (
            BorderPortSecondaryLaneTypeRead(
                border_port_id=border_port_id,
                primary_lane_type=primary_lane_type,
                secondary_lane_type=secondary_lane_type,
            )
            for (secondary_lane_type,) in secondary_lane_types
        ),
        key=lambda item: item.secondary_lane_type.value,
    )


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
    wait_times = (
        db.query(WaitTime)
        .filter(
            WaitTime.border_port_id == border_port_id,
            WaitTime.primary_lane_type == primary_lane_type,
            WaitTime.secondary_lane_type == secondary_lane_type,
            WaitTime.update_time.isnot(None),
        )
        .order_by(WaitTime.update_time.desc())
        .all()
    )
    newest = wait_times[0] if wait_times else None
    return WaitTimeHistoryRead(
        operational_status=newest.operational_status if newest else None,
        lanes_open=newest.lanes_open if newest else None,
        primary_lane_type=primary_lane_type,
        secondary_lane_type=secondary_lane_type,
        wait_times=wait_times,
    )


@app.post("/wait-times", response_model=WaitTimeRead)
def create_wait_time(
    payload: WaitTimeCreate, db: Session = Depends(get_db)
) -> WaitTime:
    wait_time = WaitTime(**payload.model_dump())
    db.add(wait_time)
    db.commit()
    db.refresh(wait_time)
    return wait_time


@app.get("/wait-times", response_model=List[WaitTimeRead])
def list_wait_times(db: Session = Depends(get_db)) -> List[WaitTime]:
    return db.query(WaitTime).all()


@app.post("/border-time-imports", response_model=BorderTimeImportRead)
def create_border_time_import(
    payload: BorderTimeImportCreate, db: Session = Depends(get_db)
) -> BorderTimeImport:
    border_time_import = BorderTimeImport(
        import_time=payload.import_time or datetime.now(timezone.utc),
        borderport_total=payload.borderport_total,
        waittime_total=payload.waittime_total,
    )
    db.add(border_time_import)
    db.commit()
    db.refresh(border_time_import)
    return border_time_import


@app.get("/border-time-imports", response_model=List[BorderTimeImportRead])
def list_border_time_imports(
    db: Session = Depends(get_db),
) -> List[BorderTimeImport]:
    return db.query(BorderTimeImport).all()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
