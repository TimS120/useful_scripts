#!/usr/bin/env bash

# Usage: ./quality_checks.sh <project_directory> [exclude_dir1] [exclude_dir2] …
# Iterates all .py files, runs autoflake and duplicate detection, then aggregates flake8 checks and other tools

set -euo pipefail

# Color definitions for output headings
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print a colored header with an empty line before
print_header() {
    echo
    echo -e "${CYAN}$1${NC}"
}

PROJECT_DIR="${1:-}"
shift || true
EXCLUDES=("$@")

if [[ -z "$PROJECT_DIR" ]]; then
    echo "Usage: $0 <project_directory> [exclude_dir1] [exclude_dir2] …"
    exit 1
fi

cd "$PROJECT_DIR" || { echo -e "${RED}ERROR:${NC} cannot cd into \"$PROJECT_DIR\""; exit 1; }

# Build find command to locate .py files, excluding specified directories
if (( ${#EXCLUDES[@]} )); then
    PRUNE=""
    for ex in "${EXCLUDES[@]}"; do
        PRUNE+=" -name \"$ex\" -prune -o"
    done
    FIND_CMD="find . $PRUNE -type f -name \"*.py\" -print"
else
    FIND_CMD='find . -type f -name "*.py"'
fi

# Flake8 base exclude list
BASE_EX=".git,__pycache__,docs"
if (( ${#EXCLUDES[@]} )); then
    EXCL="$BASE_EX,${EXCLUDES[*]}"
else
    EXCL="$BASE_EX"
fi

# Build autoflake exclude args
AUTOFLAKE_EXC=()
for ex in "${EXCLUDES[@]}"; do
    AUTOFLAKE_EXC+=(--exclude "$ex")
done

# Build grep exclude-dir args for duplicate import detection
GREP_EXC=()
for ex in "${EXCLUDES[@]}"; do
    GREP_EXC+=(--exclude-dir="$ex")
done

# Process each Python file: autoflake and duplicate detection
eval "$FIND_CMD" | while read -r file; do
    print_header "=== Processing: $file ==="

    # Autoflake: unused import detection (no in-place changes)
    autoflake --remove-all-unused-imports --recursive . "${AUTOFLAKE_EXC[@]}"

    # Check for duplicate import statements via grep
    dup_imports=$(grep "^import " -r . "${GREP_EXC[@]}" | sort | uniq -d)
    dup_froms=$(grep "^from " -r . "${GREP_EXC[@]}" | sort | uniq -d)

    if [[ -n "$dup_imports" ]]; then
        echo -e "${YELLOW}--- duplicate 'import ' lines ---${NC}"
        echo "$dup_imports"
    fi

    if [[ -n "$dup_froms" ]]; then
        echo -e "${YELLOW}--- duplicate 'from ' lines ---${NC}"
        echo "$dup_froms"
    fi

done

# === Additional checks on the full project ===

print_header "=== Running flake8 checks ==="
if ! command -v flake8 &>/dev/null; then
    echo "  → flake8 not found, please install it to run lint checks."
else
    if ! flake8 \
        --max-line-length=120 \
        --exclude="$EXCL" \
        --select=D,UFS,T001,A,G,C901 \
        "$PROJECT_DIR"; then
        echo "  → flake8 reported issues above, continuing…"
    fi
fi

print_header "=== Running isort import order checks ==="
if ! command -v isort &>/dev/null; then
    echo "  → isort not found, please install it to run import order checks."
else
    if ! isort --check-only "$PROJECT_DIR"; then
        echo "  → isort reported issues above, continuing…"
    fi
fi

# Cyclomatic complexity analysis (only report blocks with CC > 10)
if ! command -v radon &>/dev/null; then
    echo "  → radon not found, please install it to run complexity checks."
else
    CC_OUTPUT=$(radon cc "$PROJECT_DIR" -s -n C)
    if [[ -n "$CC_OUTPUT" ]]; then
        print_header "=== Running radon cyclomatic complexity checks (score > 10) ==="
        echo "$CC_OUTPUT"
        echo "  → radon reported issues above threshold, continuing…"
    fi
fi

print_header "=== Running vulture unused code checks ==="
if ! command -v vulture &>/dev/null; then
    echo "  → vulture not found, please install it to run unused code detection."
else
    if ! vulture "$PROJECT_DIR"; then
        echo "  → vulture reported issues above, continuing…"
    fi
fi

print_header "=== Duplicate-code detection (jscpd) ==="
if command -v jscpd &>/dev/null; then
    # allow jscpd to exit non-zero without killing the script
    set +e
    dup_output=$(jscpd --min-lines 10 --reporters console "$PROJECT_DIR" 2>&1)
    dup_exit=$?
    set -e

    # jscpd returns non-zero when it finds duplicate blocks
    if (( dup_exit != 0 )); then
        print_header "=== Duplicate-code detection (jscpd) ==="
        printf '%s\n' "$dup_output"
        echo "  → jscpd found duplicates, continuing…"
    fi
else
    echo "  → jscpd not installed, skipping duplicate-code detection."
fi

# Pylint naming convention (C0103) with threshold reporting
PYLINT_THRESHOLD=10.0
print_header "=== Running pylint naming convention checks ==="
if ! command -v pylint &>/dev/null; then
    echo "  → pylint not found, please install it to run naming convention checks."
else
    PYLINT_OUTPUT=$(pylint --disable=all --enable=C0103 "$PROJECT_DIR" 2>&1)
    # Extract score: 'rated at X.XX/10'
    PYLINT_SCORE=$(echo "$PYLINT_OUTPUT" | grep 'rated at' | awk '{print substr($7, 1, length($7)-3)}')
    # Compare score to threshold
    if awk "BEGIN {exit !($PYLINT_SCORE < $PYLINT_THRESHOLD)}"; then
        echo "$PYLINT_OUTPUT"
        echo "  → pylint score ${PYLINT_SCORE}/10 below threshold ${PYLINT_THRESHOLD}, continuing…"
    else
        echo -e "${GREEN}  → pylint passed with ${PYLINT_SCORE}/10${NC}"
    fi
fi
