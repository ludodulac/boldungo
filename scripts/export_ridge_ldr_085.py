"""Export the real LDraw-readable preview of the 083/084 physical ridge kit.

Usage:
  LDRAW_ROOT=/path/to/ldraw python scripts/export_ridge_ldr_085.py --output-dir artifacts/lego2-085
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from lego_geometry_engine import LDrawLibrary
from brickhouse.bricks.ridge_trial_ldraw_export_085 import write_experimental_ldr_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ldraw-root", type=Path,
                        default=Path(os.environ["LDRAW_ROOT"])
                        if "LDRAW_ROOT" in os.environ else None)
    parser.add_argument("--output-dir", type=Path,
                        default=Path("artifacts/lego2-085"))
    args = parser.parse_args()
    if args.ldraw_root is None or not args.ldraw_root.is_dir():
        parser.error("--ldraw-root or LDRAW_ROOT must point to an official LDraw library")
    result = write_experimental_ldr_files(args.output_dir, LDrawLibrary(args.ldraw_root))
    print(f"LDRAW_FRAME_FILE={args.output_dir / result['frame_file']}")
    print(f"LDRAW_UNCERTIFIED_PREVIEW={args.output_dir / result['preview_file']}")
    print(f"LDRAW_TOTAL_PIECES={result['part_count']}")
    print(f"LDRAW_FRAME_STEPS={len(result['frame_steps'])}")
    print(f"LDRAW_PHYSICAL_CERTIFICATION={result['physical_certification']}")


if __name__ == "__main__":
    main()
