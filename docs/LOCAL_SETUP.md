# Local Setup & Deployment Guide

> **AAE5303 – Visual Odometry with ORB-SLAM3**

This guide explains how to set up and run the full pipeline locally, from a fresh Ubuntu 22.04 installation all the way to generating and evaluating a `CameraTrajectory.txt`.

---

## Architecture overview

This GitHub repository is **not** a standalone ORB-SLAM3 binary. It contains:

| Component | Location | Purpose |
|-----------|----------|---------|
| Camera configuration | `docs/camera_config.yaml` | Human-readable calibration reference |
| ORB-SLAM3 settings (v1.0 format) | `docs/HKisland_Mono_v1.yaml` | **Drop this into your ORB-SLAM3 build** |
| Evaluation script | `scripts/evaluate_vo_accuracy.py` | Computes ATE / RPE / Completeness |
| Figure generation | `scripts/generate_report_figures.py` | Plots trajectory comparison |
| Image preprocessing | `scripts/preprocess_images.py` | CLAHE + optional downscale |
| Optimization presets | `docs/optimization_presets/` | Ready-to-swap parameter configs |

You also need **two external resources** that are not part of this repo:

1. **ORB-SLAM3** (C++ build) — https://github.com/UZ-SLAMLab/ORB_SLAM3
2. **HKisland_GNSS03 dataset** (bag / images / ground truth) — provided by your instructor

---

## Recommended workspace layout

```
workspace/
├── ORB_SLAM3/                  ← external: cloned + compiled ORB-SLAM3
├── AAE5303_assignment2_orbslam3/  ← THIS repository (evaluation env)
└── dataset/
    ├── HKisland_GNSS03.bag     ← provided by instructor
    ├── extracted_data/         ← images extracted from the bag
    └── ground_truth.txt        ← RTK ground truth (TUM format)
```

---

## Step 1 — Set up the Python evaluation environment

```bash
cd AAE5303_assignment2_orbslam3

# Create virtual environment (Python 3.10 or 3.11 recommended)
python3 -m venv .venv
source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt
```

Verify `evo` is ready:

```bash
evo_ape --help
evo_rpe --help
```

---

## Step 2 — Install ORB-SLAM3 system dependencies

On Ubuntu 22.04:

```bash
sudo apt update
sudo apt install -y \
    build-essential cmake git pkg-config \
    libeigen3-dev libopencv-dev \
    libglew-dev libglfw3-dev \
    libboost-all-dev libssl-dev \
    libpython3-dev python3-dev
```

Install Pangolin (ORB-SLAM3 viewer):

```bash
git clone --depth 1 https://github.com/stevenlovegrove/Pangolin.git /tmp/Pangolin
cd /tmp/Pangolin
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel $(nproc)
sudo cmake --install build
cd -
```

---

## Step 3 — Clone and build ORB-SLAM3

```bash
git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git ~/workspace/ORB_SLAM3
cd ~/workspace/ORB_SLAM3

# Decompress the vocabulary file
cd Vocabulary
tar -xvf ORBvoc.txt.tar.gz
cd ..

# Build (uses build.sh which compiles ORB-SLAM3 + DBoW2 + g2o)
chmod +x build.sh
./build.sh
```

A successful build produces (among others):

```
Examples/Monocular/mono_tum
```

---

## Step 4 — Copy the camera settings into ORB-SLAM3

This repository ships a ready-to-use ORB-SLAM3 File.version 1.0 settings file:

```bash
cp ~/workspace/AAE5303_assignment2_orbslam3/docs/HKisland_Mono_v1.yaml \
   ~/workspace/ORB_SLAM3/Examples/Monocular/HKisland_Mono.yaml
```

> **Why a separate file?** `docs/camera_config.yaml` uses the short `Camera.fx` key style
> (old ORB-SLAM3 format). `docs/HKisland_Mono_v1.yaml` uses the `Camera1.fx` key style
> required by ORB-SLAM3 File.version 1.0 (the current upstream default). Always prefer
> `HKisland_Mono_v1.yaml` unless your ORB-SLAM3 build is older than late 2022.

