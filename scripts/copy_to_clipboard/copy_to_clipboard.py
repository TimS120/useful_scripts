#!/usr/bin/env python3
"""
Usage: python3 copy_files_to_clipboard.py /path/to/overall_folder .

This script recursively copies the content of all readable text files 
in the specified folder to the clipboard using the Windows "clip" command.
"""

import os
import subprocess
import sys


def is_text_file(file_path):
    """
    Check whether a file is a text file.

    An empty file is considered a text file.
    For non-empty files, this function reads the first chunk of the file in binary mode
    and checks for null bytes. If a null byte is found, the file is considered binary.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file is empty or is likely a text file; False otherwise.
    """
    try:
        if os.path.getsize(file_path) == 0:
            return True
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b"\0" in chunk:
                return False
    except Exception:
        return False
    return True


def main():
    """
    Recursively copy the contents of all readable text files in the specified folder to clipboard.

    For each file:
    - A separator and the relative path are added.
    - The file content is appended.
    - If the file's content ends with a newline, one extra empty line is added;
      otherwise, two empty lines are appended.
    """
    print("Start to copy all files")

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} /path/to/folder")
        sys.exit(1)

    base_dir = os.path.realpath(sys.argv[1])
    if not os.path.isdir(base_dir):
        print(f"Error: Directory '{base_dir}' not found.")
        sys.exit(1)

    output_parts = []

    for root, _, files in os.walk(base_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if os.access(file_path, os.R_OK):
                # Process file if it is empty or a text file.
                if os.path.getsize(file_path) == 0 or is_text_file(file_path):
                    rel_path = os.path.relpath(file_path, base_dir)
                    output_parts.append("----------------")
                    output_parts.append(f"{rel_path}:")
                    try:
                        with open(file_path, "r", errors="replace") as f:
                            content = f.read()
                    except Exception:
                        continue
                    output_parts.append(content)
                    # Append extra newlines based on file content.
                    if len(content) == 0:
                        output_parts.append("")
                        output_parts.append("")
                    else:
                        if content.endswith("\n"):
                            output_parts.append("")
                        else:
                            output_parts.append("")
                            output_parts.append("")

    final_output = "\n".join(output_parts)
    if not final_output.endswith("\n"):
        final_output += "\n"

    try:
        # On Windows, use the built-in "clip" command.
        # Windows clip expects Unicode text as UTF-16.
        proc = subprocess.Popen("clip", stdin=subprocess.PIPE, shell=True)
        proc.stdin.write(final_output.encode("utf-16"))
        proc.stdin.close()
        proc.wait()
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        sys.exit(1)

    print("All text-readable file contents have been copied to the clipboard.")


if __name__ == "__main__":
    main()
