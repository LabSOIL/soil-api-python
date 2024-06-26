import datetime
from sqlmodel import SQLModel, Field, UniqueConstraint
from uuid import UUID, uuid4
from sqlalchemy.sql import func


class GNSSBase(SQLModel):
    last_updated: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        title="Last Updated",
        description="Date and time when the record was last updated",
        sa_column_kwargs={
            "onupdate": func.now(),
            "server_default": func.now(),
        },
    )
    latitude: float | None = None
    longitude: float | None = None
    elevation_gps: float | None = None
    elevation_corrected: float | None = None
    time: datetime.datetime | None = None
    name: str | None
    comment: str | None = None
    original_filename: str | None = None


class GNSS(GNSSBase, table=True):
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


class GNSSRead(GNSSBase):
    id: UUID


class GNSSCreate(GNSSBase):
    pass


class GNSSCreateFromFile(SQLModel):
    data_base64: str
    filename: str


class GNSSUpdate(GNSSBase):
    pass
