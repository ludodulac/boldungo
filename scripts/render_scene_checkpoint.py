#!/usr/bin/env python3
"""Render a deterministic PNG checkpoint through Boldungo's real Scene viewer.

This is intentionally a thin adapter: it does not render Scene geometry itself.
It serves the existing frontend, injects one ArchitecturalScene into the viewer's
existing localStorage input, selects a deterministic camera preset, and captures
the real WebGL canvas with Playwright.
"""
from __future__ import annotations

import argparse
import json
import shutil
import socketserver
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1280, "height": 900}
PRESETS = ("front", "south-left", "rear-oblique", "perspective")


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


def render_scene_checkpoint(scene_path: Path, preset: str, output_path: Path, repo_root: Path) -> None:
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    if scene.get("schema_version") != "0.2" or not isinstance(scene.get("volumes"), list):
        raise ValueError("Input must be a materialized ArchitecturalScene schema_version 0.2")

    server, thread = _serve(repo_root)
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
            page.wait_for_timeout(350)  # let OrbitControls damping settle deterministically
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
    args = parser.parse_args()
    render_scene_checkpoint(args.scene, args.camera_preset, args.output, args.repo_root.resolve())
    print(args.output)


if __name__ == "__main__":
    main()
