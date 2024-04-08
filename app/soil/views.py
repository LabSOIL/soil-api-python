from fastapi import APIRouter
from app.soil.profiles.models import (
    SoilProfile,
    SoilProfileCreate,
    SoilProfileRead,
    SoilProfileUpdate,
)
from app.soil.types.models import (
    SoilType,
    SoilTypeCreate,
    SoilTypeRead,
    SoilTypeUpdate,
)

from app.generic.router import ReactAdminRouter

router = APIRouter()


soil_types = ReactAdminRouter(
    name_singular="soil type",
    prefix="/types",
    db_model=SoilType,
    read_model=SoilTypeRead,
    create_model=SoilTypeCreate,
    update_model=SoilTypeUpdate,
)
soil_profiles = ReactAdminRouter(
    name_singular="soil profiles",
    prefix="/profiles",
    db_model=SoilProfile,
    read_model=SoilProfileRead,
    create_model=SoilProfileCreate,
    update_model=SoilProfileUpdate,
)

router.include_router(soil_types.router, prefix=soil_types.prefix)
router.include_router(soil_profiles.router, prefix=soil_profiles.prefix)
