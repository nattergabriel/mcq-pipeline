"""
Module for generating MCQs using an LLM, based on extracted PDF content and specified
experiment configurations.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from src.llm_client import LLMClient

logger = logging.getLogger(__name__)

SCHEMA_PATHS = {
    "single_step": Path("llm_schemas/generation_single_step.json"),
    "two_step_question": Path("llm_schemas/generation_two_step_question.json"),
    "two_step_distractor": Path("llm_schemas/generation_two_step_distractors.json"),
}


def _chunk_pages(pages: List[Dict], pages_per_chunk: int, overlap: int) -> List[List[Dict]]:
    """
    Splits pages into overlapping chunks.
    """
    if not pages:
        return []

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


def _pages_to_text(pages: List[Dict]) -> str:
    """
    Converts a list of page dictionaries to a single text string.
    """
    all_blocks = []
    for page in pages:
        for block in page.get("text_blocks", []):
            all_blocks.append(block)
    return "\n".join(all_blocks)


def _load_prompt(prompt_file: Path, schema_file: Path) -> str:
    """
    Loads and formats a prompt with its schema.
    """
    try:
        schema = json.dumps(
            json.load(schema_file.open(encoding="utf-8")), indent=4)
        # Replace {SCHEMA} placeholder in prompt template with actual schema
        return prompt_file.read_text(encoding="utf-8").replace("{SCHEMA}", schema)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load prompt or schema: {e}")
        raise


def _generate_single_step_mcq(llm_client: LLMClient, prompt: str, text: str, model: str, temperature: float) -> Dict:
    """
    Generates an MCQ in a single LLM call.
    """
    try:
        response = llm_client.call_llm(
            system_message=prompt, user_message=text, model=model, temperature=temperature
        )
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode LLM response: {e}")
        return {}


def _generate_two_step_mcq(llm_client: LLMClient, question_prompt: str, distractor_prompt: str, text: str, model: str, temperature: float,) -> Dict:
    """
    Generates an MCQ in two LLM calls.
    """
    try:
        # Generate question and correct answer
        question_response = llm_client.call_llm(
            system_message=question_prompt, user_message=text, model=model, temperature=temperature
        )
        question_data = json.loads(question_response)

        # Generate distractors
        distractor_input = json.dumps(
            {"question": question_data["question_text"],
                "correct_answer": question_data["correct_answer"]}
        )
        distractor_response = llm_client.call_llm(
            system_message=distractor_prompt,
            user_message=distractor_input,
            model=model,
            temperature=temperature,
        )
        distractor_data = json.loads(distractor_response)

        return {
            "question_text": question_data["question_text"],
            "answer_options": [
                {"text": question_data["correct_answer"], "is_correct": True},
                {"text": distractor_data["distractors"]
                    [0], "is_correct": False},
                {"text": distractor_data["distractors"]
                    [1], "is_correct": False},
                {"text": distractor_data["distractors"]
                    [2], "is_correct": False}
            ]
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode LLM response: {e}")
        return {}


def _generate_mcqs_for_experiment(experiment: Dict, content_files: List[Path], llm_client: LLMClient, output_dir: Path) -> List[Dict]:
    """
    Generates MCQs for a single experiment.
    """
    name = experiment.get("name")
    mode = experiment.get("mode", "single_step")
    model = experiment.get("model")
    temperature = experiment.get("temperature", 0.5)
    num_questions = experiment.get("num_questions_per_chunk", 1)
    pages_per_chunk = experiment.get("pages_per_chunk", 0)
    chunk_overlap = experiment.get("chunk_overlap", 0)

    logger.info(f"Processing experiment: {name}")

    # Load prompts
    try:
        if mode == "single_step":
            prompt = _load_prompt(
                Path(experiment["prompt_file"]), SCHEMA_PATHS["single_step"])
            question_prompt = distractor_prompt = None
        elif mode == "two_step":
            question_prompt = _load_prompt(
                Path(experiment["question_prompt_file"]
                     ), SCHEMA_PATHS["two_step_question"]
            )
            distractor_prompt = _load_prompt(
                Path(experiment["distractor_prompt_file"]
                     ), SCHEMA_PATHS["two_step_distractor"]
            )
            prompt = None
        else:
            logger.error(f"Unknown mode '{mode}' for experiment '{name}'")
            return []
    except Exception:
        return []

    questions = []
    for content_file in content_files:
        pages = json.load(content_file.open(encoding="utf-8"))
        # If pages_per_chunk is set, split into chunks; otherwise treat entire document as one chunk
        chunks = _chunk_pages(pages, pages_per_chunk,
                              chunk_overlap) if pages_per_chunk > 0 else [pages]

        for chunk_idx, chunk in enumerate(chunks):
            text = _pages_to_text(chunk)
            page_range = f"pages {chunk[0]['page']}-{chunk[-1]['page']}"
            logger.info(
                f"Processing chunk {chunk_idx + 1}/{len(chunks)} ({page_range}) from {content_file.name}")

            for _ in range(num_questions):
                try:
                    mcq = (
                        _generate_single_step_mcq(
                            llm_client, prompt, text, model, temperature)
                        if mode == "single_step"
                        else _generate_two_step_mcq(
                            llm_client, question_prompt, distractor_prompt, text, model, temperature
                        )
                    )
                    if "question_text" in mcq and "answer_options" in mcq:
                        mcq["metadata"] = {
                            "source_file": content_file.name,
                            "source_pages": {"start": chunk[0]["page"], "end": chunk[-1]["page"]},
                            "generated_at": datetime.now().isoformat(),
                        }
                        questions.append(mcq)
                        logger.debug(
                            f"Generated question for chunk {chunk_idx + 1}")
                    else:
                        logger.warning(
                            f"Invalid MCQ structure for chunk {chunk_idx + 1}")
                except Exception as e:
                    logger.error(f"Error generating question: {e}")

    if questions:
        output_path = output_dir / name / "generated_mcqs.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(questions, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(questions)} questions to {output_path}")

    return questions


def generate_and_save_mcqs(experiments: List[Dict], extracted_content_dir: Path, mcqs_output_dir: Path) -> None:
    """
    Generates and saves MCQs for all experiments.
    """
    logger.info(
        f"Starting MCQ generation for {len(experiments)} experiment(s)")

    content_files = list(extracted_content_dir.glob("*.json"))
    if not content_files:
        logger.warning(f"No content files found in {extracted_content_dir}")
        return

    logger.info(f"Found {len(content_files)} content files")

    llm_client = LLMClient()

    for experiment in experiments:
        questions = _generate_mcqs_for_experiment(
            experiment, content_files, llm_client, mcqs_output_dir)
        if not questions:
            logger.warning(
                f"No questions generated for experiment '{experiment.get('name')}'")
