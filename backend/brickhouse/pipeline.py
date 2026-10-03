"""End-to-end M0 pipeline from BuildingModel or ArchitecturalScene to viewer export JSON."""
from __future__ import annotations

import argparse
from pathlib import Path

from brickhouse.building.models import BuildingModel, OpeningType, RoofType
from brickhouse.building.validation import load_building_model
from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, generate_brick_model
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.export import BrickExportBundle, BrickExportFidelityIssue, create_export_bundle, export_bundle_json
from brickhouse.bricks.facade_details import generate_window_surrounds
from brickhouse.bricks.facade_rhythm_export import facade_rhythm_fidelity_issues
from brickhouse.bricks.opening_plan_anchors import apply_opening_representation_plan
from brickhouse.bricks.opening_representation_plan import LEGORepresentationPlan, build_opening_representation_plan
from brickhouse.bricks.piece_capabilities import create_current_engine_capability_registry, validate_model_part_capabilities
from brickhouse.bricks.planned_opening_parts import PlannedOpeningStatus, generate_planned_opening_parts
from brickhouse.bricks.roof import generate_spatial_gable_roof, select_roof_slope_family
from brickhouse.bricks.roof_raster_fidelity import gable_rise_error_severity, select_gable_roof_raster
from brickhouse.bricks.scale_optimizer import ScaleRecommendation, recommend_front_width_studs
from brickhouse.bricks.scaling import COURSES_PER_STUD_RATIO
from brickhouse.bricks.scene_platform_connectivity import (
    augment_brick_model_with_scene_platform_connectivity,
    platform_connectivity_fidelity_issues,
)
from brickhouse.bricks.scene_physical_support_gate import evaluate_scene_physical_support_gate
from brickhouse.bricks.scene_characteristic_fidelity import characteristic_fidelity_issues
from brickhouse.bricks.scene_chimney_solutions import select_scene_chimney_footprints
from brickhouse.bricks.scene_chimneys import augment_brick_model_with_scene_chimneys
from brickhouse.bricks.scene_glazing_plan_safe import augment_brick_model_with_planned_scene_glazing
from brickhouse.bricks.scene_grade_contact import (
    augment_brick_model_with_scene_grade_contacts,
    grade_contact_fidelity_issues,
)
from brickhouse.bricks.scene_materials import apply_scene_part_categories
from brickhouse.bricks.scene_shutters import augment_brick_model_with_scene_shutters
from brickhouse.bricks.scene_stair_connectivity_fidelity import stair_connectivity_fidelity_issues
from brickhouse.bricks.scene_supports import platform_support_level_mismatches, validate_platform_support_footprints
from brickhouse.bricks.shed_infill import augment_brick_model_with_shed_roof
from brickhouse.bricks.shed_roof import generate_spatial_shed_roof
from brickhouse.bricks.spatial import generate_spatial_brick_shell
from brickhouse.geometry import generate_building_geometry
from brickhouse.scene.models import ArchitecturalScene, SceneRoofType
from brickhouse.scene.topology_projection import project_scene_to_building
from brickhouse.vision.compatibility import assess_m0_compatibility

DEFAULT_FRONT_WIDTH_STUDS = 48
_SCALE_RECOMMENDATION_RADIUS_STUDS = 6
_SCENE_LOSSES_RECOVERED_AFTER_PROJECTION = {
    "terrain_not_supported", "local_grade_clearance_not_supported", "platform_not_supported",
    "stair_not_supported", "chimney_not_supported",
}


def _validate_generated_model(model: BrickModel) -> None:
    validate_model_part_capabilities(model, create_current_engine_capability_registry())


def _geometry_fidelity_issues(model: BrickModel, ldraw_root: str | Path | None) -> list[BrickExportFidelityIssue]:
    if ldraw_root is None:
        return []
    from lego_geometry_engine import LDrawLibrary
    from brickhouse.bricks.geometry_adapter import analyze_brick_model_geometry

    result = analyze_brick_model_geometry(model, LDrawLibrary(Path(ldraw_root)), strict=True)
    issues: list[BrickExportFidelityIssue] = []
    for collision in result.report.collisions:
        part_a = collision.get("part_a", "unknown")
        part_b = collision.get("part_b", "unknown")
        issues.append(BrickExportFidelityIssue(code="lego_geometry_collision", severity="blocker", object_id=part_a, message=f"LDraw geometry collision between placements {part_a!r} and {part_b!r}."))
    for placement_id in result.report.unsupported_parts:
        issues.append(BrickExportFidelityIssue(code="lego_geometry_unsupported", severity="warning", object_id=placement_id, message=f"LDraw geometry analysis found placement {placement_id!r} unsupported by the assembly contact graph."))
    return issues


