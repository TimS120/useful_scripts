#!/usr/bin/env python3
"""
Resize images to fit within Full HD (1920x1080) resolution while maintaining aspect ratio.

Usage:
    python resize_image.py <input_path> <output_path>
"""

import argparse

from PIL import Image


def resize_image(input_path, output_path, max_width=1920, max_height=1080):
    """
    Resize the input image while maintaining aspect ratio.

    Parameters:
        input_path (str): Path to the source image file.
        output_path (str): Path where the resized image will be saved.
        max_width (int): Maximum width of the resized image.
        max_height (int): Maximum height of the resized image.
    """
    img = Image.open(input_path)
    img.thumbnail((max_width, max_height), Image.ANTIALIAS)
    img.save(output_path)


def parse_arguments():
    """
    Parse and return command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments with 'input' and 'output' attributes.
    """
    parser = argparse.ArgumentParser(
        description="Resize an image to fit within Full HD (1920x1080) while keeping aspect ratio."
    )
    parser.add_argument(
        "input",
        help="Path to the input image"
    )
    parser.add_argument(
        "output",
        help="Path to save the resized image"
    )
    return parser.parse_args()


def main():
    """Execute the image resizing."""
    args = parse_arguments()
    resize_image(args.input, args.output)
    print(f"Resized image saved as: {args.output}")


if __name__ == "__main__":
    main()
