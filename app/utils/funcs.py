from fastapi import HTTPException
import base64
import io
from PIL import Image
import httpx
import tenacity
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import CRUD
from uuid import UUID
import shapely
from geoalchemy2 import Geometry, WKBElement
from shapely.geometry import shape, mapping


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


@tenacity.retry
async def get_elevation_swisstopo(
    x: float,
    y: float,
    srid: int = 2056,
) -> float:
    """Get the elevation from the Swiss API"""

    url = (
        f"https://api3.geo.admin.ch/rest/services/height"
        f"?easting={x}&northing={y}&sr={srid}&format=json"
        f"&geometryFormat=geojson"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()

    if not data.get("height"):
        raise HTTPException(
            status_code=400,
            detail=f"Error fetching elevation: {data}",
        )

    return data["height"]


async def set_elevation_to_db_obj(
    id: UUID,
    crud_instance: CRUD,
    session: AsyncSession,
) -> None:
    """With the given id, fetch the object from the database and set the
    elevation

    Retry and wait until the elevation is fetched from the Swiss API

    The read and update models are given to return the object with the
    elevation unwrapped from the geom field
    """

    obj = await crud_instance.get_model_by_id(model_id=id, session=session)

    # Unwrap the geom wkb field, get the elevation and set it to the object
    geom = shapely.wkb.loads(bytes(obj.geom.data))
    x, y = geom.centroid.x, geom.centroid.y
    z = await get_elevation_swisstopo(x, y)

    obj.geom = shapely.wkt.dumps(shapely.geometry.Point(x, y, z))

    session.add(obj)
    await session.commit()
    await session.refresh(obj)

    return obj
