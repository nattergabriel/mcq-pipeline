"""
Module for evaluating generated MCQs using an LLM based on quality criteria.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

from src.llm_client import get_llm_model
from src.models import EvaluationConfig, EvaluationResult

logger = logging.getLogger(__name__)


def _format_mcq_for_evaluation(mcq: dict) -> str:
    """
    Formats an MCQ into a readable text format for evaluation.
    """
    question = mcq.get("question_text", "")
    options = mcq.get("answer_options", [])

    formatted = f"Frage: {question}\n\nAntwortmöglichkeiten:\n"
    for i, option in enumerate(options, 1):
        correct_marker = " (KORREKTE ANTWORT)" if option.get("is_correct") else ""
        formatted += f"{i}. {option.get('text', '')}{correct_marker}\n"

    return formatted


def _evaluate_single_mcq(
    chain,
    mcq: dict,
    context: str,
    max_retries: int = 3,
) -> dict:
    """
    Evaluates a single MCQ using a pre-built LangChain chain.
    """
    mcq_text = _format_mcq_for_evaluation(mcq)

    for attempt in range(1, max_retries + 1):
        try:
            result = chain.invoke({"mcq_text": mcq_text, "context": context})
            return result.model_dump()
        except Exception as e:
            logger.warning(
                f"Failed to evaluate MCQ (attempt {attempt}/{max_retries}): {e}"
            )

    logger.error(f"Failed to evaluate MCQ after {max_retries} attempts")
    return {}


def _evaluate_file(
    generated_file: Path, prompt_text: str, evaluation_config: EvaluationConfig
) -> None:
    """
    Evaluates all MCQs in a single file.
    """
    logger.info(f"Evaluating MCQs in {generated_file}")

    try:
        mcqs = json.loads(generated_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load {generated_file}: {e}")
        return

    llm = get_llm_model(
        model=evaluation_config.model, temperature=evaluation_config.temperature
    )
    prompt = ChatPromptTemplate.from_messages(
        [("system", prompt_text), ("user", "{mcq_text}\n\nKontext:\n{context}")]
    )
    chain = prompt | llm.with_structured_output(EvaluationResult)

    evaluated_mcqs = []
    for idx, mcq in enumerate(mcqs, 1):
        logger.info(f"Evaluating MCQ {idx}/{len(mcqs)}")

        context = mcq.get("metadata", {}).get("chunk_text", "")
        evaluation = _evaluate_single_mcq(
            chain, mcq, context, evaluation_config.max_retries
        )

        mcq_with_eval = mcq.copy()
        if evaluation:
            mcq_with_eval["evaluation"] = evaluation
            logger.debug(f"Successfully evaluated MCQ {idx}")
        else:
            logger.warning(f"Failed to evaluate MCQ {idx}, skipping")

        evaluated_mcqs.append(mcq_with_eval)

    output_file = generated_file.parent / "evaluated_mcqs.json"
    try:
        output_file.write_text(
            json.dumps(evaluated_mcqs, indent=4, ensure_ascii=False), encoding="utf-8"
        )
        logger.info(f"Saved {len(evaluated_mcqs)} evaluated MCQs to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save evaluated MCQs: {e}")


def evaluate_and_save_mcqs(evaluation_config: EvaluationConfig, mcqs_dir: Path) -> None:
    """
    Evaluates MCQs for all experiments in parallel and saves results.
    """
    logger.info("Starting MCQ evaluation")

    prompt_file = Path(evaluation_config.prompt_file)
    try:
        prompt_text = prompt_file.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to load evaluation prompt: {e}")
        return

    generated_files = list(mcqs_dir.glob("*/generated_mcqs.json"))
    if not generated_files:
        logger.warning(f"No generated MCQ files found in {mcqs_dir}")
        return

    logger.info(f"Found {len(generated_files)} MCQ files to evaluate")

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                _evaluate_file, generated_file, prompt_text, evaluation_config
            )
            for generated_file in generated_files
        ]

        for future in futures:
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error processing file: {e}")
