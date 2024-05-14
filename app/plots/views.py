from app.plots.models import (
    Plot,
    PlotCreate,
    PlotRead,
    PlotUpdate,
    PlotCreateBatch,
)
from app.projects.models import Project
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from uuid import UUID
from app.crud import CRUD
from app.areas.models import Area
from typing import Any
from app.utils import decode_base64
from sqlmodel import select
from sqlalchemy import func

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


@router.post(
    "/batch",
    response_model=Any,
    # response_model=list[PlotSampleRead],
)
async def create_plot_batch(
    plot: PlotCreateBatch,
    session: AsyncSession = Depends(get_session),
) -> PlotRead:
    """Creates plots from a csv

    Before committing to db we need to parse the csv file and create a
    PlotSampleCreate object for each line in the csv file.

    We should make sure there are no duplicates in the DB and CSV.
    """

    rawdata, dtype = decode_base64(plot.attachment)
    if dtype != "csv":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {dtype}. Must be a csv file.",
        )
    # print(rawdata)
    lines = rawdata.decode("utf-8").split("\n")
    csv_header = tuple([line.strip() for line in lines[0].split(",")])

    # [print(dtype, line) for line in lines]
    header = list(PlotCreate.model_fields.keys())
    # header.remove("plot_id")
    header.append("project_name")
    header.append("catchment")
    header.append("gradient")

    # Add 'project_name' to header
    # Remove 'plot_id' from header
    # header
    print("CLASS", header)
    print("INCOMING", csv_header)

    for header_line in lines[0].split(","):
        if header_line.strip() not in header:
            print(f"Invalid header: {header_line}")

    objs = []
    errors = []
    for i, line in enumerate(lines[1:]):
        # For each line in lines, build a PlotSampleCreate object
        if not line:  # Skip empty lines
            continue

        line = line.split(",")
        data = dict(zip(csv_header, line))

        query = await session.exec(
            select(Area)
            .join(Project)
            .where(func.lower(Area.name) == data["area_name"].lower())
            .where(func.lower(Project.name) == data["project_name"].lower())
        )
        area = query.one_or_none()
        if not area:
            # Create Area name from catchment, gradient and plot id

            errors.append(
                {
                    "csv_line": i,
                    "message": (
                        f"Area '{data['area_name']}' not found in "
                        f"project: '{data['project_name']}'"
                    ),
                }
            )
            continue

        data["area_id"] = area.id
        data["plot_iterator"] = int(data["id"])
        data["name"] = (
            f"{area.name.upper()[0]}"
            f"{data['gradient'].upper()[0]}{data['plot_iterator']:02d}"
        )
        # Check that the data doesn't already exist in the DB
        query = await session.exec(
            select(Plot).where(
                Plot.area_id == data["area_id"],
                Plot.plot_iterator == int(data["id"]),
            )
        )
        if query.one_or_none():
            errors.append(
                {
                    "csv_line": i,
                    "message": (
                        f"Duplicate record: {data['plot_id']} {data['name']}"
                    ),
                }
            )
            continue

        create_obj = PlotCreate.model_validate(data)
        # obj = PlotSample.model_validate(plot_sample)
        objs.append(create_obj)
    print("OBJS", objs)
    print("Objs to create:", len(objs))

    # Raise exception if any errors as to not make any changes to the DB
    if errors:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Errors in CSV file",
                "errors": errors,
            },
        )

    for obj in objs:
        db_obj = Plot.model_validate(obj)
        session.add(db_obj)

    await session.commit()
    return True

    # session.add(obj)

    # await session.commit()
    # await session.refresh(obj)

    # return obj


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
