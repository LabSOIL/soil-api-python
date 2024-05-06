from app.plots.models import (
    Plot,
    PlotCreate,
    PlotRead,
    PlotUpdate,
)
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from uuid import UUID
from app.crud import CRUD

router = APIRouter()
crud = CRUD(Plot, PlotRead, PlotCreate, PlotUpdate)


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
    plot_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    res = await crud.get_model_by_id(model_id=plot_id, session=session)

    if not res:
        raise HTTPException(status_code=404, detail=f"ID: {plot_id} not found")
    return res


@router.get("/{plot_id}", response_model=PlotRead)
async def get_Plot(
    # session: AsyncSession = Depends(get_session),
    # *,
    obj: CRUD = Depends(get_one),
) -> PlotRead:
    """Get a plot by id"""

    return obj


@router.get("", response_model=list[PlotRead])
async def get_all_Plots(
    response: Response,
    plots: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[PlotRead]:
    """Get all Plot data"""

    return plots


@router.post("", response_model=PlotRead)
async def create_Plot(
    plot: PlotCreate,
    session: AsyncSession = Depends(get_session),
) -> PlotRead:
    """Creates a plot data record"""

    obj = Plot.model_validate(plot)

    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


@router.put("/{plot_id}", response_model=PlotRead)
async def update_Plot(
    plot_update: PlotUpdate,
    *,
    plot: PlotRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> PlotRead:
    """Update a plot by id"""

    update_data = plot_update.model_dump(exclude_unset=True)
    plot.sqlmodel_update(update_data)

    session.add(plot)
    await session.commit()
    await session.refresh(plot)

    return plot


@router.delete("/{plot_id}")
async def delete_Plot(
    plot: PlotRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a plot by id"""

    await session.delete(plot)
    await session.commit()

    return {"ok": True}
