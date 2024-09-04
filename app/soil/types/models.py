from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from uuid import UUID, uuid4
from typing import TYPE_CHECKING
import datetime
from sqlalchemy.sql import func
from pydantic import model_validator
from app.utils.validators import resize_image

if TYPE_CHECKING:
    from app.soil.profiles.models import SoilProfile


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
    image: str | None = Field(
        default=None,
        description="Base64 encoded image",
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

    _resize_image = model_validator(mode="after")(resize_image)


class SoilTypeUpdate(SoilTypeBase):
    pass

    _resize_image = model_validator(mode="after")(resize_image)
