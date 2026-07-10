from sqlalchemy.orm import Session

from app.core.database import BorderPort
from app.schemas.schemas import BorderPortCreate


def create(db: Session, payload: BorderPortCreate) -> BorderPort:
    port = BorderPort(**payload.model_dump())
    db.add(port)
    db.commit()
    db.refresh(port)
    return port


def list_all(db: Session, *, limit: int, offset: int) -> list[BorderPort]:
    return (
        db.query(BorderPort).order_by(BorderPort.id).offset(offset).limit(limit).all()
    )


def list_unique_borders(db: Session) -> list[str]:
    borders = (
        db.query(BorderPort.border)
        .filter(BorderPort.border.isnot(None))
        .distinct()
        .all()
    )
    return sorted(border for (border,) in borders)


def list_port_names_by_border(db: Session, border: str) -> list[BorderPort]:
    return (
        db.query(BorderPort)
        .filter(BorderPort.border == border, BorderPort.port_name.isnot(None))
        .order_by(BorderPort.port_name)
        .all()
    )
