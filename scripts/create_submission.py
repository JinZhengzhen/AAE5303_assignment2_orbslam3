#!/usr/bin/env python3
"""
AAE5303 – Leaderboard Submission Generator

Reads metrics from a JSON file produced by ``scripts/evaluate_vo_accuracy.py``
and writes a correctly-formatted leaderboard submission JSON.

Usage
-----
    python3 scripts/create_submission.py \
        --metrics evaluation_results/metrics.json \
        --group-name "Team Alpha" \
        --repo-url "https://github.com/yourusername/project.git" \
        --out Team_Alpha_leaderboard.json

The output file follows the schema defined in ``leaderboard/submission_template.json``.
Run ``--validate-only`` to check an existing submission without regenerating it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Required top-level fields and their types
_REQUIRED_TOP_LEVEL: dict[str, type] = {
    "group_name": str,
    "project_private_repo_url": str,
    "metrics": dict,
}

# Required metric keys and their types
_REQUIRED_METRICS: dict[str, tuple[type, ...]] = {
    "ate_rmse_m": (int, float),
    "rpe_trans_drift_m_per_m": (int, float),
    "rpe_rot_drift_deg_per_100m": (int, float),
    "completeness_pct": (int, float),
}


def validate_submission(submission: dict) -> list[str]:
    """
    Validate a leaderboard submission dict.

    Returns a (possibly empty) list of error strings.
    """
    errors: list[str] = []

    for field, ftype in _REQUIRED_TOP_LEVEL.items():
        if field not in submission:
            errors.append(f"Missing required field: '{field}'")
        elif not isinstance(submission[field], ftype):
            errors.append(
                f"Field '{field}' must be {ftype.__name__}, "
                f"got {type(submission[field]).__name__}"
            )

    if errors:
        return errors  # cannot check metrics if top-level fields are wrong

    url: str = submission["project_private_repo_url"]
    if not url.startswith("https://github.com/"):
        errors.append(
            f"'project_private_repo_url' must start with 'https://github.com/', got: {url!r}"
        )
    if not url.endswith(".git"):
        errors.append(
            f"'project_private_repo_url' must end with '.git', got: {url!r}"
        )

    metrics: dict = submission["metrics"]
    for key, valid_types in _REQUIRED_METRICS.items():
        if key not in metrics:
            errors.append(f"Missing required metrics key: 'metrics.{key}'")
        elif not isinstance(metrics[key], valid_types):
            errors.append(
                f"'metrics.{key}' must be a number, "
                f"got {type(metrics[key]).__name__}"
            )

    return errors


def build_submission(
    metrics_path: str,
    group_name: str,
    repo_url: str,
) -> dict:
    """
    Build a leaderboard submission dict from an evaluate_vo_accuracy.py JSON output.

    Parameters
    ----------
    metrics_path:
        Path to the JSON file written by ``evaluate_vo_accuracy.py --json-out``.
    group_name:
        Team / group name to appear on the leaderboard.
    repo_url:
        Private GitHub repository URL (must start with https://github.com/ and
        end with .git).

    Returns
    -------
    dict
        Submission dict ready to be JSON-serialised.
    """
    raw = json.loads(Path(metrics_path).read_text(encoding="utf-8"))

    required_keys = list(_REQUIRED_METRICS.keys())
    missing = [k for k in required_keys if k not in raw]
    if missing:
        raise ValueError(
            f"The metrics file is missing expected keys: {missing}. "
            f"Re-run evaluate_vo_accuracy.py with --json-out to regenerate it."
        )

    return {
        "group_name": group_name,
        "project_private_repo_url": repo_url,
        "metrics": {
            "ate_rmse_m": float(raw["ate_rmse_m"]),
            "rpe_trans_drift_m_per_m": float(raw["rpe_trans_drift_m_per_m"]),
            "rpe_rot_drift_deg_per_100m": float(raw["rpe_rot_drift_deg_per_100m"]),
            "completeness_pct": float(raw["completeness_pct"]),
        },
    }


def _print_validation_result(submission: dict, errors: list[str]) -> int:
    """Print validation outcome and return exit code (0 = valid, 1 = invalid)."""
    if errors:
        print("❌ Submission is INVALID:")
        for err in errors:
            print(f"   • {err}")
        return 1
    m = submission["metrics"]
    print("✅ Submission format is valid!")
    print(f"   Group:                   {submission['group_name']}")
    print(f"   Repo:                    {submission['project_private_repo_url']}")
    print(f"   ATE RMSE:                {m['ate_rmse_m']} m")
    print(f"   RPE trans drift:         {m['rpe_trans_drift_m_per_m']} m/m")
    print(f"   RPE rot drift:           {m['rpe_rot_drift_deg_per_100m']} deg/100m")
    print(f"   Completeness:            {m['completeness_pct']} %")
    return 0


def _cmd_generate(metrics: str, group_name: str, repo_url: str, out: str) -> int:
    """Build, validate, and write a leaderboard submission JSON."""
    try:
        submission = build_submission(metrics, group_name, repo_url)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    errors = validate_submission(submission)
    if errors:
        print("ERROR: Built submission failed validation:")
        for err in errors:
            print(f"   • {err}")
        return 1
    out_path = Path(out)
    out_path.write_text(json.dumps(submission, indent=2), encoding="utf-8")
    m = submission["metrics"]
    print(f"✅ Saved submission to: {out_path}")
    print(f"   Group:           {submission['group_name']}")
    print(f"   ATE RMSE:        {m['ate_rmse_m']:.4f} m")
    print(f"   RPE trans drift: {m['rpe_trans_drift_m_per_m']:.5f} m/m")
    print(f"   RPE rot drift:   {m['rpe_rot_drift_deg_per_100m']:.5f} deg/100m")
    print(f"   Completeness:    {m['completeness_pct']:.2f} %")
    return 0


def _cmd_validate(submission_path: str) -> int:
    """Load and validate an existing leaderboard submission JSON."""
    try:
        submission = json.loads(Path(submission_path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR reading submission file: {exc}")
        return 1
    return _print_validation_result(submission, validate_submission(submission))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or validate an AAE5303 leaderboard submission JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- generate sub-command ---
    gen = subparsers.add_parser(
        "generate",
        help="Generate a leaderboard submission JSON from evaluate_vo_accuracy.py output.",
    )
    gen.add_argument(
        "--metrics",
        required=True,
        metavar="PATH",
        help="Path to metrics JSON produced by evaluate_vo_accuracy.py --json-out.",
    )
    gen.add_argument(
        "--group-name",
        required=True,
        help="Team / group name to appear on the leaderboard.",
    )
    gen.add_argument(
        "--repo-url",
        required=True,
        help=(
            "Private GitHub repository URL, e.g. "
            "'https://github.com/yourusername/project.git'."
        ),
    )
    gen.add_argument(
        "--out",
        required=True,
        metavar="PATH",
        help="Output path for the submission JSON (e.g. Team_Alpha_leaderboard.json).",
    )

    # --- validate sub-command ---
    val = subparsers.add_parser(
        "validate",
        help="Validate an existing leaderboard submission JSON.",
    )
    val.add_argument(
        "submission",
        metavar="PATH",
        help="Path to the submission JSON to validate.",
    )

    # Fallback flat-arg interface for backward compatibility with the README examples.
    parser.add_argument("--metrics", metavar="PATH", help=argparse.SUPPRESS)
    parser.add_argument("--group-name", help=argparse.SUPPRESS)
    parser.add_argument("--repo-url", help=argparse.SUPPRESS)
    parser.add_argument("--out", metavar="PATH", help=argparse.SUPPRESS)
    parser.add_argument("--validate-only", metavar="PATH", help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.command == "generate":
        return _cmd_generate(args.metrics, args.group_name, args.repo_url, args.out)

    if args.command == "validate":
        return _cmd_validate(args.submission)

    # Flat interface (no subcommand)
    if args.validate_only:
        return _cmd_validate(args.validate_only)

    if args.metrics and args.group_name and args.repo_url and args.out:
        return _cmd_generate(args.metrics, args.group_name, args.repo_url, args.out)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
