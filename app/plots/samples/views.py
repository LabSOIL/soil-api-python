from app.plots.samples.models import (
    PlotSampleReadWithPlot,
    PlotSample,
    PlotSampleCreate,
    PlotSampleUpdate,
    PlotSampleCreateBatch,
    PlotSampleCreateBatchRead,
)
from app.plots.models import Plot
from app.areas.models import Area
from app.projects.models import Project
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException, Body
from uuid import UUID
from app.crud import CRUD
from typing import Any
from app.utils import decode_base64
from sqlmodel import select
from sqlalchemy import func

router = APIRouter()
crud = CRUD(
    PlotSample, PlotSampleReadWithPlot, PlotSampleCreate, PlotSampleUpdate
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


@router.post("", response_model=PlotSampleReadWithPlot)
async def create_plot_sample(
    plot_sample: PlotSampleCreate,
    session: AsyncSession = Depends(get_session),
) -> PlotSampleReadWithPlot:
    """Creates a plot sample data record"""

    obj = PlotSample.model_validate(plot_sample)

    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


@router.post("/batch", response_model=PlotSampleCreateBatchRead)
async def create_plot_sample_batch(
    plot_sample: PlotSampleCreateBatch,
    session: AsyncSession = Depends(get_session),
) -> PlotSampleCreateBatchRead:
    """Creates a plot sample from a csv

    Before committing to db we need to parse the csv file and create a
    PlotSampleCreate object for each line in the csv file.

    We should make sure there are no duplicates in the DB and CSV.
    """

    rawdata, dtype = plot_sample = decode_base64(plot_sample.attachment)
    if dtype != "csv":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {dtype}. Must be a csv file.",
        )
    # print(rawdata)
    lines = rawdata.decode("utf-8").split("\n")
    csv_header = tuple([line.strip() for line in lines[0].split(",")])

    # [print(dtype, line) for line in lines]
    header = list(PlotSampleCreate.model_fields.keys())
    # header.remove("area_id")
    header.append("project_name")
    header.append("area_name")
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
        # print("LINE", line)
        data = dict(zip(csv_header, line))
        # print("DATA", data)
        query = await session.exec(
            select(Plot)
            .join(Area)
            .join(Project)
            .where(Plot.plot_iterator == int(data["plot_id"]))
            .where(func.lower(Plot.gradient) == data["gradient"].lower())
            .where(func.lower(Area.name) == data["area_name"].lower())
            .where(func.lower(Project.name) == data["project_name"].lower())
        )
        plot = query.one_or_none()
        if not plot:
            # Create Plot name from catchment, gradient and plot id
            plot_name = (
                f"{data['area_name'].upper()[0]}{data['gradient'].upper()[0]}"
                f"{data['plot_id']:02}"
            )
            errors.append(
                {
                    "csv_line": i,
                    "message": (
                        f"No match for Plot: '{data['area_name']} "
                        f"{data['gradient']} {data['plot_id']}' found in "
                        f"Project: '{data['project_name']}'"
                    ),
                }
            )
            continue

        data["plot_id"] = plot.id

        # Check that the data doesn't already exist in the DB
        query = await session.exec(
            select(PlotSample).where(
                PlotSample.plot_id == data["plot_id"],
                PlotSample.name == data["name"],
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

        # Delete fields where the data is empty or empty string
        data = {k: v for k, v in data.items() if v}
        try:
            create_obj = PlotSampleCreate.model_validate(data)
            db_obj = PlotSample.model_validate(create_obj)
        except Exception as e:
            error_message = e.errors()[0]
            errors.append(
                {
                    "csv_line": i,
                    "message": (
                        f"{error_message.get('msg')}. "
                        f"Input given: {error_message.get('input')} at "
                        f"{error_message.get('loc')}"
                    ),
                }
            )
            continue
        objs.append(db_obj)

    if errors:
        raise HTTPException(
            status_code=400,
            detail=PlotSampleCreateBatchRead(
                success=False,
                message="Error creating samples",
                errors=errors,
                qty_added=0,
            ).model_dump(),
        )

    session.add_all(objs)
    await session.commit()

    return PlotSampleCreateBatchRead(
        success=True,
        message="Samples created successfully",
        errors=errors,
        qty_added=len(objs),
    )
    # obj = PlotSample.model_validate(plot_sample)

    # session.add(obj)

    # await session.commit()
    # await session.refresh(obj)

    # return obj


@router.put("/{plot_sample_id}", response_model=PlotSampleReadWithPlot)
async def update_plot_sample(
    plot_sample_update: PlotSampleUpdate,
    *,
    plot_sample: PlotSampleReadWithPlot = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> PlotSampleReadWithPlot:
    """Update a plot sample by id"""

    update_data = plot_sample_update.model_dump(exclude_unset=True)
    plot_sample.sqlmodel_update(update_data)

    session.add(plot_sample)
    await session.commit()
    await session.refresh(plot_sample)

    return plot_sample


@router.delete("/{plot_sample_id}")
async def delete_plot_sample(
    plot_sample: PlotSampleReadWithPlot = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a plot sample by id"""

    await session.delete(plot_sample)
    await session.commit()

    return {"ok": True}