---

## Step 5 — Prepare the dataset

> **ROS prerequisite**: the bag extraction steps below require a ROS installation (ROS Noetic
> for Ubuntu 20.04 or ROS 2 with rosbag compatibility layer for Ubuntu 22.04). If you do not
> have ROS, your instructor may provide pre-extracted images and ground truth directly — skip
> to step 5c (timestamp verification) in that case.

### 5a. Extract images from the ROS bag

```bash
source /opt/ros/noetic/setup.bash   # adjust for your ROS distribution
python3 extract_images_final.py HKisland_GNSS03.bag \
    --output ~/workspace/dataset/extracted_data
```

The result should be a folder with sequentially named images and a `timestamps.txt`.

### 5b. Extract RTK ground truth

```bash
python3 extract_rtk_groundtruth.py HKisland_GNSS03.bag \
    --output ~/workspace/dataset/ground_truth.txt
```

### 5c. Sanity-check timestamps

```bash
head -5 ~/workspace/dataset/ground_truth.txt
# Expected: floating-point seconds, 8 columns (t tx ty tz qx qy qz qw)
```

---

## Step 6 — Run ORB-SLAM3 (monocular VO)

```bash
cd ~/workspace/ORB_SLAM3

./Examples/Monocular/mono_tum \
    Vocabulary/ORBvoc.txt \
    Examples/Monocular/HKisland_Mono.yaml \
    ~/workspace/dataset/extracted_data
```

After the run completes, two trajectory files are saved in the current directory:

| File | Lines | Use for evaluation? |
|------|-------|---------------------|
| `CameraTrajectory.txt` | ~thousands | ✅ **Yes — use this** |
| `KeyFrameTrajectory.txt` | ~hundreds | ❌ No (biases metrics) |

---

## Step 7 — Evaluate the trajectory

```bash
cd ~/workspace/AAE5303_assignment2_orbslam3
source .venv/bin/activate

python3 scripts/evaluate_vo_accuracy.py \
    --groundtruth ~/workspace/dataset/ground_truth.txt \
    --estimated   ~/workspace/ORB_SLAM3/CameraTrajectory.txt \
    --t-max-diff  0.1 \
    --delta-m     10 \
    --workdir     evaluation_results \
    --json-out    evaluation_results/metrics.json
```

The script prints ATE RMSE, RPE drift rates, and Completeness to stdout, and optionally
saves a JSON file for leaderboard submission.

---

## Step 8 — (Optional) Generate trajectory figures

```bash
python3 scripts/generate_report_figures.py \
    --gt          ~/workspace/dataset/ground_truth.txt \
    --est         ~/workspace/ORB_SLAM3/CameraTrajectory.txt \
    --evo-ape-zip evaluation_results/ate.zip \
    --out         figures/trajectory_evaluation.png \
    --title-suffix "HKisland_GNSS03"
```

---

## Common errors and fixes

| Error | Likely cause | Fix |
|-------|--------------|-----|
| `mono_tum: No such file` | ORB-SLAM3 not compiled | Re-run `build.sh` |
| `ORBvoc.txt not found` | Vocabulary not decompressed | `cd Vocabulary && tar -xvf ORBvoc.txt.tar.gz` |
| `yaml read error` / wrong key names | Wrong yaml format | Use `HKisland_Mono_v1.yaml` (Camera1.fx style) |
| `Found no matching timestamps` | Timestamps not in seconds, or wrong dataset pair | Check `ground_truth.txt` — must be float seconds |
| Completeness very low | Using `KeyFrameTrajectory.txt` | Switch to `CameraTrajectory.txt` |
| `Fail to track local map!` frequently | ORB parameters need tuning | See [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) |

---

## Next steps

For parameter tuning and optimization experiments, see:

- [`OPTIMIZATION_GUIDE.md`](OPTIMIZATION_GUIDE.md) — structured tuning workflow
- [`optimization_presets/`](optimization_presets/) — ready-to-use parameter presets
