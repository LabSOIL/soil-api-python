from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from uuid import UUID, uuid4
from typing import TYPE_CHECKING
import datetime
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from app.soil.profiles.models import SoilProfile
    from app.plots.models import Plot


class SoilTypeBase(SQLModel):
    name: str = Field(default=None, index=True)
    description: str
    last_updated: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        title="Last Updated",
        description="Date and time when the record was last updated",
        sa_column_kwargs={
            "onupdate": func.now(),
            "server_default": func.now(),
        },
    )


class SoilType(SoilTypeBase, table=True):
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
    soil_profiles: "SoilProfile" = Relationship(
        back_populates="soil_type",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class SoilTypeRead(SoilTypeBase):
    id: UUID


class SoilTypeCreate(SoilTypeBase):
    pass


class SoilTypeUpdate(SoilTypeBase):
    pass
