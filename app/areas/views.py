from app.areas.models import (
    AreaRead,
    Area,
    AreaCreate,
    AreaUpdate,
)
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from uuid import UUID
from app.crud import CRUD

router = APIRouter()
crud = CRUD(Area, AreaRead, AreaCreate, AreaUpdate)


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
    area_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    res = await crud.get_model_by_id(model_id=area_id, session=session)

    if not res:
        raise HTTPException(status_code=404, detail=f"ID: {area_id} not found")
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


@router.delete("/{area_id}")
async def delete_area(
    area: AreaRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete an area by id"""

    await session.delete(area)
    await session.commit()

    return {"ok": True}
