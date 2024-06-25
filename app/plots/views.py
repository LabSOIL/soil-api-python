from app.plots.models import (
    Plot,
    PlotCreate,
    PlotReadWithSamples,
    PlotUpdate,
)
from app.projects.models import Project
from app.db import get_session, AsyncSession
from fastapi import (
    Depends,
    APIRouter,
    Query,
    Response,
    HTTPException,
    BackgroundTasks,
)
from uuid import UUID
from app.crud import CRUD
from app.areas.models import Area
from typing import Any
from app.utils.funcs import get_elevation_swisstopo, set_elevation_to_db_obj
from sqlmodel import select
from sqlalchemy import func

router = APIRouter()
crud = CRUD(Plot, PlotReadWithSamples, PlotCreate, PlotUpdate)


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


@router.get("/{plot_id}", response_model=PlotReadWithSamples)
async def get_plot(
    obj: CRUD = Depends(get_one),
) -> PlotReadWithSamples:
    """Get a plot by id"""

    return obj


@router.get("", response_model=list[PlotReadWithSamples])
async def get_all_plots(
    response: Response,
    plots: Plot = Depends(get_data),
    total_count: int = Depends(get_count),
    include_image: bool = Query(False, description="Include image data"),
) -> list[PlotReadWithSamples]:
    """Get all Plot data"""

    if not include_image:
        for plot in plots:
            plot.image = None

    return plots


async def create_one(
    data: dict,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
) -> Plot:
    """Create a single plot

    To be used in both create one and create many endpoints
    """

    # If area name is given, find area by name (ensuring uniqueness) else id
    if data.get("area_name"):
        res = await session.exec(
            select(Area).where(
                func.lower(Area.name) == data.get("area_name").lower()
            )
        )
        area_obj = res.one()
        data["area_id"] = area_obj.id
    else:
        res = await session.exec(
            select(Area).where(Area.id == data.get("area_id"))
        )
        area_obj = res.one()

    data["name"] = (
        f"{area_obj.name.upper()[0]}"
        f"{data['gradient'].upper()[0]}{data['plot_iterator']:02d}"
    )

    obj = Plot.model_validate(data)

    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    if float(data["coord_z"]) == 0:
        # Start background process
        background_tasks.add_task(
            set_elevation_to_db_obj,
            id=obj.id,
            crud_instance=crud,
            session=session,
        )

    return obj


@router.post("", response_model=PlotReadWithSamples)
async def create_plot(
    create_obj: PlotCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> PlotReadWithSamples:
    """Creates a plot data record"""

    obj = await create_one(create_obj.model_dump(), session, background_tasks)

    return obj


@router.post("/batch", response_model=list[PlotReadWithSamples])
async def create_many(
    plots: list[PlotCreate],
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> list[PlotReadWithSamples]:
    """Creates plots from a list of PlotCreate objects"""

    objs = []
    for plot in plots:
        obj = await create_one(plot.model_dump(), session, background_tasks)
        objs.append(obj)

    return objs


@router.put("/{plot_id}", response_model=PlotReadWithSamples)
async def update_plot(
    plot_update: PlotUpdate,
    *,
    plot: PlotReadWithSamples = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> PlotReadWithSamples:
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


@router.delete("/{plot_id}")
async def delete_plot(
    plot: PlotReadWithSamples = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a plot by id"""

    await session.delete(plot)
    await session.commit()

    return {"ok": True}
