# PART 2: OpenSplat (3D Gaussian Splatting) on AMtown02

## Overview

This document records the final OpenSplat reconstruction run using ORB-SLAM3-derived poses from AMtown02.

- Dataset source images: `F:/Cursor/opensplat/undistorted`
- Pose source: `F:/Cursor/results/vo/CameraTrajectory.txt`
- OpenSplat input project: `F:/Cursor/opensplat/amtown02_gs_step10`
- Training mode: GPU (`Using CUDA`)

## Why step=10 was used

The machine repeatedly hit WSL OOM during full-frame loading (6711 frames, `-d 2`) before optimization started.  
To ensure stable end-to-end completion on this hardware, the reconstruction was run with pose/image sampling `step=10` (672 frames), then trained to full 35,000 iterations.

## Final training command

```bash
./opensplat /mnt/f/Cursor/opensplat/amtown02_gs_step10 \
  -o /mnt/f/Cursor/opensplat/output/amtown02_vo_gs_step10/splat.ply \
  -n 35000 -d 2 -s 2000
```

## Completion evidence

- Final log line: `Step 35000: 0.108615 (100%)`
- Final files written:
  - `cameras.json`
  - `splat.ply`

## Published artifacts in this repository

- `output/amtown02_step10_final.splat` (compressed, PlayCanvas-friendly)
- `output/amtown02_step10_cameras.json`
- `output/amtown02_step10_train.log`

## Visualization

Use [PlayCanvas Viewer](https://playcanvas.com/viewer):

1. Open the viewer URL.
2. Drag and drop `output/amtown02_step10_final.splat`.
3. Inspect geometry completeness, floaters, and rendering stability.
