"""
Main entry point and command-line interface for the MCQ generation pipeline.
"""

import yaml
import argparse
from pathlib import Path

from src.pdf_extractor import extract_and_save_pdfs
from src.mcqs_generator import generate_and_save_mcqs
from src.mcqs_exporter import find_and_export_mcqs

CONFIG_PATH = Path("config.yaml")


def _load_config(config_path: Path) -> dict:
    """
    Load the YAML configuration file from the specified path.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Configuration file not found at '{config_path}'")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML config file: {e}")
        return None


def _setup_parser() -> argparse.ArgumentParser:
    """
    Sets up the command-line interface.
    """
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands")

    subparsers.add_parser(
        "run",
        help="Run the entire pipeline: extract, generate, and export.")

    subparsers.add_parser(
        "extract",
        help="Extract text from all PDFs defined in config.yaml.")

    subparsers.add_parser(
        "generate",
        help="Generate MCQs from extracted text using strategies in config.yaml.")

    subparsers.add_parser(
        "export",
        help="Export generated MCQs to Moodle XML format.")

    return parser


def _run_extract(config: dict):
    """
    Reads the necessary paths from the config file and calls the main extraction function.
    """
    paths = config.get("paths", {})
    input_dir = paths.get("input_pdfs_dir")
    output_dir = paths.get("extracted_content_dir")

    if not input_dir or not output_dir:
        print("Error: 'input_pdfs_dir' and/or 'extracted_content_dir' not defined in config.yaml")
        return

    extract_and_save_pdfs(Path(input_dir), Path(output_dir))


def _run_generate(config: dict):
    """
    Reads paths and experiment settings from the config and calls the main generator function.
    """
    paths = config.get("paths", {})
    extracted_dir = paths.get("extracted_content_dir")
    mcqs_output_dir = paths.get("generated_mcqs_dir")
    experiments = config.get("experiments")

    if not extracted_dir or not mcqs_output_dir or not experiments:
        print("Error: 'extracted_content_dir', 'generated_mcqs_dir', and/or 'experiments' not defined in config.yaml")
        return

    generate_and_save_mcqs(
        experiments=experiments,
        extracted_content_dir=Path(extracted_dir),
        mcqs_output_dir=Path(mcqs_output_dir))


def _run_export(config: dict):
    """
    Reads the output directory path from the config and calls the main export
    function to convert JSON files to Moodle XML.
    """
    paths = config.get("paths", {})
    mcqs_output_dir = paths.get("generated_mcqs_dir")

    if not mcqs_output_dir:
        print("Error: 'generated_mcqs_dir' not defined in config.yaml")
        return

    find_and_export_mcqs(Path(mcqs_output_dir))


def main():
    """
    Main entry point for the MCQ generation pipeline, handling CLI commands.
    """
    parser = _setup_parser()
    args = parser.parse_args()

    config = _load_config(CONFIG_PATH)
    if not config:
        return

    if args.command == "run":
        _run_extract(config)
        _run_generate(config)
        _run_export(config)

    elif args.command == "extract":
        _run_extract(config)

    elif args.command == "generate":
        _run_generate(config)

    elif args.command == "export":
        _run_export(config)


if __name__ == "__main__":
    main()