def _volume_geometry(geometry, volume_id: str):
    return geometry.model_copy(update={
        "walls": [wall for wall in geometry.walls if wall.volume_id == volume_id],
        "roof_planes": [plane for plane in geometry.roof_planes if plane.volume_id == volume_id],
    })


def _volume_building(building: BuildingModel, volume) -> BuildingModel:
    """Scope opening and roof planning to the volume whose local shell is being built."""
    return building.model_copy(update={
        "volumes": [volume],
        "openings": [opening for opening in building.openings if opening.volume_id == volume.id],
        "roofs": [roof for roof in building.roofs if roof.volume_id == volume.id],
    })


def _translate_model(model: BrickModel, *, prefix: str, x: int, y: int, z: int):
    return [part.model_copy(update={
        "placement_id": f"{prefix}:{part.placement_id}",
        "x_studs": part.x_studs + x,
        "y_studs": part.y_studs + y,
        "z_plates": part.z_plates + z,
    }) for part in model.parts]


def _build_local_model(building, geometry, shell, spatial_shell, roof, facade_details, window_parts):
    if roof is not None and roof.type is RoofType.SHED:
        base = generate_brick_model(spatial_shell, None, facade_details, window_parts)
        shed_roof = generate_spatial_shed_roof(geometry, shell)
        return augment_brick_model_with_shed_roof(base, spatial_shell, shed_roof)
    spatial_roof = generate_spatial_gable_roof(geometry, shell) if roof is not None and roof.type is RoofType.GABLE else None
    return generate_brick_model(spatial_shell, spatial_roof, facade_details, window_parts)


def _restore_opening_provenance(model: BrickModel, planned_parts) -> BrickModel:
    """Carry plan opening IDs through the historical BrickModel window adapter."""
    by_placement_id = {
        f"window-{index:06d}": placement.opening_id
        for index, placement in enumerate(planned_parts, start=1)
        if placement.opening_id is not None
    }
    if not by_placement_id:
        return model
    changed = False
    parts = []
    for part in model.parts:
        opening_id = by_placement_id.get(part.placement_id)
        if opening_id is not None and part.opening_id != opening_id:
            part = part.model_copy(update={"opening_id": opening_id})
            changed = True
        parts.append(part)
    return model.model_copy(update={"parts": parts}) if changed else model


def _roof_raster_issues(geometry, shell, roof) -> list[BrickExportFidelityIssue]:
    if roof is None or roof.type is not RoofType.GABLE:
        return []
    selection = select_gable_roof_raster(geometry, shell)
    issues: list[BrickExportFidelityIssue] = []
    if selection.span_adjustment_studs:
        issues.append(BrickExportFidelityIssue(code="lego_roof_eave_span_adjustment",severity="info",object_id=roof.id,message=(f"Architectural roof {roof.id!r} remains unchanged; its LEGO slope raster extends the {selection.wall_span_studs}-stud wall span to {selection.selected_span_studs} studs (+{selection.span_adjustment_studs}) so the validated {selection.slope_family_id}° family connects physically to the ridge. This is representation-only overhang.")))
    if selection.line_adjustment_studs:
        issues.append(BrickExportFidelityIssue(code="lego_roof_gable_line_adjustment",severity="info",object_id=roof.id,message=(f"Architectural roof {roof.id!r} remains unchanged; its LEGO longitudinal line extends from {selection.wall_line_length_studs} to {selection.selected_line_length_studs} studs (+{selection.line_adjustment_studs}) to tile the selected slope and ridge families exactly. This is representation-only gable-end overhang.")))
    rise_severity = gable_rise_error_severity(selection)
    if rise_severity is not None:
        direction = "taller/steeper" if selection.gable_rise_direction == "taller" else "lower/flatter"
        issues.append(BrickExportFidelityIssue(code="lego_gable_rise_distortion",severity=rise_severity,object_id=roof.id,message=(f"Architectural roof {roof.id!r} remains unchanged at {selection.target_pitch_degrees:.2f}°; the validated LEGO {selection.selected_pitch_degrees:.2f}° family makes the gable {direction} by {selection.relative_gable_rise_error * 100:.1f}% for the same half-span. This is a representation-fidelity diagnostic, not a mutation of architectural geometry.")))
    return issues


