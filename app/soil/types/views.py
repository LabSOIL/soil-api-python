from app.soil.types.models import (
    SoilType,
    SoilTypeCreate,
    SoilTypeRead,
    SoilTypeUpdate,
)

from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from uuid import UUID
from app.crud import CRUD

router = APIRouter()
crud = CRUD(SoilType, SoilTypeRead, SoilTypeCreate, SoilTypeUpdate)


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
    soil_profile_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    res = await crud.get_model_by_id(model_id=soil_profile_id, session=session)

    if not res:
        raise HTTPException(
            status_code=404, detail=f"ID: {soil_profile_id} not found"
        )
    return res


@router.get("/{soil_type_id}", response_model=SoilTypeRead)
async def get_soil_type(
    obj: CRUD = Depends(get_one),
) -> SoilTypeRead:
    """Get a soil type by id"""

    return obj


@router.get("", response_model=list[SoilTypeRead])
async def get_all_soil_types(
    response: Response,
    soil_types: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[SoilTypeRead]:
    """Get all SoilType data"""

    return soil_types


@router.post("", response_model=SoilTypeRead)
async def create_soil_type(
    soil_type: SoilTypeCreate,
    session: AsyncSession = Depends(get_session),
) -> SoilTypeRead:
    """Creates a soil type data record"""

    obj = SoilType.model_validate(soil_type)

    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


@router.put("/{soil_type_id}", response_model=SoilTypeRead)
async def update_soil_type(
    soil_type_update: SoilTypeUpdate,
    *,
    soil_type: SoilTypeRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> SoilTypeRead:
    """Update a soil type by id"""

    update_data = soil_type_update.model_dump(exclude_unset=True)
    soil_type.sqlmodel_update(update_data)

    session.add(soil_type)
    await session.commit()
    await session.refresh(soil_type)

    return soil_type


@router.delete("/{soil_type_id}")
async def delete_soil_type(
    soil_type: SoilTypeRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a soil type by id"""

    await session.delete(soil_type)
    await session.commit()

    return {"ok": True}
