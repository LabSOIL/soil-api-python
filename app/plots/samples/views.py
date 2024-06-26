from app.plots.samples.models import (
    PlotSampleReadWithPlot,
    PlotSample,
    PlotSampleCreate,
    PlotSampleUpdate,
    PlotSampleUpdateBatch,
)
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Response
from uuid import UUID
from app.crud import CRUD
from app.plots.samples.services import (
    get_one,
    get_data,
    get_count,
    create_one,
    update_one,
)

router = APIRouter()
crud = CRUD(
    PlotSample, PlotSampleReadWithPlot, PlotSampleCreate, PlotSampleUpdate
)


@router.get("/{plot_sample_id}", response_model=PlotSampleReadWithPlot)
async def get_plot_sample(
    obj: CRUD = Depends(get_one),
) -> PlotSampleReadWithPlot:
    """Get a plot sample by id"""

    return obj


@router.get("", response_model=list[PlotSampleReadWithPlot])
async def get_all_plot_samples(
    response: Response,
    plot_samples: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[PlotSampleReadWithPlot]:
    """Get all PlotSample data"""

    return plot_samples


@router.put("/batch", response_model=list[PlotSampleReadWithPlot])
async def update_many(
    plot_samples: list[PlotSampleUpdateBatch],
    session: AsyncSession = Depends(get_session),
) -> list[PlotSampleReadWithPlot]:
    """Update plot samples from a list of PlotSampleUpdate objects"""

    objs = []
    for plot_sample in plot_samples:
        obj = await update_one(
            plot_sample_id=plot_sample.id,
            plot_sample_update=plot_sample,
            session=session,
        )
        objs.append(obj)

    return objs


@router.put("/{plot_sample_id}", response_model=PlotSampleReadWithPlot)
async def update_one_plot_sample(
    updated_plot_sample: PlotSampleUpdate = Depends(update_one),
) -> PlotSampleReadWithPlot:
    """Update a plot sample by id"""

    return updated_plot_sample


@router.post("", response_model=PlotSampleReadWithPlot)
async def create_plot_sample(
    create_obj: PlotSampleCreate,
    session: AsyncSession = Depends(get_session),
) -> PlotSampleReadWithPlot:
    """Creates a plot sample data record"""

    obj = await create_one(create_obj.model_dump(), session)

    return obj


@router.post("/batch", response_model=list[PlotSampleReadWithPlot])
async def create_plot_sample_batch(
    objs: list[PlotSampleCreate],
    session: AsyncSession = Depends(get_session),
) -> list[PlotSampleReadWithPlot]:
    """Creates a many from a list"""

    created_objs = []
    for obj in objs:
        obj = await create_one(obj.model_dump(), session)
        created_objs.append(obj)

    return created_objs


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


@router.delete("/{plot_sample_id}", response_model=UUID)
async def delete_plot_sample(
    plot_sample: PlotSampleReadWithPlot = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a obj sample by id"""
    id = plot_sample.id
    await session.delete(plot_sample)
    await session.commit()

    return id
