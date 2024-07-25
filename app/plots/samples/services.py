from app.plots.samples.models import (
    PlotSampleReadWithPlot,
    PlotSample,
    PlotSampleCreate,
    PlotSampleUpdate,
)
from app.plots.models import Plot
from app.areas.models import Area
from app.projects.models import Project
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from uuid import UUID
from app.crud import CRUD
from sqlmodel import select
from sqlalchemy import func
from app.exceptions import ValidationError
from sqlalchemy.exc import NoResultFound
import sqlalchemy
from sqlalchemy.sql import cast
from sqlalchemy.exc import IntegrityError

router = APIRouter()
crud = CRUD(
    PlotSample, PlotSampleReadWithPlot, PlotSampleCreate, PlotSampleUpdate
)

TABLES_TO_JOIN = [Plot, Area, Project]
FIELDS_TO_QUERY = [Plot.name, Area.name, Project.name]


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


async def create_one(
    data: dict,
    session: AsyncSession,
) -> Plot:
    """Create a single plot

    To be used in both create one and create many endpoints
    """

    # If no plot ID is given, then obtain it from project, area,
    # and plot gradient, iterator
    if not data.get("plot_id"):
        if (
            not data.get("project_name")
            or not data.get("area_name")
            or not data.get("plot_gradient")
            or not data.get("plot_iterator")
        ):
            raise ValidationError(
                loc=["body"],
                msg=(
                    "Project name, area name, plot gradient and plot iterator "
                    "are required fields if Plot ID not given"
                ),
            )
        try:
            print(
                data["plot_gradient"].lower(),
                data["area_name"].lower(),
                data["project_name"].lower(),
                data["plot_iterator"],
            )

            query = await session.exec(
                select(Plot)
                .join(Area)
                .join(Project)
                .where(
                    Plot.plot_iterator == int(data["plot_iterator"]),
                )
                .where(
                    # Cast to string because it's an enum
                    func.lower(cast(Plot.gradient, sqlalchemy.String))
                    == data["plot_gradient"].lower()
                )
                .where(
                    func.lower(Area.name) == data["area_name"].lower(),
                )
                .where(
                    func.lower(Project.name) == data["project_name"].lower()
                )
            )

            plot = query.one()
            data["plot_id"] = plot.id
        except NoResultFound as e:
            print(e)
            raise ValidationError(
                loc=["body"],
                msg=(
                    "Plot with the given project name "
                    f"({data['project_name']}), "
                    f"area name ({data['area_name']}), "
                    f"plot gradient ({data['plot_gradient']}), "
                    f"and plot iterator ({data['plot_iterator']}) "
                    "not found"
                ),
            )
    else:
        try:
            res = await session.exec(
                select(Plot).where(Plot.id == data.get("plot_id"))
            )
            plot = res.one()
        except NoResultFound:
            raise ValidationError(
                loc=["body", "plot_id"],
                msg=f"Plot ID: {data.get('plot_id')} not found",
            )
    try:
        obj = PlotSample.model_validate(data)

        session.add(obj)

        await session.commit()
        await session.refresh(obj)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=(
                "Either the sample name is not unique, or a sample with the "
                "same replicate, upper and lower depth already exists."
            ),
        )
    return obj


async def update_one(
    plot_sample_id: UUID,
    plot_sample_update: PlotSampleUpdate,
    session: AsyncSession = Depends(get_session),
) -> Plot:
    """Update a single plot sample"""

    obj = await get_one(plot_sample_id, session=session)

    update_data = plot_sample_update.model_dump(exclude_unset=True)

    # If no plot ID is given, then obtain it from project, area,
    # and plot gradient, iterator
    if not update_data.get("plot_id"):
        if (
            not update_data.get("project_name")
            or not update_data.get("area_name")
            or not update_data.get("plot_gradient")
            or not update_data.get("plot_iterator")
        ):
            raise ValidationError(
                loc=["body"],
                msg=(
                    "Project name, area name, plot gradient and plot iterator "
                    "are required fields if Plot ID not given"
                ),
            )
        try:
            query = await session.exec(
                select(Plot)
                .join(Area)
                .join(Project)
                .where(
                    Plot.plot_iterator == int(update_data["plot_iterator"]),
                )
                .where(
                    # Cast to string because it's an enum
                    func.lower(cast(Plot.gradient, sqlalchemy.String))
                    == update_data["plot_gradient"].lower()
                )
                .where(
                    func.lower(Area.name) == update_data["area_name"].lower(),
                )
                .where(
                    func.lower(Project.name)
                    == update_data["project_name"].lower()
                )
            )
            plot = query.one()
            update_data["plot_id"] = plot.id
        except NoResultFound:
            raise ValidationError(
                loc=["body"],
                msg="Plot with the given project name, area name, plot gradient, and plot iterator not found",
            )

    else:
        try:

            res = await session.exec(
                select(Plot).where(Plot.id == update_data.get("plot_id"))
            )
            plot = res.one()
        except NoResultFound:
            raise ValidationError(
                loc=["body", "plot_id"],
                msg=f"Plot ID: {update_data.get('plot_id')} not found",
            )

    obj.sqlmodel_update(update_data)

    session.add(obj)
    await session.commit()
    await session.refresh(obj)

    return obj
