from sqlmodel import (
    SQLModel,
    Field,
    UniqueConstraint,
    Relationship,
)
from uuid import uuid4, UUID
from SecretColors import Palette
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.areas.models import Area


class ProjectBase(SQLModel):
    name: str
    description: str | None = None
    color: str = Field(default_factory=Palette().random)


class Project(ProjectBase, table=True):
    __table_args__ = (
        UniqueConstraint("id"),
        UniqueConstraint("name"),
    )
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

    areas: list["Area"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: UUID


class ProjectUpdate(ProjectBase):
    pass
