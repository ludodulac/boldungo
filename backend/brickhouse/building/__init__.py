"""Building domain models and validation helpers."""

from .models import (
    Appearance,
    AppearanceSection,
    BuildingModel,
    Facade,
    Metadata,
    Opening,
    OpeningType,
    OpeningVisualDescription,
    Position3D,
    RidgeDirection,
    Roof,
    RoofType,
    SourceInfo,
    SourceKind,
    Volume,
    VolumeShape,
    WindowStyle,
)
from .validation import load_building_model

__all__ = [
    "Appearance",
    "AppearanceSection",
    "BuildingModel",
    "Facade",
    "Metadata",
    "Opening",
    "OpeningType",
    "OpeningVisualDescription",
    "Position3D",
    "RidgeDirection",
    "Roof",
    "RoofType",
    "SourceInfo",
    "SourceKind",
    "Volume",
    "VolumeShape",
    "WindowStyle",
    "load_building_model",
]
