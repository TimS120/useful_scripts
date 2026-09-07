import argparse
import sys
from pathlib import Path

import pymupdf as fitz


def extract_images(pdf_path: Path) -> None:
    doc = fitz.open(pdf_path)
    output_dir = pdf_path.parent
    count = 0

    for page_index, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            output_path = output_dir / f"page{page_index + 1}_img{img_index + 1}.{ext}"
            output_path.write_bytes(image_bytes)
            print(f"Saved: {output_path}")
            count += 1

    print(f"\n{count} image(s) extracted from '{pdf_path.name}'.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract all images from a PDF and save them next to the PDF file."
    )
    parser.add_argument("pdf", type=Path, help="Path to the input PDF file.")
    args = parser.parse_args()

    pdf_path: Path = args.pdf.resolve()
    if not pdf_path.is_file():
        print(f"Error: '{pdf_path}' is not a file.", file=sys.stderr)
        sys.exit(1)
    if pdf_path.suffix.lower() != ".pdf":
        print(f"Error: '{pdf_path}' does not appear to be a PDF.", file=sys.stderr)
        sys.exit(1)

    extract_images(pdf_path)


if __name__ == "__main__":
    main()
