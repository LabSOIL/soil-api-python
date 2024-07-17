import numpy as np
from typing import List, Dict
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


def integrate_coulomb_as_mole(
    y: np.ndarray, x: np.ndarray, method: str = "trapz"
) -> float:
    """Calculate the integral of the x and y values and convert to moles

    The Faraday constant is used to convert the integral to moles.

    Parameters
    ----------
    y : np.ndarray
        The y values as electrical current to integrate
    x : np.ndarray
        The x values to integrate
    method : str, optional
        The method to use when calculating the integral, by default
        'trapz', to use the Simpson's rule use 'simpson'

    Returns
    -------
    float
        The integral of the x and y values converted to moles
    """

    if method == "trapz":
        area = np.trapz(y=y, x=x)
    elif method == "simpson":
        area = simpson(y=y, x=x)
    else:
        raise ValueError(
            f"Integration method '{method}' not "
            "supported, use 'trapz' or 'simpson'"
        )

    # Convert coulombs to moles using Faraday constant
    area /= physical_constants["Faraday constant"][0]

    return area


def calculate_integral_for_range(
    x_values: np.ndarray,
    y_values: np.ndarray,
    integration_method: str = "simpson",
) -> float:
    """Calculates the area under the curve using the specified method and converts to moles.

    Parameters
    ----------
    x_values : np.ndarray
        The x-values for the integration.
    y_values : np.ndarray
        The y-values for the integration.
    integration_method : str, optional
        The method to use for integration, by default 'simpson'.

    Returns
    -------
    float
        The area under the curve converted to moles.
    """
    return integrate_coulomb_as_mole(
        y_values, x_values, method=integration_method
    )


def calculate_integrals_for_pairs(
    pairs: List[Dict[str, Dict[str, float]]],
    baseline_values: np.ndarray,
    time_values: np.ndarray,
    integration_method: str = "simpson",
) -> List[Dict[str, float]]:
    """Calculates the integral for each pair of start and end points.

    Parameters
    ----------
    pairs : List[Dict[str, Dict[str, float]]]
        List of dictionaries with start and end points.
    baseline_values : np.ndarray
        The y-values for the integration.
    time_values : np.ndarray
        The x-values for the integration.
    integration_method : str, optional
        The method to use for integration, by default 'simpson'.

    Returns
    -------
    List[Dict[str, float]]
        List of dictionaries with start, end, and area.
    """
    integration_results = []

    for pair in pairs:
        start = pair["start"]["x"]
        end = pair["end"]["x"]

        # Get indices for the start and end points
        start_index = np.where(time_values == start)[0][0]
        end_index = np.where(time_values == end)[0][0]

        # Get X and Y values between start and end
        x_values = time_values[start_index : end_index + 1]
        y_values = baseline_values[start_index : end_index + 1]

        # Calculate the integral for this range
        area = calculate_integral_for_range(
            x_values, y_values, integration_method
        )

        integration_results.append(
            {
                "start": start,
                "end": end,
                "area": area,
                "sample_name": pair["sample_name"],
            }
        )

    # Sort the list in order of the start point
    integration_results = sorted(integration_results, key=lambda x: x["start"])

    return integration_results
