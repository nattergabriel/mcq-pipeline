from src.pdf_extractor import process_pdfs

import argparse
from pathlib import Path


DEFAULT_INPUT_DIR = Path("data/input/pdfs")
DEFAULT_OUTPUT_DIR = Path("data/output/extracted_content")


def setup_parser() -> argparse.ArgumentParser:
    """
    Sets up the command-line interface.
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands"
    )

    parser_extract = subparsers.add_parser(
        "extract",
        help="Extract text from all PDFs in a folder."
    )
    parser_extract.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Folder with the PDF files."
    )
    parser_extract.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Folder to save the extracted text."
    )

    return parser


def main():
    """
    Main entry point for the MCQ generation pipeline.
    """
    parser = setup_parser()
    args = parser.parse_args()

    if args.command == "extract":
        print(f"Extracting text from PDFs in '{args.input_dir}'...")
        process_pdfs(args.input_dir, args.output_dir)
        print(f"Extraction complete. Files saved in '{args.output_dir}'.")


if __name__ == "__main__":
    main()
