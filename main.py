from src.pdf_extractor import process_pdfs
from src.mcqs_generator import generate_mcqs
from src.mcqs_exporter import export_mcqs_to_moodle

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
        help="Available commands")

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
        input_dir = paths.get("input_pdfs_dir")
        output_dir = paths.get("extracted_content_dir")

        if not input_dir or not output_dir:
            print(
                "Error: 'input_pdfs_dir' and/or 'extracted_content_dir' not defined in config.yaml")
            return

        process_pdfs(Path(input_dir), Path(output_dir))

    elif args.command == "generate":
        extracted_dir = paths.get("extracted_content_dir")
        mcqs_output_dir = paths.get("generated_mcqs_dir")
        experiments = config.get("experiments")

        if not extracted_dir or not experiments:
            print(
                "Error: 'extracted_content_dir' and/or 'experiments' not defined in config.yaml")
            return

        generate_mcqs(
            experiments=experiments,
            extracted_content_dir=Path(extracted_dir),
            mcqs_output_dir=Path(mcqs_output_dir))

    elif args.command == "export":
        mcqs_output_dir = paths.get("generated_mcqs_dir")

        if not mcqs_output_dir:
            print("Error: 'generated_mcqs_dir' not defined in config.yaml")
            return

        export_mcqs_to_moodle(Path(mcqs_output_dir))


if __name__ == "__main__":
    main()
