#!/usr/bin/env python3
"""Remove a flat, border-connected background from an image.

Requires Pillow:  python -m pip install Pillow
"""

from __future__ import annotations

import argparse
from collections import Counter, deque
from pathlib import Path

from PIL import Image


def squared_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return sum((left - right) ** 2 for left, right in zip(a, b))


def border_background_colour(image: Image.Image, border: int) -> tuple[int, int, int]:
    """Return the most common (slightly quantized) opaque colour at the edge."""
    width, height = image.size
    pixels = image.load()
    samples: list[tuple[int, int, int]] = []

    for y in range(height):
        for x in range(width):
            if x < border or x >= width - border or y < border or y >= height - border:
                r, g, b, alpha = pixels[x, y]
                if alpha:
                    # Quantization makes an anti-aliased/noisy flat background stable.
                    samples.append((round(r / 8) * 8, round(g / 8) * 8, round(b / 8) * 8))

    if not samples:
        raise ValueError("The image has no opaque border pixels from which to infer a background.")
    return Counter(samples).most_common(1)[0][0]


def parse_colour(value: str) -> tuple[int, int, int]:
    """Parse #RRGGBB, RRGGBB, or #RGB into an RGB tuple."""
    value = value.strip().removeprefix("#")
    if len(value) == 3:
        value = "".join(component * 2 for component in value)
    if len(value) != 6:
        raise argparse.ArgumentTypeError("colour must be #RGB or #RRGGBB")
    try:
        return tuple(int(value[index:index + 2], 16) for index in range(0, 6, 2))  # type: ignore[return-value]
    except ValueError as error:
        raise argparse.ArgumentTypeError("colour must contain only hexadecimal digits") from error


def remove_background(
    image: Image.Image,
    tolerance: int,
    border: int,
    background: tuple[int, int, int] | None = None,
) -> Image.Image:
    """Make border-connected pixels near the inferred background transparent."""
    image = image.convert("RGBA")
    width, height = image.size
    pixels = image.load()
    background = background or border_background_colour(image, border)
    limit = tolerance * tolerance

    queue: deque[tuple[int, int]] = deque()
    visited = bytearray(width * height)

    def matches(x: int, y: int) -> bool:
        r, g, b, alpha = pixels[x, y]
        return bool(alpha) and squared_distance((r, g, b), background) <= limit

    # Begin only at the outer edge. This preserves matching colours inside the subject.
    for x in range(width):
        queue.extend(((x, 0), (x, height - 1)))
    for y in range(1, height - 1):
        queue.extend(((0, y), (width - 1, y)))

    while queue:
        x, y = queue.popleft()
        index = y * width + x
        if visited[index] or not matches(x, y):
            continue
        visited[index] = 1
        r, g, b, _ = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)
        if x:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))

    return image


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remove a flat background inferred from an image border.")
    parser.add_argument("input_image", type=Path, help="Path to the source image")
    parser.add_argument("output_folder", type=Path, help="Folder for the transparent PNG")
    parser.add_argument("--tolerance", type=int, default=35, metavar="0-255",
                        help="Colour tolerance (default: 35; raise it for JPEG/noisy backgrounds)")
    parser.add_argument("--border", type=int, default=3, metavar="PIXELS",
                        help="Width of edge strip used to identify the background (default: 3)")
    parser.add_argument("--background-colour", type=parse_colour, metavar="#RRGGBB",
                        help="Background colour to remove; skips automatic border-colour detection")
    args = parser.parse_args()
    if not args.input_image.is_file():
        parser.error(f"Input image does not exist: {args.input_image}")
    if not 0 <= args.tolerance <= 255:
        parser.error("--tolerance must be between 0 and 255")
    if args.border < 1:
        parser.error("--border must be at least 1")
    return args


def main() -> None:
    args = parse_arguments()
    with Image.open(args.input_image) as source:
        result = remove_background(source, args.tolerance, args.border, args.background_colour)
    args.output_folder.mkdir(parents=True, exist_ok=True)
    destination = args.output_folder / f"{args.input_image.stem}_no_background.png"
    result.save(destination, "PNG")
    print(f"Saved transparent image: {destination}")


if __name__ == "__main__":
    main()
