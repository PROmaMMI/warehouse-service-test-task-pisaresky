import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json
from . import models, schemas, crud
from .database import SessionLocal, engine
import asyncio
models.Base.metadata.create_all(bind=engine)
from typing import Optional
import aioredis
from dotenv import load_dotenv
from prometheus_fastapi_instrumentator import Instrumentator

load_dotenv()

app = FastAPI(
    title="Сервис мониторинга складов",
    version="1.0",
    openapi_url="/api/openapi.json",
    docs_url="/docs",
)

Instrumentator().instrument(app).expose(app)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis: Optional[aioredis.Redis] = None

@app.on_event("startup")
async def startup_event():
    global redis
    redis = await aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    if redis:
        await redis.close()
@app.get(
    "/api/movements/{movement_id}",
    response_model=schemas.MovementResponse,
    summary="Информация о перемещении по ID",
)
def read_movement(movement_id: str, db: Session = Depends(get_db)):
    mv = crud.get_movement_by_id(db, movement_id)
    if not mv:
        raise HTTPException(status_code=404, detail="Движение не найдено")

    time_diff = None
    if mv.departure_time and mv.arrival_time:
        delta = mv.arrival_time - mv.departure_time
        time_diff = int(delta.total_seconds())

    qty_diff = None
    if mv.quantity_departure is not None and mv.quantity_arrival is not None:
        qty_diff = mv.quantity_arrival - mv.quantity_departure

    return schemas.MovementResponse(
        movement_id=mv.movement_id,
        product_id=mv.product_id,
        source_warehouse_id=mv.source_warehouse_id,
        departure_time=mv.departure_time,
        destination_warehouse_id=mv.destination_warehouse_id,
        arrival_time=mv.arrival_time,
        time_diff_seconds=time_diff,
        quantity_departure=mv.quantity_departure,
        quantity_arrival=mv.quantity_arrival,
        quantity_diff=qty_diff,
    )


@app.get(
    "/api/warehouses/{warehouse_id}/products/{product_id}",
    response_model=schemas.InventoryResponse,
    summary="Текущий запас товара на складе",
)
def read_inventory(
    warehouse_id: str, product_id: str, db: Session = Depends(get_db)
):
    inv = crud.get_inventory(db, warehouse_id, product_id)
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found"
        )
    return schemas.InventoryResponse(
        warehouse_id=warehouse_id,
        product_id=product_id,
        quantity=inv.quantity,
    )
