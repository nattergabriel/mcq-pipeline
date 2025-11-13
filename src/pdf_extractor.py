"""
Module for extracting text content from PDF files and structuring it
into pages and text blocks.
"""

import json
import logging
import pymupdf
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

NOISE_PATTERNS = []


def _extract_text_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Extracts structured text blocks from a PDF and filters out common noise
    patterns.
    """
    logger.info(f"Extracting text from PDF: {pdf_path.name}")
    extracted_content = []
    try:
        doc = pymupdf.open(pdf_path)
        for page_number in range(len(doc)):
            blocks = doc[page_number].get_text("blocks")

            page_text_blocks = []
            for block in blocks:
                text = block[4]

                is_noise = any(pattern in text for pattern in NOISE_PATTERNS)
                if not is_noise:
                    clean_text = text.rstrip("\n").strip()
                    page_text_blocks.append(clean_text)

            extracted_content.append({
                "page": page_number + 1,
                "text_blocks": page_text_blocks
            })
        logger.info(
            f"Successfully extracted {len(extracted_content)} pages from {pdf_path.name}")
        return extracted_content
    except Exception as e:
        logger.error(f"Failed to process {pdf_path.name}: {e}")
        return []


def extract_and_save_pdfs(input_dir: Path, output_dir: Path):
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
        content = _extract_text_from_pdf(pdf_path)
        if content:
            output_path = output_dir / (pdf_path.stem + ".json")
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=4, ensure_ascii=False)
                logger.info(f"Saved extracted content to '{output_path}'")
            except IOError as e:
                logger.error(f"Could not write to file '{output_path}': {e}")