def _opening_anchor_issues(application) -> list[BrickExportFidelityIssue]:
    issues: list[BrickExportFidelityIssue] = []
    for anchor in application.anchors:
        if not anchor.geometry_changed:
            continue
        issues.append(BrickExportFidelityIssue(code="lego_window_local_anchor_adjustment",severity="info",object_id=anchor.opening_id,message=(f"Architectural opening {anchor.opening_id!r} remains unchanged in the source model; its LEGO representation uses a local anchor from {anchor.source_width_studs}x{anchor.source_height_bricks} at ({anchor.source_x_studs},{anchor.source_z_bricks}) to {anchor.anchored_width_studs}x{anchor.anchored_height_bricks} at ({anchor.anchored_x_studs},{anchor.anchored_z_bricks}) to preserve the selected opening family/proportions.")))
    for facade in application.rejected_facades:
        issues.append(BrickExportFidelityIssue(code="lego_window_anchor_facade_rejected",severity="warning",message=f"Architectural opening anchors on the {facade.value} facade could not be applied without invalid wall openings; the original raster was preserved."))
    return issues


def _window_representation_issues(statuses) -> list[BrickExportFidelityIssue]:
    """Compatibility helper retained for the historical window-only contract tests."""
    return [BrickExportFidelityIssue(code="lego_architectural_window_unrepresented",severity="blocker",object_id=status.opening_id,message=(f"Architectural window {status.opening_id!r} remains preserved as an opening void on the {status.facade.value} facade, but the current validated LEGO vocabulary cannot represent its known composition. The wall must not be treated as a successful blind facade and no unsupported joinery is invented.")) for status in statuses if not status.represented]


def _opening_representation_issues(plan: LEGORepresentationPlan, statuses: list[PlannedOpeningStatus]) -> list[BrickExportFidelityIssue]:
    """No required architectural opening may silently disappear or gain fake joinery."""
    status_by_id = {status.opening_id: status for status in statuses}
    issues: list[BrickExportFidelityIssue] = []
    for reservation in plan.openings:
        if reservation.status == "not_applicable":
            continue
        status = status_by_id.get(reservation.opening_id)
        if reservation.status == "reserved" and status is not None and status.represented:
            continue

        if reservation.architectural_type is OpeningType.WINDOW:
            code = "lego_architectural_window_unrepresented"
            severity = "blocker"
        else:
            code = "lego_architectural_opening_unrepresented"
            severity = "blocker" if reservation.representation_role is not None else "warning"
        reason = reservation.reason
        if status is not None and not status.represented and status.reason:
            reason = status.reason
        issues.append(BrickExportFidelityIssue(
            code=code,
            severity=severity,
            object_id=reservation.opening_id,
            message=(
                f"Architectural opening {reservation.opening_id!r} ({reservation.architectural_type.value}) remains "
                "preserved as an opening void, but the current validated LEGO representation plan cannot emit "
                f"a faithful assembly{': ' + reason if reason else ''}. No semantic reclassification or fake glazing is introduced."
            ),
        ))
    return issues


def _prepare_opening_shell(building: BuildingModel, shell):
    plan = build_opening_representation_plan(building, shell)
    application = apply_opening_representation_plan(building, shell, plan)
    issues = [*_opening_anchor_issues(application), *facade_rhythm_fidelity_issues(application)]
    return application.shell, plan, issues


