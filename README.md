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

The entire workflow is controlled from `main.py` using a command-line interface. For a full list of commands and their options, you can use the built-in help flag at any time:


See all available commands (e.g., extract):
```bash
python main.py --help
```

See the specific options for a single command:
```bash
python main.py <command> --help
```

### 1. Add PDFs

Place the lecture PDFs you want to process into the `data/input/pdfs/` directory.

### 2. Extract text from PDFs

Run the extract command. This uses the default directories to process your PDFs and save the extracted text.

```bash
python main.py extract
```