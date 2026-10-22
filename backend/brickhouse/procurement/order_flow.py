"""Application boundary from a finished BrickExportBundle to "Commander mes pièces".

This module composes the existing downstream procurement contracts. It never
rebuilds reconstruction geometry, invents a BOM, or creates a second BagPlan.
"""

from __future__ import annotations

from brickhouse.bricks.export import BrickExportBundle

from .availability import PartColorAvailabilityRegistry
from .catalog import PartCrosswalk
from .colors import ColorCrosswalk
from .manifest import generate_canonical_order_package_from_bundle
from .supplier_package import (
    ExportableRoute,
    SupplierHandoffPackage,
    supplier_handoff_zip_bytes,
)
from .user_order import (
    UserOrderOptions,
    build_user_order_options,
    generate_handoff_from_user_order_option,
)


def get_order_options(
    bundle: BrickExportBundle,
    part_crosswalk: PartCrosswalk,
    *,
    availability: PartColorAvailabilityRegistry,
    color_crosswalk: ColorCrosswalk | None = None,
) -> UserOrderOptions:
    """Expose BrickLink/Wobrick choices from the finished export bundle."""

    package = generate_canonical_order_package_from_bundle(bundle)
    return build_user_order_options(
        package,
        part_crosswalk,
        availability=availability,
        appearance=bundle.appearance,
        color_crosswalk=color_crosswalk,
    )


def prepare_order(
    bundle: BrickExportBundle,
    route: ExportableRoute,
    part_crosswalk: PartCrosswalk,
    *,
    availability: PartColorAvailabilityRegistry,
    color_crosswalk: ColorCrosswalk | None = None,
) -> SupplierHandoffPackage:
    """Prepare the existing supplier handoff for one document-ready user choice."""

    package = generate_canonical_order_package_from_bundle(bundle)
    options = build_user_order_options(
        package,
        part_crosswalk,
        availability=availability,
        appearance=bundle.appearance,
        color_crosswalk=color_crosswalk,
    )
    option = options.for_route(route)
    return generate_handoff_from_user_order_option(
        option,
        package,
        part_crosswalk,
        availability=availability,
        appearance=bundle.appearance,
        color_crosswalk=color_crosswalk,
    )


def prepare_order_zip(
    bundle: BrickExportBundle,
    route: ExportableRoute,
    part_crosswalk: PartCrosswalk,
    *,
    availability: PartColorAvailabilityRegistry,
    color_crosswalk: ColorCrosswalk | None = None,
) -> bytes:
    """Return deterministic ZIP bytes for one document-ready supplier route."""

    handoff = prepare_order(
        bundle,
        route,
        part_crosswalk,
        availability=availability,
        color_crosswalk=color_crosswalk,
    )
    return supplier_handoff_zip_bytes(handoff)
