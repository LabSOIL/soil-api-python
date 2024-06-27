from app.gnss.models import GNSS, GNSSCreate, GNSSRead, GNSSUpdate
from app.db import get_session, AsyncSession
from fastapi import (
    Depends,
    APIRouter,
    Query,
    Response,
    HTTPException,
)
from uuid import UUID
from app.crud import CRUD
from app.utils.funcs import decode_base64
from app.config import config
import xml.etree.ElementTree as ET
import datetime
import pyproj

router = APIRouter()


crud = CRUD(GNSS, GNSSRead, GNSSCreate, GNSSUpdate)


def parse_gpx(gpx_data):
    # Define the XML namespaces used in the GPX file
    ns = {
        "gpx": "http://www.topografix.com/GPX/1/1",
        "gpxx": "http://www.garmin.com/xmlschemas/GpxExtensions/v3",
        "wptx1": "http://www.garmin.com/xmlschemas/WaypointExtension/v1",
        "gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
    }

    root = ET.fromstring(gpx_data)

    waypoints = []
    for wpt in root.findall("gpx:wpt", ns):
        latitude = float(wpt.attrib["lat"])
        longitude = float(wpt.attrib["lon"])

        # Find elevation element
        ele_element = wpt.find("gpx:ele", ns)
        elevation = (
            float(ele_element.text)
            if ele_element is not None and ele_element.text
            else None
        )

        # Find time element
        time_element = wpt.find("gpx:time", ns)
        time = time_element.text if time_element is not None else None

        # Find name element
        name_element = wpt.find("gpx:name", ns)
        name = name_element.text if name_element is not None else None

        # Find comment element
        cmt_element = wpt.find("gpx:cmt", ns)
        comment = cmt_element.text if cmt_element is not None else None

        # Find symbol element
        sym_element = wpt.find("gpx:sym", ns)
        symbol = sym_element.text if sym_element is not None else None

        # Extract extensions if present
        extensions = {}
        extensions_element = wpt.find("gpx:extensions", ns)
        if extensions_element is not None:
            ogr_id_element = extensions_element.find(
                "wptx1:WaypointExtension/wptx1:Depth", ns
            )
            extensions["ogr_id"] = (
                float(ogr_id_element.text)
                if ogr_id_element is not None and ogr_id_element.text
                else None
            )

        # Fix time to be without timezone
        if time:
            time = datetime.datetime.fromisoformat(time).replace(tzinfo=None)

        # Convert lat lon to x and y with the SRID defined in the config
        transformer = pyproj.Transformer.from_crs(
            "EPSG:4326", f"EPSG:{str(config.SRID)}", always_xy=True
        )
        x, y = transformer.transform(longitude, latitude)

        waypoints.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "x": x,
                "y": y,
                "elevation": elevation,
                "time": time,
                "name": name,
                "comment": comment,
                "symbol": symbol,
                "extensions": extensions,
            }
        )

    return waypoints


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
    gnss_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    res = await crud.get_model_by_id(model_id=gnss_id, session=session)

    if not res:
        raise HTTPException(status_code=404, detail=f"ID: {gnss_id} not found")
    return res


async def create_one(
    data: dict,
    session: AsyncSession,
) -> list[GNSS]:
    """Create a single gnss

    To be used in both create one and create many endpoints
    """

    gpx_data, filetype = decode_base64(data["data_base64"])
    if filetype != "gpx":
        raise HTTPException(
            status_code=400,
            detail="Only GPX files are supported",
        )
    parsed_data = parse_gpx(gpx_data)

    objs = []
    for row in parsed_data:
        obj = GNSS(
            latitude=row["latitude"],
            longitude=row["longitude"],
            elevation_gps=row["elevation"],
            time=row["time"],
            name=row["name"],
            comment=row["comment"],
            original_filename=data["filename"],
            x=row["x"],
            y=row["y"],
        )

        objs.append(obj)

    session.add_all(objs)
    await session.commit()

    return objs


async def update_one(
    gnss_id: UUID,
    gnss_update: GNSSUpdate,
    session: AsyncSession = Depends(get_session),
) -> GNSS:
    """Update a single gnss"""

    obj = await get_one(gnss_id, session=session)

    update_data = gnss_update.model_dump(exclude_unset=True)

    obj.sqlmodel_update(update_data)

    session.add(obj)
    await session.commit()
    await session.refresh(obj)

    return obj
