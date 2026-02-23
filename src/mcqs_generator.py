"""
Module for generating MCQs using an LLM, based on extracted PDF content and specified
experiment configurations.
"""

import json
import logging
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

from src.llm_client import get_llm_model
from src.models import (
    ExperimentConfig,
    SingleStepMCQ,
    SingleStepMCQWithReasoning,
    TwoStepDistractors,
    TwoStepDistractorsWithReasoning,
    TwoStepQuestion,
    TwoStepQuestionWithReasoning,
)

logger = logging.getLogger(__name__)


def _generate_single_step_mcq(
    prompt_text: str,
    text: str,
    model: str,
    temperature: float,
    capture_reasoning: bool = False,
    max_retries: int = 3,
) -> dict:
    """
    Generates an MCQ in a single LLM call using LangChain.
    If capture_reasoning is True, uses a model that includes reasoning.
    """
    llm = get_llm_model(model=model, temperature=temperature)
    schema = SingleStepMCQWithReasoning if capture_reasoning else SingleStepMCQ
    structured_llm = llm.with_structured_output(schema)

    prompt = ChatPromptTemplate.from_messages(
        [("system", prompt_text), ("user", "{text}")]
    )
    chain = prompt | structured_llm

    for attempt in range(1, max_retries + 1):
        try:
            result = chain.invoke({"text": text})
            return result.model_dump()
        except Exception as e:
            logger.warning(
                f"Error generating single step MCQ "
                f"(attempt {attempt}/{max_retries}): {e}"
            )

    logger.error(f"Failed to generate single step MCQ after {max_retries} attempts")
    return {}


def _generate_two_step_mcq(
    question_prompt_text: str,
    distractor_prompt_text: str,
    text: str,
    model: str,
    temperature: float,
    capture_reasoning: bool = False,
    max_retries: int = 3,
) -> dict:
    """
    Generates an MCQ in two LLM calls using LangChain.
    If capture_reasoning is True, uses models that include reasoning.
    """
    llm = get_llm_model(model=model, temperature=temperature)

    question_schema = (
        TwoStepQuestionWithReasoning if capture_reasoning else TwoStepQuestion
    )
    question_chain = ChatPromptTemplate.from_messages(
        [("system", question_prompt_text), ("user", "{text}")]
    ) | llm.with_structured_output(question_schema)

    distractor_schema = (
        TwoStepDistractorsWithReasoning if capture_reasoning else TwoStepDistractors
    )
    distractor_chain = ChatPromptTemplate.from_messages(
        [("system", distractor_prompt_text), ("user", "{input}")]
    ) | llm.with_structured_output(distractor_schema)

    for attempt in range(1, max_retries + 1):
        try:
            # Step 1: Generate question and correct answer
            question_result = question_chain.invoke({"text": text})

            # Step 2: Generate distractors
            distractor_input = json.dumps(
                {
                    "question": question_result.question_text,
                    "correct_answer": question_result.correct_answer,
                },
                ensure_ascii=False,
            )
            distractor_result = distractor_chain.invoke({"input": distractor_input})

            distractors = distractor_result.distractors
            if len(distractors) != 3:
                raise ValueError(
                    f"Expected exactly 3 distractors, got {len(distractors)}"
                )

            result = {
                "question_text": question_result.question_text,
                "answer_options": [
                    {"text": question_result.correct_answer, "is_correct": True},
                    *[{"text": d, "is_correct": False} for d in distractors],
                ],
            }

            if capture_reasoning:
                result["question_reasoning"] = question_result.reasoning
                result["distractor_reasoning"] = distractor_result.reasoning

            return result
        except Exception as e:
            logger.warning(
                f"Error generating two-step MCQ (attempt {attempt}/{max_retries}): {e}"
            )

    logger.error(f"Failed to generate two-step MCQ after {max_retries} attempts")
    return {}


def _load_prompts(experiment: ExperimentConfig) -> tuple[str | None, str | None]:
    """
    Loads prompt files for the given experiment mode.
    Returns (prompt, None) for single_step,
    or (question_prompt, distractor_prompt) for two_step.
    """
    if experiment.mode == "single_step":
        prompt_text = Path(experiment.prompt_file).read_text(encoding="utf-8")
        return prompt_text, None
    elif experiment.mode == "two_step":
        question_prompt = Path(experiment.question_prompt_file).read_text(
            encoding="utf-8"
        )
        distractor_prompt = Path(experiment.distractor_prompt_file).read_text(
            encoding="utf-8"
        )
        return question_prompt, distractor_prompt
    else:
        raise ValueError(f"Unknown mode '{experiment.mode}'")


