"""
Main entry point and command-line interface for the MCQ generation pipeline.
"""

import yaml
import argparse
import logging
from pathlib import Path

from src.pdf_extractor import extract_and_save_pdfs
from src.mcqs_generator import generate_and_save_mcqs
from src.mcqs_evaluator import evaluate_and_save_mcqs
from src.mcqs_exporter import find_and_export_mcqs

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path("config.yaml")


def _load_config(config_path: Path) -> dict:
    """
    Load the YAML configuration file from the specified path.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info(
                f"Successfully loaded configuration from '{config_path}'")
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found at '{config_path}'")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Parsing YAML config file: {e}")
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
        "evaluate",
        help="Evaluate generated MCQs using quality criteria.")

    subparsers.add_parser(
        "export",
        help="Export generated MCQs to Moodle XML format.")

    return parser


def _run_extract(config: dict):
    """
    Reads the necessary paths from the config file and calls the main extraction function.
    """
    logger.info("Starting PDF extraction")
    extraction_config = config.get("extraction", {})
    input_dir = extraction_config.get("input_pdfs_dir")
    output_dir = config.get("output_dir")

    if not input_dir or not output_dir:
        logger.error(
            "'extraction.input_pdfs_dir' and/or 'output_dir' not defined in config.yaml")
        return

    extracted_output_dir = Path(output_dir) / "extracted_pdfs"
    extract_and_save_pdfs(Path(input_dir), extracted_output_dir)


def _run_generate(config: dict):
    """
    Reads paths and experiment settings from the config and calls the main generator function.
    """
    logger.info("Starting MCQ generation")
    output_dir = config.get("output_dir")
    generation_config = config.get("generation", {})
    experiments = generation_config.get("experiments")

    if not output_dir or not experiments:
        logger.error(
            "'output_dir' and/or 'generation.experiments' not defined in config.yaml")
        return

    extracted_content_dir = Path(output_dir) / "extracted_pdfs"
    mcqs_output_dir = Path(output_dir) / "mcqs"

    generate_and_save_mcqs(
        experiments=experiments,
        extracted_content_dir=extracted_content_dir,
        mcqs_output_dir=mcqs_output_dir)


def _run_evaluate(config: dict):
    """
    Reads paths and evaluation settings from the config and calls the main evaluator function.
    """
    logger.info("Starting MCQ evaluation")
    output_dir = config.get("output_dir")
    evaluation_config = config.get("evaluation", {})

    if not output_dir or not evaluation_config:
        logger.error(
            "'output_dir' and/or 'evaluation' not defined in config.yaml")
        return

    mcqs_output_dir = Path(output_dir) / "mcqs"
    evaluate_and_save_mcqs(
        evaluation_config=evaluation_config,
        mcqs_dir=mcqs_output_dir)


def _run_export(config: dict):
    """
    Reads the output directory path from the config and calls the main export
    function to convert JSON files to Moodle XML.
    """
    logger.info("Starting MCQ export")
    output_dir = config.get("output_dir")

    if not output_dir:
        logger.error("'output_dir' not defined in config.yaml")
        return

    # Export reads from output_dir/mcqs
    mcqs_output_dir = Path(output_dir) / "mcqs"
    find_and_export_mcqs(mcqs_output_dir)


def main():
    """
    Main entry point for the MCQ generation pipeline, handling CLI commands.
    """
    parser = _setup_parser()
    args = parser.parse_args()

    logger.info(f"Running command: {args.command}")

    config = _load_config(CONFIG_PATH)
    if not config:
        return

    if args.command == "run":
        _run_extract(config)
        _run_generate(config)
        _run_evaluate(config)
        _run_export(config)

    elif args.command == "extract":
        _run_extract(config)

    elif args.command == "generate":
        _run_generate(config)

    elif args.command == "evaluate":
        _run_evaluate(config)

    elif args.command == "export":
        _run_export(config)

    logger.info("Command completed successfully")


if __name__ == "__main__":
    main()
