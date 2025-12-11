#!/usr/bin/env python3
"""
Count lines of code in all Python files within a directory and its subdirectories.

Usage:
    python count_lines.py /path/to/directory
"""

import os
import sys


def count_lines_in_file(file_path: str) -> int:
    """Return the number of lines in a single Python file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        return sum(1 for _ in file)


def count_lines_in_directory(directory: str) -> int:
    """Count total lines in all Python files in the given directory recursively."""
    total_lines = 0
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".py"):
                file_path = os.path.join(root, filename)
                total_lines += count_lines_in_file(file_path)
    return total_lines


def main() -> None:
    """Parse command-line argument and print the total line count."""
    if len(sys.argv) != 2:
        print("Usage: python count_lines.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        sys.exit(1)

    total_lines = count_lines_in_directory(directory)
    print(f"Total lines of Python code in '{directory}': {total_lines}")


if __name__ == "__main__":
    main()
