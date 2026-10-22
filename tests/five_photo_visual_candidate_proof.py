from pathlib import Path
import subprocess, time
from playwright.sync_api import sync_playwright

out=Path("/tmp/five-photo-captures"); out.mkdir(parents=True,exist_ok=True)
server=subprocess.Popen(["python","-m","http.server","8765","--directory","frontend"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    time.sleep(1)
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={"width":1440,"height":1000}, device_scale_factor=1)
        page.goto("http://127.0.0.1:8765/viewer.html",wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.locator("#viewer").screenshot(path=str(out/"perspective.png"))
        for name,selector in [("front","#view-front"),("rear","#view-rear"),("left","#view-left")]:
            page.locator(selector).click(); page.wait_for_timeout(500)
            page.locator("#viewer").screenshot(path=str(out/f"{name}.png"))
        browser.close()
finally:
    server.terminate(); server.wait(timeout=5)
