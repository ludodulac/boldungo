"""Fetch a bounded, pinned LDraw part dependency closure for a small probe.

Source is a pinned public LDraw library mirror, containing LDraw files with
their original authorship and licenses. The files are downloaded only to the
CI runner (never copied into our repository). Not a replacement for a user's
full current official LDraw installation.
"""
from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

LDraw_MIRROR_SHA = "c43ed06a128a10ed65675166bf42eb6fd608b9b0"
BASE = ("https://raw.githubusercontent.com/pybricks/ldraw/"
        + LDraw_MIRROR_SHA + "/")
SIMPLE_NAME = re.compile(r"^[0-9a-z][0-9a-z._-]*\.dat$")
TYPE1 = re.compile(r"^1\s+\S+\s+(?:\S+\s+){12}(.+\.dat)\s*$", re.IGNORECASE)


def locations(name: str):
    name = name.replace("\\", "/").strip().lower()
    if name.startswith("s/") and SIMPLE_NAME.fullmatch(name[2:]):
        return ["parts/" + name]
    if name.startswith(("48/", "8/")) and SIMPLE_NAME.fullmatch(name.split("/", 1)[1]):
        return ["p/" + name]
    if SIMPLE_NAME.fullmatch(name):
        return ["parts/" + name, "p/" + name]
    raise ValueError("Unsafe/unexpected LDraw reference: " + name)


def download_ldraw_subset(root: Path, *, initial=("30363.dat", "26603.dat"),
                          max_files=180):
    root.mkdir(parents=True, exist_ok=True)
    pending = deque(initial)
    done = {}
    while pending:
        name = pending.popleft().replace("\\", "/").lower()
        if name in done:
            continue
        if len(done) >= max_files:
            raise RuntimeError("LDRAW_DEPENDENCY_LIMIT_REACHED")
        payload = None
        dest = None
        for rel in locations(name):
            target = root / rel
            if target.is_file():
                payload, dest = target.read_text(encoding="utf-8"), target
                break
            try:
                with urlopen(BASE + rel, timeout=8) as response:
                    payload = response.read(400_000).decode("utf-8")
                dest = target
                break
            except HTTPError as exc:
                if exc.code == 404:
                    continue
                raise
        if payload is None or dest is None:
            raise FileNotFoundError("Official mirror reference unavailable: " + name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(payload, encoding="utf-8")
        done[name] = dest
        for line in payload.splitlines():
            m = TYPE1.match(line.strip())
            if m:
                dependency = m.group(1).strip().replace("\\", "/").lower()
                locations(dependency)  # validate before enqueuing
                if dependency not in done:
                    pending.append(dependency)
    return done


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--max-files", type=int, default=180)
    args = parser.parse_args()
    paths = download_ldraw_subset(args.output, max_files=args.max_files)
    print("LDRAW_PINNED_REVISION=" + LDraw_MIRROR_SHA)
    print("LDRAW_SUBSET_FILES=" + str(len(paths)))
    print("LDRAW_PARTS=" + ",".join(sorted(
        p.relative_to(args.output).as_posix()
        for p in paths.values() if p.parent.name == "parts"
    )))


if __name__ == "__main__":
    main()
