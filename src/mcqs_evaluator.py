"""
Module for evaluating generated MCQs using an LLM based on quality criteria.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from src.llm_client import LLMClient
from src.models import EvaluationConfig

logger = logging.getLogger(__name__)


def _load_prompt(prompt_file: Path, schema_file: Path) -> str:
    """
    Loads and formats an evaluation prompt with its schema.
    """
    try:
        schema = json.dumps(
            json.load(schema_file.open(encoding="utf-8")), indent=4)
        return prompt_file.read_text(encoding="utf-8").replace("{SCHEMA}", schema)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load prompt or schema: {e}")
        raise


def _format_mcq_for_evaluation(mcq: Dict) -> str:
    """
    Formats an MCQ into a readable text format for evaluation.
    """
    question = mcq.get("question_text", "")
    options = mcq.get("answer_options", [])

    formatted = f"Frage: {question}\n\nAntwortmöglichkeiten:\n"
    for i, option in enumerate(options, 1):
        correct_marker = " (KORREKTE ANTWORT)" if option.get(
            "is_correct") else ""
        formatted += f"{i}. {option.get('text', '')}{correct_marker}\n"

    return formatted


def _evaluate_single_mcq(llm_client: LLMClient, prompt: str, mcq: Dict, model: str, temperature: float) -> Dict:
    """
    Evaluates a single MCQ using the LLM.
    """
    try:
        response = llm_client.call_llm(
            system_message=prompt,
            user_message=_format_mcq_for_evaluation(mcq),
            model=model,
            temperature=temperature)
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode LLM evaluation response: {e}")
        return {}


def evaluate_and_save_mcqs(evaluation_config: EvaluationConfig, mcqs_dir: Path) -> None:
    """
    Evaluates MCQs for all experiment setups and saves results with evaluations appended.
    """
    logger.info("Starting MCQ evaluation")

    prompt_file = Path(evaluation_config.prompt_file)
    schema_file = Path("llm_schemas/evaluation.json")

    try:
        prompt = _load_prompt(prompt_file, schema_file)
    except Exception:
        logger.error("Failed to load evaluation prompt")
        return

    llm_client = LLMClient()

    generated_files = list(mcqs_dir.glob("*/generated_mcqs.json"))
    if not generated_files:
        logger.warning(f"No generated MCQ files found in {mcqs_dir}")
        return

    logger.info(f"Found {len(generated_files)} MCQ files to evaluate")

    for generated_file in generated_files:
        logger.info(f"Evaluating MCQs in {generated_file}")

        try:
            # Load generated MCQs
            with generated_file.open("r", encoding="utf-8") as f:
                mcqs = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {generated_file}: {e}")
            continue

        # Evaluate each MCQ
        evaluated_mcqs = []
        for idx, mcq in enumerate(mcqs, 1):
            logger.info(f"Evaluating MCQ {idx}/{len(mcqs)}")

            evaluation = _evaluate_single_mcq(
                llm_client, prompt, mcq, evaluation_config.model, evaluation_config.temperature)

            if evaluation:
                # Append evaluation to the MCQ
                mcq_with_eval = mcq.copy()
                mcq_with_eval["evaluation"] = evaluation
                evaluated_mcqs.append(mcq_with_eval)
                logger.debug(f"Successfully evaluated MCQ {idx}")
            else:
                logger.warning(f"Failed to evaluate MCQ {idx}, skipping")
                evaluated_mcqs.append(mcq)

        # Save evaluated MCQs
        output_file = generated_file.parent / "evaluated_mcqs.json"
        try:
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(evaluated_mcqs, f, indent=4, ensure_ascii=False)
            logger.info(
                f"Saved {len(evaluated_mcqs)} evaluated MCQs to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save evaluated MCQs: {e}")
