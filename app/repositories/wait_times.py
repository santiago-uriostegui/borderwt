from sqlalchemy.orm import Session

from app.core.database import PrimaryLaneType, SecondaryLaneType, WaitTime
from app.schemas.schemas import (
    BorderPortPrimaryLaneTypeRead,
    BorderPortSecondaryLaneTypeRead,
    WaitTimeCreate,
)


def create(db: Session, payload: WaitTimeCreate) -> WaitTime:
    wait_time = WaitTime(**payload.model_dump())
    db.add(wait_time)
    db.commit()
    db.refresh(wait_time)
    return wait_time


def list_all(db: Session, *, limit: int, offset: int) -> list[WaitTime]:
    return db.query(WaitTime).order_by(WaitTime.id).offset(offset).limit(limit).all()


def list_primary_lane_types(
    db: Session, border_port_id: int
) -> list[BorderPortPrimaryLaneTypeRead]:
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


def list_secondary_lane_types(
    db: Session, border_port_id: int, primary_lane_type: PrimaryLaneType
) -> list[BorderPortSecondaryLaneTypeRead]:
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


def list_history(
    db: Session,
    border_port_id: int,
    primary_lane_type: PrimaryLaneType,
    secondary_lane_type: SecondaryLaneType,
) -> list[WaitTime]:
    return (
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
