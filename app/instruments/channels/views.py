from fastapi import Depends, APIRouter, Response
from app.crud import CRUD
from app.instruments.channels.services import (
    get_count,
    get_data,
    get_one,
    update_one,
)
from app.instruments.channels.models import (
    InstrumentExperimentChannel,
    InstrumentExperimentChannelRead,
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


@router.put("/{id}", response_model=InstrumentExperimentChannelRead)
async def update_instrument_experiment_channel(
    obj: InstrumentExperimentChannel = Depends(update_one),
) -> InstrumentExperimentChannelRead:
    """Update a instrument_experiment_channel by id"""

    return obj
