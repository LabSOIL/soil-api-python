from app.instruments.channels.models import (
    InstrumentExperimentChannel,
    InstrumentExperimentChannelRead,
    InstrumentExperimentChannelCreate,
    InstrumentExperimentChannelUpdate,
)
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from uuid import UUID
from app.crud import CRUD
from app.utils.funcs import decode_base64
import csv
import datetime
from app.config import config
from app.instruments.tools import restructure_data_to_column_time

router = APIRouter()
crud = CRUD(
    InstrumentExperimentChannel,
    InstrumentExperimentChannelRead,
    InstrumentExperimentChannelCreate,
    InstrumentExperimentChannelUpdate,
)


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
) -> list[InstrumentExperimentChannel]:

    res = await crud.get_model_data(
        sort=sort,
        range=range,
        filter=filter,
        session=session,
    )

    return res


async def get_one(
    id: UUID,
    session: AsyncSession = Depends(get_session),
) -> InstrumentExperimentChannelRead:

    res = await crud.get_model_by_id(model_id=id, session=session)

    if not res:
        raise HTTPException(status_code=404, detail=f"ID: {id} not found")

    # return res
    read_obj = InstrumentExperimentChannelRead.model_validate(res)

    x = []
    y = []
    for row in res.data:
        # Structure data to be data: {x: [], y: []]}
        x.append(row.time)
        y.append(row.value)

    data = {"x": x, "y": y}

    # data = await restructure_data_to_column_time(res.data, res.channels)
    read_obj.data = data

    return read_obj


async def create_one(
    instrument_experiment: InstrumentExperimentChannelCreate,
    session: AsyncSession = Depends(get_session),
) -> InstrumentExperimentChannel:

    # print(instrument_experiment.data_base64)
    decoded_data, filetype = decode_base64(instrument_experiment.data_base64)
    decoded_data = decoded_data.decode("utf-8").split("\n")
    # print(filetype)
    # print(decoded_data.decode("utf-8"))

    from app.instruments.tools import find_header_start

    # Find the header start
    header_start = find_header_start(decoded_data)

    print(f"Header found at line {header_start}")

    # Import data
    # measurements = {}
    # with open(filename_path, "r") as f:

    reader = csv.reader(decoded_data, delimiter=",")
    lines = list(reader)

    header = lines[header_start]
    print("HEADER:", header)

    # Seek the lines after the header until there is data (sometimes there are
    # empty lines after the header)
    data_start = header_start + 1
    while not lines[data_start]:
        data_start += 1

    # Try to get date from the first line, it is structured like:
    # June 16, 2023   19:48:38
    try:
        date_str = lines[data_start][0].strip()
        date = datetime.datetime.strptime(date_str, "%B %d, %Y %H:%M:%S")
    except ValueError:
        date = None
    # Create an Experiment
    experiment = InstrumentExperimentChannel(
        name=instrument_experiment.name,
        date=date,
        description=instrument_experiment.description,
        filename=instrument_experiment.filename,
        device_filename=instrument_experiment.device_filename,
        data_source=instrument_experiment.data_source,
        instrument_model=instrument_experiment.instrument_model,
        init_e=instrument_experiment.init_e,
        sample_interval=instrument_experiment.sample_interval,
        run_time=instrument_experiment.run_time,
        quiet_time=instrument_experiment.quiet_time,
        sensitivity=instrument_experiment.sensitivity,
        samples=instrument_experiment.samples,
    )

    session.add(experiment)
    await session.commit()
    await session.refresh(experiment)

    """
    Ingest the data, it is structured like this:

    Time/s, i1/A, i2/A, i3/A, i4/A, i5/A, i6/A, i7/A, i8/A

    5.000e+0, 3.138e-5, 2.966e-5, 1.468e-5, 1.975e-5, 6.805e-6, 9.386e-6, -1.301e-6, -1.295e-6
    1.000e+1, 2.905e-5, 2.848e-5, 1.517e-5, 1.899e-5, 6.345e-6, 8.992e-6, -1.195e-6, -1.198e-6
    1.500e+1, 2.843e-5, 2.803e-5, 1.496e-5, 1.955e-5, 7.387e-6, 8.686e-6, -1.257e-6, -1.232e-6
    2.000e+1, 2.886e-5, 2.762e-5, 1.557e-5, 1.936e-5, 7.118e-6, 8.613e-6, -1.195e-6, -1.236e-6
    2.500e+1, 2.909e-5, 2.744e-5, 1.403e-5, 1.888e-5, 7.515e-6, 8.710e-6, -1.242e-6, -1.179e-6
    3.000e+1, 2.835e-5, 2.739e-5, 1.514e-5, 1.955e-5, 6.985e-6, 8.677e-6, -1.180e-6, -1.203e-6

    """

    # Create a channel for each column
    for i, col in enumerate(header):
        if col == "Time/s":
            continue

        channel = InstrumentExperimentChannelChannel(
            channel_name=col,
            experiment_id=experiment.id,
        )

        session.add(channel)
        await session.commit()
        await session.refresh(channel)

        # Create data for each row
        for row in lines[data_start:]:
            if not row:
                continue

            data = row[i]
            data = float(data)

            data = InstrumentExperimentChannelData(
                channel_id=channel.id,
                experiment_id=experiment.id,
                time=float(row[0]),
                value=data,
            )

            session.add(data)

    await session.commit()
    await session.refresh(experiment)

    res = await get_one(experiment.id, session=session)

    return res


async def delete_one(
    id: UUID,
    session: AsyncSession = Depends(get_session),
) -> UUID:

    obj = await crud.get_model_by_id(model_id=id, session=session)
    if obj:
        await session.delete(obj)

    await session.commit()

    return id


async def delete_many(
    ids: list[UUID],
    session: AsyncSession = Depends(get_session),
) -> list[UUID]:

    for id in ids:
        obj = await crud.get_model_by_id(model_id=id, session=session)
        if obj:
            await session.delete(obj)

    await session.commit()

    return ids


async def update_one(
    id: UUID,
    instrument_experiment_update: InstrumentExperimentChannelUpdate,
    session: AsyncSession = Depends(get_session),
) -> InstrumentExperimentChannel:

    instrument_experiment = await crud.get_model_by_id(
        model_id=id, session=session
    )

    update_data = instrument_experiment_update.model_dump(exclude_unset=True)
    instrument_experiment.sqlmodel_update(update_data)

    session.add(instrument_experiment)

    await session.commit()
    await session.refresh(instrument_experiment)

    return instrument_experiment
