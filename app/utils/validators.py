import shapely
from geoalchemy2.elements import WKBElement
import pyproj
from app.config import config
from app.utils.funcs import resize_base64_image
from typing import Any


def convert_wkb_to_x_y(
    cls,
    values: Any,
) -> dict:
    """Form the geometry from the X and Y coordinates"""

    if isinstance(values.geom, WKBElement):
        if values.geom is not None:
            shapely_obj = shapely.wkb.loads(str(values.geom))
            if shapely_obj is not None:
                mapping = shapely.geometry.mapping(shapely_obj)
                values.coord_srid = values.geom.srid
                values.coord_x = mapping["coordinates"][0]
                values.coord_y = mapping["coordinates"][1]
                values.coord_z = mapping["coordinates"][2]
                values.geom = mapping

                # Set the latitude and longitude by reprojecting to WGS84
                transformer = pyproj.Transformer.from_crs(
                    f"EPSG:{str(config.SRID)}", "EPSG:4326", always_xy=True
                )
                values.longitude, values.latitude, _ = transformer.transform(
                    values.coord_x, values.coord_y, values.coord_z
                )

    elif isinstance(values.geom, dict):
        if values.geom is not None:
            values.coord_x = values.geom["coordinates"][0]
            values.coord_y = values.geom["coordinates"][1]
            values.coord_z = values.geom["coordinates"][2]
            values.geom = values.geom

            # Set the latitude and longitude by reprojecting to WGS84
            transformer = pyproj.Transformer.from_crs(
                f"EPSG:{str(config.SRID)}", "EPSG:4326", always_xy=True
            )
            values.longitude, values.latitude, _ = transformer.transform(
                values.coord_x, values.coord_y, values.coord_z
            )

    else:
        values.coord_x = None
        values.coord_y = None
        values.coord_z = None

    return values


def convert_x_y_to_wkt(cls, values: Any) -> Any:
    """Convert the X and Y coordinates to a WKT geometry"""

    # Encode the SRID into the WKT
    values.geom = shapely.wkt.dumps(
        shapely.geometry.Point(values.coord_x, values.coord_y, values.coord_z),
    )

    return values


def resize_image(cls, values: Any) -> Any:
    """Resize the image"""

    if values.image is not None:
        values.image = resize_base64_image(values.image, config.IMAGE_MAX_SIZE)

    return values


def empty_string_to_none(cls, values):
    """Convert empty strings for float and datetime fields to None."""

    for key, value in values.items():
        if isinstance(value, str) and not value:
            values[key] = None
    return values


def resize_images(cls, values: Any) -> Any:
    """Resize the images"""

    if values.photo is not None:
        values.photo = resize_base64_image(values.photo, config.IMAGE_MAX_SIZE)

    if values.soil_diagram is not None:
        values.soil_diagram = resize_base64_image(
            values.soil_diagram, config.IMAGE_MAX_SIZE
        )

    return values


def convert_wkb_to_json(cls, values: Any) -> Any:
    """Convert the WKBElement to a shapely mapping"""

    if isinstance(values.geom, WKBElement):

        values.geom = shapely.geometry.mapping(
            shapely.wkb.loads(str(values.geom))
        )
    return values
