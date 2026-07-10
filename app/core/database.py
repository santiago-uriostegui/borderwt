from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, create_engine
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class BorderTimeImport(Base):
    __tablename__ = "border_time_imports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    import_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    borderport_total: Mapped[int]
    waittime_total: Mapped[int]


class BorderPort(Base):
    __tablename__ = "border_ports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    port_number: Mapped[str] = mapped_column(unique=True, index=True)
    border: Mapped[Optional[str]]
    port_name: Mapped[Optional[str]]
    hours: Mapped[Optional[str]]
    port_status: Mapped[Optional[str]]

    wait_times: Mapped[list["WaitTime"]] = relationship(back_populates="border_port")


class PrimaryLaneType(str, PyEnum):
    COMMERCIAL_LANE = "commercial_vehicle_lanes"
    VEHICLE_LANE = "passenger_vehicle_lanes"
    PEDESTRIAN_LANE = "pedestrian_lanes"


class SecondaryLaneType(str, PyEnum):
    STANDARD_LANE = "standard_lanes"
    READY_LANE = "ready_lanes"
    NEXUS_LANE = "NEXUS_SENTRI_lanes"
    FAST_LANE = "FAST_lanes"


class WaitTime(Base):
    __tablename__ = "wait_times"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    border_port_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("border_ports.id"), index=True
    )
    operational_status: Mapped[Optional[str]]
    update_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delay_minutes: Mapped[Optional[int]]
    lanes_open: Mapped[Optional[int]]
    primary_lane_type: Mapped[Optional[PrimaryLaneType]] = mapped_column(
        SQLAlchemyEnum(PrimaryLaneType, native_enum=False)
    )
    secondary_lane_type: Mapped[Optional[SecondaryLaneType]] = mapped_column(
        SQLAlchemyEnum(SecondaryLaneType, native_enum=False)
    )

    border_port: Mapped[Optional["BorderPort"]] = relationship(
        back_populates="wait_times"
    )
