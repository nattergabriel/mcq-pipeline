# Bachelor's Thesis: MCQ Generation Pipeline

This repository contains the source code and documentation for my bachelor's thesis, which focuses on the automated generation of multiple-choice questions from university lecture materials.

## Setup

Follow these steps to set up the project environment.

### 1. Clone the Repository

```bash
git clone https://github.com/etaaa/bachelors-thesis
cd bachelors-thesis
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up Environment Variables

Create a file named `.env` in the root of the project by copying the example template (`.env.example`).
Then open it and add your API credentials. You can use any OpenAI-compatible API endpoint (e.g., [Aqueduct AI Gateway](https://aqueduct.ai.datalab.tuwien.ac.at/), OpenAI, etc.).

```bash
OPENAI_BASE_URL="your-api-base-url"
OPENAI_API_KEY="your-api-key"
```

## Usage

The entire workflow is controlled from `main.py`, while all parameters, paths, and experimental setups are managed in the `config.yaml` file.

### 1. Configuration Setup

Before running the pipeline, you'll need to create your own `config.yaml` file. A complete template is provided in `config.example.yaml` to get you started.

### 2. Add PDFs

Place the lecture PDFs you want to process into the directory you specified for `extraction.input_pdfs_dir` in `config.yaml` (e.g., `data/input/pdfs`).

### 3. Run the Pipeline

You can execute the workflow in two ways: either all at once for a complete run or step-by-step for more control.

#### Workflow 1: Run the Full Pipeline

This is the easiest and recommended way to use the tool. This single command will execute the entire process in the following order:

1. Extract content from all PDFs.
2. Generate MCQs based on your defined experiments.
3. Evaluate the generated MCQs using quality criteria.
4. Export the evaluated questions to Moodle XML.

```bash
python main.py run
```

#### Workflow 2: Run Each Step Individually

This approach is useful when you only need to perform a specific part of the process, such as re-running the export step with different weights.

1. Extract Content from PDFs

   This command processes all PDF files found in the `extraction.input_pdfs_dir`. It extracts the content from each file and saves it as a structured JSON file in `output_dir/extracted_pdfs/`.

   ```bash
   python main.py extract
   ```

2. Generate MCQs

   This command runs the experiments defined in your `config.yaml` under `generation.experiments` to generate multiple-choice questions from the extracted content. The results for each experiment are saved in a separate, named subfolder within `output_dir/mcqs/`, always using the filename `generated_mcqs.json`.

   ```bash
   python main.py generate
   ```

3. Evaluate Generated MCQs

   This command evaluates the generated MCQs using the criteria and model defined in the `evaluation` section of your `config.yaml`. The evaluation assesses each question on multiple quality dimensions (clarity, correctness and distractor_quality). The evaluated questions are saved as `evaluated_mcqs.json` in each experiment subfolder.

   ```bash
   python main.py evaluate
   ```

4. Export Evaluated Questions

   This command converts the evaluated questions for all experiments into Moodle-compatible XML files. It automatically searches `output_dir/mcqs/` and processes any file named `evaluated_mcqs.json`. Only questions that meet the quality criteria are exported:
   - The weighted average score across all evaluation metrics must be ≥ 1.5
   - No individual metric score can be 0

   **Notes:**
   - The exported questions will be categorized by their source PDF filename in Moodle, so choosing descriptive and properly formatted filenames for your input PDFs is recommended.
   - In the generated and evaluated JSON files, the correct answer is always listed first. However, when imported into Moodle, the answer options are automatically shuffled.

   ```bash
   python main.py export
   ```