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

Before running the pipeline, set up your configuration in `config.yaml`.

Example `config.yaml`:

```yaml
paths:
  input_pdfs_dir: "data/input/pdfs" 
  extracted_content_dir: "data/output/pdfs/extracted"

experiments:
  - name: "setup1"
    prompt_file: "prompts/prompt1.txt"
    model: "mistral-small-3.1-24b"
    temperature: 0.3
    num_questions: 5

  - name: "setup2"
    prompt_file: "prompts/prompt2.txt"
    model: "mistral-small-3.1-24b"
    temperature: 0.7
    num_questions: 2
```

### 2. Add PDFs

Place the lecture PDFs you want to process into the directory you specified for `input_pdfs_dir` in `config.yaml`.

### 3. Run the Pipline

Once your configuration is set, you can execute the different stages of the pipeline using simple commands. The script will automatically use the settings from your `config.yaml`.

#### 3.1. Extract content from PDFs

This command reads PDFs from your input directory, extracts the text, and saves it to the specified output directory.

```bash
python main.py extract
```

#### 3.2. Generate MCQs

This command loads the extracted text and runs all the experiments you defined in `config.yaml`.

```bash
python main.py generate
```