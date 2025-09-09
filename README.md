# Bachelor's Thesis

This repository contains the source code and documentation for my bachelor's thesis, which focuses on the automated generation of multiple-choice questions from university lecture materials.

## Setup

Follow these steps to set up the project environment.

###  Clone the repository

```bash
git clone https://github.com/etaaa/bachelors-thesis
cd bachelors-thesis
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Set up environment variables

Create a file named `.env` in the root of the project by copying the example template.
Then open the `.env` file and add your specific API credentials. You can get the necessary credentials from the [Aqueduct AI Gateway](https://aqueduct.ai.datalab.tuwien.ac.at/).

```bash
AQUEDUCT_BASE_URL="your-api-base-url"
AQUEDUCT_TOKEN="your-secret-api-token"
```