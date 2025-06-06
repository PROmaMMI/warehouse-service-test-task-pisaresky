from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from datetime import datetime

from . import models


def get_or_create_inventory(
    db: Session, warehouse_id: str, product_id: str
) -> models.Inventory:
    try:
        inv = (
            db.query(models.Inventory)
            .filter_by(warehouse_id=warehouse_id, product_id=product_id)
            .one()
        )
    except NoResultFound:
        inv = models.Inventory(
            warehouse_id=warehouse_id, product_id=product_id, quantity=0
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
    return inv


def update_inventory_on_departure(
    db: Session, warehouse_id: str, product_id: str, quantity_departure: int
) -> None:
    inv = get_or_create_inventory(db, warehouse_id, product_id)
    new_q = inv.quantity - quantity_departure
    if new_q < 0:
        raise ValueError(
            f"Недостаточно товара для отправки {quantity_departure} с склада {warehouse_id} для товара {product_id}. Сейчас: {inv.quantity}"
        )
    inv.quantity = new_q
    db.add(inv)
    db.commit()


def update_inventory_on_arrival(
    db: Session, warehouse_id: str, product_id: str, quantity_arrival: int
) -> None:
    inv = get_or_create_inventory(db, warehouse_id, product_id)
    inv.quantity += quantity_arrival
    db.add(inv)
    db.commit()


def get_inventory(
    db: Session, warehouse_id: str, product_id: str
) -> models.Inventory:

    inv = (
        db.query(models.Inventory)
        .filter_by(warehouse_id=warehouse_id, product_id=product_id)
        .one_or_none()
    )
    if inv is None:
        return models.Inventory(
            warehouse_id=warehouse_id, product_id=product_id, quantity=0
        )
    return inv


def get_movement_by_id(db: Session, movement_id: str) -> models.Movement:
    return db.query(models.Movement).filter_by(movement_id=movement_id).one_or_none()


def create_or_update_movement(
    db: Session,
    movement_id: str,
    product_id: str,
    event: str,
    warehouse_id: str,
    timestamp: datetime,
    quantity: int,
) -> models.Movement:
    mv = get_movement_by_id(db, movement_id)
    if mv is None:
        mv = models.Movement(movement_id=movement_id, product_id=product_id)
        db.add(mv)

    if event == "departure":
        mv.source_warehouse_id = warehouse_id
        mv.departure_time = timestamp
        mv.quantity_departure = quantity
    elif event == "arrival":
        mv.destination_warehouse_id = warehouse_id
        mv.arrival_time = timestamp
        mv.quantity_arrival = quantity
    else:
        raise ValueError(f"Неизвестный тип события: {event}")

    db.commit()
    db.refresh(mv)
    return mv
