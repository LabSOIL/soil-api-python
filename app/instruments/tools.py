#!/usr/bin/env python3
"""
This file contains the functions that support data transformations
during the processes in the SOIL lab.
"""
import numpy as np

# import pandas as pd

# from lab_toolbox.constants import constants
# import plotly.graph_objs as go
from typing import Dict, Tuple, List, Any

# from plotly.subplots import make_subplots
# from scipy.integrate import simpson
import os
import csv

# import pybaselines

# from scipy.constants import physical_constants
import datetime

from app.instruments.models.data import InstrumentExperimentData
from app.instruments.models.experiment import InstrumentExperimentRead
from app.instruments.channels.models import InstrumentExperimentChannel
from app.config import config


def find_header_start(input_text: str, header_text: str = "Time/s, ") -> int:
    """Find the start of the header in the file

    Iterates through the file until it finds the header start. The header is
    defined as a constant in the constants module.

    Parameters
    ----------
    filename_path : str
        The path to the file to find the header start of
    header_text : str
        The text to find in the file to indicate the start of the header

    Returns
    -------
    int
        The line number of the header start
    """

    for i, line in enumerate(input_text):
        print(i, line)
        if header_text in line.strip():
            return i

    raise ValueError("Could not find header start")


def import_data(
    decoded_data: str,
    header_start: int | None = None,
    index_column: str = "Time/s",
    delimiter: str = ",",
    encoding: str = "utf-8",
):
    """Import data from a file

    The header start variable is given to pandas, which is the value of the
    line number of the header start. If this is not given, the function will
    attempt to find the header start. If this is given manually it is important
    to not include empty lines in this count.

    For example, if the header starts on line 5 (starting at 0), but there are
    2 empty lines before the header, the header start should be 3.


    Parameters
    ----------
    filename_path : str
        The path to the file to import
    header_start : int, optional
        The line number of the header start, by default None

    Returns
    -------
    Dict[str, Measurement]
        A dictionary of measurements
    """

    # Find the header start
    if header_start is None:
        header_start = find_header_start(decoded_data)

    print(f"Header found at line {header_start}")

    # Import data
    # measurements = {}
    # with open(filename_path, "r") as f:

    reader = csv.reader(decoded_data, delimiter=delimiter)
    lines = list(reader)

    header = lines[header_start]
    print("HEADER:", header)

    # Seek the lines after the header until there is data (sometimes there are
    # empty lines after the header)
    data_start = header_start + 1
    while not lines[data_start]:
        data_start += 1

    # Create a channel for each column
    from app.instruments.models.channel import InstrumentExperimentChannel
    from app.instruments.models.experiment import InstrumentExperimentRead

    # Create an Experiment
    experiment = InstrumentExperimentRead(
        name="",
        date=datetime.datetime.now(),
        description="",
        filename="",
        device_filename="",
        data_source="",
        instrument_model="",
        init_e=0.0,
        sample_interval=0.0,
        run_time=0.0,
        quiet_time=0.0,
        sensitivity=0.0,
        samples=0,
    )
    for column in header[1:]:  # Skip the time column
        print(column.strip())

        channel = InstrumentExperimentChannel(
            channel_name=column.strip(),
            experiment_id="",
        )

    data = lines[data_start:]
    # for i, col in enumerate(data):
    # print(i, col)
    # values = [float(row[i]) for row in data]


def largest_triangle_three_buckets(data, threshold):
    """Downsample data using the Largest Triangle Three Buckets algorithm."""

    if len(data) <= threshold:
        return data

    bucket_size = (len(data) - 2) / (threshold - 2)
    downsampled = [data[0]]

    for i in range(1, threshold - 1):
        avg_x = avg_y = 0
        for j in range(
            int((i - 1) * bucket_size + 1), int(i * bucket_size + 1)
        ):
            avg_x += data[j]["time"]
            avg_y += data[j]["value"]
        avg_x /= bucket_size
        avg_y /= bucket_size

        range_start = int((i - 1) * bucket_size + 1)
        range_end = int(i * bucket_size + 1)
        max_area = area = -1

        for j in range(range_start, range_end):
            area = abs(
                (data[range_start - 1]["time"] - avg_x)
                * (data[j]["value"] - data[range_start - 1]["value"])
                - (data[range_start - 1]["time"] - data[j]["time"])
                * (avg_y - data[range_start - 1]["value"])
            )
            if area > max_area:
                max_area = area
                max_index = j

        downsampled.append(data[max_index])

    downsampled.append(data[-1])
    return downsampled


async def restructure_data_to_tabular(
    data: list[InstrumentExperimentData],
    channels: list[InstrumentExperimentChannel],
) -> list[dict]:
    """
    Restructure the data to a tabular format such that
    time: float
    i1/A
    i2/A
    ... etc
    [
        {'time': '5.000e+0', 'i1/A': 3.138e-5, 'i2/A': 2.966e-5, ...},
        {'time': '1.000e+1', 'i1/A': 2.905e-5, 'i2/A': 2.848e-5, ...},
    ]
    """
    # Create a mapping from channel ID to channel name
    channel_map = {channel.id: channel.channel_name for channel in channels}

    # Create a dictionary to hold the rows keyed by time
    rows = {}

    # Aggregate the data into rows
    for record in data:
        if record.time not in rows:
            rows[record.time] = {"Time/s": record.time}
        rows[record.time][channel_map[record.channel_id]] = record.value

    # Convert the rows dictionary to a list of dictionaries sorted by time
    sorted_rows = [rows[time] for time in sorted(rows.keys())]

    return sorted_rows


async def restructure_data_to_column_time(
    data: list[InstrumentExperimentData],
    channels: list[InstrumentExperimentChannel],
    threshold: int = config.INSTRUMENT_PLOT_DOWNSAMPLE_THRESHOLD,  # Adjust the threshold based on your needs
):
    """
    Restructure to provide for each channel, a series of data points
    For example:

    [
        {'channel': 'i1/A', 'data': [{'time': '5.000e+0', 'value': 3.138e-5}, ...]},
        {'channel': 'i2/A', 'data': [{'time': '5.000e+0', 'value': 2.966e-5}, ...]},
    ]
    """

    # Create a list of dictionaries for each channel
    channel_data = []

    for channel in channels:
        channel_name = channel.channel_name
        data_points = []

        for record in data:
            if record.channel_id == channel.id:
                data_points.append(
                    {"time": record.time, "value": record.value}
                )

        # Downsample the data points
        if len(data_points) > threshold:
            data_points = largest_triangle_three_buckets(
                data_points, threshold
            )

        channel_data.append({"channel": channel_name, "data": data_points})

    return channel_data
