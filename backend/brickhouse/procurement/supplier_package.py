"""Deterministic supplier handoff packages.

A handoff package is the user-facing boundary between Boldüngo and a supplier.
It is generated only after route-specific readiness passes, and contains the
supplier upload file, exact master/bag picking sheets, labels, reconciliation,
and explicit no-substitution instructions.
"""

from __future__ import annotations

from io import BytesIO
from typing import Literal
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from pydantic import BaseModel, Field, model_validator

from .availability import PartColorAvailabilityRegistry
from .bricklink import generate_bricklink_order_documents
from .catalog import PartCrosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .fulfillment import supplier_confirmation_template_csv
from .models import CanonicalOrderPackage
from .packing import generate_kit_packing_documents
from .readiness import assess_order_readiness
from .wobrick import generate_wobrick_order_documents


ExportableRoute = Literal["bricklink", "wobrick"]


class SupplierPackageFile(BaseModel):
    path: str = Field(min_length=1)
    content: str


class SupplierHandoffPackage(BaseModel):
    schema_version: str = "0.1"
    route: ExportableRoute
    building_id: str
    total_parts: int = Field(gt=0)
    total_bags: int = Field(gt=0)
    files: list[SupplierPackageFile] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_files(self) -> "SupplierHandoffPackage":
        names = [item.path for item in self.files]
        if len(names) != len(set(names)):
            raise ValueError("supplier package file paths must be unique")
        required = {
            "00_READINESS.txt",
            "01_SUPPLIER_REQUEST_FR.txt",
            "01_SUPPLIER_REQUEST_EN.txt",
            "02_MASTER_PICKING.csv",
            "03_LABELS.txt",
            "04_RECONCILIATION.csv",
            "06_SUPPLIER_CONFIRMATION_TEMPLATE.csv",
        }
        missing = sorted(required - set(names))
        if missing:
            raise ValueError("supplier package missing required files: " + ", ".join(missing))
        return self

    def file_map(self) -> dict[str, str]:
        return {item.path: item.content for item in self.files}


def _supplier_request_fr(package: CanonicalOrderPackage, route: ExportableRoute) -> str:
    return (
        f"Objet : Kit BOLDÜNGO {package.building_id} — {package.total_parts} pièces "
        f"— {package.total_bags} sacs\n\n"
        "Bonjour,\n\n"
        "Veuillez préparer exactement les références, couleurs et quantités indiquées "
        "dans les fichiers joints.\n"
        "AUCUNE substitution de pièce, couleur, moule ou référence n'est autorisée "
        "sans accord écrit préalable.\n"
        "Si une ligne n'est pas disponible, merci de la signaler avant préparation "
        "du kit, sans la remplacer automatiquement.\n"
        f"La commande comporte {package.total_parts} pièces réparties en "
        f"{package.total_bags} sacs numérotés selon l'ordre de construction.\n"
        "Si vous assurez l'ensachage, merci de conserver strictement la séparation "
        "Sac 01, Sac 02, etc., selon les fiches fournies.\n"
        "Le fichier de réconciliation doit rester à différence 0 pour chaque "
        "couple pièce/couleur.\n\n"
        f"Format fournisseur : {route}.\n"
        "Merci de confirmer toute indisponibilité avant exécution.\n"
    )


def _supplier_request_en(package: CanonicalOrderPackage, route: ExportableRoute) -> str:
    return (
        f"Subject: BOLDÜNGO kit {package.building_id} — {package.total_parts} parts "
        f"— {package.total_bags} bags\n\n"
        "Hello,\n\n"
        "Please prepare exactly the part references, colors and quantities listed "
        "in the attached files.\n"
        "NO substitution of part, color, mold or reference is allowed without prior "
        "written approval.\n"
        "If any line is unavailable, please report it before preparing the kit and "
        "do not replace it automatically.\n"
        f"The order contains {package.total_parts} parts split into "
        f"{package.total_bags} numbered construction bags.\n"
        "If you provide bagging, please keep Bag 01, Bag 02, etc. strictly separated "
        "according to the supplied bag sheets.\n"
        "The reconciliation file must remain at difference 0 for every part/color "
        "combination.\n\n"
        f"Supplier format: {route}.\n"
        "Please confirm any unavailable line before execution.\n"
    )


