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

from app.instruments.channels.models import (
    InstrumentExperimentChannel,
    InstrumentExperimentChannelRead,
)
from app.config import config
from typing import List, Dict
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import numpy as np
import pybaselines
from scipy.constants import physical_constants
from scipy.integrate import simpson


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


def largest_triangle_three_buckets(x, y, threshold):
    """Downsample data using the Largest Triangle Three Buckets algorithm."""

    if len(x) <= threshold:
        return x, y

    bucket_size = (len(x) - 2) / (threshold - 2)
    downsampled_x = [x[0]]
    downsampled_y = [y[0]]

    for i in range(1, threshold - 1):
        avg_x = avg_y = 0
        for j in range(
            int((i - 1) * bucket_size + 1), int(i * bucket_size + 1)
        ):
            avg_x += x[j]
            avg_y += y[j]
        avg_x /= bucket_size
        avg_y /= bucket_size

        range_start = int((i - 1) * bucket_size + 1)
        range_end = int(i * bucket_size + 1)
        max_area = area = -1

        for j in range(range_start, range_end):
            area = abs(
                (x[range_start - 1] - avg_x) * (y[j] - y[range_start - 1])
                - (x[range_start - 1] - x[j]) * (avg_y - y[range_start - 1])
            )
            if area > max_area:
                max_area = area
                max_index = j

        downsampled_x.append(x[max_index])
        downsampled_y.append(y[max_index])

    downsampled_x.append(x[-1])
    downsampled_y.append(y[-1])
    return downsampled_x, downsampled_y


def calculate_spline(
    x: np.ndarray,
    y: np.ndarray,
    baseline_selected_points: List[float],
    interpolation_method: str,
) -> np.ndarray:
    fitter = pybaselines.Baseline(x, check_finite=False)
    pairs = np.array(
        [(bp, y[np.where(x == bp)][0]) for bp in baseline_selected_points]
    )

    if len(baseline_selected_points) < 4:
        spline = fitter.interp_pts(
            x.reshape(-1, 1),
            baseline_points=pairs,
            interp_method="linear",
        )[0]
    else:
        spline = fitter.interp_pts(
            x.reshape(-1, 1),
            baseline_points=pairs,
            interp_method=interpolation_method,
        )[0]

    return spline


def filter_baseline(y: np.ndarray, spline: np.ndarray) -> np.ndarray:
    return y - spline
