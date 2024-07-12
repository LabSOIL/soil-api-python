from app.db import get_session, AsyncSession
from fastapi import Depends, APIRouter, Query, Response, HTTPException
from sqlmodel import select
from uuid import UUID
from typing import Any
from app.crud import CRUD
from app.plots.models import Plot
from app.instruments.channels.services import (
    get_count,
    get_data,
    get_one,
    create_one,
    delete_one,
    delete_many,
    update_one,
)
from app.instruments.channels.models import (
    InstrumentExperimentChannel,
    InstrumentExperimentChannelRead,
    InstrumentExperimentChannelCreate,
    InstrumentExperimentChannelUpdate,
)

router = APIRouter()


@router.get("/{id}", response_model=InstrumentExperimentChannelRead)
async def get_instrument_experiment_channel(
    obj: InstrumentExperimentChannel = Depends(get_one),
) -> InstrumentExperimentChannelRead:
    """Get an experiment channel by id"""

    return obj


@router.get("", response_model=list[InstrumentExperimentChannelRead])
async def get_all_instrument_experiment_channels(
    response: Response,
    obj: CRUD = Depends(get_data),
    total_count: int = Depends(get_count),
) -> list[InstrumentExperimentChannelRead]:
    """Get all InstrumentExperimentChannel data"""

    return obj


@router.post("", response_model=InstrumentExperimentChannelRead)
async def create_instrument_experiment_channel(
    obj: InstrumentExperimentChannel = Depends(create_one),
) -> InstrumentExperimentChannelRead:
    """Creates a instrument_experiment_channel data record"""

    return obj


@router.put("/{id}", response_model=InstrumentExperimentChannelRead)
async def update_instrument_experiment_channel(
    obj: InstrumentExperimentChannel = Depends(update_one),
) -> InstrumentExperimentChannelRead:
    """Update a instrument_experiment_channel by id"""

    return obj


@router.delete("/batch", response_model=list[UUID])
async def delete_batch_channels(
    deleted_ids: list[UUID] = Depends(delete_many),
) -> list[UUID]:
    """Delete by a list of ids"""

    return deleted_ids


@router.delete("/{id}", response_model=UUID)
async def delete_instrument_experiment_channel(
    deleted_id: UUID = Depends(delete_one),
) -> UUID:
    """Delete a instrument_experiment_channel by id"""

    return deleted_id
