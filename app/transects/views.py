from app.transects.models.transects import (
    TransectRead,
    Transect,
    TransectCreate,
    TransectUpdate,
)
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from sqlmodel import select
from uuid import UUID
from typing import Any
from app.crud import CRUD
from app.plots.models import Plot
from app.transects.models.nodes import TransectNode

router = APIRouter()
crud = CRUD(Transect, TransectRead, TransectCreate, TransectUpdate)


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
    transect_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    res = await crud.get_model_by_id(model_id=transect_id, session=session)

    if not res:
        raise HTTPException(
            status_code=404, detail=f"ID: {transect_id} not found"
        )
    return res


@router.get("/{transect_id}", response_model=TransectRead)
async def get_transect(
    # session: AsyncSession = Depends(get_session),
    # *,
    obj: CRUD = Depends(get_one),
) -> TransectRead:
    """Get a transect by id"""

    return obj


@router.get("", response_model=list[TransectRead])
async def get_all_transects(
    response: Response,
    transects: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[TransectRead]:
    """Get all Transect data"""

    return transects


@router.post("", response_model=TransectRead)
async def create_transect(
    transect: TransectCreate,
    session: AsyncSession = Depends(get_session),
) -> TransectRead:
    """Creates a transect data record"""

    transect_dict = transect.model_dump()
    transect_dict.pop("nodes", None)

    transect_obj = Transect.model_validate(transect_dict)
    transect_obj.nodes = []

    session.add(transect_obj)

    await session.commit()
    await session.refresh(transect_obj)

    for i, node in enumerate(transect.nodes):
        # Get the plot objects for each id in nodes and replace nodes with list
        res = await session.exec(select(Plot).where(Plot.id == node.id))
        obj = res.one()

        # Create Transect Node from plot and transect

        node_obj = TransectNode(
            plot_id=obj.id,
            transect_id=transect_obj.id,
            order=i,
        )
        session.add(node_obj)
        await session.commit()
        await session.refresh(node_obj)

    await session.refresh(transect_obj)

    return transect_obj


@router.put("/{transect_id}", response_model=TransectRead)
async def update_transect(
    transect_update: TransectUpdate,
    *,
    transect: TransectRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> TransectRead:
    """Update a transect by id"""

    update_data = transect_update.model_dump(exclude_unset=True)
    transect.sqlmodel_update(update_data)

    session.add(transect)
    await session.commit()
    await session.refresh(transect)

    return transect


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


@router.delete("/{transect_id}")
async def delete_transect(
    transect: TransectRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a transect by id"""

    await session.delete(transect)
    await session.commit()

    return {"ok": True}
