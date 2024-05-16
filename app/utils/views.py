from fastapi import Depends, APIRouter, Query, HTTPException
from sqlmodel import select
from app.db import get_session, AsyncSession
from sqlalchemy import func
from sqlmodel import SQLModel, Field
from geoalchemy2 import Geometry
from typing import Optional


router = APIRouter()


class HLAllgmeinZusammenfassungMerged(SQLModel, table=True):
    __tablename__ = "hlallgmein_zusammenfassung_merged"

    objectid: int = Field(default=None, primary_key=True)
    gridcode: Optional[int] = None
    lknr: Optional[int] = None
    aenderungsdatum: Optional[str] = Field(default=None, max_length=10)
    hl_klasse: Optional[str] = Field(default=None, max_length=10)
    hl_neigung_hang: Optional[str] = Field(default=None, max_length=512)
    shape_length: Optional[float] = None
    shape_area: Optional[float] = None
    shape: Optional[str] = Field(sa_column=Geometry("MULTIPOLYGON", 2056))


class Slope(SQLModel):
    slope_class: str


@router.get("/slope", response_model=Slope)
async def get_slope_class(
    x: float = Query(..., description="x coordinate"),
    y: float = Query(..., description="y coordinate"),
    srid: int = Query(2056, description="Spatial Reference Identifier"),
    session: AsyncSession = Depends(get_session),
) -> Slope:
    """Get an sensordata by id"""
    res = await session.exec(
        select(HLAllgmeinZusammenfassungMerged).where(
            func.ST_Intersects(
                HLAllgmeinZusammenfassungMerged.shape,
                func.ST_SetSRID(func.ST_MakePoint(x, y), srid),
            )
        )
    )

    obj = res.first()

    if not obj:
        return HTTPException(status_code=404, detail="No data found")

    return Slope(slope_class=obj.hl_neigung_hang)
