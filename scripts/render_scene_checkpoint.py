#!/usr/bin/env python3
"""Render a deterministic PNG checkpoint through Boldungo's real Scene viewer.

This is intentionally a thin adapter: it does not render Scene geometry itself.
It serves the existing frontend, injects one ArchitecturalScene into the viewer's
existing localStorage input, selects a deterministic camera preset, and captures
the real WebGL canvas with Playwright.

For the bounded stair-readability experiment, --stepped-stairs serves a temporary
copy of the same viewer with only renderStairs() replaced by a tread renderer.
The Scene is never mutated and the source viewer file is not rewritten by this mode.
"""
from __future__ import annotations

import argparse
import json
import shutil
import socketserver
import tempfile
import threading
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1280, "height": 900}
PRESETS = ("front", "south-left", "rear-oblique", "perspective")

LEGACY_RENDER_STAIRS = """function renderStairs() {
  for (const stair of currentScene.stairs ?? []) {
    const start = stair.start, end = stair.end;
    const width = Number(stair.width);
    if (!start || !end || ![Number(start.x), Number(start.y), Number(start.z), Number(end.x), Number(end.y), Number(end.z), width].every(Number.isFinite)) continue;
    const from = new THREE.Vector3(Number(start.x), Number(start.z), Number(start.y));
    const to = new THREE.Vector3(Number(end.x), Number(end.z), Number(end.y));
    const delta = to.clone().sub(from);
    const length = delta.length();
    if (!(length > 0)) continue;
    const thickness = 0.16;
    const geometry = new THREE.BoxGeometry(width, thickness, length);
    const mesh = new THREE.Mesh(geometry, exteriorMaterial(stair.material));
    addEdges(mesh);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), delta.clone().normalize());
    mesh.position.copy(from).add(to).multiplyScalar(0.5);
    mesh.userData.architecturalObjectId = stair.id;
    group.add(mesh);
  }
}
"""

STEPPED_RENDER_STAIRS = """function renderStairs() {
  for (const stair of currentScene.stairs ?? []) {
    const start = stair.start, end = stair.end;
    const width = Number(stair.width);
    if (!start || !end || ![Number(start.x), Number(start.y), Number(start.z), Number(end.x), Number(end.y), Number(end.z), width].every(Number.isFinite)) continue;

    const rawFrom = new THREE.Vector3(Number(start.x), Number(start.z), Number(start.y));
    const rawTo = new THREE.Vector3(Number(end.x), Number(end.z), Number(end.y));
    const lower = rawFrom.y <= rawTo.y ? rawFrom.clone() : rawTo.clone();
    const upper = rawFrom.y <= rawTo.y ? rawTo.clone() : rawFrom.clone();
    const horizontal = new THREE.Vector3(upper.x - lower.x, 0, upper.z - lower.z);
    const horizontalLength = horizontal.length();
    const rise = upper.y - lower.y;
    if (!(horizontalLength > 0) || !(rise >= 0)) continue;

    // Rendering convention only: discretize the already-defined run into readable
    // horizontal treads. Count is chosen for preview legibility, not as a measured
    // architectural tread count. Endpoints, width and rise remain exactly Scene-owned.
    const stepCount = Math.max(3, Math.min(16, Math.round(Math.max(horizontalLength / 0.28, rise / 0.18))));
    const direction = horizontal.clone().normalize();
    const treadDepth = horizontalLength / stepCount;
    const yaw = Math.atan2(direction.x, direction.z);
    const baseY = lower.y - 0.04;

    for (let index = 0; index < stepCount; index += 1) {
      const f0 = index / stepCount;
      const f1 = (index + 1) / stepCount;
      const topY = lower.y + rise * f1;
      const boxHeight = Math.max(0.08, topY - baseY);
      const center = lower.clone().addScaledVector(horizontal, (f0 + f1) / 2);
      const geometry = new THREE.BoxGeometry(width, boxHeight, treadDepth);
      const mesh = new THREE.Mesh(geometry, exteriorMaterial(stair.material));
      addEdges(mesh);
      mesh.rotation.y = yaw;
      mesh.position.set(center.x, baseY + boxHeight / 2, center.z);
      mesh.userData.architecturalObjectId = stair.id;
      mesh.userData.renderingConvention = 'stepped preview from Scene run endpoints; tread count is visual only';
      group.add(mesh);
    }
  }
}
"""


def _browser_path() -> str:
    path = next((shutil.which(name) for name in (
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"
    ) if shutil.which(name)), None)
    if not path:
        raise RuntimeError("No Chromium/Chrome binary available")
    return path


