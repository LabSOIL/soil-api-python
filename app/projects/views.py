from app.projects.models import (
    ProjectRead,
    Project,
    ProjectCreate,
    ProjectUpdate,
)
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from sqlmodel import select
from uuid import UUID
from typing import Any
from app.crud import CRUD

router = APIRouter()
crud = CRUD(Project, ProjectRead, ProjectCreate, ProjectUpdate)


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
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    res = await crud.get_model_by_id(model_id=project_id, session=session)

    if not res:
        raise HTTPException(
            status_code=404, detail=f"ID: {project_id} not found"
        )
    return res


@router.get("/{project_id}", response_model=ProjectRead)
async def get_Project(
    # session: AsyncSession = Depends(get_session),
    # *,
    obj: CRUD = Depends(get_one),
) -> ProjectRead:
    """Get a project by id"""

    return obj


@router.get("", response_model=list[ProjectRead])
async def get_all_Projects(
    response: Response,
    projects: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[ProjectRead]:
    """Get all Project data"""

    return projects


@router.post("", response_model=ProjectRead)
async def create_Project(
    project: ProjectCreate,
    session: AsyncSession = Depends(get_session),
) -> ProjectRead:
    """Creates a project data record"""

    obj = Project.model_validate(project)

    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


@router.put("/{project_id}", response_model=ProjectRead)
async def update_Project(
    project_update: ProjectUpdate,
    *,
    project: ProjectRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> ProjectRead:
    """Update a project by id"""

    update_data = project_update.model_dump(exclude_unset=True)
    project.sqlmodel_update(update_data)

    session.add(project)
    await session.commit()
    await session.refresh(project)

    return project


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


@router.delete("/{project_id}")
async def delete_Project(
    project: ProjectRead = Depends(get_one),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a project by id"""

    await session.delete(project)
    await session.commit()

    return {"ok": True}
