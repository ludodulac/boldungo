"""Supplier-independent procurement contracts for BrickHouse."""

from .availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
    SupplierRoute,
)
from .bricklink import BrickLinkOrderDocuments, generate_bricklink_order_documents
from .catalog import PartCrosswalk, load_part_crosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .manifest import (
    generate_canonical_order_package,
    generate_canonical_order_package_from_bundle,
)
from .models import BagOrderManifest, CanonicalOrderPackage, OrderLine
from .packing import BagPackingSheet, KitPackingDocumentSet, generate_kit_packing_documents
from .readiness import OrderReadinessReport, assess_order_readiness
from .wobrick import WobrickOrderDocuments, generate_wobrick_order_documents

__all__ = [
    "BagOrderManifest",
    "BagPackingSheet",
    "BrickLinkOrderDocuments",
    "CanonicalOrderPackage",
    "ColorCrosswalk",
    "KitPackingDocumentSet",
    "OrderLine",
    "OrderReadinessReport",
    "PartColorAvailabilityEvidence",
    "PartColorAvailabilityRegistry",
    "PartCrosswalk",
    "SupplierRoute",
    "WobrickOrderDocuments",
    "assess_order_readiness",
    "generate_bricklink_order_documents",
    "generate_canonical_order_package",
    "generate_canonical_order_package_from_bundle",
    "generate_kit_packing_documents",
    "generate_wobrick_order_documents",
    "load_color_crosswalk",
    "load_part_crosswalk",
]