def _serve(root: Path):
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


@contextmanager
def _viewer_root(repo_root: Path, stepped_stairs: bool):
    if not stepped_stairs:
        yield repo_root
        return
    with tempfile.TemporaryDirectory(prefix="boldungo-scene-viewer-") as tmp:
        root = Path(tmp)
        shutil.copytree(repo_root / "frontend", root / "frontend")
        viewer_js = root / "frontend" / "scene-viewer.js"
        source = viewer_js.read_text(encoding="utf-8")
        if LEGACY_RENDER_STAIRS not in source:
            raise RuntimeError("Could not locate the expected legacy renderStairs() implementation")
        viewer_js.write_text(source.replace(LEGACY_RENDER_STAIRS, STEPPED_RENDER_STAIRS, 1), encoding="utf-8")
        yield root


def _apply_preset(page, preset: str) -> None:
    # Existing viewer buttons own the canonical front/rear/perspective framing.
    if preset == "front":
        page.locator("#view-front").click()
    elif preset == "perspective":
        page.locator("#reset-view").click()
    elif preset == "south-left":
        # South is the viewer's left façade. Start from the existing left preset,
        # then use one fixed OrbitControls drag for a readable oblique checkpoint.
        page.locator("#view-left").click()
        canvas = page.locator("#viewer")
        box = canvas.bounding_box()
        if not box:
            raise RuntimeError("Scene viewer canvas has no bounding box")
        x = box["x"] + box["width"] * 0.50
        y = box["y"] + box["height"] * 0.50
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x - box["width"] * 0.12, y - box["height"] * 0.04, steps=12)
        page.mouse.up()
    elif preset == "rear-oblique":
        page.locator("#view-rear").click()
        canvas = page.locator("#viewer")
        box = canvas.bounding_box()
        if not box:
            raise RuntimeError("Scene viewer canvas has no bounding box")
        x = box["x"] + box["width"] * 0.50
        y = box["y"] + box["height"] * 0.50
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x + box["width"] * 0.14, y - box["height"] * 0.04, steps=12)
        page.mouse.up()
    else:
        raise ValueError(f"Unknown camera preset: {preset}")


def render_scene_checkpoint(
    scene_path: Path,
    preset: str,
    output_path: Path,
    repo_root: Path,
    zoom_out: float = 0.0,
    stepped_stairs: bool = False,
) -> None:
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    if scene.get("schema_version") != "0.2" or not isinstance(scene.get("volumes"), list):
        raise ValueError("Input must be a materialized ArchitecturalScene schema_version 0.2")

    with _viewer_root(repo_root, stepped_stairs) as served_root:
        server, thread = _serve(served_root)
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/frontend/scene-viewer.html"
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, executable_path=_browser_path(), args=["--no-sandbox"])
                page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1)
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                payload = json.dumps(scene, separators=(",", ":"))
                page.add_init_script(
                    script=f"localStorage.setItem('brickhouse.previewArchitecturalScene', {json.dumps(payload)});"
                )
                response = page.goto(url, wait_until="networkidle", timeout=30000)
                if not response or not response.ok:
                    raise RuntimeError(f"scene-viewer HTTP failure: {response.status if response else 'no response'}")
                page.locator("#viewer").wait_for(state="visible", timeout=10000)
                page.wait_for_function("() => document.querySelector('#message')?.textContent.includes('Aperçu architectural chargé')")
                _apply_preset(page, preset)
                page.wait_for_timeout(350)
                if zoom_out:
                    canvas = page.locator("#viewer")
                    box = canvas.bounding_box()
                    if not box:
                        raise RuntimeError("Scene viewer canvas has no bounding box")
                    page.mouse.move(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.5)
                    page.mouse.wheel(0, zoom_out)
                    page.wait_for_timeout(350)
                if errors:
                    raise RuntimeError(f"Scene viewer runtime errors: {errors}")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                page.locator("#viewer").screenshot(path=str(output_path))
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scene", type=Path, help="Materialized ArchitecturalScene JSON (schema 0.2)")
    parser.add_argument("camera_preset", choices=PRESETS)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--zoom-out", type=float, default=0.0)
    parser.add_argument("--stepped-stairs", action="store_true", help="Use experimental tread-based stair rendering without mutating the Scene")
    args = parser.parse_args()
    render_scene_checkpoint(
        args.scene,
        args.camera_preset,
        args.output,
        args.repo_root.resolve(),
        zoom_out=args.zoom_out,
        stepped_stairs=args.stepped_stairs,
    )
    print(args.output)


if __name__ == "__main__":
    main()
