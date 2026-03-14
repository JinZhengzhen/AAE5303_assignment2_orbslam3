#!/usr/bin/env python3
"""
Image preprocessing helper for ORB-SLAM3 UAV sequences.

Supported operations (can be combined):
  - Image downscaling  (--scale)
  - CLAHE contrast enhancement  (--clahe)

The output is a directory of images in the same format as the input,
plus a timestamps.txt that can be used directly with mono_tum.

Usage examples:

  # Downscale only (0.75x)
  python3 scripts/preprocess_images.py \\
      --input  dataset/extracted_data \\
      --output dataset/extracted_data_075 \\
      --scale  0.75

  # CLAHE only
  python3 scripts/preprocess_images.py \\
      --input  dataset/extracted_data \\
      --output dataset/extracted_data_clahe \\
      --clahe

  # CLAHE + downscale (0.75x)
  python3 scripts/preprocess_images.py \\
      --input  dataset/extracted_data \\
      --output dataset/extracted_data_clahe_075 \\
      --clahe --clahe-clip 2.0 --clahe-grid 8 \\
      --scale  0.75

Input directory expectations:
  The script accepts two layouts:

  Layout A — TUM-style with timestamps.txt:
    extracted_data/
    ├── timestamps.txt     (one timestamp per line, in seconds)
    └── *.png / *.jpg      (sorted alphabetically or numerically)

  Layout B — images only (no timestamps.txt):
    extracted_data/
    └── *.png / *.jpg

  In Layout B, a synthetic 10 Hz timestamps.txt is generated.
  If you have a custom timestamps file, pass --timestamps explicitly.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}


def _collect_images(input_dir: Path) -> List[Path]:
    """Return sorted list of image paths from input_dir."""
    imgs = sorted(
        p for p in input_dir.iterdir()
        if p.suffix.lower() in _IMAGE_EXTS
    )
    if not imgs:
        raise RuntimeError(f"No images found in {input_dir}")
    return imgs


def _load_timestamps(input_dir: Path, ts_file: Optional[Path], n: int, fps: float) -> List[float]:
    """Load or synthesise timestamps (seconds)."""
    candidate = ts_file or (input_dir / "timestamps.txt")
    if candidate.exists():
        with candidate.open() as f:
            timestamps = [float(line.strip()) for line in f if line.strip()]
        if len(timestamps) != n:
            print(
                f"[warn] timestamps.txt has {len(timestamps)} entries but found {n} images. "
                "Falling back to synthetic timestamps.",
                file=sys.stderr,
            )
        else:
            return timestamps
    # Synthetic timestamps starting at t=0
    return [i / fps for i in range(n)]


def _make_clahe(clip: float, grid: int) -> cv2.CLAHE:
    return cv2.createCLAHE(clipLimit=clip, tileGridSize=(grid, grid))


def _process_image(
    img_path: Path,
    scale: float,
    clahe: Optional[cv2.CLAHE],
) -> np.ndarray:
    """Load, optionally apply CLAHE, optionally resize."""
    img = cv2.imread(str(img_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise RuntimeError(f"Failed to read image: {img_path}")

    if clahe is not None:
        # CLAHE operates on grayscale; convert, apply, merge back
        if img.ndim == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            enhanced = clahe.apply(gray)
            # Reconstruct as 3-channel (ORB-SLAM3 accepts BGR)
            img = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        else:
            img = clahe.apply(img)

    if abs(scale - 1.0) > 1e-6:
        h, w = img.shape[:2]
        new_w = max(1, round(w * scale))
        new_h = max(1, round(h * scale))
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        img = cv2.resize(img, (new_w, new_h), interpolation=interp)

    return img


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preprocess ORB-SLAM3 image sequences (CLAHE + downscale)."
    )
    parser.add_argument("--input", required=True, help="Input image directory.")
    parser.add_argument("--output", required=True, help="Output image directory.")
    parser.add_argument(
        "--scale", type=float, default=1.0,
        help="Resize scale factor (e.g., 0.75 or 0.5). Default: 1.0 (no resize).",
    )
    parser.add_argument("--clahe", action="store_true", help="Apply CLAHE contrast enhancement.")
    parser.add_argument(
        "--clahe-clip", type=float, default=2.0,
        help="CLAHE clip limit (default: 2.0). Higher = more aggressive.",
    )
    parser.add_argument(
        "--clahe-grid", type=int, default=8,
        help="CLAHE tile grid size (default: 8). Applied as grid×grid tiles.",
    )
    parser.add_argument("--fps", type=float, default=10.0, help="FPS for synthetic timestamps.")
    parser.add_argument("--timestamps", default=None, help="Optional path to timestamps.txt.")
    parser.add_argument(
        "--fx", type=float, default=1444.43,
        help="Camera focal length fx (default: HKisland calibration). Used in scaled-intrinsics printout.",
    )
    parser.add_argument(
        "--fy", type=float, default=1444.34,
        help="Camera focal length fy (default: HKisland calibration). Used in scaled-intrinsics printout.",
    )
    parser.add_argument(
        "--cx", type=float, default=1179.50,
        help="Camera principal point cx (default: HKisland calibration). Used in scaled-intrinsics printout.",
    )
    parser.add_argument(
        "--cy", type=float, default=1044.90,
        help="Camera principal point cy (default: HKisland calibration). Used in scaled-intrinsics printout.",
    )

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.is_dir():
        print(f"ERROR: Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    imgs = _collect_images(input_dir)
    ts_path = Path(args.timestamps) if args.timestamps else None
    timestamps = _load_timestamps(input_dir, ts_path, len(imgs), args.fps)

    clahe_obj: Optional[cv2.CLAHE] = None
    if args.clahe:
        clahe_obj = _make_clahe(args.clahe_clip, args.clahe_grid)

    ops = []
    if args.clahe:
        ops.append(f"CLAHE(clip={args.clahe_clip}, grid={args.clahe_grid})")
    if abs(args.scale - 1.0) > 1e-6:
        ops.append(f"scale={args.scale}")
    if not ops:
        print("No operations requested (--clahe or --scale required). Exiting.")
        return 0

    print(f"Processing {len(imgs)} images: {', '.join(ops)}")
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")

    out_ts_lines: List[str] = []

    for i, (img_path, ts) in enumerate(zip(imgs, timestamps)):
        out_img = _process_image(img_path, args.scale, clahe_obj)
        out_name = output_dir / img_path.name
        cv2.imwrite(str(out_name), out_img)
        out_ts_lines.append(f"{ts:.9f}")

        if (i + 1) % 100 == 0 or (i + 1) == len(imgs):
            print(f"  [{i + 1}/{len(imgs)}]", end="\r", flush=True)

    print()  # newline after progress

    ts_out = output_dir / "timestamps.txt"
    ts_out.write_text("\n".join(out_ts_lines) + "\n", encoding="utf-8")
    print(f"Saved timestamps to: {ts_out}")

    if abs(args.scale - 1.0) > 1e-6:
        # Print the scaled intrinsics for reference using provided (or default) values
        fx, fy, cx, cy = args.fx, args.fy, args.cx, args.cy
        s = args.scale
        # Derive original dimensions from the first processed image rather than hardcoding
        first_img = cv2.imread(str(imgs[0]), cv2.IMREAD_UNCHANGED)
        orig_h, orig_w = (first_img.shape[:2] if first_img is not None else (2048, 2448))
        print("\nScaled intrinsics (update your yaml accordingly):")
        print(f"  Camera1.fx: {fx * s:.4f}")
        print(f"  Camera1.fy: {fy * s:.4f}")
        print(f"  Camera1.cx: {cx * s:.4f}")
        print(f"  Camera1.cy: {cy * s:.4f}")
        w_new = round(orig_w * s)
        h_new = round(orig_h * s)
        print(f"  Camera1.width:  {w_new}")
        print(f"  Camera1.height: {h_new}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