def generate_supplier_handoff_package(
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    *,
    route: ExportableRoute,
    purchase_colors: dict[tuple[str, str | None], str],
    availability: PartColorAvailabilityRegistry,
    color_crosswalk: ColorCrosswalk | None = None,
) -> SupplierHandoffPackage:
    """Create a complete text-file handoff package for one supplier route."""

    colors = color_crosswalk or load_color_crosswalk()
    readiness = assess_order_readiness(
        package,
        part_crosswalk,
        route=route,
        availability=availability,
        purchase_colors=purchase_colors,
        color_crosswalk=colors,
    )
    if not readiness.supplier_ready:
        details = "\n".join(
            f"- {blocker.part_id} / {blocker.purchase_color_key or '?'}: {blocker.reason}"
            for blocker in readiness.blockers
        )
        raise ValueError("supplier handoff blocked by unresolved lines:\n" + details)

    packing = generate_kit_packing_documents(
        package,
        part_crosswalk,
        route=route,
        purchase_colors=purchase_colors,
        availability=availability,
        color_crosswalk=colors,
    )

    files = [
        SupplierPackageFile(
            path="00_READINESS.txt",
            content=(
                "STATUS=READY_FOR_DOCUMENT_HANDOFF\n"
                f"ROUTE={route}\n"
                f"TOTAL_PARTS={package.total_parts}\n"
                f"TOTAL_BAGS={package.total_bags}\n"
                "UNRESOLVED_LINES=0\n"
                "RECONCILIATION_DIFFERENCES=0\n"
                "NOTE=This proves document/export readiness, not live stock availability or reservation.\n"
            ),
        ),
        SupplierPackageFile(
            path="01_SUPPLIER_REQUEST_FR.txt",
            content=_supplier_request_fr(package, route),
        ),
        SupplierPackageFile(
            path="01_SUPPLIER_REQUEST_EN.txt",
            content=_supplier_request_en(package, route),
        ),
        SupplierPackageFile(path="02_MASTER_PICKING.csv", content=packing.master_picking_csv),
        SupplierPackageFile(path="03_LABELS.txt", content=packing.labels_text + "\n"),
        SupplierPackageFile(path="04_RECONCILIATION.csv", content=packing.reconciliation_csv),
        SupplierPackageFile(
            path="06_SUPPLIER_CONFIRMATION_TEMPLATE.csv",
            content=supplier_confirmation_template_csv(
                package, part_crosswalk, purchase_colors=purchase_colors
            ),
        ),
    ]

    for sheet in packing.bag_sheets:
        files.append(
            SupplierPackageFile(
                path=f"bags/BAG_{sheet.bag_number:02d}_PICKING.csv",
                content=sheet.csv,
            )
        )

    if route == "bricklink":
        order = generate_bricklink_order_documents(
            package,
            part_crosswalk,
            purchase_colors=purchase_colors,
            availability=availability,
            color_crosswalk=colors,
        )
        files.append(SupplierPackageFile(path="05_ORDER_BRICKLINK_MASTER.xml", content=order.master.xml))
        for index, document in enumerate(order.bags, start=1):
            files.append(
                SupplierPackageFile(
                    path=f"bags/BAG_{index:02d}_BRICKLINK.xml",
                    content=document.xml,
                )
            )
    else:
        order = generate_wobrick_order_documents(
            package,
            part_crosswalk,
            purchase_colors=purchase_colors,
            availability=availability,
            color_crosswalk=colors,
        )
        files.append(SupplierPackageFile(path="05_ORDER_WOBRICK_MASTER.csv", content=order.master.csv))
        for index, document in enumerate(order.bags, start=1):
            files.append(
                SupplierPackageFile(
                    path=f"bags/BAG_{index:02d}_WOBRICK.csv",
                    content=document.csv,
                )
            )

    files.sort(key=lambda item: item.path)
    return SupplierHandoffPackage(
        route=route,
        building_id=package.building_id,
        total_parts=package.total_parts,
        total_bags=package.total_bags,
        files=files,
    )


def supplier_handoff_zip_bytes(package: SupplierHandoffPackage) -> bytes:
    """Render a deterministic UTF-8 ZIP suitable for a download endpoint."""

    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for item in sorted(package.files, key=lambda file: file.path):
            info = ZipInfo(item.path, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, item.content.encode("utf-8"))
    return buffer.getvalue()
