"""
Module for extracting text content from PDF files.
"""

import json
import pymupdf
import logging
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def extract_and_save_pdfs(input_dir: Path, output_dir: Path, chunk_size: int, chunk_overlap: int):
    """
    Processes all PDFs in the input directory and saves the extracted
    text content as JSON files in the output directory.
    """
    logger.info(
        f"Starting PDF extraction from '{input_dir}' to '{output_dir}'")

    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in '{input_dir}'")
        return

    logger.info(f"Found {len(pdf_files)} PDF file(s) to process")

    for pdf_path in pdf_files:
        try:
            doc = pymupdf.open(pdf_path)

            full_text = ""
            for page in doc:
                full_text += page.get_text()

            doc.close()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            chunks = text_splitter.split_text(full_text)

            output_path = output_dir / f"{pdf_path.stem}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved extracted content to '{output_path}'")

        except Exception as e:
            logger.error(f"Failed to process {pdf_path.name}: {e}")
