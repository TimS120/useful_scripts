#!/usr/bin/env python3
"""Export each separate non-transparent area of a PNG as a tightly cropped PNG.

Requires Pillow:  python -m pip install Pillow
"""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image


def find_areas(image: Image.Image, alpha_threshold: int) -> list[tuple[int, int, int, int]]:
    """Find 8-connected visible pixel regions and return their crop boxes."""
    image = image.convert("RGBA")
    width, height = image.size
    alpha = image.getchannel("A")
    visible = alpha.load()
    visited = bytearray(width * height)
    areas: list[tuple[int, int, int, int]] = []

    for start_y in range(height):
        for start_x in range(width):
            start_index = start_y * width + start_x
            if visited[start_index] or visible[start_x, start_y] < alpha_threshold:
                continue

            queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
            visited[start_index] = 1
            left = right = start_x
            top = bottom = start_y

            while queue:
                x, y = queue.popleft()
                left, right = min(left, x), max(right, x)
                top, bottom = min(top, y), max(bottom, y)
                for next_y in range(max(0, y - 1), min(height, y + 2)):
                    for next_x in range(max(0, x - 1), min(width, x + 2)):
                        index = next_y * width + next_x
                        if not visited[index] and visible[next_x, next_y] >= alpha_threshold:
                            visited[index] = 1
                            queue.append((next_x, next_y))

            # Pillow's right and lower crop coordinates are exclusive.
            areas.append((left, top, right + 1, bottom + 1))
    return areas


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split visible regions of a transparent image into cropped PNG files.")
    parser.add_argument("input_image", type=Path, help="Transparent image created by remove_background.py")
    parser.add_argument("output_folder", type=Path, help="Folder for the cropped area PNG files")
    parser.add_argument("--alpha-threshold", type=int, default=1, metavar="0-255",
                        help="Pixels with alpha at or above this value belong to an area (default: 1)")
    args = parser.parse_args()
    if not args.input_image.is_file():
        parser.error(f"Input image does not exist: {args.input_image}")
    if not 0 <= args.alpha_threshold <= 255:
        parser.error("--alpha-threshold must be between 0 and 255")
    return args


def main() -> None:
    args = parse_arguments()
    with Image.open(args.input_image) as source:
        image = source.convert("RGBA")
    areas = find_areas(image, args.alpha_threshold)
    args.output_folder.mkdir(parents=True, exist_ok=True)

    if not areas:
        print("No visible areas found.")
        return
    for number, box in enumerate(areas, start=1):
        destination = args.output_folder / f"{args.input_image.stem}_area_{number:03}.png"
        image.crop(box).save(destination, "PNG")
        print(f"Saved area {number}: {destination}")


if __name__ == "__main__":
    main()
