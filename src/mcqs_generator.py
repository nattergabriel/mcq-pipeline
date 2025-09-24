import json
from pathlib import Path
from typing import List, Dict, Any

from src.llm_client import LLMClient


def generate_mcqs(experiments: List[Dict[str, Any]], extracted_content_dir: Path, mcqs_output_dir: Path):
    """
    Generates MCQs for each experiment defined in the configuration.
    """
    try:
        llm_client = LLMClient()
    except ValueError as e:
        print(f"Error initializing LLM Client: {e}")
        return

    content_files = list(extracted_content_dir.glob("*.json"))
    if not content_files:
        print(
            f"No extracted content files found in '{extracted_content_dir}'.")
        return

    for experiment in experiments:
        name = experiment.get("name")
        prompt_file = Path(experiment.get("prompt_file"))
        model = experiment.get("model")
        temperature = experiment.get("temperature", 0.5)
        num_questions = experiment.get("num_questions", 1)

        try:
            system_prompt = prompt_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(
                f"Prompt file not found at '{prompt_file}'. Skipping.")
            continue

        all_generated_questions = []
        for content_path in content_files:
            try:
                with open(content_path, "r", encoding="utf-8") as f:
                    pages = json.load(f)

                all_blocks = []
                for page in pages:
                    for block in page.get("text_blocks", []):
                        all_blocks.append(block)
                full_text = "\n".join(all_blocks)

                for i in range(num_questions):
                    response_str = llm_client.call_llm(
                        system_message=system_prompt,
                        user_message=full_text,
                        model=model,
                        temperature=temperature)

                    try:
                        question_data = json.loads(response_str)

                        if "text" in question_data and "options" in question_data:
                            all_generated_questions.append(question_data)
                        else:
                            print(
                                f"LLM response for question {i+1} has an invalid schema. Skipping.")

                    except json.JSONDecodeError:
                        print(
                            f"Failed to decode JSON from LLM response for question {i+1}. Response:\n{response_str}")

            except (IOError, json.JSONDecodeError) as e:
                print(f"Error processing content file {content_path}: {e}")

        if all_generated_questions:
            experiment_output_dir = mcqs_output_dir / name
            experiment_output_dir.mkdir(parents=True, exist_ok=True)
            output_file_path = experiment_output_dir / "generated_mcqs.json"

            try:
                with open(output_file_path, "w", encoding="utf-8") as f:
                    json.dump(
                        all_generated_questions,
                        f,
                        indent=4,
                        ensure_ascii=False)
                print(
                    f"Successfully saved {len(all_generated_questions)} questions to '{output_file_path}'")
            except IOError as e:
                print(
                    f"Error writing output file for experiment '{name}': {e}")
