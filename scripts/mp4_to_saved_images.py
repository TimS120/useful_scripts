#!/usr/bin/env python3
"""Extract frames from an MP4 file into an output folder.

Usage:
    python mp4_to_saved_images.py <video_path> <output_folder>
"""

import os
import sys
import argparse
import cv2


def parse_args():
    """
    Parse command‑line arguments.

    Returns:
        argparse.Namespace: Parsed arguments with attributes `video_path` and `output_folder`
    """
    parser = argparse.ArgumentParser(
        description="Extract frames from a given MP4 file into an output folder."
    )
    parser.add_argument(
        "video_path",
        help="Path to the MP4 video file"
    )
    parser.add_argument(
        "output_folder",
        help="Path to the folder where extracted frames will be saved"
    )
    return parser.parse_args()


def extract_frames(video_path: str, output_folder: str) -> int:
    """
    Extract all frames from the specified video file and save them as PNG images.

    Args:
        video_path (str): Path to the MP4 video file
        output_folder (str): Path to the folder where frames will be saved

    Returns:
        int: Number of frames extracted
    """
    if not os.path.isfile(video_path):
        print("Error: The specified video file does not exist")
        sys.exit(1)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open the video file")
        sys.exit(1)

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        filename = os.path.join(
            output_folder,
            f"frame_{frame_count:06d}.png"
        )
        cv2.imwrite(filename, frame)
        frame_count += 1

    cap.release()
    return frame_count


def main() -> None:
    """
    Entry point for the frame extraction script.
    """
    args = parse_args()
    count = extract_frames(args.video_path, args.output_folder)
    print(f"Extracted {count} frames to '{args.output_folder}'.")


if __name__ == "__main__":
    main()