def _select_chunk_indices(total_chunks: int, experiment: ExperimentConfig) -> list[int]:
    """
    Selects which chunk indices to process based on experiment limits.
    """
    if experiment.max_questions_per_pdf is None:
        return list(range(total_chunks))

    max_chunks = experiment.max_questions_per_pdf // experiment.num_questions_per_chunk
    if max_chunks >= total_chunks:
        return list(range(total_chunks))

    return random.sample(range(total_chunks), max_chunks)


def _generate_mcqs_for_experiment(
    experiment: ExperimentConfig, content_files: list[Path], output_dir: Path
) -> list[dict]:
    """
    Generates MCQs for a single experiment.
    """
    logger.info(f"Processing experiment: {experiment.name}")

    try:
        prompt_a, prompt_b = _load_prompts(experiment)
    except Exception as e:
        logger.error(f"Failed to load prompts for experiment '{experiment.name}': {e}")
        return []

    questions = []
    for content_file in content_files:
        chunks = json.loads(content_file.read_text(encoding="utf-8"))
        selected_indices = _select_chunk_indices(len(chunks), experiment)

        if len(selected_indices) < len(chunks):
            logger.info(
                f"Randomly selected {len(selected_indices)} chunks "
                f"out of {len(chunks)} for {content_file.name}"
            )

        for chunk_idx in selected_indices:
            text = chunks[chunk_idx]
            logger.info(f"Processing chunk {chunk_idx} from {content_file.name}")

            for _ in range(experiment.num_questions_per_chunk):
                try:
                    if experiment.mode == "single_step":
                        mcq = _generate_single_step_mcq(
                            prompt_a,
                            text,
                            experiment.model,
                            experiment.temperature,
                            experiment.capture_reasoning,
                            experiment.max_retries,
                        )
                    else:
                        mcq = _generate_two_step_mcq(
                            prompt_a,
                            prompt_b,
                            text,
                            experiment.model,
                            experiment.temperature,
                            experiment.capture_reasoning,
                            experiment.max_retries,
                        )

                    if "question_text" in mcq and "answer_options" in mcq:
                        mcq["metadata"] = {
                            "source_file": content_file.name,
                            "chunk_index": chunk_idx,
                            "chunk_text": text,
                            "generated_at": datetime.now().isoformat(),
                        }
                        questions.append(mcq)
                        logger.debug(f"Generated question for chunk {chunk_idx + 1}")
                    else:
                        logger.warning(
                            f"Invalid MCQ structure for chunk {chunk_idx + 1}"
                        )
                except Exception as e:
                    logger.error(f"Error generating question: {e}")

    if questions:
        output_path = output_dir / experiment.name / "generated_mcqs.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(questions, indent=4, ensure_ascii=False), encoding="utf-8"
        )
        logger.info(f"Saved {len(questions)} questions to {output_path}")

    return questions


def generate_and_save_mcqs(
    experiments: list[ExperimentConfig],
    extracted_content_dir: Path,
    mcqs_output_dir: Path,
) -> None:
    """
    Generates and saves MCQs for all experiments in parallel using multithreading.
    """
    logger.info(f"Starting MCQ generation for {len(experiments)} experiment(s)")

    content_files = list(extracted_content_dir.glob("*.json"))
    if not content_files:
        logger.warning(f"No content files found in {extracted_content_dir}")
        return

    logger.info(f"Found {len(content_files)} content files")

    with ThreadPoolExecutor() as executor:
        futures = [
            (
                executor.submit(
                    _generate_mcqs_for_experiment,
                    experiment,
                    content_files,
                    mcqs_output_dir,
                ),
                experiment,
            )
            for experiment in experiments
        ]

        for future, experiment in futures:
            try:
                questions = future.result()
                if not questions:
                    logger.warning(
                        f"No questions generated for experiment '{experiment.name}'"
                    )
            except Exception as e:
                logger.error(f"Error processing experiment '{experiment.name}': {e}")
