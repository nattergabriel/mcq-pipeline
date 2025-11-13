"""
Module for generating MCQs using an LLM, based on extracted PDF content and specified experiment
configurations.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from src.llm_client import LLMClient

logger = logging.getLogger(__name__)


def _chunk_pages(pages: List[Dict[str, Any]], pages_per_chunk: int, overlap: int) -> List[List[Dict[str, Any]]]:
    """
    Splits pages into overlapping chunks.
    """
    chunks = []
    # Move forward by this amount (e.g., 5 pages - 1 overlap = 4)
    step = pages_per_chunk - overlap

    for i in range(0, len(pages), step):
        chunk = pages[i:i + pages_per_chunk]
        if chunk:
            chunks.append(chunk)
        # Stop after reaching the last page
        if i + pages_per_chunk >= len(pages):
            break

    return chunks


def _pages_to_text(pages: List[Dict[str, Any]]) -> str:
    """
    Converts a list of page dictionaries to a single text string.
    """
    all_blocks = []
    for page in pages:
        for block in page.get("text_blocks", []):
            all_blocks.append(block)
    return "\n".join(all_blocks)


def generate_and_save_mcqs(experiments: List[Dict[str, Any]], extracted_content_dir: Path, mcqs_output_dir: Path):
    """
    Generates MCQs for each experiment defined in the configuration.
    """
    logger.info(
        f"Running MCQ generation with {len(experiments)} experiment(s)")
    llm_client = LLMClient()

    content_files = list(extracted_content_dir.glob("*.json"))
    if not content_files:
        logger.warning(
            f"No extracted content files found in '{extracted_content_dir}'")
        return

    logger.info(f"Found {len(content_files)} content file(s) to process")

    for experiment in experiments:
        name = experiment.get("name")
        prompt_file = Path(experiment.get("prompt_file"))
        schema_file = Path(experiment.get("schema_file"))
        model = experiment.get("model")
        temperature = experiment.get("temperature", 0.5)
        num_questions = experiment.get("num_questions", 1)
        pages_per_chunk = experiment.get("pages_per_chunk", None)
        chunk_overlap = experiment.get("chunk_overlap", 0)

        logger.info(f"Processing experiment: {name}")

        try:
            # Load schema and inject into prompt template
            schema_str = json.dumps(
                json.load(open(schema_file, "r", encoding="utf-8")), indent=4)
            system_prompt = prompt_file.read_text(
                encoding="utf-8").replace("{SCHEMA}", schema_str)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(
                f"Error loading prompt/schema: {e}. Skipping experiment '{name}'")
            continue

        all_generated_questions = []
        for content_path in content_files:
            pages = json.load(open(content_path, "r", encoding="utf-8"))

            # Split into chunks or process entire document as one chunk
            if pages_per_chunk and pages_per_chunk > 0:
                page_chunks = _chunk_pages(
                    pages, pages_per_chunk, chunk_overlap)
                logger.info(f"Split {content_path.name} into {len(page_chunks)} chunks "
                            f"({pages_per_chunk} pages per chunk, {chunk_overlap} overlap)")
            else:
                # Entire document as single chunk
                page_chunks = [pages]
                logger.info(f"Processing {content_path.name} as single chunk")

            # Generate questions for each chunk
            for chunk_idx, chunk in enumerate(page_chunks):
                chunk_text = _pages_to_text(chunk)
                page_range = f"pages {chunk[0]['page']}-{chunk[-1]['page']}"
                logger.info(
                    f"Processing chunk {chunk_idx + 1}/{len(page_chunks)} ({page_range}) from {content_path.name}")

                # Generate num_questions per chunk
                for i in range(num_questions):
                    response_str = llm_client.call_llm(
                        system_message=system_prompt,
                        user_message=chunk_text,
                        model=model,
                        temperature=temperature)

                    try:
                        question_data = json.loads(response_str)
                        if "question_text" in question_data and "answer_options" in question_data:
                            # Add metadata to track where question came from
                            question_data["metadata"] = {
                                "source_file": content_path.name,
                                "source_pages": {
                                    "start": chunk[0]["page"],
                                    "end": chunk[-1]["page"]
                                },
                                "generated_at": datetime.now().isoformat()
                            }
                            all_generated_questions.append(question_data)
                            logger.debug(
                                f"Generated question {i+1}/{num_questions}")
                        else:
                            logger.warning(
                                f"Invalid schema in LLM response for question {i+1}. Skipping")
                    except json.JSONDecodeError:
                        logger.error(
                            f"Failed to decode JSON from LLM response for question {i+1}")

        if all_generated_questions:
            experiment_output_dir = mcqs_output_dir / name
            experiment_output_dir.mkdir(parents=True, exist_ok=True)
            output_file = experiment_output_dir / "generated_mcqs.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_generated_questions, f,
                          indent=4, ensure_ascii=False)
            logger.info(
                f"Successfully saved {len(all_generated_questions)} questions to '{output_file}'")
        else:
            logger.warning(f"No questions generated for experiment '{name}'")
