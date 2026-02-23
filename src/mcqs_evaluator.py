"""
Module for evaluating generated MCQs using an LLM based on quality criteria.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict

from langchain_core.prompts import ChatPromptTemplate

from src.llm_client import get_llm_model
from src.models import EvaluationConfig, EvaluationResult

logger = logging.getLogger(__name__)


def _format_mcq_for_evaluation(mcq: Dict) -> str:
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
    prompt_text: str,
    mcq: Dict,
    context: str,
    model: str,
    temperature: float,
    max_retries: int = 3,
) -> Dict:
    """
    Evaluates a single MCQ using the LLM and LangChain.
    """
    for attempt in range(1, max_retries + 1):
        try:
            llm = get_llm_model(model=model, temperature=temperature)
            structured_llm = llm.with_structured_output(EvaluationResult)

            prompt = ChatPromptTemplate.from_messages(
                [("system", prompt_text), ("user", "{mcq_text}\n\nKontext:\n{context}")]
            )

            chain = prompt | structured_llm

            mcq_text = _format_mcq_for_evaluation(mcq)
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
        # Load generated MCQs
        with generated_file.open("r", encoding="utf-8") as f:
            mcqs = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {generated_file}: {e}")
        return

    # Evaluate each MCQ
    evaluated_mcqs = []
    for idx, mcq in enumerate(mcqs, 1):
        logger.info(f"Evaluating MCQ {idx}/{len(mcqs)}")

        context = mcq.get("metadata", {}).get("chunk_text", "")
        evaluation = _evaluate_single_mcq(
            prompt_text,
            mcq,
            context,
            evaluation_config.model,
            evaluation_config.temperature,
            evaluation_config.max_retries,
        )

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

    executor = ThreadPoolExecutor()
    futures = []

    for generated_file in generated_files:
        future = executor.submit(
            _evaluate_file, generated_file, prompt_text, evaluation_config
        )
        futures.append(future)

    # Wait for all to complete
    for future in futures:
        try:
            future.result()
        except Exception as e:
            logger.error(f"Error processing file: {e}")

    executor.shutdown()
