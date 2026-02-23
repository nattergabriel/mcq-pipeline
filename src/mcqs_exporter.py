"""
Module for exporting evaluated MCQs from JSON format to Moodle XML format.
"""

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List
from xml.dom import minidom

from src.models import ExportConfig

logger = logging.getLogger(__name__)

EVALUATION_METRICS = ["clarity", "correctness", "distractor_quality", "relevance"]


def _should_export_question(
    question: Dict[str, Any], weights: Dict[str, float], min_score: float
) -> bool:
    """
    Checks if a question should be exported based on evaluation scores.
    Requirements: weighted average score >= min_score and no score is 0.
    """
    scores = []
    total_weight = 0.0
    for metric in EVALUATION_METRICS:
        if "evaluation" in question and metric in question["evaluation"]:
            score = question["evaluation"][metric]["score"]
            if score == 0:
                return False
            weight = weights.get(metric, 1.0)
            scores.append(score * weight)
            total_weight += weight
    if not scores:
        return False
    weighted_avg = sum(scores) / total_weight
    return weighted_avg >= min_score


def _convert_mcqs_to_moodle_xml(questions: List[Dict[str, Any]], category: str) -> str:
    """
    Converts a list of question dictionaries into a Moodle XML string.
    """
    logger.debug(f"Converting {len(questions)} questions to Moodle XML format")
    root = ET.Element("quiz")

    question = ET.SubElement(root, "question", type="category")
    question_category = ET.SubElement(question, "category")
    question_category_text = ET.SubElement(question_category, "text")
    question_category_text.text = f"$course$/{category}"

    for q_data in questions:
        question = ET.SubElement(root, "question", type="multichoice")

        name = ET.SubElement(question, "name")
        name_text = ET.SubElement(name, "text")
        name_text.text = q_data["question_text"][:50]

        questiontext = ET.SubElement(question, "questiontext", format="markdown")
        questiontext_text = ET.SubElement(questiontext, "text")
        questiontext_text.text = q_data["question_text"]

        ET.SubElement(question, "single").text = "true"
        ET.SubElement(question, "shuffleanswers").text = "1"

        for option in q_data["answer_options"]:
            fraction = "100" if option.get("is_correct", False) else "0"
            answer = ET.SubElement(
                question, "answer", fraction=fraction, format="markdown"
            )
            answer_text = ET.SubElement(answer, "text")
            answer_text.text = option["text"]

    raw_xml = ET.tostring(root, "utf-8")
    parsed_xml = minidom.parseString(raw_xml)
    return parsed_xml.toprettyxml(indent="  ", encoding="utf-8")


def _process_mcqs_file(path: Path, weights: Dict[str, float], min_score: float) -> None:
    """
    Processes a single evaluated_mcqs.json file: loads, filters, converts, and exports.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            questions = json.load(f)

        questions = [
            q for q in questions if _should_export_question(q, weights, min_score)
        ]

        if not questions:
            logger.warning(f"Skipping '{path}' as it contains no qualifying questions")
            return

        xml_content = _convert_mcqs_to_moodle_xml(questions, path.parent.name)

        xml_output_path = path.with_name("exported_mcqs.xml")

        with open(xml_output_path, "wb") as f:
            f.write(xml_content)

        logger.info(
            f"Successfully exported {len(questions)} questions to '{xml_output_path}'"
        )

    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to process '{path}': {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing '{path}': {e}")


def find_and_export_mcqs(mcqs_base_dir: Path, export_config: ExportConfig):
    """
    Finds all "evaluated_mcqs.json" files recursively and processes them for export.
    Only exports questions that meet the evaluation criteria.
    """
    logger.info(
        f"Using evaluation weights: {export_config.criteria_weights}, "
        f"minimum weighted average score: {export_config.min_weighted_avg_score}"
    )

    logger.info(f"Searching for MCQ files in '{mcqs_base_dir}'")
    files = list(mcqs_base_dir.rglob("evaluated_mcqs.json"))

    if not files:
        logger.warning(
            f"No 'evaluated_mcqs.json' files found in '{mcqs_base_dir}'"
        )
        return

    logger.info(f"Found {len(files)} result file(s) to export")

    for path in files:
        _process_mcqs_file(
            path, export_config.criteria_weights, export_config.min_weighted_avg_score
        )
