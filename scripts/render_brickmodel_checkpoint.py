#!/usr/bin/env python3
"""Render a deterministic PNG checkpoint through Boldungo's real BrickModel viewer."""
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
    if preset == "front":
        page.locator("#view-front").click()
    elif preset == "perspective":
        page.locator("#reset-view").click()
    elif preset == "south-left":
        page.locator("#view-left").click()
        canvas = page.locator("#viewer")
        box = canvas.bounding_box()
        if not box:
            raise RuntimeError("BrickModel viewer canvas has no bounding box")
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
            raise RuntimeError("BrickModel viewer canvas has no bounding box")
        x = box["x"] + box["width"] * 0.50
        y = box["y"] + box["height"] * 0.50
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x + box["width"] * 0.14, y - box["height"] * 0.04, steps=12)
        page.mouse.up()
    else:
        raise ValueError(f"Unknown camera preset: {preset}")


def render_brickmodel_checkpoint(
    bundle_path: Path,
    preset: str,
    output_path: Path,
    repo_root: Path,
    zoom_out: float = 0.0,
) -> None:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    if bundle.get("schema_version") != "0.1" or not isinstance(bundle.get("brick_model", {}).get("parts"), list):
        raise ValueError("Input must be a BrickHouse export bundle schema_version 0.1")

    server, thread = _serve(repo_root)
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/frontend/viewer.html"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=_browser_path(), args=["--no-sandbox"])
            page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            payload = json.dumps(bundle, separators=(",", ":"))
            page.add_init_script(
                script=f"localStorage.setItem('brickhouse.pendingExport', {json.dumps(payload)});"
            )
            response = page.goto(url, wait_until="networkidle", timeout=30000)
            if not response or not response.ok:
                raise RuntimeError(f"viewer HTTP failure: {response.status if response else 'no response'}")
            page.locator("#viewer").wait_for(state="visible", timeout=10000)
            page.wait_for_function("() => document.querySelector('#model-summary dd')?.textContent !== '—'", timeout=30000)
            _apply_preset(page, preset)
            page.wait_for_timeout(500)
            if zoom_out:
                canvas = page.locator("#viewer")
                box = canvas.bounding_box()
                if not box:
                    raise RuntimeError("BrickModel viewer canvas has no bounding box")
                page.mouse.move(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.5)
                page.mouse.wheel(0, zoom_out)
                page.wait_for_timeout(500)
            if errors:
                raise RuntimeError(f"BrickModel viewer runtime errors: {errors}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            page.locator("#viewer").screenshot(path=str(output_path))
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("camera_preset", choices=PRESETS)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--zoom-out", type=float, default=0.0)
    args = parser.parse_args()
    render_brickmodel_checkpoint(
        args.bundle,
        args.camera_preset,
        args.output,
        args.repo_root.resolve(),
        zoom_out=args.zoom_out,
    )
    print(args.output)


if __name__ == "__main__":
    main()
