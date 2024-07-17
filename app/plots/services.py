from app.plots.models import (
    Plot,
    PlotCreate,
    PlotReadWithSamples,
    PlotUpdate,
)
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
from app.utils.funcs import set_elevation_to_db_obj
from sqlmodel import select
from sqlalchemy import func
from sqlalchemy.exc import NoResultFound
from typing import Any
from app.exceptions import ValidationError

router = APIRouter()


crud = CRUD(Plot, PlotReadWithSamples, PlotCreate, PlotUpdate)

TABLES_TO_JOIN = [Area]
FIELDS_TO_QUERY = [Area.name]


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
        filter_models_to_join=TABLES_TO_JOIN,
        filter_fields_to_query=FIELDS_TO_QUERY,
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
        filter_models_to_join=TABLES_TO_JOIN,
        filter_fields_to_query=FIELDS_TO_QUERY,
    )
    print("Total results:", len(res))

    return res


async def get_one(
    plot_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    res = await crud.get_model_by_id(model_id=plot_id, session=session)

    if not res:
        raise HTTPException(status_code=404, detail=f"ID: {plot_id} not found")
    return res


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
        try:
            res = await session.exec(
                select(Area).where(
                    func.lower(Area.name) == data.get("area_name").lower()
                )
            )
            area_obj = res.one()
        except NoResultFound:
            raise ValidationError(
                loc=["body", "area_name"],
                msg=f"Area name: {data.get('area_name')} not found",
            )

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


async def update_one(
    plot_id: UUID,
    plot_update: PlotUpdate,
    session: AsyncSession = Depends(get_session),
) -> Plot:
    """Update a single plot"""

    obj = await get_one(plot_id, session=session)

    update_data = plot_update.model_dump(exclude_unset=True)

    # Get area for the plot
    # If area id exists, use it, otherwise use the name if it exists
    # This allows the import CSV to use the area name (improve user experience)
    if update_data.get("area_name"):
        try:
            res = await session.exec(
                select(Area).where(
                    func.lower(Area.name)
                    == update_data.get("area_name").lower()
                )
            )
            area_obj = res.one()  # Make sure only one returns
        except NoResultFound:
            raise ValidationError(
                loc=["body", "area_name"],
                msg=f"Area name: {update_data.get('area_name')} not found",
            )
        update_data["area_id"] = area_obj.id

    else:
        res = await session.exec(
            select(Area).where(Area.id == update_data.get("area_id"))
        )
        area_obj = res.one()

    update_data["name"] = (
        f"{area_obj.name.upper()[0]}"
        f"{update_data['gradient'].upper()[0]}"
        f"{update_data['plot_iterator']:02d}"
    )

    obj.sqlmodel_update(update_data)

    session.add(obj)
    await session.commit()
    await session.refresh(obj)

    return obj
