"""
Module for exporting generated MCQs from JSON format to Moodle XML format.
"""

import json
from pathlib import Path
from xml.dom import minidom
from typing import List, Dict, Any
import xml.etree.ElementTree as ET


def _convert_mcqs_to_moodle_xml(questions: List[Dict[str, Any]], category: str) -> str:
    """
    Converts a list of question dictionaries into a Moodle XML string.
    """
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

        questiontext = ET.SubElement(question, "questiontext")
        questiontext_text = ET.SubElement(questiontext, "text")
        questiontext_text.text = q_data["question_text"]

        ET.SubElement(question, "single").text = "true"
        ET.SubElement(question, "shuffleanswers").text = "true"

        for option in q_data["answer_options"]:
            fraction = "100" if option.get("is_correct", False) else "0"
            answer = ET.SubElement(question, "answer", fraction=fraction)
            answer_text = ET.SubElement(answer, "text")
            answer_text.text = option["text"]

    raw_xml = ET.tostring(root, "utf-8")
    parsed_xml = minidom.parseString(raw_xml)
    return parsed_xml.toprettyxml(indent="  ", encoding="utf-8")


def find_and_export_mcqs(mcqs_base_dir: Path):
    """
    Finds all "generated_mcqs.json" files recursively and converts them
    to Moodle XML format, saving the output in the same location.
    """
    files = list(mcqs_base_dir.rglob("generated_mcqs.json"))

    if not files:
        print(
            f"No 'generated_mcqs.json' files found in '{mcqs_base_dir}' or its subfolders.")
        return

    print(f"Found {len(files)} result file(s) to export.")

    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                questions = json.load(f)

            if not questions:
                print(f"Skipping '{path}' as it contains no questions.")
                continue

            xml_content = _convert_mcqs_to_moodle_xml(
                questions=questions,
                category=path.parent.name
            )

            xml_output_path = path.with_name("exported_mcqs.xml")

            with open(xml_output_path, "wb") as f:
                f.write(xml_content)

            print(
                f"Successfully exported {len(questions)} questions to '{xml_output_path}'")

        except (IOError, json.JSONDecodeError) as e:
            print(f"Failed to process '{path}': {e}")
        except Exception as e:
            print(
                f"An unexpected error occurred while processing '{path}': {e}")
