from app.areas.models import (
    AreaRead,
    Area,
    AreaCreate,
    AreaUpdate,
)
from app.soil.profiles.models import SoilProfile
from app.plots.models import Plot
from app.sensors.models import Sensor
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from uuid import UUID
from app.crud import CRUD
from sqlmodel import select
from sqlalchemy import select
from geoalchemy2 import Geography
from geoalchemy2.functions import (
    ST_ConvexHull,
    ST_Collect,
    ST_Transform,
    ST_MinimumBoundingCircle,
    ST_Buffer,
)
from sqlalchemy.sql import select as sql_select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql.expression import func
from sqlalchemy import union_all
from app.config import config

router = APIRouter()
crud = CRUD(Area, AreaRead, AreaCreate, AreaUpdate)


async def get_convex_hull(session: AsyncSession):
    # Define the subqueries for each table
    plot_subquery = select(
        Area.id.label("id"), ST_Transform(Plot.geom, config.SRID).label("geom")
    ).join(Plot, Area.id == Plot.area_id)

    soilprofile_subquery = select(
        Area.id.label("id"),
        ST_Transform(SoilProfile.geom, config.SRID).label("geom"),
    ).join(SoilProfile, Area.id == SoilProfile.area_id)

    sensor_subquery = select(
        Area.id.label("id"),
        ST_Transform(Sensor.geom, config.SRID).label("geom"),
    ).join(Sensor, Area.id == Sensor.area_id)

    # Combine the subqueries using UNION ALL
    combined_subquery = union_all(
        plot_subquery, soilprofile_subquery, sensor_subquery
    ).subquery()

    # Define the main query to group by area id and compute the convex hull
    # with a 100m buffer
    main_query = select(
        combined_subquery.c.id,
        ST_Transform(
            ST_ConvexHull(ST_Collect(combined_subquery.c.geom)),
            4326,
        ).label("convex_hull"),
    ).group_by(combined_subquery.c.id)

    geometry_results = await session.exec(main_query)
    return geometry_results.all()


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

    geometry = await get_convex_hull(session)

    area_objs = []
    for area in res:
        area = AreaRead.model_validate(area)
        for geom in geometry:
            if area.id == geom.id:
                area.geom = geom.convex_hull
        area_objs.append(area)

    return area_objs


async def get_one(
    area_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    res = await crud.get_model_by_id(model_id=area_id, session=session)

    if not res:
        raise HTTPException(status_code=404, detail=f"ID: {area_id} not found")

    geometry = await get_convex_hull(session)

    for geom in geometry:
        if res.id == geom.id:
            res = AreaRead.model_validate(res)
            res.geom = geom.convex_hull
            break

    return res


@router.get("/{area_id}", response_model=AreaRead)
async def get_area(
    obj: CRUD = Depends(get_one),
) -> AreaRead:
    """Get an area by id"""

    return obj


@router.get("", response_model=list[AreaRead])
async def get_all_areas(
    response: Response,
    areas: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[AreaRead]:
    """Get all Area data"""

    return areas


@router.post("", response_model=AreaRead)
async def create_area(
    area: AreaCreate,
    session: AsyncSession = Depends(get_session),
) -> AreaRead:
    """Creates an area data record"""

    obj = Area.model_validate(area)

    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


@router.put("/{area_id}", response_model=AreaRead)
async def update_area(
    area_update: AreaUpdate,
    *,
    area: AreaRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> AreaRead:
    """Update an area by id"""

    update_data = area_update.model_dump(exclude_unset=True)
    area.sqlmodel_update(update_data)

    session.add(area)
    await session.commit()
    await session.refresh(area)

    return area


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


@router.delete("/{area_id}")
async def delete_area(
    area: AreaRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete an area by id"""

    await session.delete(area)
    await session.commit()

    return {"ok": True}
