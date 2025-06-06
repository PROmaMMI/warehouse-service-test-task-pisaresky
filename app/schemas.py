from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class MovementResponse(BaseModel):
    movement_id: UUID
    product_id: UUID
    source_warehouse_id: Optional[UUID]
    departure_time: Optional[datetime]
    destination_warehouse_id: Optional[UUID]
    arrival_time: Optional[datetime]
    time_diff_seconds: Optional[int] = Field(
        None, description="Разница во времени (в секундах) между отправкой и приёмом, если оба есть"
    )
    quantity_departure: Optional[int]
    quantity_arrival: Optional[int]
    quantity_diff: Optional[int] = Field(
        None, description="quantity_arrival - quantity_departure, если оба есть"
    )

    class Config:
        orm_mode = True


class InventoryResponse(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    quantity: int

    class Config:
        orm_mode = True
