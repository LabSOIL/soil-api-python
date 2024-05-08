from app.plots.samples.models import (
    PlotSampleRead,
    PlotSample,
    PlotSampleCreate,
    PlotSampleUpdate,
)
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from uuid import UUID
from app.crud import CRUD

router = APIRouter()
crud = CRUD(PlotSample, PlotSampleRead, PlotSampleCreate, PlotSampleUpdate)


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
    plot_sample_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    res = await crud.get_model_by_id(model_id=plot_sample_id, session=session)

    if not res:
        raise HTTPException(
            status_code=404, detail=f"ID: {plot_sample_id} not found"
        )
    return res


@router.get("/{plot_sample_id}", response_model=PlotSampleRead)
async def get_plot_sample(
    obj: CRUD = Depends(get_one),
) -> PlotSampleRead:
    """Get a plot sample by id"""

    return obj


@router.get("", response_model=list[PlotSampleRead])
async def get_all_plot_samples(
    response: Response,
    plot_samples: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[PlotSampleRead]:
    """Get all PlotSample data"""

    return plot_samples


@router.post("", response_model=PlotSampleRead)
async def create_plot_sample(
    plot_sample: PlotSampleCreate,
    session: AsyncSession = Depends(get_session),
) -> PlotSampleRead:
    """Creates a plot sample data record"""

    obj = PlotSample.model_validate(plot_sample)

    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


@router.put("/{plot_sample_id}", response_model=PlotSampleRead)
async def update_plot_sample(
    plot_sample_update: PlotSampleUpdate,
    *,
    plot_sample: PlotSampleRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> PlotSampleRead:
    """Update a plot sample by id"""

    update_data = plot_sample_update.model_dump(exclude_unset=True)
    plot_sample.sqlmodel_update(update_data)

    session.add(plot_sample)
    await session.commit()
    await session.refresh(plot_sample)

    return plot_sample


@router.delete("/{plot_sample_id}")
async def delete_plot_sample(
    plot_sample: PlotSampleRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a plot sample by id"""

    await session.delete(plot_sample)
    await session.commit()

    return {"ok": True}
