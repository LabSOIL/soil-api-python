from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from uuid import UUID, uuid4
import datetime
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from app.transects.models.nodes import TransectNode

if TYPE_CHECKING:
    from app.plots.models import Plot


class TransectBase(SQLModel):
    name: str = Field(
        default=None,
        index=True,
    )
    description: str | None = Field(
        default=None,
    )
    date_created: datetime.datetime | None = Field(
        default=None,
        nullable=True,
        index=True,
    )
    last_updated: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        title="Last Updated",
        description="Date and time when the record was last updated",
        sa_column_kwargs={
            "onupdate": func.now(),
            "server_default": func.now(),
        },
    )


class Transect(TransectBase, table=True):
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

    nodes: list["Plot"] = Relationship(
        back_populates="transects",
        sa_relationship_kwargs={"lazy": "selectin"},
        link_model=TransectNode,
    )


class TransectRead(TransectBase):
    id: UUID


class TransectCreate(TransectBase):
    pass


class TransectUpdate(TransectBase):
    pass
