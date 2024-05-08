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
from app.areas.models import Area
from sqlmodel import select


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
async def get_plot(
    obj: CRUD = Depends(get_one),
) -> PlotRead:
    """Get a plot by id"""

    return obj


@router.get("", response_model=list[PlotRead])
async def get_all_plots(
    response: Response,
    plots: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[PlotRead]:
    """Get all Plot data"""

    return plots


@router.post("", response_model=PlotRead)
async def create_plot(
    create_obj: PlotCreate,
    session: AsyncSession = Depends(get_session),
) -> PlotRead:
    """Creates a plot data record"""

    plot = create_obj.model_dump()

    # Get area for the plot
    res = await session.exec(
        select(Area).where(Area.id == plot.get("area_id"))
    )
    area_obj = res.one()

    plot["name"] = (
        f"{area_obj.name.upper()[0]}"
        f"{plot['gradient'].upper()[0]}{plot['plot_iterator']:02d}"
    )

    obj = Plot.model_validate(plot)

    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


@router.put("/{plot_id}", response_model=PlotRead)
async def update_plot(
    plot_update: PlotUpdate,
    *,
    plot: PlotRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> PlotRead:
    """Update a plot by id"""

    update_data = plot_update.model_dump(exclude_unset=True)

    # Get area for the plot
    res = await session.exec(
        select(Area).where(Area.id == update_data.get("area_id"))
    )
    area_obj = res.one()

    update_data["name"] = (
        f"{area_obj.name.upper()[0]}"
        f"{update_data['gradient'].upper()[0]}"
        f"{update_data['plot_iterator']:02d}"
    )

    plot.sqlmodel_update(update_data)

    session.add(plot)
    await session.commit()
    await session.refresh(plot)

    return plot


@router.delete("/{plot_id}")
async def delete_plot(
    plot: PlotRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a plot by id"""

    await session.delete(plot)
    await session.commit()

    return {"ok": True}
