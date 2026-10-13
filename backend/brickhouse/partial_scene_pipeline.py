"""Conservative LEGO preview for partially resolved ArchitecturalScene data.

This path exists so BrickHouse can show useful first bricks before every roof or
external junction is metrically resolved. It never chooses missing dimensions,
roof directions, roof pitches, or hidden connections, and it keeps approximate
photo-derived metrics visibly separate from measured fact.
"""
from __future__ import annotations

from brickhouse.building.models import BuildingModel, Metadata, Opening, Roof, RoofType, Volume, VolumeShape
from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.bags import generate_bag_plan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.discretization_report import build_discretization_quality
from brickhouse.bricks.export import (
    BrickExportBundle,
    BrickExportFidelityIssue,
    derive_export_capability_summary,
)
from brickhouse.bricks.instructions import generate_instruction_plan
from brickhouse.bricks.scale_optimizer import recommend_front_width_studs
from brickhouse.bricks.scene_chimneys import augment_brick_model_with_scene_chimneys
from brickhouse.bricks.scene_grade_contact import (
    augment_brick_model_with_scene_grade_contacts,
    grade_contact_fidelity_issues,
)
from brickhouse.bricks.scene_materials import apply_scene_part_categories
from brickhouse.bricks.scene_physical_support_gate import evaluate_scene_physical_support_gate
from brickhouse.bricks.scene_platform_connectivity import augment_brick_model_with_scene_platform_connectivity
from brickhouse.bricks.scene_shutters import augment_brick_model_with_scene_shutters
from brickhouse.bricks.wall_depth import MIN_GEOMETRY_CONFIDENCE, augment_brick_model_with_wall_depth
from brickhouse.pipeline import DEFAULT_FRONT_WIDTH_STUDS, run_m0_pipeline_model
from brickhouse.scene import ArchitecturalScene, SceneRoofType
from brickhouse.scene.physical_support import analyze_physical_support
from brickhouse.scene.topology_projection import project_scene_to_building

LOW_CONFIDENCE_WARNING = 0.65
AUTO_SCALE_MIN_IMPROVEMENT = 0.10


def _is_resolved_volume(volume) -> bool:
    return (
        volume.width.value is not None
        and volume.depth.value is not None
        and volume.height.value is not None
        and volume.floors <= 3
    )


def _selected_partial_volumes(scene: ArchitecturalScene):
    """Keep every concrete volume envelope; confidence changes fidelity, not presence."""
    primary = scene.volumes[0]
    if not _is_resolved_volume(primary):
        raise ValueError(
            "Partial LEGO preview still needs the primary volume with resolved width, depth and height."
        )

    included = [primary]
    omitted = []
    for volume in scene.volumes[1:]:
        if not _is_resolved_volume(volume):
            omitted.append((volume, "unresolved metric envelope"))
            continue
        included.append(volume)
    return included, omitted


def _roof_is_representable(roof) -> bool:
    if roof.type is SceneRoofType.FLAT:
        return True
    if roof.type is SceneRoofType.GABLE:
        return roof.ridge_direction is not None and roof.pitch_degrees is not None
    if roof.type is SceneRoofType.SHED:
        return roof.down_slope_direction is not None and roof.pitch_degrees is not None
    return False


def _selected_partial_roofs(scene: ArchitecturalScene, resolved_ids: set[str]):
    included = []
    omitted = []
    for roof in scene.roofs:
        if roof.volume_id not in resolved_ids:
            omitted.append((roof, "host volume is not present in the partial preview"))
            continue
        if not _roof_is_representable(roof):
            omitted.append((roof, "construction pitch/direction is incomplete"))
            continue
        included.append(roof)
    return included, omitted


