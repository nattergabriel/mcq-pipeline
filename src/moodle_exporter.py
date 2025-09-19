import string
from pathlib import Path
from xml.dom import minidom
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET


def export_as_aiken(questions: List[Dict[str, Any]], output_path: Path):
    """
    Converts a list of question dictionaries to the Moodle Aiken format and
    saves it to a text file.
    """
    formatted_blocks = []

    for question in questions:
        question_block = [question["question_text"]]
        correct_answer_letter = None

        for i, option in enumerate(question["options"]):
            letter = string.ascii_uppercase[i]
            question_block.append(f"{letter}. {option['text']}")

            if option.get("is_correct", False):
                correct_answer_letter = letter

        if correct_answer_letter:
            question_block.append(f"ANSWER: {correct_answer_letter}")
        else:
            print(
                f"No correct answer found for question: '{question['question_text']}' - skipping.")
            continue

        formatted_blocks.append("\n".join(question_block))

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(formatted_blocks))
    except IOError as e:
        print(f"Could not write to file '{output_path}': {e}")


def export_as_moodle_xml(questions: List[Dict[str, Any]], output_path: Path, category: Optional[str] = ""):
    """
    Converts a list of question dictionaries to the MINIMAL Moodle XML format
    and saves it to an XML file.
    """
    root = ET.Element("quiz")

    if category:
        question = ET.SubElement(root, "question", type="category")
        question_category = ET.SubElement(question, "category")
        question_category_text = ET.SubElement(question_category, "text")
        question_category_text.text = f"$course$/{category}"

    for q_data in questions:
        question = ET.SubElement(root, "question", type="multichoice")

        name = ET.SubElement(question, "name")
        name_text = ET.SubElement(name, "text")
        name_text.text = q_data["question_text"]

        questiontext = ET.SubElement(question, "questiontext")
        questiontext_text = ET.SubElement(questiontext, "text")
        questiontext_text.text = q_data["question_text"]

        ET.SubElement(question, "single").text = "true"

        for option in q_data["options"]:
            fraction = "100" if option.get("is_correct", False) else "0"
            answer = ET.SubElement(question, "answer", fraction=fraction)
            answer_text = ET.SubElement(answer, "text")
            answer_text.text = option['text']

    try:
        raw = ET.tostring(root, 'utf-8')
        parsed = minidom.parseString(raw)
        prettified = parsed.toprettyxml(indent="  ", encoding="utf-8")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(prettified)
    except IOError as e:
        print(f"Could not write to file '{output_path}': {e}")


def main():
    """
    An example function to test the Aiken export process.
    """
    sample_questions = [
        {
            "question_text": "Was ist der Hauptunterschied zwischen einer `while`-Schleife und einer `do-while`-Schleife in Java?",
            "options": [
                {
                    "text": "Eine `do-while`-Schleife ist immer schneller als eine `while`-Schleife.",
                    "is_correct": False
                },
                {
                    "text": "Der Schleifenrumpf einer `do-while`-Schleife wird garantiert mindestens einmal ausgeführt.",
                    "is_correct": True
                },
                {
                    "text": "Eine `while`-Schleife kann keine booleschen Variablen als Bedingung verwenden.",
                    "is_correct": False
                },
                {
                    "text": "`do-while`-Schleifen werden hauptsächlich als Zählschleifen verwendet.",
                    "is_correct": False
                }
            ]
        },
        {
            "question_text": "Welche Art von Schleife eignet sich typischerweise am besten, wenn die genaue Anzahl der Iterationen im Voraus bekannt ist, wie z.B. beim Zählen von 0 bis 10?",
            "options": [
                {
                    "text": "Eine `for`-Schleife (Zählschleife)",
                    "is_correct": True
                },
                {
                    "text": "Eine `do-while`-Schleife",
                    "is_correct": False
                },
                {
                    "text": "Eine Endlosschleife mit `break`-Anweisung",
                    "is_correct": False
                }
            ]
        }
    ]

    output_dir = Path("data/output/mcqs/final")

    export_as_aiken(
        questions=sample_questions,
        output_path=output_dir / "aiken_export.txt"
    )

    export_as_moodle_xml(
        questions=sample_questions,
        output_path=output_dir / "moodle_xml_export.xml",
        category="2025S-4-EP1-Schleifen"
    )


if __name__ == "__main__":
    main()
