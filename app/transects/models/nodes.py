from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.plots.models import Plot
    from app.transects.models.transects import Transect


class TransectNodeBase(SQLModel):
    plot_id: UUID = Field(
        foreign_key="plot.id",
        index=True,
        nullable=False,
    )
    transect_id: UUID = Field(
        foreign_key="transect.id",
        index=True,
        nullable=False,
    )
    order: int = Field(
        default=0,
        nullable=False,
    )


class TransectNode(TransectNodeBase, table=True):
    __table_args__ = (
        UniqueConstraint(
            "transect_id",
            "plot_id",
            name="no_same_link_constraint",
        ),
        UniqueConstraint(
            "order",
            "transect_id",
            name="no_same_order_constraint",
        ),
        # Primary key is composite of transect_id and order
    )

    id: UUID = Field(
        default_factory=uuid4,
        index=True,
        nullable=False,
        primary_key=True,
    )


class TransectNodeRead(TransectNodeBase):
    pass


class TransectNodeUpdate(TransectNodeBase):
    pass