def _resolved_core_building(scene: ArchitecturalScene) -> BuildingModel:
    """Project the concrete core plus roofs whose construction geometry is complete."""
    resolved, _ = _selected_partial_volumes(scene)
    resolved_ids = {volume.id for volume in resolved}
    volumes = [
        Volume(
            id=volume.id,
            shape=VolumeShape.RECTANGULAR_PRISM,
            position=volume.position,
            width=volume.width.value,
            depth=volume.depth.value,
            height=volume.height.value,
            floors=volume.floors,
            source=volume.source,
        )
        for volume in resolved
    ]
    openings = [
        Opening(
            id=opening.id,
            type=opening.type,
            volume_id=opening.volume_id,
            facade=opening.facade,
            offset_horizontal=opening.offset_horizontal,
            offset_vertical=opening.offset_vertical,
            width=opening.width,
            height=opening.height,
            source=opening.source,
            window_style=opening.window_style,
            has_sill=opening.has_sill,
            has_decorative_surround=opening.has_decorative_surround,
            opening_visual=opening.opening_visual,
        )
        for opening in scene.openings
        if opening.volume_id in resolved_ids
    ]
    selected_roofs, _ = _selected_partial_roofs(scene, resolved_ids)
    roofs = [
        Roof(
            id=roof.id,
            volume_id=roof.volume_id,
            type=RoofType(roof.type.value),
            overhang=roof.overhang,
            ridge_direction=roof.ridge_direction,
            down_slope_direction=roof.down_slope_direction,
            pitch_degrees=roof.pitch_degrees,
            source=roof.source,
        )
        for roof in selected_roofs
    ]
    return BuildingModel(
        schema_version="0.1",
        id=scene.id,
        name=scene.name,
        building_type="building",
        units="m",
        volumes=volumes,
        openings=openings,
        roofs=roofs,
        appearance=scene.appearance,
        metadata=Metadata(
            created_from="photo_analysis",
            notes=(
                "Conservative partial LEGO preview: resolved metric envelopes and fully specified roofs are shown "
                "provisionally; unresolved geometry and hidden junctions remain omitted."
            ),
        ),
    )


def _partial_exterior_selection(scene: ArchitecturalScene):
    facts, _ = analyze_physical_support(scene)
    support_gate = evaluate_scene_physical_support_gate(scene)
    platform_ids = {item.id for item in scene.platforms}
    safe_platform_ids: set[str] = set()
    platform_reason: dict[str, str] = {}
    for platform in scene.platforms:
        support_facts = [fact for fact in facts if fact.object_id == platform.id and fact.kind in {"platform_host_contact", "platform_post_support"}]
        contradicted = next((fact for fact in support_facts if fact.state == "contradicted"), None)
        proven = [fact for fact in support_facts if fact.state == "proven"]
        if contradicted is not None:
            platform_reason[platform.id] = contradicted.reason
        elif proven:
            safe_platform_ids.add(platform.id)
        else:
            unresolved = next((fact for fact in support_facts if fact.state == "unresolved"), None)
            platform_reason[platform.id] = unresolved.reason if unresolved is not None else "no proven platform support path"

    safe_stair_ids: set[str] = set()
    stair_reason: dict[str, str] = {}
    for stair in scene.stairs:
        endpoint_facts = sorted((fact for fact in facts if fact.object_id == stair.id and fact.kind == "stair_endpoint_support"), key=lambda fact: fact.endpoint or "")
        if len(endpoint_facts) != 2 or any(fact.state != "proven" for fact in endpoint_facts):
            unresolved = next((fact for fact in endpoint_facts if fact.state != "proven"), None)
            stair_reason[stair.id] = unresolved.reason if unresolved is not None else "both stair endpoints are not proven supported"
            continue
        unsafe_platform = next((fact.supporter_id for fact in endpoint_facts if fact.supporter_id in platform_ids and fact.supporter_id not in safe_platform_ids), None)
        if unsafe_platform is not None:
            stair_reason[stair.id] = f"endpoint depends on omitted platform {unsafe_platform!r}"
            continue
        safe_stair_ids.add(stair.id)

    safe_chimney_ids = {
        item.id for item in scene.chimneys
        if item.id not in support_gate.blocked_chimney_ids
    }
    safe_scene = scene.model_copy(update={
        "platforms": [item for item in scene.platforms if item.id in safe_platform_ids],
        "stairs": [item for item in scene.stairs if item.id in safe_stair_ids],
        "chimneys": [item for item in scene.chimneys if item.id in safe_chimney_ids],
        "terrain": None,
        "platform_structure_observations": [item for item in scene.platform_structure_observations if item.platform_id in safe_platform_ids],
    })
    omitted = [("platform", item.id, platform_reason.get(item.id, "support not proven")) for item in scene.platforms if item.id not in safe_platform_ids]
    omitted.extend(("stair", item.id, stair_reason.get(item.id, "support not proven")) for item in scene.stairs if item.id not in safe_stair_ids)
    omitted.extend(("chimney", item.id, "physical support is contradicted or blocked by the Scene support gate") for item in scene.chimneys if item.id not in safe_chimney_ids)
    return safe_scene, omitted


