from datetime import datetime, timezone
from typing import List

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.celery_app import import_border_wait_times
from app.database import BorderPort, BorderTimeImport, SessionLocal, WaitTime
from app.schemas import (
    BorderPortCreate,
    BorderPortRead,
    BorderTimeImportCreate,
    BorderTimeImportRead,
    WaitTimeCreate,
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
def create_border_port(payload: BorderPortCreate, db: Session = Depends(get_db)) -> BorderPort:
    port = BorderPort(**payload.model_dump())
    db.add(port)
    db.commit()
    db.refresh(port)
    return port


@app.get("/border-ports", response_model=List[BorderPortRead])
def list_border_ports(db: Session = Depends(get_db)) -> List[BorderPort]:
    return db.query(BorderPort).all()


@app.post("/wait-times", response_model=WaitTimeRead)
def create_wait_time(payload: WaitTimeCreate, db: Session = Depends(get_db)) -> WaitTime:
    wait_time = WaitTime(**payload.model_dump())
    db.add(wait_time)
    db.commit()
    db.refresh(wait_time)
    return wait_time


@app.get("/wait-times", response_model=List[WaitTimeRead])
def list_wait_times(db: Session = Depends(get_db)) -> List[WaitTime]:
    return db.query(WaitTime).all()


@app.post("/border-time-imports", response_model=BorderTimeImportRead)
def create_border_time_import(payload: BorderTimeImportCreate, db: Session = Depends(get_db)) -> BorderTimeImport:
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
def list_border_time_imports(db: Session = Depends(get_db)) -> List[BorderTimeImport]:
    return db.query(BorderTimeImport).all()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
