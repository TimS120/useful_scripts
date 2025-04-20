#!/usr/bin/env python3
# Script to crop an image by fixed pixels and save it

"""
Crop an image by a certain amount of pixels at every side.
The cropped image will be saved beside the input image with
the name <input_image>_cropped.<file_extension>

Usage: python3 crop_image.py path/to/your/image.jpg
"""

import os
import argparse
from PIL import Image

crop_left = 0
crop_right = 0
crop_bottom = 0
crop_top = 0

def crop_image(input_path):
    """
    Crop the image by 5 pixels at the top, 4 pixels at the left,
    7 pixels at the right, and 1 pixel at the bottom.
    """
    image = Image.open(input_path)
    width, height = image.size
    left = crop_left
    top = crop_top
    right = width - crop_right
    bottom = height - crop_bottom
    cropped = image.crop((left, top, right, bottom))
    return cropped

def save_cropped_image(image, input_path):
    """
    Save the cropped image beside the input image
    with the name <input_image>_cropped.<file_extension>.
    """
    directory, filename = os.path.split(input_path)
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}_cropped{ext}"
    output_path = os.path.join(directory, output_filename)
    image.save(output_path)
    print(f"Saved cropped image to {output_path}")

def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Crop an image by fixed pixel amounts."
    )
    parser.add_argument(
        "input_image",
        help="Path to the input image file"
    )
    return parser.parse_args()

def main():
    """
    Main function to execute the cropping operation.
    """
    args = parse_arguments()
    cropped_image = crop_image(args.input_image)
    save_cropped_image(cropped_image, args.input_image)

if __name__ == "__main__":
    main()

