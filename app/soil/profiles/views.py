from fastapi import APIRouter
from app.soil.profiles.models import (
    SoilProfile,
    SoilProfileCreate,
    SoilProfileRead,
    SoilProfileUpdate,
)

from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from uuid import UUID
from app.crud import CRUD
import json

router = APIRouter()
crud = CRUD(SoilProfile, SoilProfileRead, SoilProfileCreate, SoilProfileUpdate)


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


@router.get("/{soil_profile_id}", response_model=SoilProfileRead)
async def get_soil_profile(
    # session: AsyncSession = Depends(get_session),
    # *,
    obj: CRUD = Depends(get_one),
) -> SoilProfileRead:
    """Get a soil profile by id"""

    return obj


@router.get("", response_model=list[SoilProfileRead])
async def get_all_soil_profiles(
    response: Response,
    soil_profiles: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[SoilProfileRead]:
    """Get all SoilProfile data"""

    return soil_profiles


@router.post("", response_model=SoilProfileRead)
async def create_soil_profile(
    soil_profile: SoilProfileCreate,
    session: AsyncSession = Depends(get_session),
) -> SoilProfileRead:
    """Creates a soil profile data record"""

    obj = SoilProfile.model_validate(soil_profile)

    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


@router.put("/{soil_profile_id}", response_model=SoilProfileRead)
async def update_soil_profile(
    soil_profile_update: SoilProfileUpdate,
    *,
    soil_profile: SoilProfileRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> SoilProfileRead:
    """Update a soil profile by id"""

    update_data = soil_profile_update.model_dump(exclude_unset=True)
    soil_profile.sqlmodel_update(update_data)

    session.add(soil_profile)
    await session.commit()
    await session.refresh(soil_profile)

    return soil_profile


@router.delete("/profiles/{soil_profile_id}")
async def delete_soil_profile(
    soil_profile: SoilProfileRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a soil profile by id"""

    await session.delete(soil_profile)
    await session.commit()

    return {"ok": True}
