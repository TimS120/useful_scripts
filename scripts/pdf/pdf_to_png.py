#!/usr/bin/env python3
"""
PDF to PNG converter using PyMuPDF library.

This script converts each page of a given PDF file into a PNG image.
Each page is saved as a separate PNG file (1.png, 2.png, ...).
The PNGs are stored in a new folder with the same name as the PDF file
(without extension), located next to the input PDF.

Usage:
    python pdf_to_png.py input.pdf [dpi]
    - input.pdf: Path to the PDF file.
    - dpi (optional): Desired resolution in DPI (default: 150).
"""

import sys
from pathlib import Path
import fitz  # PyMuPDF


def pdf_to_png(pdf_path: str, dpi: int = 150) -> None:
    """
    Convert a PDF into PNG images, one image per page.

    Args:
        pdf_path (str): Path to the input PDF file.
        dpi (int): Resolution in DPI. Default is 150.
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    output_dir = pdf_file.with_suffix("")
    output_dir.mkdir(exist_ok=True)

    zoom = dpi / 72  # 72 DPI is the default resolution in PDFs
    mat = fitz.Matrix(zoom, zoom)

    doc = fitz.open(str(pdf_file))
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=mat)
        output_file = output_dir / f"{i}.png"
        pix.save(str(output_file))
        print(f"Saved {output_file} at {dpi} DPI")
    doc.close()


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python pdf_to_png.py input.pdf [dpi]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    dpi = int(sys.argv[2]) if len(sys.argv) == 3 else 150
    pdf_to_png(input_pdf, dpi)
