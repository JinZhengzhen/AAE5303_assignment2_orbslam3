# 学生作业指南 | Student Assignment Guide

> **课程**: AAE5303 - 低空飞行器鲁棒控制技术
> **作业**: Visual Odometry with ORB-SLAM3
> **任务**: 在UAV航拍数据集上实现单目视觉里程计并提交评估结果

---

## 📋 目录 | Table of Contents

1. [作业概述](#-作业概述--assignment-overview)
2. [完成步骤](#-完成步骤--step-by-step-guide)
3. [环境准备](#-环境准备--environment-setup)
4. [数据准备](#-数据准备--data-preparation)
5. [运行ORB-SLAM3](#-运行orb-slam3)
6. [轨迹评估](#-轨迹评估--trajectory-evaluation)
7. [生成提交文件](#-生成提交文件--generate-submission)
8. [常见问题](#-常见问题--faq)
9. [改进建议](#-改进建议--improvement-tips)

---

## 📖 作业概述 | Assignment Overview

### 任务目标

本作业要求你：

1. ✅ 使用 **ORB-SLAM3** 实现单目视觉里程计（Monocular Visual Odometry）
2. ✅ 在 **HKisland_GNSS03** 或 **AMtown02** 数据集上运行算法
3. ✅ 提取RTK GPS数据作为Ground Truth
4. ✅ 使用 `evo` 工具评估轨迹精度
5. ✅ 生成 `{GroupName}_leaderboard.json` 提交文件

### 评估指标

排行榜使用**四个平行指标**（无加权）评估你的结果：

| 指标 | 方向 | 单位 | 说明 |
|------|------|------|------|
| **ATE RMSE** | ↓ 越低越好 | m | 全局精度（Sim(3)对齐+尺度校正） |
| **RPE Trans Drift** | ↓ 越低越好 | m/m | 平移漂移率（基于距离，delta=10m） |
| **RPE Rot Drift** | ↓ 越低越好 | deg/100m | 旋转漂移率（基于距离，delta=10m） |
| **Completeness** | ↑ 越高越好 | % | 完整度（匹配的位姿数/总GT位姿数） |

### 基线性能（AMtown02数据集）

| 指标 | 基线值 |
|------|--------|
| ATE RMSE | 88.23 m |
| RPE Trans Drift | 2.04 m/m |
| RPE Rot Drift | 76.70 deg/100m |
| Completeness | 95.73% |

**目标**：你的提交应该尽量接近或超越这些基线值。

---

## 🚀 完成步骤 | Step-by-Step Guide

### 快速检查清单

- [ ] 安装ORB-SLAM3和所有依赖项
- [ ] 准备数据集（图像序列 + RTK ground truth）
- [ ] 配置相机参数文件
- [ ] 运行ORB-SLAM3生成 `CameraTrajectory.txt`
- [ ] 使用评估脚本计算指标
- [ ] 生成 `{GroupName}_leaderboard.json`
- [ ] 提交到排行榜

---

## 🔧 环境准备 | Environment Setup

### 1. 安装ORB-SLAM3

```bash
# 克隆ORB-SLAM3仓库
git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git
cd ORB_SLAM3

# 安装依赖项（Ubuntu 22.04示例）
sudo apt update
sudo apt install -y build-essential cmake git \
    libeigen3-dev libopencv-dev libpangolin-dev \
    libboost-all-dev libssl-dev

# 编译ORB-SLAM3
chmod +x build.sh
./build.sh

# 验证安装
ls Examples/Monocular/mono_tum  # 应该存在
```

**重要提示**：
- ORB-SLAM3需要**OpenCV 4.x**和**Pangolin**可视化库
- 确保下载 `ORBvoc.txt` 词汇表文件（~80MB）
- 编译时间约5-10分钟

### 2. 安装Python评估工具

```bash
# 安装evo轨迹评估工具
pip install evo

# 安装其他Python依赖
pip install numpy matplotlib

# 验证安装
evo_ape --help
evo_rpe --help
```

---

## 📁 数据准备 | Data Preparation

### 方式1：使用ROS bag文件

如果你有 `.bag` 文件：

```bash
# 1. 提取图像序列
python3 extract_images_final.py HKisland_GNSS03.bag \
    --output extracted_data

# 2. 提取RTK Ground Truth
python3 extract_rtk_groundtruth.py HKisland_GNSS03.bag \
    --output ground_truth.txt

# 验证输出
ls extracted_data/  # 应该有 timestamps.txt 和 rgb/*.png
head ground_truth.txt  # 应该是TUM格式: t tx ty tz qx qy qz qw
```

### 方式2：直接使用图像文件夹

如果已经有提取好的图像：

```bash
# 目录结构应该是：
# extracted_data/
# ├── rgb/
# │   ├── 0000000.png
# │   ├── 0000001.png
# │   └── ...
# └── timestamps.txt

# timestamps.txt格式（TUM）：
# timestamp image_filename
# 1698132964.499888 rgb/0000000.png
# 1698132964.599976 rgb/0000001.png
```

### 关键数据格式说明

#### TUM轨迹格式
```
# timestamp tx ty tz qx qy qz qw
1698132964.499888 0.0000000 0.0000000 0.0000000 0.0 0.0 0.0 1.0
1698132964.599976 -0.0198950 0.0163751 -0.0965251 -0.0048 0.0122 0.0013 0.9999
```

**注意事项**：
- ✅ 时间戳必须是**秒**（浮点数）
- ✅ 四元数格式：`qx qy qz qw`（注意顺序）
- ❌ 不要使用帧索引作为时间戳
- ❌ 不要使用毫秒或纳秒

---

## 🎬 运行ORB-SLAM3

### 1. 准备相机配置文件

查看 `docs/camera_config.yaml` 获取相机参数参考。

创建或使用ORB-SLAM3格式的配置文件 `DJI_Camera.yaml`：

```yaml
%YAML:1.0

# Camera calibration and distortion parameters (OpenCV)
Camera.type: "PinHole"
Camera1.fx: 1444.43
Camera1.fy: 1444.34
Camera1.cx: 1179.50
Camera1.cy: 1044.90

Camera1.k1: -0.0560
Camera1.k2: 0.1180
Camera1.p1: 0.00122
Camera1.p2: 0.00064
Camera1.k3: -0.0627

Camera.width: 2448
Camera.height: 2048
Camera.fps: 10.0
Camera.RGB: 0  # 0 for BGR, 1 for RGB

# ORB feature extraction parameters
ORBextractor.nFeatures: 1500
ORBextractor.scaleFactor: 1.2
ORBextractor.nLevels: 8
ORBextractor.iniThFAST: 20
ORBextractor.minThFAST: 7

# Viewer parameters (optional)
Viewer.KeyFrameSize: 0.05
Viewer.KeyFrameLineWidth: 1.0
Viewer.GraphLineWidth: 0.9
Viewer.PointSize: 2.0
Viewer.CameraSize: 0.08
Viewer.CameraLineWidth: 3.0
Viewer.ViewpointX: 0.0
Viewer.ViewpointY: -0.7
Viewer.ViewpointZ: -1.8
Viewer.ViewpointF: 500.0
```

### 2. 运行单目VO

```bash
cd ORB_SLAM3

# 运行单目视觉里程计
./Examples/Monocular/mono_tum \
    Vocabulary/ORBvoc.txt \
    Examples/Monocular/DJI_Camera.yaml \
    /path/to/extracted_data

# 等待处理完成（可能需要几分钟）
# ORB-SLAM3会在窗口中显示实时追踪结果
```

### 3. 检查输出文件

运行完成后，ORB-SLAM3会在**当前目录**生成：

```bash
# 检查输出文件
ls -lh CameraTrajectory.txt
ls -lh KeyFrameTrajectory.txt

# CameraTrajectory.txt - 所有追踪帧的轨迹（使用这个！）
# KeyFrameTrajectory.txt - 仅关键帧轨迹（不要用于评估！）
```

**重要**：
- ✅ 使用 `CameraTrajectory.txt` 进行评估
- ❌ 不要使用 `KeyFrameTrajectory.txt`（会降低完整度）

### 4. 验证轨迹文件

```bash
# 检查轨迹格式
head CameraTrajectory.txt

# 应该是TUM格式，8列数据
# 时间戳应该是秒（浮点数），不是帧索引

# 统计位姿数量
wc -l CameraTrajectory.txt
```

---

## 📊 轨迹评估 | Trajectory Evaluation

### 方式1：使用提供的评估脚本（推荐）

```bash
# 在本仓库根目录运行
python scripts/evaluate_vo_accuracy.py \
    --groundtruth ground_truth.txt \
    --estimated CameraTrajectory.txt \
    --t-max-diff 0.1 \
    --delta-m 10 \
    --workdir evaluation_results \
    --json-out evaluation_results/metrics.json
```

**输出示例**：
```
================================================================================
PARALLEL METRICS (NO WEIGHTING)
================================================================================
ATE RMSE (m):                 132.154700
RPE trans drift (m/m):        2.870140
RPE rot drift (deg/100m):     173.331900
Completeness (%):             87.01  (1701 / 1955)
```

### 方式2：使用原生evo命令

```bash
# 1. ATE评估（Sim(3)对齐+尺度校正）
evo_ape tum ground_truth.txt CameraTrajectory.txt \
  --align --correct_scale \
  --t_max_diff 0.1 -va

# 2. RPE平移评估（基于距离，delta=10m）
evo_rpe tum ground_truth.txt CameraTrajectory.txt \
  --align --correct_scale \
  --t_max_diff 0.1 \
  --delta 10 --delta_unit m \
  --pose_relation trans_part -va

# 3. RPE旋转评估（基于距离，delta=10m）
evo_rpe tum ground_truth.txt CameraTrajectory.txt \
  --align --correct_scale \
  --t_max_diff 0.1 \
  --delta 10 --delta_unit m \
  --pose_relation angle_deg -va
```

### 理解评估参数

| 参数 | 值 | 说明 |
|------|----|----|
| `--align` | - | 应用Sim(3)对齐（旋转+平移+尺度） |
| `--correct_scale` | - | 校正单目尺度模糊性 |
| `--t_max_diff` | 0.1 | 时间戳关联容差（秒） |
| `--delta` | 10 | RPE距离间隔（米） |
| `--delta_unit` | m | 距离单位（米） |

### 计算漂移率

evo输出的是**区间内的平均误差**，需要转换为**漂移率**：

```python
# RPE平移漂移率 (m/m)
rpe_trans_drift = rpe_trans_mean_m / 10.0

# RPE旋转漂移率 (deg/100m)
rpe_rot_drift = (rpe_rot_mean_deg / 10.0) * 100.0
```

---

## 📤 生成提交文件 | Generate Submission

### 使用提供的辅助脚本

本仓库提供了一个辅助脚本来生成排行榜提交文件：

```bash
# 生成提交JSON文件
python scripts/create_leaderboard_submission.py \
    --metrics evaluation_results/metrics.json \
    --group-name "Team Alpha" \
    --repo-url "https://github.com/yourusername/project.git" \
    --output Team_Alpha_leaderboard.json
```

### 手动创建提交文件

如果你想手动创建，使用以下模板：

```json
{
  "group_name": "Team Alpha",
  "project_private_repo_url": "https://github.com/yourusername/project.git",
  "metrics": {
    "ate_rmse_m": 88.2281,
    "rpe_trans_drift_m_per_m": 2.04084,
    "rpe_rot_drift_deg_per_100m": 76.69911,
    "completeness_pct": 95.73
  }
}
```

### 验证提交文件

```bash
# 验证JSON格式
python -c "import json; json.load(open('Team_Alpha_leaderboard.json'))"

# 或使用提供的验证脚本
python scripts/validate_submission.py Team_Alpha_leaderboard.json
```

### 提交要求

✅ **必填字段**：
- `group_name`：你的组名（显示在排行榜上）
- `project_private_repo_url`：你的私有Git仓库URL（必须以`.git`结尾）
- `metrics`：包含四个指标的字典

✅ **文件命名**：`{GroupName}_leaderboard.json`

✅ **提交方式**：根据课程要求提交到指定平台

---

## ❓ 常见问题 | FAQ

### Q1: evo报错 "Found no matching timestamps"

**原因**：
- 时间戳格式不正确（不是秒）
- Ground truth文件不匹配
- `t_max_diff`太小

**解决方案**：
```bash
# 检查时间戳范围
head -1 ground_truth.txt
head -1 CameraTrajectory.txt

# 时间戳应该相近且都是秒（例如 1698132964.499）
# 如果相差很大，说明使用了错误的文件

# 增大t_max_diff试试
--t_max_diff 0.2
```

### Q2: Completeness很低（<50%）

**原因**：
- 追踪失败频繁
- ORB特征数太少
- 相机参数不准确

**解决方案**：
```yaml
# 增加特征点数量
ORBextractor.nFeatures: 2000  # 原来1500

# 降低FAST阈值
ORBextractor.iniThFAST: 15  # 原来20
ORBextractor.minThFAST: 5   # 原来7
```

### Q3: ATE RMSE很大（>200m）

**原因**：
- 相机内参不准确
- RGB/BGR设置错误
- 追踪质量差

**解决方案**：
1. 验证相机内参（fx, fy, cx, cy）
2. 检查RGB设置（OpenCV图像通常是BGR）
3. 查看ORB-SLAM3运行日志，是否有大量"Fail to track"

### Q4: 应该用CameraTrajectory还是KeyFrameTrajectory？

**答案**：**必须使用CameraTrajectory.txt**

原因：
- `CameraTrajectory.txt` 包含所有追踪帧 → 高完整度
- `KeyFrameTrajectory.txt` 只有关键帧 → 低完整度，扭曲漂移率

### Q5: 如何提高性能？

参考下方的[改进建议](#-改进建议--improvement-tips)部分。

---

## 💡 改进建议 | Improvement Tips

### 优先级：高 🔴

#### 1. 增加ORB特征数量
```yaml
ORBextractor.nFeatures: 2000  # 或更高
```
**预期改进**：ATE减少30-40%

#### 2. 降低FAST阈值
```yaml
ORBextractor.iniThFAST: 15
ORBextractor.minThFAST: 5
```
**预期改进**：RPE减少20-30%

#### 3. 验证相机标定
- 使用Kalibr或OpenCV重新标定相机
- 确保内参和畸变参数准确
**预期改进**：整体提升15-25%

### 优先级：中 🟡

#### 4. 调整尺度因子
```yaml
ORBextractor.scaleFactor: 1.15  # 原来1.2
ORBextractor.nLevels: 10        # 原来8
```

#### 5. 优化图像质量
- 减少运动模糊（使用更高快门速度）
- 改善光照条件
- 提高图像分辨率

### 优先级：低 🟢（如果允许）

#### 6. 使用IMU融合（VIO模式）
如果数据集包含IMU数据且课程允许：
```bash
./Examples/Monocular-Inertial/mono_inertial_tum ...
```
**预期改进**：精度提升50-70%

#### 7. 启用回环检测
ORB-SLAM3的SLAM模式（非纯VO）包含回环检测，可以减少累积漂移。

---

## 📚 参考资料 | References

### 官方文档
- [ORB-SLAM3 GitHub](https://github.com/UZ-SLAMLab/ORB_SLAM3)
- [evo评估工具](https://github.com/MichaelGrupp/evo)
- [MARS-LVIG数据集](https://mars.hku.hk/dataset.html)

### 论文
1. Campos et al., "ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM", IEEE TRO 2021
2. Sturm et al., "A Benchmark for the Evaluation of RGB-D SLAM Systems", IROS 2012

### 本仓库文档
- `README.md` - 完整的作业报告示例
- `leaderboard/README.md` - 排行榜说明
- `leaderboard/LEADERBOARD_SUBMISSION_GUIDE.md` - 提交指南
- `docs/camera_config.yaml` - 相机参数参考

---

## 🎯 检查清单 | Final Checklist

在提交之前，请确认：

- [ ] ✅ ORB-SLAM3成功运行并生成`CameraTrajectory.txt`
- [ ] ✅ 轨迹文件是有效的TUM格式（8列）
- [ ] ✅ 时间戳是秒（不是帧索引）
- [ ] ✅ 使用评估脚本成功计算了四个指标
- [ ] ✅ Completeness > 80%（如果太低，说明追踪有问题）
- [ ] ✅ 生成的JSON文件格式正确
- [ ] ✅ 文件命名符合要求：`{GroupName}_leaderboard.json`
- [ ] ✅ JSON包含正确的组名和仓库URL

---

## 🆘 获取帮助

如果遇到问题：

1. 📖 查看 `README.md` 中的详细说明
2. 📖 查看 `leaderboard/LEADERBOARD_SUBMISSION_GUIDE.md`
3. 🔍 检查ORB-SLAM3的运行日志
4. 💬 在课程论坛提问
5. 📧 联系助教

---

## 📊 排行榜

**实时排名**：https://qian9921.github.io/leaderboard_web/

**基线性能（AMtown02）**：
- ATE RMSE: 88.23 m
- RPE Trans Drift: 2.04 m/m
- RPE Rot Drift: 76.70 deg/100m
- Completeness: 95.73%

**祝你取得好成绩！Good luck!** 🚀
