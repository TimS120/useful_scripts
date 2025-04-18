#!/usr/bin/env python3
"""
Interactive image cropping tool.
Select the Crop Region
    Click two points on the image to mark the opposite corners of the desired crop region.
    If you make a mistake, press 'r' to reset your selection.
    After selecting two points, the script will automatically crop the image and save it in the same directory with the filename modified by appending "_cut" before the file extension.
    You can also press 'q' to quit without cropping.
    
Usage:
    python crop_image.py <image_path>
"""

import cv2
import sys
import os

# Global list to store the two selected points
refPt = []


def click_and_crop(event, x, y, flags, param):
    """
    Mouse callback function that records two left-button clicks and draws
    a circle and a rectangle on the image.
    """
    global refPt, image, clone

    if event == cv2.EVENT_LBUTTONDOWN:
        refPt.append((x, y))
        cv2.circle(image, (x, y), 3, (0, 255, 0), -1)
        cv2.imshow("Image", image)

        if len(refPt) == 2:
            cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 2)
            cv2.imshow("Image", image)


def main():
    """
    Main function to load an image, handle user input for cropping,
    and save the cropped image.
    """
    global image, clone, refPt

    if len(sys.argv) < 2:
        print("Usage: python crop_image.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Unable to load image \"{image_path}\"")
        sys.exit(1)

    clone = image.copy()

    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", click_and_crop)

    print("[INFO] Click two points in the image to define the crop region.")
    print("       Press 'r' to reset your selection, or 'q' to quit.")

    while True:
        cv2.imshow("Image", image)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("r"):
            image = clone.copy()
            refPt = []
            print("[INFO] Selection reset. Click two new points.")
        elif key == ord("q"):
            print("[INFO] Quitting without cropping.")
            cv2.destroyAllWindows()
            sys.exit(0)
        if len(refPt) == 2:
            break

    if len(refPt) == 2:
        (x1, y1), (x2, y2) = refPt
        x_min, x_max = sorted([x1, x2])
        y_min, y_max = sorted([y1, y2])

        cropped = clone[y_min:y_max, x_min:x_max]

        base, ext = os.path.splitext(image_path)
        new_filename = base + "_cut" + ext

        cv2.imwrite(new_filename, cropped)
        print(f"[INFO] Cropped image saved as \"{new_filename}\"")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
