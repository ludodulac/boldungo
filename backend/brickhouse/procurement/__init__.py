"""Supplier-independent procurement contracts for BrickHouse."""

from .availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
    SupplierRoute,
)
from .bricklink import BrickLinkOrderDocuments, generate_bricklink_order_documents
from .catalog import PartCrosswalk, load_part_crosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .color_resolution import (
    PurchaseColorResolutionReport,
    color_resolution_csv,
    resolve_purchase_colors_from_appearance,
)
from .fulfillment import (
    FulfillmentReport,
    SupplierConfirmationLine,
    parse_supplier_confirmation_csv,
    supplier_confirmation_template_csv,
    validate_supplier_confirmation,
)
from .manifest import (
    generate_canonical_order_package,
    generate_canonical_order_package_from_bundle,
)
from .models import BagOrderManifest, CanonicalOrderPackage, OrderLine
from .packing import BagPackingSheet, KitPackingDocumentSet, generate_kit_packing_documents
from .readiness import OrderReadinessReport, assess_order_readiness
from .supplier_package import (
    SupplierHandoffPackage,
    generate_supplier_handoff_package,
    supplier_handoff_zip_bytes,
)
from .wobrick import WobrickOrderDocuments, generate_wobrick_order_documents

__all__ = [
    "BagOrderManifest",
    "BagPackingSheet",
    "BrickLinkOrderDocuments",
    "CanonicalOrderPackage",
    "ColorCrosswalk",
    "KitPackingDocumentSet",
    "FulfillmentReport",
    "OrderLine",
    "OrderReadinessReport",
    "PartColorAvailabilityEvidence",
    "PartColorAvailabilityRegistry",
    "PurchaseColorResolutionReport",
    "PartCrosswalk",
    "SupplierRoute",
    "SupplierHandoffPackage",
    "SupplierConfirmationLine",
    "WobrickOrderDocuments",
    "assess_order_readiness",
    "color_resolution_csv",
    "generate_bricklink_order_documents",
    "generate_canonical_order_package",
    "generate_canonical_order_package_from_bundle",
    "generate_kit_packing_documents",
    "generate_supplier_handoff_package",
    "generate_wobrick_order_documents",
    "load_color_crosswalk",
    "parse_supplier_confirmation_csv",
    "load_part_crosswalk",
    "resolve_purchase_colors_from_appearance",
    "supplier_handoff_zip_bytes",
    "supplier_confirmation_template_csv",
    "validate_supplier_confirmation",
]
