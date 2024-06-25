from app.plots.models import (
    Plot,
    PlotCreate,
    PlotReadWithSamples,
    PlotUpdate,
    PlotUpdateBatch,
)
from app.db import get_session, AsyncSession
from fastapi import (
    Depends,
    APIRouter,
    Query,
    Response,
    BackgroundTasks,
)
from uuid import UUID
from app.crud import CRUD
from app.areas.models import Area
from sqlmodel import select
from app.plots.services import (
    get_count,
    get_data,
    get_one,
    create_one,
    update_one,
    crud,
)

router = APIRouter()


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


@router.put("/batch", response_model=list[PlotReadWithSamples])
async def update_many(
    plots: list[PlotUpdateBatch],
    session: AsyncSession = Depends(get_session),
) -> list[PlotReadWithSamples]:
    """Update plots from a list of PlotUpdate objects"""

    objs = []
    for plot in plots:
        obj = await update_one(
            plot_id=plot.id, plot_update=plot, session=session
        )
        objs.append(obj)

    return objs


@router.put("/{plot_id}", response_model=PlotReadWithSamples)
async def update_plot(
    updated_plot: Plot = Depends(update_one),
) -> PlotReadWithSamples:
    """Update a plot by id"""

    return updated_plot


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
