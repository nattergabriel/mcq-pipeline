from src.pdf_extractor import process_pdfs

import yaml
import argparse
from pathlib import Path

CONFIG_PATH = Path("config.yaml")


def load_config(config_path: Path) -> dict:
    """
    Load the YAML configuration file.
    """
    try:
        with open(config_path, 'r', encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Configuration file not found at '{config_path}'")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML config file: {e}")
        return None


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

    subparsers.add_parser(
        "extract",
        help="Extract text from all PDFs defined in config.yaml."
    )

    subparsers.add_parser(
        "generate",
        help="Generate MCQs from extracted text using strategies in config.yaml."
    )

    return parser


def main():
    """
    Main entry point for the MCQ generation pipeline.
    """
    parser = setup_parser()
    args = parser.parse_args()

    config = load_config(CONFIG_PATH)
    if not config:
        return

    paths = config.get("paths", {})

    if args.command == "extract":

        input_path_str = paths.get("input_pdfs_dir")
        output_path_str = paths.get("extracted_content_dir")

        if not input_path_str or not output_path_str:
            print(
                "Error: 'input_pdfs_dir' and/or 'extracted_content_dir' not defined in config.yaml")
            return

        input_dir = Path(input_path_str)
        output_dir = Path(output_path_str)

        print(f"Extracting text from PDFs in '{input_dir}'...")
        process_pdfs(input_dir, output_dir)
        print(f"Extraction complete. Files saved in '{output_dir}'.")


if __name__ == "__main__":
    main()
