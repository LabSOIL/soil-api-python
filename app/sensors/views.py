from app.sensors.models import (
    SensorRead,
    Sensor,
    SensorCreate,
    SensorUpdate,
)
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from sqlmodel import select
from uuid import UUID
from app.crud import CRUD
from app.plots.models import Plot
from app.sensors.services import (
    get_count,
    get_data,
    get_one,
    create_one,
    update_one,
    crud,
)

router = APIRouter()


@router.get("/{sensor_id}", response_model=SensorRead)
async def get_sensor(
    obj: CRUD = Depends(get_one),
) -> SensorRead:
    """Get a sensor by id"""

    return obj


@router.get("", response_model=list[SensorRead])
async def get_all_sensors(
    response: Response,
    sensors: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[SensorRead]:
    """Get all Sensor data"""

    return sensors


@router.post("", response_model=SensorRead)
async def create_sensor(
    sensor: SensorRead = Depends(create_one),
) -> SensorRead:
    """Creates a sensor data record"""

    return sensor


@router.put("/{sensor_id}", response_model=SensorRead)
async def update_sensor(
    sensor: SensorRead = Depends(update_one),
) -> SensorRead:
    """Update a sensor by id"""

    return sensor


@router.delete("/batch", response_model=list[str])
async def delete_batch(
    ids: list[UUID],
    session: AsyncSession = Depends(get_session),
) -> list[str]:
    """Delete by a list of ids"""

    for id in ids:
        obj = await crud.get_model_by_id(model_id=id, session=session)
        if obj:
            await session.delete(obj)

    await session.commit()

    return [str(obj_id) for obj_id in ids]


@router.delete("/{sensor_id}")
async def delete_sensor(
    sensor: SensorRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a sensor by id"""

    await session.delete(sensor)
    await session.commit()

    return {"ok": True}
