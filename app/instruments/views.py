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
import csv

router = APIRouter()


@router.get("/{id}", response_model=InstrumentExperimentRead)
async def get_instrument_experiment(
    obj: InstrumentExperiment = Depends(get_one),
) -> InstrumentExperimentRead:
    """Get an experiment by id"""

    return obj


@router.get("/{id}/raw")
async def get_instrument_experiment_rawdata(
    obj: InstrumentExperiment = Depends(get_one),
) -> Any:
    """Get an experiment's raw data by id, and all of its channels as CSV

    The time column is equivalent for each channel, the channel header is
    `channel_name` of each channel, and the value to fill is `raw_values`
    """

    header = ["Time/s"]
    # Sort channels by channel_name
    channels = sorted(obj.channels, key=lambda x: x.channel_name)
    header += [f"{channel.channel_name}" for channel in channels]

    # Form CSV by looping through each column and its data using the structure
    # defined in the docstring
    csv_data = [header]
    for i in range(len(obj.channels[0].raw_values)):
        row = [obj.channels[0].time_values[i]]
        row += [channel.raw_values[i] for channel in channels]
        csv_data.append(row)

    return csv_data


@router.get("/{id}/filtered")
async def get_instrument_experiment_baseline_filtered_data(
    obj: InstrumentExperiment = Depends(get_one),
) -> Any:
    """Get an experiment's baseline filtered data as CSV for each sample

    The time start values have been reduced to 0 and no longer represent the
    actual time values from the instrument, but rather the duration of the
    sample.
    """

    # Extract all sample slices from the integral table and combine them into a
    # single list with channel prefixes, get the baseline_values for the ranges
    # defined by the start and end values
    samples = []
    for channel in obj.channels:
        for result in channel.integral_results:
            result["channel_name"] = channel.channel_name
            result["column"] = (
                (
                    f"{channel.channel_name}_"
                    f"{result.get('sample_name', f'undefined')}"
                )
                .lower()
                .replace(" ", "_")
            )
            # Get baseline data, the data matches the time values, but they are
            # incremented in steps, not incremental indices, so we will need
            # to find the index of the start and end values in the time_values
            # to get the corresponding baseline_values index
            start_index = channel.time_values.index(result["start"])
            end_index = channel.time_values.index(result["end"])
            result["baseline_values"] = channel.baseline_values[
                start_index:end_index
            ]

            samples.append(result)

    # Check all column names are unique if not, just add the enumerator
    for i, result in enumerate(samples):
        for j, result2 in enumerate(samples):
            if i != j and result["column"] == result2["column"]:
                samples[i]["column"] = f"{result['column']}_{i}"

    samples = sorted(samples, key=lambda x: x["column"])

    # Adjust time for each sample such that the start is at 0
    for result in samples:
        result["adjusted_end"] = result["end"] - result["start"]
        result["adjusted_start"] = 0

    # Form CSV header with time and defined column name from above
    header = ["time/s"]
    header += [f"{result['column']}" for result in samples]

    # Initialize csv_data with header
    csv_data = [header]

    time_step = int(  # Get the time step from the first channel
        obj.channels[0].time_values[1] - obj.channels[0].time_values[0]
    )

    # Find the maximum time value of the longest sample in duration
    max_time = max(result["end"] for result in samples)

    # Loop through each time value and fill the row with the corresponding
    # baseline filterd value, starting the time at 0 and incrementing by the
    # time step. The max time is the max time value of the longest
    # sample in duration
    for i, time in enumerate(range(0, max_time, time_step)):
        row = [time]
        empty_data = 0
        for result in samples:
            # We just need to add the data sequentially for all the samples
            # the time doesn't matter, so we just can use the index. But we
            # will need to be sure that the index exists otherwise we will
            # get an index error
            try:
                row.append(result["baseline_values"][i])
            except IndexError:
                empty_data += 1
                row.append(None)

        # Stop when there is no data left
        if empty_data == len(samples):
            break

        csv_data.append(row)

    return csv_data


@router.get("/{id}/summary")
async def get_instrument_experiment_summary_data(
    obj: InstrumentExperiment = Depends(get_one),
) -> Any:
    """Create a CSV return that returns the channel integral data"""

    header = ["measurement"]
    channels = sorted(obj.channels, key=lambda x: x.channel_name)

    # Find the maximum number of samples
    max_samples = max(len(channel.integral_results) for channel in channels)

    # Construct the header
    for i in range(1, max_samples + 1):
        header += [
            f"sample{i}_start",
            f"sample{i}_end",
            f"sample{i}_electrons_transferred_mol",
            f"sample{i}_sample_name",
        ]

    # Create CSV rows
    csv_data = [header]
    for channel in channels:
        row = [channel.channel_name]
        for sample in channel.integral_results:
            row += [
                sample.get("start", "nan"),
                sample.get("end", "nan"),
                sample.get("area", "nan"),
                sample.get("sample_name", "nan"),
            ]
        # Fill remaining values with 'nan' if the channel has fewer samples
        remaining_samples = max_samples - len(channel.integral_results)
        row += ["nan"] * (
            remaining_samples * 3
        )  # Adjust multiplier if peak_time and peak_value are included
        csv_data.append(row)

    return csv_data


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
