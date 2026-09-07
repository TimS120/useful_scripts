"""Extract one page from a PDF and save it as a separate PDF.

Usage:
    python extract_pdf_page.py INPUT_PDF PAGE_NUMBER OUTPUT_PDF

PAGE_NUMBER is one-based. For example, page 1 selects the first PDF page.
"""

import argparse
from pathlib import Path

import fitz


def extract_pdf_page(
    input_path: Path,
    page_number: int,
    output_path: Path,
) -> None:
    """Extract one page from a PDF into a new PDF.

    Args:
        input_path: Path to the source PDF.
        page_number: One-based number of the page to extract.
        output_path: Path for the resulting PDF.

    Raises:
        ValueError: If the requested page does not exist.
    """
    source_document = fitz.open(input_path)

    if page_number > source_document.page_count:
        page_count = source_document.page_count
        source_document.close()
        raise ValueError(
            f"Page {page_number} does not exist. "
            f"The PDF contains {page_count} pages."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    target_document = fitz.open()
    target_document.insert_pdf(
        source_document,
        from_page=page_number - 1,
        to_page=page_number - 1,
    )
    target_document.save(output_path)

    target_document.close()
    source_document.close()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract one page from a PDF into a separate PDF.",
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to the source PDF.",
    )
    parser.add_argument(
        "page_number",
        type=int,
        help="One-based page number to extract.",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Path for the resulting PDF.",
    )
    arguments = parser.parse_args()

    if not arguments.input_path.is_file():
        parser.error(f"Input file not found: {arguments.input_path}")

    if arguments.input_path.suffix.lower() != ".pdf":
        parser.error("Input file must have a .pdf extension")

    if arguments.output_path.suffix.lower() != ".pdf":
        parser.error("Output file must have a .pdf extension")

    if arguments.page_number <= 0:
        parser.error("PAGE_NUMBER must be a positive integer")

    if arguments.input_path.resolve() == arguments.output_path.resolve():
        parser.error("Input and output paths must be different")

    return arguments


def main() -> None:
    """Extract the requested PDF page."""
    arguments = parse_arguments()

    extract_pdf_page(
        input_path=arguments.input_path,
        page_number=arguments.page_number,
        output_path=arguments.output_path,
    )

    print(
        f"Extracted page {arguments.page_number} to "
        f"\"{arguments.output_path}\""
    )


if __name__ == "__main__":
    main()
