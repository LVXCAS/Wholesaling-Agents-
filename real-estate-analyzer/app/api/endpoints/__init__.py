# This file makes it easier to import routers from this package.
# For example, from app.api.endpoints import properties_router

from .properties import router as properties_router
from .analysis import router as analysis_router # Assuming analysis.py also defines a router

# You can define an __all__ list if you want to control what `from . import *` imports
__all__ = [
    "properties_router",
    "analysis_router",
]
