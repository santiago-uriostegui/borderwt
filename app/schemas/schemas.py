from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.core.database import PrimaryLaneType, SecondaryLaneType


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


class BorderPortNameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    port_name: str


class BorderPortPrimaryLaneTypeRead(BaseModel):
    border_port_id: int
    primary_lane_type: PrimaryLaneType


class BorderPortSecondaryLaneTypeRead(BaseModel):
    border_port_id: int
    primary_lane_type: PrimaryLaneType
    secondary_lane_type: SecondaryLaneType


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


class WaitTimeHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operational_status: Optional[str] = None
    update_time: Optional[datetime] = None
    delay_minutes: Optional[int] = None
    lanes_open: Optional[int] = None


class WaitTimeHistoryRead(BaseModel):
    operational_status: Optional[str] = None
    current_wait: Optional[int] = None
    lanes_open: Optional[int] = None
    primary_lane_type: PrimaryLaneType
    secondary_lane_type: SecondaryLaneType
    wait_times: List[WaitTimeHistoryEntry]


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
