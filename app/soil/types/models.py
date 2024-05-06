from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID
from typing import TYPE_CHECKING
from app.generic.models import ReactAdminDBModel

if TYPE_CHECKING:
    from app.soil.profiles.models import SoilProfile
    from app.plots.models import Plot


class SoilTypeBase(SQLModel):
    name: str = Field(default=None, index=True)
    description: str


class SoilType(SoilTypeBase, ReactAdminDBModel, table=True):
    soil_profiles: "SoilProfile" = Relationship(
        back_populates="soil_type",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    plots: "Plot" = Relationship(
        back_populates="soil_type",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class SoilTypeRead(SoilTypeBase):
    id: UUID


class SoilTypeCreate(SoilTypeBase):
    pass


class SoilTypeUpdate(SoilTypeBase):
    pass
