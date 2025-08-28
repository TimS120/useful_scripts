#!/usr/bin/env python3
"""
Create an animated GIF from selected images.

Overview:
    - You can pass image paths (or directories) on the CLI, or omit them to
      open a native multi-select file dialog. The dialog supports Shift-click
      and Ctrl/Cmd-click for selecting multiple images in one go.
    - GIFs do not have a fixed size. If "--size WIDTHxHEIGHT" is given, all
      frames are resized (optionally letterboxed when "--keep-aspect" is set).
      If no size is given, frames are unified to the first frame's size.
    - Frame duration is specified in milliseconds ("--duration-ms").
    - Output is written as a single animated GIF.

Examples:
    # Pick files via GUI, 1 fps (1000 ms/frame), infinite loop
    python make_gif.py --duration-ms 1000 --output out.gif

    # Use explicit files, resize to 800x450, keep aspect ratio with padding
    python make_gif.py --duration-ms 80 --size 800x450 --keep-aspect
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageOps, features

# Pick a quantization method supported by the current Pillow build.
# Prefer libimagequant (best quality) if compiled in; else use FASTOCTREE; else MEDIANCUT.
if features.check("libimagequant"):
    QUANTIZE_METHOD = Image.LIBIMAGEQUANT  # requires libimagequant at compile time
else:
    # FASTOCTREE is builtin and generally available on Pillow wheels.
    QUANTIZE_METHOD = getattr(Image, "FASTOCTREE", 0)  # 0 == MEDIANCUT fallback

from contextlib import contextmanager


def parse_size(text: Optional[str]) -> Optional[Tuple[int, int]]:
    """
    Parse a size specification "WIDTHxHEIGHT" into a (width, height) tuple.

    Args:
        text: Size string like "800x600" or None.

    Returns:
        Tuple of integers (width, height) if provided, otherwise None.

    Raises:
        ValueError: If the size string is malformed or contains nonpositive values.
    """
    if text is None:
        return None
    if "x" not in text:
        raise ValueError('Size must be in the form "WIDTHxHEIGHT", e.g., "800x600".')
    w_str, h_str = text.lower().split("x", 1)
    width = int(w_str)
    height = int(h_str)
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive integers.")
    return width, height

@contextmanager
def select_images_via_gui_ctx():
    """
    Context manager opening a multi-select file dialog and ensuring Tk teardown.

    Yields:
        List of selected image paths. Range selection via Shift-click is supported
        by the native dialog; noncontiguous selection via Ctrl/Cmd-click.
    """
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        filepaths = filedialog.askopenfilenames(
            title="Select images for GIF",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp *.gif"),
                ("All files", "*.*"),
            ],
        )
        yield [Path(p) for p in filepaths]
    finally:
        # Guarantees no ghost window and releases GUI resources.
        root.destroy()

def discover_images(paths: Sequence[str]) -> List[Path]:
    """
    Expand and validate image paths.

    Args:
        paths: Sequence of file paths.

    Returns:
        Sorted list of existing file paths.

    Raises:
        FileNotFoundError: If any given path does not exist.
        ValueError: If no images are found.
    """
    resolved: List[Path] = []
    for p in paths:
        candidate = Path(p).expanduser()
        if not candidate.exists():
            raise FileNotFoundError(f"Path does not exist: {candidate}")
        if candidate.is_dir():
            # Include common image extensions
            resolved.extend(
                sorted(
                    list(candidate.glob("*.png"))
                    + list(candidate.glob("*.jpg"))
                    + list(candidate.glob("*.jpeg"))
                    + list(candidate.glob("*.bmp"))
                    + list(candidate.glob("*.tif"))
                    + list(candidate.glob("*.tiff"))
                    + list(candidate.glob("*.webp"))
                    + list(candidate.glob("*.gif"))
                )
            )
        else:
            resolved.append(candidate)
    # De-duplicate while preserving order
    seen = set()
    unique = []
    for p in resolved:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    if not unique:
        raise ValueError("No input images found.")
    return unique

def flatten_alpha_to_bg(img: Image.Image, bg_rgb: Tuple[int, int, int]) -> Image.Image:
    """
    Remove alpha by compositing the image over a solid background color.

    Args:
        img: PIL image (any mode).
        bg_rgb: Background color as (R, G, B).

    Returns:
        RGB image without alpha.
    """
    if img.mode in ("RGBA", "LA") or ("transparency" in img.info):
        rgb = Image.new("RGB", img.size, bg_rgb)
        return Image.alpha_composite(rgb.convert("RGBA"), img.convert("RGBA")).convert("RGB")
    return img.convert("RGB")

def prepare_frame(
    path: Path,
    size: Optional[Tuple[int, int]],
    keep_aspect: bool,
    background: Tuple[int, int, int],
) -> Image.Image:
    """
    Load an image, optionally resize, remove alpha, and quantize for GIF.

    Args:
        path: Image file path.
        size: Target (width, height) or None to keep original size.
        keep_aspect: If True, fit within size and pad; otherwise stretch to size.
        background: Background color used when removing alpha and padding.

    Returns:
        Palette-mode image suitable for GIF.
    """
    with Image.open(path) as im:
        im = im.convert("RGBA")
        if size is not None:
            if keep_aspect:
                # Fit inside the target while preserving aspect, then pad
                fitted = ImageOps.contain(im, size, Image.Resampling.LANCZOS)
                canvas = Image.new("RGBA", size, background + (255,))
                x = (size[0] - fitted.width) // 2
                y = (size[1] - fitted.height) // 2
                canvas.paste(fitted, (x, y))
                im = canvas
            else:
                im = im.resize(size, Image.Resampling.LANCZOS)
        # Remove alpha and quantize to 256 colors for GIF
        im_rgb = flatten_alpha_to_bg(im, background)
        im_p = im_rgb.quantize(colors=256, method=QUANTIZE_METHOD)
        return im_p

def create_gif(
    image_paths: Iterable[Path],
    output_path: Path,
    duration_ms: int,
    size: Optional[Tuple[int, int]],
    keep_aspect: bool,
    loop: int,
    background: Tuple[int, int, int],
) -> None:
    """
    Build an animated GIF from a sequence of images.

    Args:
        image_paths: Iterable of image file paths in desired order.
        output_path: Output GIF file path.
        duration_ms: Frame duration in milliseconds.
        size: Optional (width, height) to resize frames. If None, first image size is used.
        keep_aspect: Preserve aspect ratio with padding when resizing.
        loop: Number of loops; 0 means infinite.
        background: RGB tuple used for alpha removal and padding.

    Raises:
        ValueError: If fewer than two frames are provided.
    """
    paths = list(image_paths)
    if len(paths) < 2:
        raise ValueError("At least two images are required to create a GIF.")

    frames = [prepare_frame(p, size, keep_aspect, background) for p in paths]

    # If no size was specified, unify to the size of the first prepared frame
    if size is None:
        target_size = frames[0].size
        frames = [f if f.size == target_size else f.resize(target_size, Image.Resampling.NEAREST) for f in frames]

    output_path = output_path.with_suffix(".gif")
    first, rest = frames[0], frames[1:]
    first.save(
        output_path,
        save_all=True,
        append_images=rest,
        duration=duration_ms,
        loop=loop,
        optimize=True,
        disposal=2,
    )

def build_arg_parser() -> argparse.ArgumentParser:
    """
    Build the command-line argument parser.

    Returns:
        Configured ArgumentParser.
    """
    p = argparse.ArgumentParser(description="Create an animated GIF from images.")
    p.add_argument(
        "images",
        nargs="*",
        help="Image files or directories. If omitted, a GUI picker will open.",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path("out.gif"),
        help="Output GIF file path. Default: out.gif",
    )
    p.add_argument(
        "--duration-ms",
        type=int,
        default=100,
        help="Frame duration in milliseconds. Default: 100 (10 fps).",
    )
    p.add_argument(
        "--size",
        type=str,
        default=None,
        help='Resize frames to WIDTHxHEIGHT. Example: "800x600".',
    )
    p.add_argument(
        "--keep-aspect",
        action="store_true",
        help="Preserve aspect ratio and pad to target size with background.",
    )
    p.add_argument(
        "--bg",
        type=str,
        default="ffffff",
        help='Background color as 6-digit hex RGB used for alpha removal and padding. Default: "ffffff".',
    )
    p.add_argument(
        "--loop",
        type=int,
        default=0,
        help="Number of loops; 0 means infinite. Default: 0.",
    )
    return p

def parse_bg_hex(hex_rgb: str) -> Tuple[int, int, int]:
    """
    Parse a 6-digit hex RGB color string into an (R, G, B) tuple.

    Args:
        hex_rgb: Hex color without "#", e.g., "ffffff" or "000000".

    Returns:
        RGB tuple.

    Raises:
        ValueError: If the input is not 6 hex digits.
    """
    s = hex_rgb.strip().lower().lstrip("#")
    if len(s) != 6 or any(c not in "0123456789abcdef" for c in s):
        raise ValueError('Background must be a 6-digit hex RGB string like "ffffff".')
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def main() -> None:
    """
    Entry point for the CLI.
    """
    args = build_arg_parser().parse_args()
    size = parse_size(args.size)
    bg = parse_bg_hex(args.bg)

    if args.images:
        paths = discover_images(args.images)
    else:
        with select_images_via_gui_ctx() as selected:
            paths = selected

    if not paths:
        raise ValueError("No images selected.")

    # Stable alphabetical order unless user chose files manually via GUI
    if args.images:
        paths = sorted(paths, key=lambda p: str(p))

    create_gif(
        image_paths=paths,
        output_path=args.output,
        duration_ms=args.duration_ms,
        size=size,
        keep_aspect=args.keep_aspect,
        loop=args.loop,
        background=bg,
    )
    print(f"GIF written to: {args.output.with_suffix('.gif')}")


if __name__ == "__main__":
    main()
