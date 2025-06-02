#!/usr/bin/env bash

# Usage: ./quality_checks.sh <project_directory> [exclude_dir1] [exclude_dir2] …
# Iterates all .py files and runs checks

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


# Flake8 base exclude list
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
#   --verbose       : display configuration and file-level details
#   You can configure import sections (stdlib, third-party, first-party) via pyproject.toml or setup.cfg
if ! command -v isort &>/dev/null; then
    echo "  → isort not found, please install it to run import order checks."
else
    # First, check only and capture exit
    if ! isort --check-only "$PROJECT_DIR"; then
        echo "  → isort detected ordering issues. Showing diff of correct order:"
        isort --diff "$PROJECT_DIR"  # shows how imports should be ordered
        echo "  → apply suggested order with: isort '$PROJECT_DIR'"
    else
        echo -e "${GREEN}  → isort import order OK${NC}"
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

# Pylint default-value checks
print_header "=== Running pylint (all checks except some) ==="
if ! command -v pylint &>/dev/null; then
    echo "  → pylint not found, please install it to run lint checks."
else
    # Disable missing-docstring, invalid-name, and fixme
    if ! pylint \
         --disable=C0301,W0201,R0902,R0904 \
         "$PROJECT_DIR"; then
        echo "  → pylint reported issues above (excluding disabled checks), continuing…"
    else
        echo -e "${GREEN}  → pylint passed (with specified checks disabled)${NC}"
    fi
fi

# Fail on any character outside the ASCII range U+0000–U+007F
print_header "=== Checking for confusing Unicode punctuation ==="
# First grep finds any non-ASCII byte, second ensures it’s punctuation or symbol
if grep -R -n --include="*.py" -P "[^\x00-\x7F]" "$PROJECT_DIR" \
       | grep -P "[\p{P}\p{S}]"; then
    echo -e "${RED}--- Confusing Unicode punctuation detected in source ---${NC}"
    # Show each offending line, the exact character(s), and their code points
    grep -R -n --include="*.py" -P "[^\x00-\x7F]" "$PROJECT_DIR" \
      | grep -P "[\p{P}\p{S}]" \
      | while IFS=: read -r file line text; do
          # extract only the confusing punctuation/symbol characters
          chars=$(printf '%s' "$text" \
                   | grep -oP "[^\x00-\x7F]" \
                   | grep -oP "[\p{P}\p{S}]" \
                   | tr -d '\n')
          # convert to U+XXXX notation
          hexes=$(printf '%s' "$chars" \
                   | od -An -t u4 \
                   | tr -s ' ' ',' \
                   | sed 's/^,//')
          printf "%s:%s → %s (U+%s)\n" "$file" "$line" "$text" "$hexes"
      done
    echo "  → Please replace with standard ASCII characters (e.g. '-', '\"', etc.)."
    exit 1
else
    echo -e "${GREEN}  → No confusing Unicode punctuation found${NC}"
fi

print_header "=== Running lizard size & complexity checks ==="
if ! command -v lizard &>/dev/null; then
    echo "  → lizard not found, please install it to run advanced complexity checks."
else
    # Cyclomatic complexity threshold (CC > 10)
    # NLOC threshold (lines > 50)
    # Parameter count threshold (> 5)
    # Token count threshold (> 100)
    lizard \
      -C 10 \
      -L 50 \
      -a 5 \
      -Ttoken_count=150 \
      "$PROJECT_DIR"
fi
