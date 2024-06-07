from fastapi import HTTPException
import base64
import base64
import io
from PIL import Image


def decode_base64(value: str) -> tuple[bytes, str]:
    """Decode base64 string to csv bytes"""
    # Split the string using the comma as a delimiter
    data_parts = value.split(",")

    # Extract the data type and base64-encoded content
    if "text/csv" in data_parts[0]:
        type = "csv"
    elif "gpx" in data_parts[0]:
        type = "gpx"
    else:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and GPX files are supported",
        )

    base64_content = data_parts[1]
    rawdata = base64.b64decode(base64_content)

    return rawdata, type


def resize_base64_image(data: str, max_size: int) -> str:
    """Decode a base64 image and resize the image to a maximum of 500px"""

    try:
        # Decode the base64 string
        if data.startswith("data:image"):
            data = data.split(",")[1]

        img_data = base64.b64decode(data)

        # Open the image and resize
        img = Image.open(io.BytesIO(img_data))
        img.thumbnail((max_size, max_size))

        # Convert the image back to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        img_str = f"data:image/png;base64,{img_str}"

    except Exception as e:
        raise ValueError(f"Error decoding image: {e}")
    return img_str
