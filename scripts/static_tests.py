#!/usr/bin/env python3
"""
Script to conduct some basic static tests on a python file.

Usage: python3 static_tests.py file_to_test.py
"""


import argparse


def parse_args():
    """
    Parses command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Check Python script formatting rules."
    )
    parser.add_argument(
        "path",
        help="Path to the Python file to check."
    )
    return parser.parse_args()


def check_indentation_consistency(lines):
    """
    Checks for consistent use of indentation (spaces or tabs) in the given lines.
    """
    initial_type = None
    violations = []
    for idx, line in enumerate(lines):
        if line.strip() == "":
            continue
        indent = line[:len(line) - len(line.lstrip(" \t"))]
        if not indent:
            continue
        has_space = " " in indent
        has_tab = "\t" in indent
        if has_space and has_tab:
            violations.append((idx + 1, "mixed indentation (spaces and tabs)"))
            continue
        current_type = "spaces" if has_space else "tabs"
        if initial_type is None:
            initial_type = current_type
        elif current_type != initial_type:
            violations.append(
                (idx + 1,
                 f"inconsistent indentation (expected {initial_type}, got {current_type})")
            )
    return violations


def check_trailing_whitespace(lines):
    """
    Checks for trailing whitespace or whitespace on empty lines.
    """
    violations = []
    for idx, line in enumerate(lines):
        raw = line.rstrip("\r\n")
        if raw == "":
            if line not in ("\n", "\r\n"):
                violations.append((idx + 1, "whitespace on empty line"))
        elif raw.endswith(" ") or raw.endswith("\t"):
            violations.append((idx + 1, "trailing whitespace"))
    return violations


def check_nesting_level(lines):
    """
    Checks for maximum nesting level not exceeding 4 in the given lines.
    """
    space_indents = []
    tab_indents = []
    for line in lines:
        if line.strip() == "":
            continue
        indent = line[:len(line) - len(line.lstrip(" \t"))]
        if not indent:
            continue
        if "\t" in indent and " " not in indent:
            tab_indents.append(indent.count("\t"))
        elif " " in indent and "\t" not in indent:
            space_indents.append(len(indent))
    violations = []
    unit_spaces = min(space_indents) if space_indents else None
    for idx, line in enumerate(lines):
        if line.strip() == "":
            continue
        indent = line[:len(line) - len(line.lstrip(" \t"))]
        if not indent:
            continue
        if "\t" in indent and " " not in indent:
            level = indent.count("\t")
        elif " " in indent and "\t" not in indent and unit_spaces:
            level = len(indent) // unit_spaces
        else:
            continue
        if level > 4:
            violations.append(
                (idx + 1,
                 f"nesting level {level} exceeds maximum of 4")
            )
    return violations


def check_line_length(lines):
    """
    Checks that no line exceeds 110 characters.
    """
    violations = []
    for idx, line in enumerate(lines):
        length = len(line.rstrip("\r\n"))
        if length > 120:
            violations.append(
                (idx + 1,
                 f"line length {length} exceeds maximum of 120")
            )
    return violations


def main():
    """
    Main function to run checks on the provided file.
    """
    args = parse_args()
    with open(args.path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    all_violations = []

    for ln, msg in check_indentation_consistency(lines):
        all_violations.append(f"Line {ln}: {msg}")
    for ln, msg in check_trailing_whitespace(lines):
        all_violations.append(f"Line {ln}: {msg}")
    for ln, msg in check_nesting_level(lines):
        all_violations.append(f"Line {ln}: {msg}")
    for ln, msg in check_line_length(lines):
        all_violations.append(f"Line {ln}: {msg}")

    for violation in all_violations:
        print(violation)


if __name__ == "__main__":
    main()