def _single_volume_bundle(building: BuildingModel, geometry, front_width_studs: int, scale_recommendation: ScaleRecommendation, *, ldraw_root: str | Path | None = None) -> BrickExportBundle:
    shell = generate_building_brick_shell(geometry, front_width_studs)
    shell, opening_plan, anchor_issues = _prepare_opening_shell(building, shell)
    spatial_shell = generate_spatial_brick_shell(shell)
    opening_parts, represented_opening_ids, opening_statuses = generate_planned_opening_parts(building, shell, opening_plan)
    facade_details = generate_window_surrounds(building, shell, skip_opening_ids=represented_opening_ids)
    roof = building.roofs[0] if building.roofs else None
    roof_issues = _roof_raster_issues(geometry, shell, roof)
    brick_model = _build_local_model(building, geometry, shell, spatial_shell, roof, facade_details, opening_parts)
    brick_model = _restore_opening_provenance(brick_model, opening_parts)
    _validate_generated_model(brick_model)
    bom = generate_bom(brick_model)
    assembly_plan = generate_assembly_plan(brick_model)
    quality = [shell.discretization_quality] if shell.discretization_quality is not None else []
    return create_export_bundle(brick_model,bom,assembly_plan,appearance=building.appearance,discretization_quality=quality,scale_recommendation=scale_recommendation,fidelity_issues=[*anchor_issues,*_opening_representation_issues(opening_plan, opening_statuses),*roof_issues,*_geometry_fidelity_issues(brick_model, ldraw_root)])


def run_m0_pipeline_model(building: BuildingModel, *, front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS, ldraw_root: str | Path | None = None) -> BrickExportBundle:
    if front_width_studs <= 0: raise ValueError("front_width_studs must be positive")
    scale_recommendation = recommend_front_width_studs(building, preferred_front_width_studs=front_width_studs, search_radius_studs=_SCALE_RECOMMENDATION_RADIUS_STUDS)
    geometry = generate_building_geometry(building)
    if len(building.volumes) == 1: return _single_volume_bundle(building, geometry, front_width_studs, scale_recommendation, ldraw_root=ldraw_root)
    primary=building.volumes[0]; studs_per_meter=front_width_studs/primary.width; plates_per_meter=studs_per_meter*COURSES_PER_STUD_RATIO*3
    min_x=min(v.position.x for v in building.volumes); min_y=min(v.position.y for v in building.volumes); min_z=min(v.position.z for v in building.volumes)
    all_parts=[]; quality_reports=[]; fidelity_issues=[]; max_x=max_y=max_z=1
    for volume in building.volumes:
        local_building=_volume_building(building,volume); subgeometry=_volume_geometry(geometry,volume.id); shell=generate_building_brick_shell(subgeometry,studs_per_meter=studs_per_meter)
        if shell.discretization_quality is not None: quality_reports.append(shell.discretization_quality)
        shell,opening_plan,anchor_issues=_prepare_opening_shell(local_building,shell); fidelity_issues.extend(anchor_issues)
        spatial_shell=generate_spatial_brick_shell(shell); opening_parts,represented_opening_ids,opening_statuses=generate_planned_opening_parts(local_building,shell,opening_plan); fidelity_issues.extend(_opening_representation_issues(opening_plan,opening_statuses)); facade_details=generate_window_surrounds(local_building,shell,skip_opening_ids=represented_opening_ids); roof=local_building.roofs[0] if local_building.roofs else None; fidelity_issues.extend(_roof_raster_issues(subgeometry,shell,roof)); local_model=_build_local_model(local_building,subgeometry,shell,spatial_shell,roof,facade_details,opening_parts); local_model=_restore_opening_provenance(local_model,opening_parts)
        x=round((volume.position.x-min_x)*studs_per_meter); y=round((volume.position.y-min_y)*studs_per_meter); z=round((volume.position.z-min_z)*plates_per_meter); all_parts.extend(_translate_model(local_model,prefix=volume.id,x=x,y=y,z=z)); max_x=max(max_x,x+local_model.width_studs); max_y=max(max_y,y+local_model.depth_studs); max_z=max(max_z,z+local_model.height_plates)
    primary_x=round((primary.position.x-min_x)*studs_per_meter); primary_y=round((primary.position.y-min_y)*studs_per_meter); primary_depth=max(1,round(primary.depth*studs_per_meter))
    brick_model=BrickModel(building_id=building.id,volume_id="composite",width_studs=front_width_studs,depth_studs=primary_depth,height_plates=max_z,canvas_width_studs=max_x,canvas_depth_studs=max_y,origin_x_studs=primary_x,origin_y_studs=primary_y,parts=all_parts); _validate_generated_model(brick_model); bom=generate_bom(brick_model); assembly_plan=generate_assembly_plan(brick_model); fidelity_issues.extend(_geometry_fidelity_issues(brick_model,ldraw_root)); return create_export_bundle(brick_model,bom,assembly_plan,appearance=building.appearance,discretization_quality=quality_reports,scale_recommendation=scale_recommendation,fidelity_issues=fidelity_issues)


