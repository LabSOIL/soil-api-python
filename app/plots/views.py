from app.plots.models import (
    Plot,
    PlotCreate,
    PlotRead,
    PlotUpdate,
)

from app.generic.router import ReactAdminRouter


plots = ReactAdminRouter(
    name_singular="plot",
    prefix="/plots",
    db_model=Plot,
    read_model=PlotRead,
    create_model=PlotCreate,
    update_model=PlotUpdate,
)
