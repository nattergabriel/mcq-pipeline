# Bachelor's Thesis: MCQ Generation Pipeline

This repository contains the source code and documentation for my bachelor's thesis, which focuses on the automated generation of multiple-choice questions from university lecture materials.

## Setup

Follow these steps to set up the project environment.

### 1. Clone the repository

```bash
git clone https://github.com/etaaa/bachelors-thesis
cd bachelors-thesis
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a file named `.env` in the root of the project by copying the example template (`.env.example`).
Then open the `.env` file and add your specific API credentials. You can get the necessary credentials from the [Aqueduct AI Gateway](https://aqueduct.ai.datalab.tuwien.ac.at/).

```bash
AQUEDUCT_BASE_URL="your-api-base-url"
AQUEDUCT_TOKEN="your-secret-api-token"
```

## Usage

The entire workflow is controlled from `main.py`, while all parameters, paths, and experimental setups are managed in the `config.yaml` file.

### 1. Configuration Setup

Before running the pipeline, you'll need to create your own `config.yaml` file. A complete template is provided in `config.example.yaml` to get you started.

Example `config.yaml`:

```yaml
paths:
  input_pdfs_dir: "data/input/pdfs" 
  extracted_content_dir: "data/output/pdfs/extracted"
  generated_mcqs_dir: "data/output/mcqs"

experiments:
  - name: "setup1"
    prompt_file: "prompts/generation/baseline.txt"
    schema_file: "schemas/mcq.json"
    model: "mistral-small-3.2-24b"
    temperature: 0.8
    num_questions: 5

  - name: "setup2"
    prompt_file: "prompts/generation/fewshot.txt"
    schema_file: "schemas/mcq.json"
    model: "mistral-small-3.2-24b"
    temperature: 0.5
    num_questions: 2
```

### 2. Add PDFs

Place the lecture PDFs you want to process into the directory you specified for `input_pdfs_dir` in `config.yaml`.

### 3. Run the Pipline

Once your configuration is set, you can execute the different stages of the pipeline using simple commands. The script will automatically use the settings from your `config.yaml`.

#### 3.1. Extract content from PDFs

This command processes all PDF files found in the `input_pdfs_dir`. It extracts the content from each file and saves it as a structured JSON file in the `extracted_content_dir`.

```bash
python main.py extract
```

#### 3.2. Generate MCQs

This command runs the experiments defined in your `config.yaml` to generate multiple-choice questions from the extracted content. The results for each experiment are saved in a separate, named subfolder within the `generated_mcqs_dir`, always using the filename `generated_mcqs.json`.

```bash
python main.py generate
```

#### 3.3. Export Generated Questions

This command converts the generated questions for all completed experiments into Moodle-compatible XML files. It automatically searches the `generated_mcqs_dir` and processes any file named `generated_mcqs.json` found in the experiment subfolders.

```bash
python main.py export
```