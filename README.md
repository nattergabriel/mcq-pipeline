# Bachelor's Thesis

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

This command processes all PDF files located in the `input_pdfs_dir` defined in your config. It extracts the content and saves it in the `extracted_content_dir`.

```bash
python main.py extract
```

#### 3.2. Generate MCQs

This command generates multiple-choice questions based on the previously extracted content. It iterates through each experiment defined in your `config.yaml`, using the specified prompts and model parameters. The results for each experiment are saved in a separate, named subfolder.

```bash
python main.py generate
```