def _source_confidence_issue(kind: str, obj) -> BrickExportFidelityIssue | None:
    source=getattr(obj,"source",None)
    if source is None or source.kind=="user_provided" or source.confidence>=0.65: return None
    severity="warning" if source.confidence<0.5 else "info"
    return BrickExportFidelityIssue(code="low_confidence_exterior_geometry",severity=severity,object_id=obj.id,message=f"{kind} {obj.id!r} is rendered from inferred architectural geometry with confidence {source.confidence:.2f}. Additional overlapping views may refine its position or connectivity; the current LEGO geometry must not be treated as measured fact.")


def _chimney_footprint_issues(scene: ArchitecturalScene, front_width_studs: int) -> list[BrickExportFidelityIssue]:
    issues=[]
    for solution in select_scene_chimney_footprints(scene,front_width_studs=front_width_studs):
        if not solution.geometry_changed: continue
        severity="info" if max(solution.dimensional_error,solution.area_error)<=0.35 else "warning"; issues.append(BrickExportFidelityIssue(code="lego_chimney_footprint_adjustment",severity=severity,object_id=solution.chimney_id,message=(f"Architectural chimney {solution.chimney_id!r} remains unchanged in ArchitecturalScene; its LEGO footprint represents {solution.target_width_studs:.3f}x{solution.target_depth_studs:.3f} studs as {solution.width_studs}x{solution.depth_studs} studs to preserve dimensional and aspect-ratio fidelity without systematic outward rounding.")))
    return issues


def _scene_export_fidelity_issues(scene: ArchitecturalScene, projection, *, front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS) -> list[BrickExportFidelityIssue]:
    issues=[]
    for issue in projection.issues:
        if issue.code in _SCENE_LOSSES_RECOVERED_AFTER_PROJECTION: continue
        severity="blocker" if issue.severity.value=="blocker" else "warning"
        if issue.code=="visibility_not_supported": severity="info"
        issues.append(BrickExportFidelityIssue(code=issue.code,severity=severity,message=issue.message,object_id=issue.object_id))
    for kind,collection in (("Platform",scene.platforms),("StairRun",scene.stairs),("Chimney",scene.chimneys)):
        for obj in collection:
            issue=_source_confidence_issue(kind,obj)
            if issue is not None: issues.append(issue)
    issues.extend(_chimney_footprint_issues(scene,front_width_studs)); issues.extend(characteristic_fidelity_issues(scene,front_width_studs=front_width_studs)); issues.extend(platform_connectivity_fidelity_issues(scene,front_width_studs=front_width_studs)); issues.extend(stair_connectivity_fidelity_issues(scene,front_width_studs=front_width_studs))
    for mismatch in platform_support_level_mismatches(scene): issues.append(BrickExportFidelityIssue(code="platform_support_level_mismatch",severity="warning",object_id=mismatch.support_id,message=(f"Support {mismatch.support_id!r} on platform {mismatch.platform_id!r} ends at {mismatch.support_top_m:g}m while the platform level is {mismatch.platform_level_m:g}m (difference {mismatch.delta_m:g}m). The ArchitecturalScene values are preserved; the LEGO renderer must not silently extend the support to hide this mismatch.")))
    for roof in scene.roofs:
        if roof.type not in {SceneRoofType.GABLE,SceneRoofType.SHED} or roof.pitch_degrees is None: continue
        family=select_roof_slope_family(roof.pitch_degrees); delta=abs(family.pitch_degrees-roof.pitch_degrees)
        if delta>0.25: issues.append(BrickExportFidelityIssue(code="roof_pitch_quantized",severity="info" if delta<=5 else "warning",object_id=roof.id,message=f"Roof pitch {roof.pitch_degrees:g}° is preserved in ArchitecturalScene; the current LEGO build uses the validated {family.pitch_degrees:g}° slope family (difference {delta:g}°)."))
    compatibility=assess_m0_compatibility(projection.building)
    for warning in compatibility.warnings: issues.append(BrickExportFidelityIssue(code="m0_model_warning",severity="warning",message=warning))
    for blocker in compatibility.blockers: issues.append(BrickExportFidelityIssue(code="m0_model_blocker",severity="blocker",message=blocker))
    unique=[]; seen=set()
    for issue in issues:
        key=(issue.code,issue.object_id,issue.message)
        if key not in seen: seen.add(key); unique.append(issue)
    return unique


