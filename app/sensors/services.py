from app.sensors.models import (
    SensorRead,
    Sensor,
    SensorCreate,
    SensorUpdate,
    SensorDataCreate,
    SensorData,
)
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from sqlmodel import select, delete
from uuid import UUID
from app.crud import CRUD
from app.utils.funcs import decode_base64
import csv
from datetime import datetime

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


def ingest_csv_data(
    sensor_data: bytes,
    sensor_id: UUID,
) -> list[SensorData]:

    lines = sensor_data.decode("utf-8").split("\n")
    objs = []
    for line in lines:
        if line:
            data = line.split(";")

            time_utc = datetime.strptime(data[1], "%Y.%m.%d %H:%M")
            sensor_data_obj = SensorData(
                instrument_seq=int(data[0]),
                time_utc=time_utc,
                time_zone=int(data[2]),
                temperature_1=float(data[3]),
                temperature_2=float(data[4]),
                temperature_3=float(data[5]),
                temperature_average=(
                    (float(data[3]) + float(data[4]) + float(data[5])) / 3
                ),
                soil_moisture_count=int(data[6]),
                shake=int(data[7]),
                error_flat=int(data[8]),
                sensor_id=sensor_id,
            )

            objs.append(sensor_data_obj)

    return objs


async def create_one(
    sensor: SensorCreate,
    session: AsyncSession = Depends(get_session),
) -> Sensor:

    sensor_obj = Sensor.model_validate(sensor)

    session.add(sensor_obj)
    await session.commit()
    await session.refresh(sensor_obj)

    if sensor.data_base64:
        # Decode Base64 CSV data and add it to SensorData table
        sensor_data, filetype = decode_base64(sensor.data_base64)
        if filetype != "csv":
            raise HTTPException(
                status_code=400,
                detail="Only CSV files are supported",
            )

        data_objs = ingest_csv_data(sensor_data, sensor_obj.id)
        session.add_all(data_objs)

    await session.commit()
    await session.refresh(sensor_obj)

    return sensor_obj


async def update_one(
    sensor_update: SensorUpdate,
    sensor: SensorRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> SensorRead:

    update_data = sensor_update.model_dump(exclude_unset=True)

    sensor.sqlmodel_update(update_data)
    session.add(sensor)

    if sensor_update.data_base64:
        # Decode Base64 CSV data and add it to SensorData table
        sensor_data, filetype = decode_base64(sensor_update.data_base64)
        if filetype != "csv":
            raise HTTPException(
                status_code=400,
                detail="Only CSV files are supported",
            )

        # Delete first all the data for this sensor
        query = select(SensorData).where(SensorData.sensor_id == sensor.id)
        res = await session.exec(query)
        res_objs = res.all()

        for obj in res_objs:
            await session.delete(obj)

        await session.commit()

        # Now add the new data
        data_objs = ingest_csv_data(sensor_data, sensor.id)
        session.add_all(data_objs)

    await session.commit()
    await session.refresh(sensor)

    return sensor
