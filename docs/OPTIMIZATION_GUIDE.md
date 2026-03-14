# ORB-SLAM3 Optimization Guide

> **AAE5303 – Visual Odometry with ORB-SLAM3**  
> Baseline results (default parameters, HKisland_GNSS03 sequence, `CameraTrajectory.txt`):  
> ATE=132.15 m | RPE Trans=2.87 m/m | RPE Rot=173.33 deg/100m | Completeness=87.01%  
> (Leaderboard baseline on AMtown02: ATE≈88.2 m | RPE Trans≈2.04 m/m | RPE Rot≈76.7 deg/100m | Completeness≈95.73%)

---

## Optimization priority order

Work through these in order. **Do not change multiple parameters simultaneously** — you will not know which change had which effect.

```
1. Fix correctness issues (trajectory file, timestamps)
2. Tune ORB feature extraction
3. Try image downscaling
4. Add preprocessing (CLAHE)
5. Advanced: image masking, VIO mode
```

---

## 1. Correctness checks (zero-cost, highest impact)

### 1a. Confirm you are using `CameraTrajectory.txt`

```bash
wc -l CameraTrajectory.txt     # should be thousands of lines
wc -l KeyFrameTrajectory.txt   # typically hundreds of lines
```

Always evaluate `CameraTrajectory.txt`. Using keyframes biases completeness and drift rates.

### 1b. Verify timestamps are in seconds

```bash
head -3 CameraTrajectory.txt
head -3 ground_truth.txt
```

Expected: the first column is a large float like `1698132964.499888`, **not** `1`, `2`, `3`.

If you see frame indices, fix the trajectory export (see `leaderboard/ORB_SLAM3_TIPS.md`).

### 1c. Verify the camera config file used at runtime

Make sure the yaml you pass to `mono_tum` is `HKisland_Mono_v1.yaml` (or a preset variant),
not a stale copy with incorrect intrinsics.

---

## 2. ORB feature extraction tuning

### Baseline parameters

```yaml
ORBextractor.nFeatures:   1500
ORBextractor.scaleFactor: 1.2
ORBextractor.nLevels:     8
ORBextractor.iniThFAST:   20
ORBextractor.minThFAST:   7
```

### What each parameter controls

| Parameter | Effect when increased |
|-----------|-----------------------|
| `nFeatures` | More features per frame → better matching, higher CPU cost |
| `scaleFactor` | Wider pyramid levels → handles larger scale changes, but misses fine detail |
| `nLevels` | More pyramid levels → better scale range, more memory |
| `iniThFAST` | Higher → only strong corners → fewer but more reliable features |
| `minThFAST` | Higher → fewer fallback features in low-texture regions |

### Recommended tuning sequence

**Step 1 — vary only `nFeatures`** (keep everything else at baseline):

| Experiment | nFeatures | Expected effect |
|-----------|-----------|-----------------|
| 1 (baseline) | 1500 | Reference |
| 2 | 2000 | Modest completeness gain |
| 3 | 2500 | **Recommended first try** |
| 4 | 3000 | Diminishing returns; higher CPU |

Pick the `nFeatures` value that gives the best completeness without introducing new tracking failures.

**Step 2 — vary FAST thresholds** (fix `nFeatures` from step 1):

| Experiment | iniThFAST | minThFAST | Expected effect |
|-----------|-----------|-----------|-----------------|
| A (baseline) | 20 | 7 | Reference |
| B | 15 | 5 | **Recommended — UAV aerial scenes** |
| C | 12 | 5 | More low-texture features |
| D | 10 | 5 | Aggressive; may add noise |

Lowering thresholds helps in low-texture regions (roads, rooftops, open sky borders).

### Ready-to-use preset configs

Three preset yaml files are provided in `docs/optimization_presets/`. Copy the desired
preset into your ORB-SLAM3 examples directory to use it:

```bash
# Example: use the "stable" preset
cp docs/optimization_presets/preset_a_stable.yaml \
   ~/workspace/ORB_SLAM3/Examples/Monocular/HKisland_Mono.yaml
```

| Preset | nFeatures | iniThFAST | minThFAST | Notes |
|--------|-----------|-----------|-----------|-------|
| `preset_a_stable.yaml` | 2500 | 15 | 5 | **Best first try** |
| `preset_b_aerial.yaml` | 3000 | 15 | 5 | Denser, wider pyramid |
| `preset_c_downscaled_075.yaml` | 2500 | 15 | 5 | 0.75× resolution |

---

## 3. Image downscaling

High-resolution input (2448×2048) is not always better for VO:

- Motion blur is proportionally larger at high resolution.
- Matching becomes less stable with very large images.
- Processing latency increases (can cause thread stalls in real-time mode).

**Recommended experiments:**

| Scale | Width | Height | Notes |
|-------|-------|--------|-------|
| 1.0 (original) | 2448 | 2048 | Baseline |
| 0.75 | 1836 | 1536 | **Good trade-off** |
| 0.5 | 1224 | 1024 | Most stable; least detail |

