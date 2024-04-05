from fastapi import Depends, APIRouter, Query, Response, Body, HTTPException
from sqlmodel import select
from app.db import get_session, AsyncSession
from app.soil.profiles.models import (
    SoilProfile,
    SoilProfileCreate,
    SoilProfileRead,
    SoilProfileUpdate,
)
from app.soil.types.models import (
    SoilType,
    SoilTypeCreate,
    SoilTypeRead,
    SoilTypeUpdate,
)
from uuid import UUID
from sqlalchemy import func
import json


router = APIRouter()


@router.get("/profiles/{soil_profile_id}", response_model=SoilProfileRead)
async def get_soil_profile(
    session: AsyncSession = Depends(get_session),
    *,
    soil_profile_id: UUID,
) -> SoilProfileRead:
    """Get a soil_profile by id"""
    res = await session.execute(
        select(SoilProfile).where(SoilProfile.id == soil_profile_id)
    )
    soil_profile = res.scalars().one_or_none()

    return soil_profile


@router.get("/profiles", response_model=list[SoilProfileRead])
async def get_soil_profiles(
    response: Response,
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get all soil_profiles"""

    sort = json.loads(sort) if sort else []
    range = json.loads(range) if range else []
    filter = json.loads(filter) if filter else {}

    query = select(SoilProfile)

    # Do a query to satisfy total count for "Content-Range" header
    count_query = select(func.count(SoilProfile.iterator))
    if len(filter):  # Have to filter twice for some reason? SQLModel state?
        for field, value in filter.items():
            for qry in [query, count_query]:  # Apply filter to both queries
                if isinstance(value, list):
                    qry = qry.where(getattr(SoilProfile, field).in_(value))
                elif field == "id":
                    qry = qry.where(getattr(SoilProfile, field) == value)
                else:
                    qry = qry.where(
                        getattr(SoilProfile, field).like(f"%{value}%")
                    )

    # Execute total count query (including filter)
    total_count_query = await session.execute(count_query)
    total_count = total_count_query.scalar_one()

    # Order by sort field params ie. ["name","ASC"]
    if len(sort) == 2:
        sort_field, sort_order = sort
        if sort_order == "ASC":
            query = query.order_by(getattr(SoilProfile, sort_field))
        else:
            query = query.order_by(getattr(SoilProfile, sort_field).desc())

    # Filter by filter field params ie. {"name":"bar"}
    if len(filter):
        for field, value in filter.items():
            if isinstance(value, list):
                query = query.where(getattr(SoilProfile, field).in_(value))
            elif field == "id":
                query = query.where(getattr(SoilProfile, field) == value)
            else:
                query = query.where(
                    getattr(SoilProfile, field).like(f"%{value}%")
                )

    if len(range) == 2:
        start, end = range
        query = query.offset(start).limit(end - start + 1)
    else:
        start, end = [0, total_count]  # For content-range header

    # Execute query
    results = await session.execute(query)
    soil_profiles = results.scalars().all()

    response.headers["Content-Range"] = (
        f"soil_profiles {start}-{end}/{total_count}"
    )

    return soil_profiles


@router.post("/profiles", response_model=SoilProfileRead)
async def create_soil_profile(
    soil_profile: SoilProfileCreate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> SoilProfileRead:
    """Creates a soil profile"""
    print(soil_profile)
    soil_profile = SoilProfile.from_orm(soil_profile)
    session.add(soil_profile)
    await session.commit()
    await session.refresh(soil_profile)

    return soil_profile


@router.put("/profiles/{soil_profile_id}", response_model=SoilProfileRead)
async def update_soil_profile(
    soil_profile_id: UUID,
    soil_profile_update: SoilProfileUpdate,
    session: AsyncSession = Depends(get_session),
) -> SoilProfileRead:
    res = await session.execute(
        select(SoilProfile).where(SoilProfile.id == soil_profile_id)
    )
    soil_profile_db = res.scalars().one()
    soil_profile_data = soil_profile_update.dict(exclude_unset=True)

    if not soil_profile_db:
        raise HTTPException(status_code=404, detail="SoilProfile not found")

    # Update the fields from the request
    for field, value in soil_profile_data.items():
        print(f"Updating: {field}, {value}")
        setattr(soil_profile_db, field, value)

    session.add(soil_profile_db)
    await session.commit()
    await session.refresh(soil_profile_db)

    return soil_profile_db


@router.delete("/profiles/{soil_profile_id}")
async def delete_soil_profile(
    soil_profile_id: UUID,
    session: AsyncSession = Depends(get_session),
    filter: dict[str, str] | None = None,
) -> None:
    """Delete a soil profile by id"""
    res = await session.execute(
        select(SoilProfile).where(SoilProfile.id == soil_profile_id)
    )
    soil_profile = res.scalars().one_or_none()

    if soil_profile:
        await session.delete(soil_profile)
        await session.commit()


@router.get("/types/{soil_type_id}", response_model=SoilTypeRead)
async def get_soil_type(
    session: AsyncSession = Depends(get_session),
    *,
    soil_type_id: UUID,
) -> SoilTypeRead:
    """Get a soil type by id"""
    res = await session.execute(
        select(SoilType).where(SoilType.id == soil_type_id)
    )
    soil_type = res.scalars().one_or_none()

    return soil_type


@router.get("/types", response_model=list[SoilTypeRead])
async def get_soil_types(
    response: Response,
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get all soil types"""

    sort = json.loads(sort) if sort else []
    range = json.loads(range) if range else []
    filter = json.loads(filter) if filter else {}

    query = select(SoilType)

    # Do a query to satisfy total count for "Content-Range" header
    count_query = select(func.count(SoilType.iterator))
    if len(filter):  # Have to filter twice for some reason? SQLModel state?
        for field, value in filter.items():
            for qry in [query, count_query]:  # Apply filter to both queries
                if isinstance(value, list):
                    qry = qry.where(getattr(SoilType, field).in_(value))
                elif field == "id":
                    qry = qry.where(getattr(SoilType, field) == value)
                else:
                    qry = qry.where(
                        getattr(SoilType, field).like(f"%{value}%")
                    )

    # Execute total count query (including filter)
    total_count_query = await session.execute(count_query)
    total_count = total_count_query.scalar_one()

    # Order by sort field params ie. ["name","ASC"]
    if len(sort) == 2:
        sort_field, sort_order = sort
        if sort_order == "ASC":
            query = query.order_by(getattr(SoilType, sort_field))
        else:
            query = query.order_by(getattr(SoilType, sort_field).desc())

    # Filter by filter field params ie. {"name":"bar"}
    if len(filter):
        for field, value in filter.items():
            if isinstance(value, list):
                query = query.where(getattr(SoilType, field).in_(value))
            elif field == "id":
                query = query.where(getattr(SoilType, field) == value)
            else:
                query = query.where(
                    getattr(SoilType, field).like(f"%{value}%")
                )

    if len(range) == 2:
        start, end = range
        query = query.offset(start).limit(end - start + 1)
    else:
        start, end = [0, total_count]  # For content-range header

    # Execute query
    results = await session.execute(query)
    soil_types = results.scalars().all()

    response.headers["Content-Range"] = (
        f"soil_types {start}-{end}/{total_count}"
    )

    return soil_types


@router.post("/types", response_model=SoilTypeRead)
async def create_soil_type(
    soil_type: SoilTypeCreate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> SoilTypeRead:
    """Creates a soil type"""
    print(soil_type)
    soil_type = SoilType.from_orm(soil_type)
    session.add(soil_type)
    await session.commit()
    await session.refresh(soil_type)

    return soil_type


@router.put("/types/{soil_type_id}", response_model=SoilTypeRead)
async def update_soil_type(
    soil_type_id: UUID,
    soil_type_update: SoilTypeUpdate,
    session: AsyncSession = Depends(get_session),
) -> SoilTypeRead:
    res = await session.execute(
        select(SoilType).where(SoilType.id == soil_type_id)
    )
    soil_type_db = res.scalars().one()
    soil_type_data = soil_type_update.dict(exclude_unset=True)

    if not soil_type_db:
        raise HTTPException(status_code=404, detail="Soil Type not found")

    # Update the fields from the request
    for field, value in soil_type_data.items():
        print(f"Updating: {field}, {value}")
        setattr(soil_type_db, field, value)

    session.add(soil_type_db)
    await session.commit()
    await session.refresh(soil_type_db)

    return soil_type_db


@router.delete("/types/{soil_type_id}")
async def delete_soil_type(
    soil_type_id: UUID,
    session: AsyncSession = Depends(get_session),
    filter: dict[str, str] | None = None,
) -> None:
    """Delete a soil type by id"""
    res = await session.execute(
        select(SoilType).where(SoilType.id == soil_type_id)
    )
    soil_type = res.scalars().one_or_none()

    if soil_type:
        await session.delete(soil_type)
        await session.commit()
