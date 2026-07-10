from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.database import BorderTimeImport
from app.schemas.schemas import BorderTimeImportCreate


def create(db: Session, payload: BorderTimeImportCreate) -> BorderTimeImport:
    border_time_import = BorderTimeImport(
        import_time=payload.import_time or datetime.now(timezone.utc),
        borderport_total=payload.borderport_total,
        waittime_total=payload.waittime_total,
    )
    db.add(border_time_import)
    db.commit()
    db.refresh(border_time_import)
    return border_time_import


def list_all(db: Session, *, limit: int, offset: int) -> list[BorderTimeImport]:
    return (
        db.query(BorderTimeImport)
        .order_by(BorderTimeImport.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
