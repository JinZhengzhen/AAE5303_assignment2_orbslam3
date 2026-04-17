#!/usr/bin/env python3
"""
Download MARS-LVIG Dataset for AAE5303 Assignment

This script helps download the MARS-LVIG UAV dataset used in the assignment.
The dataset includes:
- AMtown02 sequence (used for leaderboard evaluation)
- HKisland_GNSS03 sequence (demo example)

Dataset source: https://mars.hku.hk/dataset.html
GitHub: https://github.com/sijieaaa/UAVScenes

Usage:
    python3 scripts/download_dataset.py --sequence AMtown02 --output data/
    python3 scripts/download_dataset.py --sequence HKisland_GNSS03 --output data/
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict


# Dataset information
DATASETS = {
    "AMtown02": {
        "description": "AMtown02 sequence (used for leaderboard evaluation)",
        "rosbag_url": "https://zenodo.org/record/8160110/files/AMtown02.bag",
        "size": "~12.3 GB",
        "duration": "~450 seconds",
        "images": "~4,500 frames",
    },
    "HKisland_GNSS03": {
        "description": "HKisland GNSS03 sequence (demo example from README)",
        "rosbag_url": "https://zenodo.org/record/8160110/files/HKisland_GNSS03.bag",
        "size": "~9.8 GB",
        "duration": "~390 seconds",
        "images": "~3,833 frames",
    },
}


def print_header(text: str):
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80 + "\n")


def download_with_wget(url: str, output_path: str) -> bool:
    """Download file using wget with progress bar."""
    try:
        cmd = ["wget", "--continue", "--progress=bar:force", "-O", output_path, url]
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print("ERROR: wget not found. Please install wget:")
        print("  Ubuntu/Debian: sudo apt install wget")
        print("  macOS: brew install wget")
        return False


def download_with_curl(url: str, output_path: str) -> bool:
    """Download file using curl with progress bar."""
    try:
        cmd = ["curl", "-L", "-C", "-", "-o", output_path, url]
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print("ERROR: curl not found. Please install curl:")
        print("  Ubuntu/Debian: sudo apt install curl")
        print("  macOS: curl is pre-installed")
        return False


def download_dataset(sequence: str, output_dir: str) -> bool:
    """
    Download MARS-LVIG dataset sequence.

    Args:
        sequence: Dataset sequence name (AMtown02 or HKisland_GNSS03)
        output_dir: Output directory for downloaded files

    Returns:
        True if download successful, False otherwise
    """
    if sequence not in DATASETS:
        print(f"ERROR: Unknown sequence '{sequence}'")
        print(f"Available sequences: {', '.join(DATASETS.keys())}")
        return False

    dataset = DATASETS[sequence]
    print_header(f"Downloading {sequence} Dataset")

    print(f"Description: {dataset['description']}")
    print(f"Size:        {dataset['size']}")
    print(f"Duration:    {dataset['duration']}")
    print(f"Images:      {dataset['images']}")
    print(f"URL:         {dataset['rosbag_url']}")
    print()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{sequence}.bag")

    # Check if file already exists
    if os.path.exists(output_path):
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"⚠️  File already exists: {output_path}")
        print(f"   Size: {file_size_mb:.2f} MB")
        print()
        response = input("Do you want to re-download? (y/n): ")
        if response.lower() not in ["y", "yes"]:
            print("Skipping download.")
            return True

    print(f"Downloading to: {output_path}")
    print()
    print("⏳ This may take a while depending on your internet connection...")
    print()

    # Try wget first, then curl
    success = False

    print("Trying wget...")
    success = download_with_wget(dataset["rosbag_url"], output_path)

    if not success:
        print("\nwget failed or not available. Trying curl...")
        success = download_with_curl(dataset["rosbag_url"], output_path)

    if success:
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print()
        print(f"✅ Download completed successfully!")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size_mb:.2f} MB")
        print()
        print("Next steps:")
        print(f"  1. Extract images: python3 scripts/extract_images.py {output_path} --output data/{sequence}/")
        print(f"  2. Extract ground truth: python3 scripts/extract_ground_truth.py {output_path} --output data/{sequence}/ground_truth.txt")
        print(f"  3. Run ORB-SLAM3 on the extracted images")
        return True
    else:
        print()
        print("❌ Download failed!")
        print()
        print("Manual download instructions:")
        print(f"  1. Visit: {dataset['rosbag_url']}")
        print(f"  2. Download the file manually")
        print(f"  3. Save it to: {output_path}")
        return False


def list_datasets():
    """List all available datasets."""
    print_header("Available MARS-LVIG Dataset Sequences")

    for name, info in DATASETS.items():
        print(f"📦 {name}")
        print(f"   Description: {info['description']}")
        print(f"   Size:        {info['size']}")
        print(f"   Duration:    {info['duration']}")
        print(f"   Images:      {info['images']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Download MARS-LVIG dataset for AAE5303 assignment.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available datasets
  python3 scripts/download_dataset.py --list

  # Download AMtown02 (leaderboard evaluation dataset)
  python3 scripts/download_dataset.py --sequence AMtown02 --output data/

  # Download HKisland_GNSS03 (demo example)
  python3 scripts/download_dataset.py --sequence HKisland_GNSS03 --output data/

Dataset source:
  MARS-LVIG: https://mars.hku.hk/dataset.html
  GitHub: https://github.com/sijieaaa/UAVScenes
        """
    )

    parser.add_argument(
        "--sequence",
        choices=list(DATASETS.keys()),
        help="Dataset sequence to download (AMtown02 or HKisland_GNSS03)",
    )
    parser.add_argument(
        "--output",
        default="data",
        help="Output directory for downloaded files (default: data/)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available dataset sequences",
    )

    args = parser.parse_args()

    if args.list:
        list_datasets()
        return 0

    if not args.sequence:
        parser.print_help()
        print()
        list_datasets()
        return 1

    success = download_dataset(args.sequence, args.output)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
