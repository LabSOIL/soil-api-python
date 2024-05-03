from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.config import config

from app.areas.views import router as areas_router
from app.sensors.views import router as sensors_router
from app.soil.views import router as soil_router
from app.transects.views import router as transects_router
from app.plots.views import plots as plots_router
from app.projects.views import router as projects_router

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


@app.get(
    "/healthz",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health() -> HealthCheck:
    """
    Endpoint to perform a healthcheck on for kubenernetes liveness and
    readiness probes.
    """
    return HealthCheck(status="OK")


app.include_router(
    areas_router,
    prefix=f"{config.API_V1_PREFIX}/areas",
    tags=["areas"],
)
app.include_router(
    sensors_router,
    prefix=f"{config.API_V1_PREFIX}/sensors",
    tags=["sensors"],
)
app.include_router(
    soil_router,
    prefix=f"{config.API_V1_PREFIX}/soil",
    tags=["soil"],
)
app.include_router(
    transects_router,
    prefix=f"{config.API_V1_PREFIX}/transects",
    tags=["transects"],
)
app.include_router(
    plots_router.router,
    prefix=f"{config.API_V1_PREFIX}/plots",
    tags=["plots"],
)
app.include_router(
    projects_router,
    prefix=f"{config.API_V1_PREFIX}/projects",
    tags=["projects"],
)
