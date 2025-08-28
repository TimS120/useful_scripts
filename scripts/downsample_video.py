#!/usr/bin/env python3
"""Downsamples the 4k video into a full hd video. The resulting video will be saved next to the input video as <input_video>_output.<input_video_extension>

Usage:
    python downsample_video.py <video_path>
"""

import cv2
import os
import argparse

def parse_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Downsample stated video from 4k to full hd (1920x1080)"
    )
    parser.add_argument(
        "video_path",
        help="Path to the MP4 video file"
    )
    return parser.parse_args()

def downscale_video(input_path: str) -> None:
    """
    Downscale a 4K video to Full HD (1920x1080) using OpenCV.

    Parameters
    ----------
    input_path : str
        Path to the input video file.
    output_path : str
        Path where the output Full HD video will be saved.
    """
    folder, filename = os.path.split(input_path)
    name, ext = os.path.splitext(filename)
    output_video = os.path.join(folder, f"{name}_output{ext}")

    # Open input video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video file {input_path}")

    # Get original properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # Codec for mp4

    # Set output writer with Full HD resolution
    out = cv2.VideoWriter(output_video, fourcc, fps, (1920, 1080))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize frame to Full HD
        resized_frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_AREA)

        # Write to output video
        out.write(resized_frame)

    cap.release()
    out.release()
    print(f"Video successfully downscaled to {output_video}")


if __name__ == "__main__":
    args = parse_args()

    print(f"Starting conversion of video {args.video_path}")
    downscale_video(args.video_path)
    print(f"Video conversion completed")
