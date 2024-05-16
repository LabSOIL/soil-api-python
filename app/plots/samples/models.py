from geoalchemy2 import Geometry, WKBElement
from pydantic import model_validator
from sqlmodel import SQLModel, Field, Column, UniqueConstraint, Relationship
from typing import Any
from uuid import UUID, uuid4
from enum import Enum
from app.plots.models import Plot, PlotReadWithArea
import datetime
from sqlalchemy.sql import func


class PlotSampleNames(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class PlotSampleBase(SQLModel):
    name: PlotSampleNames = Field(
        default=None,
        index=True,
    )
    created_on: datetime.date | None = Field(
        default=None,
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
    upper_depth_cm: float = Field(
        nullable=False,
        title="Upper Depth (cm)",
        description="Upper depth in centimeters from the surface where the "
        "sample was taken",
    )
    lower_depth_cm: float = Field(
        nullable=False,
        title="Lower Depth (cm)",
        description="Lower depth in centimeters from the surface where the "
        "sample was taken",
    )
    plot_id: UUID = Field(
        nullable=False,
        index=True,
        foreign_key="plot.id",
        title="Plot ID",
        description="Unique identifier for the plot",
    )
    sample_weight: float = Field(
        nullable=False,
        title="Sample Weight (g)",
        description="Weight of the complete sample collected in the field "
        "(in grams)",
    )
    subsample_weight: float = Field(
        nullable=False,
        title="Subsample Weight",
        description="Weight of the subsample taken for pH, RH, and LOI "
        "measurements. May contain additional information like replicates",
    )
    subsample_replica_weight: float | None = Field(
        default=None,
        nullable=True,
        title="Subsample Replica Weight",
        description="Weight of the subsample replica taken for pH, RH, and "
        "LOI measurements",
    )
    ph: float | None = Field(
        default=None,
        nullable=True,
        title="pH",
        description="Average pH value. If replicates are used, this "
        "represents the average pH",
    )
    rh: float | None = Field(
        default=None,
        nullable=True,
        title="Residual Humidity (RH)",
        description="Residual humidity",
    )
    loi: float | None = Field(
        default=None,
        nullable=True,
        title="Loss on Ignition (LOI)",
        description="Loss on ignition during drying process",
    )
    mfc: float | None = Field(
        default=None,
        nullable=True,
        title="Moisture Factor Correction (MFC)",
        description="Moisture factor correction, representing the ratio of "
        "air-dried soil to oven-dried soil",
    )
    c: float | None = Field(
        default=None,
        nullable=True,
        title="Carbon (C) %",
        description="Percentage of carbon content in weight",
    )
    n: float | None = Field(
        default=None,
        nullable=True,
        title="Nitrogen (N) %",
        description="Percentage of nitrogen content in weight",
    )
    cn: float | None = Field(
        default=None,
        nullable=True,
        title="Carbon:Nitrogen Ratio",
        description="Ratio of carbon to nitrogen",
    )
    clay_percent: float | None = Field(
        default=None,
        nullable=True,
        title="Clay (%)",
        description="Percentage of clay by volume",
    )
    silt_percent: float | None = Field(
        default=None,
        nullable=True,
        title="Silt (%)",
        description="Percentage of silt by volume",
    )
    sand_percent: float | None = Field(
        default=None,
        nullable=True,
        title="Sand (%)",
        description="Percentage of sand by volume",
    )

    fe_ug_per_g: float | None = Field(
        default=None,
        nullable=True,
        title="Iron (Fe) in ug/g",
        description="Iron content in micrograms per gram (ug/g)",
    )
    na_ug_per_g: float | None = Field(
        default=None,
        nullable=True,
        title="Sodium (Na) in ug/g",
        description="Sodium content in micrograms per gram (ug/g)",
    )
    al_ug_per_g: float | None = Field(
        default=None,
        nullable=True,
        title="Aluminum (Al) in ug/g",
        description="Aluminum content in micrograms per gram (ug/g)",
    )
    k_ug_per_g: float | None = Field(
        default=None,
        nullable=True,
        title="Potassium (K) in ug/g",
        description="Potassium content in micrograms per gram (ug/g)",
    )
    ca_ug_per_g: float | None = Field(
        default=None,
        nullable=True,
        title="Calcium (Ca) in ug/g",
        description="Calcium content in micrograms per gram (ug/g)",
    )
    mg_ug_per_g: float | None = Field(
        default=None,
        nullable=True,
        title="Magnesium (Mg) in ug/g",
        description="Magnesium content in micrograms per gram (ug/g)",
    )
    mn_ug_per_g: float | None = Field(
        default=None,
        nullable=True,
        title="Manganese (Mn) in ug/g",
        description="Manganese content in micrograms per gram (ug/g)",
    )
    s_ug_per_g: float | None = Field(
        default=None,
        nullable=True,
        title="Sulfur (S) in ug/g",
        description="Sulfur content in micrograms per gram (ug/g)",
    )
    cl_ug_per_g: float | None = Field(
        default=None,
        nullable=True,
        title="Chlorine (Cl) in ug/g",
        description="Chlorine content in micrograms per gram (ug/g)",
    )
    p_ug_per_g: float | None = Field(
        default=None,
        nullable=True,
        title="Phosphorus (P) in ug/g",
        description="Phosphorus content in micrograms per gram (ug/g)",
    )
    si_ug_per_g: float | None = Field(
        default=None,
        nullable=True,
        title="Silicon (Si) in ug/g",
        description="Silicon content in micrograms per gram (ug/g)",
    )


class PlotSample(PlotSampleBase, table=True):
    __table_args__ = (
        UniqueConstraint("id"),
        UniqueConstraint(
            "name",
            "plot_id",
            name="unique_plot_sample",
        ),
    )
    iterator: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
        title="Sample Iterator",
        description="Unique identifier for the sample iterator",
    )
    id: UUID = Field(
        default_factory=uuid4,
        index=True,
        nullable=False,
        title="Sample ID",
        description="Unique identifier for the sample",
    )
    plot: "Plot" = Relationship(
        back_populates="samples", sa_relationship_kwargs={"lazy": "selectin"}
    )


class PlotSampleRead(PlotSampleBase):
    id: UUID


class PlotSampleReadWithPlot(PlotSampleRead):
    plot: "PlotReadWithArea"


class PlotSampleCreate(PlotSampleBase):
    pass


class PlotSampleUpdate(PlotSampleBase):
    pass


class PlotSampleCreateBatch(SQLModel):
    attachment: str  # Base64 encoded attachment


class PlotSampleCreateBatchRead(SQLModel):
    success: bool
    message: str
    errors: list[Any] = []
    qty_added: int
