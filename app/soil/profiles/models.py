from sqlmodel import SQLModel, Field, UniqueConstraint, Relationship
from uuid import uuid4, UUID
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.soil.types.models import SoilType


class SoilProfileBase(SQLModel):
    name: str = Field(default=None, index=True)
    description: str | None = Field(default=None)
    weather: str | None = Field(default=None)
    topography: str | None = Field(default=None)
    date_created: datetime.datetime | None = Field(
        default=None,
        nullable=True,
        index=True,
    )
    soil_type_id: UUID = Field(
        foreign_key="soiltype.id",
        default=None,
        index=True,
    )


class SoilProfile(SoilProfileBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    iterator: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    id: UUID = Field(
        default_factory=uuid4,
        index=True,
        nullable=False,
    )

    soil_type: "SoilType" = Relationship(
        back_populates="soil_profiles",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class SoilProfileRead(SoilProfileBase):
    id: UUID


class SoilProfileCreate(SoilProfileBase):
    pass


class SoilProfileUpdate(SoilProfileBase):
    pass
