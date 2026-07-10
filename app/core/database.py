import os
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://devs@localhost:5432/borderwt",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class BorderTimeImport(Base):
    __tablename__ = "border_time_imports"

    id = Column(Integer, primary_key=True, index=True)
    import_time = Column(DateTime(timezone=True), nullable=False)
    borderport_total = Column(Integer, nullable=False)
    waittime_total = Column(Integer, nullable=False)


class BorderPort(Base):
    __tablename__ = "border_ports"

    id = Column(Integer, primary_key=True, index=True)
    port_number = Column(String, nullable=False, unique=True, index=True)
    border = Column(String, nullable=True)
    port_name = Column(String, nullable=True)
    hours = Column(String, nullable=True)
    port_status = Column(String, nullable=True)


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

    id = Column(Integer, primary_key=True, index=True)
    border_port_id = Column(
        Integer, ForeignKey("border_ports.id"), nullable=True, index=True
    )
    operational_status = Column(String, nullable=True)
    update_time = Column(DateTime(timezone=True), nullable=True)
    delay_minutes = Column(Integer, nullable=True)
    lanes_open = Column(Integer, nullable=True)
    primary_lane_type = Column(
        SQLAlchemyEnum(PrimaryLaneType, native_enum=False), nullable=True
    )
    secondary_lane_type = Column(
        SQLAlchemyEnum(SecondaryLaneType, native_enum=False), nullable=True
    )

    border_port = relationship("BorderPort", back_populates="wait_times")


BorderPort.wait_times = relationship("WaitTime", back_populates="border_port")
