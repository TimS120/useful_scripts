"""Convert PowerPoint presentations or PDFs into high-resolution PNG images.

Usage:
    python powerpoint_to_high_res_images.py INPUT_FILE OUTPUT_DIRECTORY [--dpi DPI]
        [--keep-pdf]

``INPUT_FILE`` can be a ``.ppt``, ``.pptx``, or ``.pdf`` file.  PowerPoint
files are first exported to PDF through Microsoft PowerPoint, then every PDF
page is rendered as ``slide_001.png``, ``slide_002.png``, and so on in
``OUTPUT_DIRECTORY``.  PDF files skip the PowerPoint export and their pages
are rendered directly.  ``--dpi`` controls image resolution (default: 300).

For PowerPoint input, ``--keep-pdf`` also saves the intermediate PDF in the
output directory.  It has no effect for PDF input, whose original file is
never changed or removed.  PowerPoint must be installed only when converting
PowerPoint files.
"""

import argparse
import os
from pathlib import Path
import tempfile

import fitz
import win32com.client


PDF_FORMAT = 32


def export_powerpoint_to_pdf(
    presentation_path: Path,
    pdf_path: Path,
) -> None:
    """Export a PowerPoint presentation to PDF using Microsoft PowerPoint.

    Args:
        presentation_path: Path to the PowerPoint presentation.
        pdf_path: Destination path for the exported PDF.
    """
    powerpoint = win32com.client.DispatchEx("PowerPoint.Application")
    powerpoint.Visible = True

    presentation = powerpoint.Presentations.Open(
        str(presentation_path.resolve()),
        WithWindow=False,
    )

    presentation.SaveAs(str(pdf_path.resolve()), PDF_FORMAT)
    presentation.Close()
    powerpoint.Quit()


def render_pdf_slides(
    pdf_path: Path,
    output_directory: Path,
    dpi: int = 300,
) -> None:
    """Render all pages of a PDF as high-resolution PNG images.

    Args:
        pdf_path: Path to the PDF.
        output_directory: Directory for the resulting images.
        dpi: Output resolution in dots per inch.
    """
    output_directory.mkdir(parents=True, exist_ok=True)

    document = fitz.open(pdf_path)

    for page_number, page in enumerate(document, start=1):
        pixmap = page.get_pixmap(dpi=dpi, alpha=False)
        output_path = output_directory / f"slide_{page_number:03d}.png"
        pixmap.save(output_path)

    document.close()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line options for a slide export."""
    parser = argparse.ArgumentParser(
        description="Convert a PowerPoint presentation or PDF to high-resolution PNG images.",
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to the input .ppt, .pptx, or .pdf file.",
    )
    parser.add_argument(
        "output_directory",
        type=Path,
        help="Directory in which to save the PNG slide images.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="PNG resolution in dots per inch (default: 300).",
    )
    parser.add_argument(
        "--keep-pdf",
        action="store_true",
        help="Keep the exported PDF in the output directory (PowerPoint input only).",
    )
    arguments = parser.parse_args()

    if not arguments.input_path.is_file():
        parser.error(f"input file not found: {arguments.input_path}")
    if arguments.input_path.suffix.lower() not in {".pdf", ".ppt", ".pptx"}:
        parser.error("input file must have a .pdf, .ppt, or .pptx extension")
    if arguments.dpi <= 0:
        parser.error("--dpi must be a positive integer")

    return arguments


def main() -> None:
    """Convert the command-line input file into high-resolution PNG images."""
    arguments = parse_arguments()
    input_path = arguments.input_path
    output_directory = arguments.output_directory
    output_directory.mkdir(parents=True, exist_ok=True)

    if input_path.suffix.lower() == ".pdf":
        pdf_path = input_path
        temporary_pdf = False
    elif arguments.keep_pdf:
        pdf_path = output_directory / f"{input_path.stem}_export.pdf"
        temporary_pdf = False
    else:
        file_descriptor, temporary_pdf_name = tempfile.mkstemp(
            prefix=f"{input_path.stem}_",
            suffix=".pdf",
        )
        os.close(file_descriptor)
        pdf_path = Path(temporary_pdf_name)
        pdf_path.unlink()
        temporary_pdf = True

    try:
        if input_path.suffix.lower() != ".pdf":
            export_powerpoint_to_pdf(
                presentation_path=input_path,
                pdf_path=pdf_path,
            )
        render_pdf_slides(
            pdf_path=pdf_path,
            output_directory=output_directory,
            dpi=arguments.dpi,
        )
    finally:
        if temporary_pdf:
            pdf_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
