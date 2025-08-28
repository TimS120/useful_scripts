#!/usr/bin/env python3
"""
Interactive image cropping tool with scalable preview and adjustable crop corners.

This tool displays the image scaled to fit within a maximum preview of
1800 px width and 800 px height without distortion, preserving aspect ratio.
You can click two points to define opposite corners of the crop rectangle.
After the initial selection, each corner can be moved by dragging it.

Controls:
- Left click: set a corner if fewer than two exist, or grab a nearby corner to move it
- Drag: move the grabbed corner
- 'r': reset selection
- 'c' or Enter: confirm and save crop (saved as "<name>_cut<ext>" next to the original)
- 'q' or ESC: quit without saving

Usage:
    python crop_image.py <image_path>
"""

import os
import sys
from typing import List, Optional, Tuple

import cv2
import numpy as np


# Display constraints
MAX_PREVIEW_WIDTH = 1800
MAX_PREVIEW_HEIGHT = 900
HANDLE_RADIUS = 8


# Globals shared with callbacks
orig_image: Optional[np.ndarray] = None
preview_image: Optional[np.ndarray] = None
preview_scale: float = 1.0
points_preview: List[Tuple[int, int]] = []
active_idx: Optional[int] = None
dragging: bool = False


def compute_preview(image: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Compute a preview image scaled to fit within MAX_PREVIEW_WIDTH x MAX_PREVIEW_HEIGHT.

    The aspect ratio is preserved. Images smaller than the maximum box are not upscaled.

    Args:
        image: Input image in BGR format.

    Returns:
        A tuple of (preview_image, scale), where scale = preview_size / original_size.
    """
    h, w = image.shape[:2]
    scale_w = min(MAX_PREVIEW_WIDTH / float(w), 1.0)
    scale_h = min(MAX_PREVIEW_HEIGHT / float(h), 1.0)
    scale = min(scale_w, scale_h)
    if scale < 1.0:
        new_w = int(round(w * scale))
        new_h = int(round(h * scale))
        preview = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        preview = image.copy()
    return preview, scale


def preview_to_orig(pt: Tuple[int, int], scale: float) -> Tuple[int, int]:
    """
    Convert a point from preview coordinates to original image coordinates.

    Args:
        pt: Point in preview coordinates (x, y).
        scale: Preview scale factor.

    Returns:
        Corresponding point in original image coordinates (x, y).
    """
    if scale <= 0:
        return pt
    x = int(round(pt[0] / scale))
    y = int(round(pt[1] / scale))
    return x, y


def draw_overlay() -> None:
    """
    Redraw the preview window with current selection overlay.
    Handles and rectangle are always visible if defined.
    """
    assert preview_image is not None
    canvas = preview_image.copy()

    if len(points_preview) > 0:
        for idx, (x, y) in enumerate(points_preview):
            cv2.circle(canvas, (x, y), HANDLE_RADIUS, (0, 255, 0), -1)
            if idx == active_idx:
                cv2.circle(canvas, (x, y), HANDLE_RADIUS + 3, (0, 200, 255), 1)

    if len(points_preview) == 2:
        p1 = points_preview[0]
        p2 = points_preview[1]
        cv2.rectangle(canvas, p1, p2, (0, 255, 0), 2)

    cv2.imshow("Image", canvas)


def find_near_handle(x: int, y: int) -> Optional[int]:
    """
    Find index of a handle that is within HANDLE_RADIUS*2 from (x, y).

    Args:
        x: X coordinate in preview space.
        y: Y coordinate in preview space.

    Returns:
        Index of the nearby handle if found, else None.
    """
    for idx, (hx, hy) in enumerate(points_preview):
        if (x - hx) ** 2 + (y - hy) ** 2 <= (HANDLE_RADIUS * 2) ** 2:
            return idx
    return None


def clamp_point_to_image(x: int, y: int, img: np.ndarray) -> Tuple[int, int]:
    """
    Clamp a point to be inside the given image boundaries.

    Args:
        x: X coordinate.
        y: Y coordinate.
        img: Image whose bounds to clamp to.

    Returns:
        Clamped (x, y).
    """
    h, w = img.shape[:2]
    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))
    return x, y


def click_and_crop(event: int, x: int, y: int, flags: int, param: object) -> None:
    """
    Mouse callback to create and adjust crop corners.

    Behavior:
    - If fewer than two points exist, left-click adds a point.
    - If two points exist, left-click near a handle to grab it, then drag to move.
    - Releasing the button drops the handle.
    """
    global points_preview, active_idx, dragging

    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points_preview) < 2:
            x, y = clamp_point_to_image(x, y, preview_image)
            points_preview.append((x, y))
            active_idx = len(points_preview) - 1
            dragging = True
        else:
            idx = find_near_handle(x, y)
            if idx is not None:
                active_idx = idx
                dragging = True

    elif event == cv2.EVENT_MOUSEMOVE:
        if dragging and active_idx is not None:
            x, y = clamp_point_to_image(x, y, preview_image)
            points_preview[active_idx] = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        dragging = False
        active_idx = None


def save_cropped(image_path: str) -> bool:
    """
    Save the cropped region based on points in preview space.

    Args:
        image_path: Path to the original image.

    Returns:
        True if a crop was saved, False otherwise.
    """
    if len(points_preview) != 2:
        print("[WARN] Need exactly two points to crop.")
        return False

    assert orig_image is not None

    p1o = preview_to_orig(points_preview[0], preview_scale)
    p2o = preview_to_orig(points_preview[1], preview_scale)

    x1, y1 = p1o
    x2, y2 = p2o
    x_min, x_max = sorted([x1, x2])
    y_min, y_max = sorted([y1, y2])

    h, w = orig_image.shape[:2]
    x_min = max(0, min(x_min, w - 1))
    x_max = max(0, min(x_max, w))
    y_min = max(0, min(y_min, h - 1))
    y_max = max(0, min(y_max, h))

    if x_max <= x_min or y_max <= y_min:
        print("[ERROR] Invalid crop region. No image saved.")
        return False

    cropped = orig_image[y_min:y_max, x_min:x_max]
    base, ext = os.path.splitext(image_path)
    new_filename = base + "_cut" + ext
    ok = cv2.imwrite(new_filename, cropped)
    if ok:
        print(f"[INFO] Cropped image saved as \"{new_filename}\"")
    else:
        print("[ERROR] Failed to write the cropped image.")
    return ok


def get_screen_size() -> Optional[Tuple[int, int]]:
    """
    Obtain the primary screen size. Returns None if unavailable.

    Tkinter is used for broad cross-platform support. If Tkinter is not
    installed, centering is skipped gracefully.
    """
    try:
        import tkinter as tk  # noqa: WPS433 (local import intentional)
        root = tk.Tk()
        root.withdraw()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.destroy()
        return int(sw), int(sh)
    except Exception:
        return None


def center_window(win_name: str, win_w: int, win_h: int) -> None:
    """
    Center the OpenCV window on screen if screen size can be determined.

    Args:
        win_name: OpenCV window name.
        win_w: Window width in pixels.
        win_h: Window height in pixels.
    """
    size = get_screen_size()
    if size is None:
        return
    sw, sh = size
    x = max((sw - win_w) // 2, 0)
    y = max((sh - win_h) // 2, 0)
    cv2.moveWindow(win_name, x, y)


def main() -> None:
    """
    Entry point that loads the image, shows a scalable preview, and handles user input.
    """
    global orig_image, preview_image, preview_scale, points_preview

    if len(sys.argv) < 2:
        print("Usage: python crop_image.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    orig_image = cv2.imread(image_path)

    if orig_image is None:
        print(f"Error: Unable to load image \"{image_path}\"")
        sys.exit(1)

    preview_image, preview_scale = compute_preview(orig_image)

    cv2.namedWindow("Image", cv2.WINDOW_NORMAL)

    # Tight window fit and centering
    ph, pw = preview_image.shape[:2]
    cv2.resizeWindow("Image", pw, ph)
    center_window("Image", pw, ph)

    cv2.setMouseCallback("Image", click_and_crop)

    print("[INFO] Click two points to define opposite corners of the crop region.")
    print("[INFO] Drag a corner to adjust it. Press 'r' to reset.")
    print("[INFO] Press 'c' or Enter to crop and save. Press 'q' or ESC to quit.")

    while True:
        # Persistent overlay rendering (handles visible even when not clicking)
        draw_overlay()

        key = cv2.waitKey(10) & 0xFF

        if key in (ord("q"), 27):
            print("[INFO] Quitting without cropping.")
            cv2.destroyAllWindows()
            sys.exit(0)

        if key == ord("r"):
            points_preview = []
            print("[INFO] Selection reset. Click two new points.")

        if key in (ord("c"), 13, 10):  # 'c' or Enter
            if save_cropped(image_path):
                cv2.destroyAllWindows()
                sys.exit(0)
            # If saving failed, remain in loop for correction


if __name__ == "__main__":
    main()
