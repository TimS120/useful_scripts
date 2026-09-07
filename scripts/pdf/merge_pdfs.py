"""Merge PDF files into one PDF, in the order given on the command line.

Usage:
    python merge_pdfs.py OUTPUT_PDF INPUT_PDF [INPUT_PDF ...]

Example:
    python merge_pdfs.py combined.pdf first.pdf second.pdf third.pdf
"""

import argparse
import sys
from pathlib import Path

try:
    import fitz
except ModuleNotFoundError:
    print(
        "PyMuPDF is required. Install it with: python -m pip install PyMuPDF",
        file=sys.stderr,
    )
    raise SystemExit(1)


def merge_pdfs(input_paths: list[Path], output_path: Path) -> int:
    """Append all pages from *input_paths* to a newly created PDF.

    Returns:
        The number of pages written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    merged_document = fitz.open()
    page_count = 0
    try:
        for input_path in input_paths:
            source_document = fitz.open(input_path)
            try:
                merged_document.insert_pdf(source_document)
                page_count += source_document.page_count
            finally:
                source_document.close()

        merged_document.save(output_path)
    finally:
        merged_document.close()

    return page_count


def parse_arguments() -> argparse.Namespace:
    """Parse and validate command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Merge PDF files into one PDF in the given order.",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Path for the merged PDF.",
    )
    parser.add_argument(
        "input_paths",
        nargs="+",
        type=Path,
        metavar="INPUT_PDF",
        help="PDF files to append, in order.",
    )
    arguments = parser.parse_args()

    if arguments.output_path.suffix.lower() != ".pdf":
        parser.error("OUTPUT_PDF must have a .pdf extension")

    output_path = arguments.output_path.resolve()
    for input_path in arguments.input_paths:
        if not input_path.is_file():
            parser.error(f"Input file not found: {input_path}")
        if input_path.suffix.lower() != ".pdf":
            parser.error(f"Input file must have a .pdf extension: {input_path}")
        if input_path.resolve() == output_path:
            parser.error("The output path must not overwrite an input PDF")

    return arguments


def main() -> None:
    """Merge the specified PDFs and report the result."""
    arguments = parse_arguments()
    page_count = merge_pdfs(arguments.input_paths, arguments.output_path)
    print(
        f'Merged {len(arguments.input_paths)} PDF(s), {page_count} page(s), '
        f'into "{arguments.output_path}"'
    )


if __name__ == "__main__":
    main()
