"""Deterministic materialization of serialized benchmark Scene recipes.

This module applies only explicit operations already recorded in benchmark artifacts. It does
not infer geometry and contains no benchmark-specific morphology or dimensions.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from brickhouse.scene.wall_profile_scene import ArchitecturalScene


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def materialize_scene_recipe(recipe_path: Path) -> ArchitecturalScene:
    recipe_path = recipe_path.resolve()
    benchmark_dir = recipe_path.parent
    recipe = _load(recipe_path)
    payload = _load((benchmark_dir / recipe["base_scene"]).resolve())

    for overlay_name in recipe.get("apply_overlays_in_order", []):
        overlay = _load(benchmark_dir / overlay_name)
        operation = overlay.get("operation")

        if operation == "replace_stair_system_geometry":
            replaced = set(overlay["replaces_scene_stair_ids"])
            payload["stairs"] = [item for item in payload.get("stairs", []) if item["id"] not in replaced]
            payload["stairs"].extend(deepcopy(overlay["stairs"]))
            payload["stair_system_links"] = deepcopy(overlay["stair_system_links"])
            relation_updates = {item["relation_id"]: item for item in overlay["relation_updates"]}
            for relation in payload.get("relations", []):
                update = relation_updates.get(relation["id"])
                if update is not None:
                    relation.update(
                        {
                            key: update[key]
                            for key in ("subject_id", "object_id", "geometry_status", "statement")
                        }
                    )
            continue

        if operation == "replace_platform_geometry":
            replaced = set(overlay["replaces_scene_platform_ids"])
            payload["platforms"] = [
                item for item in payload.get("platforms", []) if item["id"] not in replaced
            ]
            payload["platforms"].extend(deepcopy(overlay["platforms"]))
            continue

        if operation == "update_platform_geometry":
            platform_updates = {item["platform_id"]: item for item in overlay["platform_updates"]}
            for platform in payload.get("platforms", []):
                update = platform_updates.get(platform["id"])
                if update is None:
                    continue
                if "position_z" in update:
                    platform["position"]["z"] = update["position_z"]
                if "position_y" in update:
                    platform["position"]["y"] = update["position_y"]
                if "depth" in update:
                    platform["depth"] = update["depth"]
                if "source" in update:
                    platform["source"] = deepcopy(update["source"])
                if "evidence" in update:
                    platform["evidence"] = deepcopy(update["evidence"])
                support_positions_y = update.get("support_positions_y", {})
                for support in platform.get("supports", []):
                    if "support_height" in update:
                        support["height"] = update["support_height"]
                    if support["id"] in support_positions_y:
                        support["position"]["y"] = support_positions_y[support["id"]]
                    if "source" in update:
                        support["source"] = deepcopy(update["source"])
            continue

        if operation == "update_opening_semantics":
            opening_updates = {item["opening_id"]: item for item in overlay["opening_updates"]}
            for opening in payload.get("openings", []):
                update = opening_updates.get(opening["id"])
                if update is None:
                    continue
                # Semantic evidence must not rewrite photo-derived metric geometry.
                for field in ("type", "has_sill", "has_decorative_surround", "window_style"):
                    if field in update:
                        opening[field] = deepcopy(update[field])
                if "opening_visual" in update:
                    visual = deepcopy(opening.get("opening_visual") or {})
                    visual.update(deepcopy(update["opening_visual"] or {}))
                    opening["opening_visual"] = visual or None
                opening.setdefault("evidence", []).extend(deepcopy(update.get("evidence", [])))
            continue

        if operation == "append_partial_wall_segments":
            existing_ids = {item["id"] for item in payload.get("partial_wall_segments", [])}
            additions = deepcopy(overlay.get("partial_wall_segments", []))
            duplicate_ids = existing_ids.intersection(item["id"] for item in additions)
            if duplicate_ids:
                raise ValueError(f"partial wall overlay duplicates existing IDs: {sorted(duplicate_ids)!r}")
            payload.setdefault("partial_wall_segments", []).extend(additions)
            continue

        raise ValueError(f"Unsupported benchmark Scene overlay operation: {operation!r}")

    payload["id"] = recipe["scene_id"]
    return ArchitecturalScene.model_validate(payload)
