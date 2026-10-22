"""Architectural scene contracts and projection helpers."""
from .architectural_priors import (
    FR_OPENING_PRIOR_CATALOG_VERSION,
    OpeningPriorQuery,
    france_residential_opening_priors_v01,
)
from .human_relative_level_fidelity import (
    HumanRelativeLevelIssue,
    HumanRelativeLevelReport,
    validate_scene_against_human_relative_level_facts,
)
from .host_face_identity import (
    HostFaceEvidence,
    resolve_host_face,
    validate_host_face_candidate,
)
from .modular_priors import (
    GLASS_BLOCK_PRIOR_CATALOG_VERSION,
    GlassBlockGridPriorQuery,
    glass_block_grid_prior_v01,
)
from .models import (
    Chimney, DeckBoardDirection, EdgeAccessSpan, EdgeTreatment, EquipmentType,
    Evidence, ExteriorMaterial, FacadeEquipment, FacadeVisibility, GradeProfile, Platform,
    PlatformEdge, PlatformEdges, PropertyValue, RoofPitchRange, SceneOpening, SceneRoof, SceneRoofType, SceneVolume, StairRun,
    SupportPost, Terrain, VisibilitySpan, VisibilityState,
)
from .partial_wall import PartialWallSegment
from .photo_landmarks import (
    ArchitecturalLandmarkObservation,
    ArchitecturalLandmarkStatus,
    ArchitecturalLandmarkTrack,
    build_relative_landmark_tracks,
    validate_architectural_landmark_tracks,
)
from .photo_rectification import (
    NormalizedImagePoint,
    NormalizedImageQuadrilateral,
    PlanarPhotoRectification,
    rectified_plane_reference_annotation,
    rectify_photo_geometry_annotation,
    rectify_point,
)
from .photo_scale_cues import (
    PhotoGeometryAnnotation,
    PhotoScaleCueBinding,
    ReferenceExtentCoverage,
    build_visual_scale_cues_from_photo_geometry,
    validate_photo_geometry_annotations,
)
from .platform_structure import PlatformStructureKind, PlatformStructureObservation
from .projection import ProjectionIssue, ProjectionResult, ProjectionSeverity
from .relative_camera_estimation import (
    CalibratedPhotoIntrinsics,
    RelativeCameraEstimationResult,
    RelativeCameraEstimationStatus,
    estimate_relative_camera_pair,
)
from .relative_multiview import (
    RelativeCameraHypothesis,
    RelativeLandmarkCandidate,
    RelativeLandmarkObservation,
    RelativeLandmarkTrack,
    RelativePoint3D,
    RelativeReconstructionResult,
    RelativeReconstructionStatus,
    RelativeVector3D,
    reconstruct_relative_landmarks,
)
from .scale_estimation import (
    ArchitecturalDimensionPrior,
    ArchitecturalPriorProvenance,
    ArchitecturalScaleEstimate,
    ScaleCueVote,
    VisualScaleCue,
    estimate_architectural_scale,
)
from .stair_system_links import SceneStairSystemLink
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .topology import SceneRelation
from .wall_profile import WallProfileObservation
from .wall_profile_scene import ArchitecturalScene
from .multi_run_stair_fidelity import validate_scene_against_survey
from .multi_run_stair_geometry import (
    MultiRunStairGeometryFacts,
    MultiRunStairGeometryReport,
    StairRunJunction,
    analyze_multi_run_stair_geometry,
)
from .roof_geometry import (
    GableRoofGeometry,
    GableRoofPlane,
    RoofGeometryAssessment,
    RoofLine,
    derive_roof_geometry,
    derive_scene_roof_geometry,
)
from .spatial_analysis import (
    ChimneyBearingAssessment,
    SceneObjectEnvelope,
    SpatialPairFacts,
    SpatialRelationReport,
    analyze_scene_spatial_relations,
    scene_object_envelopes,
)
from .stair_spatial import (
    StairCorridor,
    StairEndpointContact,
    StairSpatialReport,
    analyze_stair_spatial,
)
from .topology_projection import project_scene_to_building
__all__=[
    "ArchitecturalDimensionPrior","ArchitecturalLandmarkObservation","ArchitecturalLandmarkStatus","ArchitecturalLandmarkTrack","ArchitecturalPriorProvenance","ArchitecturalScaleEstimate","ArchitecturalScene","CalibratedPhotoIntrinsics","Chimney","ChimneyBearingAssessment","DeckBoardDirection","EdgeAccessSpan","EdgeTreatment","EquipmentType","Evidence","ExteriorMaterial","FR_OPENING_PRIOR_CATALOG_VERSION","GLASS_BLOCK_PRIOR_CATALOG_VERSION",
    "FacadeEquipment","FacadeVisibility","GableRoofGeometry","GableRoofPlane","GlassBlockGridPriorQuery","GradeProfile","HostFaceEvidence","HumanRelativeLevelIssue","HumanRelativeLevelReport","MultiRunStairGeometryFacts","MultiRunStairGeometryReport","NormalizedImagePoint","NormalizedImageQuadrilateral","OpeningPriorQuery","PartialWallSegment","PhotoGeometryAnnotation","PhotoScaleCueBinding","PlanarPhotoRectification","Platform","PlatformEdge","PlatformEdges","PlatformStructureKind","PlatformStructureObservation","ProjectionIssue","ProjectionResult","ReferenceExtentCoverage",
    "ProjectionSeverity","PropertyValue","RelativeCameraEstimationResult","RelativeCameraEstimationStatus","RelativeCameraHypothesis","RelativeLandmarkCandidate","RelativeLandmarkObservation","RelativeLandmarkTrack","RelativePoint3D","RelativeReconstructionResult","RelativeReconstructionStatus","RelativeVector3D","RoofGeometryAssessment","RoofLine","RoofPitchRange","ScaleCueVote","SceneObjectEnvelope","SceneOpening","SceneRelation","SceneRoof","SceneRoofType","SceneStairSystemLink","SceneSurveyIssue","SceneSurveySeverity","SceneVolume","SpatialPairFacts","SpatialRelationReport","StairCorridor","StairEndpointContact","StairRun","StairRunJunction","StairSpatialReport",
    "SupportPost","Terrain","VisibilitySpan","VisibilityState","VisualScaleCue","WallProfileObservation","analyze_multi_run_stair_geometry","analyze_scene_spatial_relations","analyze_stair_spatial","build_relative_landmark_tracks","build_visual_scale_cues_from_photo_geometry","derive_roof_geometry","derive_scene_roof_geometry","estimate_architectural_scale","estimate_relative_camera_pair","france_residential_opening_priors_v01","glass_block_grid_prior_v01","project_scene_to_building","reconstruct_relative_landmarks","rectified_plane_reference_annotation","rectify_photo_geometry_annotation","rectify_point","resolve_host_face","scene_object_envelopes","validate_architectural_landmark_tracks","validate_host_face_candidate","validate_photo_geometry_annotations","validate_scene_against_human_relative_level_facts","validate_scene_against_survey",
]
