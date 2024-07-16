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
from app.instruments.tools import (
    calculate_spline,
    filter_baseline,
    largest_triangle_three_buckets,
)
import numpy as np
from app.config import config

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
    downsample: bool = Query(False),
) -> InstrumentExperimentChannelRead:

    res = await crud.get_model_by_id(model_id=id, session=session)

    if not res:
        raise HTTPException(status_code=404, detail=f"ID: {id} not found")

    # Downsample points, may be necessary, rendering can get slow
    if downsample:
        res.time_values, res.raw_values = largest_triangle_three_buckets(
            res.time_values,
            res.raw_values,
            config.INSTRUMENT_PLOT_DOWNSAMPLE_THRESHOLD,
        )

        res.time_values, res.baseline_values = largest_triangle_three_buckets(
            res.time_values,
            res.baseline_values,
            config.INSTRUMENT_PLOT_DOWNSAMPLE_THRESHOLD,
        )
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
    # Fetch the instrument experiment by ID
    channel = await crud.get_model_by_id(model_id=id, session=session)

    update_data = instrument_experiment_update.model_dump(exclude_unset=True)

    if "baseline_chosen_points" in update_data:
        baseline_chosen_points = update_data["baseline_chosen_points"]

        x = np.array(channel.time_values)
        y = np.array(channel.raw_values)

        # If there are no points, remove the baseline
        if not baseline_chosen_points:
            update_data["baseline_spline"] = []
            update_data["baseline_values"] = []
        else:

            # Calculate the spline and filtered baseline
            spline = calculate_spline(
                x,
                y,
                [bp["x"] for bp in baseline_chosen_points],
                interpolation_method="linear",
            )
            filtered_baseline = filter_baseline(y, spline)

            # Update the instrument experiment data
            update_data["baseline_spline"] = spline.tolist()
            update_data["baseline_values"] = filtered_baseline.tolist()

    # Update the instrument experiment model with the new data
    channel.sqlmodel_update(update_data)
    session.add(channel)

    await session.commit()
    await session.refresh(channel)

    return channel
