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

crud = CRUD(Sensor, SensorRead, SensorCreate, SensorUpdate)


async def get_count(
    response: Response,
    filter: str = Query(None),
    range: str = Query(None),
    sort: str = Query(None),
    session: AsyncSession = Depends(get_session),
):
    count = await crud.get_total_count(
        response=response,
        sort=sort,
        range=range,
        filter=filter,
        session=session,
    )

    return count


async def get_data(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
):
    res = await crud.get_model_data(
        sort=sort,
        range=range,
        filter=filter,
        session=session,
    )

    return res


async def get_one(
    sensor_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    res = await crud.get_model_by_id(model_id=sensor_id, session=session)

    if not res:
        raise HTTPException(
            status_code=404, detail=f"ID: {sensor_id} not found"
        )
    return res


async def create_one(
    sensor: SensorCreate,
    session: AsyncSession = Depends(get_session),
) -> list[Sensor]:
    # """Create a single gnss

    # To be used in both create one and create many endpoints
    # """

    # gpx_data, filetype = decode_base64(data["data_base64"])
    # if filetype != "gpx":
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Only GPX files are supported",
    #     )
    # parsed_data = parse_gpx(gpx_data)

    # objs = []
    # for row in parsed_data:
    #     obj = GNSS(
    #         latitude=row["latitude"],
    #         longitude=row["longitude"],
    #         elevation_gps=row["elevation"],
    #         time=row["time"],
    #         name=row["name"],
    #         comment=row["comment"],
    #         original_filename=data["filename"],
    #         x=row["x"],
    #         y=row["y"],
    #     )

    #     objs.append(obj)

    # session.add_all(objs)
    # await session.commit()

    # return objs

    sensor_obj = Sensor.model_validate(sensor)

    if sensor.data_base64:
        # Decode Base64 CSV data and add it to SensorData table
        print("Data available!", len(sensor.data_base64))

    session.add(sensor_obj)
    await session.commit()
    await session.refresh(sensor_obj)

    return sensor_obj
