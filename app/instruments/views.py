from app.instruments.models.experiment import (
    InstrumentExperiment,
    InstrumentExperimentRead,
    InstrumentExperimentCreate,
    InstrumentExperimentUpdate,
)
from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from sqlmodel import select
from uuid import UUID
from typing import Any
from app.crud import CRUD
from app.plots.models import Plot
from app.instruments.services import (
    get_count,
    get_data,
    get_one,
    create_one,
    delete_one,
    delete_many,
    update_one,
)

router = APIRouter()


@router.get("/{id}", response_model=InstrumentExperimentRead)
async def get_instrument_experiment(
    obj: InstrumentExperiment = Depends(get_one),
) -> InstrumentExperimentRead:
    """Get an experiment by id"""

    return obj


@router.get("", response_model=list[InstrumentExperimentRead])
async def get_all_instrument_experiments(
    response: Response,
    obj: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[InstrumentExperimentRead]:
    """Get all InstrumentExperiment data"""

    return obj


@router.post("", response_model=InstrumentExperimentRead)
async def create_instrument_experiment(
    obj: InstrumentExperiment = Depends(create_one),
) -> InstrumentExperimentRead:
    """Creates a instrument_experiment data record"""

    return obj


@router.put("/{id}", response_model=InstrumentExperimentRead)
async def update_instrument_experiment(
    obj: InstrumentExperiment = Depends(update_one),
) -> InstrumentExperimentRead:
    """Update a instrument_experiment by id"""

    return obj


@router.delete("/batch", response_model=list[UUID])
async def delete_batch(
    deleted_ids: list[UUID] = Depends(delete_many),
) -> list[UUID]:
    """Delete by a list of ids"""

    return deleted_ids


@router.delete("/{id}", response_model=UUID)
async def delete_instrument_experiment(
    deleted_id: UUID = Depends(delete_one),
) -> UUID:
    """Delete a instrument_experiment by id"""

    return deleted_id
