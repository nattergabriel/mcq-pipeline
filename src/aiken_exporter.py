import string
from pathlib import Path
from typing import List, Dict, Any


def export_to_aiken_format(questions: List[Dict[str, Any]], output_path: Path):
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

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(formatted_blocks))
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

    output_dir = Path("data/output/final_mcqs")

    export_to_aiken_format(
        questions=sample_questions,
        output_path=output_dir / "demo_mcqs.txt"
    )


if __name__ == "__main__":
    main()
