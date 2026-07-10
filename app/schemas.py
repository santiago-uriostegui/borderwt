from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.database import PrimaryLaneType, SecondaryLaneType


class BorderPortCreate(BaseModel):
    port_number: str
    border: Optional[str] = None
    port_name: Optional[str] = None
    hours: Optional[str] = None
    port_status: Optional[str] = None


class BorderPortRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    port_number: str
    border: Optional[str] = None
    port_name: Optional[str] = None
    hours: Optional[str] = None
    port_status: Optional[str] = None


class WaitTimeCreate(BaseModel):
    border_port_id: int
    primary_lane_type: PrimaryLaneType
    secondary_lane_type: SecondaryLaneType
    operational_status: Optional[str] = None
    update_time: Optional[datetime] = None
    delay_minutes: Optional[int] = None
    lanes_open: Optional[int] = None


class WaitTimeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    border_port_id: Optional[int] = None
    operational_status: Optional[str] = None
    update_time: Optional[datetime] = None
    delay_minutes: Optional[int] = None
    lanes_open: Optional[int] = None
    primary_lane_type: Optional[PrimaryLaneType] = None
    secondary_lane_type: Optional[SecondaryLaneType] = None


class BorderTimeImportCreate(BaseModel):
    borderport_total: int
    waittime_total: int
    import_time: Optional[datetime] = None


class BorderTimeImportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    import_time: datetime
    borderport_total: int
    waittime_total: int
