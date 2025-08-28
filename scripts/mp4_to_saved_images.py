#!/usr/bin/env python3
"""
Extract frames from an MP4 file into an output folder efficiently.

Usage:
    python mp4_to_saved_images.py <video_path> <output_folder>
                                  [--step N]
                                  [--rotate DEG]
                                  [--ext {jpg,png}]
                                  [--jpeg-quality Q]
                                  [--png-compression C]
                                  [--threads T]
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import List

import cv2


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments including video/output paths and performance options.
    """
    parser = argparse.ArgumentParser(
        description="Extract (and optionally rotate) frames from an MP4 file."
    )
    parser.add_argument("video_path", help="Path to the MP4 video file")
    parser.add_argument("output_folder", help="Folder where extracted frames will be saved")
    parser.add_argument(
        "-s",
        "--step",
        type=int,
        default=1,
        help="Save every Nth frame (default: 1)",
    )
    parser.add_argument(
        "-r",
        "--rotate",
        type=int,
        default=0,
        choices=[-270, -180, -90, 0, 90, 180, 270],
        help=(
            "Rotate frames by DEG degrees. "
            "+90 = clockwise, -90 = counter-clockwise, 180 = upside down."
        ),
    )
    parser.add_argument(
        "--ext",
        choices=["jpg", "png"],
        default="jpg",
        help="Output image format (default: jpg).",
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=92,
        help="JPEG quality 1..100 (default: 92). Higher = better quality, slower.",
    )
    parser.add_argument(
        "--png-compression",
        type=int,
        default=1,
        help="PNG compression 0..9 (default: 1). 0 = fastest, 9 = smallest files.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=0,
        help="Number of worker threads for disk writes (0 = synchronous).",
    )
    return parser.parse_args()


def _imwrite_params(ext: str, jpeg_quality: int, png_compression: int) -> List[int]:
    """
    Build cv2.imwrite parameter list based on output format.

    Args:
        ext (str): "jpg" or "png".
        jpeg_quality (int): JPEG quality 1..100.
        png_compression (int): PNG compression 0..9.

    Returns:
        List[int]: Parameter list for cv2.imwrite.
    """
    if ext == "jpg":
        return [cv2.IMWRITE_JPEG_QUALITY, int(jpeg_quality)]
    return [cv2.IMWRITE_PNG_COMPRESSION, int(png_compression)]


def extract_frames(
    video_path: str,
    output_folder: str,
    step: int = 1,
    rotate: int = 0,
    ext: str = "jpg",
    jpeg_quality: int = 92,
    png_compression: int = 1,
    threads: int = 0,
) -> int:
    """
    Extract frames from the specified video, rotating and saving only every Nth frame.

    Uses VideoCapture.grab() to skip frames cheaply and retrieve() only when needed.

    Args:
        video_path (str): Path to the MP4 video file.
        output_folder (str): Path to save frames.
        step (int): Save every Nth frame (>=1).
        rotate (int): Rotation in degrees; positive = clockwise, negative = counter-clockwise.
        ext (str): Output extension, "jpg" or "png".
        jpeg_quality (int): JPEG quality 1..100.
        png_compression (int): PNG compression 0..9.
        threads (int): Number of writer threads (0 = synchronous).

    Returns:
        int: Number of frames saved.
    """
    if not os.path.isfile(video_path):
        print("Error: The specified video file does not exist")
        sys.exit(1)

    os.makedirs(output_folder, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open the video file")
        sys.exit(1)

    rotation_map = {
        90: cv2.ROTATE_90_CLOCKWISE,
        -270: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        -180: cv2.ROTATE_180,
        -90: cv2.ROTATE_90_COUNTERCLOCKWISE,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }

    step = max(1, int(step))
    params = _imwrite_params(ext, jpeg_quality, png_compression)

    saved_count = 0
    frame_idx = 0

    executor = ThreadPoolExecutor(max_workers=threads) if threads > 0 else None
    pending = []

    try:
        while True:
            grabbed = cap.grab()
            if not grabbed:
                break

            if frame_idx % step == 0:
                ok, frame = cap.retrieve()
                if not ok:
                    break

                if rotate in rotation_map:
                    frame = cv2.rotate(frame, rotation_map[rotate])

                filename = os.path.join(output_folder, f"frame_{saved_count:06d}.{ext}")
                if executor is not None:
                    # Copy to decouple from buffer reused by OpenCV.
                    pending.append(executor.submit(cv2.imwrite, filename, frame.copy(), params))
                else:
                    cv2.imwrite(filename, frame, params)
                saved_count += 1

            frame_idx += 1
    finally:
        cap.release()
        if executor is not None:
            for f in pending:
                f.result()
            executor.shutdown(wait=True)

    return saved_count


def main() -> None:
    """Entry point for the frame extraction script."""
    args = parse_args()
    count = extract_frames(
        args.video_path,
        args.output_folder,
        args.step,
        args.rotate,
        args.ext,
        args.jpeg_quality,
        args.png_compression,
        args.threads,
    )
    print(f"Extracted {count} frames to '{args.output_folder}'.")
    

if __name__ == "__main__":
    main()
