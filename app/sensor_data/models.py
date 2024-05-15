from sqlmodel import SQLModel, Field, Column
from geoalchemy2 import Geometry
from uuid import uuid4, UUID
from typing import Any
import datetime
from sqlalchemy.sql import func


class AreaBase(SQLModel):
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


class Area(AreaBase, table=True):
    id: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    uuid: UUID = Field(
        default_factory=uuid4,
        index=True,
        nullable=False,
    )
    last_updated: datetime.datetime = Field(
        default=datetime.datetime.now,
        title="Last Updated",
        description="Date and time when the record was last updated",
    )


class AreaRead(AreaBase):
    id: int
    uuid: UUID


class AreaCreate(AreaBase):
    pass


class AreaUpdate(AreaBase):
    pass
