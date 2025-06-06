import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from .database import Base


class Inventory(Base):
    __tablename__ = "inventories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id = Column(UUID(as_uuid=True), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", name="uix_wh_prod"),
    )


class Movement(Base):
    __tablename__ = "movements"
    movement_id = Column(UUID(as_uuid=True), primary_key=True)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    source_warehouse_id = Column(UUID(as_uuid=True), nullable=True)
    departure_time = Column(DateTime, nullable=True)
    quantity_departure = Column(Integer, nullable=True)
    destination_warehouse_id = Column(UUID(as_uuid=True), nullable=True)
    arrival_time = Column(DateTime, nullable=True)
    quantity_arrival = Column(Integer, nullable=True)
