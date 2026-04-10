# Part 2: OpenSplat 3D Reconstruction (AMtown02)

## Project Goal

Build a viewable and editable 3D Gaussian Splatting scene from AMtown02 using:

- images from AMtown02
- camera poses from ORB-SLAM3 (`CameraTrajectory.txt`)
- OpenSplat GPU training

Final deliverables include `.ply` and compressed `.splat` outputs for visualization.

## End-to-End Pipeline

1. **Pose source**  
   ORB-SLAM3 monocular VO trajectory (`CameraTrajectory.txt`) was used as camera priors.

2. **Input conversion for OpenSplat**  
   We converted trajectory + undistorted images into COLMAP-compatible layout:
   - `cameras.txt/.bin`
   - `images.txt/.bin`
   - `points3D.txt/.bin` (generated sparse initialization points)

3. **GPU training with OpenSplat**  
   OpenSplat was run on CUDA and monitored continuously until completion.

4. **Export models**  
   Final outputs were exported as:
   - dense Gaussian model: `.ply`
   - compressed viewer-friendly model: `.splat`

## Stability Notes

On this machine, full-frame loading at `step=1` with `-d 2` repeatedly triggered WSL OOM kills during image loading.

To ensure a fully reproducible and complete run on available memory, we used:

- sampling `step=10` (672 images from 6711 matched pose-image pairs)
- full training schedule to `35000` steps

This produced a stable end-to-end result with valid checkpoints and final model export.

## Final Training Run

```bash
./opensplat /mnt/f/Cursor/opensplat/amtown02_gs_step10 \
  -o /mnt/f/Cursor/opensplat/output/amtown02_vo_gs_step10/splat.ply \
  -n 35000 -d 2 -s 2000
```

Completion evidence:

- final log line: `Step 35000: 0.108615 (100%)`
- final files written:
  - `cameras.json`
  - `splat.ply`

## Artifacts (Published)

- `output/amtown02_step10_final.splat`
- `output/amtown02_step10_cameras.json`
- `output/amtown02_step10_train.log`
- `output/PART2_AMtown02_OpenSplat_results.md`

## Visualization

Use [PlayCanvas Viewer](https://playcanvas.com/viewer):

1. Open the viewer.
2. Drag and drop `output/amtown02_step10_final.splat`.
3. Inspect structure completeness, floaters, and rendering quality.

## Reproducibility Summary

- Environment: WSL2 + CUDA
- Renderer/Trainer: OpenSplat
- Pose provider: ORB-SLAM3 monocular VO
- Dataset scene: AMtown02
- Training steps: 35000
