"""
Main entry point and command-line interface for the MCQ generation pipeline.
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from src.mcqs_evaluator import evaluate_and_save_mcqs
from src.mcqs_exporter import find_and_export_mcqs
from src.mcqs_generator import generate_and_save_mcqs
from src.models import AppConfig
from src.pdf_extractor import extract_and_save_pdfs

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path("config.yaml")


def _load_config(config_path: Path) -> AppConfig:
    """
    Load and validate the YAML configuration file.
    Exits the program if the config is missing, malformed, or invalid.
    """
    try:
        config_dict = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        config = AppConfig(**config_dict)
        logger.info(f"Successfully loaded configuration from '{config_path}'")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found at '{config_path}'")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Parsing YAML config file: {e}")
        sys.exit(1)
    except ValidationError as e:
        logger.error(f"Configuration validation error: {e}")
        sys.exit(1)


def _setup_parser() -> argparse.ArgumentParser:
    """
    Sets up the command-line interface.
    """
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    subparsers.add_parser(
        "run", help="Run the entire pipeline: extract, generate, evaluate, and export."
    )
    subparsers.add_parser(
        "extract", help="Extract text from all PDFs defined in config.yaml."
    )
    subparsers.add_parser(
        "generate",
        help="Generate MCQs from extracted text using strategies in config.yaml.",
    )
    subparsers.add_parser(
        "evaluate", help="Evaluate generated MCQs using quality criteria."
    )
    subparsers.add_parser("export", help="Export generated MCQs to Moodle XML format.")

    return parser


def _run_extract(config: AppConfig):
    logger.info("Starting PDF extraction")
    extracted_output_dir = Path(config.output_dir) / "extracted_pdfs"
    extract_and_save_pdfs(
        Path(config.extraction.input_pdfs_dir),
        extracted_output_dir,
        config.extraction.chunk_size,
        config.extraction.chunk_overlap,
    )


def _run_generate(config: AppConfig):
    logger.info("Starting MCQ generation")
    extracted_content_dir = Path(config.output_dir) / "extracted_pdfs"
    mcqs_output_dir = Path(config.output_dir) / "mcqs"
    generate_and_save_mcqs(
        config.generation.experiments, extracted_content_dir, mcqs_output_dir
    )


def _run_evaluate(config: AppConfig):
    logger.info("Starting MCQ evaluation")
    mcqs_output_dir = Path(config.output_dir) / "mcqs"
    evaluate_and_save_mcqs(config.evaluation, mcqs_output_dir)


def _run_export(config: AppConfig):
    logger.info("Starting MCQ export")
    mcqs_output_dir = Path(config.output_dir) / "mcqs"
    find_and_export_mcqs(mcqs_output_dir, config.export)


COMMANDS = {
    "run": lambda config: (
        _run_extract(config),
        _run_generate(config),
        _run_evaluate(config),
        _run_export(config),
    ),
    "extract": _run_extract,
    "generate": _run_generate,
    "evaluate": _run_evaluate,
    "export": _run_export,
}


def main():
    parser = _setup_parser()
    args = parser.parse_args()

    logger.info(f"Running command: {args.command}")

    config = _load_config(CONFIG_PATH)
    COMMANDS[args.command](config)

    logger.info("Command completed successfully")


if __name__ == "__main__":
    main()
