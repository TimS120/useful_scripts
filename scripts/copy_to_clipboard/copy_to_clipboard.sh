#!/bin/bash
# Usage: bash copy_files_to_clipboard.sh /path/to/overall_folder
# This script recursively copies the content of all readable text files 
# in the specified folder to the clipboard using xclip.

echo "Start to copy all files"

# Validate input.
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 /path/to/folder"
    exit 1
fi

# Get absolute path of the provided directory.
BASEDIR=$(realpath "$1")
if [ ! -d "$BASEDIR" ]; then
    echo "Error: Directory '$BASEDIR' not found."
    exit 1
fi

# Check if xclip is installed.
if ! command -v xclip &>/dev/null; then
    echo "Error: xclip is not installed. Please install it and try again."
    exit 1
fi

# Create a temporary file for concatenated output.
TMPFILE=$(mktemp)

# Iterate over all files in the directory recursively.
find "$BASEDIR" -type f | while read -r file; do
    # Check if the file is readable and is text.
    if [ -r "$file" ]; then
        # Consider empty files as text.
        if [ ! -s "$file" ] || grep -Iq . "$file" 2>/dev/null; then
            # Get the relative path.
            RELPATH=$(realpath --relative-to="$BASEDIR" "$file")
            # Output separator, filename with colon, then file content.
            echo "----------------" >> "$TMPFILE"
            echo "${RELPATH}:" >> "$TMPFILE"
            cat "$file" >> "$TMPFILE"
            # Append extra newlines based on whether the file ends with an empty line.
            if [ -s "$file" ]; then
                last_char=$(tail -c1 "$file")
                if [ "$last_char" = $'\n' ]; then
                    # File already ends with a newline; add one additional empty line.
                    echo "" >> "$TMPFILE"
                else
                    # File does not end with a newline; add two empty lines.
                    echo "" >> "$TMPFILE"
                    echo "" >> "$TMPFILE"
                fi
            else
                # Empty file; add two empty lines.
                echo "" >> "$TMPFILE"
                echo "" >> "$TMPFILE"
            fi
        fi
    fi
done

# Ensure the TMPFILE ends with a newline.
if [ -s "$TMPFILE" ] && [ "$(tail -c1 "$TMPFILE")" != $'\n' ]; then
    echo "" >> "$TMPFILE"
fi

# Copy the content of the temporary file to the clipboard.
xclip -selection clipboard < "$TMPFILE"

# Clean up.
rm "$TMPFILE"

echo "All text-readable file contents have been copied to the clipboard."