def _metric_uncertainty_issues(scene: ArchitecturalScene) -> list[BrickExportFidelityIssue]:
    included, omitted = _selected_partial_volumes(scene)
    included_ids = {volume.id for volume in included}
    issues: list[BrickExportFidelityIssue] = []
    for volume, reason in omitted:
        issues.append(BrickExportFidelityIssue(code="partial_preview_secondary_volume_omitted", severity="warning", object_id=volume.id, message=(f"Secondary volume {volume.id!r} is visible in ArchitecturalScene but is omitted from the first-bricks preview because {reason}.")))
    for volume in included:
        for name in ("width", "depth", "height"):
            value = getattr(volume, name)
            if value.source.kind == "user_provided" or value.source.confidence >= LOW_CONFIDENCE_WARNING:
                continue
            issues.append(BrickExportFidelityIssue(code="low_confidence_partial_dimension", severity="warning" if value.source.confidence < 0.5 else "info", object_id=volume.id, message=(f"{volume.id}.{name}={value.value:g} m is used provisionally in the first-bricks preview from photo inference confidence {value.source.confidence:.2f}; it is not a measured dimension.")))
    for opening in scene.openings:
        if opening.volume_id not in included_ids:
            continue
        if opening.source.kind == "user_provided" or opening.source.confidence >= LOW_CONFIDENCE_WARNING:
            continue
        issues.append(BrickExportFidelityIssue(code="low_confidence_partial_opening_geometry", severity="warning" if opening.source.confidence < 0.4 else "info", object_id=opening.id, message=(f"Opening {opening.id!r} is kept as a real wall cut, but its current rectangle is photo-derived at confidence {opening.source.confidence:.2f}; later cross-view constraints may move or resize it.")))
    for profile in getattr(scene, "wall_profile_observations", []):
        if profile.volume_id not in included_ids or profile.openings_recessed is not True:
            continue
        reveal = profile.reveal_depth
        reveal_resolved = reveal is not None and reveal.value is not None and (reveal.source.kind == "user_provided" or reveal.source.confidence >= MIN_GEOMETRY_CONFIDENCE)
        if not reveal_resolved:
            issues.append(BrickExportFidelityIssue(code="observed_recess_depth_unresolved", severity="info", object_id=profile.id, message=(f"Openings on {profile.facade.value} facade of volume {profile.volume_id!r} are visibly recessed, but the recess depth is not resolved strongly enough to move the LEGO frame inward. The first-bricks preview keeps this fact explicit instead of inventing a depth.")))
    return issues


