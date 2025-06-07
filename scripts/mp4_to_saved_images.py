#!/usr/bin/env python3
"""Extract frames from an MP4 file into an output folder.

Usage:
    python mp4_to_saved_images.py <video_path> <output_folder> [--step N] [--rotate DEG]
"""

import argparse
import os
import sys

import cv2


def parse_args():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments with attributes
            `video_path`, `output_folder`, `step`, and `rotate`.
    """
    parser = argparse.ArgumentParser(
        description="Extract (and optionally rotate) frames from an MP4 file."
    )
    parser.add_argument(
        "video_path",
        help="Path to the MP4 video file"
    )
    parser.add_argument(
        "output_folder",
        help="Path to the folder where extracted frames will be saved"
    )
    parser.add_argument(
        "-s", "--step",
        type=int,
        default=1,
        help="Save every Nth frame (default: 1)"
    )
    parser.add_argument(
        "-r", "--rotate",
        type=int,
        default=0,
        choices=[-270, -180, -90, 0, 90, 180, 270],
        help=(
            "Rotate frames by DEG degrees. "
            "+90 = turn right (clockwise), -90 = turn left (counter-clockwise). "
            "180 flips upside down; 270 is 3x90."
        )
    )
    return parser.parse_args()


def extract_frames(
    video_path: str,
    output_folder: str,
    step: int = 1,
    rotate: int = 0
) -> int:
    """
    Extract frames from the specified video file, optionally rotating and saving only every Nth frame.

    Args:
        video_path (str): Path to the MP4 video file.
        output_folder (str): Path to save frames.
        step (int): Save every Nth frame. Defaults to 1.
        rotate (int): Rotation in degrees; positive = clockwise,
            negative = counter-clockwise. Must be +-90, 180 or 270.
            Defaults to 0 (no rotation).

    Returns:
        int: Number of frames saved.
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

    # Map requested rotation to OpenCV codes
    rotation_map = {
        90: cv2.ROTATE_90_CLOCKWISE,
        -270: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        -180: cv2.ROTATE_180,
        -90: cv2.ROTATE_90_COUNTERCLOCKWISE,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE
    }

    frame_idx = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Rotate if requested
        if rotate in rotation_map:
            frame = cv2.rotate(frame, rotation_map[rotate])

        # Save only every Nth frame
        if frame_idx % step == 0:
            filename = os.path.join(
                output_folder,
                f"frame_{saved_count:06d}.png"
            )
            cv2.imwrite(filename, frame)
            saved_count += 1

        frame_idx += 1

    cap.release()
    return saved_count


def main() -> None:
    """Entry point for the frame extraction script."""
    args = parse_args()
    count = extract_frames(
        args.video_path,
        args.output_folder,
        args.step,
        args.rotate
    )
    print(f"Extracted {count} frames to '{args.output_folder}'.")


if __name__ == "__main__":
    main()
