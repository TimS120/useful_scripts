#!/usr/bin/env bash

# Usage: ./quality_checks.sh <project_directory> [exclude_dir1] [exclude_dir2] ...
# Iterates all .py files (except __init__.py) and runs checks

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
    echo "Usage: $0 <project_directory> [exclude_dir1] [exclude_dir2] ..."
    exit 1
fi

cd "$PROJECT_DIR" || { echo -e "${RED}ERROR:${NC} cannot cd into \"$PROJECT_DIR\""; exit 1; }


# Flake8 base exclude list (we will also exclude __init__.py explicitly below)
BASE_EX=".git,__pycache__,docs"
if (( ${#EXCLUDES[@]} )); then
    EXCL="$BASE_EX,${EXCLUDES[*]}"
else
    EXCL="$BASE_EX"
fi


print_header "=== Running flake8 checks ==="
if ! command -v flake8 &>/dev/null; then
    echo "  → flake8 not found, please install it to run lint checks."
else
    if ! flake8 \
        --max-line-length=120 \
        --exclude="${EXCL},__init__.py" \
        --select=D,UFS,T001,A,G,C901,E501 \
        "$PROJECT_DIR"; then
        echo "  → flake8 reported issues above, continuing…"
    fi
fi

print_header "=== Running isort import order checks ==="
# isort options:
#   --check-only    : report unsorted imports without applying changes
#   --diff          : show unified diff of proposed changes (preferred for output)
#   --skip          : skip matching files (e.g., __init__.py)
#   --verbose       : display configuration and file-level details
#   You can configure import sections (stdlib, third-party, first-party) via pyproject.toml or setup.cfg
if ! command -v isort &>/dev/null; then
    echo "  → isort not found, please install it to run import order checks."
else
    # First, check only and capture exit, skipping __init__.py
    if ! isort --check-only --skip="__init__.py" "$PROJECT_DIR"; then
        echo "  → isort detected ordering issues. Showing diff of correct order:"
        isort --diff --skip="__init__.py" "$PROJECT_DIR"  # shows how imports should be ordered
        echo "  → apply suggested order with: isort --skip='__init__.py' '$PROJECT_DIR'"
    else
        echo -e "${GREEN}  → isort import order OK${NC}"
    fi
fi

print_header "=== Duplicate-code detection (jscpd) ==="
if command -v jscpd &>/dev/null; then
    # allow jscpd to exit non-zero without killing the script
    set +e
    dup_output=$(jscpd --min-lines 10 --reporters console --ignore "**/__init__.py" "$PROJECT_DIR" 2>&1)
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

print_header "=== Checking for confusing Unicode punctuation ==="
# First grep finds any non-ASCII byte, second ensures it’s punctuation or symbol
# Skip __init__.py via --exclude
if grep -R -n --include="*.py" --exclude="__init__.py" -P "[^\x00-\x7F]" "$PROJECT_DIR" \
       | grep -P "[\p{P}\p{S}]"; then
    echo -e "${RED}--- Confusing Unicode punctuation detected in source ---${NC}"
    # Show each offending line, the exact character(s), and their code points
    # temporarily disable “exit on error” so this pipeline can fail harmlessly
    set +e
    grep -R -n --include="*.py" --exclude="__init__.py" -P "[^\x00-\x7F]" "$PROJECT_DIR" \
      | grep -P "[\p{P}\p{S}]" \
      | while IFS=: read -r file line text; do
          chars=$(printf '%s' "$text" \
                   | grep -oP "[^\x00-\x7F]" \
                   | grep -oP "[\p{P}\p{S}]" \
                   | tr -d '\n')
          hexes=$(printf '%s' "$chars" \
                   | od -An -t u4 \
                   | tr -s ' ' ',' \
                   | sed 's/^,//')
          printf "%s:%s → %s (U+%s)\n" "$file" "$line" "$text" "$hexes"
      done
    # restore “exit on error” behavior
    set -e
    echo "  → Please replace with standard ASCII characters (e.g. '-', '\"', etc.)."
else
    echo -e "${GREEN}  → No confusing Unicode punctuation found${NC}"
fi

# Pylint default-value checks
print_header "=== Running pylint (all checks except some) ==="
if ! command -v pylint &>/dev/null; then
    echo "  → pylint not found, please install it to run lint checks."
else
    # Disable missing-docstring, invalid-name, and fixme
    # Also ignore any __init__.py files
    if ! pylint \
         --disable=C0301,W0201,R0902,R0904 \
         --ignore-patterns="__init__.py" \
         "$PROJECT_DIR"; then
        echo "  → pylint reported issues above (excluding disabled checks), continuing…"
    else
        echo -e "${GREEN}  → pylint passed (with specified checks disabled)${NC}"
    fi
fi

print_header "=== Running lizard size & complexity checks ==="
if ! command -v lizard &>/dev/null; then
    echo "  → lizard not found, please install it to run advanced complexity checks."
else
    # Use find to pass only *.py files that are NOT __init__.py
    find "$PROJECT_DIR" -type f -name "*.py" ! -name "__init__.py" -print0 \
      | xargs -0 lizard \
         -C 10 \
         -L 50 \
         -a 5 \
         -Ttoken_count=150
fi