def _partial_fidelity_issues(scene: ArchitecturalScene) -> list[BrickExportFidelityIssue]:
    projection = project_scene_to_building(scene)
    issues = [*_metric_uncertainty_issues(scene), *grade_contact_fidelity_issues(scene)]
    exterior_scene, omitted_exterior = _partial_exterior_selection(scene)
    recovered_projection_losses = {
        "platform_not_supported": {item.id for item in exterior_scene.platforms},
        "stair_not_supported": {item.id for item in exterior_scene.stairs},
        "chimney_not_supported": {item.id for item in exterior_scene.chimneys},
    }
    issues.extend(
        BrickExportFidelityIssue(
            code=issue.code,
            severity="warning" if issue.severity.value == "blocker" else "info",
            object_id=issue.object_id,
            message=(f"Partial preview omission: {issue.message}" if issue.severity.value == "blocker" else issue.message),
        )
        for issue in projection.issues
        if issue.object_id not in recovered_projection_losses.get(issue.code, set())
    )
    resolved_volumes, _ = _selected_partial_volumes(scene)
    resolved_ids = {volume.id for volume in resolved_volumes}
    _, omitted_roofs = _selected_partial_roofs(scene, resolved_ids)
    for roof, reason in omitted_roofs:
        issues.append(BrickExportFidelityIssue(code="partial_preview_roof_omitted", severity="warning", object_id=roof.id, message=(f"Roof {roof.id!r} remains in ArchitecturalScene but is omitted from the partial LEGO preview because {reason}. No pitch, direction or host geometry is invented.")))
    for kind, object_id, reason in omitted_exterior:
        issues.append(BrickExportFidelityIssue(code="partial_preview_exterior_object_omitted", severity="warning" if kind in {"platform", "stair"} else "info", object_id=object_id, message=(f"{kind.capitalize()} {object_id!r} remains in ArchitecturalScene but is omitted from the partial LEGO preview because {reason}. No support or hidden connection is invented.")))
    unique = []
    seen = set()
    for issue in issues:
        key = (issue.code, issue.object_id, issue.message)
        if key not in seen:
            seen.add(key)
            unique.append(issue)
    return unique


def run_partial_scene_pipeline(scene: ArchitecturalScene, *, front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS, optimize_scale: bool = False) -> BrickExportBundle:
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")
    building = _resolved_core_building(scene)
    recommendation = recommend_front_width_studs(building, preferred_front_width_studs=front_width_studs, search_radius_studs=6)
    selected_width = front_width_studs
    if optimize_scale and recommendation.improvement_fraction >= AUTO_SCALE_MIN_IMPROVEMENT:
        selected_width = recommendation.recommended_front_width_studs
    try:
        bundle = run_m0_pipeline_model(building, front_width_studs=selected_width)
    except ValueError:
        if selected_width == front_width_studs:
            raise
        selected_width = front_width_studs
        bundle = run_m0_pipeline_model(building, front_width_studs=selected_width)
    enriched = augment_brick_model_with_wall_depth(bundle.brick_model, scene, front_width_studs=selected_width)
    exterior_scene, _ = _partial_exterior_selection(scene)
    enriched = augment_brick_model_with_scene_platform_connectivity(enriched, exterior_scene, front_width_studs=selected_width)
    enriched = augment_brick_model_with_scene_chimneys(enriched, exterior_scene, front_width_studs=selected_width)
    enriched = apply_scene_part_categories(enriched, exterior_scene)
    enriched = augment_brick_model_with_scene_shutters(enriched, scene, front_width_studs=selected_width)
    enriched = augment_brick_model_with_scene_grade_contacts(enriched, scene, front_width_studs=selected_width)
    if enriched.width_studs != selected_width:
        enriched = enriched.model_copy(update={"width_studs": selected_width})
    if enriched is not bundle.brick_model:
        assembly_plan = generate_assembly_plan(enriched)
        bundle = bundle.model_copy(update={"brick_model": enriched, "bom": generate_bom(enriched), "assembly_plan": assembly_plan, "instruction_plan": generate_instruction_plan(assembly_plan), "bag_plan": generate_bag_plan(assembly_plan)})
    quality = build_discretization_quality(building, front_width_studs=selected_width)
    metadata = bundle.metadata.model_copy(update={"discretization_quality": quality, "scale_recommendation": recommendation})
    fidelity_issues = _partial_fidelity_issues(scene)
    capability_summary = derive_export_capability_summary(assembly_plan=bundle.assembly_plan, instruction_plan=bundle.instruction_plan, bag_plan=bundle.bag_plan, fidelity_issues=fidelity_issues, mechanical_verification=(bundle.capability_summary.mechanical_verification if bundle.capability_summary is not None else None))
    return bundle.model_copy(update={"metadata": metadata, "fidelity_issues": fidelity_issues, "capability_summary": capability_summary})
