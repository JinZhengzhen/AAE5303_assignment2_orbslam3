#!/bin/bash
#
# AAE5303 Assignment Quick Start Script
# This script helps you complete the ORB-SLAM3 visual odometry assignment step by step.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check dependencies
check_dependencies() {
    print_header "Step 1: Checking Dependencies"

    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python3 installed: $PYTHON_VERSION"
    else
        print_error "Python3 not found. Please install Python 3.6 or later."
        exit 1
    fi

    # Check evo
    if command -v evo_ape &> /dev/null; then
        print_success "evo toolkit installed"
    else
        print_warning "evo toolkit not found"
        echo "Install with: pip install evo"
        echo "Continue anyway? (y/n)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Check numpy
    if python3 -c "import numpy" &> /dev/null; then
        print_success "numpy installed"
    else
        print_warning "numpy not found. Install with: pip install numpy"
    fi
}

# Guide user through the process
guide_user() {
    print_header "AAE5303 ORB-SLAM3 Visual Odometry Assignment"

    echo "This script will guide you through completing the assignment."
    echo ""
    echo "Prerequisites:"
    echo "  1. ORB-SLAM3 is compiled and working"
    echo "  2. You have generated CameraTrajectory.txt from ORB-SLAM3"
    echo "  3. You have the ground_truth.txt file"
    echo ""
    echo "If you haven't done these steps yet, please refer to:"
    echo "  docs/STUDENT_GUIDE.md"
    echo ""
    read -p "Press Enter to continue..."
}

# Evaluate trajectory
evaluate_trajectory() {
    print_header "Step 2: Evaluate Trajectory"

    # Ask for file paths
    echo "Please provide the following file paths:"
    echo ""

    read -p "Ground truth file (TUM format): " GT_FILE
    if [ ! -f "$GT_FILE" ]; then
        print_error "File not found: $GT_FILE"
        exit 1
    fi

    read -p "Estimated trajectory (CameraTrajectory.txt): " EST_FILE
    if [ ! -f "$EST_FILE" ]; then
        print_error "File not found: $EST_FILE"
        exit 1
    fi

    # Create evaluation directory
    EVAL_DIR="$PROJECT_ROOT/evaluation_results"
    mkdir -p "$EVAL_DIR"

    print_info "Running evaluation with evo..."
    echo ""

    # Run evaluation
    python3 "$SCRIPT_DIR/evaluate_vo_accuracy.py" \
        --groundtruth "$GT_FILE" \
        --estimated "$EST_FILE" \
        --t-max-diff 0.1 \
        --delta-m 10 \
        --workdir "$EVAL_DIR" \
        --json-out "$EVAL_DIR/metrics.json"

    if [ $? -eq 0 ]; then
        print_success "Evaluation completed successfully!"
        print_info "Results saved to: $EVAL_DIR/metrics.json"
    else
        print_error "Evaluation failed. Please check the error messages above."
        exit 1
    fi
}

# Create submission
create_submission() {
    print_header "Step 3: Create Leaderboard Submission"

    EVAL_DIR="$PROJECT_ROOT/evaluation_results"
    METRICS_FILE="$EVAL_DIR/metrics.json"

    if [ ! -f "$METRICS_FILE" ]; then
        print_error "Metrics file not found: $METRICS_FILE"
        print_error "Please run evaluation first."
        exit 1
    fi

    echo "Please provide the following information:"
    echo ""

    read -p "Group name (e.g., Team Alpha): " GROUP_NAME
    if [ -z "$GROUP_NAME" ]; then
        print_error "Group name cannot be empty"
        exit 1
    fi

    read -p "GitHub repository URL (must end with .git): " REPO_URL
    if [ -z "$REPO_URL" ]; then
        print_error "Repository URL cannot be empty"
        exit 1
    fi

    # Create safe filename from group name
    SAFE_NAME=$(echo "$GROUP_NAME" | sed 's/ /_/g' | sed 's/[^a-zA-Z0-9_-]//g')
    OUTPUT_FILE="$PROJECT_ROOT/${SAFE_NAME}_leaderboard.json"

    print_info "Creating submission file..."
    echo ""

    # Create submission
    python3 "$SCRIPT_DIR/create_leaderboard_submission.py" \
        --metrics "$METRICS_FILE" \
        --group-name "$GROUP_NAME" \
        --repo-url "$REPO_URL" \
        --output "$OUTPUT_FILE"

    if [ $? -eq 0 ]; then
        print_success "Submission file created successfully!"
        print_info "File location: $OUTPUT_FILE"
    else
        print_error "Failed to create submission file"
        exit 1
    fi
}

# Validate submission
validate_submission() {
    print_header "Step 4: Validate Submission"

    # Find submission files
    SUBMISSION_FILES=(*_leaderboard.json)

    if [ ${#SUBMISSION_FILES[@]} -eq 0 ] || [ ! -f "${SUBMISSION_FILES[0]}" ]; then
        print_warning "No submission files found in current directory"
        read -p "Enter path to submission file: " SUBMISSION_FILE
    elif [ ${#SUBMISSION_FILES[@]} -eq 1 ]; then
        SUBMISSION_FILE="${SUBMISSION_FILES[0]}"
        print_info "Found submission file: $SUBMISSION_FILE"
    else
        print_info "Multiple submission files found:"
        select SUBMISSION_FILE in "${SUBMISSION_FILES[@]}"; do
            break
        done
    fi

    if [ ! -f "$SUBMISSION_FILE" ]; then
        print_error "File not found: $SUBMISSION_FILE"
        exit 1
    fi

    print_info "Validating submission..."
    echo ""

    python3 "$SCRIPT_DIR/validate_submission.py" "$SUBMISSION_FILE"

    if [ $? -eq 0 ]; then
        print_success "Validation passed!"
        echo ""
        print_info "Next steps:"
        echo "  1. Submit $SUBMISSION_FILE according to course instructions"
        echo "  2. View leaderboard at: https://qian9921.github.io/leaderboard_web/"
    else
        print_error "Validation failed. Please fix the errors before submitting."
        exit 1
    fi
}

# Main workflow
main() {
    cd "$PROJECT_ROOT"

    guide_user
    check_dependencies
    evaluate_trajectory
    create_submission
    validate_submission

    print_header "Assignment Complete!"
    print_success "All steps completed successfully!"
    echo ""
    print_info "Your submission file is ready for upload."
    print_info "Good luck on the leaderboard! 🚀"
}

# Run main workflow
main
