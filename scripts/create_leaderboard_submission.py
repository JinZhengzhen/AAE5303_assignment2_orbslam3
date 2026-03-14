#!/usr/bin/env python3
"""
Create leaderboard submission JSON from evaluation metrics.

Usage:
    python3 create_leaderboard_submission.py \
        --metrics evaluation_results/metrics.json \
        --group-name "Team Alpha" \
        --repo-url "https://github.com/yourusername/project.git" \
        --output Team_Alpha_leaderboard.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict


def validate_repo_url(url: str) -> bool:
    """Validate GitHub repository URL."""
    if not url.startswith("https://github.com/"):
        return False
    if not url.endswith(".git"):
        return False
    return True


def create_submission(
    metrics_path: str,
    group_name: str,
    repo_url: str,
    output_path: str,
) -> None:
    """
    Create leaderboard submission JSON from evaluation metrics.

    Args:
        metrics_path: Path to evaluation metrics JSON file
        group_name: Team/group name
        repo_url: GitHub repository URL (must end with .git)
        output_path: Output path for submission JSON
    """
    # Validate inputs
    if not Path(metrics_path).exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    if not validate_repo_url(repo_url):
        raise ValueError(
            f"Invalid repository URL: {repo_url}\n"
            "URL must start with 'https://github.com/' and end with '.git'"
        )

    # Load metrics
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # Extract required metrics
    required_keys = [
        "ate_rmse_m",
        "rpe_trans_drift_m_per_m",
        "rpe_rot_drift_deg_per_100m",
        "completeness_pct",
    ]

    for key in required_keys:
        if key not in metrics:
            raise ValueError(f"Missing required metric: {key}")

    # Create submission
    submission = {
        "group_name": group_name,
        "project_private_repo_url": repo_url,
        "metrics": {
            "ate_rmse_m": float(metrics["ate_rmse_m"]),
            "rpe_trans_drift_m_per_m": float(metrics["rpe_trans_drift_m_per_m"]),
            "rpe_rot_drift_deg_per_100m": float(metrics["rpe_rot_drift_deg_per_100m"]),
            "completeness_pct": float(metrics["completeness_pct"]),
        },
    }

    # Write submission
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print("LEADERBOARD SUBMISSION CREATED")
    print("=" * 80)
    print(f"Group Name: {group_name}")
    print(f"Repository: {repo_url}")
    print("")
    print("Metrics:")
    print(f"  ATE RMSE:              {submission['metrics']['ate_rmse_m']:.4f} m")
    print(f"  RPE Trans Drift:       {submission['metrics']['rpe_trans_drift_m_per_m']:.6f} m/m")
    print(f"  RPE Rot Drift:         {submission['metrics']['rpe_rot_drift_deg_per_100m']:.5f} deg/100m")
    print(f"  Completeness:          {submission['metrics']['completeness_pct']:.2f}%")
    print("")
    print(f"✅ Submission saved to: {output_path}")
    print("")
    print("Next steps:")
    print("  1. Verify the JSON file format")
    print("  2. Submit to the leaderboard according to course instructions")
    print(f"  3. View rankings at: https://qian9921.github.io/leaderboard_web/")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Create leaderboard submission JSON from evaluation metrics."
    )
    parser.add_argument(
        "--metrics",
        required=True,
        help="Path to evaluation metrics JSON file (from evaluate_vo_accuracy.py)",
    )
    parser.add_argument(
        "--group-name",
        required=True,
        help="Team/group name (as shown on leaderboard)",
    )
    parser.add_argument(
        "--repo-url",
        required=True,
        help="GitHub repository URL (must start with https://github.com/ and end with .git)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for submission JSON file (e.g., Team_Alpha_leaderboard.json)",
    )

    args = parser.parse_args()

    try:
        create_submission(
            metrics_path=args.metrics,
            group_name=args.group_name,
            repo_url=args.repo_url,
            output_path=args.output,
        )
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