**Important:** when you downscale images you **must** scale intrinsics accordingly:

```
fx_new = fx_original × scale
fy_new = fy_original × scale
cx_new = cx_original × scale
cy_new = cy_original × scale
width_new  = round(width_original  × scale)
height_new = round(height_original × scale)
```

Distortion coefficients (`k1 k2 p1 p2 k3`) do **not** change with scale.

Use the provided preprocessing script to downscale images:

```bash
python3 scripts/preprocess_images.py \
    --input  dataset/extracted_data \
    --output dataset/extracted_data_075 \
    --scale  0.75
```

Then use `preset_c_downscaled_075.yaml` (already has scaled intrinsics) for the ORB-SLAM3 run.

---

## 4. Image preprocessing (CLAHE)

CLAHE (Contrast Limited Adaptive Histogram Equalization) can help when:

- The scene has large bright/dark regions (strong sun, shadows).
- Low-texture regions (uniform rooftops, roads) cause tracking failures.

```bash
python3 scripts/preprocess_images.py \
    --input  dataset/extracted_data \
    --output dataset/extracted_data_clahe \
    --clahe \
    --clahe-clip 2.0 \
    --clahe-grid 8
```

Combine CLAHE and downscaling in one pass:

```bash
python3 scripts/preprocess_images.py \
    --input  dataset/extracted_data \
    --output dataset/extracted_data_clahe_075 \
    --clahe \
    --clahe-clip 2.0 \
    --clahe-grid 8 \
    --scale  0.75
```

> **Caution**: overly strong CLAHE (clip > 4.0) can introduce artifacts and generate false
> feature matches. Always compare the four metrics before and after.

---

## 5. Suggested 9-experiment matrix

Run these in order. Record all four metrics for each run.

| # | nFeatures | iniThFAST | minThFAST | Scale | Preset |
|---|-----------|-----------|-----------|-------|--------|
| 1 | 1500 | 20 | 7 | 1.0 | baseline (`HKisland_Mono_v1.yaml`) |
| 2 | 2000 | 20 | 7 | 1.0 | manual edit |
| 3 | 2500 | 20 | 7 | 1.0 | manual edit |
| 4 | 2500 | 15 | 5 | 1.0 | `preset_a_stable.yaml` |
| 5 | 3000 | 15 | 5 | 1.0 | `preset_b_aerial.yaml` |
| 6 | 2000 | 15 | 5 | 0.75 | manual edit of `preset_c_downscaled_075.yaml` |
| 7 | 2500 | 15 | 5 | 0.75 | `preset_c_downscaled_075.yaml` |
| 8 | 2500 | 12 | 5 | 0.75 | manual edit of `preset_c_downscaled_075.yaml` |
| 9 | 2500 | 15 | 5 | 0.5 | manual edit (scale intrinsics by 0.5) |

### Evaluation priority

When comparing runs, prioritise metrics in this order:

1. **Completeness ≥ 90%** — if this is low, the trajectory has large gaps; other metrics are misleading.
2. **RPE Rot Drift** — rotation errors degrade the overall trajectory shape.
3. **RPE Trans Drift** — local translation consistency.
4. **ATE RMSE** — global error (also affected by scale alignment).

### Experiment log template

Copy this block for each run:

```
Run #: ___
Date/time: ___
nFeatures: ___   iniThFAST: ___   minThFAST: ___
Scale: ___   CLAHE: yes/no   Preset: ___
SLAM output: CameraTrajectory.txt (N poses)

ATE RMSE (m):            ___
RPE Trans Drift (m/m):   ___
RPE Rot Drift (deg/100m): ___
Completeness (%):        ___

Notes: ___
```

---

## 6. Advanced techniques

### 6a. Image region masking (suppress sky / static regions)

If tracking frequently fails on sky or water, add a mask that prevents ORB from extracting
features in those image regions. This requires a small code change in ORB-SLAM3.

### 6b. Visual-Inertial Odometry (VIO)

If the dataset provides IMU data and the course allows it, switching to VIO mode
(`Examples/Monocular_Inertial/`) yields large improvements in rotation estimation and scale
consistency. This is the single highest-impact change available.

### 6c. Loop closure

The default `mono_tum` example runs in VO-only mode (loop closure disabled or not triggered).
Running in full SLAM mode can reduce drift on long trajectories if the UAV revisits areas.

---

## Expected improvement ranges

Starting from the current baseline (ATE=132 m, Completeness=87%):

| Action | Expected Completeness gain | Expected RPE Rot improvement |
|--------|---------------------------|------------------------------|
| Correct trajectory file | up to +10 pp | significant |
| nFeatures 1500→2500 | +3–8 pp | 10–30% |
| FAST threshold 20/7→15/5 | +2–5 pp | 10–25% |
| 0.75 downscale | ±2 pp | 5–20% |
| CLAHE | ±3 pp | 5–15% |
| VIO mode (if allowed) | +5–10 pp | 50–70% |

These are rough estimates based on typical UAV aerial datasets. Actual gains depend on the
specific sequence characteristics.
