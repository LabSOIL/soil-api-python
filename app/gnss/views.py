from app.gnss.models import (
    GNSS,
    GNSSCreate,
    GNSSRead,
    GNSSUpdate,
    GNSSCreateFromFile,
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
from app.gnss.services import (
    get_count,
    get_data,
    get_one,
    create_one,
    update_one,
    crud,
)

router = APIRouter()


@router.get("/{gnss_id}", response_model=GNSSRead)
async def get_gnss(
    obj: CRUD = Depends(get_one),
) -> GNSSRead:
    """Get a gnss by id"""

    return obj


@router.get("", response_model=list[GNSSRead])
async def get_all_gnss(
    response: Response,
    gnss: GNSS = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[GNSSRead]:
    """Get all GNSS data"""

    return gnss


from typing import Any


@router.post("", response_model=GNSSRead)
async def create_gnss(
    create_obj: GNSSCreateFromFile,
    session: AsyncSession = Depends(get_session),
) -> GNSSRead:
    """Creates a gnss data record"""

    obj = await create_one(create_obj.model_dump(), session)

    # Return the first object to satisfy a "Create one". A bit of a hack
    # to get around dataProvider errors in react-admin
    return obj[0]


@router.post("/batch", response_model=list[GNSSRead])
async def create_many(
    gnss: list[GNSSCreate],
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> list[GNSSRead]:
    """Creates gnss from a list of GNSSCreate objects"""

    objs = []
    for gnss in gnss:
        obj = await create_one(gnss.model_dump(), session, background_tasks)
        objs.append(obj)

    return objs


@router.put("/{gnss_id}", response_model=GNSSRead)
async def update_gnss(
    updated_gnss: GNSS = Depends(update_one),
) -> GNSSRead:
    """Update a gnss by id"""

    return updated_gnss


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


@router.delete("/{gnss_id}")
async def delete_gnss(
    gnss: GNSSRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a gnss by id"""

    id = gnss.id

    await session.delete(gnss)
    await session.commit()

    return id
