#!/usr/bin/env python3
"""
Validate leaderboard submission JSON file.

Usage:
    python3 validate_submission.py Team_Alpha_leaderboard.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def validate_submission(submission_path: str) -> Tuple[bool, List[str]]:
    """
    Validate leaderboard submission JSON file.

    Args:
        submission_path: Path to submission JSON file

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check file exists
    if not Path(submission_path).exists():
        errors.append(f"File not found: {submission_path}")
        return False, errors

    # Load JSON
    try:
        with open(submission_path, "r", encoding="utf-8") as f:
            submission = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON format: {e}")
        return False, errors

    # Check required top-level fields
    required_fields = ["group_name", "project_private_repo_url", "metrics"]
    for field in required_fields:
        if field not in submission:
            errors.append(f"Missing required field: '{field}'")

    # Validate group_name
    if "group_name" in submission:
        if not isinstance(submission["group_name"], str):
            errors.append("'group_name' must be a string")
        elif not submission["group_name"].strip():
            errors.append("'group_name' cannot be empty")

    # Validate project_private_repo_url
    if "project_private_repo_url" in submission:
        url = submission["project_private_repo_url"]
        if not isinstance(url, str):
            errors.append("'project_private_repo_url' must be a string")
        else:
            if not url.startswith("https://github.com/"):
                errors.append("'project_private_repo_url' must start with 'https://github.com/'")
            if not url.endswith(".git"):
                errors.append("'project_private_repo_url' must end with '.git'")

    # Validate metrics
    if "metrics" not in submission:
        errors.append("Missing 'metrics' field")
    else:
        metrics = submission["metrics"]
        if not isinstance(metrics, dict):
            errors.append("'metrics' must be an object/dictionary")
        else:
            # Check required metric fields
            required_metrics = [
                "ate_rmse_m",
                "rpe_trans_drift_m_per_m",
                "rpe_rot_drift_deg_per_100m",
                "completeness_pct",
            ]

            for metric in required_metrics:
                if metric not in metrics:
                    errors.append(f"Missing required metric: 'metrics.{metric}'")
                else:
                    value = metrics[metric]
                    if not isinstance(value, (int, float)):
                        errors.append(f"'metrics.{metric}' must be a number, got {type(value).__name__}")
                    elif value < 0:
                        errors.append(f"'metrics.{metric}' cannot be negative: {value}")

            # Validate value ranges
            if "ate_rmse_m" in metrics:
                if metrics["ate_rmse_m"] > 10000:
                    errors.append(
                        f"'metrics.ate_rmse_m' seems unreasonably large: {metrics['ate_rmse_m']} m"
                    )

            if "rpe_trans_drift_m_per_m" in metrics:
                if metrics["rpe_trans_drift_m_per_m"] > 100:
                    errors.append(
                        f"'metrics.rpe_trans_drift_m_per_m' seems unreasonably large: "
                        f"{metrics['rpe_trans_drift_m_per_m']} m/m"
                    )

            if "rpe_rot_drift_deg_per_100m" in metrics:
                if metrics["rpe_rot_drift_deg_per_100m"] > 10000:
                    errors.append(
                        f"'metrics.rpe_rot_drift_deg_per_100m' seems unreasonably large: "
                        f"{metrics['rpe_rot_drift_deg_per_100m']} deg/100m"
                    )

            if "completeness_pct" in metrics:
                if not (0 <= metrics["completeness_pct"] <= 100):
                    errors.append(
                        f"'metrics.completeness_pct' must be between 0 and 100, got: "
                        f"{metrics['completeness_pct']}"
                    )

    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate leaderboard submission JSON file."
    )
    parser.add_argument(
        "submission",
        help="Path to submission JSON file (e.g., Team_Alpha_leaderboard.json)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed metrics even if valid",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("VALIDATING LEADERBOARD SUBMISSION")
    print("=" * 80)
    print(f"File: {args.submission}")
    print("")

    is_valid, errors = validate_submission(args.submission)

    if is_valid:
        print("✅ Submission is VALID!")
        print("")

        # Load and display metrics
        with open(args.submission, "r", encoding="utf-8") as f:
            submission = json.load(f)

        print(f"Group Name: {submission['group_name']}")
        print(f"Repository: {submission['project_private_repo_url']}")
        print("")
        print("Metrics:")
        metrics = submission["metrics"]
        print(f"  ATE RMSE:              {metrics['ate_rmse_m']:.4f} m")
        print(f"  RPE Trans Drift:       {metrics['rpe_trans_drift_m_per_m']:.6f} m/m")
        print(f"  RPE Rot Drift:         {metrics['rpe_rot_drift_deg_per_100m']:.5f} deg/100m")
        print(f"  Completeness:          {metrics['completeness_pct']:.2f}%")
        print("")
        print("Next steps:")
        print("  1. Submit this file according to course instructions")
        print("  2. View rankings at: https://qian9921.github.io/leaderboard_web/")
        print("=" * 80)
        return 0
    else:
        print("❌ Submission is INVALID!")
        print("")
        print("Errors found:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print("")
        print("Please fix these errors before submitting.")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