def run_m0_pipeline_scene(scene: ArchitecturalScene, *, front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS, ldraw_root: str | Path | None = None) -> BrickExportBundle:
    validate_platform_support_footprints(scene); support_gate=evaluate_scene_physical_support_gate(scene); projection=project_scene_to_building(scene)
    if projection.building is None or projection.blocked:
        blockers=" ".join(issue.message for issue in projection.issues if issue.severity.value=="blocker"); raise ValueError(blockers or "ArchitecturalScene cannot be projected to BuildingModel")
    scene_issues=_scene_export_fidelity_issues(scene,projection,front_width_studs=front_width_studs); base=run_m0_pipeline_model(projection.building,front_width_studs=front_width_studs); fidelity_issues=[*base.fidelity_issues,*scene_issues,*support_gate.fidelity_issues]
    platform_scene=support_gate.platform_scene(scene); chimney_scene=support_gate.chimney_scene(scene)
    enriched=augment_brick_model_with_scene_platform_connectivity(base.brick_model,platform_scene,front_width_studs=front_width_studs); enriched=augment_brick_model_with_scene_chimneys(enriched,chimney_scene,front_width_studs=front_width_studs); enriched=apply_scene_part_categories(enriched,scene); enriched=augment_brick_model_with_planned_scene_glazing(enriched,scene,front_width_studs=front_width_studs); enriched=augment_brick_model_with_scene_shutters(enriched,scene,front_width_studs=front_width_studs); enriched=augment_brick_model_with_scene_grade_contacts(enriched,scene,front_width_studs=front_width_studs); fidelity_issues.extend(grade_contact_fidelity_issues(scene)); _validate_generated_model(enriched); fidelity_issues.extend(_geometry_fidelity_issues(enriched,ldraw_root))
    if enriched is base.brick_model: return create_export_bundle(enriched,base.bom,base.assembly_plan,appearance=projection.building.appearance,fidelity_issues=fidelity_issues,discretization_quality=base.metadata.discretization_quality,scale_recommendation=base.metadata.scale_recommendation)
    bom=generate_bom(enriched); assembly_plan=generate_assembly_plan(enriched); return create_export_bundle(enriched,bom,assembly_plan,appearance=projection.building.appearance,fidelity_issues=fidelity_issues,discretization_quality=base.metadata.discretization_quality,scale_recommendation=base.metadata.scale_recommendation)


def run_m0_pipeline(input_path: str | Path, *, front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS, ldraw_root: str | Path | None = None) -> BrickExportBundle: return run_m0_pipeline_model(load_building_model(input_path),front_width_studs=front_width_studs,ldraw_root=ldraw_root)
def write_m0_export(input_path: str | Path, output_path: str | Path, *, front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS, ldraw_root: str | Path | None = None) -> BrickExportBundle:
    bundle=run_m0_pipeline(input_path,front_width_studs=front_width_studs,ldraw_root=ldraw_root); destination=Path(output_path); destination.parent.mkdir(parents=True,exist_ok=True); destination.write_text(export_bundle_json(bundle)+"\n",encoding="utf-8"); return bundle

def build_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(prog="brickhouse-m0",description="Generate a BrickHouse M0 BrickModel/BOM/AssemblyPlan JSON export from a BuildingModel JSON file."); parser.add_argument("input",type=Path,help="BuildingModel JSON input"); parser.add_argument("output",type=Path,help="Output export JSON path"); parser.add_argument("--front-width-studs",type=int,default=DEFAULT_FRONT_WIDTH_STUDS,help=f"target front facade width in studs (default: {DEFAULT_FRONT_WIDTH_STUDS})"); parser.add_argument("--ldraw-root",type=Path,default=None,help="optional complete LDraw library root; enables mesh collision/support validation"); return parser

def main(argv: list[str] | None = None) -> int:
    args=build_parser().parse_args(argv); bundle=write_m0_export(args.input,args.output,front_width_studs=args.front_width_studs,ldraw_root=args.ldraw_root); print(f"Generated {args.output}: {bundle.bom.total_parts} parts, {bundle.bom.unique_part_types} canonical types, {bundle.assembly_plan.total_steps if bundle.assembly_plan else 0} assembly steps"); return 0

if __name__ == "__main__": raise SystemExit(main())