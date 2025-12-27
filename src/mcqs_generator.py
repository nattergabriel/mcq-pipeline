"""
Module for generating MCQs using an LLM, based on extracted PDF content and specified
experiment configurations.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from langchain_core.prompts import ChatPromptTemplate

from src.llm_client import get_llm_model
from src.models import (
    ExperimentConfig,
    SingleStepMCQ,
    SingleStepMCQWithReasoning,
    TwoStepQuestion,
    TwoStepQuestionWithReasoning,
    TwoStepDistractors,
    TwoStepDistractorsWithReasoning,
)

logger = logging.getLogger(__name__)


def _generate_single_step_mcq(prompt_text: str, text: str, model: str, temperature: float, capture_reasoning: bool = False) -> Dict:
    """
    Generates an MCQ in a single LLM call using LangChain.
    If capture_reasoning is True (for Chain-of-Thought), uses a model that includes reasoning steps.
    """
    try:
        llm = get_llm_model(model=model, temperature=temperature)
        structured_llm = llm.with_structured_output(SingleStepMCQWithReasoning if capture_reasoning else SingleStepMCQ)

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_text),
            ("user", "{text}")
        ])

        chain = prompt | structured_llm
        result = chain.invoke({"text": text})

        return result.model_dump()
    except Exception as e:
        logger.error(f"Error generating single step MCQ: {e}")
        return {}


def _generate_two_step_mcq(question_prompt_text: str, distractor_prompt_text: str, text: str, model: str, temperature: float, capture_reasoning: bool = False) -> Dict:
    """
    Generates an MCQ in two LLM calls using LangChain.
    If capture_reasoning is True (for Chain-of-Thought), uses models that include reasoning steps.
    """
    try:
        llm = get_llm_model(model=model, temperature=temperature)

        # Step 1: Generate question and correct answer
        question_llm = llm.with_structured_output(TwoStepQuestionWithReasoning if capture_reasoning else TwoStepQuestion)
        question_prompt = ChatPromptTemplate.from_messages([
            ("system", question_prompt_text),
            ("user", "{text}")
        ])
        question_chain = question_prompt | question_llm

        question_result = question_chain.invoke({"text": text})

        # Step 2: Generate distractors
        distractor_llm = llm.with_structured_output(TwoStepDistractorsWithReasoning if capture_reasoning else TwoStepDistractors)
        distractor_prompt = ChatPromptTemplate.from_messages([
            ("system", distractor_prompt_text),
            ("user", "{input}")
        ])
        distractor_chain = distractor_prompt | distractor_llm

        distractor_input = json.dumps({
            "question": question_result.question_text,
            "correct_answer": question_result.correct_answer
        }, ensure_ascii=False)

        distractor_result = distractor_chain.invoke(
            {"input": distractor_input})

        # Combine results
        distractors = distractor_result.distractors
        if len(distractors) != 3:
            raise ValueError(
                f"Expected exactly 3 distractors, got {len(distractors)}")

        result = {
            "question_text": question_result.question_text,
            "answer_options": [
                {"text": question_result.correct_answer, "is_correct": True},
                {"text": distractors[0], "is_correct": False},
                {"text": distractors[1], "is_correct": False},
                {"text": distractors[2], "is_correct": False}
            ]
        }
        
        if capture_reasoning:
            result["question_reasoning"] = question_result.reasoning
            result["distractor_reasoning"] = distractor_result.reasoning
        
        return result
    except Exception as e:
        logger.error(f"Error generating two-step MCQ: {e}")
        return {}


def _generate_mcqs_for_experiment(experiment: ExperimentConfig, content_files: List[Path], output_dir: Path) -> List[Dict]:
    """
    Generates MCQs for a single experiment.
    """
    logger.info(f"Processing experiment: {experiment.name}")

    # Load prompts
    try:
        if experiment.mode == "single_step":
            prompt_text = Path(experiment.prompt_file).read_text(
                encoding="utf-8")
            question_prompt_text = distractor_prompt_text = None
        elif experiment.mode == "two_step":
            question_prompt_text = Path(
                experiment.question_prompt_file).read_text(encoding="utf-8")
            distractor_prompt_text = Path(
                experiment.distractor_prompt_file).read_text(encoding="utf-8")
            prompt_text = None
        else:
            logger.error(
                f"Unknown mode '{experiment.mode}' for experiment '{experiment.name}'")
            return []
    except Exception as e:
        logger.error(
            f"Failed to load prompts for experiment '{experiment.name}': {e}")
        return []

    questions = []
    for content_file in content_files:
        chunks = json.load(content_file.open(encoding="utf-8"))

        for chunk_idx, text in enumerate(chunks):
            logger.info(
                f"Processing chunk {chunk_idx} from {content_file.name}")

            for _ in range(experiment.num_questions_per_chunk):
                try:
                    mcq = (
                        _generate_single_step_mcq(
                            prompt_text, text, experiment.model, experiment.temperature, experiment.capture_reasoning)
                        if experiment.mode == "single_step"
                        else _generate_two_step_mcq(
                            question_prompt_text, distractor_prompt_text, text, experiment.model, experiment.temperature, experiment.capture_reasoning
                        )
                    )
                    if "question_text" in mcq and "answer_options" in mcq:
                        mcq["metadata"] = {
                            "source_file": content_file.name,
                            "chunk_index": chunk_idx,
                            "chunk_text": text,
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
        output_path = output_dir / experiment.name / "generated_mcqs.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(questions, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(questions)} questions to {output_path}")

    return questions


def generate_and_save_mcqs(experiments: List[ExperimentConfig], extracted_content_dir: Path, mcqs_output_dir: Path) -> None:
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

    for experiment in experiments:
        questions = _generate_mcqs_for_experiment(
            experiment, content_files, mcqs_output_dir)
        if not questions:
            logger.warning(
                f"No questions generated for experiment '{experiment.name}'")
